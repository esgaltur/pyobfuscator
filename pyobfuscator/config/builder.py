# -*- coding: utf-8 -*-
"""
Configuration builder for PyObfuscator.

Implements the Builder pattern for constructing Obfuscator configurations.
This provides a fluent API for setting up obfuscation options.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, List


@dataclass
class ObfuscatorConfig:
    """
    Configuration object for the Obfuscator.

    This immutable configuration holds all settings needed to create
    an Obfuscator instance.
    """

    # Renaming options
    rename_variables: bool = True
    rename_functions: bool = True
    rename_classes: bool = True
    rename_methods: bool = True
    rename_attributes: bool = True

    # String obfuscation
    obfuscate_strings: bool = True
    string_method: str = "xor"

    # Code transformation
    compress_code: bool = False
    remove_comments: bool = True
    remove_docstrings: bool = True

    # Name generation
    name_style: str = "random"
    name_prefix: str = "_"

    # Exclusions
    exclude_names: Set[str] = field(default_factory=set)
    frameworks: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)

    # Public API preservation
    preserve_public_api: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        valid_string_methods = {"xor", "hex", "base64"}
        if self.string_method not in valid_string_methods:
            raise ValueError(
                f"Invalid string_method: {self.string_method}. "
                f"Must be one of: {valid_string_methods}"
            )

        valid_name_styles = {"random", "hex", "hash"}
        if self.name_style not in valid_name_styles:
            raise ValueError(
                f"Invalid name_style: {self.name_style}. "
                f"Must be one of: {valid_name_styles}"
            )


class ObfuscatorBuilder:
    """
    Builder for creating ObfuscatorConfig instances.

    Provides a fluent interface for constructing configurations
    step by step.

    Example:
        config = (
            ObfuscatorBuilder()
            .with_variable_renaming(True)
            .with_string_obfuscation("xor")
            .exclude_names({"main", "app"})
            .for_framework("pyside6")
            .build()
        )
    """

    def __init__(self):
        """Initialize the builder with default values."""
        self._rename_variables = True
        self._rename_functions = True
        self._rename_classes = True
        self._rename_methods = True
        self._rename_attributes = True
        self._obfuscate_strings = True
        self._string_method = "xor"
        self._compress_code = False
        self._remove_comments = True
        self._remove_docstrings = True
        self._name_style = "random"
        self._name_prefix = "_"
        self._exclude_names: Set[str] = set()
        self._frameworks: List[str] = []
        self._entry_points: List[str] = []
        self._preserve_public_api = False

    def with_variable_renaming(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable variable renaming."""
        self._rename_variables = enabled
        return self

    def with_function_renaming(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable function renaming."""
        self._rename_functions = enabled
        return self

    def with_class_renaming(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable class renaming."""
        self._rename_classes = enabled
        return self

    def with_method_renaming(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable method renaming."""
        self._rename_methods = enabled
        return self

    def with_attribute_renaming(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable attribute renaming."""
        self._rename_attributes = enabled
        return self

    def with_all_renaming(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable all renaming options."""
        self._rename_variables = enabled
        self._rename_functions = enabled
        self._rename_classes = enabled
        self._rename_methods = enabled
        self._rename_attributes = enabled
        return self

    def with_string_obfuscation(self, method: Optional[str] = "xor") -> "ObfuscatorBuilder":
        """
        Enable string obfuscation with the specified method.

        Args:
            method: Obfuscation method ("xor", "hex", "base64", or None to disable)
        """
        if method is None:
            self._obfuscate_strings = False
        else:
            self._obfuscate_strings = True
            self._string_method = method
        return self

    def with_compression(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable code compression."""
        self._compress_code = enabled
        return self

    def with_comment_removal(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable comment removal."""
        self._remove_comments = enabled
        return self

    def with_docstring_removal(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable docstring removal."""
        self._remove_docstrings = enabled
        return self

    def with_name_style(self, style: str) -> "ObfuscatorBuilder":
        """
        Set the name generation style.

        Args:
            style: One of "random", "hex", or "hash"
        """
        self._name_style = style
        return self

    def with_name_prefix(self, prefix: str) -> "ObfuscatorBuilder":
        """Set the prefix for generated names."""
        self._name_prefix = prefix
        return self

    def exclude_names(self, names: Set[str]) -> "ObfuscatorBuilder":
        """Add names to exclude from obfuscation."""
        self._exclude_names.update(names)
        return self

    def exclude_name(self, name: str) -> "ObfuscatorBuilder":
        """Add a single name to exclude from obfuscation."""
        self._exclude_names.add(name)
        return self

    def for_framework(self, framework: str) -> "ObfuscatorBuilder":
        """
        Add a framework preset.

        This preserves framework-specific names from obfuscation.

        Args:
            framework: Framework name (e.g., "pyside6", "flask", "django")
        """
        if framework not in self._frameworks:
            self._frameworks.append(framework)
        return self

    def for_frameworks(self, frameworks: List[str]) -> "ObfuscatorBuilder":
        """Add multiple framework presets."""
        for framework in frameworks:
            self.for_framework(framework)
        return self

    def with_entry_points(self, entry_points: List[str]) -> "ObfuscatorBuilder":
        """
        Set entry points that should never be renamed.

        Args:
            entry_points: List of function/class names (e.g., ["main", "App"])
        """
        self._entry_points.extend(entry_points)
        return self

    def with_entry_point(self, entry_point: str) -> "ObfuscatorBuilder":
        """Add a single entry point."""
        self._entry_points.append(entry_point)
        return self

    def preserve_public_api(self, enabled: bool = True) -> "ObfuscatorBuilder":
        """Enable or disable public API preservation."""
        self._preserve_public_api = enabled
        return self

    def from_config(self, config: ObfuscatorConfig) -> "ObfuscatorBuilder":
        """Initialize the builder from an existing config."""
        self._rename_variables = config.rename_variables
        self._rename_functions = config.rename_functions
        self._rename_classes = config.rename_classes
        self._rename_methods = config.rename_methods
        self._rename_attributes = config.rename_attributes
        self._obfuscate_strings = config.obfuscate_strings
        self._string_method = config.string_method
        self._compress_code = config.compress_code
        self._remove_comments = config.remove_comments
        self._remove_docstrings = config.remove_docstrings
        self._name_style = config.name_style
        self._name_prefix = config.name_prefix
        self._exclude_names = set(config.exclude_names)
        self._frameworks = list(config.frameworks)
        self._entry_points = list(config.entry_points)
        self._preserve_public_api = config.preserve_public_api
        return self

    def build(self) -> ObfuscatorConfig:
        """
        Build and return the configuration object.

        Returns:
            A configured ObfuscatorConfig instance.

        Raises:
            ValueError: If configuration is invalid.
        """
        return ObfuscatorConfig(
            rename_variables=self._rename_variables,
            rename_functions=self._rename_functions,
            rename_classes=self._rename_classes,
            rename_methods=self._rename_methods,
            rename_attributes=self._rename_attributes,
            obfuscate_strings=self._obfuscate_strings,
            string_method=self._string_method,
            compress_code=self._compress_code,
            remove_comments=self._remove_comments,
            remove_docstrings=self._remove_docstrings,
            name_style=self._name_style,
            name_prefix=self._name_prefix,
            exclude_names=self._exclude_names,
            frameworks=self._frameworks,
            entry_points=self._entry_points,
            preserve_public_api=self._preserve_public_api,
        )

