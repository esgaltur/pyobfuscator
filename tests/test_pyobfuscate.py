# -*- coding: utf-8 -*-
"""Tests for PyObfuscator."""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyobfuscator import Obfuscator, RuntimeProtector


class TestObfuscator:
    """Test the Obfuscator class."""

    def test_basic_obfuscation(self):
        """Test basic name obfuscation."""
        obfuscator = Obfuscator()
        source = '''
def hello(name):
    message = f"Hello, {name}!"
    return message
'''
        result = obfuscator.obfuscate_source(source)
        assert 'hello' not in result
        assert 'message' not in result
        assert 'def ' in result

    def test_string_obfuscation_base64(self):
        """Test base64 string obfuscation."""
        obfuscator = Obfuscator(obfuscate_strings=True, string_method='base64')
        source = 'x = "secret"'
        result = obfuscator.obfuscate_source(source)
        assert 'secret' not in result
        assert 'base64' in result or 'b64decode' in result

    def test_string_obfuscation_hex(self):
        """Test hex string obfuscation."""
        obfuscator = Obfuscator(obfuscate_strings=True, string_method='hex')
        source = 'x = "test"'
        result = obfuscator.obfuscate_source(source)
        assert 'test' not in result
        assert 'fromhex' in result or 'bytes' in result

    def test_string_obfuscation_xor(self):
        """Test XOR string obfuscation."""
        obfuscator = Obfuscator(obfuscate_strings=True, string_method='xor')
        source = 'x = "hidden"'
        result = obfuscator.obfuscate_source(source)
        assert 'hidden' not in result

    def test_exclude_names(self):
        """Test excluding names from obfuscation."""
        obfuscator = Obfuscator(exclude_names={'public_api'})
        source = '''
def public_api():
    internal = 42
    return internal
'''
        result = obfuscator.obfuscate_source(source)
        assert 'public_api' in result
        assert 'internal' not in result

    def test_compression(self):
        """Test code compression."""
        obfuscator = Obfuscator(compress_code=True, encrypt_code=False)
        source = '''
def func():
    return 42
'''
        result = obfuscator.obfuscate_source(source)
        assert 'exec' in result

    def test_docstring_removal(self):
        """Test docstring removal."""
        obfuscator = Obfuscator(remove_docstrings=True)
        source = '''
def func():
    """This is a docstring."""
    return 42
'''
        result = obfuscator.obfuscate_source(source)
        assert 'docstring' not in result

    def test_keep_docstrings(self):
        """Test keeping docstrings."""
        obfuscator = Obfuscator(remove_docstrings=False, obfuscate_strings=False)
        source = '''
def func():
    """Keep this docstring."""
    return 42
'''
        result = obfuscator.obfuscate_source(source)
        assert 'Keep this docstring' in result

    def test_obfuscated_code_executes(self):
        """Test that obfuscated code can execute."""
        obfuscator = Obfuscator(exclude_names={'result', 'add'})
        source = '''
def add(a, b):
    return a + b
result = add(2, 3)
'''
        result = obfuscator.obfuscate_source(source)
        namespace = {}
        exec(result, namespace)
        assert namespace['result'] == 5


class TestRuntimeProtector:
    """Test the RuntimeProtector class."""

    def test_protection_creates_files(self):
        """Test that protection creates code and runtime."""
        protector = RuntimeProtector(anti_debug=False)
        source = 'x = 42'
        protected, runtime = protector.protect_source(source)

        assert '__pyobfuscator__' in protected
        assert 'pyobfuscator_runtime_' in protected
        assert len(runtime) > 0

    def test_machine_id(self):
        """Test machine ID generation."""
        machine_id = RuntimeProtector.get_machine_id()
        assert isinstance(machine_id, str)
        assert len(machine_id) == 32  # SHA-256 hex, truncated

    def test_runtime_id_consistent(self):
        """Test that runtime ID is consistent for same key."""
        key = b'0' * 32
        p1 = RuntimeProtector(encryption_key=key)
        p2 = RuntimeProtector(encryption_key=key)
        assert p1.runtime_id == p2.runtime_id

    def test_runtime_id_unique(self):
        """Test that runtime ID is unique for different keys."""
        p1 = RuntimeProtector()
        p2 = RuntimeProtector()
        # Different auto-generated keys should produce different IDs
        # (very high probability)
        assert p1.runtime_id != p2.runtime_id

    def test_protected_code_format(self):
        """Test protected code format."""
        protector = RuntimeProtector(license_info="Test License", anti_debug=False)
        source = 'print("hello")'
        protected, _ = protector.protect_source(source, "test.py")

        assert 'PyObfuscator' in protected
        assert 'Test License' in protected
        assert 'import' in protected


class TestCrypto:
    """Test cryptographic functions."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt/decrypt roundtrip works."""
        from pyobfuscator.crypto import CryptoEngine

        key = b'0' * 32
        engine = CryptoEngine(key)

        plaintext = b"Hello, World! This is a test message."
        ciphertext = engine.encrypt(plaintext)
        decrypted = engine.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_different_keys_produce_different_ciphertext(self):
        """Test that different keys produce different ciphertext."""
        from pyobfuscator.crypto import CryptoEngine

        key1 = b'1' * 32
        key2 = b'2' * 32

        engine1 = CryptoEngine(key1)
        engine2 = CryptoEngine(key2)

        plaintext = b"test"
        ct1 = engine1.encrypt(plaintext)
        ct2 = engine2.encrypt(plaintext)

        assert ct1 != ct2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
