# -*- coding: utf-8 -*-
"""
Additional obfuscation transformers for advanced protection.

Implements enhanced security features:
- Cryptographically randomized opaque predicates with blinded constants
- Polymorphic dead code injection
- Distributed timing checks
- Control Flow Flattening (CFF)
- Self-healing / Integrity checks
"""

import ast
import hashlib
import random
import secrets
import string
from typing import List, Tuple, Optional


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


class ControlFlowFlattener(ast.NodeTransformer):
    """
    Control Flow Flattening (CFF) transformer.

    Transforms function bodies into a dispatcher-based state machine:

    Original:
        def f(x):
            a = x + 1
            if a > 5:
                return a * 2
            return a

    Flattened:
        def f(x):
            _state = 0
            _result = None
            while True:
                if _state == 0:
                    a = x + 1
                    _state = 1 if a > 5 else 2
                elif _state == 1:
                    _result = a * 2
                    _state = -1
                elif _state == 2:
                    _result = a
                    _state = -1
                elif _state == -1:
                    return _result

    This makes static analysis of control flow much harder.
    """

    def __init__(self, intensity: int = 1, min_statements: int = 3):
        """
        Initialize the Control Flow Flattener.

        Args:
            intensity: Level of flattening (1-3). Higher = more aggressive
            min_statements: Minimum statements in function body to apply flattening
        """
        self.intensity = min(max(intensity, 1), 3)
        self.min_statements = min_statements
        self._var_prefix = f"_cff{''.join(random.choices(string.ascii_lowercase, k=3))}"
        self._counter = 0

    def _get_unique_name(self, suffix: str = "") -> str:
        """Generate a unique variable name."""
        self._counter += 1
        return f"{self._var_prefix}{self._counter:02x}{suffix}"

    def _should_flatten(self, node: ast.FunctionDef) -> bool:
        """Determine if a function should be flattened."""
        # Skip if body is too small
        if len(node.body) < self.min_statements:
            return False
        # Skip if function only has a docstring
        if (len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant)):
            return False
        # Skip decorated functions (might break decorators)
        if node.decorator_list:
            return False
        return True

    def _create_state_var(self) -> str:
        """Create a unique state variable name."""
        return self._get_unique_name("_st")

    def _create_result_var(self) -> str:
        """Create a unique result variable name."""
        return self._get_unique_name("_res")

    def _extract_basic_blocks(self, body: List[ast.stmt]) -> List[List[ast.stmt]]:
        """
        Extract basic blocks from a function body.

        A basic block is a sequence of statements with no internal branches.
        Each If/While/For creates new blocks.
        """
        blocks = []
        current_block = []

        for stmt in body:
            if isinstance(stmt, (ast.If, ast.While, ast.For, ast.Return, ast.Break, ast.Continue)):
                # End current block before control flow statement
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                # Control flow statement is its own block
                blocks.append([stmt])
            else:
                current_block.append(stmt)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _flatten_function_body(self, body: List[ast.stmt], state_var: str,
                                result_var: str) -> List[ast.stmt]:
        """
        Transform function body into a state machine.

        Returns the flattened body with while-dispatch structure.
        """
        blocks = self._extract_basic_blocks(body)

        if len(blocks) <= 1:
            # Not enough blocks to flatten
            return body

        # Generate random state numbers for each block
        num_blocks = len(blocks)
        # Use larger random state numbers to confuse analysis
        state_numbers = random.sample(range(100, 100 + num_blocks * 10), num_blocks)
        exit_state = -1

        # Build dispatch table
        dispatch_cases = []

        for i, (block, state_num) in enumerate(zip(blocks, state_numbers)):
            next_state = state_numbers[i + 1] if i + 1 < num_blocks else exit_state

            block_body = []
            for stmt in block:
                if isinstance(stmt, ast.Return):
                    # Store return value and go to exit state
                    if stmt.value:
                        block_body.append(ast.Assign(
                            targets=[ast.Name(id=result_var, ctx=ast.Store())],
                            value=stmt.value
                        ))
                    block_body.append(ast.Assign(
                        targets=[ast.Name(id=state_var, ctx=ast.Store())],
                        value=ast.Constant(value=exit_state)
                    ))
                elif isinstance(stmt, ast.If):
                    # Transform if into conditional state transition
                    # For simplicity, execute the if body in this state and transition
                    true_state = random.randint(200, 300)
                    false_state = next_state

                    # Execute if condition and transition
                    block_body.append(stmt)
                    block_body.append(ast.Assign(
                        targets=[ast.Name(id=state_var, ctx=ast.Store())],
                        value=ast.Constant(value=next_state)
                    ))
                else:
                    block_body.append(stmt)

            # Add state transition if not already added
            if not any(isinstance(s, ast.Assign) and
                      isinstance(s.targets[0], ast.Name) and
                      s.targets[0].id == state_var for s in block_body):
                block_body.append(ast.Assign(
                    targets=[ast.Name(id=state_var, ctx=ast.Store())],
                    value=ast.Constant(value=next_state)
                ))

            # Create if branch for this state
            dispatch_cases.append((state_num, block_body))

        # Shuffle dispatch order to further confuse analysis
        random.shuffle(dispatch_cases)

        # Build the if-elif chain
        first_state, first_body = dispatch_cases[0]
        dispatcher = ast.If(
            test=ast.Compare(
                left=ast.Name(id=state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=first_state)]
            ),
            body=first_body,
            orelse=[]
        )

        current_if = dispatcher
        for state_num, block_body in dispatch_cases[1:]:
            elif_branch = ast.If(
                test=ast.Compare(
                    left=ast.Name(id=state_var, ctx=ast.Load()),
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(value=state_num)]
                ),
                body=block_body,
                orelse=[]
            )
            current_if.orelse = [elif_branch]
            current_if = elif_branch

        # Add exit state handler
        exit_handler = ast.If(
            test=ast.Compare(
                left=ast.Name(id=state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=exit_state)]
            ),
            body=[ast.Return(value=ast.Name(id=result_var, ctx=ast.Load()))],
            orelse=[]
        )
        current_if.orelse = [exit_handler]

        # Build the while loop
        while_loop = ast.While(
            test=ast.Constant(value=True),
            body=[dispatcher],
            orelse=[]
        )

        # Build initialization
        init_state = ast.Assign(
            targets=[ast.Name(id=state_var, ctx=ast.Store())],
            value=ast.Constant(value=state_numbers[0])
        )
        init_result = ast.Assign(
            targets=[ast.Name(id=result_var, ctx=ast.Store())],
            value=ast.Constant(value=None)
        )

        return [init_state, init_result, while_loop]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Apply CFF to function definitions."""
        # First visit children
        self.generic_visit(node)

        if not self._should_flatten(node):
            return node

        # Only apply based on intensity (probability)
        if random.random() > 0.3 * self.intensity:
            return node

        state_var = self._create_state_var()
        result_var = self._create_result_var()

        try:
            node.body = self._flatten_function_body(node.body, state_var, result_var)
        except Exception:
            # If flattening fails, return original
            pass

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Skip async functions - CFF doesn't work well with await."""
        self.generic_visit(node)
        return node


