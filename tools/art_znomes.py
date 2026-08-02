"""32x32 1-bit battle sprites for the twelve Znomes.

Sprites are composed from parametric shapes so silhouettes stay symmetric
and the shading style is consistent: white body, ordered-dither shadow away
from the top-left light, 1px black outline, black features on top.
"""


from canvas import BLACK, CLEAR, WHITE, Canvas, dither_at

SIZE = 32


class Shape:
    """Boolean coverage mask with helpers for building creature bodies."""

    def __init__(self, size=SIZE):
        self.size = size
        self.m = [[False] * size for _ in range(size)]

    def _set(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.m[y][x] = True

    def ellipse(self, cx, cy, rx, ry):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                dx = (x - cx) / max(rx, 0.5)
                dy = (y - cy) / max(ry, 0.5)
                if dx * dx + dy * dy <= 1.0:
                    self._set(x, y)
        return self

    def box(self, x0, y0, w, h):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self._set(x, y)
        return self

    def tri(self, x0, y0, w, h, up=True):
        """Isoceles triangle, apex up or down, anchored at (x0, y0)."""
        for i in range(h):
            t = i / max(h - 1, 1)
            half = max(1, int(round((w / 2) * (1 - t))))
            cx = x0 + w // 2
            y = y0 + i if up else y0 + h - 1 - i
            for x in range(cx - half, cx + half + 1):
                self._set(x, y)
        return self

    def taper(self, x0, y0, x1, y1, r0, r1):
        """Thick line whose radius blends from r0 to r1 (tails, limbs)."""
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            cx = x0 + (x1 - x0) * t
            cy = y0 + (y1 - y0) * t
            r = r0 + (r1 - r0) * t
            self.ellipse(cx, cy, r, r)
        return self

    def mirror(self):
        """Mirror the left half onto the right half (odd-width friendly)."""
        for y in range(self.size):
            for x in range(self.size // 2):
                if self.m[y][x]:
                    self.m[y][self.size - 1 - x] = True
        return self

    def covered(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size and self.m[y][x]




def render(shape, shade=0.55, light=(9, 7)):
    """Turn a mask into a shaded, outlined 1-bit canvas.

    Shading is a soft band hugging the silhouette edge on the side facing
    away from the light, which is how Game Boy era 1-bit sprites read best.
    """
    c = Canvas(shape.size, shape.size)
    near = max(2, int(round(3 * shade)))
    far = near + 2
    for y in range(shape.size):
        for x in range(shape.size):
            if not shape.covered(x, y):
                continue
            if not shape.covered(x + near, y + near):
                level = 8
            elif not shape.covered(x + far, y + far):
                level = 4
            else:
                level = 0
            c.px[y][x] = dither_at(x, y, level)
    # 1px black outline around the silhouette.
    edge = []
    for y in range(shape.size):
        for x in range(shape.size):
            if not shape.covered(x, y):
                continue
            if not (
                shape.covered(x - 1, y)
                and shape.covered(x + 1, y)
                and shape.covered(x, y - 1)
                and shape.covered(x, y + 1)
            ):
                edge.append((x, y))
    for x, y in edge:
        c.px[y][x] = BLACK
    return c


def eyes(c, cx, cy, spread, r=2, glint=True):
    for sx in (-1, 1):
        ex = cx + sx * spread
        for y in range(cy - r, cy + r + 1):
            for x in range(ex - r, ex + r + 1):
                if (x - ex) ** 2 + (y - cy) ** 2 <= r * r and c.get(x, y) != CLEAR:
                    c.set(x, y, BLACK)
        if glint and r >= 2:
            c.set(ex - r + 1, cy - r + 1, WHITE)
    return c


def visor(c, x0, y0, w, h):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if c.get(x, y) != CLEAR:
                c.set(x, y, BLACK)
    for x in range(x0 + 1, x0 + 4):
        c.set(x, y0 + 1, WHITE)
    return c


def mouth(c, cx, cy, w):
    for x in range(cx - w // 2, cx + w // 2 + 1):
        if c.get(x, cy) != CLEAR:
            c.set(x, cy, BLACK)
    return c


def fangs(c, cx, cy, w):
    mouth(c, cx, cy, w)
    for x in range(cx - w // 2, cx + w // 2 + 1, 2):
        if c.get(x, cy + 1) != CLEAR:
            c.set(x, cy + 1, BLACK)
    return c


def seam(c, x0, y0, x1, y1):
    c.line(x0, y0, x1, y1, BLACK)
    return c


def sparks(c, points):
    for x, y in points:
        c.set(x, y, BLACK)
        c.set(x + 1, y + 1, BLACK)
        c.set(x - 1, y + 1, BLACK)
        c.set(x, y + 2, BLACK)
    return c


# --- species -------------------------------------------------------------


def rubblin():
    s = Shape()
    s.ellipse(15.5, 20, 10, 8)
    s.box(6, 20, 20, 6)
    s.tri(8, 8, 9, 7)
    s.tri(18, 10, 8, 6)
    s.box(6, 26, 4, 4)
    s.box(22, 26, 4, 4)
    c = render(s)
    eyes(c, 15, 18, 5, 2)
    mouth(c, 15, 23, 6)
    seam(c, 8, 25, 24, 25)
    return c


def cragnome():
    s = Shape()
    s.ellipse(15.5, 19, 12, 10)
    s.box(4, 18, 24, 9)
    s.tri(4, 4, 8, 9)
    s.tri(12, 1, 9, 9)
    s.tri(21, 4, 8, 9)
    s.box(3, 12, 4, 12)
    s.box(25, 12, 4, 12)
    s.box(6, 27, 6, 4)
    s.box(20, 27, 6, 4)
    c = render(s)
    eyes(c, 15, 17, 6, 2)
    fangs(c, 15, 23, 10)
    seam(c, 6, 26, 25, 26)
    seam(c, 9, 12, 12, 16)
    seam(c, 22, 12, 19, 16)
    return c


def frostpod():
    s = Shape()
    s.ellipse(15.5, 21, 8, 9)
    s.ellipse(15.5, 12, 6, 6)
    s.tri(11, 2, 4, 7)
    s.tri(14, 0, 5, 8)
    s.tri(18, 2, 4, 7)
    s.box(9, 27, 5, 3)
    s.box(18, 27, 5, 3)
    c = render(s, shade=0.5)
    eyes(c, 15, 12, 4, 2)
    mouth(c, 15, 16, 4)
    seam(c, 10, 22, 21, 22)
    seam(c, 11, 25, 20, 25)
    return c


def cryonaut():
    s = Shape()
    s.ellipse(15.5, 22, 9, 9)
    s.box(7, 20, 18, 8)
    s.ellipse(15.5, 11, 8, 8)
    s.tri(9, 0, 6, 6)
    s.tri(17, 0, 6, 6)
    s.taper(8, 18, 3, 26, 2.5, 1.5)
    s.taper(23, 18, 28, 26, 2.5, 1.5)
    s.box(9, 28, 5, 3)
    s.box(18, 28, 5, 3)
    c = render(s, shade=0.5)
    visor(c, 10, 9, 12, 4)
    seam(c, 9, 20, 22, 20)
    seam(c, 15, 21, 15, 27)
    return c


def sparklet():
    s = Shape()
    s.ellipse(15.5, 16, 8, 8)
    s.tri(11, 3, 4, 6)
    s.tri(17, 3, 4, 6)
    s.taper(12, 23, 8, 29, 2, 1)
    s.taper(19, 23, 23, 29, 2, 1)
    c = render(s, shade=0.5)
    eyes(c, 15, 15, 4, 2)
    mouth(c, 15, 20, 5)
    sparks(c, [(4, 10), (26, 12), (6, 22)])
    seam(c, 8, 16, 11, 16)
    seam(c, 20, 16, 23, 16)
    return c


def arcfang():
    s = Shape()
    s.ellipse(14, 19, 10, 7)
    s.ellipse(23, 14, 6, 6)
    s.tri(20, 4, 4, 6)
    s.tri(25, 4, 4, 6)
    s.taper(6, 18, 2, 8, 2.5, 1)
    s.box(7, 24, 4, 7)
    s.box(13, 24, 4, 7)
    s.box(19, 24, 4, 7)
    c = render(s, shade=0.6, light=(20, 8))
    eyes(c, 24, 13, 3, 1)
    fangs(c, 26, 18, 5)
    sparks(c, [(4, 6), (9, 12)])
    seam(c, 9, 22, 20, 22)
    return c


def tinplate():
    s = Shape()
    s.ellipse(15.5, 19, 11, 7)
    s.box(5, 19, 22, 5)
    s.taper(7, 16, 2, 9, 2, 2)
    s.taper(24, 16, 29, 9, 2, 2)
    s.box(7, 24, 4, 5)
    s.box(14, 24, 4, 5)
    s.box(21, 24, 4, 5)
    c = render(s, shade=0.6)
    visor(c, 10, 16, 12, 3)
    seam(c, 5, 22, 26, 22)
    seam(c, 15, 13, 15, 22)
    return c


def ferrox():
    s = Shape()
    s.ellipse(15.5, 18, 13, 10)
    s.box(3, 18, 26, 8)
    s.tri(10, 3, 5, 7)
    s.tri(18, 3, 5, 7)
    s.box(1, 14, 4, 8)
    s.box(27, 14, 4, 8)
    s.box(5, 26, 6, 5)
    s.box(21, 26, 6, 5)
    c = render(s, shade=0.65)
    visor(c, 9, 14, 14, 4)
    seam(c, 4, 21, 27, 21)
    seam(c, 4, 24, 27, 24)
    seam(c, 15, 8, 15, 14)
    return c


def mycomite():
    s = Shape()
    s.ellipse(15.5, 13, 11, 7)
    s.box(11, 15, 10, 12)
    s.box(8, 27, 5, 3)
    s.box(19, 27, 5, 3)
    c = render(s, shade=0.55)
    for x, y in ((8, 10), (13, 7), (20, 8), (24, 12)):
        c.set(x, y, BLACK)
        c.set(x + 1, y, BLACK)
        c.set(x, y + 1, BLACK)
        c.set(x + 1, y + 1, BLACK)
    eyes(c, 15, 20, 3, 1)
    mouth(c, 15, 24, 4)
    seam(c, 5, 17, 26, 17)
    return c


def bloomshade():
    s = Shape()
    s.ellipse(15.5, 11, 14, 9)
    s.box(10, 13, 12, 15)
    s.taper(10, 20, 3, 28, 2, 1)
    s.taper(21, 20, 28, 28, 2, 1)
    s.box(7, 28, 6, 3)
    s.box(19, 28, 6, 3)
    c = render(s, shade=0.6)
    for x, y in ((6, 9), (11, 5), (17, 4), (23, 8), (26, 13)):
        for dx in range(3):
            for dy in range(3):
                if (dx + dy) % 2 == 0:
                    c.set(x + dx, y + dy, BLACK)
    eyes(c, 15, 19, 4, 2)
    fangs(c, 15, 24, 7)
    seam(c, 2, 16, 29, 16)
    return c


def nullet():
    s = Shape()
    s.ellipse(15.5, 16, 9, 9)
    s.tri(12, 4, 8, 6)
    s.taper(15, 24, 15, 30, 3, 1)
    c = render(s, shade=0.42)
    for y in range(11, 22):
        for x in range(10, 22):
            if (x - 15) ** 2 + (y - 16) ** 2 <= 25:
                c.set(x, y, BLACK)
    for sx in (-1, 1):
        c.set(15 + sx * 3, 15, WHITE)
        c.set(15 + sx * 3, 16, WHITE)
        c.set(15 + sx * 2, 15, WHITE)
    return c


def vantabeast():
    s = Shape()
    s.ellipse(15.5, 19, 12, 10)
    s.ellipse(15.5, 10, 8, 7)
    s.tri(6, 1, 6, 7)
    s.tri(20, 1, 6, 7)
    s.taper(5, 20, 1, 28, 3, 1)
    s.taper(26, 20, 30, 28, 3, 1)
    s.box(7, 27, 6, 4)
    s.box(19, 27, 6, 4)
    c = render(s, shade=0.35)
    for y in range(4, 30):
        for x in range(2, 30):
            if c.get(x, y) == WHITE and dither_at(x, y, 11) == BLACK:
                c.set(x, y, BLACK)
    for sx in (-1, 1):
        for dx in range(3):
            c.set(15 + sx * 4 + dx * sx, 9, WHITE)
            c.set(15 + sx * 4 + dx * sx, 10, WHITE)
    fangs(c, 15, 15, 9)
    return c


# Order matches data/species.lua ids.
ZNOMES = [
    ("rubblin", rubblin),
    ("cragnome", cragnome),
    ("frostpod", frostpod),
    ("cryonaut", cryonaut),
    ("sparklet", sparklet),
    ("arcfang", arcfang),
    ("tinplate", tinplate),
    ("ferrox", ferrox),
    ("mycomite", mycomite),
    ("bloomshade", bloomshade),
    ("nullet", nullet),
    ("vantabeast", vantabeast),
]
