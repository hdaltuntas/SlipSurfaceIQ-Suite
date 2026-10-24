"""Reinforced-concrete bored pile wall: stiffness and bending capacity of one pile.

A bored (contiguous, secant or tangent) pile wall is a row of circular piles. The
wall analyses work per metre of wall, so a pile of diameter D at spacing s carries
the moment of a metre times s, and its stiffness is shared over s.

The bending capacity is that of a circular section with the bars on a ring, under
bending alone (the axial load of a retaining pile is small beside its bending),
by TS 500: a rectangular stress block of 0.85 fcd over the depth k1 c, an ultimate
concrete strain of 0.003 and an elastic - perfectly plastic steel. Neutral axis
depth follows from axial equilibrium.

Shear follows the TS 500 provisions with the section taken as a rectangle of width D and
effective depth 0.8 D (the usual rule for circular sections, as in ACI 318): the cracking
strength V_cr = 0.65 f_ctd b d, the concrete share V_c = 0.8 V_cr, the crushing limit
V_max = 0.22 f_cd b d, and the links V_w = (A_sw / s) f_ywd d with two legs crossing the
section. The shear is the largest of the analysis, at no reduction near the support.

Units: kPa, m, kN, kNm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List

__all__ = ["CONCRETE_GRADES", "REBAR_GRADES", "BoredPile", "circular_moment_capacity",
           "concrete_modulus", "k1_factor"]

#: Characteristic cylinder strength f_ck (kPa)
CONCRETE_GRADES: Dict[str, float] = {
    "C25": 25000.0, "C30": 30000.0, "C35": 35000.0, "C40": 40000.0, "C45": 45000.0, "C50": 50000.0,
}

#: Characteristic yield strength f_yk (kPa)
REBAR_GRADES: Dict[str, float] = {"B420C": 420000.0, "B500C": 500000.0}

ES = 200e6          # steel modulus (kPa)
EPS_CU = 0.003      # ultimate concrete strain


def concrete_modulus(fck: float) -> float:
    """TS 500: E_c = 3250 sqrt(f_ck) + 14000 (MPa), returned in kPa."""
    return (3250.0 * math.sqrt(fck / 1000.0) + 14000.0) * 1000.0


def k1_factor(fck: float) -> float:
    """TS 500 stress-block depth factor: 0.85 up to C25, 0.006 less per MPa above, not below 0.70."""
    return max(0.70, 0.85 - 0.006 * (fck / 1000.0 - 25.0)) if fck > 25000.0 else 0.85


def _segment(radius: float, depth: float):
    """Area of the circular segment of ``depth`` from the edge, and its centroid's distance from the centre."""
    depth = min(depth, 2.0 * radius)
    if depth <= 0.0:
        return 0.0, 0.0
    if depth >= 2.0 * radius:
        return math.pi * radius ** 2, 0.0
    theta = 2.0 * math.acos((radius - depth) / radius)          # central angle of the chord
    area = 0.5 * radius ** 2 * (theta - math.sin(theta))
    centroid = 4.0 * radius * math.sin(theta / 2.0) ** 3 / (3.0 * (theta - math.sin(theta)))
    return area, centroid


def _forces(c: float, radius: float, ring_radius: float, angles: List[float], bar_area: float,
            fcd: float, fyd: float, k1: float):
    """Axial force and moment about the centre (compression and top-side moment positive) at neutral axis depth ``c``."""
    area, centroid = _segment(radius, k1 * c)
    force = 0.85 * fcd * area
    moment = force * centroid
    for angle in angles:
        y = ring_radius * math.cos(angle)                       # height of the bar above the centre
        strain = EPS_CU * (y - (radius - c)) / c
        stress = max(-fyd, min(fyd, ES * strain))
        force += stress * bar_area
        moment += stress * bar_area * y
    return force, moment


def circular_moment_capacity(diameter: float, ring_radius: float, bar_count: int, bar_area: float,
                             fcd: float, fyd: float, k1: float, axial: float = 0.0):
    """Moment capacity (kNm) of a circular section with bars on a ring, and its neutral axis depth (m).

    The bars are placed both with one bar on the bending axis and half a spacing off it, and the
    weaker orientation governs.
    """
    radius = diameter / 2.0
    best = None
    for offset in (0.0, math.pi / bar_count):
        angles = [offset + 2.0 * math.pi * i / bar_count for i in range(bar_count)]
        lo, hi = 1e-4 * diameter, 20.0 * diameter
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            force, _ = _forces(mid, radius, ring_radius, angles, bar_area, fcd, fyd, k1)
            lo, hi = (mid, hi) if force < axial else (lo, mid)
        c = 0.5 * (lo + hi)
        moment = _forces(c, radius, ring_radius, angles, bar_area, fcd, fyd, k1)[1]
        if best is None or moment < best[0]:
            best = (moment, c)
    return best


