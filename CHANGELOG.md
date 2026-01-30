# Changelog

All notable changes to PyObfuscator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-31

### 🎉 Initial Release

PyObfuscator 1.0.0 is the first stable release of this comprehensive, **100% free and open source** Python code obfuscation library with enterprise-grade runtime protection.

### ✨ Core Features

#### Code Obfuscation
- **Name Obfuscation**: Intelligent renaming of variables, functions, and classes to unreadable identifiers
- **String Obfuscation**: Multiple encoding methods (Base64, Hex, XOR) for string literals
- **Code Compression**: Optional compression into single exec() statements
- **Docstring & Comment Removal**: Automatic cleanup for reduced code size
- **Configurable Obfuscation**: Fine-grained control over what gets obfuscated

#### Runtime Protection
- **Encrypted Bytecode**: AES-256-GCM encryption for compiled bytecode
- **PYD Compilation**: Compile protection runtime to C extensions (.pyd/.so)
- **Polymorphic Runtime**: Unique obfuscated code generation for each protection
- **Custom Import Hooks**: Secure module loading system for protected code

#### Encryption & Security
- **AES-256-GCM**: Military-grade authenticated encryption
- **Layered Encryption**: XOR + AES double encryption strategy
- **PBKDF2 Key Derivation**: 100,000 iterations for key strengthening
- **Bytecode Scrambling**: XOR-based obfuscation before encryption
- **Per-file Cryptographic Parameters**: Unique salt/nonce for each file
- **Constant Blinding**: Magic numbers hidden through XOR operations

#### Code Virtualization
- **Stack-based Virtual Machine**: Custom VM with 35 randomized opcodes
- **Randomized Opcode Tables**: Different opcode mappings per protection
- **Self-modifying Code**: VM bytecode that modifies itself during execution
- **Anti-analysis in VM**: Detects tracing and corrupts output
- **Subroutine Support**: CALL/RET instructions for complex transformations

#### Anti-Analysis Protection (12+ Layers)
1. **Self-integrity Check**: Runtime module hash verification
2. **Anti-patching**: Detects modifications to runtime files
3. **Call Stack Verification**: Validates execution context
4. **Anti-memory Dump**: Detects CheatEngine, x64dbg, IDA, Ghidra, etc.
5. **Parent Process Trace**: Verifies launcher legitimacy
6. **Anti-hooking**: Detects replaced built-in functions
7. **Environment Fingerprinting**: Detailed environment verification
8. **Timing-based Anti-debug**: Detects debugger slowdown
9. **Debugger Module Detection**: Checks for pydevd, debugpy, pdb
10. **Environment Variable Check**: Detects PYTHONDEBUG, PYCHARM_DEBUG, etc.
11. **VM/Sandbox Detection**: Detects VMware, VirtualBox, QEMU, Hyper-V
12. **Profile/Trace Check**: Detects sys.settrace/setprofile hooks

#### Control Flow Protection
- **Control Flow Dispatch**: Indirect function calls through dispatch tables
- **State Machine**: Execution flow verification via state transitions
- **Code Splitting**: Distributed decryption logic
- **Opaque Predicates**: Complex conditions to confuse static analysis
- **Dead Code Injection**: Realistic but never-executed code paths
- **Fake Error Paths**: Decoy error handlers triggered on analysis

#### Integrity & Authentication
- **SHA-256 Checksums**: Payload integrity verification
- **Checksum Chains**: Incremental hash verification
- **HMAC Authentication**: Cryptographic data authentication
- **Encrypted Error Messages**: XOR-encrypted error strings

#### Licensing & DRM Features
> These features allow you to add licensing to YOUR protected applications.

- **License Expiration**: Time-limited execution (trial periods)
- **Machine Binding**: Hardware-specific locking (CPU, MAC, disk serial)
- **Domain Lock**: Hostname/domain restrictions
- **Network License**: Online license validation support
- **Watermarking**: Hidden tracking identifiers
- **Honey Tokens**: Fake keys for tamper detection

### 🛠️ Command Line Interface

