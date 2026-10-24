"""Structural and integration checks for the migrated Python engines."""
import importlib

from slipsurface import APP_NAME
from slipsurface.apps import APPS, keys

EXPECTED = {
    "kinematic", "rock", "bearing", "settle", "correlation",
    "liquefaction", "pile", "spwa", "msew", "wall",
}


def test_suite_is_python_only_and_excludes_le():
    assert APP_NAME == "SlipSurfaceIQ Suite"
    assert set(keys()) == EXPECTED
    assert len(APPS) == 10
    assert "le" not in keys()


def test_every_engine_and_adapter_imports():
    for key in EXPECTED:
        assert importlib.import_module(f"slipsurface.{key}")
        assert importlib.import_module(f"slipsurface.{key}.forms")
        assert importlib.import_module(f"slipsurface.{key}.web.session")


def test_each_module_has_editable_schema_and_defaults():
    for key in EXPECTED:
        forms = importlib.import_module(f"slipsurface.{key}.forms")
        schema = forms.schema()  # Kinematic and general module schemas
        defaults = forms.defaults()
        assert isinstance(schema, dict) and schema
        assert isinstance(defaults, dict) and defaults
