"""Earth pressure coefficients against their closed forms and published values."""
import math

import pytest

from slipsurface.wall import earth


def test_rankine_level_backfill_is_tan_squared():
    for phi in (20, 25, 30, 35, 40):
        assert earth.rankine_ka(phi) == pytest.approx(math.tan(math.radians(45 - phi / 2)) ** 2)
        assert earth.rankine_kp(phi) == pytest.approx(math.tan(math.radians(45 + phi / 2)) ** 2)


def test_rankine_sloping_backfill_equals_coulomb_with_delta_equal_to_beta():
    """Behind a vertical back, Coulomb with δ = β is Rankine's sloping backfill."""
    for phi, beta in ((30, 10), (32, 15), (35, 20), (28, 5)):
        assert earth.rankine_ka(phi, beta) == pytest.approx(
            earth.coulomb_ka(phi, 90.0, beta, beta), rel=1e-9)


def test_rankine_sloping_value():
    # φ = 30°, β = 10°: cos β (cos β − √(cos²β − cos²φ)) / (cos β + √(…)) = 0.3495
    assert earth.rankine_ka(30, 10) == pytest.approx(0.3495, abs=5e-4)


def test_a_slope_steeper_than_phi_is_refused():
    with pytest.raises(ValueError):
        earth.rankine_ka(30, 31)
    with pytest.raises(ValueError):
        earth.coulomb_ka(30, 90, 0, 31)


def test_coulomb_published_values():
    assert earth.coulomb_ka(30, 90, 0, 0) == pytest.approx(1 / 3)
    # Das, Principles of Foundation Engineering: φ = 30°, δ = 20°, vertical back
    assert earth.coulomb_ka(30, 90, 20, 0) == pytest.approx(0.2973, abs=5e-4)
    # passive, φ = 30°, δ = 10°
    assert earth.coulomb_kp(30, 90, 10, 0) == pytest.approx(4.14, abs=0.01)
    assert earth.coulomb_kp(30, 90, 0, 0) == pytest.approx(3.0)


def test_k0_is_jaky_and_grows_with_ocr_and_slope():
    assert earth.k0(30) == pytest.approx(0.5)
    assert earth.k0(30, OCR=4.0) == pytest.approx(1.0)
    assert earth.k0(30, beta=10) == pytest.approx(0.5 * (1 + math.sin(math.radians(10))))


@pytest.mark.parametrize("phi,delta,beta", [(30, 0, 0), (32, 21.44, 0), (35, 20, 10),
                                            (28, 18, 15), (40, 0, 20)])
def test_the_trial_wedge_reproduces_coulomb(phi, delta, beta):
    wedge = earth.trial_wedge(phi, delta, beta, h=6.0, gamma=18.0)
    assert wedge["K"] == pytest.approx(earth.coulomb_ka(phi, 90, delta, beta), rel=2e-4)


def test_the_trial_wedge_finds_rankines_plane():
    wedge = earth.trial_wedge(30, 0, 0, h=5.0, gamma=18.0)
    assert wedge["alpha"] == pytest.approx(earth.rankine_angle(30), abs=0.05)


def test_a_surcharge_does_not_change_the_wedge_coefficient():
    dry = earth.trial_wedge(32, 20, 0, h=6.0, gamma=18.0)
    loaded = earth.trial_wedge(32, 20, 0, h=6.0, gamma=18.0, q=20.0)
    assert loaded["K"] == pytest.approx(dry["K"], rel=1e-4)
    assert loaded["P"] == pytest.approx(dry["K"] * (0.5 * 18 * 36 + 20 * 6), rel=1e-4)


def test_mononobe_okabe_without_acceleration_is_coulomb():
    for phi, delta, beta in ((30, 0, 0), (35, 17.5, 0), (32, 20, 10)):
        mo = earth.mononobe_okabe(phi, 0.0, 0.0, delta, beta)
        assert mo["KAE"] == pytest.approx(earth.coulomb_ka(phi, 90, delta, beta), rel=1e-9)
        assert not mo["limited"]


def test_mononobe_okabe_hand_value():
    # φ = 30°, δ = β = 0, kh = 0.2, kv = 0: ψ = 11.31°, KAE = 0.4732
    mo = earth.mononobe_okabe(30, 0.2)
    assert mo["psi"] == pytest.approx(11.31, abs=0.01)
    assert mo["KAE"] == pytest.approx(0.4732, abs=5e-4)


def test_mononobe_okabe_grows_with_kh_and_with_upward_kv():
    low = earth.mononobe_okabe(32, 0.1)["KAE"]
    high = earth.mononobe_okabe(32, 0.2)["KAE"]
    assert high > low
    assert earth.mononobe_okabe(32, 0.2, 0.1)["KAE"] > earth.mononobe_okabe(32, 0.2, -0.1)["KAE"]


def test_mononobe_okabe_beyond_its_limit_is_flagged():
    mo = earth.mononobe_okabe(30, 0.7, 0.0, 0.0, 10.0)
    assert mo["limited"] and math.isfinite(mo["KAE"])


def test_mononobe_okabe_passive_without_acceleration_is_rankine():
    assert earth.mononobe_okabe_kp(30, 0.0) == pytest.approx(3.0)
    assert earth.mononobe_okabe_kp(30, 0.2) < 3.0


def test_the_simplified_increments():
    assert earth.seed_whitman(0.2) == pytest.approx(0.15)
    assert earth.wood_increment(0.2, 18.0, 6.0) == pytest.approx(0.2 * 18 * 36)
