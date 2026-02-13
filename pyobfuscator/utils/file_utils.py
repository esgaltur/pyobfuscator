# -*- coding: utf-8 -*-
"""
File utility functions for PyObfuscator.

Contains functions for file operations, hashing, and finding Python files.
"""

import hashlib
import fnmatch
from pathlib import Path
from typing import List, Optional


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


def read_source_file(file_path: Path, encoding: str = 'utf-8') -> str:
    """
    Read a Python source file.

    Args:
        file_path: Path to the file
        encoding: File encoding

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file can't be decoded
    """
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()


def write_source_file(
    file_path: Path,
    content: str,
    encoding: str = 'utf-8',
    create_parents: bool = True
) -> None:
    """
    Write content to a Python source file.

    Args:
        file_path: Path to the file
        content: Content to write
        encoding: File encoding
        create_parents: Whether to create parent directories
    """
    if create_parents:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)


def is_python_file(file_path: Path) -> bool:
    """
    Check if a file is a Python source file.

    Args:
        file_path: Path to check

    Returns:
        True if file has .py extension
    """
    return file_path.suffix.lower() == '.py'


def create_backup(file_path: Path, suffix: str = '.bak') -> Path:
    """
    Create a backup copy of a file.

    Args:
        file_path: Path to the file to backup
        suffix: Suffix for backup file

    Returns:
        Path to the backup file
    """
    import shutil
    backup_path = file_path.with_suffix(file_path.suffix + suffix)
    shutil.copy2(file_path, backup_path)
    return backup_path

