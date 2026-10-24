"""
SlipSurface IQ Wall — cantilever reinforced concrete retaining walls, driven from a browser.

The program analyses and designs an inverted-T (cantilever) retaining wall — a
stem, a footing with a toe and a heel, an optional shear key, the backfill
behind and the foundation soil below — the way the classical texts and the
Turkish codes do it:

    1. Earth pressure   — Rankine, Coulomb, at rest (Jáky / EN 1997-1) and a
                          numerical trial wedge on the virtual back through
                          the heel, side by side; passive resistance in front
                          by Rankine and Coulomb; water and surcharges
    2. Stability        — sliding (base friction, adhesion, passive, shear
                          key), overturning about the toe, the eccentricity
                          of the resultant and the pressure under the base
    3. Bearing capacity — the foundation under Meyerhof's effective width by
                          the factor sets of Terzaghi, Meyerhof, Hansen,
                          Vesić and EN 1997-1, or an allowable pressure
    4. Global stability — slip circles under the wall by Bishop's simplified
                          method and by Fellenius', with a grid search
    5. Earthquake       — TBDY 2018: the site coefficients Fs and F1, SDS and
                          SD1, the design spectrum, kh = βr·0.4·SDS and kv,
                          and the dynamic thrust by Mononobe–Okabe,
                          Seed–Whitman or Wood, the inertia of the wall and of
                          the soil on the heel
    6. Reinforced concrete — TS 500 load combinations (and the earthquake
                          combination of TBDY 2018), the moment and shear of
                          the stem, the toe, the heel and the key, the steel
                          they need, the bars chosen, the curtailment of the
                          stem bars and the development lengths
    7. Drawing          — the reinforcement drawing of the section, the bar
                          bending schedule and the quantities, as figures and
                          as a DXF file

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    slipsurface.wall.config        app identity, defaults, themes, palette
    slipsurface.wall.i18n          every text of the program, English and Turkish
    slipsurface.wall.earth         earth pressure coefficients and seismic thrust
    slipsurface.wall.tbdy          TBDY 2018 site coefficients, spectrum, kh and kv
    slipsurface.common.factors       bearing capacity and correction factors
    slipsurface.wall.capacity      the general bearing capacity equation
    slipsurface.wall.concrete      TS 500 materials, flexure, shear, anchorage, bars
    slipsurface.wall.geometry      the wall's outline, areas and centroids
    slipsurface.wall.engine        the wall analysis: pressures, stability, bearing
    slipsurface.wall.globalstab    slip circles by Bishop and Fellenius
    slipsurface.wall.design        the reinforced concrete design and the bar layout
    slipsurface.wall.drawing       the reinforcement drawing, and its DXF
    slipsurface.wall.plotting      analysis figures
    slipsurface.wall.report        calculation report: HTML, PDF, DOCX
    slipsurface.wall.forms         input schema and readers (interface-independent)
    slipsurface.wall.web           local web server and the browser interface

Run it:  slipsurface-wall          (or  python -m slipsurface.wall)
"""

from .. import __version__ as __version__  # one version for the whole suite

APP_NAME = "SlipSurface IQ Wall"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
