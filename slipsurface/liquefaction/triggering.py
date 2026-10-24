"""
Liquefaction triggering: the cyclic stress ratio the earthquake imposes, the
cyclic resistance ratio the soil offers, and their quotient, the factor of
safety FS = CRR / CSR, by each of the procedures the program offers.

The demand is common to all of them (Seed & Idriss 1971):

    CSR = 0.65 · (a_max / g) · (σv / σ'v) · rd

and they differ in the stress reduction factor rd, in how the blow count is
normalised, in the resistance curve, and in how the resistance is carried from
the reference conditions (Mw = 7.5, σ'v = 1 atm) to the case at hand, through
the magnitude scaling factor MSF and the overburden factor Kσ:

    ib2014     Idriss & Boulanger (2014): rd(z, M), CN with a density-dependent
               exponent, Δ(N1)60 for the fines, MSF tied to (N1)60cs, Kσ with
               Cσ(N1)60cs
    youd2001   Youd et al. (2001), the NCEER / NSF workshop: rd of Blake
               (Liao & Whitman), α + β·(N1)60, the NCEER curve for
               (N1)60cs < 30, MSF = 10^2.24 / M^2.56, Kσ = (σ'v/Pa)^(f−1)
    cetin2004  Cetin et al. (2004), probabilistic: their own rd(z, M, a_max,
               Vs,12) and a CRR that carries M, σ'v and FC itself, read at the
               chosen probability of liquefaction (15 % is the deterministic
               recommendation)
    tbdy2018   Turkish Building Earthquake Code (TBDY 2018, § 16.6): the NCEER
               curve and fines correction, the linear rd, CN = (100/σ'v)^0.5,
               MSF = 10^2.24 / M^2.56 and no Kσ; FS ≥ 1.1 is required
    vs2000     Andrus & Stokoe (2000), from the shear-wave velocity, where it is
               measured: Vs1 = Vs·(Pa/σ'v)^0.25 against the limit Vs1*(FC)

and from the CPT:

    ib2014_cpt Idriss & Boulanger (2014): qc1N with a density-dependent CN,
               Δqc1N for the fines (FC from Ic), their CPT curve, MSF and Kσ
    rw1998     Robertson & Wride (1998), as adopted by Youd et al. (2001):
               qc1Ncs = Kc·qc1N with the NCEER rd, MSF and Kσ

A clay-like soil does not liquefy, but it may soften: `softening` gives its
factor of safety by Boulanger & Idriss (2007).

Every function returns a dictionary of arrays of the same keys, so the engine
and the figures treat the methods alike:

    n1, ncs, cn, crr75, msf, ksigma, rd, csr, crr, fs, dense, dr

(`n1` and `ncs` are qc1N and qc1Ncs for the CPT; `dr` is the relative density
the strains are read from.)

`crr75` is the resistance at M = 7.5 and σ'v = 1 atm; it is capped at
`CRR_MAX`, where the soil is too dense to liquefy (`dense`).
"""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np

from . import spt
from .config import PA

__all__ = ["CRR_MAX", "rd_idriss", "rd_blake", "rd_linear", "rd_cetin", "msf_idriss",
           "crr_nceer", "crr_ib", "ib2014", "youd2001", "cetin2004", "tbdy2018", "vs2000",
           "csr", "ib2014_cpt", "rw1998", "dr_spt", "dr_cpt", "softening", "msf_clay"]

#: The largest resistance the curves are taken to mean anything for; beyond it
#: the soil is too dense (or too stiff) to liquefy
CRR_MAX = 2.0

#: (N1)60cs from which the NCEER curve is no longer used: the soil is non-liquefiable
NCEER_LIMIT = 30.0

#: (N1)60cs where the curve of Idriss & Boulanger reaches CRR_MAX
IB_LIMIT = 37.5

#: qc1Ncs where the CPT curve of Idriss & Boulanger reaches CRR_MAX
IB_CPT_LIMIT = 211.0

#: qc1Ncs from which Robertson & Wride take a soil as non-liquefiable
RW_LIMIT = 160.0


def csr(amax: float, sigma_v, sigma_eff, rd) -> np.ndarray:
    """CSR = 0.65 · a_max · σv / σ'v · rd, a_max in g."""
    return 0.65 * float(amax) * np.asarray(sigma_v) / np.maximum(sigma_eff, 1e-6) * rd


