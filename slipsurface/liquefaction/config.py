"""
Configuration for SlipSurface IQ Liquefaction: the default project, the choice lists,
and the theme and plot palette shared by the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `slipsurface.liquefaction.i18n`.
"""

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION", "DEFAULT_CONFIG", "THEMES", "PLOT_PALETTE",
           "SOIL_FILL", "METHODS", "METHODS_CPT", "SUSCEPTIBILITY", "PGA_SOURCES", "TEST_TYPES",
           "GEOMETRIES", "ACCENT", "PA", "soil_kind"]

#: Atmospheric pressure [kPa], the reference stress of the normalisations
PA = 101.325

# --- Choice lists (the first entry is the default where one is needed) -----
#: The field test the borehole was assessed from
TEST_TYPES = ["spt", "cpt"]
#: Triggering procedures from the SPT
METHODS = ["ib2014", "youd2001", "cetin2004", "tbdy2018"]
#: Triggering procedures from the CPT
METHODS_CPT = ["ib2014_cpt", "rw1998"]
#: Susceptibility criteria for fine-grained soils
SUSCEPTIBILITY = ["bray_sancio", "boulanger_idriss", "seed2003", "andrews_martin",
                  "chinese", "none"]
#: Where the peak ground acceleration comes from: entered, or 0.4·S_DS (TBDY 2018)
PGA_SOURCES = ["direct", "tbdy"]
#: Ground geometry for lateral spreading: level (none), gentle slope, free face
GEOMETRIES = ["level", "slope", "free_face"]

# --- Interface theme (web/static/style.css) and plot palette ---------------
# --- kept together so the figures always match the page they are shown on. -
ACCENT = "#5B7A3A"  # the colour of its group in the suite (foundations)

THEMES = {
    "dark": dict(bg="#262624", panel="#30302E", input_bg="#262624", fg="#F5F4ED",
                 fg_dim="#A6A39A", border="#4A4944", hover="#3A3A37", btn="#3A3A37",
                 muted="#6B6A64", accent="#9BBA78", accent_hover="#AECB8D"),
    "light": dict(bg="#F5F4ED", panel="#FAF9F5", input_bg="#FFFFFF", fg="#141413",
                  fg_dim="#73726C", border="#E3E0D5", hover="#F0EEE6", btn="#F0EEE6",
                  muted="#B7B4AA", accent=ACCENT, accent_hover="#4A6630"),
}
# The report's figures: the light palette on white paper.
THEMES["paper"] = dict(THEMES["light"], bg="#FFFFFF", panel="#FFFFFF")

# Semantic colours: the same quantity is the same colour in every figure. Warm and
# muted, to sit on the paper-coloured page; terracotta marks the governing result.
PLOT_PALETTE = dict(
    fs="#C6613F", csr="#B0413E", crr="#4E9A8A", liquefied="#B0413E", marginal="#D9A55B",
    safe="#5E8C4A", inert="#A6A39A", water="#6FA8C7", N="#8A8680", N60="#D9A55B",
    N1="#8C6BB1", Ncs="#5B8DB8", strain="#8C6BB1", settlement="#C6613F", lpi="#D9A55B",
    lsn="#4E9A8A", allowable="#B0413E", required="#A26A12", softening="#8C6BB1",
    dry="#D9A55B", gamma="#5B8DB8", qc="#8A8680", fs_cpt="#D9A55B", ic="#8C6BB1",
    ib2014_cpt="#C6613F", rw1998="#5B8DB8",
    ib2014="#C6613F", youd2001="#5B8DB8", cetin2004="#8C6BB1", tbdy2018="#5E8C4A",
    vs2000="#4E9A8A",
)

#: Soil kinds of the schematic, from the fines content and the plasticity
SOIL_KINDS = ["sand", "silty_sand", "silt", "clay"]

