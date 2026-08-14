# Rust Native Runtime Decision and Implementation Plan

## Status

**Decision: approved for staged implementation. Implementation has not started.**

Skjol will first build a bounded Windows/CPython 3.12 proof of concept. The
native runtime will become a supported opt-in backend only after it passes the
correctness, attack-resistance, cleanup, and packaging gates in this document.
Native code must not be described as making local software impossible to
inspect.

The current portable Python runtime will remain available for users who value
simple packaging and broad compatibility. The existing Cython `--pyd` path
will remain compatible while the Rust backend is developed and evaluated.

## Why consider Rust?

The current adversarial evaluation can replace Python-level `eval`, `exec`, and
`marshal.loads`. It captures the decrypted code object and runtime canary in all
18 tested artifacts. This succeeds without breaking AES-256-GCM because the
attacker observes the payload after its legitimate decryption.

A Rust native extension could move payload verification, decryption, decoding,
and dispatch out of monkey-patchable Python functions. It could call CPython's
C API directly and avoid returning decrypted payload bytes to Python code. This
would directly address the boundary used by the current attack.

Rust is a good candidate because it provides:

- native machine-code output with no distributed Rust source required;
- memory-safe abstractions for most implementation code;
- explicit control over the lifetime of decrypted buffers and keys;
- mature Python bindings through PyO3;
- cross-platform Python wheel builds through Maturin; and
- a smaller, more focused native component than rewriting the complete Skjol
  transformation pipeline.

The value is a higher extraction cost and a smaller Python-visible attack
surface. It is not perfect confidentiality on a machine controlled by the
attacker.

## Proposed scope

The first native component should be a runtime loader, not a rewrite of Skjol.
The existing Python CLI, AST transformations, profiles, and build orchestration
can remain in Python.

The native runtime would be responsible for:

1. parsing a versioned binary artifact envelope;
2. verifying the artifact's integrity and optional signature;
3. obtaining or unwrapping the per-artifact content key;
4. decrypting the payload with authenticated encryption;
5. decoding the protected code without Python-level `marshal.loads`;
6. evaluating the code through a direct CPython API boundary;
7. returning only the program result or exception to Python; and
8. clearing temporary plaintext and key buffers as soon as possible.

The generated Python launcher should expose only a narrow call such as
`skjol_runtime.run(artifact)`. It should never receive the decrypted bytecode,
source, encryption key, or decoded code object.

## First-release decisions

These decisions remove ambiguity from the initial implementation:

| Area | Decision |
|---|---|
| Initial target | Windows x86-64 with CPython 3.12 |
| Integration style | New runtime backend; no rewrite of the Python CLI or AST pipeline |
| CLI | Add `--runtime {python,cython,rust}`; keep `--pyd` as a deprecated alias for `cython` |
| Default | `python` remains the default until the native backend completes the release matrix |
| Native build behavior | `--runtime rust` requires a successful native build and never silently falls back |
| Python ABI | Version-specific CPython extension for the first release; no `abi3` promise |
| Payload cipher | AES-256-GCM only; the native backend does not use the current non-AES fallback |
| Payload format | New versioned native format; do not overload the existing Python or Cython magic values |
| Metadata | Strict UTF-8 JSON parsed with `serde_json`; never `repr` or `eval` |
| Deployment | One generated native runtime per protection build, copied beside every directly runnable protected file |
| Offline key model | A random per-build root key is compiled into the native runtime for the first milestone |
| Stronger key model | A later provider interface supplies short-lived keys without embedding a durable root key |
| Rust source distribution | Rust templates ship with Skjol, but protected output contains only the compiled extension and launcher |
| Failure behavior | Invalid format, wrong Python version, failed authentication, unsupported policy, or missing toolchain returns a non-zero CLI result |

The first offline key model improves resistance to Python-level interception
but does not make the key secret from native reverse engineering. This
limitation must remain visible in CLI documentation and security reports.

## Non-goals for the first release

- Rewriting Skjol's transformations or CLI in Rust.
- Automatically translating arbitrary Python business logic into Rust.
- Claiming resistance to native debuggers or process-memory inspection.
- Adding post-quantum cryptography to solve runtime extraction.
- Providing remote licensing or key delivery in the first proof of concept.
- Supporting cross-compilation from one operating system to every target.
- Removing the portable Python or existing Cython runtime backends.

