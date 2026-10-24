"""
Results as text and as summary cards.

Both the browser interface and the command line show the same thing: the
headline numbers as a row of cards, and the full account of the analysis as
text. Assembling them here keeps that promise without either side copying the
other's wording, and it needs no interface toolkit at all — pass a finished
analysis and a language code.
"""

from __future__ import annotations

import math
from typing import List

from .i18n import TRANSLATIONS, warning_text

#: Card order, as the interface lays them out
CARD_KEYS = ["fs_min", "h_liq", "settlement", "lpi", "lsn", "lateral", "check_fs", "check_s"]


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def _status(L: dict, status: str, risk: bool = False) -> tuple:
    """A check status as (short text, state) — state drives the card colour."""
    if status == "N/A":
        return L["na_short"], "na"
    if status == "OK":
        return L["ok_short"], "ok"
    return (L["risk_short"] if risk else L["notok_short"]), "bad"


def fs_text(value: float) -> str:
    """A factor of safety; the capped ones read as '> 2'."""
    if value is None or not math.isfinite(value):
        return "—"
    return "> 2" if value >= 2.0 else f"{value:.2f}"


def cards(analysis, lang: str = "en") -> List[dict]:
    """The headline numbers: lowest FS, thickness, settlement, indices and checks."""
    L = _lang(lang)
    res = analysis.results
    out = []

    def card(key, value, sub="", state=""):
        out.append({"key": key, "title": L[f"card_{key}"], "value": value, "sub": sub,
                    "state": state})

    if math.isfinite(res["fs_min"]):
        state = "bad" if res["fs_min"] < 1.0 else (
            "warn" if res["fs_min"] < analysis.fs_required else "ok")
        card("fs_min", fs_text(res["fs_min"]), L["card_at"].format(z=res["z_fs_min"]), state)
    else:
        card("fs_min", L["card_none"], L["card_fs_none"], "na")
    card("h_liq", f"{res['h_liq']:.2f} m", "FS < 1", "bad" if res["h_liq"] > 0 else "ok")
    sub = L["card_to"].format(d=analysis.settlement_depth)
    if res["settlement_dry"] > 0:
        sub = L["card_sat_dry"].format(s=res["settlement_sat"], d=res["settlement_dry"])
    card("settlement", f"{res['settlement']:.1f} mm", sub)
    card("lpi", f"{res['lpi']:.1f}", L["lpi_" + res["lpi_class"]],
         {"none": "ok", "low": "", "high": "warn", "very_high": "bad"}[res["lpi_class"]])
    card("lsn", f"{res['lsn']:.1f}", L["lsn_" + res["lsn_class"]],
         "ok" if res["lsn"] < 10 else ("warn" if res["lsn"] < 30 else "bad"))
    if analysis.geometry == "level":
        card("lateral", "—", L["card_level"], "na")
    else:
        card("lateral", f"{res['ld']:.2f} m", f"LDI = {res['ldi']:.2f} m",
             "ok" if res["ld"] < 0.1 else ("warn" if res["ld"] < 0.3 else "bad"))

    check = res["checks"]["fs"]
    text, state = _status(L, check["status"], risk=True)
    card("check_fs", text,
         f"{fs_text(check['actual'])} / {check['required']:.2f}" if check["status"] != "N/A"
         else "", state)
    check = res["checks"]["settlement"]
    text, state = _status(L, check["status"])
    card("check_s", text,
         f"{check['actual']:.1f} / {check['allowable']:.1f} mm" if check["status"] != "N/A"
         else "", state)
    return out


def _row(values, widths) -> str:
    return "  " + "".join(f"{v:>{w}}" for v, w in zip(values, widths))


def _num(value, fmt: str) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "—"
    return format(value, fmt)


def _fs_cell(t: dict, m: dict, i: int) -> str:
    """The factor of safety of a test: against liquefaction where it is assessed,
    against cyclic softening (marked 'cs') for a clay-like soil."""
    if t["assessed"][i]:
        return fs_text(m["fs"][i])
    if math.isfinite(t["fs_soft"][i]):
        return f"{fs_text(t['fs_soft'][i])} cs"
    return "—"


def table_rows(analysis, lang: str = "en"):
    """The column heads and the rows of text of the per-test table, for the SPT or
    the CPT."""
    L = _lang(lang)
    res = analysis.results
    t, m = res["tests"], res["methods"][analysis.method]
    if res["kind"] == "cpt":
        heads = ["z (m)", "qc (MPa)", "Ic", "FC (%)", "qc1Ncs"]
        first = [[f"{t['z'][i]:.2f}", f"{t['qc'][i]:.2f}", f"{t['Ic'][i]:.2f}",
                  f"{t['FC'][i]:.0f}", f"{m['ncs'][i]:.1f}"] for i in range(len(t["z"]))]
    else:
        heads = ["z (m)", "N", "N60", "(N1)60", "(N1)60cs"]
        first = [[f"{t['z'][i]:.2f}", f"{t['N'][i]:g}", f"{t['N60'][i]:.1f}",
                  f"{m['n1'][i]:.1f}", f"{m['ncs'][i]:.1f}"] for i in range(len(t["z"]))]
    heads += ["σ'v (kPa)", "rd", "CSR", "CRR", "FS", "εv (%)", L["head_class"], L["head_state"]]
    rows = []
    for i, start in enumerate(first):
        assessed = bool(t["assessed"][i])
        eps = 100.0 * (m["eps"][i] if assessed else t["eps_dry"][i])
        rows.append(start + [
            f"{t['sigma_eff'][i]:.1f}", f"{m['rd'][i]:.3f}", f"{m['csr'][i]:.3f}",
            _num(m["crr"][i], ".3f") if assessed else "—", _fs_cell(t, m, i),
            f"{eps:.2f}" if assessed or eps > 0 else "—",
            L["class_" + t["class"][i]], L["state_" + t["state"][i]]])
    return heads, rows


