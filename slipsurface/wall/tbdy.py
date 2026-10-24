"""
The earthquake of TBDY 2018 (Türkiye Bina Deprem Yönetmeliği), as a
retaining wall needs it.

    site_factors      the local site coefficients Fs (short period, Table 2.1)
                      and F1 (one second, Table 2.2) of the site classes
                      ZA … ZE, interpolated linearly between the tabulated
                      spectral accelerations
    spectrum          SDS = Ss·Fs, SD1 = S1·F1 and the corner periods
                      TA = 0.2·SD1/SDS, TB = SD1/SDS, TL = 6 s (§2.3.4)
    sae               the horizontal elastic design spectrum Sae(T), eq. (2.2)
    coefficients      the equivalent seismic coefficients of a retaining
                      structure (§16.12): kh = βr·0.4·SDS, reduced by βr for a
                      wall allowed to move, and kv = ratio·kh

Ss and S1 are read from the AFAD hazard map (tdth.afad.gov.tr) for the site,
for the DD-2 ground motion level (a 475-year return period) unless the
project asks for another. The site class ZF has no tabulated coefficients:
TBDY asks for a site-specific response analysis, and the program refuses it.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from .config import MOBILITY, SITE_CLASSES

__all__ = ["SS_POINTS", "S1_POINTS", "FS_TABLE", "F1_TABLE", "TL", "site_factors",
           "spectrum", "sae", "coefficients"]

#: The spectral accelerations the site coefficients are tabulated at
SS_POINTS = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50]
S1_POINTS = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60]

#: TBDY 2018 Table 2.1: the short-period site coefficient Fs
FS_TABLE = {
    "ZA": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    "ZB": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
    "ZC": [1.3, 1.3, 1.2, 1.2, 1.2, 1.2],
    "ZD": [1.6, 1.4, 1.2, 1.1, 1.0, 1.0],
    "ZE": [2.4, 1.7, 1.3, 1.1, 0.9, 0.8],
}

#: TBDY 2018 Table 2.2: the one-second site coefficient F1
F1_TABLE = {
    "ZA": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    "ZB": [0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    "ZC": [1.5, 1.5, 1.5, 1.5, 1.5, 1.4],
    "ZD": [2.4, 2.2, 2.0, 1.9, 1.8, 1.7],
    "ZE": [4.2, 3.3, 2.8, 2.4, 2.2, 2.0],
}

#: The long-period corner of the spectrum [s]
TL = 6.0

#: The share of SDS that makes the equivalent seismic coefficient of a wall
KH_SHARE = 0.4


def site_factors(Ss: float, S1: float, site: str) -> Dict[str, float]:
    """Fs and F1 of a site class, interpolated linearly (and held at the ends)."""
    if site not in SITE_CLASSES:
        raise ValueError(f"unknown site class: {site}")
    Ss, S1 = float(Ss), float(S1)
    if Ss < 0 or S1 < 0:
        raise ValueError("the spectral accelerations cannot be negative")
    Fs = float(np.interp(Ss, SS_POINTS, FS_TABLE[site]))
    F1 = float(np.interp(S1, S1_POINTS, F1_TABLE[site]))
    return {"Fs": Fs, "F1": F1}


def spectrum(Ss: float, S1: float, site: str) -> Dict[str, float]:
    """The design spectral accelerations and the corner periods."""
    f = site_factors(Ss, S1, site)
    SDS, SD1 = float(Ss) * f["Fs"], float(S1) * f["F1"]
    TB = SD1 / SDS if SDS > 0 else 0.0
    return {"Ss": float(Ss), "S1": float(S1), "site": site, "Fs": f["Fs"], "F1": f["F1"],
            "SDS": SDS, "SD1": SD1, "TA": 0.2 * TB, "TB": TB, "TL": TL,
            "PGA_eq": KH_SHARE * SDS}


def sae(T, spec: Dict[str, float]):
    """Sae(T) of TBDY 2018 eq. (2.2), for a period or an array of periods."""
    T = np.asarray(T, dtype=float)
    SDS, SD1, TA, TB = spec["SDS"], spec["SD1"], spec["TA"], spec["TB"]
    out = np.where(T < TA, (0.4 + 0.6 * T / max(TA, 1e-12)) * SDS, SDS)
    out = np.where(T > TB, SD1 / np.maximum(T, 1e-12), out)
    out = np.where(T > TL, SD1 * TL / np.maximum(T, 1e-12) ** 2, out)
    return out if out.ndim else float(out)


def coefficients(SDS: float, mobility: str = "rigid", kv_ratio: float = 0.5,
                 kh_manual: float = 0.0) -> Dict[str, float]:
    """kh = βr·0.4·SDS (or the kh given) and kv = ratio·kh."""
    beta_r = MOBILITY.get(mobility, 1.0)
    manual = float(kh_manual) > 0
    kh = float(kh_manual) if manual else beta_r * KH_SHARE * float(SDS)
    return {"kh": kh, "kv": float(kv_ratio) * kh, "beta_r": beta_r, "manual": manual}
