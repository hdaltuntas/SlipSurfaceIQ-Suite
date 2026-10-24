"""
Bearing capacity read straight from an in-situ test.

These are the rules an engineer reaches for when the strength parameters are
not measured but the test result is: they give a pressure, not a strength, and
most of them are governed by settlement rather than by rupture. The program
shows them beside the capacities of the general equation, where they belong —
as a second opinion.

    SPT   Meyerhof's (1956) rule as revised by Bowles: the net pressure that
          keeps the settlement of a footing on sand within Se,

              q = 19.16·N60·Fd·(Se/25.4)                      B ≤ 1.22 m
              q = 11.98·N60·((3.28B + 1)/(3.28B))²·Fd·(Se/25.4)   B > 1.22 m

          with Fd = 1 + 0.33·Df/B ≤ 1.33, q in kPa and Se in mm. The friction
          angle correlated from N60 (Wolff 1989) is offered as well, so the
          general equation can be run on the same borehole.

    CPT   Meyerhof's cone rule, of the same settlement-governed kind,
          q = qc/30 for B ≤ 1.2 m and q = (qc/50)·((B + 0.3)/B)² above it,
          scaled by Se/25 and by the same depth factor; and Robertson &
          Campanella's (1983) friction angle from qc/σ'v0.

    PMT   Ménard's pressuremeter rule, q_net,ult = kp·(pl − p0), with the
          bearing factor kp of the French practice (Fascicule 62 / NF P
          94-261) for the soil category and the embedment ratio.

Pressures are in kPa, qc and pl in MPa as they are measured.
"""

from __future__ import annotations

import math
from typing import Dict

__all__ = ["spt_pressure", "phi_from_spt", "cpt_pressure", "phi_from_cpt",
           "menard_kp", "pmt_capacity", "PMT_FACTORS"]

#: The depth factor of the settlement rules, capped as Meyerhof capped it
def _depth_factor(B: float, Df: float) -> float:
    return min(1.0 + 0.33 * float(Df) / max(float(B), 1e-9), 1.33)


def spt_pressure(N60: float, B: float, Df: float, settlement: float = 25.0) -> Dict[str, float]:
    """The net allowable pressure on sand from the SPT, in kPa."""
    B = max(float(B), 1e-9)
    fd = _depth_factor(B, Df)
    scale = float(settlement) / 25.4
    if B <= 1.22:
        q = 19.16 * float(N60) * fd * scale
    else:
        q = 11.98 * float(N60) * ((3.28 * B + 1.0) / (3.28 * B)) ** 2 * fd * scale
    return {"q_all": q, "Fd": fd, "wide": B > 1.22, "settlement": float(settlement)}


def phi_from_spt(N60: float) -> float:
    """Wolff's (1989) correlation φ' = 27.1 + 0.3·N60 − 0.00054·N60² [°]."""
    n = max(float(N60), 0.0)
    return 27.1 + 0.3 * n - 0.00054 * n ** 2


def cpt_pressure(qc: float, B: float, Df: float, settlement: float = 25.0) -> Dict[str, float]:
    """The net allowable pressure from the cone, in kPa; `qc` in MPa."""
    B = max(float(B), 1e-9)
    qc_kpa = float(qc) * 1000.0
    fd = _depth_factor(B, Df)
    scale = float(settlement) / 25.0
    if B <= 1.2:
        q = qc_kpa / 30.0
    else:
        q = (qc_kpa / 50.0) * ((B + 0.3) / B) ** 2
    return {"q_all": q * fd * scale, "Fd": fd, "wide": B > 1.2,
            "settlement": float(settlement)}


def phi_from_cpt(qc: float, sigma_v: float) -> float:
    """Robertson & Campanella (1983): φ' = arctan[0.1 + 0.38·log₁₀(qc/σ'v0)].

    `qc` is in MPa and `sigma_v` the effective overburden in kPa.
    """
    ratio = (float(qc) * 1000.0) / max(float(sigma_v), 1.0)
    if ratio <= 1.0:
        return 0.0
    return math.degrees(math.atan(0.1 + 0.38 * math.log10(ratio)))


#: Ménard's bearing factor: (kp0, slope) per soil category, kp = kp0·[1 + slope·(0.6 + 0.4·B/L)·De/B]
PMT_FACTORS = {
    "clay_a": (0.8, 0.25),
    "clay_b": (0.8, 0.35),
    "sand_a": (1.0, 0.35),
    "sand_b": (1.3, 0.50),
    "rock": (1.0, 0.27),
}

#: The embedment ratio the rule is written for; beyond it kp is held constant
DE_OVER_B_MAX = 2.0


def menard_kp(category: str, B: float, L: float, Df: float, strip: bool = False) -> float:
    """Ménard's bearing factor kp for a shallow foundation."""
    kp0, slope = PMT_FACTORS.get(category, PMT_FACTORS["sand_a"])
    ratio = 0.0 if strip else min(float(B) / max(float(L), 1e-9), 1.0)
    de_b = min(float(Df) / max(float(B), 1e-9), DE_OVER_B_MAX)
    return kp0 * (1.0 + slope * (0.6 + 0.4 * ratio) * de_b)


def pmt_capacity(pl: float, p0: float, category: str, B: float, L: float, Df: float,
                 q0: float = 0.0, strip: bool = False) -> Dict[str, float]:
    """Ménard's bearing capacity: q_net,ult = kp·(pl − p0); pressures in MPa in, kPa out."""
    kp = menard_kp(category, B, L, Df, strip)
    net_limit = max(float(pl) - float(p0), 0.0) * 1000.0        # MPa -> kPa
    q_net = kp * net_limit
    return {"kp": kp, "pl_net": net_limit, "q_net_ult": q_net,
            "q_ult": q_net + float(q0)}
