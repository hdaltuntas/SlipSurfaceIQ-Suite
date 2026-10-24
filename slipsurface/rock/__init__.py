"""
SlipSurface IQ Rock — rock mass strength and deformability, driven from a browser.

The program turns what is known about a rock mass — the strength of the intact
rock, the Geological Strength Index, the disturbance of the excavation — into
the parameters an analysis needs, after the generalised Hoek–Brown criterion:

    1. Intact rock     — σci and mi typed in, picked from typical values by
                         rock type and field strength grade, or fitted to
                         triaxial tests
    2. GSI             — typed in, read from the chart's classes, or
                         converted from JCond89 and RQD, RMR89, Q', or block
                         volume and joint condition
    3. Hoek–Brown      — mb, s and a; tensile, uniaxial and global strength
    4. Mohr–Coulomb    — the equivalent c' and φ' over the confinement of a
                         tunnel, a slope, a general case or a custom range;
                         the instantaneous c and φ at any σ3
    5. Deformability   — the rock mass modulus by Hoek & Diederichs (2006),
                         generalised and simplified, and Hoek et al. (2002)
    6. Residual        — the strength after failure (Cai et al. 2007)

On top of it, a parametric or probabilistic study sweeps any input (a range,
or a distribution) and reports the statistics and sensitivities of every
output — the characteristic values of c' and φ' among them.

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    slipsurface.rock.config        app identity, defaults, themes, palette
    slipsurface.rock.i18n          every text of the program, English and Turkish
    slipsurface.rock.tables        typical values: mi, MR, σci grades, D, GSI classes
    slipsurface.rock.hoekbrown     the generalised Hoek–Brown criterion
    slipsurface.rock.gsi           GSI from other classifications
    slipsurface.rock.labfit        σci and mi fitted to triaxial tests
    slipsurface.rock.engine        the analysis
    slipsurface.rock.study         parametric / probabilistic studies
    slipsurface.rock.plotting      analysis figures
    slipsurface.rock.study_plots   study figures
    slipsurface.rock.report        calculation report: HTML, PDF, DOCX
    slipsurface.rock.forms         input schema and readers (interface-independent)
    slipsurface.rock.web           local web server and the browser interface

Run it:  slipsurface-rock          (or  python -m slipsurface.rock)
"""

from .. import __version__ as __version__  # one version for the whole suite

APP_NAME = "SlipSurface IQ Rock"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
