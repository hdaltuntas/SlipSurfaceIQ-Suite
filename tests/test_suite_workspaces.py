"""Cross-module verification of the common native workspace design.

No engineering solver is mocked here: the synthetic result dictionaries exercise
presentation only; numerical calculations stay covered by the source regressions.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox

from slipsurface.apps import APPS
from slipsurface.desktop.app import DataTable, MainWindow
from slipsurface.desktop.profiles import PROFILES, profile
from slipsurface.desktop.results import ResultDashboard, result_tables


def _qapp():
    return QApplication.instance() or QApplication([])


def test_profiles_cover_every_installed_module():
    assert tuple(PROFILES) == tuple(module.key for module in APPS)
    assert all(profile(module.key).hint_tr and profile(module.key).hint_en for module in APPS)


def test_kpi_cards_warnings_and_structured_tables():
    _qapp()
    widget = ResultDashboard("tr")
    try:
        payload = {
            "headline": "Kontrol sonucu",
            "cards": [
                {"key": "fs", "title": "FS", "value": "1.70", "state": "ok"},
                {"key": "width", "title": "B", "value": "3.0 m"},
            ],
            "warnings": ["Zemin tabakası yetersiz olabilir."],
            "table": {
                "title": "Kontroller", "columns": ["Kontrol", "FS"],
                "rows": [["Kayma", 1.7], ["Devrilme", 2.1]],
            },
        }
        assert len(result_tables(payload)) == 1
        widget.update_results(payload)
        assert len(widget.metrics) == 2
        assert widget.metrics[0].value_label.text() == "1.70"
        assert widget.metrics[0].property("checkState") == "ok"
        assert widget.warning_label.isVisible() or widget.warning_label.text()
        assert len(widget.tables) == 1
        assert widget.tables[0].item(0, 0).text() == "Kayma"
        widget.clear_results()
        assert not widget.metrics and not widget.tables
    finally:
        widget.close()


def test_kinematic_kpi_fallback():
    _qapp()
    widget = ResultDashboard("tr")
    try:
        widget.update_results({"ok": True, "result": {
            "n_critical": 2, "n_items": 15, "summary": "2 kritik süreksizlik"
        }})
        assert len(widget.metrics) == 2
        assert widget.metrics[0].value_label.text() == "2"
        widget.update_results({"ok": True, "fs_text": "1.28"})
        assert len(widget.metrics) == 1
    finally:
        widget.close()


def test_table_select_preserves_internal_engine_value_and_clone():
    _qapp()
    spec = {"columns": [
        {"key": "name", "label": "Soil", "kind": "text"},
        {"key": "behaviour", "label": "Type", "kind": "select", "options": [
            {"value": "drained", "label": "Drenajlı"},
            {"value": "undrained", "label": "Drenajsız"},
        ]},
        {"key": "thickness", "label": "H", "kind": "number"},
        {"key": "enabled", "label": "Use", "kind": "check"},
    ]}
    editor = DataTable(spec, [
        {"name": "Layer A", "behaviour": "undrained", "thickness": 4.2, "enabled": True}
    ])
    try:
        choice = editor.table.cellWidget(0, 1)
        assert isinstance(choice, QComboBox)
        assert choice.currentText() == "Drenajsız"
        assert editor.rows() == [{
            "name": "Layer A", "behaviour": "undrained", "thickness": 4.2,
            "enabled": True,
        }]
        editor.table.setCurrentCell(0, 0)
        editor.duplicate_selected()
        assert editor.table.rowCount() == 2
        assert editor.rows()[1]["behaviour"] == "undrained"
        editor.remove_selected()
        assert editor.table.rowCount() == 1
    finally:
        editor.close()


def test_each_module_uses_same_summary_panels_and_contextual_sections():
    _qapp()
    window = MainWindow(language="tr", theme="light")
    try:
        for module in APPS:
            window.open_module(module.key)
            page = window.current_page()
            assert page is not None
            assert page.key == module.key
            assert page.profile.module == module.key
            assert page.section_hint.text()
            assert page.input_tabs.count() > 0
            assert page.overview.dashboard.heading.text() == "Analiz Özeti"
            assert page.header.icon_label.pixmap() is not None
            assert page.current_values()
            window.show_home()
        assert len(window.pages) == 10
    finally:
        window.close()


def test_specialist_native_engine_controls():
    _qapp()
    window = MainWindow(language="tr", theme="dark")
    try:
        expected = {"pile": 1, "msew": 1, "wall": 1, "correlation": 2}
        for key, count in expected.items():
            window.open_module(key)
            assert len(window.current_page().special_buttons) == count
            assert all(button.isEnabled() for button in window.current_page().special_buttons)
        window.open_module("kinematic")
        page = window.current_page()
        page.mode.setCurrentText("wedge")
        assert page.input_tabs.tabText(page.input_tabs.currentIndex()) == "Denge · Kama"
        page.mode.setCurrentText("screening")
        assert page.input_tabs.tabText(page.input_tabs.currentIndex()) == "Kinematik Tarama"
    finally:
        window.close()


def test_every_module_project_roundtrip_through_native_editors(tmp_path):
    _qapp()
    window = MainWindow(language="tr", theme="light")
    try:
        for module in APPS:
            window.open_module(module.key)
            page = window.current_page()
            before = page.current_values()
            path = tmp_path / f"{module.key}.json"
            page.save_project(str(path))
            assert path.is_file()
            page.open_project(str(path))
            after = page.current_values()
            assert set(before).issubset(after)
            assert after.get("title") == before.get("title")
            window.show_home()
    finally:
        window.close()
