"""Reproducible black-box security evaluation for Skjol artifacts.

The evaluation reports concrete outcomes for a documented attacker model. It
does not combine results into a universal security or resistance score.
"""

from __future__ import annotations

import argparse
import builtins
import hashlib
import json
import marshal
import platform
import re
import subprocess
import sys
import tempfile
import traceback
import types
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_MODE = "_capture"


@dataclass(frozen=True)
class EvaluationFixture:
    """A program with values an evaluator can objectively try to recover."""

    name: str
    source: str
    expected_stdout: str
    canaries: tuple[str, ...]
    identifiers: tuple[str, ...]


@dataclass(frozen=True)
class ProtectionProfile:
    """CLI options defining a protection profile."""

    name: str
    cli_args: tuple[str, ...]


DEFAULT_FIXTURES = (
    EvaluationFixture(
        name="function_secret",
        source=(
            'SERVICE_TOKEN = "SKJOL_CANARY_ALPHA_91E7"\n'
            "def calculate_invoice(amount):\n"
            "    return amount * 3 + len(SERVICE_TOKEN)\n"
            "print(calculate_invoice(7))\n"
        ),
        expected_stdout="44",
        canaries=("SKJOL_CANARY_ALPHA_91E7",),
        identifiers=("SERVICE_TOKEN", "calculate_invoice"),
    ),
    EvaluationFixture(
        name="class_configuration",
        source=(
            'PRIVATE_ENDPOINT = "SKJOL_CANARY_BRAVO_42CD"\n'
            "class RequestSigner:\n"
            "    def render(self):\n"
            "        return PRIVATE_ENDPOINT[-4:]\n"
            "print(RequestSigner().render())\n"
        ),
        expected_stdout="42CD",
        canaries=("SKJOL_CANARY_BRAVO_42CD",),
        identifiers=("PRIVATE_ENDPOINT", "RequestSigner"),
    ),
    EvaluationFixture(
        name="container_secret",
        source=(
            'CREDENTIALS = {"token": "SKJOL_CANARY_CHARLIE_6A20"}\n'
            "def token_length():\n"
            "    return len(CREDENTIALS[\"token\"])\n"
            "print(token_length())\n"
        ),
        expected_stdout="25",
        canaries=("SKJOL_CANARY_CHARLIE_6A20",),
        identifiers=("CREDENTIALS", "token_length"),
    ),
)

DEFAULT_PROFILES = (
    ProtectionProfile(name="default", cli_args=()),
    ProtectionProfile(
        name="hardened",
        cli_args=("--all-advanced", "--intensity", "3"),
    ),
)


def _run(command: Sequence[str], *, cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _collect_code_details(code: types.CodeType) -> dict[str, Any]:
    identifiers: set[str] = set()
    strings: set[str] = set()
    code_objects = 0

    def visit(current: types.CodeType) -> None:
        nonlocal code_objects
        code_objects += 1
        identifiers.update(current.co_names)
        identifiers.update(current.co_varnames)
        for constant in current.co_consts:
            if isinstance(constant, str):
                strings.add(constant)
            elif isinstance(constant, types.CodeType):
                visit(constant)

    visit(code)
    return {
        "filename": code.co_filename,
        "code_objects": code_objects,
        "identifiers": sorted(identifiers),
        "string_constants": sorted(strings),
    }


def _collect_runtime_strings(value: Any, *, depth: int = 0, seen: set[int] | None = None) -> set[str]:
    if depth > 4:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, (bytes, bytearray)):
        try:
            return {bytes(value).decode("utf-8")}
        except UnicodeDecodeError:
            return set()
    if value is None or isinstance(value, (bool, int, float, complex)):
        return set()

    if seen is None:
        seen = set()
    value_id = id(value)
    if value_id in seen:
        return set()
    seen.add(value_id)

    strings: set[str] = set()
    if isinstance(value, dict):
        items: Iterable[Any] = (*value.keys(), *value.values())
    elif isinstance(value, (list, tuple, set, frozenset)):
        items = value
    else:
        return strings
    for item in items:
        strings.update(_collect_runtime_strings(item, depth=depth + 1, seen=seen))
    return strings


