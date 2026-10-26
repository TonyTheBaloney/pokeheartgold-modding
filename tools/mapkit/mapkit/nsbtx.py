# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26
"""NSBTX texture files: read into textures and palettes, and write them back.

The layout follows NitroSystem's include/nnsys/g3d/binres/res_struct.h (NNSG3dResTex)
and the name lookup in libraries/g3d/src/binres/res_struct_accessor.c. The writer lays
files out the way Nintendo's converter did, so every retail map texture file
(files/a/0/4/4) comes back byte for byte:

    header      'BTX0', one block, TEX0 at 0x14
    TEX0        texInfo, tex4x4Info (unused here), plttInfo: 0x3C bytes
    dictionary  of textures: texImageParam, extraParam per name
    dictionary  of palettes: offset >> 3, flag (1 = a 4-color palette) per name
    texels      in dictionary order; a texture identical to an earlier one shares its data
    palettes    in dictionary order, each padded to 16 bytes, identical ones shared

The name dictionaries are the same as in NSBMD files (nsbmd.dict_bytes).
"""

import struct

from .nsbmd import dict_bytes, read_dict

FORMATS = {1: "a3i5", 2: "palette4", 3: "palette16", 4: "palette256", 5: "tex4x4", 6: "a5i3", 7: "direct"}
FORMAT_IDS = {v: k for k, v in FORMATS.items()}
BITS = {1: 8, 2: 2, 3: 4, 4: 8, 6: 8, 7: 16}   # bits per texel
SIZES = (8, 16, 32, 64, 128, 256, 512, 1024)


class NsbtxError(Exception):
    pass


