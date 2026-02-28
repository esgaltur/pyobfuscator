# -*- coding: utf-8 -*-
"""
Virtual File System adapter for testing.
Allows testing directory obfuscation without disk I/O.
"""

from pathlib import Path
from typing import Dict, Iterable, Optional
import fnmatch


class VirtualFileSystem:
    """
    In-memory implementation of FileSystemProvider.
    """

    def __init__(self, initial_files: Optional[Dict[str, str]] = None):
        self.files: Dict[str, str] = initial_files or {}

    def read_text(self, path: Path) -> str:
        p_str = str(path).replace('\\', '/')
        if p_str not in self.files:
            raise FileNotFoundError(f"Virtual file not found: {p_str}")
        return self.files[p_str]

    def write_text(self, path: Path, content: str) -> None:
        p_str = str(path).replace('\\', '/')
        self.files[p_str] = content

    def exists(self, path: Path) -> bool:
        p_str = str(path).replace('\\', '/')
        return p_str in self.files

    def is_dir(self, path: Path) -> bool:
        p_str = str(path).replace('\\', '/')
        # Simple heuristic: if it's a prefix of any file, it's a dir
        return any(f.startswith(p_str + '/') for f in self.files)

    def mkdir(self, path: Path) -> None:
        pass # Virtual dirs are implicit

    def glob(self, path: Path, pattern: str) -> Iterable[Path]:
        p_str = str(path).replace('\\', '/')
        # Convert glob to regex-like match
        # This is a simplified glob for testing
        search_prefix = p_str if p_str.endswith('/') else p_str + '/'
        if p_str == '.': search_prefix = ''
        
        for f_path in self.files:
            if f_path.startswith(search_prefix):
                rel = f_path[len(search_prefix):]
                if fnmatch.fnmatch(rel, pattern.replace('**/', '')):
                    yield Path(f_path)

