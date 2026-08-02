"""Faithful Python port of Deep-Fold's SpriteGenerator (MIT).

https://github.com/Deep-Fold/SpriteGenerator /
https://deep-fold.itch.io/pixel-sprite-generator

Same pipeline as the Godot original: mirrored random map with centre
bias + random walks -> 4 cellular-automata steps -> flood-fill groups
(small ones culled) -> enclosed negative groups become eyes -> cosine
colour schemes + simplex-style noise + edge highlights pick per-cell
colours, with a black outline.

The only adaptation is the final display step: each cell's colour is
reduced to luminance and rendered as an ordered-dither 1-bit pattern.
"""

import math
import random

from canvas import BLACK, CLEAR, WHITE, Canvas, dither_at

SIZE = 32

BIRTH_LIMIT = 5
DEATH_LIMIT = 4
N_STEPS = 4
N_COLORS = 12


# --- OpenSimplex-style value noise (matches octaves/period/persistence
# --- parameters of the original's two OpenSimplexNoise instances)

class FractalNoise:
    def __init__(self, rng, octaves, period, persistence, lacunarity):
        self.octaves = octaves
        self.period = period
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.perm = list(range(256))
        rng.shuffle(self.perm)
        self.perm += self.perm

    def _grad(self, ix, iy):
        h = self.perm[(self.perm[ix & 255] + iy) & 255]
        ang = h * (2 * math.pi / 256)
        return math.cos(ang), math.sin(ang)

    def _noise2(self, x, y):
        x0, y0 = math.floor(x), math.floor(y)
        fx, fy = x - x0, y - y0
        u = fx * fx * (3 - 2 * fx)
        v = fy * fy * (3 - 2 * fy)
        n = 0.0
        for dy, wy in ((0, 1 - v), (1, v)):
            for dx, wx in ((0, 1 - u), (1, u)):
                gx, gy = self._grad(x0 + dx, y0 + dy)
                n += wx * wy * (gx * (fx - dx) + gy * (fy - dy))
        return n

    def get_noise_2d(self, x, y):
        amp, freq, total, peak = 1.0, 1.0 / self.period, 0.0, 0.0
        for _ in range(self.octaves):
            total += self._noise2(x * freq, y * freq) * amp
            peak += amp
            amp *= self.persistence
            freq *= self.lacunarity
        return total / peak


# --- MapGenerator.gd

