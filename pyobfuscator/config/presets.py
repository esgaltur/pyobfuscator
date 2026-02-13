# -*- coding: utf-8 -*-
"""
Configuration presets for PyObfuscator.

Provides pre-configured settings for common use cases.
"""

from typing import Dict
from .builder import ObfuscatorConfig, ObfuscatorBuilder


class ConfigPresets:
    """
    Pre-configured obfuscation settings for common use cases.

    These presets provide sensible defaults for different scenarios.
    """

    @staticmethod
    def minimal() -> ObfuscatorConfig:
        """
        Minimal obfuscation - only variable renaming.

        Good for quick protection with minimal risk of breaking code.
        """
        return (
            ObfuscatorBuilder()
            .with_variable_renaming(True)
            .with_function_renaming(False)
            .with_class_renaming(False)
            .with_method_renaming(False)
            .with_attribute_renaming(False)
            .with_string_obfuscation(None)
            .with_compression(False)
            .build()
        )

    @staticmethod
    def standard() -> ObfuscatorConfig:
        """
        Standard obfuscation - balanced protection.

        Renames all identifiers and obfuscates strings.
        Default recommended settings.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .with_compression(False)
            .build()
        )

    @staticmethod
    def maximum() -> ObfuscatorConfig:
        """
        Maximum obfuscation - all features enabled.

        Full protection with compression. May increase file size
        and slightly affect performance.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .with_compression(True)
            .with_docstring_removal(True)
            .with_comment_removal(True)
            .build()
        )

    @staticmethod
    def library() -> ObfuscatorConfig:
        """
        Library/package obfuscation - preserves public API.

        Suitable for obfuscating libraries where you want to
        maintain the external interface.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .preserve_public_api(True)
            .build()
        )

    @staticmethod
    def pyside6_app() -> ObfuscatorConfig:
        """
        PySide6/Qt application preset.

        Preserves Qt-specific names like signals, slots, and event handlers.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .for_framework("pyside6")
            .build()
        )

    @staticmethod
    def pyqt6_app() -> ObfuscatorConfig:
        """
        PyQt6 application preset.

        Similar to PySide6 but with PyQt6-specific names.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .for_framework("pyqt6")
            .build()
        )

    @staticmethod
    def flask_app() -> ObfuscatorConfig:
        """
        Flask web application preset.

        Preserves Flask framework names and common patterns.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .for_framework("flask")
            .build()
        )

    @staticmethod
    def django_app() -> ObfuscatorConfig:
        """
        Django web application preset.

        Preserves Django framework names and model patterns.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .for_framework("django")
            .build()
        )

    @staticmethod
    def fastapi_app() -> ObfuscatorConfig:
        """
        FastAPI web application preset.

        Preserves FastAPI and Pydantic names.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .for_framework("fastapi")
            .build()
        )

    @staticmethod
    def cli_app() -> ObfuscatorConfig:
        """
        CLI application preset (Click-based).

        Preserves Click decorator names and patterns.
        """
        return (
            ObfuscatorBuilder()
            .with_all_renaming(True)
            .with_string_obfuscation("xor")
            .for_framework("click")
            .with_entry_point("main")
            .build()
        )


# Registry of all presets for easy lookup
PRESET_REGISTRY: Dict[str, callable] = {
    "minimal": ConfigPresets.minimal,
    "standard": ConfigPresets.standard,
    "maximum": ConfigPresets.maximum,
    "library": ConfigPresets.library,
    "pyside6": ConfigPresets.pyside6_app,
    "pyqt6": ConfigPresets.pyqt6_app,
    "flask": ConfigPresets.flask_app,
    "django": ConfigPresets.django_app,
    "fastapi": ConfigPresets.fastapi_app,
    "cli": ConfigPresets.cli_app,
}


def get_preset(name: str) -> ObfuscatorConfig:
    """
    Get a configuration preset by name.

    Args:
        name: The preset name (e.g., "standard", "minimal", "flask")

    Returns:
        An ObfuscatorConfig instance.

    Raises:
        ValueError: If the preset name is not recognized.
    """
    preset_func = PRESET_REGISTRY.get(name.lower())
    if preset_func is None:
        available = ", ".join(PRESET_REGISTRY.keys())
        raise ValueError(f"Unknown preset: {name}. Available: {available}")
    return preset_func()


def list_presets() -> list:
    """Get list of available preset names."""
    return list(PRESET_REGISTRY.keys())

