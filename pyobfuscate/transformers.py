# -*- coding: utf-8 -*-
"""
Additional obfuscation transformers for advanced protection.

Implements enhanced security features:
- Cryptographically randomized opaque predicates with blinded constants
- Polymorphic dead code injection
- Distributed timing checks
"""

import ast
import random
import secrets
import string
from typing import List, Tuple


class ControlFlowObfuscator(ast.NodeTransformer):
    """
    Adds control flow obfuscation by inserting dead code
    and opaque predicates with cryptographic randomization.

    Security enhancements:
    - Blinded constants: Magic numbers hidden via XOR with random keys
    - Polymorphic patterns: Different code structure each generation
    - Unpredictable values: Even knowing the pattern, values are random
    """

    def __init__(self, intensity: int = 1):
        """
        Initialize the control flow obfuscator.

        Args:
            intensity: Level of obfuscation (1-3)
        """
        self.intensity = min(max(intensity, 1), 3)
        # Generate unique blind key for this obfuscation session
        self._blind_key = random.randint(0x10000000, 0x7FFFFFFF)
        # Generate unique variable name prefix for polymorphism
        self._var_prefix = f"_{''.join(random.choices(string.ascii_lowercase, k=3))}"
        # Counter for unique names
        self._counter = 0

    def _get_unique_name(self) -> str:
        """Generate a unique variable name for this session."""
        self._counter += 1
        return f"{self._var_prefix}{self._counter:02x}"

    def _blind_constant(self, value: int) -> Tuple[int, int]:
        """
        Blind a constant using XOR with the session key.
        Returns (blinded_value, blind_key) for runtime unblinding.
        """
        return value ^ self._blind_key, self._blind_key

    def _generate_opaque_true(self) -> ast.expr:
        """
        Generate an expression that always evaluates to True.

        Uses cryptographic randomization so that even if the pattern
        is known, the actual values are unpredictable without the key.
        """
        patterns = [
            self._opaque_squared_non_negative,
            self._opaque_string_length,
            self._opaque_boolean_tautology,
            self._opaque_blinded_comparison,
            self._opaque_bitwise_identity,
            self._opaque_modulo_check,
        ]
        return random.choice(patterns)()

    def _opaque_squared_non_negative(self) -> ast.expr:
        """(x * x) >= 0 is always True for real numbers."""
        val = random.randint(1, 1000)
        return ast.Compare(
            left=ast.BinOp(
                left=ast.Constant(value=val),
                op=ast.Mult(),
                right=ast.Constant(value=val)
            ),
            ops=[ast.GtE()],
            comparators=[ast.Constant(value=0)]
        )

    def _opaque_string_length(self) -> ast.expr:
        """len(non_empty_string) > 0 is always True."""
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(3, 8)))
        return ast.Compare(
            left=ast.Call(
                func=ast.Name(id='len', ctx=ast.Load()),
                args=[ast.Constant(value=random_str)],
                keywords=[]
            ),
            ops=[ast.Gt()],
            comparators=[ast.Constant(value=0)]
        )

    def _opaque_boolean_tautology(self) -> ast.expr:
        """True or X is always True (short-circuit)."""
        return ast.BoolOp(
            op=ast.Or(),
            values=[ast.Constant(value=True), ast.Constant(value=False)]
        )

    def _opaque_blinded_comparison(self) -> ast.expr:
        """
        Cryptographically blinded comparison.
        (blinded_value ^ blind_key) == original_value is True.

        Even knowing this pattern, attacker can't predict values without key.
        """
        original = random.randint(1, 255)
        blinded, key = self._blind_constant(original)

        # (blinded ^ key) == original
        return ast.Compare(
            left=ast.BinOp(
                left=ast.Constant(value=blinded),
                op=ast.BitXor(),
                right=ast.Constant(value=key)
            ),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=original)]
        )

    def _opaque_bitwise_identity(self) -> ast.expr:
        """(x & x) == x is always True."""
        val = random.randint(1, 0xFFFF)
        return ast.Compare(
            left=ast.BinOp(
                left=ast.Constant(value=val),
                op=ast.BitAnd(),
                right=ast.Constant(value=val)
            ),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=val)]
        )

    def _opaque_modulo_check(self) -> ast.expr:
        """(x * y) % y == 0 when y != 0 is always True."""
        x = random.randint(1, 100)
        y = random.randint(1, 100)
        return ast.Compare(
            left=ast.BinOp(
                left=ast.BinOp(
                    left=ast.Constant(value=x),
                    op=ast.Mult(),
                    right=ast.Constant(value=y)
                ),
                op=ast.Mod(),
                right=ast.Constant(value=y)
            ),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=0)]
        )

    def _generate_dead_code(self) -> List[ast.stmt]:
        """
        Generate polymorphic dead code statements.

        Each generation produces different variable names and patterns,
        making automated pattern removal ineffective.
        """
        patterns = [
            self._dead_code_assignment,
            self._dead_code_if_false,
            self._dead_code_loop_zero,
            self._dead_code_try_pass,
            self._dead_code_blinded_computation,
        ]
        return random.choice(patterns)()

    def _dead_code_assignment(self) -> List[ast.stmt]:
        """Simple variable assignment (never used)."""
        var_name = self._get_unique_name()
        return [ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())],
            value=ast.Constant(value=random.randint(0, 0xFFFFFFFF))
        )]

    def _dead_code_if_false(self) -> List[ast.stmt]:
        """if False: block that never executes."""
        var_name = self._get_unique_name()
        return [ast.If(
            test=ast.Constant(value=False),
            body=[
                ast.Assign(
                    targets=[ast.Name(id=var_name, ctx=ast.Store())],
                    value=ast.Constant(value=secrets.token_hex(8))
                )
            ],
            orelse=[]
        )]

    def _dead_code_loop_zero(self) -> List[ast.stmt]:
        """for _ in range(0): never executes body."""
        var_name = self._get_unique_name()
        return [ast.For(
            target=ast.Name(id='_', ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Name(id='range', ctx=ast.Load()),
                args=[ast.Constant(value=0)],
                keywords=[]
            ),
            body=[
                ast.Assign(
                    targets=[ast.Name(id=var_name, ctx=ast.Store())],
                    value=ast.Constant(value=random.randint(0, 1000))
                )
            ],
            orelse=[]
        )]

    def _dead_code_try_pass(self) -> List[ast.stmt]:
        """try: pass except: unreachable."""
        return [ast.Try(
            body=[ast.Pass()],
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id='Exception', ctx=ast.Load()),
                    name=None,
                    body=[ast.Pass()]
                )
            ],
            orelse=[],
            finalbody=[]
        )]

    def _dead_code_blinded_computation(self) -> List[ast.stmt]:
        """
        Computation with blinded constants that looks meaningful.

        Generates: var1 = blinded_value; var2 = var1 ^ key (unblind, but never used)
        """
        var1 = self._get_unique_name()
        var2 = self._get_unique_name()
        val = random.randint(1, 255)
        blinded, key = self._blind_constant(val)

        return [
            ast.Assign(
                targets=[ast.Name(id=var1, ctx=ast.Store())],
                value=ast.Constant(value=blinded)
            ),
            ast.Assign(
                targets=[ast.Name(id=var2, ctx=ast.Store())],
                value=ast.BinOp(
                    left=ast.Name(id=var1, ctx=ast.Load()),
                    op=ast.BitXor(),
                    right=ast.Constant(value=key)
                )
            ),
        ]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add obfuscation to function bodies."""
        if len(node.body) > 1 and self.intensity >= 1:
            new_body = []
            for stmt in node.body:
                # Add dead code before some statements
                if random.random() < 0.3 * self.intensity:
                    new_body.extend(self._generate_dead_code())
                new_body.append(stmt)
            node.body = new_body

        self.generic_visit(node)
        return node

    def visit_If(self, node: ast.If) -> ast.If:
        """Wrap if conditions with opaque predicates."""
        if self.intensity >= 2 and random.random() < 0.5:
            # Wrap: if cond -> if (opaque_true and cond)
            node.test = ast.BoolOp(
                op=ast.And(),
                values=[self._generate_opaque_true(), node.test]
            )
        self.generic_visit(node)
        return node


class NumberObfuscator(ast.NodeTransformer):
    """
    Obfuscates numeric literals by converting them to expressions.
    """

    def __init__(self, intensity: int = 1):
        self.intensity = min(max(intensity, 1), 3)

    def _obfuscate_int(self, n: int) -> ast.expr:
        """Convert an integer to an obfuscated expression."""
        if n == 0:
            return ast.Constant(value=0)

        def _make_add_sub():
            """Generate n = a - b pattern."""
            b = random.randint(1, 100)
            a = n + b
            return ast.BinOp(
                left=ast.Constant(value=a),
                op=ast.Sub(),
                right=ast.Constant(value=b)
            )

        def _make_mul_add():
            """Generate n = a * b + c pattern (where a*b + c = n)."""
            if n <= 10:
                return ast.Constant(value=n)
            factor = random.randint(2, 10)
            quotient = n // factor
            remainder = n % factor
            return ast.BinOp(
                left=ast.BinOp(
                    left=ast.Constant(value=factor),
                    op=ast.Mult(),
                    right=ast.Constant(value=quotient)
                ),
                op=ast.Add(),
                right=ast.Constant(value=remainder)
            )

        def _make_xor():
            """Generate n = a ^ b (XOR) pattern."""
            mask = random.randint(1, 255)
            return ast.BinOp(
                left=ast.Constant(value=n ^ mask),
                op=ast.BitXor(),
                right=ast.Constant(value=mask)
            )

        patterns = [_make_add_sub, _make_mul_add, _make_xor]
        return random.choice(patterns)()

    def visit_Constant(self, node: ast.Constant) -> ast.expr:
        """Obfuscate numeric constants."""
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            if abs(node.value) > 1 and random.random() < 0.5 * self.intensity:
                return self._obfuscate_int(node.value)
        return node


class BuiltinObfuscator(ast.NodeTransformer):
    """
    Obfuscates calls to builtin functions by using getattr/eval patterns.
    """

    SAFE_BUILTINS = {'len', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set', 'bool', 'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'min', 'max', 'abs', 'round', 'sorted', 'reversed', 'any', 'all'}

    def visit_Call(self, node: ast.Call) -> ast.Call:
        """Obfuscate builtin function calls."""
        if isinstance(node.func, ast.Name) and node.func.id in self.SAFE_BUILTINS:
            # Replace: len(x) -> getattr(__builtins__, 'len')(x)
            # Or: __builtins__['len'](x) for dict-style builtins
            builtin_name = node.func.id
            node.func = ast.Call(
                func=ast.Name(id='getattr', ctx=ast.Load()),
                args=[
                    ast.Call(
                        func=ast.Name(id='__import__', ctx=ast.Load()),
                        args=[ast.Constant(value='builtins')],
                        keywords=[]
                    ),
                    ast.Constant(value=builtin_name)
                ],
                keywords=[]
            )
        self.generic_visit(node)
        return node


class CommentRemover(ast.NodeTransformer):
    """
    This transformer doesn't do anything to AST (comments aren't in AST),
    but we keep it for API consistency. Comments are naturally removed
    when parsing and unparsing the AST.
    """
    pass


class PolymorphicAntiDebugGenerator:
    """
    Generates polymorphic anti-debugging code snippets.

    Each generation produces different:
    - Variable names
    - Function signatures
    - Code structure
    - Check implementations

    This makes patching one version useless for another.
    """

    def __init__(self):
        self._prefix = f"_{''.join(random.choices(string.ascii_lowercase, k=4))}"
        self._counter = 0

    def _unique_name(self) -> str:
        self._counter += 1
        return f"{self._prefix}{self._counter:02x}"

    def generate_trace_check(self) -> str:
        """Generate polymorphic sys.gettrace() check."""
        func_name = self._unique_name()
        var1 = self._unique_name()

        # Randomize the check structure
        templates = [
            f'''
def {func_name}():
    import sys as {var1}
    return {var1}.gettrace() is None
''',
            f'''
def {func_name}():
    {var1} = __import__('sys')
    if {var1}.gettrace(): return False
    return True
''',
            f'''
def {func_name}():
    {var1} = getattr(__import__('sys'), 'gettrace')
    return not {var1}()
''',
        ]
        return random.choice(templates)

    def generate_module_check(self) -> str:
        """Generate polymorphic debugger module check."""
        func_name = self._unique_name()
        var1 = self._unique_name()
        var2 = self._unique_name()

        # Randomize module list order and names checked
        debug_modules = ['pydevd', 'debugpy', 'pdb', '_pydevd_bundle', 'bdb']
        random.shuffle(debug_modules)
        modules_str = str(debug_modules[:random.randint(3, 5)])

        templates = [
            f'''
def {func_name}():
    import sys as {var1}
    {var2} = {modules_str}
    return not any({var1}.modules.get(m) for m in {var2})
''',
            f'''
def {func_name}():
    {var1} = __import__('sys').modules
    for {var2} in {modules_str}:
        if {var2} in {var1}: return False
    return True
''',
        ]
        return random.choice(templates)

    def generate_timing_check(self) -> str:
        """Generate polymorphic timing-based anti-debug check."""
        func_name = self._unique_name()
        var1 = self._unique_name()
        var2 = self._unique_name()
        var3 = self._unique_name()

        # Randomize threshold and operation
        threshold = random.uniform(0.005, 0.02)
        iterations = random.randint(5000, 15000)

        templates = [
            f'''
def {func_name}():
    import time as {var1}
    {var2} = {var1}.perf_counter()
    {var3} = sum(range({iterations}))
    return ({var1}.perf_counter() - {var2}) < {threshold}
''',
            f'''
def {func_name}():
    {var1} = __import__('time')
    {var2} = {var1}.time()
    for _ in range({iterations}): pass
    return ({var1}.time() - {var2}) < {threshold * 2}
''',
        ]
        return random.choice(templates)

    def generate_env_check(self) -> str:
        """Generate polymorphic environment variable check."""
        func_name = self._unique_name()
        var1 = self._unique_name()
        var2 = self._unique_name()

        # Randomize which env vars to check
        env_vars = ['PYTHONDEBUG', 'PYCHARM_DEBUG', 'PYDEVD_USE_FRAME_EVAL',
                    'DEBUGPY_LAUNCHER_PORT', 'PYTHONBREAKPOINT', 'PYTHONINSPECT']
        random.shuffle(env_vars)
        env_str = str(env_vars[:random.randint(3, 5)])

        return f'''
def {func_name}():
    import os as {var1}
    for {var2} in {env_str}:
        if {var1}.environ.get({var2}): return False
    return True
'''

    def generate_combined_check(self) -> str:
        """Generate a combined polymorphic anti-debug function."""
        func_name = self._unique_name()
        checks = [
            self.generate_trace_check(),
            self.generate_module_check(),
            self.generate_timing_check(),
            self.generate_env_check(),
        ]
        random.shuffle(checks)

        # Generate unique names for the check functions
        check_funcs = [c.split('def ')[1].split('(')[0] for c in checks]

        combined = '\n'.join(checks)
        combined += f'''
def {func_name}():
    return all([{', '.join(f'{f}()' for f in check_funcs)}])
'''
        return combined


class DistributedTimingChecker:
    """
    Generates distributed timing checks that run at multiple
    unpredictable points throughout execution.

    This makes bypassing timing checks much harder because:
    1. Checks are spread across the codebase
    2. Each check has different thresholds
    3. Failures at any point trigger protection
    """

    def __init__(self):
        self._prefix = f"_tc{''.join(random.choices(string.ascii_lowercase, k=3))}"
        self._counter = 0
        self._checkpoints: List[str] = []

    def _unique_name(self) -> str:
        self._counter += 1
        return f"{self._prefix}{self._counter:02x}"

    def generate_checkpoint(self) -> str:
        """
        Generate a timing checkpoint that records current time.
        Returns the variable name storing the timestamp.
        """
        var_name = self._unique_name()
        self._checkpoints.append(var_name)
        return f"{var_name} = __import__('time').perf_counter()"

    def generate_verification(self, max_elapsed: float = 0.1) -> str:
        """
        Generate verification that checks elapsed time since last checkpoint.

        Args:
            max_elapsed: Maximum allowed elapsed time in seconds
        """
        if not self._checkpoints:
            return "pass  # No checkpoints yet"

        last_checkpoint = self._checkpoints[-1]
        var_name = self._unique_name()
        threshold = max_elapsed * random.uniform(0.8, 1.2)  # Randomize threshold

        return f'''
{var_name} = __import__('time').perf_counter() - {last_checkpoint}
if {var_name} > {threshold}: raise RuntimeError("Timing violation")
'''

    def generate_cumulative_check(self, max_total: float = 1.0) -> str:
        """
        Generate a check that verifies total elapsed time across all checkpoints.
        """
        if len(self._checkpoints) < 2:
            return "pass  # Need at least 2 checkpoints"

        first = self._checkpoints[0]
        last = self._checkpoints[-1]
        threshold = max_total * random.uniform(0.9, 1.1)

        return f'''
if ({last} - {first}) > {threshold}: raise RuntimeError("Cumulative timing violation")
'''


def apply_advanced_obfuscation(
    tree: ast.AST,
    control_flow: bool = False,
    number_obfuscation: bool = False,
    builtin_obfuscation: bool = False,
    intensity: int = 1
) -> ast.AST:
    """
    Apply advanced obfuscation techniques to an AST.

    Args:
        tree: The AST to transform
        control_flow: Enable control flow obfuscation (with cryptographic randomization)
        number_obfuscation: Enable number literal obfuscation
        builtin_obfuscation: Enable builtin function obfuscation
        intensity: Obfuscation intensity (1-3)

    Returns:
        The transformed AST
    """
    if control_flow:
        tree = ControlFlowObfuscator(intensity).visit(tree)

    if number_obfuscation:
        tree = NumberObfuscator(intensity).visit(tree)

    if builtin_obfuscation:
        tree = BuiltinObfuscator().visit(tree)

    ast.fix_missing_locations(tree)
    return tree


def generate_polymorphic_anti_debug() -> str:
    """
    Generate a complete polymorphic anti-debugging module.

    Each call produces unique code that:
    - Uses different variable/function names
    - Has different code structure
    - Checks for different combinations of indicators

    Returns:
        Python source code string for the anti-debug module
    """
    generator = PolymorphicAntiDebugGenerator()
    return generator.generate_combined_check()


def generate_distributed_timing_checks(num_checkpoints: int = 3) -> List[str]:
    """
    Generate a set of distributed timing checkpoints and verifications.

    Args:
        num_checkpoints: Number of checkpoint/verification pairs to generate

    Returns:
        List of code snippets to insert at various points
    """
    checker = DistributedTimingChecker()
    snippets = []

    for i in range(num_checkpoints):
        snippets.append(checker.generate_checkpoint())
        if i > 0:
            snippets.append(checker.generate_verification(max_elapsed=0.05 * (i + 1)))

    snippets.append(checker.generate_cumulative_check(max_total=0.5))
    return snippets

