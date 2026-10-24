"""
The reinforced concrete design of the wall, and the bars that carry it.

The stem is a cantilever from the footing, loaded by the earth pressure on its
back (the method chosen for the analysis, on a vertical back of height Hs),
the water, the surcharges, a horizontal load at its top, and in an earthquake
by the dynamic increment and its own inertia. The toe and the heel are
cantilevers from the stem, loaded by the contact pressure under the base
(and the uplift) against their own weight and the soil and surcharge on
them. The shear key is a short cantilever loaded by the passive pressure in
front of it.

The member forces are enveloped over the combinations of TS 500 and TBDY
2018 (`engine.COMBINATIONS`):

    C1  1.4G + 1.6Q + 1.6H           (TS 500 6.2.6, earth pressure H)
    C2  0.9G + 1.6H                  (the weights at their least)
    C3  G + Q + H + E                (TBDY 2018 4.4.4, kv up and down,
                                      Q with its share ψ)
    C4  0.9G + H + E

and each section is designed by `slipsurface.wall.concrete` (TS 500): the tension
steel, never less than ρmin·b·h and kept below the maximum ratio; the shear,
which the concrete alone must carry (Vd ≤ Vcr); the bars and their spacing;
the development lengths. Half the bars of the stem stop where the moment
allows, extended by d (or 12φ) past the point where they are no longer
needed and never short of their development length above the footing.

The bar layout is then drawn up position by position (poz): the shapes, the
lengths, the number per metre of wall and the mass, which is the bar bending
schedule and the quantity takeoff of the wall.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np

from . import concrete as rc
from .engine import COMBINATIONS, N_PROFILE, _check, _increment_profile

#: Hooks at the ends of the bars: 12φ, and not shorter than this [m]
MIN_HOOK = 0.20

#: A curtailment is not worth it closer to the top than this [m]
MIN_CUT_FROM_TOP = 0.30

#: A combination leaving less than this share of the base in contact is
#: counted as one the wall does not survive
UNSTABLE_CONTACT = 0.10


def _round_up(x: float, step: float = 0.05) -> float:
    return math.ceil(x / step - 1e-9) * step


def _cumulative_from_top(p: np.ndarray, y: np.ndarray, point: float, top: float):
    """Shear and moment at each height from a pressure p(y) above it and a
    point load at the top."""
    n = len(y)
    V = np.zeros(n)
    M = np.zeros(n)
    for i in range(n - 2, -1, -1):
        dy = y[i + 1] - y[i]
        V[i] = V[i + 1] + 0.5 * (p[i] + p[i + 1]) * dy
        # moment grows with the shear above and the arm of the slice
        M[i] = M[i + 1] + V[i + 1] * dy + (p[i] / 6.0 + p[i + 1] / 3.0) * dy * dy
    V += point
    M += point * (top - y)
    return V, M


def _combinations(wall) -> List[Dict[str, Any]]:
    """The combinations that apply, the seismic ones with kv up and down."""
    out = []
    co = wall.seismic_coefficients() if wall.seismic_on else None
    for name, comb in COMBINATIONS.items():
        if comb["seismic"]:
            if not co:
                continue
            for sign, tag in ((1.0, "+"), (-1.0, "−")):
                out.append({"name": f"{name}{tag}", "f": comb,
                            "quake": {"kh": co["kh"], "kv": sign * co["kv"]}})
        else:
            out.append({"name": name, "f": comb, "quake": None})
    return out


# --------------------------------------------------------------------------- #
#  Member forces
# --------------------------------------------------------------------------- #

def stem_forces(wall) -> Dict[str, Any]:
    """Shear and moment down the stem, per combination and enveloped."""
    g = wall.geo
    y0, top = g.t_f, g.H
    coef = wall.coefficient(h=g.Hs)
    cw = math.cos(math.radians(coef["omega"]))
    y = np.linspace(y0, top, N_PROFILE)
    combos = {}
    for c in _combinations(wall):
        f, quake = c["f"], c["quake"]
        scale = wall.psi_live if quake else 1.0
        prof = wall.lateral_profile(y0, top, wall.q_live * scale, coef)
        p = cw * (f["H"] * (prof["soil"] + prof["dead"]) + f["Q"] * prof["live"])
        p = p + f["W"] * prof["water"]
        if quake:
            q_eff = wall.q_dead + scale * wall.q_live
            inc = wall.dynamic_increment(y0, top, q_eff, quake["kh"], quake["kv"], coef)
            dPh = inc["dP"] * math.cos(math.radians(inc["omega"]))
            p = p + f["E"] * _increment_profile(dPh, y0, top, wall.dyn_height, y)
            t = np.array([g.thickness(v) for v in y])
            p = p + f["E"] * quake["kh"] * wall.gc * t
        point = f["Q"] * scale * wall.H_top
        V, M = _cumulative_from_top(p, y, point, top)
        combos[c["name"]] = {"p": p, "V": V, "M": M}
    names = list(combos)
    M_env = np.max([combos[n]["M"] for n in names], axis=0)
    V_env = np.max([combos[n]["V"] for n in names], axis=0)
    governing = max(names, key=lambda n: combos[n]["M"][0])
    return {"y": y, "combos": combos, "M": M_env, "V": V_env, "governing": governing,
            "K": coef["K"], "omega": coef["omega"]}


def _soil_column(wall, x: np.ndarray, bottom: float, top, level: float, soil: dict):
    """Weight per unit length of a soil column from `bottom` to `top` over x."""
    top = np.broadcast_to(np.asarray(top, float), x.shape)
    h = np.maximum(top - bottom, 0.0)
    wet = np.clip(np.minimum(level, top) - bottom, 0.0, None)
    wet = np.minimum(wet, h)
    return soil["gamma"] * (h - wet) + soil["gamma_sat"] * wet


def footing_forces(wall) -> Dict[str, Any]:
    """Moments and shears of the toe and the heel at the faces of the stem."""
    g = wall.geo
    B, tf = wall.B, g.t_f
    x_toe = np.linspace(0.0, g.toe, 121) if g.toe > 0 else np.array([0.0, 0.0])
    x_heel = np.linspace(g.x_back_base, B, 121) if g.heel > 0 else np.array([B, B])
    combos = {}
    for c in _combinations(wall):
        f, quake = c["f"], c["quake"]
        F = wall.forces(f, live_vertical=f["live_vertical"], quake=quake)
        bp = wall.base_pressure(F["V"], F["e"], B)
        kv = quake["kv"] if quake else 0.0
        lighten = 1.0 - f["E"] * kv            # vertical inertia on the weights
        scale = wall.psi_live if quake else 1.0

        def uplift(x):
            if wall.hw <= 0 and wall.hf <= 0:
                return np.zeros_like(x)
            return f["W"] * wall.gw * (wall.hf + (wall.hw - wall.hf) * x / B)

        # ---------------------------------------------------------- toe
        if g.toe > 0:
            x = x_toe
            down = f["G"] * lighten * (wall.gc * tf
                                       + _soil_column(wall, x, tf, g.front_ground, wall.hf,
                                                      wall.fd))
            net = wall.pressure_at(x, bp, B) + uplift(x) - down
            arm = g.toe - x
            M_toe = float(np.trapezoid(net * arm, x)) if hasattr(np, "trapezoid") \
                else float(np.trapz(net * arm, x))
            toe_net = net
        else:
            M_toe, toe_net = 0.0, np.zeros_like(x_toe)
        # ---------------------------------------------------------- heel
        if g.heel > 0:
            x = x_heel
            ground = g.H + np.maximum(x - g.x_back_top, 0.0) * g.tan_beta
            down = f["G"] * lighten * (wall.gc * tf + _soil_column(wall, x, tf, ground,
                                                                   wall.hw, wall.bf)
                                       + wall.q_dead)
            if f["live_vertical"]:
                down = down + f["Q"] * scale * wall.q_live
            net = down - wall.pressure_at(x, bp, B) - uplift(x)
            end = sum(v for n, v, _, _ in F["vertical"] if n.endswith("_v"))
            arm = x - g.x_back_base
            integ = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
            M_heel = float(integ(net * arm, x)) + end * (B - g.x_back_base)
            heel_net, heel_end = net, end
        else:
            M_heel, heel_net, heel_end = 0.0, np.zeros_like(x_heel), 0.0
        combos[c["name"]] = {"M_toe": M_toe, "M_heel": M_heel, "toe_net": toe_net,
                             "heel_net": heel_net, "heel_end": heel_end, "pressure": bp,
                             "V": F["V"], "e": F["e"]}
    # a combination whose resultant leaves the base has no contact pressure to
    # design the footing for: the wall is not stable under it, which the
    # stability checks report; the footing is designed for the others
    unstable = [n for n, c in combos.items()
                if c["V"] <= 0 or c["pressure"]["contact"] < UNSTABLE_CONTACT * B]
    usable = {n: c for n, c in combos.items() if n not in unstable}
    return {"x_toe": x_toe, "x_heel": x_heel, "combos": usable or combos,
            "all": combos, "unstable": unstable}


def _shear_toe(x, net, x_cut):
    """Shear at x_cut from the free end of the toe (x = 0)."""
    mask = x <= x_cut + 1e-12
    if mask.sum() < 2:
        return 0.0
    integ = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(integ(net[mask], x[mask]))


def _shear_heel(x, net, end, x_cut):
    """Shear at x_cut from the free end of the heel (x = B)."""
    mask = x >= x_cut - 1e-12
    integ = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    if mask.sum() < 2:
        return end
    return float(integ(net[mask], x[mask])) + end


# --------------------------------------------------------------------------- #
#  Sections
# --------------------------------------------------------------------------- #

def _section(key: str, Md: float, Vd: float, h: float, cover: float, mat: rc.Material,
             rho_min: float, preferred: int = 0, top: bool = False,
             combo: str = "", shear_d: Optional[float] = None,
             s_max: Optional[float] = None) -> Dict[str, Any]:
    """Design one section one metre wide: the steel, the bars and the checks.

    The effective depth depends on the bar, so every diameter is tried with
    its own d, and the layout with the least steel kept.
    """
    As_min = rho_min * 1000.0 * h
    best = None
    for phi in ([int(preferred)] if preferred else [b for b in rc.BARS
                                                    if b >= rc.MAIN_MIN_BAR]):
        d = h - cover - phi / 2.0
        req = rc.required_steel(max(Md, 0.0), d, mat)
        design_as = max(req if req is not None else mat.rho_max * 1000.0 * d, As_min)
        layout = rc.choose_bars(design_as, s_max or rc.max_spacing(h, main=True), phi)
        rank = (not layout["ok"], req is None, round(layout["As"], 3), -layout["s"], phi)
        if best is None or rank < best[0]:
            best = (rank, layout, req, design_as)
    _, choice, As_req, As_design = best
    over = As_req is None
    d = h - cover - choice["phi"] / 2.0
    As_prov = choice["As"]
    Mr = rc.moment_capacity(As_prov, d, mat)
    shear = rc.shear_capacity(d, mat)
    rho = (As_req or 0.0) / (1000.0 * d) if not over else math.inf
    flexure = _check(Mr / Md if Md > 1e-9 else math.inf, 1.0, demand=Md, capacity=Mr,
                     extra=choice["ok"] and not over)
    shear_chk = _check(shear["Vcr"] / Vd if Vd > 1e-9 else math.inf, 1.0, demand=Vd,
                       capacity=shear["Vcr"], extra=Vd <= shear["Vmax"] + 1e-9)
    ratio = _check(rho, mat.rho_max, kind="limit")
    lb = rc.development_length(choice["phi"], mat, top=top)
    return {"key": key, "h": h, "d": d, "Md": Md, "Vd": Vd, "As_req": As_req,
            "As_min": As_min, "As_design": As_design, "phi": choice["phi"], "s": choice["s"],
            "As_prov": As_prov, "Mr": Mr, "Vcr": shear["Vcr"], "Vmax": shear["Vmax"],
            "rho": rho, "rho_max": mat.rho_max, "lb": lb, "combo": combo,
            "flexure": flexure, "shear": shear_chk, "ratio": ratio, "over": over,
            "shear_d": shear_d}


def _distribution(key: str, As_req: float, h: float, preferred: int = 0) -> Dict[str, Any]:
    """A distribution (or minimum) layer: bars no further apart than 300 mm."""
    choice = rc.choose_bars(As_req, rc.max_spacing(h, main=False), preferred,
                            min_bar=rc.DIST_MIN_BAR)
    return {"key": key, "h": h, "As_req": As_req, "phi": choice["phi"], "s": choice["s"],
            "As_prov": choice["As"], "ok": choice["ok"]}


def _curtailment(wall, stem: Dict[str, Any], sec: Dict[str, Any], mat: rc.Material,
                 cover: float) -> Dict[str, Any]:
    """Where half the stem bars can stop, and the capacity along the stem."""
    g = wall.geo
    y = stem["y"]
    phi, s = sec["phi"], sec["s"]
    t = np.array([g.thickness(v) for v in y]) * 1000.0
    d = t - cover - phi / 2.0
    As = sec["As_prov"]
    Mr_full = np.array([rc.moment_capacity(As, dd, mat) for dd in d])
    Mr_half = np.array([rc.moment_capacity(As / 2.0, dd, mat) for dd in d])
    out = {"enabled": False, "y_theory": math.nan, "y_cut": math.nan,
           "Mr_full": Mr_full, "Mr_half": Mr_half, "Mr": Mr_full.copy()}
    if not wall.concrete.get("curtail", True):
        return out
    # the half spacing must still be allowed at the cut, and hold ρmin there
    M = stem["M"]
    lb = rc.development_length(phi, mat)
    fits = M <= Mr_half + 1e-9
    # the lowest height above which the half bars always suffice
    idx = len(y) - 1
    while idx > 0 and fits[idx - 1]:
        idx -= 1
    if idx == 0 and fits[0]:
        y_theory = y[0]
    else:
        y_theory = y[idx]
    t_cut = g.thickness(y_theory) * 1000.0
    ext = max(t_cut - cover - phi / 2.0, 12.0 * phi) / 1000.0
    y_cut = _round_up(max(y_theory + ext, g.t_f + lb / 1000.0))
    if y_cut >= g.H - MIN_CUT_FROM_TOP:
        return out
    t_at = g.thickness(y_cut) * 1000.0
    if 2 * s > rc.max_spacing(t_at, main=True) + 1e-9:
        return out
    if As / 2.0 < wall.concrete["rho_min"] * 1000.0 * t_at - 1e-6:
        return out
    Mr = np.where(y >= y_cut, Mr_half, Mr_full)
    out.update(enabled=True, y_theory=float(y_theory), y_cut=float(y_cut), Mr=Mr,
               extension=ext, lb=lb / 1000.0)
    return out


# --------------------------------------------------------------------------- #
#  The whole design
# --------------------------------------------------------------------------- #

def design(wall, res: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    g = wall.geo
    con = wall.concrete
    mat = rc.Material(con["grade"], con["steel"])
    cs, cf = float(con["cover_stem"]), float(con["cover_footing"])
    rho_min = float(con["rho_min"])
    bar_stem, bar_foot = int(con.get("bar_stem") or 0), int(con.get("bar_footing") or 0)

    # ---------------------------------------------------------------- stem
    stem = stem_forces(wall)
    y = stem["y"]
    h_stem = g.t_bot * 1000.0
    Md = float(stem["M"][0])
    sec_stem = _section("stem", Md, 0.0, h_stem, cs, mat, rho_min, bar_stem,
                        combo=stem["governing"])
    y_v = g.t_f + sec_stem["d"] / 1000.0
    Vd = float(np.interp(y_v, y, stem["V"]))
    sec_stem = _section("stem", Md, Vd, h_stem, cs, mat, rho_min, bar_stem,
                        combo=stem["governing"], shear_d=y_v)
    cut = _curtailment(wall, stem, sec_stem, mat, cs)
    if con.get("curtail", True) and not cut["enabled"]:
        # half the bars can only stop if the other half is still close enough
        # together: try the bars at half the widest spacing, and keep them if
        # the curtailment then works
        dense = _section("stem", Md, Vd, h_stem, cs, mat, rho_min, bar_stem,
                         combo=stem["governing"], shear_d=y_v,
                         s_max=rc.max_spacing(g.t_top * 1000.0, main=True) / 2.0)
        dense_cut = _curtailment(wall, stem, dense, mat, cs)
        if dense_cut["enabled"]:
            sec_stem, cut = dense, dense_cut
    # the capacity must hold everywhere up the stem, the curtailment included
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = np.where(stem["M"] > 1e-6, cut["Mr"] / stem["M"], np.inf)
    worst = int(np.argmin(ratios))
    sec_stem["along"] = _check(float(ratios[worst]), 1.0, demand=float(stem["M"][worst]),
                               capacity=float(cut["Mr"][worst]))
    sec_stem["along"]["y"] = float(y[worst])

    t_avg = 0.5 * (g.t_top + g.t_bot) * 1000.0
    front = _distribution("stem_front", con["rho_front"] * 1000.0 * h_stem, h_stem)
    horiz_total = max(con["rho_dist"] * 1000.0 * t_avg, sec_stem["As_prov"] / 5.0)
    horizontal = _distribution("stem_horizontal", horiz_total / 2.0, t_avg)

    # ---------------------------------------------------------------- footing
    foot = footing_forces(wall)
    h_f = g.t_f * 1000.0
    top_M, bot_M = 0.0, 0.0
    top_c, bot_c = "", ""
    for name, c in foot["combos"].items():
        if c["M_heel"] > top_M:
            top_M, top_c = c["M_heel"], name
        if -c["M_toe"] > top_M:
            top_M, top_c = -c["M_toe"], name
        if c["M_toe"] > bot_M:
            bot_M, bot_c = c["M_toe"], name
        if -c["M_heel"] > bot_M:
            bot_M, bot_c = -c["M_heel"], name
    bottom = _section("toe", bot_M, 0.0, h_f, cf, mat, rho_min, bar_foot, combo=bot_c)
    topsec = _section("heel", top_M, 0.0, h_f, cf, mat, rho_min, bar_foot, top=h_f > 300,
                      combo=top_c)
    # shears: the toe at d from the face of the stem, the heel at the face
    V_toe = V_heel = 0.0
    x_toe_cut = g.toe - bottom["d"] / 1000.0
    for c in foot["combos"].values():
        if g.toe > 0:
            V_toe = max(V_toe, abs(_shear_toe(foot["x_toe"], c["toe_net"], x_toe_cut)))
        if g.heel > 0:
            V_heel = max(V_heel, abs(_shear_heel(foot["x_heel"], c["heel_net"], c["heel_end"],
                                                 g.x_back_base)))
    bottom = _section("toe", bot_M, V_toe, h_f, cf, mat, rho_min, bar_foot, combo=bot_c,
                      shear_d=x_toe_cut)
    topsec = _section("heel", top_M, V_heel, h_f, cf, mat, rho_min, bar_foot, top=h_f > 300,
                      combo=top_c, shear_d=g.x_back_base)
    long_total = max(con["rho_dist"] * 1000.0 * h_f,
                     max(bottom["As_prov"], topsec["As_prov"]) / 5.0)
    longitudinal = _distribution("footing_long", long_total / 2.0, h_f)

    # ---------------------------------------------------------------- key
    key_sec = None
    if g.key_on:
        pas = wall.passive()
        yk, pk = pas["profile_y"], pas["profile_p"]
        mask = yk <= 0.0
        yk, pk = yk[mask], pk[mask]
        integ = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
        f_h = COMBINATIONS["C1"]["H"]
        Vk = f_h * float(integ(pk, yk)) if len(yk) > 1 else 0.0
        Mk = f_h * float(integ(pk * (0.0 - yk), yk)) if len(yk) > 1 else 0.0
        key_sec = _section("key", Mk, Vk, g.key_width * 1000.0, cf, mat, rho_min, 0,
                           combo="C1")

    sections = {"stem": sec_stem, "toe": bottom, "heel": topsec}
    if key_sec:
        sections["key"] = key_sec
    out = {"material": mat.as_dict(), "stem_forces": stem, "footing_forces": foot,
           "unstable": foot["unstable"],
           "sections": sections, "curtailment": cut,
           "distribution": {"stem_front": front, "stem_horizontal": horizontal,
                            "footing_long": longitudinal},
           "combinations": [c["name"] for c in _combinations(wall)]}
    out["bars"] = layout(wall, out)
    out["schedule"] = schedule(out["bars"])
    out["quantities"] = quantities(wall, out["schedule"])
    out["anchorage"] = anchorage(wall, out, mat)
    return out


def all_ok(des: Dict[str, Any]) -> bool:
    for sec in des["sections"].values():
        for key in ("flexure", "shear", "ratio"):
            if sec[key]["status"] == "NOT OK":
                return False
    if des["sections"]["stem"]["along"]["status"] == "NOT OK":
        return False
    return all(d["ok"] for d in des["distribution"].values())


# --------------------------------------------------------------------------- #
#  Bars
# --------------------------------------------------------------------------- #

def _polyline_length(points) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def _hook(phi_mm: float) -> float:
    return _round_up(max(12.0 * phi_mm / 1000.0, MIN_HOOK))


def layout(wall, des: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every bar position of the section, with its shape in wall coordinates [m]."""
    g = wall.geo
    con = wall.concrete
    cs, cf = float(con["cover_stem"]) / 1000.0, float(con["cover_footing"]) / 1000.0
    S = des["sections"]
    D = des["distribution"]
    cut = des["curtailment"]
    bars: List[Dict[str, Any]] = []

    pb, pt = S["toe"]["phi"] / 1000.0, S["heel"]["phi"] / 1000.0
    pl = D["footing_long"]["phi"] / 1000.0
    y_bot = cf + pb / 2.0                      # the bottom transverse layer
    y_top = g.t_f - cf - pt / 2.0              # the top transverse layer
    x0, x1 = cf, wall.B - cf

    # ---------------------------------------------------------------- stem back
    ps = S["stem"]["phi"] / 1000.0
    foot_y = cf + pb + pl + ps / 2.0           # the foot rests on the bottom mesh

    def back_x(yy):
        return g.x_back(yy) - cs - ps / 2.0

    hook = _hook(S["stem"]["phi"])
    top_y = g.H - cs - ps / 2.0
    xb = back_x(g.t_f)
    x_hook = min(xb + hook, wall.B - cf - pt)
    full = [(x_hook, foot_y), (xb, foot_y), (back_x(g.t_f), g.t_f), (back_x(top_y), top_y)]
    # the corner at the top of the footing is only a kink when the back is inclined
    full = [full[0], full[1], full[3]] if g.taper == "front" else full
    s_main = S["stem"]["s"] / 1000.0
    if cut["enabled"]:
        yc = cut["y_cut"]
        part = [(x_hook, foot_y), (xb, foot_y), (back_x(g.t_f), g.t_f), (back_x(yc), yc)]
        part = [part[0], part[1], part[3]] if g.taper == "front" else part
        bars.append(_bar(1, "stem_back_full", "stem", S["stem"]["phi"], 2 * s_main, full))
        bars.append(_bar(2, "stem_back_cut", "stem", S["stem"]["phi"], 2 * s_main, part))
    else:
        bars.append(_bar(1, "stem_back_full", "stem", S["stem"]["phi"], s_main, full))

    # ---------------------------------------------------------------- stem front
    pf = D["stem_front"]["phi"] / 1000.0

    def front_x(yy):
        return g.x_front(yy) + cs + pf / 2.0

    hook_f = _hook(D["stem_front"]["phi"])
    ftop = g.H - cs - pf / 2.0
    xf = front_x(g.t_f)
    shape = [(max(xf - hook_f, cf + pb), foot_y), (xf, foot_y), (front_x(g.t_f), g.t_f),
             (front_x(ftop), ftop)]
    shape = [shape[0], shape[1], shape[3]] if g.taper == "back" else shape
    bars.append(_bar(len(bars) + 1, "stem_front", "stem", D["stem_front"]["phi"],
                     D["stem_front"]["s"] / 1000.0, shape))

    # ---------------------------------------------------------------- stem horizontal
    ph = D["stem_horizontal"]["phi"] / 1000.0
    sh = D["stem_horizontal"]["s"] / 1000.0
    ys = np.arange(g.t_f + 0.05, g.H - cs, sh)
    dots = ([(g.x_back(v) - cs - ps - ph / 2.0, float(v)) for v in ys]
            + [(g.x_front(v) + cs + pf + ph / 2.0, float(v)) for v in ys])
    bars.append(_bar(len(bars) + 1, "stem_horizontal", "distribution",
                     D["stem_horizontal"]["phi"], sh, [], dots=dots))

    # ---------------------------------------------------------------- footing
    leg_b = min(_hook(S["toe"]["phi"]), g.t_f - 2 * cf - pt)
    leg_t = min(_hook(S["heel"]["phi"]), g.t_f - 2 * cf - pb)
    shape = [(x0 + pb / 2, y_bot + leg_b), (x0 + pb / 2, y_bot), (x1 - pb / 2, y_bot),
             (x1 - pb / 2, y_bot + leg_b)]
    bars.append(_bar(len(bars) + 1, "footing_bottom", "footing", S["toe"]["phi"],
                     S["toe"]["s"] / 1000.0, shape))
    shape = [(x0 + pt / 2, y_top - leg_t), (x0 + pt / 2, y_top), (x1 - pt / 2, y_top),
             (x1 - pt / 2, y_top - leg_t)]
    bars.append(_bar(len(bars) + 1, "footing_top", "footing", S["heel"]["phi"],
                     S["heel"]["s"] / 1000.0, shape))
    sl = D["footing_long"]["s"] / 1000.0
    xs = np.arange(x0 + pb + pl / 2.0, x1 - pb, sl)
    dots = ([(float(v), y_bot + pb / 2 + pl / 2) for v in xs]
            + [(float(v), y_top - pt / 2 - pl / 2) for v in xs])
    bars.append(_bar(len(bars) + 1, "footing_long", "distribution", D["footing_long"]["phi"],
                     sl, [], dots=dots))

    # ---------------------------------------------------------------- key
    if "key" in S:
        pk = S["key"]["phi"] / 1000.0
        xa = g.key_x + cf + pk / 2.0
        xb2 = g.key_x + g.key_width - cf - pk / 2.0
        yb = -g.key_depth + cf + pk / 2.0
        ytop = y_top - pt / 2.0 - pl - pk / 2.0
        shape = [(xa, ytop), (xa, yb), (xb2, yb), (xb2, ytop)]
        bars.append(_bar(len(bars) + 1, "key", "key", S["key"]["phi"],
                         S["key"]["s"] / 1000.0, shape))
        dots = [(xa + pk, yb + pk), (xb2 - pk, yb + pk), (xa + pk, -0.05), (xb2 - pk, -0.05)]
        bars.append(_bar(len(bars) + 1, "key_long", "distribution", 12, 0.0, [],
                         dots=dots))
    return bars


