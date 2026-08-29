# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Type aliases for the batch transcription parameters.

Each option is passed to ``submit_job()`` / ``transcribe()`` as an individual
keyword argument; these aliases document the accepted values.
"""

from typing import Any

Language = str
Model = str
Diarize = bool
Punctuate = bool
SmartFormat = bool
Channel = int
Pci = bool

# Escape hatch: forwarded as-is to the query string. Use this to try new
# server-side parameters without waiting for an SDK release.
Extra = dict[str, Any]
