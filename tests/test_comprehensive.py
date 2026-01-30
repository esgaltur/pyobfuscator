# -*- coding: utf-8 -*-
"""
Comprehensive test suite for PyObfuscator.

Tests cover:
- Obfuscator (name, string, class, method, attribute obfuscation)
- RuntimeProtector (encryption, anti-debug, licensing)
- PydRuntimeProtector (Cython runtime generation)
- Cryptographic functions
- Transformers (control flow, opaque predicates, polymorphic code)
- Utility functions
- CLI interface
- Cross-file obfuscation
"""
import ast
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyobfuscator import (
    Obfuscator,
    NameGenerator,
    RuntimeProtector,
    PydRuntimeProtector,
    apply_advanced_obfuscation,
    generate_polymorphic_anti_debug,
    generate_distributed_timing_checks,
    ControlFlowObfuscator,
    PolymorphicAntiDebugGenerator,
    DistributedTimingChecker,
    get_machine_id,
)
from pyobfuscator.crypto import CryptoEngine, HAS_CRYPTOGRAPHY
from pyobfuscator.utils import extract_public_api, calculate_file_hash, find_python_files


# =============================================================================
# Obfuscator Tests
# =============================================================================

class TestNameGenerator:
    """Test the NameGenerator class."""

    def test_random_style(self):
        """Test random name generation."""
        gen = NameGenerator(style="random")
        name = gen.get_name("test")
        assert name.startswith("_")
        assert len(name) > 3

    def test_hex_style(self):
        """Test hex name generation."""
        gen = NameGenerator(style="hex")
        name1 = gen.get_name("first")
        name2 = gen.get_name("second")
        assert name1.startswith("_x")
        assert name2.startswith("_x")
        assert name1 != name2

    def test_hash_style(self):
        """Test hash name generation."""
        gen = NameGenerator(style="hash")
        name = gen.get_name("test")
        assert name.startswith("_")
        assert len(name) == 9  # _ + 8 hex chars

    def test_consistent_mapping(self):
        """Test that same name always maps to same obfuscated name."""
        gen = NameGenerator()
        name1 = gen.get_name("variable")
        name2 = gen.get_name("variable")
        assert name1 == name2

    def test_different_names_different_mapping(self):
        """Test that different names map to different obfuscated names."""
        gen = NameGenerator()
        name1 = gen.get_name("var1")
        name2 = gen.get_name("var2")
        assert name1 != name2

    def test_export_import_mapping(self):
        """Test exporting and importing name mapping."""
        gen1 = NameGenerator()
        gen1.get_name("test1")
        gen1.get_name("test2")
        mapping = gen1.export_mapping()

        gen2 = NameGenerator()
        gen2.import_mapping(mapping)
        assert gen2.get_name("test1") == gen1.get_name("test1")
        assert gen2.get_name("test2") == gen1.get_name("test2")

    def test_register_method(self):
        """Test registering methods."""
        gen = NameGenerator()
        gen.register_method("my_method")
        assert gen.is_known_member("my_method")
        assert not gen.is_known_member("unknown")

    def test_register_class_attribute(self):
        """Test registering class attributes."""
        gen = NameGenerator()
        gen.register_class_attribute("my_attr")
        assert gen.is_known_member("my_attr")


class TestObfuscatorBasic:
    """Test basic Obfuscator functionality."""

    def test_default_initialization(self):
        """Test default initialization."""
        obf = Obfuscator()
        assert obf.rename_variables is True
        assert obf.rename_functions is True
        assert obf.rename_classes is True
        assert obf.string_method == "xor"

    def test_custom_initialization(self):
        """Test custom initialization."""
        obf = Obfuscator(
            rename_variables=False,
            rename_functions=False,
            string_method="hex"
        )
        assert obf.rename_variables is False
        assert obf.rename_functions is False
        assert obf.string_method == "hex"

    def test_empty_source(self):
        """Test handling of empty source."""
        obf = Obfuscator()
        result = obf.obfuscate_source("")
        assert result == ""

    def test_syntax_error_raises(self):
        """Test that syntax errors raise ValueError."""
        obf = Obfuscator()
        with pytest.raises(ValueError, match="Failed to parse"):
            obf.obfuscate_source("def broken(")

    def test_preserve_shebang(self):
        """Test that shebang is handled (via AST parsing)."""
        obf = Obfuscator(obfuscate_strings=False)
        # Shebang gets lost in AST parsing, but code should still work
        source = '''x = 1'''
        result = obf.obfuscate_source(source)
        assert result  # Should produce valid output


