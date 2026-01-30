# PyObfuscate

[![CI](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml/badge.svg)](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/pyobfuscate.svg)](https://badge.fury.io/py/pyobfuscate)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security: 50+ Features](https://img.shields.io/badge/Security-50%2B%20Features-green.svg)](https://github.com/esgaltur/pyobfuscator#features)

A comprehensive, license-free Python code obfuscation library with enterprise-grade runtime protection.

## Features

### Core Obfuscation
- **Name Obfuscation**: Renames variables, functions, and classes to unreadable names
- **String Obfuscation**: Encodes string literals using base64, hex, or XOR encoding
- **Code Compression**: Optionally compresses code into a single exec() statement
- **Docstring Removal**: Removes docstrings to reduce code size and readability
- **Comment Removal**: Comments are automatically removed during AST processing
- **Configurable**: Fine-tune what gets obfuscated and what remains readable

### Runtime Protection
- **Encrypted Bytecode**: Code compiled to bytecode and encrypted before distribution
- **PYD Compilation**: Compile runtime to .pyd/.so (C extension) for maximum protection
- **Polymorphic Runtime**: Each protection generates unique obfuscated code with different variable names
- **Import Hooks**: Custom module loading system for protected imports

### Encryption
- **AES-256-GCM**: Military-grade encryption with authentication
- **Layered Encryption**: XOR + AES double encryption for defense in depth
- **PBKDF2 Key Derivation**: 100,000 iterations for key strengthening
- **Bytecode Scrambling**: XOR-based bytecode obfuscation before encryption
- **Per-file Salt/Nonce**: Unique cryptographic parameters for each file
- **Constant Blinding**: Magic numbers hidden through XOR operations

### Code Virtualization
- **Stack-based VM**: Custom virtual machine with 35 randomized opcodes
- **Randomized Opcode Table**: Opcode mappings change with each protection
- **Self-modifying Code**: VM bytecode modifies itself during execution
- **Anti-analysis in VM**: Detects tracing and corrupts output if analyzed
- **Subroutine Support**: CALL/RET instructions for complex transformation programs

### Anti-Analysis Protection (12+ Layers)
| Layer | Feature | Description |
|-------|---------|-------------|
| 1 | **Self-integrity Check** | Verifies runtime module hash |
| 2 | **Anti-patching** | Detects modifications to runtime files |
| 3 | **Call Stack Verification** | Verifies execution context is legitimate |
| 4 | **Anti-memory Dump** | Detects CheatEngine, x64dbg, IDA, Ghidra, etc. |
| 5 | **Parent Process Trace** | Verifies not launched by analysis tools |
| 6 | **Anti-hooking** | Detects if built-in functions are replaced |
| 7 | **Environment Fingerprinting** | Detailed environment verification |
| 8 | **Timing-based Anti-debug** | Detects debugger slowdown |
| 9 | **Debugger Module Detection** | Checks for pydevd, debugpy, pdb in memory |
| 10 | **Environment Variable Check** | Detects PYTHONDEBUG, PYCHARM_DEBUG, etc. |
| 11 | **VM/Sandbox Detection** | Detects VMware, VirtualBox, QEMU, Hyper-V |
| 12 | **Profile/Trace Check** | Detects sys.settrace/setprofile hooks |

### Control Flow Protection
- **Control Flow Dispatch**: Indirect function calls through dispatch table
- **State Machine**: Execution flow verification through state transitions
- **Code Splitting**: Decryption logic distributed across multiple functions
- **Opaque Predicates**: Complex conditions that always evaluate the same but confuse static analysis
- **Dead Code Injection**: Realistic but never-executed code paths
- **Fake Error Paths**: Decoy error handlers that trigger on analysis

### Integrity Verification
- **SHA-256 Checksums**: Payload integrity verification
- **Checksum Chains**: Incremental hash verification throughout execution
- **HMAC Authentication**: Cryptographic authentication of encrypted data
- **Encrypted Error Messages**: All error strings are XOR-encrypted

### Licensing & DRM
- **License Expiration**: Time-based restrictions with configurable dates
- **Machine Binding**: Lock code execution to specific hardware (CPU, MAC, disk serial)
- **Domain Lock**: Restrict execution to specific hostnames/domains
- **Network License**: Optional online license validation with server
- **Watermarking**: Hidden identifiers for tracking unauthorized distribution
- **Honey Tokens**: Fake decryption keys to detect tampering attempts

### Defense Mechanisms
- **Resource Exhaustion**: CPU-intensive loop triggered on tampering detection
- **Secure Memory Clear**: 5-pass key wiping (0x00, 0xFF, 0xAA, 0x55, 0x00)
- **String Table Encryption**: Constant strings stored in encrypted lookup table
- **Decoy Operations**: Fake key generation to confuse memory analysis

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

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `license_info` | str | "PyObfuscate..." | License/author info embedded in protected files |
| `encryption_key` | bytes | Auto-generated | Custom 32-byte encryption key |
| `expiration_date` | datetime | None | Optional expiration date for time-limited licenses |
| `allowed_machines` | list[str] | [] | List of allowed machine IDs for hardware binding |
| `anti_debug` | bool | True | Enable multi-layer anti-debugging detection |
| `domain_lock` | list[str] | [] | List of allowed domain names for web apps |
| `enable_vm_detection` | bool | False | Enable VM/sandbox detection (may have false positives) |
| `enable_network_check` | bool | False | Enable online license validation |
| `license_server_url` | str | None | URL for network license validation server |

### Getting Machine ID

```python
from pyobfuscate import RuntimeProtector

# Get current machine's unique ID for hardware binding
machine_id = RuntimeProtector.get_machine_id()
print(f"Machine ID: {machine_id}")

# Use in protection
protector = RuntimeProtector(
    allowed_machines=[machine_id, "other_machine_id"]
)
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
- Anti-debugging can be bypassed by determined attackers (defense in depth recommended)
- VM/sandbox detection may have false positives in legitimate virtualized environments

## Security Architecture

### Execution Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY VERIFICATION LAYERS                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1:  Self-integrity Check (SHA-256 hash verification)     │
│  Layer 2:  Anti-patching Detection (file modification check)    │
│  Layer 3:  Call Stack Verification (debugger frame detection)   │
│  Layer 4:  Anti-memory Dump (analysis tool detection)           │
│  Layer 5:  Parent Process Trace (launcher verification)         │
│  Layer 6:  Anti-hooking (built-in function verification)        │
│  Layer 7:  Environment Fingerprinting (suspicious env check)    │
├─────────────────────────────────────────────────────────────────┤
│                     PAYLOAD PROCESSING                           │
├─────────────────────────────────────────────────────────────────┤
│  ► Checksum Chain Initialization                                 │
│  ► Magic Header Verification (PYO00004)                         │
│  ► SHA-256 Integrity Check                                       │
│  ► AES-256-GCM Decryption (Layer 2)                             │
│  ► XOR Decryption (Layer 1)                                      │
│  ► Metadata Parsing                                              │
├─────────────────────────────────────────────────────────────────┤
│                    LICENSE VERIFICATION                          │
├─────────────────────────────────────────────────────────────────┤
│  ► Anti-debug Check (if enabled)                                │
│  ► VM/Sandbox Detection (if enabled)                            │
│  ► Expiration Date Check                                         │
│  ► Machine ID Verification                                       │
│  ► Domain Lock Check                                             │
│  ► Network License Validation (if configured)                   │
├─────────────────────────────────────────────────────────────────┤
│                     CODE EXECUTION                               │
├─────────────────────────────────────────────────────────────────┤
│  ► Zlib Decompression                                            │
│  ► VM-based Bytecode Descrambling (35 random opcodes)           │
│  ► Final Checksum Verification                                   │
│  ► Marshal Load                                                  │
│  ► Import Hook Registration                                      │
│  ► Code Execution (via Control Flow Dispatcher)                 │
│  ► Secure Memory Cleanup                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Code Virtualization VM
```
┌────────────────────────────────────────┐
│         VIRTUALIZATION ENGINE          │
├────────────────────────────────────────┤
│  Opcodes (35 total, randomized):       │
│  ├─ Stack: PUSH, POP, DUP, SWAP, ROT3  │
│  ├─ Math:  ADD, SUB, MUL, DIV, MOD     │
│  ├─ Bits:  XOR, AND, OR, NOT, SHL, SHR │
│  ├─ Bits:  ROTL, ROTR                  │
│  ├─ Flow:  JMP, JZ, JNZ, JGT, JLT      │
│  ├─ Call:  CALL, RET                   │
│  ├─ Mem:   LOAD, STORE, LOADB, STOREB  │
│  └─ Spec:  NOP, HALT, MUTATE, CHECK,   │
│            TRAP                         │
├────────────────────────────────────────┤
│  Features:                              │
│  ├─ Randomized opcode mapping          │
│  ├─ Self-modifying bytecode            │
│  ├─ Anti-analysis detection            │
│  ├─ Instruction counter limits         │
│  └─ Output corruption on tampering     │
└────────────────────────────────────────┘
```

## Comparison with Commercial Solutions

| Feature | PyObfuscate | Commercial Tools |
|---------|-------------|------------------|
| **License** | Free & Open Source | Paid |
| **Basic Obfuscation** | | |
| Name obfuscation | ✓ | ✓ |
| String obfuscation | ✓ | ✓ |
| Code compression | ✓ | ✓ |
| **Encryption** | | |
| AES-256-GCM | ✓ | ✓ |
| Layered encryption | ✓ | ✓ |
| Bytecode scrambling | ✓ | ✓ |
| **Runtime Protection** | | |
| Anti-debugging (12+ layers) | ✓ | ✓ |
| Anti-memory dump | ✓ | ✓ |
| Anti-hooking | ✓ | ✓ |
| Anti-patching | ✓ | ✓ |
| **Code Virtualization** | | |
| Custom VM | ✓ | ✓ |
| Randomized opcodes | ✓ | ✓ |
| Self-modifying code | ✓ | ✓ |
| **Control Flow** | | |
| Control flow flattening | ✓ | ✓ |
| Opaque predicates | ✓ | ✓ |
| Dead code injection | ✓ | ✓ |
| State machine verification | ✓ | Some |
| **Licensing/DRM** | | |
| License expiration | ✓ | ✓ |
| Machine binding | ✓ | ✓ |
| Domain lock | ✓ | ✓ |
| Network license | ✓ | ✓ |
| Watermarking | ✓ | ✓ |
| **Other** | | |
| PYD compilation | ✓ | ✓ |
| Polymorphic output | ✓ | ✓ |
| Checksum chains | ✓ | Some |
| Honey tokens | ✓ | Some |
| Python 3.13+ | ✓ | Limited |

**Total: 50+ security features** - PyObfuscate provides enterprise-grade protection completely free and open source.

## License

MIT License - Free for commercial and personal use.
