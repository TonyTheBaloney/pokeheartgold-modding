#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Trainer battle sprites as PNG strips and a short table per class, built into the two archives.

Like pokeemerald's graphics/trainers and src/data/trainer_graphics:

    graphics/trainers/front_pics/<pic>.png    every frame, 80x80 each, stacked top to bottom
    graphics/trainers/back_pics/<pic>.png
    graphics/trainers/palettes/<palette>.pal  JASC; only the first 16 colors are drawn
    data/trainer_graphics/front_pics.json     one entry per TRAINERCLASS_, in class order
    data/trainer_graphics/back_pics.json      one entry per TRAINER_BACKPIC_, in order

An entry, with the animation as a list of sequences of [frame, duration] (pokeemerald's
ANIMCMD_FRAME), or [frame, duration, x, y] to shift the frame; "loop" at the end repeats it:

    "TRAINERCLASS_YOUNGSTER": {"pic": "youngster", "anims": [[[0, 4], "loop"]]}

The build (`trainer_pics.py build`) makes for each entry the five files the game reads
(GetTrainerPicFileIds, src/pokemon.c) and packs them, five per entry, into
files/a/0/5/8 (front) or files/a/0/0/6 (back):

    NCGR  the frames as tiles, laid out in hardware sprites ("layouts" below)
    NCLR  the palette
    NCER  one cell per frame
    NANR  the sequences
    NCGR  a 160x80 picture of frames 0 and 1 (Hall of Fame, Pal Pad...), encrypted

Optional keys of an entry, mostly to rebuild retail sprites unchanged:

    "palette": "name"          palette file, if not the same name as "pic"
    "layout": "name"           layout of every frame (default "80x80")
    "frames": {"3": {"layout": "name", "offset": [x, y], "flip": true}}
                               per frame: another layout, a shift of the whole frame,
                               shown mirrored (the PNG holds it as shown)
    "empty_cell": true         one more cell with nothing in it, after the frames
    "flat": [0, 3]             frames for the 160x80 picture (default [0, 1], or [0] for one frame)
    "flat": "name"             or a 160x80 PNG of its own in the same folder (retail touch-ups)
    "labels": [...]            the archive's sequence labels, if not CellAnime0, 1...
    "flat_key": "0x4AF3"       the 160x80 picture's encryption seed (any value works in game)

A frame of a sequence can end with "flash" (the screen flashes when it shows; battle
intro), "end" or "play N" (switch to sequence N): the battle reads these
(OpponentTrainerEncounter_HandleAnimFrame, src/battle/battle_controller_opponent.c).

A layout is a list of hardware sprites [x, y, width, height]: the part of the 80x80 frame
each one shows, relative to its center. [x, y, width, height, palette] draws it with another
palette (a pixel of it is stored in the PNG as 16 x palette + its color);
[x, y, width, height, palette, drawX, drawY] draws it somewhere else than where its
pixels are in the frame (retail sprites nudge single pieces by a pixel this way).

Usage:
    trainer_pics.py build front|back TABLE.json OUT.narc --graphics DIR --include DIR
                    --nitrogfx PATH --nitroarc PATH --work DIR [--depfile PATH]
    trainer_pics.py check front|back TABLE.json --graphics DIR --include DIR
    trainer_pics.py extract front|back ARCHIVE --graphics DIR --include DIR --out TABLE.json
                    --nitrogfx PATH     (one-time, from the retail archive)
