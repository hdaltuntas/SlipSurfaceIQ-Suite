"""
Results as text, as summary cards and as tables.

Both the browser interface and the command line show the same thing: the
headline numbers as a row of cards, the side-by-side comparisons as tables,
and the full account of the analysis as text. Assembling them here keeps that
promise without either side copying the other's wording, and it needs no
interface toolkit at all — pass a finished analysis and a language code.
"""

from __future__ import annotations

import math
from typing import List

from . import tables
from .config import MODULUS_METHODS
from .i18n import TRANSLATIONS, warning_text

#: Card order, as the interface lays them out
CARD_KEYS = ["GSI", "hb", "c", "phi", "sigma_t", "sigma_c", "sigma_cm", "Erm",
             "sigma3_max", "query"]


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def _num(value, nd: int = 3) -> str:
    """A number with `nd` significant figures, thousands separated."""
    if value is None or not math.isfinite(value):
        return "—"
    if value == 0:
        return "0"
    digits = max(nd - 1 - int(math.floor(math.log10(abs(value)))), 0)
    return f"{value:,.{digits}f}"


def _mpa(value, nd: int = 3) -> str:
    return f"{_num(value, nd)} MPa"


def gsi_source_text(L: dict, res: dict, lang: str) -> str:
    """How GSI was arrived at, in one line."""
    g = res["gsi"]
    source = g["source"]
    if source == "chart":
        return L["gsi_from_chart"].format(
            structure=tables.name(tables.STRUCTURES, g["structure"], lang),
            surface=tables.name(tables.SURFACES, g["surface"], lang))
    if source == "jcond":
        return L["gsi_from_jcond"].format(J=g["JCond89"], RQD=g["RQD"])
    if source == "rmr":
        return L["gsi_from_rmr"].format(RMR=g["RMR89"])
    if source == "q":
        return L["gsi_from_q"].format(Q=g["Q_prime"])
    if source == "cai":
        return L["gsi_from_cai"].format(Vb=g["Vb"], Jc=g["Jc"])
    return L["gsi_from_direct"]


def cards(analysis, lang: str = "en") -> List[dict]:
    """The headline numbers."""
    L = _lang(lang)
    res = analysis.results
    out = []

    def card(key, value, sub="", state=""):
        out.append({"key": key, "title": L[f"card_{key}"], "value": value, "sub": sub,
                    "state": state})

    card("GSI", f"{res['GSI']:.1f}", L[f"gsi_source_{res['gsi']['source']}"])
    h = res["hb"]
    card("hb", f"mb = {_num(h['mb'], 4)}", f"s = {h['s']:.4g} · a = {h['a']:.4f}")
    mc = res["mc"]
    card("c", _mpa(mc["c"]), L["card_fitted"].format(s3=_num(res["sigma3_max"])))
    card("phi", f"{mc['phi']:.2f}°", L[f"application_{res['application']}"])
    st = res["strength"]
    card("sigma_t", _mpa(st["sigma_t"]), "−s·σci/mb")
    card("sigma_c", _mpa(st["sigma_c"]), "σci·s^a")
    card("sigma_cm", _mpa(st["sigma_cm"]),
         f"σcm/σci = {st['sigma_cm'] / res['intact']['sigma_ci']:.3f}")
    m = res["modulus"]
    card("Erm", _mpa(m["Erm"], 4), L[f"modulus_{m['method']}"])
    card("sigma3_max", _mpa(res["sigma3_max"]), L[f"application_{res['application']}"])
    q = res["query"]
    card("query", f"φi = {q['phi']:.1f}°",
         L["card_query_sub"].format(s3=_num(q["sigma3"]), c=_num(q["c"])))
    return out


def comparison_tables(analysis, lang: str = "en") -> List[dict]:
    """The side-by-side tables of the summary view."""
    L = _lang(lang)
    res = analysis.results
    rows = []
    for name, entry in res["applications"].items():
        rows.append({"cells": [L[f"application_{name}"], _num(entry["sigma3_max"]),
                               _num(entry["c"]), f"{entry['phi']:.2f}"],
                     "primary": name == res["application"]})
    applications = {"title": L["table_applications"],
                    "columns": [L["head_application"], "σ3max [MPa]", "c' [MPa]", "φ' [°]"],
                    "rows": rows}

    m = res["modulus"]
    rows = [{"cells": [L[f"modulus_{name}"], _num(m["all"][name], 4),
                       f"{m['all'][name] / m['Ei']:.3f}"],
             "primary": name == m["method"]} for name in MODULUS_METHODS]
    moduli = {"title": L["table_moduli"],
              "columns": [L["head_method"], "Erm [MPa]", "Erm/Ei"], "rows": rows}

    r, h, st, mc = res["residual"], res["hb"], res["strength"], res["mc"]
    rows = [{"cells": cells} for cells in (
        ["GSI", f"{res['GSI']:.1f}", f"{r['GSI']:.1f}"],
        ["mb", _num(h["mb"], 4), _num(r["mb"], 4)],
        ["s", f"{h['s']:.4g}", f"{r['s']:.4g}"],
        ["a", f"{h['a']:.4f}", f"{r['a']:.4f}"],
        ["c' [MPa]", _num(mc["c"]), _num(r["c"])],
        ["φ' [°]", f"{mc['phi']:.2f}", f"{r['phi']:.2f}"],
        ["σt [MPa]", _num(st["sigma_t"]), _num(r["sigma_t"])],
        ["σc [MPa]", _num(st["sigma_c"]), _num(r["sigma_c"])],
    )]
    residual = {"title": L["table_residual"],
                "columns": [L["head_parameter"], L["head_peak"], L["head_residual"]],
                "rows": rows}
    return [applications, moduli, residual]


