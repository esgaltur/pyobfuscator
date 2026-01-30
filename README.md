# PyObfuscate

A lightweight, license-free Python code obfuscation library with PyArmor-style runtime protection.

## Features

- **Name Obfuscation**: Renames variables, functions, and classes to unreadable names
- **String Obfuscation**: Encodes string literals using base64, hex, or XOR encoding
- **Code Compression**: Optionally compresses code into a single exec() statement
- **Docstring Removal**: Removes docstrings to reduce code size and readability
- **Comment Removal**: Comments are automatically removed during AST processing
- **Runtime Protection**: PyArmor-style encrypted bytecode with runtime decryption
- **PYD Compilation**: Compile runtime to .pyd (C extension) for maximum protection
- **Strong Encryption**: AES-256-GCM with PBKDF2 key derivation (100,000 iterations)
- **Anti-Debugging**: Detects debuggers, tracers, and inspection tools
- **License Expiration**: Time-based license with configurable expiration dates
- **Machine Binding**: Lock code execution to specific hardware/machines
- **Domain Lock**: Restrict execution to specific domain names (for web apps)
- **Memory Protection**: Secure clearing of sensitive data after use
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
├── runtime_protection.py # PyArmor-style runtime protection
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

### After PYD Protection (PyArmor-style)

```python
# PyObfuscate 1.0.0 (PYD), abc123, Protected, 2026-01-30
from pyobfuscate_runtime_abc123 import __pyobfuscate__
__pyobfuscate__(__name__, __file__, b'UFlEMDAwMDEAA...')
```

## Runtime Protection API

### Basic Usage

```python
from pyobfuscate import RuntimeProtector

# Basic protection (no restrictions)
protector = RuntimeProtector(license_info="My App v1.0")
protected_code, runtime_module = protector.protect_source(source_code, "app.py")
```

### With Expiration Date

```python
from datetime import datetime, timedelta
from pyobfuscate import RuntimeProtector

# Protection with 30-day expiration
protector = RuntimeProtector(
    license_info="Trial License",
    expiration_date=datetime.now() + timedelta(days=30)
)
protected_code, runtime_module = protector.protect_source(source_code)
```

### Machine Binding

```python
from pyobfuscate import RuntimeProtector

# Get current machine ID
machine_id = RuntimeProtector.get_machine_id()
print(f"Machine ID: {machine_id}")

# Protect code for specific machines only
protector = RuntimeProtector(
    license_info="Licensed to ACME Corp",
    allowed_machines=[machine_id, "other_machine_id"]
)
protected_code, runtime_module = protector.protect_source(source_code)
```

### Full Protection (All Features)

```python
from datetime import datetime, timedelta
from pyobfuscate import RuntimeProtector

# Full protection with all security features
protector = RuntimeProtector(
    license_info="Enterprise License",
    expiration_date=datetime.now() + timedelta(days=365),
    allowed_machines=[RuntimeProtector.get_machine_id()],
    anti_debug=True,  # Detect debuggers
    domain_lock=["mycompany.com", "localhost"]  # For web apps
)

protected_code, runtime_module = protector.protect_source(source_code, "app.py")

# Save protected files
with open("protected_app.py", "w") as f:
    f.write(protected_code)

with open(f"pyobfuscate_runtime_{protector.runtime_id}.py", "w") as f:
    f.write(runtime_module)
```

### PYD Protection (Compiled Runtime)

```python
from pyobfuscate import PydRuntimeProtector

# Create PYD protector with all features
protector = PydRuntimeProtector(
    license_info="Premium License",
    expiration_date=datetime.now() + timedelta(days=365),
    allowed_machines=[PydRuntimeProtector.get_machine_id()],
    anti_debug=True
)

# Protect and build .pyd
result = protector.protect_file("app.py", "dist/", build_pyd=True)
print(f"Protected file: {result['protected']}")
print(f"PYD runtime: {result['pyd']}")
```

### Protection Options

| Option | Type | Description |
|--------|------|-------------|
| `license_info` | str | License/author info embedded in protected files |
| `encryption_key` | bytes | Custom 32-byte key (auto-generated if not provided) |
| `expiration_date` | datetime | Optional expiration date |
| `allowed_machines` | list[str] | List of allowed machine IDs |
| `anti_debug` | bool | Enable anti-debugging detection (default: True) |
| `domain_lock` | list[str] | List of allowed domain names |

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
- Anti-debugging can be bypassed by determined attackers (defense in depth recommended)

## Comparison with PyArmor

| Feature | PyObfuscate | PyArmor |
|---------|-------------|---------|
| License | Free | Paid for full features |
| Name obfuscation | ✓ | ✓ |
| String obfuscation | ✓ | ✓ |
| Code compression | ✓ | ✓ |
| Runtime protection | ✓ | ✓ |
| Anti-debugging | ✓ | ✓ |
| License expiration | ✓ | ✓ |
| Machine binding | ✓ | ✓ |
| Domain lock | ✓ | ✓ |
| PYD compilation | ✓ | ✓ |
| Python 3.13+ | ✓ | Limited |

PyObfuscate now provides PyArmor-style runtime protection with all advanced security features, completely free and open source.
