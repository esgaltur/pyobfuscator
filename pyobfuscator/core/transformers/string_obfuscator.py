# -*- coding: utf-8 -*-
"""
String obfuscation module with Strategy pattern.

Provides various strategies for obfuscating string literals in Python code.
"""

import ast
import base64
import random
from abc import ABC, abstractmethod
from typing import Dict, Type

from .base import BaseTransformer


class StringObfuscationStrategy(ABC):
    """
    Abstract base class for string obfuscation strategies.

    Implements the Strategy pattern for different string obfuscation methods.
    Each concrete strategy provides a different way to encode strings.
    """

    @abstractmethod
    def obfuscate(self, value: str) -> ast.AST:
        """
        Obfuscate a string value.

        Args:
            value: The string literal to obfuscate.

        Returns:
            An AST node that evaluates to the original string at runtime.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this strategy."""
        ...


class XorStrategy(StringObfuscationStrategy):
    """
    XOR-based string obfuscation strategy.

    Encodes strings using XOR with a random key, decoded at runtime.
    This provides lightweight obfuscation that's fast to decode.
    """

    @property
    def name(self) -> str:
        return "xor"

    def obfuscate(self, value: str) -> ast.Call:
        """
        Obfuscate using XOR encoding.

        The result is: bytes([b ^ key for b in encoded]).decode('utf-8')
        """
        key = random.randint(1, 255)
        encoded = bytes([b ^ key for b in value.encode('utf-8')])

        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id='bytes', ctx=ast.Load()),
                    args=[
                        ast.ListComp(
                            elt=ast.BinOp(
                                left=ast.Name(id='b', ctx=ast.Load()),
                                op=ast.BitXor(),
                                right=ast.Constant(value=key)
                            ),
                            generators=[
                                ast.comprehension(
                                    target=ast.Name(id='b', ctx=ast.Store()),
                                    iter=ast.Constant(value=encoded),
                                    ifs=[],
                                    is_async=0
                                )
                            ]
                        )
                    ],
                    keywords=[]
                ),
                attr='decode',
                ctx=ast.Load()
            ),
            args=[ast.Constant(value='utf-8')],
            keywords=[]
        )


class HexStrategy(StringObfuscationStrategy):
    """
    Hex-based string obfuscation strategy.

    Encodes strings as hexadecimal, decoded at runtime.
    """

    @property
    def name(self) -> str:
        return "hex"

    def obfuscate(self, value: str) -> ast.Call:
        """
        Obfuscate using hex encoding.

        The result is: bytes.fromhex('...').decode('utf-8')
        """
        encoded = value.encode('utf-8').hex()

        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='bytes', ctx=ast.Load()),
                        attr='fromhex',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=encoded)],
                    keywords=[]
                ),
                attr='decode',
                ctx=ast.Load()
            ),
            args=[ast.Constant(value='utf-8')],
            keywords=[]
        )


class Base64Strategy(StringObfuscationStrategy):
    """
    Base64-based string obfuscation strategy.

    Encodes strings using Base64, decoded at runtime.
    """

    @property
    def name(self) -> str:
        return "base64"

    def obfuscate(self, value: str) -> ast.Call:
        """
        Obfuscate using base64 encoding.

        The result is: __import__('base64').b64decode('...').decode('utf-8')
        """
        encoded = base64.b64encode(value.encode('utf-8')).decode('ascii')

        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id='__import__', ctx=ast.Load()),
                            args=[ast.Constant(value='base64')],
                            keywords=[]
                        ),
                        attr='b64decode',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=encoded)],
                    keywords=[]
                ),
                attr='decode',
                ctx=ast.Load()
            ),
            args=[ast.Constant(value='utf-8')],
            keywords=[]
        )


class StringObfuscationFactory:
    """
    Factory for creating string obfuscation strategies.

    Implements the Factory pattern for strategy creation.
    """

    _strategies: Dict[str, Type[StringObfuscationStrategy]] = {
        "xor": XorStrategy,
        "hex": HexStrategy,
        "base64": Base64Strategy,
    }

    @classmethod
    def create(cls, method: str) -> StringObfuscationStrategy:
        """
        Create a string obfuscation strategy.

        Args:
            method: The method to use ("xor", "hex", "base64")

        Returns:
            A StringObfuscationStrategy instance.

        Raises:
            ValueError: If the method is not recognized.
        """
        strategy_class = cls._strategies.get(method)
        if strategy_class is None:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"Unknown string method: {method}. Available: {available}")
        return strategy_class()

    @classmethod
    def register(cls, method: str, strategy_class: Type[StringObfuscationStrategy]) -> None:
        """
        Register a new string obfuscation strategy.

        Args:
            method: The name for this strategy.
            strategy_class: The strategy class to register.
        """
        cls._strategies[method] = strategy_class

    @classmethod
    def get_available_methods(cls) -> list:
        """Get list of available obfuscation methods."""
        return list(cls._strategies.keys())


class StringObfuscator(ast.NodeTransformer):
    """
    AST transformer that obfuscates string literals.

    Uses the Strategy pattern to support different obfuscation methods.
    """

    # Minimum string length to obfuscate (avoid overhead for short strings)
    MIN_STRING_LENGTH = 3

    def __init__(self, method: str = "xor"):
        """
        Initialize the string obfuscator.

        Args:
            method: The obfuscation method to use ("xor", "hex", "base64")
        """
        self.method = method
        self._strategy = StringObfuscationFactory.create(method)
        self._in_fstring = False  # Track if we're inside an f-string

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:
        """Don't modify f-strings - they have special handling requirements."""
        # Skip f-strings entirely to avoid AST issues
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Obfuscate string constants."""
        if isinstance(node.value, str) and len(node.value) >= self.MIN_STRING_LENGTH:
            return self._strategy.obfuscate(node.value)
        return node

    def transform(self, source: str) -> str:
        """
        Transform source code by obfuscating strings.

        Args:
            source: The Python source code to transform.

        Returns:
            Transformed source code with obfuscated strings.
        """
        tree = ast.parse(source)
        tree = self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

