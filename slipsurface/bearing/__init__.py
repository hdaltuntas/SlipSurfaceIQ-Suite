"""
SlipSurface IQ Bearing — bearing capacity of shallow foundations, driven from a browser.

The program works out how much load a shallow foundation on a layered soil
profile can carry, by every method an engineer is likely to be asked for, and
checks the foundation against them:

    1. Strength        — the design c', φ' and cu of the failure zone, the
                         effective surcharge at the base and the effective
                         unit weight below it
    2. Capacity        — the general bearing capacity equation with the
                         bearing capacity factors of Terzaghi, Meyerhof,
                         Hansen, Vesić and EN 1997-1, and Skempton's
                         undrained Nc, each with its own shape, depth, load
                         inclination, base tilt, ground slope and
                         compressibility factors
    3. Eccentricity    — Meyerhof's effective area, the contact pressure and
                         the middle-third rule
    4. Layered ground  — strength averaged over the failure zone, or the
                         two-layer punching / load-spread checks
    5. Other methods   — SPT, CPT and pressuremeter correlations, and rock
                         (Hoek–Brown, CFEM Ksp)
    6. Seismic         — the pseudo-static inertia of the structure and of
                         the soil (Paolucci & Pecker)
    7. Checks          — bearing, sliding and eccentricity against a factor
                         of safety, or against EN 1997-1 Design Approaches

On top of it, a parametric or reliability study sweeps any input (a range, or
a distribution) and reports sensitivities and the probability of failure.

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    slipsurface.bearing.config        app identity, defaults, themes, palette
    slipsurface.bearing.i18n          every text of the program, English and Turkish
    slipsurface.common.factors       bearing capacity and correction factors
    slipsurface.bearing.capacity      the general bearing capacity equation
    slipsurface.bearing.layered       two-layer punching and load-spread checks
    slipsurface.bearing.seismic       pseudo-static bearing capacity
    slipsurface.bearing.insitu        SPT / CPT / pressuremeter correlations
    slipsurface.bearing.rock          bearing capacity on rock
    slipsurface.bearing.engine        the bearing capacity analysis
    slipsurface.bearing.study         parametric / reliability studies
    slipsurface.bearing.plotting      analysis figures
    slipsurface.bearing.study_plots   study figures
    slipsurface.bearing.report        calculation report: HTML, PDF, DOCX
    slipsurface.bearing.forms         input schema and readers (interface-independent)
    slipsurface.bearing.web           local web server and the browser interface

Run it:  slipsurface-bearing          (or  python -m slipsurface.bearing)
"""

from .. import __version__ as __version__  # one version for the whole suite

APP_NAME = "SlipSurface IQ Bearing"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
