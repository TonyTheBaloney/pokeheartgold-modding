# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26
"""Map textures as files: one folder per texture set (gen4map 1.2, docs/modding/area-textures.md).

The game loads an area's map textures from NARC a/0/4/4: member N, named by the
area header (a/0/4/2), is an NSBTX whose textures and palettes the terrain models'
materials name. The build makes that archive from

    data/area_textures/NNN/        NNN = member number
        textures.json              the textures and palettes, in file order
        textures/<name>.png        indexed; a pixel's value is the texel's value
        palettes/<name>.pal        JASC

textures.json, one entry per line:

    {"textures": [
      {"name": "tree01gs", "format": "palette16", "transparent": true, "palette": "tree01"},
      ...],
     "palettes": [
      {"name": "tree01"},
      {"name": "grass02_pl", "four_color": true},
      ...]}

"format" is palette4, palette16, palette256, a3i5 or a5i3; "transparent" makes
color 0 see-through (palette formats). "palette" is the palette the terrain draws
the texture with: the PNG shows its colors, nothing else reads it. "four_color"
marks palettes for palette4 textures. In a3i5 / a5i3 PNGs a pixel holds the color
index in its low 5 / 3 bits and the opacity in the rest, as in the texture, and the
PNG's palette shows each value with its color and opacity.

    mapkit areatex migrate            one-time: files/a/0/4/4 -> data/area_textures
    mapkit areatex pack OUT           (the build) the archive from the folders
    mapkit areatex add SET IMAGE.png  a new texture from an indexed PNG
    mapkit areatex color [SET]        refresh the PNGs' colors after editing palettes
    mapkit areatex list SET           textures, sizes, formats and VRAM use
"""

import json
import os
import re
import struct
import zlib

from . import landdata, layouts, nitro, nsbtx
from .sprites import read_png

PREBUILT = "files/a/0/4/4"
DEFAULT_DIR = "data/area_textures"
MANIFEST = "data/gen4map.json"
PALETTE_FORMATS = {"palette4": 2, "palette16": 4, "palette256": 8}   # bits per texel
ALPHA_FORMATS = {"a3i5": 5, "a5i3": 3}                               # bits of color index


class AreaTexError(Exception):
    pass


def folder(root):
    try:
        with open(os.path.join(root, MANIFEST), encoding="utf-8") as f:
            return os.path.join(root, json.load(f)["paths"].get("area_textures", DEFAULT_DIR))
    except (OSError, KeyError, ValueError):
        return os.path.join(root, DEFAULT_DIR)


def set_dirs(root):
    """The set folders in member order; their names must be 000, 001, ... with no gap."""
    base = folder(root)
    if not os.path.isdir(base):
        raise AreaTexError("%s doesn't exist" % os.path.relpath(base, root))
    names = sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n)))
    for i, n in enumerate(names):
        if n != "%03d" % i:
            raise AreaTexError("%s: expected folder %03d, found %s (sets are numbered from 000 without gaps)"
                               % (os.path.relpath(base, root), i, n))
    return [os.path.join(base, n) for n in names]


# --- textures.json --------------------------------------------------------------------------------

def load_doc(d):
    with open(os.path.join(d, "textures.json"), encoding="utf-8") as f:
        return json.load(f)


