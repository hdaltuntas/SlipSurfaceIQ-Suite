"""
The analysis of a cantilever reinforced concrete retaining wall.

Given the wall (its stem, footing and key), the backfill slope, the
surcharges, the soils and the water, `RetainingWall.run()` works out

    * the earth pressure on the virtual back — the vertical plane through the
      end of the heel — by the chosen method, and by every other one for
      comparison: Rankine, Coulomb, at rest and the trial wedge
    * the forces on the wall and the soil it carries, and its stability:
      sliding on the base (with the passive resistance and a shear key),
      overturning about the toe, the eccentricity of the resultant and the
      pressure under the base
    * the bearing capacity of the foundation under the effective width, by
      the chosen factor set and by every other one for comparison, and the
      allowable pressure if one is given
    * with an earthquake (TBDY 2018), the same checks under kh and kv, the
      dynamic thrust and the inertia of the wall and of the soil on the heel,
      with kv acting up and down
    * the overall stability of the wall and the ground by slip circles
      (`slipsurface.wall.globalstab`)
    * the reinforced concrete design of the stem, the toe, the heel and the
      key, and the bars (`slipsurface.wall.design`)
    * the heel length that the stability checks need

Stability is checked with factors of safety on unfactored loads, as the
Turkish practice and TBDY 2018 §16 do; the members are designed for the
factored combinations of TS 500 and of TBDY 2018. Every check returns the
same record — value, required value, status — so the rest of the program need
not know which one produced it.

Input problems are raised as `WallError`, which carries a translation key, so
the interface can say what is wrong in the user's language.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from . import capacity as cap
from . import earth, tbdy
from .config import (
    BEARING_METHODS,
    DEFAULT_CONFIG,
    GRADES,
    PASSIVE_METHODS,
    PRESSURE_METHODS,
    SEISMIC_METHODS,
    SITE_CLASSES,
    STEELS,
)
from .geometry import Outline, clip_above, clip_below, polygon_area_centroid

#: A strip is analysed as a very long rectangle where a length is needed
STRIP_LENGTH = 1.0e6

#: Points along the virtual back and the stem where the pressures are integrated
N_PROFILE = 241

#: Load factors of the combinations. G: the weights, Q: the live loads (the
#: surcharge's thrust included), H: the earth pressure, W: the water, E: the
#: earthquake. `live_vertical` says whether the live surcharge on the heel is
#: counted as a weight.
SERVICE = {"G": 1.0, "Q": 1.0, "H": 1.0, "W": 1.0, "E": 0.0}

#: TS 500 (6.2.6) and TBDY 2018 (4.4.4) combinations for the members
COMBINATIONS = {
    "C1": {"G": 1.4, "Q": 1.6, "H": 1.6, "W": 1.4, "E": 0.0, "live_vertical": True,
           "seismic": False},                         # 1.4G + 1.6Q + 1.6H
    "C2": {"G": 0.9, "Q": 1.6, "H": 1.6, "W": 1.4, "E": 0.0, "live_vertical": False,
           "seismic": False},                         # 0.9G + 1.6H
    "C3": {"G": 1.0, "Q": 1.0, "H": 1.0, "W": 1.0, "E": 1.0, "live_vertical": True,
           "seismic": True},                          # G + Q + H + E
    "C4": {"G": 0.9, "Q": 0.0, "H": 1.0, "W": 1.0, "E": 1.0, "live_vertical": False,
           "seismic": True},                          # 0.9G + H + E
}

#: The search range of the required heel length, as multiples of H
HEEL_RANGE = (0.0, 3.0)


class WallError(ValueError):
    """An input the analysis cannot work with; `key` names the message."""

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        from .i18n import t
        super().__init__(t("en", key, **params))


def _message(key: str, **params) -> Tuple[str, Dict[str, Any]]:
    return key, params


def _tan(deg: float) -> float:
    return math.tan(math.radians(deg))


def _check(value: float, required: float, *, demand: float = float("nan"),
           capacity: float = float("nan"), kind: str = "ratio",
           extra: bool = True) -> Dict[str, Any]:
    """One check. `kind` is ``ratio`` (value ≥ required) or ``limit`` (value ≤ required);
    `extra` is a further condition that must also hold."""
    if kind == "limit":
        ok = math.isfinite(value) and value <= required + 1e-12
    else:
        ok = (math.isfinite(value) and value >= required - 1e-9) or value == math.inf
    return {"value": value, "required": required, "demand": demand, "capacity": capacity,
            "kind": kind, "status": "OK" if (ok and extra) else "NOT OK"}


def _na() -> Dict[str, Any]:
    return {"value": float("nan"), "required": float("nan"), "demand": float("nan"),
            "capacity": float("nan"), "kind": "ratio", "status": "N/A"}


def _integrate(p: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Resultant of a pressure p(y) and the height it acts at."""
    force = float(np.trapezoid(p, y)) if hasattr(np, "trapezoid") else float(np.trapz(p, y))
    if abs(force) < 1e-12:
        return 0.0, float(y[0])
    moment = (float(np.trapezoid(p * y, y)) if hasattr(np, "trapezoid")
              else float(np.trapz(p * y, y)))
    return force, moment / force


