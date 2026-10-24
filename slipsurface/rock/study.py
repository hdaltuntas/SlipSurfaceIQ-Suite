"""
Parametric and probabilistic studies for SlipSurface IQ Rock.

A study is defined by a list of variables, each addressing one input of the
project configuration by a dotted path (``intact.sigma_ci``,
``rock_mass.GSI``, ``rock_mass.D`` …), and either

* a **range** (min, max)                                  -> parametric, or
* a **distribution** (normal, lognormal, uniform; mean, CoV) -> probabilistic.

Sampling methods
    oat   one-at-a-time sweep over each variable (the others at their
          central values)
    lhs   Latin hypercube (ranges as uniform distributions)
    mc    plain Monte Carlo

Every sample is a complete rock mass analysis — well under a millisecond —
so the runner works in one thread, reporting progress and honouring
cancellation between samples. Post-processing gives summary statistics —
the 5 % fractile among them, the characteristic value of a strength in the
sense of EN 1997-1 — and Spearman rank sensitivities.
"""

from __future__ import annotations

import copy
import csv
import math
from statistics import NormalDist
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from .engine import RockAnalysis

DISTRIBUTIONS = ["normal", "lognormal", "uniform"]
METHODS = ["oat", "lhs", "mc"]

#: Outputs collected for every sample: (key, unit)
OUTPUTS = [
    ("c", "MPa"), ("phi", "°"), ("Erm", "MPa"), ("sigma_cm", "MPa"), ("sigma_c", "MPa"),
    ("sigma_t", "MPa"), ("sigma3_max", "MPa"), ("mb", ""), ("s", ""), ("a", ""),
    ("c_i", "MPa"), ("phi_i", "°"),
]

#: Strengths whose lower 5 % fractile is their characteristic value
CHARACTERISTIC = ["c", "phi", "sigma_cm", "Erm"]


# --------------------------------------------------------------------------- #
#  The inputs a study may address
# --------------------------------------------------------------------------- #

def available_variables(cfg: Dict[str, Any]) -> List[str]:
    """Every input a study may vary, as dotted paths; only the inputs in use."""
    out: List[str] = []
    if (cfg.get("intact") or {}).get("source", "manual") != "lab":
        out += ["intact.sigma_ci", "intact.mi"]
    source = (cfg.get("rock_mass") or {}).get("gsi_source", "direct")
    out += {"direct": ["rock_mass.GSI"], "jcond": ["rock_mass.JCond89", "rock_mass.RQD"],
            "rmr": ["rock_mass.RMR89"], "q": ["rock_mass.Q_prime"],
            "cai": ["rock_mass.Vb", "rock_mass.Jc"]}.get(source, [])
    out.append("rock_mass.D")
    if (cfg.get("modulus") or {}).get("Ei_source", "mr") == "direct":
        out.append("modulus.Ei")
    else:
        out.append("modulus.MR")
    application = (cfg.get("application") or {}).get("type", "general")
    if application in ("tunnel", "slope"):
        out += ["application.unit_weight", "application.depth"]
    elif application == "custom":
        out.append("application.sigma3_max")
    out.append("query.sigma3")
    return out


def pretty_label(path: str, L: Dict[str, str]) -> str:
    """A readable name for a dotted path, in the interface's language."""
    parts = path.split(".")
    group = L.get(f"grp_{parts[0]}", parts[0])
    return f"{group} · {L.get('var_' + parts[-1], parts[-1])}"


def get_value(cfg: Dict[str, Any], path: str) -> Any:
    node: Any = cfg
    for part in path.split("."):
        node = node[int(part)] if part.isdigit() else node[part]
    return node


