# -*- coding: utf-8 -*-
"""
End-to-End Integration Tests for PyObfuscator.

These tests create real projects, apply obfuscation (with optional encryption),
verify the protected code works correctly, and clean up.

Test scenarios:
1. Single file obfuscation with all advanced features
2. Multi-file project obfuscation with cross-file imports
3. CLI-based obfuscation
4. Encryption protection (via RuntimeProtector directly)
"""
import pytest
import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyobfuscator import Obfuscator, RuntimeProtector


class TestE2ESingleFileObfuscation:
    """End-to-end tests for single file obfuscation (without encryption)."""

    def test_single_file_full_obfuscation(self):
        """Test full obfuscation pipeline on a single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create a simple Python file
            source_file = tmpdir / "calculator.py"
            source_file.write_text('''
def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def calculate(x, y, operation):
    """Perform calculation based on operation."""
    if operation == "add":
        return add(x, y)
    elif operation == "multiply":
        return multiply(x, y)
    else:
        raise ValueError(f"Unknown operation: {operation}")

# Test the functions
result1 = add(10, 20)
result2 = multiply(5, 6)
result3 = calculate(3, 4, "add")

# Assertions
assert result1 == 30, f"Expected 30, got {result1}"
assert result2 == 30, f"Expected 30, got {result2}"
assert result3 == 7, f"Expected 7, got {result3}"

print("Calculator test passed!")
''')

            # Create obfuscator with all features but NO encryption
            obfuscator = Obfuscator(
                encrypt_code=False,
                control_flow=True,
                number_obfuscation=True,
                builtin_obfuscation=True,
                obfuscation_intensity=2
            )

            # Read source and obfuscate
            source = source_file.read_text()
            obfuscated = obfuscator.obfuscate_source(source)

            # Write obfuscated file
            output_file = tmpdir / "calculator_obf.py"
            output_file.write_text(obfuscated)

            # Verify the code is obfuscated
            assert "def add" not in obfuscated
            assert "multiply" not in obfuscated
            assert "calculate" not in obfuscated

            # Execute the obfuscated code
            result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Should execute without errors
            assert result.returncode == 0, f"Obfuscated code failed: {result.stderr}"
            assert "Calculator test passed!" in result.stdout

    def test_single_file_with_all_advanced_features(self):
        """Test obfuscation with all advanced features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source = '''
def fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b

def is_prime(n):
    """Check if n is prime."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

# Test
fib_10 = fibonacci(10)
prime_check = is_prime(17)

# Verify
assert fib_10 == 55, f"Expected 55, got {fib_10}"
assert prime_check == True, f"Expected True, got {prime_check}"
print("All math tests passed!")
'''

            # Create obfuscator with ALL features enabled (except encryption)
            obfuscator = Obfuscator(
                encrypt_code=False,
                control_flow=True,
                control_flow_flatten=True,
                number_obfuscation=True,
                builtin_obfuscation=True,
                integrity_check=True,
                obfuscation_intensity=3
            )

            obfuscated = obfuscator.obfuscate_source(source)

            # Write file
            output_file = tmpdir / "math_test.py"
            output_file.write_text(obfuscated)

            # Execute
            result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0, f"Failed: {result.stderr}"
            assert "All math tests passed!" in result.stdout