def _bar(pos: int, name: str, family: str, phi: float, spacing: float, shape,
         dots=None) -> Dict[str, Any]:
    length = _polyline_length(shape) if shape else 1.0
    return {"pos": pos, "name": name, "family": family, "phi": int(phi), "s": spacing,
            "shape": [tuple(map(float, p)) for p in shape], "dots": dots or [],
            "length": length, "longitudinal": not shape}


def schedule(bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The bar bending schedule, per metre of wall."""
    rows = []
    for b in bars:
        if b["longitudinal"]:
            n = len(b["dots"])
            total = n * 1.0
        else:
            n = 1.0 / b["s"]
            total = n * b["length"]
        mass = rc.bar_mass(b["phi"])
        segments = [math.hypot(q[0] - p[0], q[1] - p[1])
                    for p, q in zip(b["shape"], b["shape"][1:])]
        rows.append({"pos": b["pos"], "name": b["name"], "family": b["family"],
                     "phi": b["phi"], "s": b["s"], "length": b["length"], "n": n,
                     "total_length": total, "unit_mass": mass, "mass": total * mass,
                     "segments": segments, "longitudinal": b["longitudinal"]})
    return rows


def quantities(wall, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    volume = wall.geo.concrete_area()
    steel = sum(r["mass"] for r in rows)
    by_phi: Dict[int, float] = {}
    for r in rows:
        by_phi[r["phi"]] = by_phi.get(r["phi"], 0.0) + r["mass"]
    return {"concrete": volume, "steel": steel,
            "ratio": steel / volume if volume > 0 else math.nan,
            "by_phi": dict(sorted(by_phi.items()))}


def anchorage(wall, des: Dict[str, Any], mat: rc.Material) -> List[Dict[str, Any]]:
    """Development lengths against the straight length each bar has."""
    g = wall.geo
    con = wall.concrete
    cf = float(con["cover_footing"]) / 1000.0
    S = des["sections"]
    rows = []

    def row(name, phi, top, available):
        lb = rc.development_length(phi, mat, top=top) / 1000.0
        rows.append({"name": name, "phi": phi, "lb": lb, "available": available,
                     "straight": available >= lb - 1e-9})

    row("stem_back_full", S["stem"]["phi"], False, g.t_f - 2 * cf)
    row("footing_bottom", S["toe"]["phi"], False, g.toe - cf)
    row("footing_top", S["heel"]["phi"], g.t_f > 0.3, g.heel - cf)
    if "key" in S:
        row("key", S["key"]["phi"], False, g.t_f - 2 * cf)
    return rows
