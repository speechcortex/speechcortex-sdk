#!/usr/bin/env python3
# Copyright 2024 Zeus SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Real-time speech transcription from audio file using Zeus SDK.

This example demonstrates:
1. Connecting to Zeus WebSocket API
2. Streaming audio from a WAV file
3. Receiving real-time transcription results
4. Handling different event types
"""

import os
import sys
import wave
import asyncio
import time
import argparse

# Add parent directory to path for local development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from zeus import (
    ZeusClient,
    TranscriptionEvents,
    RealtimeOptions,
)

class AudioFileStreamer:
    """
    Streams audio from a WAV file to the WebSocket connection.
    Simulates real-time audio by sending chunks at appropriate intervals.
    """
    
    def __init__(self, file_path: str, connection, chunk_size: int = 160):
        """
        Initialize the audio file streamer.
        
        Args:
            file_path: Path to the WAV file
            connection: Zeus WebSocket connection
            chunk_size: Number of frames to send per chunk (default: 160 = 10ms at 16kHz)
        """
        self.file_path = file_path
        self.connection = connection
        self.chunk_size = chunk_size
        self.is_streaming = False
        
    async def stream_audio(self):
        """Stream audio from file to WebSocket"""
        try:
            with wave.open(self.file_path, 'rb') as wav:
                sample_rate = wav.getframerate()
                sample_width = wav.getsampwidth()
                channels = wav.getnchannels()
                n_frames = wav.getnframes()
                
                print(f"\n📊 Audio file info:")
                print(f"   Sample rate: {sample_rate} Hz")
                print(f"   Sample width: {sample_width} bytes")
                print(f"   Channels: {channels}")
                print(f"   Total frames: {n_frames}")
                print(f"   Duration: {n_frames / sample_rate:.2f} seconds")
                print(f"   Chunk size: {self.chunk_size} frames\n")
                
                # Calculate sleep time between chunks to simulate real-time
                # chunk_duration = chunk_size / sample_rate
                chunk_duration = 0.02  # 20ms between chunks
                
                self.is_streaming = True
                chunk_num = 0
                
                # Send initial keep-alive messages
                for _ in range(2):
                    await asyncio.sleep(2)
                
                # Stream audio chunks
                while self.is_streaming:
                    wavedata = wav.readframes(self.chunk_size)
                    
                    if len(wavedata) == 0:
                        print("\n✓ Reached end of audio file")
                        break
                    
                    try:
                        # Send audio data
                        self.connection.send(wavedata)
                        chunk_num += 1
                        
                        if chunk_num % 50 == 0:  # Print progress every 50 chunks (~1 second)
                            elapsed = chunk_num * chunk_duration
                            print(f"📤 Streaming... {elapsed:.1f}s / {n_frames / sample_rate:.1f}s")
                        
                        # Wait to simulate real-time streaming
                        await asyncio.sleep(chunk_duration)
                        
                    except Exception as e:
                        print(f"❌ Error sending audio chunk: {e}")
                        break
                
                print(f"\n✓ Finished streaming {chunk_num} chunks")
                
        except FileNotFoundError:
            print(f"❌ Error: Audio file not found: {self.file_path}")
        except wave.Error as e:
            print(f"❌ Error reading WAV file: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    def stop(self):
        """Stop streaming audio"""
        self.is_streaming = False


def parse_args():
    default_wav = os.path.abspath(os.path.join(os.path.dirname(__file__), "../en_30.wav"))
    parser = argparse.ArgumentParser(description="Stream a WAV file to Zeus realtime transcription")
    parser.add_argument("file", nargs="?", default=default_wav, help="Path to WAV file (default: examples/en_30.wav)")
    parser.add_argument("--chunk-size", type=int, default=160, help="Frames per chunk (default 160 ≈10ms at 16kHz)")
    parser.add_argument("--model", default="zeus-v1", help="Model name (default: zeus-v1)")
    parser.add_argument("--language", default="en-US", help="Language (default: en-US)")
    parser.add_argument("--utterance-end-ms", type=int, default=1000, help="Silence ms to end utterance (default 1000)")
    return parser.parse_args()


def main():
    args = parse_args()

    audio_file = os.path.abspath(args.file)
    if not os.path.exists(audio_file):
        print(f"❌ Error: File not found: {audio_file}")
        sys.exit(1)

    is_finals = []
    all_finals = []

    try:
        zeus = ZeusClient()
        connection = zeus.transcribe.realtime()

        # Event handlers
        def on_open(self, open, **kwargs):
            print("✓ WebSocket connection opened")

        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if not sentence:
                return
            if result.is_final:
                print(f"\n✅ Final: {sentence}\n")
                is_finals.append(sentence)
                all_finals.append(sentence)
            else:
                print(f"\r🔄 Interim: {sentence}", end="", flush=True)

        def on_metadata(self, metadata, **kwargs):
            print(f"\n📋 Metadata: {metadata}")

        def on_speech_started(self, speech_started, **kwargs):
            print("\n🎤 Speech started")

        def on_utterance_end(self, utterance_end, **kwargs):
            if is_finals:
                utterance = " ".join(is_finals)
                print(f"\n🎯 Utterance End: {utterance}")
                is_finals.clear()

        def on_close(self, close, **kwargs):
            if close.code:
                from zeus import WebSocketStatusCode
                print(f"\n✓ WebSocket connection closed")
                print(f"   Code: {close.code} - {WebSocketStatusCode.get_description(close.code)}")
                if close.reason:
                    print(f"   Reason: {close.reason}")
            else:
                print("\n✓ WebSocket connection closed")

        def on_error(self, error, **kwargs):
            if getattr(error, "code", None):
                from zeus import WebSocketStatusCode
                print(f"\n❌ Error: {error.message}")
                print(f"   Code: {error.code} - {WebSocketStatusCode.get_description(error.code)}")
            else:
                print(f"\n❌ Error: {error}")

        def on_unhandled(self, unhandled, **kwargs):
            print(f"\n⚠️  Unhandled event: {unhandled}")

        connection.on(TranscriptionEvents.Open, on_open)
        connection.on(TranscriptionEvents.Transcript, on_message)
        connection.on(TranscriptionEvents.Metadata, on_metadata)
        connection.on(TranscriptionEvents.SpeechStarted, on_speech_started)
        connection.on(TranscriptionEvents.UtteranceEnd, on_utterance_end)
        connection.on(TranscriptionEvents.Close, on_close)
        connection.on(TranscriptionEvents.Error, on_error)
        connection.on(TranscriptionEvents.Unhandled, on_unhandled)

        options = RealtimeOptions(
            model=args.model,
            language=args.language,
            smart_format=True,
            punctuate=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms=args.utterance_end_ms,
            vad_events=True,
        )

        print("\n" + "=" * 60)
        print("🎙️  Zeus Real-Time Transcription - File Streaming")
        print("=" * 60)
        print(f"\n📁 Audio file: {audio_file}")

        if not connection.start(options):
            print("❌ Failed to start WebSocket connection")
            sys.exit(1)

        time.sleep(1)  # brief pause to establish
        streamer = AudioFileStreamer(audio_file, connection, chunk_size=args.chunk_size)

        async def stream_and_finish():
            await streamer.stream_audio()
            await asyncio.sleep(1)
            connection.finish()

        asyncio.run(stream_and_finish())

        print("\n⏳ Waiting for final transcription results...")
        time.sleep(2)

        print("\n" + "=" * 60)
        print("✓ Transcription complete!")
        print("=" * 60)

        if all_finals:
            complete_transcript = " ".join(all_finals)
            print("\n📝 Complete Transcript:")
            print("-" * 60)
            print(complete_transcript)
            print("-" * 60)
            print(f"\n📊 Total words: {len(complete_transcript.split())}")
            print(f"📊 Total characters: {len(complete_transcript)}")
        else:
            print("\n⚠️  No final transcripts received")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        try:
            connection.finish()
        except Exception:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
