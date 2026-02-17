# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
SpeechCortex SDK Errors Module

This module contains all custom exceptions used throughout the SpeechCortex SDK.
"""

from enum import IntEnum


class WebSocketStatusCode(IntEnum):
    """
    WebSocket status codes as defined in RFC 6455 and extensions.
    
    These codes indicate various WebSocket connection states and errors.
    """
    
    # ===== Standard Close Codes (1000-1015) =====
    # RFC 6455 Section 7.4.1
    NORMAL_CLOSURE = 1000          # Normal closure; the connection successfully completed
    GOING_AWAY = 1001              # Endpoint is going away (server shutdown or browser navigation)
    PROTOCOL_ERROR = 1002          # Terminating due to a protocol error
    UNSUPPORTED_DATA = 1003        # Received data type that cannot be accepted
    RESERVED = 1004                # Reserved for future use
    NO_STATUS_RECEIVED = 1005      # No status code was provided (cannot be sent in close frame)
    ABNORMAL_CLOSURE = 1006        # Connection closed abnormally without close frame
    INVALID_FRAME_PAYLOAD = 1007   # Received inconsistent data (e.g., non-UTF-8 in text message)
    POLICY_VIOLATION = 1008        # Message violates policy (generic status code)
    MESSAGE_TOO_BIG = 1009         # Message too large to process
    MISSING_EXTENSION = 1010       # Client expected server to negotiate extension(s)
    INTERNAL_ERROR = 1011          # Unexpected condition prevented server from fulfilling request
    SERVICE_RESTART = 1012         # Server is restarting
    TRY_AGAIN_LATER = 1013         # Temporary server condition (e.g., overloaded)
    BAD_GATEWAY = 1014             # Server acting as gateway received invalid response
    TLS_HANDSHAKE = 1015           # TLS handshake failed (cannot be sent in close frame)
    
    # ===== Application-Specific Codes (4000-4999) =====
    # Available for application use
    UNAUTHORIZED = 4001            # Authentication failed or token invalid
    FORBIDDEN = 4003               # Authenticated but not authorized for this resource
    NOT_FOUND = 4004               # Resource not found
    BAD_REQUEST = 4008             # Malformed request or invalid parameters
    RATE_LIMITED = 4029            # Too many requests, rate limit exceeded
    INTERNAL_APP_ERROR = 4500      # Internal application error
    SERVICE_UNAVAILABLE = 4503     # Service temporarily unavailable
    
    @classmethod
    def get_description(cls, code: int) -> str:
        """Get human-readable description for a status code."""
        descriptions = {
            # Standard WebSocket codes
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
            # Application codes
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
    """
    Base exception for all SpeechCortex SDK errors.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class SpeechCortexTypeError(SpeechCortexError):
    """
    Exception raised for type-related errors in the SpeechCortex SDK.
    """

    def __init__(self, message: str):
        super().__init__(message)


class SpeechCortexModuleError(SpeechCortexError):
    """
    Exception raised when a required module is not available.
    """

    def __init__(self, message: str):
        super().__init__(message)


class SpeechCortexApiError(SpeechCortexError):
    """
    Exception raised when the SpeechCortex API returns an error.
    """

    def __init__(self, message: str, status: int = None):
        super().__init__(message)
        self.status = status


class SpeechCortexUnknownApiError(SpeechCortexApiError):
    """
    Exception raised when an unknown API error occurs.
    """

    def __init__(self, message: str, status: int = None):
        super().__init__(message, status)


class SpeechCortexApiKeyError(SpeechCortexError):
    """
    Exception raised when there are issues with the API key.
    """

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message)


class SpeechCortexConnectionError(SpeechCortexError):
    """
    Exception raised when connection to SpeechCortex API fails.
    """

    def __init__(self, message: str):
        super().__init__(message)


class SpeechCortexTimeoutError(SpeechCortexError):
    """
    Exception raised when a request times out.
    """

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)


class SpeechCortexWebSocketError(SpeechCortexError):
    """
    Exception raised for WebSocket-specific errors.
    
    Attributes:
        message (str): The error message
        code (int): WebSocket status code (optional)
    """

    def __init__(self, message: str, code: int = None):
        super().__init__(message)
        self.code = code
        if code:
            description = WebSocketStatusCode.get_description(code)
            self.message = f"{message} (Code {code}: {description})"
        else:
            self.message = message
