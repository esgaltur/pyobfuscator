# -*- coding: utf-8 -*-
import ast
import random
import subprocess
import sys
from pathlib import Path

from pyobfuscator import Obfuscator

def test_code_virtualization_basic():
    source = """
def secure_compute(a, b):
    x = a + b
    y = x * 2
    z = y ^ 123
    return z

result = secure_compute(10, 20)
"""
    # Force virtualization by setting intensity high and seed
    random.seed(42)
    
    obfuscator = Obfuscator(
        code_virtualization=True,
        intensity=10,
        rename_variables=False,
        rename_functions=False,
        exclude_names={'result'}
    )
    
    obfuscated = obfuscator.obfuscate_source(source)
    
    # Check if VM was injected
    assert "VM()" in obfuscated or "VM" in obfuscated
    assert "execute(" in obfuscated
    
    # Verify execution
    # original logic: (10+20)*2 ^ 123 = 60 ^ 123 = 71
    namespace = {}
    exec(obfuscated, namespace)
    assert namespace.get('result') == 71, f"Virtualization failed. Expected 71, got {namespace.get('result')}"


def test_encrypted_virtualization_uses_distributed_runtime(tmp_path: Path):
    source = """
def secure_compute(a, b):
    x = a + b
    y = x * 2
    return y

print(secure_compute(10, 20))
"""
    random.seed(42)
    obfuscator = Obfuscator(
        code_virtualization=True,
        intensity=10,
        rename_variables=False,
        rename_functions=False,
        anti_debug=False,
    )

    protected, runtime = obfuscator.protect_source(source, "protected.py")
    protected_path = tmp_path / "protected.py"
    runtime_path = tmp_path / f"skjol_runtime_{obfuscator.runtime_protector.runtime_id}.py"
    protected_path.write_text(protected, encoding="utf-8")
    runtime_path.write_text(runtime, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, protected_path.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "60"


def test_unsupported_function_call_is_not_silently_virtualized():
    source = """
SECRET_VALUE = "abc"
def measured_length(offset):
    value = len(SECRET_VALUE)
    return value + offset

result = measured_length(4)
"""
    random.seed(42)
    obfuscator = Obfuscator(
        code_virtualization=True,
        intensity=10,
        encrypt_code=False,
        rename_variables=False,
        rename_functions=False,
        obfuscate_strings=False,
    )

    transformed = obfuscator.obfuscate_source(source)
    namespace = {}
    exec(transformed, namespace)

    assert namespace["result"] == 7
    assert "_SkjolVM" not in transformed

if __name__ == "__main__":
    test_code_virtualization_basic()
    print("Code virtualization test passed!")
