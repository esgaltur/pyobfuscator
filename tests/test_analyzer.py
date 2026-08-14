"""Focused tests for project-analysis collaborators and orchestration."""

import tomllib
from pathlib import Path

from pyobfuscator.analyzer import ModuleInfo, ProjectAnalyzer


def write_source(project: Path, content: str, name: str = "app.py") -> Path:
    source = project / name
    source.write_text(content, encoding="utf-8")
    return source


def test_pyproject_dependency_layouts_detect_frameworks(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["Flask>=3", "httpx>=0.27"]

[project.optional-dependencies]
cli = ["typer>=0.12"]

[tool.poetry.dependencies]
python = "^3.12"
PySide6 = "^6.7"

[tool.poetry.dev-dependencies]
SQLAlchemy = "^2"
""".strip(),
        encoding="utf-8",
    )

    analysis = ProjectAnalyzer(tmp_path).analyze()

    assert analysis.detected_frameworks == {
        "asyncio",
        "click",
        "flask",
        "pyside6",
        "sqlalchemy",
    }


def test_ast_processing_collects_imports_exports_and_public_definitions(tmp_path: Path) -> None:
    source = write_source(
        tmp_path,
        """
import PySide6.QtCore
from fastapi import FastAPI, Depends
from local_module import *

__all__ = ["published", 42]

async def main():
    return None

def helper():
    return None

def _private():
    return None

def test_internal():
    return None

class DesktopWindow:
    pass

class TestWindow:
    pass
""".strip(),
    )

    analysis = ProjectAnalyzer(tmp_path).analyze()
    module = analysis.modules[str(source)]

    assert module.imports == {"PySide6", "fastapi", "local_module"}
    assert module.from_imports == {
        "fastapi": {"FastAPI", "Depends"},
        "local_module": set(),
    }
    assert module.exports == {"published"}
    assert module.public_names == {"main", "helper", "DesktopWindow"}
    assert module.entry_points == {"main", "DesktopWindow"}
    assert analysis.public_api == {"published"}
    assert {"pyside6", "fastapi"}.issubset(analysis.detected_frameworks)


def test_only_real_main_guard_calls_become_additional_entry_points(tmp_path: Path) -> None:
    write_source(
        tmp_path,
        """
ENABLED = True

def launch_service():
    return None

def unrelated_branch():
    return None

if ENABLED:
    unrelated_branch()

if "__main__" == __name__:
    launch_service()
""".strip(),
    )

    analysis = ProjectAnalyzer(tmp_path).analyze()

    assert "launch_service" in analysis.entry_points
    assert "unrelated_branch" not in analysis.entry_points


def test_toml_formatter_escapes_values_and_keeps_metadata_as_comments(tmp_path: Path) -> None:
    analyzer = ProjectAnalyzer(tmp_path)
    config = {
        "frameworks": ["flask", 'quote"value'],
        "windows_path": r"C:\protected\app",
        "compress": False,
        "intensity": 3,
        "ratio": 1.5,
        "_metadata": {
            "generated_by": "skjol analyzer",
            "warnings": ["first line\nsecond line"],
        },
    }

    content = analyzer._dict_to_toml(config)
    parsed = tomllib.loads(content)

    assert parsed == {
        "frameworks": ["flask", 'quote"value'],
        "windows_path": r"C:\protected\app",
        "compress": False,
        "intensity": 3,
        "ratio": 1.5,
    }
    assert "# generated_by: skjol analyzer" in content
    assert "# warnings: first line" in content
    assert "# warnings: second line" in content


def test_print_summary_renders_sorted_preview_and_all_messages(
    tmp_path: Path,
    capsys,
) -> None:
    analyzer = ProjectAnalyzer(tmp_path)
    module_path = tmp_path / "app.py"
    analyzer.analysis.modules[str(module_path)] = ModuleInfo(module_path, "app")
    analyzer.analysis.detected_frameworks.update({"flask", "click"})
    analyzer.analysis.entry_points.update(f"entry_{index:02d}" for index in range(12))
    analyzer.analysis.public_api.add("public_name")
    analyzer.analysis.warnings.append("example warning")
    analyzer.analysis.recommendations.append("example recommendation")

    analyzer.print_summary()
    output = capsys.readouterr().out

    assert f"Project Analysis: {tmp_path.name}" in output
    assert "Total Python files: 1" in output
    assert output.index("  - click") < output.index("  - flask")
    assert "Entry points (12):" in output
    assert "  - entry_09" in output
    assert "  - entry_10" not in output
    assert "  ... and 2 more" in output
    assert "  ! example warning" in output
    assert "  * example recommendation" in output
