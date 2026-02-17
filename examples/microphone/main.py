#!/usr/bin/env python3
# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Real-time speech transcription from microphone using SpeechCortex SDK.

This example demonstrates:
1. Connecting to SpeechCortex WebSocket API
2. Streaming audio from microphone
3. Receiving real-time transcription results
4. Handling different event types
"""

import os
import sys


# Add parent directory to path for local development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from speechcortex import (
    SpeechCortexClient,
    TranscriptionEvents,
    RealtimeOptions,
    Microphone,
)

# We will collect the is_final=true messages here
is_finals = []


def main():
    try:
        # Initialize SpeechCortex client
        # API key can be set via SPEECHCORTEX_API_KEY environment variable
        # or passed directly: SpeechCortexClient(api_key="your_key")
        speechcortex = SpeechCortexClient()

        # Get real-time transcription connection
        connection = speechcortex.transcribe.realtime()

        # Define event handlers
        def on_open(self, open, **kwargs):
            print("✓ Connection opened")

        def on_message(self, result, **kwargs):
            global is_finals
            sentence = result.channel.alternatives[0].transcript
            
            if len(sentence) == 0:
                return
            
            if result.is_final:
                # Final transcription for this segment
                is_finals.append(sentence)

                if result.speech_final:
                    # Speech final = sufficient silence detected, end of speech
                    utterance = " ".join(is_finals)
                    print(f"\n[FINAL] {utterance}\n")
                    is_finals = []
                else:
                    print(f"[IS_FINAL] {sentence}")
            else:
                # Interim results - partial transcription
                print(f"[INTERIM] {sentence}", end="\r")

        def on_metadata(self, metadata, **kwargs):
            print(f"[METADATA] Request ID: {metadata.request_id}")

        def on_speech_started(self, speech_started, **kwargs):
            print("\n🎤 Speech detected...")

        def on_utterance_end(self, utterance_end, **kwargs):
            global is_finals
            if len(is_finals) > 0:
                utterance = " ".join(is_finals)
                print(f"\n[UTTERANCE_END] {utterance}\n")
                is_finals = []

        def on_close(self, close, **kwargs):
            print("\n✓ Connection closed")

        def on_error(self, error, **kwargs):
            print(f"\n❌ Error: {error.message}")

        def on_unhandled(self, unhandled, **kwargs):
            print(f"\n⚠️  Unhandled message: {unhandled.raw}")

        # Register event handlers
        connection.on(TranscriptionEvents.Open, on_open)
        connection.on(TranscriptionEvents.Transcript, on_message)
        connection.on(TranscriptionEvents.Metadata, on_metadata)
        connection.on(TranscriptionEvents.SpeechStarted, on_speech_started)
        connection.on(TranscriptionEvents.UtteranceEnd, on_utterance_end)
        connection.on(TranscriptionEvents.Close, on_close)
        connection.on(TranscriptionEvents.Error, on_error)
        connection.on(TranscriptionEvents.Unhandled, on_unhandled)

        # Configure transcription options
        options = RealtimeOptions(
            model="zeus-v1",
            language="en-US",
            smart_format=True,  # Enable smart formatting
            punctuate=True,     # Enable punctuation
            interim_results=True,  # Get interim results
            utterance_end_ms=1000,  # 1 second of silence = end of utterance
            vad_events=True,    # Enable voice activity detection events
        )

        print("Starting SpeechCortex real-time transcription...")
        print("Speak into your microphone. Press Ctrl+C to stop.\n")

        # Start the WebSocket connection
        if not connection.start(options):
            print("Failed to start connection")
            return

        # Start microphone streaming
        microphone = Microphone(connection.send)
        microphone.start()

        # Keep running until interrupted
        try:
            import time
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nStopping...")

        # Clean up
        microphone.finish()
        connection.finish()

        print("✓ Done")

    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
