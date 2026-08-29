# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""Batch response model parsing tests."""

from datetime import datetime, timezone
from uuid import UUID

from speechcortex.listen.batch.types import (
    JobDetails,
    TranscriptionResult,
    TranscriptionStatus,
)

JOB_ID = "0f8a1d5e-6b7c-4a2d-9e8f-0a1b2c3d4e5f"


def test_job_details_parses_z_suffix_timestamps():
    job = JobDetails.model_validate(
        {
            "job_id": JOB_ID,
            "status": "processing",
            "created_at": "2026-08-29T10:00:00Z",
            "updated_at": "2026-08-29T10:01:00Z",
        }
    )
    assert job.job_id == UUID(JOB_ID)
    assert job.created_at == datetime(2026, 8, 29, 10, 0, 0, tzinfo=timezone.utc)
    assert job.updated_at == datetime(2026, 8, 29, 10, 1, 0, tzinfo=timezone.utc)


def test_job_details_accepts_uuid_object():
    job = JobDetails.model_validate({"job_id": UUID(JOB_ID), "status": "pending"})
    assert job.job_id == UUID(JOB_ID)


def test_job_details_missing_timestamps_is_none():
    job = TranscriptionStatus.model_validate({"job_id": JOB_ID, "status": "pending"})
    assert job.created_at is None
    assert job.updated_at is None
    assert job.error_message is None


def test_unknown_fields_preserved():
    status = TranscriptionStatus.model_validate(
        {"job_id": JOB_ID, "status": "pending", "new_field": 42}
    )
    assert status.new_field == 42


def test_transcription_result_keeps_raw_transcription_dict():
    transcription = {"channels": [{"alternatives": [{"transcript": "hi"}]}]}
    result = TranscriptionResult.model_validate(
        {"job_id": JOB_ID, "status": "completed", "transcription": transcription}
    )
    assert result.transcription == transcription
