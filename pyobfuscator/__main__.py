#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compatibility entry point for the legacy ``python -m pyobfuscator`` command.
"""

from .cli import main
import sys

if __name__ == '__main__':
    sys.exit(main())
