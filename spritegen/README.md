# spritegen

Procedural 1-bit creature sprites with per-part idle animation.
Self-contained Python package — copy this folder into any project.
Core needs only the standard library; Pillow is required just for the
CLI / image export.

Based on [Deep-Fold's SpriteGenerator](https://github.com/Deep-Fold/SpriteGenerator)
(MIT): mirrored random maps grown by cellular automata, flood-fill
parts, hole-eyes, cosine colour schemes and noise shading. On top of
that, each connected part is kept as its own group and bobs on its own
sine phase across the idle frames, so parts slide over each other like
the generator's animated showcase — then everything is rendered to
crisp ordered-dither 1-bit (Playdate-friendly).

## Python API

```python
from spritegen import render_frames

# 4 idle frames, 96x96 px, generated on a 24x22 grid, forced eyes
frames = render_frames(seed=4, out_w=96, out_h=96,
                       w=24, h=22, eyes=True)
for frame in frames:
    frame.px  # rows of 0 (transparent), 1 (white), 2 (black)
```

Knobs (all optional): `w`/`h` grid shape, `cell` pixels per grid cell
(default 2), `frames` (default 4), `dark=True` for a mostly-black
creature, `eyes=True/False/None` to force/forbid/let-the-generator-pick
hole-eyes, plus generator tuning `fill`, `walks`, `walk_len`,
`ca_steps`.

Lower-level: `get_groups(seed, ...)` returns the raw connected parts
(`[{"cells": [((x, y), color)]}]`) if you want to animate or colour
them yourself, e.g. in a colour game.

## CLI

```sh
# animated preview
python3 -m spritegen --seed 4 --grid 24x22 --scale 4 --out creature.gif

# 4-frame sheet (transparent PNG, e.g. for a Playdate image table)
python3 -m spritegen --seed 4 --grid 24x22 --size 96x96 --out sheet.png

# board of seeds 0..19 to pick from
python3 -m spritegen --board 20 --grid 32x36 --out board.png
```

Tips: small grids (`20x20`-ish) give cute base forms, tall/large grids
(`30x38`+) give bigger evolved-looking creatures; `--dark` suits
void/shadow types; pick seeds from a `--board` render.
