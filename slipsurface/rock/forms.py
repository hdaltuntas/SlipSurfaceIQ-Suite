"""
Input schema and readers for SlipSurface IQ Rock.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The browser builds its forms from this schema, and the
server turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``sigma_ci``, ``GSI``, ``application`` …) are the ones the
interface uses; the nested keys of the configuration (``intact.sigma_ci``,
``rock_mass.GSI``, ``application.type`` …) are the ones the engine and the
``.rock`` project files use. `to_config()` and `from_config()` convert
between the two.

A field can declare when it applies — ``when=[("gsi_source", ["rmr"])]`` —
and the browser hides it whenever the condition does not hold. A select can
also declare what it fills in — a rock type fills mi and MR, a strength grade
fills σci, an excavation case fills D — which is how the interface offers the
typical values RocLab's pickers do, while leaving every number editable.

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from . import tables
from .config import (
    APPLICATIONS,
    DEFAULT_CONFIG,
    EI_SOURCES,
    GSI_SOURCES,
    MODULUS_METHODS,
    STRENGTH_SOURCES,
)
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "slipsurface-rock"
# Project files saved before the product was renamed still open.
READ_FORMATS = (FILE_FORMAT, "slipsurface-rock")
FILE_VERSION = "0.1"

#: The "no typical value" entry of every picker
CUSTOM = "custom"


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
    #: option value -> {field key: value} the choice fills in
    fills: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Only what the browser needs; empty values are left out."""
        keep = ("key", "label", "kind", "default", "decimals")
        # Explicit numeric bounds (especially 0) are validation metadata,
        # not optional zero-valued defaults. Dropping min=0 allowed the
        # native Qt spinbox to accept negative disturbance factors (D).
        return {k: v for k, v in asdict(self).items()
                if k in keep or (k in ("min", "max") and v is not None)
                or v not in ("", None, [], {}, 0.0)}


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


def _select(key, label, default, options, when=None, fills=None):
    """A select; an option given as (value, label, group) is listed under its group."""
    return Field(key, label, "select", default,
                 options=[{"value": o[0], "label": o[1], **({"group": o[2]} if len(o) > 2 else {})}
                          for o in options], when=_when(when), fills=fills or {})


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
#  Pickers: a select whose choice fills in typical values
# --------------------------------------------------------------------------- #

def rock_type_options(lang: str = "en"):
    """Rock types grouped by class, with their typical mi in the label."""
    out = [(CUSTOM, _t(lang, "picker_custom"))]
    for cls in tables.ROCK_CLASSES:
        for key, rock in tables.ROCK_TYPES.items():
            if rock["class"] == cls:
                out.append((key, f"{tables.name(tables.ROCK_TYPES, key, lang)}"
                                 f" (mi {rock['mi']:g} ± {rock['mi_pm']:g})",
                            _t(lang, "class_" + cls)))
    return out


def rock_type_fills() -> Dict[str, Dict[str, float]]:
    return {key: {"mi": rock["mi"], "MR": rock["MR"]}
            for key, rock in tables.ROCK_TYPES.items()}


def grade_options(lang: str = "en"):
    return [(CUSTOM, _t(lang, "picker_custom"))] + tables.picker_options(
        tables.STRENGTH_GRADES, lang)


def disturbance_options(lang: str = "en"):
    return [(CUSTOM, _t(lang, "picker_custom"))] + tables.picker_options(
        tables.DISTURBANCE, lang)


# --------------------------------------------------------------------------- #
#  Input groups
# --------------------------------------------------------------------------- #

def project_groups(lang: str = "en") -> List[Group]:
    info = DEFAULT_CONFIG["project_info"]
    return [Group(_t(lang, "group_project"), [
        _text("title", _t(lang, "title_label"), info["title"]),
        _text("analyst", _t(lang, "analyst_label"), info["analyst"]),
    ])]


def intact_groups(lang: str = "en") -> List[Group]:
    i = DEFAULT_CONFIG["intact"]
    manual = [("source", ["manual"])]
    return [Group(_t(lang, "group_intact"), [
        _select("source", _t(lang, "source_label"), i["source"],
                _choices(lang, "source", STRENGTH_SOURCES)),
        _select("rock_type", _t(lang, "rock_type_label"), i["rock_type"],
                rock_type_options(lang), fills=rock_type_fills()),
        _select("strength_grade", _t(lang, "grade_label"), i["strength_grade"],
                grade_options(lang), when=manual,
                fills={key: {"sigma_ci": g["sigma_ci"]}
                       for key, g in tables.STRENGTH_GRADES.items()}),
        _num("sigma_ci", _t(lang, "sigma_ci_label"), i["sigma_ci"], 0.1, 1000, "MPa", 2, 1,
             when=manual),
        _num("mi", _t(lang, "mi_label"), i["mi"], 0.1, 60, "", 2, 1, when=manual),
    ], note=_t(lang, "intact_note"))]


