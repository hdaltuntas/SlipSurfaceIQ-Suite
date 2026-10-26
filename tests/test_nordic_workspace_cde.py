"""Native Nordic Dark C/D/E GUI regression tests, without solver changes."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QFormLayout, QHeaderView, QScrollArea

from slipsurface.apps import catalogue
from slipsurface.desktop.app import DataTable, FigurePreview, MainWindow
from slipsurface.desktop.results import ResultDashboard
from slipsurface.desktop.theme import COLORS, stylesheet


def _app():
    return QApplication.instance() or QApplication([])


def test_all_ten_modules_have_wrapped_forms_and_dark_engine_sessions():
    _app()
    window = MainWindow(language="tr")
    try:
        assert window.theme == "dark"
        for app in catalogue():
            window.open_module(app.key)
            page = window.current_page()
            assert page is not None
            assert page.key == app.key
            if hasattr(page.session, "theme"):
                assert page.session.theme == "dark", app.key
            for group in page.findChildren(QFormLayout):
                assert group.rowWrapPolicy() == QFormLayout.RowWrapPolicy.WrapLongRows
            assert page.work_splitter.count() == 2
            assert page.overview is not None
            window.show_home()
        assert len(window.pages) == 10
    finally:
        window.close()


def test_input_table_column_widths_scroll_without_data_changes():
    _app()
    columns = [
        {"key": "name", "label": "Extremely long geotechnical layer designation", "kind": "text"},
        {"key": "gamma", "label": "Saturated soil unit weight (kN/m³)", "kind": "number"},
        {"key": "phase", "label": "Drainage regime", "kind": "select",
         "options": [{"label": "Drained", "value": "drained"}]},
    ]
    table = DataTable({"columns": columns}, [{"name": "Fill", "gamma": 19.5,
                                               "phase": "drained"}])
    try:
        header = table.table.horizontalHeader()
        assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive
        assert header.stretchLastSection() is False
        assert 90 <= header.sectionSize(0) <= 235
        assert header.sectionSize(2) >= 155
        assert header.count() == 3
        assert table.table.horizontalHeaderItem(0).toolTip() == columns[0]["label"]
        assert table.rows() == [{"name": "Fill", "gamma": 19.5, "phase": "drained"}]
    finally:
        table.close()


def test_figure_preview_keeps_original_pixels_when_narrowed():
    _app()
    viewer = FigurePreview("Run an analysis")
    raster = QPixmap(1100, 550)
    raster.fill(QColor("#EDF1F7"))
    viewer.setPixmap(raster)
    try:
        assert viewer.pixmap().size() == raster.size()
        viewer.resize(320, 360)
        viewer.show()
        _app().processEvents()
        assert viewer.grab().size() == viewer.size()
        assert viewer.pixmap().size() == raster.size()
        viewer.resize(760, 400)
        _app().processEvents()
        assert viewer.pixmap().size() == raster.size()
        viewer.setText("No chart")
        assert viewer.pixmap().isNull()
        assert viewer.text() == "No chart"
    finally:
        viewer.close()


def test_results_table_is_readable_and_scrollable():
    _app()
    dashboard = ResultDashboard("tr")
    try:
        dashboard.update_results({
            "headline": "Çıktı",
            "table": {
                "title": "Test",
                "columns": ["Long engineering method specification", "Value"],
                "rows": [["Bearing method", "1.25"]],
            },
        })
        assert len(dashboard.tables) == 1
        table = dashboard.tables[0]
        assert table.horizontalHeader().stretchLastSection() is False
        assert table.horizontalHeader().sectionSize(0) >= 105
        assert table.horizontalHeaderItem(0).toolTip() == (
            "Long engineering method specification"
        )
        assert table.item(0, 1).toolTip() == "1.25"
    finally:
        dashboard.close()


def test_nordic_dark_plot_panels_and_print_policy():
    _app()
    window = MainWindow(language="en", initial_app="bearing")
    try:
        page = window.current_page()
        assert isinstance(page.plot_label, FigurePreview)
        assert page.plot_label.objectName() == "suitePlotCanvas"
        assert page.plot_label.parent().objectName() == "qt_scrollarea_viewport"
        assert page.findChild(QScrollArea, "suitePlotScroll") is not None
        assert page.result_text.isReadOnly()
        assert page.result_text.lineWrapMode() == page.result_text.LineWrapMode.WidgetWidth
        assert "#262D39" in stylesheet()
        assert COLORS["canvas"] == "#2B303B"
        # A report/PDF comes from the engine, not the UI raster preview.
        assert hasattr(page.session, "report")
        assert page.session.theme == "dark"
    finally:
        window.close()
