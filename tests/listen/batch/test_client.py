# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""Batch client tests against httpx.MockTransport-mocked endpoints."""

import asyncio
import json

import httpx
import pytest

from speechcortex.core.api_error import ApiError
from speechcortex.core.client_options import ClientOptions
from speechcortex.errors import (
    BatchTimeoutError,
    JobFailedError,
    JobNotFoundError,
    TranscriptionNotReadyError,
)
from speechcortex.listen.batch.client import AsyncBatchV1Client, BatchV1Client
from speechcortex.listen.batch.types import JobDetails, TranscriptionStatus

BASE = "https://api.example.ai"
BATCH = "/api/v1/transcription"
API_KEY = "test-key"

JOB_RESPONSE = {
    "job_id": "0f8a1d5e-6b7c-4a2d-9e8f-0a1b2c3d4e5f",
    "status": "pending",
    "created_at": "2026-08-29T10:00:00Z",
    "updated_at": "2026-08-29T10:00:05Z",
    "error_message": None,
}

RESULT_RESPONSE = {
    "job_id": "0f8a1d5e-6b7c-4a2d-9e8f-0a1b2c3d4e5f",
    "status": "completed",
    "transcription": {"segments": [{"text": "hello"}]},
    "message": "done",
}


class MockRouter:
    """
    Minimal request router used with httpx.MockTransport.

    Maps (method, path) to either a response or a list of responses (consumed
    in order, for polling tests). Records all requests for assertions.
    """

    def __init__(self):
        self.routes: dict = {}
        self.requests: list = []

    def on(self, method: str, path: str, *responses):
        self.routes[(method, path)] = list(responses)
        return self

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        responses = self.routes.get((request.method, request.url.path))
        if not responses:
            return httpx.Response(404, json={"detail": f"unrouted {request.url.path}"})
        response = responses.pop(0) if len(responses) > 1 else responses[0]
        if callable(response):
            return response(request)
        return response


def make_client(router: MockRouter) -> BatchV1Client:
    config = ClientOptions(api_key=API_KEY, url="wss://api.example.ai")
    transport = httpx.MockTransport(router)
    return BatchV1Client(
        config=config,
        http_client=httpx.Client(
            base_url=BASE, headers=config.get_rest_headers(), transport=transport
        ),
    )


def make_async_client(router: MockRouter) -> AsyncBatchV1Client:
    config = ClientOptions(api_key=API_KEY, url="wss://api.example.ai")
    transport = httpx.MockTransport(router)
    return AsyncBatchV1Client(
        config=config,
        http_client=httpx.AsyncClient(
            base_url=BASE, headers=config.get_rest_headers(), transport=transport
        ),
    )


def test_submit_job_presigned_url():
    router = MockRouter().on("POST", f"{BATCH}/transcribe", httpx.Response(200, json=JOB_RESPONSE))
    job = make_client(router).submit_job(presigned_url="https://s3.test/audio.mp3", diarize=True)

    request = router.requests[0]
    assert request.method == "POST"
    assert request.headers["X-API-Key"] == API_KEY
    assert json.loads(request.content) == {"presigned_url": "https://s3.test/audio.mp3"}
    assert "language=en-US" in str(request.url)
    assert "model=batch-zeus" in str(request.url)
    assert "diarize=true" in str(request.url)
    # unset options are omitted (v7-style: only send what the caller sets)
    assert "pci=" not in str(request.url)

    assert isinstance(job, JobDetails)
    assert str(job.job_id) == JOB_RESPONSE["job_id"]
    assert job.status == "pending"
    # Z-suffix timestamps parsed
    assert job.created_at is not None
    assert job.created_at.year == 2026


def test_submit_job_file_upload_content_type_inferred(tmp_path):
    audio = tmp_path / "meeting.wav"
    audio.write_bytes(b"RIFF....")
    router = MockRouter().on("POST", f"{BATCH}/transcribe/upload", httpx.Response(200, json=JOB_RESPONSE))

    make_client(router).submit_job(audio_file=audio)

    body = router.requests[0].content
    assert b'name="audio_file"' in body
    assert b"meeting.wav" in body
    # mimetypes may map .wav to audio/wav or audio/x-wav
    assert b"audio/wav" in body or b"audio/x-wav" in body


def test_submit_job_file_upload_fallback_content_type(tmp_path):
    audio = tmp_path / "meeting.unknownext"
    audio.write_bytes(b"data")
    router = MockRouter().on("POST", f"{BATCH}/transcribe/upload", httpx.Response(200, json=JOB_RESPONSE))

    make_client(router).submit_job(audio_file=audio)

    assert b"audio/mpeg" in router.requests[0].content


def test_submit_job_requires_exactly_one_source():
    with pytest.raises(ValueError):
        make_client(MockRouter()).submit_job()
    with pytest.raises(ValueError):
        make_client(MockRouter()).submit_job(presigned_url="x", audio_file=b"y")


def test_get_status():
    router = MockRouter().on("GET", f"{BATCH}/status/abc", httpx.Response(200, json=JOB_RESPONSE))
    status = make_client(router).get_status("abc")
    assert isinstance(status, TranscriptionStatus)
    assert status.status == "pending"