```bash
# Basic obfuscation
pyobfuscator obfuscate input.py -o output.py

# Runtime protection with AES encryption
pyobfuscator protect input.py -o protected.py --use-crypto

# PYD protection (compile to C extension)
pyobfuscator protect input.py -o protected.py --use-pyd

# Machine-bound protection
pyobfuscator protect input.py -o protected.py --use-crypto --bind-machine

# Trial version (30-day expiration)
pyobfuscator protect input.py -o protected.py --use-crypto --expire-days 30
```

### 📦 Python API

```python
from pyobfuscator import Obfuscator, RuntimeProtector, PydRuntimeProtector

# Basic obfuscation
obfuscator = Obfuscator(obfuscate_names=True, obfuscate_strings=True)
obfuscated_code = obfuscator.obfuscate_file("input.py")

# Runtime protection
protector = RuntimeProtector(use_encryption=True)
protector.protect_file("input.py", "protected.py")

# PYD protection
pyd_protector = PydRuntimeProtector()
pyd_protector.protect_file("input.py", "protected.py")
```

### 📚 Documentation

- **White Paper**: Comprehensive overview of the protection framework
- **Technical Documentation**: Detailed scientific basis and implementation
- **Citation File**: For academic citations (CITATION.cff)
- **BibTeX References**: Bibliography for academic papers

### 🔧 Technical Specifications

- **Python Support**: Python 3.10, 3.11, 3.12, 3.13+
- **Platform**: Cross-platform (Windows, Linux, macOS)
- **License**: MIT License (100% free and open source)
- **Dependencies**: 
  - Core: No dependencies
  - Optional crypto: `cryptography>=41.0.0`
  - Optional PYD: `cython>=3.0.0`

### 🎯 Use Cases

- **Commercial Software Protection**: Protect proprietary Python applications
- **Trial/Demo Versions**: Create time-limited or feature-limited demos
- **IP Protection**: Safeguard algorithms and business logic
- **License Enforcement**: Implement hardware binding and expiration
- **Anti-piracy**: Multiple layers of anti-analysis and anti-tampering
- **Compliance**: Meet software protection requirements

### 📊 Performance

- **Fast Obfuscation**: Processes thousands of lines per second
- **Minimal Runtime Overhead**: <5% performance impact for most workloads
- **Efficient Encryption**: Optimized AES-GCM implementation
- **Scalable**: Handles projects from single files to large codebases

### 🧪 Testing

- Comprehensive test suite with 100+ test cases
- Cross-file obfuscation testing
- Runtime protection verification
- Anti-debug mechanism validation
- Encryption/decryption cycle tests

### 📝 Examples

The `examples/` directory includes:
- `demo.py`: Basic obfuscation examples
- `demo_runtime_protection.py`: Runtime protection demonstrations
- `demo_pyd_protection.py`: PYD compilation examples
- `obfuscate_dashboard.py`: Interactive obfuscation dashboard
- `protect_dashboard.py`: Interactive protection dashboard

### 🔐 Security Notes

- **No Backdoors**: Complete source code available for audit
- **No Telemetry**: No data collection or phone-home features
- **Transparent**: All protection mechanisms documented
- **Community-driven**: Open source development model

### 🚀 Getting Started

```bash
# Install from PyPI
pip install pyobfuscator

# Install with all optional dependencies
pip install pyobfuscator[all]

# Verify installation
pyobfuscator --version
```

### 🤝 Contributing

We welcome contributions! See CONTRIBUTING.md for guidelines.

### 📄 License

MIT License - See LICENSE file for details.

### 🙏 Acknowledgments

Thanks to the Python community and all contributors who made this project possible.

### 🔗 Links

- **Homepage**: https://github.com/esgaltur/pyobfuscator
- **Documentation**: https://github.com/esgaltur/pyobfuscator#readme
- **Issues**: https://github.com/esgaltur/pyobfuscator/issues
- **PyPI**: https://pypi.org/project/pyobfuscator/

---

## Version History

- **1.0.0** (2026-01-31): Initial stable release

[1.0.0]: https://github.com/esgaltur/pyobfuscator/releases/tag/v1.0.0