class Texture:
    """name, format (FORMATS value), width, height, color0_transparent, texels (bytes)."""

    def __init__(self, name, fmt, width, height, color0_transparent, texels):
        if fmt not in FORMAT_IDS or fmt in ("tex4x4", "direct"):
            raise NsbtxError("texture %s: format %s isn't supported" % (name, fmt))
        if width not in SIZES or height not in SIZES:
            raise NsbtxError("texture %s: %dx%d; sides must be 8, 16, 32 ... 1024" % (name, width, height))
        size = width * height * BITS[FORMAT_IDS[fmt]] // 8
        if len(texels) != size:
            raise NsbtxError("texture %s: %d bytes of texels, %s %dx%d needs %d" % (name, len(texels), fmt, width, height, size))
        check_name(name)
        self.name, self.format, self.width, self.height = name, fmt, width, height
        self.color0_transparent, self.texels = color0_transparent, bytes(texels)

    def indices(self):
        """One palette index per texel (with the alpha bits for a3i5 / a5i3), row by row."""
        bits = BITS[FORMAT_IDS[self.format]]
        if bits == 8:
            return list(self.texels)
        per, mask = 8 // bits, (1 << bits) - 1
        return [(self.texels[i // per] >> ((i % per) * bits)) & mask for i in range(self.width * self.height)]

    @classmethod
    def from_indices(cls, name, fmt, width, height, color0_transparent, values):
        bits = BITS[FORMAT_IDS[fmt]]
        if bits == 8:
            return cls(name, fmt, width, height, color0_transparent, bytes(values))
        per = 8 // bits
        out = bytearray(width * height // per)
        for i, v in enumerate(values):
            if v >> bits:
                raise NsbtxError("texture %s: index %d doesn't fit %s (at most %d)" % (name, v, fmt, (1 << bits) - 1))
            out[i // per] |= v << ((i % per) * bits)
        return cls(name, fmt, width, height, color0_transparent, bytes(out))


class Palette:
    """name, colors (RGB555 values), four_color (used by palette4 textures)."""

    def __init__(self, name, colors, four_color=False):
        check_name(name)
        self.name, self.colors, self.four_color = name, list(colors), four_color


def check_name(name):
    raw = name.encode("ascii")
    if not 0 < len(raw) <= 16:
        raise NsbtxError("name %r: 1 to 16 ASCII characters" % name)


# --- reading ------------------------------------------------------------------------------

def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def read(data):
    """An NSBTX file -> (textures, palettes), in file order."""
    if data[:4] != b"BTX0" or _u16(data, 14) != 1:
        raise NsbtxError("not a single-block NSBTX file")
    b = _u32(data, 16)
    if data[b:b + 4] != b"TEX0":
        raise NsbtxError("no TEX0 block")
    if _u16(data, b + 0x1C):
        raise NsbtxError("4x4-compressed textures aren't supported")
    tex_base, pal_base = b + _u32(data, b + 0x14), b + _u32(data, b + 0x38)
    textures = []
    names, params, _ = read_dict(data, b + _u16(data, b + 0x0E))
    for name, entry in zip(names, params):
        param = _u32(entry, 0)
        fmt = (param >> 26) & 7
        if fmt not in BITS:
            raise NsbtxError("texture %s: format %d isn't supported" % (name, fmt))
        w, h = 8 << ((param >> 20) & 7), 8 << ((param >> 23) & 7)
        start = tex_base + ((param & 0xFFFF) << 3)
        textures.append(Texture(name, FORMATS[fmt], w, h, bool(param >> 29 & 1),
                                data[start:start + w * h * BITS[fmt] // 8]))
    names, raw, _ = read_dict(data, b + _u16(data, b + 0x34))
    entries = [(name, _u16(e, 0) << 3, _u16(e, 2)) for name, e in zip(names, raw)]
    starts = sorted({o for _, o, _ in entries}) + [len(data) - pal_base]
    size = {s: starts[i + 1] - s for i, s in enumerate(starts[:-1])}
    palettes = []
    for name, ofs, flag in entries:
        count = 4 if flag & 1 else size[ofs] // 2
        palettes.append(Palette(name, [_u16(data, pal_base + ofs + 2 * i) for i in range(count)], bool(flag & 1)))
    return textures, palettes


# --- writing ------------------------------------------------------------------------------

def write(textures, palettes):
    """(textures, palettes) -> NSBTX bytes."""
    texels, where, params = bytearray(), {}, []
    for t in textures:
        if t.texels not in where:
            where[t.texels] = len(texels)
            texels += t.texels
        fmt = FORMAT_IDS[t.format]
        params.append(struct.pack("<II",
                                  where[t.texels] >> 3 | SIZES.index(t.width) << 20 | SIZES.index(t.height) << 23
                                  | fmt << 26 | int(t.color0_transparent) << 29,
                                  t.width | t.height << 11 | 1 << 31))
    if len(texels) >> 3 > 0xFFFF or len(texels) & 7:
        raise NsbtxError("%d bytes of texels; at most 512 KiB" % len(texels))
    plt, pwhere, pentries = bytearray(), {}, []
    for p in palettes:
        raw = b"".join(struct.pack("<H", c) for c in p.colors)
        raw += bytes(-len(raw) % 16)
        if raw not in pwhere:
            pwhere[raw] = len(plt)
            plt += raw
        pentries.append(struct.pack("<HH", pwhere[raw] >> 3, int(p.four_color)))
    if len(textures) > 255 or len(palettes) > 255:
        raise NsbtxError("%d textures, %d palettes; a file holds at most 255 of each" % (len(textures), len(palettes)))
    tex_dict = dict_bytes([t.name for t in textures], params, 8)
    pal_dict = dict_bytes([p.name for p in palettes], pentries, 4)
    ofs_tex_dict = 0x3C
    ofs_pal_dict = ofs_tex_dict + len(tex_dict)
    ofs_tex = ofs_pal_dict + len(pal_dict)
    ofs_pal = ofs_tex + len(texels)
    tex0_size = ofs_pal + len(plt)
    any4 = any(p.four_color for p in palettes)
    tex0 = struct.pack("<4sI", b"TEX0", tex0_size)
    tex0 += struct.pack("<IHHHHI", 0, len(texels) >> 3, ofs_tex_dict, 0, 0, ofs_tex)
    tex0 += struct.pack("<IHHHHII", 0, 0, ofs_tex_dict, 0, 0, ofs_pal, ofs_pal)
    tex0 += struct.pack("<IHHHHI", 0, len(plt) >> 3, 0x8000 if any4 else 0, ofs_pal_dict, 0, ofs_pal)
    tex0 += tex_dict + pal_dict + bytes(texels) + bytes(plt)
    header = struct.pack("<4sHHIHHI", b"BTX0", 0xFEFF, 1, 0x14 + len(tex0), 0x10, 1, 0x14)
    return header + tex0
