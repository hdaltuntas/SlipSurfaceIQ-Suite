"""
Earth pressure coefficients, the trial wedge, and the seismic thrust.

Everything here is a closed-form expression, or a one-dimensional search,
evaluated for one set of angles, so each one can be checked on its own
against its published value.

    rankine_ka / rankine_kp
                   Rankine's coefficients of a backfill sloping at β behind a
                   vertical back, the pressure parallel to the surface:
                   Ka = cos β·(cos β − √(cos²β − cos²φ)) / (cos β + √(…)).
                   At β = 0 they are tan²(45 ∓ φ/2).
    coulomb_ka / coulomb_kp
                   Coulomb's coefficients with the back inclined θ from the
                   horizontal (90° vertical), wall friction δ and a slope β.
    k0             The coefficient at rest, EN 1997-1 eq. (9.2):
                   (1 − sin φ)·√OCR·(1 + sin β), Jáky's 1 − sin φ at OCR = 1.
    trial_wedge    Coulomb's wedge solved numerically: the planes through the
                   heel are tried one after another and the largest thrust
                   kept, with the surcharge on the wedge counted in. It
                   reproduces coulomb_ka and gives the critical plane.
    mononobe_okabe / mononobe_okabe_kp
                   The Mononobe–Okabe coefficients KAE and KPE for the
                   seismic coefficients kh and kv, a vertical back, wall
                   friction δ and a slope β. The thrust is
                   ½·γ·H²·(1 − kv)·KAE.
    seed_whitman   ΔKAE = ¾·kh, Seed & Whitman's (1970) simplification.
    wood           Wood's (1973) dynamic thrust of a wall that cannot yield,
                   ΔP = kh·γ·H² (EN 1998-5 E.9).

Angles are given in degrees and turned into radians inside.
"""

from __future__ import annotations

import math
from typing import Dict

__all__ = ["rankine_ka", "rankine_kp", "coulomb_ka", "coulomb_kp", "k0", "trial_wedge",
           "mononobe_okabe", "mononobe_okabe_kp", "seed_whitman", "wood_increment",
           "seismic_angle", "rankine_angle"]


def _r(deg: float) -> float:
    return math.radians(float(deg))


def _slope_root(phi: float, beta: float) -> float:
    cb, cp = math.cos(_r(beta)), math.cos(_r(phi))
    return math.sqrt(max(cb * cb - cp * cp, 0.0))


def rankine_ka(phi: float, beta: float = 0.0) -> float:
    """Rankine's active coefficient, the pressure parallel to a slope β ≤ φ."""
    phi, beta = float(phi), float(beta)
    if beta > phi + 1e-9:
        raise ValueError("the backslope is steeper than the friction angle")
    cb = math.cos(_r(beta))
    root = _slope_root(phi, beta)
    return cb * (cb - root) / (cb + root)


def rankine_kp(phi: float, beta: float = 0.0) -> float:
    """Rankine's passive coefficient for a surface sloping at β ≤ φ."""
    phi, beta = float(phi), float(beta)
    if abs(beta) > phi + 1e-9:
        raise ValueError("the slope is steeper than the friction angle")
    cb = math.cos(_r(beta))
    root = _slope_root(phi, beta)
    return cb * (cb + root) / max(cb - root, 1e-12)


def rankine_angle(phi: float) -> float:
    """Inclination of Rankine's active failure plane from the horizontal, 45 + φ/2."""
    return 45.0 + float(phi) / 2.0


def coulomb_ka(phi: float, theta: float = 90.0, delta: float = 0.0,
               beta: float = 0.0) -> float:
    """Coulomb's active coefficient (AASHTO LRFD eq. 3.11.5.3-1).

    `theta` is the inclination of the back from the horizontal, 90° for a
    vertical back; `delta` the friction between the soil and the back; `beta`
    the slope of the backfill. A slope steeper than the friction angle has no
    active state, and is refused.
    """
    phi, theta, delta, beta = float(phi), float(theta), float(delta), float(beta)
    if beta > phi + 1e-9:
        raise ValueError("the backslope is steeper than the friction angle")
    p, t, d, b = _r(phi), _r(theta), _r(delta), _r(beta)
    root = math.sqrt(max(math.sin(p + d) * math.sin(p - b), 0.0)
                     / (math.sin(t - d) * math.sin(t + b)))
    gamma = (1.0 + root) ** 2
    return math.sin(t + p) ** 2 / (gamma * math.sin(t) ** 2 * math.sin(t - d))


def coulomb_kp(phi: float, theta: float = 90.0, delta: float = 0.0,
               beta: float = 0.0) -> float:
    """Coulomb's passive coefficient for a back at θ from the horizontal.

    Coulomb's plane overestimates the passive resistance once δ exceeds about
    φ/2; the caller is expected to keep δ small.
    """
    phi, theta, delta, beta = float(phi), float(theta), float(delta), float(beta)
    p, t, d, b = _r(phi), _r(theta), _r(delta), _r(beta)
    inner = (math.sin(p + d) * math.sin(p + b)) / (math.sin(t + d) * math.sin(t + b))
    root = math.sqrt(max(inner, 0.0))
    if root >= 1.0:
        raise ValueError("no Coulomb passive state for these angles")
    return math.sin(t - p) ** 2 / (math.sin(t) ** 2 * math.sin(t + d) * (1.0 - root) ** 2)


