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

## Character part sheet contract (every character is a rig)

Nobody is a drawn walk cycle: each character is drawn once as four parts
and the game rotates them every frame. Raw files
`tools/ai_raw/gen_<role>_parts_px.png`, listed in `CHARACTERS` in
`tools/ai_rig.py`, built with `python3 tools/ai_rig.py` and previewed
off-device with `python3 tools/rig_preview.py <character>`.

Prompt contract — 1024x1024, 2x2 grid on solid magenta `#FF00FF`, nothing
else in the image (no ground line, labels or grid lines):

- **True low-resolution pixel art**: large visible square pixel blocks
  (~22 screen px each), hard aligned edges, no anti-aliasing, blur,
  gradients or dithering. Pure black and pure white only. This matters:
  the converter snaps each cell onto its pixel grid by majority vote, so
  nothing is ever resampled and the art stays crisp. Smooth painted art
  downscales into mush and nubby outlines.
- Same character in every cell, side view facing right, matching scale.
- top-left head only (helmet, face, hair, small neck stub, ~22 blocks
  tall); top-right torso only (chest, belt, backpack; flat shoulders and
  hips; no head/arms/legs; ~24 tall, ~14 wide); bottom-left one arm,
  vertical, shoulder to glove (~24 tall, 5 wide); bottom-right one leg,
  vertical, hip to boot (~30 tall, 7 wide).

**New characters: edit the hero sheet, don't prompt from scratch.** Pass
`tools/ai_raw/gen_male_parts_px.png` as an input image and ask for the
identity to change (face, suit, gloves, boots) while keeping every part's
silhouette, size and cell position identical. Sheets prompted from
scratch come back with their own proportions and look goofy next to the
hero even after height normalisation.

`tools/ai_rig.py` writes `source/images/<name>parts-table-*.png` per
character plus all the pivot offsets in `source/scripts/game/rigs.lua`,
normalising everyone to `BODY_H` px tall by re-snapping on a scaled grid.
`source/scripts/game/rig.lua` composes them at runtime: `Rig.draw(name,
px, groundY, moving, t, face)`; standing characters breathe, walking ones
scissor their legs and swing their arms.

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
