"""Capture actual native PySide6 home and all ten module screens."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

from PySide6.QtWidgets import QApplication

from slipsurface.apps import APPS
from slipsurface.desktop.about import AboutDialog
from slipsurface.desktop.app import MainWindow
from slipsurface.desktop.splash import BrandSplash


def _capture(window: MainWindow, folder: Path, name: str, app: QApplication) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for _ in range(8):
        app.processEvents()
    path = folder / name
    shot = window.grab()
    if shot.isNull() or not shot.save(str(path), "PNG"):
        raise RuntimeError(f"Could not capture {path}")
    print(f"Captured {path}: {shot.width()} x {shot.height()}, {path.stat().st_size} bytes")


def capture() -> None:
    output = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    artwork = BrandSplash.render_artwork("tr")
    splash_path = output / "brand-splash.png"
    if artwork.isNull() or not artwork.save(str(splash_path), "PNG"):
        raise RuntimeError("Could not capture native branded splash artwork")
    print(f"Captured {splash_path}: {artwork.width()} x {artwork.height()}")
    for theme in ("dark",):
        window = MainWindow(language="tr", theme=theme)
        window.resize(1500, 920)
        window.show()
        if window.current_page() is not None or len(window.home.cards) != len(APPS):
            raise RuntimeError("Home dashboard did not load")
        _capture(window, output, f"native-pyside6-home-{theme}.png", app)

        # The About window is a native, bilingual dialog with license credits.
        about = AboutDialog(language="tr", parent=window)
        about.show()
        _capture(about, output, f"native-pyside6-about-{theme}.png", app)
        about.close()

        for module in APPS:
            window.open_module(module.key)
            page = window.current_page()
            if page is None or page.key != module.key:
                raise RuntimeError(f"Module {module.key} failed to open")
            _capture(window, output / "modules", f"{module.key}-{theme}.png", app)
            if module.key == "bearing":
                _capture(window, output, f"native-pyside6-bearing-{theme}.png", app)
            window.show_home()
        window.close()
        app.processEvents()


if __name__ == "__main__":
    capture()
