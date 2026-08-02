"""Part-based Znome monster generator.

Creatures are assembled from anatomy rather than grown from noise:
a body, a head, a face (eyes + mouth), and mirrored appendages (ears,
horns, arms, legs, tails, wings). Every part is drawn onto a boolean
silhouette mask first; the mask is then rendered GB-style: white body,
bottom/side dither shading, solid black outline, face on top.

Each species picks its parts and proportions; the seed only jitters
sizes and placements slightly, so a species always reads the same.
"""

import math
import random

from canvas import BLACK, WHITE, Canvas, dither_at

SIZE = 32


class Build:
    """A silhouette mask plus face/detail draw ops applied after shading."""

    def __init__(self):
        self.mask = [[False] * SIZE for _ in range(SIZE)]
        self.details = []  # (x, y, value)

    def solid(self, x, y):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.mask[y][x] = True

    def ellipse(self, cx, cy, rx, ry):
        rx, ry = max(rx, 0.5), max(ry, 0.5)
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.solid(x, y)

    def mirror_ellipse(self, dx, cy, rx, ry):
        cx = SIZE / 2 - 0.5
        self.ellipse(cx - dx, cy, rx, ry)
        self.ellipse(cx + dx, cy, rx, ry)

    def rect_mask(self, x, y, w, h):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.solid(xx, yy)

    def tri(self, x0, y0, x1, y1, x2, y2):
        def edge(ax, ay, bx, by, px, py):
            return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

        lo_x, hi_x = int(min(x0, x1, x2)), int(max(x0, x1, x2))
        lo_y, hi_y = int(min(y0, y1, y2)), int(max(y0, y1, y2))
        for y in range(lo_y, hi_y + 1):
            for x in range(lo_x, hi_x + 1):
                b0 = edge(x0, y0, x1, y1, x, y)
                b1 = edge(x1, y1, x2, y2, x, y)
                b2 = edge(x2, y2, x0, y0, x, y)
                if (b0 >= 0 and b1 >= 0 and b2 >= 0) or \
                        (b0 <= 0 and b1 <= 0 and b2 <= 0):
                    self.solid(x, y)

    def mirror_tri(self, pts):
        cx = SIZE - 1
        (x0, y0), (x1, y1), (x2, y2) = pts
        self.tri(x0, y0, x1, y1, x2, y2)
        self.tri(cx - x0, y0, cx - x1, y1, cx - x2, y2)

    def limb(self, x0, y0, x1, y1, r):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            self.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, r)

    def mirror_limb(self, x0, y0, x1, y1, r):
        cx = SIZE - 1
        self.limb(x0, y0, x1, y1, r)
        self.limb(cx - x0, y0, cx - x1, y1, r)

    def detail(self, x, y, v):
        self.details.append((int(x), int(y), v))

    def filled(self, x, y):
        return 0 <= x < SIZE and 0 <= y < SIZE and self.mask[y][x]

    def render(self, shade="d25", belly=True, dark=False):
        c = Canvas(SIZE, SIZE)
        rows = [y for y in range(SIZE) if any(self.mask[y])]
        if not rows:
            return c
        top, bottom = rows[0], rows[-1]
        for y in range(SIZE):
            for x in range(SIZE):
                if not self.mask[y][x]:
                    continue
                depth = (y - top) / max(1, bottom - top)
                if dark:
                    level = 12 if depth < 0.35 else 16
                    if not self.filled(x, y - 1) or not self.filled(x - 1, y):
                        level = 8
                    c.set(x, y, dither_at(x, y, level))
                    continue
                level = 0
                if depth > 0.72:
                    level = 8
                elif depth > 0.5:
                    level = 4
                if belly and depth > 0.45 and depth < 0.85:
                    dist = abs(x - (SIZE / 2 - 0.5))
                    if dist < 5:
                        level = 0
                if depth > 0.6 and not self.filled(x, y + 1) and level < 8:
                    level = 8  # ground-contact shade
                if shade == "none":
                    level = 0
                c.set(x, y, dither_at(x, y, level) if level else WHITE)
        # outline
        for y in range(SIZE):
            for x in range(SIZE):
                if self.mask[y][x]:
                    continue
                if (self.filled(x + 1, y) or self.filled(x - 1, y)
                        or self.filled(x, y + 1) or self.filled(x, y - 1)):
                    c.set(x, y, BLACK)
        for x, y, v in self.details:
            c.set(x, y, v)
        return c


