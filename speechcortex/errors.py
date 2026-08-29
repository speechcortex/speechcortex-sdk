# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
SpeechCortex SDK error types.

``ApiError`` covers transport-level failures (HTTP status codes, websocket
handshake failures). Domain errors (job lifecycle, polling) subclass
``SpeechCortexError`` directly.
"""

from enum import IntEnum

from .core.api_error import ApiError

__all__ = [
    "ApiError",
    "SpeechCortexError",
    "SpeechCortexApiKeyError",
    "SpeechCortexConnectionError",
    "SpeechCortexTimeoutError",
    "BatchError",
    "JobNotFoundError",
    "JobFailedError",
    "TranscriptionNotReadyError",
    "BatchTimeoutError",
    "WebSocketStatusCode",
]


class WebSocketStatusCode(IntEnum):
    """
    WebSocket status codes as defined in RFC 6455 and extensions.
    """

    # ===== Standard Close Codes (1000-1015) =====
    NORMAL_CLOSURE = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    RESERVED = 1004
    NO_STATUS_RECEIVED = 1005
    ABNORMAL_CLOSURE = 1006
    INVALID_FRAME_PAYLOAD = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MISSING_EXTENSION = 1010
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
    TRY_AGAIN_LATER = 1013
    BAD_GATEWAY = 1014
    TLS_HANDSHAKE = 1015

    # ===== Application-Specific Codes (4000-4999) =====
    UNAUTHORIZED = 4001
    FORBIDDEN = 4003
    NOT_FOUND = 4004
    BAD_REQUEST = 4008
    RATE_LIMITED = 4029
    INTERNAL_APP_ERROR = 4500
    SERVICE_UNAVAILABLE = 4503

    @classmethod
    def get_description(cls, code: int) -> str:
        """Get human-readable description for a status code."""
        descriptions = {
            1000: "Normal closure",
            1001: "Going away",
            1002: "Protocol error",
            1003: "Unsupported data",
            1004: "Reserved",
            1005: "No status received",
            1006: "Abnormal closure",
            1007: "Invalid frame payload data",
            1008: "Policy violation",
            1009: "Message too big",
            1010: "Missing extension",
            1011: "Internal error",
            1012: "Service restart",
            1013: "Try again later",
            1014: "Bad gateway",
            1015: "TLS handshake failure",
            4001: "Unauthorized - Authentication failed",
            4003: "Forbidden - Not authorized",
            4004: "Not found - Resource does not exist",
            4008: "Bad request - Invalid parameters",
            4029: "Rate limited - Too many requests",
            4500: "Internal application error",
            4503: "Service unavailable",
        }
        return descriptions.get(code, f"Unknown status code: {code}")

    @classmethod
    def is_client_error(cls, code: int) -> bool:
        """Check if code indicates a client error (4xxx)."""
        return 4000 <= code < 5000

    @classmethod
    def is_server_error(cls, code: int) -> bool:
        """Check if code indicates a server error (1011-1015, 4500+)."""
        return code in (1011, 1012, 1013, 1014, 1015) or code >= 4500

    @classmethod
    def is_normal_closure(cls, code: int) -> bool:
        """Check if code indicates normal closure."""
        return code == 1000


class SpeechCortexError(Exception):
    """Base exception for all SpeechCortex SDK errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class SpeechCortexApiKeyError(SpeechCortexError):
    """Raised when there are issues with the API key."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message)


class SpeechCortexConnectionError(SpeechCortexError):
    """Raised when connection to the SpeechCortex API fails."""

    def __init__(self, message: str):
        super().__init__(message)


class SpeechCortexTimeoutError(SpeechCortexError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)


class BatchError(SpeechCortexError):
    """Base exception for all batch transcription errors."""


class JobNotFoundError(BatchError):
    """Raised when a transcription job is not found."""

    def __init__(self, job_id: str, message: str | None = None):
        msg = message or f"Job not found: {job_id}"
        super().__init__(msg)
        self.job_id = job_id


class JobFailedError(BatchError):
    """Raised when a transcription job fails."""

    def __init__(self, job_id: str, error_message: str | None = None):
        msg = error_message or f"Job {job_id} failed"
        super().__init__(msg)
        self.job_id = job_id
        self.error_message = error_message


class TranscriptionNotReadyError(BatchError):
    """Raised when the transcription result is requested before the job completes."""

    def __init__(self, job_id: str, status: str):
        msg = f"Transcription not ready for job {job_id}. Current status: {status}"
        super().__init__(msg)
        self.job_id = job_id
        self.status = status


class BatchTimeoutError(SpeechCortexTimeoutError):
    """Raised when waiting for job completion times out."""

    def __init__(self, job_id: str, timeout: float):
        msg = f"Job {job_id} did not complete within {timeout} seconds"
        super().__init__(msg)
        self.job_id = job_id
        self.timeout = timeout
