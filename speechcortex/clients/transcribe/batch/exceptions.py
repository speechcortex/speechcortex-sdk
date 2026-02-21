# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Batch transcription specific exceptions.
"""

from ....errors import SpeechCortexError, SpeechCortexApiError, SpeechCortexTimeoutError


class BatchError(SpeechCortexError):
    """
    Base exception for all batch transcription errors.
    """
    pass


class JobNotFoundError(BatchError):
    """
    Exception raised when a transcription job is not found.
    """
    def __init__(self, job_id: str, message: str = None):
        msg = message or f"Job not found: {job_id}"
        super().__init__(msg)
        self.job_id = job_id


class JobFailedError(BatchError):
    """
    Exception raised when a transcription job fails.
    """
    def __init__(self, job_id: str, error_message: str = None):
        msg = error_message or f"Job {job_id} failed"
        super().__init__(msg)
        self.job_id = job_id
        self.error_message = error_message


class TranscriptionNotReadyError(BatchError):
    """
    Exception raised when attempting to get transcription result before job is completed.
    """
    def __init__(self, job_id: str, status: str):
        msg = f"Transcription not ready for job {job_id}. Current status: {status}"
        super().__init__(msg)
        self.job_id = job_id
        self.status = status


class BatchTimeoutError(SpeechCortexTimeoutError):
    """
    Exception raised when waiting for job completion times out.
    """
    def __init__(self, job_id: str, timeout: float):
        msg = f"Job {job_id} did not complete within {timeout} seconds"
        super().__init__(msg)
        self.job_id = job_id
        self.timeout = timeout
