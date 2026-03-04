# -*- coding: utf-8 -*-
"""
Transformers module for PyObfuscator.

Contains AST transformers and obfuscation strategies.
"""

from .base import BaseTransformer
from .code_cleaner import DocstringRemover, CodeCompressor
from .control_flow import ControlFlowObfuscator, ControlFlowFlattener, PolymorphicAntiDebugGenerator, DistributedTimingChecker
from .virtual_machine import VirtualMachineTransformer
from .integrity import IntegrityTransformer
from .literal_obfuscator import NumberObfuscator, BuiltinObfuscator
from .name_transformer import NameGenerator, NameTransformer, DefinitionCollector
from .string_obfuscator import (
    StringObfuscationStrategy,
    XorStrategy,
    HexStrategy,
    Base64Strategy,
    StringObfuscationFactory,
    StringObfuscator,
)

__all__ = [
    "BaseTransformer",
    "DocstringRemover",
    "CodeCompressor",
    "ControlFlowObfuscator",
    "ControlFlowFlattener",
    "PolymorphicAntiDebugGenerator",
    "DistributedTimingChecker",
    "IntegrityTransformer",
    "NumberObfuscator",
    "BuiltinObfuscator",
    "NameGenerator",
    "NameTransformer",
    "DefinitionCollector",
    "StringObfuscationStrategy",
    "XorStrategy",
    "HexStrategy",
    "Base64Strategy",
    "StringObfuscationFactory",
    "StringObfuscator",
]
