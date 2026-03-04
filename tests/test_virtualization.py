# -*- coding: utf-8 -*-
import ast
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
    import random
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

if __name__ == "__main__":
    test_code_virtualization_basic()
    print("Code virtualization test passed!")
