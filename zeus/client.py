# Copyright 2024 Zeus SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Optional

from .options import ZeusClientOptions, ClientOptionsFromEnv
from .errors import ZeusError, ZeusApiKeyError
from .clients.transcribe import RealtimeClient


class TranscribeRouter:
    """Router for transcription services"""
    
    def __init__(self, config: ZeusClientOptions):
        self._config = config
        self._realtime_client: Optional[RealtimeClient] = None

    def realtime(self) -> RealtimeClient:
        """
        Get a real-time transcription client.
        
        Returns:
            RealtimeClient instance for WebSocket-based live transcription
        """
        if self._realtime_client is None:
            self._realtime_client = RealtimeClient(self._config)
        return self._realtime_client


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


class ZeusClient:
    """
    Main Zeus SDK client for speech recognition services.
    
    This is the primary entry point for the Zeus SDK. It provides access to
    real-time speech recognition via WebSocket.
    
    Example:
        >>> from zeus import ZeusClient, RealtimeOptions, TranscriptionEvents
        >>> 
        >>> client = ZeusClient(api_key="your_api_key")
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
        config: Optional[ZeusClientOptions] = None,
    ):
        """
        Initialize the Zeus client.
        
        Args:
            api_key: Your Zeus API key. If not provided, will attempt to read
                    from ZEUS_API_KEY environment variable.
            config: Optional ZeusClientOptions for advanced configuration.
                   If provided, api_key parameter is ignored.
        """
        if config is None:
            if api_key:
                config = ZeusClientOptions(api_key=api_key)
            else:
                # Try to load from environment
                config = ClientOptionsFromEnv()
        
        self._config = config
        self._transcribe: Optional[TranscribeRouter] = None
        self._listen: Optional[_LegacyListenRouter] = None

    @property
    def transcribe(self) -> TranscribeRouter:
        """
        Access transcription services.
        
        Returns:
            TranscribeRouter for accessing real-time and batch transcription
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
Zeus = ZeusClient