def set_value(cfg: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    node: Any = cfg
    for part in parts[:-1]:
        node = node[int(part)] if part.isdigit() else node[part]
    last = parts[-1]
    if last.isdigit():
        node[int(last)] = value
    else:
        node[last] = value


# --------------------------------------------------------------------------- #
#  One variable
# --------------------------------------------------------------------------- #

class StudyVariable:
    """One input a study varies, by a range or by a distribution."""

    def __init__(self, path: str, label: str = "", mode: str = "range",
                 vmin: float = 0.0, vmax: float = 0.0, dist: str = "normal",
                 mean: float = 0.0, cov: float = 0.1, n_points: int = 5):
        self.path = path
        self.label = label or path
        self.mode = mode if mode in ("range", "dist") else "range"
        self.vmin, self.vmax = float(vmin), float(vmax)
        self.dist = dist if dist in DISTRIBUTIONS else "normal"
        self.mean = float(mean)
        self.cov = max(float(cov), 0.0)
        self.n_points = max(int(n_points), 2)

    @classmethod
    def from_dict(cls, spec: dict) -> "StudyVariable":
        return cls(path=str(spec.get("path", "")), label=str(spec.get("label", "")),
                   mode=str(spec.get("mode", "range")),
                   vmin=spec.get("min", 0.0) or 0.0, vmax=spec.get("max", 0.0) or 0.0,
                   dist=str(spec.get("dist", "normal")),
                   mean=spec.get("mean", 0.0) or 0.0, cov=spec.get("cov", 0.1) or 0.0,
                   n_points=spec.get("n_points", 5) or 5)

    def to_dict(self) -> dict:
        return {"path": self.path, "label": self.label, "mode": self.mode,
                "min": self.vmin, "max": self.vmax, "dist": self.dist,
                "mean": self.mean, "cov": self.cov, "n_points": self.n_points}

    @property
    def std(self) -> float:
        return abs(self.mean) * self.cov

    def sweep(self) -> np.ndarray:
        """The values of a one-at-a-time sweep."""
        if self.mode == "dist":
            spread = 2.0 * self.std
            return np.linspace(self.mean - spread, self.mean + spread, self.n_points)
        return np.linspace(self.vmin, self.vmax, self.n_points)

    def draw(self, u: np.ndarray) -> np.ndarray:
        """Values from uniform numbers in (0, 1) — the inverse transform."""
        u = np.clip(np.asarray(u, dtype=float), 1e-9, 1.0 - 1e-9)
        if self.mode == "range":
            return self.vmin + u * (self.vmax - self.vmin)
        if self.dist == "uniform":
            half = math.sqrt(3.0) * self.std
            return self.mean - half + u * 2.0 * half
        normal = np.array([NormalDist().inv_cdf(float(value)) for value in u])
        if self.dist == "lognormal":
            if self.mean <= 0 or self.std <= 0:
                return np.full_like(u, self.mean)
            sigma = math.sqrt(math.log(1.0 + (self.std / self.mean) ** 2))
            mu = math.log(self.mean) - 0.5 * sigma ** 2
            return np.exp(mu + sigma * normal)
        return self.mean + self.std * normal


# --------------------------------------------------------------------------- #
#  Sampling
# --------------------------------------------------------------------------- #

def sample(variables: Sequence[StudyVariable], method: str, n: int = 100,
           seed: int = 0) -> List[Dict[str, float]]:
    """The samples a study will analyse, one dictionary of values each."""
    if not variables:
        return []
    rng = np.random.default_rng(seed or None)
    if method == "oat":
        base = {v.path: (v.mean if v.mode == "dist" else 0.5 * (v.vmin + v.vmax))
                for v in variables}
        rows = []
        for variable in variables:
            for value in variable.sweep():
                row = dict(base)
                row[variable.path] = float(value)
                row["_swept"] = variable.path
                rows.append(row)
        return rows

    count = max(int(n), 2)
    if method == "lhs":
        grid = np.empty((count, len(variables)))
        for j in range(len(variables)):
            cuts = (np.arange(count) + rng.random(count)) / count
            grid[:, j] = rng.permutation(cuts)
    else:
        grid = rng.random((count, len(variables)))
    rows = []
    for i in range(count):
        row = {}
        for j, variable in enumerate(variables):
            row[variable.path] = float(variable.draw(np.array([grid[i, j]]))[0])
        rows.append(row)
    return rows


def evaluate(base_cfg: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
    """One sample: the configuration with the values set, analysed."""
    cfg = copy.deepcopy(base_cfg)
    for path, value in values.items():
        if path.startswith("_"):
            continue
        try:
            set_value(cfg, path, float(value))
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    row: Dict[str, Any] = {key: values[key] for key in values}
    try:
        res = RockAnalysis(cfg).run()
    except Exception as exc:                  # an impossible sample is recorded, not fatal
        row["error"] = f"{exc}"
        for key, _ in OUTPUTS:
            row[key] = float("nan")
        return row

    row.update({
        "c": res["mc"]["c"], "phi": res["mc"]["phi"], "Erm": res["modulus"]["Erm"],
        "sigma_cm": res["strength"]["sigma_cm"], "sigma_c": res["strength"]["sigma_c"],
        "sigma_t": res["strength"]["sigma_t"], "sigma3_max": res["sigma3_max"],
        "mb": res["hb"]["mb"], "s": res["hb"]["s"], "a": res["hb"]["a"],
        "c_i": res["query"]["c"], "phi_i": res["query"]["phi"],
        "error": "",
    })
    return row


# --------------------------------------------------------------------------- #
#  The study
# --------------------------------------------------------------------------- #

class Study:
    """A set of samples of one project, and what they say."""

    def __init__(self, config: Dict[str, Any], variables: Sequence[StudyVariable],
                 method: str = "lhs", n: int = 200, seed: int = 0):
        self.config = copy.deepcopy(config)
        self.variables = list(variables)
        self.method = method if method in METHODS else "lhs"
        self.n = max(int(n), 2)
        self.seed = int(seed)
        self.rows: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {}

    def run(self, progress: Optional[Callable[[int, int], None]] = None,
            is_cancelled: Optional[Callable[[], bool]] = None) -> "Study":
        samples = sample(self.variables, self.method, self.n, self.seed)
        total = len(samples)
        self.rows = []
        for index, values in enumerate(samples, start=1):
            if is_cancelled is not None and is_cancelled():
                break
            self.rows.append(evaluate(self.config, values))
            if progress is not None:
                progress(index, total)
        self.summary = summarize(self)
        return self


def _column(rows: List[Dict[str, Any]], key: str) -> np.ndarray:
    out = []
    for row in rows:
        value = row.get(key, float("nan"))
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            out.append(float("nan"))
    return np.array(out)


def _ranks(x: np.ndarray) -> np.ndarray:
    """Ranks from 0, tied values sharing the average of the ranks they span —
    so a constant column has no spread of ranks, and no correlation."""
    _, inverse, counts = np.unique(x, return_inverse=True, return_counts=True)
    ends = np.cumsum(counts) - 1.0
    return (ends - (counts - 1) / 2.0)[inverse]


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """The rank correlation of two samples; nan when there is nothing to rank."""
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return float("nan")
    rx, ry = _ranks(x[mask]), _ranks(y[mask])
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def summarize(study: Study) -> Dict[str, Any]:
    """Statistics and sensitivities."""
    rows = [row for row in study.rows if not row.get("error")]
    out: Dict[str, Any] = {"n_total": len(study.rows), "n_ok": len(rows),
                           "stats": {}, "spearman": {}}
    if not rows:
        return out

    for key, unit in OUTPUTS:
        column = _column(rows, key)
        good = column[np.isfinite(column)]
        if good.size == 0:
            continue
        mean = float(good.mean())
        std = float(good.std(ddof=1)) if good.size > 1 else 0.0
        out["stats"][key] = {
            "n": int(good.size), "unit": unit, "mean": mean, "std": std,
            "cov": std / abs(mean) if mean else float("nan"),
            "min": float(good.min()), "max": float(good.max()),
            "p5": float(np.percentile(good, 5)), "p50": float(np.percentile(good, 50)),
            "p95": float(np.percentile(good, 95)),
        }

    if study.method != "oat":
        for key, _ in OUTPUTS:
            column = _column(rows, key)
            if not np.isfinite(column).any():
                continue
            out["spearman"][key] = {
                variable.path: spearman(_column(rows, variable.path), column)
                for variable in study.variables}
    return out


def table_columns(study: Study) -> List[str]:
    """The columns of the sampled table: the inputs, then the outputs."""
    return [variable.path for variable in study.variables] + \
        [key for key, _ in OUTPUTS] + ["error"]


def to_csv(study: Study, path: str) -> None:
    columns = table_columns(study)
    header = [variable.label for variable in study.variables] + \
        [key for key, _ in OUTPUTS] + ["error"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in study.rows:
            writer.writerow([row.get(column, "") for column in columns])


def to_xlsx(study: Study, path: str) -> None:
    """The sampled table as a spreadsheet; needs openpyxl."""
    try:
        from openpyxl import Workbook
    except ImportError as exc:               # pragma: no cover - the extra is optional
        raise RuntimeError("openpyxl is not installed (pip install openpyxl).") from exc
    columns = table_columns(study)
    book = Workbook()
    sheet = book.active
    sheet.title = "samples"
    sheet.append([variable.label for variable in study.variables]
                 + [key for key, _ in OUTPUTS] + ["error"])
    for row in study.rows:
        sheet.append([row.get(column, "") for column in columns])
    book.save(path)
