"""
The analysis figures of SlipSurface IQ Wall.

Every figure is drawn on a Matplotlib `Figure` passed in by the caller, so the
same code serves the browser (PNG through `render`) and the report. Nothing
here needs a display.

    section        the wall to scale: the soils, the water, the surcharges,
                   the virtual back, the forces on the wall and the contact
                   pressure under the base
    pressure       the horizontal pressures on the virtual back — soil,
                   surcharges, water, the dynamic increment — and the passive
                   resistance in front
    methods        the earth pressure coefficient and thrust of every method
    stability      every stability check as its margin over the requirement,
                   static and seismic side by side
    bearing        the bearing capacity by every method beside the pressure
                   the wall puts on the foundation
    global         the critical slip circle, its slices and its factor
    stem           the moment and the shear down the stem for every
                   combination, their envelope and the capacity of the bars
    footing        the contact pressure under the base in every combination,
                   and the moments of the toe and the heel
    reinforcement  the reinforcement drawing of the section
    schedule       the bar bending schedule, with the shape of every bar
    spectrum       the TBDY 2018 design spectrum (with an earthquake only)
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Polygon, Rectangle

from . import drawing as drw
from . import tbdy
from .config import BAR_COLORS, METHOD_COLORS, PLOT_PALETTE, SOIL_FILL
from .i18n import TRANSLATIONS
from .plot_style import TITLE_FONT, label_box, style_axis, style_figure

#: The figures, in the order the interface offers them
PLOT_KEYS = ["section", "pressure", "methods", "stability", "bearing", "global", "stem",
             "footing", "reinforcement", "schedule", "spectrum"]

#: Colour of each check in the margin chart
CHECK_COLORS = {"sliding": "#A26A12", "overturning": "#8C6BB1", "eccentricity": "#5E8C4A",
                "bearing": PLOT_PALETTE["demand"], "global": "#5B8DB8"}

#: Line styles and colours of the combinations
COMBO_STYLES = {"C1": "-", "C2": "--", "C3": "-.", "C4": ":"}
COMBO_COLORS = ["#C6613F", "#5B8DB8", "#8C6BB1", "#4E9A8A", "#D9A55B", "#A26A12"]


def available_figures(wall) -> list:
    """The figures a finished analysis can draw."""
    res = wall.results
    keys = list(PLOT_KEYS)
    if not res.get("seismic"):
        keys.remove("spectrum")
    g = res.get("global")
    if not g or not g.get("found"):
        keys.remove("global")
    if not res.get("design"):
        for key in ("stem", "footing", "reinforcement", "schedule"):
            keys.remove(key)
    return keys


def margin(check: dict) -> float:
    """Value over required (required over value for a limit): 1 at the limit."""
    if check is None or check.get("status") == "N/A":
        return float("nan")
    value, required = check["value"], check["required"]
    if check.get("kind") == "limit":
        return required / value if value > 0 else math.inf
    return value / required if required else value


class Plotter:
    """Draws the figures of one finished `RetainingWall`."""

    def __init__(self, wall, lang: str = "en", theme="light", titles: bool = True):
        self.w = wall
        self.res = wall.results
        self.lang = lang
        self.L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        self.theme = theme
        self.titles = titles

    # ------------------------------------------------------------------ helpers
    def _fills(self):
        name = self.theme if isinstance(self.theme, str) else "light"
        return SOIL_FILL.get(name, SOIL_FILL["light"])

    def _title(self, fig, th, key: str, extra: str = "") -> None:
        if not self.titles:
            return
        text = self.L.get(f"fig_{key}", key)
        fig.suptitle(f"{text}{extra}", fontfamily=TITLE_FONT, fontsize=12.5, color=th["fg"])

    def _legend(self, ax, th, **kw) -> None:
        if not ax.get_legend_handles_labels()[0]:
            return
        legend = ax.legend(fontsize=8, frameon=True, **kw)
        legend.get_frame().set_facecolor(th["panel"])
        legend.get_frame().set_edgecolor(th["border"])
        for text in legend.get_texts():
            text.set_color(th["fg"])

    def draw(self, key: str, fig: Figure) -> None:
        if key not in PLOT_KEYS:
            raise ValueError(f"unknown figure: {key}")
        getattr(self, f"_draw_{key}")(fig)

    def _outline(self, ax, th, alpha: float = 1.0, bounds=None) -> None:
        """The wall's concrete, the soils beside it and the ground lines.

        `bounds` (left, right, bottom, top) widens the soils to a larger view.
        """
        w = self.w
        g = w.geo
        fills = self._fills()
        B, H = w.B, g.H
        span = max(B, H)
        left, right = -0.45 * span, B + 0.55 * span
        bottom = -0.35 * span - g.key_depth
        top = max(g.ground_back(right), H) + 0.25 * span
        if bounds:
            left, right, bottom, top = bounds
        ts = math.tan(math.radians(w.toe_slope))
        fg = g.front_ground
        ax.add_patch(Rectangle((left, bottom), right - left, -bottom,
                               facecolor=fills["foundation"], edgecolor=th["border"],
                               linewidth=0.8, zorder=1, alpha=alpha))
        ax.add_patch(Polygon([(left, 0.0), (0.0, 0.0), (0.0, fg), (left, fg - abs(left) * ts)],
                             closed=True, facecolor=fills["front"], edgecolor=th["border"],
                             linewidth=0.8, zorder=1, alpha=alpha))
        toe_soil = g.toe_soil()
        if toe_soil:
            ax.add_patch(Polygon(toe_soil, closed=True, facecolor=fills["front"],
                                 edgecolor=th["border"], linewidth=0.8, zorder=1, alpha=alpha))
        ax.add_patch(Polygon([(B, 0.0), (right, 0.0), (right, g.ground_back(right)),
                              (B, g.h_virtual)], closed=True, facecolor=fills["backfill"],
                             edgecolor=th["border"], linewidth=0.8, zorder=1, alpha=alpha))
        ax.add_patch(Polygon(g.heel_soil(), closed=True, facecolor=fills["backfill"],
                             edgecolor=th["border"], linewidth=0.8, zorder=2, alpha=alpha))
        for poly in g.concrete_parts().values():
            ax.add_patch(Polygon(poly, closed=True, facecolor=PLOT_PALETTE["concrete"],
                                 edgecolor=PLOT_PALETTE["concrete_edge"], linewidth=1.0,
                                 zorder=4))
        # water
        if w.hw > 0:
            ax.plot([g.x_back_base, right], [w.hw, w.hw], color=PLOT_PALETTE["water"],
                    linewidth=1.4, linestyle="--", zorder=5)
            ax.text(right, w.hw, " " + self.L["plot_water"], fontsize=8, ha="right",
                    va="bottom", color=PLOT_PALETTE["water"], zorder=6)
        if w.hf > 0:
            ax.plot([left, g.toe], [w.hf, w.hf], color=PLOT_PALETTE["water"],
                    linewidth=1.4, linestyle="--", zorder=5)
        if not (w.hw > 0 or w.hf > 0) and -w.dw > bottom:
            ax.axhline(-w.dw, color=PLOT_PALETTE["water"], linewidth=1.2, linestyle="--",
                       zorder=3)
            ax.text(right - 0.1, -w.dw, self.L["plot_water"], fontsize=8, ha="right",
                    va="bottom", color=PLOT_PALETTE["water"], zorder=6)
        ax.set_xlim(left, right)
        ax.set_ylim(bottom, top)
        ax.set_aspect("equal", adjustable="box")

    # ------------------------------------------------------------------ section
    def _draw_section(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, grid=False)
        w, res = self.w, self.res
        g = w.geo
        B, H = w.B, g.H
        span = max(B, H)
        self._outline(ax, th)

        # the virtual back
        ax.plot([B, B], [0.0, g.h_virtual], color=PLOT_PALETTE["thrust"], linewidth=1.2,
                linestyle=":", zorder=6)
        ax.text(B, g.h_virtual, " " + self.L["plot_virtual_back"], fontsize=8,
                color=PLOT_PALETTE["thrust"], va="bottom", ha="left", zorder=7)

        # surcharges
        q = w.q_dead + w.q_live
        arrow = 0.07 * span
        if q > 0:
            xs = np.linspace(g.x_back_top + 0.15, B + 0.45 * span, 9)
            for x in xs:
                y = g.ground_back(x)
                ax.annotate("", xy=(x, y), xytext=(x, y + arrow),
                            arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["surcharge"],
                                            lw=1.0), zorder=7)
            xm = xs[len(xs) // 2]
            ax.text(xm, g.ground_back(xm) + arrow * 1.15, f"q = {q:.1f} kPa", fontsize=8.5,
                    ha="center", va="bottom", color=th["fg"], bbox=label_box(th, 0.85),
                    zorder=8)

        # forces: the thrust on the virtual back and the weights
        f = res["forces"]
        scale = 0.25 * span / max([abs(v) for _, v, _, _ in f["vertical"]]
                                  + [abs(h) for _, h, _, _ in f["horizontal"]] + [1.0])
        for name, h, y, _ in f["horizontal"]:
            if h <= 0:
                continue
            x0 = B + 0.02 * span
            ax.annotate("", xy=(x0, y), xytext=(x0 + h * scale, y),
                        arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["thrust"],
                                        lw=1.6), zorder=8)
            ax.text(x0 + h * scale, y, f" {name.replace('_h', '')} {h:.0f}", fontsize=7.5,
                    color=th["fg"], va="center", ha="left", zorder=8)
        for name, v, x, _ in f["vertical"]:
            if v <= 0 or not name.startswith("W_"):
                continue
            weights = {n: yy for n, _, _, yy in w.weights()}
            y = weights.get(name, 0.0)
            ax.annotate("", xy=(x, y - v * scale * 0.5), xytext=(x, y),
                        arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["weight"],
                                        lw=1.3), zorder=8)
            ax.plot([x], [y], "o", color=PLOT_PALETTE["weight"], markersize=3, zorder=9)

        # the contact pressure under the base
        bp = res["bearing"]["pressure"]
        if bp["q_max"] > 0 and math.isfinite(bp["q_max"]):
            xs = np.linspace(0.0, B, 60)
            qs = np.asarray(w.pressure_at(xs, bp, B))
            depth = 0.18 * span / bp["q_max"]
            y0 = -g.key_depth - 0.03 * span
            ax.fill_between(xs, y0, y0 - qs * depth, color=PLOT_PALETTE["pressure"],
                            alpha=0.55, zorder=6, linewidth=0)
            ax.plot(xs, y0 - qs * depth, color=PLOT_PALETTE["pressure"], linewidth=1.2,
                    zorder=6)
            ax.text(0.0, y0 - bp["q_toe"] * depth, f"{bp['q_toe']:.0f} kPa ", fontsize=8,
                    ha="right", va="center", color=th["fg"], zorder=8)
            ax.text(B, y0 - bp["q_heel"] * depth, f" {bp['q_heel']:.0f} kPa", fontsize=8,
                    ha="left", va="center", color=th["fg"], zorder=8)
        # the resultant
        xr = f["x_r"]
        if 0 <= xr <= B:
            ax.plot([xr], [0.0], marker="v", color=PLOT_PALETTE["demand"], markersize=8,
                    zorder=9)
            ax.text(xr, 0.02 * span, f"e = {f['e']:.2f} m", fontsize=8, ha="center",
                    va="bottom", color=th["fg"], bbox=label_box(th, 0.8), zorder=9)
        ax.set_xlabel(self.L["plot_x"])
        ax.set_ylabel(self.L["plot_y"])
        self._title(fig, th, "section")

    # ------------------------------------------------------------------ pressure
    def _draw_pressure(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        w, res = self.w, self.res
        prof = res["forces"]["profile"]
        y = prof["y"]
        cw = math.cos(math.radians(prof["omega"]))
        layers = [("soil", self.L["plot_p_soil"], PLOT_PALETTE["pressure"], cw),
                  ("dead", self.L["plot_p_dead"], "#A7B8A0", cw),
                  ("live", self.L["plot_p_live"], PLOT_PALETTE["surcharge"], cw),
                  ("water", self.L["plot_p_water"], PLOT_PALETTE["water"], 1.0)]
        base = np.zeros_like(y)
        for key, label, color, factor in layers:
            p = prof[key] * factor
            if not np.any(p > 1e-9):
                continue
            ax.fill_betweenx(y, base, base + p, color=color, alpha=0.55, linewidth=0,
                             label=label)
            base = base + p
        ax.plot(base, y, color=th["fg"], linewidth=1.2)
        total_h = sum(hf for n, hf, _, _ in res["forces"]["horizontal"] if hf > 0)
        s = res["seismic"]
        if s:
            dyn = s["dynamic"]
            from .engine import _increment_profile
            dp = _increment_profile(dyn["dP"] * math.cos(math.radians(dyn["omega"])), 0.0,
                                    res["h"], w.dyn_height, y)
            ax.plot(base + dp, y, color=PLOT_PALETTE["seismic"], linewidth=1.6,
                    linestyle="--", label=self.L["plot_p_dynamic"])
        pas = res.get("passive")
        if pas:
            ax.fill_betweenx(pas["profile_y"], 0, -pas["profile_p"] * w.passive_ratio,
                             color=PLOT_PALETTE["passive"], alpha=0.5, linewidth=0,
                             label=self.L["plot_p_passive"])
        ax.axhline(0.0, color=th["fg_dim"], linewidth=0.8)
        ax.axvline(0.0, color=th["fg_dim"], linewidth=0.8)
        ax.set_xlabel(self.L["plot_p_axis"])
        ax.set_ylabel(self.L["plot_y"])
        ax.text(0.98, 0.97, self.L["plot_p_info"].format(
            K=prof["K"], omega=prof["omega"], H=total_h,
            method=self.L[f"pm_{res['method']}"]),
            transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=th["fg"],
            bbox=label_box(th))
        self._legend(ax, th, loc="lower right")
        self._title(fig, th, "pressure")

    # ------------------------------------------------------------------ methods
    def _draw_methods(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        for ax in (ax1, ax2):
            style_axis(ax, th, axis="y")
        m = self.res["methods"]
        names = list(m["active"])
        labels = [self.L[f"pm_{n}"] for n in names]
        Ks = [m["active"][n]["Kh"] for n in names]
        Ps = [m["active"][n]["Ph"] for n in names]
        colors = [METHOD_COLORS.get(n, th["fg"]) for n in names]
        s = self.res["seismic"]
        if s and math.isfinite(s["dynamic"].get("KAE", math.nan)):
            # the seismic coefficient beside the static ones, and the dynamic
            # increment of the thrust beside the static thrusts
            labels.append("M–O: KAE, ΔPAE")
            Ks.append(s["dynamic"]["KAE"])
            Ps.append(s["dynamic"]["dP"])
            colors.append(METHOD_COLORS["mononobe_okabe"])
        x = np.arange(len(labels))
        for ax, values, ylabel in ((ax1, Ks, self.L["plot_Kh"]), (ax2, Ps, self.L["plot_Ph"])):
            edge = [th["fg"] if i < len(names) and names[i] == m["primary"] else "none"
                    for i in range(len(labels))]
            bars = ax.bar(x, [v if math.isfinite(v) else 0 for v in values], color=colors,
                          edgecolor=edge, linewidth=1.6, zorder=3)
            for bar, v in zip(bars, values):
                if math.isfinite(v):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            f"{v:.3f}" if ax is ax1 else f"{v:.1f}", ha="center",
                            va="bottom", fontsize=8, color=th["fg"])
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
            ax.set_ylabel(ylabel)
        self._title(fig, th, "methods")
        fig.tight_layout(rect=(0, 0, 1, 0.94) if self.titles else None)

    # ------------------------------------------------------------------ stability
    def _draw_stability(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, axis="x")
        res = self.res
        keys = ["sliding", "overturning", "eccentricity", "bearing"]
        sets = [("static", res["stability"], None)]
        g = res.get("global")
        if res["seismic"]:
            sets.append(("seismic", res["seismic"]["stability"], None))
        rows = []
        for tag, checks, _ in sets:
            for key in keys:
                rows.append((f"{self.L['chk_' + key]} · {self.L['plot_' + tag]}",
                             margin(checks[key]), CHECK_COLORS[key], tag))
            if g and g.get("found"):
                chk = g.get("check" if tag == "static" else "check_seismic")
                if chk:
                    rows.append((f"{self.L['chk_global']} · {self.L['plot_' + tag]}",
                                 margin(chk), CHECK_COLORS["global"], tag))
        ys = np.arange(len(rows))[::-1]
        values = [r[1] if math.isfinite(r[1]) else 3.0 for r in rows]
        bars = ax.barh(ys, values, color=[r[2] for r in rows], alpha=0.85, zorder=3,
                       hatch=None)
        for bar, r in zip(bars, rows):
            if r[3] == "seismic":
                bar.set_hatch("//")
            v = r[1]
            text = "∞" if not math.isfinite(v) else f"{v:.2f}"
            ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {text}",
                    va="center", fontsize=8, color=th["fg"])
        ax.axvline(1.0, color=PLOT_PALETTE["required"], linewidth=1.4, linestyle="--",
                   zorder=4)
        ax.set_yticks(ys)
        ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
        ax.set_xlabel(self.L["plot_margin"])
        ax.set_xlim(0, max(max(values) * 1.15, 1.5))
        self._title(fig, th, "stability")

    # ------------------------------------------------------------------ bearing
    def _draw_bearing(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, axis="y")
        b = self.res["bearing"]
        names = list(b["methods"])
        if not names:
            ax.text(0.5, 0.5, self.L["plot_no_bearing"], transform=ax.transAxes,
                    ha="center", color=th["fg"])
            self._title(fig, th, "bearing")
            return
        x = np.arange(len(names))
        q = [b["methods"][n]["q_ult"] for n in names]
        colors = [METHOD_COLORS.get(n, th["fg"]) for n in names]
        bars = ax.bar(x, q, color=colors, zorder=3,
                      edgecolor=[th["fg"] if n == b["primary"] else "none" for n in names],
                      linewidth=1.6)
        for bar, v in zip(bars, q):
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.0f}", ha="center",
                    va="bottom", fontsize=8, color=th["fg"])
        FS = self.w.crit["FS_bearing"]
        ax.plot(x, np.array(q) / FS, "o", color=PLOT_PALETTE["allowable"], zorder=4,
                label=self.L["plot_allow"].format(FS=FS))
        ax.axhline(b["sigma_v"], color=PLOT_PALETTE["applied"], linewidth=1.5, linestyle="--",
                   label=self.L["plot_applied"], zorder=5)
        ax.axhline(b["pressure"]["q_max"], color=PLOT_PALETTE["pressure"], linewidth=1.2,
                   linestyle=":", label=self.L["plot_qmax"], zorder=5)
        if self.w.q_allow > 0:
            ax.axhline(self.w.q_allow, color=PLOT_PALETTE["capacity"], linewidth=1.2,
                       label=self.L["plot_q_allow_given"], zorder=5)
        ax.set_xticks(x)
        ax.set_xticklabels([self.L[f"method_{n}"] for n in names], fontsize=8.5)
        ax.set_ylabel(self.L["plot_q_axis"])
        self._legend(ax, th, loc="upper right")
        self._title(fig, th, "bearing")

    # ------------------------------------------------------------------ global
    def _draw_global(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, grid=False)
        gl = self.res["global"]
        g = self.w.geo
        span = max(self.w.B, g.H)
        cases = [("static", gl["static"], PLOT_PALETTE["failure"])]
        if gl.get("seismic") and gl["seismic"].get("found"):
            cases.append(("seismic", gl["seismic"], PLOT_PALETTE["seismic"]))
        circles = [case["circle"] for _, case, _ in cases]
        left = min([c["xL"] for c in circles] + [-0.45 * span]) - 0.5
        right = max([c["xR"] for c in circles] + [self.w.B + 0.55 * span]) + 0.5
        bottom = min([c["yc"] - c["R"] for c in circles] + [-0.35 * span]) - 0.5
        top = max([c["yc"] for c in circles]) + 0.5
        self._outline(ax, th, alpha=0.8, bounds=(left, right, bottom, top))
        lines = []
        for tag, case, color in cases:
            c = case["circle"]
            t = np.linspace(0, 2 * math.pi, 400)
            xs = c["xc"] + c["R"] * np.cos(t)
            ys = c["yc"] + c["R"] * np.sin(t)
            mask = (xs >= c["xL"]) & (xs <= c["xR"]) & (ys <= c["yc"])
            order = np.argsort(xs[mask])
            ax.plot(xs[mask][order], ys[mask][order], color=color, linewidth=2.0, zorder=7)
            ax.plot([c["xc"]], [c["yc"]], "+", color=color, markersize=9, zorder=7)
            if tag == "static":
                sl = c["slices"]
                for x, b, y in zip(sl["x"], sl["b"], sl["y"]):
                    ax.plot([x - b / 2, x - b / 2], [y, y + 0.02 * span], color=color,
                            linewidth=0.4, zorder=6)
            lines.append(self.L["plot_global_info"].format(
                case=self.L["plot_" + tag], bishop=case["bishop"], fellenius=case["fellenius"]))
        ax.text(0.98, 0.03, "\n".join(lines), transform=ax.transAxes, ha="right", va="bottom",
                fontsize=9, color=th["fg"], bbox=label_box(th), zorder=10)
        ax.set_xlabel(self.L["plot_x"])
        ax.set_ylabel(self.L["plot_y"])
        self._title(fig, th, "global")

    # ------------------------------------------------------------------ stem
    def _draw_stem(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122, sharey=ax1)
        for ax in (ax1, ax2):
            style_axis(ax, th)
        des = self.res["design"]
        st = des["stem_forces"]
        y = st["y"]
        for name, c in st["combos"].items():
            style = COMBO_STYLES.get(name[:2], "-")
            ax1.plot(c["M"], y, linestyle=style, linewidth=0.9, color=th["fg_dim"],
                     label=name)
            ax2.plot(c["V"], y, linestyle=style, linewidth=0.9, color=th["fg_dim"],
                     label=name)
        ax1.plot(st["M"], y, color=PLOT_PALETTE["moment"], linewidth=2.2,
                 label=self.L["plot_envelope"])
        ax2.plot(st["V"], y, color=PLOT_PALETTE["shear"], linewidth=2.2,
                 label=self.L["plot_envelope"])
        cut = des["curtailment"]
        ax1.plot(cut["Mr"], y, color=PLOT_PALETTE["capacity"], linewidth=1.8,
                 label=self.L["plot_Mr"])
        if cut["enabled"]:
            ax1.axhline(cut["y_cut"], color=PLOT_PALETTE["capacity"], linestyle=":",
                        linewidth=1.0)
            ax1.text(max(cut["Mr"]) * 0.98, cut["y_cut"],
                     self.L["plot_cut"].format(y=cut["y_cut"] - self.w.geo.t_f),
                     ha="right", va="bottom", fontsize=8, color=th["fg"])
        sec = des["sections"]["stem"]
        ax2.axvline(sec["Vcr"], color=PLOT_PALETTE["capacity"], linewidth=1.6,
                    label="Vcr")
        ax1.set_xlabel(self.L["plot_M_axis"])
        ax2.set_xlabel(self.L["plot_V_axis"])
        ax1.set_ylabel(self.L["plot_y"])
        ax1.set_xlim(left=0)
        ax2.set_xlim(left=0)
        self._legend(ax1, th, loc="upper right")
        self._legend(ax2, th, loc="upper right")
        self._title(fig, th, "stem")

    # ------------------------------------------------------------------ footing
    def _draw_footing(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        style_axis(ax, th)
        style_axis(ax2, th, axis="y")
        w = self.w
        g = w.geo
        des = self.res["design"]
        foot = des["footing_forces"]
        xs = np.linspace(0.0, w.B, 200)
        for i, (name, c) in enumerate(foot["all"].items()):
            bp = c["pressure"]
            if not math.isfinite(bp["q_max"]):
                continue
            ax.plot(xs, w.pressure_at(xs, bp, w.B), linestyle=COMBO_STYLES.get(name[:2], "-"),
                    color=COMBO_COLORS[i % len(COMBO_COLORS)], linewidth=1.3, label=name)
        service = self.res["bearing"]["pressure"]
        if math.isfinite(service["q_max"]):
            ax.plot(xs, w.pressure_at(xs, service, w.B), color=th["fg"], linewidth=2.0,
                    label=self.L["plot_service"])
        for x in (g.toe, g.x_back_base):
            ax.axvline(x, color=th["fg_dim"], linewidth=0.8, linestyle=":")
        ax.invert_yaxis()
        ax.set_xlabel(self.L["plot_x"])
        ax.set_ylabel(self.L["plot_q_axis"])
        self._legend(ax, th, loc="lower right", ncol=3)
        names = list(foot["all"])
        x = np.arange(len(names))
        # a combination the wall does not survive has no moment to show
        toe = [v if math.isfinite(v) else 0.0 for v in (foot["all"][n]["M_toe"] for n in names)]
        heel = [v if math.isfinite(v) else 0.0
                for v in (foot["all"][n]["M_heel"] for n in names)]
        ax2.bar(x - 0.2, toe, width=0.4, color=PLOT_PALETTE["shear"],
                label=self.L["plot_M_toe"], zorder=3)
        ax2.bar(x + 0.2, heel, width=0.4, color=PLOT_PALETTE["moment"],
                label=self.L["plot_M_heel"], zorder=3)
        ax2.set_xticks(x)
        ax2.set_xticklabels(names)
        ax2.set_ylabel(self.L["plot_M_axis"])
        ax2.axhline(0, color=th["fg_dim"], linewidth=0.8)
        self._legend(ax2, th, loc="upper right")
        self._title(fig, th, "footing")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    # ------------------------------------------------------------------ reinforcement
    def _draw_reinforcement(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        ax.set_facecolor(th["panel"])
        ax.set_axis_off()
        d = drw.build(self.w, self.lang)
        x0, x1, y0, y1 = d["extent"]
        pad = 0.03 * max(x1 - x0, y1 - y0)
        ax.set_xlim(x0 - pad, x1 + pad)
        ax.set_ylim(y0 - pad, y1 + pad)
        ax.set_aspect("equal")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.93 if self.titles else 0.99,
                            bottom=0.01)
        ax.apply_aspect()
        bbox = ax.get_window_extent()
        points_per_unit = bbox.height / (ax.get_ylim()[1] - ax.get_ylim()[0]) * 72.0 / fig.dpi
        colors = {"CONCRETE": th["fg"], "GROUND": PLOT_PALETTE["dimension"],
                  "DIMENSION": th["fg_dim"], "LEADER": th["fg_dim"], "TEXT": th["fg"]}
        fills = self._fills()
        g = self.w.geo
        for poly in g.concrete_parts().values():
            ax.add_patch(Polygon(poly, closed=True, facecolor=PLOT_PALETTE["concrete"],
                                 edgecolor="none", alpha=0.35, zorder=1))
        ax.add_patch(Polygon(g.heel_soil(), closed=True, facecolor=fills["backfill"],
                             edgecolor="none", alpha=0.25, zorder=0))
        for it in d["items"]:
            if it["type"] == "poly":
                color = (BAR_COLORS.get(it["family"], PLOT_PALETTE["rebar"]) if it["family"]
                         else colors.get(it["layer"], th["fg"]))
                pts = list(it["points"]) + ([it["points"][0]] if it["closed"] else [])
                ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color,
                        linewidth=it["width"], solid_capstyle="round", zorder=3)
            elif it["type"] == "circle":
                color = (BAR_COLORS.get(it["family"], PLOT_PALETTE["rebar"]) if it["family"]
                         else colors.get(it["layer"], th["fg"]))
                ax.add_patch(Circle(it["center"], it["r"], facecolor=color if it["fill"] else
                                    "none", edgecolor=color, zorder=4))
            else:
                size = max(it["height"] * points_per_unit * 0.95, 4.5)
                ax.text(it["pos"][0], it["pos"][1], it["text"], fontsize=size,
                        ha=it["align"], va=it["valign"], rotation=it["angle"],
                        color=colors.get(it["layer"], th["fg"]), zorder=5,
                        rotation_mode="anchor")
        self._title(fig, th, "reinforcement")

    # ------------------------------------------------------------------ schedule
    def _draw_schedule(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        ax.set_facecolor(th["panel"])
        ax.set_axis_off()
        des = self.res["design"]
        rows = des["schedule"]
        bars = {b["pos"]: b for b in des["bars"]}
        heads = [self.L["sch_pos"], "Ø", self.L["sch_spacing"], self.L["sch_shape"],
                 self.L["sch_length"], self.L["sch_count"], self.L["sch_total"],
                 self.L["sch_mass"]]
        widths = [0.06, 0.06, 0.10, 0.36, 0.10, 0.10, 0.11, 0.11]
        edges = np.concatenate([[0.0], np.cumsum(widths)])
        n = len(rows) + 2
        row_h = 1.0 / n
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        def cell(i, j, text, **kw):
            ax.text((edges[j] + edges[j + 1]) / 2, 1 - (i + 0.5) * row_h, text, ha="center",
                    va="center", fontsize=8.5, color=th["fg"], **kw)

        ax.add_patch(Rectangle((0, 1 - row_h), 1, row_h, facecolor=th["hover"],
                               edgecolor="none"))
        for j, h in enumerate(heads):
            cell(0, j, h, fontweight="bold")
        for i in range(n + 1):
            ax.plot([0, 1], [1 - i * row_h] * 2, color=th["border"], linewidth=0.6)
        for e in edges:
            ax.plot([e, e], [1 - (n - 1) * row_h, 1], color=th["border"], linewidth=0.6)
        total = 0.0
        for i, r in enumerate(rows, start=1):
            b = bars[r["pos"]]
            cell(i, 0, str(r["pos"]))
            cell(i, 1, str(r["phi"]))
            cell(i, 2, f"{r['s'] * 1000:.0f}" if r["s"] > 0 else "—")
            cell(i, 4, f"{r['length']:.2f}")
            cell(i, 5, f"{r['n']:.2f}" if not r["longitudinal"] else f"{r['n']:.0f}")
            cell(i, 6, f"{r['total_length']:.2f}")
            cell(i, 7, f"{r['mass']:.1f}")
            total += r["mass"]
            # the shape, lengthwise and not to scale, in its own cell
            x_lo, x_hi = edges[3] + 0.02, edges[4] - 0.02
            y_hi = 1 - i * row_h - 0.22 * row_h
            y_lo = 1 - (i + 1) * row_h + 0.22 * row_h
            color = BAR_COLORS.get(b["family"], PLOT_PALETTE["rebar"])
            if b["shape"]:
                pts = np.array(b["shape"], dtype=float)
                if np.ptp(pts[:, 1]) > np.ptp(pts[:, 0]):
                    pts = np.column_stack([pts[:, 1], -pts[:, 0]])
                w_, h_ = np.ptp(pts[:, 0]), np.ptp(pts[:, 1])
                sx = (x_hi - x_lo) / max(w_, 1e-9)
                sy = min((y_hi - y_lo) / max(h_, 1e-9), 6.0 * sx)
                cx = (x_lo + x_hi) / 2 - (pts[:, 0].min() + w_ / 2) * sx
                cy = (y_lo + y_hi) / 2 - (pts[:, 1].min() + h_ / 2) * sy
                ax.plot(pts[:, 0] * sx + cx, pts[:, 1] * sy + cy, color=color, linewidth=1.8)
                for (p, q), seg in zip(zip(pts[:-1], pts[1:]), r["segments"]):
                    mx = (p[0] + q[0]) / 2 * sx + cx
                    my = (p[1] + q[1]) / 2 * sy + cy
                    ax.text(mx, my, f" {seg:.2f}", fontsize=6.5, color=th["fg_dim"],
                            ha="center", va="bottom")
            else:
                ax.plot([x_lo + 0.02, x_hi - 0.02], [(y_lo + y_hi) / 2] * 2, color=color,
                        linewidth=1.8)
                ax.text((x_lo + x_hi) / 2, (y_lo + y_hi) / 2, self.L["sch_along"],
                        fontsize=6.5, color=th["fg_dim"], ha="center", va="bottom")
        q = des["quantities"]
        cell(n - 1, 3, self.L["sch_totals"].format(v=q["concrete"], r=q["ratio"]),
             fontweight="bold")
        cell(n - 1, 7, f"{total:.1f}", fontweight="bold")
        self._title(fig, th, "schedule", f" — {self.L['sch_per_metre']}")

    # ------------------------------------------------------------------ spectrum
    def _draw_spectrum(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        s = self.res["seismic"]
        spec = s["spectrum"]
        T = np.linspace(0.0, 4.0, 400)
        ax.plot(T, tbdy.sae(T, spec), color=PLOT_PALETTE["seismic"], linewidth=2.0,
                label="Sae(T)")
        for key in ("TA", "TB"):
            ax.axvline(spec[key], color=th["fg_dim"], linewidth=0.8, linestyle=":")
            ax.text(spec[key], spec["SDS"] * 1.04, f" {key} = {spec[key]:.3f} s", fontsize=8,
                    color=th["fg"], rotation=90, va="bottom", ha="right")
        co = s["coefficients"]
        ax.axhline(0.4 * spec["SDS"], color=PLOT_PALETTE["demand"], linewidth=1.2,
                   linestyle="--", label="0.4·SDS")
        ax.text(0.98, 0.97, self.L["plot_spectrum_info"].format(
            site=spec["site"], Ss=spec["Ss"], S1=spec["S1"], Fs=spec["Fs"], F1=spec["F1"],
            SDS=spec["SDS"], SD1=spec["SD1"], kh=co["kh"], kv=co["kv"], br=co["beta_r"]),
            transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=th["fg"],
            bbox=label_box(th))
        ax.set_xlabel(self.L["plot_T"])
        ax.set_ylabel(self.L["plot_Sae"])
        ax.set_xlim(0, 4.0)
        ax.set_ylim(0, spec["SDS"] * 1.35)
        self._legend(ax, th, loc="center right")
        self._title(fig, th, "spectrum")
