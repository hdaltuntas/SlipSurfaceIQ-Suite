"""
The generalised Hoek–Brown criterion and what is derived from it.

All stresses are in MPa, compression positive; the tensile strength therefore
comes out negative, as Hoek and RocLab write it.

The criterion (Hoek, Carranza-Torres & Corkum 2002)

    σ1 = σ3 + σci·(mb·σ3/σci + s)^a

    mb = mi·e^((GSI − 100)/(28 − 14·D))
    s  = e^((GSI − 100)/(9 − 3·D))
    a  = ½ + (e^(−GSI/15) − e^(−20/3))/6

Rock mass strengths

    σt  = −s·σci/mb                              tensile (biaxial = uniaxial)
    σc  = σci·s^a                                 uniaxial compressive
    σcm = σci·(mb + 4s − a(mb − 8s))·(mb/4 + s)^(a−1) / (2(1 + a)(2 + a))
                                                  "global" strength

Equivalent Mohr–Coulomb strength, fitted over σt < σ3 < σ3max, with
σ3n = σ3max/σci:

    φ' = asin[ 6a·mb·(s + mb·σ3n)^(a−1) / (2(1 + a)(2 + a) + 6a·mb·(s + mb·σ3n)^(a−1)) ]
    c' = σci·[(1 + 2a)s + (1 − a)mb·σ3n]·(s + mb·σ3n)^(a−1)
         / { (1 + a)(2 + a)·√[1 + 6a·mb·(s + mb·σ3n)^(a−1) / ((1 + a)(2 + a))] }

The upper end σ3max depends on what loads the rock mass (Hoek et al. 2002):

    general     σ3max = σci/4
    tunnel      σ3max/σcm = 0.47·(σcm/γH)^(−0.94)
    slope       σ3max/σcm = 0.72·(σcm/γH)^(−0.91)

Deformation modulus

    generalized  Erm = Ei·(0.02 + (1 − D/2)/(1 + e^((60 + 15D − GSI)/11)))
                 (Hoek & Diederichs 2006)
    simplified   Erm = 100 000·(1 − D/2)/(1 + e^((75 + 25D − GSI)/11))  [MPa]
                 (Hoek & Diederichs 2006)
    hctc2002     Erm = (1 − D/2)·√(σci/100)·10^((GSI − 10)/40)  [GPa], the root
                 taken as 1 for σci > 100 MPa (Hoek et al. 2002)

The shear-normal envelope is Balmer's (1952): at any σ3, with k = ∂σ1/∂σ3,

    σn = (σ1 + σ3)/2 − (σ1 − σ3)/2 · (k − 1)/(k + 1)
    τ  = (σ1 − σ3)·√k/(k + 1)

and the instantaneous friction angle and cohesion of the tangent there are
φi = asin((k − 1)/(k + 1)), ci = τ − σn·tan φi.

Residual strength after Cai et al. (2007): GSIr = GSI·e^(−0.0134·GSI), with
the constants of GSIr and the intact rock's mi.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List

import numpy as np

__all__ = ["constants", "sigma1", "slope", "tensile_strength", "uniaxial_strength",
           "global_strength", "mohr_coulomb_fit", "sigma3_max", "instantaneous",
           "shear_envelope", "modulus", "MODULUS_FORMULAS", "residual_gsi",
           "mohr_coulomb_sigma1", "GENERAL_RATIO"]

#: σ3max/σci of a "general" application
GENERAL_RATIO = 0.25


def constants(GSI: float, mi: float, D: float = 0.0) -> Dict[str, float]:
    """mb, s and a of the rock mass."""
    gsi, d = float(GSI), float(D)
    mb = float(mi) * math.exp((gsi - 100.0) / (28.0 - 14.0 * d))
    s = math.exp((gsi - 100.0) / (9.0 - 3.0 * d))
    a = 0.5 + (math.exp(-gsi / 15.0) - math.exp(-20.0 / 3.0)) / 6.0
    return {"mb": mb, "s": s, "a": a}


def sigma1(sigma3, sigma_ci: float, mb: float, s: float, a: float):
    """σ1 at failure; works on a number or an array. Below σt there is none (nan)."""
    s3 = np.asarray(sigma3, dtype=float)
    base = mb * s3 / sigma_ci + s
    with np.errstate(invalid="ignore"):
        out = np.where(base >= 0.0, s3 + sigma_ci * np.power(np.maximum(base, 0.0), a),
                       np.nan)
    return float(out) if np.ndim(out) == 0 else out


def slope(sigma3, sigma_ci: float, mb: float, s: float, a: float):
    """∂σ1/∂σ3 of the criterion."""
    s3 = np.asarray(sigma3, dtype=float)
    base = np.maximum(mb * s3 / sigma_ci + s, 1e-15)
    out = 1.0 + a * mb * np.power(base, a - 1.0)
    return float(out) if np.ndim(out) == 0 else out


def tensile_strength(sigma_ci: float, mb: float, s: float) -> float:
    """σt = −s·σci/mb (negative: tension)."""
    return -s * sigma_ci / mb


def uniaxial_strength(sigma_ci: float, s: float, a: float) -> float:
    """σc = σci·s^a."""
    return sigma_ci * s ** a


def global_strength(sigma_ci: float, mb: float, s: float, a: float) -> float:
    """The global rock mass strength σcm of Hoek et al. (2002)."""
    numerator = (mb + 4.0 * s - a * (mb - 8.0 * s)) * (mb / 4.0 + s) ** (a - 1.0)
    return sigma_ci * numerator / (2.0 * (1.0 + a) * (2.0 + a))


def mohr_coulomb_fit(sigma_ci: float, mb: float, s: float, a: float,
                     sigma3_max: float) -> Dict[str, float]:
    """The equivalent c' [MPa] and φ' [°] over σt < σ3 < σ3max."""
    s3n = sigma3_max / sigma_ci
    common = (s + mb * s3n) ** (a - 1.0)
    upper = 6.0 * a * mb * common
    k12 = (1.0 + a) * (2.0 + a)
    phi = math.degrees(math.asin(min(upper / (2.0 * k12 + upper), 1.0)))
    c = (sigma_ci * ((1.0 + 2.0 * a) * s + (1.0 - a) * mb * s3n) * common
         / (k12 * math.sqrt(1.0 + upper / k12)))
    sin_phi = math.sin(math.radians(phi))
    cos_phi = math.cos(math.radians(phi))
    return {"c": c, "phi": phi,
            "k": (1.0 + sin_phi) / (1.0 - sin_phi),
            # the strengths the fitted line itself has
            "sigma_cm": 2.0 * c * cos_phi / (1.0 - sin_phi),
            "sigma_t": -2.0 * c * cos_phi / (1.0 + sin_phi)}


def mohr_coulomb_sigma1(sigma3, c: float, phi: float):
    """σ1 on the fitted Mohr–Coulomb line."""
    sin_phi = math.sin(math.radians(phi))
    k = (1.0 + sin_phi) / (1.0 - sin_phi)
    ucs = 2.0 * c * math.cos(math.radians(phi)) / (1.0 - sin_phi)
    return ucs + k * np.asarray(sigma3, dtype=float)


def sigma3_max(application: str, sigma_ci: float, sigma_cm: float,
               unit_weight: float = 26.0, depth: float = 100.0,
               custom: float = 0.0) -> float:
    """The upper end of the confinement for an application.

    `unit_weight` is in kN/m³ and `depth` in m; γH is turned into MPa here.
    """
    if application == "custom":
        return float(custom)
    if application in ("tunnel", "slope"):
        gamma_h = float(unit_weight) * float(depth) / 1000.0
        ratio = sigma_cm / gamma_h
        if application == "tunnel":
            return sigma_cm * 0.47 * ratio ** -0.94
        return sigma_cm * 0.72 * ratio ** -0.91
    return GENERAL_RATIO * sigma_ci


def instantaneous(sigma3: float, sigma_ci: float, mb: float, s: float,
                  a: float) -> Dict[str, float]:
    """The tangent to the envelope at one σ3: σ1, σn, τ, φi [°] and ci [MPa]."""
    s1 = sigma1(sigma3, sigma_ci, mb, s, a)
    k = slope(sigma3, sigma_ci, mb, s, a)
    sn = 0.5 * (s1 + sigma3) - 0.5 * (s1 - sigma3) * (k - 1.0) / (k + 1.0)
    tau = (s1 - sigma3) * math.sqrt(k) / (k + 1.0)
    phi = math.asin((k - 1.0) / (k + 1.0))
    return {"sigma3": float(sigma3), "sigma1": float(s1), "k": float(k),
            "sigma_n": float(sn), "tau": float(tau), "phi": math.degrees(phi),
            "c": float(tau - sn * math.tan(phi))}


def shear_envelope(sigma3: Iterable[float], sigma_ci: float, mb: float, s: float,
                   a: float) -> Dict[str, np.ndarray]:
    """The Mohr envelope (σn, τ) traced through a set of σ3."""
    s3 = np.asarray(list(sigma3), dtype=float)
    s1 = sigma1(s3, sigma_ci, mb, s, a)
    k = slope(s3, sigma_ci, mb, s, a)
    sn = 0.5 * (s1 + s3) - 0.5 * (s1 - s3) * (k - 1.0) / (k + 1.0)
    tau = (s1 - s3) * np.sqrt(k) / (k + 1.0)
    return {"sigma_n": sn, "tau": tau}


def _generalized(GSI, D, sigma_ci, Ei):
    return Ei * (0.02 + (1.0 - D / 2.0) / (1.0 + math.exp((60.0 + 15.0 * D - GSI) / 11.0)))


def _simplified(GSI, D, sigma_ci, Ei):
    return 100000.0 * (1.0 - D / 2.0) / (1.0 + math.exp((75.0 + 25.0 * D - GSI) / 11.0))


def _hctc2002(GSI, D, sigma_ci, Ei):
    root = math.sqrt(sigma_ci / 100.0) if sigma_ci <= 100.0 else 1.0
    return 1000.0 * (1.0 - D / 2.0) * root * 10.0 ** ((GSI - 10.0) / 40.0)


#: The deformation modulus estimates, each (GSI, D, σci [MPa], Ei [MPa]) -> MPa
MODULUS_FORMULAS = {"generalized": _generalized, "simplified": _simplified,
                    "hctc2002": _hctc2002}


def modulus(method: str, GSI: float, D: float, sigma_ci: float, Ei: float) -> float:
    """The rock mass deformation modulus Erm [MPa]."""
    return MODULUS_FORMULAS[method](float(GSI), float(D), float(sigma_ci), float(Ei))


def residual_gsi(GSI: float) -> float:
    """Cai et al. (2007): GSIr = GSI·e^(−0.0134·GSI)."""
    return float(GSI) * math.exp(-0.0134 * float(GSI))


def principal_curve(sigma_ci: float, mb: float, s: float, a: float, s3_lo: float,
                    s3_hi: float, n: int = 160) -> Dict[str, List[float]]:
    """σ1 over a range of σ3, for the figures."""
    s3 = np.linspace(s3_lo, s3_hi, n)
    return {"sigma3": s3, "sigma1": sigma1(s3, sigma_ci, mb, s, a)}
