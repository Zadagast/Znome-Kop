"""spritegen - procedural 1-bit creature sprites with part animation.

Self-contained (stdlib only; Pillow needed just for the CLI/image
helpers).  Port of Deep-Fold's SpriteGenerator (MIT) plus a 1-bit
renderer that keeps each connected part as its own group and bobs it
on its own sine phase, so parts slide over each other across the idle
frames.

Typical use:

    from spritegen import render_frames
    frames = render_frames(seed=4, out_w=96, out_h=96,
                           w=24, h=22, eyes=True)

Each frame is a Canvas whose .px rows hold 0 (transparent), 1 (white)
or 2 (black).  See README.md and `python3 -m spritegen --help`.
"""

from .generator import get_groups, get_sprite
from .onebit import BLACK, CLEAR, WHITE, Canvas, dither_at, render_frames

__all__ = [
    "get_groups", "get_sprite", "render_frames",
    "Canvas", "dither_at", "CLEAR", "WHITE", "BLACK",
]
