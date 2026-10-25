"""Capture real native PySide6 launchpad and module screens, not mockups."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

from PySide6.QtWidgets import QApplication

from slipsurface.desktop.app import MainWindow


def _capture(window: MainWindow, output: Path, filename: str, app: QApplication):
    for _ in range(8):
        app.processEvents()
    path = output / filename
    shot = window.grab()
    if shot.isNull() or not shot.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture {path}")
    print(f"Captured {path}: {shot.width()} x {shot.height()}, {path.stat().st_size} bytes")


def capture() -> None:
    output = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    for theme in ("light", "dark"):
        window = MainWindow(language="tr", theme=theme)
        window.resize(1500, 920)
        window.show()
        if window.current_page() is not None or len(window.home.cards) != 10:
            raise RuntimeError("Home dashboard did not appear with ten module cards")
        _capture(window, output, f"native-pyside6-home-{theme}.png", app)

        # Exercise the same user-facing route as clicking a module card.
        window.home.cards["bearing"].launch_button.click()
        if window.current_page() is None or window.current_page().key != "bearing":
            raise RuntimeError("Bearing module could not be opened from its card")
        _capture(window, output, f"native-pyside6-bearing-{theme}.png", app)
        window.close()
        app.processEvents()


if __name__ == "__main__":
    capture()
