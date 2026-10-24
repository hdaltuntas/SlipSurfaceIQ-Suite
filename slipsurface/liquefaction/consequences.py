"""
What liquefaction does: the volumetric strain the soil suffers as the excess
pore pressure dissipates, the settlement it adds up to, and the two indices
that grade the damage at the ground surface.

Volumetric strain — Ishihara & Yoshimine (1992), in the form fitted by
Yoshimine et al. (2006) and written for the SPT by Idriss & Boulanger (2008):

    Fα    = 0.032 + 4.7·Dr − 6.0·Dr²                     (Dr ≥ 0.4)
    γmax  = 0                                            FS ≥ 2
          = 0.035·(2 − FS)·(1 − Fα) / (FS − Fα)          Fα ≤ FS < 2
          = γlim                                         FS < Fα
    γlim  = 1.859·(1.1 − Dr)³ ≥ 0
    εv    = 1.5 · exp(−2.5·Dr) · min(0.08, γmax)

with Dr = √((N1)60cs/46) for the SPT and Dr = 0.478·qc1Ncs^0.264 − 1.063 for
the CPT (Idriss & Boulanger 2008).

Settlement — s = Σ εv · Δz over the liquefiable layers below the water table,
down to the chosen depth; the dry sand above the water table adds Pradel's
(1998) seismic compression.

Lateral spreading — Zhang et al. (2004): LDI = ∫ γmax dz, and LD from the
ground slope or the free-face ratio L/H.

LPI — Iwasaki et al. (1978): LPI = ∫₀²⁰ F(z)·w(z) dz with F = 1 − FS for
FS < 1 (0 otherwise) and w = 10 − 0.5·z. 0: very low; ≤ 5: low; ≤ 15: high;
> 15: very high.

LSN — van Ballegooy et al. (2014): LSN = 1000 ∫ εv / z dz. Below 10 little to
no expression; 10–20 minor; 20–30 moderate; 30–40 moderate to severe; 40–50
major; above 50 severe.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

__all__ = ["max_shear_strain", "volumetric_strain", "ldi", "lateral_displacement", "pradel",
           "lpi", "lsn", "lpi_class", "lsn_class", "LPI_CLASSES", "LSN_CLASSES", "GEOMETRIES"]

#: Depth of the LPI integral [m]
LPI_DEPTH = 20.0

#: Step of the numerical integrals [m]
STEP = 0.05

LPI_CLASSES = ["none", "low", "high", "very_high"]
LSN_CLASSES = ["little", "minor", "moderate", "mod_severe", "major", "severe"]


def max_shear_strain(fs, dr) -> np.ndarray:
    """γmax (a fraction) from FS and the relative density Dr (a fraction)."""
    fs = np.asarray(fs, dtype=float)
    dr = np.clip(np.asarray(dr, dtype=float), 0.0, 1.0)
    d = np.maximum(dr, 0.4)
    f_alpha = 0.032 + 4.7 * d - 6.0 * d * d
    gamma_lim = np.maximum(1.859 * (1.1 - dr) ** 3, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        middle = 0.035 * (2.0 - fs) * (1.0 - f_alpha) / (fs - f_alpha)
    gamma = np.where(fs >= 2.0, 0.0, np.where(fs >= f_alpha, middle, gamma_lim))
    gamma = np.clip(np.minimum(gamma, gamma_lim), 0.0, None)
    return np.where(np.isfinite(fs), gamma, 0.0)


def volumetric_strain(fs, dr) -> np.ndarray:
    """εv = 1.5·exp(−2.5·Dr)·min(0.08, γmax), a fraction, from FS and Dr."""
    dr = np.clip(np.asarray(dr, dtype=float), 0.0, 1.0)
    eps = 1.5 * np.exp(-2.5 * dr) * np.minimum(0.08, max_shear_strain(fs, dr))
    return np.where(np.isfinite(np.asarray(fs, dtype=float)), eps, 0.0)


# --------------------------------------------------------------------------- #
#  Lateral spreading
# --------------------------------------------------------------------------- #

#: Ground geometries for the lateral displacement
GEOMETRIES = ["level", "slope", "free_face"]


def ldi(top, bot, gamma, water: float, depth: float) -> Tuple[float, np.ndarray]:
    """The lateral displacement index LDI = ∫ γmax dz [m] (Zhang et al. 2004)
    over the saturated soil down to `depth`, and each interval's share."""
    top, bot = np.asarray(top, float), np.asarray(bot, float)
    thick = np.clip(np.minimum(bot, depth) - np.maximum(top, water), 0.0, None)
    part = np.asarray(gamma, float) * thick
    return float(part.sum()), part


