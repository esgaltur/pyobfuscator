"""Focused tests for the CLI directory-processing workflow."""

from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock

from pyobfuscator.cli import _obfuscate_directory


def directory_options(**overrides) -> Namespace:
    values = {
        "verbose": False,
        "parallel": False,
        "workers": None,
        "recursive": True,
        "no_recursive": False,
        "exclude_patterns": ["skip_*.py"],
    }
    values.update(overrides)
    return Namespace(**values)


def test_plain_directory_reports_partial_failure_and_returns_nonzero(
    tmp_path: Path,
    capsys,
) -> None:
    input_path = tmp_path / "src"
    output_path = tmp_path / "dist"
    input_path.mkdir()
    obfuscator = Mock()
    obfuscator.config = {"encrypt_code": False}
    obfuscator.obfuscate_directory.return_value = {
        "broken.py": "failed: invalid syntax",
        "working.py": "success",
    }

    exit_code = _obfuscate_directory(
        obfuscator,
        input_path,
        output_path,
        directory_options(
            verbose=True,
            parallel=True,
            workers=2,
            no_recursive=True,
        ),
    )
    output = capsys.readouterr().out

    assert exit_code == 1
    assert output_path.is_dir()
    obfuscator.obfuscate_directory.assert_called_once_with(
        input_path,
        output_path,
        recursive=False,
        exclude_patterns=["skip_*.py"],
    )
    assert f"Obfuscating directory: {input_path} (parallel, 2 workers)" in output
    assert output.index("[FAIL] broken.py") < output.index("[OK] working.py")
    assert "Error: failed: invalid syntax" in output
    assert "Files processed: 1" in output
    assert "Errors: 1" in output


def test_encrypted_directory_uses_obfuscator_protection_pipeline(
    tmp_path: Path,
    capsys,
) -> None:
    input_path = tmp_path / "src"
    output_path = tmp_path / "dist"
    input_path.mkdir()
    obfuscator = Mock()
    obfuscator.config = {
        "encrypt_code": True,
        "use_pyd_compilation": False,
    }
    obfuscator.protect_directory.return_value = {
        "files": {"app.py": "success"},
        "runtime": output_path / "skjol_runtime_123.py",
    }

    exit_code = _obfuscate_directory(
        obfuscator,
        input_path,
        output_path,
        directory_options(),
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    obfuscator.protect_directory.assert_called_once_with(
        input_path,
        output_path,
        recursive=True,
        exclude_patterns=["skip_*.py"],
    )
    obfuscator.runtime_protector.protect_directory.assert_not_called()
    assert "Files processed: 1" in output
    assert "(Code is encrypted with AES-256-GCM)" in output


def test_pyd_directory_uses_native_runtime_backend(tmp_path: Path) -> None:
    input_path = tmp_path / "src"
    output_path = tmp_path / "dist"
    input_path.mkdir()
    obfuscator = Mock()
    obfuscator.config = {
        "encrypt_code": True,
        "use_pyd_compilation": True,
    }
    obfuscator.runtime_protector.protect_directory.return_value = {
        "files": {"app.py": "success"},
        "pyd": output_path / "skjol_runtime_123.pyd",
    }

    exit_code = _obfuscate_directory(
        obfuscator,
        input_path,
        output_path,
        directory_options(exclude_patterns=None),
    )

    assert exit_code == 0
    obfuscator.runtime_protector.protect_directory.assert_called_once_with(
        input_path,
        output_path,
        recursive=True,
        exclude_patterns=None,
    )
    obfuscator.protect_directory.assert_not_called()
