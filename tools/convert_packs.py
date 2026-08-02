"""Convert GB-style asset packs into the 1-bit intermediates under
tools/pack_art/ that gen_art.py assembles into the game's sheets.

Run manually when the pack sources change; the committed pack_art PNGs are
the build inputs, the raw packs themselves are NOT redistributed (see
CREDITS.md). Expects the packs unpacked under ~/assets:

  ~/assets/gb_fantasy/RPG_exterior_example.png   (Gumpy Function)
  ~/assets/scifi_SciFi_Tiles.png                 (The Pixel Nook)
  ~/assets/gb_village/GB Village/...             (Hoyb)

All three packs share the GB Studio 4-tone palette. Tones are mapped to
1-bit with ordered dithering: lightest two -> white, dark -> 50% dither,
darkest -> black. Characters skip the dither (mid tones -> white/black) so
they stay crisp at 16px.
"""

import os

from PIL import Image

HOME = os.path.expanduser("~")
PACKS = os.path.join(HOME, "assets")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pack_art")

BAYER = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)

# GB Studio palette, light -> dark.
GB = ((224, 248, 207), (134, 192, 108), (48, 104, 80), (7, 24, 33))
# Hoyb's GB Village pack uses an olive ramp instead
VILLAGE = ((196, 207, 161), (139, 149, 109), (76, 83, 60), (31, 31, 31))
GRID_GREEN = (153, 229, 80)  # guide grid in the GB Village sheets

# black fraction per tone (index into GB)
TERRAIN_LEVELS = (0.0, 0.0, 0.5, 1.0)
VILLAGE_TERRAIN_LEVELS = (0.0, 0.25, 0.5, 1.0)
ACTOR_LEVELS = (0.0, 0.0, 1.0, 1.0)


def nearest_tone(rgb, palette=GB):
    return min(range(4), key=lambda i: sum(
        (a - b) ** 2 for a, b in zip(palette[i], rgb)))


def convert(img, levels=TERRAIN_LEVELS, black_bg_transparent=False, palette=GB):
    """Map a 4-tone RGBA image to a 1-bit RGBA image (white/black/clear)."""
    img = img.convert("RGBA")
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    src, dst = img.load(), out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = src[x, y]
            if a < 128 or (r, g, b) == GRID_GREEN:
                continue
            if black_bg_transparent and (r, g, b) == (0, 0, 0):
                continue
            frac = levels[nearest_tone((r, g, b), palette)]
            dark = BAYER[y % 4][x % 4] < frac * 16
            dst[x, y] = (0, 0, 0, 255) if dark else (255, 255, 255, 255)
    return out


def crop(path, x, y, w, h):
    return Image.open(os.path.join(PACKS, path)).convert("RGBA").crop(
        (x, y, x + w, y + h))


SCIFI = "scifi_SciFi_Tiles.png"
VTILES = "gb_village/GB Village/Tiles/Tiles.png"
VBUILD = "gb_village/GB Village/Buildings and Props/Buildings.png"
VPLAYER = "gb_village/GB Village/Player/PlayerSprites.png"
VNPC = "gb_village/GB Village/NPC/NPCs.png"

# name -> (source, x, y) of a 16x16 ground/object tile (opaque terrain)
TERRAIN = {
    "dust": (VTILES, 176, 16),
    "cliff": (SCIFI, 80, 48),
    "regolith": (VTILES, 80, 96),
    "gravel": (SCIFI, 80, 64),
    "dunes": (VTILES, 96, 48),
    "plate": (SCIFI, 0, 176),
    "grate": (SCIFI, 0, 160),
    "sporegrass": (SCIFI, 80, 0),
    "sporegrass_tall": (SCIFI, 96, 16),
    "rock": (VBUILD, 160, 84),
    "ash": (SCIFI, 112, 64),
}

# name -> (source, x, y) of a 16x16 object tile (black background = clear)
OBJECTS = {
    "boulder": (SCIFI, 16, 128),
    "sign": (VBUILD, 176, 52),
    "crate": (SCIFI, 0, 48),
    "lichen": (SCIFI, 0, 80),
    "vent": (SCIFI, 0, 192),
    "marker": (SCIFI, 16, 30),
    "fence_h": (VBUILD, 80, 32),
}

# name -> (source, x, y, w, h); background transparent
SPRITES = {
    "hab": (VBUILD, 3, 4, 43, 28),
    "lab": (VBUILD, 2, 105, 51, 39),
    "airlock": (SCIFI, 64, 160, 32, 32),
    "pillar": (SCIFI, 0, 0, 16, 32),
    "solar": (SCIFI, 0, 224, 32, 32),
}

# actor -> (source, row_down, row_up, row_side); 3 cols per row, 16px cells
ACTORS = {
    "kop": (VPLAYER, 0, 1, 2),
    "colonist": (VNPC, 0, 1, 2),
    "tech": (VNPC, 0, 1, 2),  # offset by NPC block below
}
NPC_BLOCK_X = {"colonist": 0, "tech": 9}


def cell16(path, cx, cy):
    return crop(path, cx * 16, cy * 16, 16, 16)


def main():
    os.makedirs(OUT, exist_ok=True)

    for name, (src, x, y) in TERRAIN.items():
        village = src in (VTILES, VBUILD)
        cell = crop(src, x, y, 16, 16)
        pal = VILLAGE if village else GB
        base = Image.new("RGBA", cell.size, pal[0] + (255,))
        base.alpha_composite(cell)
        convert(
            base,
            levels=VILLAGE_TERRAIN_LEVELS if village else TERRAIN_LEVELS,
            palette=pal,
        ).save(os.path.join(OUT, "tile_%s.png" % name))

    for name, (src, x, y) in OBJECTS.items():
        village = src in (VTILES, VBUILD)
        convert(
            crop(src, x, y, 16, 16), black_bg_transparent=True,
            levels=ACTOR_LEVELS if village else TERRAIN_LEVELS,
            palette=VILLAGE if village else GB,
        ).save(os.path.join(OUT, "obj_%s.png" % name))

    for name, (src, x, y, w, h) in SPRITES.items():
        village = src in (VTILES, VBUILD)
        convert(
            crop(src, x, y, w, h), black_bg_transparent=True,
            palette=VILLAGE if village else GB,
        ).save(os.path.join(OUT, "spr_%s.png" % name))

    for name, (src, rd, ru, rs) in ACTORS.items():
        bx = NPC_BLOCK_X.get(name, 0)
        frames = []
        for row in (rd, ru, rs):
            for col in (1, 0):  # stand, step
                frames.append(convert(
                    cell16(src, bx + col, row), ACTOR_LEVELS, palette=VILLAGE))
        sheet = Image.new("RGBA", (16 * 6, 16), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.alpha_composite(f, (i * 16, 0))
        sheet.save(os.path.join(OUT, "actor_%s.png" % name))

    print("pack_art written to", OUT)


if __name__ == "__main__":
    main()
