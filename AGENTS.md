# AGENTS.md - AI Agent Guidelines

## Project Overview

**PyObfuscator** - A Python code protection tool featuring obfuscation, encryption, and runtime protection.

**Repository**: https://github.com/esgaltur/pyobfuscator.git  
**Branch**: main

---

## Core Principles

### Software Engineering Standards

| Principle | Application |
|-----------|-------------|
| **SOLID** | Actively apply in all implementations |
| **Clean Code** | Write readable, maintainable code |
| **Design Patterns** | Use where they add value |
| **DRY** | Never duplicate code - always extract and reuse |

### Code Quality Requirements

- Code must be clean, understandable, and easy to maintain
- All changes must be extensible without breaking existing functionality
- Prefer composition over inheritance where appropriate

---

## Development Workflow

1. **Plan First** - Create a comprehensive plan before implementation
2. **Think Step-by-Step** - Validate assumptions at each stage
3. **Test Changes** - Verify functionality before committing
4. **Clean Up** - Remove temporary files and artifacts

---

## Environment Configuration

### Platform

- **OS**: Windows
- **Shell**: PowerShell (❌ No Bash scripts)

### Command Output Handling

When direct output capture fails:

```powershell
# 1. Redirect output to file
command 2>&1 | Out-File -FilePath temp_output.txt

# 2. Read and process
$content = Get-Content temp_output.txt

# 3. Clean up
Remove-Item temp_output.txt
```

---

## Project Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `Obfuscator` | Variable and code structure obfuscation |
| `Encryptor` | Code encryption with runtime decryption |
| `RuntimeProtector` | Anti-debug, integrity checks, protection |
| `CLI` | Command-line interface for all features |

### Directory Structure

```
pyobfuscator/        # Source code
tests/               # Test suites
├── test_e2e_integration.py    # E2E integration tests
├── test_cli_*.py              # CLI-based tests
```

---

## Testing Requirements

### E2E Testing Philosophy

Tests should invoke the tool **as end users would** - through CLI flags, not internal APIs.

```powershell
# Example: Full protection pipeline
python -m pyobfuscator --obfuscate --encrypt --protect <target>
```

### Test Scenarios

1. **Obfuscate** → Verify execution
2. **Encrypt** → Verify runtime decryption
3. **Protect** → Verify RuntimeProtector integration
4. **Full Pipeline** → Obfuscate + Encrypt + Protect → Execute → Cleanup

### Key Requirement

> Protection must **always** be available. Obfuscation handles variables, but the primary feature is **hiding and encrypting the real code**.

---

## CLI Flags Reference

| Flag | Purpose |
|------|---------|
| `--obfuscate` | Apply variable/code obfuscation |
| `--encrypt` | Encrypt code with runtime decryption |
| `--protect` | Enable RuntimeProtector features |
| `--output` | Specify output path |

---

## Agent Instructions Summary

✅ **DO**:
- Follow SOLID principles
- Write clean, maintainable code
- Test via CLI (E2E approach)
- Use PowerShell for scripting
- Plan before implementing

❌ **DON'T**:
- Duplicate code
- Use Bash scripts
- Skip testing
- Leave temporary files
