# -*- coding: utf-8 -*-
"""
Configuration module for PyObfuscator.

Provides configuration classes and builder pattern implementations.
"""

from .builder import ObfuscatorConfig, ObfuscatorBuilder
from .presets import ConfigPresets, get_preset

__all__ = [
    "ObfuscatorConfig",
    "ObfuscatorBuilder",
    "ConfigPresets",
    "get_preset",
]

