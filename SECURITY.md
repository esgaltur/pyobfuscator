# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in PyObfuscate, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainers with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Resolution Timeline**: Depends on severity (critical: days, high: 1-2 weeks, medium/low: next release)

### Scope

Security issues we're interested in:
- Encryption weaknesses
- Key/data exposure
- Protection bypass methods
- Runtime security issues
- Dependency vulnerabilities

### Out of Scope

- Theoretical attacks requiring physical access
- Social engineering
- Issues in dependencies (report to upstream)
- "Security" of obfuscated code (obfuscation is not encryption)

### Safe Harbor

We will not pursue legal action against security researchers who:
- Follow responsible disclosure guidelines
- Make good faith efforts to avoid data destruction
- Do not exploit vulnerabilities beyond proof of concept

## Security Features

PyObfuscate includes 50+ security features. See [README.md](README.md) for details.

Thank you for helping keep PyObfuscate secure!
