"""Native, bilingual About and dependency-license viewer for SlipSurfaceIQ.

Qt widgets only; no web server, QWebEngine or third-party browser runtime.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from slipsurface import APP_NAME, CORE_VERSION, __version__
from slipsurface.apps import catalogue
from slipsurface.desktop.brand import BRAND_DESCRIPTOR, symbol_icon
from slipsurface.desktop.third_party import DEPENDENCIES, dependency_version, python_version


def _t(language: str, tr: str, en: str) -> str:
    return tr if language == "tr" else en


class AboutDialog(QDialog):
    """Suite identity, module versions, open-source license and dependencies."""

    def __init__(self, language: str = "tr", parent: QWidget | None = None):
        super().__init__(parent)
        self.language = language
        self.setObjectName("suiteAboutDialog")
        self.setWindowTitle(_t(language, "SlipSurfaceIQ Hakkında", "About SlipSurfaceIQ"))
        self.resize(805, 605)
        self.setMinimumSize(650, 470)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 17)
        outer.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("suiteAboutHero")
        head = QHBoxLayout(hero)
        head.setContentsMargins(20, 14, 20, 14)
        mark = QLabel()
        mark.setObjectName("suiteAboutMark")
        mark.setFixedSize(65, 82)
        mark.setPixmap(symbol_icon().pixmap(65, 82))
        head.addWidget(mark)
        brand = QVBoxLayout()
        title = QLabel("SlipSurfaceIQ Suite")
        title.setObjectName("suiteAboutTitle")
        brand.addWidget(title)
        description = QLabel(BRAND_DESCRIPTOR)
        description.setObjectName("suiteAboutDescriptor")
        brand.addWidget(description)
        edition = QLabel(
            _t(language, "Geoteknik mühendislik uygulamaları",
               "Geotechnical engineering applications")
        )
        edition.setObjectName("suiteAboutEdition")
        brand.addWidget(edition)
        head.addLayout(brand, 1)
        outer.addWidget(hero)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("suiteAboutTabs")
        overview = QTextBrowser()
        overview.setObjectName("suiteAboutOverview")
        overview.setOpenExternalLinks(True)
        overview.setHtml(self._overview_html())
        self.overview = overview
        self.tabs.addTab(overview, _t(language, "Hakkında", "About"))

        modules = QWidget()
        module_layout = QVBoxLayout(modules)
        self.module_table = self._table(
            [_t(language, "Program", "Module"), _t(language, "Sürüm", "Version")],
            len(catalogue()),
        )
        for index, module in enumerate(catalogue()):
            self._put(self.module_table, index, 0, module.tr if language == "tr" else module.name)
            self._put(self.module_table, index, 1, module.version)
        module_layout.addWidget(self.module_table)
        self.tabs.addTab(modules, _t(language, "Program sürümleri", "Module versions"))

        dependencies = QWidget()
        library_layout = QVBoxLayout(dependencies)
        self.library_table = self._table(
            [
                _t(language, "Kütüphane", "Library"),
                _t(language, "Kurulu sürüm", "Installed"),
                _t(language, "Lisans", "License"),
                _t(language, "Kullanım", "Purpose"),
            ],
            len(DEPENDENCIES) + 1,
        )
        self._put(self.library_table, 0, 0, "Python")
        self._put(self.library_table, 0, 1, python_version())
        self._put(self.library_table, 0, 2, "PSF License 2.0")
        self._put(self.library_table, 0, 3, _t(language, "Çalışma ortamı", "Runtime"))
        for index, item in enumerate(DEPENDENCIES, 1):
            self._put(self.library_table, index, 0, item.name)
            self._put(self.library_table, index, 1, dependency_version(item))
            self._put(self.library_table, index, 2, item.license)
            self._put(
                self.library_table, index, 3,
                item.purpose_tr if language == "tr" else item.purpose_en,
            )
            for column in range(4):
                cell = self.library_table.item(index, column)
                if cell is not None:
                    cell.setToolTip(item.license_url)
        self.library_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.library_table.horizontalHeader().setStretchLastSection(True)
        library_layout.addWidget(self.library_table)
        link = QLabel(
            '<a href="https://github.com/hdaltuntas/SlipSurfaceIQ-Suite/blob/main/'
            'THIRD_PARTY_NOTICES.md">'
            + _t(language, "Üçüncü taraf lisans bildirimleri",
                 "Third-party license notices") + "</a>"
        )
        link.setOpenExternalLinks(True)
        link.setTextFormat(Qt.TextFormat.RichText)
        library_layout.addWidget(link)
        self.tabs.addTab(dependencies, _t(language, "Kütüphaneler", "Libraries"))

        outer.addWidget(self.tabs, 1)
        footer = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        footer.rejected.connect(self.reject)
        outer.addWidget(footer)
        self.close_buttons = footer

    def _overview_html(self) -> str:
        tr = self.language == "tr"
        title = "Geliştirici" if tr else "Developer"
        license_name = "Lisans" if tr else "License"
        core = "Çekirdek API sürümü" if tr else "Core API version"
        module_count = "Modül" if tr else "Modules"
        source = "Kaynak kod" if tr else "Source code"
        desc = (
            "Yerel Python / PySide6 masaüstü geoteknik mühendislik yazılımı."
            if tr else "Native Python / PySide6 geotechnical desktop engineering suite."
        )
        disclaimer = (
            "Mühendislik sonuçları, tasarım kararları öncesinde bağımsız olarak "
            "doğrulanmalıdır."
            if tr else "Engineering results must be independently validated "
            "before making design decisions."
        )
        return (
            f"<h2>{APP_NAME} — {__version__}</h2>"
            f"<p>{desc}</p>"
            f"<p><b>{title}:</b> Hasan Deniz Altuntaş<br>"
            f"<b>Copyright:</b> © 2026 Hasan Deniz Altuntaş<br>"
            f"<b>{license_name}:</b> GNU Affero General Public License, "
            "Version 3 only (AGPL-3.0-only)<br>"
            f"<b>{core}:</b> {CORE_VERSION}<br>"
            f"<b>{module_count}:</b> {len(catalogue())}</p>"
            f'<p><a href="https://github.com/hdaltuntas/SlipSurfaceIQ-Suite">'
            f"{source}</a> · "
            '<a href="https://github.com/hdaltuntas/SlipSurfaceIQ-Suite/blob/main/LICENSE">'
            'AGPL v3</a> · '
            '<a href="https://github.com/hdaltuntas/SlipSurfaceIQ-Suite/blob/main/'
            'THIRD_PARTY_NOTICES.md">Third-party notices</a></p>'
            f"<p>{disclaimer}</p>"
        )

    @staticmethod
    def _put(table: QTableWidget, row: int, column: int, text: str) -> None:
        table.setItem(row, column, QTableWidgetItem(str(text)))

    @staticmethod
    def _table(headers: list[str], rows: int) -> QTableWidget:
        table = QTableWidget(rows, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        return table