def capture_runtime(protected_path: Path, report_path: Path) -> int:
    """Execute an artifact with marshal/exec interception and record recovery."""
    original_eval = builtins.eval
    original_exec = builtins.exec
    original_loads = marshal.loads
    captured_code: list[dict[str, Any]] = []
    runtime_strings: set[str] = set()
    execution_error: str | None = None
    execution_traceback: str | None = None
    anti_debug_policy_bypassed = False
    artifact_directory = str(protected_path.resolve().parent)
    added_artifact_path = artifact_directory not in sys.path

    def loads_hook(data: bytes) -> Any:
        result = original_loads(data)
        if isinstance(result, types.CodeType):
            captured_code.append({"stage": "marshal.loads", **_collect_code_details(result)})
        return result

    def eval_hook(expression: Any, globals_dict: dict[str, Any] | None = None, locals_dict: dict[str, Any] | None = None) -> Any:
        nonlocal anti_debug_policy_bypassed
        result = original_eval(expression, globals_dict, locals_dict)
        if isinstance(result, dict) and "anti_debug" in result:
            result["anti_debug"] = False
            anti_debug_policy_bypassed = True
        return result

    def exec_hook(code: Any, globals_dict: dict[str, Any] | None = None, locals_dict: dict[str, Any] | None = None) -> Any:
        if isinstance(code, types.CodeType):
            captured_code.append({"stage": "exec", **_collect_code_details(code)})
        result = original_exec(code, globals_dict, locals_dict)
        if globals_dict:
            runtime_strings.update(_collect_runtime_strings(globals_dict))
        return result

    try:
        loader_source = protected_path.read_text(encoding="utf-8")
        loader_code = compile(loader_source, str(protected_path), "exec")
        del loader_source
        loader_globals = {
            "__name__": "__main__",
            "__file__": str(protected_path),
            "__builtins__": builtins,
        }
        marshal.loads = loads_hook
        builtins.eval = eval_hook
        builtins.exec = exec_hook
        if added_artifact_path:
            sys.path.insert(0, artifact_directory)
        original_exec(loader_code, loader_globals)
    except BaseException as exc:  # The attack result must record protection failures too.
        execution_error = f"{type(exc).__name__}: {exc}"
        execution_traceback = traceback.format_exc()
    finally:
        builtins.eval = original_eval
        builtins.exec = original_exec
        marshal.loads = original_loads
        if added_artifact_path and artifact_directory in sys.path:
            sys.path.remove(artifact_directory)

    report = {
        "attack": "python_runtime_function_interposition",
        "code_object_captured": bool(captured_code),
        "anti_debug_policy_bypassed": anti_debug_policy_bypassed,
        "captured_code": captured_code,
        "runtime_strings": sorted(runtime_strings),
        "execution_error": execution_error,
        "execution_traceback": execution_traceback,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


def _static_recovery(output_dir: Path, fixture: EvaluationFixture) -> dict[str, Any]:
    artifact_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(output_dir.glob("*.py"))
    )
    recovered_canaries = [value for value in fixture.canaries if value in artifact_text]
    recovered_identifiers = [
        value
        for value in fixture.identifiers
        if re.search(rf"\b{re.escape(value)}\b", artifact_text)
    ]
    return {
        "attack": "static_text_search",
        "files_searched": len(list(output_dir.glob("*.py"))),
        "recovered_canaries": recovered_canaries,
        "recovered_identifiers": recovered_identifiers,
    }


def _dynamic_recovery(
    output_dir: Path,
    protected_path: Path,
    fixture: EvaluationFixture,
) -> dict[str, Any]:
    capture_path = output_dir / "capture.json"
    capture_command = [
        sys.executable,
        str(Path(__file__).resolve()),
        CAPTURE_MODE,
        str(protected_path),
        str(capture_path),
    ]
    result = _run(capture_command, cwd=output_dir)
    if not capture_path.exists():
        return {
            "attack": "python_runtime_function_interposition",
            "process_returncode": result.returncode,
            "process_stderr": result.stderr,
            "code_object_captured": False,
            "recovered_canaries": [],
            "recovered_identifiers": [],
            "execution_error": "capture report was not produced",
        }

    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    target_code = [
        item
        for item in capture["captured_code"]
        if Path(item["filename"]).name == protected_path.name
    ]
    searchable_strings = set(capture["runtime_strings"])
    searchable_identifiers: set[str] = set()
    for code_result in target_code:
        searchable_strings.update(code_result["string_constants"])
        searchable_identifiers.update(code_result["identifiers"])

    return {
        "attack": capture["attack"],
        "process_returncode": result.returncode,
        "process_stderr": result.stderr,
        "code_object_captured": bool(target_code),
        "anti_debug_policy_bypassed": capture["anti_debug_policy_bypassed"],
        "captured_code_objects": sum(
            item["code_objects"] for item in target_code
        ),
        "recovered_canaries": [
            value for value in fixture.canaries if value in searchable_strings
        ],
        "recovered_identifiers": [
            value for value in fixture.identifiers if value in searchable_identifiers
        ],
        "execution_error": capture["execution_error"],
        "execution_traceback": capture["execution_traceback"],
    }


