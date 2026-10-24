"""The generalised Hoek–Brown criterion, checked against hand calculations and
against the properties the 2002 paper derives it from."""
import math

import numpy as np
import pytest

from slipsurface.rock import hoekbrown as hb


def test_the_constants_by_hand():
    k = hb.constants(55, 17, 0.0)
    assert k["mb"] == pytest.approx(17 * math.exp(-45 / 28), rel=1e-12)
    assert k["s"] == pytest.approx(math.exp(-5), rel=1e-12)
    assert k["a"] == pytest.approx(0.5 + (math.exp(-55 / 15) - math.exp(-20 / 3)) / 6,
                                   rel=1e-12)
    assert k["mb"] == pytest.approx(3.40781, abs=5e-5)
    assert k["a"] == pytest.approx(0.504048, abs=5e-6)


def test_intact_rock_is_the_original_criterion():
    k = hb.constants(100, 12, 0.0)
    assert k["mb"] == pytest.approx(12) and k["s"] == pytest.approx(1)
    assert k["a"] == pytest.approx(0.5)
    # σ1 = σ3 + σci·√(mi·σ3/σci + 1)
    assert hb.sigma1(10.0, 80.0, 12, 1, 0.5) == pytest.approx(10 + 80 * math.sqrt(1.5 + 1))


def test_disturbance_weakens_the_rock_mass():
    undisturbed, disturbed = hb.constants(50, 10, 0.0), hb.constants(50, 10, 1.0)
    assert disturbed["mb"] < undisturbed["mb"] and disturbed["s"] < undisturbed["s"]
    assert disturbed["a"] == undisturbed["a"]


def test_the_strengths():
    k = hb.constants(55, 17, 0.0)
    mb, s, a = k["mb"], k["s"], k["a"]
    st = hb.tensile_strength(60, mb, s)
    assert st == pytest.approx(-s * 60 / mb)
    # the criterion passes through (σt, σt) … and through (0, σc)
    assert hb.sigma1(0.0, 60, mb, s, a) == pytest.approx(hb.uniaxial_strength(60, s, a))
    assert hb.sigma1(st, 60, mb, s, a) == pytest.approx(st, abs=1e-9)
    assert math.isnan(hb.sigma1(2 * st, 60, mb, s, a))


@pytest.mark.parametrize("gsi, mi, D, sci", [(55, 17, 0.0, 60), (30, 10, 0.5, 20),
                                              (80, 25, 0.0, 150), (15, 6, 0.8, 8)])
def test_the_mohr_coulomb_fit_is_the_least_squares_line(gsi, mi, D, sci):
    """Hoek et al. (2002) fit the line to the curve over σt < σ3 < σ3max; the closed
    form must agree with a numerical least-squares fit over that range."""
    k = hb.constants(gsi, mi, D)
    mb, s, a = k["mb"], k["s"], k["a"]
    s3max = sci / 4
    st = hb.tensile_strength(sci, mb, s)
    x = np.linspace(st * (1 - 1e-9), s3max, 40001)
    y = hb.sigma1(x, sci, mb, s, a)
    slope, intercept = np.polyfit(x, y, 1)
    phi = math.degrees(math.asin((slope - 1) / (slope + 1)))
    c = intercept * (1 - math.sin(math.radians(phi))) / (2 * math.cos(math.radians(phi)))
    fit = hb.mohr_coulomb_fit(sci, mb, s, a, s3max)
    assert fit["phi"] == pytest.approx(phi, abs=0.01)
    assert fit["c"] == pytest.approx(c, rel=2e-3)


def test_the_general_fit_reproduces_the_global_strength():
    """σcm is defined as the uniaxial strength of the line fitted up to σci/4."""
    for gsi, mi, D in [(55, 17, 0.0), (35, 8, 0.3), (75, 28, 0.0)]:
        k = hb.constants(gsi, mi, D)
        fit = hb.mohr_coulomb_fit(50.0, k["mb"], k["s"], k["a"], 50.0 / 4)
        assert fit["sigma_cm"] == pytest.approx(
            hb.global_strength(50.0, k["mb"], k["s"], k["a"]), rel=1e-9)


def test_sigma3_max_of_each_application():
    assert hb.sigma3_max("general", 60, 15) == pytest.approx(15)
    # σcm = γH makes the ratio 1, so σ3max is the bare coefficient times σcm
    assert hb.sigma3_max("tunnel", 60, 5.2, 26.0, 200.0) == pytest.approx(0.47 * 5.2)
    assert hb.sigma3_max("slope", 60, 5.2, 26.0, 200.0) == pytest.approx(0.72 * 5.2)
    assert hb.sigma3_max("custom", 60, 5.2, custom=3.3) == 3.3
    # deeper means more confinement
    assert hb.sigma3_max("tunnel", 60, 5, 26, 400) > hb.sigma3_max("tunnel", 60, 5, 26, 100)


def test_the_instantaneous_strength_is_tangent_to_the_mohr_circle():
    k = hb.constants(45, 12, 0.2)
    for s3 in (0.0, 0.5, 2.0, 8.0):
        q = hb.instantaneous(s3, 40, k["mb"], k["s"], k["a"])
        centre, radius = (q["sigma1"] + s3) / 2, (q["sigma1"] - s3) / 2
        phi = math.radians(q["phi"])
        # the tangent line is at the circle's radius from its centre
        assert radius / math.cos(phi) - centre * math.tan(phi) == pytest.approx(q["c"])
        # and the point lies on the circle
        assert (q["sigma_n"] - centre) ** 2 + q["tau"] ** 2 == pytest.approx(radius ** 2)


def test_the_friction_angle_falls_with_confinement():
    k = hb.constants(50, 15, 0.0)
    angles = [hb.instantaneous(s3, 50, k["mb"], k["s"], k["a"])["phi"] for s3 in (0, 1, 5, 20)]
    assert angles == sorted(angles, reverse=True)


def test_the_modulus_estimates_by_hand():
    assert hb.modulus("simplified", 100, 0, 50, 0) == pytest.approx(
        100000 / (1 + math.exp(-25 / 11)))
    assert hb.modulus("generalized", 60, 0, 50, 20000) == pytest.approx(20000 * 0.52)
    assert hb.modulus("hctc2002", 50, 0, 100, 0) == pytest.approx(10000)
    assert hb.modulus("hctc2002", 50, 0, 25, 0) == pytest.approx(5000)
    assert hb.modulus("hctc2002", 50, 0, 400, 0) == pytest.approx(10000)   # root capped at 1
    assert hb.modulus("hctc2002", 50, 1, 100, 0) == pytest.approx(5000)


def test_the_residual_gsi():
    assert hb.residual_gsi(50) == pytest.approx(50 * math.exp(-0.67))
    assert hb.residual_gsi(80) < 80
