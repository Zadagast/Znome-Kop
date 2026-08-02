"""Deterministic converter for the AI-generated art in tools/ai_raw/.

Raw assets are generated with a frontier image model (see
.agents/skills/ai-art/SKILL.md for the prompts and workflow):

- character sheets: 2x2 grids on solid magenta (#FF00FF), cells are
  idle + three right-facing walk frames;
- scene backdrops: 1536x1024 monochrome side-scroller scenes.

This script is the deterministic half of the pipeline (chroma-key,
crop, downscale, 1-bit threshold, halo, sheet assembly):

  hero-table-<w>-<h>.png   male model, 4 frames
  heroine-table-<w>-<h>.png female model, 4 frames
  scenes/scene-*.png       400x240 1-bit backdrops

Requires Pillow.  Run: python3 tools/ai_convert.py
"""

import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "tools", "ai_raw")
IMAGES = os.path.join(ROOT, "source", "images")

SPRITE_H = 72  # body height before 1px halo padding
BLACK = 120  # luminance threshold for interior black detail


def extract_cells(path, target_h=SPRITE_H):
    """Chroma-key a 2x2 magenta sheet into 4 RGBA 1-bit sprites."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    cw, ch = w // 2, h // 2
    out = []
    for cy in range(2):
        for cx in range(2):
            cell = img.crop((cx * cw, cy * ch, (cx + 1) * cw, (cy + 1) * ch))
            out.append(extract_sprite(cell, target_h))
    return out


def extract_sprite(cell, target_h):
    p = cell.load()
    w, h = cell.size
    fg = [[not (p[x, y][0] > 150 and p[x, y][2] > 150 and p[x, y][1] < 120)
           for x in range(w)] for y in range(h)]
    xs = [x for y in range(h) for x in range(w) if fg[y][x]]
    ys = [y for y in range(h) for x in range(w) if fg[y][x]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cwd, chg = x1 - x0 + 1, y1 - y0 + 1
    ph = target_h
    pw = max(1, round(cwd * ph / chg))
    crop = cell.crop((x0, y0, x1 + 1, y1 + 1)).convert("L") \
        .resize((pw, ph), Image.LANCZOS)
    m = Image.new("L", (cwd, chg), 0)
    mp = m.load()
    for y in range(chg):
        for x in range(cwd):
            if fg[y0 + y][x0 + x]:
                mp[x, y] = 255
    mm = m.resize((pw, ph), Image.LANCZOS).load()
    cp = crop.load()
    mask = [[mm[x, y] > 127 for x in range(pw)] for y in range(ph)]
    spr = Image.new("RGBA", (pw + 2, ph + 2), (0, 0, 0, 0))
    sp = spr.load()
    for y in range(ph):
        for x in range(pw):
            if not mask[y][x]:
                continue
            edge = any(not (0 <= x + dx < pw and 0 <= y + dy < ph
                            and mask[y + dy][x + dx])
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            sp[x + 1, y + 1] = (0, 0, 0, 255) \
                if (edge or cp[x, y] < BLACK) else (255, 255, 255, 255)
    # 1px white halo so characters pop against dark backdrops
    pw2, ph2 = pw + 2, ph + 2
    halo = []
    for y in range(ph2):
        for x in range(pw2):
            if sp[x, y][3] == 0 and any(
                    0 <= x + dx < pw2 and 0 <= y + dy < ph2
                    and sp[x + dx, y + dy][3] == 255
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                halo.append((x, y))
    for x, y in halo:
        sp[x, y] = (255, 255, 255, 255)
    return spr


def sheet(frames, name):
    """Bottom-center anchor frames into a fixed-cell Playdate imagetable."""
    cw = max(f.width for f in frames)
    if cw % 2:
        cw += 1
    chg = max(f.height for f in frames)
    img = Image.new("RGBA", (cw * len(frames), chg), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.paste(f, (i * cw + (cw - f.width) // 2, chg - f.height), f)
    out = os.path.join(IMAGES, "%s-table-%d-%d.png" % (name, cw, chg))
    for old in os.listdir(IMAGES):
        if old.startswith(name + "-table-") and old.endswith(".png"):
            os.remove(os.path.join(IMAGES, old))
    img.save(out)
    print("wrote", out)


def scene(src, name):
    im = Image.open(os.path.join(RAW, src)).convert("L") \
        .resize((400, 240), Image.LANCZOS)
    im = im.point(lambda v: 255 if v >= 128 else 0).convert("1")
    out = os.path.join(IMAGES, "scenes", "scene-%s.png" % name)
    im.save(out)
    print("wrote", out)


def main():
    os.makedirs(os.path.join(IMAGES, "scenes"), exist_ok=True)
    sheet(extract_cells(os.path.join(RAW, "gen_male_sheet.png")), "hero")
    sheet(extract_cells(os.path.join(RAW, "gen_female_sheet.png")), "heroine")
    scene("world_lab.png", "lab")
    scene("world_colony.png", "colony")
    scene("world_flats.png", "flats")
    scene("world_canyon.png", "canyon")


if __name__ == "__main__":
    main()
