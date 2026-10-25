"""Shared, vector-based programme icon provider for every Qt view."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon

from slipsurface.apps import get

ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"


def module_icon(key: str) -> QIcon:
    """Return the same SVG icon for dashboard, navigation and module headers."""
    get(key)  # validate registry key before resolving a filesystem path
    path = ICON_DIR / f"{key}.svg"
    if not path.is_file():
        path = ICON_DIR / "generic.svg"
    return QIcon(str(path))
