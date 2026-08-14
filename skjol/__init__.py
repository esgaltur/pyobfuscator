"""Skjol public API.

The implementation currently lives in the legacy ``pyobfuscator`` package so
existing integrations remain compatible during the project rename.
"""

from pyobfuscator import *  # noqa: F401,F403
from pyobfuscator import __all__ as _legacy_all
from pyobfuscator import __version__

__all__ = [*_legacy_all]