def k0(phi: float, OCR: float = 1.0, beta: float = 0.0) -> float:
    """The coefficient at rest, (1 − sin φ)·√OCR·(1 + sin β) (EN 1997-1 9.5.2)."""
    phi = float(phi)
    return (1.0 - math.sin(_r(phi))) * math.sqrt(max(float(OCR), 1.0)) \
        * (1.0 + math.sin(_r(beta)))


def trial_wedge(phi: float, delta: float, beta: float, h: float, gamma: float,
                q: float = 0.0, steps: int = 720) -> Dict[str, float]:
    """Coulomb's active wedge behind a vertical back of height h, solved by trial.

    Every plane from the heel at an angle α between β and 90° is tried; the
    wedge above it carries its weight and the surcharge q on its surface,
    the plane resists at φ from its normal and the back at δ. The largest
    thrust P, the plane that gives it and the equivalent coefficient
    K = 2·P / (γ·h² + 2·q·h) are returned.
    """
    phi, delta, beta = float(phi), float(delta), float(beta)
    h, gamma, q = float(h), float(gamma), float(q)
    if h <= 0 or gamma <= 0:
        raise ValueError("the wedge needs a height and a unit weight")
    if beta > phi + 1e-9:
        raise ValueError("the backslope is steeper than the friction angle")
    tb = math.tan(_r(beta))
    cd, sd = math.cos(_r(delta)), math.sin(_r(delta))

    def thrust(alpha_deg: float) -> float:
        a = _r(alpha_deg)
        ta = math.tan(a)
        if ta - tb <= 1e-9:
            return 0.0
        x = h / (ta - tb)                    # the plane meets the surface here
        W = 0.5 * gamma * h * x + q * x      # the wedge and its surcharge
        # R = N·(−sin α + tan φ·cos α, cos α + tan φ·sin α) resists on the plane;
        # the back pushes with P·(cos δ, sin δ); ΣF = 0 gives P.
        tp = math.tan(_r(phi))
        rx = -math.sin(a) + tp * math.cos(a)
        ry = math.cos(a) + tp * math.sin(a)
        det = cd * ry - sd * rx
        if abs(det) < 1e-12:
            return 0.0
        P = W * (-rx) / det
        return max(P, 0.0)

    lo = max(beta, 0.0) + 0.05
    best_a, best_p = lo, 0.0
    for i in range(steps + 1):
        a = lo + (89.95 - lo) * i / steps
        p = thrust(a)
        if p > best_p:
            best_a, best_p = a, p
    # refine by golden section around the best trial
    span = (89.95 - lo) / steps
    left, right = max(lo, best_a - span), min(89.95, best_a + span)
    g = (math.sqrt(5.0) - 1.0) / 2.0
    for _ in range(60):
        m1 = right - g * (right - left)
        m2 = left + g * (right - left)
        if thrust(m1) > thrust(m2):
            right = m2
        else:
            left = m1
    best_a = 0.5 * (left + right)
    best_p = thrust(best_a)
    K = 2.0 * best_p / (gamma * h * h + 2.0 * q * h)
    return {"P": best_p, "alpha": best_a, "K": K}


def seismic_angle(kh: float, kv: float = 0.0) -> float:
    """ψ = atan(kh / (1 − kv)), in degrees."""
    return math.degrees(math.atan2(float(kh), 1.0 - float(kv)))


def mononobe_okabe(phi: float, kh: float, kv: float = 0.0, delta: float = 0.0,
                   beta: float = 0.0) -> Dict[str, float]:
    """Mononobe–Okabe KAE behind a vertical back.

    `kv` is positive upward (it lightens the wedge). Where φ − ψ − β < 0 no
    pseudo-static active state exists; the limiting value, with the root
    taken as zero, is returned and flagged, since the backfill itself is then
    at failure under the acceleration.
    """
    p, d, b = _r(phi), _r(delta), _r(beta)
    psi = math.atan2(float(kh), 1.0 - float(kv))
    limited = p - psi - b < -1e-9
    root = math.sqrt(max(math.sin(p + d) * math.sin(p - psi - b), 0.0)
                     / (math.cos(d + psi) * math.cos(b)))
    kae = math.cos(p - psi) ** 2 / (math.cos(psi) * math.cos(d + psi) * (1.0 + root) ** 2)
    return {"KAE": kae, "psi": math.degrees(psi), "limited": limited}


def mononobe_okabe_kp(phi: float, kh: float, kv: float = 0.0, delta: float = 0.0,
                      beta: float = 0.0) -> float:
    """Mononobe–Okabe KPE in front of a vertical back (ground at slope β)."""
    p, d, b = _r(phi), _r(delta), _r(beta)
    psi = math.atan2(float(kh), 1.0 - float(kv))
    inner = (math.sin(p + d) * math.sin(p - psi + b)) / (math.cos(d + psi) * math.cos(b))
    root = math.sqrt(max(inner, 0.0))
    if root >= 1.0:
        raise ValueError("no Mononobe-Okabe passive state for these angles")
    return math.cos(p - psi) ** 2 / (math.cos(psi) * math.cos(d + psi) * (1.0 - root) ** 2)


def seed_whitman(kh: float) -> float:
    """ΔKAE = ¾·kh (Seed & Whitman 1970)."""
    return 0.75 * max(float(kh), 0.0)


def wood_increment(kh: float, gamma: float, h: float) -> float:
    """Wood's dynamic thrust of an unyielding wall, ΔP = kh·γ·h² (EN 1998-5 E.9)."""
    return max(float(kh), 0.0) * float(gamma) * float(h) ** 2
