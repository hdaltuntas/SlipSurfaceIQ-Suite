"""
The bearing capacity analysis against hand calculations, and its handling of
the inputs it has to refuse or warn about.
"""
import copy
import math

import pytest

from slipsurface.bearing.capacity import wedge_depth
from slipsurface.bearing.config import DEFAULT_CONFIG
from slipsurface.bearing.engine import BearingAnalysis, BearingError


def cfg(**changes):
    """The default project with some sections changed."""
    c = copy.deepcopy(DEFAULT_CONFIG)
    for section, values in changes.items():
        if isinstance(values, dict):
            c[section].update(values)
        else:
            c[section] = values
    return c


def layer(**kw):
    base = {"name": "Layer", "thickness": 20.0, "behaviour": "granular", "gamma": 18.0,
            "gamma_sat": 20.0, "c": 0.0, "phi": 30.0, "cu": 0.0, "E": 25.0, "nu": 0.3}
    base.update(kw)
    return base


@pytest.fixture(scope="module")
def default():
    a = BearingAnalysis(DEFAULT_CONFIG)
    a.run()
    return a


# --------------------------------------------------------------------------- #
#  In-situ stresses and geometry
# --------------------------------------------------------------------------- #

def test_the_in_situ_stresses_are_the_ones_computed_by_hand(default):
    P = default.profile
    # fill 1.5 m × 18 above the water table (2 m), then clay 0.5 m × 19,
    # then 2 m of saturated clay × 19.5
    sigma = 1.5 * 18.0 + 0.5 * 19.0 + 2.0 * 19.5
    assert P.total_stress(4.0) == pytest.approx(sigma)
    assert P.pore_pressure(4.0) == pytest.approx(2.0 * 9.81)
    assert P.effective_stress(4.0) == pytest.approx(sigma - 2.0 * 9.81)


def test_the_surcharge_at_the_base_is_the_overburden_above_it(default):
    assert default.results["surcharge"]["total"] == pytest.approx(1.5 * 18.0)
    assert default.results["surcharge"]["effective"] == pytest.approx(27.0)


def test_the_failure_zone_is_the_prandtl_depth_of_the_effective_width(default):
    res = default.results
    phi = res["params"]["drained"]["phi"]
    expected = wedge_depth(res["geometry"]["B_eff"], phi)
    assert res["zone"]["drained"] == pytest.approx(expected, rel=1e-6)


def test_the_strength_is_averaged_through_the_tangent_of_the_friction_angle():
    """Two layers of equal thickness in the range: tan φ averages, not φ."""
    a = BearingAnalysis(cfg(groundwater={"depth": 100.0},
                            soil_profile=[layer(thickness=1.0, phi=20.0, c=10.0),
                                          layer(thickness=5.0, phi=40.0, c=0.0)]))
    got = a.profile.average(0.0, 2.0)
    expected = 0.5 * (math.tan(math.radians(20)) + math.tan(math.radians(40)))
    assert math.tan(math.radians(got["phi"])) == pytest.approx(expected)
    assert got["c"] == pytest.approx(5.0)
    assert got["layers"] == ["Layer", "Layer"]


def test_a_submerged_soil_is_weighed_buoyant_below_the_base():
    dry = BearingAnalysis(cfg(groundwater={"depth": 100.0},
                              soil_profile=[layer(gamma=18.0, gamma_sat=20.0)])).run()
    wet = BearingAnalysis(cfg(groundwater={"depth": 0.0},
                              soil_profile=[layer(gamma=18.0, gamma_sat=20.0)])).run()
    assert wet["params"]["drained"]["gamma"] == pytest.approx(20.0 - 9.81)
    assert wet["q_ult"] < dry["q_ult"]


# --------------------------------------------------------------------------- #
#  The capacity itself
# --------------------------------------------------------------------------- #

def test_a_square_footing_on_sand_matches_the_hand_calculation():
    """Vesić, square 2 × 2 m at 1 m in dry sand: every factor written out."""
    from slipsurface.common.factors import bearing_factors
    a = BearingAnalysis(cfg(
        foundation={"shape": "square", "B": 2.0, "Df": 1.0, "base_tilt": 0,
                    "ground_slope": 0},
        loading={"V": 500.0, "Hb": 0.0, "Hl": 0.0, "Mb": 0.0, "Ml": 0.0},
        groundwater={"depth": 100.0},
        options={"method": "vesic", "analysis": "drained", "compressibility": False},
        soil_profile=[layer(phi=32.0, gamma=18.5)]))
    res = a.run()
    N = bearing_factors(32.0, "vesic")
    q = 18.5 * 1.0
    sq = 1.0 + math.tan(math.radians(32.0))
    sg = 1.0 - 0.4
    k = 1.0 / 2.0                                  # D/B = 0.5 ≤ 1
    dq = 1.0 + 2.0 * math.tan(math.radians(32.0)) * (1 - math.sin(math.radians(32.0))) ** 2 * k
    expected = q * N["Nq"] * sq * dq + 0.5 * 18.5 * 2.0 * N["Ngamma"] * sg
    assert res["methods"]["vesic"]["q_ult"] == pytest.approx(expected, rel=1e-6)


