"""
σci and mi of the intact rock, fitted to laboratory tests.

For intact rock the Hoek–Brown criterion has s = 1 and a = ½, and squaring it
turns it into a straight line (Hoek & Brown 1980):

    y = (σ1 − σ3)²  =  mi·σci·σ3 + σci²  =  m·x + b,    x = σ3

A least-squares line through the tests therefore gives

    σci = √b,    mi = m/σci

and its coefficient of determination r² says how well the criterion
describes them. Uniaxial tests enter at σ3 = 0; a tensile test enters at
σ3 = −σt with σ1 = 0. Hoek recommends tests over 0 ≤ σ3 ≤ σci/2; the range
the tests span is returned so that a narrow one can be warned about.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence

__all__ = ["fit", "read_tests", "LabFitError"]


class LabFitError(ValueError):
    """The tests cannot be fitted; `key` names the reason."""

    def __init__(self, key: str):
        super().__init__(key)
        self.key = key


def read_tests(rows: Sequence[dict]) -> List[Dict[str, float]]:
    """The usable tests of a table: rows with both stresses, σ1 > σ3."""
    tests = []
    for row in rows or []:
        try:
            s3, s1 = float(row.get("sigma3")), float(row.get("sigma1"))
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(s3) and math.isfinite(s1)) or s1 <= s3:
            continue
        tests.append({"name": str(row.get("name") or "").strip(), "sigma3": s3, "sigma1": s1})
    return tests


def fit(rows: Sequence[dict]) -> Dict[str, object]:
    """σci [MPa], mi and r² from the tests."""
    tests = read_tests(rows)
    xs = [t["sigma3"] for t in tests]
    if len(tests) < 2 or max(xs) - min(xs) <= 1e-9:
        raise LabFitError("err_lab_few")
    ys = [(t["sigma1"] - t["sigma3"]) ** 2 for t in tests]
    n = float(len(tests))
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    syy = sum(y * y for y in ys)
    denom = n * sxx - sx * sx
    m = (n * sxy - sx * sy) / denom
    b = (sy - m * sx) / n
    if b <= 0.0 or m <= 0.0:
        raise LabFitError("err_lab_fit")
    sigma_ci = math.sqrt(b)
    mi = m / sigma_ci
    ss_tot = syy - sy * sy / n
    ss_res = sum((y - (m * x + b)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return {"sigma_ci": sigma_ci, "mi": mi, "r2": r2, "slope": m, "intercept": b,
            "n": len(tests), "sigma3_min": min(xs), "sigma3_max": max(xs),
            "tests": tests}
