"""
Input schema and readers for SlipSurface IQ Bearing.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The browser builds its forms from this schema, and the
server turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``B``, ``water_depth``, ``kh`` …) are the ones the
interface uses; the nested keys of the configuration (``foundation.B``,
``groundwater.depth``, ``seismic.kh`` …) are the ones the engine and the
``.bearing`` project files use. `to_config()` and `from_config()` convert
between the two.

A field can declare when it applies — ``when=[("shape", ["rectangle"])]`` —
and the browser hides it whenever the condition does not hold, so the form
shows the inputs of the method that is actually running and no others.

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

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
)
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "slipsurface-bearing"
# Project files saved before the product was renamed still open.
READ_FORMATS = (FILE_FORMAT, "slipsurface-bearing")
FILE_VERSION = "0.1"


def _t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# --------------------------------------------------------------------------- #
#  Schema data structures
# --------------------------------------------------------------------------- #

@dataclass
class Field:
    """One input field."""
    key: str
    label: str
    kind: str = "number"                     # number | text | check | select
    default: Any = 0.0
    unit: str = ""
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    decimals: int = 2
    options: List[Dict[str, str]] = field(default_factory=list)
    when: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Only what the browser needs; empty values are left out."""
        keep = ("key", "label", "kind", "default", "decimals")
        # Explicit numeric bounds are validation metadata. In particular,
        # min=0 must survive schema serialization or the native Qt editor
        # falls back to -1e12 and accepts invalid negative engineering inputs.
        return {k: v for k, v in asdict(self).items()
                if k in keep or (k in ("min", "max") and v is not None)
                or v not in ("", None, [], 0.0)}


@dataclass
class Group:
    """A titled set of fields."""
    title: str
    fields: List[Field]
    note: str = ""
    when: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"title": self.title, "fields": [f.to_dict() for f in self.fields]}
        if self.note:
            d["note"] = self.note
        if self.when:
            d["when"] = list(self.when)
        return d


def _num(key, label, default, lo=None, hi=None, unit="", dec=2, step=None, when=None):
    return Field(key, label, "number", default, unit, lo, hi, step, dec,
                 when=_when(when))


def _check(key, label, default=False, when=None):
    return Field(key, label, "check", default, when=_when(when))


def _select(key, label, default, options, when=None):
    return Field(key, label, "select", default,
                 options=[{"value": v, "label": t} for v, t in options], when=_when(when))


def _text(key, label, default=""):
    return Field(key, label, "text", default)


def _when(conditions) -> List[Dict[str, Any]]:
    """``[("key", ["a", "b"])]`` as the browser reads it."""
    if not conditions:
        return []
    return [{"key": key, "in": list(values)} for key, values in conditions]


def _choices(lang: str, prefix: str, values: List[str]):
    return [(value, _t(lang, f"{prefix}_{value}")) for value in values]


# --------------------------------------------------------------------------- #
#  Input groups
# --------------------------------------------------------------------------- #

def project_groups(lang: str = "en") -> List[Group]:
    info = DEFAULT_CONFIG["project_info"]
    return [Group(_t(lang, "group_project"), [
        _text("title", _t(lang, "title_label"), info["title"]),
        _text("analyst", _t(lang, "analyst_label"), info["analyst"]),
    ])]


