"""The catalogue of correlations: what it promises, and the formulas themselves."""
import math

import pytest

from slipsurface.correlation import correlations as corr
from slipsurface.correlation.config import PA, PARAMS
from slipsurface.correlation.i18n import TRANSLATIONS


def sand(**kw):
    return {"behaviour": "granular", "fines": 5.0, **kw}


def clay(**kw):
    return {"behaviour": "cohesive", "PI": 30.0, "uscs": "CL", **kw}


def spt(N60, N1_60=None, sigma_eff=PA):
    return {"N60": N60, "N1_60": N60 if N1_60 is None else N1_60, "sigma_eff": sigma_eff}


# --------------------------------------------------------------------------- catalogue
def test_every_parameter_has_a_correlation():
    for param in PARAMS:
        assert corr.methods_for(param), param


def test_every_correlation_is_declared_completely():
    for key, method in corr.METHODS.items():
        assert method.key == key
        assert method.param in PARAMS
        assert method.source in ("spt", "cpt", "lab", "vs", "derived")
        assert method.behaviour in ("granular", "cohesive", "all")
        assert method.ref and method.formula


def test_described_sources_are_translated():
    for key, method in corr.METHODS.items():
        if method.ref.startswith("@"):
            for lang in ("en", "tr"):
                assert method.ref[1:] in TRANSLATIONS[lang], key
            assert corr.reference(key, "tr") != corr.reference(key, "en") or key


def test_the_point_functions_only_give_declared_correlations():
    row_cpt = {"qc": 5.0, "fs": 50.0, "u2": 200.0, "u0": 50.0, "qt": 5040.0, "net": 4900.0,
               "sigma_eff": 80.0, "Rf": 1.0, "Qt": 60.0, "Ic": 2.3}
    produced = set()
    for layer in (sand(), clay()):
        produced |= set(corr.spt_point(spt(15), layer))
        produced |= set(corr.cpt_point(row_cpt, layer, {"Nkt": 14, "Ndu": 6}))
    assert produced <= set(corr.METHODS)
    for key in produced:
        assert corr.METHODS[key].source in ("spt", "cpt")


def test_correlations_respect_the_soil_they_were_written_for():
    for key in corr.spt_point(spt(15), sand()):
        assert corr.METHODS[key].applies("granular")
    for key in corr.spt_point(spt(15), clay()):
        assert corr.METHODS[key].applies("cohesive")


# --------------------------------------------------------------------------- SPT
def test_spt_sand_correlations():
    out = corr.spt_point(spt(20, 15), sand())
    assert out["dr_skempton1986"] == pytest.approx(50.0)
    assert out["dr_idriss2008"] == pytest.approx(100 * math.sqrt(15 / 46))
    assert out["phi_hatanaka1996"] == pytest.approx(math.sqrt(300) + 20)
    assert out["phi_wolff1989"] == pytest.approx(27.1 + 6 - 0.00054 * 400)
    assert out["e_km1990"] == pytest.approx(10 * PA * 20 / 1000)
    assert out["e_bowles1996"] == pytest.approx(17.5)
    assert out["vs_imai1982"] == pytest.approx(97 * 20 ** 0.314)


def test_sand_with_fines_is_softer_after_kulhawy_and_mayne():
    clean = corr.spt_point(spt(20), sand())["e_km1990"]
    silty = corr.spt_point(spt(20), sand(fines=25.0))["e_km1990"]
    assert silty == pytest.approx(clean / 2)


def test_relative_density_is_capped():
    assert corr.spt_point(spt(200, 200), sand())["dr_skempton1986"] == 100.0


def test_spt_clay_correlations():
    out = corr.spt_point(spt(10), clay())
    assert out["cu_hara1974"] == pytest.approx(29 * 10 ** 0.72)
    assert out["cu_terzaghi1967"] == pytest.approx(62.5)
    assert out["cu_sivrikaya2006"] == pytest.approx(43.2)
    assert out["cu_stroud1974"] == pytest.approx(46.0)             # f1 = 4.6 at PI = 30
    assert out["sp_mayne2002"] == pytest.approx(0.47 * 10 * PA)
    assert "dr_skempton1986" not in out