def eyes(b, y, off, style="dot", dark=False):
    cx = SIZE / 2 - 0.5
    fg = WHITE if dark else BLACK
    bg = BLACK if dark else WHITE
    for ex in (int(cx - off), int(cx + off)):
        if style == "dot":
            b.detail(ex, y, fg)
            b.detail(ex, y - 1, fg)
        elif style == "oval":
            for dy in (-1, 0, 1):
                b.detail(ex, y + dy, bg)
                b.detail(ex - 1, y + dy, bg)
            b.detail(ex, y, fg)
            b.detail(ex, y + 1, fg)
        elif style == "angry":
            b.detail(ex, y, fg)
            b.detail(ex, y - 1, fg)
            slant = 1 if ex < cx else -1
            b.detail(ex + slant, y - 2, fg)


def mouth(b, y, style="smile", dark=False):
    cx = int(SIZE / 2 - 0.5)
    fg = WHITE if dark else BLACK
    if style == "smile":
        b.detail(cx, y + 1, fg)
        b.detail(cx + 1, y + 1, fg)
        b.detail(cx - 1, y, fg)
        b.detail(cx + 2, y, fg)
    elif style == "fang":
        b.detail(cx - 2, y, fg)
        b.detail(cx + 3, y, fg)
        b.detail(cx - 2, y + 1, fg)
        b.detail(cx + 3, y + 1, fg)
        for dx in range(-1, 3):
            b.detail(cx + dx, y, fg)
    elif style == "beak":
        b.detail(cx, y, fg)
        b.detail(cx + 1, y, fg)
        b.detail(cx, y + 1, fg)
        b.detail(cx + 1, y + 1, fg)
        b.detail(cx, y + 2, fg)
    elif style == "flat":
        for dx in range(-1, 3):
            b.detail(cx + dx, y, fg)


CX = SIZE / 2 - 0.5


def _rubblin(rng, b):
    # round pebble hatchling: big head-body, stub feet, worried face
    r = 9 + rng.randrange(2)
    b.ellipse(CX, 16, r, r - 1)
    b.mirror_ellipse(5, 25, 3, 2)          # feet
    b.mirror_tri([(12, 8), (14, 4), (16, 8)])   # rock chips on crown
    eyes(b, 14, 4, "dot")
    mouth(b, 19, "flat")


def _cragnome(rng, b):
    # broad golem: slab torso, boulder shoulders, hanging arms, small head
    b.ellipse(CX, 9, 6, 5)                 # head
    b.rect_mask(13, 11, 6, 4)              # neck
    b.ellipse(CX, 20, 8, 6)                # torso
    b.mirror_ellipse(10, 15, 3, 3)         # shoulders
    b.mirror_limb(6, 17, 4, 25, 2)         # arms
    b.mirror_ellipse(5, 27, 3, 2)          # feet
    eyes(b, 8, 3, "angry")
    mouth(b, 11, "flat")


def _frostpod(rng, b):
    # ice seed: teardrop body with crystal crown spikes
    b.ellipse(CX, 18, 8, 9)
    b.mirror_tri([(11, 9), (12, 2), (15, 9)])
    b.tri(14, 8, 15.5, 1, 17, 8)
    eyes(b, 16, 4, "oval")
    mouth(b, 21, "smile")


def _cryonaut(rng, b):
    # tall crystalline wraith: hooded head, tapering robe, no feet
    b.ellipse(CX, 9, 6, 5)                 # hood
    b.tri(9, 10, 22, 10, 15.5, 28)         # robe taper
    b.mirror_tri([(10, 5), (12, 1), (14, 6)])   # crystal horns
    b.mirror_limb(9, 14, 6, 20, 1)         # trailing sleeves
    eyes(b, 9, 3, "oval")
    mouth(b, 12, "flat")


def _sparklet(rng, b):
    # plasma wisp: flame teardrop with flicker tip and tiny arms
    b.ellipse(CX, 18, 7, 8)
    b.tri(13, 12, 15.5, 3, 18, 12)         # flame tip
    b.tri(15, 8, 13, 5, 16, 6)
    b.mirror_limb(9, 18, 7, 21, 1)         # nub arms
    eyes(b, 17, 3, "dot")
    mouth(b, 20, "smile")