def foundation_groups(lang: str = "en") -> List[Group]:
    f = DEFAULT_CONFIG["foundation"]
    load = DEFAULT_CONFIG["loading"]
    w = DEFAULT_CONFIG["groundwater"]
    return [
        Group(_t(lang, "group_foundation"), [
            _select("shape", _t(lang, "shape_label"), f["shape"],
                    _choices(lang, "shape", SHAPES)),
            _num("B", _t(lang, "B_label"), f["B"], 0.1, 100, "m", 2, 0.1),
            _num("L", _t(lang, "L_label"), f["L"], 0.1, 500, "m", 2, 0.1,
                 when=[("shape", ["rectangle"])]),
            _num("Df", _t(lang, "Df_label"), f["Df"], 0, 50, "m", 2, 0.1),
            _num("base_tilt", _t(lang, "tilt_label"), f["base_tilt"], 0, 45, "°", 1, 1),
            _num("ground_slope", _t(lang, "slope_label"), f["ground_slope"], 0, 45,
                 "°", 1, 1),
        ], note=_t(lang, "foundation_note")),
        Group(_t(lang, "group_loading"), [
            _num("V", _t(lang, "V_label"), load["V"], 0.1, 1e7, "kN", 1, 10),
            _num("Hb", _t(lang, "Hb_label"), load["Hb"], 0, 1e7, "kN", 1, 10),
            _num("Hl", _t(lang, "Hl_label"), load["Hl"], 0, 1e7, "kN", 1, 10,
                 when=[("shape", ["rectangle", "square", "circle"])]),
            _num("Mb", _t(lang, "Mb_label"), load["Mb"], 0, 1e8, "kN·m", 1, 10),
            _num("Ml", _t(lang, "Ml_label"), load["Ml"], 0, 1e8, "kN·m", 1, 10,
                 when=[("shape", ["rectangle", "square", "circle"])]),
            _num("variable_fraction", _t(lang, "varfrac_label"),
                 load["variable_fraction"], 0, 1, "", 2, 0.05),
        ], note=_t(lang, "loading_note")),
        Group(_t(lang, "group_water"), [
            _num("water_depth", _t(lang, "water_depth_label"), w["depth"], 0, 500,
                 "m", 2, 0.1),
            _num("gamma_water", _t(lang, "gamma_w_label"), w["gamma_water"], 9, 11,
                 "kN/m³", 2, 0.01),
        ]),
    ]