def results_text(analysis, lang: str = "en") -> str:
    """The whole analysis as text, in the chosen language."""
    L = _lang(lang)
    a, res = analysis, analysis.results
    t = res["tests"]
    src = L["res_from_sds"].format(s=a.sds) if a.pga_source == "tbdy" else ""
    yn = lambda b: L["yes"] if b else L["no"]  # noqa: E731
    lines = [L["res_title"], "-" * 118,
             L["res_quake"].format(m=a.magnitude, a=a.amax, src=src),
             L["res_water"].format(zw=a.zw, zt=a.zw_test)]
    if res["kind"] == "cpt":
        lines += [L["res_method_cpt"].format(method=L["method_" + a.method], ic=a.ic_limit),
                  L["res_cpt"].format(a=a.area_ratio, cfc=a.cfc, n=len(t["z"]))]
    else:
        lines += [L["res_method"].format(method=L["method_" + a.method],
                                         susc=L["susc_" + a.criterion]),
                  L["res_spt"].format(er=a.energy, ce=res["factors"]["CE"], d=a.borehole,
                                      cb=res["factors"]["CB"], cr=yn(a.rod_correction),
                                      cs=yn(not a.no_liner))]
        if a.method == "cetin2004":
            lines.append(L["res_vs12"].format(v=res["vs12"]))

    heads, rows = table_rows(analysis, lang)
    widths = [7, 9, 7, 8, 10, 10, 7, 7, 7, 9, 8, 16, 22]
    lines += ["", L["res_table_title"], _row(heads, widths)]
    lines += [_row(row[:-2] + [row[-2][:15], row[-1][:21]], widths) for row in rows]

    lines += ["", L["res_borehole_title"]]
    if math.isfinite(res["fs_min"]):
        lines.append("  " + L["res_fs_min"].format(fs=res["fs_min"], z=res["z_fs_min"]))
    else:
        lines.append("  " + L["res_no_liq"])
    lines += ["  " + L["res_h_liq"].format(h=res["h_liq"]),
              "  " + L["res_settle"].format(d=a.settlement_depth, s=res["settlement_sat"])]
    if a.dry_settlement:
        lines += ["  " + L["res_dry"].format(s=res["settlement_dry"]),
                  "  " + L["res_total"].format(s=res["settlement"])]
    if res["h_soft"] > 0:
        lines.append("  " + L["res_soft"].format(h=res["h_soft"]))
    lines += [
              "  " + L["res_lpi"].format(v=res["lpi"], c=L["lpi_" + res["lpi_class"]]),
              "  " + L["res_lsn"].format(v=res["lsn"], c=L["lsn_" + res["lsn_class"]])]
    if a.geometry != "level":
        lines.append("  " + L["res_ld"].format(ldi=res["ldi"], ld=res["ld"],
                                              geo=L["geometry_" + a.geometry].lower()))

    lines += ["", L["res_compare_title"],
              f"  {L['head_method']:<32}" + _row(["FS,min", "s (mm)", "LPI", "LD (m)",
                                                   L["head_n_liq"]], [10, 10, 10, 10, 12])[2:]]
    for key, c in res["comparison"].items():
        mark = " *" if key == a.method else ""
        lines.append(f"  {(L['method_' + key] + mark)[:32]:<32}" + _row(
            [fs_text(c["fs_min"]), _num(c["settlement"], ".1f"), f"{c['lpi']:.1f}",
             _num(c["ld"], ".2f"), c["n_liq"]], [10, 10, 10, 10, 12])[2:])

    lines += ["", L["res_checks_title"]]
    check = res["checks"]["fs"]
    if check["status"] != "N/A":
        lines.append("  " + L["res_check_fs"].format(
            fs=check["actual"], req=check["required"],
            status=_status(L, check["status"], risk=True)[0]))
    check = res["checks"]["settlement"]
    if check["status"] != "N/A":
        lines.append("  " + L["res_check_s"].format(
            s=check["actual"], a=check["allowable"], status=_status(L, check["status"])[0]))

    if res["warnings"]:
        lines += ["", L["warnings_title"]]
        lines += ["  • " + warning_text(lang, w) for w in res["warnings"]]
    return "\n".join(lines)


def test_table(analysis, lang: str = "en") -> dict:
    """The results at each test as a table for the page: column heads, rows of
    text, and each row's state (which colours it)."""
    columns, rows = table_rows(analysis, lang)
    states = [str(s) for s in analysis.results["tests"]["state"]]
    return {"columns": columns, "rows": rows, "states": states}


def warnings(analysis, lang: str = "en") -> List[str]:
    return [warning_text(lang, w) for w in analysis.results.get("warnings", [])]


def headline(analysis, lang: str = "en") -> str:
    """One line for the status bar: the lowest FS, the settlement and the check."""
    L = _lang(lang)
    res = analysis.results
    status, _ = _status(L, res["checks"]["fs"]["status"], risk=True)
    return (f"FS,min = {fs_text(res['fs_min'])} · s = {res['settlement']:.1f} mm · "
            f"LPI = {res['lpi']:.1f} · {L['card_check_fs']}: {status}")
