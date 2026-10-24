"""The analysis: what it returns, what it warns about, and what it refuses."""
import copy

import pytest

from slipsurface.rock import hoekbrown as hb
from slipsurface.rock.config import DEFAULT_CONFIG, MODULUS_METHODS
from slipsurface.rock.engine import RockAnalysis, RockError


def run(**changes):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for section, values in changes.items():
        if isinstance(values, dict):
            cfg[section].update(values)
        else:
            cfg[section] = values
    analysis = RockAnalysis(cfg)
    return analysis, analysis.run()


def keys(res):
    return [key for key, _ in res["warnings"]]


def test_the_default_project():
    _, res = run()
    assert res["GSI"] == 55
    assert res["hb"]["mb"] == pytest.approx(3.40781, abs=5e-5)
    assert res["sigma3_max"] == pytest.approx(60 / 4)
    assert res["mc"]["c"] == pytest.approx(3.769, abs=1e-3)
    assert res["mc"]["phi"] == pytest.approx(36.59, abs=0.01)
    assert res["modulus"]["Erm"] == pytest.approx(hb.modulus("generalized", 55, 0, 60, 275 * 60))
    assert set(res["modulus"]["all"]) == set(MODULUS_METHODS)
    assert set(res["applications"]) == {"general", "tunnel", "slope"}
    assert res["warnings"] == []


def test_the_application_changes_the_fit_not_the_criterion():
    _, general = run()
    _, tunnel = run(application={"type": "tunnel", "depth": 100.0})
    assert tunnel["hb"] == general["hb"]
    assert tunnel["sigma3_max"] < general["sigma3_max"]
    assert tunnel["mc"]["phi"] > general["mc"]["phi"]         # less confinement, steeper
    assert tunnel["applications"]["general"] == general["applications"]["general"]
    _, custom = run(application={"type": "custom", "sigma3_max": 2.0})
    assert custom["sigma3_max"] == 2.0 and "custom" in custom["applications"]


def test_gsi_comes_from_the_route_chosen():
    assert run(rock_mass={"gsi_source": "rmr", "RMR89": 62})[1]["GSI"] == pytest.approx(57)
    assert run(rock_mass={"gsi_source": "jcond", "JCond89": 16, "RQD": 70})[1]["GSI"] == 59
    res = run(rock_mass={"gsi_source": "chart", "structure": "blocky", "surface": "good"})[1]
    assert res["GSI"] == pytest.approx(1.5 * 21 + 35)


def test_the_laboratory_fit_replaces_sigma_ci_and_mi():
    _, res = run(intact={"source": "lab", "sigma_ci": 1.0, "mi": 1.0})
    fit = res["intact"]["fit"]
    assert res["intact"]["sigma_ci"] == fit["sigma_ci"] == pytest.approx(59.8, abs=0.5)
    assert res["intact"]["mi"] == pytest.approx(17.2, abs=0.5)
    assert fit["r2"] > 0.99


def test_the_residual_strength_is_lower():
    _, res = run()
    r = res["residual"]
    assert r["GSI"] < res["GSI"] and r["c"] < res["mc"]["c"] and r["phi"] < res["mc"]["phi"]


def test_ei_from_mr_or_typed_in():
    _, res = run(modulus={"Ei_source": "direct", "Ei": 30000.0})
    assert res["intact"]["Ei"] == 30000 and res["intact"]["MR"] == pytest.approx(500)


@pytest.mark.parametrize("changes, key", [
    ({"intact": {"sigma_ci": 0.0}}, "err_sigma_ci"),
    ({"intact": {"mi": -1.0}}, "err_mi"),
    ({"rock_mass": {"GSI": 3.0}}, "err_gsi"),
    ({"rock_mass": {"D": 1.5}}, "err_D"),
    ({"rock_mass": {"gsi_source": "q", "Q_prime": 0.0}}, "err_gsi_input"),
    ({"application": {"type": "tunnel", "depth": 0.0}}, "err_depth"),
    ({"application": {"type": "custom", "sigma3_max": 0.0}}, "err_sigma3max"),
    ({"modulus": {"Ei_source": "direct", "Ei": 0.0}}, "err_ei"),
    ({"intact": {"source": "lab"}, "lab_data": [{"sigma3": 0, "sigma1": 50}]}, "err_lab_few"),
])
def test_impossible_input_is_refused_with_a_reason(changes, key):
    with pytest.raises(RockError) as caught:
        run(**changes)
    assert caught.value.key == key


@pytest.mark.parametrize("changes, key", [
    ({"rock_mass": {"gsi_source": "rmr", "RMR89": 20}}, "warn_rmr_low"),
    ({"rock_mass": {"GSI": 92}}, "warn_gsi_high"),
    ({"intact": {"mi": 30.0}}, "warn_mi_range"),
    ({"modulus": {"MR": 900.0}}, "warn_mr_range"),
    ({"application": {"type": "tunnel"}, "rock_mass": {"D": 0.5}}, "warn_tunnel_D"),
    ({"query": {"sigma3": -5.0}}, "warn_query_tension"),
    ({"modulus": {"method": "simplified", "Ei_source": "direct", "Ei": 1000.0}},
     "warn_erm_above_ei"),
    ({"intact": {"source": "lab"},
      "lab_data": [{"sigma3": 0, "sigma1": 60}, {"sigma3": 1, "sigma1": 75},
                   {"sigma3": 2, "sigma1": 85}]}, "warn_lab_narrow"),
])
def test_questionable_input_is_warned_about(changes, key):
    assert key in keys(run(**changes)[1])


def test_the_sweeps_run_over_gsi_and_d():
    analysis, _ = run()
    sweep = analysis.sweep("GSI", [20, 50, 80])
    assert list(sweep["phi"]) == sorted(sweep["phi"])
    sweep = analysis.sweep("D", [0.0, 0.5, 1.0])
    assert list(sweep["c"]) == sorted(sweep["c"], reverse=True)


def test_the_curves_start_at_the_tensile_strength():
    _, res = run()
    curves = res["curves"]
    assert curves["sigma3"][0] == pytest.approx(res["strength"]["sigma_t"], rel=1e-6)
    assert curves["sigma3"][-1] > res["sigma3_max"]


def test_an_independent_program_agrees():
    """ORMAS V2.0 (Geraili Mikola), same inputs: σci = 60 MPa, GSI = 55, mi = 32, D = 0,
    Ei = 25 500 MPa, custom σ3max = 7.5 MPa, Hoek & Diederichs (2006) generalised."""
    _, res = run(intact={"sigma_ci": 60.0, "mi": 32.0, "rock_type": "custom"},
                 rock_mass={"GSI": 55.0, "D": 0.0},
                 modulus={"method": "generalized", "Ei_source": "direct", "Ei": 25500.0},
                 application={"type": "custom", "sigma3_max": 7.5})
    assert res["hb"]["mb"] == pytest.approx(6.4147, abs=5e-5)
    assert res["hb"]["s"] == pytest.approx(0.0067, abs=5e-5)
    assert res["hb"]["a"] == pytest.approx(0.5040, abs=5e-5)
    assert res["strength"]["sigma_t"] == pytest.approx(-0.0630, abs=5e-5)
    assert res["strength"]["sigma_c"] == pytest.approx(4.8264, abs=5e-5)
    assert res["strength"]["sigma_cm"] == pytest.approx(20.3483, abs=5e-5)
    assert res["modulus"]["Erm"] == pytest.approx(10411.16, abs=5e-3)
    assert res["mc"]["c"] == pytest.approx(2.8072, abs=5e-5)
    assert res["mc"]["phi"] == pytest.approx(47.82, abs=5e-3)
