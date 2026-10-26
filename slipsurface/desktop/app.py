"""Native, single-window PySide6 shell for the Python geotechnical engines.

No HTTP server, QWebEngine, browser content or JavaScript is used. Existing
module session adapters run in-process; results and figures remain local.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import inspect
import json
import logging
import os
import sys

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, QSize, Signal
from PySide6.QtGui import QAction, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from slipsurface import APP_NAME, __version__
from slipsurface import apps as app_catalogue
from slipsurface.apps import forms_path, get, session_path
from slipsurface.contract import satisfies_contract
from slipsurface.desktop.about import AboutDialog
from slipsurface.desktop.brand import application_icon, symbol_icon
from slipsurface.desktop.home import HomePage
from slipsurface.desktop.icons import module_icon
from slipsurface.desktop.profiles import profile
from slipsurface.desktop.results import ResultsPanel
from slipsurface.desktop.splash import BrandSplash
from slipsurface.desktop.theme import stylesheet
from slipsurface.desktop.updater import load_available_updates
from slipsurface.desktop.widgets import ModuleHeader, section_title

LOG = logging.getLogger(__name__)


def _say(language: str, en: str, tr: str) -> str:
    """One user-facing string in the interface language."""
    return tr if language == "tr" else en


def _number(text: str) -> float:
    """Parse a number typed into a table cell, tolerating a decimal comma.

    A lone ',' is a decimal comma ('1,5' becomes 1.5). When both separators
    appear, the rightmost one is taken as the decimal and the other as a
    thousands separator, so '1.234,5' and '1,234.5' both mean 1234.5.
    """
    cleaned = text.strip().replace("\u00a0", "")
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def _conditions_match(record: dict, values: dict) -> bool:
    """Interpret the three versions of existing schema visibility conditions."""
    shapes = record.get("shapes")
    if shapes and values.get("shape") not in shapes:
        return False
    when = record.get("when") or []
    if isinstance(when, dict):
        when = [{"key": key, "in": allowed} for key, allowed in when.items()]
    for condition in when:
        if not isinstance(condition, dict):
            continue
        accepted = condition.get("in", [])
        if values.get(condition.get("key")) not in accepted:
            return False
    return True


def _pretty_result(result: dict) -> str:
    if not isinstance(result, dict):
        return str(result)
    parts = []
    for name in ("headline", "text", "summary", "fs_text"):
        value = result.get(name)
        if value:
            parts.append(value if isinstance(value, str)
                         else json.dumps(value, ensure_ascii=False, indent=2, default=str))
    for name in ("warnings", "error"):
        value = result.get(name)
        if value:
            parts.append(f"{name.upper()}: {value}")
    if not parts:
        parts.append(json.dumps(result, ensure_ascii=False, indent=2, default=str)[:20000])
    return "\n\n".join(parts)



def _table_key(app_key: str, schema_name: str) -> str:
    """Map schema tab names to the module-specific project-data keys."""
    if schema_name == "soil":
        return "soil_profile"
    if schema_name == "lab":
        return "lab_data"
    if schema_name == "types":
        return "reinforcement_types"
    if app_key == "correlation":
        return {"spt": "spt_tests", "cpt": "cpt_tests", "vs": "vs_tests"}.get(
            schema_name, schema_name
        )
    if app_key == "kinematic" and schema_name == "screening":
        return "joints"
    return schema_name

class TaskSignals(QObject):
    finished = Signal(object, object)


class AnalysisTask(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = TaskSignals()

    def run(self):
        try:
            self.signals.finished.emit(self.operation(), None)
        except Exception as error:
            LOG.exception("Module analysis failed")
            self.signals.finished.emit(None, str(error))


class DataTable(QWidget):
    """Native soil/test/anchor/reinforcement input grid with typed editors.

    Choice columns store the engine's internal values, not translated labels.
    Duplicate/insert/delete operations retain the original project schema.
    """

    def __init__(self, specification: dict, rows: list, parent=None, language="tr"):
        super().__init__(parent)
        self.columns = specification.get("columns", [])
        self.language = language
        self.table = QTableWidget(self)
        self.table.setObjectName("suiteInputTable")
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([
            str(c.get("label", c.get("key", ""))) for c in self.columns
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(118)
        header.setMinimumSectionSize(70)
        for position, column in enumerate(self.columns):
            label = str(column.get("label", column.get("key", "")))
            # Keep full engineering column titles legible without forcing the
            # entire editor pane wider than the splitter; allow horizontal scroll.
            width = max(90, min(235, len(label) * 7 + 34))
            if column.get("kind") == "select":
                width = max(155, width)
            header.resizeSection(position, width)
            item = self.table.horizontalHeaderItem(position)
            if item is not None:
                item.setToolTip(label)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setMinimumHeight(245)

        add = QPushButton("+ Satır" if language == "tr" else "+ Row")
        add.setObjectName("suiteAddRow")
        duplicate = QPushButton("Çoğalt" if language == "tr" else "Duplicate")
        duplicate.setObjectName("suiteDuplicateRow")
        remove = QPushButton("Sil" if language == "tr" else "Remove")
        remove.setObjectName("suiteRemoveRow")
        add.clicked.connect(self.add_row)
        duplicate.clicked.connect(self.duplicate_selected)
        remove.clicked.connect(self.remove_selected)
        bar = QHBoxLayout()
        bar.addWidget(add)
        bar.addWidget(duplicate)
        bar.addWidget(remove)
        bar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(9)
        note = specification.get("note")
        if note:
            label = QLabel(str(note))
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addWidget(self.table)
        layout.addLayout(bar)
        self.set_rows(rows)

    def _append_row(self, row: dict):
        index = self.table.rowCount()
        self.table.insertRow(index)
        for col, spec in enumerate(self.columns):
            key = spec.get("key", "")
            kind = spec.get("kind", "text")
            value = row.get(key, "")
            if kind == "select" and spec.get("options"):
                editor = QComboBox()
                for option in spec["options"]:
                    editor.addItem(str(option.get("label", option.get("value", ""))),
                                   option.get("value"))
                found = editor.findData(value)
                if found >= 0:
                    editor.setCurrentIndex(found)
                elif value is not None and value != "":
                    # Preserve legacy/custom values rather than silently
                    # overwriting them with the first dropdown choice.
                    editor.addItem(str(value), value)
                    editor.setCurrentIndex(editor.count() - 1)
                self.table.setCellWidget(index, col, editor)
            elif kind == "check":
                editor = QCheckBox()
                editor.setChecked(bool(value))
                self.table.setCellWidget(index, col, editor)
            else:
                item = QTableWidgetItem("" if value is None else str(value))
                item.setToolTip(str(spec.get("label", key)))
                self.table.setItem(index, col, item)

    def add_row(self):
        self._append_row({})
        self.table.setCurrentCell(self.table.rowCount() - 1, 0)

    def duplicate_selected(self):
        index = self.table.currentRow()
        if index < 0:
            return
        source = self.rows()[index]
        self._append_row(source)
        self.table.setCurrentCell(self.table.rowCount() - 1, 0)

    def remove_selected(self):
        index = self.table.currentRow()
        if index >= 0:
            self.table.removeRow(index)

    def set_rows(self, rows: list):
        self.table.setRowCount(0)
        for row in rows:
            self._append_row(row if isinstance(row, dict) else {})

    def rows(self) -> list[dict]:
        result = []
        for index in range(self.table.rowCount()):
            row = {}
            for col, specification in enumerate(self.columns):
                key = specification.get("key", "")
                if not key:
                    continue
                kind = specification.get("kind", "text")
                editor = self.table.cellWidget(index, col)
                if kind == "select" and isinstance(editor, QComboBox):
                    row[key] = editor.currentData()
                    continue
                if kind == "check" and isinstance(editor, QCheckBox):
                    row[key] = editor.isChecked()
                    continue
                item = self.table.item(index, col)
                value = item.text().strip() if item else ""
                if kind == "number":
                    if value:
                        try:
                            row[key] = _number(value)
                        except ValueError as exc:
                            message = _say(
                                self.language,
                                f"Row {index + 1}: {key} must be numeric",
                                f"Satır {index + 1}: {key} alanı sayısal olmalı",
                            )
                            raise ValueError(message) from exc
                    else:
                        row[key] = 0.0
                elif kind == "check":
                    row[key] = value.lower() in ("true", "1", "yes", "evet")
                else:
                    row[key] = value
            result.append(row)
        return result


class FigurePreview(QLabel):
    """Aspect-preserving engineering image viewer inside the dark workspace.

    The raster is not modified. PDF/report output remains handled by the
    module's own report engine, not by the on-screen viewer.
    """

    def __init__(self, placeholder: str, parent=None):
        super().__init__(placeholder, parent)
        self.setObjectName("suitePlotCanvas")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._source_pixmap = QPixmap()

    def sizeHint(self) -> QSize:
        return QSize(420, 330)

    def pixmap(self) -> QPixmap:
        return QPixmap(self._source_pixmap)

    def setPixmap(self, pixmap: QPixmap) -> None:
        self._source_pixmap = QPixmap(pixmap)
        # Clear placeholder without letting QLabel's intrinsic pixmap size
        # force unwanted horizontal scrolling on a narrow results panel.
        super().setText("")
        self.update()

    def setText(self, text: str) -> None:
        self._source_pixmap = QPixmap()
        super().setText(text)
        self.update()

    def paintEvent(self, event) -> None:
        if self._source_pixmap.isNull():
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#262D39"))
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        usable = self.contentsRect().adjusted(12, 12, -12, -12)
        if usable.width() > 0 and usable.height() > 0:
            image_size = self._source_pixmap.size()
            image_size.scale(usable.size(), Qt.AspectRatioMode.KeepAspectRatio)
            origin_x = usable.x() + (usable.width() - image_size.width()) // 2
            origin_y = usable.y() + (usable.height() - image_size.height()) // 2
            painter.drawPixmap(origin_x, origin_y, self._source_pixmap.scaled(
                image_size, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        painter.end()


class ModulePage(QWidget):
    """One analysis module and its editable state in the shared main window."""

    def __init__(self, key: str, language: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.language = language
        adapter = importlib.import_module(session_path(key))
        factory = adapter.Session
        parameters = inspect.signature(factory).parameters
        if "lang" in parameters:
            self.session = factory(lang=language)
        elif "language" in parameters:
            self.session = factory(language=language)
        else:
            self.session = factory()
        if not satisfies_contract(self.session):
            raise TypeError(f"{key}: module session does not implement AppSession")
        if key == "kinematic":
            self.session.set_language(language)
            forms = importlib.import_module(forms_path(key))
            self.metadata = {"schema": forms.schema(), "defaults": forms.defaults(),
                             "figures": ["main"]}
        else:
            self.metadata = self.session.meta()
        self.data = copy.deepcopy(self.metadata["defaults"])
        self.fields = {}
        self.tables = {}
        self.conditional = []
        self.busy = False
        self.last_result = None
        self._task = None
        self._plot_target = "analysis"
        self._pending_plot_target = "analysis"
        self.profile = profile(key)
        # A direct ModulePage instantiation (e.g. plugin verification) must
        # render graphs in the single desktop theme, not the engine's legacy
        # default light figure palette.
        if hasattr(self.session, "set_theme"):
            self.session.set_theme("dark")

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 9, 10, 9)
        root.setSpacing(10)
        self.header = ModuleHeader(key, language)
        self.mode = None
        if key == "kinematic":
            self.mode = QComboBox()
            self.mode.addItems(["screening", "planar", "wedge", "toppling"])
            self.header.add_action(self.mode)
        self.run_button = QPushButton("Hesapla" if language == "tr" else "Analyze")
        self.run_button.setObjectName("suiteAnalyzeAction")
        self.run_button.clicked.connect(self.analyze)
        self.header.add_action(self.run_button)
        self._install_module_tools()
        root.addWidget(self.header)

        work = QSplitter(Qt.Horizontal)
        work.setObjectName("suiteEditorSplitter")
        work.setChildrenCollapsible(False)
        work.setHandleWidth(8)
        self.work_splitter = work
        self.input_tabs = QTabWidget()
        self.input_tabs.setDocumentMode(True)
        self._build_input_tabs()
        input_pane = QWidget()
        input_pane_layout = QVBoxLayout(input_pane)
        input_pane_layout.setContentsMargins(0, 0, 0, 0)
        input_pane_layout.setSpacing(6)
        self.section_hint = QLabel()
        self.section_hint.setObjectName("suiteSectionHint")
        self.section_hint.setWordWrap(True)
        input_pane_layout.addWidget(self.section_hint)
        input_pane_layout.addWidget(self.input_tabs, 1)
        self.input_tabs.currentChanged.connect(self._update_section_hint)
        primary = self.profile.primary_tab
        for index in range(self.input_tabs.count()):
            if self.input_tabs.tabText(index) == primary:
                self.input_tabs.setCurrentIndex(index)
                break
        self._update_section_hint()
        if self.mode is not None:
            self.mode.currentTextChanged.connect(self._mode_changed)
        input_pane.setMinimumWidth(310)
        work.addWidget(input_pane)

        right = QTabWidget()
        right.setMinimumWidth(320)
        self.overview = ResultsPanel(language)
        right.addTab(self.overview, "Özet" if language == "tr" else "Summary")
        self.result_text = QTextEdit()
        self.result_text.setObjectName("suiteResultDetails")
        self.result_text.setReadOnly(True)
        self.result_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.result_text.setPlaceholderText(
            "Hesaplama çıktıları bu panelde görüntülenir." if language == "tr"
            else "Analysis results will appear here."
        )
        right.addTab(self.result_text, "Ayrıntılar" if language == "tr" else "Details")
        plot_panel = QWidget()
        plot_panel.setObjectName("suitePlotPanel")
        figure_layout = QVBoxLayout(plot_panel)
        figure_layout.setContentsMargins(10, 12, 10, 10)
        figure_layout.setSpacing(10)
        figure_bar = QHBoxLayout()
        self.figure_choice = QComboBox()
        self.figure_choice.currentIndexChanged.connect(self.refresh_plot)
        figure_bar.addWidget(self.figure_choice, 1)
        plot_button = QPushButton("Grafiği yenile" if language == "tr" else "Refresh figure")
        plot_button.clicked.connect(self.refresh_plot)
        figure_bar.addWidget(plot_button)
        figure_layout.addLayout(figure_bar)
        scroll = QScrollArea()
        scroll.setObjectName("suitePlotScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.plot_label = FigurePreview(
            "Grafik oluşturmak için analizi çalıştırın."
            if language == "tr" else "Run an analysis to see figures."
        )
        self.plot_label.setAlignment(Qt.AlignCenter)
        self.plot_label.setMinimumHeight(350)
        scroll.setWidget(self.plot_label)
        figure_layout.addWidget(scroll)
        right.addTab(plot_panel, "Grafikler" if language == "tr" else "Figures")
        work.addWidget(right)
        # Let the graph/results pane use more space, while retaining
        # a user-adjustable divider for the parameter editor.
        work.setStretchFactor(0, 4)
        work.setStretchFactor(1, 6)
        work.setSizes([480, 720])
        root.addWidget(work, 1)
        self._update_visibility()

    def _install_module_tools(self):
        """Surface existing specialist engine operations without duplicating logic."""
        actions = {
            "pile": [("Kaya soketi" if self.language == "tr" else "Rock socket",
                       lambda: self.analyze(socket=True))],
            "msew": [("Katman üret" if self.language == "tr" else "Generate layers",
                       self._generate_layers)],
            "wall": [("Boyut öner" if self.language == "tr" else "Suggest dimensions",
                       self._suggest_dimensions)],
            "correlation": [
                ("Oturmaya aktar" if self.language == "tr" else "Export Settle",
                 lambda: self._export_correlation("settle")),
                ("Taşıma gücüne aktar" if self.language == "tr" else "Export Bearing",
                 lambda: self._export_correlation("bearing")),
            ],
        }
        self.special_buttons = []
        for label, callback in actions.get(self.key, []):
            button = QPushButton(label)
            button.setObjectName("suiteSpecialAction")
            button.clicked.connect(callback)
            self.header.add_action(button)
            self.special_buttons.append(button)

    def _update_section_hint(self, *_):
        current = self.input_tabs.tabText(self.input_tabs.currentIndex())
        hint = self.profile.hint_tr if self.language == "tr" else self.profile.hint_en
        self.section_hint.setText(f"{current}  ·  {hint}")

    def _mode_changed(self, mode: str):
        if self.key != "kinematic":
            return
        target = "Kinematik Tarama" if self.language == "tr" else "Screening"
        if mode != "screening":
            target = section_title(f"equilibrium:{mode}", self.language)
        for index in range(self.input_tabs.count()):
            if self.input_tabs.tabText(index) == target:
                self.input_tabs.setCurrentIndex(index)
                break

    def _generate_layers(self):
        if self.key != "msew":
            return
        answer = QMessageBox.question(
            self, "Katman üretimi" if self.language == "tr" else "Generate layers",
            "Mevcut donatı katmanları yeni yerleşimle değiştirilsin mi?"
            if self.language == "tr" else "Replace existing reinforcement layers?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            result = self.session.generate(self.current_values())
            layers = result["layers"]
            if not isinstance(layers, list):
                raise ValueError(_say(self.language, "Invalid layer layout",
                                      "Geçersiz katman düzeni"))
            self.tables["layers"].set_rows(layers)
            for i in range(self.input_tabs.count()):
                if self.input_tabs.tabText(i) == section_title("layers", self.language):
                    self.input_tabs.setCurrentIndex(i)
                    break
        except (ValueError, KeyError, TypeError) as error:
            QMessageBox.warning(
                self, _say(self.language, "Layer generation", "Katman üretimi"), str(error))

    def _suggest_dimensions(self):
        if self.key != "wall":
            return
        try:
            result = self.session.suggest(self.current_values())
            proposed = result["values"]
            values = self.current_values()
            for key, value in proposed.items():
                if key in self.fields:
                    values[key] = value
            self.apply_values(values)
            self._update_section_hint()
        except (ValueError, KeyError, TypeError) as error:
            QMessageBox.warning(
                self, _say(self.language, "Suggested dimensions", "Boyut önerisi"),
                str(error))

    def _export_correlation(self, target: str):
        if self.key != "correlation":
            return
        if self.last_result is None:
            QMessageBox.warning(
                self, _say(self.language, "Export", "Dışa aktar"),
                _say(self.language, "Run the correlation analysis first.",
                     "Önce korelasyon analizini çalıştırın."))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export project", f"{target}-from-correlation.json",
            "JSON projects (*.json)"
        )
        if path:
            try:
                payload = self.session.export(target)
                with open(path, "w", encoding="utf-8") as stream:
                    json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            except (ValueError, OSError, TypeError) as error:
                QMessageBox.warning(
                    self, _say(self.language, "Export", "Dışa aktar"), str(error))

    def _build_input_tabs(self):
        schema = self.metadata.get("schema", {})
        for name, specification in schema.items():
            if name == "study_vars":
                continue
            if name == "equilibrium" and self.key == "kinematic":
                for mode, section in specification.items():
                    self._add_section(section_title(f"equilibrium:{mode}", self.language), section, mode)
                continue
            if isinstance(specification, dict):
                self._add_section(section_title(name, self.language), specification, name)

    def _add_section(self, title: str, section: dict, name: str):
        page = QWidget()
        wrapper = QScrollArea()
        wrapper.setWidgetResizable(True)
        wrapper.setWidget(page)
        column = QVBoxLayout(page)
        column.setContentsMargins(12, 10, 12, 14)
        column.setSpacing(12)
        for group in section.get("groups", []):
            group_box = QGroupBox(group.get("title", "Inputs"))
            # Avoid form controls running across an ultra-wide input canvas.
            group_box.setMaximumWidth(710)
            form = QFormLayout(group_box)
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            form.setHorizontalSpacing(12)
            form.setVerticalSpacing(10)
            for field in group.get("fields", []):
                key = field.get("key")
                if not key:
                    continue
                value = self.data.get(key, field.get("default"))
                widget = self._field_widget(field, value)
                label = QLabel(field.get("label", key))
                label.setWordWrap(True)
                label.setMinimumWidth(128)
                label.setMaximumWidth(185)
                label.setToolTip(str(field.get("label", key)))
                unit = field.get("unit", "")
                box = QWidget()
                line = QHBoxLayout(box)
                line.setContentsMargins(0, 0, 0, 0)
                line.setSpacing(7)
                line.addWidget(widget, 1)
                if unit:
                    line.addWidget(QLabel(str(unit)))
                form.addRow(label, box)
                self.fields.setdefault(key, []).append((widget, name))
                self.conditional.append((label, box, field))
            self.conditional.append((group_box, None, group))
            column.addWidget(group_box)
        if "columns" in section:
            data_key = _table_key(self.key, name)
            initial = self.data.get(
                data_key, section.get("joints", section.get("rows", []))
            )
            table = DataTable(section, initial, language=self.language)
            self.tables[data_key] = table
            column.addWidget(table)
        column.addStretch(1)
        self.input_tabs.addTab(wrapper, title)

    def _field_widget(self, field: dict, value):
        kind = field.get("kind", "number")
        if kind == "check":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            widget.toggled.connect(self._update_visibility)
        elif kind == "select":
            widget = QComboBox()
            for option in field.get("options", []):
                widget.addItem(str(option.get("label", option.get("value", ""))),
                               option.get("value"))
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
            widget.currentIndexChanged.connect(self._update_visibility)
        elif kind == "number":
            widget = QDoubleSpinBox()
            lower = field.get("min")
            upper = field.get("max")
            widget.setRange(float(lower) if lower is not None else -1e12,
                            float(upper) if upper is not None else 1e12)
            widget.setDecimals(max(0, min(10, int(field.get("decimals", 3)))))
            widget.setSingleStep(float(field.get("step") or 0.1))
            widget.setValue(float(value or 0))
            widget.valueChanged.connect(self._update_visibility)
        else:
            widget = QLineEdit(str(value or ""))
            widget.textChanged.connect(self._update_visibility)
        return widget

    @staticmethod
    def _read_widget(widget):
        if isinstance(widget, QDoubleSpinBox):
            return widget.value()
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QComboBox):
            return widget.currentData()
        return widget.text()

    def _widget_for(self, key: str):
        """The widget that currently speaks for a field.

        A field may occur in several kinematic modes; the active mode's
        widget is preferred, so a field is never read from, or its
        visibility judged by, another mode's editor.
        """
        widgets = self.fields.get(key)
        if not widgets:
            return None
        chosen = widgets[0][0]
        if self.mode is not None:
            active_mode = self.mode.currentText()
            matching = [w for w, section in widgets if section.endswith(active_mode)]
            if matching:
                chosen = matching[-1]
        return chosen

    def current_values(self) -> dict:
        values = copy.deepcopy(self.data)
        for key in self.fields:
            chosen = self._widget_for(key)
            if chosen is not None:
                values[key] = self._read_widget(chosen)
        for key, table in self.tables.items():
            values[key] = table.rows()
        return values

    def _update_visibility(self, *_):
        if not hasattr(self, "conditional"):
            return
        values = copy.deepcopy(self.data)
        for key in self.fields:
            chosen = self._widget_for(key)
            if chosen is not None:
                values[key] = self._read_widget(chosen)
        for label, field, specification in self.conditional:
            visible = _conditions_match(specification, values)
            label.setVisible(visible)
            if field is not None:
                field.setVisible(visible)

    def apply_values(self, values: dict):
        self.data = copy.deepcopy(values)
        for key, widgets in self.fields.items():
            if key not in values:
                continue
            for widget, _ in widgets:
                value = values[key]
                if isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value or 0))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QComboBox):
                    index = widget.findData(value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                else:
                    widget.setText(str(value or ""))
        for key, table in self.tables.items():
            table.set_rows(values.get(key, []))
        self._update_visibility()

    def analyze(self, *_, socket=False):
        if self.busy:
            return
        try:
            values = self.current_values()
        except ValueError as error:
            QMessageBox.warning(self, _say(self.language, "Invalid input",
                                           "Geçersiz girdi"), str(error))
            return
        self.data = copy.deepcopy(values)
        self.busy = True
        self._pending_plot_target = "socket" if socket and self.key == "pile" else "analysis"
        self.run_button.setEnabled(False)
        for button in self.special_buttons:
            button.setEnabled(False)
        self.result_text.setPlainText("Hesaplanıyor…" if self.language == "tr"
                                      else "Calculating…")
        # Qt widgets belong to the GUI thread: read everything the worker
        # needs here, before the operation runs on the thread pool.
        active_mode = self.mode.currentText() if self.mode is not None else None

        def operation():
            if self.key == "kinematic":
                if active_mode == "screening":
                    return self.session.screen(values)
                return self.session.equilibrium(active_mode, values)
            if self._pending_plot_target == "socket":
                return self.session.analyse_socket(values)
            return self.session.analyse(values)

        self._task = AnalysisTask(operation)
        self._task.signals.finished.connect(self._on_analysis_finished)
        QThreadPool.globalInstance().start(self._task)

    def _on_analysis_finished(self, result, error):
        self.busy = False
        self.run_button.setEnabled(True)
        for button in self.special_buttons:
            button.setEnabled(True)
        self._task = None
        if error:
            self.overview.dashboard.clear_results()
            self.result_text.setPlainText(
                _say(self.language, "Analysis failed:\n", "Analiz başarısız oldu:\n") + error)
            QMessageBox.warning(self, _say(self.language, "Analysis error",
                                           "Analiz hatası"), error)
            return
        if isinstance(result, dict) and result.get("ok") is False:
            self.overview.dashboard.clear_results()
            self.result_text.setPlainText(str(result.get(
                "error", _say(self.language, "Analysis not completed",
                              "Analiz tamamlanmadı"))))
            return
        self.last_result = result
        self._plot_target = self._pending_plot_target
        if isinstance(result, dict):
            self.overview.dashboard.update_results(result)
        self.result_text.setPlainText(_pretty_result(result))
        figures = result.get("figures", []) if isinstance(result, dict) else []
        if not figures:
            figures = self.metadata.get("figures", [])
        if isinstance(figures, dict):
            figures = list(figures)
        self.figure_choice.blockSignals(True)
        self.figure_choice.clear()
        labels = self.metadata.get("figure_labels", {})
        for figure in figures:
            if isinstance(figure, str):
                self.figure_choice.addItem(str(labels.get(figure, figure)), figure)
        self.figure_choice.blockSignals(False)
        self.refresh_plot()

    def refresh_plot(self, *_):
        kind = self.figure_choice.currentData()
        if not kind or self.last_result is None:
            return
        try:
            if self.key in {"wall", "correlation"}:
                data = self.session.plot(kind)
            elif self.key == "kinematic":
                target = "screening" if self.mode.currentText() == "screening" else "equilibrium"
                data = self.session.plot(target, kind)
            else:
                data = self.session.plot(self._plot_target, kind)
            pixmap = QPixmap()
            if not pixmap.loadFromData(data, "PNG"):
                raise ValueError(_say(self.language, "Invalid PNG returned from analysis",
                                       "Analizden geçersiz PNG döndü"))
            # Keep the original figure, not a resized copy: reflow at paint
            # time after splitter moves or window resizing, without blur/crop.
            self.plot_label.setPixmap(pixmap)
        except Exception as error:
            LOG.exception("Unable to draw figure")
            self.plot_label.setText(str(error))

    def save_project(self, path: str):
        values = self.current_values()
        if self.key == "kinematic":
            payload = {"format": "slipsurface-kinematic-suite", "values": values}
        else:
            payload = self.session.project_file(values)
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        self.data = copy.deepcopy(values)

    def open_project(self, path: str):
        with open(path, encoding="utf-8") as stream:
            payload = json.load(stream)
        if self.key == "kinematic":
            if payload.get("format") != "slipsurface-kinematic-suite":
                raise ValueError(_say(self.language, "Not a Kinematic Suite project",
                                      "Bu dosya bir Kinematic Suite projesi değil"))
            values = payload["values"]
        else:
            loaded = self.session.load_project(payload)
            if loaded.get("ok") is False:
                raise ValueError(str(loaded.get("error")))
            values = loaded["values"]
        if not isinstance(values, dict):
            raise TypeError(_say(self.language, "Project contents are invalid",
                                 "Proje içeriği geçersiz"))
        self.apply_values(values)

    def export_pdf(self, path: str):
        if self.last_result is None:
            raise ValueError(_say(self.language, "First run an analysis",
                                  "Önce bir analiz çalıştırın"))
        if self.key == "kinematic":
            kind = "screening" if self.mode.currentText() == "screening" else "equilibrium"
            self.session.report(kind, path)
        else:
            self.session.report("pdf", path)


class MainWindow(QMainWindow):
    def __init__(self, language="tr", theme="dark", initial_app=None):
        super().__init__()
        self.language = language
        # The single Nordic Dark theme replaces both legacy display modes.
        self.theme = "dark"
        self.pages = {}
        self._update_task = None
        self._catalogue_task = None
        self.setWindowTitle(f"{APP_NAME}  ·  {__version__}")
        self.setWindowIcon(application_icon())
        self.resize(1480, 900)
        self.setMinimumSize(950, 600)
        self._create_actions()

        # The launchpad occupies the full window until the user picks a module.
        # Release catalogues are optional, so this stays quiet when offline.
        self.available_updates = load_available_updates()
        self.stack = QStackedWidget()
        self.home = HomePage(language, self.available_updates)
        self.home.module_selected.connect(self.open_module)
        self.home.update_requested.connect(self.install_update)
        self.stack.addWidget(self.home)

        self.workspace = QWidget()
        workspace_layout = QVBoxLayout(self.workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        navigation_frame = QFrame()
        navigation_frame.setObjectName("suiteWorkspaceToolbar")
        navigation_frame.setFixedHeight(54)
        navigation = QHBoxLayout(navigation_frame)
        navigation.setContentsMargins(12, 7, 12, 7)
        navigation.setSpacing(7)
        self.toolbar_brand_mark = QLabel()
        self.toolbar_brand_mark.setObjectName("suiteToolbarMark")
        self.toolbar_brand_mark.setFixedSize(25, 34)
        self.toolbar_brand_mark.setAlignment(Qt.AlignCenter)
        self.toolbar_brand_mark.setPixmap(symbol_icon().pixmap(25, 34))
        self.toolbar_brand_mark.setToolTip("SlipSurfaceIQ")
        navigation.addWidget(self.toolbar_brand_mark)
        self.toolbar_brand = QLabel("SlipSurfaceIQ")
        self.toolbar_brand.setObjectName("suiteToolbarBrand")
        navigation.addWidget(self.toolbar_brand)
        navigation.addSpacing(12)
        self.back_button = QPushButton()
        self.back_button.setObjectName("suiteHomeBack")
        self.back_button.clicked.connect(self.show_home)
        navigation.addWidget(self.back_button)
        navigation.addStretch(1)
        self.check_updates_button = QPushButton()
        self.check_updates_button.setObjectName("suiteCheckUpdates")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        navigation.addWidget(self.check_updates_button)

        # Language remains configurable; color theme is deliberately fixed.
        self.language_button = QPushButton()
        self.language_button.setObjectName("suiteLanguageSwitch")
        self.language_button.clicked.connect(self.toggle_language)
        navigation.addWidget(self.language_button)
        navigation.addSpacing(12)
        self.toolbar_actions = {}
        for key, caption, callback in (
            ("new", "Yeni" if language == "tr" else "New", self.new_project),
            ("open", "Aç" if language == "tr" else "Open", self.open_project),
            ("save", "Kaydet" if language == "tr" else "Save", self.save_project),
            ("pdf", "PDF", self.export_pdf),
        ):
            button = QPushButton(caption)
            button.setObjectName("suiteDocumentAction")
            button.clicked.connect(callback)
            navigation.addWidget(button)
            self.toolbar_actions[key] = button
        self._update_shell_labels()

        layout = QSplitter(Qt.Horizontal)
        self.navigator = QListWidget()
        self.navigator.setMinimumWidth(180)
        self.navigator.setMaximumWidth(285)
        self._build_navigator()
        self.navigator.currentItemChanged.connect(self._navigate)
        layout.addWidget(self.navigator)
        self.view = QTabWidget()
        self.view.setTabsClosable(False)
        layout.addWidget(self.view)
        layout.setStretchFactor(1, 1)
        workspace_layout.addWidget(layout)
        self.stack.addWidget(self.workspace)
        # A single global toolbar keeps Home/Language reachable on all pages.
        shell = QWidget()
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(9, 8, 9, 8)
        shell_layout.setSpacing(8)
        shell_layout.addWidget(navigation_frame)
        shell_layout.addWidget(self.stack, 1)
        self.setCentralWidget(shell)
        self.shell_header = navigation_frame

        self.set_theme("dark")
        self.show_home()
        if initial_app is not None:
            self.open_module(initial_app)

    def _create_actions(self):
        self.menuBar().clear()
        file_menu = self.menuBar().addMenu("Dosya" if self.language == "tr" else "File")
        actions = [
            ("Yeni" if self.language == "tr" else "New", self.new_project, "Ctrl+N"),
            ("Aç…" if self.language == "tr" else "Open…", self.open_project, "Ctrl+O"),
            ("Kaydet…" if self.language == "tr" else "Save…", self.save_project, "Ctrl+S"),
            ("PDF aktar…" if self.language == "tr" else "Export PDF…", self.export_pdf, "Ctrl+E"),
        ]
        self.project_actions = []
        for title, callback, shortcut in actions:
            action = QAction(title, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            file_menu.addAction(action)
            self.project_actions.append(action)
        file_menu.addSeparator()
        exit_action = QAction("Çıkış" if self.language == "tr" else "Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("Görünüm" if self.language == "tr" else "View")
        home_action = QAction("Ana ekran" if self.language == "tr" else "Home", self)
        home_action.setShortcut("Alt+Home")
        home_action.triggered.connect(self.show_home)
        view_menu.addAction(home_action)
        language_action = QAction(
            "English / Türkçe" if self.language == "tr" else "Türkçe / English", self
        )
        language_action.triggered.connect(self.toggle_language)
        view_menu.addAction(language_action)

        help_menu = self.menuBar().addMenu(
            "Yardım" if self.language == "tr" else "Help"
        )
        self.about_action = QAction(
            "SlipSurfaceIQ Hakkında" if self.language == "tr"
            else "About SlipSurfaceIQ", self
        )
        self.about_action.setObjectName("suiteAboutAction")
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

    def show_about(self):
        """Display licensing and dependency credits in a native dialog."""
        dialog = AboutDialog(self.language, self)
        dialog.exec()

    def _sync_actions(self):
        enabled = self.current_page() is not None
        for action in self.project_actions:
            action.setEnabled(enabled)
        for button in self.toolbar_actions.values():
            button.setEnabled(enabled)

    def _update_shell_labels(self):
        """Re-translate the navigation buttons without changing their actions."""
        self.back_button.setText(_say(self.language, "⌂  Home", "⌂  Ana Sayfa"))
        self.back_button.setToolTip(_say(
            self.language, "Return to all applications", "Tüm programlara dön"
        ))
        self.language_button.setText(
            "EN · English" if self.language == "tr" else "TR · Türkçe"
        )
        self.language_button.setToolTip(
            "Switch to English / İngilizceye geç" if self.language == "tr"
            else "Switch to Turkish / Türkçeye geç"
        )
        captions = {
            "new": _say(self.language, "New", "Yeni"),
            "open": _say(self.language, "Open", "Aç"),
            "save": _say(self.language, "Save", "Kaydet"),
            "pdf": "PDF",
        }
        for key, button in self.toolbar_actions.items():
            button.setText(captions[key])
        self.check_updates_button.setText(_say(
            self.language, "↻  Check updates", "↻  Güncellemeleri kontrol et"
        ))
        self.check_updates_button.setToolTip(_say(
            self.language,
            "Check new versions of individual modules on GitHub",
            "GitHub'daki modül güncellemelerini kontrol et",
        ))
    def toggle_language(self, *_):
        self.set_language("en" if self.language == "tr" else "tr")

    def set_language(self, language: str) -> bool:
        """Relocalize Qt editors while retaining inputs, sessions and results."""
        if language not in {"tr", "en"}:
            raise ValueError(f"Unsupported language: {language}")
        if language == self.language:
            return True
        if any(page.busy for page in self.pages.values()) or self._update_task is not None:
            QMessageBox.information(
                self, _say(self.language, "Task in progress", "İşlem sürüyor"),
                _say(self.language,
                     "Finish the analysis or update before changing language.",
                     "Dili değiştirmeden önce analiz veya güncellemeyi tamamlayın."),
            )
            return False

        replacements = {}
        try:
            for key, old in self.pages.items():
                values = old.current_values()
                page = ModulePage(key, language)
                replacements[key] = page
                page.apply_values(copy.deepcopy(values))
                if old.mode is not None:
                    page.mode.setCurrentText(old.mode.currentText())
                page.input_tabs.setCurrentIndex(old.input_tabs.currentIndex())
                # Keep the original engine session (results, plots and PDF export).
                page.session = old.session
                page.data = copy.deepcopy(old.data)
                page.last_result = old.last_result
                page._plot_target = old._plot_target
                page._pending_plot_target = old._pending_plot_target
                if old.last_result is not None:
                    if isinstance(old.last_result, dict):
                        page.overview.dashboard.update_results(old.last_result)
                    page.result_text.setPlainText(old.result_text.toPlainText())
                    labels = page.metadata.get("figure_labels", {})
                    for index in range(old.figure_choice.count()):
                        figure_key = old.figure_choice.itemData(index)
                        caption = old.figure_choice.itemText(index)
                        page.figure_choice.addItem(
                            str(labels.get(figure_key, caption)), figure_key
                        )
                    page.figure_choice.setCurrentIndex(old.figure_choice.currentIndex())
                    pixmap = old.plot_label.pixmap()
                    if pixmap is not None and not pixmap.isNull():
                        page.plot_label.setPixmap(pixmap)
                if hasattr(page.session, "set_language"):
                    page.session.set_language(language)
                if hasattr(page.session, "set_theme"):
                    page.session.set_theme(self.theme)
        except Exception as error:
            for page in replacements.values():
                page.deleteLater()
            LOG.exception("Unable to change UI language")
            QMessageBox.warning(
                self, _say(self.language, "Language change failed", "Dil değiştirilemedi"),
                str(error),
            )
            return False

        showing_home = self.stack.currentWidget() is self.home
        active = self.view.currentWidget()
        active_key = active.key if isinstance(active, ModulePage) else None
        for key, old in self.pages.items():
            index = self.view.indexOf(old)
            if index >= 0:
                self.view.removeTab(index)
                name = get(key).tr if language == "tr" else get(key).name
                self.view.insertTab(index, replacements[key], module_icon(key), name)
            old.deleteLater()
        self.pages = replacements
        self.language = language
        self._create_actions()
        self._update_shell_labels()
        self._build_navigator()
        self._replace_home()
        if active_key is not None:
            page = self.pages.get(active_key)
            if page is not None:
                self.view.setCurrentWidget(page)
                self.navigator.blockSignals(True)
                for index in range(self.navigator.count()):
                    if self.navigator.item(index).data(Qt.UserRole) == active_key:
                        self.navigator.setCurrentRow(index)
                        break
                self.navigator.blockSignals(False)
        if showing_home:
            self.show_home()
        else:
            self.stack.setCurrentWidget(self.workspace)
            self._sync_actions()
        return True

    def _replace_home(self):
        new_home = HomePage(self.language, self.available_updates)
        new_home.module_selected.connect(self.open_module)
        new_home.update_requested.connect(self.install_update)
        self.stack.removeWidget(self.home)
        self.home.deleteLater()
        self.stack.insertWidget(0, new_home)
        self.home = new_home

    def _build_navigator(self):
        """(Re)fill the module list from the current catalogue."""
        self.navigator.blockSignals(True)
        self.navigator.clear()
        for module in app_catalogue.catalogue():
            item = QListWidgetItem(module.tr if self.language == "tr" else module.name)
            item.setData(Qt.UserRole, module.key)
            item.setToolTip(
                module.description_tr if self.language == "tr" else module.description
            )
            item.setIcon(module_icon(module.key))
            self.navigator.addItem(item)
        self.navigator.blockSignals(False)
        self.navigator.setCurrentRow(-1)

    def check_for_updates(self, *_):
        """Fetch public module releases off-thread; keep the desktop responsive."""
        if self._catalogue_task is not None or self._update_task is not None:
            return
        self.check_updates_button.setEnabled(False)
        self.statusBar().showMessage(_say(
            self.language, "Checking module updates…", "Modül güncellemeleri kontrol ediliyor…"
        ))
        self._catalogue_task = AnalysisTask(
            lambda: load_available_updates(include_remote=True)
        )
        self._catalogue_task.signals.finished.connect(self._updates_checked)
        QThreadPool.globalInstance().start(self._catalogue_task)

    def _updates_checked(self, updates, error):
        self._catalogue_task = None
        self.check_updates_button.setEnabled(True)
        if error is not None:
            LOG.warning("Module update check failed: %s", error)
            self.statusBar().showMessage(_say(
                self.language, "Update check unavailable", "Güncelleme kontrolü yapılamadı"
            ))
            return
        if not isinstance(updates, dict):
            return
        # An installation may have completed while the catalogue was fetched.
        self.available_updates = {
            key: update for key, update in updates.items()
            if key in app_catalogue.keys()
            and app_catalogue.get(key).version == update.installed
        }
        was_home = self.stack.currentWidget() is self.home
        self._replace_home()
        if was_home:
            self.show_home()
        count = len(self.available_updates)
        self.statusBar().showMessage(_say(
            self.language, f"{count} module update(s) available",
            f"{count} modül için güncelleme mevcut",
        ))

    def install_update(self, key: str):
        """Download and install one module release in a background thread."""
        if self._update_task is not None:
            QMessageBox.information(
                self, "Update", _say(self.language,
                    "Another module update is still in progress.",
                    "Başka bir modülün güncellemesi devam ediyor."))
            return
        update = self.available_updates.get(key)
        if update is None or not update.url or not update.sha256:
            QMessageBox.information(
                self,
                _say(self.language, "No downloadable release", "İndirilebilir sürüm yok"),
                _say(
                    self.language,
                    f"{get(key).name}: the release catalogue does not name an archive for this update.",
                    f"{get(key).name}: sürüm kataloğu bu güncelleme için bir arşiv belirtmiyor.",
                ),
            )
            return
        name = get(key).name
        answer = QMessageBox.question(
            self,
            _say(self.language, "Install update", "Güncellemeyi kur"),
            _say(
                self.language,
                f"Download {name} {update.installed} → {update.latest} and install it for this Suite?",
                f"{name} {update.installed} → {update.latest} indirilip bu Suite için kurulsun mu?",
            ),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        # Never unload Python classes still serving a background analysis,
        # and never discard a live editor without first saving its project.
        active_page = self.pages.get(key)
        if active_page is not None:
            if active_page.busy:
                QMessageBox.warning(
                    self, _say(self.language, "Analysis running", "Hesaplama sürüyor"),
                    _say(self.language,
                        "Finish the running analysis before updating this module.",
                        "Bu modülü güncellemeden önce hesaplamanın tamamlanmasını bekleyin."))
                return
            path, _ = QFileDialog.getSaveFileName(
                self, _say(self.language, "Save open project before update",
                           "Güncellemeden önce açık projeyi kaydedin"),
                f"{key}-before-update.json", "JSON projects (*.json)"
            )
            if not path:
                return
            try:
                active_page.save_project(path)
            except Exception as error:
                QMessageBox.warning(
                    self, _say(self.language, "Project save failed", "Proje kaydedilemedi"),
                    str(error))
                return
        self.statusBar().showMessage(
            _say(self.language, f"Downloading {name}…", f"{name} indiriliyor…")
        )
        record = {
            "key": key,
            "version": update.latest,
            "url": update.url,
            "requires_core": update.requires_core,
            "sha256": update.sha256,
        }

        def run_install():
            from slipsurface import installer

            return installer.install_release(record, retain_backup=True)

        self._update_task = AnalysisTask(run_install)
        self.workspace.setEnabled(False)
        self.home.setEnabled(False)
        self._update_task.signals.finished.connect(self._update_installed)
        QThreadPool.globalInstance().start(self._update_task)

    def _verify_updated_module(self, key: str):
        """Try the new native page while the previous release still exists.

        The installer first checks Session/meta in an isolated subprocess.
        This second check catches actual PySide6 page-construction failures.
        Only a fully initialized page allows deletion of the backup.
        """
        app_catalogue.refresh()
        session = app_catalogue.get(key).session
        root_package = session.removesuffix(".web.session")
        for module_name in list(sys.modules):
            if module_name == root_package or module_name.startswith(root_package + "."):
                del sys.modules[module_name]
        importlib.invalidate_caches()
        page = ModulePage(key, self.language)
        try:
            if hasattr(page.session, "set_theme"):
                page.session.set_theme(self.theme)
            page.current_values()
        finally:
            page.deleteLater()

    def _update_installed(self, result, error):
        self.workspace.setEnabled(True)
        self.home.setEnabled(True)
        self._update_task = None
        if error is not None or not isinstance(result, dict):
            LOG.error("Module update failed: %s", error)
            QMessageBox.warning(
                self,
                _say(self.language, "Update failed", "Güncelleme başarısız"),
                _say(
                    self.language,
                    f"The release could not be installed: {error}",
                    f"Sürüm kurulamadı: {error}",
                ),
            )
            return

        from slipsurface import installer

        key = result["key"]
        installed_version = result["version"]
        try:
            self._verify_updated_module(key)
        except Exception as exc:
            LOG.exception("New module failed native activation: %s", key)
            rollback_issue = ""
            try:
                installer.rollback_release(key, expected_version=installed_version)
            except Exception as rollback_error:
                LOG.exception("Rollback failed for module %s", key)
                rollback_issue = f"\nRollback also failed: {rollback_error}"
            finally:
                # The previous page is retained; rediscovery removes bad
                # session modules from the candidate import path.
                app_catalogue.refresh()
                importlib.invalidate_caches()
            QMessageBox.warning(
                self,
                _say(self.language, "Module reverted", "Modül geri alındı"),
                _say(
                    self.language,
                    f"The updated module failed to open. The previous release was restored.\n{exc}",
                    f"Güncellenen modül açılamadı. Önceki sürüme geri dönüldü.\n{exc}",
                ) + rollback_issue,
            )
            return

        # An inability to remove a locked backup must never turn an already
        # running and verified module into a failed installation.
        try:
            installer.finalize_release(key, expected_version=installed_version)
        except (OSError, installer.InstallError):
            LOG.warning("Update works, but previous release backup remains for %s", key)
        name = get(key).name if key in app_catalogue.keys() else key
        self.statusBar().showMessage(
            _say(self.language, f"{name} {installed_version} installed",
                 f"{name} {installed_version} kuruldu")
        )
        self._refresh_after_update(key)
        QMessageBox.information(
            self,
            _say(self.language, "Update installed", "Güncelleme kuruldu"),
            _say(
                self.language,
                f"{name} has been updated to {installed_version}.",
                f"{name} uygulaması {installed_version} sürümüne güncellendi.",
            ),
        )

    def _refresh_after_update(self, key: str):
        """Rebuild catalogue, launchpad and navigator after an install."""
        app_catalogue.refresh()
        # Drop cached imports of the installed package so the next open runs
        # the code that was just unpacked, not the previous release.
        session = app_catalogue.get(key).session
        if session:
            root_package = session.removesuffix(".web.session")
            for module_name in [
                name for name in sys.modules
                if name == root_package or name.startswith(f"{root_package}.")
            ]:
                del sys.modules[module_name]
        # The release directory was swapped by a rename; finders may still
        # hold the old directory listing.
        importlib.invalidate_caches()
        # Preserve other remote offers; the just-installed version is no
        # longer newer and must disappear from its launchpad card.
        self.available_updates.pop(key, None)
        stale = self.pages.pop(key, None)
        if stale is not None:
            index = self.view.indexOf(stale)
            if index >= 0:
                self.view.removeTab(index)
            stale.deleteLater()
        self._build_navigator()
        self._replace_home()
        self.show_home()

    def set_theme(self, theme: str = "dark"):
        """Compatibility API: always use Nordic Dark, including legacy 'light' callers."""
        self.theme = "dark"
        QApplication.instance().setStyleSheet(stylesheet())
        for page in self.pages.values():
            if hasattr(page.session, "set_theme"):
                page.session.set_theme(self.theme)

    def show_home(self):
        self.stack.setCurrentWidget(self.home)
        self.statusBar().showMessage(
            "Program seçin" if self.language == "tr" else "Choose an application"
        )
        self._sync_actions()

    def open_module(self, key: str):
        """Open a card's module, retaining existing page state on return."""
        if key not in app_catalogue.keys():
            raise KeyError(f"Unknown module: {key}")
        for index in range(self.navigator.count()):
            item = self.navigator.item(index)
            if item.data(Qt.UserRole) == key:
                if self.navigator.currentRow() != index:
                    self.navigator.setCurrentRow(index)
                else:
                    self._navigate(item, None)
                return

    def _navigate(self, current, _previous):
        if current is None:
            return
        key = current.data(Qt.UserRole)
        if key not in self.pages:
            try:
                page = ModulePage(key, self.language)
                if hasattr(page.session, "set_theme"):
                    page.session.set_theme(self.theme)
            except Exception as error:
                LOG.exception("Failed to load module %s", key)
                QMessageBox.critical(
                    self, _say(self.language, "Module load error", "Modül yükleme hatası"),
                    f"{key}: {error}")
                return
            self.pages[key] = page
            name = get(key).tr if self.language == "tr" else get(key).name
            self.view.addTab(page, module_icon(key), name)
        self.view.setCurrentWidget(self.pages[key])
        self.stack.setCurrentWidget(self.workspace)
        self.statusBar().showMessage(f"Module: {get(key).name}")
        self._sync_actions()

    def current_page(self):
        if self.stack.currentWidget() is not self.workspace:
            return None
        widget = self.view.currentWidget()
        return widget if isinstance(widget, ModulePage) else None

    def new_project(self):
        page = self.current_page()
        if page:
            page.apply_values(copy.deepcopy(page.metadata["defaults"]))

    def open_project(self):
        page = self.current_page()
        if not page:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open project", "", "JSON projects (*.json);;All files (*)"
        )
        if filename:
            try:
                page.open_project(filename)
                self.statusBar().showMessage(f"Opened: {filename}")
            except Exception as error:
                QMessageBox.warning(
                    self, _say(self.language, "Could not open project", "Proje açılamadı"),
                    str(error))

    def save_project(self):
        page = self.current_page()
        if not page:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save project", f"{page.key}-project.json", "JSON projects (*.json)"
        )
        if filename:
            try:
                page.save_project(filename)
                self.statusBar().showMessage(f"Saved: {filename}")
            except Exception as error:
                QMessageBox.warning(
                    self, _say(self.language, "Could not save project", "Proje kaydedilemedi"),
                    str(error))

    def export_pdf(self):
        page = self.current_page()
        if not page:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", f"{page.key}-report.pdf", "PDF files (*.pdf)"
        )
        if filename:
            try:
                page.export_pdf(filename)
                self.statusBar().showMessage(f"PDF exported: {filename}")
            except Exception as error:
                QMessageBox.warning(
                    self, _say(self.language, "Could not export PDF", "PDF dışa aktarılamadı"),
                    str(error))