# --------------------------------------------------------------------------- #
#  Stress reduction factor rd
# --------------------------------------------------------------------------- #

def rd_idriss(z, magnitude: float) -> np.ndarray:
    """rd of Idriss (1999), as used by Idriss & Boulanger (2008, 2014):

        ln rd = α(z) + β(z)·M                                 z ≤ 34 m
        α = −1.012 − 1.126·sin(z/11.73 + 5.133)
        β =  0.106 + 0.118·sin(z/11.28 + 5.142)
        rd = 0.12·exp(0.22·M)                                 z > 34 m
    """
    z = np.asarray(z, dtype=float)
    alpha = -1.012 - 1.126 * np.sin(z / 11.73 + 5.133)
    beta = 0.106 + 0.118 * np.sin(z / 11.28 + 5.142)
    shallow = np.exp(alpha + beta * magnitude)
    return np.where(z <= 34.0, shallow, 0.12 * math.exp(0.22 * magnitude))


def rd_linear(z) -> np.ndarray:
    """Liao & Whitman (1986), the linear rd of the NCEER report and of TBDY 2018."""
    z = np.asarray(z, dtype=float)
    return np.select([z <= 9.15, z <= 23.0, z <= 30.0],
                     [1.0 - 0.00765 * z, 1.174 - 0.0267 * z, 0.744 - 0.008 * z], 0.5)


def rd_blake(z) -> np.ndarray:
    """Blake's fit to the mean rd of Seed & Idriss (Youd et al. 2001, eq. 3),
    down to 23 m; below it the linear expressions."""
    z = np.asarray(z, dtype=float)
    r = np.sqrt(z)
    fit = ((1.0 - 0.4113 * r + 0.04052 * z + 0.001753 * z * r)
           / (1.0 - 0.4177 * r + 0.05729 * z - 0.006205 * z * r + 0.001210 * z * z))
    return np.where(z <= 23.0, fit, rd_linear(z))


def rd_cetin(z, magnitude: float, amax: float, vs12: float) -> np.ndarray:
    """rd of Cetin et al. (2004, eq. 8), from the depth, Mw, a_max [g] and the
    average shear-wave velocity of the top 12 m [m/s]:

        rd = [1 + A / (16.258 + 0.201·e^{0.341(−d + 0.0785·Vs12 + 7.586)})]
           / [1 + A / (16.258 + 0.201·e^{0.341(0.0785·Vs12 + 7.586)})]
        A  = −23.013 − 2.949·a_max + 0.999·Mw + 0.0525·Vs12              d < 20 m
        rd = rd(20) − 0.0046·(d − 20)                                   d ≥ 20 m
    """
    z = np.asarray(z, dtype=float)
    a = -23.013 - 2.949 * amax + 0.999 * magnitude + 0.0525 * vs12
    bottom = 1.0 + a / (16.258 + 0.201 * math.exp(0.341 * (0.0785 * vs12 + 7.586)))

    def top(d):
        return 1.0 + a / (16.258 + 0.201 * np.exp(0.341 * (-d + 0.0785 * vs12 + 7.586)))

    shallow = top(np.minimum(z, 20.0)) / bottom
    deep = top(20.0) / bottom - 0.0046 * (z - 20.0)
    return np.maximum(np.where(z < 20.0, shallow, deep), 0.0)


# --------------------------------------------------------------------------- #
#  Resistance
# --------------------------------------------------------------------------- #

def msf_idriss(magnitude: float) -> float:
    """MSF = 10^2.24 / M^2.56 (Idriss, in Youd et al. 2001; TBDY 2018)."""
    return 10.0 ** 2.24 / magnitude ** 2.56


def crr_nceer(ncs) -> np.ndarray:
    """The NCEER clean-sand curve (Youd et al. 2001, eq. 4), for (N1)60cs < 30:

        CRR7.5 = 1/(34 − N) + N/135 + 50/(10·N + 45)² − 1/200

    and CRR_MAX (non-liquefiable) from 30 on.
    """
    n = np.clip(np.asarray(ncs, dtype=float), 0.0, NCEER_LIMIT - 1e-6)
    crr = 1.0 / (34.0 - n) + n / 135.0 + 50.0 / (10.0 * n + 45.0) ** 2 - 1.0 / 200.0
    return np.where(np.asarray(ncs) >= NCEER_LIMIT, CRR_MAX, np.minimum(crr, CRR_MAX))


