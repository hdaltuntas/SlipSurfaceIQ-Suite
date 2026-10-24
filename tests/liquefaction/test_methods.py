"""
The building blocks against the published expressions, evaluated by hand here
rather than through the code under test: SPT corrections, rd, MSF, Kσ, the
resistance curves, the susceptibility criteria, the volumetric strain, LPI
and LSN.
"""
import math

import numpy as np
import pytest

from slipsurface.liquefaction import consequences as cq
from slipsurface.liquefaction import spt, susceptibility, triggering
from slipsurface.liquefaction.config import PA

# --------------------------------------------------------------------------- #
#  SPT
# --------------------------------------------------------------------------- #

def test_the_energy_borehole_and_rod_factors_follow_youd_et_al():
    assert spt.energy_factor(60) == 1.0
    assert spt.energy_factor(75) == pytest.approx(1.25)
    assert spt.borehole_factor(100) == 1.0
    assert spt.borehole_factor(150) == pytest.approx(1.05)
    assert spt.borehole_factor(200) == pytest.approx(1.15)
    assert list(spt.rod_factor([2.0, 3.5, 5.0, 8.0, 12.0])) == [0.75, 0.80, 0.85, 0.95, 1.0]


def test_the_sampler_factor_is_one_with_liners_and_bounded_without():
    assert list(spt.sampler_factor([5, 20, 40], False)) == [1.0, 1.0, 1.0]
    assert list(spt.sampler_factor([5, 20, 40], True)) == pytest.approx([1.1, 1.2, 1.3])


def test_cn_is_one_at_one_atmosphere_and_capped():
    assert spt.cn_liao_whitman(PA) == pytest.approx(1.0)
    assert spt.cn_liao_whitman(4 * PA) == pytest.approx(0.5)
    assert spt.cn_liao_whitman(5.0) == pytest.approx(1.7)


def test_the_fines_corrections():
    # Idriss & Boulanger: nothing for a clean sand, about 5.5 blows at 35 % fines
    assert spt.delta_n_ib(0.0) == pytest.approx(0.0, abs=1e-6)
    assert spt.delta_n_ib(35.0) == pytest.approx(math.exp(1.63 + 9.7 / 35.01 - (15.7 / 35.01) ** 2))
    assert 5.4 < float(spt.delta_n_ib(35.0)) < 5.7
    # Youd et al.: the three branches of α and β
    alpha, beta = spt.alpha_beta_youd([3.0, 15.0, 50.0])
    assert alpha[0] == 0.0 and beta[0] == 1.0
    assert alpha[1] == pytest.approx(math.exp(1.76 - 190 / 15 ** 2))
    assert beta[1] == pytest.approx(0.99 + 15 ** 1.5 / 1000)
    assert alpha[2] == 5.0 and beta[2] == 1.2


def test_the_ib_normalisation_converges_to_a_consistent_exponent():
    n60, sigma, fc = np.array([12.0]), np.array([150.0]), np.array([10.0])
    n1, ncs, cn = spt.n1_ib2014(n60, sigma, fc)
    m = 0.784 - 0.0768 * math.sqrt(ncs[0])
    assert cn[0] == pytest.approx((PA / 150.0) ** m, rel=1e-5)
    assert ncs[0] == pytest.approx(n1[0] + float(spt.delta_n_ib(10.0)), rel=1e-9)


# --------------------------------------------------------------------------- #
#  Demand
# --------------------------------------------------------------------------- #

def test_rd_is_one_at_the_surface_and_falls_with_depth():
    for rd in (triggering.rd_idriss([0.0, 5.0, 10.0, 20.0], 7.5),
               triggering.rd_blake([0.0, 5.0, 10.0, 20.0]),
               triggering.rd_linear([0.0, 5.0, 10.0, 20.0]),
               triggering.rd_cetin([0.0, 5.0, 10.0, 20.0], 7.5, 0.3, 180.0)):
        # Idriss's expression is a fit, a little above 1 at the surface for large M
        assert rd[0] == pytest.approx(1.0, abs=0.01)
        assert np.all(np.diff(rd) < 0)


def test_rd_idriss_by_hand():
    z, m = 8.0, 6.5
    alpha = -1.012 - 1.126 * math.sin(z / 11.73 + 5.133)
    beta = 0.106 + 0.118 * math.sin(z / 11.28 + 5.142)
    assert triggering.rd_idriss(z, m) == pytest.approx(math.exp(alpha + beta * m))


def test_rd_linear_is_the_liao_whitman_line():
    assert triggering.rd_linear(5.0) == pytest.approx(1 - 0.00765 * 5)
    assert triggering.rd_linear(15.0) == pytest.approx(1.174 - 0.0267 * 15)
    assert triggering.rd_linear(40.0) == pytest.approx(0.5)


def test_csr_by_hand():
    assert triggering.csr(0.3, 100.0, 60.0, 0.95) == pytest.approx(0.65 * 0.3 * 100 / 60 * 0.95)


# --------------------------------------------------------------------------- #
#  Resistance
# --------------------------------------------------------------------------- #