def evaluate_trial(
    fixture: EvaluationFixture,
    profile: ProtectionProfile,
    trial_number: int,
    workspace: Path,
) -> dict[str, Any]:
    trial_dir = workspace / f"{profile.name}-{fixture.name}-{trial_number}"
    source_dir = trial_dir / "source"
    output_dir = trial_dir / "artifact"
    source_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    source_path = source_dir / f"{fixture.name}.py"
    protected_path = output_dir / f"{fixture.name}.py"
    source_path.write_text(fixture.source, encoding="utf-8")

    protect_command = [
        sys.executable,
        "-m",
        "skjol",
        "obfuscate",
        "-i",
        str(source_path),
        "-o",
        str(protected_path),
        *profile.cli_args,
    ]
    protection = _run(protect_command, cwd=PROJECT_ROOT)
    result: dict[str, Any] = {
        "fixture": fixture.name,
        "profile": profile.name,
        "trial": trial_number,
        "protection": {
            "returncode": protection.returncode,
            "stdout": protection.stdout,
            "stderr": protection.stderr,
        },
    }
    if protection.returncode != 0 or not protected_path.exists():
        result["normal_execution"] = {"passed": False, "error": "protection failed"}
        result["static_attack"] = None
        result["dynamic_attack"] = None
        return result

    execution = _run([sys.executable, protected_path.name], cwd=output_dir)
    result["artifact_sha256"] = hashlib.sha256(protected_path.read_bytes()).hexdigest()
    result["normal_execution"] = {
        "passed": execution.returncode == 0 and execution.stdout.strip() == fixture.expected_stdout,
        "returncode": execution.returncode,
        "expected_stdout": fixture.expected_stdout,
        "stdout": execution.stdout.strip(),
        "stderr": execution.stderr,
    }
    result["static_attack"] = _static_recovery(output_dir, fixture)
    result["dynamic_attack"] = _dynamic_recovery(output_dir, protected_path, fixture)
    return result


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "count": numerator,
        "total": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def aggregate_results(results: Sequence[dict[str, Any]], fixtures: Sequence[EvaluationFixture]) -> dict[str, Any]:
    canary_counts = {fixture.name: len(fixture.canaries) for fixture in fixtures}
    identifier_counts = {fixture.name: len(fixture.identifiers) for fixture in fixtures}
    completed = [result for result in results if result.get("static_attack") is not None]
    marker_total = sum(canary_counts[result["fixture"]] for result in completed)
    identifier_total = sum(identifier_counts[result["fixture"]] for result in completed)
    static_recovered = sum(len(result["static_attack"]["recovered_canaries"]) for result in completed)
    static_identifiers = sum(len(result["static_attack"]["recovered_identifiers"]) for result in completed)
    dynamic_recovered = sum(len(result["dynamic_attack"]["recovered_canaries"]) for result in completed)
    dynamic_identifiers = sum(len(result["dynamic_attack"]["recovered_identifiers"]) for result in completed)
    dynamic_capture = sum(bool(result["dynamic_attack"]["code_object_captured"]) for result in completed)
    normal_passed = sum(bool(result["normal_execution"]["passed"]) for result in results)

    return {
        "protection_completed": _rate(len(completed), len(results)),
        "normal_execution_passed": _rate(normal_passed, len(results)),
        "static_canary_recovery": _rate(static_recovered, marker_total),
        "static_identifier_recovery": _rate(static_identifiers, identifier_total),
        "dynamic_code_object_capture": _rate(dynamic_capture, len(completed)),
        "dynamic_canary_recovery": _rate(dynamic_recovered, marker_total),
        "dynamic_identifier_recovery": _rate(dynamic_identifiers, identifier_total),
    }


def _git_revision() -> str | None:
    result = _run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, timeout=10)
    return result.stdout.strip() if result.returncode == 0 else None


def run_evaluation(
    *,
    trials: int,
    output_path: Path,
    fixtures: Sequence[EvaluationFixture] = DEFAULT_FIXTURES,
    profiles: Sequence[ProtectionProfile] = DEFAULT_PROFILES,
) -> dict[str, Any]:
    if trials < 1:
        raise ValueError("trials must be at least 1")

    with tempfile.TemporaryDirectory(prefix="skjol-security-evaluation-") as temp_dir:
        workspace = Path(temp_dir)
        results = [
            evaluate_trial(fixture, profile, trial_number, workspace)
            for profile in profiles
            for fixture in fixtures
            for trial_number in range(1, trials + 1)
        ]

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_revision": _git_revision(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "threat_model": {
            "attacker_access": "All distributed Python loaders and runtime modules plus local execution",
            "static_attack": "Exact canary search and original-identifier search across distributed Python files",
            "dynamic_attack": "Python-level interposition of eval, marshal.loads, and exec; decrypted anti-debug metadata is changed before code-object and runtime-global inspection",
            "not_measured": [
                "Native PYD runtime extraction",
                "OS-level process memory dumping",
                "Debugger or disassembler effectiveness",
                "Time or monetary cost for a human reverse engineer",
                "Cryptographic strength of AES-256-GCM",
            ],
        },
        "profiles": [asdict(profile) for profile in profiles],
        "fixtures": [asdict(fixture) for fixture in fixtures],
        "trials_per_fixture_profile": trials,
        "results": results,
        "aggregate": aggregate_results(results, fixtures),
        "interpretation": (
            "Rates apply only to the documented fixtures, profiles, environment, "
            "and attacks. They are not a universal security score."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "benchmarks" / "adversarial_results.json",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == CAPTURE_MODE:
        if len(arguments) != 3:
            raise SystemExit(f"usage: {Path(__file__).name} {CAPTURE_MODE} PROTECTED REPORT")
        return capture_runtime(Path(arguments[1]), Path(arguments[2]))

    parsed = create_parser().parse_args(arguments)
    report = run_evaluation(trials=parsed.trials, output_path=parsed.output)
    print(json.dumps(report["aggregate"], indent=2))
    print(f"Report written to {parsed.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
