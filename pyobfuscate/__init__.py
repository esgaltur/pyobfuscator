"""
PyObfuscate - A Python code obfuscation library

A lightweight, license-free Python obfuscation tool that provides
multiple obfuscation techniques to protect your Python source code.
"""

from .obfuscator import Obfuscator
from .runtime_protection import RuntimeProtector, protect
from .pyd_protection import PydRuntimeProtector
from .cli import main

__version__ = "1.0.0"
__all__ = ["Obfuscator", "RuntimeProtector", "PydRuntimeProtector", "protect", "main"]