## What it would improve

### Resistance to Python-level interposition

The current benchmark hooks ordinary Python functions. A native loader that
does not call those hookable functions should prevent this exact extraction
method. This must be demonstrated by a test rather than assumed.

### Smaller plaintext exposure window

Rust can keep decrypted data in a short-lived native buffer, process smaller
units on demand, and erase buffers after use. This reduces accidental retention
in Python objects, module globals, tracebacks, and garbage-collected memory.

### Better runtime isolation

Artifact parsing, cipher-suite selection, integrity checks, and policy
validation can be implemented behind one narrow interface. That makes the
security boundary easier to review and reduces the amount of generated loader
code that an attacker can patch at the Python level.

### Stronger foundation for remote keys

The native runtime could request a short-lived, scoped key from a licensing or
key service and unwrap it only inside native code. This does not make the key
unextractable, but it avoids shipping one durable master key in every Python
artifact and enables expiration and revocation.

## What it would not solve

A native runtime still runs on the attacker's computer. A sufficiently capable
attacker can attach a native debugger, hook CPython or operating-system APIs,
dump process memory, patch the Rust library, or capture values after the
protected code uses them.

In particular:

- embedding a permanent AES key in the Rust binary only relocates the key;
- calling back into Python's `marshal.loads`, `eval`, or `exec` from Rust leaves
  the current attack boundary substantially intact;
- clearing buffers reduces exposure time but cannot erase values already
  copied into CPython objects;
- anti-debugging checks can increase effort but are not a trust boundary;
- post-quantum cryptography does not prevent runtime observation; and
- code that must remain secret cannot be guaranteed confidential while it is
  executed entirely on an attacker-controlled client.

The strongest protection for high-value secrets or algorithms remains keeping
them server-side and exposing a narrow authenticated API.

## Suggested protection profiles

| Profile | Runtime | Intended tradeoff |
|---|---|---|
| `portable` | Pure Python | Easiest deployment; explicitly vulnerable to Python-level runtime extraction |
| `native` | Rust extension | Raises the cost of Python hooking and casual inspection; requires platform wheels |
| `remote` | Server-side sensitive operations | Strongest confidentiality boundary; requires connectivity and service operation |

A future `compiled` option could move selected business logic itself into Rust.
That is stronger than wrapping only the loader because the sensitive algorithm
is no longer distributed as Python bytecode. It also requires manual porting or
a deliberately limited compilation model and should be evaluated separately.

## Candidate architecture

```text
Skjol CLI (Python)
    |
    | builds encrypted, versioned artifact
    v
Python launcher
    |
    | passes encrypted artifact only
    v
Rust native runtime (.pyd/.so)
    |-- validate header and policy
    |-- derive an artifact key from the build root key
    |-- authenticate and decrypt
    |-- decode code object natively
    |-- execute through CPython C API
    `-- clear temporary native buffers
