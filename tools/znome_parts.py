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

SIZE = 56

# Species are authored on a 32x32 design grid and scaled up at draw
# time, so part recipes stay small while sprites render at GB battle
# size (56x56, like the classic Game Boy monster games).
DESIGN = 32
S = SIZE / DESIGN


class Build:
    """A silhouette mask plus face/detail draw ops applied after shading."""

    def __init__(self):
        self.mask = [[False] * SIZE for _ in range(SIZE)]
        self.details = []  # (x, y, value)

    def solid(self, x, y):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.mask[y][x] = True

    def ellipse(self, cx, cy, rx, ry):
        cx, cy, rx, ry = cx * S, cy * S, rx * S, ry * S
        rx, ry = max(rx, 0.5), max(ry, 0.5)
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.solid(x, y)

    def mirror_ellipse(self, dx, cy, rx, ry):
        cx = DESIGN / 2 - 0.5
        self.ellipse(cx - dx, cy, rx, ry)
        self.ellipse(cx + dx, cy, rx, ry)

    def rect_mask(self, x, y, w, h):
        for yy in range(int(y * S), int((y + h) * S)):
            for xx in range(int(x * S), int((x + w) * S)):
                self.solid(xx, yy)

    def vline_mask(self, x, y0, y1):
        for y in range(int(y0 * S), int((y1 + 1) * S)):
            for xx in range(int(x * S), int(x * S) + 3):
                self.solid(xx, y)

    def tri(self, x0, y0, x1, y1, x2, y2):
        x0, y0, x1, y1 = x0 * S, y0 * S, x1 * S, y1 * S
        x2, y2 = x2 * S, y2 * S
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
        cx = DESIGN - 1
        (x0, y0), (x1, y1), (x2, y2) = pts
        self.tri(x0, y0, x1, y1, x2, y2)
        self.tri(cx - x0, y0, cx - x1, y1, cx - x2, y2)

    def limb(self, x0, y0, x1, y1, r):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            self.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, r)

    def mirror_limb(self, x0, y0, x1, y1, r):
        cx = DESIGN - 1
        self.limb(x0, y0, x1, y1, r)
        self.limb(cx - x0, y0, cx - x1, y1, r)

    def detail(self, x, y, v):
        px, py = int(x * S), int(y * S)
        for dy in (0, 1):
            for dx in (0, 1):
                self.details.append((px + dx, py + dy, v))

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
                if depth > 0.75:
                    level = 4
                if belly and depth > 0.45 and depth < 0.8:
                    dist = abs(x - (SIZE / 2 - 0.5))
                    if dist < 5 * S:
                        level = 0
                if depth > 0.8 and not self.filled(x, y + 1) and level < 8:
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
    cx = DESIGN / 2 - 0.5
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
        elif style == "block":
            for dy in (0, 1):
                b.detail(ex, y + dy, fg)
                b.detail(ex + (1 if ex < cx else -1), y + dy, fg)


def mouth(b, y, style="smile", dark=False):
    cx = int(DESIGN / 2 - 0.5)
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


CX = DESIGN / 2 - 0.5


# --- base forms: small, round, cute (about 2/3 of the cell)

def _rubblin(rng, b):
    # pebble hatchling: round body, stub feet, chipped crown
    b.ellipse(CX, 19, 7, 7)
    b.mirror_ellipse(4, 26, 2, 2)          # feet
    b.mirror_tri([(13, 13), (14, 9), (16, 13)])  # rock chips
    b.detail(10, 18, BLACK)                # shell crack
    b.detail(11, 19, BLACK)
    b.detail(21, 16, BLACK)
    eyes(b, 17, 3, "dot")
    mouth(b, 21, "flat")


def _frostpod(rng, b):
    # ice seed: small teardrop with a crystal sprout
    b.ellipse(CX, 20, 6, 7)
    b.mirror_tri([(13, 14), (14, 8), (16, 14)])  # sprout
    b.tri(15, 12, 15.5, 6, 17, 12)
    eyes(b, 18, 3, "oval")
    mouth(b, 22, "smile")


def _sparklet(rng, b):
    # plasma wisp: flame teardrop, flicker tip, nub arms
    b.ellipse(CX, 20, 6, 7)
    b.tri(13, 15, 15.5, 6, 18, 15)         # flame tip
    b.mirror_limb(8, 20, 6, 23, 1)         # nub arms
    eyes(b, 19, 3, "dot")
    mouth(b, 22, "smile")


def _tinplate(rng, b):
    # scrap bot: little box with a dome head and antenna
    b.rect_mask(11, 15, 10, 10)            # box body
    b.ellipse(CX, 12, 4, 4)                # dome head
    b.vline_mask(15, 6, 9)                 # antenna
    b.ellipse(15.5, 5, 1, 1)
    b.mirror_ellipse(3, 26, 2, 1)          # feet
    b.detail(12, 20, BLACK)                # rivets
    b.detail(19, 20, BLACK)
    eyes(b, 11, 2, "oval")
    mouth(b, 14, "flat")


def _mycomite(rng, b):
    # spore pup: wide cap over a stubby stalk
    b.ellipse(CX, 14, 8, 4)                # cap
    b.ellipse(CX, 21, 4, 6)                # stalk
    b.mirror_ellipse(3, 27, 2, 1)          # feet
    b.detail(12, 12, BLACK)                # cap spots
    b.detail(19, 13, BLACK)
    b.detail(15, 11, BLACK)
    eyes(b, 20, 2, "dot")
    mouth(b, 23, "smile")


