#!/usr/bin/env python3
"""
Release script for pyobfuscator package.
This script builds and publishes the package to PyPI or TestPyPI.

Usage:
    python publish.py --test    # Publish to TestPyPI
    python publish.py           # Publish to PyPI
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Error: {description} failed!")
        sys.exit(1)
    print(f"✅ {description} completed successfully!")
    return result


def clean_build():
    """Clean previous build artifacts."""
    print("\n🧹 Cleaning previous build artifacts...")
    for pattern in ['dist', 'build', '*.egg-info']:
        run_command(
            f'powershell -Command "if (Test-Path {pattern}) {{ Remove-Item -Recurse -Force {pattern} }}"',
            f"Cleaning {pattern}"
        )


def build_package():
    """Build the package."""
    run_command("python -m build", "Building package")


def check_package():
    """Check package with twine."""
    run_command("python -m twine check dist/*", "Checking package")


def publish_package(test=False):
    """Publish package to PyPI or TestPyPI."""
    if test:
        repository = "testpypi"
        url = "https://test.pypi.org/legacy/"
        print("\n📦 Publishing to TestPyPI...")
        print("Install with: pip install --index-url https://test.pypi.org/simple/ pyobfuscator")
    else:
        repository = "pypi"
        url = "https://upload.pypi.org/legacy/"
        print("\n📦 Publishing to PyPI...")
        print("Install with: pip install pyobfuscator")

    cmd = f"python -m twine upload dist/* --repository {repository}"
    if test:
        cmd += f" --repository-url {url}"

    print("\n⚠️  You will be prompted for your PyPI credentials.")
    print("💡 Tip: Use an API token for better security!")
    print("   Set up at: https://pypi.org/manage/account/token/")

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("\n❌ Publishing failed!")
        print("\n💡 Make sure you have:")
        print("   1. Created an account on PyPI")
        print("   2. Set up your credentials (use 'python -m twine upload --help' for options)")
        print("   3. Or create a .pypirc file in your home directory")
        sys.exit(1)

    print("\n🎉 Package published successfully!")


def main():
    parser = argparse.ArgumentParser(description="Build and publish pyobfuscator package")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Publish to TestPyPI instead of PyPI"
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip building and just publish existing dist/"
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip cleaning previous build artifacts"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🐍 PyObfuscator Package Release Script")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)

    try:
        if not args.skip_build:
            if not args.skip_clean:
                clean_build()
            build_package()
            check_package()

        # Ask for confirmation before publishing
        target = "TestPyPI" if args.test else "PyPI"
        print(f"\n⚠️  Ready to publish to {target}")
        response = input("Continue? (yes/no): ").strip().lower()

        if response in ['yes', 'y']:
            publish_package(test=args.test)
        else:
            print("❌ Publishing cancelled.")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
