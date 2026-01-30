# -*- coding: utf-8 -*-
"""
Utility functions for PyObfuscate.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Set, List, Optional


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


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal hash string
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_python_files(
    directory: Path,
    recursive: bool = True,
    exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Find all Python files in a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search recursively
        exclude_patterns: Glob patterns to exclude

    Returns:
        List of Python file paths
    """
    import fnmatch

    exclude_patterns = exclude_patterns or []
    pattern = '**/*.py' if recursive else '*.py'

    files = []
    for py_file in directory.glob(pattern):
        relative = py_file.relative_to(directory)

        # Check exclusions
        excluded = False
        for excl_pattern in exclude_patterns:
            if fnmatch.fnmatch(str(relative), excl_pattern):
                excluded = True
                break
            if fnmatch.fnmatch(py_file.name, excl_pattern):
                excluded = True
                break

        if not excluded:
            files.append(py_file)

    return files


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


def minify_code(source: str) -> str:
    """
    Basic minification of Python code.
    Removes extra whitespace and blank lines.

    Args:
        source: Python source code

    Returns:
        Minified source code
    """
    lines = source.split('\n')
    minified_lines = []

    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()

        # Skip completely empty lines (but keep lines with only indentation for blocks)
        if line or (minified_lines and minified_lines[-1].strip().endswith(':')):
            minified_lines.append(line)

    # Remove consecutive blank lines
    result = []
    prev_blank = False
    for line in minified_lines:
        is_blank = not line.strip()
        if not (is_blank and prev_blank):
            result.append(line)
        prev_blank = is_blank

    return '\n'.join(result)


def create_import_hook_code(module_name: str, obfuscated_code: str) -> str:
    """
    Create an import hook that loads obfuscated code.

    Args:
        module_name: Name of the module
        obfuscated_code: The obfuscated source code (base64 + compressed)

    Returns:
        Python code that sets up an import hook
    """
    return f'''# -*- coding: utf-8 -*-
"""
Protected module: {module_name}
"""
import sys
import types
import zlib
import base64

_CODE = {repr(obfuscated_code)}

def _load():
    code = zlib.decompress(base64.b64decode(_CODE)).decode('utf-8')
    module = types.ModuleType('{module_name}')
    exec(code, module.__dict__)
    return module

sys.modules['{module_name}'] = _load()
'''


def generate_license_header(
    author: str = "Protected",
    year: Optional[str] = None
) -> str:
    """
    Generate a license/protection header for obfuscated code.

    Args:
        author: Author name
        year: Copyright year

    Returns:
        Header string
    """
    import datetime
    year = year or str(datetime.datetime.now().year)

    return f'''# -*- coding: utf-8 -*-
# Protected by PyObfuscate
# Copyright (c) {year} {author}
# Unauthorized copying or distribution is prohibited.

'''