def crr_ib(ncs) -> np.ndarray:
    """The clean-sand curve of Idriss & Boulanger (2014, eq. 2.9):

        CRR7.5 = exp(N/14.1 + (N/126)² − (N/23.6)³ + (N/25.4)⁴ − 2.8)

    It reaches CRR_MAX near (N1)60cs = 37.5; from there on the soil is taken
    as too dense to liquefy.
    """
    n = np.clip(np.asarray(ncs, dtype=float), 0.0, IB_LIMIT)
    crr = np.exp(n / 14.1 + (n / 126.0) ** 2 - (n / 23.6) ** 3 + (n / 25.4) ** 4 - 2.8)
    return np.where(np.asarray(ncs) >= IB_LIMIT, CRR_MAX, np.minimum(crr, CRR_MAX))


def _finish(out: dict, amax: float, sigma_v, sigma_eff) -> dict:
    """CSR, CRR and FS from rd, CRR7.5, MSF and Kσ, the same way for every method."""
    out["csr"] = csr(amax, sigma_v, sigma_eff, out["rd"])
    out["crr"] = np.minimum(out["crr75"] * out["msf"] * out["ksigma"], CRR_MAX * 2.0)
    out["fs"] = out["crr"] / np.maximum(out["csr"], 1e-9)
    out["dense"] = out["crr75"] >= CRR_MAX - 1e-9
    if "dr" not in out:
        out["dr"] = dr_spt(out["ncs"])
    return out


# --------------------------------------------------------------------------- #
#  The procedures
# --------------------------------------------------------------------------- #

def ib2014(z, sigma_v, sigma_eff, sigma_eff_test, n60, fc, magnitude, amax, **_) -> dict:
    """Idriss & Boulanger (2014)."""
    n1, ncs, cn = spt.n1_ib2014(n60, sigma_eff_test, fc)
    msf_max = np.minimum(1.09 + (ncs / 31.5) ** 2, 2.2)
    msf = 1.0 + (msf_max - 1.0) * (8.64 * math.exp(-magnitude / 4.0) - 1.325)
    c_sigma = np.minimum(1.0 / (18.9 - 2.55 * np.sqrt(np.clip(ncs, 0.0, 37.0))), 0.3)
    ksigma = np.minimum(1.0 - c_sigma * np.log(np.maximum(sigma_eff, 1e-6) / PA), 1.1)
    out = {"n1": n1, "ncs": ncs, "cn": cn, "crr75": crr_ib(ncs), "msf": msf,
           "ksigma": ksigma, "rd": rd_idriss(z, magnitude)}
    return _finish(out, amax, sigma_v, sigma_eff)


def youd2001(z, sigma_v, sigma_eff, sigma_eff_test, n60, fc, magnitude, amax, **_) -> dict:
    """Youd et al. (2001), NCEER / NSF."""
    cn = spt.cn_liao_whitman(sigma_eff_test)
    n1 = cn * np.asarray(n60, dtype=float)
    alpha, beta = spt.alpha_beta_youd(fc)
    ncs = alpha + beta * n1
    # Kσ of Hynes & Olsen (1999), with f from the relative density: 0.8 at
    # Dr = 40 %, 0.6 at Dr = 80 %; never above 1 (the NCEER recommendation).
    dr = np.sqrt(np.clip(n1, 0.0, None) / 46.0)
    f = np.clip(0.8 - 0.5 * (dr - 0.4), 0.6, 0.8)
    ksigma = np.minimum((np.maximum(sigma_eff, 1e-6) / PA) ** (f - 1.0), 1.0)
    out = {"n1": n1, "ncs": ncs, "cn": cn, "crr75": crr_nceer(ncs),
           "msf": np.full_like(n1, msf_idriss(magnitude)), "ksigma": ksigma,
           "rd": rd_blake(z)}
    return _finish(out, amax, sigma_v, sigma_eff)