def option_groups(lang: str = "en") -> List[Group]:
    o = DEFAULT_CONFIG["options"]
    s = DEFAULT_CONFIG["seismic"]
    t = DEFAULT_CONFIG["insitu"]
    r = DEFAULT_CONFIG["rock"]
    c = DEFAULT_CONFIG["criteria"]
    return [
        Group(_t(lang, "group_options"), [
            _select("method", _t(lang, "method_label"), o["method"],
                    _choices(lang, "method", METHODS)),
            _select("analysis", _t(lang, "analysis_label"), o["analysis"],
                    _choices(lang, "analysis", ANALYSES)),
            _select("shear", _t(lang, "shear_label"), o["shear"],
                    _choices(lang, "shear", SHEAR)),
            _check("shape_factors", _t(lang, "shape_factors_label"), o["shape_factors"]),
            _check("depth_factors", _t(lang, "depth_factors_label"), o["depth_factors"]),
            _check("inclination_factors", _t(lang, "inclination_factors_label"),
                   o["inclination_factors"]),
            _check("base_factors", _t(lang, "base_factors_label"), o["base_factors"]),
            _check("ground_factors", _t(lang, "ground_factors_label"), o["ground_factors"]),
            _check("compressibility", _t(lang, "compressibility_label"),
                   o["compressibility"]),
            _check("effective_area", _t(lang, "effective_area_label"), o["effective_area"]),
        ], note=_t(lang, "options_note")),
        Group(_t(lang, "group_layers"), [
            _select("layer_model", _t(lang, "layer_model_label"), o["layer_model"],
                    _choices(lang, "layer_model", LAYER_MODELS)),
            _num("zone_factor", _t(lang, "zone_factor_label"), o["zone_factor"], 0.1, 4,
                 "", 2, 0.05),
            _select("two_layer_model", _t(lang, "two_layer_model_label"),
                    o["two_layer_model"], _choices(lang, "two_layer", TWO_LAYER_MODELS),
                    when=[("layer_model", ["two_layer"])]),
            _num("Ks", _t(lang, "Ks_label"), o["Ks"], 0, 40, "", 3, 0.05,
                 when=[("layer_model", ["two_layer"]), ("two_layer_model", ["punching"])]),
            _num("adhesion_ratio", _t(lang, "adhesion_label"), o["adhesion_ratio"], 0, 1,
                 "", 2, 0.05,
                 when=[("layer_model", ["two_layer"]), ("two_layer_model", ["punching"])]),
            _num("spread_angle", _t(lang, "spread_angle_label"), o["spread_angle"], 0, 60,
                 "°", 2, 1,
                 when=[("layer_model", ["two_layer"]), ("two_layer_model", ["spread"])]),
        ], note=_t(lang, "layers_note")),
        Group(_t(lang, "group_seismic"), [
            _check("seismic_enabled", _t(lang, "seismic_enabled_label"), s["enabled"]),
            _num("kh", _t(lang, "kh_label"), s["kh"], 0, 1, "", 3, 0.01,
                 when=[("seismic_enabled", [True])]),
            _num("kv", _t(lang, "kv_label"), s["kv"], -1, 1, "", 3, 0.01,
                 when=[("seismic_enabled", [True])]),
            _check("soil_inertia", _t(lang, "soil_inertia_label"), s["soil_inertia"],
                   when=[("seismic_enabled", [True])]),
        ], note=_t(lang, "seismic_note")),
        Group(_t(lang, "group_insitu"), [
            _check("insitu_enabled", _t(lang, "insitu_enabled_label"), t["enabled"]),
            _select("test", _t(lang, "test_label"), t["test"], _choices(lang, "test", TESTS),
                    when=[("insitu_enabled", [True])]),
            _num("N60", _t(lang, "N60_label"), t["N60"], 0, 100, "", 1, 1,
                 when=[("insitu_enabled", [True]), ("test", ["spt"])]),
            _num("qc", _t(lang, "qc_label"), t["qc"], 0, 100, "MPa", 2, 0.5,
                 when=[("insitu_enabled", [True]), ("test", ["cpt"])]),
            _num("pl", _t(lang, "pl_label"), t["pl"], 0, 20, "MPa", 3, 0.05,
                 when=[("insitu_enabled", [True]), ("test", ["pmt"])]),
            _num("p0", _t(lang, "p0_label"), t["p0"], 0, 20, "MPa", 3, 0.01,
                 when=[("insitu_enabled", [True]), ("test", ["pmt"])]),
            _select("category", _t(lang, "category_label"), t["category"],
                    _choices(lang, "category", PMT_CATEGORIES),
                    when=[("insitu_enabled", [True]), ("test", ["pmt"])]),
            _num("settlement", _t(lang, "settlement_label"), t["settlement"], 1, 200,
                 "mm", 1, 5, when=[("insitu_enabled", [True]), ("test", ["spt", "cpt"])]),
        ], note=_t(lang, "insitu_note")),
        Group(_t(lang, "group_rock"), [
            _check("rock_enabled", _t(lang, "rock_enabled_label"), r["enabled"]),
            _select("rock_method", _t(lang, "rock_method_label"), r["method"],
                    _choices(lang, "rock_method", ROCK_METHODS),
                    when=[("rock_enabled", [True])]),
            _num("sigma_ci", _t(lang, "sigma_ci_label"), r["sigma_ci"], 0.1, 400, "MPa",
                 1, 5, when=[("rock_enabled", [True])]),
            _num("GSI", _t(lang, "GSI_label"), r["GSI"], 5, 100, "", 1, 5,
                 when=[("rock_enabled", [True]), ("rock_method", ["hoek_brown"])]),
            _num("mi", _t(lang, "mi_label"), r["mi"], 1, 40, "", 1, 1,
                 when=[("rock_enabled", [True]), ("rock_method", ["hoek_brown"])]),
            _num("rock_D", _t(lang, "rock_D_label"), r["D"], 0, 1, "", 2, 0.1,
                 when=[("rock_enabled", [True]), ("rock_method", ["hoek_brown"])]),
            _num("gamma_rock", _t(lang, "gamma_rock_label"), r["gamma_rock"], 10, 35,
                 "kN/m³", 1, 0.5,
                 when=[("rock_enabled", [True]), ("rock_method", ["hoek_brown"])]),
            _num("spacing", _t(lang, "spacing_label"), r["spacing"], 0.01, 10, "m", 2, 0.1,
                 when=[("rock_enabled", [True]), ("rock_method", ["ksp"])]),
            _num("aperture", _t(lang, "aperture_label"), r["aperture"], 0, 50, "mm", 2,
                 0.5, when=[("rock_enabled", [True]), ("rock_method", ["ksp"])]),
        ], note=_t(lang, "rock_note")),
        Group(_t(lang, "group_criteria"), [
            _select("approach", _t(lang, "approach_label"), c["approach"],
                    _choices(lang, "approach", APPROACHES)),
            _num("FS", _t(lang, "FS_label"), c["FS"], 1, 10, "", 2, 0.1),
            _num("FS_sliding", _t(lang, "FS_sliding_label"), c["FS_sliding"], 1, 10,
                 "", 2, 0.1),
            _num("ecc_limit", _t(lang, "ecc_limit_label"), c["ecc_limit"], 2, 20, "", 1, 1),
            _num("delta_ratio", _t(lang, "delta_ratio_label"), o["delta_ratio"], 0, 1,
                 "", 2, 0.05),
        ], note=_t(lang, "criteria_note")),
    ]


