"""Seed-picking board for the group-wobble Deep-Fold generator."""

import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spritegen import render_frames

# name, dark, knobs
CONFIGS = [
    ("rubblin", False, dict(w=24, h=22, eyes=True)),
    ("cragnome", False, dict(w=32, h=36, eyes=True)),
    ("frostpod", False, dict(w=24, h=24, ca_steps=3, eyes=True)),
    ("cryonaut", False, dict(w=26, h=40, eyes=True)),
    ("sparklet", False, dict(w=22, h=24, walks=3, eyes=True)),
    ("arcfang", False, dict(w=32, h=34, eyes=True)),
    ("tinplate", False, dict(w=24, h=22, ca_steps=5, eyes=True)),
    ("ferrox", False, dict(w=36, h=34, eyes=True)),
    ("mycomite", False, dict(w=26, h=24, eyes=True)),
    ("bloomshade", False, dict(w=30, h=38, eyes=True)),
    ("nullet", True, dict(w=20, h=20, eyes=True)),
    ("vantabeast", True, dict(w=38, h=38, eyes=True)),
]

RGB = {0: (200, 200, 200), 1: (255, 255, 255), 2: (0, 0, 0)}

OUT = 96


def to_img(c):
    im = Image.new("RGB", (c.w, c.h))
    im.putdata([RGB[v] for row in c.px for v in row])
    return im


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    board = Image.new("RGB", (OUT * n_seeds, OUT * len(CONFIGS)),
                      (200, 200, 200))
    for row, (name, dark, knobs) in enumerate(CONFIGS):
        for s in range(n_seeds):
            f = render_frames(s, OUT, OUT, dark=dark, frames=1, **knobs)[0]
            board.paste(to_img(f), (s * OUT, row * OUT))
    board.save("/tmp/group_board.png")
    print("rows:", [c[0] for c in CONFIGS])


if __name__ == "__main__":
    main()
