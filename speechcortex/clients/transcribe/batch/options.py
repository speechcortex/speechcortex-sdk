# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Configuration options for batch transcription.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union
import os


@dataclass
class TranscriptionConfig:
    """
    Configuration for transcription parameters.
    
    Attributes:
        language: Language code (e.g., "en-US", "ENGLISH")
        model: Transcription model to use (default: "batch-zeus")
        diarize: Enable speaker diarization (default: False)
        punctuate: Enable punctuation (default: True)
        smart_format: Enable smart formatting (default: True)
        channel: Number of audio channels (default: 2)
        pci: PCI compliance flag (default: False)
        extra_params: Additional parameters as dict or JSON string
    """
    language: str = "en-US"
    model: str = "batch-zeus"
    diarize: bool = False
    punctuate: bool = False
    smart_format: bool = False
    channel: int = 2
    pci: bool = False
    extra_params: Optional[Union[Dict[str, Any], str]] = None
    
    def to_query_params(self) -> Dict[str, Any]:
        """Convert config to query parameters for API request."""
        params = {
            "language": self.language,
            "model": self.model,
            "diarize": str(self.diarize).lower(),
            "punctuate": str(self.punctuate).lower(),
            "smart_format": str(self.smart_format).lower(),
            "channel": str(self.channel),
            "pci": str(self.pci).lower(),
        }
        
        # Handle extra_params
        if self.extra_params:
            if isinstance(self.extra_params, str):
                import json
                try:
                    extra = json.loads(self.extra_params)
                    if isinstance(extra, dict):
                        params.update(extra)
                except json.JSONDecodeError:
                    pass
            elif isinstance(self.extra_params, dict):
                params.update(self.extra_params)
        
        return params


@dataclass
class BatchOptions:
    """
    Options for batch transcription operations.
    
    Attributes:
        polling_interval: Time in seconds between status checks (default: 3.0)
        timeout: Maximum time in seconds to wait for completion (default: None, no timeout)
        batch_path: API path for batch transcription endpoints (default: "/api/v1/transcription")
    """
    polling_interval: float = 3.0
    timeout: Optional[float] = None
    batch_path: str = field(default_factory=lambda: os.getenv(
        "SPEECHCORTEX_BATCH_PATH", 
        "/api/v1/transcription"
    ))
    
    def __post_init__(self):
        """Validate options after initialization."""
        if self.polling_interval <= 0:
            raise ValueError("polling_interval must be greater than 0")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be greater than 0")