def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="SlipSurfaceIQ Suite native PySide6 desktop")
    parser.add_argument("--lang", choices=("tr", "en"), default="tr")
    parser.add_argument("--theme", choices=("dark",), default="dark",
                        help="Nordic Dark is the only supported application theme")
    parser.add_argument("--app", choices=app_catalogue.keys(), default=None,
                        help="Open a module directly instead of the home dashboard")
    parser.add_argument(
        "--no-splash", action="store_true",
        help="Skip the branded startup screen (also automatic for headless Qt)"
    )
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setStyle("Fusion")
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(application_icon())
    splash = None
    if (
        args.app is None
        and not args.no_splash
        and not os.environ.get("SLIPSURFACE_NO_SPLASH")
        and app.platformName().lower() not in {"offscreen", "minimal"}
    ):
        splash = BrandSplash(args.lang)
        splash.show()
        app.processEvents()

    window = MainWindow(args.lang, "dark", args.app)
    # Startup checks must not block the Qt GUI thread and are disabled in
    # headless environments used by CI and native screenshot automation.
    if (not os.environ.get("SLIPSURFACE_DISABLE_UPDATE_CHECK")
            and app.platformName().lower() not in {"offscreen", "minimal"}):
        QTimer.singleShot(0, window.check_for_updates)
    if splash is None:
        window.show()
    else:
        def present_workspace():
            window.show()
            splash.finish(window)

        QTimer.singleShot(850, present_workspace)
    return app.exec()
