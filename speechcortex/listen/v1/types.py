# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Response models for realtime transcription websocket messages.

All models tolerate unknown fields (``extra="allow"``), so new fields added
by the server are preserved rather than rejected. Unknown message ``type``
values are logged and skipped by the socket client.
"""

from typing import Any, Literal

from ...core.unchecked_base_model import UncheckedBaseModel


class TurnInfo(UncheckedBaseModel):
    """Turn-detection event information."""

    event: bool | None = None
    confidence: float | None = None
    timestamp: float | None = None


class Word(UncheckedBaseModel):
    """A word in a transcription alternative."""

    word: str = ""
    start: float = 0.0
    end: float = 0.0
    confidence: float = 0.0
    punctuated_word: str | None = None
    speaker: int | None = None
    speaker_confidence: float | None = None


class Alternative(UncheckedBaseModel):
    """A transcription alternative for a channel."""

    transcript: str = ""
    confidence: float = 0.0
    words: list[Word] = []


class Channel(UncheckedBaseModel):
    """Audio channel data."""

    alternatives: list[Alternative] = []


class Metadata(UncheckedBaseModel):
    """Metadata about the request or session."""

    type: Literal["Metadata"] = "Metadata"
    transaction_key: str | None = None
    request_id: str | None = None
    sha256: str | None = None
    created: str | None = None
    duration: float | None = None
    channels: int | None = None
    model_info: dict[str, Any] | None = None
    model_uuid: str | None = None


class Results(UncheckedBaseModel):
    """Live transcription result.

    ``start_of_turn``/``end_of_turn`` are ``None`` when the server omits the
    field (i.e. when turn detection is disabled or no event applies).
    """

    type: Literal["Results"] = "Results"
    channel: Channel | None = None
    channel_index: list[int] | None = None
    duration: float | None = None
    start: float | None = None
    is_final: bool | None = None
    speech_final: bool | None = None
    start_of_turn: TurnInfo | None = None
    end_of_turn: TurnInfo | None = None
    metadata: Metadata | None = None


class SpeechStarted(UncheckedBaseModel):
    """Emitted when speech is detected."""

    type: Literal["SpeechStarted"] = "SpeechStarted"
    channel: list[int] | None = None
    timestamp: float | None = None


class UtteranceEnd(UncheckedBaseModel):
    """Emitted when an utterance ends (silence detected)."""

    type: Literal["UtteranceEnd"] = "UtteranceEnd"
    channel: list[int] | None = None
    last_word_end: float | None = None


class ErrorResponse(UncheckedBaseModel):
    """Error message sent by the server."""

    type: Literal["Error"] = "Error"
    code: int | None = None
    description: str | None = None
    message: str | None = None
    variant: str | None = None


class KeepAlive(UncheckedBaseModel):
    """Control message that keeps an idle websocket connection alive."""

    type: Literal["KeepAlive"] = "KeepAlive"


RealtimeSocketResponse = Results | Metadata | SpeechStarted | UtteranceEnd | ErrorResponse
