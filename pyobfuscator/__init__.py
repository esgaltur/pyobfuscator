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
- Framework presets for modular apps (PySide6, Flask, Django, FastAPI, etc.)
- Auto-detection and configuration generation for projects
"""

from .obfuscator import Obfuscator, NameGenerator, NameObfuscator
from .runtime_protection import RuntimeProtector, protect
from .pyd_protection import PydRuntimeProtector
from .crypto import get_machine_id
from .cli import main, load_config, find_config
from .analyzer import (
    ProjectAnalyzer,
    ProjectAnalysis,
    ModuleInfo,
    analyze_project,
    generate_config as generate_project_config,
)
from .transformers import (
    apply_advanced_obfuscation,
    generate_polymorphic_anti_debug,
    generate_distributed_timing_checks,
    ControlFlowObfuscator,
    PolymorphicAntiDebugGenerator,
    DistributedTimingChecker,
)

__version__ = "1.0.2"

# Available framework presets
FRAMEWORK_PRESETS = list(NameObfuscator.FRAMEWORK_PRESETS.keys())

__all__ = [
    # Core obfuscation
    "Obfuscator",
    "NameGenerator",
    "NameObfuscator",
    "FRAMEWORK_PRESETS",
    # Project analysis
    "ProjectAnalyzer",
    "ProjectAnalysis",
    "ModuleInfo",
    "analyze_project",
    "generate_project_config",
    # Runtime protection
    "RuntimeProtector",
    "PydRuntimeProtector",
    "protect",
    "get_machine_id",
    # CLI
    "main",
    "load_config",
    "find_config",
    # Advanced transformers
    "apply_advanced_obfuscation",
    "generate_polymorphic_anti_debug",
    "generate_distributed_timing_checks",
    "ControlFlowObfuscator",
    "PolymorphicAntiDebugGenerator",
    "DistributedTimingChecker",
]
