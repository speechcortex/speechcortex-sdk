# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Shared fixtures: an in-process websockets server used to test the realtime
client against a real handshake, headers, framing and all — no network, no
mocking library.
"""

import asyncio
import threading
from collections.abc import Callable
from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve


class RecordingServer:
    """In-process websockets server that records requests and can send messages."""

    def __init__(
        self,
        *,
        handler: Callable[[ServerConnection], Any] | None = None,
        reject_status: int | None = None,
    ):
        self.requests: list[tuple[str, dict[str, str]]] = []
        self.received: list[Any] = []
        self._handler = handler
        self._reject_status = reject_status
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self.port: int | None = None
        future = asyncio.run_coroutine_threadsafe(self._start(), self._loop)
        future.result(timeout=10.0)

    async def _start(self) -> None:
        # Construct the server on the loop thread, as websockets requires.
        self._server = await serve(
            self._on_connection,
            host="127.0.0.1",
            port=0,
            process_request=self._process_request,
        )
        self.port = self._server.sockets[0].getsockname()[1]

    async def _process_request(self, connection: ServerConnection, request: Any):
        self.requests.append(
            (request.path, {k.lower(): v for k, v in request.headers.items()})
        )
        if self._reject_status is not None:
            return connection.respond(self._reject_status, "rejected")
        return None

    async def _on_connection(self, connection: ServerConnection) -> None:
        if self._handler is not None:
            result = self._handler(connection)
            if asyncio.iscoroutine(result):
                await result

    @property
    def url(self) -> str:
        return f"ws://127.0.0.1:{self.port}"

    def close(self) -> None:
        if self._server is not None:
            async def _close():
                self._server.close()
                await self._server.wait_closed()

            asyncio.run_coroutine_threadsafe(_close(), self._loop).result(timeout=10.0)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5.0)


@pytest.fixture
def ws_server():
    """Factory fixture that starts recording websockets servers."""
    servers: list[RecordingServer] = []

    def start(**kwargs) -> RecordingServer:
        server = RecordingServer(**kwargs)
        servers.append(server)
        return server

    yield start
    for server in servers:
        server.close()
