"""
Demo script showing PyObfuscate in action.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscate import Obfuscator


def main():
    # Sample code to obfuscate
    sample_code = '''
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    previous = 0
    current = 1
    for i in range(2, n + 1):
        next_value = previous + current
        previous = current
        current = next_value
    return current


def format_result(number, result):
    """Format the result nicely."""
    message = f"Fibonacci({number}) = {result}"
    return message


def main():
    test_numbers = [5, 10, 15, 20]
    for num in test_numbers:
        fib = calculate_fibonacci(num)
        output = format_result(num, fib)
        print(output)


if __name__ == "__main__":
    main()
'''

    print("=" * 60)
    print("ORIGINAL CODE:")
    print("=" * 60)
    print(sample_code)

    # Create obfuscator with different settings
    obfuscator = Obfuscator(
        rename_variables=True,
        rename_functions=True,
        rename_classes=True,
        obfuscate_strings=False,  # Keep strings readable for demo
        compress_code=False,
        remove_docstrings=True,
        name_style="random"
    )

    obfuscated = obfuscator.obfuscate_source(sample_code)

    print("\n" + "=" * 60)
    print("OBFUSCATED CODE (names obfuscated, strings readable):")
    print("=" * 60)
    print(obfuscated)

    # Test that it still works
    print("\n" + "=" * 60)
    print("EXECUTION OF OBFUSCATED CODE:")
    print("=" * 60)
    exec(obfuscated, {})

    # Now with string obfuscation
    obfuscator2 = Obfuscator(
        rename_variables=True,
        rename_functions=True,
        obfuscate_strings=True,
        string_method="base64",
        remove_docstrings=True,
        name_style="hex"
    )

    obfuscated2 = obfuscator2.obfuscate_source(sample_code)

    print("\n" + "=" * 60)
    print("OBFUSCATED CODE (with string encoding, hex names):")
    print("=" * 60)
    print(obfuscated2)

    # Show compressed version
    obfuscator3 = Obfuscator(
        rename_variables=True,
        rename_functions=True,
        obfuscate_strings=True,
        compress_code=True,
        remove_docstrings=True,
    )

    compressed = obfuscator3.obfuscate_source(sample_code)

    print("\n" + "=" * 60)
    print("COMPRESSED CODE (single exec statement):")
    print("=" * 60)
    print(compressed)


if __name__ == "__main__":
    main()
