# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Response models for batch transcription.

All models tolerate unknown fields (``extra="allow"``), so new fields added
by the server are preserved rather than rejected.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import field_validator

from ...core.unchecked_base_model import UncheckedBaseModel


class _JobBase(UncheckedBaseModel):
    job_id: UUID
    status: str = "pending"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    error_message: str | None = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _parse_timestamp(cls, value: Any) -> Any:
        # Server sends ISO-8601 timestamps with a "Z" suffix.
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class JobDetails(_JobBase):
    """Details of a submitted transcription job."""


class TranscriptionStatus(_JobBase):
    """Current status of a transcription job."""


class TranscriptionResult(_JobBase):
    """Transcription result for a completed job."""

    transcription: dict[str, Any] | None = None
    message: str | None = None
