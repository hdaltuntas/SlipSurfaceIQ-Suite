"""Protect open engineering projects during optional module updates."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from slipsurface.desktop.app import MainWindow
from slipsurface.desktop.updater import AppUpdate


def test_update_cannot_discard_open_unsaved_project(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", initial_app="bearing")
    try:
        page = window.current_page()
        assert page is not None
        first_key = next(iter(page.fields))
        before = page.current_values()
        window.available_updates["bearing"] = AppUpdate(
            "bearing", "1.0.0", "1.0.1",
            url="https://example.com/bearing.zip", sha256="0" * 64,
        )
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )
        monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: ("", ""))
        window.install_update("bearing")
        assert window._update_task is None
        assert window.current_page() is page
        assert page.current_values()[first_key] == before[first_key]

        warnings = []
        monkeypatch.setattr(
            QMessageBox, "warning",
            lambda *args, **kwargs: warnings.append(args[-1]),
        )
        page.busy = True
        window.install_update("bearing")
        assert warnings
        assert window._update_task is None
    finally:
        window.close()
    assert app is not None


def test_unsigned_update_is_not_offered_as_installable(monkeypatch):
    from slipsurface.desktop.home import HomePage

    _ = QApplication.instance() or QApplication([])
    no_hash = AppUpdate(
        "bearing", "1.0.0", "1.0.1",
        url="https://example.com/bearing.zip",
    )
    page = HomePage("tr", {"bearing": no_hash})
    try:
        card = page.cards["bearing"]
        installs = card.findChildren(type(card.launch_button), "suiteCardUpdateInstall")
        assert not installs
    finally:
        page.close()
