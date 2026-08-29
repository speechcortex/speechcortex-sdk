# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import typing
from contextlib import asynccontextmanager, contextmanager
from urllib.parse import urlencode

from ...core.api_error import ApiError
from ...core.client_options import ClientOptions
from ...core.query_encoder import encode_query
from ...core.remove_none_from_dict import remove_none_from_dict
from ...core.request_options import RequestOptions, get_request_options_value
from ...transport import async_connect, status_code_from_handshake_error, sync_connect
from .options import (
    BgSpeechFilter,
    Channels,
    Encoding,
    Extra,
    InterimResults,
    Language,
    Model,
    Punctuate,
    SampleRate,
    SmartFormat,
    TurnDetection,
    TurnDetectionThreshold,
    TurnDetectionTimeoutMs,
    UtteranceEndMs,
    VadEvents,
)
from .socket_client import AsyncRealtimeV1SocketClient, RealtimeV1SocketClient

# Defaults preserved from previous SDK releases: these are always sent on the
# wire unless explicitly overridden.
_DEFAULT_TURN_DETECTION_THRESHOLD: float = 0.6
_DEFAULT_TURN_DETECTION_TIMEOUT_MS: int = 2000


def _build_request(
    config: ClientOptions,
    *,
    model: Model,
    language: Language,
    smart_format: SmartFormat | None,
    punctuate: Punctuate | None,
    interim_results: InterimResults | None,
    turn_detection: TurnDetection | None,
    turn_detection_threshold: TurnDetectionThreshold | None,
    turn_detection_timeout_ms: TurnDetectionTimeoutMs | None,
    bg_speech_filter: BgSpeechFilter | None,
    encoding: Encoding | None,
    sample_rate: SampleRate | None,
    channels: Channels | None,
    utterance_end_ms: UtteranceEndMs | None,
    vad_events: VadEvents | None,
    extra: Extra | None,
    request_options: RequestOptions | None,
) -> tuple[str, dict[str, str]]:
    params: dict[str, typing.Any] = {
        "model": model,
        "language": language,
        "smart_format": smart_format,
        "punctuate": punctuate,
        "interim_results": interim_results,
        "encoding": encoding,
        "sample_rate": sample_rate,
        "channels": channels,
        "utterance_end_ms": utterance_end_ms,
        "vad_events": vad_events,
    }
    if bg_speech_filter:
        params["bg_speech_filter"] = bg_speech_filter
    if turn_detection:
        params["turn_detection"] = turn_detection
        params["turn_detection_threshold"] = (
            turn_detection_threshold
            if turn_detection_threshold is not None
            else _DEFAULT_TURN_DETECTION_THRESHOLD
        )
        params["turn_detection_timeout_ms"] = (
            turn_detection_timeout_ms
            if turn_detection_timeout_ms is not None
            else _DEFAULT_TURN_DETECTION_TIMEOUT_MS
        )
    params.update(extra or {})
    params.update(
        get_request_options_value(request_options, "additional_query_parameters", {}) or {}
    )

    encoded = encode_query(remove_none_from_dict(params))
    ws_url = f"{config.url}{config.realtime_path}"
    if encoded:
        ws_url = ws_url + "?" + urlencode(encoded)

    headers = config.get_websocket_headers()
    additional_headers = get_request_options_value(request_options, "additional_headers", {})
    if additional_headers:
        headers.update(additional_headers)
    return ws_url, headers


def _handshake_error(status_code: int, headers: dict[str, str]) -> ApiError:
    if status_code == 401:
        return ApiError(
            status_code=status_code,
            headers=headers,
            body="Websocket initialized with invalid credentials.",
        )
    return ApiError(
        status_code=status_code,
        headers=headers,
        body="Unexpected error when initializing websocket connection.",
    )


