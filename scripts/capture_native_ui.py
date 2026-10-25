"""Capture actual running native Qt interface; no mockups or web renderer."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

from PySide6.QtWidgets import QApplication

from slipsurface.desktop.app import MainWindow


def capture() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "docs" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    for theme in ("light", "dark"):
        window = MainWindow(language="tr", theme=theme, initial_app="bearing")
        window.resize(1500, 920)
        window.show()
        for _ in range(6):
            app.processEvents()
        page = window.current_page()
        if page is None or page.key != "bearing":
            raise RuntimeError("Bearing page could not load")
        filename = output / f"native-pyside6-bearing-{theme}.png"
        shot = window.grab()
        if shot.isNull() or not shot.save(str(filename), "PNG"):
            raise RuntimeError(f"Failed to capture {filename}")
        print(f"Captured {filename}: {shot.width()} x {shot.height()}, {filename.stat().st_size} bytes")
        window.close()
        app.processEvents()


if __name__ == "__main__":
    capture()
