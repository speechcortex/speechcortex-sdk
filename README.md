# SpeechCortex Python SDK

Official Python SDK for the SpeechCortex ASR platform.

## Installation

```bash
pip install speechcortex-sdk
# with microphone support:
pip install speechcortex-sdk[microphone]
```

## Requirements

- Python 3.10+
- A SpeechCortex API key
- The host URL of the SpeechCortex API (e.g. `wss://api.speechcortex.ai`)

## Configuration

The client needs an API key and a host URL — either passed explicitly or via
the `SPEECHCORTEX_API_KEY` / `SPEECHCORTEX_HOST` environment variables:

```python
from speechcortex import SpeechCortexClient

client = SpeechCortexClient(api_key="...", url="wss://api.speechcortex.ai")

# or, from the environment:
client = SpeechCortexClient()
```

## API layout

The package is organized like Deepgram's SDK:

- `client.listen.v1` — realtime streaming transcription (websocket)
- `client.listen.batch.v1` — batch transcription jobs (REST)
- `speechcortex.helpers` — user-facing helpers (`Microphone`)
- `speechcortex.transport` — websocket transport layer

Planned namespaces (added when the endpoints ship): `client.speak` for
text-to-speech and `client.manage` for API keys/projects.

## Realtime streaming transcription

`connect()` opens a websocket and must be used as a context manager. It
raises `ApiError` on handshake failure (e.g. invalid credentials) instead of
failing silently later.

```python
import threading

import speechcortex
from speechcortex import EventType, SpeechCortexClient

client = SpeechCortexClient(api_key="...", url="wss://api.speechcortex.ai")

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
    bg_speech_filter="balanced",  # "minimal" | "balanced" | "aggressive" | False
    vad_events=True,
) as connection:

    def on_message(message):
        if isinstance(message, speechcortex.Results):
            sentence = message.channel.alternatives[0].transcript
            if message.is_final and sentence:
                print("final:", sentence)
        elif isinstance(message, speechcortex.UtteranceEnd):
            print("utterance ended")

    connection.on(EventType.OPEN, lambda _: print("opened"))
    connection.on(EventType.MESSAGE, on_message)
    connection.on(EventType.ERROR, lambda e: print("error:", repr(e)))
    connection.on(EventType.CLOSE, lambda _: print("closed"))

    # start_listening() blocks until the connection closes
    threading.Thread(target=connection.start_listening, daemon=True).start()

    with open("audio.wav", "rb") as f:
        f.seek(44)  # skip WAV header
        while chunk := f.read(3200):
            connection.send_media(chunk)

    connection.send_keep_alive()
# leaving the with-block closes the connection
```

Async equivalent (`AsyncSpeechCortexClient` + `async with`) has the same shape;
run `await connection.start_listening()` as a task:

```python
import asyncio
from speechcortex import AsyncSpeechCortexClient

client = AsyncSpeechCortexClient(api_key="...", url="wss://api.speechcortex.ai")

async def run():
    async with client.listen.v1.connect(model="cove") as connection:
        connection.on(EventType.MESSAGE, on_message)
        listening = asyncio.create_task(connection.start_listening())

        while chunk := get_audio_chunk():
            await connection.send_media(chunk)
        await connection.send_keep_alive()

    await listening  # completes when the context exit closes the socket
```

### Events

| Event | Data | Notes |
|---|---|---|
| `EventType.OPEN` | `None` | Connection established |
| `EventType.MESSAGE` | typed model | `Results`, `Metadata`, `SpeechStarted`, `UtteranceEnd`, `ErrorResponse` — discriminate with `isinstance`; unknown payload types arrive as raw dicts |
| `EventType.ERROR` | `Exception` | Connection/read errors |
| `EventType.CLOSE` | `None` | Connection closed |

Response models tolerate unknown fields, and `start_of_turn`/`end_of_turn`
are `None` when the server omits them (check before use).

## Batch transcription

```python
from speechcortex import SpeechCortexClient

client = SpeechCortexClient(api_key="...", url="wss://api.speechcortex.ai")
batch = client.listen.batch.v1

# From a presigned URL:
job = batch.submit_job(presigned_url="https://s3.test/audio.mp3", diarize=True)
result = batch.wait_for_completion(job.job_id, polling_interval=3.0, timeout=600.0)

# From a local file (multipart upload, content type inferred from the extension):
result = batch.transcribe(audio_file="meeting.mp3", language="en-US")

# Async twin: AsyncSpeechCortexClient().listen.batch.v1
client_async = AsyncSpeechCortexClient(api_key="...", url="wss://api.speechcortex.ai")
async with client_async.listen.batch.v1 as batch:
    result = await batch.transcribe(presigned_url="https://s3.test/audio.mp3")
```

Errors: `JobNotFoundError`, `JobFailedError`, `TranscriptionNotReadyError`,
`BatchTimeoutError`, and `ApiError` for HTTP failures (invalid credentials →
401).

## Microphone helper

```python
from speechcortex.helpers import Microphone

microphone = Microphone(push_callback=connection.send_media)
microphone.start()
# ... microphone.mute() / microphone.unmute()
microphone.finish()
```

## Examples

- [examples/realtime/file_streaming](examples/realtime/file_streaming/main.py) — stream a file with turn detection (sync)
- [examples/realtime/file_streaming_async](examples/realtime/file_streaming_async/main.py) — the same, using `AsyncSpeechCortexClient`
- [examples/realtime/microphone](examples/realtime/microphone/main.py) — stream from the microphone
- [examples/batch/transcribe_file](examples/batch/transcribe_file/main.py) — batch-transcribe a file (sync)
- [examples/batch/transcribe_file_async](examples/batch/transcribe_file_async/main.py) — the same, using `AsyncSpeechCortexClient`

## Development

```bash
pip install -e .[dev]
make lint      # ruff
make typecheck # mypy
make test      # pytest (no network required)
make coverage
```

## Migrating from 0.1.x

See [CHANGELOG.md](CHANGELOG.md#020) for the full list of breaking changes
and the migration table.
