# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Async version of the file-streaming example: stream an audio file to the
SpeechCortex realtime transcription API using AsyncSpeechCortexClient.

Usage:
    export SPEECHCORTEX_API_KEY="your-key"
    export SPEECHCORTEX_HOST="wss://api.speechcortex.ai"
    python main.py path/to/audio.wav
"""

import argparse
import asyncio
import os
import sys

import speechcortex
from speechcortex import AsyncSpeechCortexClient, EventType

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 3200  # 100ms of 16-bit linear16 audio
REALTIME_MS_PER_CHUNK = 20.0  # simulates real-time pacing


def parse_args():
    parser = argparse.ArgumentParser(description="Stream a file for transcription (async)")
    parser.add_argument("file", help="Path to the audio file (16-bit PCM WAV)")
    parser.add_argument(
        "--utterance-end-ms",
        type=int,
        default=1000,
        help="Silence duration (ms) that triggers an utterance end event",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    audio_file = os.path.abspath(args.file)
    if not os.path.exists(audio_file):
        print(f"❌ Error: File not found: {audio_file}")
        sys.exit(1)

    # URL comes from SPEECHCORTEX_HOST; the key from SPEECHCORTEX_API_KEY.
    client = AsyncSpeechCortexClient()

    async with client.listen.v1.connect(
        model="cove",
        language="en-US",
        smart_format=True,
        punctuate=True,
        encoding="linear16",
        sample_rate=SAMPLE_RATE,
        channels=CHANNELS,
        interim_results=True,
        turn_detection=True,
        turn_detection_threshold=0.65,
        turn_detection_timeout_ms=2000,
        utterance_end_ms=args.utterance_end_ms,
        vad_events=True,
    ) as connection:
        utterance_parts: list = []

        def on_message(message):
            if not isinstance(message, speechcortex.Results):
                if isinstance(message, speechcortex.UtteranceEnd):
                    if utterance_parts:
                        print(f"\n🎯 Utterance End: {' '.join(utterance_parts)}")
                        utterance_parts.clear()
                elif isinstance(message, speechcortex.SpeechStarted):
                    print("\n🎤 Speech started")
                elif isinstance(message, speechcortex.ErrorResponse):
                    print(f"\n❌ Server error: {message.message}")
                return

            alternative = (message.channel.alternatives or [None])[0]
            sentence = alternative.transcript if alternative else ""
            if message.start_of_turn is not None:
                print(f"start_of_turn: {message.start_of_turn.event}")
            if message.end_of_turn is not None:
                print(f"end_of_turn: {message.end_of_turn.event}")
            if not sentence:
                return
            if message.is_final:
                print(f"\n✅ Final: {sentence}\n")
                utterance_parts.append(sentence)
            else:
                print(f"\r🔄 Interim: {sentence}", end="", flush=True)

        connection.on(EventType.OPEN, lambda _: print("✓ WebSocket connection opened"))
        connection.on(EventType.MESSAGE, on_message)
        connection.on(EventType.ERROR, lambda err: print(f"\n❌ Connection error: {err!r}"))
        connection.on(EventType.CLOSE, lambda _: print("\n✓ WebSocket connection closed"))

        # start_listening() blocks until the connection closes; run it as a task.
        listening = asyncio.create_task(connection.start_listening())

        # Pump the file at (roughly) real-time pace.
        with open(audio_file, "rb") as f:
            header = f.read(44)  # skip WAV header
            if header[0:4] != b"RIFF":
                f.seek(0)
            while chunk := f.read(CHUNK_SIZE):
                await connection.send_media(chunk)
                await asyncio.sleep(REALTIME_MS_PER_CHUNK / 1000.0)

        # Keep the connection alive while trailing audio is processed.
        for _ in range(3):
            await asyncio.sleep(1.0)
            await connection.send_keep_alive()

    # Exiting the with-block closes the socket, which ends start_listening.
    await asyncio.wait_for(listening, timeout=10.0)

    print("✓ Transcription complete!")


if __name__ == "__main__":
    asyncio.run(main())