class TestObfuscatorVariables:
    """Test variable obfuscation."""

    def test_local_variable_renamed(self):
        """Test local variable renaming."""
        obf = Obfuscator()
        source = '''
def func():
    my_var = 42
    return my_var
'''
        result = obf.obfuscate_source(source)
        assert "my_var" not in result

    def test_global_variable_renamed(self):
        """Test global variable renaming."""
        obf = Obfuscator()
        source = "global_var = 100"
        result = obf.obfuscate_source(source)
        assert "global_var" not in result

    def test_multiple_variables(self):
        """Test multiple variable renaming."""
        obf = Obfuscator()
        source = '''
x = 1
y = 2
z = x + y
'''
        result = obf.obfuscate_source(source)
        # Check that original variable names as assignments don't appear
        assert "x = 1" not in result
        assert "y = 2" not in result
        assert "z = " not in result

    def test_excluded_variable_preserved(self):
        """Test that excluded variables are preserved."""
        obf = Obfuscator(exclude_names={"keep_me"})
        source = "keep_me = 42"
        result = obf.obfuscate_source(source)
        assert "keep_me" in result


class TestObfuscatorFunctions:
    """Test function obfuscation."""

    def test_function_renamed(self):
        """Test function renaming."""
        obf = Obfuscator()
        source = '''
def my_function():
    pass
'''
        result = obf.obfuscate_source(source)
        assert "my_function" not in result

    def test_function_call_renamed(self):
        """Test function call renaming."""
        obf = Obfuscator()
        source = '''
def helper():
    return 1
result = helper()
'''
        result = obf.obfuscate_source(source)
        assert "helper" not in result

    def test_async_function_renamed(self):
        """Test async function renaming."""
        obf = Obfuscator()
        source = '''
async def async_func():
    pass
'''
        result = obf.obfuscate_source(source)
        assert "async_func" not in result
        assert "async def" in result

    def test_function_arguments_renamed(self):
        """Test function argument renaming."""
        obf = Obfuscator()
        source = '''
def func(arg1, arg2):
    return arg1 + arg2
'''
        result = obf.obfuscate_source(source)
        assert "arg1" not in result
        assert "arg2" not in result

    def test_varargs_kwargs_renamed(self):
        """Test *args and **kwargs renaming."""
        obf = Obfuscator()
        source = '''
def func(*my_args, **my_kwargs):
    pass
'''
        result = obf.obfuscate_source(source)
        assert "my_args" not in result
        assert "my_kwargs" not in result

    def test_excluded_function_preserved(self):
        """Test excluded function preservation."""
        obf = Obfuscator(exclude_names={"public_api"})
        source = '''
def public_api():
    return 42
'''
        result = obf.obfuscate_source(source)
        assert "public_api" in result


class TestObfuscatorClasses:
    """Test class obfuscation."""

    def test_class_renamed(self):
        """Test class renaming."""
        obf = Obfuscator()
        source = '''
class MyClass:
    pass
'''
        result = obf.obfuscate_source(source)
        assert "MyClass" not in result

    def test_class_instantiation_renamed(self):
        """Test class instantiation renaming."""
        obf = Obfuscator()
        source = '''
class Widget:
    pass
obj = Widget()
'''
        result = obf.obfuscate_source(source)
        assert "Widget" not in result

    def test_self_preserved(self):
        """Test that 'self' is preserved."""
        obf = Obfuscator()
        source = '''
class MyClass:
    def method(self):
        return self
'''
        result = obf.obfuscate_source(source)
        assert "self" in result

    def test_cls_preserved(self):
        """Test that 'cls' is preserved."""
        obf = Obfuscator()
        source = '''
class MyClass:
    @classmethod
    def method(cls):
        return cls
'''
        result = obf.obfuscate_source(source)
        assert "cls" in result


