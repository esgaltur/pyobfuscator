# -*- coding: utf-8 -*-
"""
String obfuscation module with Strategy pattern.

Provides various strategies for obfuscating string literals in Python code.
"""

import ast
import base64
import random
import string
from abc import ABC, abstractmethod
from typing import Dict, Type, Optional

from .base import BaseTransformer
from ..registry import TransformerRegistry
from ..context import TransformationContext


class StringObfuscationStrategy(ABC):
    """
    Abstract base class for string obfuscation strategies.
    """
    @abstractmethod
    def obfuscate(self, value: str, context: Optional[TransformationContext] = None) -> ast.AST:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

class PolymorphicStrategy(StringObfuscationStrategy):
    """
    Generates a unique, randomized decryption function for each string.
    """
    @property
    def name(self) -> str:
        return "polymorphic"

    def obfuscate(self, value: str, context: Optional[TransformationContext] = None) -> ast.Call:
        key = random.randint(1, 255)
        encoded = bytes([b ^ key for b in value.encode('utf-8')])
        
        # Use context session secret to make names unpredictable
        prefix = "v"
        if context:
            prefix = f"_{context.session_secret[:4].hex()}"
            
        var_b = f"{prefix}_{random.randint(1000, 9999)}"
        
        strategy_choice = random.randint(0, 2)
        
        if strategy_choice == 0:
            # bytes([v ^ key for v in encoded]).decode('utf-8')
            decoding_expr = ast.Call(
                func=ast.Name(id='bytes', ctx=ast.Load()),
                args=[
                    ast.ListComp(
                        elt=ast.BinOp(
                            left=ast.Name(id=var_b, ctx=ast.Load()),
                            op=ast.BitXor(),
                            right=ast.Constant(value=key)
                        ),
                        generators=[
                            ast.comprehension(
                                target=ast.Name(id=var_b, ctx=ast.Store()),
                                iter=ast.Constant(value=encoded),
                                ifs=[],
                                is_async=0
                            )
                        ]
                    )
                ],
                keywords=[]
            )
        elif strategy_choice == 1:
            # ''.join(chr(v ^ key) for v in encoded)
            return ast.Call(
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
                                    left=ast.Name(id=var_b, ctx=ast.Load()),
                                    op=ast.BitXor(),
                                    right=ast.Constant(value=key)
                                )
                            ],
                            keywords=[]
                        ),
                        generators=[
                            ast.comprehension(
                                target=ast.Name(id=var_b, ctx=ast.Store()),
                                iter=ast.Constant(value=encoded),
                                ifs=[],
                                is_async=0
                            )
                        ]
                    )
                ],
                keywords=[]
            )
        else:
            # bytes(map(lambda v: v ^ key, encoded)).decode('utf-8')
            decoding_expr = ast.Call(
                func=ast.Name(id='bytes', ctx=ast.Load()),
                args=[
                    ast.Call(
                        func=ast.Name(id='map', ctx=ast.Load()),
                        args=[
                            ast.Lambda(
                                args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=var_b)], kwonlyargs=[], kw_defaults=[], defaults=[]),
                                body=ast.BinOp(
                                    left=ast.Name(id=var_b, ctx=ast.Load()),
                                    op=ast.BitXor(),
                                    right=ast.Constant(value=key)
                                )
                            ),
                            ast.Constant(value=encoded)
                        ],
                        keywords=[]
                    )
                ],
                keywords=[]
            )

        return ast.Call(
            func=ast.Attribute(
                value=decoding_expr,
                attr='decode',
                ctx=ast.Load()
            ),
            args=[ast.Constant(value='utf-8')],
            keywords=[]
        )

class XorStrategy(StringObfuscationStrategy):
    @property
    def name(self) -> str: return "xor"
    def obfuscate(self, value: str, context: Optional[TransformationContext] = None) -> ast.Call:
        key = random.randint(1, 255)
        encoded = bytes([b ^ key for b in value.encode('utf-8')])
        return ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Name(id='bytes', ctx=ast.Load()), args=[ast.ListComp(elt=ast.BinOp(left=ast.Name(id='b', ctx=ast.Load()), op=ast.BitXor(), right=ast.Constant(value=key)), generators=[ast.comprehension(target=ast.Name(id='b', ctx=ast.Store()), iter=ast.Constant(value=encoded), ifs=[], is_async=0)])], keywords=[]), attr='decode', ctx=ast.Load()), args=[ast.Constant(value='utf-8')], keywords=[])

class HexStrategy(StringObfuscationStrategy):
    @property
    def name(self) -> str: return "hex"
    def obfuscate(self, value: str, context: Optional[TransformationContext] = None) -> ast.Call:
        encoded = value.encode('utf-8').hex()
        return ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Attribute(value=ast.Name(id='bytes', ctx=ast.Load()), attr='fromhex', ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[]), attr='decode', ctx=ast.Load()), args=[ast.Constant(value='utf-8')], keywords=[])

class Base64Strategy(StringObfuscationStrategy):
    @property
    def name(self) -> str: return "base64"
    def obfuscate(self, value: str, context: Optional[TransformationContext] = None) -> ast.Call:
        encoded = base64.b64encode(value.encode('utf-8')).decode('ascii')
        return ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Name(id='__import__', ctx=ast.Load()), args=[ast.Constant(value='base64')], keywords=[]), attr='b64decode', ctx=ast.Load()), args=[ast.Constant(value=encoded)], keywords=[]), attr='decode', ctx=ast.Load()), args=[ast.Constant(value='utf-8')], keywords=[])

class StringObfuscationFactory:
    _strategies: Dict[str, Type[StringObfuscationStrategy]] = {
        "xor": XorStrategy,
        "hex": HexStrategy,
        "base64": Base64Strategy,
        "polymorphic": PolymorphicStrategy,
    }

    @classmethod
    def create(cls, method: str) -> StringObfuscationStrategy:
        strategy_class = cls._strategies.get(method, XorStrategy)
        return strategy_class()

@TransformerRegistry.register("string_obfuscator")
class StringObfuscator(BaseTransformer):
    MIN_STRING_LENGTH = 3

    def __init__(self, method: str = "polymorphic", **kwargs):
        self.method = method
        self._strategy = StringObfuscationFactory.create(method)
        self.context: Optional[TransformationContext] = None

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, str) and len(node.value) >= self.MIN_STRING_LENGTH:
            return self._strategy.obfuscate(node.value, self.context)
        return node

    def transform(self, source: str, context: Optional[TransformationContext] = None) -> str:
        self.context = context
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)