def save_doc(d, doc):
    lines = ['{"textures": [']
    lines += ["  %s%s" % (json.dumps(t), "," if i < len(doc["textures"]) - 1 else "") for i, t in enumerate(doc["textures"])]
    lines += ['], "palettes": [']
    lines += ["  %s%s" % (json.dumps(p), "," if i < len(doc["palettes"]) - 1 else "") for i, p in enumerate(doc["palettes"])]
    lines += ["]}"]
    with open(os.path.join(d, "textures.json"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# --- palettes (JASC) -------------------------------------------------------------------------------

def read_pal(path):
    with open(path, encoding="ascii") as f:
        lines = f.read().split()
    if lines[:2] != ["JASC-PAL", "0100"]:
        raise AreaTexError("%s is not a JASC palette" % path)
    n = int(lines[2])
    vals = [int(v) for v in lines[3:3 + 3 * n]]
    if len(vals) != 3 * n or any(not 0 <= v <= 255 for v in vals):
        raise AreaTexError("%s: expected %d colors of 0-255 values" % (path, n))
    return [(vals[3 * i] >> 3) | (vals[3 * i + 1] >> 3) << 5 | (vals[3 * i + 2] >> 3) << 10 for i in range(n)]


def _c8(c5):
    return c5 << 3 | c5 >> 2


def rgb(c):
    return _c8(c & 31), _c8(c >> 5 & 31), _c8(c >> 10 & 31)


def write_pal(path, colors):
    with open(path, "w", encoding="ascii", newline="") as f:
        f.write("JASC-PAL\r\n0100\r\n%d\r\n" % len(colors) + "".join("%d %d %d\r\n" % rgb(c) for c in colors))


# --- PNG ------------------------------------------------------------------------------------------

def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def png_bytes(w, h, values, entries):
    """An 8-bit indexed PNG; entries are (r, g, b, a) per palette index."""
    raw = b"".join(b"\0" + bytes(values[y * w:(y + 1) * w]) for y in range(h))
    out = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
    out += _chunk(b"PLTE", b"".join(bytes(e[:3]) for e in entries))
    alpha = bytes(e[3] for e in entries).rstrip(b"\xff")
    if alpha:
        out += _chunk(b"tRNS", alpha)
    return out + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b"")


def display_entries(fmt, colors, transparent):
    """What a PNG's palette shows for every value a texel of this format can take."""
    if colors is None:   # no palette known: shades of gray
        n = 1 << (PALETTE_FORMATS.get(fmt) or ALPHA_FORMATS[fmt])
        colors = [(v * 31 // max(1, n - 1)) * 0x421 for v in range(n)]
    if fmt in ALPHA_FORMATS:
        ibits = ALPHA_FORMATS[fmt]
        top = (1 << (8 - ibits)) - 1
        out = []
        for v in range(256):
            i = v & ((1 << ibits) - 1)
            out.append(rgb(colors[i] if i < len(colors) else 0) + ((v >> ibits) * 255 // top,))
        return out
    n = 1 << PALETTE_FORMATS[fmt]
    out = [rgb(colors[i] if i < len(colors) else 0) + (255,) for i in range(n)]
    if transparent:
        out[0] = out[0][:3] + (0,)
    return out


def texture_png(tex, colors):
    return png_bytes(tex.width, tex.height, tex.indices(), display_entries(tex.format, colors, tex.color0_transparent))


def read_texture(path, entry):
    """A textures.json entry and its PNG -> nsbtx.Texture."""
    w, h, kind, rows, _, _ = read_png(path)
    if kind != "indexed":
        raise AreaTexError("%s: save it as an indexed PNG (the pixel values are the texture's)" % path)
    fmt = entry["format"]
    if fmt not in PALETTE_FORMATS and fmt not in ALPHA_FORMATS:
        raise AreaTexError("%s: format %r (palette4, palette16, palette256, a3i5 or a5i3)" % (path, fmt))
    values = [v for row in rows for v in row]
    limit = 1 << PALETTE_FORMATS.get(fmt, 8)
    over = max(values) if values else 0
    if over >= limit:
        raise AreaTexError("%s: uses color %d; %s has %d colors" % (path, over, fmt, limit))
    try:
        return nsbtx.Texture.from_indices(entry["name"], fmt, w, h, bool(entry.get("transparent")), values)
    except nsbtx.NsbtxError as ex:
        raise AreaTexError("%s: %s" % (path, ex))


# --- building -------------------------------------------------------------------------------------

def tex_path(d, name):
    return os.path.join(d, "textures", name + ".png")


def pal_path(d, name):
    return os.path.join(d, "palettes", name + ".pal")


def read_set(d):
    """A set folder -> (textures, palettes) for nsbtx.write."""
    doc = load_doc(d)
    textures = [read_texture(tex_path(d, t["name"]), t) for t in doc["textures"]]
    palettes = []
    for p in doc["palettes"]:
        colors = read_pal(pal_path(d, p["name"]))
        if p.get("four_color") and len(colors) != 4:
            raise AreaTexError("%s: a four_color palette has 4 colors, not %d" % (pal_path(d, p["name"]), len(colors)))
        palettes.append(nsbtx.Palette(p["name"], colors, bool(p.get("four_color"))))
    return textures, palettes


def build_set(d):
    try:
        return nsbtx.write(*read_set(d))
    except nsbtx.NsbtxError as ex:
        raise AreaTexError("%s: %s" % (d, ex))


def file_list(root):
    out = []
    for d in set_dirs(root):
        doc = load_doc(d)
        out += [os.path.join(d, "textures.json")]
        out += [tex_path(d, t["name"]) for t in doc["textures"]]
        out += [pal_path(d, p["name"]) for p in doc["palettes"]]
    return out


def pack(root, out_narc, depfile=None):
    dirs = set_dirs(root)
    data = landdata.narc_bytes([build_set(d) for d in dirs])
    with open(out_narc, "wb") as f:
        f.write(data)
    if depfile:
        # the folders too: a new set or file changes them, so the build notices without reconfiguring
        deps = [folder(root)] + dirs + [os.path.join(d, s) for d in dirs for s in ("textures", "palettes")]
        deps += file_list(root)
        esc = lambda p: p.replace("\\", "/").replace(" ", "\\ ")  # noqa: E731
        with open(depfile, "w", encoding="utf-8") as f:
            f.write("%s: \\\n" % esc(out_narc) + " \\\n".join("  " + esc(os.path.abspath(p)) for p in deps) + "\n")


_sets = {}


def texture_set(root, set_id):
    """nitro.TextureSet of a set, for drawing (terrain export, the map editor)."""
    key = (os.path.abspath(root), set_id)
    if key not in _sets:
        base = folder(root)
        d = os.path.join(base, "%03d" % set_id)
        if os.path.isdir(d):
            data = build_set(d)
        else:   # a project that keeps the binary archive
            with open(os.path.join(root, PREBUILT), "rb") as f:
                members = landdata.narc_members(f.read())
            if not 0 <= set_id < len(members):
                raise AreaTexError("no map texture set %d" % set_id)
            data = members[set_id]
        _sets[key] = nitro.load_nsbtx(data)
    return _sets[key]


# --- export (migration) ---------------------------------------------------------------------------

def terrain_palettes(root):
    """{set id: {texture: palette}}: the palette terrain materials draw each texture with."""
    from . import terrain
    paths = terrain.manifest(root)["paths"]
    maps_dir = os.path.join(root, paths["maps"])
    by_name, _ = layouts.map_ids(root)
    out, models, lays = {}, {}, {}
    for name in sorted(os.listdir(maps_dir)):
        p = os.path.join(maps_dir, name, "map.json")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            m = json.load(f)
        set_id = terrain.Area(root, m["area_data"]).texture_id
        if m["layout"] not in lays:
            lays[m["layout"]] = layouts.load(root, m["layout"])
        lay = lays[m["layout"]]
        for i, land in enumerate(lay.land_ids):
            owner = lay.header_ids[i] if lay.header_ids else None
            if land is None or (owner is not None and by_name.get(m["id"]) != owner):
                continue
            if land not in models:
                path = os.path.join(terrain.cell_dir(root, land), "model.nsbmd")
                models[land] = nitro.load_nsbmd(open(path, "rb").read())[0] if os.path.exists(path) else []
            for mdl in models[land]:
                for mt in mdl.materials:
                    if mt.texture and mt.palette:
                        out.setdefault(set_id, {}).setdefault(mt.texture, mt.palette)
    return out


def export_set(data, d, shown_with=None):
    """One NSBTX -> a set folder."""
    textures, palettes = nsbtx.read(data)
    by_name = {p.name: p for p in palettes}
    os.makedirs(os.path.join(d, "textures"), exist_ok=True)
    os.makedirs(os.path.join(d, "palettes"), exist_ok=True)
    doc = {"textures": [], "palettes": []}
    for t in textures:
        pal = (shown_with or {}).get(t.name)
        if pal not in by_name:
            pal = next((n for n in (t.name, t.name + "_pl") if n in by_name), None)
        entry = {"name": t.name, "format": t.format}
        if t.color0_transparent:
            entry["transparent"] = True
        entry["palette"] = pal
        doc["textures"].append(entry)
        with open(tex_path(d, t.name), "wb") as f:
            f.write(texture_png(t, by_name[pal].colors if pal else None))
    for p in palettes:
        doc["palettes"].append({"name": p.name, "four_color": True} if p.four_color else {"name": p.name})
        write_pal(pal_path(d, p.name), p.colors)
    save_doc(d, doc)


def migrate(root):
    """files/a/0/4/4 -> data/area_textures (checks the round trip first)."""
    src = os.path.join(root, PREBUILT)
    with open(src, "rb") as f:
        data = f.read()
    members = landdata.narc_members(data)
    shown = terrain_palettes(root)
    base = folder(root)
    for i, m in enumerate(members):
        export_set(m, os.path.join(base, "%03d" % i), shown.get(i))
    if landdata.narc_bytes([build_set(d) for d in set_dirs(root)]) != data:
        raise AreaTexError("%s does not rebuild %s" % (os.path.relpath(base, root), PREBUILT))
    os.remove(src)
    return len(members)


# --- editing --------------------------------------------------------------------------------------

def set_dir(root, set_id):
    d = os.path.join(folder(root), "%03d" % int(set_id))
    if not os.path.isdir(d):
        raise AreaTexError("no texture set %s (%s)" % (set_id, os.path.relpath(d, root)))
    return d


def add(root, set_id, image, name=None, palette=None, fmt=None, transparent=None):
    """A new texture (and, unless `palette` names one of the set's, a new palette) from an indexed PNG."""
    d = set_dir(root, set_id)
    doc = load_doc(d)
    name = name or os.path.splitext(os.path.basename(image))[0]
    nsbtx.check_name(name)
    if not re.fullmatch(r"[A-Za-z0-9_.]{1,16}", name) or (palette is None and len(name) > 13):
        # file names; terrain import splits "<texture>-<palette>.png" at "-"; "_pl" is added for the palette
        raise AreaTexError("texture name %r: letters, digits, _ and . only, at most 16 characters "
                           "(13 when a palette <name>_pl is made)" % name)
    if any(t["name"] == name for t in doc["textures"]):
        raise AreaTexError("set %s already has a texture %s (pick another name, or edit %s)"
                           % (set_id, name, os.path.relpath(tex_path(d, name), root)))
    w, h, kind, rows, png_palette, png_alpha = read_png(image)
    if kind != "indexed":
        raise AreaTexError("%s: save it as an indexed PNG (16 colors for palette16, 4 for palette4)" % image)
    values = [v for row in rows for v in row]
    used = max(values) + 1 if values else 1
    if fmt is None:
        fmt = "palette4" if used <= 4 else "palette16" if used <= 16 else "palette256"
    if fmt not in PALETTE_FORMATS:
        raise AreaTexError("add makes palette4, palette16 or palette256 textures, not %s" % fmt)
    if transparent is None:
        transparent = bool(png_alpha) and png_alpha[0] == 0
    entry = {"name": name, "format": fmt}
    if transparent:
        entry["transparent"] = True
    tex = read_texture(image, entry)   # checks size and color count
    if palette is not None:
        if not any(p["name"] == palette for p in doc["palettes"]):
            raise AreaTexError("set %s has no palette %s" % (set_id, palette))
        colors = read_pal(pal_path(d, palette))
        new_palette = None
    else:
        palette = name + "_pl"
        if any(p["name"] == palette for p in doc["palettes"]):
            raise AreaTexError("set %s already has a palette %s; give --palette to share it" % (set_id, palette))
        n = 1 << PALETTE_FORMATS[fmt]
        colors = [(c[0] >> 3) | (c[1] >> 3) << 5 | (c[2] >> 3) << 10 for c in (png_palette + [(0, 0, 0)] * n)[:n]]
        if fmt == "palette16" and used <= 8:
            colors = colors[:8]   # as the retail converter stores small palettes
        new_palette = {"name": palette, "four_color": True} if fmt == "palette4" else {"name": palette}
    entry["palette"] = palette
    doc["textures"].append(entry)
    with open(tex_path(d, name), "wb") as f:
        f.write(texture_png(tex, colors))
    if new_palette:
        doc["palettes"].append(new_palette)
        write_pal(pal_path(d, palette), colors)
    save_doc(d, doc)
    build_set(d)   # fails here, not in the build, if the set no longer fits a file
    return entry


def color(root, set_id=None):
    """Rewrite PNG palettes from each texture's "palette" (the pixel values don't change)."""
    dirs = [set_dir(root, set_id)] if set_id is not None else set_dirs(root)
    n = 0
    for d in dirs:
        doc = load_doc(d)
        for t in doc["textures"]:
            tex = read_texture(tex_path(d, t["name"]), t)
            colors = read_pal(pal_path(d, t["palette"])) if t.get("palette") else None
            with open(tex_path(d, t["name"]), "wb") as f:
                f.write(texture_png(tex, colors))
            n += 1
    return n


def listing(root, set_id):
    d = set_dir(root, set_id)
    textures, palettes = read_set(d)
    data = nsbtx.write(textures, palettes)
    b = 0x14
    tex_bytes = struct.unpack_from("<H", data, b + 0x0C)[0] << 3
    pal_bytes = struct.unpack_from("<H", data, b + 0x30)[0] << 3
    rows = ["%-16s %-10s %4dx%-4d %s" % (t.name, t.format, t.width, t.height, "transparent" if t.color0_transparent else "")
            for t in textures]
    rows.append("%d textures (%d bytes of texels), %d palettes (%d bytes)" % (len(textures), tex_bytes, len(palettes), pal_bytes))
    return "\n".join(rows)


def check(root):
    """-> (count, [(path, message)]): every set builds, and its JSON matches its files."""
    problems = []
    try:
        dirs = set_dirs(root)
    except AreaTexError as ex:
        return 0, [(folder(root), str(ex))]
    for d in dirs:
        try:
            doc = load_doc(d)
            listed = {os.path.join("textures", t["name"] + ".png") for t in doc["textures"]}
            listed |= {os.path.join("palettes", p["name"] + ".pal") for p in doc["palettes"]}
            pals = {p["name"] for p in doc["palettes"]}
            for t in doc["textures"]:
                if t.get("palette") is not None and t["palette"] not in pals:
                    problems.append((d, "texture %s: palette %s isn't in the set" % (t["name"], t["palette"])))
            for sub in ("textures", "palettes"):
                for n in sorted(os.listdir(os.path.join(d, sub))):
                    if os.path.join(sub, n) not in listed:
                        problems.append((d, "%s/%s is not in textures.json" % (sub, n)))
            build_set(d)
        except (AreaTexError, nsbtx.NsbtxError, OSError, ValueError, KeyError) as ex:
            problems.append((d, str(ex)))
    return len(dirs), problems
