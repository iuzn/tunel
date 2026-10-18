"""Tunel: every glyph is a skeleton on a 1-dot grid, drawn with a 2-dot stroke by two rules and
nothing else:

1. Every skeleton dot becomes a 2 by 2 block, so every stroke is exactly 2 dots wide and every
   symmetry of the skeleton stays exact.
2. Where two skeleton dots touch only at a corner (a diagonal step), the two dots between the
   blocks are lit, so a diagonal or a rounded corner keeps its 2-dot weight instead of breaking
   into a staircase. This is the face's one corner and one diagonal.

So every lit dot lies inside a lit 2 by 2 square: there are no single dots sticking out.

The skeleton band is 11 rows; the face's band is 22: the row above the capitals lands on 0..3,
the capitals on 4..17, the descenders on 18..21.
"""
from pathlib import Path


HERE = Path(__file__).parent
BASE = 17


def stylise(dots):
    """Rule 1 and rule 2 on the skeleton dots; returns band cells (x, row)."""
    down = {(x, -yb) for x, yb in dots}   # rows counted downwards, so a step is (+1, +1)
    lit = set()
    for x, y in down:
        r = BASE - 1 + 2 * y
        lit |= {(2 * x + i, r + j) for i in (0, 1) for j in (0, 1)}
        if (x + 1, y + 1) in down and (x + 1, y) not in down and (x, y + 1) not in down:
            lit |= {(2 * x + 2, r + 1), (2 * x + 1, r + 2)}
        if (x - 1, y + 1) in down and (x - 1, y) not in down and (x, y + 1) not in down:
            lit |= {(2 * x - 1, r + 1), (2 * x, r + 2)}
    return lit


def skeletons():
    """skeletons.txt as {name: skeleton dots}."""
    out, cur = {}, None
    for line in (HERE / "skeletons.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("@ "):
            _, name, top = line.split(" ")
            cur = chr(int(name[2:], 16)) if name.startswith("U+") else name
            out[cur], row = set(), int(top)
        elif cur and line and line[0] in ".#":
            out[cur] |= {(x, 8 - row) for x, v in enumerate(line) if v == "#"}
            row += 1
        else:
            cur = None
    return out


def to_rows(lit, fixed=None):
    xs = [x for x, _ in lit]
    ys = [y for _, y in lit]
    x0, w = fixed or (min(xs), max(xs) - min(xs) + 1)
    top, bottom = min(ys), max(ys)
    return {"top": top, "rows": ["".join("#" if (x + x0, y) in lit else "." for x in range(w)) for y in range(top, bottom + 1)]}


def recipes(skip=()):
    """Every skeleton as {char: {"top", "rows"}}, cropped tight; figures keep one tabular width."""
    return {name: to_rows(stylise(dots), (0, 8) if name in "0123456789" else None)
            for name, dots in skeletons().items() if name not in skip}


def stray_dots(g):
    """Dots that lie in no lit 2 by 2 square: the check for dots sticking out."""
    lit = {(x, y) for y, row in enumerate(g["rows"]) for x, v in enumerate(row) if v == "#"}

    def held(x, y):
        return any(all((x + a + i, y + b + j) in lit for i in (0, 1) for j in (0, 1))
                   for a in (-1, 0) for b in (-1, 0))
    return [(x, y) for x, y in lit if not held(x, y)]