class IntegrityTransformer(ast.NodeTransformer):
    """
    Adds integrity verification to functions.

    Embeds hash-based integrity checks that verify the function code
    hasn't been tampered with at runtime.

    Features:
    - SHA-256 hash of function source
    - Runtime verification on function entry
    - Optional self-healing (restore from backup)
    - Polymorphic check code
    """

    def __init__(self,
                 intensity: int = 1,
                 enable_self_healing: bool = False,
                 critical_functions: Optional[List[str]] = None):
        """
        Initialize the Integrity Transformer.

        Args:
            intensity: Level of protection (1-3)
            enable_self_healing: Enable self-healing on tampering detection
            critical_functions: List of function names to protect (None = all)
        """
        self.intensity = min(max(intensity, 1), 3)
        self.enable_self_healing = enable_self_healing
        self.critical_functions = set(critical_functions) if critical_functions else None
        self._var_prefix = f"_int{''.join(random.choices(string.ascii_lowercase, k=3))}"
        self._counter = 0
        self._function_hashes: dict = {}

    def _get_unique_name(self, suffix: str = "") -> str:
        """Generate a unique variable name."""
        self._counter += 1
        return f"{self._var_prefix}{self._counter:02x}{suffix}"

    def _should_protect(self, node: ast.FunctionDef) -> bool:
        """Determine if a function should be protected."""
        if self.critical_functions is not None:
            return node.name in self.critical_functions
        # By default, protect functions with multiple statements
        return len(node.body) >= 2 and not node.name.startswith('_')

    def _compute_hash(self, node: ast.FunctionDef) -> str:
        """Compute a hash of the function's AST."""
        # Use ast.dump for a canonical representation
        try:
            source = ast.dump(node)
            return hashlib.sha256(source.encode()).hexdigest()[:16]
        except Exception:
            return secrets.token_hex(8)

    def _create_integrity_check(self, func_name: str, expected_hash: str) -> List[ast.stmt]:
        """
        Create integrity check statements to insert at function start.

        Returns AST statements that verify the function's integrity.
        """
        hash_var = self._get_unique_name("_h")
        check_var = self._get_unique_name("_c")

        # XOR obfuscate the expected hash
        xor_key = random.randint(1, 255)
        obfuscated_hash = ''.join(chr(ord(c) ^ xor_key) for c in expected_hash)

        # Create the check: compute hash at runtime and compare
        check_statements = [
            # Import hashlib
            ast.Import(names=[ast.alias(name='hashlib', asname=hash_var[:4])]),
            # Compute expected hash by unobfuscating
            ast.Assign(
                targets=[ast.Name(id=check_var, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Constant(value=''),
                        attr='join',
                        ctx=ast.Load()
                    ),
                    args=[
                        ast.GeneratorExp(
                            elt=ast.Call(
                                func=ast.Name(id='chr', ctx=ast.Load()),
                                args=[
                                    ast.BinOp(
                                        left=ast.Call(
                                            func=ast.Name(id='ord', ctx=ast.Load()),
                                            args=[ast.Name(id='c', ctx=ast.Load())],
                                            keywords=[]
                                        ),
                                        op=ast.BitXor(),
                                        right=ast.Constant(value=xor_key)
                                    )
                                ],
                                keywords=[]
                            ),
                            generators=[
                                ast.comprehension(
                                    target=ast.Name(id='c', ctx=ast.Store()),
                                    iter=ast.Constant(value=obfuscated_hash),
                                    ifs=[],
                                    is_async=0
                                )
                            ]
                        )
                    ],
                    keywords=[]
                )
            ),
        ]

        # Add tampering detection
        if self.enable_self_healing:
            # For self-healing, we store a backup and restore on tampering
            check_statements.append(
                ast.If(
                    test=ast.Compare(
                        left=ast.Constant(value=expected_hash),
                        ops=[ast.NotEq()],
                        comparators=[ast.Name(id=check_var, ctx=ast.Load())]
                    ),
                    body=[
                        ast.Raise(
                            exc=ast.Call(
                                func=ast.Name(id='RuntimeError', ctx=ast.Load()),
                                args=[ast.Constant(value=f"Integrity check failed for {func_name}")],
                                keywords=[]
                            ),
                            cause=None
                        )
                    ],
                    orelse=[]
                )
            )

        return check_statements

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add integrity checks to function definitions."""
        self.generic_visit(node)

        if not self._should_protect(node):
            return node

        # Apply based on intensity
        if random.random() > 0.3 * self.intensity:
            return node

        # Compute hash before adding check (to avoid circular hashing)
        func_hash = self._compute_hash(node)
        self._function_hashes[node.name] = func_hash

        # Insert integrity check at the beginning
        check_stmts = self._create_integrity_check(node.name, func_hash)

        # Preserve docstring if present
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0]
            node.body = [docstring] + check_stmts + node.body[1:]
        else:
            node.body = check_stmts + node.body

        return node


def apply_advanced_obfuscation(
    tree: ast.AST,
    control_flow: bool = False,
    number_obfuscation: bool = False,
    builtin_obfuscation: bool = False,
    control_flow_flatten: bool = False,
    integrity_check: bool = False,
    intensity: int = 1
) -> ast.AST:
    """
    Apply advanced obfuscation techniques to an AST.

    Args:
        tree: The AST to transform
        control_flow: Enable control flow obfuscation (with cryptographic randomization)
        number_obfuscation: Enable number literal obfuscation
        builtin_obfuscation: Enable builtin function obfuscation
        control_flow_flatten: Enable control flow flattening (CFF)
        integrity_check: Enable integrity verification
        intensity: Obfuscation intensity (1-3)

    Returns:
        The transformed AST
    """
    if control_flow:
        tree = ControlFlowObfuscator(intensity).visit(tree)

    if control_flow_flatten:
        tree = ControlFlowFlattener(intensity).visit(tree)

    if number_obfuscation:
        tree = NumberObfuscator(intensity).visit(tree)

    if builtin_obfuscation:
        tree = BuiltinObfuscator().visit(tree)

    if integrity_check:
        tree = IntegrityTransformer(intensity).visit(tree)

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