def _arcfang(rng, b):
    # static feline: eared head, crouched body, tail
    b.ellipse(CX, 11, 7, 5)                # head
    b.ellipse(CX, 21, 8, 6)                # body
    b.mirror_tri([(9, 8), (10, 2), (14, 7)])    # ears
    b.mirror_ellipse(6, 26, 2, 2)          # front paws
    b.limb(22, 22, 28, 15, 1)              # tail (unmirrored)
    eyes(b, 10, 4, "angry")
    mouth(b, 13, "fang")


def _tinplate(rng, b):
    # scrap robot: boxy torso, dome head, antenna, block feet
    for y in range(13, 26):
        for x in range(9, 23):
            b.solid(x, y)
    b.ellipse(CX, 10, 5, 4)                # dome head
    b.limb(15, 4, 15, 6, 0)                # antenna stem
    b.ellipse(15.5, 3, 1, 1)               # antenna bulb
    b.mirror_ellipse(4, 27, 3, 2)          # feet
    eyes(b, 9, 3, "oval")
    mouth(b, 12, "flat")


def _ferrox(rng, b):
    # plated quadruped: long body, wedge head, four legs, back spines
    b.ellipse(CX, 20, 11, 5)               # low wide body
    b.ellipse(CX, 11, 7, 5)                # armored head
    b.mirror_tri([(6, 8), (3, 3), (9, 6)])      # horn plates
    b.mirror_limb(7, 23, 7, 28, 2)         # outer legs
    b.mirror_limb(13, 24, 13, 29, 2)       # inner legs
    eyes(b, 10, 3, "angry")
    mouth(b, 13, "fang")


def _mycomite(rng, b):
    # spore walker: wide cap, stalk body, root feet
    b.ellipse(CX, 10, 10, 5)               # cap
    b.ellipse(CX, 19, 5, 7)                # stalk
    b.mirror_ellipse(4, 27, 3, 2)          # root feet
    b.detail(11, 7, BLACK)                 # cap spots
    b.detail(20, 8, BLACK)
    b.detail(15, 5, BLACK)
    eyes(b, 17, 3, "dot")
    mouth(b, 20, "smile")


def _bloomshade(rng, b):
    # void flower: petal crown, narrow waist, root legs
    b.ellipse(CX, 9, 7, 5)                 # bloom head
    b.mirror_tri([(7, 7), (5, 2), (11, 5)])     # side petals
    b.tri(13, 5, 15.5, 0, 18, 5)           # top petal
    b.tri(10, 13, 21, 13, 15.5, 23)        # tapered body
    b.mirror_limb(13, 21, 12, 27, 1)       # root legs
    eyes(b, 9, 3, "oval")
    mouth(b, 12, "flat")


def _nullet(rng, b):
    # void mote: small dark orb with wispy tips
    b.ellipse(CX, 17, 7, 7)
    b.mirror_tri([(10, 12), (8, 7), (13, 10)])  # wisp tips
    eyes(b, 16, 3, "dot", dark=True)
    mouth(b, 20, "flat", dark=True)


def _vantabeast(rng, b):
    # void apex: hulking torso, horned head, claw arms
    b.ellipse(CX, 12, 6, 5)                # head
    b.ellipse(CX, 21, 9, 7)                # torso
    b.mirror_tri([(9, 9), (6, 2), (12, 7)])     # horns
    b.mirror_limb(10, 18, 5, 26, 2)        # claw arms
    b.mirror_ellipse(4, 27, 2, 2)          # claw tips
    b.mirror_ellipse(4, 28, 3, 1)
    eyes(b, 11, 3, "angry", dark=True)
    mouth(b, 14, "fang", dark=True)


SPECIES = {
    "rubblin": (_rubblin, False),
    "cragnome": (_cragnome, False),
    "frostpod": (_frostpod, False),
    "cryonaut": (_cryonaut, False),
    "sparklet": (_sparklet, False),
    "arcfang": (_arcfang, False),
    "tinplate": (_tinplate, False),
    "ferrox": (_ferrox, False),
    "mycomite": (_mycomite, False),
    "bloomshade": (_bloomshade, False),
    "nullet": (_nullet, True),
    "vantabeast": (_vantabeast, True),
}


def generate(name, seed=0):
    fn, dark = SPECIES[name]
    rng = random.Random(seed)
    b = Build()
    fn(rng, b)
    return b.render(dark=dark)
