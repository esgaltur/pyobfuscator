# -*- coding: utf-8 -*-
"""
PyObfuscator - Advanced Python Code Protection Orchestrator.

Implements the Application Service in a Hexagonal Architecture.
Uses a Transformation Pipeline to apply multiple obfuscation steps.
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Core Domain
from .core.registry import TransformerRegistry
from .core.pipeline import TransformationPipeline
from .core.transformers.name_transformer import NameGenerator, NameTransformer, DefinitionCollector
from .core.transformers.string_obfuscator import StringObfuscator
from .core.transformers.control_flow import ControlFlowObfuscator, ControlFlowFlattener
from .core.transformers.literal_obfuscator import NumberObfuscator, BuiltinObfuscator
from .core.transformers.code_cleaner import DocstringRemover, CodeCompressor
from .core.transformers.integrity import IntegrityTransformer

# Infrastructure
from .infrastructure.file_processor import FileProcessor
from .runtime_protection import RuntimeProtector
from .pyd_protection import PydRuntimeProtector
from .constants import DEFAULT_EXCLUDE_PATTERNS, ReservedNames, FrameworkPresets

logger = logging.getLogger(__name__)


class Obfuscator:
    """
    Main orchestrator for code obfuscation and protection.

    Acts as an Application Service that coordinates the domain logic
    (Transformers, Pipeline) and infrastructure (FileProcessor).
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        # Dependency Injection
        name_generator: Optional[NameGenerator] = None,
        file_processor: Optional[FileProcessor] = None,
        **kwargs
    ):
        """
        Initialize the obfuscator with a configuration dictionary.
        """
        # Set default configuration
        self.config = {
            'encrypt_code': True,
            'use_pyd_compilation': False,
            'anti_debug': True,
            'rename_variables': True,
            'rename_functions': True,
            'rename_classes': True,
            'rename_methods': True,
            'rename_attributes': True,
            'obfuscate_strings': True,
            'compress_code': False,
            'remove_docstrings': True,
            'control_flow': False,
            'control_flow_flatten': False,
            'number_obfuscation': False,
            'builtin_obfuscation': False,
            'integrity_checks': False,
            'name_style': 'random',
            'string_method': 'polymorphic',
            'intensity': 1,
            'exclude_names': set(),
            'frameworks': None,
        }
        
        # Override defaults with provided config or kwargs
        if config:
            self.config.update(config)
        self.config.update(kwargs)

        # Initialize core components
        self.name_generator = name_generator or NameGenerator(style=self.config.get('name_style', 'random'))
        self.file_processor = file_processor or FileProcessor()
        
        # Build exclude names
        self.exclude_names = set(self.config.get('exclude_names') or set())
        frameworks = self.config.get('frameworks')
        if frameworks:
            self.exclude_names.update(FrameworkPresets.get_framework_excludes(frameworks))
        
        # Runtime protection
        self.runtime_protector = self._init_runtime_protector()

    def _init_runtime_protector(self) -> Optional[Any]:
        """Helper to initialize the appropriate runtime protector."""
        if self.config.get('use_pyd_compilation'):
            return PydRuntimeProtector(
                anti_debug=self.config.get('anti_debug', True),
                **self.config
            )
        if self.config.get('encrypt_code'):
            return RuntimeProtector(
                anti_debug=self.config.get('anti_debug', True),
                **self.config
            )
        return None

    def _build_pipeline(self) -> TransformationPipeline:
        """
        Dynamically construct the transformation pipeline based on config.
        """
        # Pass the global configuration into the context
        pipeline = TransformationPipeline(config=self.config)

        if self.config.get('remove_docstrings'):
            pipeline.add_transformer(TransformerRegistry.create("docstring_remover"))

        if self.config.get('rename_variables') or self.config.get('rename_functions'):
            pipeline.add_transformer(TransformerRegistry.create(
                "name_obfuscator",
                name_generator=self.name_generator,
                exclude_names=self.exclude_names,
                rename_methods=self.config.get('rename_methods'),
                rename_attributes=self.config.get('rename_attributes')
            ))

        if self.config.get('obfuscate_strings'):
            pipeline.add_transformer(TransformerRegistry.create(
                "string_obfuscator", 
                method=self.config.get('string_method')
            ))

        if self.config.get('control_flow'):
            pipeline.add_transformer(TransformerRegistry.create(
                "control_flow_obfuscator", 
                intensity=self.config.get('intensity')
            ))

        if self.config.get('control_flow_flatten'):
            pipeline.add_transformer(TransformerRegistry.create(
                "control_flow_flattener", 
                intensity=self.config.get('intensity')
            ))

        if self.config.get('number_obfuscation'):
            pipeline.add_transformer(TransformerRegistry.create(
                "number_obfuscator", 
                intensity=self.config.get('intensity')
            ))

        if self.config.get('builtin_obfuscation'):
            pipeline.add_transformer(TransformerRegistry.create("builtin_obfuscator"))

        if self.config.get('integrity_checks'):
            pipeline.add_transformer(TransformerRegistry.create(
                "integrity_transformer",
                intensity=self.config.get('intensity'),
                enable_honeypots=True
            ))

        if self.config.get('compress_code') and not self.config.get('encrypt_code') and not self.config.get('use_pyd_compilation'):
            pipeline.add_transformer(TransformerRegistry.create("code_compressor"))

        return pipeline

    @property
    def rename_variables(self) -> bool:
        return self.config.get('rename_variables', True)

    @property
    def rename_functions(self) -> bool:
        return self.config.get('rename_functions', True)

    @property
    def rename_classes(self) -> bool:
        return self.config.get('rename_classes', True)

    @property
    def string_method(self) -> str:
        return self.config.get('string_method', 'polymorphic')

    def get_obfuscated_name(self, original_name: str) -> str:
        """Get the obfuscated version of a name."""
        return self.name_generator.get_name(original_name)

    def export_name_mapping(self) -> Dict[str, str]:
        """Export the current name mapping."""
        return self.name_generator.export_mapping()

    def import_name_mapping(self, mapping: Dict[str, str]) -> None:
        """Import a previously exported name mapping."""
        self.name_generator.import_mapping(mapping)

    def obfuscate_source(self, source: str) -> str:
        """
        Obfuscate Python source code using the pipeline.
        """
        pipeline = self._build_pipeline()
        return pipeline.execute(source)

    def obfuscate_file(self, input_path: Path, output_path: Optional[Path] = None) -> str:
        """
        Obfuscate a single Python file.
        """
        source = self.file_processor.read_file(input_path)
        obfuscated = self.obfuscate_source(source)
        
        if output_path:
            self.file_processor.write_file(output_path, obfuscated)
            
        return obfuscated

    def obfuscate_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Obfuscate an entire directory using a two-phase approach for cross-file consistency.
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        exclude_patterns = (exclude_patterns or []) + DEFAULT_EXCLUDE_PATTERNS

        py_files = self.file_processor.collect_python_files(input_dir, recursive, exclude_patterns)

        # PHASE 1: Collection
        for py_file, _ in py_files:
            try:
                source = self.file_processor.read_file(py_file)
                tree = ast.parse(source)
                collector = DefinitionCollector(self.name_generator, self.exclude_names)
                collector.visit(tree)
            except Exception as e:
                logger.warning(f"Phase 1 failed for {py_file}: {e}")

        # PHASE 2: Transformation
        results = {}
        for py_file, relative_path in py_files:
            target_path = output_dir / relative_path
            try:
                self.obfuscate_file(py_file, target_path)
                results[str(relative_path)] = "success"
            except Exception as e:
                results[str(relative_path)] = f"failed: {e}"
                logger.error(f"Phase 2 failed for {py_file}: {e}")

        return results

    def protect_source(self, source: str, filename: str = "<protected>") -> Tuple[str, str]:
        """
        Full protection: Obfuscation + Encryption.
        """
        if not self.runtime_protector:
            raise ValueError("Encryption is not enabled. Set encrypt_code=True")

        obfuscated = self.obfuscate_source(source)
        return self.runtime_protector.protect_source(obfuscated, filename)

