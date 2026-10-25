"""
The general bearing capacity equation, and the geometry an eccentric or
inclined load gives it.

    q_ult = c·Nc·sc·dc·ic·bc·gc·Fc
          + q·Nq·sq·dq·iq·bq·gq·Fq
          + ½·γ·B'·Nγ·sγ·dγ·iγ·bγ·gγ·Fγ

with the factors of `slipsurface.common.factors`. Hansen's undrained expression is
additive rather than multiplicative and is written out separately:

    q_ult = 5.14·cu·(1 + s'c + d'c − i'c − b'c − g'c) + q

An eccentric load is carried on Meyerhof's effective area: the rectangle
B' = B − 2e_B by L' = L − 2e_L centred on the resultant, which for a circle
becomes the equivalent rectangle of the loaded circular segment. The capacity
is a pressure on that area, so the load it carries is q_ult·A'.

Nothing here reads the soil profile: the caller passes the design strength,
the surcharge and the unit weight it has already worked out, which keeps the
equation testable against a hand calculation line by line.
"""

from __future__ import annotations

import math
from typing import Dict

from slipsurface.common import factors as F

__all__ = ["effective_area", "contact_pressure", "ultimate", "sliding_resistance",
           "wedge_depth", "wedge_geometry"]


# --------------------------------------------------------------------------- #
#  Eccentricity: the effective area
# --------------------------------------------------------------------------- #

def effective_area(shape: str, B: float, L: float, V: float, Mb: float = 0.0,
                   Ml: float = 0.0, use_effective: bool = True) -> Dict[str, float]:
    """Meyerhof's effective area of a footing under an eccentric load.

    Returns the eccentricities e_B and e_L, the effective dimensions B' and L'
    (B' ≤ L' as the factors expect) and the effective area A'. With
    `use_effective` off the full area is returned, and the eccentricities are
    reported for the checks all the same.
    """
    B, L, V = float(B), float(L), float(V)
    if shape == "circle":
        L = B
    if shape == "square":
        L = B
    eB = abs(float(Mb)) / V if V > 0 else 0.0
    eL = abs(float(Ml)) / V if V > 0 else 0.0
    if shape == "strip":
        eL = 0.0

    out = {"e_B": eB, "e_L": eL, "B": B, "L": L}
    if not use_effective:
        area = math.pi * (B / 2.0) ** 2 if shape == "circle" else B * L
        out.update({"B_eff": B, "L_eff": L, "A_eff": area, "effective": False})
        return out

    if shape == "circle":
        radius = B / 2.0
        e = math.hypot(eB, eL)
        if e >= radius:
            out.update({"B_eff": 0.0, "L_eff": 0.0, "A_eff": 0.0, "effective": True})
            return out
        # the loaded segment, and Vesić's equivalent rectangle of the same area
        area = 2.0 * (radius ** 2 * math.acos(e / radius) - e * math.sqrt(radius ** 2 - e ** 2))
        ratio = math.sqrt((radius + e) / (radius - e)) if e > 0 else 1.0
        b_eff = math.sqrt(area / ratio)
        out.update({"B_eff": b_eff, "L_eff": area / b_eff if b_eff > 0 else 0.0,
                    "A_eff": area, "effective": True})
        return out

    b_eff = B - 2.0 * eB
    l_eff = L - 2.0 * eL
    if b_eff <= 0 or l_eff <= 0:
        out.update({"B_eff": max(b_eff, 0.0), "L_eff": max(l_eff, 0.0), "A_eff": 0.0,
                    "effective": True})
        return out
    # the factors are written for B ≤ L
    short, long_ = (b_eff, l_eff) if b_eff <= l_eff else (l_eff, b_eff)
    out.update({"B_eff": short, "L_eff": long_, "A_eff": b_eff * l_eff, "effective": True})
    return out


