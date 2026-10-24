"""
The overall stability of the wall and the ground around it, by slip circles.

A circle that passes under the footing (and under the key) and comes out in
front of the wall and in the backfill behind it carries the wall, the soil on
its heel and toe and the surcharge with it. The mass above the circle is cut
into vertical slices and the factor of safety found two ways:

    Bishop's simplified method (1955)
        F = Σ [c·b + (W − u·b)·tan φ] / mα  /  Σ [W·sin α + kh·W·(yc − yg)/R]
        with mα = cos α + sin α·tan φ / F, solved by iteration
    Fellenius' ordinary method (1936)
        F = Σ [c·l + (W·cos α − kh·W·sin α − u·l)·tan φ]  /  the same driving sum

The weight of a slice is everything above its base: the foundation soil, the
concrete of the footing, the stem and the key, the backfill and the soil in
front, saturated below the water table, and the surcharge. The pore pressure
at the base of a slice comes from a water table that runs from the water in
front of the wall to the water behind it (or lies `water_depth` below the
base when there is none). In an earthquake the horizontal inertia kh·W of
every slice drives too (kv is left out).

The critical circle is found on a grid of centres and tangent depths, refined
twice around the lowest factor. Circles that would cut the concrete are not
tried: the wall is far stronger than the soil around it.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

import numpy as np

#: Slices per circle
N_SLICES = 60

#: Coarse grid: centres across and up, tangent depths
GRID = (13, 11, 10)

#: The smallest mα Bishop's method is allowed (a steep exit at the toe)
M_ALPHA_MIN = 0.2


def _seg(ya, yb, level, gamma, gamma_sat):
    """Weight of a soil column from ya up to yb, saturated below `level`."""
    ya, yb = np.asarray(ya, float), np.asarray(yb, float)
    h = np.maximum(yb - ya, 0.0)
    wet = np.clip(np.minimum(level, yb) - ya, 0.0, None)
    wet = np.minimum(wet, h)
    return gamma * (h - wet) + gamma_sat * wet


class _Ground:
    """The section as columns: the weight above the base level, the surface."""

    def __init__(self, wall):
        self.w = wall
        g = wall.geo
        self.g = g
        self.B = wall.B
        self.fg = g.front_ground
        self.ts = math.tan(math.radians(wall.toe_slope))
        self.bf, self.fd = wall.bf, wall.fd
        self.gw, self.gc = wall.gw, wall.gc
        self.hw, self.hf, self.dw = wall.hw, wall.hf, wall.dw
        self.q = wall.q_dead + wall.q_live

    # ------------------------------------------------------------ the surface
    def front(self, x):
        return self.fg - np.abs(np.minimum(x, 0.0)) * self.ts

    def back(self, x):
        g = self.g
        return g.H + np.maximum(x - g.x_back_top, 0.0) * g.tan_beta

    def water(self, x):
        """The water table under the section."""
        y_front = self.hf if self.hf > 0 else -self.dw
        y_back = self.hw if self.hw > 0 else -self.dw
        s = np.clip(np.asarray(x, float) / max(self.B, 1e-9), 0.0, 1.0)
        return y_front + (y_back - y_front) * s

    # ------------------------------------------------------------ the stem
    def stem_top(self, x):
        """The top of the concrete of the stem above x (tf where there is none)."""
        g = self.g
        x = np.asarray(x, float)
        top = np.full_like(x, g.H)
        if g.x_back_base - g.x_back_top > 1e-9:
            yb = g.t_f + (g.x_back_base - x) / (g.x_back_base - g.x_back_top) * g.Hs
            top = np.where(x > g.x_back_top, np.minimum(top, yb), top)
        if g.x_front_top - g.toe > 1e-9:
            yf = g.t_f + (x - g.toe) / (g.x_front_top - g.toe) * g.Hs
            top = np.where(x < g.x_front_top, np.minimum(top, yf), top)
        inside = (x >= g.toe) & (x <= g.x_back_base)
        return np.where(inside, np.maximum(top, g.t_f), g.t_f)

    def above_base(self, x):
        """Weight per unit width of everything above y = 0 over x (x ≥ 0)."""
        g = self.g
        x = np.asarray(x, float)
        bf, fd = self.bf, self.fd
        w = np.zeros_like(x)
        on = (x >= 0) & (x <= self.B)
        stem_top = self.stem_top(x)
        # the footing and the stem
        w += np.where(on, self.gc * (g.t_f + (stem_top - g.t_f)), 0.0)
        # the backfill over the heel and over an inclined back
        behind = on & (x > g.x_back_top)
        ground = self.back(x)
        w += np.where(behind, _seg(stem_top, ground, self.hw, bf["gamma"], bf["gamma_sat"]),
                      0.0)
        # the soil over the toe (and against an inclined front)
        if g.D > 0:
            front_on = on & (x < g.x_front(self.fg))
            bottom = np.where(x < g.toe, g.t_f, stem_top)
            w += np.where(front_on, _seg(bottom, self.fg, self.hf, fd["gamma"],
                                         fd["gamma_sat"]), 0.0)
        # the backfill beyond the heel, from the base level up
        beyond = x > self.B
        w += np.where(beyond, _seg(0.0, ground, self.hw, bf["gamma"], bf["gamma_sat"]), 0.0)
        # the surcharge on the backfill
        w += np.where(x >= g.x_back_top, self.q, 0.0)
        return w

    def key_extra(self, x):
        """Extra weight of the key's concrete over the soil it replaces."""
        g = self.g
        if not g.key_on:
            return np.zeros_like(np.asarray(x, float))
        x = np.asarray(x, float)
        inside = (x >= g.key_x) & (x <= g.key_x + g.key_width)
        return np.where(inside, (self.gc - self.fd["gamma"]) * g.key_depth, 0.0)