def _line(label: str, value: str, width: int = 44) -> str:
    return f"  {label:<{width}}{value}"


def results_text(analysis, lang: str = "en") -> str:
    """The whole analysis as text, in the chosen language."""
    L = _lang(lang)
    res = analysis.results
    intact, h, st, mc, m, q = (res["intact"], res["hb"], res["strength"], res["mc"],
                               res["modulus"], res["query"])
    lines = [L["res_title"], "-" * 78]

    lines.append(L["res_intact"])
    rock = tables.rock_type(intact["rock_type"])
    if rock is not None:
        lines.append(_line(L["res_rock_type"], tables.name(tables.ROCK_TYPES,
                                                           intact["rock_type"], lang)))
    lines.append(_line(L["res_source"], L[f"source_{intact['source']}"]))
    lines.append(_line("σci", _mpa(intact["sigma_ci"])))
    lines.append(_line("mi", _num(intact["mi"], 4)))
    lines.append(_line("Ei", f"{_mpa(intact['Ei'], 4)}   (MR = {intact['MR']:.0f})"))
    fit = intact.get("fit")
    if fit:
        lines.append(_line(L["res_fit"], L["res_fit_line"].format(
            n=fit["n"], r2=fit["r2"], lo=fit["sigma3_min"], hi=fit["sigma3_max"])))
    lines.append("")

    lines.append(L["res_mass"])
    lines.append(_line("GSI", f"{res['GSI']:.1f}   ({gsi_source_text(L, res, lang)})"))
    lines.append(_line("D", f"{res['D']:.2f}"))
    lines.append("")

    lines.append(L["res_hb"])
    lines.append(_line("mb", _num(h["mb"], 5)))
    lines.append(_line("s", f"{h['s']:.5g}"))
    lines.append(_line("a", f"{h['a']:.5f}"))
    lines.append("")

    lines.append(L["res_strength"])
    lines.append(_line(L["res_sigma_t"], _mpa(st["sigma_t"], 4)))
    lines.append(_line(L["res_sigma_c"], _mpa(st["sigma_c"], 4)))
    lines.append(_line(L["res_sigma_cm"], _mpa(st["sigma_cm"], 4)))
    lines.append("")

    lines.append(L["res_mc"])
    lines.append(_line(L["res_application"], L[f"application_{res['application']}"]))
    if res["application"] in ("tunnel", "slope"):
        lines.append(_line("γH", _mpa(res["gamma_H"])))
    lines.append(_line("σ3max", _mpa(res["sigma3_max"], 4)))
    lines.append(_line(L["res_c"], _mpa(mc["c"], 4)))
    lines.append(_line(L["res_phi"], f"{mc['phi']:.2f}°"))
    lines.append(_line(L["res_mc_ucs"], _mpa(mc["sigma_cm"], 4)))
    lines.append(_line(L["res_mc_tension"], _mpa(mc["sigma_t"], 4)))
    lines.append("")

    lines.append(L["res_modulus"])
    for name in MODULUS_METHODS:
        mark = " *" if name == m["method"] else ""
        lines.append(_line(L[f"modulus_{name}"] + mark, _mpa(m["all"][name], 4)))
    lines.append("")

    lines.append(L["res_query"].format(s3=_num(q["sigma3"])))
    lines.append(_line("σ1", _mpa(q["sigma1"], 4)))
    lines.append(_line("σn", _mpa(q["sigma_n"], 4)))
    lines.append(_line("τ", _mpa(q["tau"], 4)))
    lines.append(_line(L["res_phi_i"], f"{q['phi']:.2f}°"))
    lines.append(_line(L["res_c_i"], _mpa(q["c"], 4)))
    lines.append("")

    r = res["residual"]
    lines.append(L["res_residual"])
    lines.append(_line("GSIr", f"{r['GSI']:.1f}"))
    lines.append(_line("mr, sr, ar", f"{_num(r['mb'], 4)}, {r['s']:.4g}, {r['a']:.4f}"))
    lines.append(_line(L["res_c"], _mpa(r["c"], 4)))
    lines.append(_line(L["res_phi"], f"{r['phi']:.2f}°"))
    lines.append("")

    lines.append(L["table_applications"])
    for name, entry in res["applications"].items():
        mark = " *" if name == res["application"] else ""
        lines.append(_line(L[f"application_{name}"] + mark,
                           f"σ3max = {_num(entry['sigma3_max']):>9} MPa   "
                           f"c' = {_num(entry['c']):>8} MPa   φ' = {entry['phi']:6.2f}°"))

    notes = warnings(analysis, lang)
    if notes:
        lines += ["", L["warnings_title"]]
        lines += [f"  • {text}" for text in notes]
    return "\n".join(lines)


def warnings(analysis, lang: str = "en") -> List[str]:
    return [warning_text(lang, w) for w in analysis.results.get("warnings", [])]


def headline(analysis, lang: str = "en") -> str:
    """One line for the status bar."""
    res = analysis.results
    return (f"GSI = {res['GSI']:.1f} · c' = {_num(res['mc']['c'])} MPa · "
            f"φ' = {res['mc']['phi']:.1f}° · Erm = {_num(res['modulus']['Erm'], 4)} MPa")
