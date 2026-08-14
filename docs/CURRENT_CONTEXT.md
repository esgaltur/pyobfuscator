# Skjol Current Project Context

**Snapshot date:** 2026-08-14

**Repository:** `https://github.com/esgaltur/skjol.git`

**Branch:** `main`

**Version:** `2.0.2`

**Local workspace:** `C:\Users\Root\Workspace\PycharmProjects\pyobfuscator`

This document is a durable handoff for the current uncommitted work. It records
decisions, implementation changes, verification evidence, limitations, and
recommended next steps. It contains no production secrets; security fixtures
use artificial canary values.

## Working rules

- Use PowerShell on Windows; do not add Bash automation for local workflows.
- Apply SOLID, Clean Code, DRY, and compatibility-conscious design.
- Protection features require executable CLI end-to-end tests.
- Clean temporary files and build artifacts after verification.
- Do not add `Co-authored-by` or other co-author trailers to commits.
- No commit has been created for the current changes.

## Product identity and compatibility

The project was renamed from **PyObfuscator** to **Skjol** because the previous
name was already in use.

| Surface | Canonical name | Compatibility behavior |
|---|---|---|
| Repository | `esgaltur/skjol` | Local `origin` already points to the renamed repository |
| Distribution | `skjol` | The Skjol distribution includes the legacy implementation package |
| Python API | `from skjol import ...` | `pyobfuscator` imports remain available |
| Module CLI | `python -m skjol` | `python -m pyobfuscator` remains available |
| Console command | `skjol` | `pyobfuscator` remains an installed alias |
| Configuration | `skjol.json` / `skjol.toml` | Legacy `pyobfuscator.json` / `.toml` files are still discovered |
| Runtime module | `skjol_runtime_<id>.py` | Old generated artifacts are not silently rewritten |
| Runtime entry point | `__skjol__` | Protected-format magic remains stable for compatibility |

The implementation currently remains under `pyobfuscator/`. The new `skjol/`
package is the public compatibility-safe facade and module entry point. This
avoids an immediate breaking package migration while establishing the new name.

## Major implementation changes

### Reliability and protection pipeline

- Fixed malformed generated VM source involving formatting braces, names, and
  opcode reverse mappings.
- Fixed the runtime anti-patch detector matching its own signature definitions.
- Corrected encrypted directory handling so the complete obfuscation and
  encryption pipeline is applied consistently.
- Generated matching runtime modules beside nested directly executable output
  files.
- Missing explicitly requested configuration files now return a non-zero CLI
  result instead of silently falling back.
- Consolidated the release version in `pyobfuscator/_version.py`.

### Skjol rename

- Added `skjol/__init__.py`, `skjol/__main__.py`, version forwarding, and the
  runtime-protection API facade.
- Centralized public branding and compatibility names in
  `pyobfuscator/constants.py`.
- Updated package metadata, console scripts, GitHub URLs, publishing workflows,
  examples, generated headers, runtime names, documentation, citation data, and
  release guidance.
- Renamed the example configuration from `examples/pyobfuscator.json` to
  `examples/skjol.json`.

### Virtualization corrections

- Encrypted virtualized artifacts now receive the VM implementation from their
  distributed runtime instead of requiring Skjol to be installed on the target
  machine.
- The generated runtime VM memory and `STORE` semantics now match the compiler.
- Unsupported VM AST nodes now raise `NotImplementedError` during transformation
  and cause the transformer to preserve the original function. Previously, an
  unsupported call such as `len(...)` could silently compile into a function
  returning an incorrect value such as `0`.
- Regression tests cover standalone encrypted virtualization and safe fallback
  for unsupported function calls.

## Security measurement decision

The previous public claims were withdrawn:

- `Resistance Score: 0.87/1.0`
- `5.0x Structural Complexity Dispersion`
- `<10% Identifier Recovery Rate`

Those values came from one small fixture and a project-defined weighted
formula. The stored result contradicted the identifier claim, and the formula
had no validated relationship to attacker success.

`pyobfuscator/analysis/red_team.py` now exposes transparent source-level
development heuristics only. It explicitly states that these do not measure
security strength. Identifier and string denominators were corrected and are
covered by regression tests.

## Reproducible adversarial evaluation

The real measurement suite is implemented in
`benchmarks/security_evaluation.py`, documented in
`docs/SECURITY_EVALUATION.md`, and recorded in
`benchmarks/adversarial_results.json`.

### Attacker model

The attacker has all distributed Python loader/runtime files and controls the
local Python process. The suite:

1. Protects programs through the public `python -m skjol` CLI.
2. Executes each artifact normally and checks exact behavior.
3. Searches distributed Python text for artificial secrets and original names.
4. Performs Python runtime interposition at the decryption/execution boundary.
5. Records artifact hashes, environment, profiles, raw outcomes, and errors.

The suite does not claim to measure native PYD extraction, OS-level memory
dumping, external debugger/decompiler effectiveness, human effort, or AES
cryptographic strength.

### Current recorded result

Environment: CPython 3.12.10 on Windows 11. Three randomized trials were run for
three fixtures with both default and hardened profiles: 18 artifacts total.

