"""
Input schema and readers for SlipSurface IQ Wall.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The browser builds its forms from this schema, and the
server turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``H``, ``gamma_b``, ``key_depth`` …) are the ones the
interface uses; the nested keys of the configuration (``geometry.H``,
``soils.backfill.gamma``, ``key.depth`` …) are the ones the engine and the
``.lwall`` project files use. `to_config()` and `from_config()` convert
between the two.

A field can declare when it applies — ``when=[("seismic_enabled", [True])]``
— and the browser hides it whenever the condition does not hold, so the form
shows the inputs of the method that is actually running and no others.

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .concrete import BARS
from .config import (
    BEARING_METHODS,
    DEFAULT_CONFIG,
    GRADES,
    MOBILITY,
    PASSIVE_METHODS,
    PRESSURE_METHODS,
    SEISMIC_METHODS,
    SITE_CLASSES,
    STEELS,
    TAPERS,
)
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "slipsurface-wall"
# Project files saved before the product was renamed still open.
READ_FORMATS = (FILE_FORMAT, "slipsurface-wall")
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
        return {k: v for k, v in asdict(self).items()
                if k in keep or v not in ("", None, [], 0.0)}


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
    return Field(key, label, "number", default, unit, lo, hi, step, dec, when=_when(when))


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


def _bar_choices(lang: str):
    return [("0", _t(lang, "bar_auto"))] + [(str(b), f"Ø{b}") for b in BARS if b >= 10]


# --------------------------------------------------------------------------- #
#  Input groups
# --------------------------------------------------------------------------- #

def project_groups(lang: str = "en") -> List[Group]:
    info = DEFAULT_CONFIG["project_info"]
    return [Group(_t(lang, "group_project"), [
        _text("title", _t(lang, "title_label"), info["title"]),
        _text("analyst", _t(lang, "analyst_label"), info["analyst"]),
    ])]


def wall_groups(lang: str = "en") -> List[Group]:
    g = DEFAULT_CONFIG["geometry"]
    k = DEFAULT_CONFIG["key"]
    q = DEFAULT_CONFIG["loads"]
    s = DEFAULT_CONFIG["soils"]
    key_on = [("key_enabled", [True])]
    return [
        Group(_t(lang, "group_geometry"), [
            _num("H", _t(lang, "H_label"), g["H"], 1.0, 20, "m", 2, 0.25),
            _num("t_top", _t(lang, "t_top_label"), g["t_top"], 0.15, 3, "m", 2, 0.05),
            _num("t_bot", _t(lang, "t_bot_label"), g["t_bot"], 0.15, 5, "m", 2, 0.05),
            _select("taper", _t(lang, "taper_label"), g["taper"],
                    _choices(lang, "taper", TAPERS)),
            _num("toe", _t(lang, "toe_label"), g["toe"], 0, 20, "m", 2, 0.05),
            _num("heel", _t(lang, "heel_label"), g["heel"], 0, 40, "m", 2, 0.05),
            _num("t_f", _t(lang, "t_f_label"), g["t_f"], 0.2, 5, "m", 2, 0.05),
            _num("D", _t(lang, "D_label"), g["D"], 0, 10, "m", 2, 0.05),
            _num("backslope", _t(lang, "backslope_label"), g["backslope"], 0, 45, "°", 1, 1),
            _num("toe_slope", _t(lang, "toe_slope_label"), g["toe_slope"], 0, 44, "°", 1, 1),
        ], note=_t(lang, "geometry_note")),
        Group(_t(lang, "group_key"), [
            _check("key_enabled", _t(lang, "key_enabled_label"), k["enabled"]),
            _num("key_depth", _t(lang, "key_depth_label"), k["depth"], 0.1, 5, "m", 2, 0.05,
                 when=key_on),
            _num("key_width", _t(lang, "key_width_label"), k["width"], 0.1, 5, "m", 2, 0.05,
                 when=key_on),
            _num("key_offset", _t(lang, "key_offset_label"), k["offset"], 0, 40, "m", 2, 0.05,
                 when=key_on),
        ], note=_t(lang, "key_note")),
        Group(_t(lang, "group_loads"), [
            _num("q_dead", _t(lang, "q_dead_label"), q["q_dead"], 0, 1000, "kPa", 1, 1),
            _num("q_live", _t(lang, "q_live_label"), q["q_live"], 0, 1000, "kPa", 1, 1),
            _num("P_top", _t(lang, "P_top_label"), q["P_top"], 0, 1e4, "kN/m", 1, 1),
            _num("H_top", _t(lang, "H_top_label"), q["H_top"], 0, 1e4, "kN/m", 1, 1),
        ], note=_t(lang, "loads_note")),
        Group(_t(lang, "group_backfill"), [
            _num("gamma_b", _t(lang, "gamma_label"), s["backfill"]["gamma"], 10, 26,
                 "kN/m³", 1, 0.5),
            _num("gamma_sat_b", _t(lang, "gamma_sat_label"), s["backfill"]["gamma_sat"], 10, 26,
                 "kN/m³", 1, 0.5),
            _num("phi_b", _t(lang, "phi_label"), s["backfill"]["phi"], 10, 50, "°", 1, 1),
            _num("c_b", _t(lang, "c_label"), s["backfill"]["c"], 0, 200, "kPa", 1, 1),
        ], note=_t(lang, "backfill_note")),
        Group(_t(lang, "group_foundation"), [
            _num("gamma_f", _t(lang, "gamma_label"), s["foundation"]["gamma"], 10, 26,
                 "kN/m³", 1, 0.5),
            _num("gamma_sat_f", _t(lang, "gamma_sat_label"), s["foundation"]["gamma_sat"],
                 10, 26, "kN/m³", 1, 0.5),
            _num("phi_f", _t(lang, "phi_label"), s["foundation"]["phi"], 0, 50, "°", 1, 1),
            _num("c_f", _t(lang, "c_label"), s["foundation"]["c"], 0, 1000, "kPa", 1, 1),
        ], note=_t(lang, "foundation_note")),
        Group(_t(lang, "group_water"), [
            _num("water_back", _t(lang, "water_back_label"), s["water_back"], 0, 20, "m", 2,
                 0.1),
            _num("water_front", _t(lang, "water_front_label"), s["water_front"], 0, 20, "m", 2,
                 0.1),
            _num("water_depth", _t(lang, "water_depth_label"), s["water_depth"], 0, 500, "m",
                 2, 0.5),
            _num("gamma_water", _t(lang, "gamma_water_label"), s["gamma_water"], 9, 11,
                 "kN/m³", 2, 0.01),
        ], note=_t(lang, "water_note")),
    ]


def option_groups(lang: str = "en") -> List[Group]:
    e = DEFAULT_CONFIG["earth"]
    o = DEFAULT_CONFIG["options"]
    k = DEFAULT_CONFIG["criteria"]
    s = DEFAULT_CONFIG["seismic"]
    quake = [("seismic_enabled", [True])]
    return [
        Group(_t(lang, "group_earth"), [
            _select("method", _t(lang, "method_label"), e["method"],
                    _choices(lang, "pm", PRESSURE_METHODS)),
            _num("delta_ratio", _t(lang, "delta_ratio_label"), e["delta_ratio"], 0, 1, "", 2,
                 0.05, when=[("method", ["coulomb", "trial_wedge"])]),
            _num("OCR", _t(lang, "OCR_label"), e["OCR"], 1, 20, "", 2, 0.1,
                 when=[("method", ["at_rest"])]),
            _check("passive", _t(lang, "passive_label"), e["passive"]),
            _select("passive_method", _t(lang, "passive_method_label"), e["passive_method"],
                    _choices(lang, "pp", PASSIVE_METHODS), when=[("passive", [True])]),
            _num("passive_ratio", _t(lang, "passive_ratio_label"), e["passive_ratio"], 0, 1,
                 "", 2, 0.05),
        ], note=_t(lang, "earth_note")),
        Group(_t(lang, "group_stability"), [
            _num("base_friction", _t(lang, "base_friction_label"), o["base_friction"], 0.1, 1,
                 "", 2, 0.05),
            _num("base_adhesion", _t(lang, "base_adhesion_label"), o["base_adhesion"], 0, 1,
                 "", 2, 0.05),
            _select("bearing_method", _t(lang, "bearing_method_label"), o["bearing_method"],
                    _choices(lang, "method", BEARING_METHODS)),
            _check("bearing_embedment", _t(lang, "bearing_embedment_label"),
                   o["bearing_embedment"]),
            _check("bearing_inclination", _t(lang, "bearing_inclination_label"),
                   o["bearing_inclination"]),
            _check("bearing_depth", _t(lang, "bearing_depth_label"), o["bearing_depth"]),
            _num("q_allow", _t(lang, "q_allow_label"), o["q_allow"], 0, 1e4, "kPa", 0, 10),
            _check("global_enabled", _t(lang, "global_enabled_label"), o["global_enabled"]),
        ], note=_t(lang, "stability_note")),
        Group(_t(lang, "group_criteria"), [
            _num("FS_sliding", _t(lang, "FS_sliding_label"), k["FS_sliding"], 1, 5, "", 2, 0.1),
            _num("FS_overturning", _t(lang, "FS_overturning_label"), k["FS_overturning"], 1, 5,
                 "", 2, 0.1),
            _num("ecc_static", _t(lang, "ecc_label"), k["ecc_static"], 2, 20, "", 1, 1),
            _num("FS_bearing", _t(lang, "FS_bearing_label"), k["FS_bearing"], 1, 6, "", 2, 0.1),
            _num("FS_global", _t(lang, "FS_global_label"), k["FS_global"], 1, 3, "", 2, 0.05),
        ], note=_t(lang, "criteria_note")),
        Group(_t(lang, "group_seismic"), [
            _check("seismic_enabled", _t(lang, "seismic_enabled_label"), s["enabled"]),
            _num("Ss", _t(lang, "Ss_label"), s["Ss"], 0, 5, "g", 3, 0.01, when=quake),
            _num("S1", _t(lang, "S1_label"), s["S1"], 0, 3, "g", 3, 0.01, when=quake),
            _select("site", _t(lang, "site_label"), s["site"],
                    _choices(lang, "site", SITE_CLASSES), when=quake),
            _select("mobility", _t(lang, "mobility_label"), s["mobility"],
                    _choices(lang, "mob", list(MOBILITY)), when=quake),
            _num("kh_manual", _t(lang, "kh_manual_label"), s["kh_manual"], 0, 0.99, "", 3,
                 0.01, when=quake),
            _num("kv_ratio", _t(lang, "kv_ratio_label"), s["kv_ratio"], 0, 1, "", 2, 0.05,
                 when=quake),
            _select("seismic_method", _t(lang, "seismic_method_label"), s["method"],
                    _choices(lang, "sm", SEISMIC_METHODS), when=quake),
            _num("dyn_height", _t(lang, "dyn_height_label"), s["dyn_height"], 0.34, 0.66, "",
                 2, 0.05, when=quake),
            _num("psi_live", _t(lang, "psi_live_label"), s["psi_live"], 0, 1, "", 2, 0.05,
                 when=quake),
        ], note=_t(lang, "seismic_note")),
        Group(_t(lang, "group_criteria_seis"), [
            _num("FS_sliding_seis", _t(lang, "FS_sliding_label"), k["FS_sliding_seis"], 1, 5,
                 "", 2, 0.05),
            _num("FS_overturning_seis", _t(lang, "FS_overturning_label"),
                 k["FS_overturning_seis"], 1, 5, "", 2, 0.05),
            _num("ecc_seismic", _t(lang, "ecc_label"), k["ecc_seismic"], 2, 20, "", 1, 1),
            _num("FS_bearing_seis", _t(lang, "FS_bearing_label"), k["FS_bearing_seis"], 1, 6,
                 "", 2, 0.05),
            _num("FS_global_seis", _t(lang, "FS_global_label"), k["FS_global_seis"], 1, 3, "",
                 2, 0.05),
        ], note=_t(lang, "criteria_seis_note"), when=_when(quake)),
    ]


def concrete_groups(lang: str = "en") -> List[Group]:
    c = DEFAULT_CONFIG["concrete"]
    s = DEFAULT_CONFIG["soils"]
    return [Group(_t(lang, "group_concrete"), [
        _select("grade", _t(lang, "grade_label"), c["grade"], [(g, g) for g in GRADES]),
        _select("steel", _t(lang, "steel_label"), c["steel"], [(g, g) for g in STEELS]),
        _num("gamma_concrete", _t(lang, "gamma_concrete_label"), s["gamma_concrete"], 20, 27,
             "kN/m³", 1, 0.5),
        _num("cover_stem", _t(lang, "cover_stem_label"), c["cover_stem"], 20, 100, "mm", 0, 5),
        _num("cover_footing", _t(lang, "cover_footing_label"), c["cover_footing"], 20, 100,
             "mm", 0, 5),
        _select("bar_stem", _t(lang, "bar_stem_label"), str(c["bar_stem"]),
                _bar_choices(lang)),
        _select("bar_footing", _t(lang, "bar_footing_label"), str(c["bar_footing"]),
                _bar_choices(lang)),
        _num("rho_min", _t(lang, "rho_min_label"), c["rho_min"], 0, 0.02, "", 4, 0.0005),
        _num("rho_front", _t(lang, "rho_front_label"), c["rho_front"], 0, 0.02, "", 4, 0.0005),
        _num("rho_dist", _t(lang, "rho_dist_label"), c["rho_dist"], 0, 0.02, "", 4, 0.0005),
        _check("curtail", _t(lang, "curtail_label"), c["curtail"]),
    ], note=_t(lang, "concrete_note"))]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #

def schema(lang: str = "en") -> dict:
    """The whole schema the browser builds its forms from, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "wall": {"groups": [g.to_dict() for g in wall_groups(lang)]},
        "options": {"groups": [g.to_dict() for g in option_groups(lang)]},
        "concrete": {"groups": [g.to_dict() for g in concrete_groups(lang)]},
    }


