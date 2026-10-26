"""Regression for explicitly zero-bounded Bearing inputs in native PySide6."""
from __future__ import annotations

import os
from dataclasses import replace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QPushButton

from slipsurface.apps import catalogue
from slipsurface.bearing import forms
from slipsurface.desktop.app import ModulePage
from slipsurface.desktop.home import HomePage
from slipsurface.desktop.updater import check


ZERO_BOUND_FIELDS = ("Ks", "adhesion_ratio", "spread_angle", "kh", "N60")


def test_schema_preserves_explicit_zero_minimum_in_both_languages():
    for language in ("tr", "en"):
        numeric = {
            field["key"]: field
            for section in forms.schema(language).values()
            if isinstance(section, dict)
            for group in section.get("groups", [])
            for field in group.get("fields", [])
            if field["kind"] == "number"
        }
        for key in ZERO_BOUND_FIELDS:
            assert numeric[key]["min"] == 0, (language, key)
        assert numeric["Ks"]["max"] == 40
        assert numeric["adhesion_ratio"]["max"] == 1
        assert numeric["spread_angle"]["max"] == 60


def test_bearing_qt_editors_clamp_zero_bounded_inputs():
    _ = QApplication.instance() or QApplication([])
    page = ModulePage("bearing", "tr")
    try:
        for key in ZERO_BOUND_FIELDS:
            widget = page._widget_for(key)
            assert isinstance(widget, QDoubleSpinBox), key
            assert widget.minimum() == 0.0, key
            widget.setValue(-0.5)
            assert page.current_values()[key] == 0.0, key

        angle = page._widget_for("spread_angle")
        angle.setValue(90.0)
        assert page.current_values()["spread_angle"] == 60.0
        angle.setValue(26.57)
        assert page.current_values()["spread_angle"] == 26.57
    finally:
        page.close()


def test_bearing_2026_0_1_update_is_shown_only_to_2026_0_0():
    installed = tuple(
        replace(app, version="2026.0.0") if app.key == "bearing" else app
        for app in catalogue()
    )
    offer = {
        "bearing": {
            "version": "2026.0.1",
            "changelog": "Bearing input bounds corrected",
            "url": "https://example.com/bearing-2026.0.1.zip",
            "sha256": "a" * 64,
            "requires_core": ">=0.1.0",
        },
    }
    updates = check(offer, apps=installed)
    assert set(updates) == {"bearing"}
    assert updates["bearing"].latest == "2026.0.1"
    assert check(offer) == {}  # installed version already current

    _ = QApplication.instance() or QApplication([])
    home = HomePage("tr", updates)
    try:
        card = home.cards["bearing"]
        button = card.findChild(QPushButton, "suiteCardUpdateInstall")
        assert button is not None and button.text() == "Güncelle"
    finally:
        home.close()
