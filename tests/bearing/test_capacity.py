"""
The general bearing capacity equation, the effective area and the contact
pressure, each against a hand calculation.
"""
import math

import pytest

from slipsurface.bearing import capacity as cap
from slipsurface.common.factors import bearing_factors

PLAIN = dict(use_shape=False, use_depth=False, use_inclination=False,
             use_base=False, use_ground=False)


def test_a_strip_on_sand_is_the_three_terms_by_hand():
    N = bearing_factors(30, "terzaghi")
    got = cap.ultimate("terzaghi", c=0.0, phi=30, gamma=18.0, q=18.0, B=2.0, L=1e6,
                       Df=1.0, shape="strip", **PLAIN)
    expected = 18.0 * N["Nq"] + 0.5 * 18.0 * 2.0 * N["Ngamma"]
    assert got["q_ult"] == pytest.approx(expected)
    assert got["terms"]["c"] == 0.0
    assert got["q_net_ult"] == pytest.approx(expected - 18.0)


def test_a_surface_strip_on_clay_is_prandtls_five_one_four():
    for method in ("meyerhof", "hansen", "vesic", "ec7"):
        got = cap.ultimate(method, c=100.0, phi=0.0, gamma=18.0, q=0.0, B=2.0, L=1e6,
                           Df=0.0, shape="strip", **PLAIN)
        assert got["q_ult"] == pytest.approx((math.pi + 2) * 100.0, abs=0.5), method


def test_terzaghis_own_undrained_value_is_five_point_seven():
    got = cap.ultimate("terzaghi", c=100.0, phi=0.0, gamma=18.0, q=0.0, B=2.0, L=1e6,
                       Df=0.0, shape="strip", **PLAIN)
    assert got["q_ult"] == pytest.approx(570.0)


def test_the_surcharge_term_is_the_only_one_a_weightless_soil_has():
    got = cap.ultimate("vesic", c=0.0, phi=35, gamma=0.0, q=50.0, B=3.0, L=6.0, Df=2.0,
                       **PLAIN)
    assert got["terms"]["g"] == 0.0
    assert got["q_ult"] == pytest.approx(50.0 * bearing_factors(35, "vesic")["Nq"])


def test_hansens_undrained_expression_is_additive_not_multiplied():
    """5.14·cu·(1 + s'c + d'c − i'c − b'c − g'c) + q, with nothing to correct."""
    got = cap.ultimate("hansen", c=80.0, phi=0.0, gamma=19.0, q=30.0, B=2.0, L=1e6,
                       Df=0.0, shape="strip", use_shape=True, use_depth=True,
                       use_inclination=True, use_base=True, use_ground=True,
                       V=1000.0, area=100.0)
    assert got["form"] == "additive"
    assert got["q_ult"] == pytest.approx(5.14 * 80.0 + 30.0)


def test_hansens_undrained_corrections_only_ever_subtract_or_add_once():
    """A tilted base and a horizontal load both have to reduce the capacity."""
    plain = cap.ultimate("hansen", c=80.0, phi=0.0, gamma=19.0, q=30.0, B=2.0, L=4.0,
                         Df=1.0, V=1000.0, Hb=0.0, area=8.0, eta=0.0)
    tilted = cap.ultimate("hansen", c=80.0, phi=0.0, gamma=19.0, q=30.0, B=2.0, L=4.0,
                          Df=1.0, V=1000.0, Hb=0.0, area=8.0, eta=10.0)
    pushed = cap.ultimate("hansen", c=80.0, phi=0.0, gamma=19.0, q=30.0, B=2.0, L=4.0,
                          Df=1.0, V=1000.0, Hb=200.0, area=8.0, eta=0.0)
    assert tilted["q_ult"] < plain["q_ult"]
    assert pushed["q_ult"] < plain["q_ult"]


def test_every_method_falls_when_the_load_is_inclined():
    for method in ("meyerhof", "hansen", "vesic", "ec7"):
        straight = cap.ultimate(method, c=10.0, phi=30, gamma=18.0, q=27.0, B=2.0,
                                L=4.0, Df=1.5, V=1000.0, Hb=0.0, area=8.0)
        leaning = cap.ultimate(method, c=10.0, phi=30, gamma=18.0, q=27.0, B=2.0,
                               L=4.0, Df=1.5, V=1000.0, Hb=300.0, area=8.0)
        assert leaning["q_ult"] < straight["q_ult"], method


# --------------------------------------------------------------------------- #
#  Effective area
# --------------------------------------------------------------------------- #

def test_meyerhofs_effective_area_takes_twice_the_eccentricity_off_the_width():
    got = cap.effective_area("rectangle", 3.0, 5.0, 1000.0, 300.0, 0.0)
    assert got["e_B"] == pytest.approx(0.3)
    assert got["B_eff"] == pytest.approx(3.0 - 0.6)
    assert got["L_eff"] == pytest.approx(5.0)
    assert got["A_eff"] == pytest.approx(2.4 * 5.0)


def test_the_effective_dimensions_come_back_with_the_short_one_first():
    """The factors are written for B ≤ L, so a long eccentricity swaps them."""
    got = cap.effective_area("rectangle", 3.0, 3.2, 1000.0, 0.0, 800.0)
    assert got["B_eff"] <= got["L_eff"]
    assert got["A_eff"] == pytest.approx(3.0 * (3.2 - 1.6))


