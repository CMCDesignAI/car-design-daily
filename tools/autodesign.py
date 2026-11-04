#!/usr/bin/env python3
"""Compatibility entry point for the multi-source design columns queue."""
try:
    from .columns import main
except ImportError:
    from columns import main

if __name__ == '__main__':
    main()
