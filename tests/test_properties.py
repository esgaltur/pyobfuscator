# -*- coding: utf-8 -*-
"""
Property-based tests for PyObfuscator.
Generates random Python-like code snippets and verifies they remain executable.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from pyobfuscator import Obfuscator


# A strategy to generate simple but valid Python snippets
def python_snippets():
    # We use a recursive strategy to build nested structures
    return st.recursive(
        st.one_of(
            st.just("x = 1"),
            st.just("def f(y): return y + 1"),
            st.just("class A: pass"),
            st.just("print('hello')"),
            st.just("[i for i in range(10)]"),
            st.just("x = {'a': 1, 'b': 2}"),
        ),
        lambda children: st.one_of(
            st.builds(lambda c: "\n".join(c), st.lists(children, min_size=1, max_size=3)),
            st.builds(lambda c: f"if True:\n    {c}", children),
        ),
        max_leaves=5
    )


@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None, max_examples=50)
@given(source=python_snippets())
def test_obfuscation_preserves_executable_syntax(source):
    """
    Hypothesis test: Any random valid snippet should remain valid syntax
    after obfuscation and execute without SyntaxError.
    """
    obfuscator = Obfuscator(
        encrypt_code=False,
        control_flow=True,
        number_obfuscation=True,
        obfuscate_strings=True,
        intensity=2
    )
    
    try:
        # Obfuscate
        obfuscated = obfuscator.obfuscate_source(source)
        
        # Verify it still parses
        import ast
        ast.parse(obfuscated)
        
        # Verify it executes (in a clean namespace)
        namespace = {"__builtins__": __builtins__}
        exec(obfuscated, namespace)
        
    except Exception as e:
        # If the original source failed, ignore it
        try:
            exec(source, {})
        except Exception:
            return
            
        # If the original worked but obfuscated failed, we found a bug!
        pytest.fail(
            f"Obfuscation broke valid code!\n"
            f"Original:\n{source}\n\n"
            f"Obfuscated:\n{obfuscated}\n"
            f"Error: {e}"
        )


def test_polymorphic_strings_property():
    """
    Verify that two runs on the same string produce different code (Polymorphism).
    """
    obf = Obfuscator(encrypt_code=False, string_method="polymorphic", exclude_names={"s"})
    source = "s = 'This is a secret string'"
    
    run1 = obf.obfuscate_source(source)
    run2 = obf.obfuscate_source(source)
    
    assert run1 != run2, "Polymorphic obfuscation failed to produce unique output"
    
    # But both must evaluate to the same value
    ns1, ns2 = {}, {}
    exec(run1, ns1)
    exec(run2, ns2)
    assert ns1['s'] == ns2['s'] == 'This is a secret string'

