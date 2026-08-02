"""32x32 Znome battle sprites from the Deep-Fold generator port.

Each species is a hand-picked seed fed straight to znome_gen (a faithful
Python port of Deep-Fold's MIT SpriteGenerator); no per-species masks or
edits, only seed selection.
"""

from znome_gen import generate

SIZE = 32

SEEDS = [
    ("rubblin", 39),
    ("cragnome", 34),
    ("frostpod", 23),
    ("cryonaut", 27),
    ("sparklet", 63),
    ("arcfang", 11),
    ("tinplate", 66),
    ("ferrox", 84),
    ("mycomite", 62),
    ("bloomshade", 97),
    ("nullet", 30),
    ("vantabeast", 4),
]

ZNOMES = [(name, lambda s=seed: generate(s, proper_eyes=True))
          for name, seed in SEEDS]