class TestE2EMultiFileProject:
    """End-to-end tests for multi-file project obfuscation."""

    def test_multi_file_project_with_imports(self):
        """Test obfuscating a project with multiple files and imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "src"
            output_dir = tmpdir / "dist"
            input_dir.mkdir()

            # Create a multi-file project
            # File 1: utils.py
            (input_dir / "utils.py").write_text('''
def format_number(n):
    """Format a number with commas."""
    return f"{n:,}"

def validate_positive(n):
    """Validate that n is positive."""
    if n <= 0:
        raise ValueError("Number must be positive")
    return n

PI = 3.14159
''')

            # File 2: calculator.py
            (input_dir / "calculator.py").write_text('''
from utils import format_number, validate_positive, PI

def circle_area(radius):
    """Calculate circle area."""
    r = validate_positive(radius)
    return PI * r * r

def format_result(value):
    """Format calculation result."""
    return f"Result: {format_number(int(value))}"
''')

            # File 3: main.py (entry point)
            (input_dir / "main.py").write_text('''
from calculator import circle_area, format_result

def main():
    """Main function."""
    area = circle_area(10)
    formatted = format_result(area)
    print(formatted)
    
    # Verification
    expected_area = 3.14159 * 100
    assert abs(area - expected_area) < 0.001, f"Area mismatch: {area}"
    print("Multi-file test passed!")
    return area

if __name__ == "__main__":
    result = main()
''')

            # Create __init__.py
            (input_dir / "__init__.py").write_text("")

            # Obfuscate the entire directory (no encryption)
            obfuscator = Obfuscator(
                encrypt_code=False,
                control_flow=True,
                obfuscation_intensity=2
            )

            results = obfuscator.obfuscate_directory(
                input_dir,
                output_dir,
                recursive=True
            )

            # Verify all files were processed
            assert all(v == "success" for v in results.values()), f"Some files failed: {results}"

            # Execute the obfuscated main.py
            result = subprocess.run(
                [sys.executable, str(output_dir / "main.py")],
                capture_output=True,
                text=True,
                cwd=str(output_dir),
                timeout=30
            )

            assert result.returncode == 0, f"Obfuscated code failed: {result.stderr}"
            assert "Multi-file test passed!" in result.stdout

    def test_package_with_submodules(self):
        """Test obfuscating a package with submodules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "mypackage"
            output_dir = tmpdir / "dist" / "mypackage"
            input_dir.mkdir()
            output_dir.parent.mkdir(parents=True)

            # Create package structure
            # mypackage/__init__.py
            (input_dir / "__init__.py").write_text('''
from .core import process_data
from .helpers import validate_input

__all__ = ["process_data", "validate_input"]
''')

            # mypackage/core.py
            (input_dir / "core.py").write_text('''
from .helpers import validate_input, transform_value

def process_data(data):
    """Process input data."""
    validated = validate_input(data)
    result = []
    for item in validated:
        result.append(transform_value(item))
    return result
''')

            # mypackage/helpers.py
            (input_dir / "helpers.py").write_text('''
def validate_input(data):
    """Validate input data."""
    if not isinstance(data, list):
        raise TypeError("Data must be a list")
    return [x for x in data if x is not None]

def transform_value(value):
    """Transform a single value."""
    return value * 2 + 1
''')

            # Create test runner outside the package
            test_runner = tmpdir / "run_test.py"
            test_runner.write_text('''
import sys
sys.path.insert(0, "dist")

from mypackage import process_data, validate_input

# Test
data = [1, 2, None, 3, 4]
result = process_data(data)
expected = [3, 5, 7, 9]  # (x * 2 + 1) for x in [1, 2, 3, 4]

assert result == expected, f"Expected {expected}, got {result}"
print(f"Result: {result}")
print("Package test passed!")
''')

            # Obfuscate the package - preserve public API names using entry_points
            obfuscator = Obfuscator(
                encrypt_code=False,
                entry_points=["process_data", "validate_input", "transform_value"],
                obfuscation_intensity=1
            )

            results = obfuscator.obfuscate_directory(
                input_dir,
                output_dir,
                recursive=True
            )

            assert all(v == "success" for v in results.values())

            # Execute test
            result = subprocess.run(
                [sys.executable, str(test_runner)],
                capture_output=True,
                text=True,
                cwd=str(tmpdir),
                timeout=30
            )

            assert result.returncode == 0, f"Package test failed: {result.stderr}"
            assert "Package test passed!" in result.stdout


class TestE2EProtectionComparison:
    """Compare obfuscation with and without encryption."""

    def test_obfuscation_hides_names(self):
        """Test that obfuscation hides function and variable names."""
        source = '''
SECRET_KEY = "my_secret_key_123"
PASSWORD = "admin123"

def authenticate(user, pwd):
    if pwd == PASSWORD:
        return f"Welcome {user}!"
    return "Access denied"

result = authenticate("admin", "admin123")
print(result)
'''

        # Obfuscation only
        obfuscator = Obfuscator(
            encrypt_code=False,
            control_flow=True,
            number_obfuscation=True,
            obfuscation_intensity=3
        )

        obfuscated = obfuscator.obfuscate_source(source)

        # Names should be obfuscated
        assert "SECRET_KEY" not in obfuscated
        assert "PASSWORD" not in obfuscated
        assert "authenticate" not in obfuscated

        # But structure is still Python code
        assert "def " in obfuscated

        # Execute
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.py"
            output_file.write_text(obfuscated)

            result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0
            assert "Welcome admin!" in result.stdout


