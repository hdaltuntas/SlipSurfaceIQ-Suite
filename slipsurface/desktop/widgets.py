"""Reusable Qt components shared by all ten engineering modules."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from slipsurface.apps import get
from slipsurface.desktop.brand import symbol_icon
from slipsurface.desktop.icons import module_icon


class ModuleHeader(QFrame):
    """Icon + name + localized subtitle + module-specific actions."""

    def __init__(self, key: str, language: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("suiteModuleHeader")
        module = get(key)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(18, 13, 18, 13)
        outer.setSpacing(15)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("suiteModuleIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setPixmap(module_icon(key).pixmap(48, 48))
        outer.addWidget(self.icon_label)

        title_stack = QVBoxLayout()
        title_stack.setSpacing(3)
        self.group_label = QLabel(
            {
                "Rock": "KAYA MÜHENDİSLİĞİ",
                "Foundations": "TEMEL VE ZEMİN",
                "Retaining": "DAYANMA YAPILARI",
            }.get(module.group, module.group)
            if language == "tr" else module.group.upper()
        )
        self.group_label.setObjectName("suiteModuleGroup")
        title_stack.addWidget(self.group_label)

        self.title_label = QLabel(module.tr if language == "tr" else module.name)
        self.title_label.setObjectName("suiteModuleHeading")
        title_stack.addWidget(self.title_label)

        self.subtitle_label = QLabel(
            module.description_tr if language == "tr" else module.description
        )
        self.subtitle_label.setObjectName("suiteModuleSubheading")
        self.subtitle_label.setWordWrap(True)
        title_stack.addWidget(self.subtitle_label)
        outer.addLayout(title_stack, 1)

        self.brand_mark = QLabel()
        self.brand_mark.setObjectName("suiteHeaderBrand")
        self.brand_mark.setFixedSize(24, 32)
        self.brand_mark.setAlignment(Qt.AlignCenter)
        self.brand_mark.setPixmap(symbol_icon().pixmap(24, 32))
        self.brand_mark.setToolTip("SlipSurfaceIQ")
        outer.addWidget(self.brand_mark)

        self.actions = QHBoxLayout()
        self.actions.setSpacing(8)
        outer.addLayout(self.actions)

    def add_action(self, widget: QWidget):
        self.actions.addWidget(widget)

TAB_LABELS_TR = {
    "project": "Proje", "foundation": "Temel", "options": "Analiz Ayarları",
    "study": "Parametrik Çalışma", "soil": "Zemin Tabakaları",
    "tests": "Deneyler", "site": "Saha Verileri", "spt": "SPT Verileri",
    "cpt": "CPT Verileri", "vs": "Kayma Dalgası", "intact": "Sağlam Kaya",
    "mass": "Kaya Kütlesi", "lab": "Laboratuvar", "pile": "Kazık",
    "socket": "Kaya Soketi", "structure": "Yapısal Sistem", "anchors": "Ankrajlar",
    "layout": "Yerleşim", "layers": "Tabakalar", "types": "Donatı Türleri",
    "wall": "Duvar", "concrete": "Betonarme", "heights": "Duvar Yükseklikleri",
    "screening": "Kinematik Tarama", "bolts": "Kaya Bulonları", "report": "Rapor",
}
KINEMATIC_MODES_TR = {"planar": "Düzlemsel", "wedge": "Kama", "toppling": "Devrilme"}


def section_title(section: str, language: str) -> str:
    """Shared localized tab captions; input keys and computations are unchanged."""
    if section.startswith("equilibrium:"):
        mode = section.split(":", 1)[1]
        suffix = KINEMATIC_MODES_TR.get(mode, mode.title()) if language == "tr" else mode.title()
        return f"Denge · {suffix}" if language == "tr" else f"Equilibrium · {suffix}"
    if language == "tr":
        return TAB_LABELS_TR.get(section, section.replace("_", " ").title())
    return section.replace("_", " ").title()
