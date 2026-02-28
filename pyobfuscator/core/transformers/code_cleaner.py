# -*- coding: utf-8 -*-
"""
Code cleaning and compression for PyObfuscator.

Provides techniques for removing metadata and compressing source code.
"""

import ast
import zlib
import base64
from typing import Optional
from .base import BaseTransformer
from ..registry import TransformerRegistry


@TransformerRegistry.register("docstring_remover")
class DocstringRemover(BaseTransformer):
    """
    Removes docstrings from the AST.
    """

    def __init__(self, **kwargs):
        """Constructor for DocstringRemover. No specific initialization required."""
        super().__init__()

    def visit_Module(self, node: ast.Module) -> ast.Module:
        return self._handle_doc(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        return self._handle_doc(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self._handle_doc(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        return self._handle_doc(node)

    def _handle_doc(self, node: ast.AST) -> ast.AST:
        """Shared logic for removing docstrings from various node types."""
        self._remove_doc(node)
        self.generic_visit(node)
        return node

    def _remove_doc(self, node: ast.AST) -> None:
        if (hasattr(node, 'body') and node.body and 
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            node.body.pop(0)

    def transform(self, source: str, context: Optional['TransformationContext'] = None) -> str:
        tree = self._parse_source(source)
        tree = self.visit(tree)
        return self._unparse_tree(tree)


@TransformerRegistry.register("code_compressor")
class CodeCompressor(BaseTransformer):
    """
    Compresses code using zlib and base64.
    """

    def __init__(self, **kwargs):
        """Constructor for CodeCompressor. No specific initialization required."""
        super().__init__()

    def transform(self, source: str, context: Optional['TransformationContext'] = None) -> str:
        compressed = zlib.compress(source.encode('utf-8'), level=9)
        encoded = base64.b64encode(compressed).decode('ascii')
        
        return f'''# -*- coding: utf-8 -*-
import zlib as _z
import base64 as _b
exec(_z.decompress(_b.b64decode({repr(encoded)})).decode('utf-8'))
'''

