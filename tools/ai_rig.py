"""Paper-doll walk-cycle baker.

Takes a 2x2 character part sheet (head / torso / arm / leg on magenta,
see .agents/skills/ai-art/SKILL.md) and bakes a consistent walk cycle by
rotating limbs around their pivots at raw resolution, so every frame is
the exact same art. Output goes through the same 1-bit conversion as
tools/ai_convert.py.

    python3 tools/ai_rig.py
"""

import math
import os

from PIL import Image

from ai_convert import (
    IMAGES, RAW, SPRITE_H, extract_sprite, keep_largest_component, sheet,
)

MAGENTA = (255, 0, 255)
ROOT_SCRIPTS = os.path.join(os.path.dirname(IMAGES), "scripts")


def load_parts(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    cw, ch = w // 2, h // 2
    cells = [img.crop((cx * cw, cy * ch, (cx + 1) * cw, (cy + 1) * ch))
             for cy in range(2) for cx in range(2)]
    head, torso, arm, leg = (trim(c) for c in cells)
    return head, torso, arm, leg


def trim(cell):
    """Crop a part to its non-magenta bounding box, magenta background kept."""
    p = cell.load()
    w, h = cell.size
    rows = [0] * h
    cols = [0] * w
    for y in range(h):
        for x in range(w):
            r, g, b = p[x, y]
            if not (r > 150 and b > 150 and g < 120):
                rows[y] += 1
                cols[x] += 1
    ys = [y for y in range(h) if rows[y] >= 3]
    xs = [x for x in range(w) if cols[x] >= 3]
    return cell.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))


def rgba(part):
    """Magenta -> transparent; keep only the main blob and crop to it."""
    out = part.convert("RGBA")
    p = out.load()
    w, h = out.size
    fg = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, _ = p[x, y]
            if r > 150 and b > 150 and g < 120:
                p[x, y] = (0, 0, 0, 0)
            else:
                fg[y][x] = True
    keep_largest_component(fg, w, h)
    xs = [x for y in range(h) for x in range(w) if fg[y][x]]
    ys = [y for y in range(h) for x in range(w) if fg[y][x]]
    for y in range(h):
        for x in range(w):
            if not fg[y][x]:
                p[x, y] = (0, 0, 0, 0)
    return out.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))


def swung(part, deg):
    """Rotate a limb around its top-center pivot."""
    pad = part.height // 2
    canvas = Image.new("RGBA", (part.width + 2 * pad, part.height + pad),
                       (0, 0, 0, 0))
    canvas.paste(part, (pad, 0), part)
    pivot = (canvas.width / 2, part.height * 0.08)
    out = canvas.rotate(deg, center=pivot, resample=Image.BICUBIC)
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = p[x, y]
            p[x, y] = (r, g, b, 255) if a > 140 else (0, 0, 0, 0)
    return out, pad


def compose(head, torso, arm, leg, phase):
    """One raw-resolution frame. phase in [0,1); phase<0 means idle."""
    if phase < 0:
        leg_a = arm_a = 0.0
        bob = 0
    else:
        s = math.sin(phase * 2 * math.pi)
        leg_a = 24 * s
        arm_a = -18 * s
        bob = round(abs(math.cos(phase * 2 * math.pi)) * torso.height * 0.03)

    th, lh = torso.height, leg.height
    hip_overlap = round(lh * 0.10)
    body_h = head.height + round(th * 0.82) + lh - hip_overlap
    W = body_h * 2
    frame = Image.new("RGBA", (W, body_h + 8), (0, 0, 0, 0))
    cx = W // 2

    neck_y = bob
    torso_y = neck_y + round(head.height * 0.92)
    hip_y = torso_y + th - hip_overlap
    shoulder_y = torso_y + round(th * 0.10)

    def put(img, x, y):
        frame.alpha_composite(img, (round(x), round(y)))

    far_leg, pad = swung(leg, -leg_a)
    put(far_leg, cx - far_leg.width / 2 + leg.width * 0.25, hip_y)
    far_arm, pad = swung(arm, -arm_a)
    put(far_arm, cx - far_arm.width / 2 - arm.width * 0.15, shoulder_y)
    put(torso.copy() if torso.mode == "RGBA" else torso, cx - torso.width / 2,
        torso_y)
    near_leg, pad = swung(leg, leg_a)
    put(near_leg, cx - near_leg.width / 2 - leg.width * 0.10, hip_y)
    put(head, cx - head.width / 2 + torso.width * 0.10, neck_y)
    near_arm, pad = swung(arm, arm_a)
    put(near_arm, cx - near_arm.width / 2 + arm.width * 0.10, shoulder_y)

    flat = Image.new("RGB", frame.size, MAGENTA)
    flat.paste(frame, (0, 0), frame)
    return flat


