"""Tests for the local PowerShell release entry point."""

import shutil
import subprocess
from pathlib import Path

import pytest

from pyobfuscator._version import __version__


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


@pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is required")
def test_release_plan_uses_the_single_version_source() -> None:
    result = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-File",
            str(PROJECT_ROOT / "scripts" / "release.ps1"),
            "-PlanOnly",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert f"Version: {__version__}" in result.stdout
    assert f"Tag:     v{__version__}" in result.stdout
    assert "no tests, build, or GitHub operation was performed" in result.stdout


@pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is required")
def test_plan_only_rejects_a_publishing_mode() -> None:
    result = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-File",
            str(PROJECT_ROOT / "scripts" / "release.ps1"),
            "-PlanOnly",
            "-Mode",
            "Publish",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert "PlanOnly can only be used with -Mode Validate" in result.stderr
