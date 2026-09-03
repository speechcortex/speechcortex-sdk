#!/usr/bin/env python3
"""Stream speech audio, call send_finalize(), report from_finalize on Results."""

import json
import os
import subprocess
import sys
import threading
import time
import wave
from pathlib import Path

from speechcortex import EventType, Results, SpeechCortexClient

CHUNK_SIZE = 3200
SAMPLE_RATE = 16000


def make_speech_wav(path: Path) -> None:
    """16 kHz mono PCM WAV with spoken English (macOS say + ffmpeg)."""
    aiff = path.with_suffix(".aiff")
    text = (
        "Hello world. This is a test of realtime speech recognition. "
        "We are checking finalize and from finalize support."
    )
    subprocess.run(
        ["say", "-v", "Samantha", "-o", str(aiff), text],
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(aiff),
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-sample_fmt", "s16",
            str(path),
        ],
        check=True,
    )
    aiff.unlink(missing_ok=True)


def load_pcm_chunks(wav_path: Path) -> list[bytes]:
    with wave.open(str(wav_path), "rb") as wf:
        if wf.getsampwidth() != 2:
            raise ValueError(f"expected 16-bit PCM, got sampwidth={wf.getsampwidth()}")
        if wf.getframerate() != SAMPLE_RATE:
            raise ValueError(f"expected {SAMPLE_RATE} Hz, got {wf.getframerate()}")
        if wf.getnchannels() != 1:
            raise ValueError(f"expected mono, got {wf.getnchannels()} channels")
        pcm = wf.readframes(wf.getnframes())
    return [pcm[i:i + CHUNK_SIZE] for i in range(0, len(pcm), CHUNK_SIZE)]


def run(api_key: str, host: str, wav_path: Path, *, midstream_finalize: bool = False) -> dict:
    client = SpeechCortexClient(api_key=api_key, url=host)
    messages: list[dict] = []
    finalize_at: float | None = None

    chunks = load_pcm_chunks(wav_path)
    duration_s = len(chunks) * CHUNK_SIZE / (SAMPLE_RATE * 2)

    with client.listen.v1.connect(
        model="cove",
        language="en-US",
        smart_format=True,
        punctuate=True,
        encoding="linear16",
        sample_rate=SAMPLE_RATE,
        channels=1,
        interim_results=True,
    ) as connection:
        def on_message(msg):
            if isinstance(msg, Results):
                alt = (msg.channel.alternatives or [None])[0]
                transcript = (alt.transcript or "") if alt else ""
                messages.append({
                    "t": round(time.time(), 3),
                    "is_final": msg.is_final,
                    "speech_final": msg.speech_final,
                    "from_finalize": msg.from_finalize,
                    "transcript": transcript,
                })
                tag = "FINALIZE" if msg.from_finalize else "result"
                if transcript or msg.from_finalize:
                    print(
                        f"  [{tag}] from_finalize={msg.from_finalize} "
                        f"is_final={msg.is_final} transcript={transcript!r}"
                    )

        connection.on(EventType.MESSAGE, on_message)
        listener = threading.Thread(target=connection.start_listening, daemon=True)
        listener.start()
        time.sleep(0.3)

        print(f"Streaming {duration_s:.1f}s audio ({len(chunks)} chunks)...")
        if midstream_finalize:
            half = max(1, len(chunks) // 2)
            print(f"Mid-stream mode: send {half} chunks fast, then finalize, then rest")
            for chunk in chunks[:half]:
                connection.send_media(chunk)
            print("Sending send_finalize()...")
            finalize_at = time.time()
            connection.send_finalize()
            time.sleep(2.0)
            for chunk in chunks[half:]:
                connection.send_media(chunk)
            time.sleep(2.0)
        else:
            for chunk in chunks:
                connection.send_media(chunk)
                time.sleep(0.02)

            print("Sending send_finalize()...")
            finalize_at = time.time()
            connection.send_finalize()
            time.sleep(3.0)

    listener.join(timeout=5.0)

    after_finalize = [m for m in messages if m["t"] >= finalize_at]
    return {
        "audio_duration_s": round(duration_s, 2),
        "total_results": len(messages),
        "results_after_finalize": len(after_finalize),
        "any_from_finalize_true": any(m["from_finalize"] is True for m in messages),
        "from_finalize_messages": [m for m in messages if m["from_finalize"] is True],
        "all_messages": messages,
    }


def main() -> int:
    api_key = os.environ.get("SPEECHCORTEX_API_KEY")
    host = os.environ.get("SPEECHCORTEX_HOST", "wss://api.speechcortex.ai")

    if not api_key:
        print("Set SPEECHCORTEX_API_KEY", file=sys.stderr)
        return 1

    wav = Path("/tmp/speechcortex_finalize_test.wav")
    print("Generating speech sample...")
    make_speech_wav(wav)
    print(f"WAV: {wav}")

    midstream = "--midstream" in sys.argv
    print("\n=== Live finalize test ===")
    try:
        summary = run(api_key, host, wav, midstream_finalize=midstream)
        print("\n=== Summary ===")
        print(json.dumps({k: v for k, v in summary.items() if k != "all_messages"}, indent=2))
        if summary["any_from_finalize_true"]:
            print("\nSUCCESS: received Results with from_finalize=true")
        else:
            print("\nNOTE: no from_finalize=true (may need more buffered audio or server timing)")
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
