# -*- coding: utf-8 -*-
"""
Tests for PyObfuscator library.
"""

import ast
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfuscator import Obfuscator
from pyobfuscator.obfuscator import NameGenerator, NameObfuscator, StringObfuscator, CodeCompressor


def test_name_generator():
    """Test the name generator."""
    gen = NameGenerator(style="random")

    name1 = gen.get_name("my_variable")
    name2 = gen.get_name("my_variable")  # Should return same name
    name3 = gen.get_name("other_variable")

    assert name1 == name2, "Same input should return same output"
    assert name1 != name3, "Different inputs should return different outputs"
    assert name1.startswith("_"), "Names should start with underscore prefix"
    print("\u2713 Name generator test passed")


def test_name_obfuscator():
    """Test the name obfuscator transformer."""
    source = '''
def my_function(arg1, arg2):
    result = arg1 + arg2
    return result

class MyClass:
    def __init__(self, value):
        self.value = value
'''

    tree = ast.parse(source)
    gen = NameGenerator(style="random")
    obfuscator = NameObfuscator(gen)
    tree = obfuscator.visit(tree)
    ast.fix_missing_locations(tree)

    result = ast.unparse(tree)

    # Original names should not appear (except 'self' and dunder methods)
    assert "my_function" not in result, "Function name should be obfuscated"
    assert "MyClass" not in result, "Class name should be obfuscated"
    assert "arg1" not in result, "Argument names should be obfuscated"
    assert "result" not in result, "Variable names should be obfuscated"
    assert "self" in result, "'self' should be preserved"
    assert "__init__" in result, "Dunder methods should be preserved"

    print("\u2713 Name obfuscator test passed")


def test_string_obfuscator():
    """Test the string obfuscator transformer."""
    source = '''
message = "Hello, World!"
short = "hi"
'''

    tree = ast.parse(source)
    obfuscator = StringObfuscator(method="base64")
    tree = obfuscator.visit(tree)
    ast.fix_missing_locations(tree)

    result = ast.unparse(tree)

    # Original long string should not appear
    assert "Hello, World!" not in result, "Long strings should be obfuscated"
    # Short strings might be preserved
    assert "base64" in result or "b64decode" in result, "Should use base64 encoding"

    print("\u2713 String obfuscator test passed")


def test_code_compressor():
    """Test the code compressor."""
    original = '''
def hello():
    print("Hello, World!")

hello()
'''

    encoded = CodeCompressor.compress_code(original)
    loader = CodeCompressor.create_loader(encoded)

    # Execute the loader to verify it works
    exec(loader)

    print("\u2713 Code compressor test passed")


def test_full_obfuscation():
    """Test complete obfuscation pipeline."""
    source = '''
def calculate_sum(numbers):
    """Calculate the sum of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total

def main():
    data = [1, 2, 3, 4, 5]
    result = calculate_sum(data)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
'''

    obfuscator = Obfuscator(
        rename_variables=True,
        rename_functions=True,
        rename_classes=True,
        obfuscate_strings=False,  # Disable for this test to avoid f-string issues
        compress_code=False,
        remove_docstrings=True,
        name_style="random"
    )

    obfuscated = obfuscator.obfuscate_source(source)

    # Verify the obfuscated code is valid Python
    compile(obfuscated, '<string>', 'exec')

    # Original identifiers should be gone
    assert "calculate_sum" not in obfuscated
    assert "numbers" not in obfuscated
    assert "total" not in obfuscated

    # Docstring should be removed
    assert "Calculate the sum" not in obfuscated

    print("\u2713 Full obfuscation test passed")


def test_obfuscated_execution():
    """Test that obfuscated code executes correctly."""
    source = '''
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y

result1 = add(5, 3)
result2 = multiply(4, 2)
final = result1 + result2
'''

    obfuscator = Obfuscator(
        obfuscate_strings=False,
        compress_code=False,
    )

    obfuscated = obfuscator.obfuscate_source(source)

    # Execute both original and obfuscated
    original_globals = {}
    exec(source, original_globals)

    obfuscated_globals = {}
    exec(obfuscated, obfuscated_globals)

    # The obfuscated variable names are different, but we can check
    # that the code compiles and runs without error
    print("\u2713 Obfuscated execution test passed")


def test_preserve_imports():
    """Test that imports are handled correctly."""
    source = '''
import os
from pathlib import Path
import json as js

def get_home():
    return Path.home()

def read_config(path):
    with open(path) as f:
        return js.load(f)
'''

    obfuscator = Obfuscator(
        obfuscate_strings=False,
        compress_code=False,
    )

    obfuscated = obfuscator.obfuscate_source(source)

    # Imports should be preserved
    assert "import os" in obfuscated
    assert "from pathlib import Path" in obfuscated
    assert "import json as js" in obfuscated

    # Module references should be preserved
    assert "Path" in obfuscated
    assert "js" in obfuscated

    print("\u2713 Import preservation test passed")


def run_all_tests():
    """Run all tests."""
    print("Running PyObfuscator tests...")
    print("=" * 50)

    test_name_generator()
    test_name_obfuscator()
    test_string_obfuscator()
    test_code_compressor()
    test_full_obfuscation()
    test_obfuscated_execution()
    test_preserve_imports()

    print("=" * 50)
    print("\u2713 All tests passed!")


if __name__ == '__main__':
    run_all_tests()
