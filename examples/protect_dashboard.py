"""
Script to apply PYD (compiled runtime) protection to github_pr_dashboard.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscator.pyd_protection import PydRuntimeProtector


def main():
    """Protect the github_pr_dashboard project with PYD runtime."""
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "github_pr_dashboard"
    output_dir = project_root / "build" / "pyd_protected" / "github_pr_dashboard"

    print("=" * 60)
    print("PyObfuscator PYD Runtime Protection")
    print("=" * 60)
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print()

    # Create protector with project-specific settings
    protector = PydRuntimeProtector(
        license_info="github_pr_dashboard-protected"
    )

    print(f"Runtime ID: {protector.runtime_id}")
    print()

    # Exclude patterns
    exclude_patterns = [
        '__pycache__',
        '*.pyc',
        'test_*.py',
        '*_test.py',
        'tests/*',
        'tools/*',
        'docs/*',
    ]

    print("Processing files...")

    # First try to build with PYD (requires Cython)
    try:
        import Cython
        has_cython = True
        print("Cython found - will build .pyd runtime")
    except ImportError:
        has_cython = False
        print("Cython not found - will create .pyx source and fallback .py runtime")

    results = protector.protect_directory(
        input_dir,
        output_dir,
        recursive=True,
        exclude_patterns=exclude_patterns,
        build_pyd=has_cython
    )

    # If no .pyd was built, create fallback .py runtime
    if not results.get('pyd'):
        print("\nCreating fallback Python runtime...")
        fallback = protector.create_fallback_py_runtime(output_dir)
        results['fallback_py'] = fallback

    # Print results
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

    if error_count > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
