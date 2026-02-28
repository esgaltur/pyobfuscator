# Security Policy

## Supported Versions

Only the latest stable version of PyObfuscator receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x     | :x:                |

## Reporting a Vulnerability

As an obfuscation and protection tool, we take security extremely seriously. 

**If you discover a way to bypass the protection (e.g., automated de-obfuscation, key extraction, anti-debug bypass), please report it responsibly.**

Please **DO NOT** create a public issue. Instead, send a detailed report to:
`dmitriy@sosnovich.com`

### What to include in your report:
1.  **Type of bypass**: (e.g., Static analysis bypass, Dynamic bypass).
2.  **Reproduction script**: A small Python script that demonstrates the bypass.
3.  **Environment details**: OS, Python version, and any tools used (e.g., IDA, Ghidra, custom scripts).

We aim to acknowledge all reports within 48 hours and provide a fix or mitigation within 14 days.

## Kerckhoffs's Principle

We believe in the [Kerckhoffs's Principle](https://en.wikipedia.org/wiki/Kerckhoffs%27s_principle): the security of our protection should not depend on the secrecy of the obfuscator's source code. 

If you find a bypass that works even when the attacker knows how the obfuscator works, that is a high-priority bug for us!
