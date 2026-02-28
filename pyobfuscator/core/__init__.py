# -*- coding: utf-8 -*-
"""
Core module for PyObfuscator.

Contains the main obfuscation components and transformers.
"""

from .registry import TransformerRegistry
from .pipeline import TransformationPipeline

__all__ = [
    "TransformerRegistry",
    "TransformationPipeline",
]