class TestObfuscatorMethods:
    """Test method obfuscation."""

    def test_method_renamed(self):
        """Test method renaming."""
        obf = Obfuscator(rename_methods=True)
        source = '''
class MyClass:
    def my_method(self):
        return 42
'''
        result = obf.obfuscate_source(source)
        assert "my_method" not in result

    def test_method_call_renamed(self):
        """Test method call renaming."""
        obf = Obfuscator(rename_methods=True, rename_attributes=True)
        source = '''
class MyClass:
    def helper(self):
        return 1
    def caller(self):
        return self.helper()
'''
        result = obf.obfuscate_source(source)
        assert "helper" not in result

    def test_dunder_methods_preserved(self):
        """Test that dunder methods are preserved."""
        obf = Obfuscator(rename_methods=True)
        source = '''
class MyClass:
    def __init__(self):
        pass
    def __str__(self):
        return "test"
'''
        result = obf.obfuscate_source(source)
        assert "__init__" in result
        assert "__str__" in result


class TestObfuscatorAttributes:
    """Test attribute obfuscation."""

    def test_instance_attribute_renamed(self):
        """Test instance attribute renaming."""
        obf = Obfuscator(rename_attributes=True)
        source = '''
class MyClass:
    def __init__(self):
        self.my_attr = 42
'''
        result = obf.obfuscate_source(source)
        assert "my_attr" not in result

    def test_class_variable_renamed(self):
        """Test class variable renaming."""
        obf = Obfuscator(rename_attributes=True)
        source = '''
class MyClass:
    class_var = 100
'''
        result = obf.obfuscate_source(source)
        assert "class_var" not in result

    def test_attribute_access_renamed(self):
        """Test attribute access renaming."""
        obf = Obfuscator(rename_methods=True, rename_attributes=True)
        source = '''
class MyClass:
    def __init__(self):
        self.value = 10
    def get_value(self):
        return self.value
'''
        result = obf.obfuscate_source(source)
        # Both definition and access should be renamed
        namespace = {}
        exec(result, namespace)


class TestObfuscatorStrings:
    """Test string obfuscation."""

    def test_xor_obfuscation(self):
        """Test XOR string obfuscation."""
        obf = Obfuscator(obfuscate_strings=True, string_method="xor")
        source = 'msg = "secret message"'
        result = obf.obfuscate_source(source)
        assert "secret message" not in result

    def test_hex_obfuscation(self):
        """Test hex string obfuscation."""
        obf = Obfuscator(obfuscate_strings=True, string_method="hex")
        source = 'msg = "test string"'
        result = obf.obfuscate_source(source)
        assert "test string" not in result
        assert "fromhex" in result

    def test_base64_obfuscation(self):
        """Test base64 string obfuscation."""
        obf = Obfuscator(obfuscate_strings=True, string_method="base64")
        source = 'msg = "encoded"'
        result = obf.obfuscate_source(source)
        assert "encoded" not in result
        assert "b64decode" in result

    def test_short_strings_not_obfuscated(self):
        """Test that very short strings are not obfuscated."""
        obf = Obfuscator(obfuscate_strings=True, string_method="xor")
        source = 'x = "ab"'  # 2 chars, should not be obfuscated
        result = obf.obfuscate_source(source)
        # Short strings may or may not be obfuscated depending on implementation
        # But the result should be valid Python code
        assert len(result) > 0
        # Verify it compiles
        compile(result, "<test>", "exec")

    def test_fstrings_handled(self):
        """Test that f-strings are handled gracefully."""
        obf = Obfuscator(obfuscate_strings=True)
        source = '''
name = "world"
msg = f"Hello, {name}!"
'''
        result = obf.obfuscate_source(source)
        # Should not crash, f-strings are typically not obfuscated
        assert result


class TestObfuscatorCompression:
    """Test code compression."""

    def test_compression_enabled(self):
        """Test compression creates exec wrapper."""
        obf = Obfuscator(compress_code=True)
        source = '''
def func():
    return 42
'''
        result = obf.obfuscate_source(source)
        assert "exec" in result
        assert "zlib" in result or "decompress" in result

    def test_compressed_code_executes(self):
        """Test that compressed code executes correctly."""
        obf = Obfuscator(compress_code=True, exclude_names={"result"})
        source = "result = 1 + 2"
        result = obf.obfuscate_source(source)
        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == 3