def cetin2004(z, sigma_v, sigma_eff, sigma_eff_test, n60, fc, magnitude, amax,
              pl: float = 15.0, vs12: float = 180.0, **_) -> dict:
    """Cetin et al. (2004), read at the probability of liquefaction `pl` [%]:

        CRR = exp[((N1)60·(1 + 0.004·FC) − 29.53·ln Mw − 3.70·ln(σ'v/Pa)
                   + 0.05·FC + 16.85 + 2.70·Φ⁻¹(PL)) / 13.32]

    with FC taken as 0 below 5 % and as 35 % above it, and CN = (Pa/σ'v)^0.5 ≤ 1.6.
    The magnitude and the overburden are inside the expression: MSF and Kσ are
    reported as the ratios that reproduce them against the M = 7.5, 1 atm value.
    """
    cn = spt.cn_liao_whitman(sigma_eff_test, cap=1.6)
    n1 = cn * np.asarray(n60, dtype=float)
    fcc = np.where(np.asarray(fc) < 5.0, 0.0, np.minimum(fc, 35.0))
    ncs = n1 * (1.0 + 0.004 * fcc) + 0.05 * fcc
    p = min(max(float(pl), 0.1), 99.9) / 100.0
    tail = 16.85 + 2.70 * NormalDist().inv_cdf(p)
    s = np.maximum(sigma_eff, 1e-6) / PA
    crr75 = np.exp((ncs - 29.53 * math.log(7.5) + tail) / 13.32)
    crr_m = np.exp((ncs - 29.53 * math.log(magnitude) + tail) / 13.32)
    crr = np.exp((ncs - 29.53 * math.log(magnitude) - 3.70 * np.log(s) + tail) / 13.32)
    out = {"n1": n1, "ncs": ncs, "cn": cn, "crr75": np.minimum(crr75, CRR_MAX),
           "msf": crr_m / crr75, "ksigma": crr / crr_m,
           "rd": rd_cetin(z, magnitude, amax, vs12)}
    return _finish(out, amax, sigma_v, sigma_eff)


def tbdy2018(z, sigma_v, sigma_eff, sigma_eff_test, n60, fc, magnitude, amax, **_) -> dict:
    """Türkiye Bina Deprem Yönetmeliği (2018), § 16.6."""
    cn = spt.cn_liao_whitman(sigma_eff_test, pa=100.0)
    n1 = cn * np.asarray(n60, dtype=float)
    alpha, beta = spt.alpha_beta_youd(fc)
    ncs = alpha + beta * n1
    out = {"n1": n1, "ncs": ncs, "cn": cn, "crr75": crr_nceer(ncs),
           "msf": np.full_like(n1, msf_idriss(magnitude)), "ksigma": np.ones_like(n1),
           "rd": rd_linear(z)}
    return _finish(out, amax, sigma_v, sigma_eff)


def vs2000(z, sigma_v, sigma_eff, sigma_eff_test, vs, fc, magnitude, amax, **_) -> dict:
    """Andrus & Stokoe (2000), from the shear-wave velocity:

        Vs1    = Vs · (Pa/σ'v)^0.25
        Vs1*   = 215 m/s (FC ≤ 5 %), 215 − 0.5·(FC − 5) (5 < FC < 35 %), 200 (FC ≥ 35 %)
        CRR7.5 = 0.022·(Vs1/100)² + 2.8·(1/(Vs1* − Vs1) − 1/Vs1*)
        MSF    = (M/7.5)^−2.56

    Vs1 ≥ Vs1* is too stiff to liquefy. Rows without a velocity come back NaN.
    """
    vs = np.asarray(vs, dtype=float)
    vs1 = vs * (PA / np.maximum(sigma_eff_test, 1e-6)) ** 0.25
    f = np.asarray(fc, dtype=float)
    limit = np.where(f <= 5.0, 215.0, np.where(f >= 35.0, 200.0, 215.0 - 0.5 * (f - 5.0)))
    gap = np.maximum(limit - vs1, 1e-6)
    crr75 = 0.022 * (vs1 / 100.0) ** 2 + 2.8 * (1.0 / gap - 1.0 / limit)
    crr75 = np.where(vs1 >= limit, CRR_MAX, np.minimum(crr75, CRR_MAX))
    out = {"n1": vs1, "ncs": limit, "cn": (PA / np.maximum(sigma_eff_test, 1e-6)) ** 0.25,
           "crr75": crr75, "msf": np.full_like(vs1, (magnitude / 7.5) ** -2.56),
           "ksigma": np.ones_like(vs1), "rd": rd_linear(z)}
    out = _finish(out, amax, sigma_v, sigma_eff)
    missing = ~(vs > 0)
    for key in ("n1", "ncs", "crr75", "crr", "fs"):
        out[key] = np.where(missing, np.nan, out[key])
    out["dense"] = out["dense"] & ~missing
    return out


