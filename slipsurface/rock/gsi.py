"""
The Geological Strength Index, from whatever the site investigation gives.

    direct   typed in
    chart    the two classes of the GSI chart — structure and surface
             condition — placed on the quantified chart (`tables.chart_gsi`)
    jcond    Hoek, Carter & Diederichs (2013): GSI = 1.5·JCond89 + RQD/2
    rmr      Hoek, Kaiser & Bawden (1995): GSI = RMR89 − 5, with the
             groundwater rating set to 15 (dry) and no orientation adjustment;
             not for RMR89 < 23
    q        Hoek et al. (1995): GSI = 9·ln Q' + 44, with Q' = RQD/Jn · Jr/Ja
    cai      Cai et al. (2004), from the block volume Vb [cm³] and the joint
             condition factor Jc = JW·JS/JA:

                 GSI = (26.5 + 8.79·ln Jc + 0.9·ln Vb)
                       / (1 + 0.0151·ln Jc − 0.0253·ln Vb)

Every route returns the value together with the numbers it came from, so the
report can say how GSI was arrived at.
"""

from __future__ import annotations

import math
from typing import Dict

from . import tables

__all__ = ["from_jcond", "from_rmr", "from_q", "from_cai", "estimate", "RMR_LIMIT"]

#: Below this RMR89 the RMR route is not recommended (Hoek et al. 1995)
RMR_LIMIT = 23.0


def from_jcond(JCond89: float, RQD: float) -> float:
    return 1.5 * float(JCond89) + float(RQD) / 2.0


def from_rmr(RMR89: float) -> float:
    return float(RMR89) - 5.0


def from_q(Q_prime: float) -> float:
    return 9.0 * math.log(float(Q_prime)) + 44.0


def from_cai(Vb: float, Jc: float) -> float:
    ln_jc, ln_vb = math.log(float(Jc)), math.log(float(Vb))
    return (26.5 + 8.79 * ln_jc + 0.9 * ln_vb) / (1.0 + 0.0151 * ln_jc - 0.0253 * ln_vb)


def estimate(rock_mass: Dict[str, float]) -> Dict[str, float]:
    """GSI by the route the rock mass section names.

    Returns ``{"GSI": value, "source": route, ...inputs}``; raises ValueError
    with the name of the offending input when the route cannot be taken.
    """
    source = rock_mass.get("gsi_source", "direct")
    if source == "chart":
        structure = rock_mass.get("structure", "very_blocky")
        surface = rock_mass.get("surface", "fair")
        return {"GSI": tables.chart_gsi(structure, surface), "source": source,
                "structure": structure, "surface": surface}
    if source == "jcond":
        jcond, rqd = float(rock_mass["JCond89"]), float(rock_mass["RQD"])
        if not 0.0 <= jcond <= 30.0:
            raise ValueError("JCond89")
        if not 0.0 <= rqd <= 100.0:
            raise ValueError("RQD")
        return {"GSI": from_jcond(jcond, rqd), "source": source, "JCond89": jcond,
                "RQD": rqd}
    if source == "rmr":
        rmr = float(rock_mass["RMR89"])
        if not 0.0 < rmr <= 100.0:
            raise ValueError("RMR89")
        return {"GSI": from_rmr(rmr), "source": source, "RMR89": rmr}
    if source == "q":
        q = float(rock_mass["Q_prime"])
        if q <= 0.0:
            raise ValueError("Q_prime")
        return {"GSI": from_q(q), "source": source, "Q_prime": q}
    if source == "cai":
        vb, jc = float(rock_mass["Vb"]), float(rock_mass["Jc"])
        if vb <= 0.0:
            raise ValueError("Vb")
        if jc <= 0.0:
            raise ValueError("Jc")
        return {"GSI": from_cai(vb, jc), "source": source, "Vb": vb, "Jc": jc}
    return {"GSI": float(rock_mass["GSI"]), "source": "direct"}
