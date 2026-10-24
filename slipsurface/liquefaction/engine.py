"""
The liquefaction analysis of one borehole, from its SPT tests or from a CPT
sounding beside it.

Given the design earthquake (Mw, a_max), the groundwater level during the
earthquake and when the ground was tested, the soil layers with their index
properties and the tests, `LiquefactionAnalysis.run()` works out, test by test,

    * σv, u and σ'v during the earthquake, and σ'v when the test was made
    * SPT: N60 from the energy, borehole, rod-length and sampler corrections,
      reduced in gravelly layers (JRA 1996);
      CPT: qt, the soil behaviour type index Ic and the fines content it implies
    * the susceptibility class: from the fines content and the Atterberg limits
      for the SPT, from Ic for the CPT
    * the normalised resistance, rd, CSR, CRR7.5, MSF, Kσ, CRR and FS by every
      triggering procedure of the test type — the chosen one governs, the
      others are kept for the comparison figure — and by Andrus & Stokoe where
      Vs is known
    * for the clay-like soils, the factor of safety against cyclic softening
      (Boulanger & Idriss 2007)
    * the post-liquefaction volumetric and maximum shear strains, and the
      seismic compression of the dry sand above the water table (Pradel 1998)

and, over the borehole,

    * the settlement (saturated and dry), the liquefaction potential index
      LPI, the severity number LSN, and the lateral displacement index LDI with
      the lateral displacement of a slope or towards a free face (Zhang et al.
      2004)
    * the lowest factor of safety and the thickness that liquefies
    * the checks against the required factor of safety and the allowable
      settlement

Each test stands for the part of its layer nearest to it: a layer is shared
among its tests at the mid-points between them, so a test in a sand never
speaks for the clay beneath it. A layer without a test is not assessed (and
the analysis says so).

Input problems are raised as `LiqError`, which carries a translation key, so
the interface can say what is wrong in the user's language.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Tuple

import numpy as np

from . import consequences as cq
from . import cpt, spt, susceptibility, triggering
from .config import (
    DEFAULT_CONFIG,
    GEOMETRIES,
    METHODS,
    METHODS_CPT,
    PGA_SOURCES,
    SUSCEPTIBILITY,
    TEST_TYPES,
)

#: Index properties a test row may carry, else it takes its layer's
INDEX_KEYS = ["FC", "clay", "LL", "PI", "wn"]

#: Soil numbers of a layer row
LAYER_KEYS = ["thickness", "gamma", "gamma_sat"] + INDEX_KEYS + ["Vs", "D50", "OCR", "su"]

#: The states of a test, from the point of view of liquefaction
STATES = ["liquefied", "marginal", "safe", "dense", "softening", "not", "dry"]

#: A blow count above which the test is taken as refusal
N_REFUSAL = 50.0

#: D50 [mm] from which a soil is gravelly
GRAVEL_D50 = 2.0


class LiqError(ValueError):
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


def _maybe(d: dict, key: str):
    """A number, or None for an empty cell."""
    value = d.get(key)
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def gravel_factor(d50) -> np.ndarray:
    """The reduction of the blow count of a gravelly soil (Japan Road
    Association 1996): 1 − 0.36·log10(D50/2) for D50 ≥ 2 mm, 1 below."""
    d = np.asarray(d50, dtype=float)
    safe = np.maximum(d, GRAVEL_D50)
    return np.where(d >= GRAVEL_D50, 1.0 - 0.36 * np.log10(safe / GRAVEL_D50), 1.0)


# --------------------------------------------------------------------------- #
#  Soil profile
# --------------------------------------------------------------------------- #

class Profile:
    """The layered soil column and its in-situ stresses."""

    def __init__(self, layers: List[dict], gamma_w: float):
        self.layers = layers
        self.gw = gamma_w
        top = 0.0
        for layer in layers:
            layer["top"] = top
            layer["bottom"] = top + layer["thickness"]
            top = layer["bottom"]
        self.depth = top

    def layer_index(self, z) -> np.ndarray:
        """Index of the layer at depth z (a boundary belongs to the layer below)."""
        bottoms = np.array([layer["bottom"] for layer in self.layers])
        index = np.searchsorted(bottoms, np.asarray(z, dtype=float), side="right")
        return np.minimum(index, len(self.layers) - 1)

    def total_stress(self, z, zw: float) -> np.ndarray:
        """σv at depth z with the water table at zw; the last layer continues."""
        z = np.atleast_1d(np.asarray(z, dtype=float))
        sigma = np.zeros_like(z)
        for i, layer in enumerate(self.layers):
            top = layer["top"]
            bottom = layer["bottom"] if i < len(self.layers) - 1 else np.inf
            seg_bot = np.clip(z, top, bottom)
            dry = np.clip(np.minimum(seg_bot, zw) - top, 0.0, None)
            wet = np.clip(seg_bot - max(top, zw), 0.0, None)
            sigma += layer["gamma"] * dry + layer["gamma_sat"] * wet
        return sigma

    def pore_pressure(self, z, zw: float) -> np.ndarray:
        z = np.atleast_1d(np.asarray(z, dtype=float))
        return self.gw * np.maximum(z - zw, 0.0)


# --------------------------------------------------------------------------- #
#  The analysis
# --------------------------------------------------------------------------- #

class LiquefactionAnalysis:
    """Liquefaction of one borehole. Build it, then call `run()`."""

    def __init__(self, config: Dict[str, Any]):
        self.config = copy.deepcopy(config)
        self.warnings: List[Tuple[str, Dict[str, Any]]] = []
        self._read()
        self.results: Dict[str, Any] = {}

    # ------------------------------------------------------------------ input
    def _read(self) -> None:
        cfg = self.config
        base = DEFAULT_CONFIG
        e = {**base["earthquake"], **cfg.get("earthquake", {})}
        w = {**base["groundwater"], **cfg.get("groundwater", {})}
        s = {**base["spt_setup"], **cfg.get("spt_setup", {})}
        g = {**base["ground"], **cfg.get("ground", {})}
        o = {**base["options"], **cfg.get("options", {})}
        c = {**base["criteria"], **cfg.get("criteria", {})}

        self.magnitude = _num(e, "magnitude", 7.5)
        self.pga_source = e["pga_source"] if e.get("pga_source") in PGA_SOURCES else "direct"
        self.sds = _num(e, "sds", 1.0)
        self.amax = 0.4 * self.sds if self.pga_source == "tbdy" else _num(e, "pga", 0.0)
        if not 4.0 <= self.magnitude <= 9.5:
            raise LiqError("err_magnitude")
        if self.amax <= 0 or self.amax > 3.0:
            raise LiqError("err_pga")
        if not 5.25 <= self.magnitude <= 8.5:
            self.warnings.append(_message("warn_magnitude"))

        self.zw = _num(w, "depth", 0.0)
        self.zw_test = _num(w, "depth_test", self.zw)
        gamma_w = _num(w, "gamma_water", 9.81)
        if self.zw < 0 or self.zw_test < 0:
            raise LiqError("err_water")

        self.test_type = o["test_type"] if o.get("test_type") in TEST_TYPES else "spt"
        self.energy = _num(s, "energy", 60.0)
        self.borehole = _num(s, "borehole", 100.0)
        self.stickup = max(0.0, _num(s, "stickup", 0.0))
        self.rod_correction = bool(s.get("rod_correction", True))
        self.no_liner = bool(s.get("no_liner", False))
        if self.test_type == "spt" and not 20.0 <= self.energy <= 120.0:
            raise LiqError("err_energy")

        self.geometry = g["geometry"] if g.get("geometry") in GEOMETRIES else "level"
        self.slope = _num(g, "slope", 0.0)
        self.face_length = _num(g, "length", 0.0)
        self.face_height = _num(g, "height", 0.0)
        if self.slope < 0 or (self.geometry == "free_face"
                              and (self.face_length <= 0 or self.face_height <= 0)):
            raise LiqError("err_ground")

        self.method_spt = o["method"] if o.get("method") in METHODS else METHODS[0]
        self.method_cpt = (o["method_cpt"] if o.get("method_cpt") in METHODS_CPT
                           else METHODS_CPT[0])
        self.method = self.method_cpt if self.test_type == "cpt" else self.method_spt
        self.criterion = (o["susceptibility"] if o.get("susceptibility") in SUSCEPTIBILITY
                          else SUSCEPTIBILITY[0])
        self.fine_threshold = _num(o, "fine_threshold", 35.0)
        self.uncertain_susceptible = bool(o.get("uncertain_susceptible", True))
        self.settlement_depth = _num(o, "settlement_depth", 20.0)
        self.cetin_pl = _num(o, "cetin_pl", 15.0)
        self.vs12_input = _num(o, "vs12", 0.0)
        self.gravel_correction = bool(o.get("gravel_correction", True))
        self.dry_settlement = bool(o.get("dry_settlement", True))
        self.softening = bool(o.get("softening", True))
        self.area_ratio = _num(o, "area_ratio", 0.8)
        self.cfc = _num(o, "cfc", 0.0)
        self.ic_limit = _num(o, "ic_limit", cpt.IC_LIMIT)
        self.nkt = _num(o, "nkt", 14.0)
        if self.settlement_depth <= 0:
            raise LiqError("err_settlement_depth")
        if not 0.0 < self.cetin_pl < 100.0:
            raise LiqError("err_pl")
        if not 0.0 <= self.area_ratio <= 1.0 or self.nkt <= 0:
            raise LiqError("err_cpt_options")

        self.fs_required = _num(c, "fs_required", 1.0)
        self.s_allow = max(0.0, _num(c, "s_allow", 0.0))
        if self.fs_required <= 0:
            raise LiqError("err_fs_required")

        layers = []
        for row in cfg.get("soil_profile") or []:
            layer = {**base["soil_profile"][0], **row}
            thickness = _num(layer, "thickness", 0.0)
            if thickness <= 0:
                continue
            layers.append(self._read_layer(layer, thickness, gamma_w))
        if not layers:
            raise LiqError("err_no_layers")
        self.profile = Profile(layers, gamma_w)
        self.tests = self._read_cpt(cfg) if self.test_type == "cpt" else self._read_spt(cfg)

    def _read_spt(self, cfg: dict) -> List[dict]:
        tests = []
        for row in cfg.get("spt") or []:
            depth, blows = _maybe(row, "depth"), _maybe(row, "N")
            if depth is None or blows is None:
                continue
            if depth <= 0 or depth > self.profile.depth + 1e-9:
                raise LiqError("err_spt_depth", z=depth, H=self.profile.depth)
            if blows < 0:
                raise LiqError("err_spt_n", z=depth)
            tests.append({"depth": depth, "N": blows,
                          **{key: _maybe(row, key) for key in INDEX_KEYS}})
        if not tests:
            raise LiqError("err_no_spt")
        return self._unique(tests)

    def _read_cpt(self, cfg: dict) -> List[dict]:
        rows = []
        for row in cfg.get("cpt") or []:
            depth, qc = _maybe(row, "depth"), _maybe(row, "qc")
            if depth is None or qc is None:
                continue
            fs, u2 = _maybe(row, "fs") or 0.0, _maybe(row, "u2") or 0.0
            if depth <= 0 or depth > self.profile.depth + 1e-9:
                raise LiqError("err_cpt_depth", z=depth, H=self.profile.depth)
            if qc <= 0 or fs < 0:
                raise LiqError("err_cpt_values", z=depth)
            rows.append({"depth": depth, "qc": qc, "fs": fs, "u2": u2})
        if not rows:
            raise LiqError("err_no_cpt")
        return self._unique(rows)

    def _unique(self, tests: List[dict]) -> List[dict]:
        tests.sort(key=lambda t: t["depth"])
        unique = []
        for test in tests:
            if unique and abs(test["depth"] - unique[-1]["depth"]) < 1e-6:
                self.warnings.append(_message("warn_duplicate", z=test["depth"]))
                continue
            unique.append(test)
        return unique

    def _read_layer(self, row: dict, thickness: float, gamma_w: float) -> dict:
        name = str(row.get("name") or "").strip() or "Layer"
        layer = {"name": name, "thickness": thickness}
        for key in LAYER_KEYS[1:]:
            layer[key] = _num(row, key, 1.0 if key == "OCR" else 0.0)
        if layer["gamma"] <= 0 or layer["gamma_sat"] <= gamma_w:
            raise LiqError("err_gamma", name=name)
        if not 0.0 <= layer["FC"] <= 100.0 or not 0.0 <= layer["clay"] <= 100.0:
            raise LiqError("err_fines", name=name)
        if min(layer["PI"], layer["LL"], layer["wn"], layer["Vs"], layer["D50"],
               layer["su"]) < 0:
            raise LiqError("err_limits", name=name)
        if layer["PI"] > 0 and layer["LL"] > 0 and layer["PI"] > layer["LL"]:
            raise LiqError("err_pi_ll", name=name)
        if layer["OCR"] < 1.0:
            raise LiqError("err_ocr", name=name)
        return layer

    # ------------------------------------------------------------------ geometry
    def _intervals(self, z: np.ndarray, lay: np.ndarray):
        """The part of its layer each test stands for: the layer is shared among
        its tests at the mid-points between them."""
        top, bot = np.zeros_like(z), np.zeros_like(z)
        for i, layer in enumerate(self.profile.layers):
            rows = np.nonzero(lay == i)[0]
            if rows.size == 0:
                self.warnings.append(_message("warn_layer_untested", name=layer["name"]))
                continue
            depths = z[rows]
            mids = 0.5 * (depths[:-1] + depths[1:])
            top[rows] = np.concatenate([[layer["top"]], mids])
            bot[rows] = np.concatenate([mids, [layer["bottom"]]])
        return top, bot

    def vs12(self) -> Tuple[float, bool]:
        """The time-averaged Vs of the top 12 m for Cetin's rd: entered, from the
        layers' Vs where every layer in the top 12 m has one, or else from N60 by
        Imai & Tonouchi (1982), Vs = 97·N^0.314. Returns (Vs12, estimated)."""
        if self.vs12_input > 0:
            return self.vs12_input, False
        travel, depth = 0.0, 0.0
        for layer in self.profile.layers:
            if depth >= 12.0:
                break
            h = min(layer["bottom"], 12.0) - layer["top"]
            if h <= 0:
                continue
            if layer["Vs"] <= 0:
                travel = None
                break
            travel += h / layer["Vs"]
            depth += h
        if travel and depth > 0:
            return (depth if depth < 12.0 else 12.0) / travel, False
        if self.test_type != "spt":
            return 180.0, True
        top = [t for t in self.tests if t["depth"] <= 12.0] or self.tests[:1]
        n = np.array([t["N"] for t in top]) * self.energy / 60.0
        vs = 97.0 * np.maximum(n, 1.0) ** 0.314
        return float(len(vs) / np.sum(1.0 / vs)), True

    # ------------------------------------------------------------------ the tests
    def _spt(self, z, lay, sigma_eff_test, common) -> Dict[str, Any]:
        """N60, susceptibility and the SPT procedures."""
        layers = self.profile.layers
        tests = self.tests
        N = np.array([t["N"] for t in tests])
        props = {key: np.array([t[key] if t[key] is not None else layers[i][key]
                                for t, i in zip(tests, lay)]) for key in INDEX_KEYS}
        bad = [float(zz) for zz, pi, ll in zip(z, props["PI"], props["LL"]) if 0 < ll < pi]
        if bad:
            raise LiqError("err_spt_pi_ll", z=bad[0])

        ce = spt.energy_factor(self.energy)
        cb = spt.borehole_factor(self.borehole)
        cr = spt.rod_factor(z + self.stickup) if self.rod_correction else np.ones_like(z)
        d50 = np.array([layers[i]["D50"] for i in lay])
        gravelly = d50 >= GRAVEL_D50
        cg = gravel_factor(d50) if self.gravel_correction else np.ones_like(z)
        if gravelly.any():
            self.warnings.append(_message("warn_gravel" if self.gravel_correction
                                          else "warn_gravel_uncorrected"))
        n_partial = N * ce * cb * cr
        cs = spt.sampler_factor(spt.cn_liao_whitman(sigma_eff_test) * n_partial, self.no_liner)
        n60 = n_partial * cs * cg
        if np.any(N > N_REFUSAL):
            self.warnings.append(_message("warn_refusal", n=N_REFUSAL))

        classes = susceptibility.classify(self.criterion, props["FC"], props["clay"],
                                          props["LL"], props["PI"], props["wn"],
                                          self.fine_threshold)
        methods = {key: fn(n60=n60, fc=props["FC"], **common)
                   for key, fn in triggering.PROCEDURES.items()}
        return {"props": props, "classes": classes, "methods": methods,
                # the blow count the dry-sand settlement is read from
                "n1_dry": methods["youd2001"]["n1"],
                "factors": {"CE": ce, "CB": cb},
                "measures": {"N": N, "CR": cr, "CS": cs, "Cg": cg, "N60": n60, "D50": d50}}

    def _cpt(self, z, lay, sigma_v_test, sigma_eff_test, common) -> Dict[str, Any]:
        """qt, Ic, the fines content, susceptibility and the CPT procedures."""
        layers = self.profile.layers
        qc = np.array([t["qc"] for t in self.tests]) * 1000.0       # MPa -> kPa
        fs = np.array([t["fs"] for t in self.tests])
        u2 = np.array([t["u2"] for t in self.tests])
        qt = cpt.tip_resistance(qc, u2, self.area_ratio)
        ic_rw, n_rw = cpt.ic_robertson_wride(qt, fs, sigma_v_test, sigma_eff_test)
        ic_09, n_09 = cpt.ic_robertson_2009(qt, fs, sigma_v_test, sigma_eff_test)
        ic = ic_rw if self.method == "rw1998" else ic_09
        fc = cpt.fines_from_ic(ic_09, self.cfc)
        props = {key: np.array([layers[i][key] for i in lay]) for key in INDEX_KEYS}
        props["FC"] = fc
        classes = ["not" if value > self.ic_limit else "sand" for value in ic]
        methods = {"ib2014_cpt": triggering.ib2014_cpt(qt=qt, fc=fc, **common),
                   "rw1998": triggering.rw1998(qt=qt, fc=fc, ic=ic_rw, n_rw=n_rw, **common)}
        n60 = cpt.n60_from_cpt(qt, ic)
        n_exp = n_rw if self.method == "rw1998" else n_09
        # Qtn (net, with the stress exponent found) and F, for the chart
        big_q, big_f = cpt.q_f(qt, fs, sigma_v_test, sigma_eff_test, n_exp)
        return {"props": props, "classes": classes, "methods": methods,
                "n1_dry": spt.cn_liao_whitman(sigma_eff_test) * n60, "factors": {},
                "measures": {"qc": qc / 1000.0, "fs_cpt": fs, "u2": u2, "qt": qt, "Ic": ic,
                             "n_exp": n_exp, "Q": big_q, "F": big_f, "N60": n60}}

    # ------------------------------------------------------------------ run
    def run(self) -> Dict[str, Any]:
        P = self.profile
        z = np.array([t["depth"] for t in self.tests])
        lay = P.layer_index(z)
        layers = P.layers

        # ---- stresses: during the earthquake, and when the test was made
        sigma_v = P.total_stress(z, self.zw)
        u = P.pore_pressure(z, self.zw)
        sigma_eff = sigma_v - u
        sigma_v_test = P.total_stress(z, self.zw_test)
        sigma_eff_test = sigma_v_test - P.pore_pressure(z, self.zw_test)

        vs12, estimated = self.vs12()
        common = dict(z=z, sigma_v=sigma_v, sigma_eff=sigma_eff, sigma_eff_test=sigma_eff_test,
                      magnitude=self.magnitude, amax=self.amax, pl=self.cetin_pl, vs12=vs12)
        if self.test_type == "cpt":
            part = self._cpt(z, lay, sigma_v_test, sigma_eff_test, common)
        else:
            part = self._spt(z, lay, sigma_eff_test, common)
            if self.method == "cetin2004" and estimated:
                self.warnings.append(_message("warn_vs12", v=vs12))
        props, classes, methods = part["props"], part["classes"], part["methods"]
        vs = np.array([layers[i]["Vs"] for i in lay])

        # ---- susceptibility
        evaluated = np.array([c in ("sand", "susceptible") or
                              (c == "moderate" and self.uncertain_susceptible)
                              for c in classes])
        wet = z > self.zw
        if any(c == "moderate" for c, w_ in zip(classes, wet) if w_):
            self.warnings.append(_message("warn_moderate" if self.uncertain_susceptible
                                          else "warn_moderate_excluded"))
        assessed = evaluated & wet

        # ---- the shear-wave check
        has_vs = bool(np.any(vs > 0))
        if has_vs:
            methods["vs2000"] = triggering.vs2000(
                z=z, sigma_v=sigma_v, sigma_eff=sigma_eff, sigma_eff_test=sigma_eff_test,
                vs=vs, fc=props["FC"], magnitude=self.magnitude, amax=self.amax)
        for key, m in methods.items():
            m["fs_eff"] = np.where(assessed, m["fs"], np.nan)
            m["eps"] = np.where(assessed, cq.volumetric_strain(m["fs"], m["dr"]), 0.0)
            m["gamma"] = np.where(assessed, cq.max_shear_strain(m["fs"], m["dr"]), 0.0)
        main = methods[self.method]
        if self.method in ("ib2014", "ib2014_cpt") and np.any(assessed & (z > 30.0)):
            self.warnings.append(_message("warn_deep"))

        # ---- clay-like soils: cyclic softening
        clay_like = wet & ~evaluated
        fs_soft = np.full_like(z, np.nan)
        su_ratio = np.full_like(z, np.nan)
        if self.softening and clay_like.any():
            su = np.array([layers[i]["su"] for i in lay])
            ocr = np.array([layers[i]["OCR"] for i in lay])
            ratio = np.where(su > 0, su / np.maximum(sigma_eff, 1e-6), 0.22 * ocr ** 0.8)
            if self.test_type == "cpt":
                su_cpt = (part["measures"]["qt"] - sigma_v) / self.nkt
                ratio = np.where(su > 0, ratio, su_cpt / np.maximum(sigma_eff, 1e-6))
            soft = triggering.softening(ratio, main["csr"], self.magnitude)
            fs_soft = np.where(clay_like, soft["fs"], np.nan)
            su_ratio = np.where(clay_like, ratio, np.nan)

        # ---- states
        fs = main["fs"]
        softens = clay_like & np.isfinite(fs_soft) & (fs_soft < 1.0)
        state = np.where(~wet, "dry", np.where(~evaluated, np.where(softens, "softening", "not"),
                         np.where(main["dense"], "dense", np.where(fs < 1.0, "liquefied", np.where(
                             fs < self.fs_required, "marginal", "safe")))))

        # ---- over the borehole
        top, bot = self._intervals(z, lay)
        eps = main["eps"]
        lo, hi = self.zw, self.settlement_depth
        thick = np.clip(np.minimum(bot, hi) - np.maximum(top, lo), 0.0, None)
        ds = eps * thick * 1000.0                                     # mm

        eps_dry = np.zeros_like(z)
        if self.dry_settlement:
            sandy = evaluated & ~wet
            strain = cq.pradel(sigma_v, sigma_eff, part["n1_dry"], main["rd"], self.amax,
                               self.magnitude)
            eps_dry = np.where(sandy, strain, 0.0)
        thick_dry = np.clip(np.minimum(np.minimum(bot, self.zw), hi) - top, 0.0, None)
        ds_dry = eps_dry * thick_dry * 1000.0

        lpi, lpi_part = cq.lpi(top, bot, main["fs_eff"], self.zw)
        lsn, lsn_part = cq.lsn(top, bot, eps, self.zw, hi)
        z_ldi = min(hi, 2.0 * self.face_height) if self.geometry == "free_face" else hi
        ldi, ldi_part = cq.ldi(top, bot, main["gamma"], self.zw, z_ldi)
        ld, ld_in_range = cq.lateral_displacement(ldi, self.geometry, self.slope,
                                                  self.face_length, self.face_height)
        if self.geometry != "level" and not ld_in_range:
            self.warnings.append(_message("warn_lateral_range"))
        liq_thick = np.clip(bot - np.maximum(top, self.zw), 0.0, None)
        h_liq = float(np.sum(np.where(state == "liquefied", liq_thick, 0.0)))
        h_soft = float(np.sum(np.where(state == "softening", liq_thick, 0.0)))

        finite = np.isfinite(main["fs_eff"])
        if finite.any():
            k = int(np.nanargmin(np.where(finite, main["fs_eff"], np.inf)))
            fs_min, z_fs_min = float(main["fs_eff"][k]), float(z[k])
        else:
            fs_min, z_fs_min = float("nan"), float("nan")
        settlement_sat = float(np.sum(ds))
        settlement_dry = float(np.sum(ds_dry))
        settlement = settlement_sat + settlement_dry

        comparison = {}
        for key, m in methods.items():
            s_m = float(np.sum(m["eps"] * thick * 1000.0))
            lpi_m = cq.lpi(top, bot, m["fs_eff"], self.zw)[0]
            ldi_m = cq.ldi(top, bot, m["gamma"], self.zw, z_ldi)[0]
            fin = m["fs_eff"][np.isfinite(m["fs_eff"])]
            comparison[key] = {"fs_min": float(fin.min()) if fin.size else float("nan"),
                               "settlement": s_m, "lpi": lpi_m,
                               "ld": cq.lateral_displacement(ldi_m, self.geometry, self.slope,
                                                             self.face_length,
                                                             self.face_height)[0],
                               "n_liq": int(np.sum(fin < 1.0))}
        if has_vs:
            # the shear-wave check has no strains of its own
            comparison["vs2000"]["settlement"] = float("nan")
            comparison["vs2000"]["ld"] = float("nan")

        at_risk = bool(finite.any() and fs_min < self.fs_required)
        checks = {
            "fs": {"actual": fs_min, "required": self.fs_required,
                   "status": "N/A" if not finite.any() else
                   ("NOT OK" if at_risk else "OK")},
            "settlement": {"actual": settlement, "allowable": self.s_allow,
                           "status": "N/A" if self.s_allow <= 0 else
                           ("OK" if settlement <= self.s_allow else "NOT OK")},
        }

        self.results = {
            "kind": self.test_type,
            "amax": self.amax, "magnitude": self.magnitude, "zw": self.zw,
            "zw_test": self.zw_test, "method": self.method, "vs12": vs12,
            "vs12_estimated": estimated,
            "factors": part["factors"],
            "tests": {
                "z": z, "top": top, "bot": bot, "layer": lay,
                "sigma_v": sigma_v, "u": u, "sigma_eff": sigma_eff,
                "sigma_eff_test": sigma_eff_test, "Vs": vs, "class": classes,
                "assessed": assessed, "state": state, "ds": ds, "ds_dry": ds_dry,
                "eps_dry": eps_dry, "lpi": lpi_part, "lsn": lsn_part, "ldi": ldi_part,
                "fs_soft": fs_soft, "su_ratio": su_ratio,
                **part["measures"], **props,
            },
            "methods": methods, "comparison": comparison,
            "fs_min": fs_min, "z_fs_min": z_fs_min, "h_liq": h_liq, "h_soft": h_soft,
            "settlement": settlement, "settlement_sat": settlement_sat,
            "settlement_dry": settlement_dry,
            "lpi": lpi, "lpi_class": cq.lpi_class(lpi),
            "lsn": lsn, "lsn_class": cq.lsn_class(lsn),
            "ldi": ldi, "ld": ld, "ld_in_range": ld_in_range, "z_ldi": z_ldi,
            "at_risk": at_risk, "checks": checks, "warnings": list(self.warnings),
        }
        return self.results