```

The artifact envelope should include an explicit format version, cipher-suite
identifier, nonce, authenticated metadata, payload length, and integrity or
signature data. Metadata must use a strict binary or structured format; it must
not be interpreted with `eval`.

Suggested Rust components for a proof of concept are:

- `pyo3` for the Python extension boundary;
- `aes-gcm` for the existing authenticated payload cipher;
- `hkdf` and `sha2` for per-artifact key derivation from the build root key;
- `zeroize` for best-effort clearing of sensitive native buffers;
- `serde` and `serde_json` for strict, versioned artifact metadata;
- `flate2` for decompression inside the native boundary;
- `base64` for decoding the encrypted launcher payload; and
- `maturin` for local development and wheel production.

Dependencies would need normal supply-chain review, version pinning, license
review, and security update procedures before production use.

## CPython compatibility and packaging

PyO3 extensions normally use a CPython-version-specific ABI. PyO3 also supports
Python's Limited API through `abi3`, which can reduce the number of wheels, but
that API restricts which CPython functions and optimizations are available.

The direct evaluation function `PyEval_EvalCode` is part of CPython's Stable
ABI. However, `PyMarshal_ReadObjectFromString` is not documented as part of the
Stable ABI, and Python documents that marshalled code objects are not compatible
across Python versions. Therefore, a proof of concept using Skjol's current
marshalled-code payload should initially expect version-specific wheels.

Maturin can build and package PyO3 extensions as Python wheels. The expected
release matrix would cover each supported Python version and operating-system
architecture. `abi3` should be adopted only after confirming that the complete
runtime path uses the Limited API and that the compatibility tradeoff is
acceptable.

## Native artifact format v1

The native backend will use a new binary envelope with magic `SKJNR001`. Integer
fields use little-endian encoding. Parsing must reject unknown versions,
unknown flags, reserved fields that are not zero, inconsistent lengths,
oversized fields, trailing data, and truncated data before allocating large
buffers.

| Field | Size | Meaning |
|---|---:|---|
| Magic | 8 bytes | `SKJNR001` |
| Format version | 2 bytes | Initially `1` |
| Header length | 2 bytes | Enables future compatible header extension |
| Cipher suite | 2 bytes | `1` means AES-256-GCM with HKDF-SHA256 |
| Flags | 2 bytes | All unassigned bits must be zero |
| Python major | 1 byte | Required CPython major version |
| Python minor | 1 byte | Required CPython minor version |
| Reserved | 2 bytes | Must be zero |
| Metadata length | 4 bytes | Length of JSON inside decrypted plaintext |
| Ciphertext length | 8 bytes | Includes the 16-byte GCM tag |
| Nonce | 12 bytes | Random and unique for this derived artifact key |
| Artifact ID | 16 bytes | Random ID used as HKDF salt and manifest identity |
| Ciphertext and tag | variable | Encrypted metadata followed by compressed marshalled code |

The complete fixed header is authenticated as AES-GCM additional authenticated
data. The per-artifact key is derived with HKDF-SHA256 from the per-build root
key, the 16-byte artifact ID, and the context string `skjol-native-v1`.

The decrypted plaintext is:

```text
UTF-8 JSON metadata (metadata length bytes)
zlib-compressed CPython marshal data (remaining bytes)
```

The JSON schema initially contains `created`, `license`, `python_version`,
`source_hash`, `expiration`, `machines`, `domains`, and `anti_debug`. Unknown
required fields or invalid field types fail closed. Optional future fields need
an explicit compatibility rule. The unauthenticated SHA-256 checksum used by
the older format is unnecessary because AES-GCM authenticates the header and
ciphertext.

## Repository structure

The implementation should use the following boundaries:

```text
pyobfuscator/
|-- artifacts/
|   |-- __init__.py
|   |-- native_format.py       # Header/schema encoding and validation
|   `-- native_builder.py      # Compile, compress, derive key, encrypt
|-- runtime_backends/
|   |-- __init__.py
|   |-- protocol.py            # RuntimeBackend contract and result model
|   |-- portable.py            # Adapter around RuntimeProtector
|   |-- cython.py              # Adapter around PydRuntimeProtector
|   `-- rust.py                # Temporary crate, Maturin, artifact staging
`-- _native/
    `-- skjol_runtime/
        |-- Cargo.toml
        |-- Cargo.lock
        `-- src/
            |-- artifact.rs    # Length-safe envelope parser
            |-- crypto.rs      # HKDF and AES-GCM
            |-- metadata.rs    # Strict policy schema and validation
            |-- policy.rs      # Expiration/machine/domain/debug decisions
            |-- cpython.rs     # Isolated unsafe CPython FFI
            |-- runtime.rs     # Orchestration with cleanup
            `-- lib.rs         # PyO3 entry point template
```

Rust crate files must be included as package data in both the wheel and source
distribution. The generated build directory and Cargo target directory must
live under a Python `TemporaryDirectory`; neither Rust source nor key material
is copied to protected output.

## Python interfaces

`RuntimeBackend` should be a small protocol so file and directory workflows do
not duplicate backend selection:

```python
class RuntimeBackend(Protocol):
    def protect_source(self, source: str, filename: str) -> ProtectedArtifact: ...
    def materialize_runtime(self, output_dir: Path) -> RuntimeBuildResult: ...
