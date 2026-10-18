"""Writes Tunel as a variable TrueType font.

Every lit cell of a glyph becomes one dot centred on the grid: pitch 100 units, 22 rows, the
baseline under row 17. Two axes change only the dot, never the grid, so an app can read the dot
centres at any setting:
  wght  100..900  dot diameter (thin dots to touching dots)
  ROND  0..100    dot shape (square to round)

Each dot is 12 points (an on, off, on triple per corner). Square: the triple meets at the
corner. Round: the on-curve points slide to the edge middles, the off-curve stays at the corner.

Then the static fonts, one per named weight at round dots, as TTF and OTF, and every font as
WOFF2 for the web:
  fonts/variable/   Tunel[ROND,wght].ttf and .woff2
  fonts/ttf/        Tunel-Thin.ttf .. Tunel-Black.ttf
  fonts/otf/        Tunel-Thin.otf .. Tunel-Black.otf
  fonts/web/        every font as .woff2, and tunel.css

Usage: .venv/bin/python font.py
"""
import json
import sys
from pathlib import Path

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import newTable
from fontTools.fontBuilder import FontBuilder
from array import array

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program
from fontTools import varLib
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.varLib import instancer

HERE = Path(__file__).parent
FAMILY = "Tünel"
PS_FAMILY = "Tunel"
VERSION = "1.000"
COPYRIGHT = "Copyright 2026 Ibrahim Uzun"
# The named weights, as every variable family ships them.
WEIGHTS = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium",
           600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}
PITCH, ROWS, BASE_ROW = 100, 22, 17
GAP_COLS, SPACE_COLS = 2, 4
RADIUS = {100: 15, 400: 38, 900: 50}   # dot radius per weight master, in font units


def dot_points(cx, cy, r, a):
    """One dot of radius r as 12 (point, on-curve) pairs. a = r gives a square, a = 0 a round dot."""
    pts = []
    for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1)):    # clockwise from the top right
        if sx == sy:
            first, last = (sx * a, sy * r), (sx * r, sy * a)
        else:
            first, last = (sx * r, sy * a), (sx * a, sy * r)
        pts += [(first, 1), ((sx * r, sy * r), 0), (last, 1)]
    return [((cx + x, cy + y), on) for (x, y), on in pts]


def make_glyph(dots):
    """A TrueType glyph built point by point, so every master keeps the same structure."""
    g = Glyph()
    coords, flags, ends = [], [], []
    for pts in dots:
        for xy, on in pts:
            coords.append(xy)
            flags.append(on)
        ends.append(len(coords) - 1)
    g.coordinates = GlyphCoordinates(coords)
    g.flags = array("B", flags)
    g.endPtsOfContours = ends
    g.numberOfContours = len(ends)
    g.program = Program()
    g.program.fromBytecode(b"")
    return g


def glyph_name(ch):
    return "space" if ch == " " else f"uni{ord(ch):04X}"


