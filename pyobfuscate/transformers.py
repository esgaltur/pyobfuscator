# -*- coding: utf-8 -*-
"""
Additional obfuscation transformers for advanced protection.
"""

import ast
import random
import string
from typing import List


class ControlFlowObfuscator(ast.NodeTransformer):
    """
    Adds control flow obfuscation by inserting dead code
    and opaque predicates.
    """

    def __init__(self, intensity: int = 1):
        """
        Initialize the control flow obfuscator.

        Args:
            intensity: Level of obfuscation (1-3)
        """
        self.intensity = min(max(intensity, 1), 3)

    def _generate_opaque_true(self) -> ast.Compare:
        """Generate an expression that always evaluates to True."""
        patterns = [
            # (x * x) >= 0
            lambda: ast.Compare(
                left=ast.BinOp(
                    left=ast.Constant(value=random.randint(1, 100)),
                    op=ast.Mult(),
                    right=ast.Constant(value=random.randint(1, 100))
                ),
                ops=[ast.GtE()],
                comparators=[ast.Constant(value=0)]
            ),
            # len('...') > 0
            lambda: ast.Compare(
                left=ast.Call(
                    func=ast.Name(id='len', ctx=ast.Load()),
                    args=[ast.Constant(value=''.join(random.choices(string.ascii_letters, k=5)))],
                    keywords=[]
                ),
                ops=[ast.Gt()],
                comparators=[ast.Constant(value=0)]
            ),
            # True or False
            lambda: ast.BoolOp(
                op=ast.Or(),
                values=[ast.Constant(value=True), ast.Constant(value=False)]
            ),
        ]
        return random.choice(patterns)()

    def _generate_dead_code(self) -> List[ast.stmt]:
        """Generate dead code statements."""
        var_name = f"_d{''.join(random.choices(string.ascii_lowercase, k=4))}"
        patterns = [
            # x = some_value
            [ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=ast.Constant(value=random.randint(0, 1000))
            )],
            # if False: pass
            [ast.If(
                test=ast.Constant(value=False),
                body=[ast.Pass()],
                orelse=[]
            )],
        ]
        return random.choice(patterns)

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

        patterns = [
            # n = a + b
            lambda: ast.BinOp(
                left=ast.Constant(value=n + random.randint(1, 100)),
                op=ast.Sub(),
                right=ast.Constant(value=random.randint(1, 100))
            ),
            # n = a * b + c (where a*b + c = n)
            lambda: (
                ast.BinOp(
                    left=ast.BinOp(
                        left=ast.Constant(value=(factor := random.randint(2, 10))),
                        op=ast.Mult(),
                        right=ast.Constant(value=n // factor)
                    ),
                    op=ast.Add(),
                    right=ast.Constant(value=n % factor)
                ) if n > 10 else ast.Constant(value=n)
            ),
            # n = a ^ b (XOR)
            lambda: ast.BinOp(
                left=ast.Constant(value=n ^ (mask := random.randint(1, 255))),
                op=ast.BitXor(),
                right=ast.Constant(value=mask)
            ),
        ]

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
        control_flow: Enable control flow obfuscation
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
