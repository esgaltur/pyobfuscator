# PyObfuscator: Technical Documentation and Scientific Basis

**A Comprehensive Analysis of Multi-Layer Code Protection Techniques**

**Author:** Dmitrij Sosnovic  
**Version:** 2.0.0  
**Date:** February 2026

---

## Table of Contents

1. [Introduction and Motivation](#1-introduction-and-motivation)
2. [Theoretical Foundations](#2-theoretical-foundations)
3. [Cryptographic Foundations](#3-cryptographic-foundations)
4. [Obfuscation Theory (v2.0 Advanced)](#4-obfuscation-theory)
5. [Implementation Details (Hexagonal Architecture)](#5-implementation-details)
6. [Security Proofs and Analysis](#6-security-proofs-and-analysis)
7. [Experimental Evaluation](#7-experimental-evaluation)
8. [Formal Verification](#8-formal-verification)
9. [Bibliography](#9-bibliography)

---

## 1. Introduction and Motivation

### 1.1 The Python Security Challenge (v2.0 Evolution)

While v1.0 focused on static obfuscation and runtime encryption, v2.0 addresses the threat of **automated symbolic execution** and **manual dynamic analysis**. The core challenge in Python remains its introspection capabilities, which v2.0 weaponizes against the attacker through polymorphic traps and distributed dependencies.

### 1.2 Threat Taxonomy (v2.0 Update)

| Threat Level | Adversary | Tools | Time Budget | v2.0 Defense |
|--------------|-----------|-------|-------------|--------------|
| T1 - Casual | End users | uncompyle6 | Minutes | Encrypted Bytecode |
| T2 - Intermediate | Developers | pdb, regex scripts | Hours | Polymorphic Strings |
| T3 - Advanced | Security researchers | IDA, Symbolic Execution | Days | Distributed Integrity Web |
| T4 - Expert | State actors | Custom JIT hooks | Weeks | Integrated .pyd Pipeline |

---

## 4. Obfuscation Theory (v2.0 Advanced)

### 4.1 Polymorphic String Decryptors

**Definition 4.1.1:** A polymorphic decryptor is a functional transformation where a static data constant $D$ is replaced by a unique, randomized recovery function $F_i$ such that $F_i(S) = D$, where $S$ is a session-specific secret.

In PyObfuscator v2.0, every string literal generates a unique AST subgraph:
1.  **Randomized Keying:** Each string uses a different XOR key and varied encoding (inline bytes, hex-slices, or base64-derivation).
2.  **Variable Name Entropy:** Local variable names within the recovery lambda are derived from a cryptographically secure 256-bit `TransformationContext` secret.
3.  **Syntactic Diversity:** The decoding loop can be represented as a list comprehension, a generator expression, or a recursive call, chosen at random.

### 4.2 Distributed Integrity Web (DIW)

**Definition 4.2.1:** A Distributed Integrity Web is a non-local dependency graph where the execution of Function $A$ depends on a side-effect (checkpoint) produced by the prior execution of Function $B$, where $A$ and $B$ are semantically unrelated.

**Mechanism:**
-   **Checkpoints:** Transformers inject "integrity markers" (hidden local variables or global state updates) into legitimate functions.
-   **Verification Cross-Links:** Subsequent functions verify these markers using opaque predicates. 
-   **Failure Cascades:** If an attacker patches out an anti-debugging routine, the missing checkpoint causes a "delayed crash" in a completely different part of the application, making the root cause difficult to trace.

### 4.3 Honey-Pot Identifiers

PyObfuscator v2.0 injects "Enticing Identifiers" (e.g., `_AWS_SECRET_KEY`, `ADMIN_PASSWORD`) into the module namespace. These are implemented as `property` descriptors or proxy objects that:
1.  **Silent Fail:** Triggers a `RuntimeError` only when accessed via `getattr()` or a debugger's "inspect" command.
2.  **Entropy Poisoning:** Corrupts the global state if modified, leading to decryption failures in legitimate code.

---

## 5. Implementation Details (Hexagonal Architecture)

### 5.1 Hexagonal (Ports & Adapters) Design

Version 2.0 introduces a strict separation between the **Obfuscation Domain** and **Infrastructure Adapters**.

```
    Adapters (Infrastructure)          Core (Domain)
    ┌───────────────────────┐        ┌───────────────────────┐
    │  CLI / Config Builder │ ───>   │  Obfuscator Service   │
    └───────────────────────┘        └──────────┬────────────┘
                                                │
    ┌───────────────────────┐        ┌──────────▼────────────┐
    │  File System Adapter  │ <───   │ Transformation Context│
    └───────────────────────┘        └──────────┬────────────┘
                                                │
    ┌───────────────────────┐        ┌──────────▼────────────┐
    │  Cython / GCC Toolchain│ <───   │ Transformation Pipeline│
    └───────────────────────┘        └───────────────────────┘
```

**Benefits:**
-   **Testability:** Transformers are tested against the `TransformationContext` in isolation without needing a file system.
-   **Extensibility:** New transformers (e.g., a "LLM-based stealth renamer") can be plugged into the `TransformerRegistry` without modifying the core orchestrator.

### 5.2 The Unified .pyd Pipeline

The integrated native compilation pipeline works as follows:
1.  **AST Pre-processing:** Applies name mangling and DIW checks.
2.  **Cythonization:** Transpiles the obfuscated AST into optimized C code.
3.  **Native Linkage:** Invokes the local compiler (MSVC/GCC) to produce a platform-specific binary.
4.  **Runtime Encapsulation:** Wraps the binary entry point in an encrypted AES-256-GCM bootstrap script.

---

## 6. Security Analysis (v2.0)

### 6.1 Resilience to Symbolic Execution

By using session-blinded constants and non-linear arithmetic in opaque predicates (e.g., $x \oplus key$ where $key$ is generated at runtime), we significantly increase the search space for SMT solvers like Z3 used in automated de-obfuscation tools.

### 6.2 Comparison of Protection Levels

| Feature | Static Analysis | Dynamic Analysis | Automated Unpacking |
|---------|-----------------|------------------|---------------------|
| v1.0 (XOR Strings) | ⚠️ Vulnerable | ❌ Blocked | ⚠️ Partial |
| v2.0 (Polymorphic) | ✅ Protected | ✅ Protected | ✅ Blocked |
| v2.0 (+ .pyd) | ⭐ Elite | ⭐ Elite | ⭐ Elite |

---

**Document Version:** 2.0.0  
**Last Updated:** February 2026  
**Copyright © 2026 Dmitrij Sosnovic. Released under MIT License.**