def test_switching_the_effective_area_off_keeps_the_whole_base():
    got = cap.effective_area("rectangle", 3.0, 5.0, 1000.0, 300.0, 0.0,
                             use_effective=False)
    assert got["A_eff"] == pytest.approx(15.0)
    assert got["e_B"] == pytest.approx(0.3)      # still reported, for the check


def test_a_circle_loses_a_segment_and_keeps_its_area():
    radius = 1.5
    got = cap.effective_area("circle", 2 * radius, 2 * radius, 1000.0, 400.0, 0.0)
    e = got["e_B"]
    expected = 2.0 * (radius ** 2 * math.acos(e / radius)
                      - e * math.sqrt(radius ** 2 - e ** 2))
    assert got["A_eff"] == pytest.approx(expected)
    assert got["B_eff"] * got["L_eff"] == pytest.approx(expected)
    assert got["A_eff"] < math.pi * radius ** 2


def test_a_resultant_off_the_base_leaves_no_effective_area():
    got = cap.effective_area("rectangle", 2.0, 4.0, 100.0, 150.0, 0.0)
    assert got["A_eff"] == 0.0


# --------------------------------------------------------------------------- #
#  Contact pressure
# --------------------------------------------------------------------------- #

def test_a_central_load_presses_evenly():
    got = cap.contact_pressure("rectangle", 2.0, 4.0, 800.0, 0.0, 0.0)
    assert got["q_max"] == pytest.approx(100.0)
    assert got["q_min"] == pytest.approx(100.0)
    assert got["in_kern"]


def test_inside_the_middle_third_the_pressure_is_the_trapezoid_by_hand():
    B, L, V, M = 2.0, 4.0, 800.0, 200.0        # e = 0.25 m = B/8 < B/6
    got = cap.contact_pressure("rectangle", B, L, V, M, 0.0)
    mean = V / (B * L)
    assert got["q_max"] == pytest.approx(mean * (1 + 6 * 0.25 / B))
    assert got["q_min"] == pytest.approx(mean * (1 - 6 * 0.25 / B))
    assert got["in_kern"]


def test_at_the_kern_the_minimum_pressure_is_exactly_zero():
    B, L, V = 3.0, 4.0, 900.0
    got = cap.contact_pressure("rectangle", B, L, V, V * B / 6.0, 0.0)
    assert got["q_min"] == pytest.approx(0.0, abs=1e-9)
    assert got["in_kern"]


def test_outside_the_kern_the_base_lifts_and_the_diagram_is_triangular():
    B, L, V, e = 3.0, 4.0, 900.0, 0.75         # e = B/4 > B/6
    got = cap.contact_pressure("rectangle", B, L, V, V * e, 0.0)
    assert not got["in_kern"]
    contact = 3.0 * (B / 2 - e)
    assert got["contact"] == pytest.approx(contact)
    assert got["q_max"] == pytest.approx(2 * V / (L * contact))
    # the triangle still carries the whole load
    assert 0.5 * got["q_max"] * contact * L == pytest.approx(V)


# --------------------------------------------------------------------------- #
#  The failure zone
# --------------------------------------------------------------------------- #

def test_the_prandtl_zone_is_seven_tenths_of_the_width_at_zero_friction():
    assert cap.wedge_depth(1.0, 0.0) == pytest.approx(1 / math.sqrt(2), abs=1e-6)


def test_the_failure_zone_deepens_with_the_friction_angle():
    depths = [cap.wedge_depth(2.0, phi) for phi in range(0, 45, 5)]
    assert depths == sorted(depths)


def test_the_drawn_mechanism_agrees_with_the_depth_it_reports():
    for phi in (0, 20, 35):
        mech = cap.wedge_geometry(2.0, phi)
        deepest = max(z for _, z in mech["spiral"])
        assert deepest == pytest.approx(mech["depth"], rel=1e-3)
        assert mech["apex"] == pytest.approx(math.tan(math.radians(45 + phi / 2)))
        assert mech["passive"][-1][1] == pytest.approx(0.0)   # it reaches the surface


# --------------------------------------------------------------------------- #
#  Sliding
# --------------------------------------------------------------------------- #

def test_sliding_is_friction_plus_adhesion():
    got = cap.sliding_resistance(1000.0, 8.0, 5.0, 30.0, delta_ratio=1.0)
    assert got["friction"] == pytest.approx(1000.0 * math.tan(math.radians(30)))
    assert got["adhesion"] == pytest.approx(40.0)
    assert got["R"] == pytest.approx(got["friction"] + got["adhesion"])


def test_undrained_sliding_is_the_adhesion_alone():
    got = cap.sliding_resistance(1000.0, 8.0, 90.0, 0.0, undrained=True)
    assert got["R"] == pytest.approx(8.0 * 90.0)
    assert got["friction"] == 0.0


def test_a_precast_base_slides_more_easily_than_one_cast_in_place():
    cast = cap.sliding_resistance(1000.0, 8.0, 0.0, 30.0, delta_ratio=1.0)
    precast = cap.sliding_resistance(1000.0, 8.0, 0.0, 30.0, delta_ratio=2 / 3)
    assert precast["R"] < cast["R"]
