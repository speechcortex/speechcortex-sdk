# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import asyncio
import inspect
import logging
import threading
from collections.abc import Callable

from .constants import CHANNELS, CHUNK, LOGGING, RATE

_logger = logging.getLogger("speechcortex")

__all__ = ["Microphone"]


class Microphone:  # pylint: disable=too-many-instance-attributes
    """
    Microphone for local audio input, backed by PyAudio.

    The push callback receives raw audio chunks as they are captured; pass
    ``connection.send_media`` (or a wrapper) to stream into a realtime
    transcription connection.
    """

    def __init__(
        self,
        push_callback: Callable | None = None,
        verbose: int = LOGGING,
        rate: int = RATE,
        chunk: int = CHUNK,
        channels: int = CHANNELS,
        input_device_index: int | None = None,
    ):
        # dynamic import of pyaudio as not to force the requirements on the SDK
        import pyaudio  # pylint: disable=import-outside-toplevel

        _logger.setLevel(verbose)

        self._audio: pyaudio.PyAudio | None = pyaudio.PyAudio()
        self._stream: pyaudio.Stream | None = None
        self._chunk = chunk
        self._rate = rate
        self._format = pyaudio.paInt16
        self._channels = channels
        self._is_muted = False
        self._input_device_index = input_device_index

        self._asyncio_loop: asyncio.AbstractEventLoop | None = None
        self._asyncio_thread: threading.Thread | None = None
        self._exit = threading.Event()

        self._push_callback_org: Callable | None = push_callback
        self._push_callback: Callable | None = None

    def is_active(self) -> bool:
        """Return True if the stream is active."""
        return self._stream is not None and self._stream.is_active()

    def set_callback(self, push_callback: Callable) -> None:
        """
        Set the callback invoked with each captured audio chunk.

        This should be the websocket send function (e.g.
        ``connection.send_media``).
        """
        self._push_callback_org = push_callback

    def start(self) -> bool:
        """Start the microphone stream. Returns True on success."""
        if self._push_callback_org is None:
            _logger.error("start failed. No callback set.")
            return False

        if inspect.iscoroutinefunction(self._push_callback_org):
            # Run an asyncio loop in our own thread for async callbacks.
            self._asyncio_loop = asyncio.new_event_loop()
            self._asyncio_thread = threading.Thread(
                target=self._asyncio_loop.run_forever, daemon=True
            )
            self._asyncio_thread.start()

            self._push_callback = lambda data: asyncio.run_coroutine_threadsafe(  # noqa: E731
                self._push_callback_org(data), self._asyncio_loop
            ).result()
        else:
            self._push_callback = self._push_callback_org

        if self._audio is not None:
            self._stream = self._audio.open(
                format=self._format,
                channels=self._channels,
                rate=self._rate,
                input=True,
                output=False,
                frames_per_buffer=self._chunk,
                input_device_index=self._input_device_index,
                stream_callback=self._callback,
            )

        if self._stream is None:
            _logger.error("start failed. No stream created.")
            return False

        self._exit.clear()
        self._stream.start_stream()
        return True

    def mute(self) -> bool:
        """Mute the microphone stream (sends silence). Returns True on success."""
        if self._stream is None:
            _logger.error("mute failed. Library not initialized.")
            return False
        self._is_muted = True
        return True

    def unmute(self) -> bool:
        """Unmute the microphone stream. Returns True on success."""
        if self._stream is None:
            _logger.error("unmute failed. Library not initialized.")
            return False
        self._is_muted = False
        return True

    def is_muted(self) -> bool:
        """Return True if the stream is muted."""
        return self._is_muted

    def finish(self) -> bool:
        """Stop the microphone stream and clean up. Returns True on success."""
        self._exit.set()

        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
        self._stream = None

        if self._asyncio_thread is not None and self._asyncio_loop is not None:
            self._asyncio_loop.call_soon_threadsafe(self._asyncio_loop.stop)
            self._asyncio_thread.join()
        self._asyncio_thread = None
        self._asyncio_loop = None

        return True

    def _callback(
        self, input_data, frame_count, time_info, status_flags
    ):  # pylint: disable=unused-argument
        """PyAudio stream callback: push captured audio to the push callback."""
        # dynamic import of pyaudio as not to force the requirements on the SDK
        import pyaudio  # pylint: disable=import-outside-toplevel

        if self._exit.is_set():
            return None, pyaudio.paAbort

        if input_data is None:
            _logger.warning("input_data is None")
            return None, pyaudio.paContinue

        try:
            if self._is_muted:
                input_data = b"\x00" * len(input_data)
            if self._push_callback is not None:
                self._push_callback(input_data)
        except Exception as e:
            _logger.error("Error while sending: %s", str(e))
            raise

        return input_data, pyaudio.paContinue
