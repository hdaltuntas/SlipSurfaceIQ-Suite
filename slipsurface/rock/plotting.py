"""
The analysis figures of SlipSurface IQ Rock.

    principal     σ1 against σ3: the Hoek–Brown envelope, the fitted
                  Mohr–Coulomb line, the residual envelope, σ3max and σt
    shear         τ against σn: the same envelopes in the Mohr plane, and
                  the tangent at the σ3 asked for
    envelopes     the two side by side, as RocLab shows them
    gsi_chart     the quantified GSI chart (Hoek, Carter & Diederichs 2013)
                  with the rock mass on it
    constants     mb/mi, s and a against GSI
    strength_gsi  c' and φ' against GSI, for the application in use
    modulus       Erm against GSI by every estimate
    disturbance   c', φ' and Erm against the disturbance factor D
    labfit        the triaxial tests and the intact envelope fitted to them

`Plotter.draw(key, fig)` draws one of them on a Matplotlib figure, in the
interface's theme ('light', 'dark') or on white paper for the report.
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure

from . import hoekbrown as hb
from . import tables
from .config import MODULUS_METHODS, PLOT_PALETTE
from .i18n import TRANSLATIONS
from .plot_style import annotate_point, figure_title, style_axis, style_figure

PLOT_KEYS = ["envelopes", "principal", "shear", "gsi_chart", "constants", "strength_gsi",
             "modulus", "disturbance", "labfit"]

__all__ = ["PLOT_KEYS", "Plotter", "available_figures"]

P = PLOT_PALETTE


def _legend(ax, th, loc="best"):
    legend = ax.legend(fontsize=8.2, frameon=True, loc=loc)
    legend.get_frame().set_facecolor(th["panel"])
    legend.get_frame().set_edgecolor(th["border"])
    for text in legend.get_texts():
        text.set_color(th["fg"])
    return legend


class Plotter:
    """Draws the figures of one finished analysis."""

    def __init__(self, analysis, lang: str = "en", theme="light", titles: bool = True):
        self.analysis = analysis
        self.res = analysis.results
        self.lang = lang
        self.L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        self.theme = theme
        self.titles = titles

    def _title(self, fig, th, key: str, extra: str = "") -> None:
        if not self.titles:
            return
        text = self.L.get(f"fig_{key}", key)
        figure_title(fig, th, f"{text} — {extra}" if extra else text)

    def draw(self, key: str, fig: Figure) -> None:
        if key not in PLOT_KEYS:
            raise ValueError(f"unknown figure: {key}")
        getattr(self, f"_draw_{key}")(fig)

    # ------------------------------------------------------------------ envelopes
    def _principal_axis(self, ax, th) -> None:
        L, res, c = self.L, self.res, self.res["curves"]
        ax.plot(c["sigma3"], c["sigma1"], color=P["rock_mass"], linewidth=2.2,
                label=L["leg_hb"], zorder=4)
        ax.plot(c["sigma3"], c["sigma1_mc"], color=P["mohr"], linewidth=1.6, linestyle="--",
                label=L["leg_mc"].format(c=res["mc"]["c"], phi=res["mc"]["phi"]), zorder=3)
        ax.plot(c["sigma3_r"], c["sigma1_r"], color=P["residual"], linewidth=1.2,
                linestyle=":", label=L["leg_residual"], zorder=2)
        s3max = res["sigma3_max"]
        ax.axvline(s3max, color=P["limit"], linewidth=1.0, linestyle="-.", zorder=1)
        top = float(np.nanmax(c["sigma1_mc"]))
        ax.text(s3max, top * 0.04, f" σ3max = {s3max:.3g}", color=P["limit"], fontsize=8,
                ha="left", va="bottom", rotation=90)
        st = res["strength"]["sigma_t"]
        annotate_point(ax, st, 0.0, f"σt = {st:.3g}", th, P["tensile"], dx=18, dy=22,
                       ha="left")
        q = res["query"]
        annotate_point(ax, q["sigma3"], q["sigma1"],
                       f"σ3 = {q['sigma3']:.3g}\nσ1 = {q['sigma1']:.3g}", th, P["query"],
                       dx=26, dy=-24)
        ax.set_xlabel(L["ax_sigma3"])
        ax.set_ylabel(L["ax_sigma1"])
        ax.set_ylim(bottom=min(0.0, float(np.nanmin(c["sigma1"]))))
        _legend(ax, th, "upper left")

    def _shear_axis(self, ax, th) -> None:
        L, res, c = self.L, self.res, self.res["curves"]
        ax.plot(c["sigma_n"], c["tau"], color=P["rock_mass"], linewidth=2.2,
                label=L["leg_hb"], zorder=4)
        mc = res["mc"]
        sn = np.linspace(mc["sigma_t"] if math.isfinite(mc["sigma_t"]) else 0.0,
                         float(np.nanmax(c["sigma_n"])), 60)
        sn = sn[sn >= float(np.nanmin(c["sigma_n"])) - abs(mc["sigma_t"])]
        ax.plot(sn, mc["c"] + sn * math.tan(math.radians(mc["phi"])), color=P["mohr"],
                linewidth=1.6, linestyle="--",
                label=L["leg_mc"].format(c=mc["c"], phi=mc["phi"]), zorder=3)
        ax.plot(c["sigma_n_r"], c["tau_r"], color=P["residual"], linewidth=1.2,
                linestyle=":", label=L["leg_residual"], zorder=2)
        q = res["query"]
        span = max(float(np.nanmax(c["sigma_n"])) * 0.18, 1e-3)
        xs = np.array([q["sigma_n"] - span, q["sigma_n"] + span])
        ax.plot(xs, q["c"] + xs * math.tan(math.radians(q["phi"])), color=P["query"],
                linewidth=1.1, label=L["leg_tangent"].format(c=q["c"], phi=q["phi"]), zorder=5)
        annotate_point(ax, q["sigma_n"], q["tau"],
                       f"σn = {q['sigma_n']:.3g}\nτ = {q['tau']:.3g}", th, P["query"],
                       dx=24, dy=-26)
        ax.set_xlabel(L["ax_sigma_n"])
        ax.set_ylabel(L["ax_tau"])
        ax.set_ylim(bottom=0.0)
        _legend(ax, th, "upper left")

    def _draw_principal(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        self._principal_axis(ax, th)
        self._title(fig, th, "principal")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    def _draw_shear(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        self._shear_axis(ax, th)
        self._title(fig, th, "shear")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    def _draw_envelopes(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        left, right = fig.add_subplot(121), fig.add_subplot(122)
        style_axis(left, th)
        style_axis(right, th)
        self._principal_axis(left, th)
        self._shear_axis(right, th)
        self._title(fig, th, "envelopes")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    # ------------------------------------------------------------------ GSI chart
    def _draw_gsi_chart(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        L, res = self.L, self.res
        ax = fig.add_subplot(111)
        style_axis(ax, th, grid=False)
        ax.set_xlim(45, 0)                      # surface: very good on the left
        ax.set_ylim(0, 50)                      # structure: intact at the top
        for value in range(10, 100, 10):
            xs = np.linspace(0, 45, 50)
            ys = value - xs
            keep = (ys >= 0) & (ys <= 50)
            if keep.sum() < 2:
                continue
            ax.plot(xs[keep], ys[keep], color=th["border"], linewidth=1.0, zorder=1)
            xm, ym = xs[keep][len(xs[keep]) // 2], ys[keep][len(ys[keep]) // 2]
            ax.text(xm, ym, f"{value}", color=th["fg_dim"], fontsize=8, ha="center",
                    va="center", bbox=dict(fc=th["panel"], ec="none", pad=0.6), zorder=2)
        # the chart's classes along the axes
        for key, entry in tables.SURFACES.items():
            ax.axvline(1.5 * entry["JCond89"], color=th["hover"], linewidth=0.6, zorder=0)
        for key, entry in tables.STRUCTURES.items():
            ax.axhline(entry["RQD"] / 2.0, color=th["hover"], linewidth=0.6, zorder=0)
        ax.set_xticks([1.5 * e["JCond89"] for e in tables.SURFACES.values()])
        ax.set_xticklabels([tables.name(tables.SURFACES, k, self.lang).split(" — ")[0]
                            for k in tables.SURFACES], fontsize=8)
        ax.set_yticks([e["RQD"] / 2.0 for e in tables.STRUCTURES.values()])
        ax.set_yticklabels([tables.name(tables.STRUCTURES, k, self.lang).split(" — ")[0]
                            for k in tables.STRUCTURES], fontsize=8)
        ax.set_xlabel(L["ax_jcond"])
        ax.set_ylabel(L["ax_rqd"])

        GSI, gsi = res["GSI"], res["gsi"]
        point = None
        if gsi["source"] == "jcond":
            point = (1.5 * gsi["JCond89"], gsi["RQD"] / 2.0)
        elif gsi["source"] == "chart":
            point = (1.5 * tables.SURFACES[gsi["surface"]]["JCond89"],
                     tables.STRUCTURES[gsi["structure"]]["RQD"] / 2.0)
        xs = np.linspace(0, 45, 100)
        ys = GSI - xs
        keep = (ys >= 0) & (ys <= 50)
        if keep.any():
            ax.plot(xs[keep], ys[keep], color=P["rock_mass"], linewidth=2.4, zorder=3,
                    label=f"GSI = {GSI:.1f}")
        if point is not None:
            annotate_point(ax, point[0], point[1], f"GSI = {GSI:.1f}", th, P["rock_mass"],
                           dx=-24, dy=18, ha="left")
        elif keep.any():
            _legend(ax, th, "lower left")
        self._title(fig, th, "gsi_chart")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    # ------------------------------------------------------------------ against GSI
    def _mark(self, ax, x, y, th, color, text):
        annotate_point(ax, x, y, text, th, color, dx=16, dy=14)

    def _draw_constants(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        L, res = self.L, self.res
        gsis = np.linspace(5, 100, 120)
        sweep = self.analysis.sweep("GSI", gsis)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.semilogy(gsis, sweep["mb_mi"], color=P["mb"], linewidth=2.0, label="mb/mi")
        ax.semilogy(gsis, sweep["s"], color=P["s"], linewidth=2.0, label="s")
        ax.set_xlabel("GSI")
        ax.set_ylabel(L["ax_constants"])
        right = ax.twinx()
        right.plot(gsis, sweep["a"], color=P["a"], linewidth=2.0, label="a")
        right.set_ylabel("a", color=th["fg_dim"])
        right.tick_params(colors=th["fg_dim"], labelsize=8.5)
        for spine in right.spines.values():
            spine.set_visible(False)
        GSI = res["GSI"]
        self._mark(ax, GSI, res["hb"]["mb_mi"], th, P["mb"], f"mb/mi = {res['hb']['mb_mi']:.3g}")
        self._mark(ax, GSI, res["hb"]["s"], th, P["s"], f"s = {res['hb']['s']:.3g}")
        annotate_point(right, GSI, res["hb"]["a"], f"a = {res['hb']['a']:.3f}", th, P["a"],
                       dx=16, dy=-14)
        lines = ax.get_lines()[:2] + right.get_lines()[:1]
        legend = ax.legend(lines, [line.get_label() for line in lines], fontsize=8.2,
                           loc="lower right")
        legend.get_frame().set_facecolor(th["panel"])
        for text in legend.get_texts():
            text.set_color(th["fg"])
        self._title(fig, th, "constants", f"D = {res['D']:.2f}")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    def _c_phi(self, fig, th, xs, sweep, x_now, xlabel):
        L, res = self.L, self.res
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.plot(xs, sweep["c"], color=P["cohesion"], linewidth=2.0, label=L["leg_c"])
        ax.set_xlabel(xlabel)
        ax.set_ylabel(L["ax_c"])
        right = ax.twinx()
        right.plot(xs, sweep["phi"], color=P["friction"], linewidth=2.0, label=L["leg_phi"])
        right.set_ylabel(L["ax_phi"], color=th["fg_dim"])
        right.tick_params(colors=th["fg_dim"], labelsize=8.5)
        for spine in right.spines.values():
            spine.set_visible(False)
        annotate_point(ax, x_now, res["mc"]["c"], f"c' = {res['mc']['c']:.3g} MPa", th,
                       P["cohesion"], dx=16, dy=16)
        annotate_point(right, x_now, res["mc"]["phi"], f"φ' = {res['mc']['phi']:.1f}°", th,
                       P["friction"], dx=16, dy=-16)
        lines = ax.get_lines()[:1] + right.get_lines()[:1]
        legend = ax.legend(lines, [line.get_label() for line in lines], fontsize=8.2,
                           loc="upper left")
        legend.get_frame().set_facecolor(th["panel"])
        for text in legend.get_texts():
            text.set_color(th["fg"])
        return ax

    def _draw_strength_gsi(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        gsis = np.linspace(5, 100, 120)
        sweep = self.analysis.sweep("GSI", gsis)
        self._c_phi(fig, th, gsis, sweep, self.res["GSI"], "GSI")
        self._title(fig, th, "strength_gsi",
                    self.L[f"application_{self.res['application']}"])
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    def _draw_modulus(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        L, res = self.L, self.res
        gsis = np.linspace(5, 100, 120)
        sweep = self.analysis.sweep("GSI", gsis)
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        chosen = res["modulus"]["method"]
        for name in MODULUS_METHODS:
            ax.plot(gsis, sweep[name] / 1000.0, color=P[name],
                    linewidth=2.4 if name == chosen else 1.4,
                    linestyle="-" if name == chosen else "--",
                    label=L[f"modulus_{name}"])
        Ei = res["modulus"]["Ei"] / 1000.0
        ax.axhline(Ei, color=th["fg_dim"], linewidth=1.0, linestyle=":")
        ax.text(6, Ei, f" Ei = {Ei:,.1f} GPa", color=th["fg_dim"], fontsize=8, va="bottom")
        Erm = res["modulus"]["Erm"] / 1000.0
        annotate_point(ax, res["GSI"], Erm, f"Erm = {Erm:,.2f} GPa", th, P[chosen],
                       dx=-20, dy=22, ha="right")
        ax.set_xlabel("GSI")
        ax.set_ylabel(L["ax_Erm"])
        ax.set_ylim(bottom=0.0)
        _legend(ax, th, "upper left")
        self._title(fig, th, "modulus", f"D = {res['D']:.2f}")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    def _draw_disturbance(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        L, res = self.L, self.res
        ds = np.linspace(0.0, 1.0, 51)
        sweep = self.analysis.sweep("D", ds)
        left = fig.add_subplot(121)
        style_axis(left, th)
        left.plot(ds, sweep["c"], color=P["cohesion"], linewidth=2.0, label=L["leg_c"])
        left.set_xlabel("D")
        left.set_ylabel(L["ax_c"])
        twin = left.twinx()
        twin.plot(ds, sweep["phi"], color=P["friction"], linewidth=2.0, label=L["leg_phi"])
        twin.set_ylabel(L["ax_phi"], color=th["fg_dim"])
        twin.tick_params(colors=th["fg_dim"], labelsize=8.5)
        for spine in twin.spines.values():
            spine.set_visible(False)
        annotate_point(left, res["D"], res["mc"]["c"], f"{res['mc']['c']:.3g}", th,
                       P["cohesion"], dx=16, dy=12)
        annotate_point(twin, res["D"], res["mc"]["phi"], f"{res['mc']['phi']:.1f}°", th,
                       P["friction"], dx=16, dy=-12)
        lines = left.get_lines()[:1] + twin.get_lines()[:1]
        legend = left.legend(lines, [line.get_label() for line in lines], fontsize=8.2,
                             loc="lower left")
        legend.get_frame().set_facecolor(th["panel"])
        for text in legend.get_texts():
            text.set_color(th["fg"])

        right = fig.add_subplot(122)
        style_axis(right, th)
        chosen = res["modulus"]["method"]
        for name in MODULUS_METHODS:
            right.plot(ds, sweep[name] / 1000.0, color=P[name],
                       linewidth=2.2 if name == chosen else 1.3,
                       linestyle="-" if name == chosen else "--", label=L[f"modulus_{name}"])
        annotate_point(right, res["D"], res["modulus"]["Erm"] / 1000.0,
                       f"{res['modulus']['Erm'] / 1000.0:,.2f} GPa", th, P[chosen],
                       dx=16, dy=12)
        right.set_xlabel("D")
        right.set_ylabel(L["ax_Erm"])
        right.set_ylim(bottom=0.0)
        _legend(right, th, "upper right")
        self._title(fig, th, "disturbance", f"GSI = {res['GSI']:.1f}")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)

    # ------------------------------------------------------------------ lab fit
    def _draw_labfit(self, fig: Figure) -> None:
        th = style_figure(fig, self.theme)
        L, res = self.L, self.res
        fit = res["intact"].get("fit")
        if not fit:
            ax = fig.add_subplot(111)
            ax.axis("off")
            ax.text(0.5, 0.5, L["no_lab_fit"], ha="center", va="center", color=th["fg_dim"])
            return
        tests = fit["tests"]
        s3 = np.array([t["sigma3"] for t in tests])
        s1 = np.array([t["sigma1"] for t in tests])
        sci, mi = fit["sigma_ci"], fit["mi"]

        left = fig.add_subplot(121)
        style_axis(left, th)
        lo = min(0.0, float(s3.min()), -sci / mi)
        xs = np.linspace(-sci / mi * (1 - 1e-9), max(float(s3.max()) * 1.15, sci * 0.1), 160)
        xs = xs[xs >= lo]
        left.plot(xs, hb.sigma1(xs, sci, mi, 1.0, 0.5), color=P["intact"], linewidth=2.0,
                  label=L["leg_intact"].format(sci=sci, mi=mi))
        left.scatter(s3, s1, s=34, color=P["data"], edgecolor=th["panel"], linewidth=1.0,
                     zorder=5, label=L["leg_tests"].format(n=fit["n"]))
        left.set_xlabel(L["ax_sigma3"])
        left.set_ylabel(L["ax_sigma1"])
        _legend(left, th, "upper left")

        right = fig.add_subplot(122)
        style_axis(right, th)
        y = (s1 - s3) ** 2
        right.scatter(s3, y, s=34, color=P["data"], edgecolor=th["panel"], linewidth=1.0,
                      zorder=5)
        xl = np.linspace(min(0.0, float(s3.min())), float(s3.max()) * 1.1, 50)
        right.plot(xl, fit["slope"] * xl + fit["intercept"], color=P["fit"], linewidth=1.8,
                   label=f"r² = {fit['r2']:.4f}")
        right.set_xlabel(L["ax_sigma3"])
        right.set_ylabel(L["ax_regression"])
        _legend(right, th, "upper left")
        self._title(fig, th, "labfit")
        fig.tight_layout(rect=(0, 0, 1, 0.95) if self.titles else None)


def available_figures(analysis=None) -> list:
    """The figures that have something to show for this analysis."""
    keys = list(PLOT_KEYS)
    if analysis is None or not analysis.results.get("intact", {}).get("fit"):
        keys.remove("labfit")
    return keys
