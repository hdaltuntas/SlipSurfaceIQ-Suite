"""
The outline of a cantilever wall, and the plane geometry it needs.

Coordinates are in metres, per metre run of wall: x from the front edge of
the footing (the toe) towards the backfill, y up from the underside of the
footing. The stem rises from the top of the footing with one face vertical
and the other inclined (the taper), the heel runs back to x = B, and a shear
key, if there is one, hangs below the base.

    polygon_area_centroid   the shoelace formula
    clip_below / clip_above a polygon cut by a horizontal line
    Outline                 the concrete parts, the soil on the heel and on
                            the toe, the faces of the stem and the ground
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

Point = Tuple[float, float]

__all__ = ["polygon_area_centroid", "clip_below", "clip_above", "Outline"]


def polygon_area_centroid(poly: Sequence[Point]) -> Tuple[float, float, float]:
    """Area and centroid (x, y) of a simple polygon; zero area gives its mean point."""
    n = len(poly)
    if n < 3:
        if not poly:
            return 0.0, 0.0, 0.0
        return 0.0, sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n
    a = cx = cy = 0.0
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    if abs(a) < 1e-12:
        return 0.0, sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n
    return abs(a), cx / (6.0 * a), cy / (6.0 * a)


def _clip(poly: Sequence[Point], level: float, keep_below: bool) -> List[Point]:
    """Sutherland–Hodgman against the half-plane y ≤ level (or y ≥ level)."""
    def inside(p: Point) -> bool:
        return p[1] <= level + 1e-12 if keep_below else p[1] >= level - 1e-12

    out: List[Point] = []
    n = len(poly)
    for i in range(n):
        cur, nxt = poly[i], poly[(i + 1) % n]
        cin, nin = inside(cur), inside(nxt)
        if cin:
            out.append(cur)
        if cin != nin:
            dy = nxt[1] - cur[1]
            t = (level - cur[1]) / dy if abs(dy) > 1e-15 else 0.0
            out.append((cur[0] + t * (nxt[0] - cur[0]), level))
    return out


def clip_below(poly: Sequence[Point], level: float) -> List[Point]:
    """The part of a polygon at or below y = level."""
    return _clip(poly, level, True)


def clip_above(poly: Sequence[Point], level: float) -> List[Point]:
    """The part of a polygon at or above y = level."""
    return _clip(poly, level, False)


class Outline:
    """The wall's outline from its dimensions."""

    def __init__(self, H: float, t_top: float, t_bot: float, taper: str, toe: float,
                 heel: float, t_f: float, D: float, beta: float,
                 key: Dict[str, float] = None):
        self.H, self.t_top, self.t_bot = float(H), float(t_top), float(t_bot)
        self.taper = taper if taper in ("back", "front") else "back"
        self.toe, self.heel, self.t_f, self.D = float(toe), float(heel), float(t_f), float(D)
        self.beta = float(beta)
        self.B = self.toe + self.t_bot + self.heel
        self.Hs = self.H - self.t_f
        key = key or {}
        self.key_on = bool(key.get("enabled", False))
        self.key_depth = float(key.get("depth", 0.0)) if self.key_on else 0.0
        self.key_width = float(key.get("width", 0.0)) if self.key_on else 0.0
        self.key_x = float(key.get("offset", 0.0)) if self.key_on else 0.0

    # ------------------------------------------------------------------ faces
    @property
    def x_back_base(self) -> float:
        return self.toe + self.t_bot

    @property
    def x_back_top(self) -> float:
        return self.toe + (self.t_top if self.taper == "back" else self.t_bot)

    @property
    def x_front_top(self) -> float:
        return self.toe if self.taper == "back" else self.toe + self.t_bot - self.t_top

    def x_front(self, y: float) -> float:
        """The front face of the stem at a height y (from the base)."""
        s = min(max((y - self.t_f) / max(self.Hs, 1e-9), 0.0), 1.0)
        return self.toe + s * (self.x_front_top - self.toe)

    def x_back(self, y: float) -> float:
        """The back face of the stem at a height y."""
        s = min(max((y - self.t_f) / max(self.Hs, 1e-9), 0.0), 1.0)
        return self.x_back_base + s * (self.x_back_top - self.x_back_base)

    def thickness(self, y: float) -> float:
        """The thickness of the stem at a height y."""
        return self.x_back(y) - self.x_front(y)

    @property
    def tan_beta(self) -> float:
        return math.tan(math.radians(self.beta))

    def ground_back(self, x: float) -> float:
        """The backfill surface above a point x behind the stem."""
        return self.H + max(x - self.x_back_top, 0.0) * self.tan_beta

    @property
    def h_virtual(self) -> float:
        """Height of the virtual back through the end of the heel."""
        return self.ground_back(self.B)

    @property
    def front_ground(self) -> float:
        """The ground over the toe, above the base."""
        return self.t_f + self.D

    # ------------------------------------------------------------------ parts
    def stem(self) -> List[Point]:
        return [(self.toe, self.t_f), (self.x_back_base, self.t_f),
                (self.x_back_top, self.H), (self.x_front_top, self.H)]

    def footing(self) -> List[Point]:
        return [(0.0, 0.0), (self.B, 0.0), (self.B, self.t_f), (0.0, self.t_f)]

    def key(self) -> List[Point]:
        if not self.key_on:
            return []
        x0, x1 = self.key_x, self.key_x + self.key_width
        return [(x0, 0.0), (x0, -self.key_depth), (x1, -self.key_depth), (x1, 0.0)]

    def heel_soil(self) -> List[Point]:
        """The soil standing on the heel, up to the ground, behind the stem."""
        return [(self.x_back_base, self.t_f), (self.B, self.t_f), (self.B, self.h_virtual),
                (self.x_back_top, self.H)]

    def toe_soil(self) -> List[Point]:
        """The soil over the toe, against the front face of the stem."""
        if self.D <= 0 or self.toe <= 0:
            return []
        top = self.front_ground
        return [(0.0, self.t_f), (self.toe, self.t_f), (self.x_front(top), top), (0.0, top)]

    def concrete_parts(self) -> Dict[str, List[Point]]:
        parts = {"stem": self.stem(), "footing": self.footing()}
        if self.key_on:
            parts["key"] = self.key()
        return parts

    def concrete_area(self) -> float:
        return sum(polygon_area_centroid(p)[0] for p in self.concrete_parts().values())
