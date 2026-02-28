# -*- coding: utf-8 -*-
"""
Transformer registry for PyObfuscator.

Provides a centralized registry for all transformation strategies,
enabling dynamic discovery and instantiation.
"""

from typing import Dict, Type, Any, Optional, Union


class TransformerRegistry:
    """
    Centralized registry for all transformers.

    Allows registering transformer classes and creating instances
    based on their registered names.
    """

    _registry: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a transformer class.

        Args:
            name: The unique name to register the transformer under.
        """
        def decorator(transformer_cls: Type[Any]):
            cls._registry[name] = transformer_cls
            return transformer_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[Type[Any]]:
        """
        Get a transformer class by name.

        Args:
            name: The registered name of the transformer.

        Returns:
            The transformer class, or None if not found.
        """
        return cls._registry.get(name)

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> Any:
        """
        Create an instance of a registered transformer.

        Args:
            name: The registered name of the transformer.
            **kwargs: Arguments to pass to the transformer constructor.

        Returns:
            An instance of the transformer.

        Raises:
            KeyError: If the transformer name is not registered.
        """
        transformer_cls = cls._registry.get(name)
        if not transformer_cls:
            raise KeyError(f"Transformer '{name}' is not registered.")
        return transformer_cls(**kwargs)

    @classmethod
    def list_registered(cls) -> Dict[str, Type[Any]]:
        """
        List all registered transformers.

        Returns:
            Dictionary of registered names and their classes.
        """
        return dict(cls._registry)