def _factor(ground: _Ground, xc: float, yc: float, R: float, kh: float = 0.0
            ) -> Optional[Dict[str, Any]]:
    """Bishop's and Fellenius' factors of one circle; None if it cannot be tried."""
    g = ground.g
    B = ground.B
    if R <= 0:
        return None
    # the circle has to pass under the base (and under the key)
    def arc(x):
        return yc - np.sqrt(np.maximum(R * R - (x - xc) ** 2, 0.0))

    if abs(xc) >= R or abs(B - xc) >= R:
        return None
    if arc(0.0) > -1e-3 or arc(B) > -1e-3:
        return None
    if g.key_on:
        if max(arc(g.key_x), arc(g.key_x + g.key_width)) > -g.key_depth - 1e-3:
            return None
    # where it comes out: in front of the toe and behind the heel
    xs = np.linspace(xc - R, 0.0, 240)
    f = arc(xs) - ground.front(xs)
    if f[0] <= 0:
        return None
    idx = np.where(f <= 0)[0]
    if not len(idx):
        return None
    i = idx[0]
    xL = xs[i - 1] + (xs[i] - xs[i - 1]) * f[i - 1] / (f[i - 1] - f[i])
    xs = np.linspace(B, xc + R, 240)
    f = arc(xs) - ground.back(xs)
    if f[-1] <= 0:
        return None
    idx = np.where(f >= 0)[0]
    i = idx[0]
    if i == 0:
        return None
    xR = xs[i - 1] + (xs[i] - xs[i - 1]) * (-f[i - 1]) / (f[i] - f[i - 1])

    edges = np.linspace(xL, xR, N_SLICES + 1)
    xm = 0.5 * (edges[:-1] + edges[1:])
    b = np.diff(edges)
    yb = arc(xm)
    fd, bf = ground.fd, ground.bf
    # the weight of every slice
    top_f = np.where(xm < 0, ground.front(xm), 0.0)
    level = ground.water(xm)
    w_found = _seg(yb, top_f, level, fd["gamma"], fd["gamma_sat"])
    w_above = np.where(xm >= 0, ground.above_base(xm), 0.0)
    W = (w_found + w_above + ground.key_extra(xm)) * b
    # the height of the column's centre, for the inertia
    top = np.where(xm < 0, ground.front(xm),
                   np.where(xm > B, ground.back(xm), np.maximum(ground.stem_top(xm), g.t_f)))
    yg = 0.5 * (yb + top)
    # the strength at the base of the slice
    backfill = (xm > B) & (yb > 0)
    c = np.where(backfill, bf["c"], fd["c"])
    tphi = np.tan(np.radians(np.where(backfill, bf["phi"], fd["phi"])))
    u = ground.gw * np.clip(level - yb, 0.0, None)
    sin_a = (xm - xc) / R
    cos_a = np.sqrt(np.maximum(1.0 - sin_a ** 2, 1e-12))
    drive = float(np.sum(W * sin_a + kh * W * (yc - yg) / R))
    if drive <= 1e-9:
        return None
    # Fellenius
    l = b / cos_a
    normal = np.maximum(W * cos_a - kh * W * sin_a - u * l, 0.0)
    fs_f = float(np.sum(c * l + normal * tphi)) / drive
    # Bishop, by iteration from Fellenius' value
    fs = max(fs_f, 0.1)
    eff = np.maximum(W - u * b, 0.0)
    for _ in range(100):
        m = np.maximum(cos_a + sin_a * tphi / fs, M_ALPHA_MIN)
        new = float(np.sum((c * b + eff * tphi) / m)) / drive
        if abs(new - fs) < 1e-5:
            fs = new
            break
        fs = new
    return {"bishop": fs, "fellenius": fs_f, "xc": xc, "yc": yc, "R": R, "xL": xL, "xR": xR,
            "slices": {"x": xm, "b": b, "y": yb, "W": W}}


