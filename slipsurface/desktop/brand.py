"""SlipSurfaceIQ corporate identity tokens and native SVG brand assets.

These SVG shapes preserve the user's selected S mark, traced into editable
vectors. No Qt resource compiler, web engine, icon fonts or binary packaging.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon

BRAND_ASSETS = Path(__file__).resolve().parent / "assets" / "brand"
PALETTE = {
    "midnight": "#0B1529",
    "cyan": "#00DDF5",
    "blue": "#238CFF",
    "iris": "#6B4CFF",
    "violet": "#B629F4",
    "mist": "#EFF5FD",
}
BRAND_NAME = "SlipSurfaceIQ"
BRAND_DESCRIPTOR = "GEOTECHNICAL ENGINEERING SUITE"


def symbol_icon() -> QIcon:
    """Editable source SVG; scales sharply in headers and on HiDPI screens."""
    return QIcon(str(BRAND_ASSETS / "symbol.svg"))


def application_icon() -> QIcon:
    """Square logo for operating-system windows and desktop task switching."""
    return QIcon(str(BRAND_ASSETS / "app_icon.svg"))
