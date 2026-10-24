"""
Input schema and readers for SlipSurface IQ Liquefaction.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The browser builds its forms from this schema, and the
server turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``magnitude``, ``water_depth``, ``energy`` …) are the ones
the interface uses; the nested keys of the configuration
(``earthquake.magnitude``, ``groundwater.depth`` …) are the ones the engine and
the ``.liq`` project files use. `to_config()` and `from_config()` convert
between the two.

A field or a group may carry a condition, ``when = {key: [values]}``: it is
shown only while the select `key` holds one of those values (the entered
a_max only when the acceleration is entered; Cetin's inputs only for Cetin).

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .config import (
    DEFAULT_CONFIG,
    GEOMETRIES,
    METHODS,
    METHODS_CPT,
    PGA_SOURCES,
    SUSCEPTIBILITY,
    TEST_TYPES,
)
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "slipsurface-liquefaction"
#: Names project files were saved under before, which still open
OLD_FILE_FORMATS = ("lythos-liquefaction",)
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
    when: Dict[str, List[str]] = field(default_factory=dict)   # shown only if …

    def to_dict(self) -> dict:
        """Only what the browser needs; empty values are left out."""
        keep = ("key", "label", "kind", "default", "decimals")
        return {k: v for k, v in asdict(self).items()
                if k in keep or v not in ("", None, [], {}, 0.0)}


@dataclass
class Group:
    """A titled set of fields."""
    title: str
    fields: List[Field]
    note: str = ""
    when: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"title": self.title, "fields": [f.to_dict() for f in self.fields]}
        if self.note:
            d["note"] = self.note
        if self.when:
            d["when"] = dict(self.when)
        return d


def _num(key, label, default, lo=None, hi=None, unit="", dec=2, step=None):
    return Field(key, label, "number", default, unit, lo, hi, step, dec)


def _check(key, label, default=False):
    return Field(key, label, "check", default)


def _select(key, label, default, options):
    return Field(key, label, "select", default,
                 options=[{"value": v, "label": t} for v, t in options])


def _text(key, label, default=""):
    return Field(key, label, "text", default)


def _when(condition: Dict[str, List[str]], item):
    """Shows a field or a group only while a select holds one of some values."""
    item.when = {key: list(values) for key, values in condition.items()}
    return item


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


SPT = {"test_type": ["spt"]}
CPT = {"test_type": ["cpt"]}


def site_groups(lang: str = "en") -> List[Group]:
    e = DEFAULT_CONFIG["earthquake"]
    w = DEFAULT_CONFIG["groundwater"]
    s = DEFAULT_CONFIG["spt_setup"]
    g = DEFAULT_CONFIG["ground"]
    o = DEFAULT_CONFIG["options"]
    return [
        Group(_t(lang, "group_test"), [
            _select("test_type", _t(lang, "test_type_label"), o["test_type"],
                    _choices(lang, "test", TEST_TYPES)),
        ], note=_t(lang, "test_note")),
        Group(_t(lang, "group_quake"), [
            _num("magnitude", _t(lang, "magnitude_label"), e["magnitude"], 4, 9.5, "", 2, 0.1),
            _select("pga_source", _t(lang, "pga_source_label"), e["pga_source"],
                    _choices(lang, "pga", PGA_SOURCES)),
            _when({"pga_source": ["direct"]},
                  _num("pga", _t(lang, "pga_label"), e["pga"], 0.01, 3, "g", 3, 0.01)),
            _when({"pga_source": ["tbdy"]},
                  _num("sds", _t(lang, "sds_label"), e["sds"], 0.01, 5, "", 3, 0.05)),
        ], note=_t(lang, "quake_note")),
        Group(_t(lang, "group_water"), [
            _num("water_depth", _t(lang, "water_depth_label"), w["depth"], 0, 100, "m", 2, 0.1),
            _num("water_depth_test", _t(lang, "water_depth_test_label"), w["depth_test"], 0,
                 100, "m", 2, 0.1),
            _num("gamma_water", _t(lang, "gamma_w_label"), w["gamma_water"], 9, 11, "kN/m³",
                 2, 0.01),
        ]),
        Group(_t(lang, "group_ground"), [
            _select("geometry", _t(lang, "geometry_label"), g["geometry"],
                    _choices(lang, "geometry", GEOMETRIES)),
            _when({"geometry": ["slope"]},
                  _num("slope", _t(lang, "slope_label"), g["slope"], 0, 10, "%", 2, 0.1)),
            _when({"geometry": ["free_face"]},
                  _num("face_length", _t(lang, "length_label"), g["length"], 0.1, 1000, "m", 1,
                       1)),
            _when({"geometry": ["free_face"]},
                  _num("face_height", _t(lang, "height_label"), g["height"], 0.1, 100, "m", 2,
                       0.5)),
        ], note=_t(lang, "ground_note")),
        _when(SPT, Group(_t(lang, "group_spt"), [
            _num("energy", _t(lang, "energy_label"), s["energy"], 20, 120, "%", 0, 1),
            _num("borehole", _t(lang, "borehole_label"), s["borehole"], 50, 250, "mm", 0, 5),
            _num("stickup", _t(lang, "stickup_label"), s["stickup"], 0, 10, "m", 2, 0.1),
            _check("rod_correction", _t(lang, "rod_label"), s["rod_correction"]),
            _check("no_liner", _t(lang, "liner_label"), s["no_liner"]),
            _check("gravel_correction", _t(lang, "gravel_label"), o["gravel_correction"]),
        ], note=_t(lang, "spt_setup_note"))),
        _when(CPT, Group(_t(lang, "group_cpt"), [
            _num("area_ratio", _t(lang, "area_ratio_label"), o["area_ratio"], 0, 1, "", 2,
                 0.05),
            _num("ic_limit", _t(lang, "ic_limit_label"), o["ic_limit"], 1.5, 4, "", 2, 0.05),
            _num("cfc", _t(lang, "cfc_label"), o["cfc"], -0.3, 0.5, "", 2, 0.05),
            _num("nkt", _t(lang, "nkt_label"), o["nkt"], 5, 30, "", 1, 0.5),
        ], note=_t(lang, "cpt_setup_note"))),
    ]


def option_groups(lang: str = "en") -> List[Group]:
    o = DEFAULT_CONFIG["options"]
    c = DEFAULT_CONFIG["criteria"]
    cetin = {"test_type": ["spt"], "method": ["cetin2004"]}
    return [
        Group(_t(lang, "group_options"), [
            _when(SPT, _select("method", _t(lang, "method_label"), o["method"],
                               _choices(lang, "method", METHODS))),
            _when(CPT, _select("method_cpt", _t(lang, "method_label"), o["method_cpt"],
                               _choices(lang, "method", METHODS_CPT))),
            _when(SPT, _select("susceptibility", _t(lang, "susceptibility_label"),
                               o["susceptibility"], _choices(lang, "susc", SUSCEPTIBILITY))),
            _when(SPT, _num("fine_threshold", _t(lang, "fine_threshold_label"),
                            o["fine_threshold"], 0, 100, "%", 0, 5)),
            _when(SPT, _check("uncertain_susceptible", _t(lang, "uncertain_label"),
                              o["uncertain_susceptible"])),
            _num("settlement_depth", _t(lang, "settlement_depth_label"), o["settlement_depth"],
                 1, 100, "m", 1, 1),
            _check("dry_settlement", _t(lang, "dry_label"), o["dry_settlement"]),
            _check("softening", _t(lang, "softening_label"), o["softening"]),
            _when(cetin, _num("cetin_pl", _t(lang, "cetin_pl_label"), o["cetin_pl"], 1, 99, "%",
                              0, 5)),
            _when(cetin, _num("vs12", _t(lang, "vs12_label"), o["vs12"], 0, 1000, "m/s", 0, 10)),
        ], note=_t(lang, "options_note")),
        Group(_t(lang, "group_criteria"), [
            _num("fs_required", _t(lang, "fs_required_label"), c["fs_required"], 0.5, 3, "",
                 2, 0.05),
            _num("s_allow", _t(lang, "s_allow_label"), c["s_allow"], 0, 2000, "mm", 1, 5),
        ], note=_t(lang, "criteria_note")),
    ]


def study_groups(lang: str = "en") -> List[Group]:
    from .study import METHODS as SAMPLING
    return [Group(_t(lang, "group_study"), [
        _select("study_method", _t(lang, "study_method"), "lhs",
                [(m, _t(lang, f"method_{m}")) for m in SAMPLING]),
        _num("study_n", _t(lang, "study_n"), 500, 3, 100000, "", 0, 50),
        _num("study_seed", _t(lang, "study_seed"), 0, 0, 10 ** 6, "", 0, 1),
    ], note=_t(lang, "study_note"))]


# --------------------------------------------------------------------------- #
#  Tables: soil layers, SPT tests, study variables
# --------------------------------------------------------------------------- #

SOIL_NUMBERS = ["thickness", "gamma", "gamma_sat", "FC", "clay", "LL", "PI", "wn", "Vs", "D50",
                "OCR", "su"]
CPT_NUMBERS = ["depth", "qc", "fs", "u2"]
SPT_NUMBERS = ["depth", "N", "FC", "clay", "LL", "PI", "wn"]
#: SPT columns that may be left empty (the layer's value is used)
SPT_OPTIONAL = ["FC", "clay", "LL", "PI", "wn"]


def _number_column(lang: str, key: str) -> dict:
    return {"key": key, "label": _t(lang, f"col_{key}"), "kind": "number"}


def soil_columns(lang: str = "en") -> List[dict]:
    """Columns of the soil profile table."""
    return ([{"key": "name", "label": _t(lang, "col_name"), "kind": "text"}]
            + [_number_column(lang, key) for key in SOIL_NUMBERS])


def spt_columns(lang: str = "en") -> List[dict]:
    """Columns of the SPT table."""
    return [_number_column(lang, key) for key in SPT_NUMBERS]


def cpt_columns(lang: str = "en") -> List[dict]:
    """Columns of the CPT table."""
    return [_number_column(lang, "depth")] + [
        {"key": key, "label": _t(lang, f"col_cpt_{key}"), "kind": "number"}
        for key in CPT_NUMBERS[1:]]


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


def default_spt_rows() -> List[dict]:
    return [dict(row) for row in DEFAULT_CONFIG["spt"]]


def default_cpt_rows() -> List[dict]:
    return [dict(row) for row in DEFAULT_CONFIG["cpt"]]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #

def schema(lang: str = "en") -> dict:
    """The whole schema the browser builds its forms from, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "site": {"groups": [g.to_dict() for g in site_groups(lang)]},
        "options": {"groups": [g.to_dict() for g in option_groups(lang)]},
        "study": {"groups": [g.to_dict() for g in study_groups(lang)]},
        "soil": {"columns": soil_columns(lang), "rows": default_soil_rows(),
                 "note": _t(lang, "soil_note")},
        "spt": {"columns": spt_columns(lang), "rows": default_spt_rows(),
                "optional": list(SPT_OPTIONAL), "note": _t(lang, "spt_note")},
        "cpt": {"columns": cpt_columns(lang), "rows": default_cpt_rows(),
                "note": _t(lang, "cpt_note")},
        "study_vars": {"columns": study_columns(lang)},
    }


