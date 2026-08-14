# -*- coding: utf-8 -*-
"""
Skjol - A Python code protection library

Advanced, production-grade Python obfuscation tool.
"""

from ._version import __version__
from .obfuscator import Obfuscator
from .core.transformers.name_transformer import NameGenerator
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
    PolymorphicAntiDebugGenerator,
    DistributedTimingChecker,
    ControlFlowObfuscator,
    ControlFlowFlattener,
    NumberObfuscator,
    BuiltinObfuscator,
    IntegrityTransformer,
)

# Core and Infrastructure
from .core.registry import TransformerRegistry

from .core.pipeline import TransformationPipeline

# Constants
from .constants import (
    RuntimeConstants,
    CryptoConstants,
    ObfuscatorConstants,
    ReservedNames,
    FrameworkPresets,
)

# Exceptions
from .exceptions import (
    PyObfuscatorError,
    SkjolError,
    SourceCodeError,
    EmptySourceError,
    InvalidSyntaxError,
    ObfuscationError,
    TransformationError,
    CryptoError,
    EncryptionError,
    DecryptionError,
    ProtectionError,
    ConfigError,
    InvalidConfigError,
)

# Configuration
from .config import (
    ObfuscatorConfig,
    ObfuscatorBuilder,
    ConfigPresets,
    get_preset,
)

__all__ = [
    "__version__",
    "Obfuscator",
    "NameGenerator",
    "TransformerRegistry",
    "TransformationPipeline",
    "ProjectAnalyzer",
    "ProjectAnalysis",
    "ModuleInfo",
    "analyze_project",
    "generate_project_config",
    "RuntimeProtector",
    "PydRuntimeProtector",
    "protect",
    "get_machine_id",
    "main",
    "load_config",
    "find_config",
    "apply_advanced_obfuscation",
    "generate_polymorphic_anti_debug",
    "generate_distributed_timing_checks",
    "PolymorphicAntiDebugGenerator",
    "DistributedTimingChecker",
    "ControlFlowObfuscator",
    "ControlFlowFlattener",
    "NumberObfuscator",
    "BuiltinObfuscator",
    "IntegrityTransformer",
    "PyObfuscatorError",
    "SkjolError",
    "SourceCodeError",
    "EmptySourceError",
    "InvalidSyntaxError",
    "ObfuscationError",
    "TransformationError",
    "CryptoError",
    "EncryptionError",
    "DecryptionError",
    "ProtectionError",
    "ConfigError",
    "InvalidConfigError",
    "RuntimeConstants",
    "CryptoConstants",
    "ObfuscatorConstants",
    "ReservedNames",
    "FrameworkPresets",
    "ObfuscatorConfig",
    "ObfuscatorBuilder",
    "ConfigPresets",
    "get_preset",
]
