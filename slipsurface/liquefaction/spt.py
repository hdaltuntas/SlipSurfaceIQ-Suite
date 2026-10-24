"""
SPT corrections: from the field blow count N to the clean-sand equivalent
(N1)60cs that the triggering curves are written for.

    N60        = N · CE · CB · CR · CS
    (N1)60     = CN · N60
    (N1)60cs   = (N1)60 + Δ(N1)60            (Idriss & Boulanger 2014)
               = α + β · (N1)60               (Youd et al. 2001; TBDY 2018)

    CE  hammer energy       ER / 60
    CB  borehole diameter   1.00 (65–115 mm), 1.05 (150 mm), 1.15 (200 mm)
    CR  rod length          0.75 (< 3 m), 0.80 (3–4), 0.85 (4–6), 0.95 (6–10), 1.00 (> 10)
    CS  sampler             1.0 with liners; 1 + (N1)60/100, between 1.1 and 1.3, without
    CN  overburden          (Pa/σ'v)^m ≤ 1.7

The overburden exponent is 0.5 (Liao & Whitman 1986) for the NCEER and TBDY
procedures, and m = 0.784 − 0.0768·√(N1)60cs for Idriss & Boulanger, which
needs a few fixed-point iterations since (N1)60cs depends on CN in turn.

All functions take and return NumPy arrays (or plain numbers), so a whole
borehole is corrected at once.
"""

from __future__ import annotations

import numpy as np

from .config import PA

__all__ = ["energy_factor", "borehole_factor", "rod_factor", "sampler_factor",
           "cn_liao_whitman", "delta_n_ib", "alpha_beta_youd", "n1_ib2014"]

#: The largest overburden correction any of the procedures allows
CN_MAX = 1.7


def energy_factor(energy_ratio: float) -> float:
    """CE = ER / 60, the energy ratio in per cent."""
    return float(energy_ratio) / 60.0


def borehole_factor(diameter_mm: float) -> float:
    """CB of Youd et al. (2001), interpolated between the tabulated diameters."""
    d = float(diameter_mm)
    return float(np.interp(d, [115.0, 150.0, 200.0], [1.0, 1.05, 1.15]))


def rod_factor(rod_length) -> np.ndarray:
    """CR of Youd et al. (2001): short rods lose energy to the anvil."""
    length = np.asarray(rod_length, dtype=float)
    return np.select([length < 3.0, length < 4.0, length < 6.0, length < 10.0],
                     [0.75, 0.80, 0.85, 0.95], 1.0)


def sampler_factor(n1_60, no_liner: bool) -> np.ndarray:
    """CS: 1 with liners; without them 1 + (N1)60/100, kept between 1.1 and 1.3
    (Seed et al. 1984, as written by Idriss & Boulanger 2014)."""
    n1 = np.asarray(n1_60, dtype=float)
    if not no_liner:
        return np.ones_like(n1)
    return np.clip(1.0 + n1 / 100.0, 1.1, 1.3)


def cn_liao_whitman(sigma_eff, cap: float = CN_MAX, pa: float = PA) -> np.ndarray:
    """CN = (Pa/σ'v)^0.5 ≤ cap."""
    s = np.maximum(np.asarray(sigma_eff, dtype=float), 1e-6)
    return np.minimum(np.sqrt(pa / s), cap)


# --------------------------------------------------------------------------- #
#  Fines content
# --------------------------------------------------------------------------- #

def delta_n_ib(fc) -> np.ndarray:
    """Δ(N1)60 of Idriss & Boulanger (2014): exp(1.63 + 9.7/(FC+0.01) − (15.7/(FC+0.01))²)."""
    f = np.asarray(fc, dtype=float) + 0.01
    return np.exp(1.63 + 9.7 / f - (15.7 / f) ** 2)


def alpha_beta_youd(fc):
    """α and β of Youd et al. (2001), after Idriss and Seed:

        FC ≤ 5 %       α = 0                     β = 1
        5 < FC < 35 %  α = exp(1.76 − 190/FC²)   β = 0.99 + FC^1.5 / 1000
        FC ≥ 35 %      α = 5                     β = 1.2
    """
    f = np.asarray(fc, dtype=float)
    safe = np.clip(f, 5.0, 35.0)
    alpha = np.where(f <= 5.0, 0.0, np.where(f >= 35.0, 5.0, np.exp(1.76 - 190.0 / safe ** 2)))
    beta = np.where(f <= 5.0, 1.0, np.where(f >= 35.0, 1.2, 0.99 + safe ** 1.5 / 1000.0))
    return alpha, beta


# --------------------------------------------------------------------------- #
#  Idriss & Boulanger: CN with the stress exponent tied to the density
# --------------------------------------------------------------------------- #

def n1_ib2014(n60, sigma_eff, fc, iterations: int = 30, pa: float = PA):
    """(N1)60, (N1)60cs and CN of Idriss & Boulanger (2014).

    CN = (Pa/σ'v)^m ≤ 1.7 with m = 0.784 − 0.0768·√(N1)60cs, and (N1)60cs
    capped at 46 inside the exponent. Converges in a handful of iterations.
    """
    n60 = np.asarray(n60, dtype=float)
    s = np.maximum(np.asarray(sigma_eff, dtype=float), 1e-6)
    dn = delta_n_ib(fc)
    ncs = n60 + dn
    for _ in range(iterations):
        m = 0.784 - 0.0768 * np.sqrt(np.clip(ncs, 0.0, 46.0))
        cn = np.minimum((pa / s) ** m, CN_MAX)
        new = cn * n60 + dn
        if np.allclose(new, ncs, atol=1e-6):
            ncs = new
            break
        ncs = new
    return cn * n60, ncs, cn
