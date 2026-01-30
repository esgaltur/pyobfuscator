#!/usr/bin/env python
"""
Entry point for running pyobfuscate as a module: python -m pyobfuscate
"""

from .cli import main
import sys

if __name__ == '__main__':
    sys.exit(main())
