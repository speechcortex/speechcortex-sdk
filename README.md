# SpeechCortex Python SDK

[![CI](https://github.com/speechcortex/speechcortex-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/speechcortex/speechcortex-sdk/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/speechcortex-sdk.svg)](https://badge.fury.io/py/speechcortex-sdk)
[![Python Versions](https://img.shields.io/pypi/pyversions/speechcortex-sdk.svg)](https://pypi.org/project/speechcortex-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Official Python SDK for SpeechCortex ASR (Automatic Speech Recognition) platform.

## Features

- **Real-time Speech Recognition**: WebSocket-based streaming ASR
- **Batch/Post-Call Transcription**: REST API for batch processing with file upload or presigned URLs
- **Easy Integration**: Simple, intuitive API
- **Async Support**: Full async/await support for modern Python applications

## Requirements

- Python 3.10 or higher

## Installation

```bash
pip install "git+https://github.com/speechcortex/speechcortex-sdk.git@package_init"
```

```bash
export SPEECHCORTEX_API_KEY=your_api_key_here
export SPEECHCORTEX_HOST=wss://api.speechcortex.com
```

## Quick Start

### Real-time Transcription

```python
from speechcortex import SpeechCortexClient, LiveTranscriptionEvents, LiveOptions

# Initialize the client
speechcortex = SpeechCortexClient(api_key="your_api_key_here")

# Get WebSocket connection
connection = speechcortex.listen.websocket.v("1")

# Set up event handlers
def on_message(self, result, **kwargs):
    sentence = result.channel.alternatives[0].transcript
    if result.is_final:
        print(f"Final: {sentence}")
    else:
        print(f"Interim: {sentence}")

def on_error(self, error, **kwargs):
    print(f"Error: {error}")

# Register event handlers
connection.on(LiveTranscriptionEvents.Transcript, on_message)
connection.on(LiveTranscriptionEvents.Error, on_error)

# Configure options
options = LiveOptions(
    model="zeus-v1",
    language="en-US",
    smart_format=True,
)

# Start the connection
connection.start(options)

# Send audio data
connection.send(audio_data)

# Close when done
connection.finish()
```

### Using with Microphone

```python
from speechcortex import SpeechCortexClient, LiveTranscriptionEvents, LiveOptions, Microphone

speechcortex = SpeechCortexClient()
connection = speechcortex.listen.websocket.v("1")

# Set up event handlers...
connection.on(LiveTranscriptionEvents.Transcript, on_message)

# Start connection
options = LiveOptions(model="zeus-v1", smart_format=True)
connection.start(options)

# Use microphone helper
microphone = Microphone(connection.send)
microphone.start()

# Microphone will stream audio automatically
# Press Ctrl+C to stop

microphone.finish()
connection.finish()
```

### Batch/Post-Call Transcription

```python
import asyncio
from speechcortex import SpeechCortexClient, BatchOptions, TranscriptionConfig

async def main():
    client = SpeechCortexClient(api_key="your_api_key_here")
    batch = client.transcribe.batch()

    async with batch:
        # Method 1: Submit with presigned URL
        job = await batch.submit_job(
            presigned_url="https://your-bucket.s3.amazonaws.com/audio.mp3?X-Amz-Algorithm=...",
            language="en-US",
            model="batch-zeus",
            diarize=True,
            punctuate=True,
        )

        # Wait for completion
        result = await batch.wait_for_completion(job.job_id, timeout=300.0)
        print(result.transcription)

        # Method 2: Upload file directly
        job = await batch.submit_job(
            audio_file="path/to/audio.mp3",
            language="en-US",
        )

        # Method 3: Convenience method (submit + wait in one call)
        result = await batch.transcribe(
            presigned_url="https://example.com/audio.mp3",
            language="en-US",
            timeout=300.0,
        )
        print(result.transcription)

asyncio.run(main())
```

### Batch Transcription with Configuration

```python
import asyncio
from speechcortex import SpeechCortexClient, BatchOptions, TranscriptionConfig

async def main():
    client = SpeechCortexClient()
    batch = client.transcribe.batch()

    async with batch:
        # Create transcription config
        config = TranscriptionConfig(
            language="en-US",
            model="batch-zeus",
            diarize=True,
            punctuate=True,
            smart_format=True,
            channel=2,
        )

        # Create batch options
        options = BatchOptions(
            polling_interval=5.0,
            timeout=600.0,
        )

        # Submit job
        job = await batch.submit_job(
            presigned_url="https://example.com/audio.mp3",
            config=config,
        )

        # Wait with custom options
        result = await batch.wait_for_completion(job.job_id, options=options)

asyncio.run(main())
```

### Manual Status Polling

```python
import asyncio
from speechcortex import SpeechCortexClient

async def main():
    client = SpeechCortexClient()
    batch = client.transcribe.batch()

    async with batch:
        # Submit job
        job = await batch.submit_job(
            presigned_url="https://example.com/audio.mp3",
            language="en-US",
        )

        # Manually poll for status
        while True:
            status = await batch.get_status(job.job_id)
            print(f"Status: {status.status}")

            if status.status.upper() == "COMPLETED":
                result = await batch.get_transcription(job.job_id)
                print(result.transcription)
                break
            elif status.status.upper() == "FAILED":
                print(f"Job failed: {status.error_message}")
                break

            await asyncio.sleep(3)

asyncio.run(main())
```

## Configuration

### API Key

Set your API key via environment variable:

```bash
export SPEECHCORTEX_API_KEY=your_api_key_here
```

Or pass it directly:

```python
speechcortex = SpeechCortexClient(api_key="your_api_key_here")
```

### Custom Endpoints

```python
from speechcortex import SpeechCortexClient, SpeechCortexClientOptions

config = SpeechCortexClientOptions(
    api_key="your_api_key",
    url="https://custom-api.speechcortex.com"
)
speechcortex = SpeechCortexClient(config=config)
```

## Features

### Real-time Transcription Options

- `model`: ASR model to use (e.g., "zeus-v1")
- `language`: Language code (e.g., "en-US")
- `smart_format`: Enable smart formatting
- `punctuate`: Enable punctuation
- `interim_results`: Receive interim results
- `utterance_end_ms`: Utterance end timeout in milliseconds
- `vad_events`: Enable voice activity detection events

### Batch Transcription Options

- `language`: Language code (e.g., "en-US", "ENGLISH")
- `model`: Transcription model (default: "batch-zeus")
- `diarize`: Enable speaker diarization (default: False)
- `punctuate`: Enable punctuation (default: True)
- `smart_format`: Enable smart formatting (default: True)
- `channel`: Number of audio channels (default: 2)
- `polling_interval`: Time between status checks in seconds (default: 3.0)
- `timeout`: Maximum time to wait for completion in seconds (default: None)

### Events

- `Open`: Connection opened
- `Transcript`: Transcription result received
- `Metadata`: Metadata received
- `SpeechStarted`: Speech detected
- `UtteranceEnd`: End of utterance detected
- `Close`: Connection closed
- `Error`: Error occurred
- `Unhandled`: Unhandled message received

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/speechcortex/speechcortex-sdk.git
cd speechcortex-sdk

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
pylint speechcortex/

# Format code
black speechcortex/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please visit our [GitHub repository](https://github.com/speechcortex/speechcortex-sdk).
