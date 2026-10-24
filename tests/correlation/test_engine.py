"""The analysis: stresses, tests, derived parameters and the selection."""
import copy
import math

import pytest

from slipsurface.correlation.config import DEFAULT_CONFIG, PARAMS
from slipsurface.correlation.engine import CorrelationAnalysis, CorrelationError, combine


def run(cfg=None):
    return CorrelationAnalysis(cfg or copy.deepcopy(DEFAULT_CONFIG)).run()


@pytest.fixture(scope="module")
def default():
    return run()


def layer(analysis, name):
    return next(lay for lay in analysis.results["layers"] if lay["name"] == name)


def test_the_default_project_derives_parameters_without_warnings(default):
    res = default.results
    assert res["counts"]["layers"] == 4
    assert res["counts"]["spt"] == 13 and res["counts"]["cpt"] == 39 and res["counts"]["vs"] == 6
    assert res["warnings"] == []
    for lay in res["layers"]:
        assert set(lay["params"]) == set(PARAMS)


def test_sands_get_sand_parameters_and_clays_clay_parameters(default):
    sand = layer(default, "Medium dense sand")["params"]
    clay = layer(default, "Soft to firm clay")["params"]
    for key in ("Dr", "phi", "E", "Vs", "K0"):
        assert sand[key]["value"] is not None, key
    for key in ("cu", "Eu", "Cc"):
        assert sand[key]["value"] is None, key
    for key in ("cu", "sigma_p", "OCR", "Eu", "Cc", "Cr", "Calpha", "cv", "phi", "Vs"):
        assert clay[key]["value"] is not None, key
    assert clay["Dr"]["value"] is None and clay["E"]["value"] is None


def test_values_are_physically_sensible(default):
    for lay in default.results["layers"]:
        p = lay["params"]
        assert 12 < p["gamma"]["value"] < 24
        assert 20 < p["phi"]["value"] < 50
        assert 0 < p["K0"]["value"] < 2
        assert 50 < p["Vs"]["value"] < 600
    clay = layer(default, "Soft to firm clay")["params"]
    assert 10 < clay["cu"]["value"] < 150
    assert 1 <= clay["OCR"]["value"] < 5
    assert 0.1 < clay["Cc"]["value"] < 1.0
    assert clay["Cr"]["value"] < clay["Cc"]["value"]


def test_the_selected_value_lies_within_the_correlations(default):
    for lay in default.results["layers"]:
        for param, info in lay["params"].items():
            if info["how"] == "combined":
                assert info["min"] - 1e-9 <= info["value"] <= info["max"] + 1e-9, param


def test_entered_unit_weights_are_used_as_they_are(default):
    fill = layer(default, "Fill")["params"]
    assert fill["gamma"]["value"] == 18.0 and fill["gamma"]["how"] == "input"
    assert fill["gamma_sat"]["value"] == 19.0


def test_ocr_follows_from_the_preconsolidation_pressure(default):
    clay = layer(default, "Soft to firm clay")
    assert clay["params"]["OCR"]["value"] == pytest.approx(
        clay["params"]["sigma_p"]["value"] / clay["sigma_eff"])
    assert "cu_mesri1975" in clay["params"]["cu"]["methods"]


def test_combination_rules():
    values = [30.0, 34.0, 38.0, 44.0]
    assert combine("phi", values, "median") == 36.0
    assert combine("phi", values, "mean") == 36.5
    cautious = combine("phi", values, "cautious")
    assert cautious < 36.5 and cautious >= 30.0
    assert combine("Cc", [0.2, 0.3, 0.4], "cautious") > 0.3        # compressibility: upper side
    assert combine("k", [1e-6, 1e-4], "mean") == pytest.approx(1e-5)    # geometric


def test_a_chosen_correlation_is_used_and_reported():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["options"]["methods"] = {"phi": "phi_hatanaka1996", "cu": "cu_qu"}
    a = run(cfg)
    sand = layer(a, "Dense sand")["params"]["phi"]
    assert sand["how"] == "phi_hatanaka1996"
    assert sand["value"] == sand["methods"]["phi_hatanaka1996"]["value"]
    assert layer(a, "Soft to firm clay")["params"]["cu"]["value"] == 35.0
    # the clay has no SPT friction angle: the program falls back and says so
    assert any(key == "warn_method_missing" for key, _ in a.results["warnings"])


def test_the_cautious_estimate_is_lower_for_strength():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["options"]["combine"] = "cautious"
    cautious = layer(run(cfg), "Dense sand")["params"]["phi"]["value"]
    cfg["options"]["combine"] = "mean"
    mean = layer(run(cfg), "Dense sand")["params"]["phi"]["value"]
    assert cautious < mean


def test_a_layer_with_nothing_measured_gets_typical_weights_and_a_warning():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["soil_profile"].append({"name": "Rock head", "thickness": 3.0, "behaviour": "granular"})
    a = run(cfg)
    keys = [key for key, _ in a.results["warnings"]]
    assert "warn_gamma_typical" in keys and "warn_no_data" in keys


def test_tests_below_the_profile_are_left_out_with_a_warning():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["spt_tests"].append({"depth": 35.0, "N": 50})
    a = run(cfg)
    assert a.results["counts"]["spt"] == len(DEFAULT_CONFIG["spt_tests"])
    assert ("warn_test_outside", {"test": "SPT", "depth": 35.0}) in a.results["warnings"]


def test_only_laboratory_data_is_enough():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["spt_tests"], cfg["cpt_tests"], cfg["vs_tests"] = [], [], []
    clay = layer(run(cfg), "Soft to firm clay")["params"]
    assert clay["Cc"]["value"]
    # the unconfined strength, and Mesri's from σ'p after Stas & Kulhawy's liquidity index
    assert set(clay["cu"]["methods"]) == {"cu_qu", "cu_mesri1975"}
    assert clay["Vs"]["value"] is None


def test_a_cpt_that_contradicts_the_layer_is_pointed_out():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["soil_profile"][2]["behaviour"] = "granular"
    keys = [key for key, _ in run(cfg).results["warnings"]]
    assert "warn_ic_clay" in keys


@pytest.mark.parametrize("change, key", [
    (lambda c: c.update(soil_profile=[]), "err_no_layers"),
    (lambda c: c["groundwater"].update(depth=-1), "err_water"),
    (lambda c: c["cpt"].update(area_ratio=0), "err_area_ratio"),
    (lambda c: c["cpt"].update(Nkt=0), "err_factor"),
    (lambda c: c["soil_profile"][0].update(w=-5), "err_negative"),
    (lambda c: c["soil_profile"][0].update(fines=80, gravel=30), "err_fractions"),
])
def test_impossible_input_is_refused(change, key):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    change(cfg)
    with pytest.raises(CorrelationError) as caught:
        CorrelationAnalysis(cfg)
    assert caught.value.key == key


def test_test_rows_carry_the_values_of_the_depth_plots(default):
    for row in default.results["spt"] + default.results["cpt"]:
        for param, value in row["selected"].items():
            assert math.isfinite(value), param
