#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Entry point for running pyobfuscator as a module: python -m pyobfuscator
"""

from .cli import main
import sys

if __name__ == '__main__':
    sys.exit(main())
