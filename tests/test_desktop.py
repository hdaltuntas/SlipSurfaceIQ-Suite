"""Headless Qt smoke tests; set QT_QPA_PLATFORM=offscreen in CI."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from slipsurface.apps import APPS
from slipsurface.desktop.app import MainWindow, ModulePage, _conditions_match, _table_key


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


def test_module_table_key_mapping():
    assert _table_key("correlation", "spt") == "spt_tests"
    assert _table_key("correlation", "vs") == "vs_tests"
    assert _table_key("liquefaction", "spt") == "spt"
    assert _table_key("msew", "types") == "reinforcement_types"
    assert _table_key("bearing", "soil") == "soil_profile"
    assert _table_key("kinematic", "screening") == "joints"


def test_each_module_opens_in_native_qt():
    app = QApplication.instance() or QApplication([])
    pages = []
    try:
        for module in APPS:
            page = ModulePage(module.key, "tr")
            pages.append(page)
            assert page.key == module.key
            assert page.input_tabs.count() > 0
            assert page.current_values()
    finally:
        for page in pages:
            page.close()
    assert app is not None
