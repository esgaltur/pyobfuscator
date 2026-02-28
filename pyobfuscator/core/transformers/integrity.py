# -*- coding: utf-8 -*-
"""
Integrity and Honey-Pot transformer for PyObfuscator.

Provides distributed integrity checks and fake identifier generation.
"""

import ast
import random
import secrets
from typing import Optional

from .base import BaseTransformer
from ..registry import TransformerRegistry
from ..context import TransformationContext


@TransformerRegistry.register("integrity_transformer")
class IntegrityTransformer(BaseTransformer):
    """
    Implements Distributed Integrity Verification and Honey-Pots.
    """

    def __init__(self, intensity: int = 1, enable_honeypots: bool = True, **kwargs):
        self.intensity = min(max(intensity, 1), 3)
        self.enable_honeypots = enable_honeypots
        self.context: Optional[TransformationContext] = None

    def _generate_honeypot(self) -> ast.stmt:
        """
        Generates a fake variable with an enticing name.
        If accessed, it triggers an exception.
        """
        enticing_names = ['_API_KEY', 'ADMIN_PASSWORD', 'AWS_SECRET_ACCESS_KEY', 'DB_CREDENTIALS']
        name = random.choice(enticing_names)
        
        # Add to shared context so we know it exists
        if self.context:
            self.context.state["honeypots"].add(name)

        # property that raises RuntimeError when accessed
        return ast.Assign(
            targets=[ast.Name(id=name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id='property', ctx=ast.Load()),
                args=[
                    ast.Lambda(
                        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg='_')], kwonlyargs=[], kw_defaults=[], defaults=[]),
                        body=ast.Call(
                            func=ast.Name(id='RuntimeError', ctx=ast.Load()),
                            args=[ast.Constant(value="Honey-Pot Triggered: Unauthorized access detected.")],
                            keywords=[]
                        )
                    )
                ],
                keywords=[]
            )
        )

    def _generate_distributed_check(self) -> Optional[ast.stmt]:
        """
        Generates a check against a previously recorded checkpoint
        from the TransformationContext.
        """
        if not self.context or not self.context.state.get("checkpoints"):
            return None

        # Pick a random previous checkpoint to verify
        target_checkpoint = random.choice(self.context.state["checkpoints"])
        
        # A simple check: if the checkpoint exists, assert it is True
        return ast.If(
            test=ast.Compare(
                left=ast.Name(id=target_checkpoint, ctx=ast.Load()),
                ops=[ast.IsNot()],
                comparators=[ast.Name(id='True', ctx=ast.Load())]
            ),
            body=[ast.Raise(exc=ast.Call(func=ast.Name(id='RuntimeError', ctx=ast.Load()), args=[ast.Constant(value="Integrity failure")], keywords=[]), cause=None)],
            orelse=[]
        )

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Inject honeypots at the module level."""
        self.generic_visit(node)
        if self.enable_honeypots and self.intensity > 1:
            if random.random() < 0.5:
                node.body.insert(0, self._generate_honeypot())
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Inject distributed checks into functions."""
        self.generic_visit(node)
        
        # Record this function as a checkpoint
        checkpoint_name = f"_chk_{secrets.token_hex(4)}"
        if self.context:
            self.context.state["checkpoints"].append(checkpoint_name)
            
            # Inject the checkpoint definition
            node.body.insert(0, ast.Assign(
                targets=[ast.Name(id=checkpoint_name, ctx=ast.Store())],
                value=ast.Constant(value=True)
            ))

            # Optionally verify a previous checkpoint
            if random.random() < 0.3 * self.intensity:
                check = self._generate_distributed_check()
                if check:
                    node.body.append(check)

        return node

    def transform(self, source: str, context: Optional[TransformationContext] = None) -> str:
        self.context = context
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)
