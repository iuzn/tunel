"""Writes the Tunel sources and builds every font from them.

Every lit cell of a glyph becomes one dot centred on the grid: pitch 100 units, 22 rows, the
baseline under row 17. Two axes change only the dot, never the grid, so an app can read the dot
centres at any setting:
  wght  100..900  dot diameter (thin dots to touching dots), default 400
  ROND  0..100    dot shape (square to round), default 0 as the Google Fonts axis registry sets it

Each dot is 12 points (an on, off, on triple per corner). Square: the triple meets at the
corner. Round: the on-curve points slide to the edge middles, the off-curve stays at the corner.

Step 1 writes the sources, six UFO masters (wght 100, 400, 900 at ROND 0 and 100) and
sources/Tunel.designspace. Step 2 runs the Google Fonts builder on sources/config.yaml:
  fonts/variable/   Tunel[ROND,wght].ttf
  fonts/ttf/        Tunel-Thin.ttf .. Tunel-Black.ttf
  fonts/otf/        Tunel-Thin.otf .. Tunel-Black.otf
  fonts/web/        every font as .woff2, and tunel.css

Usage: python font.py            sources and fonts
       python font.py sources    sources only
The builder needs gftools (pip install gftools), which needs Python 3.10 or newer.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import ufoLib2
from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor

HERE = Path(__file__).parent
SOURCES = HERE / "sources"
FAMILY = "Tunel"
VERSION = (1, 100)
COPYRIGHT = "Copyright 2026 The Tunel Project Authors (https://github.com/iuzn/tunel)"
LICENSE = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
           "This license is available with a FAQ at: https://openfontlicense.org")
# The named weights, as every variable family ships them.
WEIGHTS = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium",
           600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}
PITCH, ROWS, BASE_ROW = 100, 22, 17
GAP_COLS, SPACE_COLS = 2, 4
RADIUS = {100: 15, 400: 38, 900: 50}   # dot radius per weight master, in font units
ASC, DESC = (BASE_ROW + 1) * PITCH, (ROWS - BASE_ROW - 1) * PITCH   # the grid: 1800 and 400
# Line spacing at 1.2 em, the extra space shared above and below the grid.
LINE_ASC, LINE_DESC = ASC + 240, DESC + 200
# .notdef: an open box of dots, capital height, 8 dots wide.
NOTDEF = ["########"] + ["#......#"] * 12 + ["########"]


def dot(pen, cx, cy, r, a):
    """One dot of radius r as 12 points. a = r gives a square, a = 0 a round dot.

    Drawn counter-clockwise, the UFO convention; the TrueType build reverses it to clockwise."""
    pts = []
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):    # counter-clockwise from the top right
        if sx == sy:
            first, last = (sx * r, sy * a), (sx * a, sy * r)
        else:
            first, last = (sx * a, sy * r), (sx * r, sy * a)
        pts += [(first, "line"), ((sx * r, sy * r), None), (last, "qcurve")]
    pen.beginPath()
    for (x, y), kind in pts:
        pen.addPoint((cx + x, cy + y), kind)
    pen.endPath()


def glyph_name(ch):
    return "space" if ch == " " else f"uni{ord(ch):04X}"


def draw(glyph, top, rows, r, a):
    pen = glyph.getPointPen()
    for r_i, row in enumerate(rows):
        for x, v in enumerate(row):
            if v == "#":
                cx = (x + GAP_COLS // 2) * PITCH + PITCH // 2
                cy = (BASE_ROW - top - r_i) * PITCH + PITCH // 2
                dot(pen, cx, cy, r, a)
    glyph.width = (len(rows[0]) + GAP_COLS) * PITCH


def style_name(weight, rond):
    """The square masters carry the weight name alone, since ROND 0 is the default."""
    return f"{WEIGHTS[weight]} Round" if rond else WEIGHTS[weight]


def master(glyphs, weight, rond):
    r = RADIUS[weight]
    a = r * (100 - rond) // 100
    font = ufoLib2.Font()
    info = font.info
    info.familyName = FAMILY
    info.styleName = style_name(weight, rond)
    info.versionMajor, info.versionMinor = VERSION
    info.copyright = COPYRIGHT
    info.openTypeNameLicense = LICENSE
    info.openTypeNameLicenseURL = "https://openfontlicense.org"
    info.openTypeNameDesigner = "Ibrahim Uzun"
    info.openTypeNameDesignerURL = "https://ibrahimuzun.com"
    info.openTypeNameManufacturer = "Ibrahim Uzun"
    info.openTypeNameManufacturerURL = "https://github.com/iuzn/tunel"
    info.unitsPerEm = PITCH * ROWS
    info.ascender, info.descender = ASC, -DESC
    info.capHeight = (BASE_ROW - 4 + 1) * PITCH
    info.xHeight = (BASE_ROW - 8 + 1) * PITCH
    info.openTypeHheaAscender, info.openTypeHheaDescender, info.openTypeHheaLineGap = LINE_ASC, -LINE_DESC, 0
    info.openTypeOS2TypoAscender, info.openTypeOS2TypoDescender, info.openTypeOS2TypoLineGap = LINE_ASC, -LINE_DESC, 0
    info.openTypeOS2WinAscent, info.openTypeOS2WinDescent = LINE_ASC, LINE_DESC
    info.openTypeOS2Selection = [7]      # USE_TYPO_METRICS
    info.openTypeOS2Type = []            # installable embedding, no restriction
    info.openTypeOS2WeightClass = weight
    info.openTypeGaspRangeRecords = [{"rangeMaxPPEM": 65535, "rangeGaspBehavior": [0, 1, 2, 3]}]
    order = [".notdef", "space"] + [glyph_name(c) for c in glyphs]
    font.glyphOrder = order
    notdef = font.newGlyph(".notdef")
    draw(notdef, 4, NOTDEF, r, a)
    space = font.newGlyph("space")
    space.unicodes = [0x20, 0xA0]
    space.width = PITCH * (SPACE_COLS + GAP_COLS)
    for ch, g in glyphs.items():
        glyph = font.newGlyph(glyph_name(ch))
        glyph.unicodes = [ord(ch)]
        draw(glyph, g["top"], g["rows"], r, a)
    return font


def sources():
    glyphs = json.loads((HERE / "glyphs.json").read_text())["glyphs"]
    glyphs = {c: g for c, g in glyphs.items() if c not in (" ", "\xa0")}
    SOURCES.mkdir(exist_ok=True)
    doc = DesignSpaceDocument()
    for tag, name, lo, default, hi in (("wght", "Weight", 100, 400, 900), ("ROND", "Roundness", 0, 0, 100)):
        ax = AxisDescriptor()
        ax.tag, ax.name, ax.minimum, ax.default, ax.maximum = tag, name, lo, default, hi
        doc.addAxis(ax)
    for w in RADIUS:
        for rond in (0, 100):
            name = f"{FAMILY}-{style_name(w, rond).replace(' ', '')}.ufo"
            path = SOURCES / name
            if path.exists():
                shutil.rmtree(path)   # regenerated output, rebuilt from glyphs.json every time
            master(glyphs, w, rond).save(path)
            src = SourceDescriptor()
            src.filename, src.familyName = name, FAMILY
            src.styleName = style_name(w, rond)
            src.location = {"Weight": w, "Roundness": rond}
            doc.addSource(src)
    for w, style in WEIGHTS.items():
        inst = InstanceDescriptor()
        inst.familyName, inst.styleName = FAMILY, style
        inst.filename = f"instances/{FAMILY}-{style}.ufo"
        inst.postScriptFontName = f"{FAMILY}-{style}"
        inst.location = {"Weight": w, "Roundness": 0}
        doc.addInstance(inst)
    doc.write(SOURCES / f"{FAMILY}.designspace")
    print(SOURCES / f"{FAMILY}.designspace", len(glyphs), "glyphs")


def css():
    web = HERE / "fonts" / "web"
    faces = ["""@font-face {
  font-family: "Tunel";
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
  src: url("Tunel[ROND,wght].woff2") format("woff2");
}
"""]
    for w, style in WEIGHTS.items():
        faces.append(f"""@font-face {{
  font-family: "Tunel Static";
  font-style: normal;
  font-weight: {w};
  font-display: swap;
  src: url("{FAMILY}-{style}.woff2") format("woff2");
}}
""")
    (web / "tunel.css").write_text("\n".join(faces))


def fonts():
    gftools = shutil.which("gftools") or str(Path(sys.executable).parent / "gftools")
    subprocess.run([gftools, "builder", "config.yaml"], cwd=SOURCES, check=True)
    # CFF fonts on Windows want Thin at 250 and ExtraLight at 275, or they bold the lightest two.
    from fontTools.ttLib import TTFont
    for style, cls in (("Thin", 250), ("ExtraLight", 275)):
        path = HERE / "fonts" / "otf" / f"{FAMILY}-{style}.otf"
        f = TTFont(path)
        f["OS/2"].usWeightClass = cls
        f.save(path)
    css()


if __name__ == "__main__":
    sources()
    if sys.argv[1:] != ["sources"]:
        fonts()
