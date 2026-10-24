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
CARD_KEYS = ["q_ult", "q_net", "q_all", "applied", "check_bearing", "check_sliding",
             "check_ecc", "width"]


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def _status(L: dict, status: str) -> tuple:
    """A check status as (short text, state) — state drives the card colour."""
    if status == "N/A":
        return L["na_short"], "na"
    return (L["ok_short"], "ok") if status == "OK" else (L["notok_short"], "bad")


def method_label(L: dict, key: str) -> str:
    return L.get(f"method_{key}", key)


def _pressure(value: float, nd: int = 1) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    return f"{value:,.{nd}f} kPa"


def cards(analysis, lang: str = "en") -> List[dict]:
    """The headline numbers: the capacity, what is applied, and the checks."""
    L = _lang(lang)
    res = analysis.results
    checks = res["checks"]
    out = []

    def card(key, value, sub="", state="", title=None):
        out.append({"key": key, "title": title or L[f"card_{key}"], "value": value,
                    "sub": sub, "state": state})

    governing = L["card_governing"].format(name=method_label(L, res["governing"]))
    card("q_ult", _pressure(res["q_ult"]), governing)
    card("q_net", _pressure(res["q_net_ult"]),
         L[f"analysis_label_short_{res['methods'].get(res['primary'], {}).get('governing', 'drained')}"]
         if res["primary"] in res["methods"] else "")
    bearing = checks["bearing"]
    card("q_all", _pressure(bearing["q_all"]),
         f"q_net,all = {bearing['q_all_net']:,.1f} kPa")
    card("applied", _pressure(res["applied"]["q"]),
         L["card_on_area"].format(area=res["applied"]["A"]))

    ec7 = res.get("eurocode")
    if ec7 and ec7.get("combinations"):
        text, state = _status(L, ec7["status"])
        card("check_bearing", text,
             f"{ec7['governing']}: Λ = {ec7['utilisation']:.2f}", state,
             title=L["card_ec7"])
    else:
        text, state = _status(L, bearing["status"])
        card("check_bearing", text,
             f"FS = {bearing['actual']:.2f} / {bearing['allowable']:.2f}", state)

    slide = checks["sliding"]
    text, state = _status(L, slide["status"])
    card("check_sliding", text,
         "" if slide["status"] == "N/A"
         else f"FS = {slide['actual']:.2f} / {slide['allowable']:.2f}", state)

    ecc = checks["eccentricity"]
    text, state = _status(L, ecc["status"])
    card("check_ecc", text,
         f"e/B = {ecc['actual']:.3f} / {ecc['allowable']:.3f}", state)

    width = res["required_width"]
    card("width", f"{width:.2f} m" if math.isfinite(width) else L["card_none"],
         "" if math.isfinite(width) else "", "" if math.isfinite(width) else "na")
    return out


def _row(first: str, values, width: int = 26) -> str:
    return f"  {first:<{width}}" + "".join(f"{v:>13}" for v in values)


def _num(value, nd: int = 1) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    return f"{value:,.{nd}f}"


