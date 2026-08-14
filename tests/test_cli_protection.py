"""End-to-end tests for the public encryption CLI workflow."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: object, module: str = "skjol") -> subprocess.CompletedProcess[str]:
    """Invoke Skjol exactly as an end user would."""
    return subprocess.run(
        [sys.executable, "-m", module, *map(str, args)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )


def run_python(script: Path) -> subprocess.CompletedProcess[str]:
    """Execute generated output from its own directory."""
    return subprocess.run(
        [sys.executable, script.name],
        capture_output=True,
        text=True,
        cwd=script.parent,
        timeout=30,
    )


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"command failed with exit code {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_cli_reports_package_version() -> None:
    from skjol import __version__

    result = run_cli("--version")

    assert_success(result)
    assert result.stdout.strip() == f"skjol {__version__}"


def test_legacy_module_alias_reports_skjol_version() -> None:
    from skjol import __version__

    result = run_cli("--version", module="pyobfuscator")

    assert_success(result)
    assert result.stdout.strip() == f"skjol {__version__}"


def test_public_api_preserves_legacy_identity() -> None:
    from pyobfuscator import Obfuscator as LegacyObfuscator
    from skjol import Obfuscator

    assert Obfuscator is LegacyObfuscator


def test_cli_encrypts_and_executes_single_file(tmp_path: Path) -> None:
    source = tmp_path / "secret_app.py"
    output = tmp_path / "dist" / "secret_app.py"
    source.write_text(
        'SECRET_MESSAGE = "encrypted payload executed"\n'
        "def reveal():\n"
        "    return SECRET_MESSAGE\n"
        "print(reveal())\n",
        encoding="utf-8",
    )

    protection = run_cli(
        "obfuscate",
        "-i",
        source,
        "-o",
        output,
        "--no-anti-debug",
    )

    assert_success(protection)
    protected_source = output.read_text(encoding="utf-8")
    assert "SECRET_MESSAGE" not in protected_source
    assert "encrypted payload executed" not in protected_source
    assert len(list(output.parent.glob("skjol_runtime_*.py"))) == 1

    execution = run_python(output)
    assert_success(execution)
    assert execution.stdout.strip() == "encrypted payload executed"


def test_cli_encrypts_nested_directory_with_local_runtime(tmp_path: Path) -> None:
    input_dir = tmp_path / "src"
    nested_dir = input_dir / "commands"
    output_dir = tmp_path / "dist"
    nested_dir.mkdir(parents=True)
    source = nested_dir / "main.py"
    source.write_text('print("nested protection executed")\n', encoding="utf-8")

    protection = run_cli(
        "obfuscate",
        "-i",
        input_dir,
        "-o",
        output_dir,
        "--no-anti-debug",
    )

    assert_success(protection)
    protected_script = output_dir / "commands" / "main.py"
    assert protected_script.exists()
    assert len(list(protected_script.parent.glob("skjol_runtime_*.py"))) == 1

    execution = run_python(protected_script)
    assert_success(execution)
    assert execution.stdout.strip() == "nested protection executed"


def test_cli_rejects_missing_explicit_config(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    output = tmp_path / "app.protected.py"
    missing_config = tmp_path / "missing.json"
    source.write_text('print("must not be generated")\n', encoding="utf-8")

    result = run_cli(
        "obfuscate",
        "-i",
        source,
        "-o",
        output,
        "--config",
        missing_config,
    )

    assert result.returncode == 1
    assert "Config file not found" in result.stderr
    assert not output.exists()


def test_cli_init_uses_skjol_config_name(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text('print("config scan")\n', encoding="utf-8")

    result = run_cli("init", project)

    assert_success(result)
    assert (project / "skjol.json").exists()
    assert not (project / "pyobfuscator.json").exists()


def test_cli_accepts_legacy_config_filename(tmp_path: Path) -> None:
    source_dir = tmp_path / "src"
    output_dir = tmp_path / "dist"
    source_dir.mkdir()
    (source_dir / "app.py").write_text(
        'print("legacy config remains compatible")\n',
        encoding="utf-8",
    )
    (source_dir / "pyobfuscator.json").write_text(
        json.dumps({"no_string_obfuscation": True}),
        encoding="utf-8",
    )

    result = run_cli(
        "obfuscate",
        "-i",
        source_dir,
        "-o",
        output_dir,
        "--no-encrypt",
    )

    assert_success(result)
    protected = (output_dir / "app.py").read_text(encoding="utf-8")
    assert "legacy config remains compatible" in protected
