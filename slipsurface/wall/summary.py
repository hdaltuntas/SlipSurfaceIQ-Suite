"""
Results as text, as summary cards and as tables.

Both the browser interface and the command line show the same thing: the
headline checks as a row of cards, the full account of the analysis as text,
and the tables of stability, bearing, earth pressure, member design and bar
schedule. Assembling them here keeps that promise without either side
copying the other's wording, and it needs no interface toolkit at all — pass
a finished analysis and a language code.
"""

from __future__ import annotations

import math
from typing import List

from .i18n import TRANSLATIONS, warning_text

#: The stability checks, in order
STABILITY = ["sliding", "overturning", "eccentricity", "bearing"]

#: The designed sections, in order
SECTIONS = ["stem", "toe", "heel", "key"]

#: Card order, as the interface lays them out
CARD_KEYS = ["sliding", "overturning", "eccentricity", "bearing", "global", "stem", "toe",
             "heel", "heel_length"]


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def status_text(L: dict, status: str) -> tuple:
    """A check status as (short text, state) — state drives the card colour."""
    if status == "N/A":
        return L["na_short"], "na"
    return (L["ok_short"], "ok") if status == "OK" else (L["notok_short"], "bad")


def num(value, nd: int = 2) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "∞" if value == math.inf else "—"
    return f"{value:,.{nd}f}"


def check_sub(L: dict, check: dict, unit: str = "m") -> str:
    """'FS = 2.31 ≥ 1.50' or 'e = 0.45 ≤ 0.90 m'."""
    if check["status"] == "N/A":
        return ""
    if check["kind"] == "limit":
        return f"e = {num(check['value'], 3)} ≤ {num(check['required'], 3)} {unit}"
    return f"{L['value_FS']} = {num(check['value'])} ≥ {num(check['required'])}"


def _section_status(sec: dict) -> str:
    keys = ["flexure", "shear", "ratio"]
    states = [sec[k]["status"] for k in keys] + ([sec["along"]["status"]] if "along" in sec
                                                 else [])
    return "NOT OK" if "NOT OK" in states else "OK"


def bars_text(sec: dict) -> str:
    return f"Ø{sec['phi']}/{sec['s']:.0f}"


def cards(wall, lang: str = "en") -> List[dict]:
    """The headline numbers: every stability check, the members, the heel."""
    L = _lang(lang)
    res = wall.results
    out = []

    def card(key, check, sub=None):
        text, state = status_text(L, check["status"])
        out.append({"key": key, "title": L[f"card_{key}"], "value": text,
                    "sub": check_sub(L, check) if sub is None else sub, "state": state})

    for key in STABILITY:
        card(key, res["stability"][key])
    g = res.get("global")
    if g and g.get("found"):
        chk = g["check"]
        card("global", chk, f"Bishop {L['value_FS']} = {num(chk['value'])} ≥ "
                            f"{num(chk['required'])}")
    else:
        out.append({"key": "global", "title": L["card_global"], "value": L["na_short"],
                    "sub": L["card_global_off"] if not wall.global_on else L["card_none"],
                    "state": "na"})
    des = res.get("design")
    if des:
        for key in ("stem", "toe", "heel"):
            sec = des["sections"][key]
            status = _section_status(sec)
            text, state = status_text(L, status)
            out.append({"key": key, "title": L[f"card_{key}"], "value": text,
                        "sub": f"{bars_text(sec)} · Md = {num(sec['Md'], 1)} kNm",
                        "state": state})
    heel = res["required_heel"]
    out.append({"key": "heel_length", "title": L["card_heel_length"],
                "value": f"{heel:.2f} m" if math.isfinite(heel) else L["card_none"],
                "sub": L["card_heel_sub"].format(heel=wall.heel),
                "state": ("ok" if heel <= wall.heel + 1e-6 else "bad")
                if math.isfinite(heel) else "bad"})
    if res["seismic"]:
        checks = list(res["seismic"]["stability"].values())
        if g and g.get("check_seismic"):
            checks.append(g["check_seismic"])
        counted = [c for c in checks if c["status"] != "N/A"]
        good = sum(c["status"] == "OK" for c in counted)
        state = "ok" if good == len(counted) else "bad"
        co = res["seismic"]["coefficients"]
        out.append({"key": "seismic", "title": L["card_seismic"],
                    "value": L["ok_short"] if state == "ok" else L["notok_short"],
                    "sub": L["card_seismic_sub"].format(n=good, total=len(counted),
                                                        kh=co["kh"]),
                    "state": state})
    return out