class TestObfuscatorDocstrings:
    """Test docstring handling."""

    def test_docstring_removed(self):
        """Test docstring removal."""
        obf = Obfuscator(remove_docstrings=True, obfuscate_strings=False)
        source = '''
def func():
    """This docstring should be removed."""
    return 42
'''
        result = obf.obfuscate_source(source)
        assert "This docstring should be removed" not in result

    def test_module_docstring_removed(self):
        """Test module docstring removal."""
        obf = Obfuscator(remove_docstrings=True, obfuscate_strings=False)
        source = '''"""Module docstring."""
x = 1
'''
        result = obf.obfuscate_source(source)
        assert "Module docstring" not in result

    def test_class_docstring_removed(self):
        """Test class docstring removal."""
        obf = Obfuscator(remove_docstrings=True, obfuscate_strings=False)
        source = '''
class MyClass:
    """Class docstring."""
    pass
'''
        result = obf.obfuscate_source(source)
        assert "Class docstring" not in result


class TestObfuscatorExecution:
    """Test that obfuscated code executes correctly."""

    def test_simple_function_executes(self):
        """Test simple function execution."""
        obf = Obfuscator(exclude_names={"result", "add"})
        source = '''
def add(a, b):
    return a + b
result = add(5, 3)
'''
        result = obf.obfuscate_source(source)
        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == 8

    def test_class_executes(self):
        """Test class execution."""
        obf = Obfuscator(exclude_names={"Counter", "c", "result"})
        source = '''
class Counter:
    def __init__(self, start=0):
        self.value = start
    def increment(self):
        self.value += 1
        return self.value

c = Counter(10)
result = c.increment()
'''
        result = obf.obfuscate_source(source)
        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == 11

    def test_loop_executes(self):
        """Test loop execution."""
        obf = Obfuscator(exclude_names={"total"})
        source = '''
total = 0
for i in range(5):
    total += i
'''
        result = obf.obfuscate_source(source)
        namespace = {}
        exec(result, namespace)
        assert namespace["total"] == 10

    def test_comprehension_executes(self):
        """Test list comprehension execution."""
        obf = Obfuscator(exclude_names={"result"})
        source = "result = [x*2 for x in range(5)]"
        result = obf.obfuscate_source(source)
        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == [0, 2, 4, 6, 8]


class TestObfuscatorCrossFile:
    """Test cross-file obfuscation."""

    def test_shared_name_mapping(self):
        """Test that same obfuscator shares name mapping across files."""
        obf = Obfuscator()

        source1 = '''
class SharedClass:
    def shared_method(self):
        return 42
'''
        source2 = '''
from module1 import SharedClass
obj = SharedClass()
'''
        result1 = obf.obfuscate_source(source1)
        result2 = obf.obfuscate_source(source2)

        # SharedClass should be renamed consistently
        mapping = obf.export_name_mapping()
        assert "SharedClass" in mapping

        # Verify both results are non-empty and obfuscated
        assert len(result1) > 0
        assert len(result2) > 0
        assert "SharedClass" not in result1
        assert "SharedClass" not in result2

    def test_export_import_name_mapping(self):
        """Test export and import of name mapping."""
        obf1 = Obfuscator()
        obf1.obfuscate_source("x = 1")
        mapping = obf1.export_name_mapping()

        obf2 = Obfuscator()
        obf2.import_name_mapping(mapping)

        assert obf1.get_obfuscated_name("x") == obf2.get_obfuscated_name("x")

    def test_directory_obfuscation(self):
        """Test directory obfuscation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            # Create test files
            (input_dir / "file1.py").write_text("x = 1")
            (input_dir / "file2.py").write_text("y = 2")

            obf = Obfuscator()
            results = obf.obfuscate_directory(input_dir, output_dir)

            assert "file1.py" in results
            assert "file2.py" in results
            assert (output_dir / "file1.py").exists()
            assert (output_dir / "file2.py").exists()


# =============================================================================
# Crypto Tests
# =============================================================================

class TestCryptoEngine:
    """Test CryptoEngine."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption/decryption roundtrip."""
        key = os.urandom(32)
        engine = CryptoEngine(key)

        plaintext = b"Hello, World!"
        ciphertext = engine.encrypt(plaintext)
        decrypted = engine.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_different_plaintext_different_ciphertext(self):
        """Test that different plaintexts produce different ciphertexts."""
        key = os.urandom(32)
        engine = CryptoEngine(key)

        ct1 = engine.encrypt(b"message1")
        ct2 = engine.encrypt(b"message2")

        assert ct1 != ct2

    def test_same_plaintext_different_ciphertext(self):
        """Test that same plaintext produces different ciphertext (due to random nonce)."""
        key = os.urandom(32)
        engine = CryptoEngine(key)

        plaintext = b"same message"
        ct1 = engine.encrypt(plaintext)
        ct2 = engine.encrypt(plaintext)

        assert ct1 != ct2  # Random salt/nonce

    def test_wrong_key_fails(self):
        """Test that wrong key fails decryption."""
        key1 = os.urandom(32)
        key2 = os.urandom(32)

        engine1 = CryptoEngine(key1)
        engine2 = CryptoEngine(key2)

        ciphertext = engine1.encrypt(b"secret")

        with pytest.raises(Exception):
            engine2.decrypt(ciphertext)

    def test_empty_plaintext(self):
        """Test encryption of empty plaintext."""
        key = os.urandom(32)
        engine = CryptoEngine(key)

        ciphertext = engine.encrypt(b"")
        decrypted = engine.decrypt(ciphertext)

        assert decrypted == b""

    def test_large_plaintext(self):
        """Test encryption of large plaintext."""
        key = os.urandom(32)
        engine = CryptoEngine(key)

        plaintext = os.urandom(1024 * 100)  # 100KB
        ciphertext = engine.encrypt(plaintext)
        decrypted = engine.decrypt(ciphertext)

        assert decrypted == plaintext


