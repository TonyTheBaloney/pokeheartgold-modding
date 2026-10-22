# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""NITRO-System 3D resources: NSBMD models and NSBTX textures, decoded to
triangles and RGBA images for tools (the map editor's terrain view).

Layouts follow NitroSystem's own headers and code in subprojects/NitroSystem-*:
include/nnsys/g3d/binres/res_struct.h (structures), libraries/g3d/src/sbc.c
(structure byte code, node transforms), kernel.c (binding textures to
materials), util.c (SBC command lengths). The display lists are DS geometry
engine commands (GX), as documented in GBATEK.

Coordinates stay in model units (fx32 / 4096). A model is rendered with the
GX matrix rules: row vectors, v' = v * M, and MULT/TRANS/SCALE pre-multiply.
"""

import math
import struct

FX = 4096.0


class NitroError(Exception):
    pass


# --- small helpers ----------------------------------------------------------------------

def _u8(d, o):
    return d[o]


def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _s16(d, o):
    return struct.unpack_from("<h", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def _s32(d, o):
    return struct.unpack_from("<i", d, o)[0]


def _sext(v, bits):
    return v - (1 << bits) if v & (1 << (bits - 1)) else v


def read_dict(d, base):
    """NNSG3dResDict at `base` -> [(name, data offset in d, sizeUnit)] in entry order."""
    num = _u8(d, base + 1)
    ofs_entry = _u16(d, base + 6)
    hdr = base + ofs_entry
    size_unit = _u16(d, hdr)
    ofs_name = _u16(d, hdr + 2)
    out = []
    for i in range(num):
        name = d[hdr + ofs_name + 16 * i:hdr + ofs_name + 16 * (i + 1)].split(b"\0")[0].decode("ascii", "replace")
        out.append((name, hdr + 4 + size_unit * i))
    return out


def blocks(d, sig):
    if d[:4] != sig:
        raise NitroError("not a %s file" % sig.decode())
    n = _u16(d, 14)
    return {d[o:o + 4]: o for o in (_u32(d, 16 + 4 * i) for i in range(n))}


# --- matrices (4x4, row-major lists, GX row-vector convention) -------------------------------

IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)


def mat_mul(a, b):
    """a * b."""
    return tuple(sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)) for r in range(4) for c in range(4))


def mat_from_3x3(m, t=(0.0, 0.0, 0.0)):
    return (m[0], m[1], m[2], 0.0, m[3], m[4], m[5], 0.0, m[6], m[7], m[8], 0.0, t[0], t[1], t[2], 1.0)


def mat_scale(s):
    return (s[0], 0, 0, 0, 0, s[1], 0, 0, 0, 0, s[2], 0, 0, 0, 0, 1.0)


def mat_trans(t):
    return (1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, t[0], t[1], t[2], 1.0)


def transform(m, v):
    x, y, z = v
    return (x * m[0] + y * m[4] + z * m[8] + m[12],
            x * m[1] + y * m[5] + z * m[9] + m[13],
            x * m[2] + y * m[6] + z * m[10] + m[14])


def rotation_xyz(deg):
    """Euler degrees (x, y, z) -> 3x3 for props (MapPropArcData.rotation)."""
    rx, ry, rz = (math.radians(a) for a in deg)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    mx = (1, 0, 0, 0, cx, sx, 0, -sx, cx)
    my = (cy, 0, -sy, 0, 1, 0, sy, 0, cy)
    mz = (cz, sz, 0, -sz, cz, 0, 0, 0, 1)
    m = mat_mul(mat_from_3x3(mx), mat_mul(mat_from_3x3(my), mat_from_3x3(mz)))
    return m


# --- textures (NSBTX / TEX0) --------------------------------------------------------------------

FMT_NAMES = {1: "A3I5", 2: "4-color", 3: "16-color", 4: "256-color", 5: "4x4", 6: "A5I3", 7: "direct"}


def rgb555(c):
    r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
    return (r * 255 // 31, g * 255 // 31, b * 255 // 31)


class Texture:
    def __init__(self, name, param, data_ofs, idx_ofs, d):
        self.name = name
        self.param = param
        self.width = 8 << ((param >> 20) & 7)
        self.height = 8 << ((param >> 23) & 7)
        self.format = (param >> 26) & 7
        self.color0_transparent = bool(param >> 29 & 1)
        self._d, self._data, self._idx = d, data_ofs, idx_ofs

    def decode(self, palette):
        """RGBA bytes (width*height*4). palette: list of RGB555 values (unused by direct)."""
        w, h, d, o, fmt = self.width, self.height, self._d, self._data, self.format
        n = w * h
        out = bytearray(n * 4)
        pal = [rgb555(c) for c in (palette or [])]

        def color(i):
            return pal[i] if i < len(pal) else (255, 0, 255)

        def put(i, rgb, a):
            out[i * 4:i * 4 + 4] = bytes((rgb[0], rgb[1], rgb[2], a))

        if fmt == 1 or fmt == 6:  # A3I5, A5I3
            ibits = 5 if fmt == 1 else 3
            for i in range(n):
                v = d[o + i]
                idx, a = v & ((1 << ibits) - 1), v >> ibits
                abits = 8 - ibits
                put(i, color(idx), a * 255 // ((1 << abits) - 1))
        elif fmt in (2, 3, 4):
            bpp = {2: 2, 3: 4, 4: 8}[fmt]
            per = 8 // bpp
            mask = (1 << bpp) - 1
            for i in range(n):
                idx = (d[o + i // per] >> ((i % per) * bpp)) & mask
                put(i, color(idx), 0 if (idx == 0 and self.color0_transparent) else 255)
        elif fmt == 7:
            for i in range(n):
                c = _u16(d, o + 2 * i)
                put(i, rgb555(c), 255 if c & 0x8000 else 0)
        elif fmt == 5:
            bw = w // 4
            for b in range((w // 4) * (h // 4)):
                texels = _u32(d, o + 4 * b)
                info = _u16(d, self._idx + 2 * b)
                base, mode = (info & 0x3FFF) * 2, info >> 14
                c = [color(base + k) for k in range(4)]
                if mode == 0:
                    cols = [(c[0], 255), (c[1], 255), (c[2], 255), ((0, 0, 0), 0)]
                elif mode == 1:
                    mid = tuple((c[0][k] + c[1][k]) // 2 for k in range(3))
                    cols = [(c[0], 255), (c[1], 255), (mid, 255), ((0, 0, 0), 0)]
                elif mode == 2:
                    cols = [(c[k], 255) for k in range(4)]
                else:
                    m1 = tuple((5 * c[0][k] + 3 * c[1][k]) // 8 for k in range(3))
                    m2 = tuple((3 * c[0][k] + 5 * c[1][k]) // 8 for k in range(3))
                    cols = [(c[0], 255), (c[1], 255), (m1, 255), (m2, 255)]
                bx, by = (b % bw) * 4, (b // bw) * 4
                for t in range(16):
                    rgb, a = cols[(texels >> (2 * t)) & 3]
                    put((by + t // 4) * w + bx + t % 4, rgb, a)
        else:
            raise NitroError("texture %s: unknown format %d" % (self.name, fmt))
        return bytes(out)


class TextureSet:
    """A TEX0 block: textures and palettes by name."""

    def __init__(self, d, base):
        self.textures, self.palettes = {}, {}
        tex_ofs = base + _u32(d, base + 0x14)          # texInfo.ofsTex
        tex_dict = base + _u16(d, base + 0x0E)         # texInfo.ofsDict
        t4_ofs = base + _u32(d, base + 0x24)           # tex4x4Info.ofsTex
        t4_idx = base + _u32(d, base + 0x28)           # tex4x4Info.ofsTexPlttIdx
        pal_dict = base + _u16(d, base + 0x34)         # plttInfo.ofsDict
        pal_ofs = base + _u32(d, base + 0x38)          # plttInfo.ofsPlttData
        for name, p in read_dict(d, tex_dict):
            param = _u32(d, p)
            off = (param & 0xFFFF) << 3
            if (param >> 26) & 7 == 5:
                self.textures[name] = Texture(name, param, t4_ofs + off, t4_idx + off // 2, d)
            else:
                self.textures[name] = Texture(name, param, tex_ofs + off, 0, d)
        entries = read_dict(d, pal_dict)
        starts = sorted(set(_u16(d, p) << 3 for _, p in entries))
        end = base + _u32(d, base + 4)
        for name, p in entries:
            start = pal_ofs + (_u16(d, p) << 3)
            following = [s for s in starts if pal_ofs + s > start]
            stop = pal_ofs + following[0] if following else end
            count = max(0, min(256, (stop - start) // 2))
            self.palettes[name] = [_u16(d, start + 2 * i) for i in range(count)]

    def image(self, tex_name, pal_name):
        t = self.textures.get(tex_name)
        if t is None:
            return None
        return t.width, t.height, t.decode(self.palettes.get(pal_name))


def load_nsbtx(data):
    b = blocks(data, b"BTX0")
    if b"TEX0" not in b:
        raise NitroError("NSBTX without TEX0")
    return TextureSet(data, b[b"TEX0"])


# --- models (NSBMD / MDL0) -------------------------------------------------------------------------

GX_PARAMS = {0x00: 0, 0x10: 1, 0x11: 0, 0x12: 1, 0x13: 1, 0x14: 1, 0x15: 0, 0x16: 16, 0x17: 12, 0x18: 16,
             0x19: 12, 0x1A: 9, 0x1B: 3, 0x1C: 3, 0x20: 1, 0x21: 1, 0x22: 1, 0x23: 2, 0x24: 1, 0x25: 1,
             0x26: 1, 0x27: 1, 0x28: 1, 0x29: 1, 0x2A: 1, 0x2B: 1, 0x30: 1, 0x31: 1, 0x32: 1, 0x33: 1,
             0x34: 32, 0x40: 1, 0x41: 0, 0x50: 1, 0x60: 1, 0x70: 3, 0x71: 2, 0x72: 1}
SBC_LEN = {0x00: 1, 0x01: 1, 0x02: 3, 0x03: 2, 0x04: 2, 0x05: 2, 0x06: 4, 0x07: 2, 0x08: 2, 0x0A: 9, 0x0B: 1,
           0x0C: 3, 0x0D: 3}
PIVOT_UTIL = ((4, 5, 7, 8), (3, 5, 6, 8), (3, 4, 6, 7), (1, 2, 7, 8), (0, 2, 6, 8), (0, 1, 6, 7),
              (1, 2, 4, 5), (0, 2, 3, 5), (0, 1, 3, 4))


class Material:
    def __init__(self, name, d, o):
        self.name = name
        self.diff_amb = _u32(d, o + 4)
        self.poly_attr = _u32(d, o + 12)
        self.tex_param = _u32(d, o + 20)
        self.flag = _u16(d, o + 30)
        self.orig_w, self.orig_h = _u16(d, o + 32), _u16(d, o + 34)
        self.texture = None
        self.palette = None
        # texture matrix (NNS_G3D_MATFLAG_TEXMTX_*), after the fixed 0x2C bytes
        self.tex_scale, self.tex_rot, self.tex_trans = (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)
        p = o + 0x2C
        if self.flag & 0x0001:
            if not self.flag & 0x0002:
                self.tex_scale = (_s32(d, p) / FX, _s32(d, p + 4) / FX)
                p += 8
            if not self.flag & 0x0004:
                self.tex_rot = (_s16(d, p) / FX, _s16(d, p + 2) / FX)
                p += 4
            if not self.flag & 0x0008:
                self.tex_trans = (_s32(d, p) / FX, _s32(d, p + 4) / FX)

    @property
    def alpha(self):
        """Polygon alpha 0-31 (0 draws as wireframe on the DS)."""
        return (self.poly_attr >> 16) & 31

    @property
    def repeat(self):
        return bool(self.tex_param >> 16 & 1), bool(self.tex_param >> 17 & 1)

    @property
    def flip(self):
        return bool(self.tex_param >> 18 & 1), bool(self.tex_param >> 19 & 1)

    @property
    def diffuse(self):
        return rgb555(self.diff_amb & 0x7FFF)


class Triangle:
    __slots__ = ("pos", "uv", "color", "material")

    def __init__(self, pos, uv, color, material):
        self.pos, self.uv, self.color, self.material = pos, uv, color, material


class Model:
    def __init__(self, name, d, o):
        self.name = name
        self.d, self.o = d, o
        ofs_sbc, ofs_mat, ofs_shp = _u32(d, o + 4), _u32(d, o + 8), _u32(d, o + 12)
        self.evp = o + _u32(d, o + 16)  # NNSG3dResEvpMtx per node: invM (4x3), invN (3x3), fx32
        info = o + 20
        self.num_node, self.num_mat, self.num_shp = d[info + 3], d[info + 4], d[info + 5]
        self.pos_scale = _s32(d, info + 8) / FX
        self.inv_pos_scale = _s32(d, info + 12) / FX
        self.box = tuple(_s16(d, info + 0x18 + 2 * i) for i in range(6))
        self.box_pos_scale = _s32(d, info + 0x24) / FX
        node_info = o + 20 + 0x2C  # NNSG3dResMdlInfo is 0x2C bytes
        self.nodes = [(n, node_info + _u32(d, p)) for n, p in read_dict(d, node_info)]
        mat_base = o + ofs_mat
        self.materials = [Material(n, d, mat_base + _u32(d, p)) for n, p in read_dict(d, mat_base + 4)]
        for dict_ofs, attr in ((_u16(d, mat_base), "texture"), (_u16(d, mat_base + 2), "palette")):
            for name, p in read_dict(d, mat_base + dict_ofs):
                lst, num = mat_base + _u16(d, p), d[p + 2]
                for j in range(num):
                    idx = d[lst + j]
                    if idx < len(self.materials):
                        setattr(self.materials[idx], attr, name)
        shp_base = o + ofs_shp
        self.shapes = []
        for name, p in read_dict(d, shp_base):
            s = shp_base + _u32(d, p)
            self.shapes.append((name, s + _u32(d, s + 8), _u32(d, s + 12)))
        self.sbc = o + ofs_sbc
        self.sbc_end = o + ofs_mat

    @property
    def bounding_box(self):
        """(x, y, z, w, h, d) in model units."""
        return tuple(v / FX * self.box_pos_scale for v in self.box)

    def _inv_bind(self, node):
        """invM of the envelope matrix for a node (sbc.c NNSi_G3dFuncSbc_NODEMIX)."""
        o = self.evp + node * (12 + 9) * 4
        v = [_s32(self.d, o + 4 * i) / FX for i in range(12)]
        return mat_from_3x3(v[0:9], v[9:12])

    def _node_matrix(self, idx):
        d = self.d
        o = self.nodes[idx][1]
        flag, a00 = _u16(d, o), _s16(d, o + 2)
        p = o + 4
        t = (0.0, 0.0, 0.0)
        if not flag & 0x1:
            t = (_s32(d, p) / FX, _s32(d, p + 4) / FX, _s32(d, p + 8) / FX)
            p += 12
        rot = None
        if not flag & 0x2:
            if flag & 0x8:
                a, b = _s16(d, p) / FX, _s16(d, p + 2) / FX
                piv = (flag >> 4) & 0xF
                r = [0.0] * 9
                r[piv] = -1.0 if flag & 0x100 else 1.0
                u = PIVOT_UTIL[piv]
                r[u[0]], r[u[1]] = a, b
                r[u[2]] = -b if flag & 0x200 else b
                r[u[3]] = -a if flag & 0x400 else a
                rot = r
                p += 4
            else:
                rot = [a00 / FX] + [_s16(d, p + 2 * i) / FX for i in range(8)]
                p += 16
        m = mat_from_3x3(rot or (1, 0, 0, 0, 1, 0, 0, 0, 1), t)
        if not flag & 0x4:
            m = mat_mul(mat_scale((_s32(d, p) / FX, _s32(d, p + 4) / FX, _s32(d, p + 8) / FX)), m)
        return m

    def triangles(self):
        """Run the structure byte code and every shape's display list -> [Triangle]."""
        d = self.d
        out = []
        cur = IDENTITY
        stack = {}
        material = None
        c = self.sbc
        while c < self.sbc_end:
            op = d[c]
            cmd, opt = op & 0x1F, op & 0xE0
            if cmd == 0x01:  # RET
                break
            if cmd == 0x09:  # NODEMIX dest, n, n * (src, node, ratio): weighted invM[node] * stack[src]
                n = d[c + 2]
                acc = [0.0] * 16
                for k in range(n):
                    src, node, ratio = d[c + 3 + 3 * k:c + 6 + 3 * k]
                    x = mat_mul(self._inv_bind(node), stack.get(src, IDENTITY))
                    w = ratio / 256.0
                    acc = [a + w * v for a, v in zip(acc, x)]
                acc[3], acc[7], acc[11], acc[15] = 0.0, 0.0, 0.0, 1.0
                cur = tuple(acc)
                stack[d[c + 1]] = cur
                c += 3 + 3 * n
                continue
            length = SBC_LEN.get(cmd)
            if length is None:
                raise NitroError("%s: unknown SBC command %02X" % (self.name, op))
            if cmd == 0x03:  # MTX: restore
                cur = stack.get(d[c + 1], cur)
            elif cmd == 0x04:  # MAT
                i = d[c + 1]
                material = self.materials[i] if i < len(self.materials) else None
            elif cmd == 0x05:  # SHP
                i = d[c + 1]
                if i < len(self.shapes):
                    out += self._run_dl(self.shapes[i], cur, stack, material)
            elif cmd == 0x06:  # NODEDESC node, parent, attr [dest] [src]
                if opt in (0x40, 0x60):
                    src = d[c + 4] if opt == 0x40 else d[c + 5]
                    cur = stack.get(src, cur)
                    length += 1
                if d[c + 1] < len(self.nodes):
                    cur = mat_mul(self._node_matrix(d[c + 1]), cur)
                if opt in (0x20, 0x60):
                    stack[d[c + 4]] = cur
                    length += 1
            elif cmd in (0x07, 0x08):  # billboards: keep the matrix, skip the extra args
                if opt in (0x20, 0x60):
                    length += 1
                if opt in (0x40, 0x60):
                    length += 1
            elif cmd == 0x0B:  # POSSCALE
                s = self.pos_scale if opt == 0 else self.inv_pos_scale
                cur = mat_mul(mat_scale((s, s, s)), cur)
            c += length
        return out

    def _run_dl(self, shape, mtx, stack, material):
        d = self.d
        _, o, size = shape
        end = o + size
        tris = []
        cur = mtx
        prim, verts = None, []
        vtx = [0.0, 0.0, 0.0]
        uv, color = (0.0, 0.0), material.diffuse if material else (255, 255, 255)

        def emit():
            p = transform(cur, tuple(vtx))
            verts.append((p, uv, color))
            n = len(verts)
            if prim == 0 and n % 3 == 0:
                tris.append(Triangle(*zip(*verts[-3:]), material))
            elif prim == 1 and n % 4 == 0:
                a, b, c_, e = verts[-4:]
                tris.append(Triangle(*zip(a, b, c_), material))
                tris.append(Triangle(*zip(a, c_, e), material))
            elif prim == 2 and n >= 3:
                a, b, c_ = verts[-3:]
                tris.append(Triangle(*zip(*((a, b, c_) if n % 2 else (b, a, c_))), material))
            elif prim == 3 and n >= 4 and n % 2 == 0:
                a, b, c_, e = verts[-4:]
                tris.append(Triangle(*zip(a, b, e), material))
                tris.append(Triangle(*zip(a, e, c_), material))

        while o < end:
            cmds = d[o:o + 4]
            o += 4
            for cmd in cmds:
                n = GX_PARAMS.get(cmd)
                if n is None:
                    raise NitroError("%s: unknown GX command %02X" % (self.name, cmd))
                p = o
                o += 4 * n
                if cmd == 0x14:  # MTX_RESTORE
                    cur = stack.get(_u32(d, p) & 31, cur)
                elif cmd == 0x13:  # MTX_STORE
                    stack[_u32(d, p) & 31] = cur
                elif cmd == 0x15:  # MTX_IDENTITY
                    cur = IDENTITY
                elif cmd in (0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C):  # load / multiply / scale / translate
                    v = [_s32(d, p + 4 * i) / FX for i in range(n)]
                    if cmd in (0x16, 0x18):
                        m = tuple(v)
                    elif cmd in (0x17, 0x19):
                        m = mat_from_3x3(v[0:9], v[9:12])
                    elif cmd == 0x1A:
                        m = mat_from_3x3(v)
                    elif cmd == 0x1B:
                        m = mat_scale(v)
                    else:
                        m = mat_trans(v)
                    cur = m if cmd in (0x16, 0x17) else mat_mul(m, cur)
                elif cmd == 0x20:  # COLOR
                    color = rgb555(_u32(d, p))
                elif cmd == 0x22:  # TEXCOORD, 12.4 texels
                    v = _u32(d, p)
                    uv = (_sext(v & 0xFFFF, 16) / 16.0, _sext(v >> 16, 16) / 16.0)
                elif cmd == 0x23:  # VTX_16
                    a, b = _u32(d, p), _u32(d, p + 4)
                    vtx = [_sext(a & 0xFFFF, 16) / FX, _sext(a >> 16, 16) / FX, _sext(b & 0xFFFF, 16) / FX]
                    emit()
                elif cmd == 0x24:  # VTX_10, 4.6
                    v = _u32(d, p)
                    vtx = [_sext(v & 0x3FF, 10) / 64.0, _sext((v >> 10) & 0x3FF, 10) / 64.0,
                           _sext((v >> 20) & 0x3FF, 10) / 64.0]
                    emit()
                elif cmd in (0x25, 0x26, 0x27):  # VTX_XY / XZ / YZ
                    v = _u32(d, p)
                    a, b = _sext(v & 0xFFFF, 16) / FX, _sext(v >> 16, 16) / FX
                    if cmd == 0x25:
                        vtx[0], vtx[1] = a, b
                    elif cmd == 0x26:
                        vtx[0], vtx[2] = a, b
                    else:
                        vtx[1], vtx[2] = a, b
                    emit()
                elif cmd == 0x28:  # VTX_DIFF, units of 1/4096 (1/8 of VTX_10's 1/64... see GBATEK)
                    v = _u32(d, p)
                    vtx = [vtx[0] + _sext(v & 0x3FF, 10) / FX, vtx[1] + _sext((v >> 10) & 0x3FF, 10) / FX,
                           vtx[2] + _sext((v >> 20) & 0x3FF, 10) / FX]
                    emit()
                elif cmd == 0x40:  # BEGIN_VTXS
                    prim, verts = _u32(d, p) & 3, []
                elif cmd == 0x41:  # END_VTXS
                    prim, verts = None, []
        return tris


def load_nsbmd(data):
    """-> ([Model], TextureSet or None)."""
    b = blocks(data, b"BMD0")
    if b"MDL0" not in b:
        raise NitroError("NSBMD without MDL0")
    base = b[b"MDL0"]
    models = [Model(n, data, base + _u32(data, p)) for n, p in read_dict(data, base + 8)]
    tex = TextureSet(data, b[b"TEX0"]) if b"TEX0" in b else None
    return models, tex
