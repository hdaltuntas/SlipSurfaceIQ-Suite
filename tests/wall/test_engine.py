"""The wall analysis against hand calculations, and its behaviour."""
import copy
import math

import pytest

from slipsurface.wall import earth
from slipsurface.wall.config import DEFAULT_CONFIG
from slipsurface.wall.engine import RetainingWall, WallError, proportions


def config(**changes):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for path, value in changes.items():
        node = cfg
        keys = path.split("__")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return cfg


def wall(**changes):
    return RetainingWall(config(**changes))


def run(**changes):
    w = wall(**changes)
    w.run(with_heel=False, with_global=False, with_design=False)
    return w


# --------------------------------------------------------------------------- #
#  Hand calculation of the default wall
# --------------------------------------------------------------------------- #

def test_weights_by_hand():
    w = wall()
    W = {name: value for name, value, _, _ in w.weights()}
    assert W["W_stem"] == pytest.approx(0.5 * (0.30 + 0.60) * 5.3 * 25)
    assert W["W_footing"] == pytest.approx(4.8 * 0.7 * 25)
    assert W["W_heel_soil"] == pytest.approx((3.0 * 5.3 + 0.5 * 0.3 * 5.3) * 18)
    assert W["W_toe_soil"] == pytest.approx(1.2 * 0.5 * 19)


def test_thrust_and_sliding_by_hand():
    w = run()
    res = w.results
    ka = math.tan(math.radians(45 - 16)) ** 2
    horizontal = {n: (h, y) for n, h, y, _ in res["forces"]["horizontal"]}
    assert horizontal["Pa_h"][0] == pytest.approx(0.5 * ka * 18 * 36, rel=1e-4)
    assert horizontal["Pa_h"][1] == pytest.approx(2.0, abs=1e-3)
    assert horizontal["Pq_live_h"][0] == pytest.approx(ka * 10 * 6, rel=1e-4)
    assert horizontal["Pq_live_h"][1] == pytest.approx(3.0, abs=1e-3)
    V = sum(v for _, v, _, _ in w.weights())
    H = 0.5 * ka * 18 * 36 + ka * 10 * 6
    R = V * math.tan(math.radians(0.67 * 30)) + 0.67 * 5 * 4.8
    assert res["stability"]["sliding"]["value"] == pytest.approx(R / H, rel=1e-4)
    MO = 0.5 * ka * 18 * 36 * 2.0 + ka * 10 * 6 * 3.0
    assert res["forces"]["M_O"] == pytest.approx(MO, rel=1e-4)


def test_the_live_surcharge_on_the_heel_only_counts_for_bearing():
    res = run().results
    slide = [n for n, *_ in res["forces"]["vertical"]]
    bear = [n for n, *_ in res["bearing_forces"]["vertical"]]
    assert "Q_live" not in slide and "Q_live" in bear


def test_the_default_wall_passes_statically():
    res = run().results
    assert all(c["status"] != "NOT OK" for c in res["stability"].values())


def test_eccentricity_and_base_pressure():
    res = run().results
    f = res["bearing_forces"]
    bp = res["bearing"]["pressure"]
    B, V, e = 4.8, f["V"], f["e"]
    assert bp["q_toe"] == pytest.approx(V / B * (1 + 6 * e / B))
    assert bp["q_heel"] == pytest.approx(V / B * (1 - 6 * e / B))
    assert (bp["q_toe"] + bp["q_heel"]) / 2 * B == pytest.approx(V)


def test_the_base_pressure_becomes_a_triangle_beyond_the_middle_third():
    bp = RetainingWall.base_pressure(300.0, 1.0, 4.0)
    assert bp["q_heel"] == 0.0
    assert bp["contact"] == pytest.approx(3 * (2.0 - 1.0))
    assert bp["q_toe"] == pytest.approx(2 * 300 / 3.0)
    heel_side = RetainingWall.base_pressure(300.0, -1.0, 4.0)
    assert heel_side["q_toe"] == 0.0 and heel_side["q_heel"] == pytest.approx(200.0)


def test_bearing_uses_the_effective_width():
    res = run().results
    b = res["bearing"]
    assert b["B_eff"] == pytest.approx(4.8 - 2 * abs(res["bearing_forces"]["e"]))
    assert b["sigma_v"] == pytest.approx(res["bearing_forces"]["V"] / b["B_eff"])
    assert set(b["methods"]) == {"vesic", "meyerhof", "hansen", "terzaghi", "ec7"}
    assert res["stability"]["bearing"]["value"] == pytest.approx(b["q_ult"] / b["sigma_v"])