```

`ProtectedArtifact` records launcher text, encrypted payload bytes, runtime ID,
format version, and required Python tag. `RuntimeBuildResult` records the native
module path, build command, target tag, hashes, and diagnostics. Concrete result
types replace dictionaries with optional keys for new code.

The canonical CLI becomes:

```powershell
python -m skjol obfuscate -i .\app.py -o .\dist\app.py --runtime rust
```

Backend rules are:

- `--runtime python` selects the portable generated Python runtime.
- `--runtime cython` selects the existing Cython runtime.
- `--runtime rust` selects the new Rust runtime and requires Rust, Cargo, and
  Maturin.
- `--pyd` remains a deprecated alias for `--runtime cython` for one major
  release cycle.
- Combining `--pyd` with a conflicting `--runtime` value is a CLI error.
- `--no-encrypt` cannot be combined with `--runtime rust` or `cython`.
- Native build failure is fatal and leaves no partial output.

The generated launcher imports `skjol_runtime_<runtime_id>` and calls only its
`run(__name__, __file__, encrypted_payload)` entry point. Rust obtains the
caller's module dictionary and passes the decoded code object directly to
`PyEval_EvalCode`, so public names naturally remain in the caller's module.

## Rust safety boundary

All direct CPython calls must be isolated in `cpython.rs`. That module will:

1. require the GIL for the complete decode/evaluation transition;
2. decode with `PyMarshal_ReadObjectFromString`, not Python `marshal.loads`;
3. verify that the decoded object is a code object;
4. obtain the existing module dictionary for `name`;
5. set `__name__`, `__file__`, and `__builtins__` consistently;
6. execute through `PyEval_EvalCode`, not Python `exec` or `eval`;
7. convert CPython errors into normal Python exceptions; and
8. balance every owned and borrowed reference on success and failure.

Every `unsafe` block needs a short safety comment and a focused test. Rust
panics must not cross the FFI boundary. Plaintext, derived keys, the build root
key copy, and decompressed marshal buffers use `Zeroizing` or an equivalent
drop guard. The CPython code object remains observable to native process tools;
the implementation and documentation must say so.

## Build workflow

For each protection build, the Rust backend will:

1. generate a random 32-byte build root key and random runtime ID;
2. transform and compile every selected source using the current Python
   pipeline;
3. produce one native-format artifact per Python file using a unique artifact
   ID and nonce;
4. copy the reviewed Rust crate template into a temporary directory;
5. generate only the module-name wrapper and a temporary `key.bin` there;
6. set `CARGO_TARGET_DIR` inside the same temporary directory;
7. invoke Maturin in release mode with the running Python interpreter and
   `--locked` dependency resolution;
8. validate that exactly one compatible wheel was produced;
9. extract only the expected `.pyd` or `.so` into a staging output directory;
10. copy the same extension beside each directly runnable protected file;
11. execute a generated-artifact smoke test before publishing output;
12. atomically replace the requested output only after every file succeeds; and
13. delete the temporary crate, key file, Cargo target directory, wheel, and
    decrypted test artifacts on success or failure.

Command output must redact the root key, derived keys, decrypted payloads, and
temporary `key.bin` path. Verbose mode may show tool versions, target triple,
wheel tag, runtime ID, duration, and final artifact hashes.

## Staged implementation backlog

### Milestone 0 — Freeze the baseline

- Record the existing 18-artifact portable-runtime results.
- Add a minimal CLI test proving current `--pyd` behavior before changing
  backend selection.
- Record protection time, protected size, and startup time for the three
  adversarial fixtures.
- Add an architecture decision record linking this plan.

Exit gate: the current behavior and attack outcomes are reproducible from a
clean Windows/CPython 3.12 environment.

### Milestone 1 — Artifact format and Python builder

- Implement `NativeArtifactHeader`, `NativeMetadata`, and bounded parsing.
- Implement HKDF-SHA256 derivation and AES-256-GCM encryption with authenticated
  headers.
- Require `cryptography`; do not use the existing stream/HMAC fallback.
- Generate deterministic test vectors from fixed keys, IDs, nonces, metadata,
  and bytecode fixtures.
- Test truncation at every header boundary, altered lengths, unknown versions,
  unknown flags, invalid UTF-8/JSON, ciphertext modification, tag modification,
  wrong root key, and Python-version mismatch.

Exit gate: Python round-trip tests pass and every one-bit mutation of protected
header/ciphertext test samples is rejected or remains authenticated according
to the documented mutable fields.

### Milestone 2 — Rust runtime core

- Implement format parsing against the shared test vectors.
- Implement HKDF, AES-GCM, JSON validation, decompression, and zeroization.
- Add direct CPython marshal/evaluation calls behind the isolated FFI module.
- Initially implement expiration and policy schema validation; reject any
  policy that has not yet been implemented instead of ignoring it.
- Add Rust unit tests for parsing, crypto vectors, policy decisions, length
  limits, corrupted input, and cleanup guards.
- Run `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test`, and
  dependency auditing in CI.

Exit gate: a fixed native extension executes one protected fixture correctly
without calling Python-level `eval`, `exec`, or `marshal.loads`.

### Milestone 3 — Backend and CLI integration

- Introduce `RuntimeBackend`, `ProtectedArtifact`, and `RuntimeBuildResult`.
- Add the Rust backend without copying file/directory traversal logic.
- Add `--runtime` parsing, compatibility validation, config-file support, help
  text, and deprecated `--pyd` handling.
- Build through Maturin in a temporary directory with a locked Cargo graph.
- Stage output atomically and remove every temporary file on all error paths.
- Preserve nested-directory runtime placement and exclusion behavior.
- Emit actionable errors for missing Rust, Cargo, Maturin, compiler toolchain,
  incompatible Python, build failure, and missing extension output.

Exit gate: the public CLI protects and executes both a single file and a nested
directory using `--runtime rust`, and forced build failures leave no protected
or key-bearing partial output.

### Milestone 4 — Policy parity and behavior coverage

- Implement anti-debug, expiration, allowed-machine, and domain policy checks
  natively with explicit platform behavior.
- Keep network licensing and remote keys disabled until their provider contract
  exists.
- Run semantic-equivalence tests for imports, packages, exceptions, async code,
  generators, decorators, context managers, Unicode, paths with spaces, and
  user-visible tracebacks.
- Verify public names, `__name__`, `__file__`, relative imports, and exit codes.
- Verify unsupported combinations fail rather than silently reducing
  protection.

Exit gate: native execution has no known behavior regression across the
documented supported-input suite, and every advertised policy has positive,
negative, and tamper tests.

### Milestone 5 — Security evaluation

- Add a `native-rust` profile to `benchmarks/security_evaluation.py`.
- Run three randomized trials for all three fixtures on the initial target.
- Verify the existing Python interposition attack cannot capture the code
  object or canary through its current hook boundary.
- Search the launcher, native library, logs, temporary locations, and build
  output for plaintext canaries and serialized metadata.
- Add an authorized, documented native-debugger or process-memory observation
  procedure and report successful extraction honestly.
- Record commands, tool versions, environment, hashes, raw results, and
  limitations in a separate native report.

Exit gate: all correctness targets pass, the existing Python-hook attack
records `0/18` code captures and `0/18` dynamic canary recoveries, and native
attack results are published without being combined into a synthetic score.

### Milestone 6 — Supported platform matrix

- Extend CI to CPython 3.10 through 3.13 on Windows, Linux, and macOS.
- Build on the target platform; cross-compilation remains out of scope.
- Test x86-64 first, then add ARM64 only where runners and toolchains are
  reliable.
- Validate wheel tags and reject loading an extension built for another Python
  version or architecture.
- Measure build time, startup time, output size, and runtime overhead against
  the portable backend.
- Exercise clean installation from the built Skjol wheel and source
  distribution so the packaged Cargo template is proven complete.

Exit gate: the backend passes the supported matrix and unexplained performance
regressions over the project's 20% release threshold are resolved or explicitly
accepted and documented.

### Milestone 7 — Remote key provider

- Define a `KeyProvider` interface independent of HTTP transport.
- Use authenticated requests, short-lived scoped authorization, replay
  protection, explicit timeouts, and revocation.
- Bind returned key material to artifact ID, policy, and a short validity
  period.
- Define fail-closed, offline, renewal, privacy, and service-outage behavior.
- Keep transport and credentials out of generated Python code.
- Add a mock provider for deterministic E2E and failure tests before selecting
  a production service.

Exit gate: the remote profile contains no durable root decryption key in the
launcher or native runtime, and copied artifacts cannot execute after their
authorization expires or is revoked.

## Test files to add or extend

| Test location | Coverage |
|---|---|
| `tests/test_native_artifact_format.py` | Header/schema round trips, bounds, mutations, authentication failures |
| `tests/test_rust_runtime_builder.py` | Tool detection, redaction, temporary cleanup, wheel validation |
| `tests/test_cli_native_runtime.py` | Public CLI file/directory E2E execution and failure behavior |
| `tests/test_native_runtime_semantics.py` | Imports, exceptions, async, generators, decorators, module globals |
| `tests/test_security_evaluation.py` | Native profile aggregation and attack evidence |
| Rust crate unit tests | Parser, crypto vectors, policy, FFI error mapping, zeroization guards |
| `benchmarks/security_evaluation.py` | Real Python-hook attack against native artifacts |
| `benchmarks/performance_suite.py` | Build, size, startup, and execution overhead |

All user-facing protection tests invoke `python -m skjol` in a subprocess and
execute the generated artifact, following the repository's E2E requirement.

## Measurable release gates

| Measure | Initial native target | Remote-key target |
|---|---:|---:|
| Protection completed | 18/18 | 18/18 |
| Normal execution passed | 18/18 | 18/18 |
| Existing Python-hook code capture | 0/18 | 0/18 |
| Existing Python-hook canary recovery | 0/18 | 0/18 |
| Semantic-equivalence regressions | 0 | 0 |
| Plaintext payload returned to Python | 0 occurrences | 0 occurrences |
| Silent fallback to a weaker runtime | 0 occurrences | 0 occurrences |
| Temporary key/source/build artifacts after completion or failure | 0 | 0 |
| Durable root decryption key embedded in runtime | Known limitation | 0 |

Reaching `0/18` for the existing Python-level attack demonstrates only that the
specific hook boundary was removed. It does not establish a universal security
score. Native debugger and memory-observation results must be reported
separately, including successful extractions.

## Definition of done

The Rust backend is complete only when:

- the CLI and configuration schema document backend selection and conflicts;
- clean-environment builds work from both the Skjol wheel and source archive;
- protected file and nested-directory artifacts execute through CLI E2E tests;
- the native format has stable test vectors and rejects malformed input;
- no supported policy is ignored or downgraded;
- missing prerequisites and build failures are actionable and atomic;
- the complete Python and Rust test suites pass on the declared platform
  matrix;
- performance and security reports are regenerated;
- the limitations of embedded offline keys and native process ownership remain
  explicit; and
- release notes describe compatibility, toolchain, deployment, and rollback
  behavior.

## Costs and risks

- CI and release builds become a matrix of Python versions, operating systems,
  architectures, and wheel tags.
- Users on unsupported platforms need a clear error or explicit portable mode.
- Rust and CPython FFI add specialist maintenance and review requirements.
- Python-version-specific code objects can complicate artifact portability.
- Native crashes are more severe than normal Python exceptions and require
  careful unsafe-code isolation and tests.
- Remote key delivery introduces service availability, privacy, enrollment,
  offline-use, and recovery-policy questions.
- Attackers may shift from Python hooks to native debugging, so the adversarial
  suite must evolve with the implementation.

## Recommendation

Rust is a good idea for a bounded native-runtime proof of concept because it can
remove the exact Python-level interception point demonstrated by the current
evaluation and can reduce accidental plaintext exposure. It should not begin as
a full rewrite, and it should not be marketed as making extraction impossible.

Implementation should follow Milestones 0 through 6 in order. Milestone 7 is a
separate security capability and must not block learning from the offline native
runtime, but the embedded-root-key limitation prevents the offline profile from
being presented as strong secret storage. Truly confidential logic and
long-lived secrets should remain off the client.

## References

- [Skjol reproducible security evaluation](SECURITY_EVALUATION.md)
- [Skjol requirements and roadmap](REQUIREMENTS_AND_ROADMAP.md)
- [PyO3 features and `abi3`](https://pyo3.rs/main/features)
- [PyO3 building and distribution](https://pyo3.rs/main/building-and-distribution.html)
- [Maturin tutorial](https://www.maturin.rs/tutorial.html)
- [CPython data marshalling C API](https://docs.python.org/3/c-api/marshal.html)
- [CPython very-high-level C API](https://docs.python.org/3/c-api/veryhigh.html)
- [Python `marshal` compatibility warning](https://docs.python.org/3/library/marshal.html)
