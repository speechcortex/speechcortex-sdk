# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Optional

from .options import SpeechCortexClientOptions
from .errors import SpeechCortexError, SpeechCortexApiKeyError
from .clients.transcribe import RealtimeClient, BatchClient


class TranscribeRouter:
    """Router for transcription services"""
    
    def __init__(self, config: SpeechCortexClientOptions):
        self._config = config
        self._realtime_client: Optional[RealtimeClient] = None
        self._batch_client: Optional[BatchClient] = None

    def realtime(self) -> RealtimeClient:
        """
        Get a real-time transcription client.
        
        Returns:
            RealtimeClient instance for WebSocket-based live transcription
        """
        if self._realtime_client is None:
            self._realtime_client = RealtimeClient(self._config)
        return self._realtime_client
    
    def batch(self) -> BatchClient:
        """
        Get a batch/post-call transcription client.
        
        Returns:
            BatchClient instance for batch transcription
        """
        if self._batch_client is None:
            self._batch_client = BatchClient(self._config)
        return self._batch_client


class _LegacyWebsocket:
    """Backwards-compatible websocket router (listen.websocket.v("1"))"""

    def __init__(self, realtime_factory):
        self._realtime_factory = realtime_factory

    def v(self, version: str = "1") -> RealtimeClient:  # pylint: disable=unused-argument
        return self._realtime_factory()


class _LegacyListenRouter:
    """Backwards-compatible listen router mapping to transcribe.realtime"""

    def __init__(self, transcribe_router: TranscribeRouter):
        self.websocket = _LegacyWebsocket(transcribe_router.realtime)


class SpeechCortexClient:
    """
    Main SpeechCortex SDK client for speech recognition services.
    
    This is the primary entry point for the SpeechCortex SDK. It provides access to
    real-time speech recognition via WebSocket.
    
    Example:
        >>> from speechcortex import SpeechCortexClient, RealtimeOptions, TranscriptionEvents
        >>> 
        >>> client = SpeechCortexClient(api_key="your_api_key")
        >>> connection = client.transcribe.realtime()
        >>> 
        >>> def on_message(self, result, **kwargs):
        ...     print(result.channel.alternatives[0].transcript)
        >>> 
        >>> connection.on(TranscriptionEvents.Transcript, on_message)
        >>> connection.start(RealtimeOptions(model="zeus-v1"))
        >>> connection.send(audio_bytes)
        >>> connection.finish()
    """

    def __init__(
        self,
        api_key: str = "",
        config: Optional[SpeechCortexClientOptions] = None,
    ):
        """
        Initialize the SpeechCortex client.
        
        Args:
            api_key: Your SpeechCortex API key. If not provided, will attempt to read
                    from SPEECHCORTEX_API_KEY environment variable.
            config: Optional SpeechCortexClientOptions for advanced configuration.
                   If provided, api_key parameter is ignored.
        """
        if config is None:
            # SpeechCortexClientOptions now automatically reads from environment
            config = SpeechCortexClientOptions(api_key=api_key)
        
        self._config = config
        self._transcribe: Optional[TranscribeRouter] = None
        self._listen: Optional[_LegacyListenRouter] = None

    @property
    def transcribe(self) -> TranscribeRouter:
        """
        Access transcription services.
        
        Returns:
            TranscribeRouter for accessing real-time and batch transcription.
            
        Example:
            >>> # Real-time transcription
            >>> client.transcribe.realtime()
            >>> 
            >>> # Batch/post-call transcription
            >>> client.transcribe.batch()
        """
        if self._transcribe is None:
            self._transcribe = TranscribeRouter(self._config)
        return self._transcribe

    @property
    def listen(self) -> _LegacyListenRouter:
        """Backwards-compatible accessor for listen.websocket.v("1") API"""
        if self._listen is None:
            self._listen = _LegacyListenRouter(self.transcribe)
        return self._listen


# Alias for backwards compatibility
SpeechCortex = SpeechCortexClient
