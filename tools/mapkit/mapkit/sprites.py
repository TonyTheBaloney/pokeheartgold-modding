# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25
"""Overworld sprites (files/data/mmodel/mmodel/*.NSBTX) as PNG sheets.

    mapkit sprite export SPRITE_BOY1 boy1.png        all frames in a row, indexed PNG
    mapkit sprite import boy1.png SPRITE_BOY1        write the pixels and palette back
    mapkit sprite add MY_NPC --like SPRITE_BOY1 [--png my_npc.png]

A sprite's NSBTX keeps its layout (frame count, size, format, names): import only replaces
texels and one palette, so any edit stays loadable by the game. docs/modding/overworld-sprites.md.
"""

import os
import re
import shutil
import struct
import zlib

from . import nitro

MMODEL_DIR = "files/data/mmodel/mmodel"
MMODEL_H = "include/constants/mmodel.h"
SPRITES_H = "include/constants/sprites.h"
SPRITE_DATA = "asm/overlay_01_sprite_data.s"
MESON = "files/data/mmodel/mmodel/meson.build"
FIRST_FREE_SPRITE_ID = 1050   # above every retail id except SPRITE_CAMERA_FOCUS (8192)

_DEFINE = re.compile(r"^#define\s+(\w+)\s+(\d+)\s*$", re.M)
_ROW = re.compile(r"^\s*\.short\s+(SPRITE_\w+|0xFFFF),\s*(\w+),\s*(.+?)\s*$", re.M)


class SpriteError(Exception):
    pass


def _read(root, rel):
    # newline="": keep the file's own line endings (some are CRLF) so edits stay one-line diffs
    with open(os.path.join(root, rel), encoding="utf-8", newline="") as f:
        return f.read()


def _write(root, rel, text):
    with open(os.path.join(root, rel), "w", encoding="utf-8", newline="") as f:
        f.write(text)


def _nl(text):
    return "\r\n" if "\r\n" in text else "\n"


def _defines(root, rel, prefix):
    return {n: int(v) for n, v in _DEFINE.findall(_read(root, rel)) if n.startswith(prefix)}


def _graphics_rows(root):
    """SPRITE_X -> (MMODEL_X, packed expression) from gObjectEventGraphicsInfos."""
    text = _read(root, SPRITE_DATA)
    start = text.index("gObjectEventGraphicsInfos:")
    rows = {}
    for m in _ROW.finditer(text, start):
        if m.group(1) == "0xFFFF":
            break
        rows[m.group(1)] = (m.group(2), m.group(3))
    return rows


def texture_paths(root):
    """SPRITE_X -> path of its NSBTX for every row of gObjectEventGraphicsInfos, read once
    (for tools that look up many sprites; resolve() reads the tables on each call). Rows
    whose MMODEL_ constant is unknown are left out; a path may not exist."""
    mmodels = _defines(root, MMODEL_H, "MMODEL_")
    return {sprite: os.path.join(root, MMODEL_DIR, "mmodel_%08d.NSBTX" % mmodels[mmodel])
            for sprite, (mmodel, _) in _graphics_rows(root).items() if mmodel in mmodels}


def resolve(root, ref):
    """SPRITE_X, MMODEL_X, a member number or a path -> path of the NSBTX."""
    if os.path.isfile(ref):
        return ref
    mmodels = _defines(root, MMODEL_H, "MMODEL_")
    if ref.startswith("SPRITE_"):
        row = _graphics_rows(root).get(ref)
        if row is None:
            raise SpriteError("%s has no row in gObjectEventGraphicsInfos (%s)" % (ref, SPRITE_DATA))
        ref = row[0]
    if ref.startswith("MMODEL_"):
        if ref not in mmodels:
            raise SpriteError("unknown %s (%s)" % (ref, MMODEL_H))
        number = mmodels[ref]
    else:
        try:
            number = int(ref, 0)
        except ValueError:
            raise SpriteError("not a sprite, MMODEL_ constant, member number or file: %s" % ref)
    path = os.path.join(root, MMODEL_DIR, "mmodel_%08d.NSBTX" % number)
    if not os.path.isfile(path):
        raise SpriteError("member %d is not an NSBTX texture (%s)" % (number, os.path.relpath(path, root)))
    return path


