# PyObfuscate

A lightweight, license-free Python code obfuscation library with advanced runtime protection.

## Features

- **Name Obfuscation**: Renames variables, functions, and classes to unreadable names
- **String Obfuscation**: Encodes string literals using base64, hex, or XOR encoding
- **Code Compression**: Optionally compresses code into a single exec() statement
- **Docstring Removal**: Removes docstrings to reduce code size and readability
- **Comment Removal**: Comments are automatically removed during AST processing
- **Runtime Protection**: Encrypted bytecode with runtime decryption
- **PYD Compilation**: Compile runtime to .pyd (C extension) for maximum protection
- **Strong Encryption**: AES-256-GCM with PBKDF2 key derivation (100,000 iterations)
- **Configurable**: Fine-tune what gets obfuscated and what remains readable

## Security

### Encryption
- **Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Authentication**: Built-in integrity verification (AEAD)
- **Per-file Salt**: Random 16-byte salt for each encryption
- **Per-file Nonce**: Random 12-byte nonce for each encryption

### Optional Dependencies
For best performance, install the `cryptography` package:
```bash
pip install cryptography
```
Without it, a pure Python fallback is used (same security, slower).

## Project Structure

```
pyobfuscate/
├── __init__.py           # Package exports
├── __main__.py           # CLI entry point
├── cli.py                # Command-line interface
├── obfuscator.py         # Core AST-based obfuscation
├── runtime_protection.py # Runtime protection with encryption
├── pyd_protection.py     # PYD (Cython-compiled) runtime protection
├── transformers.py       # Advanced AST transformers
├── utils.py              # Utility functions
├── README.md
└── examples/             # Demos and example scripts
    ├── demo.py
    ├── demo_runtime_protection.py
    ├── demo_pyd_protection.py
    ├── obfuscate_dashboard.py
    ├── protect_dashboard.py
    └── tests.py
```

## Installation

This library is included in the project. For PYD protection, install Cython:
```bash
pip install cython
```

## Usage

### Command Line

```bash
# Obfuscate a single file
python -m pyobfuscate -i script.py -o obfuscated.py

# Obfuscate a directory
python -m pyobfuscate -i src/ -o dist/ --recursive

# With compression
python -m pyobfuscate -i script.py -o obfuscated.py --compress

# Using XOR for string obfuscation
python -m pyobfuscate -i script.py -o obfuscated.py --string-method xor

# Verbose output
python -m pyobfuscate -i src/ -o dist/ -v
```

### Python API

```python
from pyobfuscate import Obfuscator

# Create obfuscator with desired options
obfuscator = Obfuscator(
    rename_variables=True,
    rename_functions=True,
    rename_classes=True,
    obfuscate_strings=True,
    compress_code=False,
    remove_docstrings=True,
    name_style="random",  # or "hex", "hash"
    string_method="base64",  # or "hex", "xor"
    exclude_names={'my_public_api'}  # names to preserve
)

# Obfuscate source code
source = '''
def hello(name):
    """Greet someone."""
    message = f"Hello, {name}!"
    return message
'''

obfuscated = obfuscator.obfuscate_source(source)
print(obfuscated)

# Obfuscate a file
obfuscator.obfuscate_file('input.py', 'output.py')

# Obfuscate a directory
results = obfuscator.obfuscate_directory(
    'src/',
    'dist/',
    recursive=True,
    exclude_patterns=['test_*', '*_test.py']
)
```

## Options

### Name Styles

- `random`: Random alphanumeric names (default)
- `hex`: Hexadecimal-based names (_x1, _x2, etc.)
- `hash`: Hash-based names derived from original names

### String Obfuscation Methods

- `base64`: Base64 encoding (default, most compatible)
- `hex`: Hexadecimal encoding
- `xor`: XOR encryption with random key (more secure)

### CLI Options

| Option | Description |
|--------|-------------|
| `-i, --input` | Input file or directory |
| `-o, --output` | Output file or directory |
| `-r, --recursive` | Process directories recursively (default) |
| `--no-recursive` | Don't process directories recursively |
| `--no-rename-vars` | Keep variable names |
| `--no-rename-funcs` | Keep function names |
| `--no-rename-classes` | Keep class names |
| `--no-string-obfuscation` | Keep strings readable |
| `--compress` | Compress output to exec() |
| `--keep-docstrings` | Preserve docstrings |
| `--name-style` | Name generation style |
| `--string-method` | String obfuscation method |
| `--exclude` | Names to exclude from renaming |
| `--exclude-patterns` | File patterns to skip |
| `-v, --verbose` | Show detailed output |

## Example

### Before Obfuscation

```python
def calculate_discount(price, percentage):
    """Calculate the discounted price."""
    discount = price * (percentage / 100)
    final_price = price - discount
    return final_price

def main():
    original = 100.0
    result = calculate_discount(original, 20)
    print(f"Final price: ${result:.2f}")
```

### After Obfuscation (AST-based)

```python
def _aK7mPx2(_qR3nL, _wY8tB):
    _vN5jC = _qR3nL * (_wY8tB / 100)
    _hM2kF = _qR3nL - _vN5jC
    return _hM2kF

def _zX9pD():
    _bT4sG = 100.0
    _cU6rH = _aK7mPx2(_bT4sG, 20)
    print(f'{__import__("base64").b64decode("RmluYWwgcHJpY2U6ICQ=").decode("utf-8")}{_cU6rH:.2f}')
```

### After PYD Protection (Encrypted Runtime)

```python
# PyObfuscate 1.0.0 (PYD), abc123, Protected, 2026-01-30
from pyobfuscate_runtime_abc123 import __pyobfuscate__
__pyobfuscate__(__name__, __file__, b'UFlEMDAwMDEAA...')
```

## Running Examples

```bash
# Basic obfuscation demo
python pyobfuscate/examples/demo.py

# Runtime protection demo
python pyobfuscate/examples/demo_runtime_protection.py

# PYD protection demo
python pyobfuscate/examples/demo_pyd_protection.py

# Obfuscate github_pr_dashboard (AST-based)
python pyobfuscate/examples/obfuscate_dashboard.py

# Protect github_pr_dashboard (PYD runtime)
python pyobfuscate/examples/protect_dashboard.py

# Run tests
python pyobfuscate/examples/tests.py
```

## Running Tests

```bash
python pyobfuscate/tests.py
```

## Limitations

- Does not obfuscate attribute names (could break external API calls)
- Some Python features like decorators may need excluded names
- f-strings with complex expressions may not obfuscate perfectly
- Pure Python runtime can be reverse-engineered (use PYD compilation for stronger protection)

## Comparison with Commercial Solutions

| Feature | PyObfuscate | Commercial Tools |
|---------|-------------|------------------|
| License | Free & Open Source | Paid |
| Name obfuscation | ✓ | ✓ |
| String obfuscation | ✓ | ✓ |
| Code compression | ✓ | ✓ |
| Runtime protection | ✓ | ✓ |
| License expiration | ✓ | ✓ |
| Machine binding | ✓ | ✓ |
| Python 3.13+ | ✓ | Limited |

PyObfuscate provides enterprise-grade protection without licensing restrictions.
