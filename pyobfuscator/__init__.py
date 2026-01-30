# -*- coding: utf-8 -*-
"""
PyObfuscator - A Python code obfuscation library

A lightweight, license-free Python obfuscation tool that provides
multiple obfuscation techniques to protect your Python source code.

Features:
- Single file and multi-file (cross-file) obfuscation
- Method and class attribute renaming
- Polymorphic anti-debug code generation
- Distributed timing checks
- AES-256-GCM encryption with runtime protection
"""

from .obfuscator import Obfuscator, NameGenerator
from .runtime_protection import RuntimeProtector, protect
from .pyd_protection import PydRuntimeProtector
from .crypto import get_machine_id
from .cli import main
from .transformers import (
    apply_advanced_obfuscation,
    generate_polymorphic_anti_debug,
    generate_distributed_timing_checks,
    ControlFlowObfuscator,
    PolymorphicAntiDebugGenerator,
    DistributedTimingChecker,
)

__version__ = "1.0.0"
__all__ = [
    # Core obfuscation
    "Obfuscator",
    "NameGenerator",
    # Runtime protection
    "RuntimeProtector",
    "PydRuntimeProtector",
    "protect",
    "get_machine_id",
    # CLI
    "main",
    # Advanced transformers
    "apply_advanced_obfuscation",
    "generate_polymorphic_anti_debug",
    "generate_distributed_timing_checks",
    "ControlFlowObfuscator",
    "PolymorphicAntiDebugGenerator",
    "DistributedTimingChecker",
]