def test_every_method_runs_and_lands_in_the_same_neighbourhood(default):
    values = [entry["q_ult"] for entry in default.results["methods"].values()]
    assert len(values) == 6
    assert min(values) > 0
    assert max(values) / min(values) < 2.0


def test_whichever_analysis_governs_is_the_one_reported(default):
    for entry in default.results["methods"].values():
        governing = entry["runs"][entry["governing"]]
        assert entry["q_net_ult"] == pytest.approx(governing["q_net_ult"])
        assert all(governing["q_net_ult"] <= run["q_net_ult"] + 1e-9
                   for run in entry["runs"].values())


def test_a_drained_only_run_leaves_skempton_out():
    res = BearingAnalysis(cfg(options={"analysis": "drained"})).run()
    assert "skempton" not in res["methods"]
    assert all(entry["governing"] == "drained" for entry in res["methods"].values())


def test_the_undrained_strength_ignores_the_sand_in_the_zone():
    a = BearingAnalysis(cfg(soil_profile=[layer(thickness=1.0),
                                          layer(thickness=5.0, behaviour="cohesive",
                                                phi=0.0, cu=60.0)]))
    assert a.profile.average(0.0, 3.0)["cu"] == pytest.approx(60.0)


def test_a_granular_profile_has_no_undrained_capacity():
    res = BearingAnalysis(cfg(soil_profile=[layer(cu=0.0)])).run()
    assert all(entry["governing"] == "drained" for entry in res["methods"].values())
    assert "skempton" not in res["methods"]


def test_local_shear_never_gives_more_than_general_shear():
    general = BearingAnalysis(cfg(options={"shear": "general"})).run()
    local = BearingAnalysis(cfg(options={"shear": "local"})).run()
    assert local["q_ult"] < general["q_ult"]


def test_switching_the_corrections_off_leaves_the_bare_equation():
    res = BearingAnalysis(cfg(options={
        "shape_factors": False, "depth_factors": False, "inclination_factors": False,
        "base_factors": False, "ground_factors": False})).run()
    for entry in res["methods"].values():
        for name in ("shape", "depth", "inclination", "base", "ground"):
            factor = entry["factors"][name]
            assert factor["q"] == 1.0 and factor["g"] == 1.0


def test_a_deeper_footing_carries_more():
    shallow = BearingAnalysis(cfg(foundation={"Df": 0.5})).run()
    deep = BearingAnalysis(cfg(foundation={"Df": 2.5})).run()
    assert deep["q_ult"] > shallow["q_ult"]


def test_a_tilted_base_and_a_sloping_ground_both_cost_capacity():
    flat = BearingAnalysis(cfg()).run()
    tilted = BearingAnalysis(cfg(foundation={"base_tilt": 10.0})).run()
    sloping = BearingAnalysis(cfg(foundation={"ground_slope": 10.0})).run()
    assert tilted["q_ult"] < flat["q_ult"]
    assert sloping["q_ult"] < flat["q_ult"]


# --------------------------------------------------------------------------- #
#  Checks
# --------------------------------------------------------------------------- #

def test_the_factor_of_safety_is_taken_on_the_net_capacity(default):
    res = default.results
    bearing = res["checks"]["bearing"]
    assert bearing["actual"] == pytest.approx(
        res["q_net_ult"] / bearing["q_net_applied"])
    assert bearing["q_all"] == pytest.approx(
        res["q_net_ult"] / default.FS + res["surcharge"]["effective"])


def test_the_required_width_is_where_the_utilisation_reaches_one(default):
    width = default.results["required_width"]
    assert math.isfinite(width)
    assert default.utilisation_for_width(width * 1.02) < 1.0
    assert default.utilisation_for_width(width * 0.95) > 1.0


