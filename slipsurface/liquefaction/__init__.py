"""
SlipSurface IQ Liquefaction — liquefaction assessment from SPT and CPT, driven from a browser.

The program works out, depth by depth down a borehole — from its SPT tests or
from a CPT sounding — whether the ground liquefies in the design earthquake and
what that costs in settlement and lateral displacement:

    1. Susceptibility  — which soils can liquefy at all: sand-like soils, and
                         fine-grained soils judged from their Atterberg limits,
                         water content and clay fraction (Chinese criteria,
                         Andrews & Martin 2000, Seed et al. 2003, Bray &
                         Sancio 2006, Boulanger & Idriss 2006)
    2. SPT             — N60 and (N1)60 with the energy, borehole, rod length
                         and sampler corrections; the fines content correction
    3. Triggering      — CSR against CRR by Idriss & Boulanger (2014), Youd et
                         al. (2001, NCEER), Cetin et al. (2004) or the Turkish
                         Building Earthquake Code (TBDY 2018) from the SPT; by
                         Idriss & Boulanger (2014) or Robertson & Wride (1998)
                         from the CPT; a shear-wave check by Andrus & Stokoe
                         (2000) where Vs is known; cyclic softening of the
                         clay-like soils (Boulanger & Idriss 2007)
    4. Consequences    — post-liquefaction volumetric strain and settlement
                         (Ishihara & Yoshimine 1992, as fitted by Yoshimine et
                         al. 2006), the seismic compression of dry sand
                         (Pradel 1998), lateral spreading (Zhang et al. 2004),
                         the liquefaction potential index LPI (Iwasaki 1978)
                         and the severity number LSN (van Ballegooy et al. 2014)

On top of it, a parametric or reliability study sweeps any input (a range, or
a distribution) and reports sensitivities and the probability of liquefaction
or of exceeding the allowable settlement.

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    slipsurface.liquefaction.config          app identity, defaults, themes, palette
    slipsurface.liquefaction.i18n            every text of the program, English and Turkish
    slipsurface.liquefaction.spt             SPT corrections: N60, CN, (N1)60, fines
    slipsurface.liquefaction.cpt             CPT interpretation: qt, Ic, FC from Ic
    slipsurface.liquefaction.triggering      rd, MSF, Kσ and CRR of each method
    slipsurface.liquefaction.susceptibility  the fine-grained soil criteria
    slipsurface.liquefaction.consequences    strains, settlement (saturated and dry), LDI and
                                       lateral displacement, LPI, LSN
    slipsurface.liquefaction.engine          the liquefaction analysis
    slipsurface.liquefaction.study           parametric / reliability studies
    slipsurface.liquefaction.plotting        analysis figures
    slipsurface.liquefaction.study_plots     study figures
    slipsurface.liquefaction.report          calculation report: HTML, PDF, DOCX
    slipsurface.liquefaction.forms           input schema and readers (interface-independent)
    slipsurface.liquefaction.web             local web server and the browser interface

Run it:  slipsurface-liquefaction            (or  python -m slipsurface.liquefaction)
"""

from .. import __version__ as __version__  # one version for the whole suite

APP_NAME = "SlipSurface IQ Liquefaction"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
