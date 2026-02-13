# -*- coding: utf-8 -*-
"""
Protocol definitions for PyObfuscator.

Defines interfaces using Python's Protocol class for type hints and
structural subtyping. These protocols enable dependency injection,
testability, and adherence to the Interface Segregation Principle.
"""

from typing import Protocol, Dict, Optional, runtime_checkable
import ast


@runtime_checkable
class Transformer(Protocol):
    """
    Protocol for AST transformers.

    Any class that transforms Python source code or AST nodes should
    implement this protocol.
    """

    def transform(self, source: str) -> str:
        """
        Transform Python source code.

        Args:
            source: The Python source code to transform.

        Returns:
            Transformed Python source code.
        """
        ...


@runtime_checkable
class ASTTransformer(Protocol):
    """
    Protocol for AST node transformers.

    Classes implementing this protocol transform AST nodes directly.
    """

    def visit(self, node: ast.AST) -> ast.AST:
        """
        Visit and potentially transform an AST node.

        Args:
            node: The AST node to visit.

        Returns:
            The transformed AST node (may be the same or different).
        """
        ...


@runtime_checkable
class Encryptor(Protocol):
    """
    Protocol for encryption engines.

    Any class providing encryption/decryption capabilities should
    implement this protocol.
    """

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt binary data.

        Args:
            data: The data to encrypt.

        Returns:
            Encrypted data (includes any necessary metadata like IV/nonce).
        """
        ...

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt binary data.

        Args:
            data: The encrypted data to decrypt.

        Returns:
            Decrypted original data.

        Raises:
            ValueError: If decryption fails (e.g., authentication failure).
        """
        ...


@runtime_checkable
class NameMappingProvider(Protocol):
    """
    Protocol for name mapping providers.

    Classes that generate obfuscated names and maintain mappings
    should implement this protocol.
    """

    def get_name(self, original: str) -> str:
        """
        Get or create an obfuscated name for the original identifier.

        Args:
            original: The original identifier name.

        Returns:
            The obfuscated name.
        """
        ...

    def export_mapping(self) -> Dict[str, str]:
        """
        Export the current name mapping.

        Returns:
            Dictionary mapping original names to obfuscated names.
        """
        ...


@runtime_checkable
class StringObfuscationStrategy(Protocol):
    """
    Protocol for string obfuscation strategies.

    Implements the Strategy pattern for different string obfuscation methods.
    """

    def obfuscate(self, value: str) -> ast.AST:
        """
        Obfuscate a string value.

        Args:
            value: The string literal to obfuscate.

        Returns:
            An AST node that evaluates to the original string at runtime.
        """
        ...


@runtime_checkable
class NameGeneratorStrategy(Protocol):
    """
    Protocol for name generation strategies.

    Implements the Strategy pattern for different name generation styles.
    """

    def generate(self, original: str, context: Optional[Dict] = None) -> str:
        """
        Generate an obfuscated name.

        Args:
            original: The original identifier name.
            context: Optional context for generation (e.g., counter, used names).

        Returns:
            A new obfuscated name.
        """
        ...


@runtime_checkable
class CodeProtector(Protocol):
    """
    Protocol for code protection implementations.

    Classes that protect Python code (e.g., encryption, bytecode protection)
    should implement this protocol.
    """

    def protect_source(self, source: str, filename: Optional[str] = None) -> tuple:
        """
        Protect Python source code.

        Args:
            source: The Python source code to protect.
            filename: Optional filename for error messages.

        Returns:
            Tuple of protected artifacts (implementation-specific).
        """
        ...

    def protect_file(self, input_path: str, output_dir: str) -> Dict[str, str]:
        """
        Protect a Python file.

        Args:
            input_path: Path to the input Python file.
            output_dir: Directory for output files.

        Returns:
            Dictionary of output file paths.
        """
        ...


@runtime_checkable
class ConfigBuilder(Protocol):
    """
    Protocol for configuration builders.

    Implements the Builder pattern for constructing configuration objects.
    """

    def build(self) -> object:
        """
        Build and return the configuration object.

        Returns:
            The constructed configuration object.
        """
        ...


@runtime_checkable
class MachineIdentifier(Protocol):
    """
    Protocol for machine identification.

    Classes that provide machine-specific identifiers for hardware binding.
    """

    def get_machine_id(self) -> str:
        """
        Get a unique machine identifier.

        Returns:
            A hash or identifier unique to this machine.
        """
        ...