def test_a_hopeless_footing_reports_no_required_width():
    res = BearingAnalysis(cfg(loading={"V": 5.0e6, "Mb": 0.0, "Hb": 0.0})).run()
    assert not math.isfinite(res["required_width"])


def test_sliding_is_checked_against_the_horizontal_load(default):
    slide = default.results["checks"]["sliding"]
    assert slide["actual"] == pytest.approx(slide["resistance"] / slide["H"])
    assert slide["status"] in ("OK", "NOT OK")


def test_no_horizontal_load_means_no_sliding_check():
    res = BearingAnalysis(cfg(loading={"Hb": 0.0, "Hl": 0.0})).run()
    assert res["checks"]["sliding"]["status"] == "N/A"


def test_the_eccentricity_check_is_the_middle_third(default):
    ecc = default.results["checks"]["eccentricity"]
    assert ecc["allowable"] == pytest.approx(1 / 6)
    assert ecc["actual"] == pytest.approx(default.results["geometry"]["e_B"] / default.B)


# --------------------------------------------------------------------------- #
#  Eurocode 7
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("approach,count", [("da1", 2), ("da2", 1), ("da3", 1)])
def test_each_design_approach_runs_its_combinations(approach, count):
    res = BearingAnalysis(cfg(criteria={"approach": approach})).run()
    ec7 = res["eurocode"]
    assert len(ec7["combinations"]) == count
    for comb in ec7["combinations"]:
        assert comb["Ed"] > 0 and comb["Rd"] > 0
        assert comb["utilisation"] == pytest.approx(comb["Ed"] / comb["Rd"])
        assert comb["status"] == ("OK" if comb["Ed"] <= comb["Rd"] else "NOT OK")


def test_the_material_factors_reach_the_design_strength():
    res = BearingAnalysis(cfg(criteria={"approach": "da3"})).run()
    comb = res["eurocode"]["combinations"][0]
    characteristic = res["params"]["drained"]
    assert comb["c_d"] == pytest.approx(characteristic["c"] / 1.25)
    assert math.tan(math.radians(comb["phi_d"])) == pytest.approx(
        math.tan(math.radians(characteristic["phi"])) / 1.25)


def test_the_worst_combination_is_the_one_reported():
    res = BearingAnalysis(cfg(criteria={"approach": "da1"})).run()
    ec7 = res["eurocode"]
    worst = max(c["utilisation"] for c in ec7["combinations"])
    assert ec7["utilisation"] == pytest.approx(worst)


def test_a_factor_of_safety_run_has_no_eurocode_block(default):
    assert default.results["eurocode"] is None


# --------------------------------------------------------------------------- #
#  Two layers, in-situ, rock, earthquake
# --------------------------------------------------------------------------- #

def test_punching_through_a_thin_strong_layer_costs_capacity():
    profile = [layer(name="Dense sand", thickness=1.0, phi=40.0, gamma=20.0),
               layer(name="Soft clay", thickness=15.0, behaviour="cohesive", phi=0.0,
                     c=0.0, cu=25.0, gamma=17.0, gamma_sat=17.5)]
    vertical = {"V": 400.0, "Hb": 0.0, "Hl": 0.0, "Mb": 0.0, "Ml": 0.0}
    averaged = BearingAnalysis(cfg(foundation={"Df": 0.0, "B": 2.0}, loading=vertical,
                                   soil_profile=profile)).run()
    punched = BearingAnalysis(cfg(foundation={"Df": 0.0, "B": 2.0}, loading=vertical,
                                  options={"layer_model": "two_layer"},
                                  soil_profile=profile)).run()
    assert "punching" in punched["others"]
    detail = punched["others"]["punching"]["detail"]
    # the sand alone would carry far more than the clay under it lets it
    assert detail["q_ult"] < detail["q_top"]
    # q_b + side friction − γ₁·H, the pieces of Meyerhof & Hanna's expression
    assert detail["q_ult"] == pytest.approx(
        detail["q_bottom"] + detail["adhesion"] + detail["friction"] - 20.0 * 1.0)
    assert averaged["q_ult"] > 0


def test_punching_can_never_beat_the_strong_layer_on_its_own():
    profile = [layer(name="Dense sand", thickness=4.0, phi=40.0),
               layer(name="Soft clay", thickness=15.0, behaviour="cohesive", phi=0.0,
                     c=0.0, cu=25.0)]
    res = BearingAnalysis(cfg(foundation={"Df": 0.0, "B": 1.0},
                              options={"layer_model": "two_layer"},
                              soil_profile=profile)).run()
    detail = res["others"]["punching"]["detail"]
    assert detail["q_ult"] <= detail["q_top"] + 1e-9


