"""
SlipSurface IQ MSEW — mechanically stabilised earth walls, driven from a browser.

The program designs and checks a reinforced soil wall — a facing, layers of
steel strips or geosynthetics in a compacted fill, and the retained soil
behind — the way the FHWA and AASHTO guidance (FHWA-NHI-10-024,
AASHTO LRFD 11.10) does it, and the way the MSEW program made familiar:

    1. Earth pressure   — Coulomb / Rankine Ka of the retained and the
                          reinforced fill, with a battered face and a sloping
                          backfill
    2. External         — sliding, overturning and eccentricity of the
                          reinforced block, and the bearing capacity of the
                          foundation under it by the factor sets of
                          Terzaghi, Meyerhof, Hansen, Vesić and EN 1997-1
    3. Internal         — the maximum tension at every reinforcement layer
                          (the Simplified Method), and each layer's tensile,
                          pullout and connection checks, and sliding along it
    4. Reinforcement    — geosynthetic strength after installation damage,
                          creep and durability; steel strip section after
                          corrosion over the design life
    5. Earthquake       — the pseudo-static method: the dynamic thrust, the
                          inertia of the reinforced mass and of the active zone
    6. Design           — ASD factors of safety or LRFD load and resistance
                          factors, and the reinforcement length the checks need

On top of it, a height study runs the same design rule over a range of wall
heights and reports how every check, and the length needed, changes with
the height.

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    slipsurface.msew.config        app identity, defaults, themes, palette
    slipsurface.msew.i18n          every text of the program, English and Turkish
    slipsurface.msew.earth         earth pressure coefficients and seismic thrust
    slipsurface.msew.reinforcement reinforcement strength, corrosion and pullout
    slipsurface.common.factors       bearing capacity and correction factors
    slipsurface.msew.capacity      the general bearing capacity equation
    slipsurface.msew.engine        the wall analysis: external, bearing, internal
    slipsurface.msew.heights       the height study
    slipsurface.msew.plotting      analysis figures
    slipsurface.msew.report        calculation report: HTML, PDF, DOCX
    slipsurface.msew.forms         input schema and readers (interface-independent)
    slipsurface.msew.web           local web server and the browser interface

Run it:  slipsurface-msew          (or  python -m slipsurface.msew)
"""

from slipsurface.versioning import module_version

__version__ = module_version(__file__)

APP_NAME = "SlipSurface IQ MSEW"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
