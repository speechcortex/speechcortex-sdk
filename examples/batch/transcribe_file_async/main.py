# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Async version of the batch transcription example: submit an audio file and
wait for the result using AsyncSpeechCortexClient.

Usage:
    export SPEECHCORTEX_API_KEY="your-key"
    export SPEECHCORTEX_HOST="wss://api.speechcortex.ai"
    python main.py path/to/audio.mp3
"""

import argparse
import asyncio
import json
import os
import sys

from speechcortex import AsyncSpeechCortexClient


async def main():
    parser = argparse.ArgumentParser(description="Batch-transcribe an audio file (async)")
    parser.add_argument("file", help="Path to the audio file")
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

    # URL comes from SPEECHCORTEX_HOST; the key from SPEECHCORTEX_API_KEY.
    client = AsyncSpeechCortexClient()

    async with client.listen.batch.v1 as batch:
        print(f"Submitting {args.file} for transcription...")
        result = await batch.transcribe(
            audio_file=args.file,
            language=args.language,
            timeout=args.timeout,
        )

    print("✅ Transcription complete")
    print(json.dumps(result.transcription, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
