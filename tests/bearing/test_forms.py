"""
The input schema and its readers, which the interface and the project files
both depend on.
"""
from slipsurface.bearing import forms
from slipsurface.bearing.config import DEFAULT_CONFIG
from slipsurface.bearing.i18n import TRANSLATIONS


def test_every_default_value_has_a_field():
    values = forms.defaults()
    assert values["B"] == DEFAULT_CONFIG["foundation"]["B"]
    assert values["V"] == DEFAULT_CONFIG["loading"]["V"]
    assert values["kh"] == DEFAULT_CONFIG["seismic"]["kh"]
    assert values["soil_profile"] == DEFAULT_CONFIG["soil_profile"]


def test_the_defaults_turn_back_into_the_default_configuration():
    cfg = forms.to_config(forms.defaults())
    for section in ("foundation", "loading", "groundwater", "options", "seismic",
                    "insitu", "rock", "criteria"):
        assert cfg[section] == DEFAULT_CONFIG[section], section


def test_a_project_file_round_trips():
    values = forms.defaults()
    values.update(B=3.3, shape="circle", kh=0.2, seismic_enabled=True, method="hansen",
                  rock_D=0.5, approach="da2")
    values["study_variables"] = [{"path": "loading.V", "mode": "range", "min": 1, "max": 2}]
    back = forms.from_config(forms.project_file(values))
    for key, value in values.items():
        assert back[key] == value, key


def test_a_file_missing_entries_keeps_the_defaults():
    back = forms.from_config({"foundation": {"B": 9.0}})
    assert back["B"] == 9.0
    assert back["Df"] == DEFAULT_CONFIG["foundation"]["Df"]


def test_unknown_choices_fall_back_to_the_default():
    cfg = forms.to_config({**forms.defaults(), "method": "nonsense", "shape": "hexagon"})
    assert cfg["options"]["method"] == DEFAULT_CONFIG["options"]["method"]
    assert cfg["foundation"]["shape"] == DEFAULT_CONFIG["foundation"]["shape"]


def test_rows_without_a_thickness_are_dropped():
    values = forms.defaults()
    values["soil_profile"] = values["soil_profile"] + [{"name": "x", "thickness": None}]
    assert len(forms.read_soil_profile(values)) == len(DEFAULT_CONFIG["soil_profile"])


def test_every_label_exists_in_both_languages():
    for lang in ("en", "tr"):
        schema = forms.schema(lang)
        for part in ("project", "foundation", "options", "study"):
            for group in schema[part]["groups"]:
                assert group["title"] and group["title"] not in TRANSLATIONS[lang]
                for field in group["fields"]:
                    assert field["label"] and not field["label"].endswith("_label"), \
                        field["key"]
                    for option in field.get("options", []):
                        assert "_" not in option["label"] or " " in option["label"], option


def test_every_condition_names_a_field_that_exists():
    keys = set(forms.defaults())
    schema = forms.schema()
    for part in ("project", "foundation", "options", "study"):
        for group in schema[part]["groups"]:
            for item in [group] + group["fields"]:
                for condition in item.get("when", []):
                    assert condition["key"] in keys, condition


def test_the_study_may_vary_every_layer_and_the_loads():
    choices = forms.variable_choices(forms.defaults())
    paths = {choice["value"] for choice in choices}
    assert "loading.V" in paths and "foundation.B" in paths
    assert "soil_profile.1.phi" in paths
    assert all(isinstance(choice["base"], float) for choice in choices)
