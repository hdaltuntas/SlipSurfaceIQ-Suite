"""
CPT interpretation: the corrected tip resistance, the soil behaviour type
index Ic, and the fines content and blow count it implies.

    qt   = qc + (1 − a)·u2                      a: net area ratio of the cone
    Q    = (qt − σv)/Pa · (Pa/σ'v)^n            normalised tip resistance
    F    = fs / (qt − σv) · 100                 normalised friction ratio [%]
    Ic   = √((3.47 − log Q)² + (log F + 1.22)²)

The stress exponent n is found in two ways:

    robertson_wride   Robertson & Wride (1998), as written by Youd et al.
                      (2001): n = 1 (Q with qt − σv) first; where Ic ≤ 2.6,
                      n = 0.5 with Q = qt/Pa·(Pa/σ'v)^0.5; where that Ic
                      is above 2.6, n = 0.75
    robertson_2009    Robertson (2009), used by Idriss & Boulanger (2014):
                      n = 0.381·Ic + 0.05·σ'v/Pa − 0.15 ≤ 1, iterated

Fines content from Ic (Idriss & Boulanger 2014): FC = 80·(Ic + CFC) − 137,
between 0 and 100 %; CFC = 0 is their general-purpose value.

An SPT-equivalent blow count (Robertson 2012, after Jefferies & Davies 1993):
(qt/Pa)/N60 = 10^(1.1268 − 0.2817·Ic), used where a CPT has to feed a method
written for the SPT (the dry sand settlement).

Pressures are in kPa; qc is entered in MPa and converted by the engine.
"""

from __future__ import annotations

import numpy as np

from .config import PA

__all__ = ["tip_resistance", "q_f", "ic_value", "ic_robertson_wride", "ic_robertson_2009",
           "fines_from_ic", "n60_from_cpt", "IC_LIMIT"]

#: Ic above which a soil is taken as clay-like (Robertson & Wride 1998)
IC_LIMIT = 2.6


def tip_resistance(qc, u2, area_ratio: float = 0.8) -> np.ndarray:
    """qt = qc + (1 − a)·u2 [kPa]."""
    return np.asarray(qc, dtype=float) + (1.0 - area_ratio) * np.asarray(u2, dtype=float)


def q_f(qt, fs, sigma_v, sigma_eff, n, net: bool = True):
    """Q and F [%] with the stress exponent n (Q ≥ 1, F ≥ 0.1)."""
    return _q_f(qt, fs, sigma_v, sigma_eff, n, net)


def _q_f(qt, fs, sigma_v, sigma_eff, n, net: bool = True):
    net_q = np.maximum(np.asarray(qt) - sigma_v, 1e-6)
    q = (net_q if net else np.asarray(qt)) / PA * (PA / np.maximum(sigma_eff, 1e-6)) ** n
    f = np.asarray(fs) / net_q * 100.0
    return np.maximum(q, 1.0), np.maximum(f, 0.1)


def ic_value(q, f) -> np.ndarray:
    return np.sqrt((3.47 - np.log10(q)) ** 2 + (np.log10(f) + 1.22) ** 2)


def ic_robertson_wride(qt, fs, sigma_v, sigma_eff):
    """Ic and n by the iteration of Robertson & Wride (1998) / Youd et al. (2001)."""
    q1, f = _q_f(qt, fs, sigma_v, sigma_eff, 1.0, net=True)
    ic1 = ic_value(q1, f)
    q5, _ = _q_f(qt, fs, sigma_v, sigma_eff, 0.5, net=False)
    ic5 = ic_value(q5, f)
    q75, _ = _q_f(qt, fs, sigma_v, sigma_eff, 0.75, net=False)
    ic75 = ic_value(q75, f)
    clay = ic1 > IC_LIMIT
    n = np.where(clay, 1.0, np.where(ic5 <= IC_LIMIT, 0.5, 0.75))
    ic = np.where(clay, ic1, np.where(ic5 <= IC_LIMIT, ic5, ic75))
    return ic, n


def ic_robertson_2009(qt, fs, sigma_v, sigma_eff, iterations: int = 50):
    """Ic and n by Robertson (2009): n = 0.381·Ic + 0.05·σ'v/Pa − 0.15 ≤ 1."""
    n = np.ones_like(np.asarray(qt, dtype=float))
    for _ in range(iterations):
        q, f = _q_f(qt, fs, sigma_v, sigma_eff, n, net=True)
        ic = ic_value(q, f)
        new = np.clip(0.381 * ic + 0.05 * np.asarray(sigma_eff) / PA - 0.15, 0.0, 1.0)
        if np.allclose(new, n, atol=1e-6):
            n = new
            break
        n = new
    q, f = _q_f(qt, fs, sigma_v, sigma_eff, n, net=True)
    return ic_value(q, f), n


def fines_from_ic(ic, cfc: float = 0.0) -> np.ndarray:
    """FC = 80·(Ic + CFC) − 137, between 0 and 100 % (Idriss & Boulanger 2014)."""
    return np.clip(80.0 * (np.asarray(ic) + cfc) - 137.0, 0.0, 100.0)


def n60_from_cpt(qt, ic) -> np.ndarray:
    """N60 from (qt/Pa)/N60 = 10^(1.1268 − 0.2817·Ic) (Robertson 2012)."""
    return np.asarray(qt) / PA / 10.0 ** (1.1268 - 0.2817 * np.asarray(ic))
