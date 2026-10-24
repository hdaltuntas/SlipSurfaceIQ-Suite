#!/usr/bin/env python3
"""Launch the SlipSurfaceIQ Suite native PySide6 desktop application.

Run: python main.py [--lang tr|en] [--theme light|dark] [--app bearing]
"""
from slipsurface.desktop import main

if __name__ == "__main__":
    raise SystemExit(main())