def contact_pressure(shape: str, B: float, L: float, V: float, Mb: float = 0.0,
                     Ml: float = 0.0) -> Dict[str, float]:
    """The linear contact pressure under the full base.

    Inside the kern (e ≤ B/6 in both directions) the pressure is trapezoidal,
    q = V/A·(1 ± 6e_B/B ± 6e_L/L). Outside it the base lifts, and for an
    eccentricity in one direction only the pressure is the triangular
    q_max = 2V/(3·L·(B/2 − e)) over a contact length of 3(B/2 − e).
    """
    B, L, V = float(B), float(L), float(V)
    if shape in ("square", "circle"):
        L = B
    area = math.pi * (B / 2.0) ** 2 if shape == "circle" else B * L
    eB = abs(float(Mb)) / V if V > 0 else 0.0
    eL = abs(float(Ml)) / V if V > 0 else 0.0
    if shape == "strip":
        eL = 0.0
    mean = V / area if area > 0 else 0.0
    inside = (eB <= B / 6.0 + 1e-12) and (eL <= L / 6.0 + 1e-12)

    if inside:
        spread = 6.0 * eB / B + 6.0 * eL / L
        return {"q_mean": mean, "q_max": mean * (1.0 + spread),
                "q_min": mean * (1.0 - spread), "in_kern": True,
                "contact": B, "e_B": eB, "e_L": eL, "kern": B / 6.0}

    if eL <= 1e-12 and shape != "circle" and eB < B / 2.0:
        contact = 3.0 * (B / 2.0 - eB)
        return {"q_mean": mean, "q_max": 2.0 * V / (L * contact) if contact > 0 else float("inf"),
                "q_min": 0.0, "in_kern": False, "contact": contact,
                "e_B": eB, "e_L": eL, "kern": B / 6.0}

    # Two-way eccentricity outside the kern, or a circle: the linear
    # distribution is no longer valid and only the effective area is reported.
    return {"q_mean": mean, "q_max": float("nan"), "q_min": 0.0, "in_kern": False,
            "contact": float("nan"), "e_B": eB, "e_L": eL, "kern": B / 6.0}


# --------------------------------------------------------------------------- #
#  The failure zone
# --------------------------------------------------------------------------- #

def wedge_depth(B: float, phi: float) -> float:
    """Depth of the Prandtl failure zone below the base.

    The elastic wedge under the footing reaches (B/2)·tan(45 + φ/2); the log
    spiral r = r₀·e^(θ tan φ) that springs from the footing edge, r₀ =
    (B/2)/cos(45 + φ/2), turns through 90° to meet the passive Rankine zone.
    The spiral is deepest where its radius makes 90° − φ with the horizontal,

        z_max = (B/2)·cos φ / cos(45 + φ/2)·e^((π/4 + φ/2)·tan φ)

    which is the familiar 0.707·B at φ = 0 and about 1.6·B at φ = 30°. It is
    the depth the figures draw, and the depth over which the strength of a
    layered profile is averaged.
    """
    p = math.radians(max(float(phi), 0.0))
    r0 = (float(B) / 2.0) / math.cos(math.radians(45.0 + float(phi) / 2.0))
    return r0 * math.cos(p) * math.exp((math.pi / 4.0 + p / 2.0) * math.tan(p))


def wedge_geometry(B: float, phi: float, points: int = 60) -> Dict[str, list]:
    """The Prandtl failure mechanism as polylines, for the section drawing.

    Returns the elastic wedge (a triangle under the base), the log spiral of
    the right-hand fan and the straight face of the passive Rankine zone that
    carries it to the ground surface. x is measured from the centre of the
    base and z downwards from it; the left-hand half is the mirror image.
    """
    B = float(B)
    half = B / 2.0
    p = math.radians(max(float(phi), 0.0))
    alpha = math.radians(45.0 + float(phi) / 2.0)
    apex = half * math.tan(alpha)
    r0 = half / math.cos(alpha)

    wedge = [(-half, 0.0), (0.0, apex), (half, 0.0)]
    start = math.radians(135.0 - float(phi) / 2.0)      # direction of O → apex
    spiral = []
    for i in range(points + 1):
        theta = (math.pi / 2.0) * i / points             # the fan turns 90°
        psi = start - theta
        r = r0 * math.exp(theta * math.tan(p))
        spiral.append((half + r * math.cos(psi), r * math.sin(psi)))
    # the passive wedge: from the end of the spiral up to the ground surface
    # along a plane at 45 − φ/2 to the horizontal
    end_x, end_z = spiral[-1]
    rise = math.radians(45.0 - float(phi) / 2.0)
    surface_x = end_x + end_z / math.tan(rise) if rise > 0 else end_x
    passive = [(end_x, end_z), (surface_x, 0.0)]
    return {"wedge": wedge, "spiral": spiral, "passive": passive,
            "apex": apex, "depth": wedge_depth(B, phi), "extent": surface_x}