def test_the_nceer_curve_by_hand_and_its_limit():
    n = 10.0
    expected = 1 / (34 - n) + n / 135 + 50 / (10 * n + 45) ** 2 - 1 / 200
    assert triggering.crr_nceer(n) == pytest.approx(expected)
    assert triggering.crr_nceer(30.0) == triggering.CRR_MAX


def test_the_ib_curve_by_hand_and_its_cap():
    n = 15.0
    expected = math.exp(n / 14.1 + (n / 126) ** 2 - (n / 23.6) ** 3 + (n / 25.4) ** 4 - 2.8)
    assert triggering.crr_ib(n) == pytest.approx(expected)
    assert triggering.crr_ib(45.0) == triggering.CRR_MAX


def test_the_magnitude_scaling_factors_are_one_at_magnitude_7_5():
    assert triggering.msf_idriss(7.5) == pytest.approx(1.0, abs=0.005)
    out = triggering.ib2014(z=np.array([5.0]), sigma_v=np.array([PA]), sigma_eff=np.array([PA]),
                            sigma_eff_test=np.array([PA]), n60=np.array([15.0]),
                            fc=np.array([0.0]), magnitude=7.5, amax=0.3)
    assert out["msf"][0] == pytest.approx(1.0, abs=0.005)
    assert out["ksigma"][0] == pytest.approx(1.0)


def test_the_resistance_rises_as_the_magnitude_falls():
    kw = dict(z=np.array([6.0]), sigma_v=np.array([110.0]), sigma_eff=np.array([70.0]),
              sigma_eff_test=np.array([70.0]), n60=np.array([12.0]), fc=np.array([10.0]),
              amax=0.3)
    for fn in triggering.PROCEDURES.values():
        assert fn(magnitude=6.0, **kw)["crr"][0] > fn(magnitude=7.5, **kw)["crr"][0]


def test_cetin_by_hand_at_the_reference_conditions():
    """M = 7.5, σ'v = Pa, clean sand, PL = 50 %: the expression reduces to its core."""
    n = 14.0
    out = triggering.cetin2004(z=np.array([4.0]), sigma_v=np.array([PA]),
                               sigma_eff=np.array([PA]), sigma_eff_test=np.array([PA]),
                               n60=np.array([n]), fc=np.array([2.0]), magnitude=7.5, amax=0.3,
                               pl=50.0, vs12=180.0)
    expected = math.exp((n - 29.53 * math.log(7.5) + 16.85) / 13.32)
    assert out["crr"][0] == pytest.approx(expected, rel=1e-6)
    assert out["msf"][0] == pytest.approx(1.0) and out["ksigma"][0] == pytest.approx(1.0)


def test_tbdy_by_hand():
    """A hand calculation of TBDY 2018 § 16.6 at one depth."""
    z, sv, se, n60, fc, M, a = 5.0, 96.0, 66.57, 10.0, 20.0, 7.0, 0.4
    cn = min((100.0 / se) ** 0.5, 1.7)
    n1 = cn * n60
    alpha = math.exp(1.76 - 190 / fc ** 2)
    beta = 0.99 + fc ** 1.5 / 1000
    nf = alpha + beta * n1
    crr75 = 1 / (34 - nf) + nf / 135 + 50 / (10 * nf + 45) ** 2 - 1 / 200
    cm = 10 ** 2.24 / M ** 2.56
    tau_eq = 0.65 * sv * a * (1 - 0.00765 * z)
    fs = crr75 * cm * se / tau_eq
    out = triggering.tbdy2018(z=np.array([z]), sigma_v=np.array([sv]), sigma_eff=np.array([se]),
                              sigma_eff_test=np.array([se]), n60=np.array([n60]),
                              fc=np.array([fc]), magnitude=M, amax=a)
    assert out["fs"][0] == pytest.approx(fs, rel=1e-9)


def test_andrus_stokoe_by_hand_and_the_stiff_limit():
    vs, se = 170.0, 80.0
    vs1 = vs * (PA / se) ** 0.25
    limit = 215.0 - 0.5 * (15.0 - 5.0)
    crr75 = 0.022 * (vs1 / 100) ** 2 + 2.8 * (1 / (limit - vs1) - 1 / limit)
    kw = dict(z=np.array([6.0, 6.0, 6.0]), sigma_v=np.array([120.0] * 3),
              sigma_eff=np.array([se] * 3), sigma_eff_test=np.array([se] * 3),
              vs=np.array([vs, 260.0, 0.0]), fc=np.array([15.0] * 3), magnitude=7.5, amax=0.3)
    out = triggering.vs2000(**kw)
    assert out["crr75"][0] == pytest.approx(crr75)
    assert out["dense"][1] and out["crr75"][1] == triggering.CRR_MAX
    assert math.isnan(out["fs"][2])                  # no velocity, no answer


