"""Focused tests for the CLI single-file workflow."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pyobfuscator.cli import _obfuscate_single_file, _warn_if_local_imports


def test_plain_single_file_resolves_existing_output_directory(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source.py"
    output_directory = tmp_path / "dist"
    source.write_text('print("plain")\n', encoding="utf-8")
    output_directory.mkdir()
    obfuscator = Mock()
    obfuscator.config = {"encrypt_code": False}

    exit_code = _obfuscate_single_file(
        obfuscator,
        source,
        output_directory,
        verbose=True,
    )

    assert exit_code == 0
    obfuscator.obfuscate_file.assert_called_once_with(
        source,
        output_directory / source.name,
    )
    output = capsys.readouterr().out
    assert f"Obfuscating {source}..." in output
    assert f"Output written to {output_directory / source.name}" in output
    assert "Obfuscation complete!" in output


def test_portable_protection_writes_launcher_and_runtime(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    output = tmp_path / "dist" / "protected.py"
    source.write_text('print("portable")\n', encoding="utf-8")
    obfuscator = Mock()
    obfuscator.config = {"encrypt_code": True, "runtime_backend": "python"}
    obfuscator.runtime_protector.runtime_id = "runtime123"
    obfuscator.protect_source.return_value = ("protected launcher", "runtime code")

    exit_code = _obfuscate_single_file(
        obfuscator,
        source,
        output,
        verbose=False,
    )

    assert exit_code == 0
    obfuscator.protect_source.assert_called_once_with(
        'print("portable")\n',
        source.name,
    )
    assert output.read_text(encoding="utf-8") == "protected launcher"
    runtime = output.parent / "skjol_runtime_runtime123.py"
    assert runtime.read_text(encoding="utf-8") == "runtime code"
    obfuscator.obfuscate_file.assert_not_called()


def test_rust_protection_is_delegated_to_native_backend(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source.py"
    output_directory = tmp_path / "native-dist"
    source.write_text('print("native")\n', encoding="utf-8")
    obfuscator = Mock()
    obfuscator.config = {"encrypt_code": True, "runtime_backend": "rust"}
    backend = Mock()
    extension = output_directory / "skjol_runtime_test.pyd"
    backend.protect_file.return_value = SimpleNamespace(extension_path=extension)

    with patch(
        "pyobfuscator.runtime_backends.RustRuntimeBackend",
        return_value=backend,
    ) as backend_type:
        exit_code = _obfuscate_single_file(
            obfuscator,
            source,
            output_directory,
            verbose=True,
        )

    target = output_directory / source.name
    assert exit_code == 0
    backend_type.assert_called_once_with(obfuscator)
    backend.protect_file.assert_called_once_with(source, target)
    obfuscator.protect_source.assert_not_called()
    output = capsys.readouterr().out
    assert f"Runtime module: {extension}" in output
    assert "Rust native runtime" in output


def test_local_import_warning_is_emitted_as_one_diagnostic(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source.py"
    source.write_text("from .helpers import run\n", encoding="utf-8")

    _warn_if_local_imports(source)

    assert capsys.readouterr().err == (
        "Warning: This file appears to have local imports.\n"
        "         For multi-file projects, obfuscate the entire directory.\n\n"
    )


def test_local_import_warning_ignores_unreadable_path(
    tmp_path: Path,
    capsys,
) -> None:
    _warn_if_local_imports(tmp_path / "missing.py")

    assert capsys.readouterr().err == ""
