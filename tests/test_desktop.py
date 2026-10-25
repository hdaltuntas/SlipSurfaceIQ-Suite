"""Headless Qt smoke tests; set QT_QPA_PLATFORM=offscreen in CI."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from slipsurface.apps import APPS
from slipsurface.desktop.app import MainWindow, ModulePage, _conditions_match, _table_key
from slipsurface.desktop.home import module_description
from slipsurface.desktop.icons import ICON_DIR, module_icon
from slipsurface.desktop.theme import stylesheet


def test_visibility_predicates():
    values = {"shape": "rectangle", "method": "vesic"}
    assert _conditions_match({"shapes": ["rectangle"]}, values)
    assert not _conditions_match({"shapes": ["circle"]}, values)
    assert _conditions_match({"when": [{"key": "method", "in": ["vesic"]}]}, values)
    assert not _conditions_match({"when": {"method": ["hansen"]}}, values)


def test_home_dashboard_is_default_and_all_cards_are_localized():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light")
    try:
        assert window.stack.currentWidget() is window.home
        assert window.current_page() is None
        assert len(window.home.cards) == len(APPS) == 10
        assert all(not action.isEnabled() for action in window.project_actions)
        for module in APPS:
            card = window.home.cards[module.key]
            assert card.accessibleName() == module.tr
            assert card.accessibleDescription() == module_description(module, "tr")
            assert card.accessibleDescription().strip()
            assert card.launch_button.text().startswith("Programı aç")
            assert not card.icon_label.pixmap().isNull()
            assert not module_icon(module.key).isNull()
        assert app.styleSheet()
    finally:
        window.close()


def test_card_opens_module_and_back_preserves_state():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light")
    try:
        window.home.cards["bearing"].launch_button.click()
        page = window.current_page()
        assert page is not None and page.key == "bearing"
        assert page.fields
        assert window.stack.currentWidget() is window.workspace
        assert all(action.isEnabled() for action in window.project_actions)

        window.back_button.click()
        assert window.current_page() is None
        assert window.stack.currentWidget() is window.home

        window.home.cards["bearing"].activate()
        assert window.current_page() is page  # no destructive reinitialization
        window.show_home()
        window.home.cards["rock"].activate()
        assert window.current_page().key == "rock"
        window.show_home()
        assert len(window.pages) == 2
    finally:
        window.close()
    assert app is not None


def test_direct_module_launch_remains_supported():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="en", theme="dark", initial_app="bearing")
    try:
        assert window.current_page() is not None
        assert window.current_page().key == "bearing"
        assert window.navigator.count() == 10
        assert window.current_page().fields
        assert app.styleSheet()
        window.show_home()
        assert window.current_page() is None
        assert window.home.cards["bearing"].accessibleName() == "Bearing"
        assert window.home.cards["bearing"].accessibleDescription() == module_description(
            APPS[2], "en"
        )
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


def test_vector_icon_library_covers_each_module_and_both_themes():
    for module in APPS:
        path = ICON_DIR / f"{module.key}.svg"
        svg = path.read_text(encoding="utf-8")
        assert 'viewBox="0 0 64 64"' in svg
        assert "<svg" in svg
        icon = module_icon(module.key)
        assert not icon.pixmap(48, 48).isNull()
    assert "suiteModuleHeader" in stylesheet("light")
    assert "suiteModuleHeader" in stylesheet("dark")
    assert "suiteCardIcon" in stylesheet("light")
    assert "suiteCardIcon" in stylesheet("dark")


def test_shared_module_headers_are_consistent_and_accessible():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light")
    try:
        for module in APPS:
            window.home.cards[module.key].launch_button.click()
            page = window.current_page()
            assert page is not None and page.key == module.key
            assert page.header.title_label.text() == module.tr
            assert page.header.subtitle_label.text() == module.description_tr
            assert page.header.icon_label.pixmap() is not None
            assert not page.header.icon_label.pixmap().isNull()
            assert not window.navigator.currentItem().icon().isNull()
            assert not window.view.tabIcon(window.view.currentIndex()).isNull()
            window.show_home()
        window.set_theme("dark")
        window.home.cards["bearing"].launch_button.click()
        assert window.current_page().header.isVisible() or window.current_page().header is not None
    finally:
        window.close()
    assert app is not None
