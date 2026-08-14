# Skjol v2.0.2

[![CI](https://github.com/esgaltur/skjol/actions/workflows/ci.yml/badge.svg)](https://github.com/esgaltur/skjol/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Skjol** is a Python code protection framework for proprietary applications and algorithms. It combines AST transformation, authenticated encryption, runtime protection, instruction-level virtualization, white-box cryptography, and control-flow flattening. These defenses raise the cost of analysis; they cannot make recoverable Python code impossible to reverse engineer.

## 🛡️ Key Security Features

Skjol uses a **Hexagonal Architecture** to compose its protection layers:

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

## Security evaluation status

The repository includes a reproducible black-box evaluation that protects
programs through the public CLI, executes the resulting artifacts, and performs
static and dynamic extraction attacks. The dynamic attack interposes Python's
`eval`, `marshal.loads`, and `exec` functions to test whether decrypted code and
runtime canaries can be recovered. Results are reported as observed attack
success rates, never as a universal security score.

In the current recorded run, all 18 artifacts executed correctly and none
exposed the canary through static text search. The dynamic attack captured the
decrypted code object and recovered the canary in all 18 artifacts, including
the hardened profile. This identifies runtime extraction as an open security
limitation. Here, zero static recoveries is the desired result; the dynamic
`18/18` recovery outcomes are what require mitigation.

Earlier documentation presented results from one small source-level fixture as
a `0.87` resistance score. That claim was not independently validated and has
been withdrawn. The old source-level measurements remain available only as
development heuristics.

Security claims should instead be supported by reproducible multi-fixture
benchmarks, documented environments and attack procedures, raw results, and
independent review. See the [security evaluation](docs/SECURITY_EVALUATION.md)
for the threat model, reproduction command, results, and interpretation.

## 🛠️ Quick Start

### Installation
```powershell
pip install skjol
```

### Full Protection (Default)

The `obfuscate` command applies AST obfuscation and AES-256-GCM runtime
encryption by default. It accepts either a Python file or a directory.

```powershell
python -m skjol obfuscate -i .\my_app -o .\dist
```

Each output directory containing a protected Python file also contains its
matching `skjol_runtime_<id>.py`. Distribute that runtime alongside the
protected file. To apply AST transformations without encryption, add
`--no-encrypt`.

### Experimental Rust Native Runtime

The opt-in Rust backend moves authenticated decryption, metadata parsing,
marshal decoding, and code dispatch behind a PyO3 extension. Install its build
dependencies and ensure `rustc` and Cargo are available:

```powershell
pip install "skjol[rust]"
python -m skjol obfuscate -i .\app.py -o .\dist\app.py --runtime rust
```

The output contains the Python launcher and a matching
`skjol_runtime_<id>.pyd` (or `.so` on Unix). Keep them together. The current
proof of concept has been exercised on Windows 11 with CPython 3.12; the
portable `python` backend remains the default. Expiration, machine binding,
domain locking, white-box encryption, and code virtualization currently fail
closed when the Rust backend is selected.

A focused native trial executed successfully and prevented the repository's
Python-level `eval`, `exec`, and `marshal.loads` hooks from capturing the
protected code object or canary. This does not prevent a native debugger,
memory inspection, binary patching, or extraction of the embedded offline root
key. See the [native runtime design and sequence diagrams](docs/RUST_NATIVE_RUNTIME_CONSIDERATION.md).

### Advanced Protection

```powershell
python -m skjol obfuscate -i .\secret_script.py -o .\protected.py --code-virtualization --whitebox --control-flow-flatten --intensity 3
```

Disable anti-debugging only when the target environment requires tracing or
instrumentation:

```powershell
python -m skjol obfuscate -i .\app.py -o .\dist\app.py --no-anti-debug
```

## Rename and compatibility

The project and distribution were renamed from **PyObfuscator** to **Skjol**.
New installations should use `pip install skjol`, `python -m skjol`, the `skjol`
console command, and `from skjol import ...`. Installing Skjol also provides the
legacy `pyobfuscator` Python package and console command as compatibility aliases.
Existing configuration files named `pyobfuscator.json` or `pyobfuscator.toml`
remain readable, while newly generated configuration uses the `skjol` name.

## ✅ Testing

The end-to-end tests invoke the public CLI, execute generated output, and use
pytest-managed temporary directories for automatic cleanup.

```powershell
python -m pytest -q tests\test_cli_protection.py
python -m pytest -q
```

## 📖 Documentation

- [Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md) - Architectural deep-dive
- [Requirements and Roadmap](docs/REQUIREMENTS_AND_ROADMAP.md) - Testable product requirements, new ideas, and release phases
- [Security Evaluation](docs/SECURITY_EVALUATION.md) - Reproducible static and dynamic attack outcomes
- [Rust Native Runtime Plan](docs/RUST_NATIVE_RUNTIME_CONSIDERATION.md) - Architecture, implementation milestones, tests, and release gates
- [Strategic Use Cases](docs/USE_CASES.md) - Implementation patterns
- [Whitepaper](docs/WHITEPAPER.md) - Theoretical basis and performance research
- [Evaluation Heuristics](pyobfuscator/analysis/red_team.py) - Source-level development measurements and limitations

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to Skjol.

## 🔒 Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md).

---
**Document Version:** 2.0.2  
**Copyright © 2026 Dmitrij Sosnovic. Released under MIT License.**