def _all_groups(lang: str = "en") -> List[Group]:
    return project_groups(lang) + site_groups(lang) + option_groups(lang) + study_groups(lang)


def defaults(lang: str = "en") -> Dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: Dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    values["soil_profile"] = default_soil_rows()
    values["spt"] = default_spt_rows()
    values["cpt"] = default_cpt_rows()
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


def _opt(values: dict, key: str) -> Optional[float]:
    """A numeric cell that may be left empty."""
    v = values.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


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
        thickness = _opt(row, "thickness")
        if thickness is None or thickness <= 0:
            continue
        layer = {"name": str(row.get("name") or "").strip() or "Layer"}
        for key in SOIL_NUMBERS:
            layer[key] = _f(row, key, base[key])
        layer["thickness"] = thickness
        layers.append(layer)
    return layers


def read_spt(values: dict) -> List[dict]:
    """SPT tests from the table; rows without a depth or a blow count are dropped."""
    tests = []
    for row in values.get("spt") or []:
        depth, blows = _opt(row, "depth"), _opt(row, "N")
        if depth is None or blows is None:
            continue
        tests.append({"depth": depth, "N": blows,
                      **{key: _opt(row, key) for key in SPT_OPTIONAL}})
    return tests


def read_cpt(values: dict) -> List[dict]:
    """CPT readings from the table; rows without a depth or a cone resistance are dropped."""
    rows = []
    for row in values.get("cpt") or []:
        depth, qc = _opt(row, "depth"), _opt(row, "qc")
        if depth is None or qc is None:
            continue
        rows.append({"depth": depth, "qc": qc, "fs": _opt(row, "fs") or 0.0,
                     "u2": _opt(row, "u2") or 0.0})
    return rows


