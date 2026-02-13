# -*- coding: utf-8 -*-
"""
Utils module for PyObfuscator.

Contains utility functions for file operations, AST manipulation, and more.
"""

# Re-export from submodules for convenience
from .file_utils import (
    calculate_file_hash,
    find_python_files,
    read_source_file,
    write_source_file,
    is_python_file,
    create_backup,
)

from .ast_utils import (
    extract_public_api,
    is_valid_python,
    parse_source,
    unparse_ast,
    get_defined_names,
    get_imported_names,
    has_docstring,
    remove_docstring,
    count_nodes,
)

__all__ = [
    # File utilities
    "calculate_file_hash",
    "find_python_files",
    "read_source_file",
    "write_source_file",
    "is_python_file",
    "create_backup",
    # AST utilities
    "extract_public_api",
    "is_valid_python",
    "parse_source",
    "unparse_ast",
    "get_defined_names",
    "get_imported_names",
    "has_docstring",
    "remove_docstring",
    "count_nodes",
]