class TestE2EEncryptionWithRuntimeProtector:
    """Test encryption using RuntimeProtector directly."""

    def test_runtime_protector_encrypts_code(self):
        """Test that RuntimeProtector properly encrypts code."""
        source = '''
VISIBLE_SECRET = "this_should_be_hidden"

def hidden_function():
    return VISIBLE_SECRET

result = hidden_function()
'''

        # Use RuntimeProtector directly
        protector = RuntimeProtector(
            license_info="Test License",
            anti_debug=False  # Disable for testing
        )

        protected, runtime = protector.protect_source(source, "secret.py")

        # The actual code content should NOT be visible
        assert "VISIBLE_SECRET" not in protected
        assert "this_should_be_hidden" not in protected
        assert "hidden_function" not in protected

        # Only the loader should be visible
        assert "__pyobfuscator__" in protected
        assert "pyobfuscator_runtime_" in protected

    def test_runtime_protector_with_obfuscation(self):
        """Test RuntimeProtector with pre-obfuscated code."""
        source = '''
def calculate_secret(x):
    magic_number = 42
    return x * magic_number + 100

result = calculate_secret(10)
assert result == 520, f"Expected 520, got {result}"
'''

        # First obfuscate
        obfuscator = Obfuscator(
            encrypt_code=False,
            number_obfuscation=True,
            obfuscation_intensity=2
        )
        obfuscated = obfuscator.obfuscate_source(source)

        # Verify obfuscation worked
        assert "calculate_secret" not in obfuscated
        assert "magic_number" not in obfuscated

        # Then encrypt
        protector = RuntimeProtector(
            license_info="Test",
            anti_debug=False
        )
        protected, runtime = protector.protect_source(obfuscated, "calc.py")

        # Verify encryption - code structure should be hidden
        assert "def " not in protected  # No function definitions visible
        assert "__pyobfuscator__" in protected  # Loader present