def search(wall, kh: float = 0.0) -> Dict[str, Any]:
    """The critical circle by Bishop's method, and Fellenius' factor for it (and his own)."""
    ground = _Ground(wall)
    g = wall.geo
    H, B = g.H, wall.B
    bottom = -g.key_depth if g.key_on else 0.0
    xs = np.linspace(-0.8 * H, B + 0.3 * H, GRID[0])
    ys = np.linspace(g.H * 0.9, g.H * 2.6 + 0.5 * B, GRID[1])
    depths = np.linspace(bottom - 0.10, bottom - max(1.2 * H, 3.0), GRID[2])
    best: Optional[Dict[str, Any]] = None
    worst_fellenius: Optional[Dict[str, Any]] = None
    tried = 0

    def consider(xc, yc, yt):
        nonlocal best, worst_fellenius, tried
        r = _factor(ground, xc, yc, yc - yt, kh)
        if r is None:
            return
        tried += 1
        if best is None or r["bishop"] < best["bishop"]:
            best = r
        if worst_fellenius is None or r["fellenius"] < worst_fellenius["fellenius"]:
            worst_fellenius = r

    for xc in xs:
        for yc in ys:
            for yt in depths:
                consider(xc, yc, yt)
    if best is None:
        return {"found": False, "tried": tried}
    dx, dy, dt = xs[1] - xs[0], ys[1] - ys[0], depths[0] - depths[1]
    for _ in range(3):
        cx, cy, ct = best["xc"], best["yc"], best["yc"] - best["R"]
        dx, dy, dt = dx / 2.5, dy / 2.5, dt / 2.5
        for i in (-2, -1, 0, 1, 2):
            for j in (-2, -1, 0, 1, 2):
                for k in (-2, -1, 0, 1, 2):
                    consider(cx + i * dx, cy + j * dy, min(ct + k * dt, bottom - 0.02))
    return {"found": True, "tried": tried, "bishop": best["bishop"],
            "fellenius": best["fellenius"], "circle": best,
            "fellenius_min": worst_fellenius["fellenius"], "fellenius_circle": worst_fellenius}


def analyse(wall, res: Dict[str, Any]) -> Dict[str, Any]:
    """The static (and seismic) search, with the checks against the criteria."""
    from .engine import _check
    crit = wall.crit
    static = search(wall)
    out: Dict[str, Any] = {"found": static["found"], "static": static, "seismic": None}
    if static["found"]:
        out["check"] = _check(static["bishop"], crit["FS_global"])
        out["check_fellenius"] = _check(static["fellenius_min"], crit["FS_global"])
    if res.get("seismic"):
        kh = res["seismic"]["coefficients"]["kh"]
        quake = search(wall, kh)
        out["seismic"] = quake
        if quake["found"]:
            out["check_seismic"] = _check(quake["bishop"], crit["FS_global_seis"])
            out["check_seismic_fellenius"] = _check(quake["fellenius_min"],
                                                    crit["FS_global_seis"])
    return out
