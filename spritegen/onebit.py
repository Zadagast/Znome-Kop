"""1-bit renderer for generator output.

Turns the cell groups from generator.py into idle-animation frames on
a tiny self-contained canvas (pixel values: 0 transparent, 1 white,
2 black), using ordered dithering so the output stays crisp on 1-bit
displays like the Playdate's.
"""

import math

from .generator import get_groups

CLEAR, WHITE, BLACK = 0, 1, 2

# Ordered 4x4 Bayer matrix; a pixel is black when bayer[y][x] < level.
BAYER = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def dither_at(x, y, level):
    """Return WHITE/BLACK for position (x, y) at density level 0..16."""
    if level <= 0:
        return WHITE
    if level >= 16:
        return BLACK
    return BLACK if BAYER[y % 4][x % 4] < level else WHITE


class Canvas:
    def __init__(self, w, h, fill=CLEAR):
        self.w = w
        self.h = h
        self.px = [[fill] * w for _ in range(h)]

    def set(self, x, y, v):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = v

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return CLEAR


def render_frames(seed, out_w, out_h, cell=2, frames=4, dark=False,
                  **knobs):
    """Render a generated creature as idle-animation frames.

    Each connected part bobs on its own sine phase (one cell of
    amplitude), sliding over its neighbours like the generator's
    animated showcase.  Cells are drawn as cell x cell blocks; tones
    are luminance-quantized to ordered dither (dark=True inverts to a
    mostly-black creature).  Returns a list of Canvas frames,
    bottom-centre aligned."""
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
