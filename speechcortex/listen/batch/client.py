# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Batch transcription clients (sync and async) on httpx.

Usage::

    batch = client.listen.batch.v1

    job = batch.submit_job(presigned_url="https://example.com/audio.mp3", language="en-US")
    result = batch.wait_for_completion(job.job_id, polling_interval=3.0, timeout=600.0)

    # or, for file uploads (content type inferred from the file extension):
    result = batch.transcribe(audio_file="meeting.mp3", language="en-US")
"""

import asyncio
import logging
import mimetypes
import time
import typing
from pathlib import Path
from uuid import UUID

import httpx

from ...core.api_error import ApiError
from ...core.client_options import ClientOptions
from ...core.query_encoder import encode_query
from ...core.remove_none_from_dict import remove_none_from_dict
from ...core.request_options import RequestOptions, get_request_options_value
from ...errors import (
    BatchTimeoutError,
    JobFailedError,
    JobNotFoundError,
    TranscriptionNotReadyError,
)
from .options import Channel, Diarize, Extra, Language, Model, Pci, Punctuate, SmartFormat
from .types import JobDetails, TranscriptionResult, TranscriptionStatus

_logger = logging.getLogger("speechcortex")

_DEFAULT_REQUEST_TIMEOUT: float = 300.0
_FALLBACK_CONTENT_TYPE = "audio/mpeg"


def _build_params(
    *,
    language: Language,
    model: Model,
    diarize: Diarize | None,
    punctuate: Punctuate | None,
    smart_format: SmartFormat | None,
    channel: Channel | None,
    pci: Pci | None,
    extra: Extra | None,
    request_options: RequestOptions | None,
) -> dict[str, typing.Any]:
    params: dict[str, typing.Any] = {
        "language": language,
        "model": model,
        "diarize": diarize,
        "punctuate": punctuate,
        "smart_format": smart_format,
        "channel": channel,
        "pci": pci,
    }
    params.update(extra or {})
    params.update(
        get_request_options_value(request_options, "additional_query_parameters", {}) or {}
    )
    encoded = encode_query(remove_none_from_dict(params))
    return dict(encoded) if encoded else {}


def _guess_content_type(filename: str) -> str:
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or _FALLBACK_CONTENT_TYPE


def _error_from_response(response: httpx.Response) -> ApiError:
    if response.status_code == 401:
        return ApiError(
            status_code=401,
            body="Invalid credentials. Check your API key.",
        )
    body: typing.Any
    try:
        body = response.json()
    except Exception:
        body = response.text
    return ApiError(status_code=response.status_code, body=body)


def _validate_job_response(data: dict[str, typing.Any]) -> JobDetails:
    if "job_id" not in data:
        raise ApiError(
            body=f"Job submission failed: {data.get('message', 'no job_id in response')}"
        )
    return JobDetails.model_validate(data)


class BatchV1Client:
    """Batch transcription client (``client.listen.batch.v1``)."""

    def __init__(self, *, config: ClientOptions, http_client: httpx.Client | None = None):
        self._config = config
        self._injected_client = http_client
        self._client: httpx.Client | None = None

    def __enter__(self) -> "BatchV1Client":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def submit_job(
        self,
        *,
        presigned_url: str | None = None,
        audio_file: str | Path | typing.BinaryIO | bytes | None = None,
        language: Language = "en-US",
        model: Model = "batch-zeus",
        diarize: Diarize | None = None,
        punctuate: Punctuate | None = None,
        smart_format: SmartFormat | None = None,
        channel: Channel | None = None,
        pci: Pci | None = None,
        extra: Extra | None = None,
        request_options: RequestOptions | None = None,
    ) -> JobDetails:
        """
        Submit a transcription job.

        Provide exactly one of ``presigned_url`` or ``audio_file``.

        Args:
            presigned_url: Presigned URL to the audio file (S3, etc.).
            audio_file: Audio file path, file-like object, or bytes. The
                multipart content type is inferred from the file extension.
            language: Language code (default ``en-US``).
            model: Model to use (default ``batch-zeus``).
            diarize: Enable speaker diarization.
            punctuate: Enable punctuation.
            smart_format: Enable smart formatting.
            channel: Number of audio channels.
            pci: PCI compliance flag.
            extra: Additional query parameters forwarded as-is.
            request_options: Per-request overrides.

        Raises:
            ApiError: On HTTP errors, including invalid credentials (401).
            ValueError: If both or neither of presigned_url/audio_file are given.
        """
        if presigned_url and audio_file:
            raise ValueError("Cannot specify both presigned_url and audio_file")
        if not presigned_url and not audio_file:
            raise ValueError("Must provide either presigned_url or audio_file")

        params = _build_params(
            language=language,
            model=model,
            diarize=diarize,
            punctuate=punctuate,
            smart_format=smart_format,
            channel=channel,
            pci=pci,
            extra=extra,
            request_options=request_options,
        )

        if presigned_url:
            data = self._request_json(
                "POST",
                "/transcribe",
                params=params,
                json={"presigned_url": presigned_url},
                request_options=request_options,
            )
        else:
            data = self._request_json(
                "POST",
                "/transcribe/upload",
                params=params,
                files=self._multipart(audio_file),  # type: ignore[arg-type]
                request_options=request_options,
            )
        return _validate_job_response(data)

    def get_status(self, job_id: str | UUID) -> TranscriptionStatus:
        """Get the current status of a transcription job."""
        data = self._request_json("GET", f"/status/{job_id}")
        return TranscriptionStatus.model_validate(data)

    def get_transcription(self, job_id: str | UUID) -> TranscriptionResult:
        """
        Get the transcription result for a completed job.

        Raises:
            TranscriptionNotReadyError: If the job is not completed yet (202).
            JobFailedError: If the job failed.
            JobNotFoundError: If the job does not exist (404).
        """
        data = self._request_json("GET", f"/get_transcription/{job_id}", allow_202=True)
        if data.get("_status_code") == 202:
            raise TranscriptionNotReadyError(str(job_id), data.get("status", "unknown"))
        if str(data.get("status", "")).upper() == "FAILED":
            raise JobFailedError(str(job_id), data.get("message", "Transcription failed"))
        return TranscriptionResult.model_validate(data)

    def wait_for_completion(
        self,
        job_id: str | UUID,
        *,
        polling_interval: float = 3.0,
        timeout: float | None = None,
    ) -> TranscriptionResult:
        """
        Poll job status until completion and return the result.

        Args:
            job_id: Job identifier.
            polling_interval: Seconds between status checks (default 3.0).
            timeout: Maximum seconds to wait; None waits indefinitely.
        """
        job_id_str = str(job_id)
        deadline = time.monotonic() + timeout if timeout is not None else None

        while True:
            status = self.get_status(job_id_str)
            status_upper = status.status.upper()

            if status_upper == "COMPLETED":
                return self.get_transcription(job_id_str)
            if status_upper == "FAILED":
                raise JobFailedError(job_id_str, status.error_message or "Job failed")

            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise BatchTimeoutError(job_id_str, timeout)  # type: ignore[arg-type]
                time.sleep(min(polling_interval, remaining))
            else:
                time.sleep(polling_interval)

    def transcribe(
        self,
        *,
        presigned_url: str | None = None,
        audio_file: str | Path | typing.BinaryIO | bytes | None = None,
        language: Language = "en-US",
        model: Model = "batch-zeus",
        diarize: Diarize | None = None,
        punctuate: Punctuate | None = None,
        smart_format: SmartFormat | None = None,
        channel: Channel | None = None,
        pci: Pci | None = None,
        extra: Extra | None = None,
        polling_interval: float = 3.0,
        timeout: float | None = None,
        request_options: RequestOptions | None = None,
    ) -> TranscriptionResult:
        """Convenience method: submit a job and wait for completion."""
        job = self.submit_job(
            presigned_url=presigned_url,
            audio_file=audio_file,
            language=language,
            model=model,
            diarize=diarize,
            punctuate=punctuate,
            smart_format=smart_format,
            channel=channel,
            pci=pci,
            extra=extra,
            request_options=request_options,
        )
        return self.wait_for_completion(
            job.job_id, polling_interval=polling_interval, timeout=timeout
        )

    def close(self) -> None:
        """Close the underlying HTTP client. Safe to call multiple times."""
        if self._client is not None:
            self._client.close()
            self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _http_client(self) -> httpx.Client:
        if self._client is None:
            self._client = self._injected_client or httpx.Client(
                base_url=self._config.rest_base_url,
                headers=self._config.get_rest_headers(),
            )
        return self._client

    @staticmethod
    def _multipart(
        audio_file: str | Path | typing.BinaryIO | bytes,
    ) -> dict[str, typing.Any]:
        if isinstance(audio_file, (str, Path)):
            file_path = Path(audio_file)
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            return {
                "audio_file": (
                    file_path.name,
                    file_path.read_bytes(),
                    _guess_content_type(file_path.name),
                )
            }
        if isinstance(audio_file, bytes):
            return {"audio_file": ("audio", audio_file, _FALLBACK_CONTENT_TYPE)}
        # File-like object
        filename = getattr(audio_file, "name", "audio")
        filename = Path(str(filename)).name
        return {
            "audio_file": (
                filename,
                audio_file.read(),
                _guess_content_type(filename),
            )
        }

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, typing.Any] | None = None,
        json: dict[str, typing.Any] | None = None,
        files: dict[str, typing.Any] | None = None,
        allow_202: bool = False,
        request_options: RequestOptions | None = None,
    ) -> dict[str, typing.Any]:
        path = f"{self._config.batch_path}{path}"
        timeout = get_request_options_value(
            request_options, "timeout", _DEFAULT_REQUEST_TIMEOUT
        )
        try:
            response = self._http_client().request(
                method,
                path,
                params=params,
                json=json,
                files=files,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            raise ApiError(body=f"Request failed: {exc}") from exc

        if response.status_code == 202 and allow_202:
            data: dict = response.json()
            data["_status_code"] = 202
            return data
        if response.status_code >= 400:
            if response.status_code == 404:
                raise JobNotFoundError("unknown", "Resource not found")
            raise _error_from_response(response)

        result: dict = response.json()
        return result


class AsyncBatchV1Client:
    """Async batch transcription client."""

    def __init__(
        self, *, config: ClientOptions, http_client: httpx.AsyncClient | None = None
    ):
        self._config = config
        self._injected_client = http_client
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AsyncBatchV1Client":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def submit_job(
        self,
        *,
        presigned_url: str | None = None,
        audio_file: str | Path | typing.BinaryIO | bytes | None = None,
        language: Language = "en-US",
        model: Model = "batch-zeus",
        diarize: Diarize | None = None,
        punctuate: Punctuate | None = None,
        smart_format: SmartFormat | None = None,
        channel: Channel | None = None,
        pci: Pci | None = None,
        extra: Extra | None = None,
        request_options: RequestOptions | None = None,
    ) -> JobDetails:
        """Async version of :meth:`BatchV1Client.submit_job`."""
        if presigned_url and audio_file:
            raise ValueError("Cannot specify both presigned_url and audio_file")
        if not presigned_url and not audio_file:
            raise ValueError("Must provide either presigned_url or audio_file")

        params = _build_params(
            language=language,
            model=model,
            diarize=diarize,
            punctuate=punctuate,
            smart_format=smart_format,
            channel=channel,
            pci=pci,
            extra=extra,
            request_options=request_options,
        )

        if presigned_url:
            data = await self._request_json(
                "POST",
                "/transcribe",
                params=params,
                json={"presigned_url": presigned_url},
                request_options=request_options,
            )
        else:
            data = await self._request_json(
                "POST",
                "/transcribe/upload",
                params=params,
                files=self._multipart(audio_file),  # type: ignore[arg-type]
                request_options=request_options,
            )
        return _validate_job_response(data)

    async def get_status(self, job_id: str | UUID) -> TranscriptionStatus:
        """Async version of :meth:`BatchV1Client.get_status`."""
        data = await self._request_json("GET", f"/status/{job_id}")
        return TranscriptionStatus.model_validate(data)

    async def get_transcription(self, job_id: str | UUID) -> TranscriptionResult:
        """Async version of :meth:`BatchV1Client.get_transcription`."""
        data = await self._request_json("GET", f"/get_transcription/{job_id}", allow_202=True)
        if data.get("_status_code") == 202:
            raise TranscriptionNotReadyError(str(job_id), data.get("status", "unknown"))
        if str(data.get("status", "")).upper() == "FAILED":
            raise JobFailedError(str(job_id), data.get("message", "Transcription failed"))
        return TranscriptionResult.model_validate(data)

    async def wait_for_completion(
        self,
        job_id: str | UUID,
        *,
        polling_interval: float = 3.0,
        timeout: float | None = None,
    ) -> TranscriptionResult:
        """Async version of :meth:`BatchV1Client.wait_for_completion`."""
        job_id_str = str(job_id)
        deadline = time.monotonic() + timeout if timeout is not None else None

        while True:
            status = await self.get_status(job_id_str)
            status_upper = status.status.upper()

            if status_upper == "COMPLETED":
                return await self.get_transcription(job_id_str)
            if status_upper == "FAILED":
                raise JobFailedError(job_id_str, status.error_message or "Job failed")

            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise BatchTimeoutError(job_id_str, timeout)  # type: ignore[arg-type]
                await asyncio.sleep(min(polling_interval, remaining))
            else:
                await asyncio.sleep(polling_interval)

    async def transcribe(
        self,
        *,
        presigned_url: str | None = None,
        audio_file: str | Path | typing.BinaryIO | bytes | None = None,
        language: Language = "en-US",
        model: Model = "batch-zeus",
        diarize: Diarize | None = None,
        punctuate: Punctuate | None = None,
        smart_format: SmartFormat | None = None,
        channel: Channel | None = None,
        pci: Pci | None = None,
        extra: Extra | None = None,
        polling_interval: float = 3.0,
        timeout: float | None = None,
        request_options: RequestOptions | None = None,
    ) -> TranscriptionResult:
        """Convenience method: submit a job and wait for completion."""
        job = await self.submit_job(
            presigned_url=presigned_url,
            audio_file=audio_file,
            language=language,
            model=model,
            diarize=diarize,
            punctuate=punctuate,
            smart_format=smart_format,
            channel=channel,
            pci=pci,
            extra=extra,
            request_options=request_options,
        )
        return await self.wait_for_completion(
            job.job_id, polling_interval=polling_interval, timeout=timeout
        )

    async def close(self) -> None:
        """Close the underlying HTTP client. Safe to call multiple times."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _http_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = self._injected_client or httpx.AsyncClient(
                base_url=self._config.rest_base_url,
                headers=self._config.get_rest_headers(),
            )
        return self._client

    _multipart = staticmethod(BatchV1Client._multipart)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, typing.Any] | None = None,
        json: dict[str, typing.Any] | None = None,
        files: dict[str, typing.Any] | None = None,
        allow_202: bool = False,
        request_options: RequestOptions | None = None,
    ) -> dict[str, typing.Any]:
        path = f"{self._config.batch_path}{path}"
        timeout = get_request_options_value(
            request_options, "timeout", _DEFAULT_REQUEST_TIMEOUT
        )
        try:
            response = await self._http_client().request(
                method,
                path,
                params=params,
                json=json,
                files=files,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            raise ApiError(body=f"Request failed: {exc}") from exc

        if response.status_code == 202 and allow_202:
            data: dict = response.json()
            data["_status_code"] = 202
            return data
        if response.status_code >= 400:
            if response.status_code == 404:
                raise JobNotFoundError("unknown", "Resource not found")
            raise _error_from_response(response)

        result: dict = response.json()
        return result
