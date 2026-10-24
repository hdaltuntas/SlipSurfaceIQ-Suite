"""
The reinforcement drawing of the wall's section, and its DXF.

The drawing is described once, as a list of plain primitives — polylines,
circles and texts, each on a layer — in the wall's own coordinates (metres,
x from the toe, y up from the base). The same list is drawn by Matplotlib
for the screen and the report (`plotting`) and written out as an AutoCAD R12
DXF in millimetres (`to_dxf`), so what is on screen and what goes to the CAD
office are the same drawing.

What is drawn: the concrete outline (stem, footing, key), the ground in
front and the backfill line, every bar position with its shape, the bars
that run along the wall as dots, a label per position — number, diameter,
spacing and length — with a leader to its bar, the dimensions of the
section and the height where the curtailed bars stop, and a title block with
the materials and the covers.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from .i18n import TRANSLATIONS

#: DXF layers and their AutoCAD colour numbers
LAYERS = {"CONCRETE": 7, "REBAR": 1, "REBAR_DIST": 3, "DIMENSION": 8, "TEXT": 7,
          "GROUND": 30, "LEADER": 8}

#: Layer of each bar family
FAMILY_LAYER = {"stem": "REBAR", "footing": "REBAR", "key": "REBAR",
                "distribution": "REBAR_DIST"}

Point = Tuple[float, float]


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def bar_label(bar: Dict[str, Any]) -> str:
    """'(1) Ø16/150 L=6.25' for a transverse bar, '(3) Ø12/300' or '(9) 4Ø12' along it."""
    phi = bar["phi"]
    if bar["longitudinal"]:
        if bar["s"] > 0:
            return f"({bar['pos']}) Ø{phi}/{bar['s'] * 1000:.0f}"
        return f"({bar['pos']}) {len(bar['dots'])}Ø{phi}"
    return f"({bar['pos']}) Ø{phi}/{bar['s'] * 1000:.0f}  L={bar['length']:.2f}"


class _Sheet:
    """Collects primitives and keeps the extents."""

    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def poly(self, points, layer, closed=False, width=1.0, family=None):
        self.items.append({"type": "poly", "points": [tuple(map(float, p)) for p in points],
                           "layer": layer, "closed": closed, "width": width,
                           "family": family})

    def line(self, a, b, layer, width=0.6):
        self.poly([a, b], layer, width=width)

    def circle(self, c, r, layer, fill=True, family=None):
        self.items.append({"type": "circle", "center": (float(c[0]), float(c[1])),
                           "r": float(r), "layer": layer, "fill": fill, "family": family})

    def text(self, pos, text, height, layer="TEXT", align="left", valign="center",
             angle=0.0):
        self.items.append({"type": "text", "pos": (float(pos[0]), float(pos[1])),
                           "text": text, "height": float(height), "layer": layer,
                           "align": align, "valign": valign, "angle": float(angle)})

    def dim(self, p1: Point, p2: Point, offset: float, text: str, th: float,
            vertical: bool = False):
        """A dimension between two points, its line `offset` away from them."""
        if vertical:
            x = p1[0] + offset
            a, b = (x, p1[1]), (x, p2[1])
            self.line(p1, (x + math.copysign(th * 0.4, offset), p1[1]), "DIMENSION", 0.4)
            self.line(p2, (x + math.copysign(th * 0.4, offset), p2[1]), "DIMENSION", 0.4)
        else:
            y = p1[1] + offset
            a, b = (p1[0], y), (p2[0], y)
            self.line(p1, (p1[0], y + math.copysign(th * 0.4, offset)), "DIMENSION", 0.4)
            self.line(p2, (p2[0], y + math.copysign(th * 0.4, offset)), "DIMENSION", 0.4)
        self.line(a, b, "DIMENSION", 0.5)
        t = th * 0.35
        for p in (a, b):                    # architectural ticks
            self.line((p[0] - t, p[1] - t), (p[0] + t, p[1] + t), "DIMENSION", 0.8)
        mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        if vertical:
            self.text((mid[0] - th * 0.45, mid[1]), text, th * 0.85, "DIMENSION",
                      align="center", valign="bottom", angle=90.0)
        else:
            self.text((mid[0], mid[1] + th * 0.35), text, th * 0.85, "DIMENSION",
                      align="center", valign="bottom")

    def extent(self) -> Tuple[float, float, float, float]:
        xs, ys = [], []
        for it in self.items:
            if it["type"] == "poly":
                xs += [p[0] for p in it["points"]]
                ys += [p[1] for p in it["points"]]
            elif it["type"] == "circle":
                xs.append(it["center"][0])
                ys.append(it["center"][1])
            else:
                x, y = it["pos"]
                w = 0.55 * it["height"] * len(it["text"])
                if it["angle"]:
                    xs += [x, x - it["height"]]
                    ys += [y - w / 2, y + w / 2]
                else:
                    x0 = x - (w if it["align"] == "right" else w / 2 if it["align"] == "center"
                              else 0.0)
                    xs += [x0, x0 + w]
                    ys += [y - it["height"], y + it["height"]]
        return min(xs), max(xs), min(ys), max(ys)


def _spread(targets: List[float], gap: float) -> List[float]:
    """Label heights pushed apart so none is closer than `gap` to the next."""
    order = sorted(range(len(targets)), key=lambda i: targets[i])
    out = list(targets)
    for k in range(1, len(order)):
        i, j = order[k - 1], order[k]
        if out[j] < out[i] + gap:
            out[j] = out[i] + gap
    return out


def build(wall, lang: str = "en") -> Dict[str, Any]:
    """The drawing of a designed wall, as primitives."""
    L = _lang(lang)
    res = wall.results
    des = res["design"]
    g = wall.geo
    B, H = wall.B, g.H
    span = max(B, H + g.key_depth)
    th = 0.022 * span                        # text height
    sh = _Sheet()

    # ------------------------------------------------------------ concrete
    for name, poly in g.concrete_parts().items():
        sh.poly(poly, "CONCRETE", closed=True, width=1.4)
    # ------------------------------------------------------------ ground
    fg = g.front_ground
    ts = math.tan(math.radians(wall.toe_slope))
    left = -0.12 * span
    sh.poly([(left, fg - abs(left) * ts), (0.0, fg), (g.x_front(fg), fg)], "GROUND", width=0.8)
    right = B + 0.12 * span
    sh.poly([(g.x_back_top, H), (right, g.ground_back(right))], "GROUND", width=0.8)
    if wall.hw > 0:
        sh.line((g.x_back_base + 0.1, wall.hw), (right, wall.hw), "GROUND", 0.5)
        sh.text((right, wall.hw + th * 0.3), "▽", th, "GROUND", align="right",
                valign="bottom")

    # ------------------------------------------------------------ bars
    bars = des["bars"]
    for b in bars:
        layer = FAMILY_LAYER.get(b["family"], "REBAR")
        if b["shape"]:
            sh.poly(b["shape"], layer, width=1.6, family=b["family"])
        r = max(b["phi"] / 2000.0, 0.0035 * span)
        for d in b["dots"]:
            sh.circle(d, r, layer, family=b["family"])

    # ------------------------------------------------------------ labels
    gap = th * 2.1
    right_x = B + 0.06 * span
    left_x = -0.06 * span
    lab_right, lab_left, lab_bottom = [], [], []
    by_name = {b["name"]: b for b in bars}

    def anchor(b, share):
        pts = b["shape"]
        if not pts:
            d = b["dots"][int(len(b["dots"]) * share) % max(len(b["dots"]), 1)]
            return d
        seg = max(range(len(pts) - 1),
                  key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        a, c = pts[seg], pts[seg + 1]
        return (a[0] + share * (c[0] - a[0]), a[1] + share * (c[1] - a[1]))

    placing = {"stem_back_full": ("right", 0.80), "stem_back_cut": ("right", 0.55),
               "footing_top": ("right", 0.85), "stem_front": ("left", 0.75),
               "stem_horizontal": ("left", 0.30), "footing_bottom": ("bottom", 0.15),
               "footing_long": ("bottom", 0.40), "key": ("bottom", 0.5),
               "key_long": ("bottom", 0.0)}
    for name, (side, share) in placing.items():
        b = by_name.get(name)
        if b is None:
            continue
        p = anchor(b, share)
        (lab_right if side == "right" else lab_left if side == "left" else lab_bottom).append(
            (b, p))
    for group, x, align in ((lab_right, right_x, "left"), (lab_left, left_x, "right")):
        ys = _spread([p[1] for _, p in group], gap)
        for (b, p), y in zip(group, ys):
            sh.line(p, (x, y), "LEADER", 0.4)
            sh.circle(p, th * 0.18, "LEADER")
            sh.text((x + (th * 0.3 if align == "left" else -th * 0.3), y), bar_label(b), th,
                    align=align)
    # the labels under the footing: in the order of their bars, spread over the
    # width, on two staggered rows so that neighbours cannot overlap
    bottom = -g.key_depth - 0.10 * span
    lab_bottom.sort(key=lambda item: item[1][0])
    n = len(lab_bottom)
    for k, (b, p) in enumerate(lab_bottom):
        x = B * (k + 0.5) / max(n, 1)
        y = bottom - (k % 2) * gap
        sh.line(p, (x, y + th * 0.6), "LEADER", 0.4)
        sh.circle(p, th * 0.18, "LEADER")
        sh.text((x, y), bar_label(b), th, align="center", valign="top")

    # ------------------------------------------------------------ dimensions
    dim_left = left_x - 0.22 * span
    sh.dim((0.0, 0.0), (0.0, H), dim_left, f"H = {H:.2f}", th, vertical=True)
    sh.dim((0.0, 0.0), (0.0, g.t_f), dim_left * 0.55, f"{g.t_f:.2f}", th, vertical=True)
    y_dim = -g.key_depth - 0.05 * span - 3 * gap
    chain = [(0.0, g.toe), (g.toe, g.x_back_base), (g.x_back_base, B)]
    for a, c in chain:
        if c - a > 1e-6:
            sh.dim((a, 0.0), (c, 0.0), y_dim, f"{c - a:.2f}", th)
    sh.dim((0.0, 0.0), (B, 0.0), y_dim - 2.2 * th, f"B = {B:.2f}", th)
    sh.dim((g.x_front_top, H), (g.x_back_top, H), 0.06 * span, f"{g.t_top:.2f}", th)
    if g.key_on:
        sh.dim((g.key_x, -g.key_depth), (g.key_x + g.key_width, -g.key_depth),
               -0.04 * span, f"{g.key_width:.2f}", th)
    cut = des["curtailment"]
    if cut["enabled"]:
        x_c = g.x_back(cut["y_cut"]) + 0.04 * span
        sh.dim((x_c, g.t_f), (x_c, cut["y_cut"]), 0.0, f"{cut['y_cut'] - g.t_f:.2f}", th,
               vertical=True)

    # ------------------------------------------------------------ title block
    con = wall.concrete
    x0, x1, y0, _ = sh.extent()
    title_y = y0 - 1.5 * th
    sh.text((x0, title_y), L["drw_title"], th * 1.3, align="left", valign="top")
    sh.text((x0, title_y - 2.0 * th),
            L["drw_materials"].format(grade=con["grade"], steel=con["steel"],
                                      cs=con["cover_stem"], cf=con["cover_footing"]),
            th * 0.9, align="left", valign="top")
    q = des["quantities"]
    sh.text((x0, title_y - 3.6 * th),
            L["drw_quantities"].format(v=q["concrete"], s=q["steel"], r=q["ratio"]),
            th * 0.9, align="left", valign="top")
    return {"items": sh.items, "extent": sh.extent(), "text_height": th}


# --------------------------------------------------------------------------- #
#  DXF
# --------------------------------------------------------------------------- #

def _dxf_text(s: str) -> str:
    """AutoCAD's own code for the diameter sign; the rest in the code page."""
    return s.replace("Ø", "%%c").replace("▽", "v")


