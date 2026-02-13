# -*- coding: utf-8 -*-
"""
Custom exceptions for PyObfuscator.

Provides a hierarchy of exceptions for better error handling and
more informative error messages throughout the library.
"""

from typing import Optional


class PyObfuscatorError(Exception):
    """
    Base exception for all PyObfuscator errors.

    All custom exceptions in this library inherit from this class,
    making it easy to catch any PyObfuscator-related error.
    """

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


# =============================================================================
# Source Code Errors
# =============================================================================

class SourceCodeError(PyObfuscatorError):
    """Base exception for source code related errors."""
    pass


class EmptySourceError(SourceCodeError):
    """Raised when source code is empty or contains only whitespace."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Source code cannot be empty", details)


class InvalidSyntaxError(SourceCodeError):
    """Raised when source code contains invalid Python syntax."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Invalid Python syntax", details)


class UnsupportedPythonVersionError(SourceCodeError):
    """Raised when source code uses features from an unsupported Python version."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Unsupported Python version features", details)


# =============================================================================
# Obfuscation Errors
# =============================================================================

class ObfuscationError(PyObfuscatorError):
    """Base exception for obfuscation related errors."""
    pass


class TransformationError(ObfuscationError):
    """Raised when an AST transformation fails."""

    def __init__(self, transformer_name: str, details: Optional[str] = None):
        self.transformer_name = transformer_name
        super().__init__(
            f"Transformation failed in {transformer_name}",
            details
        )


class NameGenerationError(ObfuscationError):
    """Raised when name generation fails."""

    def __init__(self, original_name: str, details: Optional[str] = None):
        self.original_name = original_name
        super().__init__(
            f"Failed to generate name for '{original_name}'",
            details
        )


class StringObfuscationError(ObfuscationError):
    """Raised when string obfuscation fails."""

    def __init__(self, method: str, details: Optional[str] = None):
        self.method = method
        super().__init__(
            f"String obfuscation failed using method '{method}'",
            details
        )


class CodeGenerationError(ObfuscationError):
    """Raised when generating obfuscated code fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Failed to generate obfuscated code", details)


# =============================================================================
# Encryption Errors
# =============================================================================

class CryptoError(PyObfuscatorError):
    """Base exception for cryptography related errors."""
    pass


class EncryptionError(CryptoError):
    """Raised when encryption fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Encryption failed", details)


class DecryptionError(CryptoError):
    """Raised when decryption fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Decryption failed", details)


class AuthenticationError(CryptoError):
    """Raised when authentication/integrity check fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Authentication failed", details)


class InvalidKeyError(CryptoError):
    """Raised when an encryption key is invalid."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Invalid encryption key", details)


# =============================================================================
# Protection Errors
# =============================================================================

class ProtectionError(PyObfuscatorError):
    """Base exception for code protection related errors."""
    pass


class RuntimeProtectionError(ProtectionError):
    """Raised when runtime protection fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Runtime protection failed", details)


class PydProtectionError(ProtectionError):
    """Raised when PYD/Cython protection fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("PYD protection failed", details)


class LicenseError(ProtectionError):
    """Raised when license validation fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("License validation failed", details)


class MachineBindingError(ProtectionError):
    """Raised when machine binding validation fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Machine binding validation failed", details)


class ExpirationError(ProtectionError):
    """Raised when protected code has expired."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Protected code has expired", details)


class AntiDebugError(ProtectionError):
    """Raised when debugger detection is triggered."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Debugger detected", details)


# =============================================================================
# File/IO Errors
# =============================================================================

class FileError(PyObfuscatorError):
    """Base exception for file operation errors."""
    pass


class FileNotFoundError(FileError):
    """Raised when a required file is not found."""

    def __init__(self, filepath: str, details: Optional[str] = None):
        self.filepath = filepath
        super().__init__(f"File not found: {filepath}", details)


class FileReadError(FileError):
    """Raised when reading a file fails."""

    def __init__(self, filepath: str, details: Optional[str] = None):
        self.filepath = filepath
        super().__init__(f"Failed to read file: {filepath}", details)


class FileWriteError(FileError):
    """Raised when writing a file fails."""

    def __init__(self, filepath: str, details: Optional[str] = None):
        self.filepath = filepath
        super().__init__(f"Failed to write file: {filepath}", details)


class DirectoryError(FileError):
    """Raised when a directory operation fails."""

    def __init__(self, dirpath: str, details: Optional[str] = None):
        self.dirpath = dirpath
        super().__init__(f"Directory operation failed: {dirpath}", details)


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigError(PyObfuscatorError):
    """Base exception for configuration related errors."""
    pass


class InvalidConfigError(ConfigError):
    """Raised when configuration is invalid."""

    def __init__(self, config_key: Optional[str] = None, details: Optional[str] = None):
        self.config_key = config_key
        message = f"Invalid configuration for '{config_key}'" if config_key else "Invalid configuration"
        super().__init__(message, details)


class ConfigNotFoundError(ConfigError):
    """Raised when a configuration file is not found."""

    def __init__(self, filepath: str, details: Optional[str] = None):
        self.filepath = filepath
        super().__init__(f"Configuration file not found: {filepath}", details)


class UnsupportedFrameworkError(ConfigError):
    """Raised when an unsupported framework is specified."""

    def __init__(self, framework: str, available: Optional[list] = None):
        self.framework = framework
        self.available = available
        details = f"Available frameworks: {', '.join(available)}" if available else None
        super().__init__(f"Unsupported framework: {framework}", details)


# =============================================================================
# Analysis Errors
# =============================================================================

class AnalysisError(PyObfuscatorError):
    """Base exception for code analysis errors."""
    pass


class ProjectAnalysisError(AnalysisError):
    """Raised when project analysis fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Project analysis failed", details)


class DependencyAnalysisError(AnalysisError):
    """Raised when dependency analysis fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__("Dependency analysis failed", details)

