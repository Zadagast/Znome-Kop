"""Battle sprites for the 12 Znome species.

Generated with the standalone spritegen package (repo root), the
faithful Deep-Fold SpriteGenerator port: mirrored random maps grown by cellular automata, flood-fill
parts, hole-eyes and noise shading.  Each species is a picked seed plus
grid-shape knobs; every connected part bobs on its own phase across
FRAMES idle frames, sliding over its neighbours like the generator's
animated showcase.  Base forms use small grids, evolved forms large
ones.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spritegen import render_frames

SIZE = 96
FRAMES = 4

# name, seed, dark, grid knobs
SPECIES = [
    ("rubblin", 4, False, dict(w=24, h=22, eyes=True)),
    ("cragnome", 6, False, dict(w=32, h=36, eyes=True)),
    ("frostpod", 5, False, dict(w=24, h=24, ca_steps=3, eyes=True)),
    ("cryonaut", 13, False, dict(w=26, h=40, eyes=True)),
    ("sparklet", 2, False, dict(w=22, h=24, walks=3, eyes=True)),
    ("arcfang", 8, False, dict(w=32, h=34, eyes=True)),
    ("tinplate", 11, False, dict(w=24, h=22, ca_steps=5, eyes=True)),
    ("ferrox", 8, False, dict(w=36, h=34, eyes=True)),
    ("mycomite", 2, False, dict(w=26, h=24, eyes=True)),
    ("bloomshade", 13, False, dict(w=30, h=38, eyes=True)),
    ("nullet", 18, True, dict(w=20, h=20, eyes=True)),
    ("vantabeast", 11, True, dict(w=38, h=38, eyes=True)),
]

ORDER = [name for name, _s, _d, _k in SPECIES]


def _frames(seed, dark, knobs):
    return render_frames(seed, SIZE, SIZE, frames=FRAMES, dark=dark, **knobs)


ZNOMES = [(name, lambda s=seed, d=dark, k=knobs: _frames(s, d, k))
          for name, seed, dark, knobs in SPECIES]