def master(glyphs, r, a):
    names = [".notdef", "space"] + [glyph_name(c) for c in glyphs]
    fb = FontBuilder(PITCH * ROWS, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({0x20: "space", 0xA0: "space", **{ord(c): glyph_name(c) for c in glyphs}})
    outlines, metrics = {}, {}
    empty = TTGlyphPen(None)
    outlines[".notdef"] = outlines["space"] = empty.glyph()
    metrics[".notdef"] = (PITCH * (SPACE_COLS + GAP_COLS), 0)
    metrics["space"] = (PITCH * (SPACE_COLS + GAP_COLS), 0)
    for ch, g in glyphs.items():
        dots = []
        width = len(g["rows"][0])
        for r_i, row in enumerate(g["rows"]):
            y = g["top"] + r_i
            for x, v in enumerate(row):
                if v == "#":
                    cx = (x + GAP_COLS // 2) * PITCH + PITCH // 2
                    cy = (BASE_ROW - y) * PITCH + PITCH // 2
                    dots.append(dot_points(cx, cy, r, a))
        outlines[glyph_name(ch)] = make_glyph(dots)
        metrics[glyph_name(ch)] = ((width + GAP_COLS) * PITCH, (GAP_COLS // 2) * PITCH)
    fb.setupGlyf(outlines)
    fb.setupHorizontalMetrics(metrics)
    asc, desc = (BASE_ROW + 1) * PITCH, (ROWS - BASE_ROW - 1) * PITCH
    fb.setupHorizontalHeader(ascent=asc, descent=-desc)
    fb.setupNameTable({
        "copyright": COPYRIGHT,
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{VERSION};NONE;{PS_FAMILY}-Regular",
        "fullName": f"{FAMILY} Regular",
        "version": f"Version {VERSION}",
        "psName": f"{PS_FAMILY}-Regular",
        "variationsPostScriptNamePrefix": PS_FAMILY,
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1.",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=-desc, sTypoLineGap=0, usWinAscent=asc,
                usWinDescent=desc, sxHeight=(BASE_ROW - 8 + 1) * PITCH, sCapHeight=(BASE_ROW - 4 + 1) * PITCH)
    fb.setupPost()
    fb.font["head"].fontRevision = float(VERSION)
    gasp = newTable("gasp")
    gasp.gaspRange = {0xFFFF: 0x000F}
    fb.font["gasp"] = gasp
    return fb.font


def build(out):
    glyphs = json.loads((HERE / "glyphs.json").read_text())["glyphs"]
    glyphs = {c: g for c, g in glyphs.items() if c not in (" ", " ")}
    doc = DesignSpaceDocument()
    for tag, name, lo, default, hi in (("wght", "Weight", 100, 400, 900), ("ROND", "Roundness", 0, 100, 100)):
        ax = AxisDescriptor()
        ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = tag, name, lo, default, hi
        doc.addAxis(ax)
    for w, r in RADIUS.items():
        for rond in (0, 100):
            src = SourceDescriptor()
            src.font = master(glyphs, r, r * (100 - rond) // 100)
            src.location = {"Weight": w, "Roundness": rond}
            src.name = f"w{w}r{rond}"
            doc.addSource(src)
    for w, style in WEIGHTS.items():
        inst = InstanceDescriptor()
        inst.familyName, inst.styleName = FAMILY, style
        inst.postScriptFontName = f"{PS_FAMILY}-{style}"
        inst.location = {"Weight": w, "Roundness": 100}
        doc.addInstance(inst)
    vf, _, _ = varLib.build(doc)
    buildStatTable(vf, [
        dict(tag="wght", name="Weight", values=[
            dict(value=w, name=n, **({"flags": 0x2, "linkedValue": 700} if w == 400 else {}))
            for w, n in WEIGHTS.items()]),
        dict(tag="ROND", name="Roundness", values=[
            dict(value=0, name="Square"), dict(value=100, name="Round", flags=0x2)]),
    ])
    vf.save(out)
    print(out, len(glyphs), "glyphs")


def to_otf(ttf):
    """The same font with CFF outlines: the quadratic dots redrawn as cubic curves."""
    order = ttf.getGlyphOrder()
    gs = ttf.getGlyphSet()
    charstrings = {}
    for name in order:
        pen = T2CharStringPen(gs[name].width, gs)
        gs[name].draw(pen)
        charstrings[name] = pen.getCharString()
    fb = FontBuilder(ttf["head"].unitsPerEm, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(ttf.getBestCmap())
    name = ttf["name"]
    fb.setupCFF(name.getDebugName(6), {"FullName": name.getDebugName(4), "FamilyName": name.getDebugName(1)},
                charstrings, {})
    fb.setupHorizontalMetrics({g: ttf["hmtx"][g] for g in order})
    hhea = ttf["hhea"]
    fb.setupHorizontalHeader(ascent=hhea.ascent, descent=hhea.descent)
    for tag in ("name", "OS/2", "gasp"):
        fb.font[tag] = ttf[tag]
    fb.setupPost()
    fb.font["head"].fontRevision = ttf["head"].fontRevision
    fb.font["head"].macStyle = ttf["head"].macStyle
    return fb.font


def web(path, out_dir):
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    f.flavor = "woff2"
    out = out_dir / (Path(path).stem + ".woff2")
    f.save(out)
    return out


def release():
    fonts = HERE / "fonts"
    dirs = {k: fonts / k for k in ("variable", "ttf", "otf", "web")}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    vf_path = dirs["variable"] / f"{PS_FAMILY}[ROND,wght].ttf"
    build(str(vf_path))
    from fontTools.ttLib import TTFont
    web(vf_path, dirs["variable"])
    web(vf_path, dirs["web"])
    css = [f"""@font-face {{
  font-family: "{FAMILY}";
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
  src: url("{vf_path.stem}.woff2") format("woff2");
}}
"""]
    for w, style in WEIGHTS.items():
        st = instancer.instantiateVariableFont(TTFont(vf_path), {"wght": w, "ROND": 100}, updateFontNames=True)
        ttf_path = dirs["ttf"] / f"{PS_FAMILY}-{style}.ttf"
        st.save(ttf_path)
        to_otf(TTFont(ttf_path)).save(dirs["otf"] / f"{PS_FAMILY}-{style}.otf")
        web(ttf_path, dirs["web"])
        css.append(f"""@font-face {{
  font-family: "{FAMILY} Static";
  font-style: normal;
  font-weight: {w};
  font-display: swap;
  src: url("{ttf_path.stem}.woff2") format("woff2");
}}
""")
    (dirs["web"] / "tunel.css").write_text("\n".join(css))


if __name__ == "__main__":
    release()