# --------------------------------------------------------------------------- #
#  Susceptibility
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("criterion, props, expected", [
    # (FC, clay, LL, PI, wn)
    ("bray_sancio", (80, 10, 30, 8, 28), "susceptible"),
    ("bray_sancio", (80, 15, 36, 15, 30), "moderate"),
    ("bray_sancio", (80, 30, 45, 24, 30), "not"),
    ("bray_sancio", (80, 10, 30, 8, 20), "not"),            # wn/LL too low
    ("boulanger_idriss", (80, 10, 30, 6, 10), "susceptible"),
    ("boulanger_idriss", (80, 10, 30, 7, 30), "not"),
    ("seed2003", (80, 10, 35, 10, 30), "susceptible"),      # zone A
    ("seed2003", (80, 10, 45, 18, 40), "moderate"),         # zone B
    ("seed2003", (80, 10, 50, 25, 45), "not"),
    ("andrews_martin", (80, 5, 28, 6, 25), "susceptible"),
    ("andrews_martin", (80, 15, 40, 18, 30), "not"),
    ("andrews_martin", (80, 5, 40, 15, 30), "moderate"),
    ("chinese", (80, 10, 30, 8, 28), "susceptible"),
    ("chinese", (80, 20, 30, 8, 28), "not"),
    ("chinese", (80, 10, 30, 8, 25), "not"),                # wn < 0.9 LL
])
def test_the_criteria(criterion, props, expected):
    assert susceptibility.classify_one(criterion, *props) == expected


def test_coarse_and_non_plastic_soils_are_sand_like_whatever_the_criterion():
    for criterion in ("bray_sancio", "seed2003", "chinese", "andrews_martin"):
        assert susceptibility.classify_one(criterion, 20, 5, 30, 20, 10) == "sand"   # FC < 35
        assert susceptibility.classify_one(criterion, 90, 5, 0, 0, 30) == "sand"     # NP
    assert susceptibility.classify_one("none", 95, 40, 60, 35, 30) == "sand"


def test_the_threshold_decides_what_is_fine_grained():
    props = (40, 30, 45, 24, 30)
    assert susceptibility.classify_one("bray_sancio", *props, fine_threshold=35) == "not"
    assert susceptibility.classify_one("bray_sancio", *props, fine_threshold=50) == "sand"


# --------------------------------------------------------------------------- #
#  Consequences
# --------------------------------------------------------------------------- #

def test_the_volumetric_strain_by_hand():
    ncs, fs = 10.0, 0.5
    dr = math.sqrt(ncs / 46)
    f_alpha = 0.032 + 4.7 * dr - 6.0 * dr ** 2
    assert fs < f_alpha                            # beyond the limiting strain
    expected = 1.5 * math.exp(-2.5 * dr) * 0.08
    assert cq.volumetric_strain(fs, dr) == pytest.approx(expected)
    assert triggering.dr_spt(ncs) == pytest.approx(dr)
    # between Fα and 2
    fs = 1.2
    gamma = 0.035 * (2 - fs) * (1 - f_alpha) / (fs - f_alpha)
    assert cq.volumetric_strain(fs, dr) == pytest.approx(1.5 * math.exp(-2.5 * dr) * gamma)
    assert cq.max_shear_strain(fs, dr) == pytest.approx(gamma)


def test_the_strain_vanishes_at_fs_2_and_grows_as_fs_falls():
    dr = float(triggering.dr_spt(12.0))
    assert cq.volumetric_strain(2.0, dr) == 0.0
    eps = cq.volumetric_strain(np.array([1.8, 1.4, 1.0, 0.8, 0.5]), dr)
    assert np.all(np.diff(eps) >= 0)
    # a looser sand strains more for the same factor of safety
    assert cq.volumetric_strain(0.6, 0.4) > cq.volumetric_strain(0.6, 0.7)


def test_lpi_by_hand():
    # one interval, 2–4 m, FS = 0.5: F = 0.5 and ∫(10 − z/2) dz = 17
    value, part = cq.lpi([2.0], [4.0], [0.5], water=0.0)
    assert value == pytest.approx(8.5, rel=1e-9)
    assert part[0] == pytest.approx(8.5)
    # only above 20 m, only where FS < 1
    assert cq.lpi([18.0], [24.0], [0.0], water=0.0)[0] == pytest.approx(
        (10 * 20 - 0.25 * 400) - (10 * 18 - 0.25 * 324))
    assert cq.lpi([2.0], [4.0], [1.2], water=0.0)[0] == 0.0
    assert cq.lpi([2.0], [4.0], [float("nan")], water=0.0)[0] == 0.0


def test_lpi_below_the_water_table_only():
    # water at 3 m, FS = 0: F = 1 and only ∫₃⁴ (10 − z/2) dz counts
    value, _ = cq.lpi([2.0], [4.0], [0.0], water=3.0)
    assert value == pytest.approx((10 * 4 - 0.25 * 16) - (10 * 3 - 0.25 * 9))


def test_lsn_by_hand():
    value, _ = cq.lsn([2.0], [4.0], [0.03], water=0.0, depth=20.0)
    assert value == pytest.approx(1000 * 0.03 * math.log(2.0), rel=1e-3)


def test_the_grades():
    assert [cq.lpi_class(v) for v in (0, 3, 10, 20)] == ["none", "low", "high", "very_high"]
    assert [cq.lsn_class(v) for v in (5, 15, 25, 35, 45, 60)] == cq.LSN_CLASSES