@dataclass
class BoredPile:
    """One reinforced-concrete pile of a bored pile wall and its properties per metre of wall."""

    diameter: float            # m
    spacing: float             # m, centre to centre
    concrete: str
    rebar: str
    bar_count: int
    bar_diameter: float        # m
    cover: float               # m, clear cover to the links
    link_diameter: float       # m
    link_spacing: float        # m, along the pile
    link_grade: str
    fywk: float                # links, kPa
    stiffness_factor: float    # cracked / gross flexural stiffness
    moment_factor: float       # factor on the analysis moment (loads)
    gamma_c: float
    gamma_s: float
    fck: float
    fyk: float

    @classmethod
    def from_config(cls, data: Dict[str, Any], concrete_grades=None, rebar_grades=None) -> "BoredPile":
        concrete_grades = concrete_grades or CONCRETE_GRADES
        rebar_grades = rebar_grades or REBAR_GRADES
        concrete, rebar = data["concrete_grade"], data["rebar_grade"]
        link_grade = data.get("link_grade", rebar)
        if concrete not in concrete_grades:
            raise ValueError(f"Concrete grade '{concrete}' not in database.")
        for grade in (rebar, link_grade):
            if grade not in rebar_grades:
                raise ValueError(f"Reinforcement grade '{grade}' not in database.")
        pile = cls(
            diameter=float(data["diameter"]), spacing=float(data["spacing"]),
            concrete=concrete, rebar=rebar, bar_count=int(round(float(data["bar_count"]))),
            bar_diameter=float(data["bar_diameter"]) / 1000.0, cover=float(data["cover"]) / 1000.0,
            link_diameter=float(data["link_diameter"]) / 1000.0,
            link_spacing=float(data.get("link_spacing", 150.0)) / 1000.0,
            link_grade=link_grade, fywk=rebar_grades[link_grade],
            stiffness_factor=float(data["stiffness_factor"]),
            moment_factor=float(data["moment_factor"]),
            gamma_c=float(data["gamma_c"]), gamma_s=float(data["gamma_s"]),
            fck=concrete_grades[concrete], fyk=rebar_grades[rebar])
        pile.validate()
        return pile

    # -------------------------------------------------------------- geometry
    @property
    def ring_radius(self) -> float:
        """Radius of the ring of bar centres (m)."""
        return self.diameter / 2.0 - self.cover - self.link_diameter - self.bar_diameter / 2.0

    @property
    def bar_area(self) -> float:
        return math.pi * self.bar_diameter ** 2 / 4.0

    @property
    def steel_area(self) -> float:
        return self.bar_count * self.bar_area

    @property
    def gross_area(self) -> float:
        return math.pi * self.diameter ** 2 / 4.0

    @property
    def reinforcement_ratio(self) -> float:
        return self.steel_area / self.gross_area

    @property
    def clear_bar_spacing(self) -> float:
        """Clear distance between neighbouring bars along the ring (m)."""
        return 2.0 * math.pi * self.ring_radius / self.bar_count - self.bar_diameter

    def validate(self) -> None:
        if self.diameter <= 0 or self.spacing <= 0:
            raise ValueError("The pile diameter and spacing must be positive.")
        if self.bar_count < 6:
            raise ValueError("A bored pile needs at least 6 longitudinal bars.")
        if self.bar_diameter <= 0 or self.cover < 0 or self.link_diameter < 0:
            raise ValueError("Bar diameter, cover and link diameter must not be negative.")
        if self.ring_radius <= 0:
            raise ValueError("The cover leaves no room for the reinforcement ring.")
        if self.clear_bar_spacing <= 0:
            raise ValueError("The bars do not fit on the ring: use fewer or thinner bars.")
        if self.link_spacing <= 0:
            raise ValueError("The link spacing must be positive.")
        if not 0.1 <= self.stiffness_factor <= 1.0:
            raise ValueError("The stiffness factor must lie between 0.1 and 1.0.")
        if self.moment_factor < 1.0 or self.gamma_c < 1.0 or self.gamma_s < 1.0:
            raise ValueError("The moment factor and the material factors must be at least 1.0.")

    # ------------------------------------------------------ material, stiffness
    @property
    def fcd(self) -> float:
        return self.fck / self.gamma_c

    @property
    def fyd(self) -> float:
        return self.fyk / self.gamma_s

    @property
    def ecm(self) -> float:
        return concrete_modulus(self.fck)

    @property
    def gross_inertia(self) -> float:
        """Second moment of area of one gross pile section (m^4)."""
        return math.pi * self.diameter ** 4 / 64.0

    @property
    def inertia_per_metre(self) -> float:
        """Effective (cracked) second moment of area per metre of wall (m^4/m)."""
        return self.stiffness_factor * self.gross_inertia / self.spacing

    # ---------------------------------------------------------------- capacity
    def capacity(self):
        """Design bending capacity M_Rd of one pile (kNm) and the neutral axis depth (m)."""
        return circular_moment_capacity(
            self.diameter, self.ring_radius, self.bar_count, self.bar_area,
            self.fcd, self.fyd, k1_factor(self.fck))

    @property
    def m_rd(self) -> float:
        return self.capacity()[0]

    @property
    def m_rd_per_metre(self) -> float:
        """Design bending capacity per metre of wall (kNm/m)."""
        return self.m_rd / self.spacing

    # ------------------------------------------------------------------ shear
    @property
    def shear_width(self) -> float:
        """Width b of the equivalent rectangle (m)."""
        return self.diameter

    @property
    def shear_depth(self) -> float:
        """Effective depth d of the equivalent rectangle (m)."""
        return 0.8 * self.diameter

    @property
    def fctd(self) -> float:
        """Design tensile strength: 0.35 sqrt(f_ck) (MPa) over the concrete factor, in kPa."""
        return 0.35 * math.sqrt(self.fck / 1000.0) * 1000.0 / self.gamma_c

    @property
    def fywd(self) -> float:
        """Design yield stress of the links (kPa)."""
        return self.fywk / self.gamma_s

    @property
    def link_area(self) -> float:
        """Area of the links crossing one shear plane: two legs (m^2)."""
        return 2.0 * math.pi * self.link_diameter ** 2 / 4.0

    @property
    def max_link_spacing(self) -> float:
        """Largest link spacing: half the effective depth, and not more than 200 mm (m)."""
        return min(0.5 * self.shear_depth, 0.2)

    def shear_check(self, v_max_abs: float) -> Dict[str, Any]:
        """The shear and link check for the largest shear of the analysis (kN per metre of wall).

        Returns the demand and the capacities per pile (kN) and a status string like the
        other checks ("OK" or "NOT OK - reason").
        """
        b, d = self.shear_width, self.shear_depth
        v_ed = v_max_abs * self.spacing * self.moment_factor
        v_cr = 0.65 * self.fctd * b * d
        v_c = 0.8 * v_cr
        v_max = 0.22 * self.fcd * b * d
        per_metre_of_pile = self.link_area / self.link_spacing                 # A_sw / s
        v_w = per_metre_of_pile * self.fywd * d
        asw_min = 0.3 * self.fctd * b / self.fywd                            # minimum A_sw / s
        if v_ed > v_c:
            required = min(self.link_area * self.fywd * d / (v_ed - v_c), self.max_link_spacing)
        else:
            required = self.max_link_spacing
        if v_ed > v_max:
            status = "NOT OK - SECTION TOO SMALL (CONCRETE CRUSHING)"
        elif per_metre_of_pile < asw_min:
            status = "NOT OK - LINKS BELOW THE MINIMUM"
        elif self.link_spacing > self.max_link_spacing:
            status = "NOT OK - LINKS TOO WIDELY SPACED"
        elif v_ed > v_c + v_w:
            status = "NOT OK - LINKS INSUFFICIENT"
        else:
            status = "OK"
        return {
            "v_ed": v_ed, "v_cr": v_cr, "v_c": v_c, "v_w": v_w, "v_max": v_max,
            "v_rd": min(v_c + v_w, v_max), "asw_min": asw_min, "asw_s": per_metre_of_pile,
            "link_spacing": self.link_spacing, "max_link_spacing": self.max_link_spacing,
            "required_spacing": required, "status": status,
        }
