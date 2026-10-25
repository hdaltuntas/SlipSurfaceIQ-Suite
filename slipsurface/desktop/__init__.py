"""Native PySide6 interface.

The Qt shell is imported lazily: ``desktop`` also hosts Qt-free helpers such
as ``updater``, and importing PySide6 at package level would make those
helpers — and their tests — impossible to run headless.
"""
__all__ = ["main"]


def __getattr__(name):
    if name == "main":
        from slipsurface.desktop.app import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