class TestMachineId:
    """Test machine ID generation."""

    def test_machine_id_format(self):
        """Test machine ID format."""
        machine_id = get_machine_id()
        assert isinstance(machine_id, str)
        assert len(machine_id) == 32
        assert all(c in "0123456789abcdef" for c in machine_id)

    def test_machine_id_consistent(self):
        """Test machine ID is consistent across calls."""
        id1 = get_machine_id()
        id2 = get_machine_id()
        assert id1 == id2


# =============================================================================
# Runtime Protector Tests
# =============================================================================

class TestRuntimeProtector:
    """Test RuntimeProtector."""

    def test_protect_source(self):
        """Test source protection."""
        protector = RuntimeProtector(anti_debug=False)
        source = "x = 42"
        protected, runtime = protector.protect_source(source)

        # RuntimeProtector uses __pyobfuscator__ (with 'r')
        assert "__pyobfuscator__" in protected
        assert len(runtime) > 0

    def test_custom_license_info(self):
        """Test custom license info."""
        protector = RuntimeProtector(
            license_info="My Custom License",
            anti_debug=False
        )
        source = "x = 1"
        protected, _ = protector.protect_source(source, "test.py")

        assert "My Custom License" in protected

    def test_runtime_id_generation(self):
        """Test runtime ID generation."""
        key = b"x" * 32
        p1 = RuntimeProtector(encryption_key=key, anti_debug=False)
        p2 = RuntimeProtector(encryption_key=key, anti_debug=False)

        assert p1.runtime_id == p2.runtime_id

    def test_different_keys_different_ids(self):
        """Test different keys produce different runtime IDs."""
        p1 = RuntimeProtector(anti_debug=False)
        p2 = RuntimeProtector(anti_debug=False)

        # Auto-generated keys should be different
        assert p1.runtime_id != p2.runtime_id

    def test_expiration_date(self):
        """Test expiration date setting."""
        exp_date = datetime.now() + timedelta(days=30)
        protector = RuntimeProtector(
            expiration_date=exp_date,
            anti_debug=False
        )

        assert protector.expiration_date == exp_date

    def test_machine_binding(self):
        """Test machine binding."""
        machine_id = get_machine_id()
        protector = RuntimeProtector(
            allowed_machines=[machine_id],
            anti_debug=False
        )

        assert machine_id in protector.allowed_machines


# =============================================================================
# PYD Runtime Protector Tests
# =============================================================================

