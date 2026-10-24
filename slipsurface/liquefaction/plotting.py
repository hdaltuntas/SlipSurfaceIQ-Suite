"""
The analysis figures of SlipSurface IQ Liquefaction.

Every figure is drawn on a Matplotlib `Figure` passed in by the caller, so the
same code serves the browser (PNG through `render`) and the report. Nothing
here needs a display. Depth runs downwards in every depth plot, the water
table is the same dashed blue line, and each test is coloured by its state:
liquefies, marginal, safe, too dense, not susceptible or dry.

    log             borehole log: soil column, blow counts, FS and settlement
    fs              factor of safety with depth, the liquefied zones shaded
    csr             CSR (demand) against CRR (resistance) with depth
    spt             N, N60, (N1)60 and (N1)60cs with depth
    settlement      volumetric strain, and the settlement of the soil below
    indices         LPI and LSN accumulated from the surface
    methods         FS with depth by every procedure
    susceptibility  the fine-grained samples on the plasticity chart and on
                    Bray & Sancio's chart
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from .config import PLOT_PALETTE, SOIL_FILL, soil_kind
from .i18n import TRANSLATIONS
from .plot_style import TITLE_FONT, label_box, style_axis, style_figure

#: The figures, in the order the interface offers them
PLOT_KEYS = ["log", "fs", "csr", "spt", "cpt", "settlement", "lateral", "indices", "methods",
             "susceptibility", "sbt"]

#: Figures that belong to one test type only
ONLY_SPT = {"spt", "susceptibility"}
ONLY_CPT = {"cpt", "sbt"}


def available(analysis) -> list:
    """The figures that apply to an analysis: the SPT or the CPT ones."""
    skip = ONLY_SPT if analysis.results.get("kind") == "cpt" else ONLY_CPT
    return [key for key in PLOT_KEYS if key not in skip]

#: The factor of safety axis ends here; higher values sit on the edge
FS_PLOT_MAX = 2.0

#: Colour of each state of a test
STATE_COLORS = {"liquefied": PLOT_PALETTE["liquefied"], "marginal": PLOT_PALETTE["marginal"],
                "safe": PLOT_PALETTE["safe"], "dense": PLOT_PALETTE["safe"],
                "not": PLOT_PALETTE["inert"], "dry": PLOT_PALETTE["inert"],
                "softening": PLOT_PALETTE["softening"]}

#: Marker of the tests that are not assessed for liquefaction (the rest are dots);
#: a clay-like soil checked for softening is a diamond
STATE_MARKERS = {"not": "o", "dry": "s", "softening": "D"}

#: Colour of each susceptibility class
CLASS_COLORS = {"sand": PLOT_PALETTE["Ncs"], "susceptible": PLOT_PALETTE["liquefied"],
                "moderate": PLOT_PALETTE["marginal"], "not": PLOT_PALETTE["safe"]}


class Plotter:
    """Draws the figures of one finished `LiquefactionAnalysis`."""

    def __init__(self, analysis, lang: str = "en", theme: str = "light", titles: bool = True):
        self.a = analysis
        self.res = analysis.results
        self.tests = self.res["tests"]
        self.main = self.res["methods"][analysis.method]
        self.L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        self.theme = theme if theme in ("light", "dark", "paper") else "light"
        # The report writes each figure's name above it; there the figure goes untitled.
        self.titles = titles

    # ------------------------------------------------------------------ entry
    def draw(self, key: str, fig: Figure) -> None:
        if key not in PLOT_KEYS:
            raise ValueError(f"unknown figure: {key}")
        th = style_figure(fig, self.theme)
        getattr(self, f"_{key}")(fig, th)

    # ------------------------------------------------------------------ helpers
    def _title(self, fig, th, key):
        if not self.titles:
            return
        info = self.a.config.get("project_info", {}).get("title", "")
        fig.suptitle(self.L[f"fig_{key}"], color=th["fg"], fontsize=13.5, fontfamily=TITLE_FONT,
                     x=0.02, ha="left")
        if info:
            fig.text(0.98, 0.965, info, color=th["fg_dim"], fontsize=8.5, ha="right",
                     va="center")

    @property
    def z_max(self) -> float:
        return self.a.profile.depth

    def _depth_axis(self, ax, th, label=True):
        """Depth downwards, with the layer boundaries and the water table."""
        a = self.a
        ax.set_ylim(self.z_max, 0.0)
        if label:
            ax.set_ylabel(self.L["ax_depth"])
        for layer in a.profile.layers[:-1]:
            ax.axhline(layer["bottom"], color=th["border"], lw=0.8, zorder=1)
        if 0 <= a.zw <= self.z_max:
            ax.axhline(a.zw, color=PLOT_PALETTE["water"], lw=1.2, ls=(0, (6, 3)), zorder=2)
        ax.grid(True, axis="both", color=th["border"], lw=0.6, alpha=0.7)

    def _legend(self, ax, th, **kw):
        kw.setdefault("fontsize", 8)
        legend = ax.legend(frameon=True, **kw)
        legend.get_frame().set_facecolor(th["panel"])
        legend.get_frame().set_edgecolor(th["border"])
        for text in legend.get_texts():
            text.set_color(th["fg"])
        return legend

    def _shade_liquefied(self, ax):
        """The parts of the profile that liquefy, as bands across the axis."""
        t = self.tests
        for top, bot, state in zip(t["top"], t["bot"], t["state"]):
            if state in ("liquefied", "marginal", "softening"):
                lo = max(top, self.a.zw)
                if bot > lo:
                    ax.axhspan(lo, bot, color=STATE_COLORS[state], alpha=0.10, lw=0, zorder=0)

    def _state_legend(self, th):
        L = self.L
        present = list(dict.fromkeys(self.tests["state"]))
        order = ["liquefied", "marginal", "safe", "dense", "softening", "not", "dry"]
        soft_checked = np.isfinite(self.tests["fs_soft"]).any()

        def marker(s):
            if s == "not" and soft_checked:
                return "D"
            return STATE_MARKERS.get(s, "o")

        return [Line2D([], [], marker=marker(s), ls="", color=STATE_COLORS[s],
                       markerfacecolor=STATE_COLORS[s] if s not in ("not", "dry") else "none",
                       label=L["state_" + s]) for s in order if s in present]

    def _column(self, ax, th, labels=True):
        """The soil column, coloured by the kind of soil, with the water table."""
        a, L = self.a, self.L
        fills = SOIL_FILL[self.theme]
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        for layer in a.profile.layers:
            kind = soil_kind(layer["FC"], layer["PI"])
            ax.add_patch(Rectangle((0, layer["top"]), 1, layer["thickness"],
                                   facecolor=fills[kind], edgecolor=th["border"], lw=0.8,
                                   zorder=1))
            if labels:
                ax.text(0.05, layer["top"] + 0.5 * layer["thickness"],
                        f"{layer['name']}", fontsize=7.2, color=th["fg"], va="center",
                        ha="left", zorder=4, wrap=True, clip_on=True)
        if 0 <= a.zw <= self.z_max:
            ax.axhline(a.zw, color=PLOT_PALETTE["water"], lw=1.3, ls=(0, (6, 3)), zorder=3)
            ax.plot([0.9], [a.zw], marker="v", color=PLOT_PALETTE["water"], ms=8, zorder=5)
        ax.set_ylim(self.z_max, 0.0)
        ax.set_xlabel(L["ax_soil"])

    def _fs_points(self, ax, th, fs, states, z, color_line=None, label=None):
        """FS at each test: the assessed ones on a line, the rest on the edge."""
        shown = np.minimum(fs, FS_PLOT_MAX)
        soft = np.minimum(self.tests["fs_soft"], FS_PLOT_MAX)
        assessed = np.array([s not in ("not", "dry", "softening") for s in states])
        if color_line is not None and assessed.any():
            # a test that is not assessed breaks the line: the soil between is different
            ax.plot(np.where(assessed, shown, np.nan), z, "-", color=color_line, lw=1.4,
                    zorder=3, alpha=0.9, label=label)
        for zi, fi, si, state in zip(z, shown, soft, states):
            color = STATE_COLORS[state]
            if state in ("not", "softening") and np.isfinite(si):
                # a clay-like soil, at its factor of safety against cyclic softening
                ax.plot([si], [zi], marker="D", ms=5.5, color=PLOT_PALETTE["softening"],
                        mfc=PLOT_PALETTE["softening"] if state == "softening" else "none",
                        mew=1.2, zorder=5, clip_on=False)
            elif state in ("not", "dry"):
                ax.plot([FS_PLOT_MAX], [zi], marker=STATE_MARKERS[state], ms=6, mfc="none",
                        mec=color, mew=1.2, zorder=4, clip_on=False)
            else:
                marker = ">" if fi >= FS_PLOT_MAX else "o"
                ax.plot([fi], [zi], marker=marker, ms=6.5, color=color, mec=th["panel"],
                        mew=0.9, zorder=5, clip_on=False)

    def _fs_frame(self, ax, th):
        a, L = self.a, self.L
        ax.set_xlim(0, FS_PLOT_MAX)
        ax.axvline(1.0, color=PLOT_PALETTE["liquefied"], lw=1.2, zorder=2, label=L["lg_fs1"])
        if abs(a.fs_required - 1.0) > 1e-9:
            ax.axvline(a.fs_required, color=PLOT_PALETTE["required"], lw=1.1, ls="--",
                       zorder=2, label=L["lg_required"].format(v=a.fs_required))
        ax.set_xlabel(L["ax_fs"])

    def _settlement_curve(self):
        """Settlement of the soil below each depth [mm], at the interval edges."""
        t = self.tests
        order = np.argsort(t["top"])
        top, bot = t["top"][order], t["bot"][order]
        ds = (t["ds"] + t["ds_dry"])[order]
        edges = np.concatenate([[0.0], np.sort(np.concatenate([top, bot])), [self.z_max]])
        edges = np.unique(edges)
        below = np.array([np.sum(ds * np.clip((bot - np.maximum(top, e)) /
                                              np.maximum(bot - top, 1e-12), 0.0, 1.0))
                          for e in edges])
        return edges, below

    # ------------------------------------------------------------------ figures
    def _log(self, fig, th):
        res, L, t = self.res, self.L, self.tests
        grid = fig.add_gridspec(1, 4, width_ratios=[0.9, 1.0, 1.2, 1.0], wspace=0.08)
        col = fig.add_subplot(grid[0])
        style_axis(col, th, grid=False)
        self._column(col, th)
        col.set_ylabel(L["ax_depth"])

        ax_n = fig.add_subplot(grid[1], sharey=col)
        style_axis(ax_n, th)
        self._depth_axis(ax_n, th, label=False)
        if res["kind"] == "cpt":
            ax_n.plot(t["qc"], t["z"], "-", color=PLOT_PALETTE["qc"], lw=1.3, label="qc")
            ax_n.set_xlim(0, max(5.0, float(np.nanmax(t["qc"])) * 1.1))
            ax_n.set_xlabel(L["ax_qc"])
        else:
            ax_n.plot(t["N"], t["z"], "o-", color=PLOT_PALETTE["N"], ms=4, lw=1.1, label="N")
            ax_n.plot(self.main["ncs"], t["z"], "s-", color=PLOT_PALETTE["Ncs"], ms=4, lw=1.3,
                      label="(N1)60cs")
            ax_n.set_xlim(0, max(10.0, float(np.nanmax(np.concatenate(
                [t["N"], self.main["ncs"]]))) * 1.1))
            ax_n.set_xlabel(L["ax_blows"])
        self._legend(ax_n, th, loc="lower left")
        ax_n.tick_params(labelleft=False)

        ax_fs = fig.add_subplot(grid[2], sharey=col)
        style_axis(ax_fs, th)
        self._depth_axis(ax_fs, th, label=False)
        self._shade_liquefied(ax_fs)
        self._fs_frame(ax_fs, th)
        self._fs_points(ax_fs, th, self.main["fs"], t["state"], t["z"], th["fg_dim"])
        ax_fs.tick_params(labelleft=False)
        handles = self._state_legend(th)
        if handles:
            self._legend(ax_fs, th, handles=handles, loc="lower left", fontsize=7.2)

        ax_s = fig.add_subplot(grid[3], sharey=col)
        style_axis(ax_s, th)
        self._depth_axis(ax_s, th, label=False)
        edges, below = self._settlement_curve()
        ax_s.fill_betweenx(edges, 0, below, color=PLOT_PALETTE["settlement"], alpha=0.18, lw=0)
        ax_s.plot(below, edges, color=PLOT_PALETTE["settlement"], lw=1.8)
        ax_s.set_xlim(0, max(10.0, float(below.max()) * 1.15))
        ax_s.set_xlabel(L["ax_settlement"])
        ax_s.tick_params(labelleft=False)
        ax_s.text(0.97, 0.02, L["lg_total"].format(v=res["settlement"]), transform=ax_s.transAxes,
                  ha="right", va="bottom", fontsize=8.5, color=th["fg"], bbox=label_box(th))
        if self.titles:
            fig.subplots_adjust(top=0.9)
        self._title(fig, th, "log")

    def _fs(self, fig, th):
        L, t = self.L, self.tests
        grid = fig.add_gridspec(1, 2, width_ratios=[0.35, 1.0], wspace=0.05)
        col = fig.add_subplot(grid[0])
        style_axis(col, th, grid=False)
        self._column(col, th)
        col.set_ylabel(L["ax_depth"])
        ax = fig.add_subplot(grid[1], sharey=col)
        style_axis(ax, th)
        self._depth_axis(ax, th, label=False)
        ax.tick_params(labelleft=False)
        self._shade_liquefied(ax)
        self._fs_frame(ax, th)
        self._fs_points(ax, th, self.main["fs"], t["state"], t["z"], PLOT_PALETTE["fs"],
                        L["method_" + self.a.method])
        dense_data = len(t["z"]) > 40            # a CPT: no labels on every point
        for zi, fi, state in zip(t["z"], self.main["fs"], t["state"]):
            if state not in ("not", "dry", "softening") and not dense_data:
                ax.annotate(f"{min(fi, FS_PLOT_MAX):.2f}" if fi < FS_PLOT_MAX else "> 2",
                            (min(fi, FS_PLOT_MAX), zi), xytext=(7, 0),
                            textcoords="offset points", fontsize=7, color=th["fg_dim"],
                            va="center", clip_on=False)
        handles, _ = ax.get_legend_handles_labels()
        handles += self._state_legend(th)
        handles.append(Line2D([], [], color=PLOT_PALETTE["water"], ls=(0, (6, 3)),
                              label=L["lg_water"]))
        self._legend(ax, th, handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0),
                     fontsize=7.5)
        self._title(fig, th, "fs")

    def _csr(self, fig, th):
        L, t, m = self.L, self.tests, self.main
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        self._depth_axis(ax, th)
        self._shade_liquefied(ax)
        wet = t["z"] > self.a.zw
        ax.plot(m["csr"][wet], t["z"][wet], "o-", color=PLOT_PALETTE["csr"], lw=1.7, ms=5,
                label=L["lg_csr"])
        ok = t["assessed"]
        # the resistance is broken where a test is not assessed (a clay, the dry crust)
        ax.plot(np.where(ok, m["crr"], np.nan), t["z"], "s-", color=PLOT_PALETTE["crr"], lw=1.7,
                ms=5, label=L["lg_crr"])
        ax.plot(np.where(ok, m["crr75"], np.nan), t["z"], "s--", color=PLOT_PALETTE["crr"],
                lw=1.0, ms=3, alpha=0.6, label=L["lg_crr75"])
        top = [m["csr"][wet].max()] if wet.any() else [0.3]
        if ok.any():
            top.append(float(np.nanmax(np.minimum(m["crr"][ok], 1.0))))
        ax.set_xlim(0, max(0.3, 1.15 * max(top)))
        ax.set_xlabel(L["ax_ratio"])
        handles, _ = ax.get_legend_handles_labels()
        handles.append(Line2D([], [], color=PLOT_PALETTE["water"], ls=(0, (6, 3)),
                              label=L["lg_water"]))
        self._legend(ax, th, handles=handles, loc="lower left")
        ax.set_title(L["method_" + self.a.method], fontsize=9.5, color=th["fg_dim"], loc="left")
        self._title(fig, th, "csr")

    def _spt(self, fig, th):
        L, t, m = self.L, self.tests, self.main
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        self._depth_axis(ax, th)
        series = [(t["N"], "N", "N", "o"), (t["N60"], "N60", "N60", "^"),
                  (m["n1"], "N1", "(N1)60", "D"), (m["ncs"], "Ncs", "(N1)60cs", "s")]
        for values, color, label, marker in series:
            ax.plot(values, t["z"], marker=marker, ls="-", color=PLOT_PALETTE[color], lw=1.3,
                    ms=4.5, label=label)
        top = float(np.nanmax(np.concatenate([s[0] for s in series])))
        ax.set_xlim(0, max(10.0, top * 1.1))
        ax.set_xlabel(L["ax_blows"])
        self._legend(ax, th, loc="lower left")
        ax.set_title(L["method_" + self.a.method], fontsize=9.5, color=th["fg_dim"], loc="left")
        self._title(fig, th, "spt")


    def _settlement(self, fig, th):
        L, t, res = self.L, self.tests, self.res
        grid = fig.add_gridspec(1, 2, wspace=0.08)
        ax_e = fig.add_subplot(grid[0])
        style_axis(ax_e, th)
        self._depth_axis(ax_e, th)
        for top, bot, eps, state in zip(t["top"], t["bot"], self.main["eps"], t["state"]):
            lo = max(top, self.a.zw)
            if eps > 0 and bot > lo:
                ax_e.add_patch(Rectangle((0, lo), 100.0 * eps, bot - lo,
                                         facecolor=STATE_COLORS[state], alpha=0.55,
                                         edgecolor=th["panel"], lw=0.6, zorder=3))
        for top, bot, eps in zip(t["top"], t["bot"], t["eps_dry"]):
            hi = min(bot, self.a.zw)
            if eps > 0 and hi > top:
                ax_e.add_patch(Rectangle((0, top), 100.0 * eps, hi - top,
                                         facecolor=PLOT_PALETTE["dry"], alpha=0.55,
                                         edgecolor=th["panel"], lw=0.6, zorder=3))
        eps_all = np.concatenate([self.main["eps"], t["eps_dry"]])
        peak = 100.0 * float(np.max(eps_all)) if eps_all.size else 0.0
        ax_e.set_xlim(0, max(1.0, peak * 1.2))
        ax_e.set_xlabel(L["ax_strain"])
        if self.a.settlement_depth < self.z_max:
            ax_e.axhline(self.a.settlement_depth, color=th["fg_dim"], lw=1.0, ls=":")

        ax_s = fig.add_subplot(grid[1], sharey=ax_e)
        style_axis(ax_s, th)
        self._depth_axis(ax_s, th, label=False)
        ax_s.tick_params(labelleft=False)
        edges, below = self._settlement_curve()
        ax_s.fill_betweenx(edges, 0, below, color=PLOT_PALETTE["settlement"], alpha=0.18, lw=0)
        ax_s.plot(below, edges, color=PLOT_PALETTE["settlement"], lw=2.0)
        limit = max(10.0, float(below.max()) * 1.15)
        if self.a.s_allow > 0:
            ax_s.axvline(self.a.s_allow, color=PLOT_PALETTE["allowable"], lw=1.2, ls="-.",
                         label=f"{L['lg_allow']} = {self.a.s_allow:.0f} mm")
            limit = max(limit, self.a.s_allow * 1.1)
            self._legend(ax_s, th, loc="lower right")
        ax_s.set_xlim(0, limit)
        ax_s.set_xlabel(L["ax_settlement"])
        ax_s.text(0.97, 0.10, L["lg_total"].format(v=res["settlement"]), transform=ax_s.transAxes,
                  ha="right", va="bottom", fontsize=9, color=th["fg"], bbox=label_box(th))
        self._title(fig, th, "settlement")

    def _cpt(self, fig, th):
        L, t = self.L, self.tests
        grid = fig.add_gridspec(1, 3, wspace=0.08)
        panels = [("qc", L["ax_qc"]), ("fs_cpt", L["ax_fs_cpt"]), ("Ic", "Ic")]
        for index, (key, label) in enumerate(panels):
            ax = fig.add_subplot(grid[index])
            style_axis(ax, th)
            self._depth_axis(ax, th, label=index == 0)
            if index:
                ax.tick_params(labelleft=False)
            color = {"qc": "qc", "fs_cpt": "fs_cpt", "Ic": "ic"}[key]
            ax.plot(t[key], t["z"], "-", color=PLOT_PALETTE[color], lw=1.4)
            if key == "qc":
                ax.plot(t["qt"] / 1000.0, t["z"], "--", color=PLOT_PALETTE["Ncs"], lw=1.0,
                        label="qt")
                ax.plot(self.main["ncs"] * 0.1013, t["z"], ":", color=PLOT_PALETTE["N1"], lw=1.2,
                        label="qc1Ncs·Pa")
                self._legend(ax, th, loc="lower right")
            if key == "Ic":
                ax.axvline(self.a.ic_limit, color=PLOT_PALETTE["required"], lw=1.2, ls="--",
                           label=f"Ic = {self.a.ic_limit:.2f}")
                ax.set_xlim(1.0, 4.0)
                ax.fill_betweenx(t["z"], self.a.ic_limit, np.maximum(t["Ic"], self.a.ic_limit),
                                 color=PLOT_PALETTE["safe"], alpha=0.25, lw=0)
                self._legend(ax, th, loc="lower right")
            else:
                ax.set_xlim(0, float(np.nanmax(t[key])) * 1.1 + 1e-9)
            ax.set_xlabel(label)
        self._title(fig, th, "cpt")

    def _sbt(self, fig, th):
        """Robertson's normalised soil behaviour type chart, with the Ic zones."""
        L, t = self.L, self.tests
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.set_xscale("log")
        ax.set_yscale("log")
        f = np.logspace(-1, 1, 200)
        q = np.logspace(0, 3, 200)
        ff, qq = np.meshgrid(f, q)
        ic = np.sqrt((3.47 - np.log10(qq)) ** 2 + (np.log10(ff) + 1.22) ** 2)
        levels = [1.31, 2.05, 2.60, 2.95, 3.60]
        cs = ax.contour(ff, qq, ic, levels=levels, colors=[th["fg_dim"]], linewidths=0.9)
        ax.clabel(cs, fmt="Ic=%.2f", fontsize=7)
        ax.contour(ff, qq, ic, levels=[self.a.ic_limit], colors=[PLOT_PALETTE["required"]],
                   linewidths=1.6, linestyles="--")
        for state in list(dict.fromkeys(t["state"])):
            rows = t["state"] == state
            hollow = state in ("not", "dry")
            ax.scatter(t["F"][rows], t["Q"][rows], s=20, marker=STATE_MARKERS.get(state, "o"),
                       facecolor="none" if hollow else STATE_COLORS[state],
                       edgecolor=STATE_COLORS[state] if hollow else th["panel"],
                       lw=1.0 if hollow else 0.5, zorder=4, label=L["state_" + state])
        ax.set_xlim(0.1, 10)
        ax.set_ylim(1, 1000)
        ax.set_xlabel(L["ax_F"])
        ax.set_ylabel(L["ax_Q"])
        ax.grid(True, which="both", color=th["border"], lw=0.5, alpha=0.6)
        self._legend(ax, th, loc="upper right")
        self._title(fig, th, "sbt")

    def _lateral(self, fig, th):
        L, t, res, a = self.L, self.tests, self.res, self.a
        grid = fig.add_gridspec(1, 2, wspace=0.08)
        ax_g = fig.add_subplot(grid[0])
        style_axis(ax_g, th)
        self._depth_axis(ax_g, th)
        gamma = self.main["gamma"]
        for top, bot, g, state in zip(t["top"], t["bot"], gamma, t["state"]):
            lo, hi = max(top, a.zw), min(bot, res["z_ldi"])
            if g > 0 and hi > lo:
                ax_g.add_patch(Rectangle((0, lo), 100.0 * g, hi - lo,
                                         facecolor=STATE_COLORS[state], alpha=0.55,
                                         edgecolor=th["panel"], lw=0.6, zorder=3))
        ax_g.set_xlim(0, max(5.0, 100.0 * float(np.max(gamma, initial=0.0)) * 1.15))
        ax_g.set_xlabel(L["ax_gamma"])
        if res["z_ldi"] < self.z_max:
            ax_g.axhline(res["z_ldi"], color=th["fg_dim"], lw=1.0, ls=":")

        ax = fig.add_subplot(grid[1], sharey=ax_g)
        style_axis(ax, th)
        self._depth_axis(ax, th, label=False)
        ax.tick_params(labelleft=False)
        order = np.argsort(t["top"])
        top, bot, part = t["top"][order], t["bot"][order], t["ldi"][order]
        cumulative = np.cumsum(part)
        z = np.concatenate([[0.0], np.column_stack([top, bot]).ravel()])
        c = np.concatenate([[0.0], np.column_stack([cumulative - part, cumulative]).ravel()])
        ax.plot(c, z, color=PLOT_PALETTE["gamma"], lw=2.0)
        ax.fill_betweenx(z, 0, c, color=PLOT_PALETTE["gamma"], alpha=0.18, lw=0)
        ax.set_xlim(0, max(0.1, res["ldi"] * 1.15))
        ax.set_xlabel(L["ax_ldi"])
        if a.geometry == "level":
            text = f"LDI = {res['ldi']:.2f} m · {L['geometry_level'].lower()}"
        else:
            text = f"LDI = {res['ldi']:.2f} m → LD = {res['ld']:.2f} m"
        ax.text(0.97, 0.03, text, transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8.5, color=th["fg"], bbox=label_box(th))
        self._title(fig, th, "lateral")

    def _indices(self, fig, th):
        L, t, res = self.L, self.tests, self.res
        grid = fig.add_gridspec(1, 2, wspace=0.08)
        order = np.argsort(t["top"])
        top, bot = t["top"][order], t["bot"][order]
        for index, (key, color, label) in enumerate([("lpi", "lpi", "ax_lpi"),
                                                     ("lsn", "lsn", "ax_lsn")]):
            ax = fig.add_subplot(grid[index])
            style_axis(ax, th)
            self._depth_axis(ax, th, label=index == 0)
            if index:
                ax.tick_params(labelleft=False)
            part = t[key][order]
            cumulative = np.cumsum(part)
            z = np.concatenate([[0.0], np.column_stack([top, bot]).ravel()])
            c = np.concatenate([[0.0], np.column_stack([cumulative - part, cumulative]).ravel()])
            # an interval's share grows through it; drawn straight across for clarity
            ax.plot(c, z, color=PLOT_PALETTE[color], lw=2.0)
            ax.fill_betweenx(z, 0, c, color=PLOT_PALETTE[color], alpha=0.18, lw=0)
            total = res[key]
            ax.set_xlim(0, max(5.0, total * 1.15))
            ax.set_xlabel(L[label])
            if key == "lpi":
                for level in (5.0, 15.0):
                    ax.axvline(level, color=th["fg_dim"], lw=0.9, ls=":")
                text = f"LPI = {total:.1f} — {L['lpi_' + res['lpi_class']]}"
            else:
                for level in (10.0, 20.0, 30.0, 40.0):
                    ax.axvline(level, color=th["fg_dim"], lw=0.8, ls=":")
                text = f"LSN = {total:.1f} — {L['lsn_' + res['lsn_class']]}"
            ax.text(0.97, 0.03, text, transform=ax.transAxes, ha="right", va="bottom",
                    fontsize=8.5, color=th["fg"], bbox=label_box(th))
        self._title(fig, th, "indices")

    def _methods(self, fig, th):
        L, t, res = self.L, self.tests, self.res
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        self._depth_axis(ax, th)
        self._fs_frame(ax, th)
        for key, m in res["methods"].items():
            fs = m["fs_eff"]
            if not np.isfinite(fs).any():
                continue
            main = key == self.a.method
            # NaN (not assessed) breaks the line across a clay or above the water
            ax.plot(np.minimum(fs, FS_PLOT_MAX), t["z"],
                    marker="o" if main else ".", ls="-" if key != "vs2000" else "--",
                    color=PLOT_PALETTE[key], lw=2.2 if main else 1.2, ms=6 if main else 5,
                    label=L["method_" + key], zorder=4 if main else 3, clip_on=False)
        handles, _ = ax.get_legend_handles_labels()
        handles.append(Line2D([], [], color=PLOT_PALETTE["water"], ls=(0, (6, 3)),
                              label=L["lg_water"]))
        self._legend(ax, th, handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0))
        self._title(fig, th, "methods")

    def _susceptibility(self, fig, th):
        L, t = self.L, self.tests
        plastic = np.asarray(t["PI"]) > 0
        if not plastic.any():
            ax = fig.add_subplot(111)
            ax.set_axis_off()
            ax.text(0.5, 0.5, L["lg_no_fines"], ha="center", va="center", color=th["fg_dim"],
                    fontsize=11)
            self._title(fig, th, "susceptibility")
            return
        LL, PI, wn = (np.asarray(t[k], float)[plastic] for k in ("LL", "PI", "wn"))
        z = t["z"][plastic]
        classes = [c for c, p in zip(t["class"], plastic) if p]
        grid = fig.add_gridspec(1, 2, wspace=0.22)

        # ---- plasticity chart with Seed et al.'s zones
        ax = fig.add_subplot(grid[0])
        style_axis(ax, th)
        ax.grid(True, color=th["border"], lw=0.6)
        ll_max = max(60.0, float(np.max(LL)) * 1.2)
        x = np.linspace(0, ll_max, 100)
        ax.plot(x, np.maximum(0.73 * (x - 20.0), 0.0), color=th["fg_dim"], lw=1.1,
                label=L["lg_a_line"])
        ax.plot(x, np.maximum(0.9 * (x - 8.0), 0.0), color=th["fg_dim"], lw=1.0, ls="--",
                label=L["lg_u_line"])
        ax.add_patch(Rectangle((0, 0), 37, 12, facecolor=PLOT_PALETTE["liquefied"], alpha=0.12,
                               edgecolor=PLOT_PALETTE["liquefied"], lw=1.0,
                               label=L["lg_seed_a"]))
        ax.add_patch(Rectangle((0, 0), 47, 20, facecolor="none",
                               edgecolor=PLOT_PALETTE["marginal"], lw=1.2, ls="--",
                               label=L["lg_seed_b"]))
        self._samples(ax, th, LL, PI, z, classes)
        ax.set_xlim(0, ll_max)
        ax.set_ylim(0, max(30.0, float(np.max(PI)) * 1.25))
        ax.set_xlabel(L["ax_LL"])
        ax.set_ylabel(L["ax_PI"])
        self._legend(ax, th, loc="upper left", fontsize=7.2)

        # ---- Bray & Sancio (2006)
        ax = fig.add_subplot(grid[1])
        style_axis(ax, th)
        ax.grid(True, color=th["border"], lw=0.6)
        ratio = np.where(LL > 0, wn / np.where(LL > 0, LL, 1.0), np.nan)
        pi_max = max(30.0, float(np.max(PI)) * 1.25)
        r_max = max(1.4, float(np.nanmax(ratio)) * 1.1 if np.isfinite(ratio).any() else 1.4)
        ax.add_patch(Rectangle((0, 0.85), 12, r_max - 0.85, facecolor=PLOT_PALETTE["liquefied"],
                               alpha=0.14, edgecolor=PLOT_PALETTE["liquefied"], lw=1.0,
                               label=L["lg_bs_susc"]))
        ax.add_patch(Rectangle((0, 0.8), 18, r_max - 0.8, facecolor="none",
                               edgecolor=PLOT_PALETTE["marginal"], lw=1.2, ls="--",
                               label=L["lg_bs_mod"]))
        self._samples(ax, th, PI, ratio, z, classes)
        ax.set_xlim(0, pi_max)
        ax.set_ylim(0.4, r_max)
        ax.set_xlabel(L["ax_PI"])
        ax.set_ylabel(L["ax_wc_ll"])
        handles, _ = ax.get_legend_handles_labels()
        present = list(dict.fromkeys(classes))
        handles += [Patch(color=CLASS_COLORS[c], label=L["class_" + c]) for c in present]
        self._legend(ax, th, handles=handles, loc="lower right", fontsize=7.2)
        ax.set_title(L["susc_" + self.a.criterion], fontsize=9.5, color=th["fg_dim"], loc="left")
        self._title(fig, th, "susceptibility")

    def _samples(self, ax, th, x, y, z, classes):
        """The samples as dots, labelled with their depths; samples with the same
        properties (a layer's values, inherited) share one dot and one label."""
        places = {}
        for xi, yi, zi, c in zip(x, y, z, classes):
            if np.isfinite(xi) and np.isfinite(yi):
                places.setdefault((round(float(xi), 6), round(float(yi), 6), c), []).append(zi)
        for (xi, yi, c), depths in places.items():
            ax.plot([xi], [yi], "o", ms=7, color=CLASS_COLORS[c], mec=th["panel"], mew=1.0,
                    zorder=5)
            ax.annotate(", ".join(f"{d:g}" for d in depths) + " m", (xi, yi), xytext=(6, 4),
                        textcoords="offset points", fontsize=7, color=th["fg_dim"])