def test_an_allowable_pressure_is_checked_against_the_peak():
    res = run(options__q_allow=200.0).results
    chk = res["stability"]["allowable"]
    assert chk["status"] == "OK"
    assert chk["value"] == pytest.approx(200.0 / res["bearing"]["pressure"]["q_max"])
    assert run(options__q_allow=50.0).results["stability"]["allowable"]["status"] == "NOT OK"


# --------------------------------------------------------------------------- #
#  Methods
# --------------------------------------------------------------------------- #

def test_every_method_is_compared_and_the_wedge_matches_coulomb():
    m = run().results["methods"]
    assert set(m["active"]) == {"rankine", "coulomb", "at_rest", "trial_wedge"}
    assert m["active"]["trial_wedge"]["K"] == pytest.approx(m["active"]["coulomb"]["K"],
                                                            rel=1e-3)
    assert m["active"]["at_rest"]["K"] > m["active"]["rankine"]["K"]


def test_coulomb_thrust_is_inclined_and_helps():
    rankine = run().results
    coulomb = run(earth__method="coulomb").results
    names = [n for n, *_ in coulomb["forces"]["vertical"]]
    assert "Pa_v" in names
    assert coulomb["stability"]["overturning"]["value"] > rankine["stability"]["overturning"]["value"]


def test_a_backslope_adds_the_vertical_component_of_rankine():
    res = run(geometry__backslope=15.0, loads__q_live=0.0).results
    vertical = {n: v for n, v, _, _ in res["forces"]["vertical"]}
    horizontal = {n: h for n, h, _, _ in res["forces"]["horizontal"]}
    assert vertical["Pa_v"] / horizontal["Pa_h"] == pytest.approx(math.tan(math.radians(15)))
    assert res["K"] == pytest.approx(earth.rankine_ka(32, 15))


def test_water_behind_pushes_and_lifts():
    dry = run().results
    wet = run(soils__water_back=3.0).results
    names = [n for n, *_ in wet["forces"]["horizontal"]]
    assert "Pw_back" in names
    Pw = [h for n, h, _, _ in wet["forces"]["horizontal"] if n == "Pw_back"][0]
    assert Pw == pytest.approx(0.5 * 9.81 * 9.0, rel=1e-4)
    U = [v for n, v, _, _ in wet["forces"]["vertical"] if n == "U"][0]
    assert U == pytest.approx(-0.5 * 9.81 * 3.0 * 4.8)
    assert wet["stability"]["sliding"]["value"] < dry["stability"]["sliding"]["value"]


def test_the_passive_resistance_and_the_key_help_sliding():
    base = run().results["stability"]["sliding"]["value"]
    passive = run(earth__passive=True).results
    assert passive["stability"]["sliding"]["value"] > base
    kp = earth.rankine_kp(30)
    top = 0.7 + 0.5
    expected = 0.5 * kp * 19 * top ** 2 + 2 * 5 * math.sqrt(kp) * top
    assert passive["passive"]["P"] == pytest.approx(expected, rel=1e-3)
    assert passive["resistance"]["passive"] == pytest.approx(0.5 * expected, rel=1e-3)
    keyed = run(key__enabled=True).results
    assert keyed["stability"]["sliding"]["value"] > passive["stability"]["sliding"]["value"]
    assert keyed["passive"]["depth"] == pytest.approx(top + 0.6)


def test_the_front_taper_moves_the_stem_weight():
    back = wall()
    front = wall(geometry__taper="front")
    assert back.geo.thickness(0.7) == pytest.approx(0.6)
    assert front.geo.thickness(6.0) == pytest.approx(0.3)
    xb = {n: x for n, _, x, _ in back.weights()}["W_stem"]
    xf = {n: x for n, _, x, _ in front.weights()}["W_stem"]
    assert xf > xb


# --------------------------------------------------------------------------- #
#  Earthquake
# --------------------------------------------------------------------------- #

def test_the_earthquake_checks_both_directions_of_kv_and_keeps_the_worse():
    w = run(seismic__enabled=True)
    s = w.results["seismic"]
    assert set(s["cases"]) == {"up", "down"}
    for key in ("sliding", "overturning"):
        values = [s["cases"][n]["stability"][key]["value"] for n in ("up", "down")]
        assert s["stability"][key]["value"] == pytest.approx(min(values))
    values = [s["cases"][n]["bearing"]["check"]["value"] for n in ("up", "down")]
    assert s["stability"]["bearing"]["value"] == pytest.approx(min(values))
    co = s["coefficients"]
    assert co["kh"] == pytest.approx(0.5 * 0.4 * s["spectrum"]["SDS"])
    assert s["spectrum"]["SDS"] == pytest.approx(0.80 * 1.2)


