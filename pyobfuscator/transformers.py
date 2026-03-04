# -*- coding: utf-8 -*-
"""
Compatibility layer for advanced transformers.
Delegates to the new core transformation engine.
"""

import ast
from typing import List, Optional

from .core.registry import TransformerRegistry
from .core.pipeline import TransformationPipeline

# Import the actual implementations for backward compatibility of class names
from .core.transformers.control_flow import ControlFlowObfuscator, ControlFlowFlattener
from .core.transformers.literal_obfuscator import NumberObfuscator, BuiltinObfuscator
from .core.transformers.integrity import IntegrityTransformer

def apply_advanced_obfuscation(
    tree: ast.AST,
    control_flow: bool = False,
    number_obfuscation: bool = False,
    builtin_obfuscation: bool = False,
    control_flow_flatten: bool = False,
    integrity_check: bool = False,
    intensity: int = 1
) -> ast.AST:
    """
    Legacy helper function for advanced obfuscation.
    """
    source = ast.unparse(tree)
    pipeline = TransformationPipeline()
    
    if control_flow:
        pipeline.add_transformer(TransformerRegistry.create("control_flow_obfuscator", intensity=intensity))
    if control_flow_flatten:
        pipeline.add_transformer(TransformerRegistry.create("control_flow_flattener", intensity=intensity))
    if number_obfuscation:
        pipeline.add_transformer(TransformerRegistry.create("number_obfuscator", intensity=intensity))
    if builtin_obfuscation:
        pipeline.add_transformer(TransformerRegistry.create("builtin_obfuscator"))
    if integrity_check:
        pipeline.add_transformer(TransformerRegistry.create("integrity_transformer", intensity=intensity))
    
    obfuscated = pipeline.execute(source)
    return ast.parse(obfuscated)


# Re-export other legacy generators
from .core.transformers.control_flow import (
    generate_polymorphic_anti_debug,
    generate_distributed_timing_checks,
    PolymorphicAntiDebugGenerator,
    DistributedTimingChecker
)
