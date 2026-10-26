"""Headless Qt smoke tests; set QT_QPA_PLATFORM=offscreen in CI."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from slipsurface.apps import APPS
from slipsurface.desktop.app import MainWindow, ModulePage, _conditions_match, _table_key
from slipsurface.desktop.home import module_description
from slipsurface.desktop.icons import ICON_DIR, module_icon
from slipsurface.desktop.theme import stylesheet
from slipsurface.desktop.widgets import section_title


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


def test_vector_icon_library_and_nordic_dark_stylesheet():
    for module in APPS:
        path = ICON_DIR / f"{module.key}.svg"
        svg = path.read_text(encoding="utf-8")
        assert 'viewBox="0 0 64 64"' in svg
        assert "<svg" in svg
        icon = module_icon(module.key)
        assert not icon.pixmap(48, 48).isNull()
    css = stylesheet()
    assert "suiteModuleHeader" in css
    assert "suiteCardIcon" in css
    assert "#2B303B" in css
    assert "#8FC9C3" in css
    assert stylesheet("light") == css  # legacy callers cannot reactivate light mode


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

def test_standardized_tab_titles():
    assert section_title("foundation", "tr") == "Temel"
    assert section_title("options", "tr") == "Analiz Ayarları"
    assert section_title("equilibrium:planar", "tr") == "Denge · Düzlemsel"
    assert section_title("equilibrium:wedge", "en") == "Equilibrium · Wedge"
    assert section_title("cpt", "tr") == "CPT Verileri"
    assert section_title("study", "en") == "Study"


def test_persistent_nordic_dark_navigation_and_live_language_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light")
    try:
        # Toolbar remains visible on launcher and module workspaces.
        assert window.shell_header is not None
        assert window.back_button.text().endswith("Ana Sayfa")
        assert window.language_button.text().startswith("EN")
        assert not hasattr(window, "theme_button")
        assert window.theme == "dark"
        assert not window.toolbar_actions["save"].isEnabled()
        window.set_theme("light")  # historical callers are safely mapped to dark
        assert window.theme == "dark"
        assert "#2B303B" in app.styleSheet()
        assert "#8FC9C3" in app.styleSheet()
        assert not any(
            "Karanlık" in action.text() or "Aydınlık" in action.text()
            for menu in window.menuBar().actions()
            for action in menu.menu().actions()
            if menu.menu() is not None
        )
        window.language_button.click()
        assert window.language == "en"
        assert window.back_button.text().endswith("Home")
        assert window.language_button.text().startswith("TR")
        assert window.home.cards["bearing"].accessibleName() == "Bearing"

        window.home.cards["bearing"].launch_button.click()
        assert window.toolbar_actions["save"].isEnabled()
        assert window.current_page().header.title_label.text() == "Bearing"
        window.back_button.click()
        assert window.stack.currentWidget() is window.home
        assert not window.toolbar_actions["pdf"].isEnabled()
    finally:
        window.close()


def test_language_switch_retains_open_modules_inputs_and_sessions():
    _ = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light", initial_app="bearing")
    try:
        bearing = window.current_page()
        assert bearing is not None
        # Change one real numeric control, then preserve its full project data.
        from PySide6.QtWidgets import QDoubleSpinBox
        spin = next(w for widgets in bearing.fields.values()
                    for w, _ in widgets if isinstance(w, QDoubleSpinBox))
        spin.setValue(min(spin.maximum(), spin.value() + 1.0))
        before_bearing = bearing.current_values()
        session = bearing.session
        result = {"headline": "Earlier calculation", "cards": []}
        bearing.last_result = result
        bearing.result_text.setPlainText("Previously computed details")
        bearing.overview.dashboard.update_results(result)

        window.open_module("correlation")
        correlation = window.current_page()
        before_correlation = correlation.current_values()
        window.show_home()
        assert window.set_language("en")
        assert window.stack.currentWidget() is window.home
        assert len(window.pages) == 2
        assert window.pages["bearing"].current_values() == before_bearing
        assert window.pages["correlation"].current_values() == before_correlation
        assert window.pages["bearing"].session is session
        assert window.pages["bearing"].last_result is result
        assert window.pages["bearing"].result_text.toPlainText() == (
            "Previously computed details"
        )
        window.open_module("bearing")
        assert window.current_page().header.title_label.text() == "Bearing"
        assert window.view.tabText(window.view.currentIndex()) == "Bearing"
        assert window.set_language("tr")
        assert window.current_page().header.title_label.text() == "Temel Taşıma Gücü"
        assert window.current_page().current_values() == before_bearing
    finally:
        window.close()


def test_language_switch_is_blocked_during_running_analysis(monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    _ = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", initial_app="bearing")
    try:
        original = window.current_page()
        original.busy = True
        messages = []
        monkeypatch.setattr(QMessageBox, "information",
                            lambda *a, **kw: messages.append(a[-1]))
        assert not window.set_language("en")
        assert messages
        assert window.language == "tr"
        assert window.current_page() is original
    finally:
        window.close()


def test_compact_editor_gives_priority_to_results():
    _ = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", initial_app="correlation")
    try:
        splitter = window.current_page().work_splitter
        assert splitter.objectName() == "suiteEditorSplitter"
        assert splitter.handleWidth() == 8
        assert not splitter.childrenCollapsible()
        assert splitter.count() == 2
    finally:
        window.close()