def to_config(values: dict) -> Dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    d = DEFAULT_CONFIG
    cfg["project_info"] = {"title": _s(values, "title", d["project_info"]["title"]),
                           "analyst": str(values.get("analyst") or "")}
    e = d["earthquake"]
    cfg["earthquake"] = {
        "magnitude": _f(values, "magnitude", e["magnitude"]),
        "pga_source": _s(values, "pga_source", e["pga_source"], PGA_SOURCES),
        "pga": _f(values, "pga", e["pga"]),
        "sds": _f(values, "sds", e["sds"]),
    }
    w = d["groundwater"]
    cfg["groundwater"] = {"depth": _f(values, "water_depth", w["depth"]),
                          "depth_test": _f(values, "water_depth_test", w["depth_test"]),
                          "gamma_water": _f(values, "gamma_water", w["gamma_water"])}
    s = d["spt_setup"]
    cfg["spt_setup"] = {
        "energy": _f(values, "energy", s["energy"]),
        "borehole": _f(values, "borehole", s["borehole"]),
        "stickup": _f(values, "stickup", s["stickup"]),
        "rod_correction": _b(values, "rod_correction", s["rod_correction"]),
        "no_liner": _b(values, "no_liner", s["no_liner"]),
    }
    gr = d["ground"]
    cfg["ground"] = {"geometry": _s(values, "geometry", gr["geometry"], GEOMETRIES),
                     "slope": _f(values, "slope", gr["slope"]),
                     "length": _f(values, "face_length", gr["length"]),
                     "height": _f(values, "face_height", gr["height"])}
    cfg["soil_profile"] = read_soil_profile(values)
    cfg["spt"] = read_spt(values)
    cfg["cpt"] = read_cpt(values)
    o = d["options"]
    cfg["options"] = {
        "test_type": _s(values, "test_type", o["test_type"], TEST_TYPES),
        "method_cpt": _s(values, "method_cpt", o["method_cpt"], METHODS_CPT),
        "gravel_correction": _b(values, "gravel_correction", o["gravel_correction"]),
        "dry_settlement": _b(values, "dry_settlement", o["dry_settlement"]),
        "softening": _b(values, "softening", o["softening"]),
        "area_ratio": _f(values, "area_ratio", o["area_ratio"]),
        "cfc": _f(values, "cfc", o["cfc"]),
        "ic_limit": _f(values, "ic_limit", o["ic_limit"]),
        "nkt": _f(values, "nkt", o["nkt"]),
        "method": _s(values, "method", o["method"], METHODS),
        "susceptibility": _s(values, "susceptibility", o["susceptibility"], SUSCEPTIBILITY),
        "fine_threshold": _f(values, "fine_threshold", o["fine_threshold"]),
        "uncertain_susceptible": _b(values, "uncertain_susceptible",
                                    o["uncertain_susceptible"]),
        "settlement_depth": _f(values, "settlement_depth", o["settlement_depth"]),
        "cetin_pl": _f(values, "cetin_pl", o["cetin_pl"]),
        "vs12": _f(values, "vs12", o["vs12"]),
    }
    c = d["criteria"]
    cfg["criteria"] = {"fs_required": _f(values, "fs_required", c["fs_required"]),
                       "s_allow": _f(values, "s_allow", c["s_allow"])}
    return cfg


