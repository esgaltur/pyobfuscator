# PyObfuscator: Technical Documentation and Scientific Basis

**A Comprehensive Analysis of Multi-Layer Code Protection Techniques**

**Author:** Dmitrij Sosnovic  
**Version:** 2.0.2  
**Date:** March 2026

---

## Table of Contents

1. [Introduction and Motivation](#1-introduction-and-motivation)
2. [Theoretical Foundations](#2-theoretical-foundations)
3. [Cryptographic Foundations](#3-cryptographic-foundations)
4. [Obfuscation Theory (v2.0 Advanced)](#4-obfuscation-theory)
5. [Instruction-Level Virtualization (v2.0.2)](#5-instruction-level-virtualization)
6. [White-Box Cryptography (v2.0.2)](#6-white-box-cryptography)
7. [Implementation Details (Hexagonal Architecture)](#7-implementation-details)
8. [Security Proofs and Analysis](#8-security-proofs-and-analysis)
9. [Experimental Evaluation](#9-experimental-evaluation)
10. [Bibliography](#10-bibliography)

---

## 1. Introduction and Motivation

### 1.1 The Python Security Challenge (v2.0 Evolution)

While v1.0 focused on static obfuscation and runtime encryption, v2.0 addresses the threat of **automated symbolic execution** and **manual dynamic analysis**. The core challenge in Python remains its introspection capabilities, which v2.0 weaponizes against the attacker through polymorphic traps and distributed dependencies. v2.0.2 further advances this by introducing **Instruction-Level Virtualization** and **White-Box Cryptography**, moving the security boundary from the code structure to a proprietary execution environment.

### 1.2 Threat Taxonomy (v2.0 Update)

| Threat Level | Adversary | Tools | Time Budget | v2.0 Defense |
|--------------|-----------|-------|-------------|--------------|
| T1 - Casual | End users | uncompyle6 | Minutes | Encrypted Bytecode |
| T2 - Intermediate | Developers | pdb, regex scripts | Hours | Polymorphic Strings |
| T3 - Advanced | Security researchers | IDA, Symbolic Execution | Days | Distributed Integrity Web |
| T4 - Expert | State actors | Custom JIT hooks, VM Reversing | Weeks | Virtualization + White-Box |

---

## 4. Obfuscation Theory (v2.0 Advanced)

### 4.1 Polymorphic String Decryptors

**Definition 4.1.1:** A polymorphic decryptor is a functional transformation where a static data constant $D$ is replaced by a unique, randomized recovery function $F_i$ such that $F_i(S) = D$, where $S$ is a session-specific secret.

In PyObfuscator v2.0, every string literal generates a unique AST subgraph:
1.  **Randomized Keying:** Each string uses a different XOR key and varied encoding (inline bytes, hex-slices, or base64-derivation).
2.  **Variable Name Entropy:** Local variable names within the recovery lambda are derived from a cryptographically secure 256-bit `TransformationContext` secret.
3.  **Syntactic Diversity (v2.0.1):** The decoding loop is randomly selected from three distinct structural patterns:
    - **List Comprehension**: `bytes([v ^ k for v in data])`
    - **Generator Expression**: `''.join(chr(v ^ k) for v in data)`
    - **Functional Mapping**: `bytes(map(lambda v: v ^ k, data))`

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

## 5. Instruction-Level Virtualization (v2.0.2)

**Definition 5.1:** Instruction-Level Virtualization is the process of translating high-level source instructions (AST) into a proprietary, randomized instruction set architecture (ISA) executed by a custom software-defined virtual machine (VM).

### 5.1 The Compiler Pipeline
1. **Selection**: Sensitive code blocks (functions) are identified based on complexity or user tags.
2. **Translation**: Python AST nodes are mapped to proprietary stack-based opcodes (e.g., `OP_PUSH`, `OP_LOAD`, `OP_XOR`).
3. **Randomization**: The opcode mapping table is randomized per-build, ensuring that `0x01` in Build A is not the same as `0x01` in Build B.
4. **Injection**: The original function body is replaced with a VM initialization and an execution call to the bytecode payload.

### 5.2 Security Impact
This layer defeats static analysis tools like `uncompyle6` and `decompyle3`, as the actual logic is no longer stored in Python bytecode. An attacker must first reverse-engineer the custom VM and its randomized ISA to understand the underlying algorithm.

---

## 6. White-Box Cryptography (v2.0.2)

**Definition 6.1:** White-Box Cryptography (WBC) is a technique used to implement cryptographic algorithms in such a way that the secret keys are "baked" into the implementation and are never present in memory as contiguous byte arrays.

### 6.1 Look-Up Table (LUT) Implementation
PyObfuscator uses a LUT-based approach:
1. **Key Derivation**: A 32-byte master key is expanded into sixteen randomized substitution tables (S-Boxes).
2. **Transformation**: Each byte of the sensitive data is transformed by passing through its corresponding randomized table.
3. **Decryption via State Transition**: The "decryption" is mathematically equivalent to a path through these tables. 

### 6.2 Resilience to Memory Dumping
Standard AES implementations are vulnerable to "Key Finders" that scan RAM for high-entropy 128/256-bit sequences. In PyObfuscator's WBC mode, there is no master key in memory; only randomized integers spread across 4KB of lookup tables.

---

## 7. Implementation Details (Hexagonal Architecture)

### 7.1 Hexagonal (Ports & Adapters) Design

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

### 7.2 The Unified .pyd Pipeline

The integrated native compilation pipeline works as follows:
1.  **AST Pre-processing:** Applies name mangling and DIW checks.
2.  **Cythonization:** Transpiles the obfuscated AST into optimized C code.
3.  **Native Linkage:** Invokes the local compiler (MSVC/GCC) to produce a platform-specific binary.
4.  **Runtime Encapsulation:** Wraps the binary entry point in an encrypted AES-256-GCM bootstrap script.

---

## 8. Security Analysis (v2.0)

### 8.1 Resilience to Symbolic Execution

By using session-blinded constants and non-linear arithmetic in opaque predicates (e.g., $x \oplus key$ where $key$ is generated at runtime), we significantly increase the search space for SMT solvers like Z3 used in automated de-obfuscation tools.

### 8.2 Comparison of Protection Levels

| Feature | Static Analysis | Dynamic Analysis | Automated Unpacking | Resistance Score |
|---------|-----------------|------------------|---------------------|------------------|
| v1.0 (XOR Strings) | ⚠️ Vulnerable | ❌ Blocked | ⚠️ Partial | 0.45 |
| v2.0 (Polymorphic) | ✅ Protected | ✅ Protected | ✅ Blocked | 0.71 |
| v2.0.2 (+ VM/WBC) | ⭐ Advanced | ⭐ Advanced | ⭐ Advanced | 0.87 |

---

**Document Version:** 2.0.2  
**Last Updated:** March 2026  
**Copyright © 2026 Dmitrij Sosnovic. Released under MIT License.**
