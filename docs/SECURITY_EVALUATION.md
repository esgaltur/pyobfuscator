# Reproducible Security Evaluation

## Purpose

This evaluation measures concrete attack outcomes against artifacts produced by
the public Skjol CLI. It does not assign a universal resistance score. Every
reported rate is limited to the named fixtures, profiles, environment, trials,
and attack implementation recorded in the JSON report.

## Attacker model

The attacker receives every distributed Python loader and runtime module and
can execute them locally under a modified Python interpreter environment. This
matches the normal threat model for client-side Python distribution: the user
controls the process that must eventually decrypt and execute the protected
program.

The suite performs two attacks:

1. **Static text recovery** searches all distributed Python files for unique
   canary values and original identifiers.
2. **Dynamic runtime interposition** replaces Python's `eval`, `marshal.loads`,
   and `exec` functions. It changes the decrypted anti-debug metadata, captures
   the decrypted code object, executes it, and inspects runtime globals for the
   canaries.

The dynamic attack does not need the encryption key in advance and does not
modify the generated artifact files.

## Reproduce it

From the repository root in PowerShell:

```powershell
python benchmarks\security_evaluation.py --trials 3
```

The command protects three independent fixtures with both the default and
hardened profiles. It executes each artifact normally, performs both attacks,
and writes the complete environment, commands, hashes, per-trial evidence, and
aggregate rates to `benchmarks/adversarial_results.json`.

## Interpretation

- A zero static recovery rate means the exact canaries were not present in the
  shipped Python text. It does not prove that static reverse engineering is
  impossible.
- A successful code-object capture means the attacker obtained the decrypted
  Python code object at the runtime boundary.
- A successful dynamic canary recovery means the protected secret value became
  observable to the attacker during execution.
- Results cannot be generalized to native PYD runtimes, OS-level memory tools,
  other applications, or attacks not implemented by the suite.

The current machine-readable results are stored in
[`benchmarks/adversarial_results.json`](../benchmarks/adversarial_results.json).
They should be regenerated for release candidates and after changes to runtime
protection.

## Current recorded result

The report generated on 2026-08-14 used CPython 3.12.10 on Windows 11. It ran
three randomized trials for each combination of three fixtures and two profiles
(18 protected artifacts total):

| Outcome | Observed | Desired | Status |
|---|---:|---:|---|
| Protection completed | 18/18 | 18/18 | Pass |
| Normal protected execution passed | 18/18 | 18/18 | Pass |
| Canaries recovered by static attack | 0/18 | 0/18 | Pass |
| Original identifiers recovered by static attack | 0/36 | 0/36 | Pass |
| Decrypted code objects captured dynamically | 18/18 | 0/18 | Open limitation |
| Canaries recovered dynamically | 18/18 | 0/18 | Open limitation |
| Original identifiers recovered dynamically | 0/36 | 0/36 | Pass |

For this attacker model, encryption prevented direct plaintext recovery from
the shipped Python files but did not prevent recovery during execution. The
anti-debug setting was bypassed by changing its decrypted metadata through the
interposed `eval` call. The default and hardened profiles had the same outcome.

## Experimental Rust-runtime result

On the same Windows 11 and CPython 3.12.10 environment, a focused automated
proof-of-concept trial protected one independent canary fixture through the
public CLI with `--runtime rust --no-anti-debug`. The test then executed the
artifact normally and applied the same Python-level `eval`, `exec`, and
`marshal.loads` interposition procedure:

| Outcome | Observed |
|---|---:|
| Native protection completed | 1/1 |
| Normal native execution passed | 1/1 |
| Protected code objects captured by Python hooks | 0/1 |
| Native canaries recovered by Python hooks | 0/1 |
| Modified native ciphertext rejected | 1/1 |

This is an implementation test, not the full native security release gate and
not evidence of universal resistance. The offline root key is embedded in the
compiled extension, and native debugging, binary instrumentation, process
memory inspection, and key extraction remain possible. The next security gate
is the documented 18-artifact native run plus a separate native-observation
procedure.

## Remediation hierarchy

Pure Python cannot provide a hard confidentiality boundary against the owner of
the process: executable code and required values must eventually become usable
by that process. The practical goal is therefore to remove valuable secrets
from that boundary and raise extraction cost without claiming impossibility.

1. **Do not ship long-lived secrets.** API keys, signing keys, database
   credentials, and master encryption keys belong in a server, KMS, or secrets
   service. Give clients short-lived, scoped tokens instead.
2. **Keep the most sensitive logic server-side.** This is the strongest fix for
   algorithms that must remain confidential. The client receives only results.
3. **Evaluate the native PYD runtime separately.** Native code can raise the
   effort required for Python-level interposition, but it remains subject to
   native debugging, memory inspection, and reverse engineering. The
   [Rust native-runtime plan](RUST_NATIVE_RUNTIME_CONSIDERATION.md) describes
   the implementation stages and measurable acceptance criteria.
4. **Reduce exposure duration.** Decrypt smaller units only when needed, avoid
   storing recovered values in module globals, and clear temporary buffers.
   This narrows the observation window but cannot eliminate it.
5. **Use remote authorization and revocation.** Bind valuable operations to
   short-lived server decisions so a copied artifact does not grant durable
   access. Offline behavior and failure policy must be explicit.
6. **Keep measuring actual attacks.** Add native, debugger, memory-dump, and
   decompiler procedures with versioned tools and exact success criteria.

For the current pure-Python profile, changing anti-hook checks or adding more
obfuscation may slow this specific attack but cannot guarantee `0/18` dynamic
recovery on an attacker-controlled interpreter.
