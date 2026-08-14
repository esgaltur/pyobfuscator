"""Rust native-runtime build and protection backend."""

from __future__ import annotations

import base64
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ..artifacts import NativeArtifactBuilder, ProtectedArtifact
from ..constants import DEFAULT_EXCLUDE_PATTERNS
from .protocol import RuntimeBuildResult

if TYPE_CHECKING:
    from ..obfuscator import Obfuscator


class RustRuntimeError(RuntimeError):
    """Raised when native protection cannot be built safely."""


class RustRuntimeCompiler:
    """Materialize a per-build PyO3 extension through Maturin."""

    TEMPLATE_DIRECTORY = Path(__file__).resolve().parents[1] / "_native" / "skjol_runtime"

    def build(self, module_name: str, root_key: bytes, output_dir: Path) -> RuntimeBuildResult:
        self._validate_prerequisites()
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="skjol-rust-build-") as temporary:
            workspace = Path(temporary)
            crate = workspace / "crate"
            wheels = workspace / "wheels"
            shutil.copytree(self.TEMPLATE_DIRECTORY, crate, ignore=shutil.ignore_patterns("target"))
            self._configure_crate(crate, module_name, root_key)
            wheel = self._build_wheel(crate, wheels, workspace / "target")
            extension = self._extract_extension(wheel, module_name, output_dir)
            return RuntimeBuildResult(
                module_name=module_name,
                extension_path=extension,
                wheel_name=wheel.name,
                python_tag=f"cp{sys.version_info.major}{sys.version_info.minor}",
            )

    @staticmethod
    def _validate_prerequisites() -> None:
        missing = [tool for tool in ("rustc", "cargo") if shutil.which(tool) is None]
        if importlib.util.find_spec("maturin") is None:
            missing.append("maturin Python package")
        if missing:
            raise RustRuntimeError(
                "Rust runtime requires " + ", ".join(missing) + ". Install Skjol with the 'rust' extra."
            )

    @staticmethod
    def _configure_crate(crate: Path, module_name: str, root_key: bytes) -> None:
        if not module_name.isidentifier() or len(root_key) != 32:
            raise RustRuntimeError("Invalid generated native module configuration")
        cargo_path = crate / "Cargo.toml"
        cargo = cargo_path.read_text(encoding="utf-8")
        cargo = cargo.replace("skjol_runtime_template", module_name)
        cargo_path.write_text(cargo, encoding="utf-8")

        lib_path = crate / "src" / "lib.rs"
        lib_source = lib_path.read_text(encoding="utf-8")
        lib_path.write_text(
            lib_source.replace("skjol_runtime_template", module_name),
            encoding="utf-8",
        )
        key_values = ", ".join(str(value) for value in root_key)
        (crate / "src" / "root_key.rs").write_text(
            f"pub const ROOT_KEY: [u8; 32] = [{key_values}];\n",
            encoding="utf-8",
        )

    @staticmethod
    def _build_wheel(crate: Path, wheels: Path, cargo_target: Path) -> Path:
        wheels.mkdir()
        environment = os.environ.copy()
        environment["CARGO_TARGET_DIR"] = str(cargo_target)
        environment["PYO3_PYTHON"] = sys.executable
        command = [
            sys.executable,
            "-m",
            "maturin",
            "build",
            "--release",
            "--locked",
            "--interpreter",
            sys.executable,
            "--out",
            str(wheels),
        ]
        completed = subprocess.run(
            command,
            cwd=crate,
            env=environment,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if completed.returncode != 0:
            diagnostic = RustRuntimeCompiler._safe_diagnostic(completed.stderr or completed.stdout)
            raise RustRuntimeError(f"Rust runtime build failed: {diagnostic}")
        built_wheels = list(wheels.glob("*.whl"))
        if len(built_wheels) != 1:
            raise RustRuntimeError(f"Rust runtime build produced {len(built_wheels)} wheels; expected one")
        return built_wheels[0]

    @staticmethod
    def _extract_extension(wheel: Path, module_name: str, output_dir: Path) -> Path:
        with zipfile.ZipFile(wheel) as archive:
            candidates = [
                member
                for member in archive.namelist()
                if Path(member).name.startswith(f"{module_name}.")
                and Path(member).suffix.lower() in {".pyd", ".so"}
            ]
            if len(candidates) != 1:
                raise RustRuntimeError(
                    f"Rust runtime wheel contains {len(candidates)} matching extensions; expected one"
                )
            member = candidates[0]
            destination = output_dir / Path(member).name
            destination.write_bytes(archive.read(member))
            return destination

    @staticmethod
    def _safe_diagnostic(output: str) -> str:
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return " | ".join(lines[-8:])[:2000] or "no compiler diagnostic was produced"


class RustRuntimeBackend:
    """Apply Skjol transformations and package them for the Rust loader."""

    def __init__(
        self,
        obfuscator: "Obfuscator",
        *,
        root_key: Optional[bytes] = None,
        runtime_id: Optional[str] = None,
        compiler: Optional[RustRuntimeCompiler] = None,
    ):
        self.obfuscator = obfuscator
        self.root_key = root_key or os.urandom(32)
        self.runtime_id = runtime_id or base64.b32encode(os.urandom(5)).decode("ascii").lower().rstrip("=")
        self.artifacts = NativeArtifactBuilder(self.root_key, self.runtime_id)
        self.compiler = compiler or RustRuntimeCompiler()
        self._validate_configuration()

    def protect_source(self, source: str, filename: str) -> ProtectedArtifact:
        transformed = self.obfuscator.obfuscate_source(source)
        return self.artifacts.protect_source(
            transformed,
            filename,
            license_info=self.obfuscator.config.get("license_info", "Protected by Skjol"),
            anti_debug=bool(self.obfuscator.config.get("anti_debug", True)),
        )

    def protect_file(self, input_path: Path, output_path: Path) -> RuntimeBuildResult:
        source = input_path.read_text(encoding="utf-8")
        artifact = self.protect_source(source, input_path.name)
        with tempfile.TemporaryDirectory(prefix="skjol-native-output-") as temporary:
            staging = Path(temporary)
            build = self.compiler.build(artifact.module_name, self.root_key, staging)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            destination = output_path.parent / build.extension_path.name
            shutil.copy2(build.extension_path, destination)
            output_path.write_text(artifact.launcher, encoding="utf-8")
        return RuntimeBuildResult(
            module_name=build.module_name,
            extension_path=destination,
            wheel_name=build.wheel_name,
            python_tag=build.python_tag,
        )

    def protect_directory(
        self,
        input_path: Path,
        output_path: Path,
        *,
        recursive: bool,
        exclude_patterns: Optional[list[str]],
    ) -> dict[str, Any]:
        patterns = (exclude_patterns or []) + DEFAULT_EXCLUDE_PATTERNS
        files = self.obfuscator.file_processor.collect_python_files(input_path, recursive, patterns)
        self.obfuscator._collect_directory_definitions(files)
        launchers: dict[Path, str] = {}
        for source_path, relative_path in files:
            source = source_path.read_text(encoding="utf-8")
            launchers[relative_path] = self.protect_source(source, str(relative_path)).launcher

        with tempfile.TemporaryDirectory(prefix="skjol-native-directory-") as temporary:
            staging = Path(temporary)
            build = self.compiler.build(self.artifacts.module_name, self.root_key, staging)
            runtime_directories: set[Path] = set()
            for relative_path, launcher in launchers.items():
                target = staging / "output" / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(launcher, encoding="utf-8")
                runtime_directories.add(target.parent)
            for directory in runtime_directories:
                shutil.copy2(build.extension_path, directory / build.extension_path.name)
            output_path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(staging / "output", output_path, dirs_exist_ok=True)

        return {
            "files": {str(relative): "success" for relative in launchers},
            "runtime": output_path / build.extension_path.name,
        }

    def _validate_configuration(self) -> None:
        unsupported = []
        if self.obfuscator.config.get("expiration_date") is not None:
            unsupported.append("expiration")
        if self.obfuscator.config.get("allowed_machines"):
            unsupported.append("machine binding")
        if self.obfuscator.config.get("domain_lock"):
            unsupported.append("domain locking")
        if self.obfuscator.config.get("use_whitebox"):
            unsupported.append("white-box payload encryption")
        if self.obfuscator.config.get("code_virtualization"):
            unsupported.append("code virtualization")
        if unsupported:
            raise RustRuntimeError(
                "Rust runtime does not yet support: " + ", ".join(unsupported)
            )
