"""The input schema, and the conversion between the page's values and a project file."""
from slipsurface.correlation import forms
from slipsurface.correlation.config import DEFAULT_CONFIG


def test_defaults_become_the_default_configuration():
    cfg = forms.to_config(forms.defaults())
    for section in ("groundwater", "spt", "cpt"):
        assert cfg[section] == DEFAULT_CONFIG[section], section
    assert cfg["options"]["methods"] == {}
    assert len(cfg["soil_profile"]) == len(DEFAULT_CONFIG["soil_profile"])
    assert len(cfg["cpt_tests"]) == len(DEFAULT_CONFIG["cpt_tests"])


def test_a_project_file_round_trips():
    values = forms.defaults()
    values.update(water_depth=3.5, er=45, method_phi="phi_wolff1989", combine="cautious")
    values["spt_tests"] = [{"depth": 1.5, "N": 7}]
    back = forms.from_config(forms.project_file(values))
    assert back["water_depth"] == 3.5 and back["er"] == 45
    assert back["method_phi"] == "phi_wolff1989" and back["method_cu"] == "auto"
    assert back["combine"] == "cautious"
    assert back["spt_tests"] == [{"depth": 1.5, "N": 7.0}]
    assert forms.to_config(back) == forms.to_config(values)


def test_rows_that_cannot_be_read_are_dropped():
    values = forms.defaults()
    values["soil_profile"] = [{"name": "", "thickness": None}, {"name": "", "thickness": 2}]
    values["cpt_tests"] = [{"depth": 1, "qc": "x", "fs": 2}, {"depth": 1, "qc": 2, "fs": 20}]
    cfg = forms.to_config(values)
    assert len(cfg["soil_profile"]) == 1 and cfg["soil_profile"][0]["name"] == "Layer"
    assert cfg["cpt_tests"] == [{"depth": 1.0, "qc": 2.0, "fs": 20.0, "u2": 0.0}]


def test_an_unknown_choice_falls_back_to_the_default():
    values = forms.defaults()
    values.update(method_phi="astrology", combine="vibes", sampler="bucket")
    cfg = forms.to_config(values)
    assert "phi" not in cfg["options"]["methods"]
    assert cfg["options"]["combine"] == "median" and cfg["spt"]["sampler"] == "standard"


def test_the_schema_is_complete_in_both_languages():
    for lang in ("en", "tr"):
        schema = forms.schema(lang)
        for part in ("project", "tests", "options"):
            for group in schema[part]["groups"]:
                assert group["title"]
                for field in group["fields"]:
                    assert field["label"] and field["label"] != field["key"]
        for table in ("soil", "spt", "cpt", "vs"):
            assert all(c["label"] for c in schema[table]["columns"])


def test_every_choosable_parameter_offers_its_correlations():
    for param in forms.CHOOSABLE:
        options = forms.method_options(param)
        assert options[0][0] == "auto" and len(options) >= 3