# --- NSBTX layout -------------------------------------------------------------------------------------------

class Layout:
    """Where an NSBTX keeps each frame's texels and each palette's colours."""

    def __init__(self, data):
        self.data = bytearray(data)
        base = nitro.blocks(bytes(data), b"BTX0")[b"TEX0"]
        d = self.data
        tex_ofs = base + nitro._u32(d, base + 0x14)
        tex_dict = base + nitro._u16(d, base + 0x0E)
        pal_dict = base + nitro._u16(d, base + 0x34)
        pal_ofs = base + nitro._u32(d, base + 0x38)
        self.frames = []
        for name, p in nitro.read_dict(d, tex_dict):
            param = nitro._u32(d, p)
            fmt = (param >> 26) & 7
            if fmt not in (2, 3, 4):
                raise SpriteError("texture %s has format %d; only paletted 4/16/256-colour textures are supported" % (name, fmt))
            self.frames.append({
                "name": name,
                "width": 8 << ((param >> 20) & 7),
                "height": 8 << ((param >> 23) & 7),
                "bpp": {2: 2, 3: 4, 4: 8}[fmt],
                "offset": tex_ofs + ((param & 0xFFFF) << 3),
                "transparent0": bool(param >> 29 & 1),
            })
        suffix = [re.match(r".*\.(\d+)$", f["name"]) for f in self.frames]
        if all(suffix):
            self.frames.sort(key=lambda f: int(re.match(r".*\.(\d+)$", f["name"]).group(1)))
        if len({(f["width"], f["height"], f["bpp"]) for f in self.frames}) != 1:
            raise SpriteError("frames of different sizes or formats are not supported")
        entries = nitro.read_dict(d, pal_dict)
        starts = sorted(set(nitro._u16(d, p) << 3 for _, p in entries))
        end = base + nitro._u32(d, base + 4)
        self.palettes = []
        for name, p in entries:
            rel = nitro._u16(d, p) << 3
            following = [s for s in starts if s > rel]
            stop = pal_ofs + following[0] if following else end
            count = max(0, min(256, (stop - pal_ofs - rel) // 2))
            self.palettes.append({"name": name, "offset": pal_ofs + rel, "count": count})

    @property
    def width(self):
        return self.frames[0]["width"]

    @property
    def height(self):
        return self.frames[0]["height"]

    @property
    def colours(self):
        return 1 << self.frames[0]["bpp"]

    def palette(self, index):
        p = self.palettes[index]
        return [nitro._u16(self.data, p["offset"] + 2 * i) for i in range(min(p["count"], self.colours))]

    def set_palette(self, index, colours):
        p = self.palettes[index]
        for i, c in enumerate(colours[:min(p["count"], self.colours)]):
            struct.pack_into("<H", self.data, p["offset"] + 2 * i, c)

    def indices(self, frame):
        f = self.frames[frame]
        bpp, n = f["bpp"], f["width"] * f["height"]
        per, mask = 8 // bpp, (1 << bpp) - 1
        return [(self.data[f["offset"] + i // per] >> ((i % per) * bpp)) & mask for i in range(n)]

    def set_indices(self, frame, idx):
        f = self.frames[frame]
        bpp, n = f["bpp"], f["width"] * f["height"]
        per = 8 // bpp
        for b in range(n // per):
            v = 0
            for k in range(per):
                v |= idx[b * per + k] << (k * bpp)
            self.data[f["offset"] + b] = v


def _to_rgb(c):
    return nitro.rgb555(c)


def _to_555(r, g, b):
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


# --- PNG ------------------------------------------------------------------------------------------------------

def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_indexed_png(path, w, h, pixels, palette_rgb, transparent0):
    raw = b"".join(b"\x00" + bytes(pixels[y * w:(y + 1) * w]) for y in range(h))
    plte = b"".join(bytes(c) for c in palette_rgb)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0)) + _chunk(b"PLTE", plte)
    if transparent0:
        png += _chunk(b"tRNS", b"\x00")
    png += _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def read_png(path):
    """-> (width, height, kind, rows). kind 'indexed': rows of indices plus .palette/.alpha;
    'rgba': rows of (r, g, b, a). 8-bit RGB/RGBA and 1/2/4/8-bit indexed, not interlaced."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SpriteError("%s is not a PNG" % path)
    pos, idat, palette, alpha = 8, b"", [], []
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b"tRNS":
            alpha = list(body)
        elif kind == b"IDAT":
            idat += body
    if interlace:
        raise SpriteError("%s: interlaced PNGs are not supported" % path)
    channels = {3: 1, 2: 3, 6: 4}.get(ctype)
    if channels is None or (ctype != 3 and depth != 8):
        raise SpriteError("%s: use an indexed, RGB or RGBA PNG (8 bits per channel)" % path)
    bits = depth * channels
    stride = (w * bits + 7) // 8
    bpp = max(1, bits // 8)
    raw = zlib.decompress(idat)
    rows, prev = [], bytearray(stride)
    for y in range(h):
        ft = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                line[i] = (line[i] + a) & 255
            elif ft == 2:
                line[i] = (line[i] + b) & 255
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if ctype == 3:
            per = 8 // depth
            rows.append([(line[x // per] >> (8 - depth * (x % per + 1))) & ((1 << depth) - 1) for x in range(w)])
        elif ctype == 2:
            rows.append([(line[3 * x], line[3 * x + 1], line[3 * x + 2], 255) for x in range(w)])
        else:
            rows.append([tuple(line[4 * x:4 * x + 4]) for x in range(w)])
    return w, h, ("indexed" if ctype == 3 else "rgba"), rows, palette, alpha


# --- commands -------------------------------------------------------------------------------------------------

def export(root, ref, out, palette=0):
    lay = Layout(open(resolve(root, ref), "rb").read())
    if palette >= len(lay.palettes):
        raise SpriteError("only %d palette(s)" % len(lay.palettes))
    w, h, n = lay.width, lay.height, len(lay.frames)
    pixels = [0] * (w * n * h)
    for k in range(n):
        idx = lay.indices(k)
        for y in range(h):
            pixels[y * w * n + k * w:y * w * n + (k + 1) * w] = idx[y * w:(y + 1) * w]
    pal = [_to_rgb(c) for c in lay.palette(palette)]
    pal += [(0, 0, 0)] * (lay.colours - len(pal))
    write_indexed_png(out, w * n, h, pixels, pal, lay.frames[0]["transparent0"])
    return {"frames": n, "width": w, "height": h, "colours": lay.colours,
            "palettes": [p["name"] for p in lay.palettes], "names": [f["name"] for f in lay.frames]}


def import_png(root, png, ref, palette=0):
    path = resolve(root, ref)
    lay = Layout(open(path, "rb").read())
    w, h, n = lay.width, lay.height, len(lay.frames)
    pw, ph, kind, rows, png_pal, png_alpha = read_png(png)
    if (pw, ph) != (w * n, h):
        raise SpriteError("%s is %dx%d; this sprite needs %dx%d (%d frames of %dx%d in a row)" % (png, pw, ph, w * n, h, n, w, h))
    colours = lay.colours
    if kind == "indexed":
        used = {i for r in rows for i in r}
        if max(used) >= colours:
            raise SpriteError("%s uses palette index %d; this sprite has %d colours" % (png, max(used), colours))
        new_pal = [_to_555(*c) for c in png_pal[:colours]]
        grid = rows
    else:
        # RGB(A): transparent pixels become index 0. Keep the current palette if it already has
        # every colour (an exported sheet edited in an RGB editor); otherwise build a new one.
        current = lay.palette(palette)
        opaque = list(dict.fromkeys(_to_555(*p[:3]) for r in rows for p in r if p[3] >= 128))
        lookup = {}
        for i in range(len(current) - 1, 0, -1):
            lookup[current[i]] = i
        if all(c in lookup for c in opaque):
            new_pal = list(current)
        else:
            if len(opaque) > colours - 1:
                raise SpriteError("%s has %d colours; this sprite allows %d plus transparency" % (png, len(opaque), colours - 1))
            new_pal = [current[0] if current else 0] + opaque
            lookup = {c: i + 1 for i, c in enumerate(opaque)}
        grid = [[0 if p[3] < 128 else lookup[_to_555(*p[:3])] for p in r] for r in rows]
    for k in range(n):
        lay.set_indices(k, [grid[y][k * w + x] for y in range(h) for x in range(w)])
    lay.set_palette(palette, new_pal + [0] * (colours - len(new_pal)))
    with open(path, "wb") as f:
        f.write(lay.data)
    return {"path": os.path.relpath(path, root), "frames": n}


def add(root, name, like, png=None):
    """A new sprite copied from `like` (a SPRITE_ constant). Returns what was written."""
    name = name.upper()
    for p in ("SPRITE_", "MMODEL_"):
        if name.startswith(p):
            name = name[len(p):]
    sprite, mmodel = "SPRITE_" + name, "MMODEL_" + name
    sprites = _defines(root, SPRITES_H, "SPRITE_")
    mmodels = _defines(root, MMODEL_H, "MMODEL_")
    if sprite in sprites or mmodel in mmodels:
        raise SpriteError("%s or %s already exists" % (sprite, mmodel))
    rows = _graphics_rows(root)
    if not like.startswith("SPRITE_") or like not in rows:
        raise SpriteError("--like needs a SPRITE_ constant with a row in gObjectEventGraphicsInfos (e.g. SPRITE_BOY1)")
    template = resolve(root, like)

    numbers = [int(m.group(1)) for f in os.listdir(os.path.join(root, MMODEL_DIR))
               for m in [re.match(r"mmodel_(\d{8})\.", f)] if m]
    member = max(numbers) + 1
    new_file = "mmodel_%08d.NSBTX" % member
    taken = set(sprites.values())
    sprite_id = FIRST_FREE_SPRITE_ID
    while sprite_id in taken:
        sprite_id += 1

    meson = _read(root, MESON)
    last = None
    for m in re.finditer(r"^[ \t]*'mmodel_\d{8}\.NSBTX',", meson, re.M):
        last = m
    if last is None:
        raise SpriteError("can't find the NSBTX list in %s" % MESON)
    meson = meson[:last.end()] + _nl(meson) + "    '%s'," % new_file + meson[last.end():]

    def append_define(text, define, value):
        nl = _nl(text)
        i = text.rindex("#endif")
        return text[:i].rstrip("\r\n") + nl + "#define %-38s %d" % (define, value) + nl + nl + text[i:]

    asm = _read(root, SPRITE_DATA)
    start = asm.index("gObjectEventGraphicsInfos:")
    term = re.compile(r"^[ \t]*\.short\s+0xFFFF,", re.M).search(asm, start)
    row = "\t.short %s, %s, %s%s" % (sprite, mmodel, rows[like][1], _nl(asm))

    shutil.copyfile(template, os.path.join(root, MMODEL_DIR, new_file))
    _write(root, MESON, meson)
    _write(root, MMODEL_H, append_define(_read(root, MMODEL_H), mmodel, member))
    _write(root, SPRITES_H, append_define(_read(root, SPRITES_H), sprite, sprite_id))
    _write(root, SPRITE_DATA, asm[:term.start()] + row + asm[term.start():])
    done = {"sprite": sprite, "sprite_id": sprite_id, "mmodel": mmodel, "member": member,
            "file": os.path.join(MMODEL_DIR, new_file), "like": like}
    if png:
        import_png(root, png, sprite)
    return done
