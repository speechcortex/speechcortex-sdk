# Copyright 2024 Zeus SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Zeus Python SDK

Official Python SDK for Zeus ASR (Automatic Speech Recognition) platform.
"""

__version__ = "0.1.0"

# Core client
from .client import ZeusClient, Zeus, TranscribeRouter
from .options import ZeusClientOptions, ClientOptionsFromEnv

# Errors
from .errors import (
    WebSocketStatusCode,
    ZeusError,
    ZeusTypeError,
    ZeusModuleError,
    ZeusApiError,
    ZeusUnknownApiError,
    ZeusApiKeyError,
    ZeusConnectionError,
    ZeusTimeoutError,
    ZeusWebSocketError,
)

# Transcribe client and options
from .clients.transcribe import (
    RealtimeClient,
    RealtimeOptions,
    LiveOptions,
    LiveTranscriptionEvents,
    LiveTranscriptionEvents as TranscriptionEvents,
    OpenResponse,
    CloseResponse,
    ErrorResponse,
    UnhandledResponse,
    LiveResultResponse,
    MetadataResponse,
    SpeechStartedResponse,
    UtteranceEndResponse,
    Alternative,
    Channel,
    Word,
)

# Audio utilities
from .audio import Microphone, ZeusMicrophoneError

# Logging
from .utils import (
    VerboseLogger,
    NOTICE,
    SPAM,
    SUCCESS,
    VERBOSE,
    WARNING,
    ERROR,
    FATAL,
    CRITICAL,
    INFO,
    DEBUG,
    NOTSET,
)

__all__ = [
    # Version
    "__version__",
    # Client
    "ZeusClient",
    "Zeus",
    "TranscribeRouter",
    # Options
    "ZeusClientOptions",
    "ClientOptionsFromEnv",
    # Errors
    "WebSocketStatusCode",
    "ZeusError",
    "ZeusTypeError",
    "ZeusModuleError",
    "ZeusApiError",
    "ZeusUnknownApiError",
    "ZeusApiKeyError",
    "ZeusConnectionError",
    "ZeusTimeoutError",
    "ZeusWebSocketError",
    # Transcribe
    "RealtimeClient",
    "RealtimeOptions",
    "LiveOptions",
    "LiveTranscriptionEvents",
    "TranscriptionEvents",
    # Responses
    "OpenResponse",
    "CloseResponse",
    "ErrorResponse",
    "UnhandledResponse",
    "LiveResultResponse",
    "MetadataResponse",
    "SpeechStartedResponse",
    "UtteranceEndResponse",
    "Alternative",
    "Channel",
    "Word",
    # Audio
    "Microphone",
    "ZeusMicrophoneError",
    # Logging
    "VerboseLogger",
    "NOTICE",
    "SPAM",
    "SUCCESS",
    "VERBOSE",
    "WARNING",
    "ERROR",
    "FATAL",
    "CRITICAL",
    "INFO",
    "DEBUG",
    "NOTSET",
]