def _nullet(rng, b):
    # void mote: dark orb, wispy tips
    b.ellipse(CX, 19, 6, 6)
    b.mirror_tri([(11, 15), (9, 10), (14, 13)])  # wisps
    eyes(b, 18, 3, "dot", dark=True)
    mouth(b, 22, "flat", dark=True)


# --- evolved forms: tall, humanoid stance, more detail

def _cragnome(rng, b):
    # rock golem: head, broad shoulders, fists, legs apart
    b.ellipse(CX, 6, 6, 5)                 # head
    b.rect_mask(13, 9, 6, 3)               # neck
    b.rect_mask(8, 11, 16, 9)              # slab torso
    b.mirror_ellipse(9, 12, 3, 3)          # shoulder boulders
    b.mirror_limb(6, 14, 4, 22, 2)         # arms
    b.mirror_ellipse(11, 24, 2, 2)         # fists
    b.mirror_limb(12, 20, 12, 28, 2)       # legs
    b.mirror_ellipse(4, 29, 3, 1)          # feet
    b.detail(12, 14, BLACK)                # chest cracks
    b.detail(13, 15, BLACK)
    b.detail(19, 17, BLACK)
    eyes(b, 5, 3, "block")
    mouth(b, 8, "flat")


def _cryonaut(rng, b):
    # crystalline wraith: horned hood, robed body, sleeve arms
    b.ellipse(CX, 7, 6, 5)                 # hood
    b.mirror_tri([(10, 3), (12, 0), (14, 4)])   # crystal horns
    b.tri(8, 11, 23, 11, 15.5, 29)         # robe
    b.mirror_limb(12, 13, 7, 21, 1)        # arms
    b.mirror_tri([(7, 20), (4, 25), (9, 23)])   # shard hands
    b.detail(15, 20, BLACK)                # robe seam
    b.detail(15, 22, BLACK)
    b.detail(15, 24, BLACK)
    eyes(b, 7, 3, "oval")
    mouth(b, 10, "flat")


def _arcfang(rng, b):
    # storm feline biped: eared head, slim torso, claws, tail
    b.ellipse(CX, 7, 6, 5)                 # head
    b.mirror_tri([(10, 4), (11, 0), (15, 4)])   # ears
    b.rect_mask(13, 11, 6, 4)              # neck
    b.ellipse(CX, 19, 5, 6)                # slim torso
    b.mirror_limb(9, 15, 7, 21, 1)         # arms
    b.mirror_limb(12, 22, 12, 27, 2)       # digitigrade legs
    b.mirror_ellipse(4, 28, 3, 1)          # paws
    b.limb(20, 22, 27, 14, 1)              # tail
    b.tri(26, 11, 29, 15, 25, 15)          # tail bolt tip
    eyes(b, 7, 3, "angry")
    mouth(b, 10, "fang")


def _ferrox(rng, b):
    # plated juggernaut: horned helm, armored torso, gauntlets
    b.ellipse(CX, 6, 6, 5)                 # helm
    b.mirror_tri([(8, 4), (5, 0), (11, 3)])     # helm horns
    b.rect_mask(10, 10, 12, 9)             # armored torso
    b.mirror_ellipse(9, 11, 2, 2)          # pauldrons
    b.mirror_limb(6, 13, 5, 21, 2)         # arms
    b.mirror_ellipse(10, 23, 3, 2)         # gauntlets
    b.mirror_limb(12, 20, 12, 28, 2)       # legs
    b.mirror_ellipse(4, 29, 3, 1)          # sabatons
    b.detail(15, 12, BLACK)                # chest plate seams
    b.detail(16, 12, BLACK)
    b.detail(13, 16, BLACK)
    b.detail(18, 16, BLACK)
    eyes(b, 6, 3, "block")
    mouth(b, 9, "flat")


def _bloomshade(rng, b):
    # dusk bloom: petal-crowned head, slim body, vine arms, leaf skirt
    b.ellipse(CX, 8, 6, 5)                 # head
    b.mirror_tri([(8, 6), (4, 1), (11, 4)])     # side petals
    b.tri(13, 4, 15.5, 0, 18, 4)           # top petal
    b.ellipse(CX, 17, 4, 6)                # slim body
    b.mirror_limb(13, 14, 7, 21, 1)        # vine arms
    b.tri(10, 21, 21, 21, 15.5, 29)        # leaf skirt
    eyes(b, 7, 3, "oval")
    mouth(b, 10, "flat")


def _vantabeast(rng, b):
    # void apex: horned head, hulking shoulders, claw arms, stance
    b.ellipse(CX, 8, 5, 4)                 # head
    b.mirror_tri([(9, 6), (5, 0), (12, 4)])     # long horns
    b.rect_mask(10, 11, 12, 8)             # torso
    b.mirror_ellipse(8, 12, 3, 3)          # shoulders
    b.mirror_limb(6, 15, 3, 23, 2)         # arms
    b.mirror_tri([(3, 23), (1, 27), (5, 25)])   # claws
    b.mirror_limb(12, 20, 12, 28, 2)       # legs
    b.mirror_ellipse(4, 29, 3, 1)          # feet
    eyes(b, 7, 3, "block", dark=True)
    mouth(b, 10, "fang", dark=True)


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
