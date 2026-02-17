# SpeechCortex Python SDK

[![CI](https://github.com/speechcortex/speechcortex-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/speechcortex/speechcortex-sdk/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/speechcortex-sdk.svg)](https://badge.fury.io/py/speechcortex-sdk)
[![Python Versions](https://img.shields.io/pypi/pyversions/speechcortex-sdk.svg)](https://pypi.org/project/speechcortex-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Official Python SDK for SpeechCortex ASR (Automatic Speech Recognition) platform.

## Features

- **Real-time Speech Recognition**: WebSocket-based streaming ASR
- **Pre-recorded Transcription**: REST API for batch processing (coming soon)
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
