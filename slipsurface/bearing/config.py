"""
Configuration for SlipSurface IQ Bearing: the default project, the choice lists, and
the theme and plot palette shared by the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `slipsurface.bearing.i18n`.
"""

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION", "DEFAULT_CONFIG", "THEMES", "PLOT_PALETTE",
           "SOIL_FILL", "METHOD_COLORS", "SHAPES", "METHODS", "UNDRAINED_METHODS",
           "ANALYSES", "SHEAR", "BEHAVIOURS", "LAYER_MODELS", "TWO_LAYER_MODELS",
           "APPROACHES", "TESTS", "PMT_CATEGORIES", "ROCK_METHODS", "ACCENT"]

# --- Choice lists (the first entry is the default where one is needed) -----
SHAPES = ["rectangle", "square", "strip", "circle"]

#: The bearing capacity factor sets, in the order the interface offers them.
#: `skempton` is an undrained method only and is left out of a drained run.
METHODS = ["terzaghi", "meyerhof", "hansen", "vesic", "ec7", "skempton"]
UNDRAINED_METHODS = ["skempton"]

ANALYSES = ["both", "drained", "undrained"]
SHEAR = ["general", "local"]
BEHAVIOURS = ["granular", "cohesive"]
LAYER_MODELS = ["average", "two_layer"]
TWO_LAYER_MODELS = ["punching", "spread"]

#: Verification: a global factor of safety, or an EN 1997-1 Design Approach
APPROACHES = ["fs", "da1", "da2", "da3"]

#: In-situ tests offering a bearing capacity of their own
TESTS = ["spt", "cpt", "pmt"]

#: Ménard pressuremeter soil categories (NF P 94-261 / Fascicule 62)
PMT_CATEGORIES = ["clay_a", "clay_b", "sand_a", "sand_b", "rock"]

ROCK_METHODS = ["hoek_brown", "ksp"]

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

# Semantic colours: the same quantity is the same colour in every figure. Warm
# and muted, to sit on the paper-coloured page; terracotta marks the capacity.
PLOT_PALETTE = dict(
    cohesion="#5B8DB8", surcharge="#8C6BB1", weight="#D9A55B",
    ultimate="#C6613F", allowable="#4E9A8A", applied="#B0413E", design="#5E8C4A",
    water="#6FA8C7", footing="#8A8680", wedge="#C9A876", spiral="#A26A12",
    Nc="#5B8DB8", Nq="#8C6BB1", Ngamma="#D9A55B",
    limit="#A26A12", seismic="#B0413E", insitu="#4E9A8A", rock="#6B6A64",
)

#: One colour per method, so a method keeps its colour in every figure.
METHOD_COLORS = {
    "terzaghi": "#5B8DB8", "meyerhof": "#8C6BB1", "hansen": "#D9A55B",
    "vesic": "#C6613F", "ec7": "#4E9A8A", "skempton": "#5E8C4A",
    "spt": "#73726C", "cpt": "#8A8680", "pmt": "#A26A12",
    "hoek_brown": "#6B6A64", "ksp": "#B7B4AA",
    "punching": "#B0413E", "spread": "#6FA8C7",
}

# Fill colours of the two soil behaviours in the schematic (theme-dependent,
# since a light sandy tone reads poorly on a dark background).
SOIL_FILL = {
    "light": {"granular": "#E3C98F", "cohesive": "#A7B8A0"},
    "dark": {"granular": "#8A7250", "cohesive": "#5E6E58"},
}
SOIL_FILL["paper"] = SOIL_FILL["light"]

DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: Footing on layered soil",
        "analyst": "",
    },
    "foundation": {
        "shape": "rectangle",
        "B": 2.50,                 # width, or diameter of a circle [m]
        "L": 4.00,                 # length of a rectangle [m]
        "Df": 1.50,                # depth of the foundation base [m]
        "base_tilt": 0.0,          # η, tilt of the base from the horizontal [°]
        "ground_slope": 0.0,       # β, slope of the ground in front of it [°]
    },
    # Characteristic actions at the centre of the base. A moment is turned into
    # an eccentricity, e = M / V, and the horizontal components into the load
    # inclination. `variable_fraction` is the share of every action that is a
    # variable action, which the Eurocode's partial factors need.
    "loading": {
        "V": 1700.0,               # vertical [kN]
        "Hb": 150.0,               # horizontal, parallel to B [kN]
        "Hl": 0.0,                 # horizontal, parallel to L [kN]
        "Mb": 300.0,               # moment giving an eccentricity along B [kNm]
        "Ml": 0.0,                 # moment giving an eccentricity along L [kNm]
        "variable_fraction": 0.30,
    },
    "groundwater": {
        "depth": 2.0,              # below ground surface [m]
        "gamma_water": 9.81,       # [kN/m³]
    },
    # Layers from the ground surface down. c and φ are the effective (drained)
    # strength, cu the undrained shear strength; E [MPa] and ν give the shear
    # modulus of Vesić's compressibility factors.
    "soil_profile": [
        {"name": "Fill", "thickness": 1.5, "behaviour": "granular", "gamma": 18.0,
         "gamma_sat": 19.5, "c": 0.0, "phi": 30.0, "cu": 0.0, "E": 15.0, "nu": 0.30},
        {"name": "Stiff clay", "thickness": 5.0, "behaviour": "cohesive", "gamma": 19.0,
         "gamma_sat": 19.5, "c": 5.0, "phi": 24.0, "cu": 90.0, "E": 25.0, "nu": 0.45},
        {"name": "Dense sand", "thickness": 8.0, "behaviour": "granular", "gamma": 19.5,
         "gamma_sat": 21.0, "c": 0.0, "phi": 38.0, "cu": 0.0, "E": 60.0, "nu": 0.30},
    ],
    "options": {
        "method": "vesic",
        "analysis": "both",        # drained, undrained, or whichever governs
        "shear": "general",        # general or local shear (Terzaghi's reduction)
        "shape_factors": True,
        "depth_factors": True,
        "inclination_factors": True,
        "base_factors": True,
        "ground_factors": True,
        "compressibility": False,  # Vesić's rigidity index factors
        "effective_area": True,    # Meyerhof's effective area for an eccentric load
        "layer_model": "average",  # average over the failure zone, or two-layer
        "zone_factor": 1.0,        # averaging depth = zone_factor · B below the base
        "two_layer_model": "punching",
        "Ks": 0.0,                 # punching shear coefficient (0: use 1 − sin φ₁)
        "adhesion_ratio": 1.0,     # ca / c₁ of the punching model
        "spread_angle": 26.57,     # load spread of the spread model [°] (2:1)
        "delta_ratio": 1.0,        # δ / φ' of the base, for sliding
    },
    "seismic": {
        "enabled": False,
        "kh": 0.10,                # horizontal seismic coefficient
        "kv": 0.0,                 # vertical seismic coefficient (+ downwards)
        "soil_inertia": True,      # Paolucci & Pecker's reduction of the γ-term
    },
    # A bearing capacity read from an in-situ test, shown beside the others.
    "insitu": {
        "enabled": False,
        "test": "spt",
        "N60": 20.0,               # SPT blow count, corrected to 60 % energy
        "qc": 8.0,                 # cone resistance [MPa]
        "pl": 0.80,                # Ménard limit pressure [MPa]
        "p0": 0.05,                # at-rest pressure at the test depth [MPa]
        "category": "sand_a",
        "settlement": 25.0,        # settlement the SPT / CPT rule allows [mm]
    },
    # Bearing capacity on rock, when the founding stratum is rock.
    "rock": {
        "enabled": False,
        "method": "hoek_brown",
        "sigma_ci": 50.0,          # uniaxial compressive strength of the intact rock [MPa]
        "GSI": 55.0,               # Geological Strength Index
        "mi": 10.0,                # Hoek–Brown constant of the intact rock
        "D": 0.0,                  # disturbance factor
        "gamma_rock": 25.0,        # unit weight of the rock mass [kN/m³]
        "spacing": 0.60,           # spacing of the discontinuities [m]
        "aperture": 2.0,           # aperture of the discontinuities [mm]
    },
    "criteria": {
        "approach": "fs",          # global factor of safety, or DA1 / DA2 / DA3
        "FS": 3.0,                 # required factor of safety on the net capacity
        "FS_sliding": 1.5,
        "ecc_limit": 6.0,          # allowable eccentricity, B / x (6: middle third)
    },
}
