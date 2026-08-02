# AI art pipeline (characters + scene backdrops)

All player/NPC sprites and side-scroller scene backdrops are made with a
frontier image-generation model (GPT image gen or similar) plus the
deterministic converter `tools/ai_convert.py`. Any agent with image
generation — or a human using any image AI (ChatGPT, Gemini, etc.) —
can produce matching assets by following this contract.

## Workflow

1. Generate a raw PNG with one of the prompt templates below.
2. Save it into `tools/ai_raw/` (character sheets: `gen_<name>_sheet.png`;
   scenes: `world_<name>.png`).
3. Run `python3 tools/ai_convert.py` (requires Pillow). It chroma-keys,
   crops, downscales, 1-bit converts and writes game-ready assets into
   `source/images/`.
4. New scenes must be registered in `SCENES` in
   `source/scripts/core/assets.lua` and given a room entry in
   `source/scripts/game/sidescroller.lua`; new character sheets need a
   `sheet(...)` call in `tools/ai_convert.py`.

## Character part sheet contract (preferred: rig-baked animation)

The hero is animated from a paper-doll part sheet baked by
`python3 tools/ai_rig.py` (rotates limbs around pivots at raw resolution,
so all frames are the exact same art). Raw file:
`tools/ai_raw/gen_male_parts.png` — a 1024x1024 2x2 grid on solid magenta
`#FF00FF`, side view facing right, consistent scale, one part per cell:
top-left head (helmet + neck stub), top-right torso (shoulders/hips flat,
no head/arms/legs), bottom-left one arm (shoulder to hand, vertical),
bottom-right one leg (hip to boot, vertical). Output table: frame 1 idle +
6 walk frames.

## Character sheet contract (legacy: pre-drawn frames)

- 1024x1024 image, 2x2 grid of equal cells.
- Solid magenta `#FF00FF` background everywhere (this is the chroma key —
  no gradients, no anti-aliased magenta edges if avoidable).
- Cell order: top-left = front-facing idle; the other three = right-facing
  walk frames (contact, passing, contact).
- One character per cell, fully inside the cell, centered, consistent
  scale and feet baseline across cells.
- Style: modern monochrome pixel art, bold black outlines, white fills
  with black interior detail. No grays.

Prompt template:

> Pixel art sprite sheet, 2x2 grid on a solid magenta #FF00FF background.
> A [male/female] Mars astronaut explorer in a fitted spacesuit with
> [visor up, short dark hair / ponytail], full body. Top-left cell:
> standing idle facing the viewer. Remaining three cells: side view
> walking animation frames facing right (contact pose, passing pose,
> contact pose). Each character fully inside its cell, same size and
> ground line in every cell. Style: crisp black and white 1-bit pixel
> art, bold black outlines, white fills, black interior detail lines,
> high contrast, no gray tones.

## Scene backdrop contract

- 1536x1024 landscape image (downscaled to 400x240 by the converter).
- Walkable flat ground strip along the bottom quarter.
- Style: bold-outline 1-bit monochrome; dither only for sky gradients and
  distant haze; strictly pure black and pure white; no characters.

Prompt template:

> Side-scrolling 2D game background scene, wide landscape format.
> [SCENE DESCRIPTION — e.g. "A Mars colony exterior: geodesic dome
> habitats, antenna towers, airlock doors, distant layered mesas"],
> flat walkable dusty ground strip along the bottom quarter. Style:
> crisp black and white 1-bit pixel art with bold black outlines, white
> and black fills, sparse deliberate dither ONLY for sky gradient and
> distant haze, clean readable shapes, modern indie monochrome pixel art
> (like Playdate console games), high contrast, no gray tones — strictly
> pure black and pure white pixels. No characters.

## Quality checks

- After conversion, view `source/images/scenes/scene-*.png` at 1x: shapes
  must stay readable after the downscale; regenerate if detail turns to
  noise.
- Character frames must not have disconnected outline fragments; the
  converter adds a 1px white halo so sprites pop against dark backdrops.
- Keep Znome generation out of this pipeline — Znomes come from
  `spritegen/` (procedural, approved) and must not be replaced by AI art.