#: Flat key <- (section, key) of the configuration
_MAP = [("title", "project_info", "title"), ("analyst", "project_info", "analyst")] + \
    [(k, "earthquake", k) for k in ("magnitude", "pga_source", "pga", "sds")] + \
    [("water_depth", "groundwater", "depth"), ("water_depth_test", "groundwater", "depth_test"),
     ("gamma_water", "groundwater", "gamma_water")] + \
    [("geometry", "ground", "geometry"), ("slope", "ground", "slope"),
     ("face_length", "ground", "length"), ("face_height", "ground", "height")] + \
    [(k, "spt_setup", k) for k in DEFAULT_CONFIG["spt_setup"]] + \
    [(k, "options", k) for k in DEFAULT_CONFIG["options"]] + \
    [(k, "criteria", k) for k in DEFAULT_CONFIG["criteria"]]


def from_config(cfg: dict, base: Optional[dict] = None) -> Dict[str, Any]:
    """Flat values from a nested configuration — reads a `.liq` project file.

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
    if cfg.get("spt"):
        blank = {key: None for key in SPT_NUMBERS}
        values["spt"] = [{**blank, **row} for row in cfg["spt"] if isinstance(row, dict)]
    if cfg.get("cpt"):
        blank = {key: None for key in CPT_NUMBERS}
        values["cpt"] = [{**blank, **row} for row in cfg["cpt"] if isinstance(row, dict)]
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
        "n": int(_f(values, "study_n", 500)),
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
    return [{"value": path, "label": pretty_label(cfg, path, L),
             "base": float(get_value(cfg, path))}
            for path, _ in available_variables(cfg)]