def test_get_transcription_completed():
    router = MockRouter().on(
        "GET", f"{BATCH}/get_transcription/abc", httpx.Response(200, json=RESULT_RESPONSE)
    )
    result = make_client(router).get_transcription("abc")
    assert result.transcription == {"segments": [{"text": "hello"}]}
    assert result.message == "done"


def test_get_transcription_not_ready():
    router = MockRouter().on(
        "GET", f"{BATCH}/get_transcription/abc", httpx.Response(202, json={"status": "processing"})
    )
    with pytest.raises(TranscriptionNotReadyError):
        make_client(router).get_transcription("abc")


def test_get_transcription_failed():
    router = MockRouter().on(
        "GET",
        f"{BATCH}/get_transcription/abc",
        httpx.Response(200, json={"job_id": JOB_RESPONSE["job_id"], "status": "FAILED", "message": "bad audio"}),
    )
    with pytest.raises(JobFailedError, match="bad audio"):
        make_client(router).get_transcription("abc")


def test_401_raises_api_error():
    router = MockRouter().on("GET", f"{BATCH}/status/abc", httpx.Response(401, json={"detail": "nope"}))
    with pytest.raises(ApiError) as exc_info:
        make_client(router).get_status("abc")
    assert exc_info.value.status_code == 401


def test_404_raises_job_not_found():
    router = MockRouter().on("GET", f"{BATCH}/status/abc", httpx.Response(404, json={"detail": "missing"}))
    with pytest.raises(JobNotFoundError):
        make_client(router).get_status("abc")


def test_wait_for_completion_polls_until_completed():
    router = MockRouter().on(
        "GET",
        f"{BATCH}/status/abc",
        httpx.Response(200, json={"job_id": JOB_RESPONSE["job_id"], "status": "processing"}),
        httpx.Response(200, json={"job_id": JOB_RESPONSE["job_id"], "status": "COMPLETED"}),
    ).on("GET", f"{BATCH}/get_transcription/abc", httpx.Response(200, json=RESULT_RESPONSE))

    result = make_client(router).wait_for_completion("abc", polling_interval=0)
    status_requests = [r for r in router.requests if "/status/" in r.url.path]
    assert len(status_requests) == 2
    assert result.transcription is not None


def test_wait_for_completion_raises_on_failed():
    router = MockRouter().on(
        "GET",
        f"{BATCH}/status/abc",
        httpx.Response(200, json={"job_id": JOB_RESPONSE["job_id"], "status": "FAILED", "error_message": "transcode error"}),
    )
    with pytest.raises(JobFailedError, match="transcode error"):
        make_client(router).wait_for_completion("abc", polling_interval=0)


def test_wait_for_completion_timeout():
    router = MockRouter().on(
        "GET", f"{BATCH}/status/abc", httpx.Response(200, json={"job_id": JOB_RESPONSE["job_id"], "status": "processing"})
    )
    with pytest.raises(BatchTimeoutError):
        make_client(router).wait_for_completion("abc", polling_interval=0, timeout=0.05)


def test_transcribe_convenience():
    router = (
        MockRouter()
        .on("POST", f"{BATCH}/transcribe", httpx.Response(200, json=JOB_RESPONSE))
        .on(
            "GET",
            f"{BATCH}/status/{JOB_RESPONSE['job_id']}",
            httpx.Response(200, json={"job_id": JOB_RESPONSE["job_id"], "status": "completed"}),
        )
        .on(
            "GET",
            f"{BATCH}/get_transcription/{JOB_RESPONSE['job_id']}",
            httpx.Response(200, json=RESULT_RESPONSE),
        )
    )
    result = make_client(router).transcribe(presigned_url="https://s3.test/a.mp3", polling_interval=0)
    assert result.status == "completed"


def test_extra_params_forwarded():
    router = MockRouter().on("POST", f"{BATCH}/transcribe", httpx.Response(200, json=JOB_RESPONSE))
    make_client(router).submit_job(presigned_url="https://s3.test/a.mp3", extra={"new_flag": True})
    assert "new_flag=true" in str(router.requests[0].url)


def test_async_submit_and_wait():
    router = (
        MockRouter()
        .on("POST", f"{BATCH}/transcribe", httpx.Response(200, json=JOB_RESPONSE))
        .on(
            "GET",
            f"{BATCH}/status/{JOB_RESPONSE['job_id']}",
            httpx.Response(200, json={"job_id": JOB_RESPONSE["job_id"], "status": "completed"}),
        )
        .on(
            "GET",
            f"{BATCH}/get_transcription/{JOB_RESPONSE['job_id']}",
            httpx.Response(200, json=RESULT_RESPONSE),
        )
    )

    async def run():
        async with make_async_client(router) as batch:
            return await batch.transcribe(presigned_url="https://s3.test/a.mp3", polling_interval=0)

    result = asyncio.run(run())
    assert result.transcription is not None


def test_async_401_raises_api_error():
    router = MockRouter().on("GET", f"{BATCH}/status/abc", httpx.Response(401, json={"detail": "nope"}))

    async def run():
        async with make_async_client(router) as batch:
            await batch.get_status("abc")

    with pytest.raises(ApiError):
        asyncio.run(run())
