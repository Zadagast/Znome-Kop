"""CLI: render creatures to PNG sheets, GIF previews or seed boards.

Examples:
    python3 -m spritegen --seed 4 --grid 24x22 --out creature.gif
    python3 -m spritegen --seed 4 --grid 24x22 --frames 4 --out sheet.png
    python3 -m spritegen --board 20 --grid 32x36 --out board.png
"""

import argparse

from .onebit import CLEAR, WHITE, Canvas, render_frames


def to_image(canvas, background=None, scale=1):
    """Canvas -> PIL image (RGBA when background is None)."""
    from PIL import Image

    if background is None:
        img = Image.new("RGBA", (canvas.w, canvas.h), (0, 0, 0, 0))
        pal = {WHITE: (255, 255, 255, 255), 2: (0, 0, 0, 255)}
    else:
        img = Image.new("RGB", (canvas.w, canvas.h), background)
        pal = {WHITE: (255, 255, 255), 2: (0, 0, 0)}
    px = img.load()
    for y in range(canvas.h):
        for x in range(canvas.w):
            v = canvas.px[y][x]
            if v != CLEAR:
                px[x, y] = pal[v]
    if scale > 1:
        from PIL import Image as I
        img = img.resize((canvas.w * scale, canvas.h * scale), I.NEAREST)
    return img


def main():
    ap = argparse.ArgumentParser(
        prog="spritegen",
        description="Procedural 1-bit creature sprites (Deep-Fold port "
                    "with per-part idle animation).")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--grid", default="30x30",
                    help="generator grid WxH (default 30x30)")
    ap.add_argument("--size", default=None,
                    help="output frame WxH in pixels (default grid*cell "
                         "plus margins)")
    ap.add_argument("--cell", type=int, default=2,
                    help="pixels per generator cell (default 2)")
    ap.add_argument("--frames", type=int, default=4)
    ap.add_argument("--dark", action="store_true",
                    help="mostly-black creature (for void/shadow types)")
    ap.add_argument("--no-eyes", action="store_true",
                    help="let the generator decide which holes are eyes")
    ap.add_argument("--fill", type=float, default=0.48)
    ap.add_argument("--walks", type=int, default=2)
    ap.add_argument("--ca-steps", type=int, default=4)
    ap.add_argument("--board", type=int, default=0, metavar="N",
                    help="render seeds 0..N-1 as a picking board instead")
    ap.add_argument("--scale", type=int, default=1,
                    help="nearest-neighbour upscale of the output image")
    ap.add_argument("--out", required=True,
                    help=".gif = animated preview, .png = frame sheet")
    args = ap.parse_args()

    from PIL import Image

    gw, gh = (int(v) for v in args.grid.lower().split("x"))
    if args.size:
        ow, oh = (int(v) for v in args.size.lower().split("x"))
    else:
        ow, oh = (gw + 4) * args.cell, (gh + 4) * args.cell
    knobs = dict(w=gw, h=gh, eyes=not args.no_eyes, fill=args.fill,
                 walks=args.walks, ca_steps=args.ca_steps)

    if args.board:
        cols = min(args.board, 10)
        rows = (args.board + cols - 1) // cols
        img = Image.new("RGB", (ow * cols, oh * rows), (200, 200, 200))
        for s in range(args.board):
            f = render_frames(s, ow, oh, cell=args.cell, frames=1,
                              dark=args.dark, **knobs)[0]
            img.paste(to_image(f, background=(200, 200, 200)),
                      ((s % cols) * ow, (s // cols) * oh))
    else:
        fs = render_frames(args.seed, ow, oh, cell=args.cell,
                           frames=args.frames, dark=args.dark, **knobs)
        if args.out.lower().endswith(".gif"):
            imgs = [to_image(f, background=(200, 200, 200),
                             scale=max(args.scale, 1)) for f in fs]
            imgs[0].save(args.out, save_all=True, append_images=imgs[1:],
                         duration=180, loop=0)
            print("wrote", args.out)
            return
        img = Image.new("RGBA", (ow * len(fs), oh), (0, 0, 0, 0))
        for i, f in enumerate(fs):
            img.alpha_composite(to_image(f), (i * ow, 0))
    if args.scale > 1:
        img = img.resize((img.width * args.scale, img.height * args.scale),
                         Image.NEAREST)
    img.save(args.out)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
