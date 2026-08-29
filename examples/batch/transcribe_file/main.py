# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Submit an audio file for batch transcription and wait for the result.

Usage:
    export SPEECHCORTEX_API_KEY="your-key"
    export SPEECHCORTEX_HOST="wss://api.speechcortex.ai"
    python main.py path/to/audio.mp3
"""

import argparse
import json
import os
import sys

from speechcortex import SpeechCortexClient


def main():
    parser = argparse.ArgumentParser(description="Batch-transcribe an audio file")
    parser.add_argument("file", help="Path to the audio file")
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

    # URL comes from SPEECHCORTEX_HOST; the key from SPEECHCORTEX_API_KEY.
    client = SpeechCortexClient()

    with client.listen.batch.v1 as batch:
        print(f"Submitting {args.file} for transcription...")
        result = batch.transcribe(
            audio_file=args.file,
            language=args.language,
            timeout=args.timeout,
        )

    print("✅ Transcription complete")
    print(json.dumps(result.transcription, indent=2, default=str))


if __name__ == "__main__":
    main()