# --------------------------------------------------------------------------- #
#  CPT procedures
# --------------------------------------------------------------------------- #

def crr_ib_cpt(qcs) -> np.ndarray:
    """The CPT clean-sand curve of Idriss & Boulanger (2014, eq. 2.24):

        CRR7.5 = exp(q/113 + (q/1000)² − (q/140)³ + (q/137)⁴ − 2.8),  q = qc1Ncs

    capped at CRR_MAX (reached near qc1Ncs = 211), too dense to liquefy beyond.
    """
    q = np.clip(np.asarray(qcs, dtype=float), 0.0, IB_CPT_LIMIT)
    crr = np.exp(q / 113.0 + (q / 1000.0) ** 2 - (q / 140.0) ** 3 + (q / 137.0) ** 4 - 2.8)
    return np.where(np.asarray(qcs) >= IB_CPT_LIMIT, CRR_MAX, np.minimum(crr, CRR_MAX))


def crr_rw(qcs) -> np.ndarray:
    """Robertson & Wride (1998), as adopted by Youd et al. (2001):

        CRR7.5 = 0.833·(q/1000) + 0.05          q < 50
               = 93·(q/1000)³ + 0.08            50 ≤ q < 160
    and non-liquefiable from qc1Ncs = 160 on.
    """
    q = np.asarray(qcs, dtype=float)
    crr = np.where(q < 50.0, 0.833 * q / 1000.0 + 0.05, 93.0 * (q / 1000.0) ** 3 + 0.08)
    return np.where(q >= RW_LIMIT, CRR_MAX, np.minimum(crr, CRR_MAX))


def kc_rw(ic) -> np.ndarray:
    """The grain characteristic correction of Robertson & Wride (1998)."""
    ic = np.asarray(ic, dtype=float)
    kc = -0.403 * ic ** 4 + 5.581 * ic ** 3 - 21.63 * ic ** 2 + 33.75 * ic - 17.88
    return np.where(ic <= 1.64, 1.0, kc)


def ib2014_cpt(z, sigma_v, sigma_eff, sigma_eff_test, qt, fc, magnitude, amax, **_) -> dict:
    """Idriss & Boulanger (2014), CPT: qc1Ncs = qc1N + Δqc1N,

        CN      = (Pa/σ'v)^m ≤ 1.7,  m = 1.338 − 0.249·qc1Ncs^0.264   (21 ≤ qc1Ncs ≤ 254)
        Δqc1N   = (11.9 + qc1N/14.6)·exp(1.63 − 9.7/(FC + 2) − (15.7/(FC + 2))²)
        MSFmax  = 1.09 + (qc1Ncs/180)³ ≤ 2.2
        Cσ      = 1/(37.3 − 8.27·qc1Ncs^0.264) ≤ 0.3
    """
    qt = np.asarray(qt, dtype=float)
    se = np.maximum(np.asarray(sigma_eff_test, dtype=float), 1e-6)
    f = np.asarray(fc, dtype=float) + 2.0
    shape = np.exp(1.63 - 9.7 / f - (15.7 / f) ** 2)
    qcs = qt / PA
    for _ in range(50):
        m = 1.338 - 0.249 * np.clip(qcs, 21.0, 254.0) ** 0.264
        cn = np.minimum((PA / se) ** m, 1.7)
        q1 = cn * qt / PA
        new = q1 + (11.9 + q1 / 14.6) * shape
        if np.allclose(new, qcs, atol=1e-6):
            qcs = new
            break
        qcs = new
    msf_max = np.minimum(1.09 + (qcs / 180.0) ** 3, 2.2)
    msf = 1.0 + (msf_max - 1.0) * (8.64 * math.exp(-magnitude / 4.0) - 1.325)
    c_sigma = np.minimum(1.0 / (37.3 - 8.27 * np.clip(qcs, 0.0, 211.0) ** 0.264), 0.3)
    ksigma = np.minimum(1.0 - c_sigma * np.log(np.maximum(sigma_eff, 1e-6) / PA), 1.1)
    out = {"n1": q1, "ncs": qcs, "cn": cn, "crr75": crr_ib_cpt(qcs), "msf": msf,
           "ksigma": ksigma, "rd": rd_idriss(z, magnitude), "dr": dr_cpt(qcs)}
    return _finish(out, amax, sigma_v, sigma_eff)