def stability_table(wall, lang: str = "en") -> dict:
    """Static (and seismic) stability checks side by side."""
    L = _lang(lang)
    res = wall.results
    seismic = res["seismic"]
    columns = ["", f"{L['value_FS']} · {L['plot_static']}", L["res_required"], ""]
    if seismic:
        columns += [f"{L['value_FS']} · {L['plot_seismic']}", L["res_required"], ""]
    rows = []
    g = res.get("global")
    names = list(STABILITY)
    if res["stability"]["allowable"]["status"] != "N/A":
        names.append("allowable")
    extra = []
    if g and g.get("found"):
        extra = [("global", g.get("check"), g.get("check_seismic")),
                 ("global_fellenius", g.get("check_fellenius"),
                  g.get("check_seismic_fellenius"))]
    for key in names:
        sets = [res["stability"][key]] + ([seismic["stability"][key]] if seismic else [])
        rows.append(_check_row(L, L[f"chk_{key}"], sets))
    for key, st, se in extra:
        sets = [st] + ([se] if seismic else [])
        # Fellenius' ordinary method is shown beside Bishop's for comparison;
        # the verdict on the global stability is Bishop's
        rows.append(_check_row(L, L[f"chk_{key}"], sets, info=key == "global_fellenius"))
    return {"columns": columns, "rows": rows}


def _check_row(L, label, checks, info: bool = False):
    cells, states = [label], [""]
    for check in checks:
        if check is None:
            cells += ["—", "—", L["na_short"]]
            states += ["", "", "na"]
            continue
        nd = 3 if check["kind"] == "limit" else 2
        text, state = status_text(L, check["status"])
        if info:
            text, state = L["info_short"], "na"
        cells += [num(check["value"], nd), num(check["required"], nd), text]
        states += ["", "", state]
    return {"cells": cells, "states": states}


def bearing_table(wall, lang: str = "en") -> dict:
    """Every bearing capacity method side by side."""
    L = _lang(lang)
    res = wall.results
    b = res["bearing"]
    FS = wall.crit["FS_bearing"]
    columns = [L["head_method"], L["head_Nc"], L["head_Nq"], L["head_Ng"], L["head_qult"],
               L["head_qallow"], L["value_FS"]]
    rows = []
    sigma = b.get("sigma_v", math.nan)
    for key, entry in b["methods"].items():
        q = entry["q_ult"]
        value = q / sigma if sigma > 0 else math.nan
        ok = value >= FS
        rows.append({"cells": [L[f"method_{key}"], num(entry["N"]["Nc"]), num(entry["N"]["Nq"]),
                               num(entry["N"]["Ngamma"]), num(q, 1), num(q / FS, 1),
                               num(value)],
                     "states": ["", "", "", "", "", "", "ok" if ok else "bad"],
                     "primary": key == b["primary"]})
    return {"columns": columns, "rows": rows}


def methods_table(wall, lang: str = "en") -> dict:
    """The earth pressure of every method on the virtual back."""
    L = _lang(lang)
    res = wall.results
    m = res["methods"]
    columns = [L["head_pmethod"], "K", "ω °", "Kh", L["head_P"], L["head_Ph"], L["head_Pv"]]
    rows = []
    for key, r in m["active"].items():
        rows.append({"cells": [L[f"pm_{key}"], num(r["K"], 4), num(r["omega"], 1),
                               num(r["Kh"], 4), num(r["P"], 1), num(r["Ph"], 1),
                               num(r["Pv"], 1)],
                     "states": [""] * 7, "primary": key == m["primary"]})
    for key, kp in m["passive"].items():
        rows.append({"cells": [L[f"pp_{key}"], num(kp, 3), "", "", "", "", ""],
                     "states": [""] * 7})
    s = res["seismic"]
    if s and math.isfinite(s["dynamic"].get("KAE", math.nan)):
        rows.append({"cells": [L["pm_mo_increment"], num(s["dynamic"]["KAE"], 4),
                               num(s["dynamic"]["omega"], 1), "", num(s["dynamic"]["dP"], 1),
                               "", ""], "states": [""] * 7})
    return {"columns": columns, "rows": rows}


def forces_table(wall, lang: str = "en", seismic: bool = False) -> dict:
    """The forces on the wall and their moments about the toe."""
    L = _lang(lang)
    res = wall.results
    f = res["seismic"]["forces"] if seismic and res["seismic"] else res["forces"]
    columns = [L["head_force"], L["head_V"], L["head_H"], L["head_arm"], L["head_moment"]]
    rows = []
    for name, v, x, _ in f["vertical"]:
        rows.append({"cells": [L.get(f"force_{name}", name), num(v, 1), "", num(x, 3),
                               num(v * x, 1)], "states": [""] * 5})
    for name, h, y, _ in f["horizontal"]:
        rows.append({"cells": [L.get(f"force_{name}", name), "", num(h, 1), num(y, 3),
                               num(-h * y, 1)], "states": [""] * 5})
    rows.append({"cells": ["Σ", num(f["V"], 1), num(f["H"], 1), "",
                           num(f["M_R"] - f["M_O"], 1)], "states": [""] * 5,
                 "primary": True})
    return {"columns": columns, "rows": rows}


