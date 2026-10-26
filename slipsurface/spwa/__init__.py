"""
SlipSurface IQ Pile Wall Analysis — steel sheet pile and reinforced concrete bored pile walls, driven from a browser.

The program analyses cantilever and anchored sheet pile walls two ways and
compares them:

    0. The wall             — a steel sheet pile section, or a row of reinforced concrete
                             bored piles (stiffness per metre of wall, TS 500 bending capacity)
    1. Limit equilibrium   — free-earth support, Coulomb / Mononobe-Okabe
                             pressures, embedment by root-finding, anchor
                             forces, internal-force diagrams, design checks
    2. Beam-spring         — Winkler beam on elastoplastic soil springs with
                             automatic staged construction and tension-only
                             inclined anchors

On top of either, a parametric or reliability study sweeps any input (range,
or a distribution) and reports sensitivities, failure probability and the
reliability index.

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    slipsurface.spwa.config           app identity, defaults, themes, translations
    slipsurface.spwa.bored_pile       reinforced concrete pile: stiffness and bending capacity
    slipsurface.spwa.analysis_engine  limit-equilibrium core (free-earth support)
    slipsurface.spwa.beam_spring      Winkler beam-spring core (staged construction)
    slipsurface.spwa.study            parametric / reliability studies
    slipsurface.spwa.plotting         analysis figures (schematic + diagrams)
    slipsurface.spwa.study_plots      study figures (sweeps, scatter, histogram, tornado)
    slipsurface.spwa.report           calculation report: HTML, PDF, DOCX
    slipsurface.spwa.forms            input schema and readers (interface-independent)
    slipsurface.spwa.web              local web server and the browser interface

Run it:  slipsurface-spwa            (or  python -m slipsurface.spwa)
"""

from slipsurface.versioning import module_version

__version__ = module_version(__file__)

APP_NAME = "SlipSurface IQ Pile Wall Analysis"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
