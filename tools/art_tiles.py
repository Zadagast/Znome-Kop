"""Own procedural 32px Mars tileset.

Everything is generated (no third-party packs): GB drawing conventions
(black outline, white fill, sparse ordered dither) at native 32px, the
size Playdate needs for tiles to read at Game Boy physical scale
(donaldhays.com/2019/12/30/playdate-art-scale).  Organic tiles use the
same cellular-automata growth as spritegen; manufactured tiles are
parametric.
"""

import math
import random

from canvas import BLACK, CLEAR, WHITE, Canvas, dither_at

T = 32


def rnd(x, y, salt=0):
    """Stable hash noise so tiles regenerate identically."""
    h = (x * 374761393 + y * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def ca_blob(seed, w, h, fill=0.55, steps=3, mirror=True):
    """Grow a connected blob mask with cellular automata (spritegen's
    rules), optionally x-mirrored.  Returns set of (x, y)."""
    rng = random.Random(seed)
    half = (w + 1) // 2 if mirror else w
    grid = [[rng.random() < fill for _ in range(h)] for _ in range(half)]
    for _ in range(steps):
        nxt = [col[:] for col in grid]
        for x in range(half):
            for y in range(h):
                n = 0
                for i in (-1, 0, 1):
                    for j in (-1, 0, 1):
                        if i == j == 0:
                            continue
                        xx, yy = x + i, y + j
                        if xx < 0 or yy < 0 or yy >= h:
                            continue
                        if xx >= half:
                            xx = half - 1 if mirror else half
                        if xx < half and grid[xx][yy]:
                            n += 1
                nxt[x][y] = n >= 5 if not grid[x][y] else n >= 3
        grid = nxt
    pts = set()
    for x in range(half):
        for y in range(h):
            if grid[x][y]:
                pts.add((x, y))
                if mirror:
                    pts.add((w - 1 - x, y))
    return pts


def draw_blob(c, pts, ox, oy, shade=0, shadow=True):
    """Draw a blob mask with outline, white fill, dither on the lower
    right (GB light-from-upper-left)."""
    for (x, y) in pts:
        px, py = ox + x, oy + y
        if shadow and ((x + 2, y) not in pts or (x, y + 2) not in pts) \
                and (x - 1, y) in pts and (x, y - 1) in pts:
            c.set(px, py, dither_at(px, py, 6))
        else:
            c.set(px, py, dither_at(px, py, shade))
    for (x, y) in pts:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in pts:
                c.set(ox + nx, oy + ny, BLACK)


def base(fill=WHITE):
    return Canvas(T, T, fill)


# --- ground --------------------------------------------------------------


def t_dust():
    """Clean walkable path: white with sparse dash marks."""
    c = base()
    for x, y in ((7, 9), (22, 22), (13, 27)):
        c.hline(x, x + 2, y, BLACK)
    return c


def t_regolith():
    c = base()
    for i, (x, y) in enumerate(((5, 6), (21, 11), (10, 24), (26, 25), (16, 15))):
        c.hline(x, x + 1 + i % 2, y, BLACK)
        c.set(x + 3, y - 2, BLACK)
    return c


def t_gravel():
    """Outlined pebbles, uneven sizes."""
    c = base()
    stones = ((3, 4, 6, 4), (17, 2, 8, 5), (24, 12, 6, 4),
              (5, 14, 8, 5), (16, 21, 7, 5), (4, 25, 5, 3))
    for (x, y, w, h) in stones:
        c.rect(x + 1, y + 1, w - 2, h - 2, WHITE)
        c.hline(x + 1, x + w - 2, y, BLACK)
        c.hline(x + 1, x + w - 2, y + h - 1, BLACK)
        c.vline(x, y + 1, y + h - 2, BLACK)
        c.vline(x + w - 1, y + 1, y + h - 2, BLACK)
        c.hline(x + 2, x + w - 3, y + h - 2, dither_at(x, y, 8) and BLACK)
    return c


def t_dunes():
    """Wind ripples: stepped crests with a shadow dash under each."""
    c = base()
    for row, (y0, off) in enumerate(((5, 0), (14, 8), (23, 0))):
        x = 2 + off
        while x < T - 6:
            c.hline(x, x + 6, y0, BLACK)
            c.line(x + 6, y0, x + 8, y0 + 2, BLACK)
            c.hline(x + 2, x + 5, y0 + 2, dither_at(x, y0, 4) and BLACK)
            x += 14
    return c


def t_plate():
    """Colony deck plate with corner bolts."""
    c = base()
    c.outline_rect(0, 0, T, T, BLACK)
    for x, y in ((4, 4), (T - 6, 4), (4, T - 6), (T - 6, T - 6)):
        c.outline_rect(x, y, 2, 2, BLACK)
    c.hline(10, 21, T - 7, BLACK)
    return c


def t_grate():
    c = t_plate()
    for y in range(8, 24, 5):
        c.hline(8, 23, y, BLACK)
        c.hline(8, 23, y + 1, BLACK)
    c.vline(8, 8, 20, BLACK)
    c.vline(23, 8, 20, BLACK)
    return c


def tuft(c, x, y):
    """GB encounter-grass tuft, 9x6: three blades splaying from a base."""
    c.vline(x + 4, y, y + 1, BLACK)
    c.set(x + 2, y + 1, BLACK)
    c.set(x + 6, y + 1, BLACK)
    c.set(x + 1, y + 2, BLACK)
    c.vline(x + 4, y + 2, y + 3, BLACK)
    c.set(x + 7, y + 2, BLACK)
    c.set(x, y + 3, BLACK)
    c.set(x + 8, y + 3, BLACK)
    c.set(x + 2, y + 4, BLACK)
    c.set(x + 6, y + 4, BLACK)
    c.hline(x + 3, x + 5, y + 5, BLACK)


def t_sporegrass():
    """Uniform tuft lattice like the Pokemon encounter grass."""
    c = base()
    for gy, off in ((2, 1), (12, 12), (22, 1)):
        for gx in range(off, T - 9, 21):
            tuft(c, gx, gy)
    return c


def t_sporegrass_tall():
    c = base()
    for gy, off in ((0, 1), (8, 12), (16, 1), (24, 12)):
        for gx in range(off, T - 9, 21):
            tuft(c, gx, gy)
    for x in (4, 26):
        c.vline(x, 12, 20, BLACK)
    return c


def t_coolant():
    """Coolant pool: light wash with clean wave dashes."""
    c = base()
    c.dither_rect(0, 0, T, T, "d12")
    for y, off in ((6, 3), (16, 14), (26, 3)):
        c.hline(off, off + 8, y, BLACK)
        c.set(off + 9, y + 1, BLACK)
        c.hline(off + 14, off + 19, y + 1, BLACK)
    return c


def t_rock():
    """Impassable rock face, GB-mountain style facets."""
    c = base()
    c.dither_rect(0, 0, T, T, "d50")
    # one rounded boulder per tile so walls read as stacked rocks
    r = 5
    pts = set()
    for y in range(1, T - 1):
        for x in range(1, T - 1):
            cx = min(max(x, 1 + r), T - 2 - r)
            cy = min(max(y, 1 + r), T - 2 - r)
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                pts.add((x, y))
    draw_blob(c, pts, 0, 0)
    # facet cracks + shading
    c.line(10, 7, 16, 13, BLACK)
    c.line(16, 13, 12, 21, BLACK)
    c.line(21, 9, 24, 16, BLACK)
    c.hline(7, 13, 25, BLACK)
    return c


def t_cliff():
    """Strata cliff: dark cap, cracked white face, dark base."""
    c = base()
    c.rect(0, 0, T, 4, BLACK)
    c.hline(0, T - 1, 14, BLACK)
    c.hline(0, T - 1, 15, BLACK)
    c.rect(0, 29, T, 3, BLACK)
    for x, y0, y1 in ((9, 4, 12), (25, 4, 9), (5, 16, 25), (19, 16, 28)):
        c.vline(x, y0, y1, BLACK)
    c.dither_rect(0, 25, T, 4, "d50")
    return c


def t_crater():
    """Impact pit: raised outlined rim around a dark floor."""
    c = base()
    cx, cy = 15.5, 15.5
    for y in range(T):
        for x in range(T):
            r = math.hypot((x - cx), (y - cy) * 1.15)
            if r < 9:
                c.set(x, y, dither_at(x, y, 12))
            elif r < 12:
                c.set(x, y, WHITE)
            elif r < 13.5:
                c.set(x, y, BLACK)
    for y in range(T):
        for x in range(T):
            r = math.hypot((x - cx), (y - cy) * 1.15)
            if 8 <= r < 9.5 and c.get(x, y) != BLACK:
                c.set(x, y, BLACK if (x + y) % 2 else c.get(x, y))
    return c


def t_tube():
    """Collapsed lava-tube floor: dark with pale cracks."""
    c = base()
    c.dither_rect(0, 0, T, T, "d75")
    c.line(4, 28, 12, 12, WHITE)
    c.line(12, 12, 10, 2, WHITE)
    c.line(20, 30, 24, 16, WHITE)
    c.line(24, 16, 30, 10, WHITE)
    return c


def t_ash():
    """Encounter terrain for volcanic sectors: ash drifts."""
    c = base()
    for gy, off in ((4, 2), (14, 13), (24, 2)):
        for gx in range(off, T - 8, 20):
            c.hline(gx + 1, gx + 5, gy + 2, BLACK)
            c.set(gx, gy + 1, BLACK)
            c.set(gx + 6, gy + 1, BLACK)
            c.set(gx + 3, gy, BLACK)
            c.set(gx + 2, gy + 4, dither_at(gx, gy, 8))
    return c


# --- objects (drawn over ground, CLEAR background) -------------------------


def o_boulder():
    c = Canvas(T, T)
    pts = ca_blob(11, 26, 22, fill=0.62, steps=3)
    draw_blob(c, pts, 3, 6)
    return c


def o_fence_h():
    """Perimeter railing: two rails on posts."""
    c = Canvas(T, T)
    for x in (2, 15, 28):
        c.rect(x + 1, 9, 1, 17, WHITE)
        c.outline_rect(x, 8, 3, 19, BLACK)
    for y in (12, 20):
        c.rect(0, y + 1, T, 1, WHITE)
        c.hline(0, T - 1, y, BLACK)
        c.hline(0, T - 1, y + 2, BLACK)
    return c


def o_fence_v():
    c = Canvas(T, T)
    for y in (2, 15, 28):
        c.rect(9, y + 1, 17, 1, WHITE)
        c.outline_rect(8, y, 19, 3, BLACK)
    for x in (12, 20):
        c.rect(x + 1, 0, 1, T, WHITE)
        c.vline(x, 0, T - 1, BLACK)
        c.vline(x + 2, 0, T - 1, BLACK)
    return c


def o_sign():
    c = Canvas(T, T)
    c.rect(5, 4, 22, 14, WHITE)
    c.outline_rect(4, 3, 24, 16, BLACK)
    for y in (8, 12):
        c.hline(8, 23, y, BLACK)
    c.rect(14, 19, 4, 10, WHITE)
    c.vline(13, 19, 29, BLACK)
    c.vline(18, 19, 29, BLACK)
    c.hline(13, 18, 29, BLACK)
    return c


def o_crate():
    c = Canvas(T, T)
    c.rect(3, 5, 26, 24, WHITE)
    c.outline_rect(2, 4, 28, 26, BLACK)
    c.outline_rect(6, 8, 20, 18, BLACK)
    c.line(6, 8, 25, 25, BLACK)
    c.line(25, 8, 6, 25, BLACK)
    c.dither_rect(3, 26, 26, 3, "d50")
    return c


def o_pipe_h():
    c = Canvas(T, T)
    c.rect(0, 11, T, 10, WHITE)
    c.hline(0, T - 1, 10, BLACK)
    c.hline(0, T - 1, 21, BLACK)
    c.hline(0, T - 1, 18, BLACK)
    c.dither_rect(0, 19, T, 2, "d50")
    for x in (8, 24):
        c.vline(x, 11, 20, BLACK)
        c.vline(x + 2, 11, 20, BLACK)
    return c


def o_pipe_v():
    c = Canvas(T, T)
    c.rect(11, 0, 10, T, WHITE)
    c.vline(10, 0, T - 1, BLACK)
    c.vline(21, 0, T - 1, BLACK)
    c.vline(18, 0, T - 1, BLACK)
    c.dither_rect(19, 0, 2, T, "d50")
    for y in (8, 24):
        c.hline(11, 20, y, BLACK)
        c.hline(11, 20, y + 2, BLACK)
    return c


def o_lichen():
    """Alien lichen patch: small outlined sprigs."""
    c = Canvas(T, T)
    for (x, y, s) in ((6, 8, 5), (20, 5, 4), (13, 18, 6), (24, 22, 4)):
        pts = ca_blob(x * 7 + y, s + 3, s, fill=0.75, steps=1, mirror=False)
        draw_blob(c, pts, x, y, shade=4, shadow=False)
    return c


def o_vent():
    c = Canvas(T, T)
    c.rect(5, 7, 22, 20, WHITE)
    c.outline_rect(4, 6, 24, 22, BLACK)
    for y in range(11, 24, 4):
        c.hline(8, 23, y, BLACK)
    c.set(10, 3, BLACK)
    c.set(14, 1, BLACK)
    c.set(19, 3, BLACK)
    return c


def o_marker():
    """Waypoint flag on a pole."""
    c = Canvas(T, T)
    c.vline(15, 6, 30, BLACK)
    c.vline(16, 6, 30, BLACK)
    c.rect(17, 6, 10, 7, WHITE)
    c.outline_rect(16, 5, 12, 9, BLACK)
    c.dither_rect(18, 7, 8, 5, "d50")
    c.hline(12, 19, 30, BLACK)
    return c


# --- structures ------------------------------------------------------------


def panel(c, x, y, w, h, density="white"):
    c.dither_rect(x, y, w, h, density)
    c.outline_rect(x, y, w, h, BLACK)


def window(c, x, y, w=12, h=10):
    """GB-house window: white frame, dark glass, highlight line."""
    c.rect(x - 1, y - 1, w + 2, h + 2, WHITE)
    c.dither_rect(x, y, w, h, "d75")
    c.outline_rect(x - 1, y - 1, w + 2, h + 2, BLACK)
    c.hline(x + 1, x + w - 2, y + 1, WHITE)
    c.vline(x + w // 2, y, y + h - 1, BLACK)


def door(c, x, y, w, h):
    """Sliding airlock door with a track shadow."""
    c.rect(x + 1, y + 1, w - 2, h - 1, WHITE)
    c.outline_rect(x, y, w, h, BLACK)
    c.vline(x + w // 2 - 1, y + 2, y + h - 2, BLACK)
    c.vline(x + w // 2, y + 2, y + h - 2, BLACK)
    c.dither_rect(x + 2, y + 2, w - 4, 3, "d50")
    c.hline(x + 3, x + w - 4, y + h - 3, BLACK)


def dome(c, cx, base_y, rx, ry, seam_step=8):
    """Dome roof: outlined half-ellipse with seam lines + side shading."""
    for y in range(base_y - ry, base_y + 1):
        dy = (y - base_y) / ry
        span = rx * math.sqrt(max(0.0, 1 - dy * dy))
        for x in range(int(cx - span), int(cx + span) + 1):
            shade = 4 if x > cx + span * 0.45 else 0
            c.set(x, y, dither_at(x, y, shade))
    for y in range(base_y - ry, base_y + 1):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if c.get(x, y) == CLEAR:
                continue
            if CLEAR in (c.get(x - 1, y), c.get(x + 1, y), c.get(x, y - 1)):
                c.set(x, y, BLACK)
    for y in range(base_y - ry + seam_step // 2, base_y, seam_step):
        dy = (y - base_y) / ry
        span = rx * math.sqrt(max(0.0, 1 - dy * dy))
        c.hline(int(cx - span) + 2, int(cx + span) - 2, y, BLACK)


def s_hab():
    """4x3 tile habitat: dome roof, riveted body, two windows, airlock."""
    w, h = 4 * T, 3 * T
    c = Canvas(w, h)
    dome(c, w // 2, 52, w // 2 - 2, 40)
    panel(c, 2, 52, w - 4, h - 53)
    c.hline(3, w - 4, 55, BLACK)
    window(c, 14, 62)
    window(c, w - 26, 62)
    door(c, 2 * T + 4, h - 26, 24, 26)
    for x in (8, w - 9):
        c.set(x, 58, BLACK)
        c.set(x, h - 6, BLACK)
    return c, {"w": 4, "h": 3, "doors": [(2, 2)]}


def s_lab():
    """5x4 tile research lab: stacked hull, antenna, window band."""
    w, h = 5 * T, 4 * T
    c = Canvas(w, h)
    panel(c, 0, 44, w, h - 44)
    panel(c, 14, 18, w - 28, 30, "white")
    for y in (26, 36):
        c.hline(16, w - 17, y, BLACK)
    panel(c, 40, 4, w - 80, 16, "d25")
    c.vline(w // 2, 0, 4, BLACK)
    c.hline(w // 2 - 6, w // 2 + 6, 0, BLACK)
    # window band
    panel(c, 10, 52, w - 20, 18, "d75")
    for x in range(26, w - 20, 24):
        c.vline(x, 52, 69, WHITE)
        c.vline(x + 1, 52, 69, WHITE)
    c.hline(12, w - 13, 54, WHITE)
    door(c, 2 * T + 4, h - 30, 24, 30)
    for sx in (10, w - 22):
        panel(c, sx, 84, 12, h - 88, "white")
        c.hline(sx + 2, sx + 9, 96, BLACK)
    return c, {"w": 5, "h": 4, "doors": [(2, 3)]}


def s_gate():
    """3x2 perimeter airlock: pillar - gateway - pillar."""
    w, h = 3 * T, 2 * T
    c = Canvas(w, h)
    for px in (0, 2 * T):
        panel(c, px + 2, 2, T - 4, h - 2, "white")
        c.dither_rect(px + 4, 6, T - 8, 6, "d50")
        c.outline_rect(px + 4, 6, T - 8, 6, BLACK)
        for y in range(20, h - 4, 10):
            c.hline(px + 5, px + T - 6, y, BLACK)
    c.rect(T - 2, 0, T + 4, 8, WHITE)
    c.outline_rect(T - 2, 0, T + 4, 8, BLACK)
    c.dither_rect(T, 2, T, 4, "d25")
    door(c, T + 4, 12, T - 8, h - 12)
    return c, {"w": 3, "h": 2, "doors": [(1, 1)]}


def s_solar():
    """2x2 solar array on a mast."""
    w, h = 2 * T, 2 * T
    c = Canvas(w, h)
    panel(c, 2, 4, w - 4, 34, "d12")
    for x in range(10, w - 4, 10):
        c.vline(x, 5, 37, BLACK)
    c.hline(3, w - 4, 21, BLACK)
    c.hline(3, w - 4, 22, BLACK)
    c.vline(w // 2 - 1, 38, h - 4, BLACK)
    c.vline(w // 2, 38, h - 4, BLACK)
    c.hline(w // 2 - 8, w // 2 + 8, h - 4, BLACK)
    c.hline(w // 2 - 8, w // 2 + 8, h - 3, BLACK)
    return c, {"w": 2, "h": 2, "doors": []}


def s_tank():
    """2x2 coolant tank: cylinder with hoops."""
    w, h = 2 * T, 2 * T
    c = Canvas(w, h)
    for y in range(4, h - 4):
        for x in range(4, w - 4):
            dx = (x - w / 2 + 0.5) / (w / 2 - 5)
            if abs(dx) <= 1.0:
                c.set(x, y, dither_at(x, y, 0 if dx < 0.3 else 6))
    c.outline_rect(4, 4, w - 8, h - 8, BLACK)
    for y in range(12, h - 8, 14):
        c.hline(5, w - 6, y, BLACK)
        c.hline(5, w - 6, y + 1, BLACK)
    c.hline(24, 39, 2, BLACK)
    c.vline(24, 2, 4, BLACK)
    c.vline(39, 2, 4, BLACK)
    return c, {"w": 2, "h": 2, "doors": []}


def s_tower():
    """2x3 relay tower: lattice mast with beacon head."""
    w, h = 2 * T, 3 * T
    c = Canvas(w, h)
    c.line(8, h - 1, w // 2 - 2, 10, BLACK)
    c.line(9, h - 1, w // 2 - 1, 10, BLACK)
    c.line(w - 9, h - 1, w // 2 + 1, 10, BLACK)
    c.line(w - 10, h - 1, w // 2, 10, BLACK)
    for y in range(16, h - 2, 12):
        lx = int(8 + (w // 2 - 10) * (h - 1 - y) / (h - 11))
        c.hline(lx, w - 1 - lx, y, BLACK)
    c.rect(w // 2 - 7, 2, 14, 9, WHITE)
    c.outline_rect(w // 2 - 7, 2, 14, 9, BLACK)
    c.dither_rect(w // 2 - 4, 4, 8, 5, "d50")
    c.vline(w // 2 - 1, 0, 2, BLACK)
    c.set(w // 2 - 3, 1, BLACK)
    c.set(w // 2 + 1, 1, BLACK)
    return c, {"w": 2, "h": 3, "doors": []}


GROUND_TILES = [
    ("dust", t_dust, {}),
    ("regolith", t_regolith, {}),
    ("gravel", t_gravel, {}),
    ("dunes", t_dunes, {}),
    ("plate", t_plate, {}),
    ("grate", t_grate, {}),
    ("sporegrass", t_sporegrass, {"encounter": True}),
    ("sporegrass_tall", t_sporegrass_tall, {"encounter": True}),
    ("coolant", t_coolant, {"solid": True}),
    ("rock", t_rock, {"solid": True}),
    ("cliff", t_cliff, {"solid": True}),
    ("crater", t_crater, {"solid": True}),
    ("tube", t_tube, {}),
    ("ash", t_ash, {"encounter": True}),
]

OBJECT_TILES = [
    ("boulder", o_boulder, {"solid": True}),
    ("fence_h", o_fence_h, {"solid": True}),
    ("fence_v", o_fence_v, {"solid": True}),
    ("sign", o_sign, {"solid": True}),
    ("crate", o_crate, {"solid": True}),
    ("pipe_h", o_pipe_h, {"solid": True}),
    ("pipe_v", o_pipe_v, {"solid": True}),
    ("lichen", o_lichen, {}),
    ("vent", o_vent, {"solid": True}),
    ("marker", o_marker, {"solid": True}),
]

STRUCTURES = [
    ("hab", s_hab),
    ("lab", s_lab),
    ("gate", s_gate),
    ("solar", s_solar),
    ("tank", s_tank),
    ("tower", s_tower),
]
