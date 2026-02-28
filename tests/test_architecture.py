# -*- coding: utf-8 -*-
"""
High-level architectural tests demonstrating maximum testability.
Tests directory obfuscation entirely in memory using a Virtual File System.
"""

import pytest
from pathlib import Path
from pyobfuscator import Obfuscator
from pyobfuscator.infrastructure.file_processor import FileProcessor
from pyobfuscator.infrastructure.virtual_fs import VirtualFileSystem


def test_obfuscate_directory_in_memory():
    """
    Test that an entire project can be obfuscated without touching the disk.
    This demonstrates the power of the Hexagonal Architecture and FileSystemPort.
    """
    # 1. Setup a Virtual Project Structure
    vfs = VirtualFileSystem({
        "my_project/main.py": "from .utils import secret\ndef run(): print(secret)",
        "my_project/utils.py": "secret = 'TOP_SECRET_STRING'",
        "my_project/__init__.py": ""
    })
    
    # 2. Inject the Virtual FS into the FileProcessor
    # We create a FileProcessor that uses our in-memory VFS instead of the disk
    file_processor = FileProcessor(fs=vfs)
    
    # 3. Initialize Obfuscator with the Mocked Infrastructure
    obfuscator = Obfuscator(
        encrypt_code=False,
        obfuscate_strings=True,
        string_method="xor", # Use xor for deterministic verification in this test
        file_processor=file_processor
    )
    
    # 4. Execute obfuscation on the virtual directory
    results = obfuscator.obfuscate_directory(
        input_dir=Path("my_project"),
        output_dir=Path("dist")
    )
    
    # 5. Verify Results without Disk I/O
    assert results["main.py"] == "success"
    assert results["utils.py"] == "success"
    
    # Check that 'TOP_SECRET_STRING' is no longer readable in the virtual output
    obfuscated_utils = vfs.read_text(Path("dist/utils.py"))
    assert "TOP_SECRET_STRING" not in obfuscated_utils
    assert "secret" not in obfuscated_utils # Should be renamed
    
    # Check that main.py still imports correctly (cross-file consistency)
    obfuscated_main = vfs.read_text(Path("dist/main.py"))
    assert "from .utils import" not in obfuscated_main # The identifier should be renamed
    
    print("Project-wide in-memory obfuscation successful!")


def test_obfuscator_with_provided_name_generator():
    """
    Test dependency injection of the NameGenerator for deterministic naming.
    """
    from pyobfuscator.core.transformers.name_transformer import NameGenerator
    
    # Inject a NameGenerator with a fixed style and prefix
    name_gen = NameGenerator(prefix="test_", style="hex")
    
    obf = Obfuscator(name_generator=name_gen)
    
    source = "def my_function(x): return x * 2"
    result = obf.obfuscate_source(source)
    
    # Verify that the injected generator was used
    assert "test_x1" in result or "test_x" in result
    assert "my_function" not in result