def _increment_profile(dP: float, y0: float, y1: float, share: float,
                       y: np.ndarray) -> np.ndarray:
    """A linear pressure over [y0, y1] with the resultant dP at y0 + share·(y1 − y0).

    share = 1/3 gives a triangle, 1/2 a rectangle, 2/3 an inverted triangle.
    """
    h = y1 - y0
    if h <= 0 or dP == 0:
        return np.zeros_like(y)
    share = min(max(share, 1.0 / 3.0), 2.0 / 3.0)
    top = dP / h * (6.0 * share - 2.0)
    bottom = dP / h * (4.0 - 6.0 * share)
    s = np.clip((y - y0) / h, 0.0, 1.0)
    return bottom + (top - bottom) * s


class RetainingWall:
    """One wall, set up from a configuration dictionary and analysed by `run()`."""

    def __init__(self, config: Optional[dict] = None):
        self.config = copy.deepcopy(config if config is not None else DEFAULT_CONFIG)
        self.results: Dict[str, Any] = {}
        self._read()

    # ------------------------------------------------------------------ inputs
    def _read(self) -> None:
        c = self.config
        g, loads, soils = c["geometry"], c["loads"], c["soils"]
        self.H = float(g["H"])
        self.t_top = float(g["t_top"])
        self.t_bot = float(g["t_bot"])
        self.taper = g.get("taper", "back")
        self.toe = float(g["toe"])
        self.heel = float(g["heel"])
        self.t_f = float(g["t_f"])
        self.D = float(g["D"])
        self.beta = float(g["backslope"])
        self.toe_slope = float(g["toe_slope"])
        self.key_cfg = dict(c.get("key", DEFAULT_CONFIG["key"]))
        self.geo = Outline(self.H, self.t_top, self.t_bot, self.taper, self.toe, self.heel,
                           self.t_f, self.D, self.beta, self.key_cfg)
        self.B = self.geo.B

        self.q_dead = float(loads["q_dead"])
        self.q_live = float(loads["q_live"])
        self.P_top = float(loads["P_top"])
        self.H_top = float(loads["H_top"])

        self.bf = dict(soils["backfill"])
        self.fd = dict(soils["foundation"])
        self.hw = float(soils["water_back"])
        self.hf = float(soils["water_front"])
        self.dw = float(soils["water_depth"])
        self.gw = float(soils["gamma_water"])
        self.gc = float(soils["gamma_concrete"])

        e = c["earth"]
        self.method = e["method"] if e["method"] in PRESSURE_METHODS else "rankine"
        self.delta_ratio = float(e["delta_ratio"])
        self.OCR = float(e["OCR"])
        self.passive_on = bool(e["passive"])
        self.passive_method = (e["passive_method"] if e["passive_method"] in PASSIVE_METHODS
                               else "rankine")
        self.passive_ratio = float(e["passive_ratio"])

        o = c["options"]
        self.bearing_method = (o["bearing_method"] if o["bearing_method"] in BEARING_METHODS
                               else "vesic")
        self.use_embedment = bool(o["bearing_embedment"])
        self.use_inclination = bool(o["bearing_inclination"])
        self.use_depth = bool(o["bearing_depth"])
        self.base_friction = float(o["base_friction"])
        self.base_adhesion = float(o["base_adhesion"])
        self.q_allow = float(o["q_allow"])
        self.global_on = bool(o["global_enabled"])
        self.crit = dict(c["criteria"])

        s = c["seismic"]
        self.seismic_on = bool(s["enabled"])
        self.Ss, self.S1 = float(s["Ss"]), float(s["S1"])
        self.site = s["site"]
        self.mobility = s["mobility"]
        self.kh_manual = float(s["kh_manual"])
        self.kv_ratio = float(s["kv_ratio"])
        self.seismic_method = (s["method"] if s["method"] in SEISMIC_METHODS
                               else "mononobe_okabe")
        self.dyn_height = float(s["dyn_height"])
        self.psi_live = float(s["psi_live"])
        self.concrete = dict(c["concrete"])

    def _validate(self) -> None:
        if self.H <= 0:
            raise WallError("err_height")
        if self.t_top <= 0 or self.t_bot < self.t_top:
            raise WallError("err_stem")
        if self.t_f <= 0 or self.H - self.t_f < 0.3:
            raise WallError("err_footing")
        if self.toe < 0 or self.heel < 0:
            raise WallError("err_toe_heel")
        if self.D < 0 or self.t_f + self.D >= self.H:
            raise WallError("err_cover")
        if self.beta < 0 or self.beta >= self.bf["phi"]:
            raise WallError("err_backslope", phi=self.bf["phi"])
        if not 0 <= self.toe_slope < 45:
            raise WallError("err_toe_slope")
        for name, soil in (("backfill", self.bf), ("foundation", self.fd)):
            if soil["gamma"] <= 0:
                raise WallError("err_gamma", soil=f"soil_{name}")
            if not 0 <= soil["phi"] < 60:
                raise WallError("err_phi", soil=f"soil_{name}")
            if soil["c"] < 0:
                raise WallError("err_cohesion", soil=f"soil_{name}")
            if soil["gamma_sat"] <= self.gw:
                raise WallError("err_gamma_sat", soil=f"soil_{name}")
        if self.bf["phi"] <= 0:
            raise WallError("err_backfill_phi")
        if self.fd["phi"] <= 0 and self.fd["c"] <= 0:
            raise WallError("err_foundation_strength")
        if self.gc <= 0:
            raise WallError("err_gamma_concrete")
        if not 0 <= self.hw <= self.H or not 0 <= self.hf <= self.H or self.dw < 0:
            raise WallError("err_water")
        if self.geo.key_on:
            k = self.geo
            if (k.key_depth <= 0 or k.key_width <= 0 or k.key_x < 0
                    or k.key_x + k.key_width > self.B + 1e-9):
                raise WallError("err_key")
        if not 0 <= self.delta_ratio <= 1 or not 0 <= self.passive_ratio <= 1:
            raise WallError("err_ratios")
        if not 0 < self.base_friction <= 1 or not 0 <= self.base_adhesion <= 1:
            raise WallError("err_base_ratios")
        if self.OCR < 1:
            raise WallError("err_ocr")
        if min(self.q_dead, self.q_live, self.P_top, self.H_top, self.q_allow) < 0:
            raise WallError("err_loads")
        if self.seismic_on:
            if self.Ss < 0 or self.S1 < 0 or self.site not in SITE_CLASSES:
                raise WallError("err_seismic")
            if not 0 <= self.kv_ratio <= 1 or not 1 / 3 - 1e-9 <= self.dyn_height <= 2 / 3 + 1e-9:
                raise WallError("err_seismic")
            if not 0 <= self.psi_live <= 1 or self.kh_manual < 0 or self.kh_manual >= 1:
                raise WallError("err_seismic")
        con = self.concrete
        if con["grade"] not in GRADES or con["steel"] not in STEELS:
            raise WallError("err_material")
        cs, cf = float(con["cover_stem"]) / 1000.0, float(con["cover_footing"]) / 1000.0
        if cs <= 0 or cf <= 0 or 2 * cs + 0.02 >= self.t_top or 2 * cf + 0.02 >= self.t_f:
            raise WallError("err_cover_concrete")

    # ------------------------------------------------------------------ earth pressure
    @property
    def delta(self) -> float:
        """The wall friction of Coulomb and the trial wedge, δ = ratio·φ."""
        return self.delta_ratio * self.bf["phi"]

    def coefficient(self, method: Optional[str] = None,
                    h: Optional[float] = None) -> Dict[str, float]:
        """K and the inclination ω of the thrust from the horizontal, for one method."""
        method = method or self.method
        phi, beta = self.bf["phi"], self.beta
        if method == "rankine":
            return {"K": earth.rankine_ka(phi, beta), "omega": beta}
        if method == "coulomb":
            return {"K": earth.coulomb_ka(phi, 90.0, self.delta, beta), "omega": self.delta}
        if method == "at_rest":
            return {"K": earth.k0(phi, self.OCR, beta), "omega": beta}
        wedge = earth.trial_wedge(phi, self.delta, beta, h or self.geo.h_virtual,
                                  self.bf["gamma"])
        return {"K": wedge["K"], "omega": self.delta, "alpha": wedge["alpha"]}

    def _sigma_v(self, y: np.ndarray, top: float) -> np.ndarray:
        """Effective vertical stress in the backfill at heights y under ground at `top`."""
        g, gsat = self.bf["gamma"], self.bf["gamma_sat"]
        hw = min(self.hw, top)
        above = g * (top - y)
        below = g * (top - hw) + (gsat - self.gw) * (hw - y)
        return np.where(y >= hw, above, below)

    def _water(self, y: np.ndarray) -> np.ndarray:
        return self.gw * np.clip(self.hw - y, 0.0, None)

    def lateral_profile(self, y0: float, top: float, q_live: float,
                        coef: Dict[str, float]) -> Dict[str, Any]:
        """Pressures on a vertical plane from y0 up to the ground at `top`.

        The pressure of the soil (and of the surcharges) acts at ω from the
        horizontal; the water horizontally. Rankine's pressure takes the
        cohesion of the backfill (a tension crack is not counted on), the
        other methods leave it out.
        """
        y = np.linspace(y0, top, N_PROFILE)
        K = coef["K"]
        sv = self._sigma_v(y, top)
        c = self.bf["c"] if self.method == "rankine" else 0.0
        rc = 2.0 * c * math.sqrt(K)

        def active(extra):
            return np.maximum(K * (sv + extra) - rc, 0.0)

        soil = active(0.0)
        dead = active(self.q_dead) - soil
        live = active(self.q_dead + q_live) - active(self.q_dead)
        return {"y": y, "soil": soil, "dead": dead, "live": live, "water": self._water(y),
                "K": K, "omega": coef["omega"]}

    def _stress_integral(self, y0: float, top: float) -> float:
        """∫σ'v over the plane: the thrust of a coefficient of one."""
        y = np.linspace(y0, top, N_PROFILE)
        return _integrate(self._sigma_v(y, top), y)[0]

    # ------------------------------------------------------------------ passive
    def passive(self, quake: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """The passive resistance of the soil in front, down to the base or the key."""
        g = self.geo
        top = g.front_ground
        bottom = -g.key_depth if g.key_on else 0.0
        phi, c = self.fd["phi"], self.fd["c"]
        if quake:
            try:
                Kp = earth.mononobe_okabe_kp(phi, quake["kh"], quake["kv"], 0.0,
                                             -self.toe_slope)
            except ValueError:
                Kp = 1.0
        elif self.passive_method == "coulomb":
            Kp = earth.coulomb_kp(phi, 90.0, min(self.delta_ratio, 0.5) * phi,
                                  -self.toe_slope)
        else:
            Kp = earth.rankine_kp(phi, 0.0)
        y = np.linspace(bottom, top, N_PROFILE)
        gm, gsat = self.fd["gamma"], self.fd["gamma_sat"]
        hf = min(self.hf, top)
        sv = np.where(y >= hf, gm * (top - y), gm * (top - hf) + (gsat - self.gw) * (hf - y))
        p = Kp * sv + 2.0 * c * math.sqrt(Kp)
        force, arm = _integrate(p, y)
        return {"Kp": Kp, "P": force, "y": arm, "depth": top - bottom, "profile_y": y,
                "profile_p": p}

    # ------------------------------------------------------------------ seismic
    def spectrum(self) -> Dict[str, float]:
        return tbdy.spectrum(self.Ss, self.S1, self.site)

    def seismic_coefficients(self) -> Dict[str, float]:
        spec = self.spectrum()
        return tbdy.coefficients(spec["SDS"], self.mobility, self.kv_ratio, self.kh_manual)

    def dynamic_increment(self, y0: float, top: float, q_eff: float, kh: float, kv: float,
                          static: Dict[str, float]) -> Dict[str, float]:
        """The dynamic increment of the thrust on a plane from y0 to `top`.

        `kv` is positive upward. Returns the increment ΔP, its inclination and
        the total seismic coefficient; the static part is the one the chosen
        method gives, so ΔP = P_E − P_static, never below zero.
        """
        S = self._stress_integral(y0, top)          # ∫σ'v dy
        h = top - y0
        load = S + q_eff * h
        if self.seismic_method == "wood":
            dP = kh * 2.0 * S + kh * q_eff * h      # kh·γ·h², and kh·q·h
            return {"dP": dP, "omega": 0.0, "KAE": float("nan"), "limited": False}
        if self.seismic_method == "seed_whitman":
            dK = earth.seed_whitman(kh)
            return {"dP": dK * load, "omega": 0.0, "KAE": static["K"] + dK, "limited": False}
        delta = self.delta if self.method in ("coulomb", "trial_wedge") else self.beta
        mo = earth.mononobe_okabe(self.bf["phi"], kh, kv, delta, self.beta)
        total = (1.0 - kv) * mo["KAE"] * load
        dP = max(total - static["K"] * load, 0.0)
        return {"dP": dP, "omega": delta, "KAE": mo["KAE"], "limited": mo["limited"],
                "psi": mo["psi"]}

    # ------------------------------------------------------------------ forces
    def _soil_weight(self, poly, gamma: float, gamma_sat: float,
                     level: float) -> Tuple[float, float, float]:
        """Weight and centroid of a soil polygon, saturated below `level`."""
        if not poly:
            return 0.0, 0.0, 0.0
        below = clip_below(poly, level) if level > 0 else []
        above = clip_above(poly, level) if level > 0 else poly
        a1, x1, y1 = polygon_area_centroid(above) if above else (0.0, 0.0, 0.0)
        a2, x2, y2 = polygon_area_centroid(below) if below else (0.0, 0.0, 0.0)
        w1, w2 = gamma * a1, gamma_sat * a2
        W = w1 + w2
        if W <= 0:
            return 0.0, 0.0, 0.0
        return W, (w1 * x1 + w2 * x2) / W, (w1 * y1 + w2 * y2) / W

    def weights(self) -> List[Tuple[str, float, float, float]]:
        """The permanent weights: (name, W, x, y) of the concrete and the soils."""
        out = []
        for name, poly in self.geo.concrete_parts().items():
            a, x, y = polygon_area_centroid(poly)
            out.append((f"W_{name}", self.gc * a, x, y))
        W, x, y = self._soil_weight(self.geo.heel_soil(), self.bf["gamma"],
                                    self.bf["gamma_sat"], self.hw)
        if W > 0:
            out.append(("W_heel_soil", W, x, y))
        W, x, y = self._soil_weight(self.geo.toe_soil(), self.fd["gamma"],
                                    self.fd["gamma_sat"], self.hf)
        if W > 0:
            out.append(("W_toe_soil", W, x, y))
        return out

    def forces(self, f: Dict[str, float], live_vertical: bool = True,
               quake: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Every force on the wall and the soil it carries, per metre.

        `f` holds the load factors, `live_vertical` whether the live surcharge
        on the heel counts as a weight, `quake` the seismic coefficients (kv
        positive upward). Vertical forces are positive downwards, horizontal
        ones positive towards the front; each carries its arm from the toe.
        """
        g = self.geo
        B, hv = self.B, g.h_virtual
        vertical: List[Tuple[str, float, float, str]] = []
        horizontal: List[Tuple[str, float, float, str]] = []
        live_scale = self.psi_live if quake else 1.0

        weights = self.weights()
        for name, W, x, _ in weights:
            vertical.append((name, f["G"] * W, x, "G"))
        Lq = max(B - g.x_back_top, 0.0)
        xq = 0.5 * (g.x_back_top + B)
        if self.q_dead > 0 and Lq > 0:
            vertical.append(("Q_dead", f["G"] * self.q_dead * Lq, xq, "G"))
        if live_vertical and self.q_live > 0 and Lq > 0 and f["Q"] > 0:
            vertical.append(("Q_live", f["Q"] * live_scale * self.q_live * Lq, xq, "Q"))
        x_top = 0.5 * (g.x_front_top + g.x_back_top)
        if self.P_top > 0:
            vertical.append(("P_top", f["G"] * self.P_top, x_top, "G"))
        if self.H_top > 0 and f["Q"] > 0:
            horizontal.append(("H_top", f["Q"] * live_scale * self.H_top, self.H, "Q"))

        coef = self.coefficient()
        prof = self.lateral_profile(0.0, hv, self.q_live * live_scale, coef)
        cw, sw = math.cos(math.radians(coef["omega"])), math.sin(math.radians(coef["omega"]))
        y = prof["y"]
        for name, key, cat in (("Pa", "soil", "H"), ("Pq_dead", "dead", "H"),
                               ("Pq_live", "live", "Q")):
            P, arm = _integrate(prof[key], y)
            if P <= 0 or f[cat] <= 0:
                continue
            horizontal.append((f"{name}_h", f[cat] * P * cw, arm, cat))
            if sw > 1e-12:
                vertical.append((f"{name}_v", f[cat] * P * sw, B, cat))
        Pw, arm = _integrate(prof["water"], y)
        if Pw > 0:
            horizontal.append(("Pw_back", f["W"] * Pw, arm, "W"))
        if self.hf > 0:
            horizontal.append(("Pw_front", -f["W"] * 0.5 * self.gw * self.hf ** 2,
                               self.hf / 3.0, "W"))
        if self.hw > 0 or self.hf > 0:
            ub, uf = self.gw * self.hw, self.gw * self.hf
            U = 0.5 * (ub + uf) * B
            xu = B * (uf + 2.0 * ub) / (3.0 * (uf + ub))
            vertical.append(("U", -f["W"] * U, xu, "W"))

        dynamic: Dict[str, Any] = {}
        if quake and f["E"] > 0:
            kh, kv = quake["kh"], quake["kv"]
            mass = [(n, W, x, yy) for n, W, x, yy in weights if n != "W_toe_soil"]
            if self.q_dead > 0 and Lq > 0:
                mass.append(("Q_dead", self.q_dead * Lq, xq, hv))
            if self.P_top > 0:
                mass.append(("P_top", self.P_top, x_top, self.H))
            Wm = sum(m[1] for m in mass)
            xm = sum(m[1] * m[2] for m in mass) / Wm
            ym = sum(m[1] * m[3] for m in mass) / Wm
            horizontal.append(("E_inertia", f["E"] * kh * Wm, ym, "E"))
            if kv != 0:
                vertical.append(("E_vertical", -f["E"] * kv * Wm, xm, "E"))
            q_eff = self.q_dead + live_scale * self.q_live
            inc = self.dynamic_increment(0.0, hv, q_eff, kh, kv, coef)
            yd = self.dyn_height * hv
            ow = math.radians(inc["omega"])
            horizontal.append(("dPAE_h", f["E"] * inc["dP"] * math.cos(ow), yd, "E"))
            if math.sin(ow) > 1e-12:
                vertical.append(("dPAE_v", f["E"] * inc["dP"] * math.sin(ow), B, "E"))
            dynamic = {"kh": kh, "kv": kv, "W_inertia": Wm, "y_inertia": ym,
                       "dP": inc["dP"], "KAE": inc["KAE"], "omega": inc["omega"],
                       "limited": inc["limited"], "y_dP": yd, "psi": inc.get("psi", 0.0)}

        sum_v = sum(v for _, v, _, _ in vertical)
        sum_h = sum(hf for _, hf, _, _ in horizontal)
        m_r = (sum(v * x for _, v, x, _ in vertical if v > 0)
               + sum(-hf * yy for _, hf, yy, _ in horizontal if hf < 0))
        m_o = (sum(-v * x for _, v, x, _ in vertical if v < 0)
               + sum(hf * yy for _, hf, yy, _ in horizontal if hf > 0))
        x_res = (m_r - m_o) / sum_v if sum_v > 0 else 0.0
        e = B / 2.0 - x_res
        return {"vertical": vertical, "horizontal": horizontal, "V": sum_v, "H": sum_h,
                "M_R": m_r, "M_O": m_o, "x_r": x_res, "e": e, "B": B, "h": hv,
                "K": coef["K"], "omega": coef["omega"], "profile": prof,
                "dynamic": dynamic}

    # ------------------------------------------------------------------ base pressure
    @staticmethod
    def base_pressure(V: float, e: float, B: float) -> Dict[str, float]:
        """Contact pressure under a rigid base: a trapezoid, or a triangle once e > B/6.

        e > 0 puts the resultant towards the toe. Returns the pressure at the
        toe and at the heel and the length in contact.
        """
        if V <= 0:
            return {"q_toe": 0.0, "q_heel": 0.0, "contact": 0.0, "q_max": 0.0, "q_min": 0.0}
        if abs(e) <= B / 6.0 + 1e-12:
            q1 = V / B * (1.0 + 6.0 * e / B)
            q2 = V / B * (1.0 - 6.0 * e / B)
            contact = B
        else:
            contact = max(3.0 * (B / 2.0 - abs(e)), 0.0)
            peak = 2.0 * V / contact if contact > 0 else math.inf
            q1, q2 = (peak, 0.0) if e > 0 else (0.0, peak)
        return {"q_toe": q1, "q_heel": q2, "contact": contact, "q_max": max(q1, q2),
                "q_min": min(q1, q2)}

    @staticmethod
    def pressure_at(x, bp: Dict[str, float], B: float):
        """The contact pressure at x (from the toe), for a base pressure record."""
        x = np.asarray(x, dtype=float)
        if bp["contact"] >= B - 1e-9:
            return bp["q_toe"] + (bp["q_heel"] - bp["q_toe"]) * x / B
        c = bp["contact"]
        if bp["q_toe"] >= bp["q_heel"]:
            return np.where(x <= c, bp["q_toe"] * (1.0 - x / max(c, 1e-12)), 0.0)
        return np.where(x >= B - c, bp["q_heel"] * (1.0 - (B - x) / max(c, 1e-12)), 0.0)

    # ------------------------------------------------------------------ stability
    def _sliding_resistance(self, V: float, passive: Optional[Dict[str, float]]) -> Dict[str, Any]:
        phi, c = self.fd["phi"], self.fd["c"]
        friction = max(V, 0.0) * _tan(self.base_friction * phi)
        adhesion = self.base_adhesion * c * self.B
        pp = self.passive_ratio * passive["P"] if passive else 0.0
        return {"friction": friction, "adhesion": adhesion, "passive": pp,
                "R": friction + adhesion + pp}

    def _stability(self, quake: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Sliding, overturning, eccentricity and the forces of the bearing check."""
        seismic = quake is not None
        crit = self.crit
        f = dict(SERVICE, E=1.0 if seismic else 0.0)
        slide = self.forces(f, live_vertical=False, quake=quake)
        bear = self.forces(f, live_vertical=True, quake=quake)
        use_passive = self.passive_on or self.geo.key_on
        passive = self.passive(quake) if use_passive else None
        res = self._sliding_resistance(slide["V"], passive)
        Hd = slide["H"]
        value = res["R"] / Hd if Hd > 0 else math.inf
        sliding = _check(value, crit["FS_sliding_seis" if seismic else "FS_sliding"],
                         demand=Hd, capacity=res["R"])
        fs_ot = slide["M_R"] / slide["M_O"] if slide["M_O"] > 0 else math.inf
        overturning = _check(fs_ot, crit["FS_overturning_seis" if seismic else "FS_overturning"],
                             demand=slide["M_O"], capacity=slide["M_R"])
        limit = self.B / crit["ecc_seismic" if seismic else "ecc_static"]
        ecc = max(abs(slide["e"]), abs(bear["e"]))
        eccentricity = _check(ecc, limit, kind="limit")
        return {"forces": slide, "bearing_forces": bear, "resistance": res, "passive": passive,
                "sliding": sliding, "overturning": overturning, "eccentricity": eccentricity}

    # ------------------------------------------------------------------ bearing
    def _gamma_below(self, width: float) -> float:
        """Unit weight under the base for the Nγ term, the water table allowed for."""
        g, gsat = self.fd["gamma"], self.fd["gamma_sat"]
        buoyant = gsat - self.gw
        if self.hw > 0 or self.hf > 0:
            return buoyant
        dw = max(self.dw, 0.0)
        if dw >= width:
            return g
        return buoyant + (dw / max(width, 1e-9)) * (g - buoyant)

    def overburden(self) -> float:
        """Effective vertical stress beside the base, from the ground in front."""
        top = self.geo.front_ground
        g, gsat = self.fd["gamma"], self.fd["gamma_sat"]
        hf = min(self.hf, top)
        return g * (top - hf) + (gsat - self.gw) * hf

    def bearing_capacity(self, method: str, B: float, V: float, H: float) -> Dict[str, Any]:
        """q_ult of the foundation under an effective width B'."""
        q = self.overburden() if self.use_embedment else 0.0
        return cap.ultimate(method, c=self.fd["c"], phi=self.fd["phi"],
                            gamma=self._gamma_below(B), q=q, B=B, L=STRIP_LENGTH,
                            Df=self.geo.front_ground, shape="strip", V=V, Hb=abs(H), Hl=0.0,
                            area=B * 1.0, eta=0.0, beta=self.toe_slope, use_shape=False,
                            use_depth=self.use_depth, use_inclination=self.use_inclination,
                            use_base=False, use_ground=self.toe_slope > 0,
                            use_compressibility=False)

    def _bearing(self, forces: Dict[str, Any], seismic: bool = False) -> Dict[str, Any]:
        crit = self.crit
        B, V, Hf, e = self.B, forces["V"], forces["H"], forces["e"]
        Beff = B - 2.0 * abs(e)
        bp = self.base_pressure(V, e, B)
        out = {"e": e, "B_eff": Beff, "V": V, "H": Hf, "methods": {},
               "primary": self.bearing_method, "pressure": bp}
        required = crit["FS_bearing_seis" if seismic else "FS_bearing"]
        if Beff <= 0 or V <= 0:
            out.update(sigma_v=math.inf, q_ult=0.0, check=_check(0.0, required),
                       allowable=_na())
            return out
        sigma = V / Beff
        for method in BEARING_METHODS:
            try:
                out["methods"][method] = self.bearing_capacity(method, Beff, V, Hf)
            except (ValueError, ZeroDivisionError):
                continue
        q_ult = out["methods"][self.bearing_method]["q_ult"]
        out.update(sigma_v=sigma, q_ult=q_ult, q_allow=q_ult / required,
                   check=_check(q_ult / sigma, required, demand=sigma,
                                capacity=q_ult / required))
        if self.q_allow > 0 and not seismic:
            out["allowable"] = _check(self.q_allow / bp["q_max"] if bp["q_max"] > 0 else math.inf,
                                      1.0, demand=bp["q_max"], capacity=self.q_allow)
        else:
            out["allowable"] = _na()
        return out

    # ------------------------------------------------------------------ comparison
    def method_table(self) -> Dict[str, Any]:
        """Every earth pressure method on the virtual back, side by side."""
        hv = self.geo.h_virtual
        rows = {}
        for method in PRESSURE_METHODS:
            try:
                coef = self.coefficient(method)
            except ValueError:
                continue
            S = self._stress_integral(0.0, hv)
            load = S + (self.q_dead + self.q_live) * hv
            P = coef["K"] * load
            ow = math.radians(coef["omega"])
            rows[method] = {"K": coef["K"], "omega": coef["omega"], "P": P,
                            "Ph": P * math.cos(ow), "Pv": P * math.sin(ow),
                            "Kh": coef["K"] * math.cos(ow), "alpha": coef.get("alpha")}
        phi = self.fd["phi"]
        passive = {"rankine": earth.rankine_kp(phi, 0.0)}
        try:
            passive["coulomb"] = earth.coulomb_kp(phi, 90.0, min(self.delta_ratio, 0.5) * phi,
                                                  -self.toe_slope)
        except ValueError:
            pass
        return {"active": rows, "passive": passive, "primary": self.method}

    # ------------------------------------------------------------------ the whole
    def run(self, with_heel: bool = True, with_global: bool = True,
            with_design: bool = True) -> Dict[str, Any]:
        self._validate()
        warnings: List[Tuple[str, Dict[str, Any]]] = []
        try:
            stat = self._stability()
        except ValueError as exc:
            if isinstance(exc, WallError):
                raise
            raise WallError("err_pressure") from exc
        bearing = self._bearing(stat["bearing_forces"])

        res: Dict[str, Any] = {
            "B": self.B, "h": self.geo.h_virtual, "Hs": self.geo.Hs,
            "K": stat["forces"]["K"], "omega": stat["forces"]["omega"], "method": self.method,
            "forces": stat["forces"], "bearing_forces": stat["bearing_forces"],
            "resistance": stat["resistance"], "passive": stat["passive"],
            "stability": {"sliding": stat["sliding"], "overturning": stat["overturning"],
                          "eccentricity": stat["eccentricity"], "bearing": bearing["check"],
                          "allowable": bearing["allowable"]},
            "bearing": bearing,
            "methods": self.method_table(),
            "seismic": None,
            "global": None,
            "design": None,
            "warnings": warnings,
        }

        if self.seismic_on:
            spec = self.spectrum()
            co = self.seismic_coefficients()
            cases = {}
            for sign, name in ((1.0, "up"), (-1.0, "down")):
                quake = {"kh": co["kh"], "kv": sign * co["kv"]}
                st = self._stability(quake)
                cases[name] = {"stability": st, "bearing": self._bearing(st["bearing_forces"],
                                                                         seismic=True)}
            checks = {}
            for key in ("sliding", "overturning", "eccentricity"):
                pair = [cases[n]["stability"][key] for n in ("up", "down")]
                checks[key] = self._worse(pair)
            checks["bearing"] = self._worse([cases[n]["bearing"]["check"] for n in ("up", "down")])
            checks["allowable"] = _na()
            governing = min(("up", "down"),
                            key=lambda n: cases[n]["stability"]["sliding"]["value"])
            dyn = cases[governing]["stability"]["forces"]["dynamic"]
            res["seismic"] = {"spectrum": spec, "coefficients": co, "cases": cases,
                              "stability": checks, "governing": governing,
                              "dynamic": dyn,
                              "forces": cases[governing]["stability"]["forces"],
                              "bearing": cases[governing]["bearing"]}
            if any(cases[n]["stability"]["forces"]["dynamic"].get("limited") for n in cases):
                warnings.append(_message("warn_mo_limited"))
            if self.hw > 0 or self.hf > 0:
                warnings.append(_message("warn_water_seismic"))

        if with_global and self.global_on:
            from . import globalstab
            res["global"] = globalstab.analyse(self, res)
            if res["global"] is None or not res["global"].get("found"):
                warnings.append(_message("warn_global_none"))

        if with_design:
            from . import design
            res["design"] = design.design(self, res)
            if not design.all_ok(res["design"]):
                warnings.append(_message("warn_design"))
            if res["design"]["unstable"]:
                warnings.append(_message("warn_footing_unstable",
                                         combos=", ".join(res["design"]["unstable"])))

        # ---------------------------------------------------------- warnings
        if self.bf["c"] > 0 and self.method != "rankine":
            warnings.append(_message("warn_cohesion_ignored"))
        if self.bf["c"] > 0 and self.method == "rankine":
            warnings.append(_message("warn_cohesion_backfill"))
        if (self.passive_on or self.geo.key_on) and self.toe_slope > 0 \
                and self.passive_method == "rankine":
            warnings.append(_message("warn_passive_slope"))
        if self.geo.key_on and not self.passive_on:
            warnings.append(_message("warn_key_passive"))
        if abs(stat["bearing_forces"]["e"]) > self.B / 6.0 + 1e-9:
            warnings.append(_message("warn_uplift_base"))
        if self.dw < self.B and self.hw <= 0 and self.hf <= 0:
            warnings.append(_message("warn_water", dw=self.dw))
        if self.fd["phi"] <= 0:
            warnings.append(_message("warn_undrained"))
        if self.t_top < 0.20:
            warnings.append(_message("warn_thin_stem"))
        if self.B < 0.4 * self.H:
            warnings.append(_message("warn_narrow_base", ratio=self.B / self.H))
        if self.beta > 0 and self.q_live > 0:
            warnings.append(_message("warn_live_on_slope"))
        if self.method == "at_rest" and self.seismic_on and \
                self.seismic_method == "mononobe_okabe":
            warnings.append(_message("warn_at_rest_mo"))

        res["required_heel"] = self.required_heel() if with_heel else float("nan")
        self.results = res
        return res

    @staticmethod
    def _worse(checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """The worse of two records of the same check."""
        def margin(c):
            if c["status"] == "N/A":
                return math.inf
            if c["kind"] == "limit":
                return c["required"] / c["value"] if c["value"] > 0 else math.inf
            return c["value"] / c["required"] if c["required"] else c["value"]
        return min(checks, key=margin)

    # ------------------------------------------------------------------ design heel
    def passes(self) -> bool:
        """Do the stability and bearing checks hold, static and seismic?"""
        res = self.run(with_heel=False, with_global=False, with_design=False)
        checks = list(res["stability"].values())
        if res["seismic"]:
            checks += list(res["seismic"]["stability"].values())
        return all(c["status"] != "NOT OK" for c in checks)

    def with_heel(self, heel: float) -> "RetainingWall":
        cfg = copy.deepcopy(self.config)
        cfg["geometry"]["heel"] = float(heel)
        return RetainingWall(cfg)

    def required_heel(self) -> float:
        """The shortest heel that satisfies the stability and bearing checks,
        by bisection; infinite when even 3·H is not enough."""
        lo, hi = HEEL_RANGE[0] * self.H, HEEL_RANGE[1] * self.H

        def ok(heel: float) -> bool:
            try:
                return self.with_heel(heel).passes()
            except WallError:
                return False

        if not ok(hi):
            return math.inf
        if ok(lo):
            return lo
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if ok(mid):
                hi = mid
            else:
                lo = mid
            if hi - lo < 0.005:
                break
        return hi


# --------------------------------------------------------------------------- #
#  Preliminary dimensions
# --------------------------------------------------------------------------- #

def proportions(H: float, backslope: float = 0.0) -> Dict[str, float]:
    """The textbook first guess at a cantilever wall's dimensions.

    Stem 0.25–0.30 m at the top and about H/10 at the base, a footing about
    H/10 thick, a base about 0.5–0.7·H wide (more under a slope), of which a
    third is toe. Rounded to 5 cm; the checks decide.
    """
    H = float(H)
    if H <= 0:
        raise WallError("err_height")

    def r5(x):
        return max(round(x / 0.05) * 0.05, 0.05)

    t_top = 0.30 if H >= 4.0 else 0.25
    t_bot = r5(max(0.10 * H, t_top))
    t_f = r5(max(0.10 * H, 0.40))
    B = r5((0.60 + 0.005 * max(float(backslope), 0.0)) * H)
    toe = r5(B / 3.0)
    heel = r5(max(B - toe - t_bot, 0.30))
    return {"t_top": t_top, "t_bot": t_bot, "t_f": t_f, "toe": toe, "heel": heel,
            "D": r5(min(0.10 * H + 0.30, 1.0))}