def mass_groups(lang: str = "en") -> List[Group]:
    r = DEFAULT_CONFIG["rock_mass"]
    m = DEFAULT_CONFIG["modulus"]
    a = DEFAULT_CONFIG["application"]
    q = DEFAULT_CONFIG["query"]
    return [
        Group(_t(lang, "group_gsi"), [
            _select("gsi_source", _t(lang, "gsi_source_label"), r["gsi_source"],
                    _choices(lang, "gsi_source", GSI_SOURCES)),
            _num("GSI", _t(lang, "GSI_label"), r["GSI"], 5, 100, "", 1, 1,
                 when=[("gsi_source", ["direct"])]),
            _select("structure", _t(lang, "structure_label"), r["structure"],
                    tables.picker_options(tables.STRUCTURES, lang),
                    when=[("gsi_source", ["chart"])]),
            _select("surface", _t(lang, "surface_label"), r["surface"],
                    tables.picker_options(tables.SURFACES, lang),
                    when=[("gsi_source", ["chart"])]),
            _num("JCond89", _t(lang, "JCond89_label"), r["JCond89"], 0, 30, "", 1, 1,
                 when=[("gsi_source", ["jcond"])]),
            _num("RQD", _t(lang, "RQD_label"), r["RQD"], 0, 100, "%", 0, 5,
                 when=[("gsi_source", ["jcond"])]),
            _num("RMR89", _t(lang, "RMR89_label"), r["RMR89"], 0, 100, "", 0, 1,
                 when=[("gsi_source", ["rmr"])]),
            _num("Q_prime", _t(lang, "Q_prime_label"), r["Q_prime"], 0.001, 1000, "", 3, 0.5,
                 when=[("gsi_source", ["q"])]),
            _num("Vb", _t(lang, "Vb_label"), r["Vb"], 0.1, 1e9, "cm³", 1, 100,
                 when=[("gsi_source", ["cai"])]),
            _num("Jc", _t(lang, "Jc_label"), r["Jc"], 0.01, 50, "", 2, 0.1,
                 when=[("gsi_source", ["cai"])]),
        ], note=_t(lang, "gsi_note")),
        Group(_t(lang, "group_disturbance"), [
            _select("disturbance_case", _t(lang, "disturbance_case_label"),
                    r["disturbance_case"], disturbance_options(lang),
                    fills={key: {"D": d["D"]} for key, d in tables.DISTURBANCE.items()}),
            _num("D", _t(lang, "D_label"), r["D"], 0, 1, "", 2, 0.1),
        ], note=_t(lang, "disturbance_note")),
        Group(_t(lang, "group_application"), [
            _select("application", _t(lang, "application_label"), a["type"],
                    _choices(lang, "application", APPLICATIONS)),
            _num("unit_weight", _t(lang, "unit_weight_label"), a["unit_weight"], 10, 40,
                 "kN/m³", 1, 0.5, when=[("application", ["tunnel", "slope"])]),
            _num("depth", _t(lang, "depth_label"), a["depth"], 0.1, 5000, "m", 1, 10,
                 when=[("application", ["tunnel", "slope"])]),
            _num("sigma3_max", _t(lang, "sigma3_max_label"), a["sigma3_max"], 0.001, 1000,
                 "MPa", 3, 0.5, when=[("application", ["custom"])]),
        ], note=_t(lang, "application_note")),
        Group(_t(lang, "group_modulus"), [
            _select("modulus_method", _t(lang, "modulus_method_label"), m["method"],
                    _choices(lang, "modulus", MODULUS_METHODS)),
            _select("Ei_source", _t(lang, "Ei_source_label"), m["Ei_source"],
                    _choices(lang, "Ei_source", EI_SOURCES)),
            _num("MR", _t(lang, "MR_label"), m["MR"], 10, 2000, "", 0, 25,
                 when=[("Ei_source", ["mr"])]),
            _num("Ei", _t(lang, "Ei_label"), m["Ei"], 1, 1e6, "MPa", 0, 1000,
                 when=[("Ei_source", ["direct"])]),
        ], note=_t(lang, "modulus_note")),
        Group(_t(lang, "group_query"), [
            _num("query_sigma3", _t(lang, "query_sigma3_label"), q["sigma3"], -100, 1000,
                 "MPa", 3, 0.5),
        ], note=_t(lang, "query_note")),
    ]


def study_groups(lang: str = "en") -> List[Group]:
    from .study import METHODS as SAMPLING
    return [Group(_t(lang, "group_study"), [
        _select("study_method", _t(lang, "study_method"), "lhs",
                [(m, _t(lang, f"sampling_{m}")) for m in SAMPLING]),
        _num("study_n", _t(lang, "study_n"), 500, 3, 100000, "", 0, 50),
        _num("study_seed", _t(lang, "study_seed"), 0, 0, 10 ** 6, "", 0, 1),
    ], note=_t(lang, "study_note"))]


# --------------------------------------------------------------------------- #
#  Tables: laboratory tests, study variables
# --------------------------------------------------------------------------- #

LAB_NUMBERS = ["sigma3", "sigma1"]


def lab_columns(lang: str = "en") -> List[dict]:
    """Columns of the triaxial test table."""
    return [{"key": "name", "label": _t(lang, "col_test"), "kind": "text"},
            {"key": "sigma3", "label": _t(lang, "col_sigma3"), "kind": "number"},
            {"key": "sigma1", "label": _t(lang, "col_sigma1"), "kind": "number"}]


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


