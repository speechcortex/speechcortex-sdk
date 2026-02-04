# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class RealtimeOptions:
    """
    Options for configuring live transcription via WebSocket.
    
    Attributes:
        model: The model to use (e.g., "zeus-v1")
        language: Language code (e.g., "en-US")
        smart_format: Enable smart formatting
        punctuate: Enable punctuation
        interim_results: Receive interim results
        encoding: Audio encoding format
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels
        utterance_end_ms: Milliseconds of silence for utterance end detection
        vad_events: Enable voice activity detection events
    """
    
    model: Optional[str] = "zeus-v1"
    language: Optional[str] = "en-US"
    smart_format: bool = False
    punctuate: bool = False
    interim_results: bool = True
    encoding: Optional[str] = "linear16"
    sample_rate: Optional[int] = 16000
    channels: Optional[int] = 1
    utterance_end_ms: Optional[int] = 1000
    vad_events: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to dictionary for API request"""
        params = {}
        
        if self.model:
            params["model"] = self.model
        if self.language:
            params["language"] = self.language
        if self.smart_format:
            params["smart_format"] = "true"
        if self.punctuate:
            params["punctuate"] = "true"
        if self.interim_results:
            params["interim_results"] = "true"
        if self.encoding:
            params["encoding"] = self.encoding
        if self.sample_rate:
            params["sample_rate"] = str(self.sample_rate)
        if self.channels:
            params["channels"] = str(self.channels)
        if self.utterance_end_ms:
            params["utterance_end_ms"] = str(self.utterance_end_ms)
        if self.vad_events:
            params["vad_events"] = "true"
            
        return params
    
    def check(self) -> bool:
        """Validate options"""
        # Basic validation
        if self.sample_rate and self.sample_rate <= 0:
            return False
        if self.channels and self.channels <= 0:
            return False
        return True


# Backwards compatibility: legacy name
class LiveOptions(RealtimeOptions):
    """Alias maintained for backward compatibility with earlier SDK versions."""

