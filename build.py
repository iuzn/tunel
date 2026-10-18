"""Resolves the LED face source into every glyph it encodes.

glyphs.txt holds the drawn glyphs and the accent marks. Accented letters are composites, as in
any professional font: the Unicode decomposition (NFD) of a character names its base letter and
its marks, and the mark is placed over or under the base. Output: glyphs.json, one entry per
encoded character with its top row, its rows, and how it was made.

Usage: python3 build.py [preview.png "line one" "line two" ...]
"""
import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
ROWS, GAP, SPACE = 22, 2, 4

MARKS = {
    "̀": "grave", "́": "acute", "̂": "circumflex", "̃": "tilde",
    "̄": "macron", "̆": "breve", "̇": "dot", "̈": "dieresis",
    "̊": "ring", "̋": "doubleacute", "̌": "caron", "̧": "cedilla",
    "̨": "ogonek",
}
BELOW = {"cedilla", "ogonek", "commabelow"}
# Latvian letters decompose with a cedilla but are drawn with a comma below.
COMMA_BELOW = set("ĢĶķĻļŅņŖŗ")
ALIASES = {"Đ": "Ð", " ": " ", "\xad": "-"}
PAIRS = {"Ĳ": "IJ", "ĳ": "ij", "ŉ": "’n"}
# Spacing forms of the marks, set at the x-height accent rows (cedilla stays below).
SPACING = {"¨": "dieresis", "¯": "macron", "´": "acute", "¸": "cedilla"}
# Vulgar fractions: superior numerator, the slash, a numerator-sized denominator on the baseline.
FRACTIONS = {"¼": ("¹", "frac.4"), "½": ("¹", "²"), "¾": ("³", "frac.4")}


