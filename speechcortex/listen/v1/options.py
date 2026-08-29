# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Type aliases for the realtime transcription connect options.

Each option is passed to ``connect()`` as an individual keyword argument;
these aliases document the accepted values.
"""

from typing import Any, Literal

Model = str
Language = str
SmartFormat = bool
Punctuate = bool
InterimResults = bool
TurnDetection = bool
TurnDetectionThreshold = float
TurnDetectionTimeoutMs = int
BgSpeechFilter = Literal["minimal", "balanced", "aggressive", False]
Encoding = str
SampleRate = int
Channels = int
UtteranceEndMs = int
VadEvents = bool

# Escape hatch: forwarded as-is to the query string. Use this to try new
# server-side parameters without waiting for an SDK release.
Extra = dict[str, Any] | None
