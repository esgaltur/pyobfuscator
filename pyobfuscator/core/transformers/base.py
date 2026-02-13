# -*- coding: utf-8 -*-
"""
Base transformer classes for PyObfuscator.

Provides abstract base classes for AST transformers.
"""

import ast
from abc import ABC, abstractmethod
from typing import Optional


class BaseTransformer(ABC, ast.NodeTransformer):
    """
    Abstract base class for AST transformers.

    Provides common functionality for all transformers.
    """

    @abstractmethod
    def transform(self, source: str) -> str:
        """
        Transform Python source code.

        Args:
            source: The Python source code to transform.

        Returns:
            Transformed Python source code.
        """
        ...

    def _parse_source(self, source: str) -> ast.AST:
        """
        Parse source code into an AST.

        Args:
            source: The Python source code to parse.

        Returns:
            The parsed AST.

        Raises:
            ValueError: If the source code contains syntax errors.
        """
        try:
            return ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Failed to parse source code: {e}")

    def _unparse_tree(self, tree: ast.AST) -> str:
        """
        Convert an AST back to source code.

        Args:
            tree: The AST to convert.

        Returns:
            Python source code.

        Raises:
            ValueError: If code generation fails.
        """
        try:
            ast.fix_missing_locations(tree)
            return ast.unparse(tree)
        except Exception as e:
            raise ValueError(f"Failed to generate code: {e}")

