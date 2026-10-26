#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25
"""Town Map helpers (docs/modding/town-map-and-fly.md).

    python3 tools/townmap/townmap.py render out.png          # the map with a grid of Overworld cells
    python3 tools/townmap/townmap.py render --sheet out.png  # the whole 64x64 tilemap, patches included
    python3 tools/townmap/townmap.py follow-rules [COUNT]     # give new map sections their follow rules

The Town Map is one 8bpp tile sheet (pgmap_gra_00000010.png) and one 64x64
tilemap (pgmap_gra_00000011.NSCR). One tile is one cell of the Overworld layout:
Overworld cell (x, y) is tile (x, y + 2). Rows 20 and below hold the patches
the code copies over the map (grey towns, locked Kanto, highlights).

`follow-rules` appends empty members to files/a/2/2/0, the following-Pokemon
rules: member 0 is shared, member N + 1 belongs to map section N, so every
new MAPSEC_* needs one (600 bytes of zeros = no rules).
"""

import argparse
import struct
import sys

from PIL import Image, ImageDraw

GFX = "files/application/pokegear/map/pgmap_gra/"
TILES = GFX + "pgmap_gra_00000010.png"
SCREEN = GFX + "pgmap_gra_00000011.NSCR"
FOLLOW_RULES = "files/a/2/2/0"
FOLLOW_RULES_SIZE = 600  # 30 rules of 20 bytes
MAP_W, MAP_H, ROW_OFFSET = 47, 20, 2


def read_screen(path):
    data = open(path, "rb").read()
    scrn = data.find(b"NRCS")
    width, height = struct.unpack_from("<HH", data, scrn + 8)
    size = struct.unpack_from("<I", data, scrn + 16)[0]
    body = data[scrn + 20:scrn + 20 + size]
    return width // 8, height // 8, [struct.unpack_from("<H", body, i)[0] for i in range(0, size, 2)]


def draw_tilemap(tiles, cols, rows, entries):
    per_row = tiles.size[0] // 8
    out = Image.new("P", (cols * 8, rows * 8))
    out.putpalette(tiles.getpalette())
    for i, entry in enumerate(entries):
        tile = entry & 0x3FF
        src = tiles.crop((tile % per_row * 8, tile // per_row * 8, tile % per_row * 8 + 8, tile // per_row * 8 + 8))
        if entry & 0x400:
            src = src.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if entry & 0x800:
            src = src.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        out.paste(src, (i % cols * 8, i // cols * 8))
    return out.convert("RGB")


def render(args):
    tiles = Image.open(TILES)
    cols, rows, entries = read_screen(SCREEN)
    img = draw_tilemap(tiles, cols, rows, entries)
    if not args.sheet:
        img = img.crop((0, 0, MAP_W * 8, MAP_H * 8))
    scale = args.scale
    img = img.resize((img.size[0] * scale, img.size[1] * scale), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    step = 8 * scale
    # Overworld cell numbers on the map (row = tile row - 2), tile numbers on the sheet.
    row_offset = 0 if args.sheet else ROW_OFFSET
    for x in range(0, img.size[0] // step + 1):
        draw.line([(x * step, 0), (x * step, img.size[1])], fill=(0, 0, 0) if x % 5 == 0 else (90, 90, 90))
        if x % 5 == 0:
            draw.text((x * step + 2, 1), str(x), fill=(255, 255, 255))
    for y in range(0, img.size[1] // step + 1):
        label = y - row_offset
        draw.line([(0, y * step), (img.size[0], y * step)], fill=(0, 0, 0) if label % 5 == 0 else (90, 90, 90))
        if label % 5 == 0 and label >= 0:
            draw.text((2, y * step + 2), str(label), fill=(255, 255, 255))
        if row_offset and y % 5 == 0:
            # tile row on the right: sLocationSpecs and the tilemap use it
            draw.text((img.size[0] - 4 * scale - 14, y * step + 2), "t%d" % y, fill=(255, 255, 160))
    img.save(args.out)
    what = "tiles" if args.sheet else "Overworld cells (left) and tile rows (right, t = cell + 2)"
    print("%s: %dx%d, grid in %s" % (args.out, img.size[0], img.size[1], what))


def narc_append(path, size, count):
    data = open(path, "rb").read()
    fat, fnt, img = data.find(b"BTAF"), data.find(b"BTNF"), data.find(b"GMIF")
    n = struct.unpack_from("<H", data, fat + 8)[0]
    ranges = [struct.unpack_from("<II", data, fat + 12 + 8 * i) for i in range(n)]
    image = data[img + 8:img + struct.unpack_from("<I", data, img + 4)[0]]
    members = [image[s:e] for s, e in ranges] + [bytes(size)] * count
    names = data[fnt:fnt + struct.unpack_from("<I", data, fnt + 4)[0]]
    body, offsets = b"", []
    for m in members:
        offsets.append((len(body), len(body) + len(m)))
        body += m + bytes(-len(m) % 4)
    btaf = b"BTAF" + struct.pack("<IHH", 12 + 8 * len(members), len(members), 0)
    btaf += b"".join(struct.pack("<II", *o) for o in offsets)
    gmif = b"GMIF" + struct.pack("<I", 8 + len(body)) + body
    total = 16 + len(btaf) + len(names) + len(gmif)
    with open(path, "wb") as f:
        f.write(data[:8] + struct.pack("<IHH", total, 16, 3) + btaf + names + gmif)
    return n, len(members)


def follow_rules(args):
    before, after = narc_append(FOLLOW_RULES, FOLLOW_RULES_SIZE, args.count)
    print("%s: %d -> %d members (map sections 0-%d)" % (FOLLOW_RULES, before, after, after - 2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("render", help="write the Town Map as a PNG with a grid")
    p.add_argument("out")
    p.add_argument("--sheet", action="store_true", help="the whole tilemap, with tile numbers")
    p.add_argument("--scale", type=int, default=3)
    p.set_defaults(func=render)
    p = sub.add_parser("follow-rules", help="append empty following-Pokemon rules for new map sections")
    p.add_argument("count", type=int, nargs="?", default=1)
    p.set_defaults(func=follow_rules)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
