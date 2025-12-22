# Contributing to Zeus Python SDK

First off, thank you for considering contributing to Zeus Python SDK! It's people like you that make Zeus SDK such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Be collaborative
- Be open to constructive criticism
- Focus on what is best for the community

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and what behavior you expected**
- **Include Python version, OS, and SDK version**
- **Include error messages and stack traces if applicable**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any similar features in other SDKs if applicable**

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install development dependencies**: `pip install -r requirements-dev.txt`
3. **Make your changes** following our coding standards
4. **Add tests** if you've added code that should be tested
5. **Ensure the test suite passes**: `make test`
6. **Run linting**: `make lint`
7. **Run type checking**: `make mypy`
8. **Update documentation** if you've changed APIs
9. **Commit your changes** with a clear commit message
10. **Push to your fork** and submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/zeus-sdk-py.git
cd zeus-sdk-py

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in editable mode
pip install -e .
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://github.com/psf/black) for code formatting (88 character line length)
- Use type hints for all functions and methods
- Write docstrings for all public modules, functions, classes, and methods

### Example:

```python
def transcribe_audio(
    file_path: str,
    language: str = "en",
    *,
    model: str = "general"
) -> dict[str, Any]:
    """
    Transcribe an audio file.

    Args:
        file_path: Path to the audio file to transcribe
        language: Language code (default: "en")
        model: Model to use for transcription (default: "general")

    Returns:
        Dictionary containing transcription results

    Raises:
        ZeusError: If transcription fails
    """
    pass
```

### Testing

- Write tests for all new features and bug fixes
- Use pytest for testing
- Aim for high test coverage (>80%)
- Include both unit tests and integration tests where appropriate

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=zeus --cov-report=html

# Run specific test file
pytest tests/test_client.py
```

### Type Checking

- Use mypy for static type checking
- All code must pass mypy checks

```bash
# Run mypy
mypy zeus/
```

### Linting

- Use pylint for code quality checks

```bash
# Run pylint
pylint zeus/
```

## Project Structure

```
zeus-sdk-py/
├── zeus/                  # Main package
│   ├── __init__.py       # Package initialization
│   ├── client.py         # Main client implementation
│   ├── errors.py         # Error classes
│   ├── options.py        # Configuration options
│   ├── audio/            # Audio processing
│   ├── clients/          # Client implementations
│   └── utils/            # Utility functions
├── examples/             # Usage examples
├── tests/                # Test files
├── docs/                 # Documentation
└── setup.py              # Package setup
```

## Commit Messages

- Use clear and meaningful commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update", "Remove")
- Reference issues and pull requests when applicable

Examples:
```
Add support for custom audio encodings
Fix WebSocket reconnection logic
Update documentation for LiveOptions
Remove deprecated API endpoints
```

## Release Process

Releases are handled by maintainers:

1. Update version in `zeus/__init__.py`, `setup.py`, and `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Create a git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions will automatically publish to PyPI

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
