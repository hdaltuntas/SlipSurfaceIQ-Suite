"""The liquefaction analysis of a borehole: stresses, states, sharing of the layers
among the tests, totals, and the refusals of impossible input."""
import copy
import math

import numpy as np
import pytest

from slipsurface.liquefaction.config import DEFAULT_CONFIG, METHODS
from slipsurface.liquefaction.engine import LiqError, LiquefactionAnalysis


def run(**changes):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for path, value in changes.items():
        section, key = path.split("__")
        cfg[section][key] = value
    analysis = LiquefactionAnalysis(cfg)
    analysis.run()
    return analysis


def one_layer(**layer):
    """A uniform sand with tests every metre, for the checks by hand."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    base = {"name": "Sand", "thickness": 10.0, "gamma": 18.0, "gamma_sat": 20.0, "FC": 5.0,
            "clay": 0.0, "LL": 0.0, "PI": 0.0, "wn": 20.0, "Vs": 0.0}
    base.update(layer)
    cfg["soil_profile"] = [base]
    cfg["spt"] = [{"depth": float(z), "N": 10} for z in range(1, 10)]
    cfg["groundwater"].update(depth=2.0, depth_test=2.0)
    return cfg


@pytest.fixture(scope="module")
def default():
    return run()


def test_the_default_borehole_runs_and_is_consistent(default):
    res = default.results
    t = res["tests"]
    assert len(t["z"]) == len(DEFAULT_CONFIG["spt"])
    assert res["settlement_sat"] == pytest.approx(float(np.sum(t["ds"])))
    assert res["settlement_dry"] == pytest.approx(float(np.sum(t["ds_dry"])))
    assert res["settlement"] == pytest.approx(res["settlement_sat"] + res["settlement_dry"])
    assert res["ldi"] == pytest.approx(float(np.sum(t["ldi"])))
    assert res["lpi"] == pytest.approx(float(np.sum(t["lpi"])))
    assert res["lsn"] == pytest.approx(float(np.sum(t["lsn"])))
    assert set(res["methods"]) == set(METHODS) | {"vs2000"}
    assert res["fs_min"] == pytest.approx(np.nanmin(res["methods"][default.method]["fs_eff"]))


def test_the_states(default):
    t = default.results["tests"]
    states = dict(zip(t["z"], t["state"]))
    assert states[1.5] == "dry"                   # on the water table
    # the lean clay is not liquefiable, but it softens cyclically in this earthquake
    assert states[10.5] == "softening" and states[12.0] == "softening"
    assert states[3.0] == "liquefied"
    assert states[19.5] == "safe"


def test_stresses_by_hand():
    a = LiquefactionAnalysis(one_layer())
    t = a.run()["tests"]
    i = list(t["z"]).index(5.0)
    assert t["sigma_v"][i] == pytest.approx(2 * 18 + 3 * 20)
    assert t["u"][i] == pytest.approx(3 * 9.81)
    assert t["sigma_eff"][i] == pytest.approx(96 - 3 * 9.81)


def test_the_test_water_table_only_changes_the_normalisation():
    cfg = one_layer()
    cfg["groundwater"]["depth_test"] = 6.0
    t = LiquefactionAnalysis(cfg).run()["tests"]
    i = list(t["z"]).index(5.0)
    assert t["sigma_eff_test"][i] == pytest.approx(5 * 18)
    assert t["sigma_eff"][i] == pytest.approx(96 - 3 * 9.81)


def test_each_layer_is_shared_among_its_own_tests(default):
    t = default.results["tests"]
    layers = default.profile.layers
    for i, layer in enumerate(layers):
        rows = np.nonzero(t["layer"] == i)[0]
        if rows.size == 0:
            continue
        assert t["top"][rows[0]] == pytest.approx(layer["top"])
        assert t["bot"][rows[-1]] == pytest.approx(layer["bottom"])
        assert np.allclose(t["bot"][rows[:-1]], t["top"][rows[1:]])
        assert np.all((t["z"][rows] >= t["top"][rows]) & (t["z"][rows] <= t["bot"][rows]))


def test_an_untested_layer_is_reported():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["spt"] = [row for row in cfg["spt"] if not 9.5 <= row["depth"] <= 12.5]
    analysis = LiquefactionAnalysis(cfg)
    analysis.run()
    assert ("warn_layer_untested", {"name": "Lean clay (CL)"}) in analysis.results["warnings"]


def test_nothing_liquefies_above_the_water_table():
    a = run(groundwater__depth=30.0)
    res = a.results
    assert set(res["tests"]["state"]) == {"dry"}
    assert res["settlement_sat"] == 0 and res["lpi"] == 0 and res["lsn"] == 0
    assert res["ldi"] == 0 and res["ld"] == 0
    # the dry sand still compresses (Pradel)
    assert res["settlement_dry"] > 0 and res["settlement"] == res["settlement_dry"]
    assert math.isnan(res["fs_min"]) and res["checks"]["fs"]["status"] == "N/A"


def test_a_dense_sand_does_not_liquefy():
    cfg = one_layer()
    for row in cfg["spt"]:
        row["N"] = 45
    res = LiquefactionAnalysis(cfg).run()
    wet = res["tests"]["z"] > 2.0
    assert set(res["tests"]["state"][wet]) <= {"dense", "safe"}
    assert res["settlement_sat"] == pytest.approx(0.0, abs=1e-9)
    assert res["checks"]["fs"]["status"] == "OK"


def test_a_stronger_earthquake_lowers_the_factor_of_safety_and_raises_the_settlement():
    weak, strong = run(earthquake__pga=0.15), run(earthquake__pga=0.35)
    assert strong.results["fs_min"] < weak.results["fs_min"]
    assert strong.results["settlement"] > weak.results["settlement"]
    assert strong.results["lpi"] >= weak.results["lpi"]


def test_the_acceleration_can_come_from_sds():
    a = run(earthquake__pga_source="tbdy", earthquake__sds=0.8)
    assert a.amax == pytest.approx(0.32)


@pytest.mark.parametrize("method", METHODS)
def test_every_procedure_can_govern(method):
    a = run(options__method=method)
    assert a.results["methods"][method]["fs"] is a.results["methods"][a.method]["fs"]
    assert math.isfinite(a.results["fs_min"])


def test_the_susceptibility_criterion_decides_what_is_assessed():
    # With no criterion the lean clay is treated as a sand; with Bray & Sancio it is not.
    loose = run(options__susceptibility="none").results["tests"]
    strict = run(options__susceptibility="bray_sancio").results["tests"]
    i = list(loose["z"]).index(10.5)
    assert loose["state"][i] not in ("not", "softening")
    assert strict["state"][i] in ("not", "softening")


def test_the_uncertain_band_can_be_excluded():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["spt"][5].update(LL=36.0, PI=15.0, wn=30.0)        # Bray & Sancio: to be tested
    included = LiquefactionAnalysis(cfg)
    included.run()
    cfg["options"]["uncertain_susceptible"] = False
    excluded = LiquefactionAnalysis(cfg)
    excluded.run()
    assert included.results["tests"]["class"][5] == "moderate"
    assert included.results["tests"]["state"][5] != "not"
    assert excluded.results["tests"]["state"][5] in ("not", "softening")
    assert ("warn_moderate_excluded", {}) in excluded.results["warnings"]


def test_a_test_row_overrides_its_layer_only_where_it_has_a_value():
    res = run().results
    t = res["tests"]
    i = list(t["z"]).index(3.0)                   # carries FC = 16 of its own
    j = list(t["z"]).index(6.0)                   # inherits the layer's 18
    assert t["FC"][i] == 16.0 and t["FC"][j] == 18.0


def test_the_settlement_depth_limits_the_sum():
    shallow, deep = run(options__settlement_depth=5.0), run(options__settlement_depth=20.0)
    assert shallow.results["settlement"] < deep.results["settlement"]


def test_the_checks():
    res = run(criteria__s_allow=1000.0, criteria__fs_required=1.1).results
    assert res["checks"]["settlement"]["status"] == "OK"
    assert res["checks"]["fs"]["status"] == "NOT OK" and res["at_risk"]
    assert run(criteria__s_allow=0.0).results["checks"]["settlement"]["status"] == "N/A"


def test_cetin_estimates_vs12_when_the_layers_have_none():
    cfg = one_layer()
    cfg["options"]["method"] = "cetin2004"
    a = LiquefactionAnalysis(cfg)
    a.run()
    assert a.results["vs12_estimated"] and 100 < a.results["vs12"] < 300
    assert any(key == "warn_vs12" for key, _ in a.results["warnings"])
    cfg["soil_profile"][0]["Vs"] = 200.0
    b = LiquefactionAnalysis(cfg)
    b.run()
    assert not b.results["vs12_estimated"] and b.results["vs12"] == pytest.approx(200.0)


def test_the_shear_wave_check_appears_only_with_velocities():
    assert "vs2000" not in LiquefactionAnalysis(one_layer()).run()["methods"]
    assert "vs2000" in LiquefactionAnalysis(one_layer(Vs=170.0)).run()["methods"]


def test_duplicate_tests_are_dropped_with_a_warning():
    cfg = one_layer()
    cfg["spt"].append({"depth": 5.0, "N": 30})
    a = LiquefactionAnalysis(cfg)
    a.run()
    assert list(a.results["tests"]["z"]).count(5.0) == 1
    assert ("warn_duplicate", {"z": 5.0}) in a.results["warnings"]


@pytest.mark.parametrize("change, key", [
    ({"earthquake": {"magnitude": 3.0}}, "err_magnitude"),
    ({"earthquake": {"pga": 0.0}}, "err_pga"),
    ({"groundwater": {"depth": -1.0}}, "err_water"),
    ({"spt_setup": {"energy": 5.0}}, "err_energy"),
    ({"spt": []}, "err_no_spt"),
    ({"soil_profile": []}, "err_no_layers"),
    ({"spt": [{"depth": 50.0, "N": 10}]}, "err_spt_depth"),
    ({"spt": [{"depth": 5.0, "N": -1}]}, "err_spt_n"),
    ({"options": {"settlement_depth": 0.0}}, "err_settlement_depth"),
    ({"criteria": {"fs_required": 0.0}}, "err_fs_required"),
])
def test_impossible_input_is_refused_with_a_key(change, key):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for section, value in change.items():
        if isinstance(value, dict):
            cfg[section].update(value)
        else:
            cfg[section] = value
    with pytest.raises(LiqError) as caught:
        LiquefactionAnalysis(cfg).run()
    assert caught.value.key == key


@pytest.mark.parametrize("layer, key", [
    ({"gamma_sat": 9.0}, "err_gamma"),
    ({"FC": 120.0}, "err_fines"),
    ({"PI": -1.0}, "err_limits"),
    ({"LL": 20.0, "PI": 30.0}, "err_pi_ll"),
])
def test_impossible_layers_are_refused(layer, key):
    with pytest.raises(LiqError) as caught:
        LiquefactionAnalysis(one_layer(**layer))
    assert caught.value.key == key