# --------------------------------------------------------------------------- #
#  The equation
# --------------------------------------------------------------------------- #

def ultimate(method: str, *, c: float, phi: float, gamma: float, q: float,
             B: float, L: float, Df: float, shape: str = "rectangle",
             V: float = 0.0, Hb: float = 0.0, Hl: float = 0.0, area: float = 0.0,
             eta: float = 0.0, beta: float = 0.0, G: float = 0.0, q_mid: float = 0.0,
             **flags) -> Dict[str, object]:
    """One method's ultimate bearing capacity, term by term.

    `B` and `L` are the effective dimensions, `q` the surcharge at the base
    (effective in a drained analysis, total in an undrained one), `gamma` the
    unit weight below the base (buoyant where the soil is submerged) and
    `area` the effective area A'. The flags are passed straight to
    `factors.all_factors`.
    """
    fac = F.all_factors(method, B=B, L=L, Df=Df, phi=phi, c=c, V=V, Hb=Hb, Hl=Hl,
                        area=area, eta=eta, beta=beta, shape=shape, G=G, q_mid=q_mid,
                        **flags)
    N = fac["N"]

    def product(part: str) -> float:
        return (fac["shape"][part] * fac["depth"][part] * fac["inclination"][part]
                * fac["base"][part] * fac["ground"][part] * fac["compressibility"][part])

    undrained = phi <= F.PHI_ZERO
    if method == "hansen" and undrained:
        # Hansen's additive form: the corrections add to, and subtract from, 1
        bracket = (1.0 + fac["shape"]["c"] - 1.0 + fac["depth"]["c"] - 1.0
                   - fac["inclination"]["c"] - fac["base"]["c"] - fac["ground"]["c"])
        term_c = 5.14 * c * bracket * fac["compressibility"]["c"]
        term_q, term_g = q, 0.0
        form = "additive"
    else:
        term_c = c * N["Nc"] * product("c")
        term_q = q * N["Nq"] * product("q")
        term_g = 0.5 * gamma * B * N["Ngamma"] * product("g")
        form = "product"

    q_ult = term_c + term_q + term_g
    return {
        "method": method,
        "q_ult": q_ult,
        "q_net_ult": q_ult - q,
        "terms": {"c": term_c, "q": term_q, "g": term_g},
        "N": N,
        "factors": {key: dict(fac[key]) for key in
                    ("shape", "depth", "inclination", "base", "ground", "compressibility")},
        "form": form,
        "undrained": undrained,
        "inputs": {"c": c, "phi": phi, "gamma": gamma, "q": q, "B": B, "L": L,
                   "A": area, "Df": Df},
    }


def sliding_resistance(V: float, area: float, c: float, phi: float,
                       delta_ratio: float = 1.0, undrained: bool = False,
                       adhesion_ratio: float = 1.0) -> Dict[str, float]:
    """Resistance of the base to sliding.

    Drained: R = V·tan δ + A'·c'a, with δ = delta_ratio·φ' (1.0 for a footing
    cast against the soil, 2/3 for a precast one). Undrained: R = A'·cu,
    limited by the adhesion the interface can take.
    """
    V = float(V)
    if undrained:
        resistance = float(area) * float(c) * float(adhesion_ratio)
        return {"R": resistance, "friction": 0.0, "adhesion": resistance,
                "delta": 0.0}
    delta = float(delta_ratio) * float(phi)
    friction = V * math.tan(math.radians(delta))
    adhesion = float(area) * float(c) * float(adhesion_ratio)
    return {"R": friction + adhesion, "friction": friction, "adhesion": adhesion,
            "delta": delta}