# Fill colours of the soil kinds in the borehole column (theme-dependent,
# since a light sandy tone reads poorly on a dark background).
SOIL_FILL = {
    "light": {"sand": "#E9D29B", "silty_sand": "#D8C08A", "silt": "#C2B8A0",
              "clay": "#A7B8A0"},
    "dark": {"sand": "#8A7250", "silty_sand": "#7A6A4E", "silt": "#6E6858",
             "clay": "#5E6E58"},
}
SOIL_FILL["paper"] = SOIL_FILL["light"]


def soil_kind(FC: float, PI: float) -> str:
    """The kind of soil drawn in the column: sand, silty sand, silt or clay."""
    if FC < 15.0:
        return "sand"
    if FC < 50.0:
        return "silty_sand"
    return "clay" if PI >= 7.0 else "silt"


def _example_cpt() -> list:
    """A CPT sounding beside the example borehole, every 0.2 m: a stiff crust,
    loose silty sand, a low-plasticity silt, a lean clay, then a sand that
    densifies with depth."""
    import math
    rows = []
    for i in range(2, 100):
        z = round(0.2 * i, 2)
        wiggle = 1.0 + 0.12 * math.sin(3.1 * z) + 0.06 * math.sin(7.7 * z)
        if z < 2.0:
            qc, rf = 3.5, 1.4
        elif z < 6.5:
            qc, rf = 3.6 + 0.35 * (z - 2.0), 1.1
        elif z < 9.5:
            qc, rf = 2.2, 2.4
        elif z < 12.5:
            qc, rf = 0.95 + 0.04 * (z - 9.5), 4.2
        else:
            qc, rf = 9.0 + 2.6 * (z - 12.5), 0.55
        qc *= wiggle
        u2 = 0.0 if z < 1.5 else 9.81 * (z - 1.5) * (3.0 if 6.5 <= z < 12.5 else 1.0)
        rows.append({"depth": z, "qc": round(qc, 2), "fs": round(qc * 1000.0 * rf / 100.0, 1),
                     "u2": round(u2, 1)})
    return rows


DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: Liquefaction assessment, BH-1",
        "analyst": "",
    },
    "earthquake": {
        "magnitude": 7.5,          # moment magnitude Mw
        "pga_source": "direct",    # direct | tbdy (PGA = 0.4·S_DS)
        "pga": 0.25,               # peak ground acceleration [g]
        "sds": 1.00,               # short-period design spectral acceleration S_DS [-]
    },
    "groundwater": {
        "depth": 1.5,              # during the earthquake, below the ground surface [m]
        "depth_test": 2.0,         # when the SPT was made [m]
        "gamma_water": 9.81,       # [kN/m³]
    },
    "spt_setup": {
        "energy": 60.0,            # energy ratio of the hammer ER [%]
        "borehole": 100.0,         # borehole diameter [mm]
        "stickup": 1.0,            # rod length above the ground surface [m]
        "rod_correction": True,    # the short-rod correction CR
        "no_liner": False,         # split-spoon sampler without liners (CS > 1)
    },
    # The ground around the borehole, for lateral spreading
    "ground": {
        "geometry": "slope",       # level | slope | free_face
        "slope": 1.0,              # ground slope S [%]
        "length": 40.0,            # distance to the free face L [m]
        "height": 5.0,             # height of the free face H [m]
    },
    # Layers from the ground surface down, with their index properties.
    # FC: fines content (passing No. 200, < 75 µm) [%]; clay: fraction finer
    # than 2 µm [%]; LL, PI, wn [%] (PI = 0: non-plastic); Vs [m/s] (0: not measured);
    # D50 [mm] (0: not known; ≥ 2 mm: gravelly); OCR and su [kPa] of the clay-like
    # layers (su = 0: from the OCR).
    "soil_profile": [
        {"name": "Fill (silty sand)", "thickness": 2.0, "gamma": 18.0, "gamma_sat": 19.0,
         "FC": 20.0, "clay": 4.0, "LL": 0.0, "PI": 0.0, "wn": 12.0, "Vs": 0.0,
         "D50": 0.25, "OCR": 1.0, "su": 0.0},
        {"name": "Loose silty sand (SM)", "thickness": 4.5, "gamma": 18.5, "gamma_sat": 19.5,
         "FC": 18.0, "clay": 3.0, "LL": 0.0, "PI": 0.0, "wn": 24.0, "Vs": 160.0,
         "D50": 0.18, "OCR": 1.0, "su": 0.0},
        {"name": "Low-plasticity silt (ML)", "thickness": 3.0, "gamma": 18.0,
         "gamma_sat": 19.0, "FC": 78.0, "clay": 8.0, "LL": 30.0, "PI": 8.0, "wn": 28.0,
         "Vs": 170.0, "D50": 0.04, "OCR": 1.0, "su": 0.0},
        {"name": "Lean clay (CL)", "thickness": 3.0, "gamma": 18.5, "gamma_sat": 19.0,
         "FC": 92.0, "clay": 32.0, "LL": 44.0, "PI": 23.0, "wn": 30.0, "Vs": 190.0,
         "D50": 0.005, "OCR": 1.2, "su": 0.0},
        {"name": "Medium dense sand (SP-SM)", "thickness": 7.5, "gamma": 19.0,
         "gamma_sat": 20.0, "FC": 8.0, "clay": 1.0, "LL": 0.0, "PI": 0.0, "wn": 20.0,
         "Vs": 240.0, "D50": 0.35, "OCR": 1.0, "su": 0.0},
    ],
    # SPT tests: depth [m] and the field blow count N. The index properties of a
    # test row are optional: an empty cell takes the value of the layer it lies in.
    "spt": [
        {"depth": 1.5, "N": 7, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 3.0, "N": 9, "FC": 16.0, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 4.5, "N": 8, "FC": 22.0, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 6.0, "N": 13, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 7.5, "N": 8, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 9.0, "N": 10, "FC": 70.0, "clay": 10.0, "LL": 33.0, "PI": 11.0,
         "wn": 29.0},
        {"depth": 10.5, "N": 11, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 12.0, "N": 13, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 13.5, "N": 20, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 15.0, "N": 26, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 16.5, "N": 31, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 18.0, "N": 35, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
        {"depth": 19.5, "N": 40, "FC": None, "clay": None, "LL": None, "PI": None, "wn": None},
    ],
    # CPT soundings: depth [m], cone resistance qc [MPa], sleeve friction fs [kPa]
    # and pore pressure behind the cone u2 [kPa] (0: not measured).
    "cpt": _example_cpt(),
    "options": {
        "test_type": "spt",        # spt | cpt
        "method": "ib2014",
        "method_cpt": "ib2014_cpt",
        "susceptibility": "bray_sancio",
        "fine_threshold": 35.0,    # FC [%] from which the fine-grained criteria apply
        "uncertain_susceptible": True,  # soils "to be tested" are taken as susceptible
        "settlement_depth": 20.0,  # depth down to which strains are summed [m]
        "cetin_pl": 15.0,          # probability of liquefaction of Cetin et al. [%]
        "vs12": 0.0,               # average Vs of the top 12 m for Cetin's rd [m/s] (0: estimate)
        "gravel_correction": True,  # reduce N in gravelly layers (JRA 1996, D50 ≥ 2 mm)
        "dry_settlement": True,    # add the seismic compression of dry sand (Pradel 1998)
        "softening": True,         # check clay-like soils for cyclic softening
        "area_ratio": 0.8,         # net area ratio of the cone a
        "cfc": 0.0,                # fitting parameter of FC from Ic (Idriss & Boulanger)
        "ic_limit": 2.6,           # Ic above which a CPT soil is clay-like
        "nkt": 14.0,               # cone factor for su = (qt − σv)/Nkt
    },
    "criteria": {
        "fs_required": 1.10,       # required factor of safety against liquefaction
        "s_allow": 100.0,          # allowable settlement [mm] (0: no check)
    },
}
