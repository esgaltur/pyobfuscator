# Skjol Requirements and Roadmap

This document defines the product contract for Skjol and turns future
ideas into testable outcomes. `IMPROVEMENTS.md` remains the engineering design
backlog; this document focuses on user-visible behavior and release priorities.

## Scope and Product Goal

Skjol protects Python applications while preserving their observable
behavior. Its primary workflow is a CLI-driven pipeline:

1. Read and validate a Python file or project.
2. Apply configured AST transformations.
3. Encrypt compiled code when runtime protection is enabled.
4. Emit runnable output and every runtime dependency it needs.
5. Report partial or complete failures with a non-zero exit code.

Protection raises the cost of analysis; it does not make Python code impossible
to recover. Security documentation and CLI messages must avoid absolute claims.

## Functional Requirements

Status values are **Current**, **Next**, and **Future**.

| ID | Requirement | Acceptance criteria | Status |
|---|---|---|---|
| FR-001 | Protect one Python file through the CLI | `python -m skjol obfuscate -i app.py -o dist/app.py` returns 0; the output hides source literals/names and executes with equivalent output | Current |
| FR-002 | Protect a Python directory recursively | Every included `.py` file is processed, relative paths are preserved, and an error in any file makes the command return non-zero | Current |
| FR-003 | Keep runtime dependencies deployable | Every directory containing a directly runnable protected file receives the matching runtime module | Current |
| FR-004 | Support obfuscation without encryption | `--no-encrypt` emits valid transformed Python that runs without a generated runtime | Current |
| FR-005 | Preserve program behavior | Supported inputs produce the same return values, stdout, exceptions, imports, and public API behavior before and after protection | Current |
| FR-006 | Preserve cross-file name consistency | Definitions, imports, and references use one shared mapping during project processing | Current |
| FR-007 | Allow compatibility exclusions | Users can preserve names, entry points, frameworks, public APIs, and excluded file patterns through CLI/config options | Current |
| FR-008 | Load JSON and TOML configuration | Explicit missing or invalid configuration fails before output is written; documented CLI values override configuration values | Next |
| FR-009 | Provide licensing controls | Expiration, machine binding, domain restrictions, and anti-debug options are enforced consistently across file and directory workflows | Current |
| FR-010 | Analyze projects before protection | `analyze` reports frameworks, entry points, public APIs, packages, warnings, and recommendations in text or JSON | Current |
| FR-011 | Generate starter configuration | `init` creates JSON or TOML configuration and refuses accidental overwrite unless `--force` is supplied | Current |
| FR-012 | Produce a machine-readable build report | An optional JSON report lists source, output, applied profile, skipped files, runtime ID, hashes, warnings, and failures | Next |
| FR-013 | Validate output atomically | Failed processing leaves the previous output intact and does not publish a partially protected release | Next |
| FR-014 | Support dry-run planning | `--dry-run` shows selected files, exclusions, detected compatibility risks, and expected outputs without writing files | Next |
| FR-015 | Make protection reproducible when requested | A user-supplied seed produces stable name mappings and artifacts for the same source, configuration, Python version, and tool version | Future |
| FR-016 | Support incremental project builds | Unchanged files may be reused only when source, configuration, dependency mapping, and runtime identity match | Future |
| FR-017 | Version the protected artifact format | The loader rejects incompatible formats with a clear message and supports a documented migration/compatibility policy | Next |
| FR-018 | Offer native-runtime protection | `--pyd` produces a native runtime when prerequisites exist and gives an actionable error or explicit fallback when they do not | Next |
| FR-019 | Support cryptographic agility and post-quantum migration | Protected formats identify their cipher suite; future releases can add hybrid post-quantum key encapsulation and signatures without silently breaking existing artifacts | Future |

## Non-Functional Requirements

| ID | Quality attribute | Measurable target |
|---|---|---|
| NFR-001 | Correctness | All supported protection profiles pass CLI-based semantic-equivalence tests for files, packages, imports, exceptions, async code, generators, decorators, and context managers |
| NFR-002 | Reliability | The full automated suite has no known failures on supported Python versions; generated artifacts are executed as part of CI, not only parsed or inspected |
| NFR-003 | Compatibility | Support Python 3.10 through 3.13 on Windows, Linux, and macOS; publish a tested-version matrix for every release |
| NFR-004 | Security | Use authenticated encryption for protected payloads, unique per-payload nonces/salts, explicit format versioning, and no plaintext source in protected loaders |
| NFR-005 | Security assurance | Every security claim maps to a test, benchmark, threat-model section, or external review; unsupported absolute claims are prohibited |
| NFR-006 | Performance | Track protection time, output size, startup time, and runtime slowdown against an unobfuscated baseline; release gates reject unexplained regressions over 20% |
| NFR-007 | Scalability | A 1,000-file project completes without unbounded memory growth; directory collection and transformation remain deterministic in scope |
| NFR-008 | Usability | Invalid paths, configs, combinations, and dependencies return non-zero with a concise actionable error; `--help` examples use real supported flags |
| NFR-009 | Maintainability | Public functions are typed, protection stages have focused responsibilities, duplicated file/directory logic is extracted, and new transformers use the registry/pipeline interfaces |
| NFR-010 | Testability | New defects require a failing regression test; protection features require at least one subprocess-based CLI E2E test that executes generated output |
| NFR-011 | Portability | Project automation and documented local commands work in PowerShell on Windows; platform-specific runtime behavior is isolated and tested |
| NFR-012 | Observability | Verbose and JSON reports identify the failing stage and file without logging keys, decrypted bytecode, secrets, or protected source |
| NFR-013 | Backward compatibility | Minor releases do not silently change CLI meaning, config keys, or protected-format support; breaking changes require a major version and migration notes |
| NFR-014 | Supply-chain safety | Dependencies are minimized, version constraints are documented, release artifacts include hashes, and CI performs dependency and static-security checks |
| NFR-015 | Post-quantum readiness | Post-quantum algorithms are introduced only from finalized, reviewed standards; hybrid modes retain a classical component, use test vectors, and document compatibility and performance costs |
| NFR-016 | Empirical security evaluation | Release candidates run versioned static and dynamic attack procedures against every supported profile for at least three randomized trials; reports include environment, artifact hashes, raw outcomes, limitations, and no synthetic aggregate security score |

