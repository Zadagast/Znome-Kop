"""Tiny 1-bit drawing canvas used by the art generator.

Pixel values: 0 = transparent, 1 = white, 2 = black.
All shading is ordered dithering so the output stays crisp on the
Playdate's 1-bit display.
"""

CLEAR, WHITE, BLACK = 0, 1, 2

# Ordered 4x4 Bayer matrix; a pixel is black when bayer[y][x] < level.
BAYER = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)

# Density presets, expressed as "how many of 16 pixels are black".
DENSITY = {
    "white": 0,
    "d12": 2,
    "d25": 4,
    "d50": 8,
    "d75": 12,
    "black": 16,
}


def dither_at(x, y, density):
    """Return WHITE/BLACK for world position (x, y) at the given density."""
    level = DENSITY[density] if isinstance(density, str) else density
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

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, v):
        if self.inside(x, y):
            self.px[y][x] = v

    def get(self, x, y):
        return self.px[y][x] if self.inside(x, y) else CLEAR

    def fill(self, v):
        self.rect(0, 0, self.w, self.h, v)

    def rect(self, x, y, w, h, v):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, v)

    def dither_rect(self, x, y, w, h, density, origin=(0, 0)):
        ox, oy = origin
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, dither_at(xx + ox, yy + oy, density))

    def outline_rect(self, x, y, w, h, v=BLACK):
        self.hline(x, x + w - 1, y, v)
        self.hline(x, x + w - 1, y + h - 1, v)
        self.vline(x, y, y + h - 1, v)
        self.vline(x + w - 1, y, y + h - 1, v)

    def hline(self, x0, x1, y, v=BLACK):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.set(x, y, v)

    def vline(self, x, y0, y1, v=BLACK):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, y, v)

    def line(self, x0, y0, x1, y1, v=BLACK):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, v)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def blit(self, other, x, y, skip_clear=True):
        for yy in range(other.h):
            for xx in range(other.w):
                v = other.px[yy][xx]
                if skip_clear and v == CLEAR:
                    continue
                self.set(x + xx, y + yy, v)

    def sub(self, x, y, w, h):
        out = Canvas(w, h)
        for yy in range(h):
            for xx in range(w):
                out.px[yy][xx] = self.get(x + xx, y + yy)
        return out

    def flip_h(self):
        out = Canvas(self.w, self.h)
        for y in range(self.h):
            out.px[y] = list(reversed(self.px[y]))
        return out

    def is_blank(self):
        return all(v == CLEAR for row in self.px for v in row)


ASCII_MAP = {
    ".": CLEAR,
    " ": WHITE,
    "o": WHITE,
    "#": BLACK,
    "-": "d25",
    "+": "d50",
    "=": "d75",
}


def from_ascii(rows):
    """Build a canvas from ASCII art. See ASCII_MAP for the character set."""
    h = len(rows)
    w = max(len(r) for r in rows)
    c = Canvas(w, h)
    for y, row in enumerate(rows):
        for x in range(w):
            ch = row[x] if x < len(row) else "."
            v = ASCII_MAP[ch]
            c.px[y][x] = dither_at(x, y, v) if isinstance(v, str) else v
    return c


def from_png(path):
    """Load a 1-bit RGBA PNG (as written by convert_packs.py) into a Canvas."""
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    c = Canvas(img.width, img.height)
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            c.px[y][x] = BLACK if r < 128 else WHITE
    return c


def write_sheet(path, frames, cols, cell_w, cell_h):
    """Write frames into a grid PNG that pdc reads as an image table."""
    from PIL import Image

    rows = (len(frames) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cell_w, rows * cell_h), (0, 0, 0, 0))
    pixels = img.load()
    for i, frame in enumerate(frames):
        ox = (i % cols) * cell_w
        oy = (i // cols) * cell_h
        for y in range(cell_h):
            for x in range(cell_w):
                v = frame.get(x, y)
                if v == CLEAR:
                    continue
                shade = 255 if v == WHITE else 0
                pixels[ox + x, oy + y] = (shade, shade, shade, 255)
    img.save(path)
