"""Capture real native PySide6 launchpad and module screens, not mockups."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

from PySide6.QtWidgets import QApplication

from slipsurface.apps import APPS
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
        _capture(window, output, f"native        module_dir = output / "modules"
        module_dir.mkdir(exist_ok=True)
        for module in APPS:
            window.open_module(module.key)
            page = window.current_page()
            if page is None or page.key != module.key:
                raise RuntimeError(f"Module {module.key} failed to open")
            _capture(window, module_dir, f"{module.key}-{theme}.png", app)
            if module.key == "bearing":
                _capture(window, output, f"native-pyside6-bearing-{theme}.png", app)
            window.show_home()
yside6-bearing-{theme}.png", app)
        window.close()
        app.processEvents()


if __name__ == "__main__":
    capture()