def default_lab_rows() -> List[dict]:
    return [dict(row) for row in DEFAULT_CONFIG["lab_data"]]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #

def schema(lang: str = "en") -> dict:
    """The whole schema the browser builds its forms from, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "intact": {"groups": [g.to_dict() for g in intact_groups(lang)]},
        "mass": {"groups": [g.to_dict() for g in mass_groups(lang)]},
        "study": {"groups": [g.to_dict() for g in study_groups(lang)]},
        "lab": {"columns": lab_columns(lang), "rows": default_lab_rows(),
                "note": _t(lang, "lab_note"), "when": _when([("source", ["lab"])])},
        "study_vars": {"columns": study_columns(lang)},
    }


def _all_groups(lang: str = "en") -> List[Group]:
    return project_groups(lang) + intact_groups(lang) + mass_groups(lang) + study_groups(lang)


def defaults(lang: str = "en") -> Dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: Dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    values["lab_data"] = default_lab_rows()
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


def _s(values: dict, key: str, default: str = "", allowed: Optional[List[str]] = None) -> str:
    v = values.get(key, default)
    text = str(default if v is None or v == "" else v)
    return text if allowed is None or text in allowed else default


def read_lab_data(values: dict) -> List[dict]:
    """The test table; rows without both stresses are dropped."""
    rows = []
    for row in values.get("lab_data") or []:
        try:
            s3, s1 = float(row.get("sigma3")), float(row.get("sigma1"))
        except (TypeError, ValueError):
            continue
        rows.append({"name": str(row.get("name") or "").strip(), "sigma3": s3, "sigma1": s1})
    return rows


#: Flat key <- (section, key) of the configuration
_MAP = [
    ("title", "project_info", "title"), ("analyst", "project_info", "analyst"),
    ("source", "intact", "source"), ("rock_type", "intact", "rock_type"),
    ("strength_grade", "intact", "strength_grade"), ("sigma_ci", "intact", "sigma_ci"),
    ("mi", "intact", "mi"),
    ("gsi_source", "rock_mass", "gsi_source"), ("GSI", "rock_mass", "GSI"),
    ("structure", "rock_mass", "structure"), ("surface", "rock_mass", "surface"),
    ("JCond89", "rock_mass", "JCond89"), ("RQD", "rock_mass", "RQD"),
    ("RMR89", "rock_mass", "RMR89"), ("Q_prime", "rock_mass", "Q_prime"),
    ("Vb", "rock_mass", "Vb"), ("Jc", "rock_mass", "Jc"),
    ("disturbance_case", "rock_mass", "disturbance_case"), ("D", "rock_mass", "D"),
    ("modulus_method", "modulus", "method"), ("Ei_source", "modulus", "Ei_source"),
    ("Ei", "modulus", "Ei"), ("MR", "modulus", "MR"),
    ("application", "application", "type"), ("unit_weight", "application", "unit_weight"),
    ("depth", "application", "depth"), ("sigma3_max", "application", "sigma3_max"),
    ("query_sigma3", "query", "sigma3"),
]

#: The choices each select may take; anything else falls back to the default
_ALLOWED = {
    "source": STRENGTH_SOURCES,
    "rock_type": [CUSTOM] + list(tables.ROCK_TYPES),
    "strength_grade": [CUSTOM] + list(tables.STRENGTH_GRADES),
    "gsi_source": GSI_SOURCES,
    "structure": list(tables.STRUCTURES),
    "surface": list(tables.SURFACES),
    "disturbance_case": [CUSTOM] + list(tables.DISTURBANCE),
    "modulus_method": MODULUS_METHODS,
    "Ei_source": EI_SOURCES,
    "application": APPLICATIONS,
}


def to_config(values: dict) -> Dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for flat, section, key in _MAP:
        default = DEFAULT_CONFIG[section][key]
        if flat in _ALLOWED:
            cfg[section][key] = _s(values, flat, default, _ALLOWED[flat])
        elif isinstance(default, str):
            cfg[section][key] = str(values.get(flat) if values.get(flat) is not None
                                    else default)
        else:
            cfg[section][key] = _f(values, flat, default)
    cfg["project_info"]["title"] = _s(values, "title", DEFAULT_CONFIG["project_info"]["title"])
    cfg["lab_data"] = read_lab_data(values)
    return cfg


def from_config(cfg: dict, base: Optional[dict] = None) -> Dict[str, Any]:
    """Flat values from a nested configuration — reads a `.rock` project file.

    Whatever the file does not carry keeps its default.
    """
    values = dict(base) if base is not None else defaults()
    for flat, section, key in _MAP:
        if key in (cfg.get(section) or {}):
            values[flat] = cfg[section][key]
    if isinstance(cfg.get("lab_data"), list):
        values["lab_data"] = [dict(row) for row in cfg["lab_data"] if isinstance(row, dict)]
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
    out = []
    for path in available_variables(cfg):
        try:
            base = float(get_value(cfg, path))
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        out.append({"value": path, "label": pretty_label(path, L), "base": base})
    return out
