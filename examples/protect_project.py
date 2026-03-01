"""
Example: Apply PYD (compiled runtime) protection to a sample project.

Creates a temporary sample project, protects it with PYD compilation,
and demonstrates the full protection pipeline.
"""

import sys
import shutil
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscator.pyd_protection import PydRuntimeProtector


def create_sample_project(project_dir: Path) -> None:
    """Create a small sample project to protect."""
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "__init__.py").write_text(
        'from .engine import DataEngine\n'
        '\n'
        '__version__ = "1.0.0"\n'
    )

    (project_dir / "engine.py").write_text(
        '"""Data processing engine with proprietary logic."""\n'
        '\n'
        '\n'
        'class DataEngine:\n'
        '    """Core engine - this is the code we want to protect."""\n'
        '\n'
        '    SECRET_FACTOR = 42\n'
        '\n'
        '    def __init__(self, seed: int = 7):\n'
        '        self.seed = seed\n'
        '        self._state = seed * self.SECRET_FACTOR\n'
        '\n'
        '    def transform(self, values: list) -> list:\n'
        '        """Apply proprietary transformation."""\n'
        '        return [\n'
        '            (v * self._state + self.seed) % 1000\n'
        '            for v in values\n'
        '        ]\n'
        '\n'
        '    def verify(self, original: list, transformed: list) -> bool:\n'
        '        """Verify transformation integrity."""\n'
        '        expected = self.transform(original)\n'
        '        return expected == transformed\n'
    )

    (project_dir / "main.py").write_text(
        '"""Entry point."""\n'
        '\n'
        'from .engine import DataEngine\n'
        '\n'
        '\n'
        'def run():\n'
        '    engine = DataEngine(seed=13)\n'
        '    data = [10, 20, 30, 40, 50]\n'
        '    result = engine.transform(data)\n'
        '    print(f"Input:       {data}")\n'
        '    print(f"Transformed: {result}")\n'
        '    print(f"Verified:    {engine.verify(data, result)}")\n'
        '\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    run()\n'
    )


def main():
    """Protect the sample project with PYD runtime."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="pyobf_pyd_example_"))
    project_dir = tmp_dir / "sample_project"
    output_dir = tmp_dir / "pyd_protected" / "sample_project"

    try:
        create_sample_project(project_dir)

        print("=" * 60)
        print("PyObfuscator v2.0 - PYD Runtime Protection Example")
        print("=" * 60)
        print(f"Input:  {project_dir}")
        print(f"Output: {output_dir}")
        print()

        protector = PydRuntimeProtector(
            license_info="sample-project-protected"
        )

        print(f"Runtime ID: {protector.runtime_id}")
        print()

        exclude_patterns = [
            '__pycache__',
            '*.pyc',
            'test_*.py',
            '*_test.py',
        ]

        # Check for Cython
        try:
            import Cython
            has_cython = True
            print("Cython found - will build .pyd runtime")
        except ImportError:
            has_cython = False
            print("Cython not found - will create .pyx source and fallback .py runtime")

        print("\nProcessing files...")
        results = protector.protect_directory(
            project_dir,
            output_dir,
            recursive=True,
            exclude_patterns=exclude_patterns,
            build_pyd=has_cython,
        )

        if not results.get('pyd'):
            print("\nCreating fallback Python runtime...")
            fallback = protector.create_fallback_py_runtime(output_dir)
            results['fallback_py'] = fallback

        success_count = 0
        error_count = 0

        for file_path, result in sorted(results['files'].items()):
            if result == "success":
                print(f"  ✓ {file_path}")
                success_count += 1
            else:
                print(f"  ✗ {file_path}: {result}")
                error_count += 1

        print()
        if results.get('pyd'):
            print(f"PYD runtime: {results['pyd']}")
        if results.get('pyx'):
            print(f"Cython source: {results['pyx']}")
        if results.get('setup'):
            print(f"Setup script: {results['setup']}")
        if results.get('fallback_py'):
            print(f"Fallback runtime: {results['fallback_py']}")

        print()
        print("Protection complete!")
        print(f"  Files processed: {success_count}")
        print(f"  Errors: {error_count}")

        if not has_cython:
            print()
            print("To build the .pyd runtime manually:")
            print("  1. Install Cython: pip install cython")
            print(f"  2. cd {output_dir}")
            print("  3. python setup.py build_ext --inplace")

        return 0 if error_count == 0 else 1

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