| Observed outcome | Result | Desired | Interpretation |
|---|---:|---:|---|
| Protection completed | 18/18 | 18/18 | Good: every artifact was created |
| Normal execution passed | 18/18 | 18/18 | Good: behavior was preserved |
| Canaries recovered by static attack | 0/18 | 0/18 | Good: no plaintext canary was found in shipped Python text |
| Original identifiers recovered by static attack | 0/36 | 0/36 | Good: original names were not found in shipped Python text |
| Decrypted code objects captured dynamically | 18/18 | 0/18 | Open limitation: runtime code was observable in every trial |
| Canaries recovered dynamically | 18/18 | 0/18 | Open limitation: runtime secret values were observable in every trial |
| Original identifiers recovered dynamically | 0/36 | 0/36 | Good: original names remained transformed |

Interpretation: the tested artifacts concealed exact source canaries and names
at rest, but an attacker controlling the Python process recovered decrypted code
objects and runtime secret values in every trial. AES-256-GCM was not broken;
the information was observed after legitimate runtime decryption. Runtime
extraction is therefore an explicit open limitation for the tested pure-Python
profiles, including the hardened profile.

The zero recovery values are successful results, not failures. The findings
that require remediation are the two dynamic `18/18` recovery outcomes.

Reproduce the measurement from the repository root:

```powershell
python benchmarks\security_evaluation.py --trials 3
```

## Requirements and roadmap

`docs/REQUIREMENTS_AND_ROADMAP.md` contains testable functional and
non-functional requirements, release gates, product ideas, and phased work.

Post-quantum cryptography is a future cryptographic-agility goal:

- Protected formats should identify versioned cipher suites.
- A future profile may use standardized hybrid post-quantum key encapsulation
  and artifact signatures.
- Hybrid modes retain a reviewed classical component.
- AES-256-GCM remains the authenticated payload cipher unless evidence and
  standards justify changing it.
- Implementations require finalized standards, test vectors, compatibility
  documentation, performance measurements, and review.

## Tests and verification

Latest verification after all runtime and VM changes:

```text
190 passed in 16.90s
```

Also verified:

- `python -m skjol --version` reports `skjol 2.0.2`.
- `python -m pyobfuscator --version` reports the same compatibility identity.
- Python compilation checks pass for the new evaluation and changed runtime
  modules.
- `git diff --check` passes; Git only reports expected Windows line-ending
  conversion warnings.
- An isolated package build produced `skjol-2.0.2-py3-none-any.whl` and source
  distribution containing both `skjol` and `pyobfuscator` packages.
- Temporary package-build directories were removed.

The local environment does not currently have `flake8` installed, so the
optional local Flake8 invocation could not run. CI remains configured to install
development dependencies and lint both packages.

## Important files

| File | Purpose |
|---|---|
| `README.md` | Public identity, installation, migration, and honest security status |
| `pyproject.toml` | Skjol distribution metadata and canonical/legacy console scripts |
| `skjol/` | Canonical public package facade |
| `pyobfuscator/constants.py` | Product, CLI, config, and generated-runtime names |
| `pyobfuscator/runtime_protection.py` | Python encrypted runtime generation |
| `pyobfuscator/core/transformers/virtual_machine.py` | VM compiler and transformation safeguards |
| `tests/test_cli_protection.py` | Executable canonical and compatibility CLI tests |
| `tests/test_virtualization.py` | VM behavior, standalone runtime, and safe fallback tests |
| `tests/test_red_team_metrics.py` | Development-heuristic calculation tests |
| `tests/test_security_evaluation.py` | Real adversarial-evaluation regression tests |
| `benchmarks/security_evaluation.py` | Reproducible static/dynamic security measurement |
| `benchmarks/adversarial_results.json` | Current machine-readable attack evidence |
| `docs/SECURITY_EVALUATION.md` | Threat model, procedure, results, and limitations |
| `docs/REQUIREMENTS_AND_ROADMAP.md` | Functional/NFR contract, ideas, PQ work, and roadmap |

## Current worktree

The worktree intentionally contains a broad uncommitted change set spanning the
bug fixes, test additions, Skjol rename, documentation, packaging metadata, and
security evaluation. Preserve these changes. Use `git status --short` and
`git diff` before staging; do not reset or overwrite unrelated user work.

No commit has been created. If commits are requested later, group them
intentionally and do not add co-author trailers.

## Recommended next priorities

1. Add the adversarial evaluation to CI on Windows, Linux, and macOS and retain
   versioned reports for release comparisons.
2. Expand the fixture corpus to packages, imports, async programs, larger
   applications, and realistic secret lifetimes.
3. Add authorized external decompiler/debugger procedures and native PYD runtime
   evaluation with exact tool versions and success criteria.
4. Treat pure-Python runtime extraction as an architectural constraint. Explore
   native execution boundaries, remote licensing/key services, minimized secret
   lifetime, and server-side placement for logic that must remain confidential.
5. Add atomic output staging, build manifests, format/cipher-suite versioning,
   dry-run support, and machine-readable build reports from the roadmap.
6. Resolve the duplicate pytest configuration warning (`pytest.ini` currently
   takes precedence over `pyproject.toml`).
7. Install the full development toolchain and run Flake8, Mypy, Bandit, and
   package metadata checks before release.

## Security communication rule

Describe measured outcomes, attacker assumptions, sample sizes, environments,
and limitations. Do not publish synthetic aggregate security scores or claim
that obfuscation makes Python code impossible to recover. A successful static
test is evidence only for that static test; it does not override a successful
dynamic extraction result.
