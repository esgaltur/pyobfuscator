# -*- coding: utf-8 -*-
"""
File processor infrastructure for PyObfuscator.

Handles file system operations, globbing, and reading/writing source files.
"""

import os
import fnmatch
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Iterable, Callable
import logging

logger = logging.getLogger(__name__)


class LocalFileSystem:
    """
    Standard implementation of FileSystemProvider using the local disk.
    """
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding='utf-8')

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        return path.is_dir()

    def mkdir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def glob(self, path: Path, pattern: str) -> Iterable[Path]:
        return path.glob(pattern)


class FileProcessor:
    """
    Adapter for file system operations.
    """

    def __init__(self, fs: Optional[LocalFileSystem] = None):
        self.fs = fs or LocalFileSystem()

    def collect_python_files(
        self,
        input_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[Tuple[Path, Path]]:
        """
        Collect Python files to process.
        """
        input_dir = Path(input_dir)
        pattern = '**/*.py' if recursive else '*.py'
        exclude_patterns = exclude_patterns or []

        py_files = []
        for py_file in self.fs.glob(input_dir, pattern):
            relative_path = py_file.relative_to(input_dir)
            
            should_exclude = False
            for p in exclude_patterns:
                if fnmatch.fnmatch(str(relative_path), p) or fnmatch.fnmatch(py_file.name, p):
                    should_exclude = True
                    break
            
            if not should_exclude:
                py_files.append((py_file, relative_path))
        
        return py_files

    def read_file(self, path: Path) -> str:
        return self.fs.read_text(path)

    def write_file(self, path: Path, content: str) -> None:
        self.fs.write_text(path, content)

