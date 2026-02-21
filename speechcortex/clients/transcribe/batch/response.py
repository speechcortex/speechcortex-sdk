# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Response models for batch transcription.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class JobDetails:
    """
    Details about a transcription job.
    
    Attributes:
        job_id: Unique job identifier
        status: Current job status (pending, downloading, uploading, queued, processing, completed, failed)
        created_at: Job creation timestamp
        updated_at: Last update timestamp (optional)
        error_message: Error message if job failed (optional)
    """
    job_id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobDetails":
        """Create JobDetails from API response dictionary."""
        # Handle both UUID string and UUID object
        job_id = data.get("job_id")
        if isinstance(job_id, str):
            job_id = UUID(job_id)
        elif not isinstance(job_id, UUID):
            raise ValueError(f"Invalid job_id format: {job_id}")
        
        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            # Handle ISO format with or without timezone
            created_at = created_at.replace("Z", "+00:00")
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()
        
        updated_at = data.get("updated_at")
        if updated_at:
            if isinstance(updated_at, str):
                updated_at = updated_at.replace("Z", "+00:00")
                updated_at = datetime.fromisoformat(updated_at)
            elif not isinstance(updated_at, datetime):
                updated_at = None
        
        return cls(
            job_id=job_id,
            status=data.get("status", "pending"),
            created_at=created_at,
            updated_at=updated_at,
            error_message=data.get("error_message"),
        )


@dataclass
class TranscriptionStatus:
    """
    Status information for a transcription job.
    
    Attributes:
        job_id: Unique job identifier
        status: Current job status
        created_at: Job creation timestamp
        updated_at: Last update timestamp (optional)
        error_message: Error message if job failed (optional)
    """
    job_id: UUID
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptionStatus":
        """Create TranscriptionStatus from API response dictionary."""
        job_id = data.get("job_id")
        if isinstance(job_id, str):
            job_id = UUID(job_id)
        elif not isinstance(job_id, UUID):
            raise ValueError(f"Invalid job_id format: {job_id}")
        
        created_at = None
        if data.get("created_at"):
            created_at_str = data["created_at"]
            if isinstance(created_at_str, str):
                created_at_str = created_at_str.replace("Z", "+00:00")
                created_at = datetime.fromisoformat(created_at_str)
        
        updated_at = None
        if data.get("updated_at"):
            updated_at_str = data["updated_at"]
            if isinstance(updated_at_str, str):
                updated_at_str = updated_at_str.replace("Z", "+00:00")
                updated_at = datetime.fromisoformat(updated_at_str)
        
        return cls(
            job_id=job_id,
            status=data.get("status", "pending"),
            created_at=created_at,
            updated_at=updated_at,
            error_message=data.get("error_message"),
        )


@dataclass
class TranscriptionResult:
    """
    Transcription result for a completed job.
    
    Attributes:
        job_id: Unique job identifier
        status: Job status
        transcription: Transcription data (dict) - only present if completed
        message: Status message
    """
    job_id: UUID
    status: str
    transcription: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptionResult":
        """Create TranscriptionResult from API response dictionary."""
        job_id = data.get("job_id")
        if isinstance(job_id, str):
            job_id = UUID(job_id)
        elif not isinstance(job_id, UUID):
            raise ValueError(f"Invalid job_id format: {job_id}")
        
        return cls(
            job_id=job_id,
            status=data.get("status", "pending"),
            transcription=data.get("transcription"),
            message=data.get("message"),
        )
