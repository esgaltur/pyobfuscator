# Skjol Security Assurance Report
**Version:** 2.0.2
**Audit Status:** DEVELOPMENT CHECKS ONLY

## 1. Static Security Analysis (Bandit)
- **Status:** FAIL
- **Total Issues Found:** 1
- **High Severity:** 0

## 2. Cryptographic Compliance
| Primitive | Implementation | Standard |
| :--- | :--- | :--- |
| **Encryption** | AES-256-GCM | NIST SP 800-38D |
| **KDF** | PBKDF2-SHA256 | NIST SP 800-132 |
| **Entropy** | os.urandom | CSPRNG |
| **Decryption** | White-Box (LUT) | Proprietary |

## 3. Adversarial Evaluation Status

The repository now includes a reproducible Python-level extraction harness at
`benchmarks/security_evaluation.py`. It records the environment, profile,
fixture, artifact hash, normal execution result, static recovery result, and
dynamic recovery result for every trial. The full report is stored in
`benchmarks/adversarial_results.json`.

External decompilers, native-runtime extraction, OS-level memory dumping, and
human reverse-engineering effort are not yet measured. No claim that those
attacks are blocked is made.

Current stored run: 18/18 artifacts passed normal execution, static canary
search recovered 0/18, and Python runtime interposition captured decrypted code
objects and runtime canaries in 18/18. Runtime extraction is therefore an open
limitation for the tested Python-runtime profiles.

## 4. Integrity Proofs
The test suite includes property-based and executable CLI cases. These tests
cover specific supported behavior and do not prove equivalence for every valid
Python program.

---
*This report is generated automatically by the High-Assurance Security Auditor.*
