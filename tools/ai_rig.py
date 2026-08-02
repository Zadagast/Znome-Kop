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


if __name__ == "__main__":
    main()