class TestE2ECLI:
    """Test CLI-based obfuscation end-to-end - simulating real-world usage."""

    def test_cli_obfuscate_single_file_no_encrypt(self):
        """Test CLI obfuscation of a single file without encryption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create source file
            source_file = tmpdir / "app.py"
            source_file.write_text('''
def greet(name):
    return f"Hello, {name}!"

message = greet("World")
print(message)
''')

            output_file = tmpdir / "app_obf.py"

            # Run CLI with --no-encrypt
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_file),
                    "--no-encrypt",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Verify output exists and runs
            assert output_file.exists()

            exec_result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert exec_result.returncode == 0
            assert "Hello, World!" in exec_result.stdout

    def test_cli_obfuscate_directory_no_encrypt(self):
        """Test CLI obfuscation of a directory without encryption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "src"
            output_dir = tmpdir / "dist"
            input_dir.mkdir()

            # Create source files
            (input_dir / "module1.py").write_text('''
def func1():
    return "Function 1"
''')

            (input_dir / "module2.py").write_text('''
def func2():
    return "Function 2"
''')

            # Run CLI
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(input_dir),
                    "-o", str(output_dir),
                    "--no-encrypt",
                    "--all-advanced",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Verify output directory has files
            assert output_dir.exists()
            py_files = list(output_dir.glob("*.py"))
            assert len(py_files) >= 2

    def test_cli_with_frameworks_option(self):
        """Test CLI with --frameworks option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "flask_app.py"
            source_file.write_text('''
# Simulated Flask app
def route(path):
    def decorator(f):
        return f
    return decorator

@route("/")
def index():
    return "Hello"

@route("/api")
def api_endpoint():
    return {"status": "ok"}

print("Flask-like app")
''')

            output_file = tmpdir / "flask_obf.py"

            # Run CLI with framework option
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_file),
                    "--no-encrypt",
                    "--frameworks", "flask",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Execute
            exec_result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert exec_result.returncode == 0
            assert "Flask-like app" in exec_result.stdout

    def test_cli_all_advanced_flags(self):
        """Test CLI with all advanced obfuscation flags individually."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "advanced.py"
            source_file.write_text('''
def compute(x):
    y = 100
    z = len([1, 2, 3])
    if x > 5:
        return y + z
    return x

result = compute(10)
assert result == 103, f"Expected 103, got {result}"
print("Advanced test passed!")
''')

            output_file = tmpdir / "advanced_obf.py"

            # Run CLI with individual advanced flags
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_file),
                    "--no-encrypt",
                    "--control-flow",
                    "--control-flow-flatten",
                    "--numbers",
                    "--builtins",
                    "--intensity", "2",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Verify output and execute
            assert output_file.exists()

            exec_result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert exec_result.returncode == 0, f"Execution failed: {exec_result.stderr}"
            assert "Advanced test passed!" in exec_result.stdout

    def test_cli_entry_points_flag(self):
        """Test CLI with --entry-points to preserve specific names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "api.py"
            source_file.write_text('''
def public_api_function(data):
    """This function name should be preserved."""
    return process_internal(data)

def process_internal(data):
    """This should be obfuscated."""
    return data * 2

result = public_api_function(21)
assert result == 42
print("Entry points test passed!")
''')

            output_file = tmpdir / "api_obf.py"

            # Run CLI with entry-points
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_file),
                    "--no-encrypt",
                    "--entry-points", "public_api_function",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Verify the entry point name is preserved
            obfuscated_content = output_file.read_text()
            assert "public_api_function" in obfuscated_content
            assert "process_internal" not in obfuscated_content

            # Execute
            exec_result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert exec_result.returncode == 0
            assert "Entry points test passed!" in exec_result.stdout

    def test_cli_exclude_names_flag(self):
        """Test CLI with --exclude to preserve specific variable names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "config.py"
            source_file.write_text('''
CONFIG_VALUE = 42
SECRET_KEY = "should_be_obfuscated"
internal_var = 100

result = CONFIG_VALUE + internal_var
print(f"Result: {result}")
''')

            output_file = tmpdir / "config_obf.py"

            # Run CLI with exclude
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_file),
                    "--no-encrypt",
                    "--exclude", "CONFIG_VALUE", "result",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Verify excluded names are preserved
            obfuscated_content = output_file.read_text()
            assert "CONFIG_VALUE" in obfuscated_content
            assert "result" in obfuscated_content
            assert "SECRET_KEY" not in obfuscated_content
            assert "internal_var" not in obfuscated_content

    def test_cli_string_method_options(self):
        """Test CLI with different string obfuscation methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "strings.py"
            source_file.write_text('''
message = "Hello World"
print(message)
''')

            for method in ["xor", "hex", "base64"]:
                output_file = tmpdir / f"strings_{method}.py"

                result = subprocess.run(
                    [
                        sys.executable, "-m", "pyobfuscator", "obfuscate",
                        "-i", str(source_file),
                        "-o", str(output_file),
                        "--no-encrypt",
                        "--string-method", method,
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(Path(__file__).parent.parent),
                    timeout=60
                )

                assert result.returncode == 0, f"CLI failed for {method}: {result.stderr}"

                # Execute
                exec_result = subprocess.run(
                    [sys.executable, str(output_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                assert exec_result.returncode == 0
                assert "Hello World" in exec_result.stdout

    def test_cli_multi_file_project_real_workflow(self):
        """Test real-world workflow: obfuscate a multi-file project via CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            project_dir = tmpdir / "myproject"
            output_dir = tmpdir / "dist"
            project_dir.mkdir()

            # Create a realistic project structure
            (project_dir / "main.py").write_text('''
from utils import calculate, format_output

def main():
    result = calculate(10, 5)
    output = format_output(result)
    print(output)
    assert result == 50
    print("Project test passed!")

if __name__ == "__main__":
    main()
''')

            (project_dir / "utils.py").write_text('''
def calculate(a, b):
    return a * b

def format_output(value):
    return f"Result: {value}"
''')

            (project_dir / "__init__.py").write_text("")

            # Run CLI to obfuscate the entire project
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(project_dir),
                    "-o", str(output_dir),
                    "--no-encrypt",
                    "--control-flow",
                    "--numbers",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "complete" in result.stdout.lower()

            # Execute the obfuscated project
            exec_result = subprocess.run(
                [sys.executable, str(output_dir / "main.py")],
                capture_output=True,
                text=True,
                cwd=str(output_dir),
                timeout=30
            )

            assert exec_result.returncode == 0, f"Execution failed: {exec_result.stderr}"
            assert "Project test passed!" in exec_result.stdout

    def test_cli_parallel_processing(self):
        """Test CLI with --parallel flag for directory processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "src"
            output_dir = tmpdir / "dist"
            input_dir.mkdir()

            # Create multiple files
            for i in range(5):
                (input_dir / f"module{i}.py").write_text(f'''
def func{i}():
    return "Module {i}"
''')

            # Run CLI with parallel flag
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(input_dir),
                    "-o", str(output_dir),
                    "--no-encrypt",
                    "--parallel",
                    "--workers", "2",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Verify all files were created
            output_files = list(output_dir.glob("*.py"))
            assert len(output_files) == 5

    def test_cli_compress_flag(self):
        """Test CLI with --compress flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "compress_test.py"
            source_file.write_text('''
def hello():
    return "Hello from compressed code!"

print(hello())
''')

            output_file = tmpdir / "compressed.py"

            # Run CLI with compress
            result = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_file),
                    "--no-encrypt",
                    "--compress",
                    "-v"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Verify output contains exec (compressed format)
            content = output_file.read_text()
            assert "exec" in content
            assert "zlib" in content or "decompress" in content

            # Execute
            exec_result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert exec_result.returncode == 0
            assert "Hello from compressed code!" in exec_result.stdout

    def test_cli_name_style_options(self):
        """Test CLI with different name style options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "names.py"
            source_file.write_text('''
def my_function():
    my_variable = 42
    return my_variable

print(my_function())
''')

            for style in ["random", "hex", "hash"]:
                output_file = tmpdir / f"names_{style}.py"

                result = subprocess.run(
                    [
                        sys.executable, "-m", "pyobfuscator", "obfuscate",
                        "-i", str(source_file),
                        "-o", str(output_file),
                        "--no-encrypt",
                        "--name-style", style,
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(Path(__file__).parent.parent),
                    timeout=60
                )

                assert result.returncode == 0, f"CLI failed for {style}: {result.stderr}"

                # Verify original names are gone
                content = output_file.read_text()
                assert "my_function" not in content
                assert "my_variable" not in content

                # Execute
                exec_result = subprocess.run(
                    [sys.executable, str(output_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                assert exec_result.returncode == 0
                assert "42" in exec_result.stdout

    def test_cli_keep_docstrings_flag(self):
        """Test CLI with --keep-docstrings flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source_file = tmpdir / "docstrings.py"
            source_file.write_text('''
def documented_function():
    """DOCSTRING_MARKER"""
    return 42

print(documented_function())
''')

            # Without --keep-docstrings (default removes them)
            output_no_docs = tmpdir / "no_docs.py"
            result1 = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_no_docs),
                    "--no-encrypt",
                    "--no-string-obfuscation",
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )
            assert result1.returncode == 0, f"CLI failed: {result1.stderr}"

            # With --keep-docstrings
            output_with_docs = tmpdir / "with_docs.py"
            result2 = subprocess.run(
                [
                    sys.executable, "-m", "pyobfuscator", "obfuscate",
                    "-i", str(source_file),
                    "-o", str(output_with_docs),
                    "--no-encrypt",
                    "--no-string-obfuscation",
                    "--keep-docstrings",
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent),
                timeout=60
            )
            assert result2.returncode == 0, f"CLI failed: {result2.stderr}"

            # Verify both files exist
            assert output_no_docs.exists()
            assert output_with_docs.exists()

            # Verify docstring handling
            no_docs_content = output_no_docs.read_text()
            with_docs_content = output_with_docs.read_text()

            # The file without --keep-docstrings should NOT have the docstring
            assert "DOCSTRING_MARKER" not in no_docs_content
            # The file with --keep-docstrings should have the docstring
            assert "DOCSTRING_MARKER" in with_docs_content

            # Both should execute correctly
            exec1 = subprocess.run([sys.executable, str(output_no_docs)], capture_output=True, text=True, timeout=30)
            exec2 = subprocess.run([sys.executable, str(output_with_docs)], capture_output=True, text=True, timeout=30)
            assert exec1.returncode == 0
            assert exec2.returncode == 0
            assert "42" in exec1.stdout
            assert "42" in exec2.stdout


