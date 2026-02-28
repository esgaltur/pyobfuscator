# Contributing to PyObfuscator

First off, thank you for considering contributing to PyObfuscator! It's people like you that make PyObfuscator such a great tool for the community.

## 🚀 Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/pyobfuscator.git
    cd pyobfuscator
    ```
3.  **Set up a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  **Install dependencies**:
    ```bash
    pip install -e .[all,dev]
    ```
5.  **Install pre-commit hooks**:
    ```bash
    pre-commit install
    ```

## 🛠️ Development Workflow

*   **Refactoring / Features**: We follow Hexagonal Architecture. New transformers should be registered in `pyobfuscator/core/registry.py` and implement the `BaseTransformer` interface.
*   **Testing**: We aim for 100% coverage.
    *   Run unit tests: `pytest tests/test_pyobfuscate.py`
    *   Run architectural tests: `pytest tests/test_architecture.py`
    *   Run property-based tests: `pytest tests/test_properties.py`
*   **Linting**: Code must pass `black`, `isort`, `flake8`, and `mypy` checks.

## 🤝 Pull Request Process

1.  Create a new branch for your feature or bugfix.
2.  Ensure tests pass and coverage is maintained.
3.  Update the documentation if you've added new features or changed APIs.
4.  Submit a Pull Request against the `main` branch.
5.  Two maintainers must approve the PR before it is merged.

## 🛡️ Security Contributions

If you find a security vulnerability, **please do not open an issue**. Instead, follow the instructions in our [Security Policy](SECURITY.md).

---

By contributing, you agree that your contributions will be licensed under its [MIT License](LICENSE).