def test_the_spread_model_also_finds_the_weak_layer():
    profile = [layer(name="Crust", thickness=1.0, phi=38.0),
               layer(name="Soft clay", thickness=15.0, behaviour="cohesive", phi=0.0,
                     c=0.0, cu=20.0)]
    res = BearingAnalysis(cfg(foundation={"Df": 0.0, "B": 2.0},
                              options={"layer_model": "two_layer",
                                       "two_layer_model": "spread"},
                              soil_profile=profile)).run()
    assert "spread" in res["others"]
    assert res["others"]["spread"]["q_ult"] > 0


def test_an_in_situ_test_joins_the_comparison():
    res = BearingAnalysis(cfg(insitu={"enabled": True, "test": "spt", "N60": 25})).run()
    assert "spt" in res["others"]
    assert res["others"]["spt"]["q_all"] > 0
    assert res["others"]["spt"]["settlement_rule"]


def test_the_pressuremeter_gives_an_ultimate_capacity():
    res = BearingAnalysis(cfg(insitu={"enabled": True, "test": "pmt", "pl": 1.2,
                                      "p0": 0.05})).run()
    assert res["others"]["pmt"]["q_net_ult"] > 0


def test_rock_runs_the_same_equation_on_an_equivalent_strength():
    res = BearingAnalysis(cfg(rock={"enabled": True, "sigma_ci": 40.0, "GSI": 50.0,
                                    "mi": 12.0})).run()
    assert "hoek_brown" in res["others"]
    detail = res["others"]["hoek_brown"]["detail"]
    assert 0 < detail["phi"] < 70 and detail["c"] > 0


def test_an_earthquake_reduces_the_capacity():
    quiet = BearingAnalysis(cfg()).run()
    shaken = BearingAnalysis(cfg(seismic={"enabled": True, "kh": 0.15})).run()
    assert shaken["q_ult"] < quiet["q_ult"]
    assert shaken["applied"]["H"] > quiet["applied"]["H"]


def test_the_soil_inertia_can_be_left_out_of_the_earthquake():
    both = BearingAnalysis(cfg(seismic={"enabled": True, "kh": 0.15,
                                        "soil_inertia": True})).run()
    structure_only = BearingAnalysis(cfg(seismic={"enabled": True, "kh": 0.15,
                                                  "soil_inertia": False})).run()
    assert both["q_ult"] < structure_only["q_ult"]


# --------------------------------------------------------------------------- #
#  Refusals and warnings
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("key,changes", [
    ("err_dimensions", {"foundation": {"B": 0.0}}),
    ("err_depth", {"foundation": {"Df": -1.0}}),
    ("err_tilt", {"foundation": {"base_tilt": 60.0, "ground_slope": 40.0}}),
    ("err_load", {"loading": {"V": 0.0}}),
    ("err_base_below", {"foundation": {"Df": 50.0}}),
    ("err_eccentricity", {"loading": {"V": 100.0, "Mb": 1000.0}}),
])
def test_an_impossible_input_is_refused_with_its_own_message(key, changes):
    with pytest.raises(BearingError) as caught:
        BearingAnalysis(cfg(**changes)).run()
    assert caught.value.key == key


def test_a_layer_without_any_strength_is_refused():
    with pytest.raises(BearingError) as caught:
        BearingAnalysis(cfg(soil_profile=[layer(phi=0.0, c=0.0, cu=0.0)])).run()
    assert caught.value.key == "err_no_strength"


def test_an_empty_profile_is_refused():
    with pytest.raises(BearingError) as caught:
        BearingAnalysis(cfg(soil_profile=[])).run()
    assert caught.value.key == "err_no_layers"


def test_a_short_rectangle_is_swapped_and_says_so():
    res = BearingAnalysis(cfg(foundation={"B": 4.0, "L": 2.0})).run()
    assert ("warn_swapped", {}) in res["warnings"]


def test_leaving_the_middle_third_is_warned_about():
    res = BearingAnalysis(cfg(loading={"V": 1000.0, "Mb": 600.0})).run()
    assert any(key == "warn_kern" for key, _ in res["warnings"])
    assert not res["pressure"]["in_kern"]


def test_terzaghi_says_it_cannot_take_the_horizontal_load():
    res = BearingAnalysis(cfg(options={"method": "terzaghi"},
                              loading={"Hb": 200.0})).run()
    assert any(key == "warn_no_inclination" for key, _ in res["warnings"])
