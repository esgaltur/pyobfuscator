# -*- coding: utf-8 -*-
"""
Transformation pipeline for PyObfuscator.

Provides a structured way to chain multiple transformations.
"""

from typing import List, Optional, Dict, Any
import logging
from .transformers.base import BaseTransformer
from .context import TransformationContext

logger = logging.getLogger(__name__)


class TransformationPipeline:
    """
    Executes a sequence of transformers on source code.

    Enables chaining multiple obfuscation steps in a configurable order.
    """

    def __init__(self, transformers: Optional[List[BaseTransformer]] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the pipeline.

        Args:
            transformers: Optional list of transformer instances to include.
            config: Optional configuration dictionary.
        """
        self.transformers: List[BaseTransformer] = transformers or []
        self.context = TransformationContext(config)

    def add_transformer(self, transformer: BaseTransformer) -> 'TransformationPipeline':
        """
        Add a transformer to the end of the pipeline.

        Args:
            transformer: The transformer instance to add.

        Returns:
            The pipeline instance for chaining.
        """
        self.transformers.append(transformer)
        return self

    def execute(self, source: str) -> str:
        """
        Execute all transformers in the pipeline on the given source code.

        Args:
            source: The Python source code to transform.

        Returns:
            The fully transformed source code.
        """
        current_source = source

        for transformer in self.transformers:
            try:
                logger.debug(f"Executing transformer: {transformer.__class__.__name__}")
                current_source = transformer.transform(current_source, context=self.context)
            except Exception as e:
                logger.error(f"Transformation failed in {transformer.__class__.__name__}: {e}")
                raise

        return current_source

    def __len__(self) -> int:
        return len(self.transformers)

