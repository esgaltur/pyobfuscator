"""Focused tests for native build orchestration and failure cleanup."""

from pathlib import Path

import pytest

from pyobfuscator.obfuscator import Obfuscator
from pyobfuscator.runtime_backends.rust import (
    RustRuntimeBackend,
    RustRuntimeCompiler,
    RustRuntimeError,
)


class FailingCompiler:
    def build(self, module_name: str, root_key: bytes, output_dir: Path):
        raise RustRuntimeError("forced native build failure")


def test_crate_configuration_keeps_locked_package_identity(tmp_path: Path) -> None:
    crate = tmp_path / "crate"
    crate.mkdir()
    (crate / "src").mkdir()
    (crate / "Cargo.toml").write_text(
        '[package]\nname = "skjol-runtime-template"\n'
        '[lib]\nname = "skjol_runtime_template"\n',
        encoding="utf-8",
    )
    (crate / "src" / "lib.rs").write_text(
        "fn skjol_runtime_template() {}\n",
        encoding="utf-8",
    )

    RustRuntimeCompiler._configure_crate(
        crate,
        "skjol_runtime_abc123",
        bytes(range(32)),
    )

    cargo = (crate / "Cargo.toml").read_text(encoding="utf-8")
    assert 'name = "skjol-runtime-template"' in cargo
    assert 'name = "skjol_runtime_abc123"' in cargo
    assert "skjol_runtime_abc123" in (crate / "src" / "lib.rs").read_text(
        encoding="utf-8"
    )
    root_key_source = (crate / "src" / "root_key.rs").read_text(encoding="utf-8")
    assert "pub const ROOT_KEY: [u8; 32]" in root_key_source
    assert "0, 1, 2, 3" in root_key_source


def test_failed_native_build_does_not_publish_launcher(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    output = tmp_path / "dist" / "protected.py"
    source.write_text('print("must not be published")\n', encoding="utf-8")
    obfuscator = Obfuscator(
        config={
            "runtime_backend": "rust",
            "anti_debug": False,
        }
    )
    backend = RustRuntimeBackend(
        obfuscator,
        root_key=bytes(range(32)),
        runtime_id="failure",
        compiler=FailingCompiler(),
    )

    with pytest.raises(RustRuntimeError, match="forced native build failure"):
        backend.protect_file(source, output)

    assert not output.exists()
    assert not output.parent.exists()


@pytest.mark.parametrize("module_name", ["with-dash", "bad name", "", "123module"])
def test_crate_configuration_rejects_invalid_module_names(
    tmp_path: Path,
    module_name: str,
) -> None:
    with pytest.raises(RustRuntimeError, match="Invalid generated"):
        RustRuntimeCompiler._configure_crate(tmp_path, module_name, b"x" * 32)