"""

import argparse
import itertools
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pokedata import DataError, load_json, narc_members, pack, read_defines  # noqa: E402

FRAME = 80                      # frames are 80x80, centered on the sprite's position
FLAT_W, FLAT_H = 160, 80        # the flat picture: frames 0 and 1 side by side
KIND = {
    "front": ("constants/trainer_class.h", "TRAINERCLASS_", "front_pics"),
    "back": ("constants/trainer_class.h", "TRAINER_BACKPIC_", "back_pics"),
}
NOT_PICS = ("TRAINERCLASS_PHONE_",)  # phone contacts share the prefix but have no sprite
LAYOUTS = {
    "80x80": [[-40, -40, 64, 64], [24, -40, 16, 32], [24, -8, 16, 32],
              [-40, 24, 32, 16], [-8, 24, 32, 16], [24, 24, 16, 16]],
}
# hardware sprite sizes: (shape, size) for each width x height
OBJ_SIZES = {(8, 8): (0, 0), (16, 16): (0, 1), (32, 32): (0, 2), (64, 64): (0, 3),
             (16, 8): (1, 0), (32, 8): (1, 1), (32, 16): (1, 2), (64, 32): (1, 3),
             (8, 16): (2, 0), (8, 32): (2, 1), (16, 32): (2, 2), (32, 64): (2, 3)}
SIZE_OF = {v: k for k, v in OBJ_SIZES.items()}
TAGS = {"flash": 1, "end": 0xFFF}   # frame attributes; "play N" is 0x100 + N + 1
NCGR_HEADER = bytes.fromhex("5247434efffe0101000000001000010052414843000000"
                            "00ffffffff0300000010001000000100000000000018000000")
NCBR_HEADER = bytes.fromhex("5247434efffe0001301900001000010052414843201900"
                            "000a0014000300000000000000010000000019000018000000")
NCLR_HEADER = bytes.fromhex("524c434efffe0001280200001000010054544c50180200"
                            "0003000000000000000002000010000000")


# --- PNG and JASC palettes ---------------------------------------------------------------

def read_png(path):
    """(width, height, rows of color indices) of an indexed PNG."""
    with open(path, "rb") as f:
        d = f.read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise DataError("%s: not a PNG" % path)
    pos, idat, ihdr = 8, b"", None
    while pos < len(d):
        n, kind = struct.unpack_from(">I4s", d, pos)
        body = d[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    w, h, depth, ctype, _, _, interlace = ihdr
    if ctype != 3 or interlace:
        raise DataError("%s: must be an indexed-color (paletted) PNG, not interlaced" % path)
    raw, stride, bpp = zlib.decompress(idat), (w * depth + 7) // 8, max(1, depth // 8)
    rows, prev, pos = [], bytearray(stride), 0
    for _ in range(h):
        ftype, line = raw[pos], bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], prev[i - bpp] if i >= bpp else 0
            if ftype == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ftype == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ftype == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
        prev = line
        per = 8 // depth if depth < 8 else 1
        if depth == 8:
            rows.append(list(line[:w]))
        else:
            mask = (1 << depth) - 1
            rows.append([(line[x // per] >> (8 - depth * (x % per + 1))) & mask for x in range(w)])
    return w, h, rows


def write_png(path, rows, colors):
    """Indexed PNG, 4 bits per pixel if every index fits, else 8."""
    depth = 4 if max(max(r) for r in rows) < 16 else 8
    colors = (list(colors) + [(0, 0, 0)] * 256)[:1 << depth]
    w = len(rows[0])
    raw = bytearray()
    for r in rows:
        raw.append(0)
        if depth == 8:
            raw += bytes(r)
        else:
            raw += bytes((r[x] << 4) | (r[x + 1] if x + 1 < w else 0) for x in range(0, w, 2))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    plte = b"".join(bytes(c) for c in colors)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, len(rows), depth, 3, 0, 0, 0))
                + chunk(b"PLTE", plte) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def read_pal(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split()
    if lines[:2] != ["JASC-PAL", "0100"]:
        raise DataError("%s: not a JASC palette" % path)
    n = int(lines[2])
    if not 1 <= n <= 256 or len(lines) < 3 + 3 * n:
        raise DataError("%s: expected %s colors" % (path, lines[2]))
    vals = [int(v) for v in lines[3:3 + 3 * n]]
    if any(not 0 <= v <= 255 for v in vals):
        raise DataError("%s: color values go from 0 to 255" % path)
    return [tuple(vals[i:i + 3]) for i in range(0, len(vals), 3)]


def write_pal(path, colors):
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("JASC-PAL\n0100\n%d\n" % len(colors))
        for c in colors:
            f.write("%d %d %d\n" % c)


def to_555(c):
    return (c[0] >> 3) | (c[1] >> 3) << 5 | (c[2] >> 3) << 10


def from_555(v):
    return tuple(((v >> s) & 31) << 3 | ((v >> s) & 31) >> 2 for s in (0, 5, 10))


# --- the table ---------------------------------------------------------------------------

def constants(kind, include):
    header, prefix, _ = KIND[kind]
    defs = {k: v for k, v in read_defines(os.path.join(include, header), prefix).items() if not k.startswith(NOT_PICS)}
    return sorted(defs, key=defs.get), defs


def parse_frame(f, where):
    """[cell, duration] or [cell, duration, x, y], optionally ending with a tag."""
    if not isinstance(f, list) or not f:
        raise DataError("%s: a frame is [frame, duration] or [frame, duration, x, y]" % where)
    attr = 0
    if isinstance(f[-1], str):
        tag, f = f[-1], f[:-1]
        if tag in TAGS:
            attr = TAGS[tag]
        elif tag.startswith("play ") and tag[5:].isdigit():
            attr = 0x100 + int(tag[5:]) + 1
        else:
            raise DataError("%s: unknown tag %r (\"flash\", \"end\" or \"play N\")" % (where, tag))
    if len(f) not in (2, 4) or not all(isinstance(v, int) and not isinstance(v, bool) for v in f):
        raise DataError("%s: a frame is [frame, duration] or [frame, duration, x, y]" % where)
    if not 0 <= f[1] <= 0xFFFF:
        raise DataError("%s: duration must be 0-65535" % where)
    if len(f) == 4 and not all(-0x8000 <= v < 0x8000 for v in f[2:]):
        raise DataError("%s: x and y must fit in 16 bits" % where)
    return {"cell": f[0], "duration": f[1], "pos": tuple(f[2:]) if len(f) == 4 else None, "attr": attr}


def parse_entry(name, e, layouts, where):
    if not isinstance(e, dict):
        raise DataError("%s: expected an object" % where)
    known = {"pic", "palette", "layout", "frames", "empty_cell", "labels", "anims", "flat", "flat_key"}
    for k in e:
        if k not in known:
            raise DataError("%s: unknown key %r" % (where, k))
    if not isinstance(e.get("pic"), str):
        raise DataError("%s: \"pic\" (the PNG's name) is required" % where)
    layout = e.get("layout", "80x80")
    if layout not in layouts:
        raise DataError("%s: unknown layout %r" % (where, layout))
    frames = {}
    for i, opt in e.get("frames", {}).items():
        if not i.isdigit() or not isinstance(opt, dict):
            raise DataError("%s: \"frames\" maps a frame number to its options" % where)
        for k in opt:
            if k not in ("layout", "offset", "flip"):
                raise DataError("%s: frame %s: unknown key %r" % (where, i, k))
        if opt.get("layout", layout) not in layouts:
            raise DataError("%s: frame %s: unknown layout %r" % (where, i, opt["layout"]))
        off = opt.get("offset", [0, 0])
        if not (isinstance(off, list) and len(off) == 2 and all(isinstance(v, int) for v in off)):
            raise DataError("%s: frame %s: \"offset\" is [x, y]" % (where, i))
        frames[int(i)] = {"layout": opt.get("layout", layout), "offset": tuple(off), "flip": bool(opt.get("flip"))}
    anims = e.get("anims")
    if not isinstance(anims, list) or not anims:
        raise DataError("%s: \"anims\" needs at least one sequence" % where)
    seqs = []
    for si, s in enumerate(anims):
        w = "%s: sequence %d" % (where, si)
        if not isinstance(s, list) or not s:
            raise DataError("%s: a sequence is a list of frames" % w)
        loop = s[-1] == "loop"
        body = s[:-1] if loop else s
        if not body:
            raise DataError("%s: no frames" % w)
        fs = [parse_frame(f, "%s, frame %d" % (w, fi)) for fi, f in enumerate(body)]
        positioned = any(f["pos"] is not None for f in fs)
        if positioned and any(f["pos"] is None for f in fs):
            raise DataError("%s: give x and y for every frame, or for none" % w)
        seqs.append({"loop": loop, "frames": fs, "positioned": positioned})
    labels = e.get("labels")
    if labels is not None and not (isinstance(labels, list) and all(isinstance(x, str) for x in labels)):
        raise DataError("%s: \"labels\" is a list of strings" % where)
    key = e.get("flat_key", "0x0")
    try:
        key = int(key, 16)
    except (TypeError, ValueError):
        key = -1
    if not 0 <= key <= 0xFFFF:
        raise DataError("%s: \"flat_key\" is a hex number up to 0xFFFF" % where)
    flat = e.get("flat")
    if flat is not None and not (isinstance(flat, str) or isinstance(flat, list) and 1 <= len(flat) <= 2
                                 and all(isinstance(v, int) and v >= 0 for v in flat)):
        raise DataError("%s: \"flat\" is one or two frame numbers, or a PNG name" % where)
    return {"name": name, "pic": e["pic"], "palette": e.get("palette", e["pic"]), "layout": layout,
            "frames": frames, "empty_cell": bool(e.get("empty_cell")), "labels": labels, "seqs": seqs,
            "flat": flat, "flat_key": key}


def load_table(kind, path, include):
    doc = load_json(path)
    if not isinstance(doc, dict) or not isinstance(doc.get("pics"), dict):
        raise DataError("%s: expected {\"layouts\": {...}, \"pics\": {...}}" % path)
    layouts = dict(LAYOUTS)
    for lname, objs in doc.get("layouts", {}).items():
        for o in objs:
            if not (isinstance(o, list) and len(o) in (4, 5, 7) and all(isinstance(v, int) for v in o)
                    and (o[2], o[3]) in OBJ_SIZES):
                raise DataError("%s: layout %s: each sprite is [x, y, width, height(, palette(, drawX, drawY))] "
                                "with a hardware size (8 to 64)" % (path, lname))
            if not (-40 <= o[0] and o[0] + o[2] <= 40 and -40 <= o[1] and o[1] + o[3] <= 40):
                raise DataError("%s: layout %s: sprite %r reaches outside the 80x80 frame" % (path, lname, o))
        layouts[lname] = objs
    order, defs = constants(kind, include)
    names = list(doc["pics"])
    for n in names:
        if n not in defs:
            raise DataError("%s: unknown constant %s (%s)" % (path, n, KIND[kind][0]))
    if names != order:
        missing = [n for n in order if n not in doc["pics"]]
        if missing:
            raise DataError("%s: no entry for %s" % (path, ", ".join(missing)))
        raise DataError("%s: entries must be in number order (%s)" % (path, KIND[kind][0]))
    if [defs[n] for n in order] != list(range(len(order))):
        raise DataError("%s: the %s numbers must be 0, 1, 2... with no gaps (the archive is indexed by them)"
                        % (KIND[kind][0], KIND[kind][1]))
    entries = [parse_entry(n, doc["pics"][n], layouts, "%s: %s" % (path, n)) for n in names]
    return entries, layouts


# --- tiles -----------------------------------------------------------------------------

def frame_objs(layout, offset=(0, 0), flip=False):
    """The hardware sprites of a frame: (x, y, w, h, palette) as shown, plus where each
    sprite's pixels are in the 80x80 frame image before mirroring."""
    out = []
    for o in layout:
        x, y, w, h = o[:4]
        pal = o[4] if len(o) > 4 else 0
        dx, dy = (o[5], o[6]) if len(o) == 7 else (x, y)
        sx = -(dx + w) if flip else dx
        out.append({"x": sx + offset[0], "y": dy + offset[1], "w": w, "h": h, "pal": pal, "src": (x + 40, y + 40),
                    "flip": flip})
    return out