def design_table(wall, lang: str = "en") -> dict:
    """The member design, section by section."""
    L = _lang(lang)
    des = wall.results["design"]
    columns = [L["head_member"], "h mm", "d mm", "Md kNm", "Vd kN", L["head_As_req"],
               L["head_As_min"], L["head_bars"], L["head_As_prov"], "Mr/Md", "Vcr/Vd",
               L["head_combo"], L["head_status"]]
    rows = []
    for key in SECTIONS:
        sec = des["sections"].get(key)
        if not sec:
            continue
        status = _section_status(sec)
        text, state = status_text(L, status)
        rows.append({"cells": [L[f"member_{key}"], num(sec["h"], 0), num(sec["d"], 0),
                               num(sec["Md"], 1), num(sec["Vd"], 1),
                               num(sec["As_req"], 0) if sec["As_req"] is not None else "∞",
                               num(sec["As_min"], 0), bars_text(sec), num(sec["As_prov"], 0),
                               num(sec["flexure"]["value"]), num(sec["shear"]["value"]),
                               sec["combo"], text],
                     "states": [""] * 9 + [
                         "ok" if sec["flexure"]["status"] == "OK" else "bad",
                         "ok" if sec["shear"]["status"] == "OK" else "bad", "", state]})
    for key, d in des["distribution"].items():
        rows.append({"cells": [L[f"member_{key}"], num(d["h"], 0), "", "", "",
                               num(d["As_req"], 0), "", f"Ø{d['phi']}/{d['s']:.0f}",
                               num(d["As_prov"], 0), "", "", "",
                               L["ok_short"] if d["ok"] else L["notok_short"]],
                     "states": [""] * 12 + ["ok" if d["ok"] else "bad"]})
    return {"columns": columns, "rows": rows}


def schedule_table(wall, lang: str = "en") -> dict:
    """The bar bending schedule, per metre of wall."""
    L = _lang(lang)
    des = wall.results["design"]
    columns = [L["sch_pos"], L["sch_name"], "Ø mm", L["sch_spacing"], L["sch_length"],
               L["sch_count"], L["sch_total"], L["sch_unit"], L["sch_mass"]]
    rows = []
    for r in des["schedule"]:
        rows.append({"cells": [str(r["pos"]), L[f"bar_{r['name']}"], str(r["phi"]),
                               f"{r['s'] * 1000:.0f}" if r["s"] > 0 else "—",
                               num(r["length"]), num(r["n"], 2 if not r["longitudinal"] else 0),
                               num(r["total_length"]), num(r["unit_mass"], 3),
                               num(r["mass"], 1)], "states": [""] * 9})
    q = des["quantities"]
    rows.append({"cells": ["", L["sch_sum"], "", "", "", "", "", "", num(q["steel"], 1)],
                 "states": [""] * 9, "primary": True})
    return {"columns": columns, "rows": rows}


def seismic_table(wall, lang: str = "en") -> dict:
    """The TBDY 2018 parameters of the earthquake."""
    L = _lang(lang)
    s = wall.results["seismic"]
    spec, co, dyn = s["spectrum"], s["coefficients"], s["dynamic"]
    rows = [[L["tb_site"], spec["site"]], ["Ss / S1", f"{spec['Ss']:.3f} / {spec['S1']:.3f}"],
            ["Fs / F1", f"{spec['Fs']:.3f} / {spec['F1']:.3f}"],
            ["SDS / SD1", f"{spec['SDS']:.3f} / {spec['SD1']:.3f}"],
            ["TA / TB / TL", f"{spec['TA']:.3f} / {spec['TB']:.3f} / {spec['TL']:.1f} s"],
            [L["tb_beta_r"], num(co["beta_r"])],
            ["kh / kv", f"{co['kh']:.3f} / {co['kv']:.3f}"],
            [L["tb_method"], L[f"sm_{wall.seismic_method}"]],
            ["KAE", num(dyn.get("KAE"), 4)],
            [L["tb_dP"], f"{num(dyn['dP'], 1)} kN/m @ {num(dyn['y_dP'], 2)} m"],
            [L["tb_inertia"], f"{num(dyn['kh'] * dyn['W_inertia'], 1)} kN/m"],
            [L["tb_governing"], L[f"kv_{s['governing']}"]]]
    return {"columns": [L["head_parameter"], L["head_value"]],
            "rows": [{"cells": r, "states": ["", ""]} for r in rows]}


