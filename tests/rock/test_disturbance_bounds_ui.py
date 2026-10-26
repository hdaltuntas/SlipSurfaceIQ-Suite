"""Regression tests: valid Hoek–Brown D bounds survive schema -> Qt -> engine."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDoubleSpinBox

from slipsurface.desktop.app import ModulePage
from slipsurface.rock import forms


def test_zero_is_a_serialized_form_minimum_in_both_languages():
    for language in ("tr", "en"):
        schema = forms.schema(language)
        number_fields = [
            field
            for section in schema.values()
            if isinstance(section, dict)
            for group in section.get("groups", [])
            for field in group.get("fields", [])
            if field["kind"] == "number"
        ]
        disturbance = next(field for field in number_fields if field["key"] == "D")
        assert disturbance["min"] == 0
        assert disturbance["max"] == 1
        assert disturbance["decimals"] == 2
        # Zero lower bounds matter for every other numeric field as well.
        for field in number_fields:
            if field["key"] in {"JCond89", "RQD", "RMR89"}:
                assert field["min"] == 0, field["key"]


def test_native_rock_editor_rejects_negative_or_excessive_disturbance():
    _ = QApplication.instance() or QApplication([])
    page = ModulePage("rock", "tr")
    try:
        spin = page._widget_for("D")
        assert isinstance(spin, QDoubleSpinBox)
        assert spin.minimum() == 0.0
        assert spin.maximum() == 1.0

        spin.setValue(-0.2)
        assert page.current_values()["D"] == 0.0
        spin.setValue(1.4)
        assert page.current_values()["D"] == 1.0
        spin.setValue(0.5)
        values = page.current_values()
        assert values["D"] == 0.5

        result = page.session.analyse(values)
        assert result["ok"] is True
    finally:
        page.close()