def lateral_displacement(ldi_value: float, geometry: str, slope: float = 0.0,
                         length: float = 0.0, height: float = 0.0) -> Tuple[float, bool]:
    """Lateral displacement LD [m] from the LDI (Zhang et al. 2004):

        gently sloping ground, no free face   LD = (S + 0.2)·LDI      0.2 < S < 3.5 %
        level ground with a free face         LD = 6·(L/H)^−0.8·LDI   4 < L/H < 40

    Returns (LD, within the range of the case histories).
    """
    if geometry == "slope":
        return (slope + 0.2) * ldi_value, 0.2 <= slope <= 3.5
    if geometry == "free_face" and height > 0 and length > 0:
        ratio = length / height
        return 6.0 * ratio ** -0.8 * ldi_value, 4.0 <= ratio <= 40.0
    return 0.0, True


# --------------------------------------------------------------------------- #
#  Dry sand
# --------------------------------------------------------------------------- #

def pradel(sigma_v, sigma_eff, n1_60, rd, amax: float, magnitude: float,
           k0: float = 0.5, pa: float = 101.325) -> np.ndarray:
    """Volumetric strain of dry sand by Pradel (1998), a fraction, already
    doubled for multidirectional shaking:

        τav    = 0.65·(a_max/g)·σv·rd
        p      = (1 + 2·K0)/3 · σ'v
        Gmax   = 447·Pa·(N1)60^(1/3)·(p/Pa)^0.5
        a      = 0.0389·(p/Pa) + 0.124,   b = 6400·(p/Pa)^−0.6
        γ      = (1 + a·exp(b·τav/Gmax)) / (1 + a) · τav/Gmax
        ε15    = γ·((N1)60/20)^−1.2
        εv     = 2 · ε15 · (Neq/15)^0.45,   Neq = (M − 4)^2.17
    """
    n1 = np.maximum(np.asarray(n1_60, dtype=float), 1.0)
    p = np.maximum((1.0 + 2.0 * k0) / 3.0 * np.asarray(sigma_eff, dtype=float), 1e-3)
    tau = 0.65 * amax * np.asarray(sigma_v, dtype=float) * np.asarray(rd, dtype=float)
    g_max = 447.0 * pa * n1 ** (1.0 / 3.0) * (p / pa) ** 0.5
    a = 0.0389 * (p / pa) + 0.124
    b = 6400.0 * (p / pa) ** -0.6
    ratio = tau / g_max
    gamma = (1.0 + a * np.exp(np.minimum(b * ratio, 50.0))) / (1.0 + a) * ratio
    eps15 = gamma * (n1 / 20.0) ** -1.2
    n_eq = max(magnitude - 4.0, 0.1) ** 2.17
    return np.minimum(2.0 * eps15 * (n_eq / 15.0) ** 0.45, DRY_STRAIN_MAX)


#: The largest dry-sand strain taken [fraction]; beyond it the fit is extrapolated
DRY_STRAIN_MAX = 0.05


def _pieces(top: np.ndarray, bot: np.ndarray, lo: float, hi: float):
    """Each interval clipped to [lo, hi], cut into pieces of at most STEP.

    Returns (index of the interval, mid-depth, thickness) of every piece.
    """
    index, mid, dz = [], [], []
    for i, (a, b) in enumerate(zip(top, bot)):
        a, b = max(float(a), lo), min(float(b), hi)
        if b <= a + 1e-12:
            continue
        n = max(1, int(np.ceil((b - a) / STEP - 1e-9)))
        edges = np.linspace(a, b, n + 1)
        index.extend([i] * n)
        mid.extend(0.5 * (edges[:-1] + edges[1:]))
        dz.extend(np.diff(edges))
    return np.array(index, dtype=int), np.array(mid), np.array(dz)


def lpi(top, bot, fs, water: float) -> Tuple[float, np.ndarray]:
    """Iwasaki's LPI of the intervals [top, bot] with factor of safety fs
    (NaN: not liquefiable), and the contribution of each interval."""
    top, bot = np.asarray(top, float), np.asarray(bot, float)
    fs = np.asarray(fs, float)
    severity = np.where(np.isfinite(fs) & (fs < 1.0), 1.0 - fs, 0.0)
    part = np.zeros(len(top))
    index, mid, dz = _pieces(top, bot, max(water, 0.0), LPI_DEPTH)
    if index.size:
        np.add.at(part, index, severity[index] * (10.0 - 0.5 * mid) * dz)
    return float(part.sum()), part


def lsn(top, bot, eps, water: float, depth: float) -> Tuple[float, np.ndarray]:
    """LSN = 1000·∫ εv/z dz of the intervals, with εv as a fraction, and the
    contribution of each interval."""
    top, bot = np.asarray(top, float), np.asarray(bot, float)
    eps = np.asarray(eps, float)
    part = np.zeros(len(top))
    index, mid, dz = _pieces(top, bot, max(water, 0.0), depth)
    if index.size:
        np.add.at(part, index, 1000.0 * eps[index] * dz / np.maximum(mid, STEP / 2.0))
    return float(part.sum()), part


def lpi_class(value: float) -> str:
    if value <= 0.0:
        return "none"
    if value <= 5.0:
        return "low"
    return "high" if value <= 15.0 else "very_high"


def lsn_class(value: float) -> str:
    for limit, name in zip((10.0, 20.0, 30.0, 40.0, 50.0), LSN_CLASSES):
        if value < limit:
            return name
    return "severe"