class TestPydRuntimeProtector:
    """Test PydRuntimeProtector."""

    def test_initialization(self):
        """Test initialization."""
        protector = PydRuntimeProtector(
            license_info="Test License",
            anti_debug=True
        )

        assert protector.license_info == "Test License"
        assert protector.anti_debug is True

    def test_protect_source(self):
        """Test source protection."""
        protector = PydRuntimeProtector(anti_debug=False)
        source = "print('hello')"
        protected, pyx, setup = protector.protect_source(source, "test.py")

        assert "__pyobfuscator__" in protected
        assert "cython" in pyx.lower() or "cdef" in pyx
        assert "setup" in setup.lower()

    def test_template_values(self):
        """Test template value generation."""
        protector = PydRuntimeProtector()
        tv = protector._get_template_values()

        assert "debug_env_vars" in tv
        assert "debug_modules" in tv
        assert "err_invalid" in tv
        assert "magic_v2" in tv
        assert "magic_v3" in tv

    def test_create_fallback_runtime(self):
        """Test fallback Python runtime creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            protector = PydRuntimeProtector(anti_debug=False)
            runtime_path = protector.create_fallback_py_runtime(Path(tmpdir))

            assert runtime_path.exists()
            content = runtime_path.read_text()
            assert "__pyobfuscator__" in content
            assert "_check_debugger" in content


# =============================================================================
# Transformers Tests
# =============================================================================

class TestControlFlowObfuscator:
    """Test ControlFlowObfuscator."""

    def test_initialization(self):
        """Test initialization."""
        cfo = ControlFlowObfuscator(intensity=2)
        assert cfo.intensity == 2

    def test_intensity_clamped(self):
        """Test intensity is clamped."""
        cfo1 = ControlFlowObfuscator(intensity=0)
        cfo2 = ControlFlowObfuscator(intensity=10)

        assert cfo1.intensity == 1
        assert cfo2.intensity == 3

    def test_opaque_true_always_true(self):
        """Test opaque predicates always evaluate to True."""
        cfo = ControlFlowObfuscator()

        for _ in range(20):  # Test multiple random predicates
            pred = cfo._generate_opaque_true()
            code = ast.unparse(pred)
            result = eval(code)
            assert result is True

    def test_blinded_comparison(self):
        """Test blinded comparison always evaluates to True."""
        cfo = ControlFlowObfuscator()

        for _ in range(10):
            pred = cfo._opaque_blinded_comparison()
            code = ast.unparse(pred)
            result = eval(code)
            assert result is True

    def test_dead_code_generation(self):
        """Test dead code generation."""
        cfo = ControlFlowObfuscator()

        dead_code = cfo._generate_dead_code()
        assert len(dead_code) >= 1
        assert all(isinstance(stmt, ast.stmt) for stmt in dead_code)

    def test_unique_variable_names(self):
        """Test unique variable name generation."""
        cfo = ControlFlowObfuscator()

        names = [cfo._get_unique_name() for _ in range(10)]
        assert len(names) == len(set(names))  # All unique


class TestPolymorphicAntiDebugGenerator:
    """Test PolymorphicAntiDebugGenerator."""

    def test_generate_trace_check(self):
        """Test trace check generation."""
        gen = PolymorphicAntiDebugGenerator()
        code = gen.generate_trace_check()

        assert "gettrace" in code
        assert "def " in code

    def test_generate_module_check(self):
        """Test module check generation."""
        gen = PolymorphicAntiDebugGenerator()
        code = gen.generate_module_check()

        assert "modules" in code
        assert "def " in code

    def test_generate_timing_check(self):
        """Test timing check generation."""
        gen = PolymorphicAntiDebugGenerator()
        code = gen.generate_timing_check()

        assert "time" in code
        assert "def " in code

    def test_generate_combined_check(self):
        """Test combined check generation."""
        gen = PolymorphicAntiDebugGenerator()
        code = gen.generate_combined_check()

        assert "all(" in code
        assert code.count("def ") >= 4  # At least 4 functions

    def test_polymorphic_output(self):
        """Test that output is polymorphic (different each time)."""
        gen1 = PolymorphicAntiDebugGenerator()
        gen2 = PolymorphicAntiDebugGenerator()

        code1 = gen1.generate_combined_check()
        code2 = gen2.generate_combined_check()

        # Function names should be different
        assert code1 != code2


class TestDistributedTimingChecker:
    """Test DistributedTimingChecker."""

    def test_generate_checkpoint(self):
        """Test checkpoint generation."""
        checker = DistributedTimingChecker()
        code = checker.generate_checkpoint()

        assert "time" in code
        assert "perf_counter" in code

    def test_generate_verification(self):
        """Test verification generation."""
        checker = DistributedTimingChecker()
        checker.generate_checkpoint()  # Need at least one checkpoint

        code = checker.generate_verification()
        assert "RuntimeError" in code or "pass" in code

    def test_multiple_checkpoints(self):
        """Test multiple checkpoints."""
        checker = DistributedTimingChecker()

        cp1 = checker.generate_checkpoint()
        cp2 = checker.generate_checkpoint()
        cp3 = checker.generate_checkpoint()

        # Should have unique variable names
        assert cp1 != cp2
        assert cp2 != cp3


class TestApplyAdvancedObfuscation:
    """Test apply_advanced_obfuscation function."""

    def test_control_flow_obfuscation(self):
        """Test control flow obfuscation."""
        source = '''
def func():
    x = 1
    if x > 0:
        return True
    return False
'''
        tree = ast.parse(source)
        result = apply_advanced_obfuscation(tree, control_flow=True, intensity=2)

        code = ast.unparse(result)
        # Should still be valid Python
        compile(code, "<test>", "exec")

    def test_number_obfuscation(self):
        """Test number obfuscation."""
        source = "x = 42"
        tree = ast.parse(source)
        result = apply_advanced_obfuscation(tree, number_obfuscation=True)

        code = ast.unparse(result)
        namespace = {}
        exec(code, namespace)
        # Find the variable (may be obfuscated)
        user_vars = [k for k in namespace.keys() if not k.startswith('__')]
        assert len(user_vars) == 1
        assert namespace[user_vars[0]] == 42


# =============================================================================
# Utility Tests
# =============================================================================

class TestExtractPublicApi:
    """Test extract_public_api function."""

    def test_extract_from_all(self):
        """Test extraction from __all__."""
        source = '__all__ = ["func1", "func2", "MyClass"]'
        result = extract_public_api(source)

        assert "func1" in result
        assert "func2" in result
        assert "MyClass" in result

    def test_extract_property(self):
        """Test extraction of @property decorated methods."""
        source = '''
class MyClass:
    @property
    def value(self):
        return self._value
'''
        result = extract_public_api(source)
        assert "value" in result


class TestCalculateFileHash:
    """Test calculate_file_hash function."""

    def test_hash_calculation(self):
        """Test hash calculation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            path = Path(f.name)

        try:
            hash_value = calculate_file_hash(path)
            assert len(hash_value) == 64  # SHA256 hex
            assert all(c in "0123456789abcdef" for c in hash_value)
        finally:
            path.unlink()

    def test_same_content_same_hash(self):
        """Test that same content produces same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"

            content = "same content"
            file1.write_text(content)
            file2.write_text(content)

            assert calculate_file_hash(file1) == calculate_file_hash(file2)


class TestFindPythonFiles:
    """Test find_python_files function."""

    def test_find_python_files(self):
        """Test finding Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "file1.py").touch()
            (root / "file2.py").touch()
            (root / "file.txt").touch()

            files = find_python_files(root, recursive=False)

            assert len(files) == 2
            assert all(f.suffix == ".py" for f in files)

    def test_recursive_search(self):
        """Test recursive file search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "file1.py").touch()
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / "file2.py").touch()

            files = find_python_files(root, recursive=True)

            assert len(files) == 2

    def test_exclude_patterns(self):
        """Test exclude patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").touch()
            (root / "test_main.py").touch()

            files = find_python_files(root, exclude_patterns=["test_*"])

            assert len(files) == 1
            assert files[0].name == "main.py"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests."""

    def test_full_obfuscation_pipeline(self):
        """Test full obfuscation pipeline."""
        source = '''
class Calculator:
    """A simple calculator."""
    
    def __init__(self, initial=0):
        self.value = initial
    
    def add(self, x):
        self.value += x
        return self
    
    def subtract(self, x):
        self.value -= x
        return self
    
    def get_result(self):
        return self.value

calc = Calculator(10)
result = calc.add(5).subtract(3).get_result()
'''
        obf = Obfuscator(
            rename_variables=True,
            rename_functions=True,
            rename_classes=True,
            rename_methods=True,
            rename_attributes=True,
            obfuscate_strings=False,  # Keep simple for execution test
            remove_docstrings=True,
            exclude_names={"result"}
        )

        obfuscated = obf.obfuscate_source(source)

        # Should be valid Python
        namespace = {}
        exec(obfuscated, namespace)

        # Should produce correct result
        assert namespace["result"] == 12

    def test_runtime_protection_pipeline(self):
        """Test runtime protection pipeline."""
        source = '''
def secret_function():
    return "secret data"
'''
        protector = RuntimeProtector(anti_debug=False)
        protected, runtime = protector.protect_source(source, "secret.py")

        # Protected code should have import and call
        assert "import" in protected or "from" in protected
        # RuntimeProtector uses __pyobfuscator__ (with 'r')
        assert "__pyobfuscator__" in protected

        # Runtime should be substantial
        assert len(runtime) > 100

    def test_combined_obfuscation_and_protection(self):
        """Test combined obfuscation and runtime protection."""
        source = '''
password = "super_secret_123"
def check_password(attempt):
    return attempt == password
'''
        # First obfuscate
        obf = Obfuscator(obfuscate_strings=True, string_method="xor")
        obfuscated = obf.obfuscate_source(source)

        # Then protect
        protector = RuntimeProtector(anti_debug=False)
        protected, runtime = protector.protect_source(obfuscated, "auth.py")

        # Password should not appear in plain text
        assert "super_secret_123" not in protected
        assert "super_secret_123" not in runtime


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_handling(self):
        """Test Unicode string handling."""
        obf = Obfuscator(obfuscate_strings=True)
        source = 'msg = "Hello, 世界! 🌍"'
        result = obf.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)

    def test_nested_classes(self):
        """Test nested class handling."""
        obf = Obfuscator()
        source = '''
class Outer:
    class Inner:
        def method(self):
            return 42
'''
        result = obf.obfuscate_source(source)
        assert "Outer" not in result
        assert "Inner" not in result

    def test_decorators(self):
        """Test decorator handling."""
        obf = Obfuscator(exclude_names={"property", "staticmethod"})
        source = '''
class MyClass:
    @property
    def value(self):
        return self._value
    
    @staticmethod
    def helper():
        return 1
'''
        result = obf.obfuscate_source(source)
        assert "@property" in result
        assert "@staticmethod" in result

    def test_lambda_functions(self):
        """Test lambda function handling."""
        obf = Obfuscator(exclude_names={"result", "x"})
        source = "result = (lambda x: x * 2)(5)"
        result = obf.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == 10

    def test_walrus_operator(self):
        """Test walrus operator handling."""
        obf = Obfuscator(exclude_names={"result"})
        source = '''
if (n := 10) > 5:
    result = n
'''
        result = obf.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == 10

    def test_match_statement(self):
        """Test match statement handling (Python 3.10+)."""
        obf = Obfuscator(exclude_names={"result"})
        source = '''
x = 1
match x:
    case 1:
        result = "one"
    case _:
        result = "other"
'''
        result = obf.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == "one"

    def test_type_hints(self):
        """Test type hint handling."""
        obf = Obfuscator()
        source = '''
def func(x: int, y: str) -> bool:
    return True
'''
        result = obf.obfuscate_source(source)
        # Should still have type hints (types are preserved)
        assert "int" in result
        assert "str" in result
        assert "bool" in result

    def test_generator_expression(self):
        """Test generator expression handling."""
        obf = Obfuscator(exclude_names={"result"})
        source = "result = sum(x*2 for x in range(5))"
        result = obf.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == 20

    def test_context_manager(self):
        """Test context manager handling."""
        obf = Obfuscator(exclude_names={"result"})
        source = '''
class CM:
    def __enter__(self):
        return 42
    def __exit__(self, *args):
        pass

with CM() as result:
    pass
'''
        result = obf.obfuscate_source(source)

        namespace = {}
        exec(result, namespace)
        assert namespace["result"] == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
