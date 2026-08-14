"""Tests for the local PowerShell release entry point."""

import shutil
import subprocess
from pathlib import Path

import pytest

from pyobfuscator._version import __version__


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
RELEASE_SCRIPT = PROJECT_ROOT / "scripts" / "release.ps1"


@pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is required")
def test_release_plan_uses_the_single_version_source() -> None:
    result = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-File",
            str(RELEASE_SCRIPT),
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
            str(RELEASE_SCRIPT),
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


def test_remote_tag_check_does_not_depend_on_an_expected_404() -> None:
    script = RELEASE_SCRIPT.read_text(encoding="utf-8")

    assert "git/matching-refs/tags/$Tag" in script
    assert "'--jq',\n        '.[].ref'" in script
    assert "select(.ref ==" not in script
    assert "git/ref/tags/$Tag" not in script
    assert "Test-GitHubApiResource" not in script
