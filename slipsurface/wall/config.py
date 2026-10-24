"""
Configuration for SlipSurface IQ Wall: the default project, the choice lists, and the
theme and plot palette shared by the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `slipsurface.wall.i18n`.
"""

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION", "DEFAULT_CONFIG", "THEMES", "PLOT_PALETTE",
           "SOIL_FILL", "METHOD_COLORS", "PRESSURE_METHODS", "PASSIVE_METHODS",
           "BEARING_METHODS", "SEISMIC_METHODS", "TAPERS", "SITE_CLASSES", "MOBILITY",
           "GRADES", "STEELS", "ACCENT", "BAR_COLORS"]

# --- Choice lists (the first entry is the default where one is needed) -----
#: The earth pressure on the virtual back: Rankine's, Coulomb's, the pressure
#: at rest of a wall that cannot yield, and a numerical trial wedge
PRESSURE_METHODS = ["rankine", "coulomb", "at_rest", "trial_wedge"]

#: The passive resistance of the soil in front of the wall
PASSIVE_METHODS = ["rankine", "coulomb"]

#: The bearing capacity factor sets offered for the foundation of the wall
BEARING_METHODS = ["vesic", "meyerhof", "hansen", "terzaghi", "ec7"]

#: The dynamic thrust: Mononobe–Okabe, Seed–Whitman's simplification, and
#: Wood's for a wall that cannot yield
SEISMIC_METHODS = ["mononobe_okabe", "seed_whitman", "wood"]

#: Which face of the stem is inclined
TAPERS = ["back", "front"]

#: TBDY 2018 local site classes with tabulated coefficients (ZF needs a
#: site-specific study)
SITE_CLASSES = ["ZA", "ZB", "ZC", "ZD", "ZE"]

#: How far the wall may move during the earthquake, and the reduction βr of
#: the equivalent seismic coefficient that goes with it (TBDY 2018 §16.12,
#: EN 1998-5 Table 7.1): a flexural reinforced concrete wall is counted as
#: one that cannot yield (βr = 1) unless the designer accepts displacement
MOBILITY = {"rigid": 1.0, "free_200": 0.67, "free_300": 0.5}

#: Concrete classes of TS 500 and their characteristic cylinder strength [MPa]
GRADES = {"C20": 20.0, "C25": 25.0, "C30": 30.0, "C35": 35.0, "C40": 40.0,
          "C45": 45.0, "C50": 50.0}

#: Reinforcing steels (TS 708) and their characteristic yield strength [MPa]
STEELS = {"B420C": 420.0, "B500C": 500.0}

# --- Interface theme (web/static/style.css) and plot palette ---------------
# --- kept together so the figures always match the page they are shown on. -
ACCENT = "#9A6A1A"  # the colour of its group in the suite (retaining)

THEMES = {
    "dark": dict(bg="#262624", panel="#30302E", input_bg="#262624", fg="#F5F4ED",
                 fg_dim="#A6A39A", border="#4A4944", hover="#3A3A37", btn="#3A3A37",
                 muted="#6B6A64", accent="#D6A44E", accent_hover="#E2B769"),
    "light": dict(bg="#F5F4ED", panel="#FAF9F5", input_bg="#FFFFFF", fg="#141413",
                  fg_dim="#73726C", border="#E3E0D5", hover="#F0EEE6", btn="#F0EEE6",
                  muted="#B7B4AA", accent=ACCENT, accent_hover="#825812"),
}
# The report's figures: the light palette on white paper.
THEMES["paper"] = dict(THEMES["light"], bg="#FFFFFF", panel="#FFFFFF")

# Semantic colours: the same quantity is the same colour in every figure. Warm
# and muted, to sit on the paper-coloured page; terracotta marks the demand.
PLOT_PALETTE = dict(
    demand="#C6613F", capacity="#4E9A8A", required="#B0413E", seismic="#8C6BB1",
    water="#6FA8C7", concrete="#B9B5AC", concrete_edge="#6B6A64", failure="#B0413E",
    thrust="#C6613F", weight="#6B6A64", surcharge="#8C6BB1", pressure="#D9A55B",
    passive="#5E8C4A", ok="#5E8C4A", bad="#B0413E", ultimate="#C6613F",
    allowable="#4E9A8A", applied="#B0413E", moment="#C6613F", shear="#5B8DB8",
    rebar="#B0413E", dimension="#5B6770",
)

#: One colour per bar family in the drawing and the schedule
BAR_COLORS = {"stem": "#B0413E", "footing": "#2F5F8A", "distribution": "#5E8C4A",
              "key": "#8C6BB1"}

#: One colour per bearing capacity method, and per earth pressure method
METHOD_COLORS = {"terzaghi": "#5B8DB8", "meyerhof": "#8C6BB1", "hansen": "#D9A55B",
                 "vesic": "#C6613F", "ec7": "#4E9A8A",
                 "rankine": "#C6613F", "coulomb": "#5B8DB8", "at_rest": "#8C6BB1",
                 "trial_wedge": "#4E9A8A", "mononobe_okabe": "#B0413E"}

