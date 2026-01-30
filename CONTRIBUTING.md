# Contributing to PyObfuscate

Thank you for your interest in contributing to PyObfuscate! This document provides guidelines and information for contributors.

## Code of Conduct

Please be respectful and considerate of others. We're all here to make PyObfuscate better.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/esgaltur/pyobfuscator/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Relevant code snippets

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with the "enhancement" label
3. Describe the feature and its use case
4. Explain why it would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python examples/tests.py`)
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pyobfuscator.git
cd pyobfuscator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[all]"

# Install development dependencies
pip install pytest pytest-cov black isort flake8

# Run tests
python examples/tests.py
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to public functions and classes
- Keep functions focused and small
- Write tests for new features

## Testing

- Run `python examples/tests.py` before submitting
- Add tests for new features
- Ensure all tests pass on Python 3.9+

## Security

If you discover a security vulnerability, please:
1. **Do NOT** open a public issue
2. Email the maintainers directly
3. Allow time for a fix before public disclosure

## Questions?

Open an issue with the "question" label or start a discussion.

Thank you for contributing! 🎉