class RealtimeV1Client:
    """Realtime transcription client for speech-to-text (``client.listen.v1``)."""

    def __init__(self, *, config: ClientOptions):
        self._config = config

    @contextmanager
    def connect(
        self,
        *,
        model: Model = "cove",
        language: Language = "en-US",
        smart_format: SmartFormat | None = None,
        punctuate: Punctuate | None = None,
        interim_results: InterimResults | None = True,
        turn_detection: TurnDetection | None = None,
        turn_detection_threshold: TurnDetectionThreshold | None = None,
        turn_detection_timeout_ms: TurnDetectionTimeoutMs | None = None,
        bg_speech_filter: BgSpeechFilter | None = None,
        encoding: Encoding | None = "linear16",
        sample_rate: SampleRate | None = 16000,
        channels: Channels | None = 1,
        utterance_end_ms: UtteranceEndMs | None = 1000,
        vad_events: VadEvents | None = None,
        extra: Extra | None = None,
        request_options: RequestOptions | None = None,
    ) -> typing.Iterator[RealtimeV1SocketClient]:
        """
        Open a realtime transcription websocket.

        Use as a context manager::

            with client.listen.v1.connect(model="cove") as connection:
                connection.on(EventType.MESSAGE, on_message)
                threading.Thread(target=connection.start_listening, daemon=True).start()
                connection.send_media(audio_chunk)

        The connection raises :class:`ApiError` on handshake failure (e.g.
        invalid credentials) instead of failing silently later.

        Args:
            model: Model to use (default ``cove``).
            language: Language code (default ``en-US``).
            smart_format: Enable smart formatting.
            punctuate: Enable punctuation.
            interim_results: Receive interim results (default True).
            turn_detection: Enable turn detection events. When enabled,
                ``turn_detection_threshold`` and ``turn_detection_timeout_ms``
                are also sent (0.6 / 2000 unless overridden).
            bg_speech_filter: Background-speech filter strength
                (``"minimal"``, ``"balanced"`` or ``"aggressive"``).
            encoding: Audio encoding (default ``linear16``).
            sample_rate: Audio sample rate in Hz (default 16000).
            channels: Number of audio channels (default 1).
            utterance_end_ms: Milliseconds of silence for utterance end
                detection (default 1000).
            vad_events: Enable voice activity detection events.
            extra: Additional query parameters forwarded as-is; use this to
                try new server-side parameters without an SDK update.
            request_options: Per-request overrides (additional headers/query
                parameters).
        """
        ws_url, headers = _build_request(
            self._config,
            model=model,
            language=language,
            smart_format=smart_format,
            punctuate=punctuate,
            interim_results=interim_results,
            turn_detection=turn_detection,
            turn_detection_threshold=turn_detection_threshold,
            turn_detection_timeout_ms=turn_detection_timeout_ms,
            bg_speech_filter=bg_speech_filter,
            encoding=encoding,
            sample_rate=sample_rate,
            channels=channels,
            utterance_end_ms=utterance_end_ms,
            vad_events=vad_events,
            extra=extra,
            request_options=request_options,
        )
        try:
            with sync_connect(ws_url, headers) as websocket:
                yield RealtimeV1SocketClient(websocket=websocket)
        except Exception as exc:
            status_code = status_code_from_handshake_error(exc)
            if status_code is None:
                raise
            raise _handshake_error(status_code, headers) from exc


class AsyncRealtimeV1Client:
    """Async realtime transcription client."""

    def __init__(self, *, config: ClientOptions):
        self._config = config

    @asynccontextmanager
    async def connect(
        self,
        *,
        model: Model = "cove",
        language: Language = "en-US",
        smart_format: SmartFormat | None = None,
        punctuate: Punctuate | None = None,
        interim_results: InterimResults | None = True,
        turn_detection: TurnDetection | None = None,
        turn_detection_threshold: TurnDetectionThreshold | None = None,
        turn_detection_timeout_ms: TurnDetectionTimeoutMs | None = None,
        bg_speech_filter: BgSpeechFilter | None = None,
        encoding: Encoding | None = "linear16",
        sample_rate: SampleRate | None = 16000,
        channels: Channels | None = 1,
        utterance_end_ms: UtteranceEndMs | None = 1000,
        vad_events: VadEvents | None = None,
        extra: Extra | None = None,
        request_options: RequestOptions | None = None,
    ) -> typing.AsyncIterator[AsyncRealtimeV1SocketClient]:
        """Async version of :meth:`RealtimeV1Client.connect`."""
        ws_url, headers = _build_request(
            self._config,
            model=model,
            language=language,
            smart_format=smart_format,
            punctuate=punctuate,
            interim_results=interim_results,
            turn_detection=turn_detection,
            turn_detection_threshold=turn_detection_threshold,
            turn_detection_timeout_ms=turn_detection_timeout_ms,
            bg_speech_filter=bg_speech_filter,
            encoding=encoding,
            sample_rate=sample_rate,
            channels=channels,
            utterance_end_ms=utterance_end_ms,
            vad_events=vad_events,
            extra=extra,
            request_options=request_options,
        )
        try:
            async with async_connect(ws_url, headers) as websocket:
                yield AsyncRealtimeV1SocketClient(websocket=websocket)
        except Exception as exc:
            status_code = status_code_from_handshake_error(exc)
            if status_code is None:
                raise
            raise _handshake_error(status_code, headers) from exc
