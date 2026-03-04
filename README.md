# PyObfuscator v2.0.2

[![CI](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml/badge.svg)](https://github.com/esgaltur/pyobfuscator/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Red Team Score](https://img.shields.io/badge/Red_Team_Resistance-0.87/1.0-green.svg)](#security-metrics)

**PyObfuscator** is a principal-grade Python code protection framework designed for high-security backend systems and proprietary algorithm protection. It moves beyond simple renaming to provide multi-layer defense-in-depth using instruction-level virtualization, white-box cryptography, and control flow flattening.

## 🛡️ Key Security Features

PyObfuscator employs a **Hexagonal Architecture** to deliver industry-leading protection layers:

- **Instruction-Level Virtualization**: Compiles sensitive Python logic into a proprietary bytecode executed by a custom, randomized stack-based VM.
- **White-Box Cryptography (WBC)**: LUT-based symmetric encryption where the key is "baked" into randomized substitution tables, eliminating contiguous 32-byte secrets from memory.
- **Control Flow Flattening (CFF)**: Reconstructs functions as state-machine dispatchers, removing all original sequential logic signatures.
- **Polymorphic String Engine**: Structurally diverse inline decoding (Generator expressions, Map-Lambdas, List Comprehensions) with randomized session-based keys.
- **Unified .pyd Pipeline**: Seamless integration with Cython to compile critical protection layers into native machine code.
- **Advanced Anti-Analysis**: 7+ layers of detection for Debuggers, VM/Sandboxes, Memory Dumpers, and Function Hooking.

## 🚀 Strategic Use Cases

| Use Case | Recommended Configuration |
| :--- | :--- |
| **Enterprise SaaS Licensing** | Virtualization + Machine Binding + Network Check |
| **Proprietary AI/Algo Trading** | CFF + WBC + .pyd Compilation |
| **Microservice Hardening** | Polymorphic Strings + Integrity Checks |
| **Security Research** | Red Team Metrics + Semantic Fuzzing |

## 📊 Security Metrics (Red Teaming)

We quantify our security using an automated adversary suite that measures:
- **Resistance Score: 0.87/1.0** (Hardened Tier)
- **Structural Complexity Dispersion**: 5.0x increase in logical branching.
- **Identifier Recovery Rate**: < 10% for protected symbols.

## 🛠️ Quick Start

### Installation
```bash
pip install pyobfuscator
```

### Basic Obfuscation
```bash
pyobfuscator obfuscate -i ./my_app -o ./dist
```

### High-Security Protection
```bash
pyobfuscator obfuscate -i secret_script.py -o protected.py --virtualize --whitebox --cff --intensity 3
```

## 📖 Documentation

- [Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md) - Architectural deep-dive
- [Strategic Use Cases](docs/USE_CASES.md) - Implementation patterns
- [Whitepaper](docs/WHITEPAPER.md) - Theoretical basis and performance research
- [Red Team Metrics](pyobfuscator/analysis/red_team.py) - Security quantification logic

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to PyObfuscator.

## 🔒 Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md).

---
**Document Version:** 2.0.2  
**Copyright © 2026 Dmitrij Sosnovic. Released under MIT License.**
