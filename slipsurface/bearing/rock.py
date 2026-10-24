"""
Bearing capacity of a foundation on rock.

Two routes, both in everyday use:

    hoek_brown  The Hoek–Brown rock mass is turned into the equivalent
                Mohr–Coulomb strength of Hoek, Carranza-Torres & Corkum
                (2002) over the stress range a foundation works in, and that
                c' and φ' are given to the general bearing capacity equation
                like any other soil. The rock mass constants are

                    mb = mi·e^((GSI − 100)/(28 − 14·D))
                    s  = e^((GSI − 100)/(9 − 3·D))
                    a  = ½ + (e^(−GSI/15) − e^(−20/3))/6

                and the fit is made up to σ3max = σci/4, the upper end of the
                confinement a shallow foundation on rock mobilises.

    ksp         The Canadian Foundation Engineering Manual's discontinuity
                spacing method: for a jointed rock mass whose joints are near
                vertical, tight and more widely spaced than the footing is
                pressed into them,

                    Ksp = (3 + s/B) / (10·√(1 + 300·δ/s))

                and the allowable pressure is Ksp·σci·d, with a depth factor
                d = 1 + 0.4·D/B ≤ 3.4. A factor of safety of about 3 is
                already inside Ksp, so the ultimate capacity is three times it.

σci is in MPa; the pressures returned are in kPa like the rest of the program.
"""

from __future__ import annotations

import math
from typing import Dict

__all__ = ["hoek_brown_constants", "rock_mass_strength", "equivalent_mohr_coulomb",
           "ksp_capacity", "SIGMA3_RATIO"]

#: The upper end of the confinement the equivalent Mohr–Coulomb fit covers
SIGMA3_RATIO = 0.25


def hoek_brown_constants(GSI: float, mi: float, D: float = 0.0) -> Dict[str, float]:
    """mb, s and a of the Hoek–Brown (2002) rock mass."""
    gsi = min(max(float(GSI), 5.0), 100.0)
    d = min(max(float(D), 0.0), 1.0)
    mb = float(mi) * math.exp((gsi - 100.0) / (28.0 - 14.0 * d))
    s = math.exp((gsi - 100.0) / (9.0 - 3.0 * d))
    a = 0.5 + (math.exp(-gsi / 15.0) - math.exp(-20.0 / 3.0)) / 6.0
    return {"mb": mb, "s": s, "a": a, "GSI": gsi, "D": d}


def rock_mass_strength(sigma_ci: float, GSI: float, mi: float, D: float = 0.0) -> float:
    """The global rock mass strength σcm (2002), in the units of σci."""
    k = hoek_brown_constants(GSI, mi, D)
    mb, s, a = k["mb"], k["s"], k["a"]
    numerator = (mb + 4.0 * s - a * (mb - 8.0 * s)) * (mb / 4.0 + s) ** (a - 1.0)
    return float(sigma_ci) * numerator / (2.0 * (1.0 + a) * (2.0 + a))


def equivalent_mohr_coulomb(sigma_ci: float, GSI: float, mi: float, D: float = 0.0,
                            sigma3_max: float = 0.0) -> Dict[str, float]:
    """The equivalent c' [kPa] and φ' [°] of the rock mass.

    `sigma_ci` and `sigma3_max` are in MPa; leaving `sigma3_max` at zero takes
    σci/4, the confinement a shallow foundation on rock works within.
    """
    k = hoek_brown_constants(GSI, mi, D)
    mb, s, a = k["mb"], k["s"], k["a"]
    sci = max(float(sigma_ci), 1e-9)
    s3max = float(sigma3_max) if sigma3_max and sigma3_max > 0 else SIGMA3_RATIO * sci
    s3n = s3max / sci

    common = (s + mb * s3n) ** (a - 1.0)
    upper = 6.0 * a * mb * common
    phi = math.degrees(math.asin(min(upper / (2.0 * (1.0 + a) * (2.0 + a) + upper), 1.0)))
    c = (sci * ((1.0 + 2.0 * a) * s + (1.0 - a) * mb * s3n) * common
         / ((1.0 + a) * (2.0 + a) * math.sqrt(1.0 + upper / ((1.0 + a) * (2.0 + a)))))
    return {"c": c * 1000.0, "phi": phi, "sigma3_max": s3max,
            "sigma_cm": rock_mass_strength(sci, GSI, mi, D) * 1000.0, **k}


def ksp_capacity(sigma_ci: float, spacing: float, aperture: float, B: float,
                 Df: float = 0.0, FS: float = 3.0) -> Dict[str, float]:
    """The CFEM discontinuity-spacing capacity, in kPa.

    `sigma_ci` is in MPa, the spacing in m and the aperture in mm. The method
    is written for a spacing greater than 0.3 m and an aperture below 5 mm;
    outside that range the result is reported with `valid` false.
    """
    B = max(float(B), 1e-9)
    s = max(float(spacing), 1e-6)
    delta = max(float(aperture), 0.0) / 1000.0          # mm -> m
    ksp = (3.0 + s / B) / (10.0 * math.sqrt(1.0 + 300.0 * delta / s))
    depth = min(1.0 + 0.4 * float(Df) / B, 3.4)
    q_all = ksp * float(sigma_ci) * 1000.0 * depth      # MPa -> kPa
    return {"Ksp": ksp, "depth_factor": depth, "q_all": q_all,
            "q_ult": q_all * float(FS), "FS_inside": float(FS),
            "valid": s >= 0.3 and float(aperture) <= 5.0 and B >= 0.3}
