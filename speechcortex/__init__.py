# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
SpeechCortex Python SDK

Official Python SDK for SpeechCortex ASR (Automatic Speech Recognition) platform.
"""

__version__ = "0.1.dev2"

# Core client
from .client import SpeechCortexClient, SpeechCortex, TranscribeRouter
from .options import SpeechCortexClientOptions

# Errors
from .errors import (
    WebSocketStatusCode,
    SpeechCortexError,
    SpeechCortexTypeError,
    SpeechCortexModuleError,
    SpeechCortexApiError,
    SpeechCortexUnknownApiError,
    SpeechCortexApiKeyError,
    SpeechCortexConnectionError,
    SpeechCortexTimeoutError,
    SpeechCortexWebSocketError,
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
    # Batch transcription
    BatchClient,
    BatchOptions,
    TranscriptionConfig,
    JobDetails,
    TranscriptionResult,
    TranscriptionStatus,
    BatchError,
    JobNotFoundError,
    JobFailedError,
    TranscriptionNotReadyError,
    BatchTimeoutError,
)

# Audio utilities
from .audio import Microphone, SpeechCortexMicrophoneError

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
    "SpeechCortexClient",
    "SpeechCortex",
    "TranscribeRouter",
    # Options
    "SpeechCortexClientOptions",
    # Errors
    "WebSocketStatusCode",
    "SpeechCortexError",
    "SpeechCortexTypeError",
    "SpeechCortexModuleError",
    "SpeechCortexApiError",
    "SpeechCortexUnknownApiError",
    "SpeechCortexApiKeyError",
    "SpeechCortexConnectionError",
    "SpeechCortexTimeoutError",
    "SpeechCortexWebSocketError",
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
    # Batch transcription
    "BatchClient",
    "BatchOptions",
    "TranscriptionConfig",
    "JobDetails",
    "TranscriptionResult",
    "TranscriptionStatus",
    "BatchError",
    "JobNotFoundError",
    "JobFailedError",
    "TranscriptionNotReadyError",
    "BatchTimeoutError",
    # Audio
    "Microphone",
    "SpeechCortexMicrophoneError",
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
