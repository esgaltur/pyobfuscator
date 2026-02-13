# -*- coding: utf-8 -*-
"""
Core module for PyObfuscator.

Contains the main obfuscation components and transformers.
"""

from .name_generator import NameGenerator, NameGeneratorFactory
from .transformers import (
    StringObfuscator,
    XorStrategy,
    HexStrategy,
    Base64Strategy,
    StringObfuscationFactory,
)
from .transformers.string_obfuscator import StringObfuscationStrategy

__all__ = [
    "NameGenerator",
    "NameGeneratorFactory",
    "StringObfuscationStrategy",
    "XorStrategy",
    "HexStrategy",
    "Base64Strategy",
    "StringObfuscationFactory",
    "StringObfuscator",
]

