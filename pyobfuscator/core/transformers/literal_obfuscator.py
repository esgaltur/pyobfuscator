# -*- coding: utf-8 -*-
"""
Literal and builtin obfuscation for PyObfuscator.

Provides techniques for obscuring numeric literals and builtin function calls.
"""

import ast
import random
from typing import Set, Optional

from .base import BaseTransformer
from ..registry import TransformerRegistry


@TransformerRegistry.register("number_obfuscator")
class NumberObfuscator(BaseTransformer):
    """
    Obfuscates numeric literals.
    """

    def __init__(self, intensity: int = 1, **kwargs):
        self.intensity = min(max(intensity, 1), 3)

    def _obfuscate_int(self, n: int) -> ast.expr:
        if n == 0: return ast.Constant(value=0)
        
        def _make_xor():
            mask = random.randint(1, 255)
            return ast.BinOp(left=ast.Constant(value=n ^ mask), op=ast.BitXor(), right=ast.Constant(value=mask))

        return _make_xor()

    def visit_Constant(self, node: ast.Constant) -> ast.expr:
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            if abs(node.value) > 1 and random.random() < 0.4 * self.intensity:
                return self._obfuscate_int(node.value)
        return node

    def transform(self, source: str, context: Optional['TransformationContext'] = None) -> str:
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)


@TransformerRegistry.register("builtin_obfuscator")
class BuiltinObfuscator(BaseTransformer):
    """
    Obfuscates calls to builtin functions.
    """

    SAFE_BUILTINS = {'len', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set', 'bool'}

    def __init__(self, **kwargs):
        """Constructor for BuiltinObfuscator. No specific configuration needed."""
        super().__init__()

    def visit_Call(self, node: ast.Call) -> ast.Call:
        if isinstance(node.func, ast.Name) and node.func.id in self.SAFE_BUILTINS:
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

    def transform(self, source: str, context: Optional['TransformationContext'] = None) -> str:
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)

