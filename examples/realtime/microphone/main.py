# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Stream microphone audio to the SpeechCortex realtime transcription API.

Requires the microphone extra: pip install speechcortex-sdk[microphone]

Usage:
    export SPEECHCORTEX_API_KEY="your-key"
    export SPEECHCORTEX_HOST="wss://api.speechcortex.ai"
    python main.py
"""

import threading

import speechcortex
from speechcortex import EventType, SpeechCortexClient
from speechcortex.helpers import Microphone


def main():
    # URL comes from SPEECHCORTEX_HOST; the key from SPEECHCORTEX_API_KEY.
    client = SpeechCortexClient()

    with client.listen.v1.connect(
        model="cove",
        language="en-US",
        smart_format=True,
        punctuate=True,
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        interim_results=True,
        turn_detection=True,
        turn_detection_threshold=0.65,
        turn_detection_timeout_ms=2000,
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
                return

            alternative = (message.channel.alternatives or [None])[0]
            sentence = alternative.transcript if alternative else ""
            if not sentence:
                return
            if message.is_final:
                print(f"\n✅ Final: {sentence}\n")
                utterance_parts.append(sentence)
            else:
                print(f"\r🔄 Interim: {sentence}", end="", flush=True)

        connection.on(EventType.MESSAGE, on_message)
        connection.on(EventType.ERROR, lambda err: print(f"\n❌ {err!r}"))

        # start_listening() blocks until the connection closes.
        listening = threading.Thread(target=connection.start_listening, daemon=True)
        listening.start()

        microphone = Microphone(push_callback=connection.send_media)
        microphone.start()
        print("🎤 Listening — press Ctrl+C to stop")

        try:
            listening.join()
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            microphone.finish()


if __name__ == "__main__":
    main()
