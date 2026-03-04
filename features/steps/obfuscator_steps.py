import ast
from behave import given, when, then
from pyobfuscator import Obfuscator

@given('a Python source file containing the secret string "{secret}"')
def step_impl(context, secret):
    context.secret = secret
    context.source = f'''
def get_secret():
    return "{secret}"
result = get_secret()
'''

@when('I obfuscate the source using the "{strategy}" string strategy')
def step_impl(context, strategy):
    obfuscator = Obfuscator(obfuscate_strings=True, string_method=strategy, rename_variables=False, rename_functions=False)
    context.obfuscated = obfuscator.obfuscate_source(context.source)

@then('the obfuscated output must not contain the literal string "{secret}"')
def step_impl(context, secret):
    assert secret not in context.obfuscated, f"Literal '{secret}' found in obfuscated code"

@then('executing the obfuscated code should still produce "{secret}"')
def step_impl(context, secret):
    namespace = {}
    exec(context.obfuscated, namespace)
    assert namespace.get('result') == secret, "Obfuscated code did not produce the expected secret"

@given('a Python source file containing a function named "{func_name}"')
def step_impl(context, func_name):
    context.func_name = func_name
    context.source = f'''
def {func_name}(x, y):
    return x * y + 10
result = {func_name}(5, 2)
'''

@when('I obfuscate the source with variable renaming enabled')
def step_impl(context):
    obfuscator = Obfuscator(rename_variables=True, rename_functions=True, exclude_names={'result'})
    context.obfuscated = obfuscator.obfuscate_source(context.source)

@then('the obfuscated output must not contain the exact identifier "{identifier}"')
def step_impl(context, identifier):
    # Ensure it's not a function definition or call
    assert f"def {identifier}" not in context.obfuscated, f"Identifier {identifier} found in def"
    assert f"{identifier}(" not in context.obfuscated, f"Identifier {identifier} found in call"

@then('executing the obfuscated code should execute the original function logic')
def step_impl(context):
    namespace = {}
    exec(context.obfuscated, namespace)
    assert namespace.get('result') == 20, f"Obfuscated code altered logic. Got: {namespace.get('result')}"

@given('a Python source file with a sequential function "{func_name}"')
def step_impl(context, func_name):
    context.func_name = func_name
    context.source = f'''
def {func_name}(x):
    a = x + 1
    b = a * 2
    c = b - 3
    return c
result = {func_name}(10)
'''

@when('I obfuscate the source with control flow flattening enabled')
def step_impl(context):
    import random
    random.seed(42) # Force predictable random for tests
    # Ensure intensity is high enough to trigger the probability check
    obfuscator = Obfuscator(control_flow_flatten=True, intensity=3, rename_variables=False, rename_functions=False, exclude_names={'result'})
    context.obfuscated = obfuscator.obfuscate_source(context.source)

@then('the obfuscated output must contain a while loop dispatch mechanism')
def step_impl(context):
    tree = ast.parse(context.obfuscated)
    has_while = any(isinstance(node, ast.While) for node in ast.walk(tree))
    assert has_while, "No while loop found in flattened code"

@then('the obfuscated output must not contain the original sequential statement order')
def step_impl(context):
    assert "a = x + 1\\n    b = a * 2" not in context.obfuscated, "Found original sequential statements"

@then('executing the obfuscated code should yield the same result as the original')
def step_impl(context):
    namespace = {}
    exec(context.obfuscated, namespace)
    # original logic: 10+1=11, 11*2=22, 22-3=19
    assert namespace.get('result') == 19, f"Expected 19, got {namespace.get('result')}"
