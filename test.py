"""Checks every glyph of glyphs.json against the face's rules. Run after build.py.

  stray      every lit dot lies in a lit 2 by 2 square (no dot sticks out)
  blob       no lit 3 by 3 square (a stroke is 2 dots, never a lump)
  mirror     letters that are symmetric are exactly symmetric
  turn       N S Z s z are the same turned 180 degrees
  parts      shared parts are identical: d is b mirrored, q is p mirrored, u is n turned,
             W is M upside down, 9 is 6 turned, R and P share the bowl, h is n with a stem
  lines      capitals and figures sit on the cap line and baseline, lowercase on the x-height,
             ascenders and descenders reach their lines
  coverage   every character build.py targets exists

What it cannot judge is taste: whether a diagonal starts where the eye expects. specimen.png
is for that.

Usage: python test.py   (exit code 1 when a check fails)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
CAP, XH, BASE, DESC = 4, 8, 17, 21
RING = set("ÅåŮů˚\u030a")   # the ring is the one mark drawn with a 1-dot stroke
# Where a solid block is the form itself (a filled dot, a crossing, the N's corner), not a lump.
SOLID = set("%&N®°¶º¼¾Ñ×đŃŅŇŊ˚\u030a•™")


def cells(g):
    return {(x, g["top"] + y) for y, row in enumerate(g["rows"]) for x, v in enumerate(row) if v == "#"}


def squares(lit, n):
    """Top-left corners of lit n by n squares."""
    return {(x, y) for x, y in lit if all((x + i, y + j) in lit for i in range(n) for j in range(n))}


def stray(g):
    lit = cells(g)
    held = set()
    for x, y in squares(lit, 2):
        held |= {(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)}
    return lit - held


def flip(rows):
    return [r[::-1] for r in rows]


def main():
    data = json.loads((HERE / "glyphs.json").read_text())
    g = data["glyphs"]
    fails = {}

    def check(name, bad):
        fails[name] = bad
        print(f"{'ok  ' if not bad else 'FAIL'} {name}: {', '.join(bad) if bad else 'all pass'}")

    check("stray", [c for c, v in g.items() if c not in RING and stray(v)])
    check("blob", [c for c, v in g.items() if c not in SOLID and squares(cells(v), 3)])
    check("mirror", [c for c in "AHIMOTUVWXYovwx08" if flip(g[c]["rows"]) != g[c]["rows"]])
    check("turn", [c for c in "NSZsz" if flip(g[c]["rows"][::-1]) != g[c]["rows"]])

    def same(a, b):
        return a == b
    parts = {
        "d = b mirrored": same(g["d"]["rows"], flip(g["b"]["rows"])),
        "q = p mirrored": same(g["q"]["rows"], flip(g["p"]["rows"])),
        "u = n turned": same(g["u"]["rows"], flip(g["n"]["rows"][::-1])),
        "W = M upside down": same(g["W"]["rows"], g["M"]["rows"][::-1]),
        "9 = 6 turned": same(g["9"]["rows"], flip(g["6"]["rows"][::-1])),
        "R bowl = P bowl": same(g["R"]["rows"][:8], g["P"]["rows"][:8]),
        "h = n with a stem": same(g["h"]["rows"][4:], g["n"]["rows"]),
        "b bowl = p bowl": same(g["b"]["rows"][4:], g["p"]["rows"][:10]),
    }
    check("parts", [k for k, ok in parts.items() if not ok])

    def span(c):
        ys = [y for _, y in cells(g[c])]
        return min(ys), max(ys)
    bad = []
    for c in "ABCDEFGHIJKLMNOPRSTUVWXYZ0123456789":
        if span(c) != (CAP, BASE):
            bad.append(f"{c} {span(c)}")
    for c in "acemnorsuvwxz":
        if span(c) != (XH, BASE):
            bad.append(f"{c} {span(c)}")
    for c in "bdhkl":
        if span(c) != (CAP, BASE):
            bad.append(f"{c} {span(c)}")
    for c in "gpqy":
        if span(c)[1] != DESC:
            bad.append(f"{c} {span(c)}")
    check("lines", bad)

    sys.path.insert(0, str(HERE))
    from build import targets, ALIASES
    check("coverage", [c for c in targets() if c not in g and c not in ALIASES and not c.isspace()])
    return 1 if any(fails.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
