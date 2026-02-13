# -*- coding: utf-8 -*-
"""
Name Generator module with Factory pattern.

Provides various strategies for generating obfuscated names.
"""

import hashlib
import random
import string
from typing import Dict, Set
from abc import ABC, abstractmethod


class NameGenerationStrategy(ABC):
    """
    Abstract base class for name generation strategies.

    Implements the Strategy pattern for different name generation styles.
    """

    @abstractmethod
    def generate(self, original: str, prefix: str, counter: int, used_names: Set[str]) -> str:
        """
        Generate an obfuscated name.

        Args:
            original: The original identifier name.
            prefix: The prefix to use for the generated name.
            counter: Current counter value for unique generation.
            used_names: Set of already used names to avoid duplicates.

        Returns:
            A new obfuscated name.
        """
        ...


class RandomNameStrategy(NameGenerationStrategy):
    """Generates random alphanumeric names."""

    def __init__(self, length: int = 8):
        self.length = length

    def generate(self, original: str, prefix: str, counter: int, used_names: Set[str]) -> str:
        chars = string.ascii_letters + string.digits
        while True:
            # First char must be letter or underscore
            name = prefix + random.choice(string.ascii_letters)
            name += ''.join(random.choices(chars, k=self.length - 1))
            if name not in used_names:
                return name


class HexNameStrategy(NameGenerationStrategy):
    """Generates hex-based names."""

    def generate(self, original: str, prefix: str, counter: int, used_names: Set[str]) -> str:
        name = f"{prefix}x{hex(counter + 1)[2:]}"
        return name


class HashNameStrategy(NameGenerationStrategy):
    """Generates hash-based names from the original identifier."""

    def generate(self, original: str, prefix: str, counter: int, used_names: Set[str]) -> str:
        h = hashlib.md5(original.encode()).hexdigest()[:8]
        name = f"{prefix}{h}"
        if name in used_names:
            name = f"{name}_{counter}"
        return name


class NameGeneratorFactory:
    """
    Factory for creating name generation strategies.

    Implements the Factory pattern for name generator creation.
    """

    _strategies: Dict[str, type] = {
        "random": RandomNameStrategy,
        "hex": HexNameStrategy,
        "hash": HashNameStrategy,
    }

    @classmethod
    def create(cls, style: str, **kwargs) -> NameGenerationStrategy:
        """
        Create a name generation strategy.

        Args:
            style: The style of name generation ("random", "hex", "hash")
            **kwargs: Additional arguments for the strategy

        Returns:
            A NameGenerationStrategy instance.

        Raises:
            ValueError: If the style is not recognized.
        """
        strategy_class = cls._strategies.get(style)
        if strategy_class is None:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(f"Unknown name style: {style}. Available: {available}")
        return strategy_class(**kwargs)

    @classmethod
    def register(cls, style: str, strategy_class: type) -> None:
        """
        Register a new name generation strategy.

        Args:
            style: The name for this strategy.
            strategy_class: The strategy class to register.
        """
        cls._strategies[style] = strategy_class

    @classmethod
    def get_available_styles(cls) -> list:
        """Get list of available name generation styles."""
        return list(cls._strategies.keys())


class NameGenerator:
    """
    Generates obfuscated names for variables, functions, and classes.

    Can be shared across multiple files to ensure consistent renaming
    for cross-file obfuscation.

    This class uses the Strategy pattern internally for name generation.
    """

    def __init__(self, prefix: str = "_", style: str = "random"):
        self.prefix = prefix
        self.style = style
        self.counter = 0
        self.name_map: Dict[str, str] = {}
        self._used_names: Set[str] = set()
        # Track which names are methods/attributes for cross-reference
        self.method_names: Set[str] = set()
        self.class_attributes: Set[str] = set()

        # Create the strategy for name generation
        self._strategy = NameGeneratorFactory.create(style)

    def _generate_name(self, original: str) -> str:
        """Generate a new name using the configured strategy."""
        name = self._strategy.generate(
            original,
            self.prefix,
            self.counter,
            self._used_names
        )
        self.counter += 1
        self._used_names.add(name)
        return name

    def get_name(self, original: str) -> str:
        """Get or create an obfuscated name for the original identifier."""
        if original in self.name_map:
            return self.name_map[original]

        new_name = self._generate_name(original)
        self.name_map[original] = new_name
        return new_name

    def register_method(self, name: str) -> None:
        """Register a name as a method for attribute renaming."""
        self.method_names.add(name)

    def register_class_attribute(self, name: str) -> None:
        """Register a name as a class attribute for attribute renaming."""
        self.class_attributes.add(name)

    def is_known_member(self, name: str) -> bool:
        """Check if a name is a known method or class attribute."""
        return name in self.method_names or name in self.class_attributes

    def export_mapping(self) -> Dict[str, str]:
        """Export the name mapping for use in other files or debugging."""
        return dict(self.name_map)

    def import_mapping(self, mapping: Dict[str, str]) -> None:
        """Import a name mapping from another obfuscation session."""
        self.name_map.update(mapping)
        self._used_names.update(mapping.values())

    def pre_register_name(self, original: str) -> str:
        """
        Pre-register a name to ensure consistent mapping across files.

        This is used in the two-phase obfuscation approach:
        Phase 1: Collect all definitions and pre-register them
        Phase 2: Apply transformations using the complete mapping
        """
        return self.get_name(original)

