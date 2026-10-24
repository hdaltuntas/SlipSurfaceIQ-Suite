"""
Figure production for SlipSurface IQ Wall.

The interface runs in a browser, so figures are drawn on the server and sent
as PNG. The same functions draw the figures that go into the report, so what
is on screen and what is in the report are the same picture.

Matplotlib is used through the Agg backend: the server needs no display.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure  # noqa: E402

from .plotting import PLOT_KEYS, Plotter, available_figures  # noqa: E402

#: Resolution of the PNGs (enough for the screen, and used by the report)
DPI = 130

#: Figures drawn taller than the rest: the drawing and the schedule
TALL = {"reinforcement": (10.0, 9.0), "schedule": (10.0, 7.5)}

__all__ = ["DPI", "PLOT_KEYS", "figure_to_png", "analysis_figure", "available_figures",
           "figure_size"]


def figure_size(key: str, default=(10.0, 7.0)):
    return TALL.get(key, default)


def figure_to_png(fig: Figure, dpi: int = DPI) -> bytes:
    """The figure as PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    return buf.getvalue()


def analysis_figure(wall, key: str, lang: str = "en", theme: str = "light",
                    size=None) -> Figure:
    """One analysis figure."""
    if key not in PLOT_KEYS:
        raise ValueError(f"unknown figure: {key}")
    fig = Figure(figsize=size or figure_size(key), dpi=DPI)
    Plotter(wall, lang, theme).draw(key, fig)
    return fig