class TestE2ERealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_data_processing_script(self):
        """Test obfuscating a data processing script."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            source = '''
# Sensitive algorithm
def proprietary_algorithm(data):
    """This is our secret sauce."""
    weights = [0.1, 0.2, 0.3, 0.4]
    result = 0
    for i, value in enumerate(data[:4]):
        result += value * weights[i]
    return round(result, 2)

# Test data
test_values = [10, 20, 30, 40]

# Process
output = proprietary_algorithm(test_values)

# Verify: 10*0.1 + 20*0.2 + 30*0.3 + 40*0.4 = 1 + 4 + 9 + 16 = 30
assert output == 30.0, f"Expected 30.0, got {output}"

print(f"Result: {output}")
print("Data processing test passed!")
'''

            # Obfuscate - exclude some names for the test to work
            obfuscator = Obfuscator(
                encrypt_code=False,
                control_flow=True,
                number_obfuscation=True,
                obfuscation_intensity=2,
                exclude_names={"output", "test_values"}  # Preserve these for assertions
            )

            obfuscated = obfuscator.obfuscate_source(source)

            # Verify algorithm details are hidden
            assert "proprietary_algorithm" not in obfuscated
            assert "weights" not in obfuscated

            # Write and execute
            output_file = tmpdir / "processor.py"
            output_file.write_text(obfuscated)

            result = subprocess.run(
                [sys.executable, str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0, f"Data processing failed: {result.stderr}"
            assert "Data processing test passed!" in result.stdout

    def test_web_app_structure(self):
        """Test obfuscating a web app structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "webapp"
            output_dir = tmpdir / "dist"
            input_dir.mkdir()

            # Simulate a simple web app structure
            (input_dir / "app.py").write_text('''
class App:
    def __init__(self):
        self.routes = {}
    
    def route(self, path):
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator
    
    def handle_request(self, path):
        if path in self.routes:
            return self.routes[path]()
        return "404 Not Found"

app = App()

@app.route("/")
def index():
    return "Welcome to the app!"

@app.route("/api/data")
def get_data():
    return {"status": "ok", "value": 42}
''')

            (input_dir / "config.py").write_text('''
SECRET_KEY = "super_secret_key_12345"
DATABASE_URL = "postgresql://user:pass@localhost/db"
DEBUG = False
''')

            (input_dir / "run.py").write_text('''
from app import app
from config import SECRET_KEY, DEBUG

def main():
    # Test routes
    index_result = app.handle_request("/")
    api_result = app.handle_request("/api/data")
    
    assert "Welcome" in index_result
    assert api_result["value"] == 42
    
    # Verify config loaded
    assert len(SECRET_KEY) > 10
    assert DEBUG == False
    
    print("Webapp test passed!")
    return True

if __name__ == "__main__":
    main()
''')

            # Obfuscate with entry points preserved
            obfuscator = Obfuscator(
                encrypt_code=False,
                entry_points=["app", "main", "App"],
                obfuscation_intensity=2
            )

            results = obfuscator.obfuscate_directory(
                input_dir,
                output_dir
            )

            assert all(v == "success" for v in results.values())

            # Execute
            result = subprocess.run(
                [sys.executable, str(output_dir / "run.py")],
                capture_output=True,
                text=True,
                cwd=str(output_dir),
                timeout=30
            )

            assert result.returncode == 0, f"Webapp test failed: {result.stderr}"
            assert "Webapp test passed!" in result.stdout



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
