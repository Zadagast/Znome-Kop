"""Character part rig builder.

Takes a 2x2 chunky-pixel-art part sheet (head / torso / arm / leg on
magenta, see .agents/skills/ai-art/SKILL.md), snaps each part onto its
true pixel grid so nothing is ever resampled, and writes the part
imagetable plus the pivot offsets the game rig animates with
(source/scripts/game/herorig.lua).

    python3 tools/ai_rig.py
    python3 tools/rig_preview.py   # see the walk without a Playdate
"""

import os

from PIL import Image

from ai_convert import IMAGES, RAW

ROOT_SCRIPTS = os.path.join(os.path.dirname(IMAGES), "scripts")


def snap_to_pixel_grid(cell, lo=48, hi=140):
    """Collapse an AI 'chunky pixel art' cell onto its true pixel grid.

    The model draws big square blocks; we find the grid resolution whose
    blocks are most uniform and take a majority vote per block, which gives
    crisp two-colour pixels instead of the mush a plain downscale produces.
    """
    rgb = cell.convert("RGB")
    w, h = rgb.size
    p = rgb.load()
    kinds = [[0] * w for _ in range(h)]  # 0 background, 1 white, 2 black
    for y in range(h):
        for x in range(w):
            r, g, b = p[x, y]
            if r > 150 and b > 150 and g < 120:
                kinds[y][x] = 0
            elif r + g + b < 330:
                kinds[y][x] = 2
            else:
                kinds[y][x] = 1

    best, best_score = None, -1.0
    for n in range(lo, hi + 1):
        step = w / n
        if step < 4:
            continue
        pure, blocks = 0.0, 0
        for by in range(0, n, 2):
            for bx in range(0, n, 2):
                counts = [0, 0, 0]
                x0, x1 = int(bx * step), max(int(bx * step) + 1,
                                             int((bx + 1) * step))
                y0, y1 = int(by * step), max(int(by * step) + 1,
                                             int((by + 1) * step))
                for y in range(y0, min(y1, h)):
                    for x in range(x0, min(x1, w)):
                        counts[kinds[y][x]] += 1
                total = sum(counts)
                if total:
                    pure += max(counts) / total
                    blocks += 1
        score = pure / max(1, blocks)
        if score > best_score:
            best, best_score = n, score
    n = best
    step = w / n
    out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    op = out.load()
    for by in range(n):
        for bx in range(n):
            counts = [0, 0, 0]
            x0, x1 = int(bx * step), max(int(bx * step) + 1,
                                         int((bx + 1) * step))
            y0, y1 = int(by * step), max(int(by * step) + 1,
                                         int((by + 1) * step))
            for y in range(y0, min(y1, h)):
                for x in range(x0, min(x1, w)):
                    counts[kinds[y][x]] += 1
            kind = counts.index(max(counts))
            op[bx, by] = ((0, 0, 0, 0), (255, 255, 255, 255),
                          (0, 0, 0, 255))[kind]
    return out


def crop_opaque(img):
    p = img.load()
    xs = [x for y in range(img.height) for x in range(img.width)
          if p[x, y][3]]
    ys = [y for y in range(img.height) for x in range(img.width)
          if p[x, y][3]]
    return img.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))


def anchored(img, ax, ay):
    """Pad so (ax, ay) sits at the image center and the part still fits when
    rotated about it (square canvas of the swing radius)."""
    w, h = img.size
    left = max(0, round(w - 2 * ax))
    right = max(0, round(2 * ax - w))
    top = max(0, round(h - 2 * ay))
    bottom = max(0, round(2 * ay - h))
    out = Image.new("RGBA", (w + left + right, h + top + bottom), (0, 0, 0, 0))
    out.paste(img, (left, top), img)
    side = max(out.size) + 2
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(out, ((side - out.width) // 2, (side - out.height) // 2), out)
    return square


def load_pixel_parts(path):
    """Parts from a chunky-pixel-art sheet, snapped to their true grid so no
    resampling is needed: what the model drew is what ships."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    cells = [img.crop((cx * w // 2, cy * h // 2,
                       (cx + 1) * w // 2, (cy + 1) * h // 2))
             for cy in range(2) for cx in range(2)]
    return [crop_opaque(snap_to_pixel_grid(c, 24, 70)) for c in cells]


def export_parts(src, name):
    """Ship head/torso/arm/leg as an imagetable plus a Lua rig description,
    so the walk can be composed at runtime instead of baked."""
    head, torso, arm, leg = load_pixel_parts(os.path.join(RAW, src))
    th, lh = torso.height, leg.height
    hip_overlap = lh * 0.10
    torso_y = head.height * 0.92
    shoulder_y = torso_y + th * 0.10
    hip_y = torso_y + th - hip_overlap
    body_h = hip_y + lh
    s = 1.0  # native pixel art: never resample

    parts = {
        # head seats into the collar: its base overlaps the torso top
        "head": (head, head.width / 2, head.height / 2,
                 torso.width * 0.10,
                 torso_y - head.height * 0.5 + head.height * 0.12),
        "torso": (torso, torso.width / 2, torso.height / 2,
                  0.0, torso_y + th * 0.5),
        "arm": (arm, arm.width / 2, arm.height * 0.08, 0.0, shoulder_y),
        "leg": (leg, leg.width / 2, leg.height * 0.08, 0.0, hip_y),
    }
    order = ("head", "torso", "arm", "leg")
    cells = {}
    for key in order:
        img, ax, ay = parts[key][0], parts[key][1], parts[key][2]
        cells[key] = anchored(img, ax * s, ay * s)
    cw = max(c.width for c in cells.values())
    ch = max(c.height for c in cells.values())
    if cw % 2:
        cw += 1
    if ch % 2:
        ch += 1
    table = Image.new("RGBA", (cw * len(order), ch), (0, 0, 0, 0))
    for i, key in enumerate(order):
        c = cells[key]
        table.paste(c, (i * cw + (cw - c.width) // 2, (ch - c.height) // 2), c)
    out = os.path.join(IMAGES, "%s-table-%d-%d.png" % (name, cw, ch))
    for old in os.listdir(IMAGES):
        if old.startswith(name + "-table-") and old.endswith(".png"):
            os.remove(os.path.join(IMAGES, old))
    table.save(out)
    print("wrote", out)

    lua = [
        "-- Generated by tools/ai_rig.py. Do not edit by hand.",
        "-- Offsets are in pixels from the character's feet-center anchor.",
        "",
        "HeroRig = {",
        "\theight = %d," % round(body_h),
        "\tframes = { head = 1, torso = 2, arm = 3, leg = 4 },",
    ]
    for key in order:
        _, _, _, ox, oy = parts[key]
        lua.append("\t%s = { x = %d, y = %d }," % (
            key, round(ox * s), round((oy - body_h) * s)))
    # limbs sit either side of the body, offset from the torso's own width so
    # the near ones read in front of it and the far ones peek out behind
    lua.append("\thipSpread = %d," % round(torso.width * 0.12 * s))
    lua.append("\tshoulderSpread = %d," % round(torso.width * 0.16 * s))
    lua.append("}")
    lua.append("")
    path = os.path.join(ROOT_SCRIPTS, "game", "herorig.lua")
    with open(path, "w") as f:
        f.write("\n".join(lua))
    print("wrote", path)


def main():
    export_parts("gen_male_parts_px.png", "heroparts")


if __name__ == "__main__":
    main()