def read_source():
    glyphs, cur = {}, None
    for line in (HERE / "glyphs.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("@ "):
            _, name, top = line.split(" ")
            if name.startswith("U+"):
                name = chr(int(name[2:], 16))
            cur = name
            glyphs[name] = {"top": int(top), "rows": []}
        elif cur and line and line[0] in ".#":
            glyphs[cur]["rows"].append(line)
        else:
            cur = None
    from parts import recipes
    glyphs.update(recipes(skip=set(glyphs)))   # a glyph drawn in glyphs.txt wins
    for name, g in glyphs.items():
        widths = {len(r) for r in g["rows"]}
        assert len(widths) == 1, f"{name!r}: ragged rows {widths}"
        assert g["top"] + len(g["rows"]) <= ROWS, f"{name!r}: below the band"
    return glyphs


def cells(g, dx=0):
    return {(dx + k, g["top"] + r) for r, row in enumerate(g["rows"]) for k, v in enumerate(row) if v == "#"}


def to_glyph(lit, width):
    ys = [y for _, y in lit]
    top, bottom = min(ys), max(ys)
    rows = ["".join("#" if (x, y) in lit else "." for x in range(width)) for y in range(top, bottom + 1)]
    return {"top": top, "rows": rows}


def compose(ch, src):
    if ch in SPACING:
        g = dict(src["mark." + SPACING[ch]])
        if SPACING[ch] != "cedilla":
            g["top"] = 4
        return to_glyph(cells(g), len(g["rows"][0])), [{"name": "mark." + SPACING[ch], "x": 0, "top": g["top"] - src["mark." + SPACING[ch]]["top"]}]
    if ch in FRACTIONS:
        num, den = (src[n] for n in FRACTIONS[ch])
        slash = src["/"]
        wn = len(num["rows"][0])
        xs, xd = wn - 1, wn + 4
        den = {"top": 8, "rows": den["rows"]}
        lit = cells(num) | cells(slash, xs) | cells(den, xd)
        parts = [{"name": FRACTIONS[ch][0], "x": 0, "top": 0}, {"name": "/", "x": xs, "top": 0},
                 {"name": FRACTIONS[ch][1], "x": xd, "top": 8 - src[FRACTIONS[ch][1]]["top"]}]
        return to_glyph(lit, xd + len(den["rows"][0])), parts
    if ch in PAIRS:
        a, b = (src[c] for c in PAIRS[ch])
        wa = len(a["rows"][0])
        lit = cells(a) | cells(b, wa + GAP)
        parts = [{"name": PAIRS[ch][0], "x": 0, "top": 0}, {"name": PAIRS[ch][1], "x": wa + GAP, "top": 0}]
        return to_glyph(lit, wa + GAP + len(b["rows"][0])), parts
    nfd = unicodedata.normalize("NFD", ch)
    base, marks = nfd[0], [MARKS.get(m) for m in nfd[1:]]
    if not marks or None in marks or base not in src:
        return None, None
    if ch in COMMA_BELOW:
        marks = ["commabelow" if m == "cedilla" else m for m in marks]
    above = [m for m in marks if m not in BELOW]
    if above and base in "ij":
        base = {"i": "ı", "j": "ȷ"}[base]
    b = src[base]
    bw = len(b["rows"][0])
    placed = []
    for m in marks:
        g = dict(src["mark." + m])
        mw = len(g["rows"][0])
        if m in BELOW:
            x = bw - mw if m == "ogonek" else (bw - mw) // 2
        else:
            x = (bw - mw) // 2
            # Over a capital or an ascender the mark ends on row 2, one row over the cap line;
            # over an x-height letter it starts on row 4, on the row of the dot of the i.
            g["top"] = 3 - len(g["rows"]) if (base.isupper() or b["top"] < 8) else 4
        placed.append(("mark." + m, g, x))
    left = min([0] + [x for _, _, x in placed])
    lit = cells(b, -left)
    parts = [{"name": base, "x": -left, "top": 0}]
    for name, g, x in placed:
        lit |= cells(g, x - left)
        parts.append({"name": name, "x": x - left, "top": g["top"] - src[name]["top"]})
    width = max([bw - left] + [x - left + len(g["rows"][0]) for _, g, x in placed])
    return to_glyph(lit, width), parts


def targets():
    chars = [chr(c) for c in range(0x21, 0x7F)]
    chars += [chr(c) for c in range(0xA0, 0x100)]
    chars += [chr(c) for c in range(0x100, 0x180)]
    return chars


def build():
    src = read_source()
    out, missing = {}, []
    wanted = targets()
    for ch in wanted + [n for n in src if len(n) == 1 and n not in wanted]:
        if ch in src:
            out[ch] = {**src[ch], "made": "drawn"}
        elif ch in ALIASES:
            if ALIASES[ch] in src:
                out[ch] = {**src[ALIASES[ch]], "made": "alias:" + ALIASES[ch]}
        else:
            g, parts = compose(ch, src)
            if g:
                out[ch] = {**g, "made": "composite", "parts": parts}
            else:
                missing.append(ch)
    marks = {n: g for n, g in src.items() if n.startswith("mark.")}
    (HERE / "glyphs.json").write_text(json.dumps({"glyphs": out, "marks": marks}, ensure_ascii=False, indent=1))
    return out, missing


def preview(out, path, lines):
    from PIL import Image, ImageDraw
    P = 8
    def width(t): return sum((len(out[c]["rows"][0]) if c in out else SPACE) + GAP for c in t)
    W = max(width(t) for t in lines) + 4
    img = Image.new("RGB", (W * P, ((ROWS + 2) * len(lines) + 1) * P), (8, 8, 8))
    d = ImageDraw.Draw(img)
    for li, t in enumerate(lines):
        y0, x, lit = li * (ROWS + 2) + 1, 2, set()
        for c in t:
            if c not in out:
                x += SPACE + GAP
                continue
            lit |= cells(out[c], x)
            x += len(out[c]["rows"][0]) + GAP
        for cx in range(W):
            for cy in range(ROWS):
                col = (255, 170, 40) if (cx, cy) in lit else (40, 28, 10)
                d.ellipse([cx * P + 1, (y0 + cy) * P + 1, cx * P + P - 1, (y0 + cy) * P + P - 1], fill=col)
    img.save(path)


if __name__ == "__main__":
    out, missing = build()
    print(len(out), "glyphs; missing:", "".join(missing) or "none")
    if len(sys.argv) > 2:
        preview(out, sys.argv[1], sys.argv[2:])
