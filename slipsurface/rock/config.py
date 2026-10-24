"""
Configuration for SlipSurface IQ Rock: the default project, the choice lists, and the
theme and plot palette shared by the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `slipsurface.rock.i18n`, and the tables
an engineer picks typical values from (mi, MR, σci, D, GSI) in
`slipsurface.rock.tables`.
"""

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION", "DEFAULT_CONFIG", "THEMES", "PLOT_PALETTE",
           "APPLICATIONS", "STRENGTH_SOURCES", "GSI_SOURCES", "MODULUS_METHODS",
           "EI_SOURCES", "ACCENT"]

# --- Choice lists (the first entry is the default where one is needed) -----

#: Where the intact rock's σci and mi come from: typed in, or fitted to
#: triaxial tests
STRENGTH_SOURCES = ["manual", "lab"]

#: How GSI is arrived at: typed in, read from the chart's classes, or
#: converted from another classification
GSI_SOURCES = ["direct", "chart", "jcond", "rmr", "q", "cai"]

#: What the rock mass is loaded by, which fixes the upper end σ3max of the
#: confinement the equivalent Mohr–Coulomb strength is fitted over
APPLICATIONS = ["general", "tunnel", "slope", "custom"]

#: Estimates of the rock mass deformation modulus
MODULUS_METHODS = ["generalized", "simplified", "hctc2002"]

#: The intact modulus Ei: typed in, or MR·σci
EI_SOURCES = ["mr", "direct"]

# --- Interface theme (web/static/style.css) and plot palette ---------------
# --- kept together so the figures always match the page they are shown on. -
ACCENT = "#4F6388"  # the colour of its group in the suite (rock)

THEMES = {
    "dark": dict(bg="#262624", panel="#30302E", input_bg="#262624", fg="#F5F4ED",
                 fg_dim="#A6A39A", border="#4A4944", hover="#3A3A37", btn="#3A3A37",
                 muted="#6B6A64", accent="#8FA3C8", accent_hover="#A5B6D6"),
    "light": dict(bg="#F5F4ED", panel="#FAF9F5", input_bg="#FFFFFF", fg="#141413",
                  fg_dim="#73726C", border="#E3E0D5", hover="#F0EEE6", btn="#F0EEE6",
                  muted="#B7B4AA", accent=ACCENT, accent_hover="#3F5275"),
}
# The report's figures: the light palette on white paper.
THEMES["paper"] = dict(THEMES["light"], bg="#FFFFFF", panel="#FFFFFF")

# Semantic colours: the same quantity is the same colour in every figure. Warm
# and muted, to sit on the paper-coloured page; terracotta marks the rock mass.
PLOT_PALETTE = dict(
    rock_mass="#C6613F", intact="#8C6BB1", mohr="#4E9A8A", residual="#6B6A64",
    limit="#A26A12", query="#B0413E", data="#5B8DB8", fit="#C6613F",
    cohesion="#5B8DB8", friction="#D9A55B", strength="#C6613F", tensile="#B0413E",
    mb="#5B8DB8", s="#8C6BB1", a="#D9A55B",
    generalized="#C6613F", simplified="#4E9A8A", hctc2002="#5B8DB8",
    general="#8C6BB1", tunnel="#C6613F", slope="#4E9A8A", custom="#D9A55B",
)

DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: Rock mass strength",
        "analyst": "",
    },
    # The intact rock. σci is the uniaxial compressive strength of the intact
    # rock, mi the Hoek–Brown constant; either typed in (a rock type and a
    # field strength grade fill them with typical values) or fitted to the
    # triaxial tests of `lab_data`.
    "intact": {
        "source": "manual",
        "rock_type": "sandstone",
        "strength_grade": "custom",
        "sigma_ci": 60.0,          # [MPa]
        "mi": 17.0,
    },
    # The rock mass: GSI and the disturbance factor D.
    "rock_mass": {
        "gsi_source": "direct",
        "GSI": 55.0,
        "structure": "very_blocky",   # the chart's classes (gsi_source = chart)
        "surface": "fair",
        "JCond89": 15.0,           # joint condition rating of RMR89 (0–30)
        "RQD": 60.0,               # rock quality designation [%]
        "RMR89": 60.0,             # RMR89 with a dry rating for groundwater
        "Q_prime": 5.0,            # Q' = RQD/Jn · Jr/Ja
        "Vb": 1000.0,              # block volume [cm³] (Cai et al.)
        "Jc": 1.0,                 # joint condition factor JW·JS/JA (Cai et al.)
        "disturbance_case": "custom",
        "D": 0.0,
    },
    # Deformability: the intact modulus Ei (typed in, or MR·σci) and how the
    # rock mass modulus is estimated from it.
    "modulus": {
        "method": "generalized",
        "Ei_source": "mr",
        "Ei": 20000.0,             # [MPa]
        "MR": 275.0,               # modulus ratio Ei/σci
    },
    # The confinement the equivalent Mohr–Coulomb strength is fitted over.
    "application": {
        "type": "general",
        "unit_weight": 26.0,       # of the rock mass [kN/m³]
        "depth": 100.0,            # depth of the tunnel, or height of the slope [m]
        "sigma3_max": 5.0,         # the custom upper end [MPa]
    },
    # One minor principal stress at which the instantaneous strength is read.
    "query": {
        "sigma3": 1.0,             # [MPa]
    },
    # Triaxial tests on intact specimens, for fitting σci and mi. σ3 = 0 is a
    # uniaxial test; a negative σ3 with σ1 = 0 a tensile one.
    "lab_data": [
        {"name": "UCS-1", "sigma3": 0.0, "sigma1": 62.0},
        {"name": "UCS-2", "sigma3": 0.0, "sigma1": 57.5},
        {"name": "TX-1", "sigma3": 5.0, "sigma1": 98.0},
        {"name": "TX-2", "sigma3": 10.0, "sigma1": 129.0},
        {"name": "TX-3", "sigma3": 15.0, "sigma1": 151.0},
        {"name": "TX-4", "sigma3": 20.0, "sigma1": 176.0},
    ],
}
