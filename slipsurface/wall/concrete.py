"""
Reinforced concrete by TS 500 (2000), as the members of a retaining wall need it.

Every member of a cantilever wall — the stem, the toe, the heel, the key — is
a slab one metre wide bent in one direction, so what is needed is short:

    Material          fcd = fck/γmc, fyd = fyk/γms (γmc = 1.5, γms = 1.15),
                      fctk = 0.35·√fck, fctd = fctk/γmc, and the depth factor
                      k1 of the equivalent stress block (0.85 up to C25, less
                      0.006 per MPa above, not below 0.70)
    required_steel    the tension steel of a moment, from the rectangular
                      stress block 0.85·fcd over a depth a:
                      Md = 0.85·fcd·b·a·(d − a/2), As = 0.85·fcd·b·a / fyd
    moment_capacity   Mr of a given steel
    balanced_ratio    ρb = 0.85·k1·(fcd/fyd)·εcu·Es / (εcu·Es + fyd); the
                      tension steel is kept below 0.85·ρb (TS 500 7.3)
    shear             Vcr = 0.65·fctd·b·d — a slab carries its shear without
                      stirrups — and the upper limit 0.22·fcd·b·d (TS 500 8.1)
    development       lb = 0.12·(fyd/fctd)·φ ≥ 20·φ (TS 500 9.1), ×1.4 for a
                      bar with more than 300 mm of fresh concrete below it
    choose_bars       the diameter and spacing that give the steel asked for
                      with the least area, within the spacing allowed

Units: moments in kNm, shears in kN, lengths in mm, areas in mm² — per metre
of wall, so b = 1000 mm unless said otherwise.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from .config import GRADES, STEELS

__all__ = ["Material", "GAMMA_C", "GAMMA_S", "ES", "ECU", "BARS", "SPACINGS",
           "bar_area", "bar_mass", "k1_factor", "required_steel", "moment_capacity",
           "shear_capacity", "development_length", "choose_bars", "max_spacing"]

GAMMA_C = 1.5
GAMMA_S = 1.15
ES = 200000.0             # MPa
ECU = 0.003

#: The bar diameters offered [mm]
BARS = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32]

#: The spacings the bars are laid at [mm]
SPACINGS = [100, 125, 150, 175, 200, 250, 300]

#: TS 500 one-way slabs: the main bars no further apart than 1.5·h and 200 mm,
#: the distribution bars no further than 300 mm
MAIN_SPACING, DIST_SPACING = 200.0, 300.0

#: The smallest bar of a main (tension) layer, and of a distribution layer
MAIN_MIN_BAR, DIST_MIN_BAR = 12, 10


def bar_area(phi: float) -> float:
    """Area of one bar [mm²]."""
    return math.pi * float(phi) ** 2 / 4.0


def bar_mass(phi: float) -> float:
    """Mass of one metre of bar [kg/m], steel at 7850 kg/m³."""
    return 7850.0 * bar_area(phi) * 1e-6


def k1_factor(fck: float) -> float:
    """Depth factor of the equivalent rectangular stress block (TS 500 Table 7.1)."""
    fck = float(fck)
    if fck <= 25.0:
        return 0.85
    return max(0.85 - 0.006 * (fck - 25.0), 0.70)


class Material:
    """Design strengths of one concrete class and one steel grade."""

    def __init__(self, grade: str = "C30", steel: str = "B420C"):
        if grade not in GRADES:
            raise ValueError(f"unknown concrete class: {grade}")
        if steel not in STEELS:
            raise ValueError(f"unknown steel grade: {steel}")
        self.grade, self.steel = grade, steel
        self.fck = GRADES[grade]
        self.fyk = STEELS[steel]
        self.fcd = self.fck / GAMMA_C
        self.fyd = self.fyk / GAMMA_S
        self.fctk = 0.35 * math.sqrt(self.fck)
        self.fctd = self.fctk / GAMMA_C
        self.k1 = k1_factor(self.fck)
        self.rho_b = balanced_ratio(self)
        self.rho_max = min(0.85 * self.rho_b, 0.02)

    def as_dict(self) -> Dict[str, float]:
        return {"grade": self.grade, "steel": self.steel, "fck": self.fck, "fyk": self.fyk,
                "fcd": self.fcd, "fyd": self.fyd, "fctk": self.fctk, "fctd": self.fctd,
                "k1": self.k1, "rho_b": self.rho_b, "rho_max": self.rho_max}


def balanced_ratio(mat: Material) -> float:
    """ρb = 0.85·k1·(fcd/fyd)·εcu·Es / (εcu·Es + fyd)."""
    return 0.85 * mat.k1 * mat.fcd / mat.fyd * ECU * ES / (ECU * ES + mat.fyd)


def required_steel(Md: float, d: float, mat: Material, b: float = 1000.0) -> Optional[float]:
    """The tension steel [mm²] a moment Md [kNm] needs over an effective depth d.

    None when the section cannot carry the moment with tension steel alone
    (the compression block would have to be deeper than the section allows).
    A moment of zero or less needs none.
    """
    M = float(Md) * 1e6
    if M <= 0:
        return 0.0
    disc = d * d - 2.0 * M / (0.85 * mat.fcd * b)
    if disc < 0:
        return None
    a = d - math.sqrt(disc)
    return 0.85 * mat.fcd * b * a / mat.fyd


def moment_capacity(As: float, d: float, mat: Material, b: float = 1000.0) -> float:
    """Mr [kNm] of a tension steel As [mm²] at the effective depth d."""
    a = As * mat.fyd / (0.85 * mat.fcd * b)
    return As * mat.fyd * (d - a / 2.0) / 1e6


def shear_capacity(d: float, mat: Material, b: float = 1000.0) -> Dict[str, float]:
    """Vcr and the upper limit Vmax [kN] of a section without stirrups."""
    return {"Vcr": 0.65 * mat.fctd * b * d / 1e3, "Vmax": 0.22 * mat.fcd * b * d / 1e3}


def development_length(phi: float, mat: Material, top: bool = False) -> float:
    """lb [mm] of a straight bar in tension, TS 500 eq. (9.2)."""
    lb = max(0.12 * mat.fyd / mat.fctd * phi, 20.0 * phi)
    return lb * (1.4 if top else 1.0)


def max_spacing(h: float, main: bool = True) -> float:
    """The widest spacing of a layer in a slab h [mm] thick (TS 500 11.4)."""
    return min(1.5 * h, MAIN_SPACING) if main else DIST_SPACING


def choose_bars(As_req: float, s_max: float, preferred: int = 0,
                min_bar: int = MAIN_MIN_BAR, bars: Optional[List[int]] = None,
                spacings: Optional[List[int]] = None) -> Dict[str, object]:
    """The bar and spacing that give at least As_req [mm²/m] with the least steel.

    `preferred` fixes the diameter; otherwise every diameter from `min_bar` up
    is tried. Of two layouts with the same area the one with the fewer, wider
    spaced bars is kept, then the thinner bar. When nothing is enough the
    heaviest layout is returned with ``ok`` False.
    """
    bars = [b for b in (bars or BARS) if b >= min_bar]
    if preferred:
        bars = [int(preferred)]
    spacings = [s for s in (spacings or SPACINGS) if s <= s_max + 1e-9] or [min(SPACINGS)]
    best = None
    heaviest = None
    for phi in bars:
        for s in spacings:
            area = bar_area(phi) * 1000.0 / s
            layout = {"phi": phi, "s": s, "As": area, "ok": area >= As_req - 1e-6}
            if heaviest is None or area > heaviest["As"]:
                heaviest = layout
            if not layout["ok"]:
                continue
            key = (round(area, 3), -s, phi)
            if best is None or key < best[0]:
                best = (key, layout)
    if best is None:
        return dict(heaviest, ok=False)
    return best[1]
