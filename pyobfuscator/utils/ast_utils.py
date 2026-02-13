# -*- coding: utf-8 -*-
"""
AST utility functions for PyObfuscator.

Contains functions for AST manipulation and source code analysis.
"""

import ast
import re
from typing import Set


def extract_public_api(source: str) -> Set[str]:
    """
    Extract public API names from Python source code.
    These names should typically not be obfuscated.

    Args:
        source: Python source code

    Returns:
        Set of public API names
    """
    public_names = set()

    # Find __all__ definition
    all_match = re.search(r'__all__\s*=\s*\[([^\]]+)\]', source)
    if all_match:
        names = re.findall(r'["\'](\w+)["\']', all_match.group(1))
        public_names.update(names)

    # Find decorated functions/classes (likely public API)
    decorator_patterns = [
        r'@property\s+def\s+(\w+)',
        r'@staticmethod\s+def\s+(\w+)',
        r'@classmethod\s+def\s+(\w+)',
        r'@abstractmethod\s+def\s+(\w+)',
    ]

    for pattern in decorator_patterns:
        matches = re.findall(pattern, source)
        public_names.update(matches)

    return public_names


def is_valid_python(source: str) -> bool:
    """
    Check if a string is valid Python source code.

    Args:
        source: Python source code string

    Returns:
        True if valid, False otherwise
    """
    try:
        compile(source, '<string>', 'exec')
        return True
    except SyntaxError:
        return False


def parse_source(source: str, filename: str = '<unknown>') -> ast.AST:
    """
    Parse Python source code into an AST.

    Args:
        source: Python source code
        filename: Filename for error messages

    Returns:
        The parsed AST

    Raises:
        SyntaxError: If source code is invalid
    """
    return ast.parse(source, filename=filename)


def unparse_ast(tree: ast.AST) -> str:
    """
    Convert an AST back to Python source code.

    Args:
        tree: The AST to convert

    Returns:
        Python source code
    """
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def get_defined_names(tree: ast.AST) -> Set[str]:
    """
    Get all names defined in an AST (functions, classes, variables).

    Args:
        tree: The AST to analyze

    Returns:
        Set of defined names
    """
    names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)

    return names


def get_imported_names(tree: ast.AST) -> Set[str]:
    """
    Get all names imported in an AST.

    Args:
        tree: The AST to analyze

    Returns:
        Set of imported names
    """
    names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split('.')[0]
                names.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != '*':
                    name = alias.asname if alias.asname else alias.name
                    names.add(name)

    return names


def has_docstring(node: ast.AST) -> bool:
    """
    Check if a node has a docstring.

    Args:
        node: AST node (Module, FunctionDef, ClassDef)

    Returns:
        True if node has a docstring
    """
    if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False

    if not node.body:
        return False

    first_stmt = node.body[0]
    if isinstance(first_stmt, ast.Expr):
        if isinstance(first_stmt.value, ast.Constant):
            return isinstance(first_stmt.value.value, str)

    return False


def remove_docstring(node: ast.AST) -> None:
    """
    Remove docstring from a node in-place.

    Args:
        node: AST node to modify
    """
    if has_docstring(node):
        node.body = node.body[1:] or [ast.Pass()]


def count_nodes(tree: ast.AST) -> int:
    """
    Count total number of nodes in an AST.

    Args:
        tree: The AST to count

    Returns:
        Number of nodes
    """
    return sum(1 for _ in ast.walk(tree))

