"""Native branded startup screen; rendered on the GUI thread without web content."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QSplashScreen

from slipsurface.desktop.brand import BRAND_DESCRIPTOR, BRAND_NAME, symbol_icon
from slipsurface.desktop.theme import COLORS


class BrandSplash(QSplashScreen):
    """Short optional splash shown before the dashboard, not during headless CI."""

    def __init__(self, language: str = "tr"):
        super().__init__(self.render_artwork(language))
        self.setObjectName("suiteBrandSplash")

    @staticmethod
    def render_artwork(language: str = "tr") -> QPixmap:
        width, height = 900, 480
        canvas = QPixmap(width, height)
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        background = QLinearGradient(0, 0, width, height)
        background.setColorAt(0, QColor(COLORS["input"]))
        background.setColorAt(0.66, QColor(COLORS["sidebar"]))
        background.setColorAt(1, QColor(COLORS["surface"]))
        painter.fillRect(canvas.rect(), QBrush(background))

        for x, y, radius, color in (
            (170, 220, 260, QColor(143, 201, 195, 28)),
            (770, 410, 370, QColor(155, 203, 216, 22)),
        ):
            bloom = QRadialGradient(QPointF(x, y), radius)
            bloom.setColorAt(0, color)
            bloom.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillRect(canvas.rect(), QBrush(bloom))

        # Wireframe ground contours: engineering geometry, not decorative dots.
        painter.setPen(QPen(QColor(143, 201, 195, 72), 1.0))
        for ridge in range(7):
            points = []
            for x in range(30, 901, 22):
                rise = 50 * math.sin(x / 142 + ridge * 0.18)
                ground = 394 + rise + ridge * 8 - 18 * math.sin(x / 300)
                points.append(QPointF(float(x), float(ground)))
            for start, end in zip(points, points[1:]):
                painter.drawLine(start, end)
        for x in range(45, 900, 42):
            painter.drawLine(
                QPointF(float(x), 393.0 + 50.0 * math.sin(x / 142)),
                QPointF(float(x + 35), 468.0),
            )

        mark = symbol_icon().pixmap(186, 230)
        painter.drawPixmap(100, 91, mark)

        painter.setPen(QColor(COLORS["text"]))
        painter.setFont(QFont("Segoe UI", 37, QFont.Bold))
        painter.drawText(325, 134, 550, 75, Qt.AlignVCenter, BRAND_NAME)

        painter.setPen(QColor(COLORS["secondary"]))
        painter.setFont(QFont("Segoe UI", 12, QFont.Medium))
        painter.drawText(330, 210, 530, 34, Qt.AlignVCenter, BRAND_DESCRIPTOR)

        painter.setPen(QColor(COLORS["accent"]))
        painter.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        motto = ("MODELLE  /  ANALİZ ET  /  TASARLA" if language == "tr"
                 else "MODEL  /  ANALYZE  /  DESIGN")
        painter.drawText(330, 265, 530, 32, Qt.AlignVCenter, motto)

        line_gradient = QLinearGradient(100, 351, 800, 351)
        for stop, color in [(0, COLORS["accent"]), (0.5, "#9BCBD8"),
                            (0.8, "#BAABD7"), (1, COLORS["border"])]:
            line_gradient.setColorAt(stop, QColor(color))
        painter.setPen(QPen(QBrush(line_gradient), 3.0))
        painter.drawLine(100, 351, 800, 351)

        painter.setPen(QColor(COLORS["secondary"]))
        painter.setFont(QFont("Segoe UI", 10))
        footer = ("GEOTEKNİK MÜHENDİSLİĞİ • YEREL MASAÜSTÜ"
                  if language == "tr" else "GEOTECHNICAL ENGINEERING • NATIVE DESKTOP")
        painter.drawText(100, 373, 710, 29, Qt.AlignVCenter, footer)
        painter.end()
        return canvas
