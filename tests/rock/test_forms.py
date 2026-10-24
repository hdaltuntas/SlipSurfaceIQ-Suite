"""The input schema, the pickers, and the round trip between the page and the file."""
from slipsurface.rock import forms, tables
from slipsurface.rock.config import DEFAULT_CONFIG


def test_the_defaults_are_the_default_project():
    assert forms.to_config(forms.defaults()) == {**DEFAULT_CONFIG,
                                                 "lab_data": DEFAULT_CONFIG["lab_data"]}


def test_a_project_file_opens_again_unchanged():
    values = forms.defaults()
    values.update(GSI=48.0, gsi_source="rmr", RMR89=51.0, application="slope", depth=40.0,
                  rock_type="granite", mi=31.0)
    values["study_variables"] = [{"path": "rock_mass.GSI", "mode": "range", "min": 40,
                                  "max": 60}]
    back = forms.from_config(forms.project_file(values))
    for key in ("GSI", "gsi_source", "RMR89", "application", "depth", "rock_type", "mi"):
        assert back[key] == values[key], key
    assert back["study_variables"][0]["path"] == "rock_mass.GSI"
    assert back["lab_data"] == forms.default_lab_rows()


def test_a_choice_that_does_not_exist_falls_back():
    values = forms.defaults()
    values.update(application="moon", rock_type="cheese", gsi_source="guess")
    cfg = forms.to_config(values)
    assert cfg["application"]["type"] == "general"
    assert cfg["intact"]["rock_type"] == DEFAULT_CONFIG["intact"]["rock_type"]
    assert cfg["rock_mass"]["gsi_source"] == "direct"


def test_the_pickers_fill_what_the_tables_say():
    groups = {f.key: f for g in forms.intact_groups() + forms.mass_groups() for f in g.fields}
    assert groups["rock_type"].fills["granite"] == {"mi": 32.0, "MR": 425.0}
    assert groups["strength_grade"].fills["R4"] == {"sigma_ci": 75.0}
    assert groups["disturbance_case"].fills["slope_poor_blast"] == {"D": 1.0}
    options = [o["value"] for o in groups["rock_type"].to_dict()["options"]]
    assert options[0] == forms.CUSTOM and set(options[1:]) == set(tables.ROCK_TYPES)


def test_every_field_that_depends_on_another_names_one_that_exists():
    schema = forms.schema("tr")
    keys = set(forms.defaults())
    for part in ("project", "intact", "mass", "study"):
        for group in schema[part]["groups"]:
            for field in group["fields"]:
                for condition in field.get("when", []):
                    assert condition["key"] in keys, field["key"]
                for filled in field.get("fills", {}).values():
                    assert set(filled) <= keys, field["key"]
    assert schema["lab"]["when"] == [{"key": "source", "in": ["lab"]}]


def test_the_study_offers_only_the_inputs_in_use():
    values = forms.defaults()
    paths = [c["value"] for c in forms.variable_choices(values)]
    assert "rock_mass.GSI" in paths and "intact.sigma_ci" in paths
    assert "application.depth" not in paths
    values.update(source="lab", gsi_source="q", application="tunnel")
    paths = [c["value"] for c in forms.variable_choices(values, "tr")]
    assert "intact.sigma_ci" not in paths and "rock_mass.GSI" not in paths
    assert "rock_mass.Q_prime" in paths and "application.depth" in paths
