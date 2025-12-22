# Zeus Python SDK

[![CI](https://github.com/skanda-observeai/zeus-sdk-py/actions/workflows/ci.yml/badge.svg)](https://github.com/skanda-observeai/zeus-sdk-py/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/zeus-sdk.svg)](https://badge.fury.io/py/zeus-sdk)
[![Python Versions](https://img.shields.io/pypi/pyversions/zeus-sdk.svg)](https://pypi.org/project/zeus-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Official Python SDK for Zeus ASR (Automatic Speech Recognition) platform.

## Features

- **Real-time Speech Recognition**: WebSocket-based streaming ASR
- **Pre-recorded Transcription**: REST API for batch processing (coming soon)
- **Easy Integration**: Simple, intuitive API
- **Async Support**: Full async/await support for modern Python applications

## Requirements

- Python 3.10 or higher

## Installation

```bash
pip install zeus-sdk
```

## Quick Start

### Real-time Transcription

```python
from zeus import ZeusClient, LiveTranscriptionEvents, LiveOptions

# Initialize the client
zeus = ZeusClient(api_key="your_api_key_here")

# Get WebSocket connection
connection = zeus.listen.websocket.v("1")

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
    model="nova-2",
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
from zeus import ZeusClient, LiveTranscriptionEvents, LiveOptions, Microphone

zeus = ZeusClient()
connection = zeus.listen.websocket.v("1")

# Set up event handlers...
connection.on(LiveTranscriptionEvents.Transcript, on_message)

# Start connection
options = LiveOptions(model="nova-2", smart_format=True)
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
export ZEUS_API_KEY=your_api_key_here
```

Or pass it directly:

```python
zeus = ZeusClient(api_key="your_api_key_here")
```

### Custom Endpoints

```python
from zeus import ZeusClient, ZeusClientOptions

config = ZeusClientOptions(
    api_key="your_api_key",
    url="https://custom-api.zeus.com"
)
zeus = ZeusClient(config=config)
```

## Features

### Real-time Transcription Options

- `model`: ASR model to use (e.g., "nova-2")
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
git clone https://github.com/zeus/zeus-sdk.git
cd zeus-sdk

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
pylint zeus/

# Format code
black zeus/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please visit our [GitHub repository](https://github.com/zeus/zeus-sdk).
