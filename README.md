# PyObfuscator v2.0

[![CI](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml/badge.svg)](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/pyobfuscator.svg)](https://badge.fury.io/py/pyobfuscator)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security: 60+ Features](https://img.shields.io/badge/Security-60%2B%20Features-green.svg)](https://github.com/esgaltur/pyobfuscator#features)
[![White Paper](https://img.shields.io/badge/White%20Paper-Available-blue.svg)](docs/WHITEPAPER.md)
[![Documentation](https://img.shields.io/badge/Docs-Technical-green.svg)](docs/TECHNICAL_DOCUMENTATION.md)

A comprehensive, **100% free and open source** Python code obfuscation library with enterprise-grade runtime protection.
PyObfuscator v2.0 introduces a **Hexagonal (Ports & Adapters) Architecture** and elite-tier security features like 
**Polymorphic Decryptors** and **Distributed Integrity Webs**.

## 🚀 What's New in v2.0 (Elite Edition)

- **Hexagonal Architecture**: Refactored for production-grade modularity and extensibility.
- **Polymorphic String Engine**: Every string gets a unique, randomized inline decryption function. No two obfuscation runs are the same.
- **Distributed Integrity Web**: Functions now check each other's integrity in a tangled web, making isolated bypasses impossible.
- **Honey-Pot Identifiers**: Automated injection of fake trap variables (e.g., `AWS_SECRET_KEY`) that trigger crashes if accessed.
- **Unified .pyd Pipeline**: The "Gold Standard" native C-compilation is now integrated directly into the main obfuscation flow.

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

## Features

### Core Obfuscation

- **Name Obfuscation**: Renames variables, functions, and classes to unreadable names
- **Polymorphic String Obfuscation**: (New Default) Unique, randomized decoding logic for every string literal.
- **Legacy String Encoding**: Optional support for base64, hex, or XOR encoding strategies.
- **Code Compression**: Optionally compresses code into a single exec() statement
- **Docstring Removal**: Removes docstrings to reduce code size and readability
- **Comment Removal**: Comments are automatically removed during AST processing
- **Transformation Pipeline**: Modular engine allows chaining dozens of transformations in sequence.

### Runtime Protection

- **Encrypted Bytecode**: Code compiled to bytecode and encrypted before distribution
- **PYD Compilation**: (The Gold Standard) Compile runtime to .pyd/.so (C extension) for maximum protection.
- **Polymorphic Runtime**: Each protection generates unique obfuscated code with different variable names
- **Import Hooks**: Custom module loading system for protected imports

### Encryption

- **AES-256-GCM**: Military-grade encryption with authentication
- **Layered Encryption**: XOR + AES double encryption for defense in depth
- **PBKDF2 Key Derivation**: 100,000 iterations for key strengthening
- **Bytecode Scrambling**: XOR-based bytecode obfuscation before encryption
- **Per-file Salt/Nonce**: Unique cryptographic parameters for each file
- **Constant Blinding**: Magic numbers hidden through XOR operations using randomized session secrets.

### Code Virtualization

- **Stack-based VM**: Custom virtual machine with 35 randomized opcodes
- **Randomized Opcode Table**: Opcode mappings change with each protection
- **Self-modifying Code**: VM bytecode modifies itself during execution
- **Anti-analysis in VM**: Detects tracing and corrupts output if analyzed
- **Subroutine Support**: CALL/RET instructions for complex transformation programs

### Anti-Analysis Protection (15+ Layers)

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
| 13    | **Honey-Pot Identifiers**      | **(NEW)** Trap variables that crash debuggers  |
| 14    | **Distributed Integrity**      | **(NEW)** Inter-dependent function verification |
| 15    | **Opaque Predicates v2**       | **(NEW)** Session-blinded opaque conditions     |

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
- **Distributed Verification**: Function A verifies Function B, creating a "Web of Trust".
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

## Installation

```bash
pip install pyobfuscator
```

For PYD protection, install Cython:

```bash
pip install cython
```

## Usage

### Command Line

```bash
# NEW: Obfuscate with integrated PYD compilation (Gold Standard)
pyobfuscator obfuscate -i script.py -o ./dist --pyd

# NEW: Enable distributed integrity checks and honeypots
pyobfuscator obfuscate -i src/ -o ./dist --integrity-check

# Standard obfuscation
pyobfuscator obfuscate -i script.py -o obfuscated.py

# Single file (short form)
pyobfuscator -i script.py -o obfuscated.py
```

### Python API

```python
from pyobfuscator import Obfuscator

# Create elite-tier obfuscator
obfuscator = Obfuscator(
    use_pyd_compilation=True,  # The ultimate protection
    integrity_checks=True,     # Distributed integrity web
    string_method="polymorphic", # Randomized unique decryptors
    intensity=3                # Maximum obfuscation depth
)

# Obfuscate source code
source = 'def hello(): print("Secret")'
obfuscated = obfuscator.obfuscate_source(source)
```

## Comparison with Other Solutions

| Feature                 | PyObfuscator v2.0 | PyArmor | Nuitka |
|-------------------------|-------------------|---------|--------|
| **Cost**                | **$0 (MIT)**      | $56+    | $0     |
| **Polymorphic Output**  | ✅ Yes             | ❌ No    | ❌ No   |
| **Honey-Pot Traps**     | ✅ Yes             | ❌ No    | ❌ No   |
| **Integrity Web**       | ✅ Yes             | ❌ No    | ❌ No   |
| **Native Compilation**  | ✅ integrated .pyd | ❌ No    | ✅ Yes  |
| **Open Source**         | ✅ Full            | ❌ No    | ✅ Full |

## License

MIT License - Free for commercial and personal use.
