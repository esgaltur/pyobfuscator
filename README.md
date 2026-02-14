# PyObfuscator

[![CI](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml/badge.svg)](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/pyobfuscator.svg)](https://badge.fury.io/py/pyobfuscator)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security: 50+ Features](https://img.shields.io/badge/Security-50%2B%20Features-green.svg)](https://github.com/esgaltur/pyobfuscator#features)
[![White Paper](https://img.shields.io/badge/White%20Paper-Available-blue.svg)](docs/WHITEPAPER.md)
[![Documentation](https://img.shields.io/badge/Docs-Technical-green.svg)](docs/TECHNICAL_DOCUMENTATION.md)

A comprehensive, **100% free and open source** Python code obfuscation library with enterprise-grade runtime protection.
PyObfuscator itself has **no trial, no paid tiers, no licensing restrictions** - it's completely free under the MIT
License.

## 📚 Documentation

- **[White Paper](docs/WHITEPAPER.md)** - Comprehensive overview of the protection framework
- **[Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md)** - Detailed scientific basis and implementation details
- **[Citation File](CITATION.cff)** - For academic citations
- **[BibTeX References](docs/references.bib)** - Bibliography for academic papers

## ⚠️ Important: Understanding the Terminology

| Term                       | What it means                                                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **PyObfuscator**           | This tool. 100% free, open source, MIT License. No restrictions.                                                                  |
| **Your Code**              | The Python code YOU want to protect using PyObfuscator.                                                                           |
| **Protected Code**         | Your code after PyObfuscator processes it.                                                                                        |
| **Licensing/DRM Features** | Tools for YOU to add restrictions to YOUR code (e.g., trial periods, machine binding). These do NOT apply to PyObfuscator itself. |

> **Example:** You can use PyObfuscator (free) to create a trial version of your commercial app that expires in 30 days.
> The "trial" is for YOUR app, not PyObfuscator.

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

| Layer | Feature                        | Description                                    |
|-------|--------------------------------|------------------------------------------------|
| 1     | **Self-integrity Check**       | Verifies runtime module hash                   |
| 2     | **Anti-patching**              | Detects modifications to runtime files         |
| 3     | **Call Stack Verification**    | Verifies execution context is legitimate       |
| 4     | **Anti-memory Dump**           | Detects CheatEngine, x64dbg, IDA, Ghidra, etc. |
| 5     | **Parent Process Trace**       | Verifies not launched by analysis tools        |
| 6     | **Anti-hooking**               | Detects if built-in functions are replaced     |
| 7     | **Environment Fingerprinting** | Detailed environment verification              |
| 8     | **Timing-based Anti-debug**    | Detects debugger slowdown                      |
| 9     | **Debugger Module Detection**  | Checks for pydevd, debugpy, pdb in memory      |
| 10    | **Environment Variable Check** | Detects PYTHONDEBUG, PYCHARM_DEBUG, etc.       |
| 11    | **VM/Sandbox Detection**       | Detects VMware, VirtualBox, QEMU, Hyper-V      |
| 12    | **Profile/Trace Check**        | Detects sys.settrace/setprofile hooks          |

### Control Flow Protection

- **Control Flow Dispatch**: Indirect function calls through dispatch table
- **Control Flow Flattening (CFF)**: Transforms functions into dispatcher-based state machines
- **State Machine**: Execution flow verification through state transitions
- **Code Splitting**: Decryption logic distributed across multiple functions
- **Opaque Predicates**: Complex conditions that always evaluate the same but confuse static analysis
- **Dead Code Injection**: Realistic but never-executed code paths
- **Fake Error Paths**: Decoy error handlers that trigger on analysis

### Integrity Verification

- **SHA-256 Checksums**: Payload integrity verification
- **Checksum Chains**: Incremental hash verification throughout execution
- **Function Integrity Checks**: Hash-based verification of function code at runtime
- **HMAC Authentication**: Cryptographic authentication of encrypted data
- **Encrypted Error Messages**: All error strings are XOR-encrypted

### Licensing & DRM (Features to Protect YOUR Code)

> 🆓 **PyObfuscator is free.** These features let you add licensing to YOUR protected applications.

- **License Expiration**: Add time limits to YOUR protected code (e.g., 30-day trial)
- **Machine Binding**: Lock YOUR code to specific hardware (CPU, MAC, disk serial)
- **Domain Lock**: Restrict YOUR code to specific hostnames/domains
- **Network License**: Add online license validation to YOUR apps
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

### Why Open Source? (Kerckhoffs's Principle)

> *"A cryptographic system should be secure even if everything about the system, except the key, is public
knowledge."* — Auguste Kerckhoffs, 1883

PyObfuscator is intentionally open source because:

1. **Cryptographic security doesn't depend on algorithm secrecy** — AES-256 is a public standard; security comes from
   the secret key
2. **Python libraries can't be hidden anyway** — `.pyc` bytecode is trivially decompilable
3. **Security by obscurity always fails** — Attackers will reverse-engineer closed-source tools
4. **Trust through transparency** — Open source allows security audits

**What IS secret (unique per protection):**

- Your 256-bit encryption key
- Random salt/nonce per file
- Polymorphic variable names
- Randomized VM opcode mapping

See the [White Paper](docs/WHITEPAPER.md#84-open-source-security-model-kerckhoffss-principle) for detailed analysis.

### Optional Dependencies

For best performance, install the `cryptography` package:

```bash
pip install cryptography
```

Without it, a pure Python fallback is used (same security, slower).

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
python -m pyobfuscator -i script.py -o obfuscated.py

# Obfuscate a directory
python -m pyobfuscator -i src/ -o dist/ --recursive

# With compression
python -m pyobfuscator -i script.py -o obfuscated.py --compress

# Using XOR for string obfuscation
python -m pyobfuscator -i script.py -o obfuscated.py --string-method xor

# Verbose output
python -m pyobfuscator -i src/ -o dist/ -v
```

### Python API

```python
from pyobfuscator import Obfuscator

# Create obfuscator with desired options
obfuscator = Obfuscator(
    rename_variables=True,
    rename_functions=True,
    rename_classes=True,
    obfuscate_strings=True,
    compress_code=False,
    remove_docstrings=True,
    name_style="random",  # or "hex", "hash"
    string_method="xor",  # recommended (or "hex", "base64" - encoding only)
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

- `xor`: XOR encryption with random key (default, recommended - actual obfuscation)
- `hex`: Hexadecimal encoding (easily reversible - encoding only)
- `base64`: Base64 encoding (easily reversible - encoding only)

> ⚠️ **Security Note:** Base64 and hex are **encoding**, not encryption. They can be trivially decoded. Use `xor` for
> actual string obfuscation. For maximum protection, use Runtime Protection which encrypts all code with AES-256-GCM.

### CLI Options

| Option                    | Description                               |
|---------------------------|-------------------------------------------|
| `-i, --input`             | Input file or directory                   |
| `-o, --output`            | Output file or directory                  |
| `-r, --recursive`         | Process directories recursively (default) |
| `--no-recursive`          | Don't process directories recursively     |
| `--no-rename-vars`        | Keep variable names                       |
| `--no-rename-funcs`       | Keep function names                       |
| `--no-rename-classes`     | Keep class names                          |
| `--no-string-obfuscation` | Keep strings readable                     |
| `--compress`              | Compress output to exec()                 |
| `--keep-docstrings`       | Preserve docstrings                       |
| `--name-style`            | Name generation style                     |
| `--string-method`         | String obfuscation method                 |
| `--exclude`               | Names to exclude from renaming            |
| `--exclude-patterns`      | File patterns to skip                     |
| `-v, --verbose`           | Show detailed output                      |

### Advanced Obfuscation Options

| Option                   | Description                                                                     |
|--------------------------|---------------------------------------------------------------------------------|
| `--control-flow`         | Enable opaque predicates and dead code injection                                |
| `--control-flow-flatten` | Enable control flow flattening (CFF) - transforms functions into state machines |
| `--numbers`              | Enable numeric literal obfuscation                                              |
| `--builtins`             | Enable builtin function call obfuscation                                        |
| `--integrity-check`      | Enable hash-based integrity verification in functions                           |
| `--all-advanced`         | Enable all advanced obfuscation features                                        |
| `--intensity`            | Intensity level (1-3) for advanced obfuscation                                  |
| `--parallel`             | Enable parallel processing for directory obfuscation                            |
| `--workers`              | Number of worker threads for parallel processing                                |

### Encryption Options (Protection)

By default, code is encrypted with AES-256-GCM. Use `--no-encrypt` for obfuscation-only mode.

| Option            | Description                                            |
|-------------------|--------------------------------------------------------|
| `--no-encrypt`    | Disable encryption (only apply name obfuscation)       |
| `--no-anti-debug` | Disable anti-debugging protection                      |
| `--license-info`  | License/author information embedded in protected files |
| `--expire-days`   | Set expiration in days from now                        |
| `--bind-machine`  | Bind code to the current machine (hardware lock)       |

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
# PyObfuscator 1.0.0 (PYD), abc123, Protected, 2026-01-30
from pyobfuscator_runtime_abc123 import __pyobfuscator__

__pyobfuscator__(__name__, __file__, b'UFlEMDAwMDEAA...')
```

## Runtime Protection API

> 🆓 **Reminder:** PyObfuscator is free. The examples below show how to add licensing restrictions to YOUR code.

### Basic Usage (No Restrictions on Your Code)

```python
from pyobfuscator import RuntimeProtector

# Basic protection (no restrictions)
protector = RuntimeProtector(license_info="My App v1.0")
protected_code, runtime_module = protector.protect_source(source_code, "app.py")
```

### With Expiration Date (Create Trial Versions of YOUR App)

```python
from datetime import datetime, timedelta
from pyobfuscator import RuntimeProtector

# Create a 30-day trial version of YOUR app
protector = RuntimeProtector(
    license_info="My App - Trial Version",
    expiration_date=datetime.now() + timedelta(days=30)
)
protected_code, runtime_module = protector.protect_source(source_code)
```

### Machine Binding (Lock YOUR Code to Specific Computers)

```python
from pyobfuscator import RuntimeProtector

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

### Full Protection (All Features for YOUR Code)

```python
from datetime import datetime, timedelta
from pyobfuscator import RuntimeProtector

# Full protection with all security features for YOUR app
protector = RuntimeProtector(
    license_info="My App - Enterprise Edition",
    expiration_date=datetime.now() + timedelta(days=365),
    allowed_machines=[RuntimeProtector.get_machine_id()],
    anti_debug=True,  # Detect debuggers
    domain_lock=["mycompany.com", "localhost"]  # For web apps
)

protected_code, runtime_module = protector.protect_source(source_code, "app.py")

# Save protected files
with open("protected_app.py", "w") as f:
    f.write(protected_code)

with open(f"pyobfuscator_runtime_{protector.runtime_id}.py", "w") as f:
    f.write(runtime_module)
```

### PYD Protection (Compiled Runtime for YOUR Code)

```python
from pyobfuscator import PydRuntimeProtector

# Create PYD protector with all features for YOUR app
protector = PydRuntimeProtector(
    license_info="My App - Premium Edition",
    expiration_date=datetime.now() + timedelta(days=365),
    allowed_machines=[PydRuntimeProtector.get_machine_id()],
    anti_debug=True
)

# Protect and build .pyd
result = protector.protect_file("app.py", "dist/", build_pyd=True)
print(f"Protected file: {result['protected']}")
print(f"PYD runtime: {result['pyd']}")
```

### Protection Options (for YOUR Code)

| Option                 | Type      | Default           | Description                                            |
|------------------------|-----------|-------------------|--------------------------------------------------------|
| `license_info`         | str       | "PyObfuscator..." | License/author info embedded in YOUR protected files   |
| `encryption_key`       | bytes     | Auto-generated    | Custom 32-byte encryption key                          |
| `expiration_date`      | datetime  | None              | Optional expiration date for time-limited licenses     |
| `allowed_machines`     | list[str] | []                | List of allowed machine IDs for hardware binding       |
| `anti_debug`           | bool      | True              | Enable multi-layer anti-debugging detection            |
| `domain_lock`          | list[str] | []                | List of allowed domain names for web apps              |
| `enable_vm_detection`  | bool      | False             | Enable VM/sandbox detection (may have false positives) |
| `enable_network_check` | bool      | False             | Enable online license validation                       |
| `license_server_url`   | str       | None              | URL for network license validation server              |

### Getting Machine ID

```python
from pyobfuscator import RuntimeProtector

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
python pyobfuscator/examples/demo.py

# Runtime protection demo
python pyobfuscator/examples/demo_runtime_protection.py

# PYD protection demo
python pyobfuscator/examples/demo_pyd_protection.py

# Obfuscate github_pr_dashboard (AST-based)
python pyobfuscator/examples/obfuscate_dashboard.py

# Protect github_pr_dashboard (PYD runtime)
python pyobfuscator/examples/protect_dashboard.py

# Run tests
python pyobfuscator/examples/tests.py
```

## Running Tests

```bash
python pyobfuscator/tests.py
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
│                    SECURITY VERIFICATION LAYERS                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1:  Self-integrity Check (SHA-256 hash verification)     │
│  Layer 2:  Anti-patching Detection (file modification check)    │
│  Layer 3:  Call Stack Verification (debugger frame detection)   │
│  Layer 4:  Anti-memory Dump (analysis tool detection)           │
│  Layer 5:  Parent Process Trace (launcher verification)         │
│  Layer 6:  Anti-hooking (built-in function verification)        │
│  Layer 7:  Environment Fingerprinting (suspicious env check)    │
├─────────────────────────────────────────────────────────────────┤
│                     PAYLOAD PROCESSING                          │
├─────────────────────────────────────────────────────────────────┤
│  ► Checksum Chain Initialization                                │
│  ► Magic Header Verification (PYO00004)                         │
│  ► SHA-256 Integrity Check                                      │
│  ► AES-256-GCM Decryption (Layer 2)                             │
│  ► XOR Decryption (Layer 1)                                     │
│  ► Metadata Parsing                                             │
├─────────────────────────────────────────────────────────────────┤
│                    LICENSE VERIFICATION                         │
├─────────────────────────────────────────────────────────────────┤
│  ► Anti-debug Check (if enabled)                                │
│  ► VM/Sandbox Detection (if enabled)                            │
│  ► Expiration Date Check                                        │
│  ► Machine ID Verification                                      │
│  ► Domain Lock Check                                            │
│  ► Network License Validation (if configured)                   │
├─────────────────────────────────────────────────────────────────┤
│                     CODE EXECUTION                              │
├─────────────────────────────────────────────────────────────────┤
│  ► Zlib Decompression                                           │
│  ► VM-based Bytecode Descrambling (35 random opcodes)           │
│  ► Final Checksum Verification                                  │
│  ► Marshal Load                                                 │
│  ► Import Hook Registration                                     │
│  ► Code Execution (via Control Flow Dispatcher)                 │
│  ► Secure Memory Cleanup                                        │
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

## Comparison with Other Solutions

### Quick Overview

| Tool                  | Type                            | License           | Price         | Protection Level |
|-----------------------|---------------------------------|-------------------|---------------|------------------|
| **PyObfuscator**      | Obfuscator + Runtime Protection | MIT (Free)        | Free          | ⭐⭐⭐⭐⭐            |
| **PyArmor**           | Obfuscator + Runtime Protection | Proprietary       | $56-$512/year | ⭐⭐⭐⭐⭐            |
| **Nuitka**            | Compiler                        | MIT (Free)        | Free          | ⭐⭐⭐              |
| **Cython**            | Compiler                        | Apache 2.0 (Free) | Free          | ⭐⭐⭐              |
| **PyInstaller**       | Packager                        | GPL               | Free          | ⭐                |
| **pyminifier**        | Obfuscator                      | MIT (Free)        | Free          | ⭐⭐               |
| **python-obfuscator** | Obfuscator                      | MIT (Free)        | Free          | ⭐⭐               |

### Detailed Feature Comparison

#### Licensing & Cost

| Feature                | PyObfuscator | PyArmor         | Nuitka | Cython     |
|------------------------|--------------|-----------------|--------|------------|
| **License**            | MIT (Free)   | Proprietary     | MIT    | Apache 2.0 |
| **Cost**               | $0           | $56-$512/year   | $0     | $0         |
| **Commercial Use**     | ✅ Free       | 💰 Paid license | ✅ Free | ✅ Free     |
| **Source Available**   | ✅ Full       | ❌ Closed        | ✅ Full | ✅ Full     |
| **No Usage Limits**    | ✅            | ❌ Tiered        | ✅      | ✅          |
| **Offline Activation** | ✅ N/A        | ❌ Requires      | ✅ N/A  | ✅ N/A      |

#### Code Obfuscation

| Feature                 | PyObfuscator | PyArmor | Nuitka | Cython | pyminifier |
|-------------------------|--------------|---------|--------|--------|------------|
| Name obfuscation        | ✅            | ✅       | ❌      | ❌      | ✅          |
| String obfuscation      | ✅ (3 modes)  | ✅       | ❌      | ❌      | ❌          |
| Control flow flattening | ✅            | ✅       | ❌      | ❌      | ❌          |
| Opaque predicates       | ✅            | ✅       | ❌      | ❌      | ❌          |
| Dead code injection     | ✅            | ❌       | ❌      | ❌      | ❌          |
| Docstring removal       | ✅            | ✅       | ✅      | ✅      | ✅          |
| Code compression        | ✅            | ❌       | ❌      | ❌      | ✅          |

#### Encryption & Bytecode Protection

| Feature               | PyObfuscator | PyArmor | Nuitka | Cython |
|-----------------------|--------------|---------|--------|--------|
| AES-256 encryption    | ✅ GCM        | ✅       | ❌      | ❌      |
| Layered encryption    | ✅ XOR+AES    | ❌       | ❌      | ❌      |
| Bytecode scrambling   | ✅            | ✅       | N/A    | N/A    |
| PBKDF2 key derivation | ✅ 100k iter  | ❌       | ❌      | ❌      |
| Per-file salt/nonce   | ✅            | ❌       | ❌      | ❌      |
| Constant blinding     | ✅            | ❌       | ❌      | ❌      |
| Native compilation    | ✅ PYD/SO     | ❌       | ✅      | ✅      |

#### Code Virtualization

| Feature             | PyObfuscator  | PyArmor | Nuitka | Cython |
|---------------------|---------------|---------|--------|--------|
| Custom VM           | ✅ Stack-based | ✅       | ❌      | ❌      |
| Randomized opcodes  | ✅ 35 opcodes  | ✅       | ❌      | ❌      |
| Self-modifying code | ✅             | ❌       | ❌      | ❌      |
| Anti-analysis in VM | ✅             | ❌       | ❌      | ❌      |
| Subroutine support  | ✅ CALL/RET    | ❌       | ❌      | ❌      |

#### Anti-Analysis & Anti-Debug (12+ Layers)

| Feature                    | PyObfuscator  | PyArmor | Nuitka | Cython |
|----------------------------|---------------|---------|--------|--------|
| Debugger detection         | ✅ Multi-layer | ✅       | ❌      | ❌      |
| Timing-based anti-debug    | ✅             | ✅       | ❌      | ❌      |
| Memory dump detection      | ✅             | ❌       | ❌      | ❌      |
| Anti-hooking               | ✅             | ❌       | ❌      | ❌      |
| Anti-patching              | ✅             | ✅       | ❌      | ❌      |
| Call stack verification    | ✅             | ❌       | ❌      | ❌      |
| Parent process check       | ✅             | ❌       | ❌      | ❌      |
| Environment fingerprinting | ✅             | ❌       | ❌      | ❌      |
| VM/Sandbox detection       | ✅             | ✅       | ❌      | ❌      |
| Profile/Trace detection    | ✅             | ✅       | ❌      | ❌      |
| Self-integrity check       | ✅             | ✅       | ❌      | ❌      |
| Debugger module detection  | ✅             | ✅       | ❌      | ❌      |

#### Licensing & DRM Features

| Feature            | PyObfuscator | PyArmor | Nuitka | Cython |
|--------------------|--------------|---------|--------|--------|
| License expiration | ✅            | ✅       | ❌      | ❌      |
| Machine binding    | ✅            | ✅       | ❌      | ❌      |
| Domain lock        | ✅            | ✅       | ❌      | ❌      |
| Network license    | ✅            | ✅       | ❌      | ❌      |
| Watermarking       | ✅            | ❌       | ❌      | ❌      |
| Honey tokens       | ✅            | ❌       | ❌      | ❌      |

#### Integrity & Defense

| Feature                     | PyObfuscator | PyArmor | Nuitka | Cython |
|-----------------------------|--------------|---------|--------|--------|
| SHA-256 checksums           | ✅            | ✅       | ❌      | ❌      |
| Checksum chains             | ✅            | ❌       | ❌      | ❌      |
| HMAC authentication         | ✅            | ❌       | ❌      | ❌      |
| Encrypted error messages    | ✅            | ❌       | ❌      | ❌      |
| Resource exhaustion defense | ✅            | ❌       | ❌      | ❌      |
| Secure memory wipe          | ✅ 5-pass     | ❌       | ❌      | ❌      |
| Decoy operations            | ✅            | ❌       | ❌      | ❌      |

#### Platform & Compatibility

| Feature               | PyObfuscator | PyArmor    | Nuitka     | Cython     |
|-----------------------|--------------|------------|------------|------------|
| Python 3.10           | ✅            | ✅          | ✅          | ✅          |
| Python 3.11           | ✅            | ✅          | ✅          | ✅          |
| Python 3.12           | ✅            | ✅          | ✅          | ✅          |
| Python 3.13+          | ✅            | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited |
| Windows               | ✅            | ✅          | ✅          | ✅          |
| Linux                 | ✅            | ✅          | ✅          | ✅          |
| macOS                 | ✅            | ✅          | ✅          | ✅          |
| Cross-platform output | ✅            | ❌          | ❌          | ❌          |

#### Output & Performance

| Feature               | PyObfuscator    | PyArmor         | Nuitka         | Cython          |
|-----------------------|-----------------|-----------------|----------------|-----------------|
| Polymorphic output    | ✅               | ❌               | ❌              | ❌               |
| Standalone executable | Via PyInstaller | Via PyInstaller | ✅ Native       | Via PyInstaller |
| Performance overhead  | ~5-15%          | ~10-20%         | +10-30% faster | +10-50% faster  |
| Output size           | Small           | Medium          | Large          | Medium          |

### When to Use What?

| Use Case                      | Recommended Tool           | Why                                     |
|-------------------------------|----------------------------|-----------------------------------------|
| **Maximum protection (free)** | **PyObfuscator**           | 50+ security features, completely free  |
| **Maximum protection (paid)** | PyArmor                    | Mature, well-tested, commercial support |
| **Performance critical**      | Nuitka or Cython           | Native compilation for speed boost      |
| **Simple distribution**       | PyInstaller + PyObfuscator | Easy packaging with protection          |
| **IP protection + speed**     | PyObfuscator (PYD mode)    | Native .pyd/.so with full protection    |
| **Budget constrained**        | **PyObfuscator**           | Enterprise features at $0 cost          |

### Cost Analysis (Annual)

| Scenario                | PyArmor | PyObfuscator | Savings     |
|-------------------------|---------|--------------|-------------|
| Personal/Hobby          | $56     | $0           | $56/year    |
| Small Team (5 devs)     | $280    | $0           | $280/year   |
| Enterprise              | $512+   | $0           | $512+/year  |
| 5-year TCO (Enterprise) | $2,560+ | $0           | **$2,560+** |

### Summary

**PyObfuscator** offers **50+ security features** completely free and open source, matching or exceeding commercial
tools like PyArmor in most categories:

- ✅ **More anti-analysis layers** (12+ vs typical 5-6)
- ✅ **Advanced encryption** (layered XOR+AES, PBKDF2)
- ✅ **Code virtualization** with self-modifying VM
- ✅ **Unique features**: Honey tokens, checksum chains, polymorphic output, watermarking
- ✅ **Better Python 3.13+ support**
- ✅ **$0 cost** - No licensing fees ever

## License

MIT License - Free for commercial and personal use.
