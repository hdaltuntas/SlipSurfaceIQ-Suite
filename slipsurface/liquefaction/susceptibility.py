"""
Can the soil liquefy at all? The susceptibility of fine-grained soils, judged
from the Atterberg limits, the natural water content and the clay fraction.

The SPT triggering curves are written for sands and non-plastic silts. A soil
with enough plastic fines behaves like a clay instead: it softens under cyclic
load but does not liquefy, and its resistance is not what an SPT curve says.
Which soils belong to which side is decided here, before any factor of safety
is worked out.

A soil is treated as coarse-grained (sand-like, susceptible) when its fines
content is below the chosen threshold, or when it is non-plastic (PI = 0).
Otherwise one of these criteria decides:

    chinese           Wang (1979), Seed & Idriss (1982): clay fraction ≤ 15 %,
                      LL ≤ 35 % and wn ≥ 0.9·LL. The clay fraction was defined
                      as finer than 5 µm; the one entered is used as given.
    andrews_martin    Andrews & Martin (2000): clay (< 2 µm) < 10 % and
                      LL < 32 % susceptible; clay ≥ 10 % and LL ≥ 32 % not;
                      otherwise to be tested.
    seed2003          Seed et al. (2003): LL ≤ 37, PI ≤ 12 and wn ≥ 0.8·LL
                      (zone A) susceptible; LL ≤ 47, PI ≤ 20 and wn ≥ 0.85·LL
                      (zone B) to be tested; not otherwise.
    bray_sancio       Bray & Sancio (2006): PI ≤ 12 and wn/LL ≥ 0.85
                      susceptible; 12 < PI ≤ 18 and wn/LL ≥ 0.8 moderately
                      susceptible (to be tested); not otherwise.
    boulanger_idriss  Boulanger & Idriss (2006): PI < 7 sand-like (liquefies);
                      PI ≥ 7 clay-like (cyclic softening, not liquefaction).
    none              every soil is taken as sand-like.

The classes are

    sand         coarse-grained or non-plastic: sand-like, susceptible
    susceptible  fine-grained, susceptible by the criterion
    moderate     fine-grained, in the band a criterion leaves to laboratory tests
    not          fine-grained and clay-like: not susceptible
"""

from __future__ import annotations

from typing import List

import numpy as np

from .config import SUSCEPTIBILITY

__all__ = ["CLASSES", "classify", "classify_one"]

CLASSES = ["sand", "susceptible", "moderate", "not"]


def _criterion(criterion: str, clay: float, LL: float, PI: float, wn: float) -> str:
    ratio = wn / LL if LL > 0 else float("nan")
    if criterion == "boulanger_idriss":
        return "susceptible" if PI < 7.0 else "not"
    if LL <= 0:                      # a plastic soil without a liquid limit
        return "moderate"
    if criterion == "chinese":
        return "susceptible" if clay <= 15.0 and LL <= 35.0 and ratio >= 0.9 else "not"
    if criterion == "andrews_martin":
        if clay < 10.0 and LL < 32.0:
            return "susceptible"
        if clay >= 10.0 and LL >= 32.0:
            return "not"
        return "moderate"
    if criterion == "seed2003":
        if LL <= 37.0 and PI <= 12.0 and ratio >= 0.8:
            return "susceptible"
        if LL <= 47.0 and PI <= 20.0 and ratio >= 0.85:
            return "moderate"
        return "not"
    # bray_sancio
    if PI <= 12.0 and ratio >= 0.85:
        return "susceptible"
    if PI <= 18.0 and ratio >= 0.8:
        return "moderate"
    return "not"


def classify_one(criterion: str, FC: float, clay: float, LL: float, PI: float, wn: float,
                 fine_threshold: float = 35.0) -> str:
    """The susceptibility class of one sample."""
    if criterion not in SUSCEPTIBILITY:
        criterion = SUSCEPTIBILITY[0]
    if criterion == "none" or FC < fine_threshold or PI <= 0:
        return "sand"
    return _criterion(criterion, clay, LL, PI, wn)


def classify(criterion: str, FC, clay, LL, PI, wn, fine_threshold: float = 35.0) -> List[str]:
    """The susceptibility class of every sample."""
    rows = np.broadcast_arrays(*(np.asarray(v, dtype=float) for v in (FC, clay, LL, PI, wn)))
    return [classify_one(criterion, *(float(v) for v in values), fine_threshold)
            for values in zip(*rows)]