def _generate_new(rng, w, h, fill=0.48, walks=2, walk_len=100):
    grid = [[False] * h for _ in range(w)]  # map[x][y] like the original
    for x in range(int(math.ceil(w * 0.5))):
        col = []
        for y in range(h):
            v = rng.uniform(0.0, 1.0) > fill
            to_center = abs(y - h * 0.5) * 2.0 / h
            if x in (w // 2 - 1, w // 2 - 2):
                if rng.uniform(0.0, 0.4) > to_center:
                    v = True
            col.append(v)
        grid[x] = col[:]
        grid[w - x - 1] = col[:]
    for _ in range(walks):
        _random_walk(rng, w, h, grid, walk_len)
    return grid


def _random_walk(rng, w, h, grid, walk_len=100):
    x, y = rng.randrange(w), rng.randrange(h)
    for _ in range(walk_len):
        if 0 <= x < w and 0 <= y < h:
            grid[x][y] = True
            grid[w - x - 1][y] = True
        x += rng.randrange(3) - 1
        y += rng.randrange(3) - 1


# --- CellularAutomata.gd

def _do_steps(grid, w, h, steps=N_STEPS):
    for _ in range(steps):
        grid = _step(grid, w, h)
    return grid


def _step(grid, w, h):
    out = [col[:] for col in grid]
    for x in range(w):
        for y in range(h):
            n = 0
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    if i == 0 and j == 0:
                        continue
                    xx, yy = x + i, y + j
                    if 0 <= xx < w and 0 <= yy < h and grid[xx][yy]:
                        n += 1
            if out[x][y] and n < DEATH_LIMIT:
                out[x][y] = False
            elif not out[x][y] and n > BIRTH_LIMIT:
                out[x][y] = True
    return out


# --- ColorSchemeGenerator.gd

def _generate_new_colorscheme(rng, n_colors):
    a = [rng.uniform(0.0, 0.5) for _ in range(3)]
    b = [rng.uniform(0.1, 0.6) for _ in range(3)]
    c = [rng.uniform(0.15, 0.8) for _ in range(3)]
    d = [rng.uniform(0.0, 1.0) for _ in range(3)]
    n = float(n_colors - 1)
    cols = []
    for i in range(n_colors):
        t = i / n
        cols.append(tuple(
            a[k] + b[k] * math.cos(6.28318 * (c[k] * t + d[k])) + t * 0.8
            for k in range(3)))
    return cols


# --- ColorFiller.gd

def _get_at(grid, w, h, x, y):
    if x < 0 or x >= w or y < 0 or y >= h:
        return None
    return grid[x][y]


def _fill_colors(rng, grid, w, h, scheme, eye_scheme, n_colors, outline):
    noise = FractalNoise(rng, 5, 30.0, 0.4, 3.0)
    noise2 = FractalNoise(rng, 3, 40.0, 0.4, 3.0)

    def flood(map_, is_negative):
        checked = [[False] * h for _ in range(w)]
        groups = []
        for sx in range(w):
            for sy in range(h):
                if checked[sx][sy]:
                    continue
                checked[sx][sy] = True
                if not map_[sx][sy]:
                    continue
                bucket = [(sx, sy)]
                group = {"arr": [], "valid": True}
                while bucket:
                    px, py = bucket.pop()
                    right = _get_at(map_, w, h, px + 1, py)
                    left = _get_at(map_, w, h, px - 1, py)
                    down = _get_at(map_, w, h, px, py + 1)
                    up = _get_at(map_, w, h, px, py - 1)
                    if is_negative and None in (left, up, down, right):
                        group["valid"] = False
                    col = _get_color(
                        map_, w, px, py, is_negative, right, left, down, up,
                        scheme, eye_scheme, n_colors, outline, group,
                        noise, noise2)
                    group["arr"].append(((px, py), col))
                    if right and not checked[px + 1][py]:
                        checked[px + 1][py] = True
                        bucket.append((px + 1, py))
                    if left and not checked[px - 1][py]:
                        checked[px - 1][py] = True
                        bucket.append((px - 1, py))
                    if down and not checked[px][py + 1]:
                        checked[px][py + 1] = True
                        bucket.append((px, py + 1))
                    if up and not checked[px][py - 1]:
                        checked[px][py - 1] = True
                        bucket.append((px, py - 1))
                groups.append(group)
        return groups

    groups = flood(grid, False)
    negative_map = [[not grid[x][y] for y in range(h)] for x in range(w)]
    negative_groups = flood(negative_map, True)
    return groups, negative_groups


def _get_color(map_, w, pos_x, pos_y, is_negative, right, left, down, up,
               scheme, eye_scheme, n_colors, outline, group, noise, noise2):
    col_x = math.ceil(abs(pos_x - (w - 1) * 0.5))
    n = pow(abs(noise.get_noise_2d(col_x, pos_y)), 1.5) * 3.0
    n2 = pow(abs(noise2.get_noise_2d(col_x, pos_y)), 1.5) * 3.0

    if not down:
        if is_negative:
            n2 -= 0.1
        else:
            n -= 0.45
        n *= 0.8
        if outline:
            group["arr"].append(((pos_x, pos_y + 1), "outline"))
    if not right:
        if is_negative:
            n2 += 0.1
        else:
            n += 0.2
        n *= 1.1
        if outline:
            group["arr"].append(((pos_x + 1, pos_y), "outline"))
    if not up:
        if is_negative:
            n2 += 0.15
        else:
            n += 0.45
        n *= 1.2
        if outline:
            group["arr"].append(((pos_x, pos_y - 1), "outline"))
    if not left:
        if is_negative:
            n2 += 0.1
        else:
            n += 0.2
        n *= 1.1
        if outline:
            group["arr"].append(((pos_x - 1, pos_y), "outline"))

    def scheme_at(cx, cy):
        i = math.floor(noise.get_noise_2d(cx, cy) * (n_colors - 1))
        return scheme[i]

    c_0 = scheme_at(col_x, pos_y)
    diff = 0.0
    for cx, cy in ((col_x, pos_y - 1), (col_x, pos_y + 1),
                   (col_x - 1, pos_y), (col_x + 1, pos_y)):
        c = scheme_at(cx, cy)
        diff += sum(abs(c_0[k] - c[k]) for k in range(3))
    if diff > 2.0:
        n += 0.3
        n *= 1.5
        n2 += 0.3
        n2 *= 1.5

    n = math.floor(max(0.0, min(1.0, n)) * (n_colors - 1))
    n2 = math.floor(max(0.0, min(1.0, n2)) * (n_colors - 1))
    return eye_scheme[int(n2)] if is_negative else scheme[int(n)]


# --- GroupDrawer.gd / CellDrawer.gd

def _touching(g1, g2):
    for (p1, _c1) in g1:
        for (p2, _c2) in g2:
            if p1[0] == p2[0] and abs(p1[1] - p2[1]) == 1:
                return True
            if p1[1] == p2[1] and abs(p1[0] - p2[0]) == 1:
                return True
    return False


def get_sprite(seed, size=30, n_colors=N_COLORS, outline=True, w=None,
               h=None, fill=0.48, walks=2, walk_len=100, ca_steps=N_STEPS,
               eyes=None):
    """Returns list of ((x, y), color) cells; color is an rgb tuple,
    'outline', or ('eye', rgb) for darkened eye-centre cells.

    Defaults reproduce Deep-Fold's generator; the keyword knobs (grid
    shape, fill density, walk count/length, CA steps, forced eyes) only
    retune its parameters for more alien results."""
    rng = random.Random(seed)
    w = w or size
    h = h or size
    grid = _generate_new(rng, w, h, fill, walks, walk_len)
    grid = _do_steps(grid, w, h, ca_steps)
    scheme = _generate_new_colorscheme(rng, n_colors)
    eye_scheme = _generate_new_colorscheme(rng, n_colors)
    groups, negative_groups = _fill_colors(
        rng, grid, w, h, scheme, eye_scheme, n_colors, outline)

    largest = 0
    for g in groups:
        largest = max(largest, len(g["arr"]))

    kept = [g for g in groups if len(g["arr"]) >= largest * 0.25]

    cells = []
    for g in kept:
        cells.extend(g["arr"])

    for g in negative_groups:
        if not g["valid"]:
            continue
        if not any(_touching(g["arr"], g2["arr"]) for g2 in kept):
            continue
        if eyes is None:
            is_eye = (len(g["arr"]) + len(negative_groups)) % 5 >= 3
        else:
            is_eye = eyes
        cells.extend(g["arr"])
        if is_eye:
            pts = [p for (p, _c) in g["arr"]]
            ax = sum(p[0] for p in pts) / len(pts)
            ay = sum(p[1] for p in pts) / len(pts)
            cutoff = math.sqrt(len(pts)) * 0.3
            for (p, c) in g["arr"]:
                if math.hypot(p[0] - ax, p[1] - ay) < cutoff:
                    cells.append((p, ("eye", c)))
    return cells


def get_groups(seed, size=30, n_colors=N_COLORS, outline=True, w=None,
               h=None, fill=0.48, walks=2, walk_len=100, ca_steps=N_STEPS,
               eyes=None):
    """Like get_sprite but keeps the flood-fill groups separate, the way
    the generator's Godot drawer does: each connected part is its own
    group so it can be animated independently.  Valid negative groups
    (holes/eyes) are attached to the kept group they touch so they move
    with it.  Returns a list of {"cells": [((x, y), col)]} dicts."""
    rng = random.Random(seed)
    w = w or size
    h = h or size
    grid = _generate_new(rng, w, h, fill, walks, walk_len)
    grid = _do_steps(grid, w, h, ca_steps)
    scheme = _generate_new_colorscheme(rng, n_colors)
    eye_scheme = _generate_new_colorscheme(rng, n_colors)
    groups, negative_groups = _fill_colors(
        rng, grid, w, h, scheme, eye_scheme, n_colors, outline)

    largest = 0
    for g in groups:
        largest = max(largest, len(g["arr"]))
    kept = [{"cells": list(g["arr"])} for g in groups
            if len(g["arr"]) >= largest * 0.25]

    for g in negative_groups:
        if not g["valid"]:
            continue
        parent = None
        for k in kept:
            if _touching(g["arr"], k["cells"]):
                parent = k
                break
        if parent is None:
            continue
        if eyes is None:
            is_eye = (len(g["arr"]) + len(negative_groups)) % 5 >= 3
        else:
            is_eye = eyes
        parent["cells"].extend(g["arr"])
        if is_eye:
            pts = [p for (p, _c) in g["arr"]]
            ax = sum(p[0] for p in pts) / len(pts)
            ay = sum(p[1] for p in pts) / len(pts)
            cutoff = math.sqrt(len(pts)) * 0.3
            for (p, c) in g["arr"]:
                if math.hypot(p[0] - ax, p[1] - ay) < cutoff:
                    parent["cells"].append((p, ("eye", c)))
    return kept


def render_frames(seed, out_w, out_h, cell=2, frames=4, dark=False,
                  **knobs):
    """Render a generated creature as idle-animation frames.

    Each connected part bobs on its own sine phase (one cell of
    amplitude), sliding over its neighbours like the generator's
    animated showcase.  Cells are drawn as cell x cell blocks; tones
    are luminance-quantized to ordered dither.  Returns a list of
    Canvas frames, bottom-centre aligned."""
    groups = get_groups(seed, **knobs)
    if not groups:
        return [Canvas(out_w, out_h) for _ in range(frames)]

    def lum_of(col):
        return 0.2126 * col[0] + 0.7152 * col[1] + 0.0722 * col[2]

    lums = [lum_of(col) for g in groups for (_p, col) in g["cells"]
            if col != "outline" and not (isinstance(col, tuple)
                                         and col[0] == "eye")]
    lo, hi = min(lums), max(lums)
    span = (hi - lo) or 1.0

    all_pts = [p for g in groups for (p, _c) in g["cells"]]
    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    ox = (out_w - (max_x - min_x + 1) * cell) // 2 - min_x * cell
    oy = out_h - cell - (max_y + 2) * cell  # bottom-aligned, wobble margin

    # big parts drawn first so small parts slide over them
    order = sorted(range(len(groups)),
                   key=lambda i: -len(groups[i]["cells"]))
    out = []
    for f in range(frames):
        c = Canvas(out_w, out_h)
        for gi in order:
            g = groups[gi]
            amp = 1
            phase = gi * 2.399
            dy = round(amp * math.sin(2 * math.pi * f / frames + phase))
            for (x, y), col in g["cells"]:
                px = x * cell + ox
                py = (y + dy) * cell + oy
                if col == "outline":
                    v = BLACK
                elif isinstance(col, tuple) and col[0] == "eye":
                    v = WHITE if dark else BLACK
                else:
                    lum = (lum_of(col) - lo) / span
                    if dark:
                        # dark species: mostly solid with dither glints
                        level = 16 if lum < 0.55 else (12 if lum < 0.8 else 8)
                    else:
                        # mostly white body, shade only the darkest tones
                        level = 0 if lum > 0.35 else (4 if lum > 0.15 else 8)
                    # dither in cell coords so tone blocks stay chunky
                    v = dither_at(x, y, level) if level > 0 else WHITE
                for yy in range(py, py + cell):
                    for xx in range(px, px + cell):
                        c.set(xx, yy, v)
        out.append(c)
    return out


def _proper_eyes(c):
    """Stamp two symmetric, readable eyes (white sclera + dark pupil)
    into the head region of the rendered sprite."""
    body_rows = {}
    for y in range(SIZE):
        xs = [x for x in range(SIZE) if c.get(x, y) != CLEAR]
        if xs:
            body_rows[y] = (min(xs), max(xs))
    if not body_rows:
        return
    ys = sorted(body_rows)
    top, bottom = ys[0], ys[-1]
    target = top + max(2, (bottom - top) * 25 // 100)
    for y in range(target, min(bottom - 4, target + 10)):
        if y not in body_rows or y + 3 not in body_rows:
            continue
        x0, x1 = body_rows[y]
        span = x1 - x0
        if span < 9:
            continue
        cx = (x0 + x1) / 2.0
        off = max(3, span // 5 + 1)
        lx = int(cx - off) - 1
        rx = int(cx + off) - 2
        if lx < x0 or rx + 3 > x1:
            off = span // 4
            lx = int(cx - off) - 1
            rx = int(cx + off) - 2
            if lx < x0 or rx + 3 > x1:
                continue
        for ex in (lx, rx):
            for dy in range(4):
                for dx in range(4):
                    edge = dx in (0, 3) or dy in (0, 3)
                    c.set(ex + dx, y + dy, BLACK if edge else WHITE)
            c.set(ex + 1, y + 2, BLACK)
            c.set(ex + 2, y + 2, BLACK)
        return


def generate(seed, size=30, proper_eyes=False, **knobs):
    """Render a generated sprite into a SIZE x SIZE 1-bit Canvas."""
    if proper_eyes:
        knobs.setdefault("eyes", False)
    cells = get_sprite(seed, size, **knobs)
    c = Canvas(SIZE, SIZE)
    if not cells:
        return c
    xs = [p[0] for (p, _col) in cells]
    ys = [p[1] for (p, _col) in cells]
    ext = max(max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    if ext > SIZE:
        # generated on a larger grid: nearest-neighbour downscale
        f = SIZE / ext
        cells = [((int(p[0] * f), int(p[1] * f)), col) for (p, col) in cells]
        xs = [p[0] for (p, _col) in cells]
        ys = [p[1] for (p, _col) in cells]
    ox = (SIZE - (max(xs) - min(xs) + 1)) // 2 - min(xs)
    oy = (SIZE - (max(ys) - min(ys) + 1)) // 2 - min(ys)

    def put(x, y, v):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            c.set(x, y, v)

    for (x, y), col in cells:
        if col == "outline":
            put(x + ox, y + oy, BLACK)
    def lum_of(col):
        return 0.2126 * col[0] + 0.7152 * col[1] + 0.0722 * col[2]

    lums = [lum_of(col) for (_p, col) in cells
            if col != "outline" and not (isinstance(col, tuple)
                                         and col[0] == "eye")]
    lo, hi = min(lums), max(lums)
    span = (hi - lo) or 1.0

    for (x, y), col in cells:
        if col == "outline":
            continue
        if isinstance(col, tuple) and col[0] == "eye":
            put(x + ox, y + oy, BLACK)
            continue
        # contrast-stretch, then quantize to 5 tones so regions stay
        # flat and readable in 1-bit
        lum = (lum_of(col) - lo) / span
        level = round((1.0 - lum) * 2) * 2
        put(x + ox, y + oy,
            dither_at(x, y, level) if level > 0 else WHITE)
    if proper_eyes:
        _proper_eyes(c)
    return c
