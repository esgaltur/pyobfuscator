# Skjol

A free and open-source Python code protection framework with layered defenses.

## Features

### Core Obfuscation

- **Name Obfuscation**: Renames variables, functions, and classes to unreadable names
- **Polymorphic String Obfuscation**: Unique, randomized decoding logic for every string literal
- **Legacy String Encoding**: Optional support for base64, hex, or XOR encoding strategies
- **Code Compression**: Optionally compresses code into a single exec() statement
- **Docstring Removal**: Removes docstrings to reduce code size and readability
- **Comment Removal**: Comments are automatically removed during AST processing

### Runtime Protection

- **Encrypted Bytecode**: Code compiled to bytecode and encrypted before distribution
- **PYD Compilation**: Compile runtime to .pyd/.so (C extension) for maximum protection
- **Polymorphic Runtime**: Each protection generates unique obfuscated code
- **Import Hooks**: Custom module loading system for protected imports

### Encryption

- **AES-256-GCM**: Military-grade encryption with authentication
- **PBKDF2 Key Derivation**: 100,000 iterations for key strengthening
- **Per-file Salt/Nonce**: Unique cryptographic parameters for each file

## Project Structure

```
pyobfuscator/
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
    ├── obfuscate_project.py
    ├── protect_project.py
    └── tests.py
```

## Installation

Clone the repository and install dependencies:
```powershell
git clone https://github.com/esgaltur/skjol.git
cd skjol
pip install -e .
```

For PYD protection, install Cython:
```powershell
pip install cython
```

## Usage

### Command Line

```powershell
# Obfuscate and encrypt a single file (the default protection pipeline)
python -m skjol obfuscate -i script.py -o protected.py

# Obfuscate and encrypt a directory recursively
python -m skjol obfuscate -i src -o dist

# Obfuscate without runtime encryption
python -m skjol obfuscate -i script.py -o obfuscated.py --no-encrypt

# Compress obfuscation-only output
python -m skjol obfuscate -i script.py -o obfuscated.py --no-encrypt --compress

# Using XOR for string obfuscation
python -m skjol obfuscate -i script.py -o protected.py --string-method xor

# Verbose output
python -m skjol obfuscate -i src -o dist -v
```

Runtime-encrypted output imports a generated
`skjol_runtime_<id>.py`. Keep that file in the same output directory as
the protected script. Directory protection creates a matching runtime in each
subdirectory that contains protected Python files, allowing nested entry points
to run directly.

### Python API

```python
from skjol import Obfuscator

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
| `--no-encrypt` | Apply AST obfuscation without runtime encryption |
| `--no-anti-debug` | Disable runtime anti-debug checks |
| `--code-virtualization` | Enable VM-based code transformation |
| `--whitebox` | Enable white-box encryption support |
| `--control-flow-flatten` | Enable control-flow flattening |
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
# Skjol 2.0.2 (PYD), abc123, Protected, 2026-03-01
from skjol_runtime_abc123 import __skjol__
__skjol__(__name__, __file__, b'UFlEMDAwMDEAA...')
```

## Running Examples

```powershell
# Basic obfuscation demo
python examples\demo.py

# Runtime protection demo
python examples\demo_runtime_protection.py

# PYD protection demo
python examples\demo_pyd_protection.py

# Obfuscate a sample project (directory-level)
python examples\obfuscate_project.py

# Protect a sample project (PYD runtime)
python examples\protect_project.py
```

## Running Tests

The CLI protection tests generate real protected programs, execute them, and
clean up through pytest's temporary-directory fixtures.

```powershell
python -m pytest -q tests\test_cli_protection.py
python -m pytest -q
```

## Limitations

- Does not obfuscate attribute names (could break external API calls)
- Some Python features like decorators may need excluded names
- f-strings with complex expressions may not obfuscate perfectly
- Pure Python runtime can be reverse-engineered (use PYD compilation for stronger protection)

## Comparison with Commercial Solutions

| Feature | Skjol | Commercial Tools |
|---------|-------------|------------------|
| License | Free & Open Source | Paid |
| Name obfuscation | ✓ | ✓ |
| String obfuscation | ✓ | ✓ |
| Code compression | ✓ | ✓ |
| Runtime protection | ✓ | ✓ |
| License expiration | ✓ | ✓ |
| Machine binding | ✓ | ✓ |
| Python 3.13+ | ✓ | Limited |

Skjol provides layered protection without licensing restrictions. Its output
can still be recovered by a sufficiently capable attacker, so protection
profiles should be selected using the documented threat model and tests.
