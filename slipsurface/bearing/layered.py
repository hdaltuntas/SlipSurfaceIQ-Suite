"""
Bearing capacity of a foundation on two layers.

Averaging the strength over the failure zone is fair when the layers are not
very different. When a strong layer of limited thickness lies over a weak one
the footing punches through it instead, and the failure surface never
develops; two checks are offered for that case.

    punching   Meyerhof & Hanna (1978). The block of the top layer under the
               footing punches into the weak layer, carrying with it the
               shear on its vertical faces:

                   q_ult = q_b + (1 + B/L)·[2·ca·H/B
                           + γ₁·H²·(1 + 2·Df/H)·Ks·tan φ₁ / B] − γ₁·H   ≤ q_t

               where q_b is the capacity of the lower layer with the footing
               brought down onto it, q_t the capacity of the top layer had it
               continued for ever, ca the adhesion on the punching faces and
               Ks the punching shear coefficient. Meyerhof and Hanna read Ks
               off a chart against φ₁ and q₂/q₁; the program uses the
               at-rest coefficient 1 − sin φ₁ unless a value is entered, which
               is the estimate Bowles suggests and is on the safe side of the
               chart.

    spread     The load is spread from the base into the top layer at a
               chosen angle (2 vertical to 1 horizontal by default) and the
               weak layer is checked under the spread pressure, as a footing
               of the spread dimensions founded on its surface. Less refined
               than punching, but it needs no chart at all.

Both are written against numbers the caller has already worked out — the two
capacities, the geometry, the top layer's strength — so neither reads the soil
profile or the configuration.
"""

from __future__ import annotations

import math
from typing import Dict

__all__ = ["punching_coefficient", "punching", "spread", "spread_dimensions"]


def punching_coefficient(phi1: float, given: float = 0.0) -> float:
    """Ks: the value entered, or the at-rest coefficient 1 − sin φ₁."""
    if given and given > 0:
        return float(given)
    return max(1.0 - math.sin(math.radians(max(float(phi1), 0.0))), 0.0)


def punching(*, q_bottom: float, q_top: float, B: float, L: float, H: float, Df: float,
             gamma1: float, c1: float, phi1: float, Ks: float = 0.0,
             adhesion_ratio: float = 1.0, strip: bool = False) -> Dict[str, float]:
    """Meyerhof & Hanna's punching capacity of a strong layer over a weak one.

    `H` is the thickness of the top layer below the foundation base, `q_bottom`
    the capacity of the lower layer with the footing brought down to depth
    Df + H, and `q_top` the capacity of the top layer alone. The result never
    exceeds `q_top`: a thick enough top layer fails in its own right.
    """
    B, L, H = float(B), max(float(L), 1e-9), float(H)
    ratio = 0.0 if strip else min(B / L, 1.0)
    ks = punching_coefficient(phi1, Ks)
    ca = float(adhesion_ratio) * float(c1)

    adhesion = (1.0 + ratio) * 2.0 * ca * H / B if B > 0 else 0.0
    friction = ((1.0 + ratio) * float(gamma1) * H ** 2 * (1.0 + 2.0 * float(Df) / H)
                * ks * math.tan(math.radians(phi1)) / B) if (B > 0 and H > 0) else 0.0
    raw = float(q_bottom) + adhesion + friction - float(gamma1) * H
    capped = min(raw, float(q_top))
    return {"q_ult": max(capped, 0.0), "q_raw": raw, "q_bottom": float(q_bottom),
            "q_top": float(q_top), "adhesion": adhesion, "friction": friction,
            "Ks": ks, "ca": ca, "H": H, "governs_top": raw > float(q_top)}


def spread_dimensions(B: float, L: float, H: float, angle: float = 26.57,
                      strip: bool = False) -> Dict[str, float]:
    """The dimensions the load has spread to at depth H below the base."""
    spread_width = 2.0 * float(H) * math.tan(math.radians(float(angle)))
    b = float(B) + spread_width
    length = float(L) if strip else float(L) + spread_width
    return {"B": b, "L": length, "A": b * length if not strip else b,
            "spread": spread_width}


def spread(*, V: float, q_bottom: float, B: float, L: float, H: float,
           angle: float = 26.57, strip: bool = False) -> Dict[str, float]:
    """The weak layer checked under the pressure the load has spread to.

    `q_bottom` is the capacity of the lower layer for a footing of the spread
    dimensions founded on its surface; the result is reported back as an
    equivalent pressure on the real base, so it can stand beside the other
    methods.
    """
    geom = spread_dimensions(B, L, H, angle, strip)
    area = geom["B"] * geom["L"] if not strip else geom["B"]
    base_area = float(B) * float(L) if not strip else float(B)
    q_spread = float(V) / area if area > 0 else float("inf")
    # the capacity of the lower layer, expressed as a pressure on the real base
    equivalent = float(q_bottom) * area / base_area if base_area > 0 else 0.0
    return {"q_ult": equivalent, "q_spread": q_spread, "q_bottom": float(q_bottom),
            "B_spread": geom["B"], "L_spread": geom["L"], "area": area,
            "FS": float(q_bottom) / q_spread if q_spread > 0 else float("inf")}
