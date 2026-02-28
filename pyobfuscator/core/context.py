# -*- coding: utf-8 -*-
"""
Transformation Context for PyObfuscator.

Provides a strict contract for passing state, configuration, and shared
secrets between different stages of the transformation pipeline.
"""

from typing import Dict, Any, Optional
import secrets


class TransformationContext:
    """
    Context object passed to transformers during execution.
    Holds shared state like the global name map, configuration, and session secrets.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # A cryptographically secure random secret unique to this specific obfuscation run
        self.session_secret: bytes = secrets.token_bytes(32)
        # Shared state between transformers (e.g., recorded checkpoints, honeypot names)
        self.state: Dict[str, Any] = {
            "checkpoints": [],
            "honeypots": set()
        }

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