def to_dxf(drawing: Dict[str, Any]) -> bytes:
    """The drawing as an AutoCAD R12 DXF, in millimetres (ANSI 1254 code page)."""
    k = 1000.0
    out: List[str] = []

    def w(code, value):
        out.append(str(code))
        out.append(str(value))

    w(0, "SECTION")
    w(2, "HEADER")
    w(9, "$ACADVER")
    w(1, "AC1009")
    w(9, "$DWGCODEPAGE")
    w(3, "ANSI_1254")
    w(9, "$INSUNITS")
    w(70, 4)
    x0, x1, y0, y1 = drawing["extent"]
    w(9, "$EXTMIN")
    w(10, f"{x0 * k:.1f}")
    w(20, f"{y0 * k:.1f}")
    w(9, "$EXTMAX")
    w(10, f"{x1 * k:.1f}")
    w(20, f"{y1 * k:.1f}")
    w(0, "ENDSEC")

    w(0, "SECTION")
    w(2, "TABLES")
    w(0, "TABLE")
    w(2, "LTYPE")
    w(70, 1)
    w(0, "LTYPE")
    w(2, "CONTINUOUS")
    w(70, 0)
    w(3, "Solid line")
    w(72, 65)
    w(73, 0)
    w(40, "0.0")
    w(0, "ENDTAB")
    w(0, "TABLE")
    w(2, "LAYER")
    w(70, len(LAYERS))
    for name, color in LAYERS.items():
        w(0, "LAYER")
        w(2, name)
        w(70, 0)
        w(62, color)
        w(6, "CONTINUOUS")
    w(0, "ENDTAB")
    w(0, "ENDSEC")

    w(0, "SECTION")
    w(2, "ENTITIES")
    for it in drawing["items"]:
        if it["type"] == "poly":
            pts = it["points"]
            if len(pts) == 2 and not it["closed"]:
                w(0, "LINE")
                w(8, it["layer"])
                w(10, f"{pts[0][0] * k:.2f}")
                w(20, f"{pts[0][1] * k:.2f}")
                w(30, "0.0")
                w(11, f"{pts[1][0] * k:.2f}")
                w(21, f"{pts[1][1] * k:.2f}")
                w(31, "0.0")
                continue
            w(0, "POLYLINE")
            w(8, it["layer"])
            w(66, 1)
            w(10, "0.0")
            w(20, "0.0")
            w(30, "0.0")
            w(70, 1 if it["closed"] else 0)
            for p in pts:
                w(0, "VERTEX")
                w(8, it["layer"])
                w(10, f"{p[0] * k:.2f}")
                w(20, f"{p[1] * k:.2f}")
                w(30, "0.0")
            w(0, "SEQEND")
            w(8, it["layer"])
        elif it["type"] == "circle":
            w(0, "CIRCLE")
            w(8, it["layer"])
            w(10, f"{it['center'][0] * k:.2f}")
            w(20, f"{it['center'][1] * k:.2f}")
            w(30, "0.0")
            w(40, f"{it['r'] * k:.2f}")
        else:
            w(0, "TEXT")
            w(8, it["layer"])
            x, y = it["pos"]
            w(10, f"{x * k:.2f}")
            w(20, f"{y * k:.2f}")
            w(30, "0.0")
            w(40, f"{it['height'] * k:.2f}")
            w(1, _dxf_text(it["text"]))
            if it["angle"]:
                w(50, f"{it['angle']:.1f}")
            h = {"left": 0, "center": 1, "right": 2}[it["align"]]
            v = {"bottom": 1, "center": 2, "top": 3}[it["valign"]]
            if h or v:
                w(72, h)
                w(11, f"{x * k:.2f}")
                w(21, f"{y * k:.2f}")
                w(31, "0.0")
                w(73, v)
    w(0, "ENDSEC")
    w(0, "EOF")
    return ("\r\n".join(out) + "\r\n").encode("cp1254", errors="replace")
