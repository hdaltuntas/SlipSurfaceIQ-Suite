"""Native clickable module launchpad shown when the Suite starts."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from slipsurface.apps import App, catalogue
from slipsurface.desktop.brand import BRAND_DESCRIPTOR, BRAND_NAME, symbol_icon
from slipsurface.desktop.icons import module_icon
from slipsurface.registry import incompatible_modules


def module_description(app: App, language: str) -> str:
    """A localized, concise description for the launchpad cards."""
    return app.description_tr if language == "tr" else app.description


class ModuleCard(QFrame):
    """Entire card is clickable and also supports keyboard activation."""

    activated = Signal(str)
    update_requested = Signal(str)

    def __init__(self, module: App, language: str, update=None, parent: QWidget | None = None):
        super().__init__(parent)
        self.module = module
        self.setObjectName("suiteModuleCard")
        self.setProperty("moduleKey", module.key)
        self.setMinimumSize(245, 170)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        name = module.tr if language == "tr" else module.name
        description = module_description(module, language)
        self.setAccessibleName(name)
        self.setAccessibleDescription(description)
        self.setToolTip(description)

        content = QVBoxLayout(self)
        content.setContentsMargins(18, 12, 18, 11)
        content.setSpacing(5)

        top = QHBoxLayout()
        category = QLabel(
            {"Rock": "KAYA", "Foundations": "TEMELLER", "Retaining": "DAYANMA YAPILARI"}.get(
                module.group, module.group
            ) if language == "tr" else module.group.upper()
        )
        category.setObjectName("suiteCardCategory")
        top.addWidget(category)
        top.addStretch()
        self.icon_label = QLabel()
        self.icon_label.setObjectName("suiteCardIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(44, 44)
        self.icon_label.setPixmap(module_icon(module.key).pixmap(34, 34))
        top.addWidget(self.icon_label)
        content.addLayout(top)

        title = QLabel(name)
        title.setObjectName("suiteCardTitle")
        title.setWordWrap(True)
        content.addWidget(title)

        summary = QLabel(description)
        summary.setObjectName("suiteCardDescription")
        summary.setWordWrap(True)
        summary.setMinimumHeight(30)
        content.addWidget(summary)

        # Installed version, with a badge whenever a newer release exists.
        footer = QHBoxLayout()
        version = QLabel(f"v{module.version}")
        version.setObjectName("suiteCardVersion")
        footer.addWidget(version)
        if update is not None and update.update_available:
            badge = QLabel(
                f"Güncelleme: v{update.latest}" if language == "tr"
                else f"Update available: v{update.latest}"
            )
            badge.setObjectName("suiteCardUpdateBadge")
            if not update.core_ok:
                badge.setObjectName("suiteCardUpdateBadgeIncompatible")
            tooltip = update.changelog if update.changelog else badge.text()
            if update.url and not update.sha256:
                tooltip += "\nSHA-256 checksum required before installation."
            badge.setToolTip(tooltip)
            footer.addWidget(badge)
            if update.core_ok and update.url and update.sha256:
                install = QPushButton("Güncelle" if language == "tr" else "Update")
                install.setObjectName("suiteCardUpdateInstall")
                install.setToolTip(
                    f"{name} {update.installed} → {update.latest}"
                )
                install.clicked.connect(lambda: self.update_requested.emit(self.module.key))
                footer.addWidget(install)
        footer.addStretch()
        content.addLayout(footer)

        content.addStretch(1)

        self.launch_button = QPushButton(
            "Programı aç  ›" if language == "tr" else "Open program  ›"
        )
        self.launch_button.setObjectName("suiteCardLaunch")
        self.launch_button.setAccessibleName(
            f"{name} programını aç" if language == "tr" else f"Open {name}"
        )
        self.launch_button.clicked.connect(self.activate)
        content.addWidget(self.launch_button, alignment=Qt.AlignRight)

    def activate(self):
        self.activated.emit(self.module.key)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.activate()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.activate()
            event.accept()
            return
        super().keyPressEvent(event)


class HomePage(QWidget):
    """Landing screen independent of all engineering session imports."""

    module_selected = Signal(str)
    update_requested = Signal(str)

    def __init__(
        self, language: str = "tr", updates: dict | None = None, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.setObjectName("suiteHomePage")
        self.cards: dict[str, ModuleCard] = {}
        self.updates = updates or {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("suiteHomeScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        body = QWidget()
        body.setObjectName("suiteHomeBody")
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(14)

        # Original user-approved S logo and core product identity.
        # The hero stays midnight in both themes so the neon mark is legible.
        self.brand_hero = QFrame()
        self.brand_hero.setObjectName("suiteBrandHero")
        self.brand_hero.setMinimumHeight(148)
        hero_layout = QHBoxLayout(self.brand_hero)
        hero_layout.setContentsMargins(26, 16, 28, 16)
        hero_layout.setSpacing(20)

        self.brand_mark = QLabel()
        self.brand_mark.setObjectName("suiteBrandMark")
        self.brand_mark.setAlignment(Qt.AlignCenter)
        self.brand_mark.setFixedSize(84, 108)
        self.brand_mark.setPixmap(symbol_icon().pixmap(84, 108))
        hero_layout.addWidget(self.brand_mark)

        identity = QVBoxLayout()
        identity.setSpacing(3)
        name_row = QHBoxLayout()
        name_row.setSpacing(0)
        self.brand_title = QLabel("SlipSurface")
        self.brand_title.setObjectName("suiteBrandName")
        self.brand_suffix = QLabel("IQ")
        self.brand_suffix.setObjectName("suiteBrandIQ")
        name_row.addWidget(self.brand_title)
        name_row.addWidget(self.brand_suffix)
        name_row.addStretch()
        identity.addLayout(name_row)

        self.brand_descriptor = QLabel(BRAND_DESCRIPTOR)
        self.brand_descriptor.setObjectName("suiteBrandDescriptor")
        identity.addWidget(self.brand_descriptor)

        self.brand_motto = QLabel(
            "MODELLE   /   ANALİZ ET   /   TASARLA" if language == "tr"
            else "MODEL   /   ANALYZE   /   DESIGN"
        )
        self.brand_motto.setObjectName("suiteBrandMotto")
        identity.addWidget(self.brand_motto)
        hero_layout.addLayout(identity, 1)

        self.hero_category = QLabel(
            "GEOTEKNİK  •  KAYA  •  TEMELLER" if language == "tr"
            else "GEOTECHNICS  •  ROCK  •  FOUNDATIONS"
        )
        self.hero_category.setObjectName("suiteBrandCategory")
        self.hero_category.setWordWrap(True)
        self.hero_category.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hero_layout.addWidget(self.hero_category)
        self.brand_hero.setAccessibleName(BRAND_NAME)
        layout.addWidget(self.brand_hero)

        eyebrow = QLabel("UYGULAMA KATALOĞU  /  MODULE LIBRARY")
        eyebrow.setObjectName("suiteHomeEyebrow")
        layout.addWidget(eyebrow)

        heading = QLabel("Mühendislik Uygulamaları" if language == "tr" else "Engineering Applications")
        heading.setObjectName("suiteHomeHeading")
        layout.addWidget(heading)

        subheading = QLabel(
            f"{len(catalogue())} geoteknik ve kaya mühendisliği programı. Başlamak için bir uygulama seçin."
            if language == "tr"
            else f"{len(catalogue())} geotechnical and rock engineering tools. Select an application to begin."
        )
        subheading.setObjectName("suiteHomeSubtitle")
        subheading.setWordWrap(True)
        layout.addWidget(subheading)

        # Incompatible releases are not launchable and do not replace a
        # compatible bundled application. Explain why they were skipped.
        self.incompatible = incompatible_modules()
        if self.incompatible:
            details = ", ".join(
                f"{item['name']} (requires {item['requires_core']}, core {item['core']})"
                for item in self.incompatible[:3]
            )
            if len(self.incompatible) > 3:
                details += ", …"
            warning = QLabel(
                (
                    f"{len(self.incompatible)} uyumsuz eklenti yüklenmedi: {details}"
                    if language == "tr" else
                    f"{len(self.incompatible)} incompatible plugins were not loaded: {details}"
                )
            )
            warning.setObjectName("suiteIncompatibleBanner")
            warning.setWordWrap(True)
            layout.addWidget(warning)

        # One quiet banner when any installed application has a newer release.
        available = [update for update in self.updates.values() if update.update_available]
        if available:
            banner = QLabel(
                f"{len(available)} uygulamanın yeni sürümü var."
                if language == "tr"
                else f"{len(available)} applications have newer versions."
            )
            banner.setObjectName("suiteUpdateBanner")
            banner.setWordWrap(True)
            layout.addWidget(banner)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        for index, module in enumerate(catalogue()):
            card = ModuleCard(module, language, update=self.updates.get(module.key))
            card.activated.connect(self.module_selected.emit)
            card.update_requested.connect(self.update_requested.emit)
            self.cards[module.key] = card
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)
        layout.addStretch()
