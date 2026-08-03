"""Preview the runtime hero rig exactly as source/scripts/game/hero.lua
draws it (same offsets, same angles), so the live rig can be checked
without the Playdate simulator.

    python3 tools/rig_preview.py [out.gif]
"""

import glob
import math
import os
import re
import sys

from PIL import Image

from ai_convert import IMAGES, ROOT

RIG_LUA = os.path.join(ROOT, "source", "scripts", "game", "herorig.lua")
ORDER = {"head": 1, "torso": 2, "arm": 3, "leg": 4}


def load_rig():
    txt = open(RIG_LUA).read()
    offs = {k: (int(a), int(b)) for k, a, b in
            re.findall(r"(\w+) = \{ x = (-?\d+), y = (-?\d+) \}", txt)}
    spread = {k: int(v) for k, v in
              re.findall(r"(hipSpread|shoulderSpread) = (-?\d+)", txt)}
    table = glob.glob(os.path.join(IMAGES, "heroparts-table-*.png"))[0]
    cw, ch = (int(v) for v in re.findall(r"-(\d+)-(\d+)\.png", table)[0])
    img = Image.open(table)
    cells = [img.crop((i * cw, 0, (i + 1) * cw, ch)) for i in range(4)]
    return offs, spread, cells


def rotated(img, deg):
    out = img.rotate(deg, resample=Image.BICUBIC,
                     center=(img.width / 2, img.height / 2))
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = p[x, y]
            p[x, y] = (r, g, b, 255) if a > 140 else (0, 0, 0, 0)
    return out


def frame(offs, spread, cells, phase):
    s = math.sin(phase)
    leg_a, arm_a = 24 * s, -18 * s
    bob = -1 if abs(math.cos(phase)) < 0.5 else 0
    w, h, ground, px = 140, 130, 118, 70
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def place(part, dx, angle):
        ox, oy = offs[part]
        c = cells[ORDER[part] - 1]
        if angle:
            c = rotated(c, angle)
        canvas.alpha_composite(c, (round(px + ox + dx - c.width / 2),
                                   round(ground + oy + bob - c.height / 2)))

    hip, sh = spread["hipSpread"], spread["shoulderSpread"]
    place("leg", hip, -leg_a)
    place("arm", -sh, -arm_a)
    place("torso", 0, 0)
    place("leg", -hip, leg_a)
    place("head", 0, 0)
    place("arm", sh, arm_a)
    flat = Image.new("RGB", (w, h), (140, 140, 140))
    flat.paste(canvas, (0, 0), canvas)
    return flat.resize((w * 2, h * 2), Image.NEAREST)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/rig_runtime.gif"
    offs, spread, cells = load_rig()
    n = 12
    frames = [frame(offs, spread, cells, i / n * 2 * math.pi) for i in range(n)]
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=80, loop=0)
    frames[3].save(os.path.splitext(out)[0] + ".png")
    print("wrote", out)


if __name__ == "__main__":
    main()