## Product Ideas

| Idea | User value | Effort | Suggested priority |
|---|---|---:|---|
| Protection manifest | Makes releases auditable by recording input/output hashes, runtime IDs, profiles, and tool/Python versions | Medium | High |
| Compatibility scanner | Detects dynamic imports, reflection, pickling, decorators, framework hooks, and public names likely to break before writing output | Medium | High |
| Named protection profiles | Replaces long flag lists with reviewed presets such as `compatible`, `balanced`, and `hardened` | Low | High |
| Atomic staging and publish | Prevents incomplete `dist` directories after one file fails | Medium | High |
| Differential behavior lab | Executes original and protected programs with the same generated inputs and compares results, output, and exceptions | High | High |
| Secure mapping vault | Optionally exports encrypted symbol mappings for support and crash diagnosis without shipping them with artifacts | Medium | Medium |
| CI policy command | `skjol verify` checks manifests, format versions, plaintext leakage, runtime presence, and execution smoke tests | Medium | Medium |
| Plugin SDK | Lets third parties register transformers with declared ordering, compatibility, and configuration schemas | High | Medium |
| Incremental protection cache | Speeds large builds while invalidating dependents when shared name mappings change | High | Medium |
| External key/licensing provider | Allows production deployments to retrieve or unwrap keys from a license service or KMS rather than embedding all policy locally | High | Medium |
| Reproducible-build mode | Helps CI compare artifacts and diagnose regressions while keeping randomized mode as the production default | Medium | Medium |
| IDE/config schema support | JSON Schema validation and completion reduce invalid configuration and improve discoverability | Low | Medium |
| Hybrid post-quantum protection profile | Adds standardized post-quantum key encapsulation and artifact signatures alongside the existing authenticated-encryption pipeline | High | Medium |

## Roadmap

### Phase 0 — Reliability Baseline (2.0.x)

- Keep the full suite green on all currently supported Python versions.
- Require executable CLI E2E tests for single-file and nested-directory
  protection.
- Validate malformed JSON/TOML and reject unknown or incompatible options.
- Unify duplicated pytest configuration and publish a Windows/Linux CI matrix.
- Add tests for Unicode paths, spaces in paths, empty projects, syntax errors,
  excluded files, and output directories located inside the input tree.
- Run the adversarial extraction suite in CI and treat unexpected changes in
  correctness or attack outcomes as review-required findings.

Exit gate: no known critical protection-path defect; generated output is
executed in CI on every supported platform.

### Phase 1 — Predictable CLI and Builds (2.1)

- Add named protection profiles and a documented config schema.
- Add `--dry-run` and a JSON build report.
- Stage output atomically and preserve a previous successful build on failure.
- Add a compatibility scanner with actionable exclusions/recommendations.
- Define protected-format compatibility and deprecation policies.

Exit gate: a user can preview, run, audit, and reproduce the scope of a
protection build without reading source code or internal logs.

### Phase 2 — Project-Scale Protection (2.2)

- Add a protection manifest and `verify` command.
- Expand cross-file tests to packages, namespace packages, dynamic imports,
  async applications, and common frameworks.
- Add safe incremental caching with dependency-aware invalidation.
- Benchmark 100-, 500-, and 1,000-file projects and publish regression trends.
- Make native-runtime prerequisite and fallback behavior explicit.

Exit gate: large projects can build repeatedly with measurable performance,
auditable artifacts, and no stale name mappings.

### Phase 3 — Security Assurance and Extensibility (3.0)

- Publish a versioned threat model for each protection profile.
- Separate payload construction, runtime generation, policy enforcement, and
  deployment packaging behind stable interfaces.
- Add external key/licensing provider interfaces and documented offline/failure
  policies.
- Introduce versioned cipher suites and prototype a hybrid post-quantum profile
  for key encapsulation and signed artifact manifests. AES-256-GCM remains the
  authenticated payload cipher unless evidence and standards justify a change.
- Introduce a transformer plugin SDK with ordering and compatibility contracts.
- Commission an independent cryptographic/runtime review and address findings
  before declaring the format stable.

Exit gate: security claims are evidence-backed, extension points are stable,
and protected-format changes follow a published compatibility policy.

## Release Acceptance Checklist

A release is ready only when:

- All functional requirements marked **Current** have passing automated tests.
- The full test suite passes on the supported platform matrix.
- At least one clean-environment smoke test installs the built wheel, protects a
  file through the CLI, and executes the result.
- Performance and artifact-size results are compared with the previous release.
- Documentation examples are executed or otherwise checked against `--help`.
- No temporary plaintext, key material, build directory, or partial output is
  left behind after success or failure.
- Changelog entries identify format, CLI, configuration, and compatibility
  changes.
