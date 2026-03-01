# PyObfuscator v2.0

[![CI](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml/badge.svg)](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security: 60+ Features](https://img.shields.io/badge/Security-60%2B%20Features-green.svg)](https://github.com/esgaltur/pyobfuscator#features)
[![White Paper](https://img.shields.io/badge/White%20Paper-Available-blue.svg)](docs/WHITEPAPER.md)
[![Documentation](https://img.shields.io/badge/Docs-Technical-green.svg)](docs/TECHNICAL_DOCUMENTATION.md)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive, **100% free and open source** Python code protection framework with enterprise-grade security.
PyObfuscator v2.0 implements a **Hexagonal (Ports & Adapters) Architecture** delivering advanced features including
**Polymorphic Decryptors**, **Distributed Integrity Webs**, and **Native PYD Compilation**.

## 🚀 What's New in v2.0

- **Hexagonal Architecture**: Production-grade modularity with clean separation of concerns
- **Polymorphic String Engine**: Every string gets a unique, randomized inline decryption function
- **Distributed Integrity Web**: Functions verify each other's integrity in a tangled web
- **Honey-Pot Identifiers**: Automated injection of trap variables that crash debuggers
- **Unified .pyd Pipeline**: Native C-compilation integrated directly into main obfuscation flow
- **Enhanced CLI**: Full E2E workflow support with `--encrypt`, `--protect`, and `--obfuscate` flags
- **Runtime Protection**: Anti-debug, integrity checks, and environment fingerprinting built-in

> **Core Philosophy**: Protection is the primary feature. Obfuscation handles variables, but the real power is in **hiding and encrypting the actual code**.

## 📚 Documentation

- **[White Paper](docs/WHITEPAPER.md)** - Comprehensive overview of the protection framework
- **[Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md)** - Detailed scientific basis and implementation details
- **[Citation File](CITATION.cff)** - For academic citations
- **[BibTeX References](docs/references.bib)** - Bibliography for academic papers

## ⚡ Quick Start

```bash
# Install
git clone https://github.com/esgaltur/pyobfuscator.git
cd pyobfuscator && pip install -e .

# Full protection: obfuscate + encrypt + protect
pyobfuscator -i script.py -o protected/ --obfuscate --encrypt --protect

# Run protected code
python protected/script.py
```

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
# Clone the repository
git clone https://github.com/esgaltur/pyobfuscator.git
cd pyobfuscator

# Install in development mode
pip install -e .
```

For PYD protection, install Cython:

```bash
pip install cython
```

## Usage

### Command Line

```bash
# Full protection pipeline (recommended)
pyobfuscator -i script.py -o ./dist --obfuscate --encrypt --protect

# Obfuscate with PYD compilation (Gold Standard)
pyobfuscator obfuscate -i script.py -o ./dist --pyd

# Enable distributed integrity checks and honeypots
pyobfuscator obfuscate -i src/ -o ./dist --integrity-check

# Standard obfuscation only
pyobfuscator obfuscate -i script.py -o obfuscated.py

# Encryption only
pyobfuscator -i script.py -o encrypted.py --encrypt

# Runtime protection only
pyobfuscator -i script.py -o protected.py --protect
```

### Python API

```python
from pyobfuscator import Obfuscator
from pyobfuscator.runtime_protection import RuntimeProtector
from pyobfuscator.crypto import CryptoEngine

# Full protection pipeline
source = 'def hello(): print("Secret message")'

# Step 1: Obfuscate
obfuscator = Obfuscator(
    use_pyd_compilation=True,  # The ultimate protection
    integrity_checks=True,     # Distributed integrity web
    string_method="polymorphic", # Randomized unique decryptors
    intensity=3                # Maximum obfuscation depth
)
obfuscated = obfuscator.obfuscate_source(source)

# Step 2: Encrypt
crypto = CryptoEngine(key=b"your-secret-key-32bytes-long!!")
encrypted = crypto.encrypt(obfuscated.encode())

# Step 3: Add Runtime Protection
protector = RuntimeProtector()
protected = protector.protect(source)
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

## 📖 Citation

If you use PyObfuscator in academic research, please cite:

```bibtex
@software{pyobfuscator2026,
  author = {Sosnovic, Dmitrij},
  title = {PyObfuscator: A Multi-Layer Defense Framework for Python Code Protection},
  version = {2.0.0},
  year = {2026},
  url = {https://github.com/esgaltur/pyobfuscator}
}
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to PyObfuscator.

## 🔒 Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md).