def study_groups(lang: str = "en") -> List[Group]:
    from .study import METHODS as SAMPLING
    return [Group(_t(lang, "group_study"), [
        _select("study_method", _t(lang, "study_method"), "lhs",
                [(m, _t(lang, f"sampling_{m}")) for m in SAMPLING]),
        _num("study_n", _t(lang, "study_n"), 300, 3, 100000, "", 0, 50),
        _num("study_seed", _t(lang, "study_seed"), 0, 0, 10 ** 6, "", 0, 1),
    ], note=_t(lang, "study_note"))]


# --------------------------------------------------------------------------- #
#  Tables: soil layers, study variables
# --------------------------------------------------------------------------- #

SOIL_NUMBERS = ["thickness", "gamma", "gamma_sat", "c", "phi", "cu", "E", "nu"]

#: Columns that mean nothing in a granular layer, which the table greys out
CLAY_ONLY = ["cu"]


def soil_columns(lang: str = "en") -> List[dict]:
    """Columns of the soil profile table."""
    def number(key):
        return {"key": key, "label": _t(lang, f"col_{key}"), "kind": "number"}

    return ([{"key": "name", "label": _t(lang, "col_name"), "kind": "text"},
             number("thickness"),
             {"key": "behaviour", "label": _t(lang, "col_behaviour"), "kind": "select",
              "options": [{"value": v, "label": _t(lang, f"behaviour_{v}")}
                          for v in BEHAVIOURS]}]
            + [number(key) for key in SOIL_NUMBERS[1:]])


def study_columns(lang: str = "en") -> List[dict]:
    """Columns of the study variable table."""
    from .study import DISTRIBUTIONS
    return [
        {"key": "path", "label": _t(lang, "col_param"), "kind": "select", "options": []},
        {"key": "mode", "label": _t(lang, "col_mode"), "kind": "select",
         "options": [{"value": "range", "label": _t(lang, "mode_range")},
                     {"value": "dist", "label": _t(lang, "mode_dist")}]},
        {"key": "min", "label": _t(lang, "col_min"), "kind": "number"},
        {"key": "max", "label": _t(lang, "col_max"), "kind": "number"},
        {"key": "dist", "label": _t(lang, "col_dist"), "kind": "select",
         "options": [{"value": d, "label": _t(lang, f"dist_{d}")} for d in DISTRIBUTIONS]},
        {"key": "mean", "label": _t(lang, "col_mean"), "kind": "number"},
        {"key": "cov", "label": _t(lang, "col_cov"), "kind": "number"},
        {"key": "n_points", "label": _t(lang, "col_points"), "kind": "number"},
    ]


def default_soil_rows() -> List[dict]:
    return [dict(layer) for layer in DEFAULT_CONFIG["soil_profile"]]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #

