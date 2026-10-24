"""
The analysis figures of SlipSurface IQ Bearing.

Every figure is drawn on a Matplotlib `Figure` passed in by the caller, so the
same code serves the browser (PNG through `render`) and the report. Nothing
here needs a display.

    schematic    section through the foundation: layers, water table, footing,
                 the actions on it and the Prandtl failure mechanism
    factors      Nc, Nq and Nγ against φ' for every method, the design value
                 marked on each curve
    comparison   the ultimate and allowable capacity of every method beside
                 the pressure the foundation actually carries
    components   the cohesion, surcharge and self-weight terms of each method
    pressure     the contact pressure under the base and the effective area
    width        capacity and factor of safety against the width B
    depth        capacity and factor of safety against the founding depth Df
    envelope     the V–H failure envelope, with the applied load on it
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle

from ..common.factors import bearing_factors
from .capacity import wedge_geometry
from .config import METHOD_COLORS, PLOT_PALETTE, SOIL_FILL
from .i18n import TRANSLATIONS
from .plot_style import TITLE_FONT, label_box, style_axis, style_figure

#: The figures, in the order the interface offers them
PLOT_KEYS = ["schematic", "factors", "comparison", "components", "pressure",
             "width", "depth", "envelope"]

#: The factor sets drawn on the `factors` figure
CURVE_METHODS = ["terzaghi", "meyerhof", "hansen", "vesic", "ec7"]

#: Points of the sweeps behind the design charts
SWEEP_POINTS = 24


class Plotter:
    """Draws the figures of one finished `BearingAnalysis`."""

    def __init__(self, analysis, lang: str = "en", theme="light", titles: bool = True):
        self.a = analysis
        self.res = analysis.results
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
        fig.suptitle(f"{text}{extra}", fontfamily=TITLE_FONT, fontsize=12.5,
                     color=th["fg"])

    def _method_label(self, key: str) -> str:
        return self.L.get(f"method_{key}", key)

    def _entries(self):
        """Every method that produced a capacity, the equation ones first."""
        out = [(key, entry) for key, entry in self.res["methods"].items()]
        out += [(key, entry) for key, entry in self.res["others"].items()]
        return out

    def draw(self, key: str, fig: Figure) -> None:
        if key not in PLOT_KEYS:
            raise ValueError(f"unknown figure: {key}")
        getattr(self, f"_draw_{key}")(fig)

    # ------------------------------------------------------------------ section
    def _draw_schematic(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, grid=False)
        a, res = self.a, self.res
        geom = res["geometry"]
        B, Df = a.B, a.Df
        phi = res["params"]["drained"]["phi"]
        mech = wedge_geometry(geom["B_eff"], phi if geom["B_eff"] > 0 else 0.0)

        half = max(1.15 * mech["extent"], 1.8 * B)
        bottom = max(Df + 1.35 * mech["depth"], a.profile.depth * 0.6, Df + B)
        bottom = min(bottom, a.profile.depth)
        if bottom <= Df:
            bottom = Df + B

        fills = self._fills()
        for layer in a.profile.layers:
            if layer["top"] >= bottom:
                break
            top, base = layer["top"], min(layer["bottom"], bottom)
            ax.add_patch(Rectangle((-half, top), 2 * half, base - top,
                                   facecolor=fills[layer["behaviour"]], edgecolor=th["border"],
                                   linewidth=0.8, zorder=1))
            ax.text(-half * 0.97, 0.5 * (top + base), layer["name"], fontsize=8.5,
                    va="center", color=th["fg"], zorder=6, bbox=label_box(th, 0.8))

        # the water table
        if a.profile.zw < bottom:
            ax.axhline(a.profile.zw, color=PLOT_PALETTE["water"], linewidth=1.4,
                       linestyle="--", zorder=4)
            ax.text(half * 0.9, a.profile.zw, self.L["plot_water"], fontsize=8,
                    ha="right", va="bottom", color=PLOT_PALETTE["water"], zorder=6)

        # the failure mechanism: it belongs to the effective width, so it is
        # centred on the resultant and mirrored about it
        shift = geom["e_B"] if a.shape != "circle" else 0.0
        for sign in (1, -1):
            wedge = [(shift + sign * x, Df + z) for x, z in mech["wedge"]]
            ax.add_patch(Polygon(wedge, closed=True, facecolor=PLOT_PALETTE["wedge"],
                                 alpha=0.45, edgecolor=PLOT_PALETTE["spiral"],
                                 linewidth=1.1, zorder=3))
            spiral = np.array([(shift + sign * x, Df + z) for x, z in mech["spiral"]])
            ax.plot(spiral[:, 0], spiral[:, 1], color=PLOT_PALETTE["spiral"],
                    linewidth=1.5, zorder=3)
            passive = np.array([(shift + sign * x, Df + z) for x, z in mech["passive"]])
            ax.plot(passive[:, 0], passive[:, 1], color=PLOT_PALETTE["spiral"],
                    linewidth=1.5, zorder=3)

        # the footing
        thickness = max(0.12 * B, 0.15)
        ax.add_patch(Rectangle((-B / 2, Df - thickness), B, thickness,
                               facecolor=PLOT_PALETTE["footing"], edgecolor=th["border"],
                               linewidth=1.0, zorder=5))
        ax.plot([-half, -B / 2], [Df, Df], color=th["border"], linewidth=0.8, zorder=4)
        ax.plot([B / 2, half], [Df, Df], color=th["border"], linewidth=0.8, zorder=4)

        # the actions
        arrow_top = Df - thickness - max(0.55 * B, 0.7)
        ecc = geom["e_B"] if a.shape != "strip" else geom["e_B"]
        ax.annotate("", xy=(ecc, Df - thickness), xytext=(ecc, arrow_top),
                    arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["applied"],
                                    lw=2.0), zorder=7)
        ax.text(ecc, arrow_top, f"V = {res['applied']['V']:,.0f} kN", fontsize=8.5,
                ha="center", va="bottom", color=th["fg"], bbox=label_box(th), zorder=8)
        if res["applied"]["H"] > 0:
            length = max(0.45 * B, 0.5)
            y = Df - thickness / 2
            ax.annotate("", xy=(-B / 2 + length, y), xytext=(-B / 2 - length * 0.15, y),
                        arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["applied"],
                                        lw=1.8), zorder=7)
            ax.text(-B / 2 - length * 0.2, y, f"H = {res['applied']['H']:,.0f} kN",
                    fontsize=8.5, ha="right", va="center", color=th["fg"],
                    bbox=label_box(th), zorder=8)

        # dimensions
        ax.annotate("", xy=(-B / 2, Df + 0.06 * bottom), xytext=(B / 2, Df + 0.06 * bottom),
                    arrowprops=dict(arrowstyle="<->", color=th["fg_dim"], lw=1.0), zorder=7)
        ax.text(0, Df + 0.06 * bottom, f"B = {B:.2f} m", fontsize=8.5, ha="center",
                va="bottom", color=th["fg"], bbox=label_box(th), zorder=8)
        ax.annotate("", xy=(-half * 0.42, 0.0), xytext=(-half * 0.42, Df),
                    arrowprops=dict(arrowstyle="<->", color=th["fg_dim"], lw=1.0), zorder=7)
        ax.text(-half * 0.42, Df / 2 if Df > 0 else 0.1, f"Df = {Df:.2f} m", fontsize=8.5,
                ha="center", va="center", color=th["fg"], bbox=label_box(th), zorder=8)

        ax.set_xlim(-half, half)
        ax.set_ylim(bottom, -max(0.6 * B, 0.8))
        ax.set_xlabel("x (m)", fontsize=9)
        ax.set_ylabel("z (m)", fontsize=9)
        ax.set_aspect("equal", adjustable="box")
        self._title(fig, th, "schematic",
                    f" — q_ult = {res['q_ult']:,.0f} kPa, {self._method_label(res['governing'])}")
        fig.tight_layout(rect=(0, 0, 1, 0.95))

    # ------------------------------------------------------------------ factors
    def _draw_factors(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        phis = np.linspace(0.0, 45.0, 181)
        design = self.res["params"]["drained"]["phi"]
        names = [("Nc", "Nc"), ("Nq", "Nq"), ("Ngamma", "Nγ")]
        for index, (key, label) in enumerate(names, start=1):
            ax = fig.add_subplot(1, 3, index)
            style_axis(ax, th)
            for method in CURVE_METHODS:
                values = [bearing_factors(float(p), method)[key] for p in phis]
                primary = method == self.res["primary"]
                ax.plot(phis, values, color=METHOD_COLORS[method],
                        linewidth=2.2 if primary else 1.1,
                        alpha=1.0 if primary else 0.55,
                        label=self._method_label(method) if index == 1 else None)
            ax.set_yscale("log")
            ax.set_ylim(1.0, 400.0)
            ax.axvline(design, color=th["fg_dim"], linestyle=":", linewidth=1.2)
            value = bearing_factors(design, self.res["primary"])[key] \
                if self.res["primary"] in CURVE_METHODS else None
            if value and value >= 1.0:
                ax.scatter([design], [value], s=28, color=METHOD_COLORS.get(
                    self.res["primary"], th["accent"]), zorder=5,
                    edgecolor=th["panel"], linewidth=1.0)
                ax.annotate(f"{value:.1f}", xy=(design, value), xytext=(6, 6),
                            textcoords="offset points", fontsize=8.5, color=th["fg"],
                            bbox=label_box(th))
            ax.set_xlabel(self.L["plot_phi"], fontsize=9)
            ax.set_title(label, fontsize=10, color=th["fg"])
        handles, labels = fig.axes[0].get_legend_handles_labels()
        legend = fig.legend(handles, labels, loc="lower center", ncol=len(CURVE_METHODS),
                            fontsize=8.5, frameon=False)
        for text in legend.get_texts():
            text.set_color(th["fg"])
        self._title(fig, th, "factors", f" — φ' = {design:.1f}°")
        fig.tight_layout(rect=(0, 0.08, 1, 0.94))

    # ------------------------------------------------------------------ comparison
    def _draw_comparison(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, axis="x")
        entries = [(key, entry) for key, entry in self._entries()
                   if math.isfinite(entry.get("q_ult", float("nan")))
                   or math.isfinite(entry.get("q_all", float("nan")))]
        if not entries:
            ax.axis("off")
            ax.text(0.5, 0.5, self.L["plot_no_data"], ha="center", va="center",
                    color=th["fg_dim"])
            return
        labels = [self._method_label(key) for key, _ in entries]
        ultimate = [entry.get("q_ult", float("nan")) for _, entry in entries]
        allowable = [entry.get("q_all", entry.get("q_ult", float("nan")) / self.a.FS)
                     for _, entry in entries]
        y = np.arange(len(entries))

        ax.barh(y + 0.19, [0 if not math.isfinite(v) else v for v in ultimate],
                height=0.36, color=[METHOD_COLORS.get(key, th["accent"])
                                    for key, _ in entries],
                label=self.L["plot_ultimate"])
        ax.barh(y - 0.19, [0 if not math.isfinite(v) else v for v in allowable],
                height=0.36, color=[METHOD_COLORS.get(key, th["accent"])
                                    for key, _ in entries],
                alpha=0.45, label=self.L["plot_allowable"])
        for index, value in enumerate(ultimate):
            if math.isfinite(value):
                ax.text(value, y[index] + 0.19, f" {value:,.0f}", fontsize=8,
                        va="center", color=th["fg"])

        applied = self.res["applied"]["q"]
        ax.axvline(applied, color=PLOT_PALETTE["applied"], linestyle="--", linewidth=1.6)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9, color=th["fg"])
        ax.set_xlabel(f"{self.L['plot_pressure']} (kPa)", fontsize=9)
        widest = max([v for v in ultimate + allowable if math.isfinite(v)] or [1.0])
        ax.set_xlim(0, max(widest, applied) * 1.14)

        # the bars carry a colour each, so the key is drawn with neutral proxies
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch
        handles = [Patch(facecolor=th["fg_dim"], label=self.L["plot_ultimate"]),
                   Patch(facecolor=th["fg_dim"], alpha=0.45,
                         label=self.L["plot_allowable"]),
                   Line2D([0], [0], color=PLOT_PALETTE["applied"], linestyle="--",
                          linewidth=1.6,
                          label=f"{self.L['plot_applied']} = {applied:,.0f} kPa")]
        legend = ax.legend(handles=handles, fontsize=8.5, frameon=False, ncol=3,
                           loc="upper center", bbox_to_anchor=(0.5, -0.09))
        for text in legend.get_texts():
            text.set_color(th["fg"])
        self._title(fig, th, "comparison")
        fig.tight_layout(rect=(0, 0.04, 1, 0.95))

    # ------------------------------------------------------------------ terms
    def _draw_components(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th, axis="y")
        entries = [(key, entry) for key, entry in self.res["methods"].items()]
        labels = [self._method_label(key) for key, _ in entries]
        x = np.arange(len(entries))
        parts = [("c", "cohesion", "head_c_term"), ("q", "surcharge", "head_q_term"),
                 ("g", "weight", "head_g_term")]
        bottom = np.zeros(len(entries))
        for part, colour, key in parts:
            values = np.array([entry["terms"][part] for _, entry in entries])
            ax.bar(x, values, bottom=bottom, width=0.58,
                   color=PLOT_PALETTE[colour], label=self.L[key])
            for index, value in enumerate(values):
                if value > 0.06 * max(bottom.max() + values.max(), 1.0):
                    ax.text(x[index], bottom[index] + value / 2, f"{value:,.0f}",
                            ha="center", va="center", fontsize=8, color=th["panel"])
            bottom += values
        for index, total in enumerate(bottom):
            ax.text(x[index], total, f"{total:,.0f}", ha="center", va="bottom",
                    fontsize=8.5, color=th["fg"])
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8.5, color=th["fg"], rotation=12,
                           ha="right")
        ax.set_ylabel(f"{self.L['plot_pressure']} (kPa)", fontsize=9)
        legend = ax.legend(fontsize=8.5, frameon=False)
        for text in legend.get_texts():
            text.set_color(th["fg"])
        self._title(fig, th, "components")
        fig.tight_layout(rect=(0, 0, 1, 0.95))

    # ------------------------------------------------------------------ pressure
    def _draw_pressure(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        a, res = self.a, self.res
        pressure, geom = res["pressure"], res["geometry"]
        B = a.B

        ax = fig.add_subplot(2, 1, 1)
        style_axis(ax, th, axis="y")
        # the resultant leans towards +x, so the pressure peaks at that edge
        if pressure["in_kern"] and math.isfinite(pressure["q_max"]):
            xs = np.array([-B / 2, B / 2])
            ys = np.array([pressure["q_min"], pressure["q_max"]])
        elif math.isfinite(pressure["q_max"]):
            contact = pressure["contact"]
            xs = np.array([B / 2 - contact, B / 2])
            ys = np.array([0.0, pressure["q_max"]])
        else:
            xs, ys = np.array([-B / 2, B / 2]), np.array([pressure["q_mean"]] * 2)
        ax.fill_between(xs, 0, ys, color=PLOT_PALETTE["applied"], alpha=0.35)
        ax.plot(xs, ys, color=PLOT_PALETTE["applied"], linewidth=1.8)
        ax.axhline(pressure["q_mean"], color=th["fg_dim"], linestyle=":", linewidth=1.2)
        ax.plot([-B / 2, B / 2], [0, 0], color=PLOT_PALETTE["footing"], linewidth=3.0)
        for x, y, text in ((xs[0], ys[0], f"{ys[0]:,.0f}"), (xs[-1], ys[-1], f"{ys[-1]:,.0f}")):
            ax.annotate(f"{text} kPa", xy=(x, y), xytext=(0, 8),
                        textcoords="offset points", fontsize=8.5, ha="center",
                        color=th["fg"], bbox=label_box(th))
        ax.set_xlim(-B / 2 * 1.2, B / 2 * 1.2)
        ax.set_xlabel("x (m)", fontsize=9)
        ax.set_ylabel(f"{self.L['plot_pressure']} (kPa)", fontsize=9)
        ax.invert_yaxis()

        # the plan: the base and the effective area
        ax2 = fig.add_subplot(2, 1, 2)
        style_axis(ax2, th, grid=False)
        L = a.L if a.shape != "strip" else 3.0 * B
        ax2.add_patch(Rectangle((-B / 2, -L / 2), B, L, facecolor=th["panel"],
                                edgecolor=th["fg_dim"], linewidth=1.2))
        be, le = geom["B_eff"], min(geom["L_eff"], L)
        ax2.add_patch(Rectangle((-B / 2 + 2 * geom["e_B"] if geom["e_B"] > 0 else -be / 2,
                                 -le / 2), be, le,
                                facecolor=PLOT_PALETTE["allowable"], alpha=0.35,
                                edgecolor=PLOT_PALETTE["allowable"], linewidth=1.4,
                                label=self.L["plot_effective"]))
        ax2.scatter([geom["e_B"]], [geom["e_L"]], s=40, color=PLOT_PALETTE["applied"],
                    zorder=5, label=self.L["plot_resultant"])
        ax2.set_xlim(-B * 0.95, B * 0.95)
        ax2.set_ylim(-L * 0.62, L * 0.95)
        ax2.set_aspect("equal", adjustable="box")
        ax2.set_xlabel(f"B = {B:.2f} m,  B' = {be:.2f} m,  A' = {geom['A_eff']:.2f} m²",
                       fontsize=9)
        legend = ax2.legend(fontsize=8.5, frameon=False, loc="upper center", ncol=2)
        for text in legend.get_texts():
            text.set_color(th["fg"])
        self._title(fig, th, "pressure")
        fig.tight_layout(rect=(0, 0, 1, 0.95))

    # ------------------------------------------------------------------ sweeps
    def _sweep_figure(self, fig: Figure, key: str, values, label: str) -> None:
        th = style_figure(fig, self.theme)
        rows = self.a.sweep_dimension(key, values)
        if not rows:
            ax = fig.add_subplot(111)
            style_axis(ax, th, grid=False)
            ax.axis("off")
            ax.text(0.5, 0.5, self.L["plot_no_data"], ha="center", va="center",
                    color=th["fg_dim"])
            return
        x = np.array([row[key] for row in rows])
        ax = fig.add_subplot(2, 1, 1)
        style_axis(ax, th)
        ax.plot(x, [row["q_ult"] for row in rows], color=PLOT_PALETTE["ultimate"],
                linewidth=2.0, label=self.L["plot_ultimate"])
        ax.plot(x, [row["q_all"] for row in rows], color=PLOT_PALETTE["allowable"],
                linewidth=2.0, label=self.L["plot_allowable"])
        ax.plot(x, [row["q_applied"] for row in rows], color=PLOT_PALETTE["applied"],
                linewidth=2.0, linestyle="--", label=self.L["plot_applied"])
        ax.set_ylabel(f"{self.L['plot_pressure']} (kPa)", fontsize=9)
        ax.set_ylim(0, max(np.percentile([row["q_applied"] for row in rows], 85),
                           max(row["q_ult"] for row in rows)) * 1.15)
        legend = ax.legend(fontsize=8.5, frameon=False)
        for text in legend.get_texts():
            text.set_color(th["fg"])

        ax2 = fig.add_subplot(2, 1, 2)
        style_axis(ax2, th)
        # A footing whose net pressure is nil has an infinite factor of safety;
        # the axis is capped, so those points are drawn at the top of it.
        ceiling = 25.0
        fs = np.array([row["FS"] for row in rows], dtype=float)
        finite = fs[np.isfinite(fs)]
        top = min(max(finite.max() * 1.1 if finite.size else 0.0, self.a.FS * 1.5), ceiling)
        ax2.plot(x, np.where(np.isfinite(fs), fs, ceiling), color=PLOT_PALETTE["design"],
                 linewidth=2.0)
        ax2.axhline(self.a.FS, color=PLOT_PALETTE["limit"], linestyle="--", linewidth=1.4)
        ax2.set_ylim(0, top)
        ax2.set_xlabel(label, fontsize=9)
        ax2.set_ylabel(self.L["head_FS"], fontsize=9)

        current = self.a.B if key == "B" else self.a.Df
        for axis in (ax, ax2):
            axis.axvline(current, color=th["fg_dim"], linestyle=":", linewidth=1.2)
        if key == "B":
            width = self.res["required_width"]
            if math.isfinite(width):
                ax2.annotate(self.L["plot_required"].format(B=width),
                             xy=(width, self.a.FS), xytext=(8, 10),
                             textcoords="offset points", fontsize=8.5, color=th["fg"],
                             bbox=label_box(th),
                             arrowprops=dict(arrowstyle="-", color=th["fg_dim"], lw=0.8))
        self._title(fig, th, key if key != "B" else "width")
        fig.tight_layout(rect=(0, 0, 1, 0.95))

    def _draw_width(self, fig: Figure) -> None:
        lo = max(0.3, 0.35 * self.a.B)
        hi = max(2.6 * self.a.B, lo + 1.0)
        self._sweep_figure(fig, "B", np.linspace(lo, hi, SWEEP_POINTS),
                           f"{self.L['plot_width']} (m)")

    def _draw_depth(self, fig: Figure) -> None:
        hi = min(max(2.5 * max(self.a.Df, 0.5), self.a.B), self.a.profile.depth * 0.9)
        self._sweep_figure(fig, "Df", np.linspace(0.0, max(hi, 1.0), SWEEP_POINTS),
                           f"{self.L['plot_depth']} (m)")

    # ------------------------------------------------------------------ envelope
    def _draw_envelope(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        points = self.a.envelope()
        if not points:
            ax.axis("off")
            ax.text(0.5, 0.5, self.L["plot_no_data"], ha="center", va="center",
                    color=th["fg_dim"])
            return
        V = np.array([p[0] for p in points])
        H = np.array([p[1] for p in points])
        order = np.argsort(-V)
        V, H = V[order], H[order]
        ax.fill_between(np.concatenate([[0], V[::-1], [0]]),
                        np.concatenate([[0], H[::-1], [0]]),
                        color=PLOT_PALETTE["allowable"], alpha=0.18)
        ax.plot(np.concatenate([[0], V[::-1]]), np.concatenate([[0], H[::-1]]),
                color=PLOT_PALETTE["ultimate"], linewidth=2.2,
                label=self.L["plot_ultimate"])
        applied = self.res["applied"]
        ax.scatter([applied["V"]], [applied["H"]], s=60,
                   color=PLOT_PALETTE["applied"], zorder=6, edgecolor=th["panel"],
                   linewidth=1.2, label=self.L["plot_this_case"])
        ax.annotate(f"V = {applied['V']:,.0f} kN\nH = {applied['H']:,.0f} kN",
                    xy=(applied["V"], applied["H"]), xytext=(14, 14),
                    textcoords="offset points", fontsize=8.5, color=th["fg"],
                    bbox=label_box(th),
                    arrowprops=dict(arrowstyle="-", color=th["fg_dim"], lw=0.8))
        ax.set_xlabel("V (kN)", fontsize=9)
        ax.set_ylabel("H (kN)", fontsize=9)
        ax.set_xlim(0, max(V.max(), applied["V"]) * 1.08)
        ax.set_ylim(0, max(H.max(), applied["H"]) * 1.25 or 1.0)
        legend = ax.legend(fontsize=8.5, frameon=False)
        for text in legend.get_texts():
            text.set_color(th["fg"])
        self._title(fig, th, "envelope",
                    f" — {self._method_label(self.res['primary'])}")
        fig.tight_layout(rect=(0, 0, 1, 0.95))


def available_figures(analysis=None) -> list:
    """The figures that can be drawn for the analysis just run."""
    return list(PLOT_KEYS)
