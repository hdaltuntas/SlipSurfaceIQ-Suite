"""The input schema and the readers between flat values and the configuration."""
import copy

from slipsurface.wall import forms
from slipsurface.wall.config import DEFAULT_CONFIG


def test_the_defaults_give_the_default_configuration():
    cfg = forms.to_config(forms.defaults())
    expected = copy.deepcopy(DEFAULT_CONFIG)
    assert cfg == expected


def test_a_project_round_trips():
    values = forms.defaults()
    values.update({"H": 7.5, "taper": "front", "key_enabled": True, "key_depth": 0.8,
                   "phi_b": 34.0, "seismic_enabled": True, "site": "ZD",
                   "seismic_method": "wood", "grade": "C35", "bar_stem": "20",
                   "curtail": False, "passive": True, "passive_method": "coulomb"})
    cfg = forms.project_file(values)
    assert cfg["format"] == forms.FILE_FORMAT
    back = forms.from_config(cfg)
    for key in values:
        assert back[key] == values[key], key


def test_bad_values_fall_back_to_the_defaults():
    values = forms.defaults()
    values.update({"H": "", "method": "nonsense", "site": "ZF", "grade": "C99",
                   "bar_stem": "17", "q_live": "abc"})
    cfg = forms.to_config(values)
    assert cfg["geometry"]["H"] == DEFAULT_CONFIG["geometry"]["H"]
    assert cfg["earth"]["method"] == "rankine"
    assert cfg["seismic"]["site"] == "ZC"
    assert cfg["concrete"]["grade"] == "C30"
    assert cfg["concrete"]["bar_stem"] == 0
    assert cfg["loads"]["q_live"] == DEFAULT_CONFIG["loads"]["q_live"]


def test_the_schema_in_both_languages():
    for lang in ("en", "tr"):
        schema = forms.schema(lang)
        assert set(schema) == {"project", "wall", "options", "concrete"}
        keys = [f["key"] for part in schema.values() for g in part["groups"]
                for f in g["fields"]]
        assert len(keys) == len(set(keys))
        assert set(keys) == set(forms.defaults(lang))
    tr = forms.schema("tr")["wall"]["groups"][0]
    assert tr["title"] == "Duvar geometrisi"


def test_conditional_fields_name_existing_keys():
    defaults = forms.defaults()
    for part in forms.schema("en").values():
        for group in part["groups"]:
            for item in [group] + group["fields"]:
                for condition in item.get("when", []):
                    assert condition["key"] in defaults
