"""Headless Qt smoke tests; set QT_QPA_PLATFORM=offscreen in CI."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402
from slipsurface.desktop.app import MainWindow, _conditions_match  # noqa: E402


def test_visibility_predicates():
    values = {"shape": "rectangle", "method": "vesic"}
    assert _conditions_match({"shapes": ["rectangle"]}, values)
    assert not _conditions_match({"shapes": ["circle"]}, values)
    assert _conditions_match({"when": [{"key": "method", "in": ["vesic"]}]}, values)
    assert not _conditions_match({"when": {"method": ["hansen"]}}, values)


def test_bearing_page_loads_in_native_shell():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light", initial_app="bearing")
    try:
        assert window.current_page() is not None
        assert window.current_page().key == "bearing"
        assert window.navigator.count() == 10
        assert window.current_page().fields
        assert app.styleSheet()
    finally:
        window.close()
