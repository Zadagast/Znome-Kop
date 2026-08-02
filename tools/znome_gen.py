"""Procedural Znome sprite generator.

Port of Deep-Fold's MIT-licensed SpriteGenerator algorithm (Godot,
https://github.com/Deep-Fold/SpriteGenerator) to the 1-bit pipeline:
mirrored random map -> cellular automata -> flood-fill groups -> enclosed
holes become eyes -> edge/noise shading mapped to dither tones + outline.

Species identity comes from a coarse authored bias mask per species (the
silhouette the random fill grows around) plus a hand-picked seed.
"""

import random

from canvas import BLACK, WHITE, Canvas, dither_at

SIZE = 32

BIRTH_LIMIT = 5
DEATH_LIMIT = 4
CA_STEPS = 4


def _value_noise(rng, w, h, period):
    lat_w = w // period + 2
    lat_h = h // period + 2
    lat = [[rng.random() for _ in range(lat_w)] for _ in range(lat_h)]

    def at(x, y):
        gx, gy = x / period, y / period
        x0, y0 = int(gx), int(gy)
        fx, fy = gx - x0, gy - y0
        v00, v10 = lat[y0][x0], lat[y0][x0 + 1]
        v01, v11 = lat[y0 + 1][x0], lat[y0 + 1][x0 + 1]
        top = v00 + (v10 - v00) * fx
        bot = v01 + (v11 - v01) * fx
        return top + (bot - top) * fy

    return at


def _mask_prob(mask, x, y, w, h):
    """Fill probability for cell (x,y) from a coarse ASCII bias mask."""
    if not mask:
        return 0.52
    my = int(y * len(mask) / h)
    mx = int(x * len(mask[0]) / w)
    ch = mask[my][mx]
    return {"#": 0.82, "+": 0.55, ".": 0.08}[ch]


def _generate_map(rng, w, h, mask):
    grid = [[False] * w for _ in range(h)]
    half = (w + 1) // 2
    for y in range(h):
        for x in range(half):
            p = _mask_prob(mask, x, y, w, h)
            v = rng.random() < p
            grid[y][x] = v
            grid[y][w - 1 - x] = v
    # mirrored random walks knit the halves together
    for _ in range(2):
        x = rng.randrange(w)
        y = rng.randrange(h)
        for _ in range(60):
            if 0 <= x < w and 0 <= y < h:
                if _mask_prob(mask, min(x, w - 1 - x), y, w, h) > 0.2:
                    grid[y][x] = True
                    grid[y][w - 1 - x] = True
            x += rng.randrange(-1, 2)
            y += rng.randrange(-1, 2)
    return grid


def _ca_step(grid, w, h):
    out = [row[:] for row in grid]
    for y in range(h):
        for x in range(w):
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and grid[yy][xx]:
                        n += 1
            if grid[y][x] and n < DEATH_LIMIT:
                out[y][x] = False
            elif not grid[y][x] and n > BIRTH_LIMIT:
                out[y][x] = True
    return out


def _flood(grid, w, h, want):
    seen = [[False] * w for _ in range(h)]
    groups = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or grid[y][x] is not want:
                continue
            bucket = [(x, y)]
            seen[y][x] = True
            cells, edge = [], False
            while bucket:
                cx, cy = bucket.pop()
                cells.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = cx + dx, cy + dy
                    if not (0 <= xx < w and 0 <= yy < h):
                        edge = True
                        continue
                    if not seen[yy][xx] and grid[yy][xx] is want:
                        seen[yy][xx] = True
                        bucket.append((xx, yy))
            groups.append((cells, edge))
    return groups


def _stamp_eyes(c, grid, w, h, ox, oy):
    """Carve two symmetric eyes into the head region of the silhouette."""
    rows = [y for y in range(h) if any(grid[y])]
    if not rows:
        return
    top, bottom = rows[0], rows[-1]
    ey = top + max(2, (bottom - top) * 3 // 10)
    for dy in range(0, 5):
        y = ey + dy
        if y >= h:
            break
        xs = [x for x in range(w) if grid[y][x]]
        if not xs:
            continue
        span = max(xs) - min(xs)
        if span < 7:
            continue
        off = max(2, span // 5)
        lx, rx = w // 2 - off, (w - 1) - (w // 2 - off)
        ok = all(
            0 <= x < w and grid[yy][x]
            for x in (lx, lx + 1, rx - 1, rx)
            for yy in (y, min(h - 1, y + 1))
        )
        if not ok:
            continue
        for x0 in (lx, rx - 1):
            c.set(ox + x0, oy + y, WHITE)
            c.set(ox + x0 + 1, oy + y, WHITE)
            c.set(ox + x0, oy + y + 1, BLACK)
            c.set(ox + x0 + 1, oy + y + 1, BLACK)
        return


def generate(seed, mask=None, w=26, h=26, dark=False):
    """Return a SIZE x SIZE Canvas with the generated creature centred."""
    rng = random.Random(seed)
    grid = _generate_map(rng, w, h, mask)
    for _ in range(CA_STEPS):
        grid = _ca_step(grid, w, h)

    # keep only groups >= 25% of the largest
    groups = [g for g, _ in _flood(grid, w, h, True)]
    if not groups:
        return Canvas(SIZE, SIZE)
    largest = max(len(g) for g in groups)
    for g in groups:
        if len(g) < largest * 0.25:
            for x, y in g:
                grid[y][x] = False

    # enclosed holes: small ones are eyes (white + dark core), large stay holes
    holes = [g for g, edge in _flood(grid, w, h, False) if not edge]

    noise = _value_noise(rng, w, h, 6)
    c = Canvas(SIZE, SIZE)
    ox, oy = (SIZE - w) // 2, (SIZE - h) // 2

    def filled(x, y):
        return 0 <= x < w and 0 <= y < h and grid[y][x]

    for y in range(h):
        for x in range(w):
            if not grid[y][x]:
                continue
            mx = min(x, w - 1 - x)  # mirrored shading like the original
            n = abs(noise(mx, y)) * 1.2 - 0.3
            if not filled(x, y + 1):
                n += 0.55
            if not filled(x, y - 1):
                n -= 0.35
            if not filled(x + 1, y):
                n += 0.15
            if not filled(x - 1, y):
                n += 0.15
            tone = max(0, min(3, int(n * 4)))
            level = ((16, 12, 8, 4) if dark else (0, 4, 8, 16))[tone]
            c.set(ox + x, oy + y, dither_at(x, y, level) if level else WHITE)

    # black outline around the silhouette
    for y in range(h):
        for x in range(w):
            if grid[y][x]:
                continue
            if (filled(x + 1, y) or filled(x - 1, y)
                    or filled(x, y + 1) or filled(x, y - 1)):
                c.set(ox + x, oy + y, BLACK)
    for y in range(h):
        for x in range(w):
            if filled(x, y) and (x in (0, w - 1) or y in (0, h - 1)):
                c.set(ox + x, oy + y, c.get(ox + x, oy + y))

    # eyes from enclosed holes
    got_hole_eyes = False
    for hole in holes:
        if len(hole) > 12:
            continue
        got_hole_eyes = True
        cx = sum(p[0] for p in hole) / len(hole)
        cy = sum(p[1] for p in hole) / len(hole)
        for x, y in hole:
            c.set(ox + x, oy + y, WHITE)
        for x, y in hole:
            if abs(x - cx) <= 0.7 and abs(y - cy) <= 0.7:
                c.set(ox + x, oy + y, BLACK)
    if not got_hole_eyes:
        _stamp_eyes(c, grid, w, h, ox, oy)
    return c
