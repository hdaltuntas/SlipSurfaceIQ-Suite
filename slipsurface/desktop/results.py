"""Shared native engineering results view for all ten modules.

Uses structured result cards and tables from calculation sessions without
changing calculations or interpreting check states as engineering approval.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


def _string(value: object) -> str:
    return "—" if value is None else str(value)


def result_tables(result: dict) -> list[dict]:
    """Collect only known row/column table payloads from every engine."""
    tables = []
    for key in (
        "table", "tables", "methods", "tests", "external", "bearing",
        "layers", "seismic_layers", "stability", "forces", "seismic",
        "design", "schedule",
    ):
        value = result.get(key)
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if not isinstance(candidate.get("columns"), list):
                continue
            if not isinstance(candidate.get("rows"), list):
                continue
            tables.append(candidate)
    return tables


class MetricCard(QFrame):
    """One KPI from the analysis engine, with an optional engineering status."""

    def __init__(self, card: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("suiteResultCard")
        self.setProperty("checkState", str(card.get("state") or "neutral"))
        self.setMinimumHeight(108)
        self.setAccessibleName(_string(card.get("title") or card.get("key") or "Result"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 11)
        layout.setSpacing(5)
        title = QLabel(_string(card.get("title") or card.get("key") or "Result"))
        title.setObjectName("suiteMetricTitle")
        title.setWordWrap(True)
        value = QLabel(_string(card.get("value")))
        value.setObjectName("suiteMetricValue")
        value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        value.setWordWrap(True)
        detail = QLabel(_string(card.get("sub")) if card.get("sub") else "")
        detail.setObjectName("suiteMetricDetail")
        detail.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(value)
        layout.addWidget(detail)
        self.title_label = title
        self.value_label = value


class ResultDashboard(QWidget):
    """Results shown as cards, warnings and tables with native Qt controls."""

    def __init__(self, language: str = "tr", parent=None):
        super().__init__(parent)
        self.language = language
        self.metrics: list[MetricCard] = []
        self.tables: list[QTableWidget] = []
        self.setObjectName("suiteResultsOverview")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(12)
        self.heading = QLabel("Analiz Özeti" if language == "tr" else "Analysis Summary")
        self.heading.setObjectName("suiteResultsHeading")
        self.layout.addWidget(self.heading)
        self.headline = QLabel()
        self.headline.setWordWrap(True)
        self.headline.setObjectName("suiteResultsHeadline")
        self.layout.addWidget(self.headline)
        self.warning_label = QLabel()
        self.warning_label.setObjectName("suiteResultWarnings")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        self.layout.addWidget(self.warning_label)
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(14)
        self.layout.addWidget(self.body)
        self.layout.addStretch(1)

    def clear_results(self):
        self.headline.clear()
        self.warning_label.clear()
        self.warning_label.hide()
        for i in reversed(range(self.body_layout.count())):
            item = self.body_layout.takeAt(i)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.metrics = []
        self.tables = []

    def update_results(self, result: dict):
        self.clear_results()
        self.headline.setText(_string(result.get("headline") or ""))
        warnings = result.get("warnings") or []
        if isinstance(warnings, str):
            warnings = [warnings]
        if warnings:
            prefix = "Uyarılar" if self.language == "tr" else "Warnings"
            self.warning_label.setText(prefix + ":\n" + "\n".join(
                "• " + _string(w) for w in warnings
            ))
            self.warning_label.show()
        cards = result.get("cards")
        if not isinstance(cards, list):
            cards = []
        if not cards:
            # Kinematic screening/equilibrium returns native structured values,
            # not cards. Keep those results visible in the same UI hierarchy.
            kinematic = result.get("result")
            if isinstance(kinematic, dict):
                cards = [
                    {"title": "Kritik süreksizlik" if self.language == "tr" else "Critical joints",
                     "value": kinematic.get("n_critical", "—")},
                    {"title": "İncelenen" if self.language == "tr" else "Evaluated",
                     "value": kinematic.get("n_items", "—")},
                ]
            elif result.get("fs_text") is not None:
                cards = [{"title": "Güvenlik katsayısı" if self.language == "tr" else
                          "Factor of safety", "value": result["fs_text"]}]

        if cards:
            panel = QWidget()
            grid = QGridLayout(panel)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(10)
            for index, card in enumerate(cards):
                if not isinstance(card, dict):
                    continue
                metric = MetricCard(card)
                self.metrics.append(metric)
                grid.addWidget(metric, index // 2, index % 2)
            self.body_layout.addWidget(panel)

        for definition in result_tables(result):
            group = QFrame()
            group.setObjectName("suiteResultTablePanel")
            column = QVBoxLayout(group)
            caption = QLabel(_string(definition.get("title") or
                                     ("Sonuç Tablosu" if self.language == "tr" else "Results Table")))
            caption.setObjectName("suiteResultTableTitle")
            column.addWidget(caption)
            headers = [_string(value) for value in definition["columns"]]
            grid = QTableWidget(len(definition["rows"]), len(headers))
            grid.setObjectName("suiteResultTable")
            grid.setHorizontalHeaderLabels(headers)
            grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            grid.setAlternatingRowColors(True)
            grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            grid.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            grid.setWordWrap(False)
            horizontal = grid.horizontalHeader()
            horizontal.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            horizontal.setStretchLastSection(False)
            horizontal.setMinimumSectionSize(75)
            for col_index, heading in enumerate(headers):
                horizontal.resizeSection(col_index, max(105, min(245, len(heading) * 7 + 36)))
                item = grid.horizontalHeaderItem(col_index)
                if item is not None:
                    item.setToolTip(heading)
            grid.verticalHeader().setDefaultSectionSize(30)
            grid.setMinimumHeight(min(360, max(140, len(definition["rows"]) * 30 + 52)))
            for row_index, row in enumerate(definition["rows"]):
                cells = row.get("cells", []) if isinstance(row, dict) else row
                if not isinstance(cells, (tuple, list)):
                    continue
                for col_index, value in enumerate(cells[:len(headers)]):
                    cell = QTableWidgetItem(_string(value))
                    cell.setToolTip(_string(value))
                    grid.setItem(row_index, col_index, cell)
            column.addWidget(grid)
            self.tables.append(grid)
            self.body_layout.addWidget(group)


class ResultsPanel(QScrollArea):
    """Scrollable result summary that does not force the analysis UI to overflow."""

    def __init__(self, language: str = "tr", parent=None):
        super().__init__(parent)
        self.setObjectName("suiteResultsScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.dashboard = ResultDashboard(language)
        self.setWidget(self.dashboard)