def owners(objs):
    """For each pixel of the frame, which sprite holds it: the first one covering it whose
    palette is the pixel's (palette 0 for a transparent pixel; then no sprite needs it)."""
    cover = {}
    for i, o in enumerate(objs):
        sx, sy = o["src"]
        for yy in range(sy, sy + o["h"]):
            for xx in range(sx, sx + o["w"]):
                cover.setdefault((xx, yy), []).append(i)
    return cover


def encode_frame(img, objs, where):
    """80x80 rows (as stored, unmirrored) -> 4bpp tiles in sprite order."""
    cover = owners(objs)
    for yy in range(FRAME):
        for xx in range(FRAME):
            if img[yy][xx] and (xx, yy) not in cover:
                raise DataError("%s: pixel (%d, %d) is outside the frame's sprites (its layout)" % (where, xx, yy))
    out = bytearray()
    for i, o in enumerate(objs):
        sx, sy = o["src"]
        for ty in range(0, o["h"], 8):
            for tx in range(0, o["w"], 8):
                for yy in range(sy + ty, sy + ty + 8):
                    row = []
                    for xx in range(sx + tx, sx + tx + 8):
                        v = img[yy][xx]
                        mine = v and v >> 4 == o["pal"] and next(j for j in cover[(xx, yy)]
                                                                if objs[j]["pal"] == v >> 4) == i
                        if v and not any(objs[j]["pal"] == v >> 4 for j in cover[(xx, yy)]):
                            raise DataError("%s: pixel (%d, %d) uses palette %d, which no sprite there has"
                                            % (where, xx, yy, v >> 4))
                        row.append(v & 15 if mine else 0)
                    out += bytes(row[k] | row[k + 1] << 4 for k in range(0, 8, 2))
    return bytes(out)


