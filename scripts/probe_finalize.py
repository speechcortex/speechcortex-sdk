#!/usr/bin/env python3
"""Probe SpeechCortex websocket for Finalize / from_finalize support."""

import json
import os
import struct
import sys
import threading
import time
import wave
from pathlib import Path

from speechcortex import EventType, Results, SpeechCortexClient
from speechcortex.listen.v1.socket_client import RealtimeV1SocketClient


def check_sdk_surface() -> dict:
    sync_has = hasattr(RealtimeV1SocketClient, "send_finalize")
    async_cls = __import__(
        "speechcortex.listen.v1.socket_client", fromlist=["AsyncRealtimeV1SocketClient"]
    ).AsyncRealtimeV1SocketClient
    results_fields = set(Results.model_fields.keys())
    return {
        "send_finalize_on_sync_client": sync_has,
        "send_finalize_on_async_client": hasattr(async_cls, "send_finalize"),
        "from_finalize_in_results_model": "from_finalize" in results_fields,
        "results_model_fields": sorted(results_fields),
    }


def make_test_wav(path: Path, seconds: float = 2.0) -> None:
    """Minimal 16kHz mono PCM WAV (silence; server may still accept Finalize)."""
    sample_rate = 16000
    n = int(sample_rate * seconds)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n}h", *([0] * n)))


def run_live_probe(api_key: str, host: str) -> dict:
    client = SpeechCortexClient(api_key=api_key, url=host)
    received: list = []
    finalize_sent = False
    lock = threading.Lock()

    wav = Path("/tmp/speechcortex_probe.wav")
    make_test_wav(wav)

    with client.listen.v1.connect(
        model="cove",
        language="en-US",
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        interim_results=True,
    ) as connection:
        def on_message(msg):
            with lock:
                if isinstance(msg, Results):
                    received.append(
                        {
                            "type": "Results",
                            "is_final": msg.is_final,
                            "speech_final": msg.speech_final,
                            "from_finalize_model_field": msg.from_finalize,
                            "from_finalize_in_dump": msg.model_dump().get("from_finalize"),
                            "transcript": (
                                (msg.channel.alternatives[0].transcript or "")
                                if msg.channel and msg.channel.alternatives
                                else ""
                            ),
                        }
                    )
                else:
                    received.append({"type": getattr(msg, "type", type(msg).__name__), "raw": str(msg)})

        connection.on(EventType.MESSAGE, on_message)
        listener = threading.Thread(target=connection.start_listening, daemon=True)
        listener.start()
        time.sleep(0.3)

        with open(wav, "rb") as f:
            f.seek(44)
            while chunk := f.read(3200):
                connection.send_media(chunk)
                time.sleep(0.02)

        connection.send_finalize()
        finalize_sent = True
        time.sleep(2.0)
        connection.send_keep_alive()
        time.sleep(1.0)

    listener.join(timeout=5.0)

    from_finalize_values = [
        r.get("from_finalize_model_field") for r in received if r.get("type") == "Results"
    ]
    return {
        "finalize_message_sent": finalize_sent,
        "results_message_count": len(from_finalize_values),
        "from_finalize_values_seen": from_finalize_values,
        "any_from_finalize_true": any(v is True for v in from_finalize_values),
        "all_results_messages": [r for r in received if r.get("type") == "Results"],
        "other_messages": [r for r in received if r.get("type") != "Results"],
    }


def main() -> int:
    sdk = check_sdk_surface()
    print("=== SDK surface ===")
    print(json.dumps(sdk, indent=2))

    api_key = os.environ.get("SPEECHCORTEX_API_KEY")
    host = os.environ.get("SPEECHCORTEX_HOST", "wss://api.speechcortex.ai")

    if not api_key or api_key == "your-api-key":
        print("\n=== Live API probe ===")
        print("SKIPPED: set SPEECHCORTEX_API_KEY (and optionally SPEECHCORTEX_HOST) to test the server.")
        return 0

    print("\n=== Live API probe ===")
    try:
        live = run_live_probe(api_key, host)
        print(json.dumps(live, indent=2))
    except Exception as exc:
        print(f"LIVE_PROBE_ERROR: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
