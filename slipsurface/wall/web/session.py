"""
The one working session the server keeps.

Kept apart from the HTTP layer: there is no network here, only "take a
dictionary of inputs, run the analysis, give the results back as a
dictionary". Everything the interface does can therefore be tested without
opening a socket.

An analysis — the stability, the slip circle search, the member design and
the search for the required heel — takes well under a second and runs
inline, so there is no background job to poll.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from .. import drawing, forms, render, report, summary
from ..engine import RetainingWall, WallError, proportions
from ..i18n import TRANSLATIONS, t
from .strings import shell_strings

#: Languages the interface offers
LANGS = ("en", "tr")


class Session:
    """The single analysis session the server knows about."""

    def __init__(self, lang: str = "en", theme: str = "light"):
        self.lock = threading.Lock()
        self.lang = lang if lang in LANGS else "en"
        self.theme = theme
        self.wall: Optional[RetainingWall] = None
        self.values: Dict[str, Any] = {}

    # ------------------------------------------------------------------ language
    def set_language(self, lang: str) -> str:
        with self.lock:
            self.lang = lang if lang in LANGS else "en"
            return self.lang

    def set_theme(self, theme: str) -> str:
        with self.lock:
            self.theme = "dark" if theme == "dark" else "light"
            return self.theme

    @property
    def L(self) -> dict:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

    def _explain(self, exc: Exception) -> str:
        """An input error in the user's language."""
        if isinstance(exc, WallError):
            return t(self.lang, exc.key, **exc.params)
        return str(exc)

    # ------------------------------------------------------------------ what the page loads with
    def meta(self) -> dict:
        """Everything the interface reads on startup: version, texts, schema."""
        from .. import APP_NAME, __version__
        return {
            "app": APP_NAME,
            "version": __version__,
            "language": self.lang,
            "languages": list(LANGS),
            "strings": shell_strings(self.lang),
            "schema": forms.schema(self.lang),
            "defaults": forms.defaults(self.lang),
            "figures": render.PLOT_KEYS,
            "figure_labels": {key: self.L[f"fig_{key}"] for key in render.PLOT_KEYS},
        }

    def state(self) -> dict:
        with self.lock:
            return {"has_analysis": self.wall is not None}

    # ================================================================== analysis
    def analyse(self, values: dict) -> dict:
        """Runs the wall analysis on the interface's values."""
        try:
            wall = RetainingWall(forms.to_config(values))
            wall.run()
        except WallError as exc:
            raise ValueError(self._explain(exc)) from exc

        with self.lock:
            self.wall = wall
            self.values = dict(values)

        res = wall.results
        lang = self.lang
        return {
            "ok": True,
            "cards": summary.cards(wall, lang),
            "text": summary.results_text(wall, lang),
            "headline": summary.headline(wall, lang),
            "figures": render.available_figures(wall),
            "warnings": summary.warnings(wall, lang),
            "stability": summary.stability_table(wall, lang),
            "bearing": summary.bearing_table(wall, lang),
            "methods": summary.methods_table(wall, lang),
            "forces": summary.forces_table(wall, lang),
            "seismic": summary.seismic_table(wall, lang) if res["seismic"] else None,
            "design": summary.design_table(wall, lang) if res["design"] else None,
            "schedule": summary.schedule_table(wall, lang) if res["design"] else None,
            "all_ok": summary.all_ok(res),
            "required_heel": res["required_heel"],
        }

    def suggest(self, values: dict) -> dict:
        """Preliminary dimensions for the wall's height and backslope."""
        cfg = forms.to_config(values)
        try:
            dims = proportions(cfg["geometry"]["H"], cfg["geometry"]["backslope"])
        except WallError as exc:
            raise ValueError(self._explain(exc)) from exc
        if cfg["key"]["enabled"]:
            dims["key_offset"] = dims["toe"]
        return {"ok": True, "values": dims}

    # ------------------------------------------------------------------ figures
    def plot(self, kind: str) -> bytes:
        """The requested figure as PNG."""
        with self.lock:
            wall, theme = self.wall, self.theme
        if wall is None:
            raise ValueError(shell_strings(self.lang)["no_results"])
        return render.figure_to_png(render.analysis_figure(wall, kind, self.lang, theme))

    # ================================================================== outputs
    def report(self, fmt: str, path: str) -> str:
        """Writes the calculation report in the chosen format; returns the path."""
        with self.lock:
            wall = self.wall
        if wall is None:
            raise ValueError(shell_strings(self.lang)["no_results"])
        writer = {"pdf": report.export_pdf, "html": report.export_html,
                  "docx": report.export_docx}.get(fmt)
        if writer is None:
            raise ValueError(f"unknown report format: {fmt}")
        writer(path, wall, self.lang)
        return path

    def dxf(self) -> bytes:
        """The reinforcement drawing as DXF."""
        with self.lock:
            wall = self.wall
        if wall is None or not wall.results.get("design"):
            raise ValueError(shell_strings(self.lang)["no_results"])
        return drawing.to_dxf(drawing.build(wall, self.lang))

    # ================================================================== project files
    def project_file(self, values: dict) -> dict:
        """What `Save` downloads."""
        return forms.project_file(values)

    def load_project(self, data: dict) -> dict:
        """Flat interface values from a project file, defaults filling the gaps."""
        if not isinstance(data, dict) or data.get("format") not in (None, *forms.READ_FORMATS):
            raise ValueError(shell_strings(self.lang)["bad_file"])
        return {"ok": True, "values": forms.from_config(data, forms.defaults(self.lang))}