def test_the_seismic_forces_hold_the_inertia_and_the_increment():
    w = run(seismic__enabled=True, seismic__mobility="rigid")
    f = w.results["seismic"]["forces"]
    names = [n for n, *_ in f["horizontal"]]
    assert "E_inertia" in names and "dPAE_h" in names
    dyn = w.results["seismic"]["dynamic"]
    mass = sum(W for n, W, _, _ in w.weights() if n != "W_toe_soil")
    assert dyn["W_inertia"] == pytest.approx(mass)
    # Mononobe–Okabe: ΔP = (1 − kv)·KAE·(½γh² + q·h) − Ka·(½γh² + q·h)
    kh, kv = dyn["kh"], dyn["kv"]
    mo = earth.mononobe_okabe(32, kh, kv, 0.0, 0.0)["KAE"]
    load = 0.5 * 18 * 36 + 0.3 * 10 * 6
    ka = earth.rankine_ka(32)
    assert dyn["dP"] == pytest.approx((1 - kv) * mo * load - ka * load, rel=1e-3)


def test_the_simplified_dynamic_thrusts():
    sw = run(seismic__enabled=True, seismic__method="seed_whitman").results["seismic"]
    kh = sw["coefficients"]["kh"]
    load = 0.5 * 18 * 36 + 0.3 * 10 * 6
    assert sw["dynamic"]["dP"] == pytest.approx(0.75 * kh * load, rel=1e-3)
    wood = run(seismic__enabled=True, seismic__method="wood").results["seismic"]
    assert wood["dynamic"]["dP"] == pytest.approx(kh * 18 * 36 + kh * 0.3 * 10 * 6, rel=1e-3)


def test_the_earthquake_is_worse_than_the_static_case():
    res = run(seismic__enabled=True).results
    assert res["seismic"]["stability"]["sliding"]["value"] < res["stability"]["sliding"]["value"]


# --------------------------------------------------------------------------- #
#  The heel the wall needs, and the first guess at the dimensions
# --------------------------------------------------------------------------- #

def test_the_required_heel_is_the_shortest_that_passes():
    w = wall()
    heel = w.required_heel()
    assert 0 < heel < 3.0
    assert w.with_heel(heel).passes()
    assert not w.with_heel(heel - 0.05).passes()


def test_preliminary_dimensions():
    dims = proportions(6.0)
    assert dims["t_bot"] == pytest.approx(0.60)
    assert dims["t_f"] == pytest.approx(0.60)
    B = dims["toe"] + dims["t_bot"] + dims["heel"]
    assert 0.5 * 6 <= B <= 0.75 * 6
    assert proportions(6.0, 20.0)["heel"] > dims["heel"]


# --------------------------------------------------------------------------- #
#  Refused input, warnings
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("changes,key", [
    ({"geometry__H": 0.0}, "err_height"),
    ({"geometry__t_bot": 0.2}, "err_stem"),
    ({"geometry__t_f": 5.9}, "err_footing"),
    ({"geometry__heel": -1.0}, "err_toe_heel"),
    ({"geometry__backslope": 40.0}, "err_backslope"),
    ({"soils__foundation__phi": 0.0, "soils__foundation__c": 0.0}, "err_foundation_strength"),
    ({"key__enabled": True, "key__offset": 10.0}, "err_key"),
    ({"soils__water_back": 9.0}, "err_water"),
    ({"concrete__cover_stem": 200.0}, "err_cover_concrete"),
    ({"seismic__enabled": True, "seismic__dyn_height": 0.9}, "err_seismic"),
])
def test_impossible_input_is_refused_with_a_key(changes, key):
    with pytest.raises(WallError) as caught:
        run(**changes)
    assert caught.value.key == key


def test_warnings():
    keys = [k for k, _ in run(soils__backfill__c=10.0).results["warnings"]]
    assert "warn_cohesion_backfill" in keys
    keys = [k for k, _ in run(earth__method="coulomb",
                              soils__backfill__c=10.0).results["warnings"]]
    assert "warn_cohesion_ignored" in keys
    keys = [k for k, _ in run(key__enabled=True).results["warnings"]]
    assert "warn_key_passive" in keys
    keys = [k for k, _ in run(geometry__heel=0.4).results["warnings"]]
    assert "warn_narrow_base" in keys
