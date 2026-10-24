"""
slipsurface.kinematic.kinematics.plots — kinematik tarama stereoneti.

Çizim tamamen `slipsurface.kinematic.stereonet` ortak projeksiyonu üzerine kuruludur; limit
denge modülünün stereoneti ile aynı geometriyi ve aynı görsel dili paylaşır.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from .. import stereonet as _st
from ..rockslope import style as rstyle
from .engine import PLANAR, TOPPLING, ScreeningResult, critical_zone_grid, friction_cone_angle

MIN_DENSITY_SAMPLES = 6       # altında kutup yoğunluğu anlamlı değil

CRIT = "#c0392b"
#: low concentration blue, then cyan, green, yellow, orange and red where the poles cluster most
DENSITY_CMAP = LinearSegmentedColormap.from_list(
    "concentration", ["#4a78b8", "#5bb8d4", "#8fcf72", "#f1d84a", "#f08a3c", "#c0392b"])
SAFE_DARK = "#1f2937"


def _density_levels(vmax: float) -> np.ndarray:
    """Contour levels in round percentages, from just above zero to the maximum."""
    step = next((s for s in (0.5, 1, 2, 2.5, 5, 10) if vmax / s <= 12), 20)
    top = np.ceil(vmax / step) * step
    return np.arange(step / 2.0, top + step, step) if vmax / step < 3 else np.arange(step, top + step, step)


def plot_screening(ax, result: ScreeningResult, labels: Sequence[str], dips, dip_dirs,
                   show_zone: bool = True, show_density: bool = True, title: str = "",
                   palette: Optional[dict] = None, direction_labels=("K", "D", "G", "B"),
                   slope_label: str = "Şev yüzü", cone_label: str = "Limit konisi",
                   density_label: str = "Kutup yoğunluğu (% / %1 alan)"):
    """Kinematik tarama stereonetini `ax` üzerine çizer.

    `palette`: {"fg", "muted", "grid", "accent"} — koyu temada okunabilirlik için.
    """
    p = {"fg": SAFE_DARK, "muted": rstyle.GREY, "grid": "#e2e6ea", "accent": rstyle.NAVY}
    p.update(palette or {})

    dips = np.atleast_1d(np.asarray(dips, float))
    dip_dirs = np.atleast_1d(np.asarray(dip_dirs, float))

    ax.clear()
    _st.draw_net(ax, grid_color=p["grid"], edge_color=p["accent"], text_color=p["muted"],
                 labels=direction_labels)
    if title:
        ax.set_title(title, color=p["accent"], fontweight="bold", fontsize=11, pad=12)
    if len(dips) == 0:
        return ax

    mode = result.mode

    # --- kritik bölge taraması (hafif kırmızı bulut) --------------------------
    if show_zone:
        pl, tr = critical_zone_grid(mode, result.slope_dip, result.slope_dir,
                                    result.friction, result.lateral_limit)
        if len(pl):
            zx, zy = _st.line_xy(tr, pl)
            ax.plot(zx, zy, marker="s", ls="none", ms=3, color=CRIT, alpha=0.10, zorder=2)

    # --- kutup yoğunluğu ------------------------------------------------------
    # Yoğunlaşma arttıkça maviden yeşil ve sarıya, en sıkı kümelerde kırmızıya geçen dolgu. Kamb sayım konisi çok küçük örneklemlerde tüm
    # ağı kaplayacak kadar açıldığından altı eşik altında çizilmez.
    if show_density and len(dips) >= MIN_DENSITY_SAMPLES:
        p_plunge, p_trend = 90.0 - dips, (dip_dirs + 180.0) % 360.0
        grid = _st.density_grid(p_trend, p_plunge)
        if grid is not None:
            X, Y, Z = grid
            vmax = float(np.nanmax(Z))
            if vmax > 0:
                levels = _density_levels(vmax)
                fill = ax.contourf(X, Y, Z, levels=levels, cmap=DENSITY_CMAP, alpha=0.8,
                                   zorder=1.5, extend="max")
                ax.contour(X, Y, Z, levels=levels[1:], colors="white", linewidths=0.6,
                           alpha=0.9, zorder=1.6)
                cb = ax.figure.colorbar(fill, ax=ax, shrink=0.55, pad=0.03, aspect=22)
                cb.set_label(density_label, fontsize=8, color=p["muted"])
                cb.ax.tick_params(labelsize=7, colors=p["muted"])
                cb.outline.set_edgecolor(p["grid"])

    # --- şev yüzü ve limit konisi --------------------------------------------
    sx, sy = _st.great_circle(result.slope_dip, result.slope_dir)
    ax.plot(sx, sy, color="#2874a6", lw=2.2, zorder=6,
            label=f"{slope_label} {result.slope_dip:.0f}/{result.slope_dir:03.0f}")
    cone = friction_cone_angle(mode, result.slope_dip, result.friction)
    cx, cy = _st.small_circle(0.0, 90.0, cone)
    ax.plot(cx, cy, color=CRIT, lw=1.2, ls="--", zorder=5,
            label=f"{cone_label} {cone:.0f}° (φ = {result.friction:.0f}°)")

    # --- bileşenler -----------------------------------------------------------
    if mode in (PLANAR, TOPPLING):
        for it in result.items:
            col = CRIT if it.critical else p["fg"]
            x, y = _st.pole_xy(it.value1, it.value2)
            ax.plot(x, y, marker="o", ls="none", ms=7 if it.critical else 6, color=col,
                    mec="#7b241c" if it.critical else p["fg"], mew=0.8, zorder=8)
            ax.text(x, y, f"  {it.name}", fontsize=9, color=col, fontweight="bold",
                    va="center", zorder=9)
    else:
        for d, dd in zip(dips, dip_dirs):
            gx, gy = _st.great_circle(d, dd)
            ax.plot(gx, gy, color=p["muted"], lw=1.0, alpha=0.6, zorder=4)
        for it in result.items:
            if np.isnan(it.value1):
                continue
            col = CRIT if it.critical else p["fg"]
            x, y = _st.line_xy(it.value2, it.value1)
            ax.plot(x, y, marker="D", ls="none", ms=8 if it.critical else 6, color=col,
                    mec="#7b241c" if it.critical else p["fg"], mew=0.8, zorder=8)
            if it.critical:
                ax.text(x, y, f"  {it.name}", fontsize=8, color=col, va="center", zorder=9)

    leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=8, ncol=2,
                    frameon=True)
    if leg is not None:
        leg.get_frame().set_alpha(0.9)
        for t in leg.get_texts():
            t.set_color(p["fg"])
    return ax
