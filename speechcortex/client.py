# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
SpeechCortex SDK client entry points.

Usage::

    from speechcortex import SpeechCortexClient

    client = SpeechCortexClient(api_key="...", url="wss://api.speechcortex.ai")
    # streaming:  client.listen.v1.connect(...)
    # batch:      client.listen.batch.v1.submit_job(...)
"""

from .core.client_options import ClientOptions
from .errors import SpeechCortexError
from .listen.batch.client import AsyncBatchV1Client, BatchV1Client
from .listen.v1.client import AsyncRealtimeV1Client, RealtimeV1Client


class _ListenV1Router:
    """Realtime transcription. Access via ``client.listen.v1``."""

    def __init__(self, config: ClientOptions):
        self._config = config
        self._client: RealtimeV1Client | None = None

    @property
    def connect(self):
        return self.client.connect

    @property
    def client(self) -> RealtimeV1Client:
        if self._client is None:
            self._client = RealtimeV1Client(config=self._config)
        return self._client


class _AsyncListenV1Router:
    """Realtime transcription (async). Access via ``client.listen.v1``."""

    def __init__(self, config: ClientOptions):
        self._config = config
        self._client: AsyncRealtimeV1Client | None = None

    @property
    def connect(self):
        return self.client.connect

    @property
    def client(self) -> AsyncRealtimeV1Client:
        if self._client is None:
            self._client = AsyncRealtimeV1Client(config=self._config)
        return self._client


class _ListenBatchRouter:
    """Batch transcription jobs. Access via ``client.listen.batch.v1``."""

    def __init__(self, config: ClientOptions):
        self._config = config
        self._v1: BatchV1Client | None = None

    @property
    def v1(self) -> BatchV1Client:
        if self._v1 is None:
            self._v1 = BatchV1Client(config=self._config)
        return self._v1


class _AsyncListenBatchRouter:
    def __init__(self, config: ClientOptions):
        self._config = config
        self._v1: AsyncBatchV1Client | None = None

    @property
    def v1(self) -> AsyncBatchV1Client:
        if self._v1 is None:
            self._v1 = AsyncBatchV1Client(config=self._config)
        return self._v1


class _ListenRouter:
    """Namespace for speech-to-text. Access via ``client.listen``."""

    def __init__(self, config: ClientOptions):
        self._v1: _ListenV1Router | None = None
        self._batch: _ListenBatchRouter | None = None
        self._config = config

    @property
    def v1(self) -> _ListenV1Router:
        if self._v1 is None:
            self._v1 = _ListenV1Router(self._config)
        return self._v1

    @property
    def batch(self) -> _ListenBatchRouter:
        if self._batch is None:
            self._batch = _ListenBatchRouter(self._config)
        return self._batch


class _AsyncListenRouter:
    def __init__(self, config: ClientOptions):
        self._v1: _AsyncListenV1Router | None = None
        self._batch: _AsyncListenBatchRouter | None = None
        self._config = config

    @property
    def v1(self) -> _AsyncListenV1Router:
        if self._v1 is None:
            self._v1 = _AsyncListenV1Router(self._config)
        return self._v1

    @property
    def batch(self) -> _AsyncListenBatchRouter:
        if self._batch is None:
            self._batch = _AsyncListenBatchRouter(self._config)
        return self._batch


class SpeechCortexClient:
    """
    SpeechCortex API client.

    Args:
        api_key: SpeechCortex API key. Defaults to the ``SPEECHCORTEX_API_KEY``
            environment variable.
        url: Base URL of the SpeechCortex API (e.g. ``wss://api.speechcortex.ai``).
            Required — defaults to the ``SPEECHCORTEX_HOST`` environment variable.
        config: Fully-specified :class:`ClientOptions`, as an alternative to
            the individual keyword arguments.
    """

    def __init__(
        self,
        api_key: str = "",
        url: str = "",
        config: ClientOptions | None = None,
    ) -> None:
        if config is None:
            config = ClientOptions(api_key=api_key, url=url)
        elif api_key or url:
            raise SpeechCortexError(
                "Pass either config or individual options (api_key, url), not both."
            )
        self._config = config
        self._listen: _ListenRouter | None = None

    @property
    def listen(self) -> _ListenRouter:
        if self._listen is None:
            self._listen = _ListenRouter(self._config)
        return self._listen


class AsyncSpeechCortexClient:
    """Async counterpart of :class:`SpeechCortexClient`."""

    def __init__(
        self,
        api_key: str = "",
        url: str = "",
        config: ClientOptions | None = None,
    ) -> None:
        if config is None:
            config = ClientOptions(api_key=api_key, url=url)
        elif api_key or url:
            raise SpeechCortexError(
                "Pass either config or individual options (api_key, url), not both."
            )
        self._config = config
        self._listen: _AsyncListenRouter | None = None

    @property
    def listen(self) -> _AsyncListenRouter:
        if self._listen is None:
            self._listen = _AsyncListenRouter(self._config)
        return self._listen
