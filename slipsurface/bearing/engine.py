"""
The bearing capacity analysis of a shallow foundation on a layered profile.

Given the foundation (shape, size, depth, tilt), the actions on it, the
groundwater level and the soil layers, `BearingAnalysis.run()` works out

    * the in-situ stresses σv0, u0 and σ'v0, and the surcharge at the base
    * the eccentricity of the resultant, Meyerhof's effective area and the
      contact pressure under the full base
    * the depth of the failure zone and the design strength averaged over it,
      or the two-layer punching / load-spread checks where the profile is a
      strong layer over a weak one
    * the ultimate bearing capacity by every applicable method — Terzaghi,
      Meyerhof, Hansen, Vesić, EN 1997-1 and Skempton — drained, undrained or
      whichever governs, and by the in-situ and rock methods when their data
      are given
    * the bearing, sliding and eccentricity checks, against a global factor of
      safety or against an EN 1997-1 Design Approach
    * the width the foundation would need to satisfy them

Input problems are raised as `BearingError`, which carries a translation key,
so the interface can say what is wrong in the user's language.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..common import factors as F
from . import capacity as cap
from . import insitu, layered, rock, seismic
from .config import (
    ANALYSES,
    APPROACHES,
    BEHAVIOURS,
    DEFAULT_CONFIG,
    LAYER_MODELS,
    METHODS,
    PMT_CATEGORIES,
    ROCK_METHODS,
    SHAPES,
    SHEAR,
    TESTS,
    TWO_LAYER_MODELS,
    UNDRAINED_METHODS,
)

#: A strip is analysed as a very long rectangle where a length is needed
STRIP_LENGTH = 1.0e6

#: Iterations of the failure-zone depth, which depends on the strength it
#: averages, which depends on the depth
ZONE_ITERATIONS = 6

#: The search range of the required width [m]
WIDTH_RANGE = (0.30, 60.0)

#: Partial factors of EN 1997-1, Annex A (the recommended values)
PARTIAL = {
    "A1": {"G": 1.35, "Q": 1.50},
    "A2": {"G": 1.00, "Q": 1.30},
    "M1": {"phi": 1.00, "c": 1.00, "cu": 1.00, "gamma": 1.00},
    "M2": {"phi": 1.25, "c": 1.25, "cu": 1.40, "gamma": 1.00},
    "R1": {"Rv": 1.00, "Rh": 1.00},
    "R2": {"Rv": 1.40, "Rh": 1.10},
    "R3": {"Rv": 1.00, "Rh": 1.00},
}

#: The combinations each Design Approach asks for
COMBINATIONS = {
    "da1": [("DA1-1", "A1", "M1", "R1"), ("DA1-2", "A2", "M2", "R1")],
    "da2": [("DA2", "A1", "M1", "R2")],
    "da3": [("DA3", "A1", "M2", "R3")],
}


class BearingError(ValueError):
    """An input the analysis cannot work with; `key` names the message."""

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        from .i18n import TRANSLATIONS
        super().__init__(TRANSLATIONS["en"].get(key, key).format(**params))


def _message(key: str, **params) -> Tuple[str, Dict[str, Any]]:
    return key, params


def _num(d: dict, key: str, default: float) -> float:
    value = d.get(key, default)
    if value is None or value == "":
        return float(default)
    return float(value)


# --------------------------------------------------------------------------- #
#  Soil profile
# --------------------------------------------------------------------------- #

class Profile:
    """The layered soil column, its in-situ stresses and its averages."""

    def __init__(self, layers: List[dict], water_depth: float, gamma_w: float):
        self.layers = layers
        self.zw = water_depth
        self.gw = gamma_w
        top = 0.0
        for layer in layers:
            layer["top"] = top
            layer["bottom"] = top + layer["thickness"]
            top = layer["bottom"]
        self.depth = top

    # ------------------------------------------------------------------ stresses
    def layer_at(self, z: float) -> dict:
        """The layer containing depth z; the last one continues below the profile."""
        for layer in self.layers:
            if z < layer["bottom"] - 1e-12:
                return layer
        return self.layers[-1]

    def total_stress(self, z: float) -> float:
        """σv0 at depth z; the last layer is taken as continuing below the profile."""
        z = max(float(z), 0.0)
        sigma = 0.0
        for i, layer in enumerate(self.layers):
            top = layer["top"]
            bottom = layer["bottom"] if i < len(self.layers) - 1 else float("inf")
            if z <= top:
                break
            seg = min(z, bottom)
            dry = max(min(seg, self.zw) - top, 0.0)
            wet = max(seg - max(top, self.zw), 0.0)
            sigma += layer["gamma"] * dry + layer["gamma_sat"] * wet
        return sigma

    def pore_pressure(self, z: float) -> float:
        return self.gw * max(float(z) - self.zw, 0.0)

    def effective_stress(self, z: float) -> float:
        return self.total_stress(z) - self.pore_pressure(z)

    def unit_weight(self, z: float, effective: bool = True) -> float:
        """The unit weight at depth z: buoyant below the water table if asked."""
        layer = self.layer_at(z)
        if z >= self.zw:
            return layer["gamma_sat"] - (self.gw if effective else 0.0)
        return layer["gamma"]

    # ------------------------------------------------------------------ averages
    def segments(self, z1: float, z2: float) -> List[Tuple[dict, float, float]]:
        """The (layer, top, bottom) pieces the depth range z1…z2 is made of."""
        out = []
        for i, layer in enumerate(self.layers):
            top = layer["top"]
            bottom = layer["bottom"] if i < len(self.layers) - 1 else max(z2, layer["bottom"])
            lo, hi = max(z1, top), min(z2, bottom)
            if hi - lo > 1e-9:
                out.append((layer, lo, hi))
        return out

    def average(self, z1: float, z2: float, effective: bool = True) -> Dict[str, float]:
        """The strength and unit weight of the range, weighted by thickness.

        The friction angle is averaged through its tangent, which is what the
        capacity equation uses; everything else is averaged directly. The
        undrained strength is averaged over the cohesive layers only: a sand
        is drained whatever the rate of loading, and its zero cu would
        otherwise drag down the short-term strength of the clay beside it.
        """
        pieces = self.segments(z1, z2)
        if not pieces:
            layer = self.layer_at(z1)
            pieces = [(layer, z1, z1 + 1.0)]
        total = sum(hi - lo for _, lo, hi in pieces)
        out = {"c": 0.0, "cu": 0.0, "tan_phi": 0.0, "gamma": 0.0, "E": 0.0, "nu": 0.0}
        cohesive = sum(hi - lo for layer, lo, hi in pieces if layer["behaviour"] == "cohesive")
        for layer, lo, hi in pieces:
            w = (hi - lo) / total
            out["c"] += w * layer["c"]
            if layer["behaviour"] == "cohesive" and cohesive > 0:
                out["cu"] += (hi - lo) / cohesive * layer["cu"]
            out["tan_phi"] += w * math.tan(math.radians(layer["phi"]))
            out["E"] += w * layer["E"]
            out["nu"] += w * layer["nu"]
            mid = 0.5 * (lo + hi)
            out["gamma"] += w * self.unit_weight(mid, effective)
        out["phi"] = math.degrees(math.atan(out["tan_phi"]))
        out["thickness"] = total
        out["layers"] = [layer["name"] for layer, _, _ in pieces]
        return out


# --------------------------------------------------------------------------- #
#  The analysis
# --------------------------------------------------------------------------- #

class BearingAnalysis:
    """Bearing capacity of one shallow foundation. Build it, then call `run()`."""

    def __init__(self, config: Dict[str, Any]):
        self.config = copy.deepcopy(config)
        self.warnings: List[Tuple[str, Dict[str, Any]]] = []
        self._read()
        self.results: Dict[str, Any] = {}

    # ------------------------------------------------------------------ input
    def _read(self) -> None:
        cfg = self.config
        base = DEFAULT_CONFIG
        f = {**base["foundation"], **cfg.get("foundation", {})}
        load = {**base["loading"], **cfg.get("loading", {})}
        w = {**base["groundwater"], **cfg.get("groundwater", {})}
        o = {**base["options"], **cfg.get("options", {})}
        s = {**base["seismic"], **cfg.get("seismic", {})}
        t = {**base["insitu"], **cfg.get("insitu", {})}
        r = {**base["rock"], **cfg.get("rock", {})}
        c = {**base["criteria"], **cfg.get("criteria", {})}

        self.shape = f["shape"] if f["shape"] in SHAPES else "rectangle"
        self.B = _num(f, "B", 1.0)
        if self.shape in ("square", "circle"):
            self.L = self.B
        elif self.shape == "strip":
            self.L = STRIP_LENGTH
        else:
            self.L = _num(f, "L", self.B)
        self.Df = _num(f, "Df", 0.0)
        self.eta = _num(f, "base_tilt", 0.0)
        self.beta = _num(f, "ground_slope", 0.0)
        if self.B <= 0 or self.L <= 0:
            raise BearingError("err_dimensions")
        if self.Df < 0:
            raise BearingError("err_depth")
        if self.shape == "rectangle" and self.L < self.B:
            self.B, self.L = self.L, self.B
            self.warnings.append(_message("warn_swapped"))
        if self.eta < 0 or self.beta < 0 or self.eta + self.beta >= 90.0:
            raise BearingError("err_tilt")

        self.V = _num(load, "V", 0.0)
        self.Hb = abs(_num(load, "Hb", 0.0))
        self.Hl = abs(_num(load, "Hl", 0.0))
        self.Mb = abs(_num(load, "Mb", 0.0))
        self.Ml = abs(_num(load, "Ml", 0.0))
        self.variable_fraction = min(max(_num(load, "variable_fraction", 0.0), 0.0), 1.0)
        if self.V <= 0:
            raise BearingError("err_load")

        self.method = o["method"] if o["method"] in METHODS else "vesic"
        self.analysis = o["analysis"] if o["analysis"] in ANALYSES else "both"
        self.shear = o["shear"] if o["shear"] in SHEAR else "general"
        self.use_shape = bool(o.get("shape_factors", True))
        self.use_depth = bool(o.get("depth_factors", True))
        self.use_inclination = bool(o.get("inclination_factors", True))
        self.use_base = bool(o.get("base_factors", True))
        self.use_ground = bool(o.get("ground_factors", True))
        self.use_compressibility = bool(o.get("compressibility", False))
        self.use_effective_area = bool(o.get("effective_area", True))
        self.layer_model = o["layer_model"] if o["layer_model"] in LAYER_MODELS else "average"
        self.two_layer_model = (o["two_layer_model"] if o["two_layer_model"] in TWO_LAYER_MODELS
                                else "punching")
        self.zone_factor = max(_num(o, "zone_factor", 1.0), 0.05)
        self.Ks = max(_num(o, "Ks", 0.0), 0.0)
        self.adhesion_ratio = min(max(_num(o, "adhesion_ratio", 1.0), 0.0), 1.0)
        self.spread_angle = min(max(_num(o, "spread_angle", 26.57), 0.0), 60.0)
        self.delta_ratio = min(max(_num(o, "delta_ratio", 1.0), 0.0), 1.0)

        self.seismic_on = bool(s.get("enabled", False))
        self.kh = max(_num(s, "kh", 0.0), 0.0)
        self.kv = _num(s, "kv", 0.0)
        self.soil_inertia = bool(s.get("soil_inertia", True))

        self.insitu_on = bool(t.get("enabled", False))
        self.test = t["test"] if t.get("test") in TESTS else "spt"
        self.N60 = _num(t, "N60", 0.0)
        self.qc = _num(t, "qc", 0.0)
        self.pl = _num(t, "pl", 0.0)
        self.p0 = _num(t, "p0", 0.0)
        self.category = t["category"] if t.get("category") in PMT_CATEGORIES else "sand_a"
        self.test_settlement = max(_num(t, "settlement", 25.0), 1.0)

        self.rock_on = bool(r.get("enabled", False))
        self.rock_method = r["method"] if r.get("method") in ROCK_METHODS else "hoek_brown"
        self.sigma_ci = _num(r, "sigma_ci", 0.0)
        self.GSI = _num(r, "GSI", 50.0)
        self.mi = _num(r, "mi", 10.0)
        self.rock_D = _num(r, "D", 0.0)
        self.gamma_rock = _num(r, "gamma_rock", 25.0)
        self.spacing = _num(r, "spacing", 0.6)
        self.aperture = _num(r, "aperture", 1.0)

        self.approach = c["approach"] if c["approach"] in APPROACHES else "fs"
        self.FS = max(_num(c, "FS", 3.0), 1.0)
        self.FS_sliding = max(_num(c, "FS_sliding", 1.5), 1.0)
        self.ecc_limit = max(_num(c, "ecc_limit", 6.0), 2.0)

        gamma_w = _num(w, "gamma_water", 9.81)
        layers = []
        for raw in cfg.get("soil_profile") or []:
            layer = {**DEFAULT_CONFIG["soil_profile"][0], **raw}
            thickness = _num(layer, "thickness", 0.0)
            if thickness <= 0:
                continue
            name = str(layer.get("name") or "Layer").strip() or "Layer"
            behaviour = (layer.get("behaviour") if layer.get("behaviour") in BEHAVIOURS
                         else "granular")
            gamma = _num(layer, "gamma", 18.0)
            gamma_sat = _num(layer, "gamma_sat", gamma)
            if gamma <= 0 or gamma_sat <= gamma_w:
                raise BearingError("err_gamma", name=name)
            phi = _num(layer, "phi", 0.0)
            if phi < 0 or phi >= 60.0:
                raise BearingError("err_phi", name=name)
            nu = _num(layer, "nu", 0.3)
            if not 0.0 <= nu < 0.5 + 1e-9:
                raise BearingError("err_nu", name=name)
            layers.append({
                "name": name, "thickness": thickness, "behaviour": behaviour,
                "gamma": gamma, "gamma_sat": gamma_sat,
                "c": max(_num(layer, "c", 0.0), 0.0), "phi": phi,
                "cu": max(_num(layer, "cu", 0.0), 0.0),
                "E": max(_num(layer, "E", 0.0), 0.0), "nu": nu,
            })
        if not layers:
            raise BearingError("err_no_layers")
        self.profile = Profile(layers, max(_num(w, "depth", 0.0), 0.0), gamma_w)
        if self.Df >= self.profile.depth:
            raise BearingError("err_base_below", depth=self.profile.depth)
        for layer in layers:
            if layer["c"] <= 0 and layer["phi"] <= 0 and layer["cu"] <= 0:
                raise BearingError("err_no_strength", name=layer["name"])

    # ------------------------------------------------------------------ helpers
    @property
    def is_strip(self) -> bool:
        return self.shape == "strip"

    def _actions(self) -> Dict[str, float]:
        """The actions at the base, with the earthquake's inertia if asked for."""
        if not self.seismic_on or (self.kh == 0 and self.kv == 0):
            return {"V": self.V, "Hb": self.Hb, "Hl": self.Hl, "Mb": self.Mb,
                    "Ml": self.Ml, "psi": 0.0}
        return seismic.apply_to_loads(self.V, self.Hb, self.Hl, self.Mb, self.Ml,
                                      self.kh, self.kv)

    def _zone_depth(self, B_eff: float, undrained: bool) -> Tuple[float, Dict[str, float]]:
        """The failure zone below the base, and the strength averaged over it.

        The zone depends on the friction angle it averages, so the two are
        settled by repeating the average a few times; the starting point is
        the layer the foundation sits on.
        """
        start = self.profile.layer_at(self.Df + 1e-6)
        phi = 0.0 if undrained else start["phi"]
        params = {}
        depth = 0.0
        for _ in range(ZONE_ITERATIONS):
            depth = self.zone_factor * cap.wedge_depth(B_eff, phi)
            params = self.profile.average(self.Df, self.Df + depth, effective=not undrained)
            new_phi = 0.0 if undrained else params["phi"]
            if abs(new_phi - phi) < 1e-6:
                phi = new_phi
                break
            phi = new_phi
        params = self.profile.average(self.Df, self.Df + depth, effective=not undrained)
        params["zone"] = depth
        return depth, params

    def _design_strength(self, params: dict, undrained: bool,
                         gamma_phi: float = 1.0, gamma_c: float = 1.0,
                         gamma_cu: float = 1.0) -> Tuple[float, float]:
        """(c, φ) of the analysis, reduced by the partial factors if any."""
        if undrained:
            return params["cu"] / gamma_cu, 0.0
        c, phi = params["c"], params["phi"]
        if self.shear == "local":
            c, phi = F.local_shear(c, phi)
        c = c / gamma_c
        phi = math.degrees(math.atan(math.tan(math.radians(phi)) / gamma_phi))
        return c, phi

    # ------------------------------------------------------------------ one method
    def _one(self, method: str, undrained: bool, geom: dict, actions: dict,
             params: dict, *, gamma_phi: float = 1.0, gamma_c: float = 1.0,
             gamma_cu: float = 1.0, V: Optional[float] = None,
             Hb: Optional[float] = None, Hl: Optional[float] = None) -> Optional[dict]:
        """One method, one analysis: the capacity and everything that made it."""
        c, phi = self._design_strength(params, undrained, gamma_phi, gamma_c, gamma_cu)
        if undrained and c <= 0:
            return None
        if not undrained and c <= 0 and phi <= 0:
            return None
        q = (self.profile.total_stress(self.Df) if undrained
             else self.profile.effective_stress(self.Df))
        gamma = params["gamma"]
        if self.seismic_on and self.kv:
            gamma *= (1.0 - self.kv)
            q *= (1.0 - self.kv)
        shear_modulus = 1000.0 * params["E"] / (2.0 * (1.0 + params["nu"]))   # MPa -> kPa
        q_mid = q + gamma * geom["B_eff"] / 2.0

        result = cap.ultimate(
            method, c=c, phi=phi, gamma=gamma, q=q,
            B=geom["B_eff"], L=geom["L_eff"], Df=self.Df, shape=self.shape,
            V=self.V if V is None else V,
            Hb=self.Hb if Hb is None else Hb, Hl=self.Hl if Hl is None else Hl,
            area=geom["A_eff"], eta=self.eta, beta=self.beta,
            G=shear_modulus, q_mid=q_mid,
            use_shape=self.use_shape,
            use_depth=self.use_depth and (F.HAS_DEPTH[method] or method == "ec7"),
            use_inclination=self.use_inclination and F.HAS_INCLINATION[method],
            use_base=self.use_base and F.HAS_BASE[method],
            use_ground=self.use_ground and (F.HAS_GROUND[method] or method == "ec7"),
            use_compressibility=self.use_compressibility,
        )
        result["analysis"] = "undrained" if undrained else "drained"
        result["seismic"] = {"applied": False}
        if self.seismic_on and self.soil_inertia and self.kh > 0:
            z = seismic.paolucci_pecker(self.kh, phi)
            terms = result["terms"]
            terms["c"] *= z["c"]
            terms["q"] *= z["q"]
            terms["g"] *= z["g"]
            result["q_ult"] = terms["c"] + terms["q"] + terms["g"]
            result["q_net_ult"] = result["q_ult"] - q
            result["seismic"] = {"applied": True, **z}
            if z["exceeded"]:
                self.warnings.append(_message("warn_seismic_limit", kh=self.kh,
                                              limit=z["limit"]))
        return result

    def _method_entry(self, method: str, geom: dict, actions: dict,
                      drained_params: dict, undrained_params: dict) -> Optional[dict]:
        """Both analyses of one method, and whichever of them governs."""
        runs: Dict[str, dict] = {}
        want_drained = self.analysis in ("both", "drained") and method not in UNDRAINED_METHODS
        want_undrained = self.analysis in ("both", "undrained")
        if want_drained:
            got = self._one(method, False, geom, actions, drained_params)
            if got:
                runs["drained"] = got
        if want_undrained:
            got = self._one(method, True, geom, actions, undrained_params)
            if got:
                runs["undrained"] = got
        if not runs:
            return None
        governing = min(runs, key=lambda key: runs[key]["q_net_ult"])
        entry = dict(runs[governing])
        entry["runs"] = runs
        entry["governing"] = governing
        entry["kind"] = "equation"
        entry["key"] = method
        return entry

    # ------------------------------------------------------------------ the run
    def run(self, with_width: bool = True) -> Dict[str, Any]:
        """The whole analysis. `with_width` off leaves the required width out,
        which is how the width search itself runs its trials."""
        actions = self._actions()
        geom = cap.effective_area(self.shape, self.B, self.L, actions["V"],
                                  actions["Mb"], actions["Ml"], self.use_effective_area)
        if geom["A_eff"] <= 0:
            raise BearingError("err_eccentricity")
        pressure = cap.contact_pressure(self.shape, self.B, self.L, actions["V"],
                                        actions["Mb"], actions["Ml"])
        if not pressure["in_kern"]:
            self.warnings.append(_message("warn_kern", e=pressure["e_B"],
                                          limit=self.B / 6.0))

        zone_d, drained_params = self._zone_depth(geom["B_eff"], False)
        zone_u, undrained_params = self._zone_depth(geom["B_eff"], True)
        if self.Df + max(zone_d, zone_u) > self.profile.depth + 1e-9:
            self.warnings.append(_message("warn_zone_below",
                                          depth=self.profile.depth))
        if self.shear == "local":
            self.warnings.append(_message("warn_local_shear"))

        methods: Dict[str, dict] = {}
        for method in METHODS:
            entry = self._method_entry(method, geom, actions, drained_params,
                                       undrained_params)
            if entry is not None:
                methods[method] = entry
        if not methods:
            raise BearingError("err_no_method")
        if self.method not in methods:
            self.warnings.append(_message("warn_method_unavailable",
                                          method=self.method))
            primary_key = next(iter(methods))
        else:
            primary_key = self.method
        primary = methods[primary_key]

        if self.use_inclination and (self.Hb or self.Hl) and not F.HAS_INCLINATION[primary_key]:
            self.warnings.append(_message("warn_no_inclination", method=primary_key))
        if self.use_depth and primary_key == "ec7" and self.Df > 0:
            self.warnings.append(_message("warn_ec7_depth"))

        others: Dict[str, dict] = {}
        two_layer = self._two_layer(geom, actions, drained_params, undrained_params,
                                    primary_key)
        if two_layer:
            others.update(two_layer)
        others.update(self._insitu(geom))
        others.update(self._rock(geom, actions))

        governing_key, governing = self._governing(primary_key, primary, others)
        applied = self._applied(actions, geom)
        checks = self._checks(governing, applied, geom, actions, drained_params,
                              undrained_params)
        ec7 = (self._eurocode(primary_key, geom, actions, drained_params, undrained_params)
               if self.approach != "fs" else None)

        self.results = {
            "shape": self.shape, "B": self.B, "L": self.L, "Df": self.Df,
            "geometry": geom, "pressure": pressure, "actions": actions,
            "applied": applied,
            "zone": {"drained": zone_d, "undrained": zone_u,
                     "depth": zone_u if governing.get("analysis") == "undrained" else zone_d},
            "params": {"drained": drained_params, "undrained": undrained_params},
            "surcharge": {"total": self.profile.total_stress(self.Df),
                          "effective": self.profile.effective_stress(self.Df),
                          "pore": self.profile.pore_pressure(self.Df)},
            "methods": methods, "others": others,
            "primary": primary_key, "governing": governing_key,
            "q_ult": governing["q_ult"], "q_net_ult": governing["q_net_ult"],
            "checks": checks, "eurocode": ec7,
            "required_width": self.required_width() if with_width else float("nan"),
            "layers": self._layer_table(),
            "warnings": self.warnings,
        }
        return self.results

    # ------------------------------------------------------------------ pieces
    def _applied(self, actions: dict, geom: dict) -> Dict[str, float]:
        """What the foundation actually carries."""
        area = geom["A_eff"]
        q = actions["V"] / area if area > 0 else float("inf")
        q0 = self.profile.effective_stress(self.Df)
        q0_total = self.profile.total_stress(self.Df)
        H = math.hypot(actions["Hb"], actions["Hl"])
        return {"q": q, "q_net": q - q0, "q_net_total": q - q0_total,
                "V": actions["V"], "H": H, "A": area,
                "inclination": math.degrees(math.atan2(H, actions["V"]))
                if actions["V"] > 0 else 90.0}

    def _two_layer(self, geom: dict, actions: dict, drained: dict, undrained: dict,
                   primary: str) -> Dict[str, dict]:
        """The punching or load-spread check of a strong layer over a weak one."""
        if self.layer_model != "two_layer":
            return {}
        top = self.profile.layer_at(self.Df + 1e-6)
        H = top["bottom"] - self.Df
        if H <= 1e-6 or top["bottom"] >= self.profile.depth - 1e-9:
            self.warnings.append(_message("warn_two_layer_single"))
            return {}
        lower = self.profile.layer_at(top["bottom"] + 1e-6)

        def capacity_of(layer: dict, depth: float, B: float, L: float, area: float,
                        undrained_run: bool) -> float:
            """One layer's capacity, as if the footing were founded on its top."""
            if undrained_run:
                c, phi = layer["cu"], 0.0
            else:
                c, phi = layer["c"], layer["phi"]
                if self.shear == "local":
                    c, phi = F.local_shear(c, phi)
            if (undrained_run and c <= 0) or (not undrained_run and c <= 0 and phi <= 0):
                return float("nan")
            q = (self.profile.total_stress(depth) if undrained_run
                 else self.profile.effective_stress(depth))
            gamma = self.profile.unit_weight(depth + 1e-6, effective=not undrained_run)
            out = cap.ultimate(primary, c=c, phi=phi, gamma=gamma, q=q, B=B, L=L,
                               Df=depth, shape=self.shape, V=actions["V"],
                               Hb=actions["Hb"], Hl=actions["Hl"], area=area,
                               eta=self.eta, beta=self.beta,
                               use_shape=self.use_shape,
                               use_depth=self.use_depth and F.HAS_DEPTH[primary],
                               use_inclination=self.use_inclination
                               and F.HAS_INCLINATION[primary],
                               use_base=self.use_base and F.HAS_BASE[primary],
                               use_ground=self.use_ground and F.HAS_GROUND[primary])
            return out["q_ult"]

        # Each layer is taken in the condition that governs it: a sand over a
        # soft clay is a drained sand over an undrained clay, and a clay with
        # only a cu has no drained capacity to speak of.
        wanted = {"both": (False, True), "drained": (False,),
                  "undrained": (True,)}[self.analysis]

        def weakest(layer: dict, depth: float, B: float, L: float, area: float):
            options = [(capacity_of(layer, depth, B, L, area, u), u) for u in wanted]
            options = [(q, u) for q, u in options if math.isfinite(q)]
            return min(options) if options else (float("nan"), False)

        q_top, top_undrained = weakest(top, self.Df, geom["B_eff"], geom["L_eff"],
                                       geom["A_eff"])
        q_bottom, use_undrained = weakest(lower, self.Df + H, geom["B_eff"],
                                          geom["L_eff"], geom["A_eff"])
        if not (math.isfinite(q_top) and math.isfinite(q_bottom)):
            self.warnings.append(_message("warn_two_layer_strength"))
            return {}

        q0 = (self.profile.total_stress(self.Df) if use_undrained
              else self.profile.effective_stress(self.Df))
        if self.two_layer_model == "punching":
            c1 = top["cu"] if top_undrained else top["c"]
            phi1 = 0.0 if top_undrained else top["phi"]
            out = layered.punching(
                q_bottom=q_bottom, q_top=q_top, B=geom["B_eff"], L=geom["L_eff"], H=H,
                Df=self.Df, gamma1=self.profile.unit_weight(self.Df + H / 2.0,
                                                            effective=not top_undrained),
                c1=c1, phi1=phi1, Ks=self.Ks, adhesion_ratio=self.adhesion_ratio,
                strip=self.is_strip)
            entry = {"kind": "two_layer", "key": "punching", "q_ult": out["q_ult"],
                     "q_net_ult": out["q_ult"] - q0,
                     "analysis": "undrained" if use_undrained else "drained",
                     "detail": out}
            return {"punching": entry}

        strip_L = geom["L_eff"] if not self.is_strip else 1.0
        spread_geom = layered.spread_dimensions(geom["B_eff"], strip_L, H,
                                                self.spread_angle, self.is_strip)
        q_spread_layer, _ = weakest(lower, self.Df + H, spread_geom["B"],
                                    max(spread_geom["L"], spread_geom["B"]),
                                    spread_geom["B"] * spread_geom["L"])
        out = layered.spread(V=actions["V"], q_bottom=q_spread_layer, B=geom["B_eff"],
                             L=strip_L, H=H, angle=self.spread_angle, strip=self.is_strip)
        out["q_ult"] = min(out["q_ult"], q_top)
        entry = {"kind": "two_layer", "key": "spread", "q_ult": out["q_ult"],
                 "q_net_ult": out["q_ult"] - q0,
                 "analysis": "undrained" if use_undrained else "drained", "detail": out}
        return {"spread": entry}

    def _insitu(self, geom: dict) -> Dict[str, dict]:
        """The bearing capacity the in-situ test gives, if one was entered."""
        if not self.insitu_on:
            return {}
        q0 = self.profile.effective_stress(self.Df)
        if self.test == "spt":
            if self.N60 <= 0:
                return {}
            out = insitu.spt_pressure(self.N60, self.B, self.Df, self.test_settlement)
            return {"spt": {"kind": "insitu", "key": "spt", "q_all": out["q_all"],
                            "q_net_all": out["q_all"], "q_ult": float("nan"),
                            "q_net_ult": float("nan"), "settlement_rule": True,
                            "phi": insitu.phi_from_spt(self.N60), "detail": out}}
        if self.test == "cpt":
            if self.qc <= 0:
                return {}
            out = insitu.cpt_pressure(self.qc, self.B, self.Df, self.test_settlement)
            return {"cpt": {"kind": "insitu", "key": "cpt", "q_all": out["q_all"],
                            "q_net_all": out["q_all"], "q_ult": float("nan"),
                            "q_net_ult": float("nan"), "settlement_rule": True,
                            "phi": insitu.phi_from_cpt(self.qc, max(q0, 1.0)),
                            "detail": out}}
        if self.pl <= 0:
            return {}
        out = insitu.pmt_capacity(self.pl, self.p0, self.category, self.B, self.L,
                                  self.Df, q0, self.is_strip)
        return {"pmt": {"kind": "insitu", "key": "pmt", "q_ult": out["q_ult"],
                        "q_net_ult": out["q_net_ult"],
                        "q_all": out["q_net_ult"] / self.FS + q0,
                        "settlement_rule": False, "detail": out}}

    def _rock(self, geom: dict, actions: dict) -> Dict[str, dict]:
        """The bearing capacity of a rock founding stratum, if one was entered."""
        if not self.rock_on or self.sigma_ci <= 0:
            return {}
        q0 = self.profile.effective_stress(self.Df)
        if self.rock_method == "ksp":
            out = rock.ksp_capacity(self.sigma_ci, self.spacing, self.aperture,
                                    self.B, self.Df)
            if not out["valid"]:
                self.warnings.append(_message("warn_ksp_range"))
            return {"ksp": {"kind": "rock", "key": "ksp", "q_ult": out["q_ult"],
                            "q_net_ult": out["q_ult"] - q0, "q_all": out["q_all"],
                            "detail": out}}
        mc = rock.equivalent_mohr_coulomb(self.sigma_ci, self.GSI, self.mi, self.rock_D)
        result = cap.ultimate(
            self.method if self.method != "skempton" else "vesic",
            c=mc["c"], phi=mc["phi"], gamma=self.gamma_rock, q=q0,
            B=geom["B_eff"], L=geom["L_eff"], Df=self.Df, shape=self.shape,
            V=actions["V"], Hb=actions["Hb"], Hl=actions["Hl"], area=geom["A_eff"],
            eta=self.eta, beta=self.beta, use_shape=self.use_shape,
            use_depth=self.use_depth, use_inclination=self.use_inclination,
            use_base=self.use_base, use_ground=self.use_ground)
        return {"hoek_brown": {"kind": "rock", "key": "hoek_brown",
                               "q_ult": result["q_ult"],
                               "q_net_ult": result["q_net_ult"],
                               "q_all": result["q_net_ult"] / self.FS + q0,
                               "detail": {**mc, "result": result}}}

    def _governing(self, primary_key: str, primary: dict,
                   others: Dict[str, dict]) -> Tuple[str, dict]:
        """The capacity the checks are made against.

        The chosen method governs unless a two-layer or rock check gives less:
        a footing cannot be stronger than the weakest mechanism it has.
        """
        key, entry = primary_key, primary
        for name, other in others.items():
            value = other.get("q_net_ult")
            if value is None or not math.isfinite(value):
                continue
            if other["kind"] in ("two_layer", "rock") and value < entry["q_net_ult"]:
                key, entry = name, other
        return key, entry

    def _checks(self, governing: dict, applied: dict, geom: dict, actions: dict,
                drained: dict, undrained: dict) -> Dict[str, dict]:
        """Bearing, sliding and eccentricity."""
        q_net_ult = governing["q_net_ult"]
        q_net_applied = applied["q_net"]
        undrained_run = governing.get("analysis") == "undrained"
        if undrained_run:
            q_net_applied = applied["q_net_total"]
        fs = (q_net_ult / q_net_applied if q_net_applied > 0 else float("inf"))
        q_all_net = q_net_ult / self.FS
        q0 = (self.profile.total_stress(self.Df) if undrained_run
              else self.profile.effective_stress(self.Df))

        params = undrained if undrained_run else drained
        c_base, phi_base = self._design_strength(params, undrained_run)
        slide = cap.sliding_resistance(actions["V"], geom["A_eff"], c_base, phi_base,
                                       self.delta_ratio, undrained_run,
                                       self.adhesion_ratio)
        H = math.hypot(actions["Hb"], actions["Hl"])
        fs_slide = slide["R"] / H if H > 0 else float("inf")

        e_max = max(geom["e_B"] / self.B, geom["e_L"] / self.L if self.L > 0 else 0.0)
        allowed = 1.0 / self.ecc_limit

        def status(value: float, required: float) -> str:
            if not math.isfinite(value):
                return "OK"
            return "OK" if value >= required - 1e-9 else "NOT OK"

        return {
            "bearing": {"actual": fs, "allowable": self.FS,
                        "status": status(fs, self.FS),
                        "q_net_ult": q_net_ult, "q_net_applied": q_net_applied,
                        "q_all_net": q_all_net, "q_all": q_all_net + q0,
                        "utilisation": (q_net_applied / q_all_net
                                        if q_all_net > 0 else float("inf"))},
            "sliding": {"actual": fs_slide, "allowable": self.FS_sliding,
                        "status": "N/A" if H <= 0 else status(fs_slide, self.FS_sliding),
                        "resistance": slide["R"], "H": H, **slide},
            "eccentricity": {"actual": e_max, "allowable": allowed,
                             "status": "OK" if e_max <= allowed + 1e-9 else "NOT OK",
                             "e_B": geom["e_B"], "e_L": geom["e_L"],
                             "limit": self.ecc_limit},
        }

    def _eurocode(self, primary_key: str, geom: dict, actions: dict, drained: dict,
                  undrained: dict) -> Dict[str, Any]:
        """The EN 1997-1 Design Approach the criteria ask for."""
        out: Dict[str, Any] = {"approach": self.approach, "combinations": []}
        q0_eff = self.profile.effective_stress(self.Df)
        q0_tot = self.profile.total_stress(self.Df)
        fraction = self.variable_fraction
        for name, a_set, m_set, r_set in COMBINATIONS[self.approach]:
            A, M, R = PARTIAL[a_set], PARTIAL[m_set], PARTIAL[r_set]
            factor = A["G"] * (1.0 - fraction) + A["Q"] * fraction
            Vd = actions["V"] * factor
            Hbd, Hld = actions["Hb"] * factor, actions["Hl"] * factor
            Mbd, Mld = actions["Mb"] * factor, actions["Ml"] * factor
            g = cap.effective_area(self.shape, self.B, self.L, Vd, Mbd, Mld,
                                   self.use_effective_area)
            if g["A_eff"] <= 0:
                continue
            runs = {}
            if self.analysis in ("both", "drained") and primary_key not in UNDRAINED_METHODS:
                got = self._one(primary_key, False, g, actions, drained,
                                gamma_phi=M["phi"], gamma_c=M["c"], V=Vd, Hb=Hbd, Hl=Hld)
                if got:
                    runs["drained"] = got
            if self.analysis in ("both", "undrained"):
                got = self._one(primary_key, True, g, actions, undrained,
                                gamma_cu=M["cu"], V=Vd, Hb=Hbd, Hl=Hld)
                if got:
                    runs["undrained"] = got
            if not runs:
                continue
            which = min(runs, key=lambda key: runs[key]["q_net_ult"])
            run = runs[which]
            q0 = q0_tot if which == "undrained" else q0_eff
            Rd = (run["q_net_ult"] / R["Rv"]) * g["A_eff"] + q0 * g["A_eff"]
            Ed = Vd
            params = undrained if which == "undrained" else drained
            c_d, phi_d = self._design_strength(params, which == "undrained",
                                               M["phi"], M["c"], M["cu"])
            slide = cap.sliding_resistance(Vd, g["A_eff"], c_d, phi_d, self.delta_ratio,
                                           which == "undrained", self.adhesion_ratio)
            Hd = math.hypot(Hbd, Hld)
            Rhd = slide["R"] / R["Rh"]
            out["combinations"].append({
                "name": name, "sets": [a_set, m_set, r_set], "analysis": which,
                "Ed": Ed, "Rd": Rd, "utilisation": Ed / Rd if Rd > 0 else float("inf"),
                "status": "OK" if Ed <= Rd + 1e-9 else "NOT OK",
                "Hd": Hd, "Rhd": Rhd,
                "slide_utilisation": Hd / Rhd if Rhd > 0 else float("inf"),
                "slide_status": "N/A" if Hd <= 0 else ("OK" if Hd <= Rhd + 1e-9
                                                       else "NOT OK"),
                "q_ult": run["q_ult"], "q_net_ult": run["q_net_ult"],
                "factors": {"A": dict(A), "M": dict(M), "R": dict(R)},
                "c_d": c_d, "phi_d": phi_d, "B_eff": g["B_eff"], "L_eff": g["L_eff"],
                "A_eff": g["A_eff"],
            })
        if out["combinations"]:
            worst = max(out["combinations"], key=lambda comb: comb["utilisation"])
            out["governing"] = worst["name"]
            out["utilisation"] = worst["utilisation"]
            out["status"] = ("NOT OK" if any(c["status"] == "NOT OK"
                                             for c in out["combinations"]) else "OK")
        return out

    def _layer_table(self) -> List[dict]:
        """Each layer with the stresses at its middle, for the report."""
        rows = []
        for layer in self.profile.layers:
            mid = 0.5 * (layer["top"] + layer["bottom"])
            rows.append({
                "name": layer["name"], "top": layer["top"], "bottom": layer["bottom"],
                "thickness": layer["thickness"], "behaviour": layer["behaviour"],
                "gamma": layer["gamma"], "gamma_sat": layer["gamma_sat"],
                "c": layer["c"], "phi": layer["phi"], "cu": layer["cu"],
                "E": layer["E"], "nu": layer["nu"],
                "sigma_v": self.profile.total_stress(mid),
                "u": self.profile.pore_pressure(mid),
                "sigma_eff": self.profile.effective_stress(mid),
            })
        return rows

    # ------------------------------------------------------------------ width
    def utilisation_for_width(self, B: float) -> float:
        """The bearing utilisation a trial width would give.

        Everything but the width is held as it is; a rectangle keeps its
        length-to-width ratio, a square and a circle stay square and round,
        and a strip keeps its length.
        """
        trial = copy.deepcopy(self.config)
        f = trial.setdefault("foundation", {})
        ratio = self.L / self.B if self.shape == "rectangle" else 1.0
        f["B"] = float(B)
        if self.shape == "rectangle":
            f["L"] = float(B) * ratio
        trial.setdefault("criteria", {})["approach"] = self.approach
        try:
            other = BearingAnalysis(trial)
            res = other.run(with_width=False)
        except (BearingError, ValueError, ZeroDivisionError):
            return float("inf")
        if self.approach != "fs" and res.get("eurocode", {}).get("combinations"):
            return res["eurocode"]["utilisation"]
        return res["checks"]["bearing"]["utilisation"]

    def required_width(self, tolerance: float = 1e-3) -> float:
        """The smallest width that satisfies the bearing check, by bisection."""
        lo, hi = WIDTH_RANGE
        if self.utilisation_for_width(hi) > 1.0:
            return float("nan")
        if self.utilisation_for_width(lo) <= 1.0:
            return lo
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if self.utilisation_for_width(mid) > 1.0:
                lo = mid
            else:
                hi = mid
            if hi - lo < tolerance:
                break
        return hi


    # ------------------------------------------------------------------ sweeps
    def sweep_dimension(self, key: str, values) -> List[dict]:
        """Re-run the analysis with one dimension changed, for the design charts.

        `key` is ``B`` or ``Df``; a rectangle keeps its length-to-width ratio
        as the width is swept. Each point carries the capacity, the allowable
        pressure, what the foundation would then be carrying, and the factor
        of safety, so the chart can show where the three meet.
        """
        out = []
        ratio = self.L / self.B if self.shape == "rectangle" else 1.0
        for value in values:
            trial = copy.deepcopy(self.config)
            f = trial.setdefault("foundation", {})
            if key == "B":
                f["B"] = float(value)
                if self.shape == "rectangle":
                    f["L"] = float(value) * ratio
            else:
                f["Df"] = float(value)
            try:
                res = BearingAnalysis(trial).run(with_width=False)
            except (BearingError, ValueError, ZeroDivisionError):
                continue
            bearing = res["checks"]["bearing"]
            out.append({key: float(value), "q_ult": res["q_ult"],
                        "q_net_ult": res["q_net_ult"], "q_all": bearing["q_all"],
                        "q_applied": res["applied"]["q"], "FS": bearing["actual"],
                        "utilisation": bearing["utilisation"]})
        return out

    def envelope(self, ratios=None, iterations: int = 60) -> List[Tuple[float, float]]:
        """The V–H failure envelope of the base, by the governing method.

        For each ratio H/V the vertical load at failure satisfies
        V = q_ult(V, H = ratio·V)·A', which the load inclination factors make
        implicit; it is settled by repeated substitution. The moment is left
        out, so the envelope is the classical one drawn in the V–H plane.
        """
        entry = self.results.get("methods", {}).get(self.results.get("primary"))
        if entry is None:
            return []
        undrained = entry["governing"] == "undrained"
        params = self.results["params"]["undrained" if undrained else "drained"]
        c, phi = self._design_strength(params, undrained)
        q = (self.profile.total_stress(self.Df) if undrained
             else self.profile.effective_stress(self.Df))
        area = self.B * self.L
        if self.shape == "circle":
            area = math.pi * (self.B / 2.0) ** 2
        B_eff, L_eff = self.B, self.L
        if ratios is None:
            top = math.tan(math.radians(phi)) + 0.2 if not undrained else 1.2
            ratios = np.linspace(0.0, max(top, 0.2), 28)

        points = []
        for ratio in ratios:
            V = max(self.V, 1.0)
            for _ in range(iterations):
                out = cap.ultimate(
                    self.results["primary"], c=c, phi=phi, gamma=params["gamma"], q=q,
                    B=B_eff, L=L_eff, Df=self.Df, shape=self.shape, V=V,
                    Hb=ratio * V, Hl=0.0, area=area, eta=self.eta, beta=self.beta,
                    use_shape=self.use_shape,
                    use_depth=self.use_depth and (F.HAS_DEPTH[self.results["primary"]]
                                                  or self.results["primary"] == "ec7"),
                    use_inclination=self.use_inclination
                    and F.HAS_INCLINATION[self.results["primary"]],
                    use_base=self.use_base and F.HAS_BASE[self.results["primary"]],
                    use_ground=self.use_ground and F.HAS_GROUND[self.results["primary"]])
                new = out["q_ult"] * area
                if new <= 0:
                    break
                if abs(new - V) < 1e-6 * max(new, 1.0):
                    V = new
                    break
                V = 0.5 * (V + new)
            if V > 0:
                points.append((V, ratio * V))
        # the sliding cut-off: the base cannot take more shear than it can resist
        c_base, phi_base = c, phi
        cut = []
        for V, H in points:
            slide = cap.sliding_resistance(V, area, c_base, phi_base, self.delta_ratio,
                                           undrained, self.adhesion_ratio)
            cut.append((V, min(H, slide["R"])))
        return cut


def analyse(config: Dict[str, Any]) -> BearingAnalysis:
    """Build and run an analysis in one call."""
    analysis = BearingAnalysis(config)
    analysis.run()
    return analysis