def _all_groups(lang: str = "en") -> List[Group]:
    return (project_groups(lang) + wall_groups(lang) + option_groups(lang)
            + concrete_groups(lang))


def defaults(lang: str = "en") -> Dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: Dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    return values


# --------------------------------------------------------------------------- #
#  Readers: flat values <-> configuration dictionary
# --------------------------------------------------------------------------- #

def _f(values: dict, key: str, default: float = 0.0) -> float:
    """A numeric field; missing or empty falls back to the default."""
    v = values.get(key, default)
    if v is None or v == "":
        return float(default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _b(values: dict, key: str, default: bool = False) -> bool:
    v = values.get(key, default)
    return bool(default if v is None or v == "" else v)


def _s(values: dict, key: str, default: str = "", allowed: Optional[List[str]] = None) -> str:
    v = values.get(key, default)
    text = str(default if v is None or v == "" else v)
    return text if allowed is None or text in allowed else default


def _bar(values: dict, key: str, default: int = 0) -> int:
    bar = int(round(_f(values, key, default)))
    return bar if bar in BARS else 0


#: Flat key <- (path of the configuration)
_MAP = ([("title", ("project_info", "title")), ("analyst", ("project_info", "analyst"))]
        + [(k, ("geometry", k)) for k in DEFAULT_CONFIG["geometry"]]
        + [(f"key_{k}", ("key", k)) for k in DEFAULT_CONFIG["key"]]
        + [(k, ("loads", k)) for k in DEFAULT_CONFIG["loads"]]
        + [("gamma_b", ("soils", "backfill", "gamma")),
           ("gamma_sat_b", ("soils", "backfill", "gamma_sat")),
           ("phi_b", ("soils", "backfill", "phi")), ("c_b", ("soils", "backfill", "c")),
           ("gamma_f", ("soils", "foundation", "gamma")),
           ("gamma_sat_f", ("soils", "foundation", "gamma_sat")),
           ("phi_f", ("soils", "foundation", "phi")), ("c_f", ("soils", "foundation", "c")),
           ("water_back", ("soils", "water_back")), ("water_front", ("soils", "water_front")),
           ("water_depth", ("soils", "water_depth")), ("gamma_water", ("soils", "gamma_water")),
           ("gamma_concrete", ("soils", "gamma_concrete"))]
        + [(k, ("earth", k)) for k in DEFAULT_CONFIG["earth"]]
        + [(k, ("options", k)) for k in DEFAULT_CONFIG["options"]]
        + [(k, ("criteria", k)) for k in DEFAULT_CONFIG["criteria"]]
        + [("seismic_enabled", ("seismic", "enabled")), ("seismic_method", ("seismic", "method"))]
        + [(k, ("seismic", k)) for k in DEFAULT_CONFIG["seismic"]
           if k not in ("enabled", "method")]
        + [(k, ("concrete", k)) for k in DEFAULT_CONFIG["concrete"]])


def to_config(values: dict) -> Dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    d = DEFAULT_CONFIG
    cfg = copy.deepcopy(d)
    cfg["project_info"] = {"title": _s(values, "title", d["project_info"]["title"]),
                           "analyst": str(values.get("analyst") or "")}
    g = d["geometry"]
    cfg["geometry"] = {k: _f(values, k, g[k]) for k in g if k != "taper"}
    cfg["geometry"]["taper"] = _s(values, "taper", g["taper"], TAPERS)
    k = d["key"]
    cfg["key"] = {"enabled": _b(values, "key_enabled", k["enabled"]),
                  "depth": _f(values, "key_depth", k["depth"]),
                  "width": _f(values, "key_width", k["width"]),
                  "offset": _f(values, "key_offset", k["offset"])}
    cfg["loads"] = {key: _f(values, key, d["loads"][key]) for key in d["loads"]}
    s = d["soils"]
    cfg["soils"] = {
        "backfill": {"gamma": _f(values, "gamma_b", s["backfill"]["gamma"]),
                     "gamma_sat": _f(values, "gamma_sat_b", s["backfill"]["gamma_sat"]),
                     "phi": _f(values, "phi_b", s["backfill"]["phi"]),
                     "c": _f(values, "c_b", s["backfill"]["c"])},
        "foundation": {"gamma": _f(values, "gamma_f", s["foundation"]["gamma"]),
                       "gamma_sat": _f(values, "gamma_sat_f", s["foundation"]["gamma_sat"]),
                       "phi": _f(values, "phi_f", s["foundation"]["phi"]),
                       "c": _f(values, "c_f", s["foundation"]["c"])},
        "water_back": _f(values, "water_back", s["water_back"]),
        "water_front": _f(values, "water_front", s["water_front"]),
        "water_depth": _f(values, "water_depth", s["water_depth"]),
        "gamma_water": _f(values, "gamma_water", s["gamma_water"]),
        "gamma_concrete": _f(values, "gamma_concrete", s["gamma_concrete"]),
    }
    e = d["earth"]
    cfg["earth"] = {"method": _s(values, "method", e["method"], PRESSURE_METHODS),
                    "delta_ratio": _f(values, "delta_ratio", e["delta_ratio"]),
                    "OCR": _f(values, "OCR", e["OCR"]),
                    "passive": _b(values, "passive", e["passive"]),
                    "passive_method": _s(values, "passive_method", e["passive_method"],
                                         PASSIVE_METHODS),
                    "passive_ratio": _f(values, "passive_ratio", e["passive_ratio"])}
    o = d["options"]
    cfg["options"] = {
        "bearing_method": _s(values, "bearing_method", o["bearing_method"], BEARING_METHODS),
        "bearing_embedment": _b(values, "bearing_embedment", o["bearing_embedment"]),
        "bearing_inclination": _b(values, "bearing_inclination", o["bearing_inclination"]),
        "bearing_depth": _b(values, "bearing_depth", o["bearing_depth"]),
        "base_friction": _f(values, "base_friction", o["base_friction"]),
        "base_adhesion": _f(values, "base_adhesion", o["base_adhesion"]),
        "q_allow": _f(values, "q_allow", o["q_allow"]),
        "global_enabled": _b(values, "global_enabled", o["global_enabled"]),
    }
    cfg["criteria"] = {key: _f(values, key, d["criteria"][key]) for key in d["criteria"]}
    q = d["seismic"]
    cfg["seismic"] = {
        "enabled": _b(values, "seismic_enabled", q["enabled"]),
        "Ss": _f(values, "Ss", q["Ss"]), "S1": _f(values, "S1", q["S1"]),
        "site": _s(values, "site", q["site"], SITE_CLASSES),
        "mobility": _s(values, "mobility", q["mobility"], list(MOBILITY)),
        "kh_manual": _f(values, "kh_manual", q["kh_manual"]),
        "kv_ratio": _f(values, "kv_ratio", q["kv_ratio"]),
        "method": _s(values, "seismic_method", q["method"], SEISMIC_METHODS),
        "dyn_height": _f(values, "dyn_height", q["dyn_height"]),
        "psi_live": _f(values, "psi_live", q["psi_live"]),
    }
    c = d["concrete"]
    cfg["concrete"] = {
        "grade": _s(values, "grade", c["grade"], list(GRADES)),
        "steel": _s(values, "steel", c["steel"], list(STEELS)),
        "cover_stem": _f(values, "cover_stem", c["cover_stem"]),
        "cover_footing": _f(values, "cover_footing", c["cover_footing"]),
        "bar_stem": _bar(values, "bar_stem", c["bar_stem"]),
        "bar_footing": _bar(values, "bar_footing", c["bar_footing"]),
        "rho_min": _f(values, "rho_min", c["rho_min"]),
        "rho_front": _f(values, "rho_front", c["rho_front"]),
        "rho_dist": _f(values, "rho_dist", c["rho_dist"]),
        "curtail": _b(values, "curtail", c["curtail"]),
    }
    return cfg


def _lookup(cfg: dict, path):
    node = cfg
    for key in path:
        if not isinstance(node, dict) or key not in node:
            raise KeyError(key)
        node = node[key]
    return node


def from_config(cfg: dict, base: Optional[dict] = None) -> Dict[str, Any]:
    """Flat values from a nested configuration — reads a `.lwall` project file.

    Whatever the file does not carry keeps its default.
    """
    values = dict(base) if base is not None else defaults()
    for flat, path in _MAP:
        try:
            value = _lookup(cfg, path)
        except KeyError:
            continue
        if flat in ("bar_stem", "bar_footing"):
            value = str(int(value or 0))
        values[flat] = value
    return values


def project_file(values: dict) -> Dict[str, Any]:
    """What `Save` writes: the configuration, with a format stamp."""
    return {"format": FILE_FORMAT, "version": FILE_VERSION, **to_config(values)}
