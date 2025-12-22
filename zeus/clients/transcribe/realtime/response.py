# Copyright 2024 Zeus SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from typing import Optional, List, Any
from dataclasses_json import dataclass_json, config


@dataclass_json
@dataclass
class BaseResponse:
    """Base response class"""
    pass


@dataclass_json
@dataclass
class OpenResponse(BaseResponse):
    """Response when WebSocket connection opens"""
    type: str = "Open"


@dataclass_json
@dataclass
class CloseResponse(BaseResponse):
    """Response when WebSocket connection closes"""
    type: str = "Close"
    code: Optional[int] = None
    reason: Optional[str] = None


@dataclass_json
@dataclass
class ErrorResponse(BaseResponse):
    """Error response from the API"""
    type: str = "Error"
    code: Optional[int] = None
    description: Optional[str] = None
    message: Optional[str] = None
    variant: Optional[str] = None


@dataclass_json
@dataclass
class UnhandledResponse(BaseResponse):
    """Unhandled message response"""
    type: str = "Unhandled"
    raw: Optional[str] = None


@dataclass_json
@dataclass
class Word:
    """Word in transcription"""
    word: str = ""
    start: float = 0.0
    end: float = 0.0
    confidence: float = 0.0
    punctuated_word: Optional[str] = None


@dataclass_json
@dataclass
class Alternative:
    """Transcription alternative"""
    transcript: str = ""
    confidence: float = 0.0
    words: List[Word] = field(default_factory=list)


@dataclass_json
@dataclass
class Channel:
    """Audio channel data"""
    alternatives: List[Alternative] = field(default_factory=list)


@dataclass_json
@dataclass
class Metadata:
    """Metadata about the request"""
    request_id: Optional[str] = None
    model_info: Optional[Any] = None
    model_uuid: Optional[str] = None


@dataclass_json
@dataclass
class LiveResultResponse(BaseResponse):
    """Live transcription result"""
    type: str = "Results"
    channel: Channel = field(default_factory=Channel)
    duration: float = 0.0
    start: float = 0.0
    is_final: bool = False
    speech_final: bool = False
    channel_index: List[int] = field(default_factory=list)
    metadata: Optional[Metadata] = None


@dataclass_json
@dataclass
class MetadataResponse(BaseResponse):
    """Metadata response"""
    type: str = "Metadata"
    transaction_key: Optional[str] = None
    request_id: Optional[str] = None
    sha256: Optional[str] = None
    created: Optional[str] = None
    duration: Optional[float] = None
    channels: Optional[int] = None


@dataclass_json
@dataclass
class SpeechStartedResponse(BaseResponse):
    """Speech started event"""
    type: str = "SpeechStarted"
    channel: List[int] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass_json
@dataclass
class UtteranceEndResponse(BaseResponse):
    """Utterance end event"""
    type: str = "UtteranceEnd"
    channel: List[int] = field(default_factory=list)
    last_word_end: float = 0.0
