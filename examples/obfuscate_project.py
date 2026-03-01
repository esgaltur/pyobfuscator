#!/usr/bin/env python
"""
Example: Obfuscate a sample project directory using PyObfuscator.

Creates a temporary sample project, applies obfuscation, and shows the results.
"""

import sys
import shutil
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscator import Obfuscator


def create_sample_project(project_dir: Path) -> None:
    """Create a small sample project to obfuscate."""
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "__init__.py").write_text(
        'from .core import Engine\n'
        'from .utils import format_output\n'
        '\n'
        '__version__ = "1.0.0"\n'
    )

    (project_dir / "core.py").write_text(
        '"""Core engine for data processing."""\n'
        '\n'
        '\n'
        'class Engine:\n'
        '    """Process and transform data records."""\n'
        '\n'
        '    def __init__(self, multiplier: int = 2):\n'
        '        self.multiplier = multiplier\n'
        '        self._history = []\n'
        '\n'
        '    def process(self, values: list) -> list:\n'
        '        """Apply transformation to each value."""\n'
        '        results = []\n'
        '        for value in values:\n'
        '            transformed = value * self.multiplier\n'
        '            results.append(transformed)\n'
        '            self._history.append((value, transformed))\n'
        '        return results\n'
        '\n'
        '    def summary(self) -> dict:\n'
        '        """Return processing summary."""\n'
        '        total_in = sum(v for v, _ in self._history)\n'
        '        total_out = sum(v for _, v in self._history)\n'
        '        return {\n'
        '            "records": len(self._history),\n'
        '            "total_input": total_in,\n'
        '            "total_output": total_out,\n'
        '            "multiplier": self.multiplier,\n'
        '        }\n'
    )

    (project_dir / "utils.py").write_text(
        '"""Utility functions for formatting and validation."""\n'
        '\n'
        '\n'
        'def format_output(data: dict) -> str:\n'
        '    """Format a dictionary into a readable report."""\n'
        '    lines = ["=== Report ==="]\n'
        '    for key, value in data.items():\n'
        '        label = key.replace("_", " ").title()\n'
        '        lines.append(f"  {label}: {value}")\n'
        '    lines.append("==============")\n'
        '    return "\\n".join(lines)\n'
        '\n'
        '\n'
        'def validate_input(values: list) -> bool:\n'
        '    """Check that all values are positive numbers."""\n'
        '    return all(isinstance(v, (int, float)) and v > 0 for v in values)\n'
    )

    (project_dir / "main.py").write_text(
        '"""Entry point for the sample project."""\n'
        '\n'
        'from .core import Engine\n'
        'from .utils import format_output, validate_input\n'
        '\n'
        '\n'
        'def run():\n'
        '    data = [10, 20, 30, 40, 50]\n'
        '\n'
        '    if not validate_input(data):\n'
        '        print("Invalid input data")\n'
        '        return\n'
        '\n'
        '    engine = Engine(multiplier=3)\n'
        '    results = engine.process(data)\n'
        '\n'
        '    print(f"Input:   {data}")\n'
        '    print(f"Output:  {results}")\n'
        '    print()\n'
        '    print(format_output(engine.summary()))\n'
        '\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    run()\n'
    )


def main():
    """Obfuscate the sample project directory."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="pyobf_example_"))
    project_dir = tmp_dir / "sample_project"
    output_dir = tmp_dir / "obfuscated" / "sample_project"

    try:
        create_sample_project(project_dir)

        print("=" * 55)
        print("PyObfuscator v2.0 - Directory Obfuscation Example")
        print("=" * 55)
        print(f"Input:  {project_dir}")
        print(f"Output: {output_dir}")
        print()

        obfuscator = Obfuscator(
            rename_variables=True,
            rename_functions=True,
            rename_classes=True,
            obfuscate_strings=True,
            compress_code=False,
            remove_docstrings=True,
            name_style="random",
            string_method="xor",
        )

        exclude_patterns = [
            '__pycache__',
            '*.pyc',
            'test_*.py',
            '*_test.py',
        ]

        print("Processing files...")
        results = obfuscator.obfuscate_directory(
            project_dir,
            output_dir,
            recursive=True,
            exclude_patterns=exclude_patterns,
        )

        success_count = 0
        error_count = 0

        for file_path, result in sorted(results.items()):
            if result == "success":
                print(f"  ✓ {file_path}")
                success_count += 1
            else:
                print(f"  ✗ {file_path}: {result}")
                error_count += 1

        print()
        print("Obfuscation complete!")
        print(f"  Files processed: {success_count}")
        print(f"  Errors: {error_count}")

        # Show a sample of the obfuscated output
        obfuscated_core = output_dir / "core.py"
        if obfuscated_core.exists():
            print()
            print("Sample obfuscated output (core.py):")
            print("-" * 55)
            content = obfuscated_core.read_text()
            print(content[:600])
            if len(content) > 600:
                print("...")

        return 0 if error_count == 0 else 1

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