def schema(lang: str = "en") -> dict:
    """The whole schema the browser builds its forms from, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "foundation": {"groups": [g.to_dict() for g in foundation_groups(lang)]},
        "options": {"groups": [g.to_dict() for g in option_groups(lang)]},
        "study": {"groups": [g.to_dict() for g in study_groups(lang)]},
        "soil": {"columns": soil_columns(lang), "rows": default_soil_rows(),
                 "note": _t(lang, "soil_note"), "clay_only": list(CLAY_ONLY)},
        "study_vars": {"columns": study_columns(lang)},
    }


def _all_groups(lang: str = "en") -> List[Group]:
    return (project_groups(lang) + foundation_groups(lang) + option_groups(lang)
            + study_groups(lang))


def defaults(lang: str = "en") -> Dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: Dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    values["soil_profile"] = default_soil_rows()
    values["study_variables"] = []
    return values


# --------------------------------------------------------------------------- #
#  Readers: flat values <-> configuration dictionary
# --------------------------------------------------------------------------- #

def _f(values: dict, key: str, default: float = 0.0) -> float:
    """A numeric field; missing or empty falls back to the default."""
    v = values.get(key, default)
    if v is None or v == "":
        return float(default)
    return float(v)


def _b(values: dict, key: str, default: bool = False) -> bool:
    v = values.get(key, default)
    return bool(default if v is None or v == "" else v)


def _s(values: dict, key: str, default: str = "", allowed: Optional[List[str]] = None) -> str:
    v = values.get(key, default)
    text = str(default if v is None or v == "" else v)
    return text if allowed is None or text in allowed else default


def read_soil_profile(values: dict) -> List[dict]:
    """Soil layers from the table; rows without a usable thickness are dropped."""
    base = DEFAULT_CONFIG["soil_profile"][0]
    layers = []
    for row in values.get("soil_profile") or []:
        try:
            thickness = float(row.get("thickness"))
        except (TypeError, ValueError):
            continue
        if thickness <= 0:
            continue
        layer = {"name": str(row.get("name") or "").strip() or "Layer",
                 "behaviour": _s(row, "behaviour", "granular", BEHAVIOURS)}
        for key in SOIL_NUMBERS:
            layer[key] = _f(row, key, base[key])
        layer["thickness"] = thickness
        layers.append(layer)
    return layers


def to_config(values: dict) -> Dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    d = DEFAULT_CONFIG
    cfg["project_info"] = {"title": _s(values, "title", d["project_info"]["title"]),
                           "analyst": str(values.get("analyst") or "")}
    cfg["foundation"] = {
        "shape": _s(values, "shape", d["foundation"]["shape"], SHAPES),
        "B": _f(values, "B", d["foundation"]["B"]),
        "L": _f(values, "L", d["foundation"]["L"]),
        "Df": _f(values, "Df", d["foundation"]["Df"]),
        "base_tilt": _f(values, "base_tilt", d["foundation"]["base_tilt"]),
        "ground_slope": _f(values, "ground_slope", d["foundation"]["ground_slope"]),
    }
    cfg["loading"] = {key: _f(values, key, d["loading"][key]) for key in d["loading"]}
    cfg["groundwater"] = {"depth": _f(values, "water_depth", d["groundwater"]["depth"]),
                          "gamma_water": _f(values, "gamma_water",
                                            d["groundwater"]["gamma_water"])}
    cfg["soil_profile"] = read_soil_profile(values)
    o = d["options"]
    cfg["options"] = {
        "method": _s(values, "method", o["method"], METHODS),
        "analysis": _s(values, "analysis", o["analysis"], ANALYSES),
        "shear": _s(values, "shear", o["shear"], SHEAR),
        "shape_factors": _b(values, "shape_factors", o["shape_factors"]),
        "depth_factors": _b(values, "depth_factors", o["depth_factors"]),
        "inclination_factors": _b(values, "inclination_factors", o["inclination_factors"]),
        "base_factors": _b(values, "base_factors", o["base_factors"]),
        "ground_factors": _b(values, "ground_factors", o["ground_factors"]),
        "compressibility": _b(values, "compressibility", o["compressibility"]),
        "effective_area": _b(values, "effective_area", o["effective_area"]),
        "layer_model": _s(values, "layer_model", o["layer_model"], LAYER_MODELS),
        "zone_factor": _f(values, "zone_factor", o["zone_factor"]),
        "two_layer_model": _s(values, "two_layer_model", o["two_layer_model"],
                              TWO_LAYER_MODELS),
        "Ks": _f(values, "Ks", o["Ks"]),
        "adhesion_ratio": _f(values, "adhesion_ratio", o["adhesion_ratio"]),
        "spread_angle": _f(values, "spread_angle", o["spread_angle"]),
        "delta_ratio": _f(values, "delta_ratio", o["delta_ratio"]),
    }
    s = d["seismic"]
    cfg["seismic"] = {"enabled": _b(values, "seismic_enabled", s["enabled"]),
                      "kh": _f(values, "kh", s["kh"]), "kv": _f(values, "kv", s["kv"]),
                      "soil_inertia": _b(values, "soil_inertia", s["soil_inertia"])}
    t = d["insitu"]
    cfg["insitu"] = {
        "enabled": _b(values, "insitu_enabled", t["enabled"]),
        "test": _s(values, "test", t["test"], TESTS),
        "N60": _f(values, "N60", t["N60"]), "qc": _f(values, "qc", t["qc"]),
        "pl": _f(values, "pl", t["pl"]), "p0": _f(values, "p0", t["p0"]),
        "category": _s(values, "category", t["category"], PMT_CATEGORIES),
        "settlement": _f(values, "settlement", t["settlement"]),
    }
    r = d["rock"]
    cfg["rock"] = {
        "enabled": _b(values, "rock_enabled", r["enabled"]),
        "method": _s(values, "rock_method", r["method"], ROCK_METHODS),
        "sigma_ci": _f(values, "sigma_ci", r["sigma_ci"]),
        "GSI": _f(values, "GSI", r["GSI"]), "mi": _f(values, "mi", r["mi"]),
        "D": _f(values, "rock_D", r["D"]),
        "gamma_rock": _f(values, "gamma_rock", r["gamma_rock"]),
        "spacing": _f(values, "spacing", r["spacing"]),
        "aperture": _f(values, "aperture", r["aperture"]),
    }
    cfg["criteria"] = {
        "approach": _s(values, "approach", d["criteria"]["approach"], APPROACHES),
        "FS": _f(values, "FS", d["criteria"]["FS"]),
        "FS_sliding": _f(values, "FS_sliding", d["criteria"]["FS_sliding"]),
        "ecc_limit": _f(values, "ecc_limit", d["criteria"]["ecc_limit"]),
    }
    return cfg


#: Flat key <- (section, key) of the configuration
_MAP = [("title", "project_info", "title"), ("analyst", "project_info", "analyst")] + \
    [(k, "foundation", k) for k in DEFAULT_CONFIG["foundation"]] + \
    [(k, "loading", k) for k in DEFAULT_CONFIG["loading"]] + \
    [("water_depth", "groundwater", "depth"), ("gamma_water", "groundwater", "gamma_water")] + \
    [(k, "options", k) for k in DEFAULT_CONFIG["options"]] + \
    [("seismic_enabled", "seismic", "enabled"), ("kh", "seismic", "kh"),
     ("kv", "seismic", "kv"), ("soil_inertia", "seismic", "soil_inertia")] + \
    [("insitu_enabled", "insitu", "enabled"), ("test", "insitu", "test"),
     ("N60", "insitu", "N60"), ("qc", "insitu", "qc"), ("pl", "insitu", "pl"),
     ("p0", "insitu", "p0"), ("category", "insitu", "category"),
     ("settlement", "insitu", "settlement")] + \
    [("rock_enabled", "rock", "enabled"), ("rock_method", "rock", "method"),
     ("sigma_ci", "rock", "sigma_ci"), ("GSI", "rock", "GSI"), ("mi", "rock", "mi"),
     ("rock_D", "rock", "D"), ("gamma_rock", "rock", "gamma_rock"),
     ("spacing", "rock", "spacing"), ("aperture", "rock", "aperture")] + \
    [(k, "criteria", k) for k in DEFAULT_CONFIG["criteria"]]


def from_config(cfg: dict, base: Optional[dict] = None) -> Dict[str, Any]:
    """Flat values from a nested configuration — reads a `.bearing` project file.

    Whatever the file does not carry keeps its default.
    """
    values = dict(base) if base is not None else defaults()
    for flat, section, key in _MAP:
        if key in (cfg.get(section) or {}):
            values[flat] = cfg[section][key]
    if cfg.get("soil_profile"):
        layer_defaults = DEFAULT_CONFIG["soil_profile"][0]
        values["soil_profile"] = [{**layer_defaults, **layer} for layer in cfg["soil_profile"]
                                  if isinstance(layer, dict)]
    study = cfg.get("study") or {}
    for src, dst in (("method", "study_method"), ("n", "study_n"), ("seed", "study_seed")):
        if src in study:
            values[dst] = study[src]
    if "variables" in study:
        values["study_variables"] = [dict(spec) for spec in study["variables"]]
    return values


def study_spec(values: dict) -> Dict[str, Any]:
    """The study block of a project file: options plus the variable table."""
    from .study import METHODS as SAMPLING
    return {
        "method": _s(values, "study_method", "lhs", SAMPLING),
        "n": int(_f(values, "study_n", 300)),
        "seed": int(_f(values, "study_seed", 0)),
        "variables": [dict(spec) for spec in values.get("study_variables") or []],
    }


def project_file(values: dict) -> Dict[str, Any]:
    """What `Save` writes: the configuration plus the study definition."""
    cfg = to_config(values)
    return {"format": FILE_FORMAT, "version": FILE_VERSION, **cfg, "study": study_spec(values)}


def study_variables(values: dict):
    """The study variables as `study.StudyVariable` objects."""
    from .study import StudyVariable
    return [StudyVariable.from_dict(spec) for spec in values.get("study_variables") or []]


def variable_choices(values: dict, lang: str = "en") -> List[dict]:
    """Every input a study may vary, with a readable label and its project value."""
    from .study import available_variables, get_value, pretty_label
    cfg = to_config(values)
    L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    out = []
    for path, _ in available_variables(cfg):
        try:
            base = float(get_value(cfg, path))
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        out.append({"value": path, "label": pretty_label(cfg, path, L), "base": base})
    return out
