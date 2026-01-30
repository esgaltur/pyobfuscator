"""
Demo of PYD (compiled runtime) protection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscate.pyd_protection import PydRuntimeProtector


def main():
    sample_code = '''
def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"  fib({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()
'''

    print("=" * 60)
    print("PYD Runtime Protection Demo")
    print("=" * 60)

    protector = PydRuntimeProtector(license_info="demo")

    # Generate protected code and Cython source
    protected, pyx, setup = protector.protect_source(sample_code, "demo.py")

    print("\n[PROTECTED CODE]")
    print("-" * 60)
    print(protected)

    print("\n[CYTHON SOURCE (.pyx)]")
    print("-" * 60)
    # Show first 80 lines
    pyx_lines = pyx.split('\n')[:80]
    print('\n'.join(pyx_lines))
    print("... (truncated)")

    print("\n[SETUP.PY]")
    print("-" * 60)
    print(setup)

    # Test with fallback Python runtime
    print("\n[TESTING WITH FALLBACK PYTHON RUNTIME]")
    print("-" * 60)

    output_dir = Path(__file__).parent.parent / "build" / "pyd_demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write protected file
    protected_file = output_dir / "demo.py"
    with open(protected_file, 'w') as f:
        f.write(protected)

    # Create fallback runtime
    runtime_file = protector.create_fallback_py_runtime(output_dir)
    print(f"Created fallback runtime: {runtime_file}")

    # Execute
    print("\nExecuting protected code...\n")
    sys.path.insert(0, str(output_dir))
    try:
        exec(open(protected_file).read(), {'__name__': '__main__', '__file__': str(protected_file)})
    finally:
        sys.path.remove(str(output_dir))

    print("\n" + "=" * 60)
    print("To build the .pyd runtime (requires Cython + C compiler):")
    print(f"  cd {output_dir}")
    print("  pip install cython")
    print("  python setup.py build_ext --inplace")
    print("=" * 60)


if __name__ == "__main__":
    main()
