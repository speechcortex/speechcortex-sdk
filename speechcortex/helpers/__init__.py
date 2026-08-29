# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from .errors import SpeechCortexMicrophoneError
from .microphone import Microphone

__all__ = ["Microphone", "SpeechCortexMicrophoneError"]