# Fill colours of the soils in the section (theme-dependent, since a light
# sandy tone reads poorly on a dark background).
SOIL_FILL = {
    "light": {"backfill": "#E3C98F", "front": "#C9D3B8", "foundation": "#A7B8A0"},
    "dark": {"backfill": "#8A7250", "front": "#66735C", "foundation": "#5E6E58"},
}
SOIL_FILL["paper"] = SOIL_FILL["light"]

DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: cantilever retaining wall",
        "analyst": "",
    },
    "geometry": {
        "H": 6.0,                  # underside of the footing to the top of the stem [m]
        "t_top": 0.30,             # stem thickness at the top [m]
        "t_bot": 0.60,             # stem thickness at the top of the footing [m]
        "taper": "back",           # which face of the stem is inclined
        "toe": 1.20,               # toe length, front of the footing to the stem [m]
        "heel": 3.00,              # heel length, stem to the back of the footing [m]
        "t_f": 0.70,               # footing thickness [m]
        "D": 0.50,                 # soil over the toe, above the top of the footing [m]
        "backslope": 0.0,          # β, slope of the backfill from the top of the stem [°]
        "toe_slope": 0.0,          # slope of the ground in front of the wall [°]
    },
    # A shear key under the footing: its depth below the base, its width, and
    # the distance from the front of the footing to the front of the key.
    "key": {"enabled": False, "depth": 0.60, "width": 0.50, "offset": 1.20},
    # Uniform surcharges on the backfill, and loads at the top of the stem.
    "loads": {
        "q_dead": 0.0,             # permanent uniform surcharge [kPa]
        "q_live": 10.0,            # live (traffic) uniform surcharge [kPa]
        "P_top": 0.0,              # permanent vertical line load on the stem [kN/m]
        "H_top": 0.0,              # live horizontal load at the top of the stem [kN/m]
    },
    "soils": {
        "backfill": {"gamma": 18.0, "gamma_sat": 20.0, "phi": 32.0, "c": 0.0},
        "foundation": {"gamma": 19.0, "gamma_sat": 20.0, "phi": 30.0, "c": 5.0},
        "water_back": 0.0,         # water table behind the wall, above the base [m]
        "water_front": 0.0,        # water in front of the wall, above the base [m]
        "water_depth": 10.0,       # water table below the base, for the bearing capacity [m]
        "gamma_water": 9.81,
        "gamma_concrete": 25.0,
    },
    "earth": {
        "method": "rankine",
        "delta_ratio": 0.67,       # δ/φ: wall friction of Coulomb and the trial wedge
        "OCR": 1.0,                # overconsolidation of the backfill, for K0
        "passive": False,          # count the passive resistance in front
        "passive_method": "rankine",
        "passive_ratio": 0.50,     # the share of the passive resistance counted
    },
    "options": {
        "bearing_method": "vesic",
        "bearing_embedment": True,     # the soil in front as a surcharge on the base
        "bearing_inclination": True,   # load inclination factors
        "bearing_depth": False,        # depth factors
        "base_friction": 0.67,         # δb/φ of the base
        "base_adhesion": 0.67,         # ca/c of the base
        "q_allow": 0.0,                # allowable soil pressure, 0 = none given [kPa]
        "global_enabled": True,        # the slip circle search
    },
    "criteria": {
        "FS_sliding": 1.5,
        "FS_overturning": 2.0,
        "ecc_static": 6.0,         # e ≤ B / ecc_static
        "FS_bearing": 3.0,
        "FS_global": 1.5,
        # the earthquake: TBDY 2018 §16.7 resistance factors of shallow
        # foundations for sliding (γRh) and bearing (γRv)
        "FS_sliding_seis": 1.1,
        "FS_overturning_seis": 1.5,
        "ecc_seismic": 3.0,
        "FS_bearing_seis": 1.4,
        "FS_global_seis": 1.1,
    },
    "seismic": {
        "enabled": False,
        "Ss": 0.80,                # short-period map spectral acceleration (AFAD)
        "S1": 0.22,                # 1-second map spectral acceleration (AFAD)
        "site": "ZC",
        "mobility": "free_300",
        "kh_manual": 0.0,          # a kh given directly, 0 = from TBDY
        "kv_ratio": 0.5,           # kv = ratio · kh
        "method": "mononobe_okabe",
        "dyn_height": 0.5,         # the dynamic increment acts at this share of the height
        "psi_live": 0.3,           # share of the live load in the earthquake combination
    },
    "concrete": {
        "grade": "C30",
        "steel": "B420C",
        "cover_stem": 50.0,        # clear cover of the stem [mm]
        "cover_footing": 60.0,     # clear cover of the footing [mm]
        "bar_stem": 0,             # main bar of the stem, 0 = chosen by the program [mm]
        "bar_footing": 0,          # main bar of the footing, 0 = chosen [mm]
        "rho_min": 0.0020,         # minimum ratio of the main steel, on b·h
        "rho_front": 0.0010,       # minimum ratio of the front face of the stem
        "rho_dist": 0.0015,        # minimum distribution steel, both faces together
        "curtail": True,           # stop half the stem bars where they are not needed
    },
}
