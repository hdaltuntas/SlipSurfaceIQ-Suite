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

from slipsurface.apps import APPS, App
from slipsurface.desktop.icons import module_icon


def module_description(app: App, language: str) -> str:
    """A localized, concise description for the launchpad cards."""
    return app.description_tr if language == "tr" else app.description


class ModuleCard(QFrame):
    """Entire card is clickable and also supports keyboard activation."""

    activated = Signal(str)

    def __init__(self, module: App, language: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.module = module
        self.setObjectName("suiteModuleCard")
        self.setProperty("moduleKey", module.key)
        self.setMinimumSize(245, 192)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        name = module.tr if language == "tr" else module.name
        description = module_description(module, language)
        self.setAccessibleName(name)
        self.setAccessibleDescription(description)
        self.setToolTip(description)

        content = QVBoxLayout(self)
        content.setContentsMargins(20, 17, 20, 16)
        content.setSpacing(8)

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
        self.icon_label.setFixedSize(54, 54)
        self.icon_label.setPixmap(module_icon(module.key).pixmap(40, 40))
        top.addWidget(self.icon_label)
        content.addLayout(top)

        title = QLabel(name)
        title.setObjectName("suiteCardTitle")
        title.setWordWrap(True)
        content.addWidget(title)

        summary = QLabel(description)
        summary.setObjectName("suiteCardDescription")
        summary.setWordWrap(True)
        summary.setMinimumHeight(38)
        content.addWidget(summary)
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

    def __init__(self, language: str = "tr", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("suiteHomePage")
        self.cards: dict[str, ModuleCard] = {}

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
        layout.setContentsMargins(38, 34, 38, 36)
        layout.setSpacing(20)

        eyebrow = QLabel("SLIPSURFACEIQ  /  ENGINEERING DESKTOP")
        eyebrow.setObjectName("suiteHomeEyebrow")
        layout.addWidget(eyebrow)

        heading = QLabel("Mühendislik Uygulamaları" if language == "tr" else "Engineering Applications")
        heading.setObjectName("suiteHomeHeading")
        layout.addWidget(heading)

        subheading = QLabel(
            f"{len(APPS)} geoteknik ve kaya mühendisliği programı. Başlamak için bir uygulama seçin."
            if language == "tr"
            else f"{len(APPS)} geotechnical and rock engineering tools. Select an application to begin."
        )
        subheading.setObjectName("suiteHomeSubtitle")
        subheading.setWordWrap(True)
        layout.addWidget(subheading)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        for index, module in enumerate(APPS):
            card = ModuleCard(module, language)
            card.activated.connect(self.module_selected.emit)
            self.cards[module.key] = card
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)
        layout.addStretch()
