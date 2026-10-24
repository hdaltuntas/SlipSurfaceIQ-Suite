"""
The rock mass analysis.

`RockAnalysis(config).run()` takes the nested configuration (see
`config.DEFAULT_CONFIG`) and returns a dictionary with everything the
interface, the figures and the report show:

    intact        σci, mi and Ei used, and the laboratory fit if there was one
    gsi           GSI and how it was arrived at
    hb            mb, s, a
    strength      σt, σc and σcm of the rock mass
    sigma3_max    the upper end of the confinement, and the rule that set it
    mc            the equivalent c', φ' and the strengths of the fitted line
    modulus       Erm by the chosen estimate, and by every estimate
    query         the instantaneous strength at the σ3 asked for
    residual      the residual GSI and strength (Cai et al. 2007)
    applications  c', φ' and σ3max of every application, side by side
    curves        what the figures draw
    warnings      (key, params) pairs, turned into sentences by i18n

Input that cannot be analysed raises `RockError`, whose key and parameters
the interface turns into a sentence in the user's language.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Tuple

import numpy as np

from . import gsi as gsi_mod
from . import hoekbrown as hb
from . import labfit, tables
from .config import APPLICATIONS, DEFAULT_CONFIG, MODULUS_METHODS

__all__ = ["RockAnalysis", "RockError"]

#: GSI the criterion is written for
GSI_MIN, GSI_MAX = 5.0, 100.0
#: Above this GSI the rock mass may be too little jointed to be isotropic
GSI_ISOTROPIC = 85.0


class RockError(ValueError):
    """Input that cannot be analysed: a translation key and its parameters."""

    def __init__(self, key: str, **params):
        super().__init__(key)
        self.key = key
        self.params = params


def _merge(defaults: dict, given: dict) -> dict:
    out = copy.deepcopy(defaults)
    for key, value in (given or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


class RockAnalysis:
    """One rock mass, analysed."""

    def __init__(self, config: Dict[str, Any]):
        self.config = _merge(DEFAULT_CONFIG, config or {})
        if "lab_data" in (config or {}):
            self.config["lab_data"] = copy.deepcopy(config["lab_data"])
        self.results: Dict[str, Any] = {}
        self.warnings: List[Tuple[str, dict]] = []

    # ------------------------------------------------------------------ helpers
    def _warn(self, key: str, **params) -> None:
        self.warnings.append((key, params))

    @property
    def intact_cfg(self) -> dict:
        return self.config["intact"]

    @property
    def mass_cfg(self) -> dict:
        return self.config["rock_mass"]

    @property
    def modulus_cfg(self) -> dict:
        return self.config["modulus"]

    @property
    def application_cfg(self) -> dict:
        return self.config["application"]

    # ------------------------------------------------------------------ steps
    def _intact(self) -> Dict[str, Any]:
        cfg = self.intact_cfg
        rock = tables.rock_type(cfg.get("rock_type", ""))
        fit = None
        if cfg.get("source") == "lab":
            try:
                fit = labfit.fit(self.config.get("lab_data") or [])
            except labfit.LabFitError as exc:
                raise RockError(exc.key) from exc
            sigma_ci, mi = fit["sigma_ci"], fit["mi"]
            if fit["r2"] < 0.9:
                self._warn("warn_lab_r2", r2=fit["r2"])
            if fit["sigma3_max"] < 0.2 * sigma_ci:
                self._warn("warn_lab_narrow", s3=fit["sigma3_max"], limit=0.5 * sigma_ci)
            elif fit["sigma3_max"] > 0.6 * sigma_ci:
                self._warn("warn_lab_wide", s3=fit["sigma3_max"], limit=0.5 * sigma_ci)
        else:
            sigma_ci, mi = float(cfg["sigma_ci"]), float(cfg["mi"])
        if not (math.isfinite(sigma_ci) and sigma_ci > 0.0):
            raise RockError("err_sigma_ci")
        if not (math.isfinite(mi) and mi > 0.0):
            raise RockError("err_mi")
        if rock is not None and abs(mi - rock["mi"]) > rock["mi_pm"] + 1e-9:
            self._warn("warn_mi_range", mi=mi, lo=rock["mi"] - rock["mi_pm"],
                       hi=rock["mi"] + rock["mi_pm"], rock=cfg.get("rock_type", ""))

        m = self.modulus_cfg
        if m.get("Ei_source") == "direct":
            Ei = float(m["Ei"])
            MR = Ei / sigma_ci
        else:
            MR = float(m["MR"])
            Ei = MR * sigma_ci
            if rock is not None and not rock["MR_lo"] - 1e-9 <= MR <= rock["MR_hi"] + 1e-9:
                self._warn("warn_mr_range", MR=MR, lo=rock["MR_lo"], hi=rock["MR_hi"],
                           rock=cfg.get("rock_type", ""))
        if not (math.isfinite(Ei) and Ei > 0.0):
            raise RockError("err_ei")
        return {"sigma_ci": sigma_ci, "mi": mi, "Ei": Ei, "MR": MR,
                "source": cfg.get("source", "manual"), "rock_type": cfg.get("rock_type", ""),
                "fit": fit}

    def _gsi(self) -> Dict[str, Any]:
        try:
            result = gsi_mod.estimate(self.mass_cfg)
        except (ValueError, TypeError, KeyError) as exc:
            raise RockError("err_gsi_input", name=str(exc).strip("'")) from exc
        value = result["GSI"]
        if not (math.isfinite(value) and GSI_MIN <= value <= GSI_MAX):
            raise RockError("err_gsi", gsi=value, lo=GSI_MIN, hi=GSI_MAX)
        if result["source"] == "rmr" and result["RMR89"] < gsi_mod.RMR_LIMIT:
            self._warn("warn_rmr_low", rmr=result["RMR89"], limit=gsi_mod.RMR_LIMIT)
        if value > GSI_ISOTROPIC:
            self._warn("warn_gsi_high", gsi=value)
        return result

    def _sigma3_max(self, application: str, sigma_ci: float, sigma_cm: float) -> float:
        a = self.application_cfg
        if application in ("tunnel", "slope"):
            if not float(a["unit_weight"]) > 0.0 or not float(a["depth"]) > 0.0:
                raise RockError("err_depth")
        value = hb.sigma3_max(application, sigma_ci, sigma_cm, float(a["unit_weight"]),
                              float(a["depth"]), float(a["sigma3_max"]))
        if not (math.isfinite(value) and value > 0.0):
            raise RockError("err_sigma3max")
        return value

    # ------------------------------------------------------------------ the analysis
    def run(self) -> Dict[str, Any]:
        self.warnings = []
        intact = self._intact()
        gsi = self._gsi()
        GSI = gsi["GSI"]
        D = float(self.mass_cfg["D"])
        if not 0.0 <= D <= 1.0:
            raise RockError("err_D")
        sigma_ci, mi = intact["sigma_ci"], intact["mi"]

        k = hb.constants(GSI, mi, D)
        mb, s, a = k["mb"], k["s"], k["a"]
        strength = {
            "sigma_t": hb.tensile_strength(sigma_ci, mb, s),
            "sigma_c": hb.uniaxial_strength(sigma_ci, s, a),
            "sigma_cm": hb.global_strength(sigma_ci, mb, s, a),
        }

        application = self.application_cfg.get("type", "general")
        if application not in APPLICATIONS:
            application = "general"
        s3max = self._sigma3_max(application, sigma_ci, strength["sigma_cm"])
        mc = hb.mohr_coulomb_fit(sigma_ci, mb, s, a, s3max)
        if application == "tunnel" and D > 0.0:
            self._warn("warn_tunnel_D", D=D)

        # every application side by side; the ones that need a depth only when
        # there is one to use
        applications = {}
        for name in APPLICATIONS:
            if name == "custom" and application != "custom":
                continue
            try:
                value = self._sigma3_max(name, sigma_ci, strength["sigma_cm"])
            except RockError:
                continue
            fitted = hb.mohr_coulomb_fit(sigma_ci, mb, s, a, value)
            applications[name] = {"sigma3_max": value, "c": fitted["c"], "phi": fitted["phi"]}

        # deformability
        method = self.modulus_cfg.get("method", "generalized")
        if method not in MODULUS_METHODS:
            method = "generalized"
        moduli = {name: hb.modulus(name, GSI, D, sigma_ci, intact["Ei"])
                  for name in MODULUS_METHODS}
        Erm = moduli[method]
        if Erm > intact["Ei"]:
            self._warn("warn_erm_above_ei", Erm=Erm, Ei=intact["Ei"])

        # the instantaneous strength at the σ3 asked for
        s3_query = float(self.config["query"]["sigma3"])
        if s3_query < strength["sigma_t"]:
            self._warn("warn_query_tension", s3=s3_query, st=strength["sigma_t"])
            s3_query = strength["sigma_t"]
        query = hb.instantaneous(s3_query, sigma_ci, mb, s, a)
        query["sigma1_mc"] = float(hb.mohr_coulomb_sigma1(s3_query, mc["c"], mc["phi"]))

        # residual strength
        gsi_r = hb.residual_gsi(GSI)
        kr = hb.constants(gsi_r, mi, D)
        mc_r = hb.mohr_coulomb_fit(sigma_ci, kr["mb"], kr["s"], kr["a"], s3max)
        residual = {"GSI": gsi_r, **kr, "c": mc_r["c"], "phi": mc_r["phi"],
                    "sigma_t": hb.tensile_strength(sigma_ci, kr["mb"], kr["s"]),
                    "sigma_c": hb.uniaxial_strength(sigma_ci, kr["s"], kr["a"])}

        curves = self._curves(sigma_ci, mb, s, a, strength["sigma_t"], s3max, mc,
                              max(s3_query, 0.0), kr)

        self.results = {
            "intact": intact, "gsi": gsi, "GSI": GSI, "D": D,
            "hb": {"mb": mb, "s": s, "a": a, "mb_mi": mb / mi},
            "strength": strength,
            "application": application,
            "sigma3_max": s3max,
            "gamma_H": float(self.application_cfg["unit_weight"])
            * float(self.application_cfg["depth"]) / 1000.0,
            "mc": mc,
            "modulus": {"method": method, "Erm": Erm, "all": moduli, "Ei": intact["Ei"],
                        "ratio": Erm / intact["Ei"]},
            "query": query,
            "residual": residual,
            "applications": applications,
            "curves": curves,
            "warnings": list(self.warnings),
        }
        return self.results

    # ------------------------------------------------------------------ curves
    @staticmethod
    def _curves(sigma_ci, mb, s, a, sigma_t, s3max, mc, s3_query, kr) -> Dict[str, Any]:
        top = max(s3max, s3_query) * 1.15
        # start a hair inside the tension cut-off so the root stays real
        s3 = np.linspace(sigma_t * (1.0 - 1e-9), top, 240)
        s1 = hb.sigma1(s3, sigma_ci, mb, s, a)
        s1_mc = hb.mohr_coulomb_sigma1(s3, mc["c"], mc["phi"])
        env = hb.shear_envelope(s3, sigma_ci, mb, s, a)
        sigma_t_r = hb.tensile_strength(sigma_ci, kr["mb"], kr["s"])
        s3_r = np.linspace(sigma_t_r * (1.0 - 1e-9), top, 240)
        s1_r = hb.sigma1(s3_r, sigma_ci, kr["mb"], kr["s"], kr["a"])
        env_r = hb.shear_envelope(s3_r, sigma_ci, kr["mb"], kr["s"], kr["a"])
        return {"sigma3": s3, "sigma1": s1, "sigma1_mc": s1_mc,
                "sigma_n": env["sigma_n"], "tau": env["tau"],
                "sigma3_r": s3_r, "sigma1_r": s1_r,
                "sigma_n_r": env_r["sigma_n"], "tau_r": env_r["tau"]}

    # ------------------------------------------------------------------ sweeps
    def sweep(self, what: str, values) -> Dict[str, np.ndarray]:
        """c', φ', σcm, Erm and the constants against GSI or D, the rest held."""
        res = self.results
        sigma_ci, mi = res["intact"]["sigma_ci"], res["intact"]["mi"]
        Ei = res["intact"]["Ei"]
        out = {key: [] for key in ("mb_mi", "s", "a", "c", "phi", "sigma_cm", "sigma_t",
                                   "sigma_c", *MODULUS_METHODS)}
        for value in values:
            GSI = float(value) if what == "GSI" else res["GSI"]
            D = float(value) if what == "D" else res["D"]
            k = hb.constants(GSI, mi, D)
            sigma_cm = hb.global_strength(sigma_ci, k["mb"], k["s"], k["a"])
            try:
                s3max = self._sigma3_max(res["application"], sigma_ci, sigma_cm)
            except RockError:
                s3max = res["sigma3_max"]
            fitted = hb.mohr_coulomb_fit(sigma_ci, k["mb"], k["s"], k["a"], s3max)
            out["mb_mi"].append(k["mb"] / mi)
            out["s"].append(k["s"])
            out["a"].append(k["a"])
            out["c"].append(fitted["c"])
            out["phi"].append(fitted["phi"])
            out["sigma_cm"].append(sigma_cm)
            out["sigma_t"].append(hb.tensile_strength(sigma_ci, k["mb"], k["s"]))
            out["sigma_c"].append(hb.uniaxial_strength(sigma_ci, k["s"], k["a"]))
            for name in MODULUS_METHODS:
                out[name].append(hb.modulus(name, GSI, D, sigma_ci, Ei))
        return {key: np.asarray(v) for key, v in out.items()}