def decode_frame(tiles, objs):
    """Inverse of encode_frame: sprites drawn with the first one on top."""
    img = [[0] * FRAME for _ in range(FRAME)]
    pos, parts = 0, []
    for o in objs:
        n = o["w"] * o["h"] // 2
        parts.append(tiles[pos:pos + n])
        pos += n
    for o, data in reversed(list(zip(objs, parts))):
        sx, sy = o["src"]
        tw = o["w"] // 8
        for t in range(len(data) // 32):
            bx, by = sx + (t % tw) * 8, sy + (t // tw) * 8
            for r in range(8):
                for k in range(4):
                    b = data[t * 32 + r * 4 + k]
                    for half, v in ((0, b & 15), (1, b >> 4)):
                        if v:
                            img[by + r][bx + k * 2 + half] = o["pal"] << 4 | v
    return img


def mirror(img):
    return [list(reversed(r)) for r in img]


def flat_data(rows, key, where):
    """The 160x80 picture: scanned 4bpp, encrypted back to front from `key` (the game takes
    the key from the last word, so the last 4 pixels must be transparent)."""
    rows = [[v & 15 for v in r] for r in rows]
    if any(rows[-1][-4:]):
        raise DataError("%s: the bottom-right 4 pixels of the 160x80 picture (of its second frame) must be "
                        "transparent" % where)
    data = bytearray()
    for r in rows:
        data += bytes(r[x] | r[x + 1] << 4 for x in range(0, FLAT_W, 2))
    words = list(struct.unpack("<%dH" % (len(data) // 2), data))
    for i in range(len(words) - 1, -1, -1):
        words[i] ^= key & 0xFFFF
        key = (key * 1103515245 + 24691) & 0xFFFFFFFF
    return struct.pack("<%dH" % len(words), *words)


def unflat(data):
    """Inverse of flat_data: (rows, key)."""
    words = list(struct.unpack("<%dH" % (len(data) // 2), data))
    key = start = words[-1]
    for i in range(len(words) - 1, -1, -1):
        words[i] ^= key & 0xFFFF
        key = (key * 1103515245 + 24691) & 0xFFFFFFFF
    raw = struct.pack("<%dH" % len(words), *words)
    rows = [[(raw[y * 80 + x // 2] >> (4 * (x & 1))) & 15 for x in range(FLAT_W)] for y in range(FLAT_H)]
    return rows, start


# --- NCER / NANR as nitrogfx JSON ------------------------------------------------------------

def cell_json(objs):
    if not objs:
        return {"cellAttrs": {"hFlip": False, "vFlip": False, "hvFlip": False, "boundingRect": True,
                              "boundingSphereRadius": 0},
                "maxX": 0, "maxY": 0, "minX": 0, "minY": 0, "oamCount": 0, "OAM": []}
    minx, miny = min(o["x"] for o in objs), min(o["y"] for o in objs)
    maxx, maxy = max(o["x"] + o["w"] for o in objs) - 1, max(o["y"] + o["h"] for o in objs) - 1
    r = (math.isqrt(max(-minx, maxx + 1) ** 2 + max(-miny, maxy + 1) ** 2) + 3) // 4
    oam, char = [], 0
    for o in objs:
        shape, size = OBJ_SIZES[(o["w"], o["h"])]
        oam.append({"Attr0": {"YCoordinate": o["y"], "Rotation": False, "SizeDisable": False, "Mode": 0,
                              "Mosaic": False, "Colours": 16, "Shape": shape},
                    "Attr1": {"XCoordinate": o["x"], "RotationScaling": 8 if o.get("flip") else 0, "Size": size},
                    "Attr2": {"CharName": char, "Priority": 0, "Palette": o["pal"]}})
        char += o["w"] * o["h"] // 64 // 2
    return {"cellAttrs": {"hFlip": objs[0]["flip"], "vFlip": False, "hvFlip": False, "boundingRect": True,
                          "boundingSphereRadius": r},
            "maxX": maxx, "maxY": maxy, "minX": minx, "minY": miny, "oamCount": len(objs), "OAM": oam}


def labels_of(e):
    return e["labels"] if e["labels"] is not None else ["CellAnime%d" % i for i in range(len(e["seqs"]))]


def ncer_json(e, frame_objs_list, sizes):
    cells = [cell_json(objs) for objs in frame_objs_list]
    transfer, off = [], 0
    for s in sizes:
        transfer.append({"offset": off, "size": s})
        off += s
    if e["empty_cell"]:
        cells.append(cell_json([]))
        transfer.append({"offset": off, "size": 0})
    labels = labels_of(e)
    return {"labelEnabled": True, "dontPadKbec": False, "extended": True, "vramTransferEnabled": True,
            "ucatEnabled": True, "cellCount": len(cells), "mappingType": 1, "cells": cells,
            "labels": labels, "labelCount": len(labels), "vramTransferMaxSize": max(sizes),
            "transferData": transfer, "cellAttributes": [0] * len(cells)}


def nanr_json(e):
    results, index, seqs, attrs = [], {}, [], []
    for s in e["seqs"]:
        data = []
        for f in s["frames"]:
            r = ({"resultType": 2, "index": f["cell"], "positionX": f["pos"][0], "positionY": f["pos"][1]}
                 if s["positioned"] else {"resultType": 0, "index": f["cell"]})
            k = tuple(r.values())
            if k not in index:
                index[k] = len(results)
                results.append(r)
            data.append({"frameDelay": f["duration"], "resultId": index[k]})
            attrs.append(f["attr"])
        seqs.append({"frameCount": len(data), "loopStartFrame": 0, "animationElement": 2 if s["positioned"] else 0,
                     "animationType": 1, "playbackMode": 2 if s["loop"] else 1, "frameData": data})
    labels = labels_of(e)
    return {"labelEnabled": True, "uaatEnabled": True, "sequenceCount": len(seqs), "frameCount": len(attrs),
            "sequences": seqs, "animationResults": results, "resultCount": len(results), "labels": labels,
            "labelCount": len(labels),
            "uaatData": {"sequenceAttributes": [0] * len(seqs), "frameAttributes": attrs}}


# --- building ----------------------------------------------------------------------------

def strip(path, where):
    w, h, rows = read_png(path)
    if w != FRAME or h % FRAME or not h:
        raise DataError("%s: must be %d wide and a multiple of %d tall (one %dx%d frame under another), "
                        "not %dx%d" % (where, FRAME, FRAME, FRAME, FRAME, w, h))
    return [rows[i:i + FRAME] for i in range(0, h, FRAME)]


def entry_files(kind, e, layouts, graphics, read):
    """The five member files of one entry; `read` collects the source paths."""
    where = e["name"]
    png = os.path.join(graphics, KIND[kind][2], e["pic"] + ".png")
    pal = os.path.join(graphics, "palettes", e["palette"] + ".pal")
    for p in (png, pal):
        if not os.path.exists(p):
            raise DataError("%s: %s is missing" % (where, p))
        read.append(p)
    frames = strip(png, "%s (%s)" % (where, png))
    colors = read_pal(pal)
    bad = [i for i in e["frames"] if i >= len(frames)]
    if bad:
        raise DataError("%s: \"frames\" has frame %d but the PNG has %d" % (where, bad[0], len(frames)))
    ncells = len(frames) + e["empty_cell"]
    for si, s in enumerate(e["seqs"]):
        for f in s["frames"]:
            if not 0 <= f["cell"] < ncells:
                raise DataError("%s: sequence %d shows frame %d; there are %d" % (where, si, f["cell"], ncells))
            if f["attr"] > 0x100 and f["attr"] != 0xFFF and f["attr"] - 0x101 >= len(e["seqs"]):
                raise DataError("%s: sequence %d plays sequence %d, which doesn't exist"
                                % (where, si, f["attr"] - 0x101))
    tiles, objs_list, sizes = b"", [], []
    for i, img in enumerate(frames):
        opt = e["frames"].get(i, {"layout": e["layout"], "offset": (0, 0), "flip": False})
        objs = frame_objs(layouts[opt["layout"]], opt["offset"], opt["flip"])
        if any(v >> 4 >= max(1, len(colors) // 16) for r in img for v in r if v):
            raise DataError("%s: frame %d uses colors beyond the palette's %d" % (where, i, len(colors)))
        data = encode_frame(mirror(img) if opt["flip"] else img, objs, "%s, frame %d" % (where, i))
        tiles += data
        objs_list.append(objs)
        sizes.append(len(data))
    ncgr = bytearray(NCGR_HEADER)
    struct.pack_into("<I", ncgr, 8, len(NCGR_HEADER) + len(tiles))
    struct.pack_into("<I", ncgr, 0x14, 0x20 + len(tiles))
    struct.pack_into("<I", ncgr, 0x28, len(tiles))
    if isinstance(e["flat"], str):
        path = os.path.join(graphics, KIND[kind][2], e["flat"] + ".png")
        read.append(path)
        w, h, flat = read_png(path)
        if (w, h) != (FLAT_W, FLAT_H):
            raise DataError("%s: %s must be %dx%d" % (where, path, FLAT_W, FLAT_H))
    else:
        pick = e["flat"] or ([0, 1] if len(frames) > 1 else [0])
        if max(pick) >= len(frames):
            raise DataError("%s: \"flat\" uses frame %d; there are %d" % (where, max(pick), len(frames)))
        halves = [frames[i] for i in pick] + [[[0] * FRAME for _ in range(FRAME)]]
        flat = [a + b for a, b in zip(halves[0], halves[1])]
    ncbr = NCBR_HEADER + flat_data(flat, e["flat_key"], where)
    nclr = NCLR_HEADER + struct.pack("<256H", *([to_555(c) for c in colors] + [0] * (256 - len(colors))))
    return bytes(ncgr) + tiles, nclr, ncer_json(e, objs_list, sizes), nanr_json(e), ncbr


def nitro(nitrogfx, doc, out, work):
    src = out + ".json"
    with open(src, "w", encoding="utf-8") as f:
        json.dump(doc, f)
    subprocess.run([os.path.abspath(nitrogfx), src, out], check=True, cwd=work)
    with open(out, "rb") as f:
        return f.read()


def build(kind, table, out, graphics, include, nitrogfx, nitroarc, work, depfile=None):
    entries, layouts = load_table(kind, table, include)
    work = os.path.abspath(work)
    tmp = os.path.join(work, kind + "_files")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    members, read = [], [table]
    for i, e in enumerate(entries):
        ncgr, nclr, ncer, nanr, ncbr = entry_files(kind, e, layouts, graphics, read)
        members += [ncgr, nclr, nitro(nitrogfx, ncer, os.path.join(tmp, "%03d.NCER" % i), tmp),
                    nitro(nitrogfx, nanr, os.path.join(tmp, "%03d.NANR" % i), tmp), ncbr]
    pack(members, out, nitroarc, work)
    if depfile:
        with open(depfile, "w", encoding="utf-8") as f:
            f.write("%s: %s\n" % (out.replace(" ", "\\ "), " ".join(p.replace(" ", "\\ ") for p in read)))


def check(kind, table, graphics, include):
    entries, layouts = load_table(kind, table, include)
    for e in entries:
        entry_files(kind, e, layouts, graphics, [])
    return len(entries)


# --- extracting the retail archives (one-time) -------------------------------------------

def nitro_json(nitrogfx, data, ext, work):
    p = os.path.join(work, "member." + ext)
    with open(p, "wb") as f:
        f.write(data)
    subprocess.run([os.path.abspath(nitrogfx), p, p + ".json"], check=True)
    with open(p + ".json", encoding="utf-8") as f:
        return json.load(f)


def place(sprites):
    """A layout for sprites drawn at (x, y): each keeps its pixels where it is drawn, unless
    that overlaps an earlier one (Castle Valet); then they go to the nearest free spot of the
    frame, so no pixel is hidden in the PNG. Keeps as many sprites in place as it can."""
    def free(r, taken):
        x, y, w, h = r
        return -40 <= x and x + w <= 40 and -40 <= y and y + h <= 40 and not any(
            x < tx + tw and tx < x + w and y < ty + th and ty < y + h for tx, ty, tw, th in taken)
    n = len(sprites)
    for k in range(n, -1, -1):
        for kept in itertools.combinations(range(n), k):
            spot, taken = {}, []
            for i in kept:
                if not free(sprites[i][:4], taken):
                    break
                taken.append(sprites[i][:4])
                spot[i] = sprites[i][:2]
            else:
                for i in range(n):
                    if i in spot:
                        continue
                    x, y, w, h, _ = sprites[i]
                    spots = sorted(((sx, sy) for sx in range(-40, 41 - w, 8) for sy in range(-40, 41 - h, 8)),
                                   key=lambda s: abs(s[0] - x) + abs(s[1] - y))
                    found = next((s for s in spots if free((s[0], s[1], w, h), taken)), None)
                    if found is None:
                        break
                    taken.append((found[0], found[1], w, h))
                    spot[i] = found
                else:
                    return [[spot[i][0], spot[i][1], w, h] + ([p, x, y] if spot[i] != (x, y) else [p] if p else [])
                            for i, (x, y, w, h, p) in enumerate(sprites)]
    raise DataError("the sprites don't fit in an 80x80 frame")


def cell_frame(cell, layouts, extra, pic):
    """(layout name, offset, flip) for a retail cell; adds a layout to `extra` if no known one
    fits: the first with the same sprite sizes, with the sprites that are moved drawn elsewhere,
    or else the cell's own sprites."""
    flip = cell["OAM"][0]["Attr1"]["RotationScaling"] == 8
    if any(o["Attr1"]["RotationScaling"] != (8 if flip else 0) for o in cell["OAM"]):
        raise DataError("%s: a cell with some sprites mirrored and some not" % pic)
    seen = [(o["Attr1"]["XCoordinate"], o["Attr0"]["YCoordinate"], SIZE_OF[(o["Attr0"]["Shape"], o["Attr1"]["Size"])],
             o["Attr2"]["Palette"]) for o in cell["OAM"]]
    near = None
    for name, lay in layouts.items():
        base = frame_objs(lay, (0, 0), flip)
        if [(b["w"], b["h"], b["pal"]) for b in base] != [(s[2][0], s[2][1], s[3]) for s in seen]:
            continue
        dx, dy = seen[0][0] - base[0]["x"], seen[0][1] - base[0]["y"]
        moved = [(s[0] - b["x"] - dx, s[1] - b["y"] - dy) for s, b in zip(seen, base)]
        if not any(m != (0, 0) for m in moved):
            return name, (dx, dy), flip
        if near is None:
            near = (lay, moved, (dx, dy))
    if near:
        lay, moved, off = near
        new = []
        for o, (mx, my) in zip(lay, moved):
            x, y, w, h = o[:4]
            pal = o[4] if len(o) > 4 else 0
            ox, oy = (o[5], o[6]) if len(o) == 7 else (x, y)
            ox += -mx if flip else mx
            oy += my
            new.append([x, y, w, h] + ([pal, ox, oy] if (ox, oy) != (x, y) else [pal] if pal else []))
    else:
        off, new = (0, 0), place([(x, y, w, h, p) for x, y, (w, h), p in seen])
    for name, lay in extra.items():
        if lay == new:
            return name, off, flip
    name = pic if pic not in extra else "%s_%d" % (pic, sum(k.startswith(pic) for k in extra) + 1)
    layouts[name] = extra[name] = new
    return name, off, flip


def extract(kind, archive, graphics, include, out, nitrogfx):
    order, defs = constants(kind, include)
    files = narc_members(archive)
    if len(files) != 5 * len(order):
        raise DataError("%s has %d files, expected 5 per %s (%d)" % (archive, len(files), KIND[kind][1], len(order)))
    os.makedirs(os.path.join(graphics, KIND[kind][2]), exist_ok=True)
    os.makedirs(os.path.join(graphics, "palettes"), exist_ok=True)
    work = os.path.join(os.path.dirname(os.path.abspath(out)), ".extract")
    os.makedirs(work, exist_ok=True)
    layouts, extra, pics, prefix = dict(LAYOUTS), {}, {}, KIND[kind][1]
    # palettes share one folder: a back sprite named like a front one gets "<pic>_back"
    front_pics = {n[len(KIND["front"][1]):].lower() for n in constants("front", include)[0]}
    try:
        for n, name in enumerate(order):
            ncgr, nclr, ncer, nanr, ncbr = files[5 * n:5 * n + 5]
            cells = nitro_json(nitrogfx, ncer, "NCER", work)
            anim = nitro_json(nitrogfx, nanr, "NANR", work)
            pic = name[len(prefix):].lower()
            entry = {"pic": pic}
            pal_name = pic
            if kind == "back" and pic in front_pics:
                pal_name = entry["palette"] = pic + "_back"
            colors = [from_555(v) for v in struct.unpack_from("<256H", nclr, 0x28)]
            # retail palettes keep stray colors after the 16 drawn ones; keep them so nothing changes
            used = max([i for i, c in enumerate(colors) if c != (0, 0, 0)] + [15]) + 1
            write_pal(os.path.join(graphics, "palettes", pal_name + ".pal"), colors[:used])
            # cells -> frames
            frames_opt, tiles, pos = {}, ncgr[0x30:], 0
            real = [c for c in cells["cells"] if c["OAM"]]
            if any(not c["OAM"] for c in cells["cells"][:len(real)]):
                raise DataError("%s: an empty cell before the last" % name)
            if len(cells["cells"]) == len(real) + 1:
                entry["empty_cell"] = True
            elif len(cells["cells"]) != len(real):
                raise DataError("%s: more than one empty cell" % name)
            imgs, frame_layouts = [], []
            for i, c in enumerate(real):
                lname, off, flip = cell_frame(c, layouts, extra, pic)
                frame_layouts.append(lname)
                objs = frame_objs(layouts[lname], off, flip)
                size = sum(o["w"] * o["h"] // 2 for o in objs)
                img = decode_frame(tiles[pos:pos + size], objs)
                pos += size
                imgs.append(mirror(img) if flip else img)
                opt = {}
                if off != (0, 0):
                    opt["offset"] = list(off)
                if flip:
                    opt["flip"] = True
                frames_opt[i] = (lname, opt)
            if pos != len(tiles):
                raise DataError("%s: the cells use %d bytes of %d" % (name, pos, len(tiles)))
            common = max(set(frame_layouts), key=frame_layouts.count)
            if common != "80x80":
                entry["layout"] = common
            fopts = {}
            for i, (lname, opt) in frames_opt.items():
                if lname != common:
                    opt = dict(layout=lname, **opt)
                if opt:
                    fopts[str(i)] = opt
            if fopts:
                entry["frames"] = fopts
            labels = ["CellAnime%d" % i for i in range(anim["sequenceCount"])]
            if anim["labels"] != labels:
                entry["labels"] = anim["labels"]
            if cells["labels"] != anim["labels"]:
                raise DataError("%s: cell and animation labels differ" % name)
            entry["anims"] = anims_of(anim, name)
            rows, key = unflat(ncbr[0x30:])
            halves = [[r[:FRAME] for r in rows], [r[FRAME:] for r in rows]]
            low = [[[v & 15 for v in r] for r in img] for img in imgs]
            left = [i for i, img in enumerate(low) if img == halves[0]]
            right = [i for i, img in enumerate(low) if img == halves[1]]
            blank = not any(any(r) for r in halves[1])
            if left and (blank or right):
                pick = [left[0]] + ([] if blank else [1 if 1 in right else right[0]])
                if pick != ([0, 1] if len(imgs) > 1 else [0]):
                    entry["flat"] = pick
            else:
                entry["flat"] = pic + "_flat"
                write_png(os.path.join(graphics, KIND[kind][2], pic + "_flat.png"), rows, colors)
            entry["flat_key"] = "0x%04X" % key
            write_png(os.path.join(graphics, KIND[kind][2], pic + ".png"), [r for img in imgs for r in img], colors)
            pics[name] = entry
    finally:
        shutil.rmtree(work, ignore_errors=True)
    doc = {"layouts": extra, "pics": pics} if extra else {"pics": pics}
    write_table(out, doc)


def anims_of(anim, name):
    attrs = iter(anim["uaatData"]["frameAttributes"])
    if any(anim["uaatData"]["sequenceAttributes"]):
        raise DataError("%s: sequence attributes aren't supported" % name)
    out = []
    for s in anim["sequences"]:
        if s["loopStartFrame"] or s["animationType"] != 1 or s["playbackMode"] not in (1, 2) \
                or s["animationElement"] not in (0, 2):
            raise DataError("%s: unsupported sequence %r" % (name, {k: v for k, v in s.items() if k != "frameData"}))
        seq = []
        for f in s["frameData"]:
            r = anim["animationResults"][f["resultId"]]
            fr = [r["index"], f["frameDelay"]]
            if s["animationElement"] == 2:
                fr += [r["positionX"], r["positionY"]]
            a = next(attrs)
            if a:
                tag = {v: k for k, v in TAGS.items()}.get(a) or ("play %d" % (a - 0x101) if a > 0x100 else None)
                if tag is None:
                    raise DataError("%s: unknown frame attribute %d" % (name, a))
                fr.append(tag)
            seq.append(fr)
        if s["playbackMode"] == 2:
            seq.append("loop")
        out.append(seq)
    return out


def write_table(path, doc):
    """JSON with one line per sequence, frame option and layout sprite."""
    def dump(v):
        return json.dumps(v, ensure_ascii=False)
    lines = ["{"]
    if "layouts" in doc:
        lines.append('  "layouts": {')
        ls = list(doc["layouts"].items())
        for i, (k, objs) in enumerate(ls):
            lines.append('    %s: [%s]%s' % (dump(k), ", ".join(dump(o) for o in objs), "," if i < len(ls) - 1 else ""))
        lines.append("  },")
    lines.append('  "pics": {')
    items = list(doc["pics"].items())
    for i, (k, e) in enumerate(items):
        parts = []
        for key, v in e.items():
            if key == "anims":
                seqs = ",\n".join("        " + dump(s) for s in v)
                parts.append('      "anims": [\n%s\n      ]' % seqs)
            elif key == "frames":
                fr = ",\n".join("        %s: %s" % (dump(n), dump(o)) for n, o in v.items())
                parts.append('      "frames": {\n%s\n      }' % fr)
            else:
                parts.append("      %s: %s" % (dump(key), dump(v)))
        lines.append("    %s: {\n%s\n    }%s" % (dump(k), ",\n".join(parts), "," if i < len(items) - 1 else ""))
    lines += ["  }", "}"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("build", "check", "extract"))
    ap.add_argument("kind", choices=("front", "back"))
    ap.add_argument("input", help="the table (build, check) or the retail archive (extract)")
    ap.add_argument("output", nargs="?", help="the archive to write (build)")
    ap.add_argument("--graphics", required=True, help="graphics/trainers")
    ap.add_argument("--include", required=True, help="the repo's include/ directory")
    ap.add_argument("--nitrogfx")
    ap.add_argument("--nitroarc")
    ap.add_argument("--work", help="scratch directory (build)")
    ap.add_argument("--depfile", help="write the PNG and palette files read, for the build system")
    ap.add_argument("--out", help="table to write (extract)")
    a = ap.parse_args(argv)
    try:
        if a.action == "build":
            if not (a.output and a.nitrogfx and a.nitroarc):
                ap.error("build needs OUT.narc, --nitrogfx and --nitroarc")
            build(a.kind, a.input, a.output, a.graphics, a.include, a.nitrogfx, a.nitroarc,
                  a.work or os.path.dirname(os.path.abspath(a.output)), a.depfile)
        elif a.action == "check":
            n = check(a.kind, a.input, a.graphics, a.include)
            print("%s: %d %s sprites OK" % (a.input, n, a.kind))
        else:
            if not (a.out and a.nitrogfx):
                ap.error("extract needs --out and --nitrogfx")
            extract(a.kind, a.input, a.graphics, a.include, a.out, a.nitrogfx)
    except DataError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
