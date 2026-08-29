# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
SpeechCortex Python SDK

Official Python SDK for SpeechCortex ASR (Automatic Speech Recognition) platform.

Usage::

    from speechcortex import SpeechCortexClient, EventType

    client = SpeechCortexClient(api_key="...", url="wss://api.speechcortex.ai")

    with client.listen.v1.connect(model="cove") as connection:
        connection.on(EventType.MESSAGE, on_message)
        threading.Thread(target=connection.start_listening, daemon=True).start()
        connection.send_media(audio_chunk)
"""

# Helpers
# Client
from .client import (
    AsyncSpeechCortexClient,
    SpeechCortexClient,
)
from .core.api_error import ApiError
from .core.client_options import ClientOptions
from .core.events import EventType
from .core.request_options import RequestOptions

# Errors
from .errors import (
    BatchError,
    BatchTimeoutError,
    JobFailedError,
    JobNotFoundError,
    SpeechCortexApiKeyError,
    SpeechCortexConnectionError,
    SpeechCortexError,
    SpeechCortexTimeoutError,
    TranscriptionNotReadyError,
    WebSocketStatusCode,
)
from .helpers import Microphone

# Listen (batch transcription)
from .listen.batch import (
    AsyncBatchV1Client,
    BatchV1Client,
    JobDetails,
    TranscriptionResult,
    TranscriptionStatus,
)

# Listen (realtime transcription)
from .listen.v1 import (
    AsyncRealtimeV1Client,
    AsyncRealtimeV1SocketClient,
    ErrorResponse,
    KeepAlive,
    Metadata,
    RealtimeV1Client,
    RealtimeV1SocketClient,
    Results,
    SpeechStarted,
    TurnInfo,
    UtteranceEnd,
)
from .version import __version__

__all__ = [
    "__version__",
    # Client
    "AsyncSpeechCortexClient",
    "SpeechCortexClient",
    "ClientOptions",
    "RequestOptions",
    # Core
    "ApiError",
    "EventType",
    # Errors
    "BatchError",
    "BatchTimeoutError",
    "JobFailedError",
    "JobNotFoundError",
    "SpeechCortexApiKeyError",
    "SpeechCortexConnectionError",
    "SpeechCortexError",
    "SpeechCortexTimeoutError",
    "TranscriptionNotReadyError",
    "WebSocketStatusCode",
    # Realtime
    "AsyncRealtimeV1Client",
    "AsyncRealtimeV1SocketClient",
    "RealtimeV1Client",
    "RealtimeV1SocketClient",
    "ErrorResponse",
    "KeepAlive",
    "Metadata",
    "Results",
    "SpeechStarted",
    "TurnInfo",
    "UtteranceEnd",
    # Batch
    "AsyncBatchV1Client",
    "BatchV1Client",
    "JobDetails",
    "TranscriptionResult",
    "TranscriptionStatus",
    # Helpers
    "Microphone",
]