def results_text(analysis, lang: str = "en") -> str:
    """The whole analysis as text, in the chosen language."""
    L = _lang(lang)
    a, res = analysis, analysis.results
    geom, applied, pressure = res["geometry"], res["applied"], res["pressure"]
    lines = [L["res_title"], "-" * 80]

    length = "" if a.shape in ("square", "circle", "strip") else f", L = {a.L:.2f} m"
    lines.append(L["res_foundation"].format(shape=L["shape_" + a.shape], B=a.B, L=length,
                                            Df=a.Df))
    if a.eta or a.beta:
        lines.append(L["res_tilt"].format(eta=a.eta, beta=a.beta))
    lines.append(L["res_loading"].format(V=applied["V"], H=applied["H"],
                                         angle=applied["inclination"]))
    if a.seismic_on:
        lines.append(L["res_seismic"].format(kh=a.kh, kv=a.kv, psi=res["actions"]["psi"]))
    lines.append(L["res_eccentricity"].format(eB=geom["e_B"], eL=geom["e_L"],
                                              Be=geom["B_eff"], Le=geom["L_eff"],
                                              A=geom["A_eff"]))
    kern = (L["res_in_kern"] if pressure["in_kern"]
            else L["res_out_kern"].format(c=pressure["contact"]))
    lines.append(L["res_pressure"].format(qmax=pressure["q_max"], qmin=pressure["q_min"],
                                          kern=kern))
    surcharge = res["surcharge"]
    lines.append(L["res_surcharge"].format(total=surcharge["total"], u=surcharge["pore"],
                                           eff=surcharge["effective"]))
    params = res["params"]["drained"]
    lines.append(L["res_zone"].format(depth=res["zone"]["depth"],
                                      layers=", ".join(params["layers"])))
    lines.append(L["res_params"].format(c=params["c"], phi=params["phi"],
                                        cu=res["params"]["undrained"]["cu"],
                                        gamma=params["gamma"]))

    heads = [L["head_analysis"], L["head_qult"], L["head_qnet"], L["head_Nc"],
             L["head_Nq"], L["head_Ng"]]
    lines += ["", L["res_methods_title"], _row(L["head_method"], heads)]
    for key, entry in res["methods"].items():
        mark = " *" if key == res["primary"] else ""
        N = entry["N"]
        lines.append(_row(method_label(L, key)[:24] + mark,
                          [L[f"analysis_label_short_{entry['governing']}"],
                           _num(entry["q_ult"]), _num(entry["q_net_ult"]),
                           _num(N["Nc"], 2), _num(N["Nq"], 2), _num(N["Ngamma"], 2)]))

    if res["others"]:
        lines += ["", L["res_others_title"]]
        for key, entry in res["others"].items():
            value = entry.get("q_ult")
            allowable = entry.get("q_all")
            lines.append(_row(method_label(L, key)[:24],
                              [entry.get("analysis", "") and
                               L[f"analysis_label_short_{entry['analysis']}"] or "",
                               _num(value), _num(entry.get("q_net_ult")),
                               _num(allowable), "", ""]))
            if entry["kind"] == "two_layer":
                d = entry["detail"]
                lines.append("    " + L["res_two_layer"].format(
                    top=d.get("q_top", float("nan")), bottom=d.get("q_bottom", float("nan")),
                    H=d.get("H", res["zone"]["depth"]), Ks=d.get("Ks", 0.0)))
            if key == "hoek_brown":
                d = entry["detail"]
                lines.append("    " + L["res_rock"].format(mb=d["mb"], s=d["s"], a=d["a"],
                                                           c=d["c"], phi=d["phi"]))

    primary = res["methods"].get(res["primary"])
    if primary:
        lines += ["", L["res_factors_title"].format(name=method_label(L, res["primary"])),
                  _row(L["head_factor"], [L["head_c_term"], L["head_q_term"],
                                          L["head_g_term"]])]
        for name in ("shape", "depth", "inclination", "base", "ground", "compressibility"):
            f = primary["factors"][name]
            lines.append(_row(L[f"factor_{name}"], [f"{f['c']:.3f}", f"{f['q']:.3f}",
                                                    f"{f['g']:.3f}"]))
        total = primary["q_ult"] or 1.0
        lines += ["", L["res_terms_title"]]
        for part, key in (("c", "head_c_term"), ("q", "head_q_term"), ("g", "head_g_term")):
            value = primary["terms"][part]
            lines.append("  " + L["res_term_line"].format(
                name=L[key], value=value, share=100.0 * value / total))

    checks = res["checks"]
    lines += ["", L["res_checks_title"]]
    bearing = checks["bearing"]
    lines.append("  " + L["res_check_bearing"].format(
        actual=bearing["actual"], allowable=bearing["allowable"],
        status=_status(L, bearing["status"])[0]))
    slide = checks["sliding"]
    if slide["status"] != "N/A":
        lines.append("  " + L["res_check_sliding"].format(
            actual=slide["actual"], allowable=slide["allowable"],
            status=_status(L, slide["status"])[0]))
    ecc = checks["eccentricity"]
    lines.append("  " + L["res_check_ecc"].format(
        actual=ecc["actual"], allowable=ecc["allowable"],
        status=_status(L, ecc["status"])[0]))

    ec7 = res.get("eurocode")
    if ec7 and ec7.get("combinations"):
        lines += ["", L["res_ec7_title"].format(approach=L[f"approach_{ec7['approach']}"])]
        for comb in ec7["combinations"]:
            lines.append("  " + L["res_ec7_line"].format(
                name=comb["name"], sets=" + ".join(comb["sets"]), Ed=comb["Ed"],
                Rd=comb["Rd"], util=comb["utilisation"],
                status=_status(L, comb["status"])[0]))
            if comb["slide_status"] != "N/A":
                lines.append(L["res_ec7_slide"].format(
                    Hd=comb["Hd"], Rd=comb["Rhd"],
                    status=_status(L, comb["slide_status"])[0]))

    width = res["required_width"]
    lines += ["", ("  " + L["res_required_width"].format(B=width)) if math.isfinite(width)
              else ("  " + L["res_no_width"].format(hi=60.0))]

    lines += ["", L["res_layers_title"],
              _row(L["head_layer"], [L["head_depth"], L["col_gamma"], L["col_c"],
                                     L["col_phi"], L["col_cu"], L["head_sigma"]])]
    for row in res["layers"]:
        lines.append(_row(row["name"][:24],
                          [f"{row['top']:.1f}–{row['bottom']:.1f}", _num(row["gamma"], 1),
                           _num(row["c"], 1), _num(row["phi"], 1), _num(row["cu"], 1),
                           _num(row["sigma_eff"], 1)]))

    if res["warnings"]:
        lines += ["", L["warnings_title"]]
        lines += ["  • " + warning_text(lang, w) for w in res["warnings"]]
    return "\n".join(lines)


def warnings(analysis, lang: str = "en") -> List[str]:
    return [warning_text(lang, w) for w in analysis.results.get("warnings", [])]


def headline(analysis, lang: str = "en") -> str:
    """One line for the status bar: the capacity, the check and the width."""
    L = _lang(lang)
    res = analysis.results
    bearing = res["checks"]["bearing"]
    status, _ = _status(L, bearing["status"])
    width = res["required_width"]
    tail = f" · B ≥ {width:.2f} m" if math.isfinite(width) else ""
    return (f"q_ult = {res['q_ult']:,.1f} kPa · FS = {bearing['actual']:.2f} · "
            f"{L['card_FS']}: {status}{tail}")
