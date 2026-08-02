#!/usr/bin/env python3
"""Generates every art asset plus the Lua tile atlas.

    python3 tools/gen_art.py

Outputs (all committed so the game builds without Python):
    source/images/tiles-table-16-16.png
    source/images/actors-table-16-16.png
    source/images/znomes-table-32-32.png
    source/scripts/world/atlas.lua
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from art_actors import ACTORS
from art_znomes import FRAMES as ZNOME_FRAMES, SIZE as ZNOME_SIZE, ZNOMES
from canvas import (
    BLACK, CLEAR, WHITE, Canvas, dither_at, from_ascii, from_png, write_sheet,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(ROOT, "source", "images")
PACK_ART = os.path.join(ROOT, "tools", "pack_art")
T = 16  # tile size


def pack(name):
    """Load a converted asset-pack element (see tools/convert_packs.py)."""
    return from_png(os.path.join(PACK_ART, name + ".png"))


def pack_fn(name):
    return lambda: pack(name)


def rot90(c):
    out = Canvas(c.h, c.w)
    for y in range(c.h):
        for x in range(c.w):
            out.px[x][c.h - 1 - y] = c.px[y][x]
    return out


def rnd(x, y, salt=0):
    """Stable hash noise so tiles look scattered but regenerate identically."""
    h = (x * 374761393 + y * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


# --- ground tiles --------------------------------------------------------


def t_dust():
    # Pallet-Town-style path: clean white with sparse 2px dash marks.
    c = Canvas(T, T, WHITE)
    for x, y in ((4, 5), (12, 12)):
        c.set(x, y, BLACK)
        c.set(x + 1, y, BLACK)
    return c


def t_regolith():
    c = Canvas(T, T, WHITE)
    for x, y in ((2, 3), (10, 6), (5, 12), (13, 13)):
        c.set(x, y, BLACK)
    c.hline(6, 7, 8, BLACK)
    return c


def t_gravel():
    # Outlined pebbles on white, comic-clean.
    c = Canvas(T, T, WHITE)
    for i, (x, y) in enumerate(((1, 2), (8, 1), (12, 6), (3, 9), (9, 11))):
        w = 3 + (i % 2)
        c.hline(x + 1, x + w - 1, y, BLACK)
        c.hline(x + 1, x + w - 1, y + 2, BLACK)
        c.set(x, y + 1, BLACK)
        c.set(x + w, y + 1, BLACK)
    return c


def t_dunes():
    # Clean wind ripples, no dither wash.
    c = Canvas(T, T, WHITE)
    for y in (3, 11):
        for x in range(1, T - 1):
            c.set(x, y + (1 if (x // 4) % 2 else 0), BLACK)
    for x in range(5, 12):
        c.set(x, 7, BLACK)
    return c


def t_plate():
    c = Canvas(T, T, WHITE)
    c.outline_rect(0, 0, T, T, BLACK)
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        c.set(x, y, BLACK)
    return c


def t_grate():
    c = t_plate()
    for y in range(4, 13, 3):
        c.hline(4, 11, y, BLACK)
    return c


def tuft(c, x, y):
    """A GB-grass style 5x3 tuft: two blades splaying from a base."""
    c.set(x + 2, y, BLACK)
    c.set(x + 1, y + 1, BLACK)
    c.set(x + 3, y + 1, BLACK)
    c.set(x, y + 2, BLACK)
    c.set(x + 2, y + 2, BLACK)
    c.set(x + 4, y + 2, BLACK)


def t_sporegrass():
    # Uniform tuft lattice like the Pokemon encounter-grass tile.
    c = Canvas(T, T, WHITE)
    for gy, offset in ((1, 0), (6, 5), (11, 0)):
        for gx in range(offset, T - 4, 10):
            tuft(c, gx, gy)
    return c


def t_sporegrass_tall():
    c = Canvas(T, T, WHITE)
    for gy, offset in ((0, 0), (4, 5), (8, 0), (12, 5)):
        for gx in range(offset, T - 4, 10):
            tuft(c, gx, gy)
    for x in (2, 12):
        c.vline(x, 5, 10, BLACK)
    return c


def t_coolant():
    # GB water: light dither wash with clean wave dashes.
    c = Canvas(T, T, WHITE)
    c.dither_rect(0, 0, T, T, "d12")
    for y in (3, 9):
        c.hline(2, 6, y, BLACK)
        c.hline(9, 13, y + 1, BLACK)
    c.hline(5, 9, 14, BLACK)
    return c


def t_rock():
    # A single outlined boulder filling the tile, faceted like GB mountain rock.
    c = Canvas(T, T, WHITE)
    c.outline_rect(0, 0, T, T, BLACK)
    c.line(1, 5, 5, 1, BLACK)
    c.line(10, 1, 14, 5, BLACK)
    c.line(1, 10, 5, 14, BLACK)
    c.line(10, 14, 14, 10, BLACK)
    c.dither_rect(2, 10, 12, 4, "d25")
    c.hline(5, 10, 7, BLACK)
    return c


def t_cliff():
    # Layered strata: dark cap, white face with staggered cracks.
    c = Canvas(T, T, WHITE)
    c.rect(0, 0, T, 2, BLACK)
    c.hline(0, T - 1, 7, BLACK)
    c.hline(0, T - 1, 15, BLACK)
    for x in (5, 13):
        c.vline(x, 2, 6, BLACK)
    for x in (1, 9):
        c.vline(x, 8, 14, BLACK)
    return c


def t_crater():
    c = Canvas(T, T, WHITE)
    c.outline_rect(2, 2, 12, 12, BLACK)
    c.set(2, 2, WHITE)
    c.set(13, 2, WHITE)
    c.set(2, 13, WHITE)
    c.set(13, 13, WHITE)
    c.dither_rect(5, 5, 6, 6, "d75")
    c.hline(4, 11, 12, BLACK)
    return c


def t_tube():
    c = Canvas(T, T, WHITE)
    c.dither_rect(0, 0, T, T, "d25")
    for x, y in ((3, 3), (10, 7), (5, 12)):
        c.hline(x, x + 2, y, BLACK)
        c.set(x + 1, y + 1, BLACK)
    return c


def t_ash():
    c = Canvas(T, T, WHITE)
    for x, y in ((2, 3), (12, 2), (7, 7), (3, 12), (12, 12)):
        c.set(x, y, BLACK)
        c.set(x, y - 1, BLACK)
        c.set(x - 1, y, BLACK)
        c.set(x + 1, y, BLACK)
        c.set(x, y + 1, BLACK)
    return c


# --- object tiles (transparent background) -------------------------------


def o_boulder():
    c = Canvas(T, T)
    for y in range(3, 15):
        for x in range(1, 15):
            dx, dy = (x - 8) / 7.0, (y - 9.5) / 6.0
            if dx * dx + dy * dy <= 1.0:
                c.set(x, y, dither_at(x, y, 0 if y < 9 else 4))
    for y in range(3, 15):
        for x in range(1, 15):
            if c.get(x, y) == CLEAR:
                continue
            if CLEAR in (c.get(x - 1, y), c.get(x + 1, y), c.get(x, y - 1), c.get(x, y + 1)):
                c.set(x, y, BLACK)
    c.line(5, 8, 9, 11, BLACK)
    return c


def o_fence_h():
    c = Canvas(T, T)
    c.hline(0, T - 1, 6, BLACK)
    c.hline(0, T - 1, 10, BLACK)
    c.vline(3, 4, 14, BLACK)
    c.vline(12, 4, 14, BLACK)
    return c


def o_fence_v():
    c = Canvas(T, T)
    c.vline(6, 0, T - 1, BLACK)
    c.vline(10, 0, T - 1, BLACK)
    c.hline(4, 12, 4, BLACK)
    c.hline(4, 12, 12, BLACK)
    return c


def o_sign():
    c = Canvas(T, T)
    c.rect(2, 3, 12, 8, WHITE)
    c.outline_rect(2, 3, 12, 8, BLACK)
    c.hline(4, 11, 6, BLACK)
    c.hline(4, 9, 8, BLACK)
    c.rect(7, 11, 2, 4, BLACK)
    return c


def o_crate():
    c = Canvas(T, T)
    c.rect(2, 4, 12, 11, WHITE)
    c.outline_rect(2, 4, 12, 11, BLACK)
    c.line(2, 4, 13, 14, BLACK)
    c.line(13, 4, 2, 14, BLACK)
    return c


def o_pipe_h():
    c = Canvas(T, T)
    c.rect(0, 5, T, 6, WHITE)
    c.hline(0, T - 1, 5, BLACK)
    c.hline(0, T - 1, 10, BLACK)
    c.vline(4, 5, 10, BLACK)
    c.vline(11, 5, 10, BLACK)
    return c


def o_pipe_v():
    c = Canvas(T, T)
    c.rect(5, 0, 6, T, WHITE)
    c.vline(5, 0, T - 1, BLACK)
    c.vline(10, 0, T - 1, BLACK)
    c.hline(5, 10, 4, BLACK)
    c.hline(5, 10, 11, BLACK)
    return c


def o_lichen():
    c = Canvas(T, T)
    for i in range(5):
        x = 2 + int(rnd(i, 17, 9) * 11)
        y = 4 + int(rnd(i, 19, 9) * 9)
        c.set(x, y, BLACK)
        c.set(x + 1, y + 1, BLACK)
        c.set(x - 1, y + 1, BLACK)
    return c


def o_vent():
    c = Canvas(T, T)
    c.rect(3, 6, 10, 8, WHITE)
    c.outline_rect(3, 6, 10, 8, BLACK)
    for y in (8, 10, 12):
        c.hline(5, 10, y, BLACK)
    c.set(7, 3, BLACK)
    c.set(9, 1, BLACK)
    return c


def o_marker():
    c = Canvas(T, T)
    c.vline(8, 4, 15, BLACK)
    c.rect(9, 4, 5, 4, WHITE)
    c.outline_rect(8, 4, 6, 5, BLACK)
    return c


GROUND_TILES = [
    ("dust", pack_fn("tile_dust"), {}),
    ("regolith", pack_fn("tile_regolith"), {}),
    ("gravel", pack_fn("tile_gravel"), {}),
    ("dunes", pack_fn("tile_dunes"), {}),
    ("plate", pack_fn("tile_plate"), {}),
    ("grate", pack_fn("tile_grate"), {}),
    ("sporegrass", pack_fn("tile_sporegrass"), {"encounter": True}),
    ("sporegrass_tall", pack_fn("tile_sporegrass_tall"), {"encounter": True}),
    ("coolant", t_coolant, {"solid": True}),
    ("rock", pack_fn("tile_rock"), {"solid": True}),
    ("cliff", pack_fn("tile_cliff"), {"solid": True}),
    ("crater", t_crater, {"solid": True}),
    ("tube", t_tube, {}),
    ("ash", pack_fn("tile_ash"), {"encounter": True}),
]

OBJECT_TILES = [
    ("boulder", pack_fn("obj_boulder"), {"solid": True}),
    ("fence_h", pack_fn("obj_fence_h"), {"solid": True}),
    ("fence_v", lambda: rot90(pack("obj_fence_h")), {"solid": True}),
    ("sign", pack_fn("obj_sign"), {"solid": True}),
    ("crate", pack_fn("obj_crate"), {"solid": True}),
    ("pipe_h", o_pipe_h, {"solid": True}),
    ("pipe_v", o_pipe_v, {"solid": True}),
    ("lichen", pack_fn("obj_lichen"), {}),
    ("vent", pack_fn("obj_vent"), {"solid": True}),
    ("marker", pack_fn("obj_marker"), {"solid": True}),
]


# --- structures ----------------------------------------------------------


def panel(c, x, y, w, h, density="white"):
    c.dither_rect(x, y, w, h, density)
    c.outline_rect(x, y, w, h, BLACK)


def rivets(c, x, y, w, h, step=6):
    for yy in range(y + 2, y + h - 1, step):
        for xx in range(x + 2, x + w - 1, step):
            c.set(xx, yy, BLACK)


def door(c, x, y, w=T, h=None):
    """Airlock doorway; the tile under it is the walkable entrance."""
    h = h or T
    c.rect(x, y, w, h, WHITE)
    c.outline_rect(x, y, w, h, BLACK)
    c.dither_rect(x + 3, y + 2, w - 6, h - 4, "d50")
    c.outline_rect(x + 3, y + 2, w - 6, h - 4, BLACK)
    c.vline(x + w // 2, y + 3, y + h - 4, BLACK)
    c.hline(x + 4, x + w - 5, y + h // 2, BLACK)


def s_hab():
    """4x3 tile colony habitat (GB Village cottage, door on tile 2,2)."""
    w, h = 4 * T, 3 * T
    c = Canvas(w, h)
    art = pack("spr_hab")
    c.blit(art, 12, h - art.h)
    return c, {"w": 4, "h": 3, "doors": [(2, 2)]}


def s_lab():
    """5x4 tile research outpost (GB Village two-story house)."""
    w, h = 5 * T, 4 * T
    c = Canvas(w, h)
    art = pack("spr_lab")
    c.blit(art, (w - art.w) // 2, h - art.h)
    return c, {"w": 5, "h": 4, "doors": [(2, 3)]}


def s_gate():
    """3x2 perimeter airlock; the middle bottom tile is the zone exit."""
    w, h = 3 * T, 2 * T
    c = Canvas(w, h)
    c.blit(pack("spr_airlock"), 8, 0)
    c.blit(pack("spr_pillar"), 0, 0)
    c.blit(pack("spr_pillar"), 2 * T, 0)
    return c, {"w": 3, "h": 2, "doors": [(1, 1)]}


def s_solar():
    """2x2 comms/solar dish from the sci-fi pack."""
    c = Canvas(2 * T, 2 * T)
    c.blit(pack("spr_solar"), 0, 0)
    return c, {"w": 2, "h": 2, "doors": []}


def s_tank():
    w, h = 2 * T, 2 * T
    c = Canvas(w, h)
    for y in range(2, h - 2):
        for x in range(2, w - 2):
            dx = (x - w / 2 + 0.5) / (w / 2 - 3)
            if abs(dx) <= 1.0:
                c.set(x, y, dither_at(x, y, 0 if x < w * 0.5 else 6))
    c.outline_rect(2, 2, w - 4, h - 4, BLACK)
    for y in range(6, h - 4, 8):
        c.hline(3, w - 4, y, BLACK)
    return c, {"w": 2, "h": 2, "doors": []}


def s_tower():
    w, h = 2 * T, 3 * T
    c = Canvas(w, h)
    c.line(4, h - 1, w // 2 - 1, 4, BLACK)
    c.line(w - 5, h - 1, w // 2, 4, BLACK)
    for y in range(8, h - 2, 6):
        c.hline(4 + (y - 8) // 6, w - 5 - (y - 8) // 6, y, BLACK)
    c.rect(w // 2 - 5, 0, 10, 5, WHITE)
    c.outline_rect(w // 2 - 5, 0, 10, 5, BLACK)
    c.dither_rect(w // 2 - 3, 1, 6, 3, "d50")
    return c, {"w": 2, "h": 3, "doors": []}


STRUCTURES = [
    ("hab", s_hab),
    ("lab", s_lab),
    ("gate", s_gate),
    ("solar", s_solar),
    ("tank", s_tank),
    ("tower", s_tower),
]


# --- build ---------------------------------------------------------------


def build_tiles():
    frames, names, flags, structures = [], {}, {}, {}

    def add(name, canvas, props):
        frames.append(canvas)
        idx = len(frames)  # image tables are 1-based
        names[name] = idx
        if props:
            flags[idx] = props
        return idx

    for name, fn, props in GROUND_TILES:
        add(name, fn(), props)
    for name, fn, props in OBJECT_TILES:
        add(name, fn(), props)

    for name, fn in STRUCTURES:
        canvas, meta = fn()
        grid, solid = [], []
        for ty in range(meta["h"]):
            for tx in range(meta["w"]):
                cell = canvas.sub(tx * T, ty * T, T, T)
                is_door = (tx, ty) in meta["doors"]
                idx = 0 if cell.is_blank() else add(
                    "%s_%d_%d" % (name, tx, ty), cell, {"solid": not is_door}
                )
                grid.append(idx)
                solid.append(0 if (is_door or idx == 0) else 1)
        structures[name] = {
            "w": meta["w"],
            "h": meta["h"],
            "tiles": grid,
            "solid": solid,
            "doors": meta["doors"],
        }
    return frames, names, flags, structures


def lua_atlas(names, flags, structures, count):
    out = ["-- Generated by tools/gen_art.py. Do not edit by hand.", "", "Atlas = {}", ""]
    out.append("Atlas.count = %d" % count)
    out.append("")
    out.append("Atlas.tile = {")
    for name in sorted(names):
        out.append("\t%s = %d," % (name, names[name]))
    out.append("}")
    out.append("")
    for prop in ("solid", "encounter"):
        out.append("Atlas.%s = {" % prop)
        for idx in sorted(i for i, p in flags.items() if p.get(prop)):
            out.append("\t[%d] = true," % idx)
        out.append("}")
        out.append("")
    out.append("Atlas.structures = {")
    for name in sorted(structures):
        s = structures[name]
        out.append("\t%s = {" % name)
        out.append("\t\tw = %d, h = %d," % (s["w"], s["h"]))
        out.append("\t\ttiles = { %s }," % ", ".join(str(v) for v in s["tiles"]))
        out.append("\t\tsolid = { %s }," % ", ".join(str(v) for v in s["solid"]))
        doors = ", ".join("{ x = %d, y = %d }" % (d[0], d[1]) for d in s["doors"])
        out.append("\t\tdoors = { %s }," % doors)
        out.append("\t},")
    out.append("}")
    out.append("")
    return "\n".join(out)


def build_actors():
    """Actor sheets from the GB Village pack: down/up/side pairs, side faces
    left in the pack, so right is the mirror."""
    frames = []
    order = []
    for name in ("kop", "colonist", "tech"):
        sheet = pack("actor_" + name)
        arts = [sheet.sub(i * T, 0, T, T) for i in range(6)]
        d0, d1, u0, u1, l0, l1 = arts
        base = len(frames) + 1
        frames.extend([d0, d1, u0, u1, l0, l1, l0.flip_h(), l1.flip_h()])
        order.append((name, base))
    return frames, order


def build_launcher(znome_frames):
    """Launcher card (350x155) and icon (32x32), 1-bit like everything else."""
    from PIL import Image, ImageDraw, ImageFont

    out = os.path.join(IMAGES, "launcher")
    os.makedirs(out, exist_ok=True)

    card = Canvas(350, 155, WHITE)
    card.dither_rect(0, 96, 350, 59, "d25")
    for i in range(0, 350, 40):
        card.line(i, 96, i + 18, 155, BLACK)
    card.outline_rect(0, 0, 350, 155, BLACK)
    card.blit(znome_frames[0 * ZNOME_FRAMES], 18, 54)
    card.blit(znome_frames[4 * ZNOME_FRAMES], 128, 56)
    card.blit(znome_frames[11 * ZNOME_FRAMES], 244, 52)
    panel(card, 40, 16, 270, 34)
    write_sheet(os.path.join(out, "card.png"), [card], 1, 350, 155)

    img = Image.open(os.path.join(out, "card.png")).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((150, 28), "ZNOME KOP", fill=(0, 0, 0), font=font)
    img.convert("RGBA").save(os.path.join(out, "card.png"))

    icon = Canvas(32, 32, WHITE)
    icon.blit(znome_frames[0], -32, -58)
    icon.outline_rect(0, 0, 32, 32, BLACK)
    write_sheet(os.path.join(out, "icon.png"), [icon], 1, 32, 32)


def main():
    os.makedirs(IMAGES, exist_ok=True)
    frames, names, flags, structures = build_tiles()
    write_sheet(os.path.join(IMAGES, "tiles-table-16-16.png"), frames, 8, T, T)

    actor_frames, actor_order = build_actors()
    write_sheet(os.path.join(IMAGES, "actors-table-16-16.png"), actor_frames, 8, T, T)

    znome_frames = []
    for _, fn in ZNOMES:
        znome_frames.extend(fn())
    write_sheet(
        os.path.join(IMAGES, "znomes-table-96-96.png"),
        znome_frames, ZNOME_FRAMES, ZNOME_SIZE, ZNOME_SIZE,
    )

    build_launcher(znome_frames)

    atlas = lua_atlas(names, flags, structures, len(frames))
    atlas += "\nAtlas.actors = {\n"
    for name, base in actor_order:
        atlas += "\t%s = %d,\n" % (name, base)
    atlas += "}\n\nAtlas.znomeFrames = %d\n\nAtlas.znomeSprite = {\n" % ZNOME_FRAMES
    for i, (name, _) in enumerate(ZNOMES):
        atlas += "\t%s = %d,\n" % (name, i * ZNOME_FRAMES + 1)
    atlas += "}\n"
    with open(os.path.join(ROOT, "source", "scripts", "world", "atlas.lua"), "w") as f:
        f.write(atlas)

    print("tiles: %d  actors: %d  znome frames: %d" % (
        len(frames), len(actor_frames), len(znome_frames)))


if __name__ == "__main__":
    main()
