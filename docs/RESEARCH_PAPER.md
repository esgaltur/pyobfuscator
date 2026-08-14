# A Multi-Layer Virtualization and White-Box Cryptography Framework for Enhancing Intellectual Property Protection in Interpreted Languages

**Author:** Dmitrij Sosnovic  
**Version:** 2.0.2  
**Date:** March 2026  
**Keywords:** Software Protection, Obfuscation, Virtualization, White-Box Cryptography, Python Security

---

## Abstract

As high-value intellectual property (IP) increasingly moves to interpreted environments like Python, unauthorized analysis and copying remain practical risks. This paper introduces **Skjol v2.0.2**, a layered framework that includes **Instruction-Level Virtualization (ILV)** and **White-Box Cryptography (WBC)**. Sensitive logic can be translated to randomized bytecode and executed by a software-defined virtual machine. Current evaluation includes executable correctness tests, small synthetic performance workloads, source-level visibility heuristics, and a reproducible Python runtime-interposition attack. The attack recovered decrypted code and canaries in all 18 current trials. No universal attacker-resistance score or independent security validation is claimed.

---

## 1. Introduction

The dominance of Python in data science and backend engineering has created a critical security gap: the transparency of Python bytecode. Standard tools like `uncompyle6` and `Ghidra` can reconstruct high-level source code from distributed binaries with near-perfect fidelity. This transparency poses an existential threat to companies distributing proprietary logic on-premise or in untrusted cloud environments.

Existing solutions often rely on simple "packing" or "encryption" which merely delays the attacker until the runtime key is extracted from memory. Skjol v2.0.2 proposes a paradigm shift: **The code is the environment.** By virtualizing the instructions and baking the keys into the logic, we eliminate the binary "secret/non-secret" boundary.

## 2. Methodology: Multi-Barrier Defense

Skjol implements a hexagonal architecture comprising six distinct security layers:

### 2.1 Instruction-Level Virtualization (ILV)
We implement a stack-based virtual machine (VM) within the Python runtime. The compiler transforms Abstract Syntax Tree (AST) nodes into a proprietary Instruction Set Architecture (ISA). 
- **Randomized Opcodes**: Every build generates a unique mapping between opcodes and operations (e.g., `0xAF` may mean `ADD` in Build 1 and `XOR` in Build 2).
- **Control Flow Dispatch**: The logic is executed via an indirect jump table, breaking the linear execution pattern visible to debuggers.

### 2.2 White-Box Cryptography (WBC)
To solve the "contiguious key in RAM" problem, we implemented a Look-Up Table (LUT) based symmetric engine.
- **Key Injection**: The 256-bit AES key is expanded into a series of randomized substitution boxes.
- **Path Transformation**: Decryption is treated as a path through a randomized state machine. An attacker dumping the memory sees 4KB of randomized integers but never the 32-byte secret key.

### 2.3 Distributed Integrity Web (DIW)
We introduce non-local dependencies where function $f(x)$ verifies the side-effects of an unrelated function $g(y)$. This prevents "surgical patching" where an attacker attempts to disable a single security check.

## 3. Security Analysis

### 3.1 Adversarial Threat Model
We assume a **Tier 3 Adversary**:
- Full access to the protected binary.
- Capability to perform dynamic instrumentation (Frida/X64dbg).
- Access to symbolic execution engines (Z3/angr).

### 3.2 Development heuristics

The repository measures visible source strings, unchanged renameable
identifiers, branch-node counts, and text entropy. These are regression signals,
not probabilities of resisting an attacker. A previous aggregate formula used
project-selected weights and a five-times branch threshold without empirical
validation. Its numeric resistance scores have been withdrawn.

## 4. Experimental Evaluation

### 4.1 Performance Benchmarks
Testing across diverse workloads (Computational, IO-Bound, Recursive) yielded the following average execution overheads:
- **Basic Tier**: 1.00x (No measurable impact)
- **Hardened Tier**: 1.05x (5% impact)
- **Maximum Tier**: 1.15x (15% impact)

These synthetic measurements do not establish suitability for a particular
latency-sensitive production system. Users should benchmark their own workloads.

### 4.2 Semantic Verification
The test suite includes **Property-Based Testing** (Hypothesis) and CLI tests
that execute generated artifacts. Passing tests provide regression evidence for
the covered cases; they do not prove semantic equivalence for all Python programs.

## 5. Conclusion

Skjol v2.0.2 combines multiple techniques intended to raise the cost of
analyzing Python code. Establishing how much they impede specific adversaries
requires broader reproducible experiments and independent review. Future work
will strengthen the threat model, evaluation corpus, and adversarial testing.

---
**Copyright © 2026 Dmitrij Sosnovic. Released under MIT License.**
