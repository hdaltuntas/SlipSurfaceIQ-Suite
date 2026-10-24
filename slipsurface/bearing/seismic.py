"""
Pseudo-static bearing capacity.

An earthquake reaches a footing twice over: through the structure, whose
inertia adds a horizontal force and a moment at the base, and through the
soil itself, whose own inertia weakens the failure wedge. Both are treated
here in the pseudo-static way, with a horizontal and a vertical seismic
coefficient.

    structure   the inertia force kh·V is added to the horizontal load and
                the vertical load becomes V·(1 − kv), so the load inclination
                and eccentricity factors of the chosen method carry it
    soil        the factors of Paolucci & Pecker (1997) reduce the bearing
                capacity terms:

                    z_q = z_γ = (1 − kh / tan φ)^0.35        (φ > 0)
                    z_c = 1 − 0.32·kh

                which are written for a strip footing on dry soil and require
                kh < tan φ: beyond that the soil mass alone is at failure.

`kv` is taken as positive upwards, so it lightens the soil and the structure
alike; enter zero to leave the vertical direction out of it, as most codes
allow.
"""

from __future__ import annotations

import math
from typing import Dict

__all__ = ["seismic_angle", "paolucci_pecker", "apply_to_loads"]


def seismic_angle(kh: float, kv: float = 0.0) -> float:
    """ψ = arctan(kh / (1 − kv)), the tilt of the resultant body force [°]."""
    denom = 1.0 - float(kv)
    if denom <= 0:
        return 90.0
    return math.degrees(math.atan(float(kh) / denom))


def paolucci_pecker(kh: float, phi: float) -> Dict[str, float]:
    """The soil-inertia reduction of the three capacity terms."""
    kh = abs(float(kh))
    if kh <= 0:
        return {"c": 1.0, "q": 1.0, "g": 1.0, "limit": float("inf"), "exceeded": False}
    zc = max(1.0 - 0.32 * kh, 0.0)
    tan_phi = math.tan(math.radians(max(float(phi), 0.0)))
    if tan_phi <= 1e-9:                       # undrained: only the cohesion term exists
        return {"c": zc, "q": 1.0, "g": 1.0, "limit": float("inf"), "exceeded": False}
    if kh >= tan_phi:
        return {"c": zc, "q": 0.0, "g": 0.0, "limit": tan_phi, "exceeded": True}
    z = (1.0 - kh / tan_phi) ** 0.35
    return {"c": zc, "q": z, "g": z, "limit": tan_phi, "exceeded": False}


def apply_to_loads(V: float, Hb: float, Hl: float, Mb: float, Ml: float,
                   kh: float, kv: float = 0.0, height: float = 0.0) -> Dict[str, float]:
    """The actions with the structure's inertia added.

    The inertia kh·V acts in the direction of B, the direction a designer
    checks first; `height` is the height above the base at which it acts, and
    adds kh·V·h to the moment about that axis. The vertical load is scaled by
    (1 − kv).
    """
    V = float(V)
    return {
        "V": V * (1.0 - float(kv)),
        "Hb": float(Hb) + float(kh) * V,
        "Hl": float(Hl),
        "Mb": float(Mb) + float(kh) * V * float(height),
        "Ml": float(Ml),
        "psi": seismic_angle(kh, kv),
    }
