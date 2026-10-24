"""The input schema, the defaults and the conversions to and from project files."""
import pytest

from slipsurface.liquefaction import forms
from slipsurface.liquefaction.config import DEFAULT_CONFIG
from slipsurface.liquefaction.engine import LiquefactionAnalysis


@pytest.mark.parametrize("lang", ["en", "tr"])
def test_every_field_of_the_schema_has_a_label_and_a_default(lang):
    schema = forms.schema(lang)
    values = forms.defaults(lang)
    for section in ("project", "site", "options", "study"):
        for group in schema[section]["groups"]:
            assert group["title"]
            for field in group["fields"]:
                assert field["label"] and field["key"] in values
    assert [c["key"] for c in schema["soil"]["columns"]][:2] == ["name", "thickness"]
    assert [c["key"] for c in schema["spt"]["columns"]][:2] == ["depth", "N"]
    assert all(c["label"] for c in schema["soil"]["columns"] + schema["spt"]["columns"])


def test_the_conditions_name_selects_and_their_values():
    schema = forms.schema("en")
    selects = {f["key"]: [o["value"] for o in f["options"]]
               for section in ("site", "options") for g in schema[section]["groups"]
               for f in g["fields"] if f["kind"] == "select"}
    for section in ("site", "options"):
        for group in schema[section]["groups"]:
            for field in group["fields"]:
                for key, values in field.get("when", {}).items():
                    assert key in selects and set(values) <= set(selects[key])


def test_the_languages_differ_where_they_should():
    en, tr = forms.schema("en"), forms.schema("tr")
    assert en["site"]["groups"][1]["title"] == "Design earthquake"
    assert tr["site"]["groups"][1]["title"] == "Tasarım depremi"


def test_the_defaults_are_the_default_project():
    assert forms.to_config(forms.defaults()) == DEFAULT_CONFIG


def test_a_project_file_round_trips():
    values = forms.defaults()
    values.update(magnitude=6.8, water_depth=3.0, method="youd2001", s_allow=60.0, study_n=77,
                  pga_source="tbdy", sds=0.9)
    values["soil_profile"][1]["FC"] = 27.0
    values["spt"][2]["N"] = 14
    values["study_variables"] = [{"path": "earthquake.pga", "mode": "range", "min": 1, "max": 2}]
    project = forms.project_file(values)
    assert project["format"] == forms.FILE_FORMAT
    back = forms.from_config(project)
    for key in ("magnitude", "water_depth", "method", "s_allow", "study_n", "pga_source", "sds"):
        assert back[key] == values[key]
    assert back["soil_profile"][1]["FC"] == 27.0
    assert back["spt"][2]["N"] == 14
    assert back["spt"][0]["FC"] is None             # an empty cell stays empty
    assert back["study_variables"][0]["path"] == "earthquake.pga"


def test_a_partial_project_file_keeps_the_defaults():
    values = forms.from_config({"earthquake": {"pga": 0.4}})
    assert values["pga"] == 0.4
    assert values["magnitude"] == DEFAULT_CONFIG["earthquake"]["magnitude"]
    assert len(values["soil_profile"]) == len(DEFAULT_CONFIG["soil_profile"])
    assert len(values["spt"]) == len(DEFAULT_CONFIG["spt"])


def test_empty_and_unusable_table_rows_are_dropped():
    values = forms.defaults()
    values["soil_profile"] = values["soil_profile"] + [{"name": "blank", "thickness": None},
                                                       {"name": "zero", "thickness": 0}]
    values["spt"] = values["spt"] + [{"depth": None, "N": 5}, {"depth": 5.0, "N": ""}]
    cfg = forms.to_config(values)
    assert len(cfg["soil_profile"]) == len(DEFAULT_CONFIG["soil_profile"])
    assert len(cfg["spt"]) == len(DEFAULT_CONFIG["spt"])


def test_empty_cells_fall_back_to_defaults_and_unknown_choices_are_ignored():
    values = forms.defaults()
    values.update(pga="", method="guesswork", susceptibility=None)
    values["soil_profile"][0]["gamma"] = None
    cfg = forms.to_config(values)
    assert cfg["earthquake"]["pga"] == DEFAULT_CONFIG["earthquake"]["pga"]
    assert cfg["options"]["method"] == "ib2014"
    assert cfg["options"]["susceptibility"] == "bray_sancio"
    assert cfg["soil_profile"][0]["gamma"] == DEFAULT_CONFIG["soil_profile"][0]["gamma"]
    LiquefactionAnalysis(cfg).run()


def test_variable_choices_carry_label_and_project_value():
    choices = forms.variable_choices(forms.defaults(), "en")
    by_path = {c["value"]: c for c in choices}
    assert by_path["earthquake.pga"]["base"] == DEFAULT_CONFIG["earthquake"]["pga"]
    assert by_path["soil_profile.1.FC"]["label"] == "Loose silty sand (SM) · FC"
    assert by_path["spt.2.N"]["label"] == "SPT @ 4.5 m · N"
    assert by_path["spt.2.N"]["base"] == DEFAULT_CONFIG["spt"][2]["N"]


def test_sds_replaces_pga_among_the_choices_when_it_is_used():
    values = forms.defaults()
    values["pga_source"] = "tbdy"
    paths = {c["value"] for c in forms.variable_choices(values)}
    assert "earthquake.sds" in paths and "earthquake.pga" not in paths
