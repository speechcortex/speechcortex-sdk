# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import json
import logging
import typing

from ...core.events import EventEmitterMixin, EventType
from ...core.unchecked_base_model import construct_type
from .types import CloseStream, Finalize, KeepAlive, RealtimeSocketResponse

_logger = logging.getLogger("speechcortex")


def _parse(raw_message: str) -> typing.Any:
    """
    Parse a text frame into a typed response model.

    Payloads the current SDK does not fully understand are returned as the
    raw dict instead of raising, so new server fields never break parsing.
    """
    return construct_type(type_=RealtimeSocketResponse, object_=json.loads(raw_message))


class AsyncRealtimeV1SocketClient(EventEmitterMixin):
    """Async realtime websocket client. Obtained from ``connect()``."""

    def __init__(self, *, websocket: typing.Any):
        super().__init__()
        self._websocket = websocket

    async def __aiter__(self) -> typing.AsyncIterator[typing.Any]:
        async for message in self._websocket:
            if isinstance(message, bytes):
                yield message
                continue
            try:
                yield _parse(message)
            except Exception:
                _logger.warning(
                    "Skipping unknown WebSocket message; update your SDK version "
                    "to support new message types."
                )
                continue

    async def start_listening(self) -> None:
        """
        Start listening for messages on the websocket connection.

        Emits events in the following order:
        - EventType.OPEN when the connection is established
        - EventType.MESSAGE for each message received
        - EventType.ERROR if an error occurs
        - EventType.CLOSE when the connection is closed

        Blocks until the connection closes; run it as a task.
        """
        await self._emit_async(EventType.OPEN, None)
        try:
            async for raw_message in self._websocket:
                if isinstance(raw_message, bytes):
                    parsed = raw_message
                else:
                    try:
                        parsed = _parse(raw_message)
                    except Exception:
                        _logger.warning(
                            "Skipping unknown WebSocket message; update your SDK version "
                            "to support new message types."
                        )
                        continue
                await self._emit_async(EventType.MESSAGE, parsed)
        except Exception as exc:
            await self._emit_async(EventType.ERROR, exc)
        finally:
            await self._emit_async(EventType.CLOSE, None)

    async def send_media(self, message: bytes) -> None:
        """Send raw audio bytes to the websocket connection."""
        await self._send(message)

    async def send_keep_alive(self, message: KeepAlive | None = None) -> None:
        """Send a KeepAlive control message."""
        await self._send_model(message or KeepAlive())

    async def send_finalize(self, message: Finalize | None = None) -> None:
        """Send a Finalize control message to flush buffered audio."""
        await self._send_model(message or Finalize())

    async def send_close_stream(self, message: CloseStream | None = None) -> None:
        """Send a CloseStream control message to end the session."""
        await self._send_model(message or CloseStream())

    async def recv(self) -> typing.Any:
        """Receive a single message from the websocket connection."""
        data = await self._websocket.recv()
        if isinstance(data, bytes):
            return data
        return _parse(data)

    async def _send(self, data: typing.Any) -> None:
        if isinstance(data, dict):
            data = json.dumps(data)
        await self._websocket.send(data)

    async def _send_model(self, model: typing.Any) -> None:
        await self._send(model.model_dump(exclude_none=True))


class RealtimeV1SocketClient(EventEmitterMixin):
    """Sync realtime websocket client. Obtained from ``connect()``."""

    def __init__(self, *, websocket: typing.Any):
        super().__init__()
        self._websocket = websocket

    def __iter__(self) -> typing.Iterator[typing.Any]:
        for message in self._websocket:
            if isinstance(message, bytes):
                yield message
                continue
            try:
                yield _parse(message)
            except Exception:
                _logger.warning(
                    "Skipping unknown WebSocket message; update your SDK version "
                    "to support new message types."
                )
                continue

    def start_listening(self) -> None:
        """
        Start listening for messages on the websocket connection.

        Emits events in the following order:
        - EventType.OPEN when the connection is established
        - EventType.MESSAGE for each message received
        - EventType.ERROR if an error occurs
        - EventType.CLOSE when the connection is closed

        Blocks until the connection closes; run it in a thread.
        """
        self._emit(EventType.OPEN, None)
        try:
            for raw_message in self._websocket:
                if isinstance(raw_message, bytes):
                    parsed = raw_message
                else:
                    try:
                        parsed = _parse(raw_message)
                    except Exception:
                        _logger.warning(
                            "Skipping unknown WebSocket message; update your SDK version "
                            "to support new message types."
                        )
                        continue
                self._emit(EventType.MESSAGE, parsed)
        except Exception as exc:
            self._emit(EventType.ERROR, exc)
        finally:
            self._emit(EventType.CLOSE, None)

    def send_media(self, message: bytes) -> None:
        """Send raw audio bytes to the websocket connection."""
        self._send(message)

    def send_keep_alive(self, message: KeepAlive | None = None) -> None:
        """Send a KeepAlive control message."""
        self._send_model(message or KeepAlive())

    def send_finalize(self, message: Finalize | None = None) -> None:
        """Send a Finalize control message to flush buffered audio."""
        self._send_model(message or Finalize())

    def send_close_stream(self, message: CloseStream | None = None) -> None:
        """Send a CloseStream control message to end the session."""
        self._send_model(message or CloseStream())

    def recv(self) -> typing.Any:
        """Receive a single message from the websocket connection."""
        data = self._websocket.recv()
        if isinstance(data, bytes):
            return data
        return _parse(data)

    def _send(self, data: typing.Any) -> None:
        if isinstance(data, dict):
            data = json.dumps(data)
        self._websocket.send(data)

    def _send_model(self, model: typing.Any) -> None:
        self._send(model.model_dump(exclude_none=True))