def rw1998(z, sigma_v, sigma_eff, sigma_eff_test, qt, fc, magnitude, amax, ic=None,
           n_rw=None, **_) -> dict:
    """Robertson & Wride (1998) / Youd et al. (2001), CPT:

        qc1N   = CQ·qt/Pa,  CQ = (Pa/σ'v)^n ≤ 1.7, n from the Ic iteration
        qc1Ncs = Kc·qc1N
    with the NCEER rd, MSF and Kσ of the SPT procedure.
    """
    qt = np.asarray(qt, dtype=float)
    se = np.maximum(np.asarray(sigma_eff_test, dtype=float), 1e-6)
    cq = np.minimum((PA / se) ** n_rw, 1.7)
    q1 = cq * qt / PA
    qcs = kc_rw(ic) * q1
    dr = dr_cpt(qcs)
    f = np.clip(0.8 - 0.5 * (dr - 0.4), 0.6, 0.8)
    ksigma = np.minimum((np.maximum(sigma_eff, 1e-6) / PA) ** (f - 1.0), 1.0)
    out = {"n1": q1, "ncs": qcs, "cn": cq, "crr75": crr_rw(qcs),
           "msf": np.full_like(q1, msf_idriss(magnitude)), "ksigma": ksigma,
           "rd": rd_blake(z), "dr": dr}
    return _finish(out, amax, sigma_v, sigma_eff)


# --------------------------------------------------------------------------- #
#  Relative density, for the strains
# --------------------------------------------------------------------------- #

def dr_spt(ncs) -> np.ndarray:
    """Dr = √((N1)60cs / 46) (Idriss & Boulanger 2008), between 0 and 1."""
    return np.sqrt(np.clip(np.asarray(ncs, dtype=float), 0.0, 46.0) / 46.0)


def dr_cpt(qcs) -> np.ndarray:
    """Dr = 0.478·qc1Ncs^0.264 − 1.063 (Idriss & Boulanger 2008), between 0 and 1."""
    return np.clip(0.478 * np.clip(np.asarray(qcs, dtype=float), 1e-6, None) ** 0.264 - 1.063,
                   0.0, 1.0)


# --------------------------------------------------------------------------- #
#  Clay-like soils: cyclic softening
# --------------------------------------------------------------------------- #

def msf_clay(magnitude: float) -> float:
    """MSF = 1.12·exp(−M/4) + 0.828 ≤ 1.13 (Boulanger & Idriss 2007)."""
    return min(1.12 * math.exp(-magnitude / 4.0) + 0.828, 1.13)


def softening(su_ratio, csr_value, magnitude: float) -> dict:
    """Cyclic softening of a clay-like soil (Boulanger & Idriss 2007), level ground:

        CRR7.5 = C2D · 0.83 · su/σ'vc = 0.8 · su/σ'vc,   CRR = CRR7.5 · MSF_clay

    `su_ratio` is su/σ'v, measured or 0.22·OCR^0.8 (SHANSEP).
    """
    crr75 = 0.8 * np.asarray(su_ratio, dtype=float)
    crr = crr75 * msf_clay(magnitude)
    return {"crr75": crr75, "crr": crr, "fs": crr / np.maximum(csr_value, 1e-9)}


#: The SPT procedures by key, in the order of config.METHODS
PROCEDURES = {"ib2014": ib2014, "youd2001": youd2001, "cetin2004": cetin2004,
              "tbdy2018": tbdy2018}

#: The CPT procedures by key, in the order of config.METHODS_CPT
CPT_PROCEDURES = {"ib2014_cpt": ib2014_cpt, "rw1998": rw1998}