def results_text(wall, lang: str = "en") -> str:
    """The whole analysis as text, in the chosen language."""
    L = _lang(lang)
    w, res = wall, wall.results
    g = w.geo
    lines = [L["res_title"], "-" * 96]
    lines.append(L["res_wall"].format(H=w.H, B=w.B, toe=w.toe, heel=w.heel, t_top=w.t_top,
                                      t_bot=w.t_bot, t_f=w.t_f, D=w.D, beta=w.beta))
    lines.append(L["res_method"].format(method=L[f"pm_{res['method']}"], K=res["K"],
                                        omega=res["omega"], h=g.h_virtual))
    f = res["forces"]
    lines.append(L["res_forces"].format(V=f["V"], Hf=f["H"], MR=f["M_R"], MO=f["M_O"],
                                        e=f["e"]))

    def table(title, tab):
        lines.extend(["", title])
        widths = [max(len(str(r["cells"][i])) for r in tab["rows"] + [{"cells": tab["columns"]}])
                  for i in range(len(tab["columns"]))]
        widths = [min(max(wd, 6), 36) for wd in widths]
        lines.append("  " + "  ".join(f"{str(c)[:wd]:<{wd}}" if i == 0 else
                                      f"{str(c)[:wd]:>{wd}}"
                                      for i, (c, wd) in enumerate(zip(tab["columns"], widths))))
        for r in tab["rows"]:
            lines.append("  " + "  ".join(f"{str(c)[:wd]:<{wd}}" if i == 0 else
                                          f"{str(c)[:wd]:>{wd}}"
                                          for i, (c, wd) in enumerate(zip(r["cells"], widths))))

    table(L["res_stability_title"], stability_table(w, lang))
    res_r = res["resistance"]
    lines.append("  " + L["res_sliding"].format(fr=res_r["friction"], ad=res_r["adhesion"],
                                                pp=res_r["passive"], R=res_r["R"]))
    bp = res["bearing"]["pressure"]
    lines.append("  " + L["res_base"].format(qt=bp["q_toe"], qh=bp["q_heel"],
                                             c=bp["contact"]))
    b = res["bearing"]
    if b["B_eff"] > 0:
        lines.append("  " + L["res_bearing"].format(B=b["B_eff"], s=b["sigma_v"], q=b["q_ult"],
                                                   method=L[f"method_{b['primary']}"]))
        table(L["res_bearing_title"], bearing_table(w, lang))
    table(L["res_methods_title"], methods_table(w, lang))
    if res["seismic"]:
        table(L["res_seismic_title"], seismic_table(w, lang))
    if res.get("design"):
        des = res["design"]
        mat = des["material"]
        lines.extend(["", L["res_design_title"],
                      "  " + L["res_material"].format(**mat)])
        table(L["res_sections_title"], design_table(w, lang))
        cut = des["curtailment"]
        lines.append("  " + (L["res_cut"].format(y=cut["y_cut"] - g.t_f)
                             if cut["enabled"] else L["res_no_cut"]))
        table(L["res_schedule_title"], schedule_table(w, lang))
        q = des["quantities"]
        lines.append("  " + L["res_quantities"].format(v=q["concrete"], s=q["steel"],
                                                       r=q["ratio"]))
    heel = res["required_heel"]
    lines += ["", ("  " + L["res_heel"].format(heel=heel, cur=w.heel))
              if math.isfinite(heel) else ("  " + L["res_no_heel"])]
    if res["warnings"]:
        lines += ["", L["warnings_title"]]
        lines += ["  • " + warning_text(lang, x) for x in res["warnings"]]
    return "\n".join(lines)


def warnings(wall, lang: str = "en") -> List[str]:
    return [warning_text(lang, w) for w in wall.results.get("warnings", [])]


def all_ok(res: dict) -> bool:
    checks = list(res["stability"].values())
    if res["seismic"]:
        checks += list(res["seismic"]["stability"].values())
    g = res.get("global")
    if g and g.get("found"):
        checks += [c for c in (g.get("check"), g.get("check_seismic")) if c]
    ok = all(c["status"] != "NOT OK" for c in checks)
    if res.get("design"):
        from .design import all_ok as design_ok
        ok = ok and design_ok(res["design"])
    return ok


def headline(wall, lang: str = "en") -> str:
    """One line for the status bar: the verdict, the weakest checks and the steel."""
    L = _lang(lang)
    res = wall.results
    st = res["stability"]
    verdict = L["ok_short"] if all_ok(res) else L["notok_short"]
    tail = ""
    if res.get("design"):
        tail = f" · {L['card_stem']} {bars_text(res['design']['sections']['stem'])}"
    return (f"{verdict} · {L['chk_sliding']} {L['value_FS']} = {num(st['sliding']['value'])} · "
            f"{L['chk_overturning']} {L['value_FS']} = {num(st['overturning']['value'])} · "
            f"{L['chk_bearing']} {L['value_FS']} = {num(st['bearing']['value'])}{tail}")
