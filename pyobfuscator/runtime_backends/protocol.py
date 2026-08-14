"""Shared result types for runtime backends."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeBuildResult:
    """Auditable output from one native runtime build."""

    module_name: str
    extension_path: Path
    wheel_name: str
    python_tag: str