def test_stroud_factor_falls_with_plasticity():
    values = [corr.stroud_f1(pi) for pi in (10, 15, 20, 30, 40, 60, 80)]
    assert values == sorted(values, reverse=True)
    assert corr.stroud_f1(None) == 4.4


# --------------------------------------------------------------------------- CPT
def cpt_row(**kw):
    row = {"qc": 10.0, "fs": 60.0, "u2": 0.0, "u0": 20.0, "qt": 10000.0, "net": 9925.0,
           "sigma_eff": 55.0, "Rf": 0.6, "Qt": 180.0, "Ic": 1.7}
    row.update(kw)
    return row


def test_cpt_sand_correlations():
    out = corr.cpt_point(cpt_row(), sand(), {"Nkt": 14, "Ndu": 6})
    assert out["phi_rc1983"] == pytest.approx(
        math.degrees(math.atan(0.1 + 0.38 * math.log10(10000 / 55))))
    qt1 = (10000 / PA) / math.sqrt(55 / PA)
    assert out["phi_km1990"] == pytest.approx(17.6 + 11 * math.log10(qt1))
    assert out["dr_baldi1986"] == pytest.approx(100 * math.log(10000 / (157 * 55 ** 0.55)) / 2.41)
    assert out["e_schmertmann1978"] == pytest.approx(25.0)
    assert out["k_robertson2010"] == pytest.approx(10 ** (0.952 - 3.04 * 1.7))
    assert 14 < out["gamma_rc2010"] < 22


def test_cpt_clay_correlations():
    row = cpt_row(qc=0.8, fs=20.0, u2=400.0, u0=80.0, qt=880.0, net=700.0, sigma_eff=90.0,
                  Rf=2.3, Qt=7.8, Ic=3.1)
    out = corr.cpt_point(row, clay(), {"Nkt": 14, "Ndu": 6})
    assert out["cu_nkt"] == pytest.approx(50.0)
    assert out["cu_ndu"] == pytest.approx(320 / 6)
    assert out["sp_km1990"] == pytest.approx(0.33 * 700)
    assert out["m_robertson2009"] == pytest.approx(7.8 * 700 / 1000)
    assert out["cv_km"] > 0
    assert "phi_rc1983" not in out


@pytest.mark.parametrize("ic, expected", [(1.0, 10 ** (0.952 - 3.04)), (3.5, 10 ** (-4.52 - 4.795)),
                                          (4.2, None)])
def test_robertson_permeability(ic, expected):
    value = corr.cpt_permeability(ic)
    assert value == (pytest.approx(expected) if expected else None)


# --------------------------------------------------------------------------- laboratory
def test_laboratory_clay_correlations():
    layer = {"behaviour": "cohesive", "w": 40.0, "Gs": 2.7, "qu": 80.0}
    index = {"LL": 50.0, "PL": 25.0, "PI": 25.0, "LI": 0.6}
    out = corr.lab_layer(layer, index, {"e0": 1.08, "source": "wGs"})
    assert out["cc_skempton1944"] == pytest.approx(0.36)
    assert out["cc_azzouz1976"] == pytest.approx(0.4 * 0.83)
    assert out["cc_nishida1956"] == pytest.approx(1.15 * 0.73)
    assert out["cc_koppula1981"] == pytest.approx(0.40)
    assert out["cc_wroth1978"] == pytest.approx(0.5 * 2.7 * 0.25)
    assert out["cr_nagaraj1985"] == pytest.approx(0.0463 * 0.5 * 2.7)
    assert out["ca_mesri1973"] == pytest.approx(0.004)
    assert out["cu_qu"] == 40.0
    assert out["sp_stas1984"] == pytest.approx(PA * 10 ** (1.11 - 1.62 * 0.6))
    assert out["phi_kenney1959"] == pytest.approx(math.degrees(math.asin(0.8 - 0.094 * math.log(25))))
    assert out["phi_sorensen2013"] == pytest.approx(43 - 10 * math.log10(25))
    assert out["e0_wgs"] == 1.08


def test_hazen_for_a_sand():
    out = corr.lab_layer({"behaviour": "granular", "D10": 0.2}, {}, {})
    assert out == {"k_hazen1911": pytest.approx(0.01 * 0.04)}