def part_bitmap(part, scale):
    """1-bit render of one raw part at game scale (no halo; the assembled
    figure gets its outline from the parts themselves)."""
    from PIL import ImageFilter

    pw = max(1, round(part.width * scale))
    ph = max(1, round(part.height * scale))
    gray = part.convert("L")
    alpha = part.getchannel("A")
    small = gray.resize((pw, ph), Image.LANCZOS).load()
    dark = gray.filter(ImageFilter.MinFilter(7)) \
        .resize((pw, ph), Image.LANCZOS).load()
    mm = alpha.resize((pw, ph), Image.LANCZOS).load()
    mask = [[mm[x, y] > 127 for x in range(pw)] for y in range(ph)]
    out = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    op = out.load()
    for y in range(ph):
        for x in range(pw):
            if not mask[y][x]:
                continue
            edge = any(not (0 <= x + dx < pw and 0 <= y + dy < ph
                            and mask[y + dy][x + dx])
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            black = small[x, y] < 100 or (small[x, y] < 200 and dark[x, y] < 60)
            op[x, y] = (0, 0, 0, 255) if (edge or black) \
                else (255, 255, 255, 255)
    return out


def anchored(img, ax, ay):
    """Pad so (ax, ay) sits exactly at the image center, for drawRotated."""
    w, h = img.size
    left = max(0, round(w - 2 * ax))
    right = max(0, round(2 * ax - w))
    top = max(0, round(h - 2 * ay))
    bottom = max(0, round(2 * ay - h))
    out = Image.new("RGBA", (w + left + right, h + top + bottom), (0, 0, 0, 0))
    out.paste(img, (left, top), img)
    return out


def export_parts(src, name):
    """Ship head/torso/arm/leg as an imagetable plus a Lua rig description,
    so the walk can be composed at runtime instead of baked."""
    head, torso, arm, leg = load_parts(os.path.join(RAW, src))
    head, torso, arm, leg = rgba(head), rgba(torso), rgba(arm), rgba(leg)
    th, lh = torso.height, leg.height
    hip_overlap = lh * 0.10
    torso_y = head.height * 0.92
    shoulder_y = torso_y + th * 0.10
    hip_y = torso_y + th - hip_overlap
    body_h = hip_y + lh
    s = SPRITE_H / body_h

    parts = {
        "head": (part_bitmap(head, s), head.width / 2, head.height / 2,
                 torso.width * 0.10, torso_y + head.height * 0.5 - head.height),
        "torso": (part_bitmap(torso, s), torso.width / 2, torso.height / 2,
                  0.0, torso_y + th * 0.5),
        "arm": (part_bitmap(arm, s), arm.width / 2, arm.height * 0.08,
                0.0, shoulder_y),
        "leg": (part_bitmap(leg, s), leg.width / 2, leg.height * 0.08,
                0.0, hip_y),
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
        "\theight = %d," % SPRITE_H,
        "\tframes = { head = 1, torso = 2, arm = 3, leg = 4 },",
    ]
    for key in order:
        _, _, _, ox, oy = parts[key]
        lua.append("\t%s = { x = %d, y = %d }," % (
            key, round(ox * s), round((oy - body_h) * s)))
    lua.append("\thipSpread = %d," % round(leg.width * 0.10 * s))
    lua.append("\tshoulderSpread = %d," % round(arm.width * 0.12 * s))
    lua.append("}")
    lua.append("")
    path = os.path.join(ROOT_SCRIPTS, "game", "herorig.lua")
    with open(path, "w") as f:
        f.write("\n".join(lua))
    print("wrote", path)


def bake(src, name, frames=7):
    head, torso, arm, leg = load_parts(os.path.join(RAW, src))
    head, torso, arm, leg = rgba(head), rgba(torso), rgba(arm), rgba(leg)
    out = [extract_sprite(compose(head, torso, arm, leg, -1), SPRITE_H)]
    for i in range(frames - 1):
        out.append(extract_sprite(
            compose(head, torso, arm, leg, i / (frames - 1)), SPRITE_H))
    sheet(out, name)


def main():
    bake("gen_male_parts.png", "hero")
    export_parts("gen_male_parts.png", "heroparts")


if __name__ == "__main__":
    main()
