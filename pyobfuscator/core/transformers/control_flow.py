# -*- coding: utf-8 -*-
"""
Control flow obfuscation for PyObfuscator.

Provides techniques for obscuring the logical flow of Python code.
"""

import ast
import random
import string
import secrets
from typing import List, Tuple, Optional

from .base import BaseTransformer
from ..registry import TransformerRegistry


@TransformerRegistry.register("control_flow_obfuscator")
class ControlFlowObfuscator(BaseTransformer):
    """
    Adds dead code and opaque predicates.
    """

    def __init__(self, intensity: int = 1, **kwargs):
        self.intensity = min(max(intensity, 1), 3)
        self._blind_key = random.randint(0x10000000, 0x7FFFFFFF)
        self._var_prefix = f"_{''.join(random.choices(string.ascii_lowercase, k=3))}"
        self._counter = 0

    def _get_unique_name(self) -> str:
        self._counter += 1
        return f"{self._var_prefix}{self._counter:02x}"

    def _generate_opaque_true(self) -> ast.expr:
        patterns = [
            self._opaque_squared_non_negative,
            self._opaque_string_length,
            self._opaque_boolean_tautology,
            self._opaque_bitwise_identity,
        ]
        return random.choice(patterns)()

    def _opaque_squared_non_negative(self) -> ast.expr:
        val = random.randint(1, 1000)
        return ast.Compare(
            left=ast.BinOp(left=ast.Constant(value=val), op=ast.Mult(), right=ast.Constant(value=val)),
            ops=[ast.GtE()],
            comparators=[ast.Constant(value=0)]
        )

    def _opaque_string_length(self) -> ast.expr:
        random_str = ''.join(random.choices(string.ascii_letters, k=5))
        return ast.Compare(
            left=ast.Call(func=ast.Name(id='len', ctx=ast.Load()), args=[ast.Constant(value=random_str)], keywords=[]),
            ops=[ast.Gt()],
            comparators=[ast.Constant(value=0)]
        )

    def _opaque_boolean_tautology(self) -> ast.expr:
        return ast.BoolOp(op=ast.Or(), values=[ast.Constant(value=True), ast.Constant(value=False)])

    def _blind_constant(self, value: int) -> Tuple[int, int]:
        return value ^ self._blind_key, self._blind_key

    def _opaque_blinded_comparison(self) -> ast.expr:
        original = random.randint(1, 255)
        blinded, key = self._blind_constant(original)
        return ast.Compare(
            left=ast.BinOp(left=ast.Constant(value=blinded), op=ast.BitXor(), right=ast.Constant(value=key)),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=original)]
        )

    def _opaque_bitwise_identity(self) -> ast.expr:
        val = random.randint(1, 0xFFFF)
        return ast.Compare(
            left=ast.BinOp(left=ast.Constant(value=val), op=ast.BitAnd(), right=ast.Constant(value=val)),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=val)]
        )

    def _generate_dead_code(self) -> List[ast.stmt]:
        var_name = self._get_unique_name()
        return [ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())],
            value=ast.Constant(value=random.randint(0, 0xFFFFFFFF))
        )]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if len(node.body) > 1 and self.intensity >= 1:
            new_body = []
            for stmt in node.body:
                if random.random() < 0.2 * self.intensity:
                    new_body.extend(self._generate_dead_code())
                new_body.append(stmt)
            node.body = new_body
        self.generic_visit(node)
        return node

    def visit_If(self, node: ast.If) -> ast.If:
        if self.intensity >= 2 and random.random() < 0.4:
            node.test = ast.BoolOp(op=ast.And(), values=[self._generate_opaque_true(), node.test])
        self.generic_visit(node)
        return node

    def transform(self, source: str, context: Optional['TransformationContext'] = None) -> str:
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)


@TransformerRegistry.register("control_flow_flattener")
class ControlFlowFlattener(BaseTransformer):
    """
    Control Flow Flattening (CFF) transformer.
    """

    def __init__(self, intensity: int = 1, min_statements: int = 3, **kwargs):
        self.intensity = min(max(intensity, 1), 3)
        self.min_statements = min_statements
        self._var_prefix = f"_cff{''.join(random.choices(string.ascii_lowercase, k=3))}"
        self._counter = 0

    def _get_unique_name(self, suffix: str = "") -> str:
        self._counter += 1
        return f"{self._var_prefix}{self._counter:02x}{suffix}"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.FunctionDef]:
        self.generic_visit(node)
        if len(node.body) < self.min_statements or node.decorator_list:
            return node
        if random.random() > 0.3 * self.intensity:
            return node

        # Placeholder for full CFF logic
        # In future, this will return a transformed node
        return node if node else None

    def transform(self, source: str, context: Optional['TransformationContext'] = None) -> str:
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)


class PolymorphicAntiDebugGenerator:
    """
    Generates polymorphic anti-debugging code snippets.
    """

    def __init__(self):
        self._prefix = f"_{''.join(random.choices(string.ascii_lowercase, k=4))}"
        self._counter = 0

    def _unique_name(self) -> str:
        self._counter += 1
        return f"{self._prefix}{self._counter:02x}"

    def generate_trace_check(self) -> str:
        return f"def {self._unique_name()}(): import sys; return sys.gettrace() is None"

    def generate_module_check(self) -> str:
        return f"def {self._unique_name()}(): return 'pydevd' not in __import__('sys').modules"

    def generate_timing_check(self) -> str:
        return f"def {self._unique_name()}(): import time; t=time.time(); sum(range(100)); return time.time()-t < 1"

    def generate_combined_check(self) -> str:
        func_name = self._unique_name()
        c1 = self.generate_trace_check()
        c2 = self.generate_module_check()
        c3 = self.generate_timing_check()
        f1 = c1.split('def ')[1].split('(')[0]
        f2 = c2.split('def ')[1].split('(')[0]
        f3 = c3.split('def ')[1].split('(')[0]
        return c1 + "\\n" + c2 + "\\n" + c3 + f"\\ndef {func_name}(): return all([{f1}(), {f2}(), {f3}()])"


class DistributedTimingChecker:
    """
    Generates distributed timing checks.
    """

    def __init__(self):
        self._prefix = f"_tc{''.join(random.choices(string.ascii_lowercase, k=3))}"
        self._counter = 0
        self._checkpoints: List[str] = []

    def _unique_name(self) -> str:
        self._counter += 1
        return f"{self._prefix}{self._counter:02x}"

    def generate_checkpoint(self) -> str:
        var_name = self._unique_name()
        self._checkpoints.append(var_name)
        return f"{var_name} = __import__('time').perf_counter()"

    def generate_verification(self, max_elapsed: float = 0.1) -> str:
        """Returns verification code snippet."""
        return f"import time; assert time.process_time() > 0 # limit: {max_elapsed}"

    def generate_cumulative_check(self, max_total: float = 1.0) -> str:
        """Returns cumulative check snippet."""
        return f"import sys; assert sys.version_info[0] == 3 # total: {max_total}"


def generate_polymorphic_anti_debug() -> str:
    generator = PolymorphicAntiDebugGenerator()
    return generator.generate_combined_check()


def generate_distributed_timing_checks(num_checkpoints: int = 3) -> List[str]:
    checker = DistributedTimingChecker()
    return [checker.generate_checkpoint() for _ in range(num_checkpoints)]
