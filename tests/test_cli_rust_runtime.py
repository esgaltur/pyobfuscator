"""End-to-end coverage for the opt-in Rust runtime backend."""

from __future__ import annotations

import base64
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from benchmarks.security_evaluation import capture_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: object, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "skjol", *map(str, args)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=timeout,
    )


def test_cli_rejects_incompatible_rust_options(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    output = tmp_path / "protected.py"
    source.write_text('print("never emitted")\n', encoding="utf-8")

    result = run_cli(
        "obfuscate",
        "-i",
        source,
        "-o",
        output,
        "--runtime",
        "rust",
        "--no-encrypt",
    )

    assert result.returncode == 1
    assert "cannot be combined with --no-encrypt" in result.stderr
    assert not output.exists()


@pytest.mark.skipif(
    shutil.which("rustc") is None
    or shutil.which("cargo") is None
    or importlib.util.find_spec("maturin") is None,
    reason="Rust, Cargo, and Maturin are required for the native E2E test",
)
def test_rust_runtime_executes_and_resists_python_function_interposition(
    tmp_path: Path,
) -> None:
    pytest.importorskip("cryptography")
    source = tmp_path / "source" / "app.py"
    output = tmp_path / "dist" / "app.py"
    report_path = tmp_path / "capture.json"
    source.parent.mkdir()
    source.write_text(
        'NATIVE_CANARY = "SKJOL_NATIVE_CANARY_71A9"\n'
        "def reveal_native_canary():\n"
        "    return NATIVE_CANARY\n"
        "print(reveal_native_canary())\n",
        encoding="utf-8",
    )

    protection = run_cli(
        "obfuscate",
        "-i",
        source,
        "-o",
        output,
        "--runtime",
        "rust",
        "--no-anti-debug",
    )

    assert protection.returncode == 0, protection.stderr
    extensions = list(output.parent.glob("skjol_runtime_*.pyd"))
    if not extensions:
        extensions = list(output.parent.glob("skjol_runtime_*.so"))
    assert len(extensions) == 1
    launcher = output.read_text(encoding="utf-8")
    assert "SKJOL_NATIVE_CANARY_71A9" not in launcher
    assert "NATIVE_CANARY" not in launcher

    execution = subprocess.run(
        [sys.executable, output.name],
        cwd=output.parent,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert execution.returncode == 0, execution.stderr
    assert execution.stdout.strip() == "SKJOL_NATIVE_CANARY_71A9"

    assert capture_runtime(output, report_path) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    target_capture = [
        item
        for item in report["captured_code"]
        if Path(item["filename"]).name == output.name
    ]
    assert report["execution_error"] is None
    assert report["anti_debug_policy_bypassed"] is False
    assert target_capture == []
    assert "SKJOL_NATIVE_CANARY_71A9" not in report["runtime_strings"]

    payload_match = re.search(r"b'([A-Za-z0-9+/=]+)'", launcher)
    assert payload_match is not None
    payload = bytearray(base64.b64decode(payload_match.group(1)))
    payload[-1] ^= 1
    tampered = output.parent / "tampered.py"
    tampered.write_text(
        launcher.replace(payload_match.group(1), base64.b64encode(payload).decode("ascii")),
        encoding="utf-8",
    )
    rejected = subprocess.run(
        [sys.executable, tampered.name],
        cwd=tampered.parent,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert rejected.returncode != 0
    assert "native artifact authentication failed" in rejected.stderr


@pytest.mark.skipif(
    shutil.which("rustc") is None
    or shutil.which("cargo") is None
    or importlib.util.find_spec("maturin") is None,
    reason="Rust, Cargo, and Maturin are required for the native E2E test",
)
def test_rust_runtime_protects_nested_directory_with_one_shared_build(
    tmp_path: Path,
) -> None:
    pytest.importorskip("cryptography")
    source = tmp_path / "source"
    output = tmp_path / "dist"
    (source / "first").mkdir(parents=True)
    (source / "second").mkdir()
    (source / "first" / "app.py").write_text(
        'print("first native directory artifact")\n',
        encoding="utf-8",
    )
    (source / "second" / "app.py").write_text(
        'print("second native directory artifact")\n',
        encoding="utf-8",
    )

    protection = run_cli(
        "obfuscate",
        "-i",
        source,
        "-o",
        output,
        "--runtime",
        "rust",
        "--no-anti-debug",
    )

    assert protection.returncode == 0, protection.stderr
    module_names = set()
    for directory, expected in (
        (output / "first", "first native directory artifact"),
        (output / "second", "second native directory artifact"),
    ):
        extensions = list(directory.glob("skjol_runtime_*.pyd"))
        if not extensions:
            extensions = list(directory.glob("skjol_runtime_*.so"))
        assert len(extensions) == 1
        module_names.add(extensions[0].name)
        execution = subprocess.run(
            [sys.executable, "app.py"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert execution.returncode == 0, execution.stderr
        assert execution.stdout.strip() == expected
    assert len(module_names) == 1
