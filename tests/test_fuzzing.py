import ast
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
from pyobfuscator import Obfuscator

# Define a strategy to generate simple arithmetic ASTs
def simple_expr_strategy():
    # Base cases: integers
    leaves = st.integers(min_value=-100, max_value=100)
    
    # Recursive case: operations
    def build_binop(children):
        left, right = children
        ops = [ast.Add(), ast.Sub(), ast.Mult()]
        # We avoid Div to prevent ZeroDivisionError during random generation
        return st.builds(ast.BinOp, left=st.just(left), op=st.sampled_from(ops), right=st.just(right))

    # Wrap integers in ast.Constant
    ast_leaves = st.builds(ast.Constant, value=leaves)
    
    # Recursive strategy
    return st.recursive(
        ast_leaves,
        lambda children: st.tuples(children, children).flatmap(build_binop),
        max_leaves=10
    )

@given(expr=simple_expr_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_semantic_equivalence_fuzzing(expr):
    """
    Fuzz test: Generates random mathematical expressions, evaluates them,
    obfuscates them using all features, and verifies the result is identical.
    """
    # Wrap expression in an assignment
    assign = ast.Assign(
        targets=[ast.Name(id='result', ctx=ast.Store())],
        value=expr
    )
    module = ast.Module(body=[assign], type_ignores=[])
    ast.fix_missing_locations(module)
    
    source = ast.unparse(module)
    
    # Evaluate original
    original_namespace = {}
    try:
        exec(source, original_namespace)
        expected_result = original_namespace.get('result')
    except Exception:
        # Ignore expressions that cause generic errors (e.g., overflow)
        return

    # Obfuscate with heavy settings
    obfuscator = Obfuscator(
        rename_variables=True,
        obfuscate_strings=True,
        number_obfuscation=True,
        control_flow_flatten=True, # Even though it's an assignment, tests pipeline resilience
        intensity=3,
        exclude_names={'result'}
    )
    
    try:
        obfuscated_source = obfuscator.obfuscate_source(source)
    except Exception as e:
        assert False, f"Obfuscator failed on source:\\n{source}\\nError: {e}"

    # Evaluate obfuscated
    obfuscated_namespace = {}
    try:
        exec(obfuscated_source, obfuscated_namespace)
        actual_result = obfuscated_namespace.get('result')
    except Exception as e:
        assert False, f"Obfuscated code crashed.\\nOriginal:\\n{source}\\nObfuscated:\\n{obfuscated_source}\\nError: {e}"

    assert actual_result == expected_result, f"Mismatch!\\nOriginal logic produced {expected_result}\\nObfuscated produced {actual_result}\\nOriginal source:\\n{source}\\nObfuscated source:\\n{obfuscated_source}"
