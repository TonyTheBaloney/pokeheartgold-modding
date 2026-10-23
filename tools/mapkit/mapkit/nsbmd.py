# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""NSBMD files as data: a lossless reader and a writer.

`nitro.py` decodes models to triangles for drawing; this module keeps a model's
parts (nodes, structure byte code, materials, shapes and their display lists)
so that a file can be read, changed and written back. `write(read(data))`
reproduces every retail terrain model byte for byte (tests/test_nsbmd.py), so
the writer lays files out the way NITRO-System's converter does.

Structures: subprojects/NitroSystem-*/include/nnsys/g3d/binres/res_struct.h.
Name dictionaries are Patricia trees (res_struct_accessor.c,
NNS_G3dGetResDataByName); `dict_bytes` builds them.
"""

import struct

from .nitro import NitroError


def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def _align(n, a=4):
    return (n + a - 1) // a * a


# --- dictionaries ------------------------------------------------------------------------

def _name16(name):
    b = name.encode("ascii") if isinstance(name, str) else bytes(name)
    if len(b) > 16:
        raise NitroError("name longer than 16 bytes: %r" % name)
    return b.ljust(16, b"\0")


def _bit(key, b):
    return (key >> b) & 1


def _tree(names):
    """Patricia tree nodes [(refBit, left, right, entry)] for names inserted in order.

    Node 0 is the head (refBit 127, key 0); node i + 1 belongs to entry i. Keys are
    the 16-byte names as little-endian 128-bit integers, which is what the lookup's
    `name->val[bit >> 5] >> (bit & 31)` reads.
    """
    keys = [int.from_bytes(_name16(n), "little") for n in names]
    nodes = [[127, 0, 0, 0]]
    node_key = [0]
    for i, k in enumerate(keys):
        # search: the leaf reached for k
        p, x = 0, nodes[0][1]
        while nodes[p][0] > nodes[x][0]:
            p, x = x, nodes[x][1 + _bit(k, nodes[x][0])]
        diff = k ^ node_key[x]
        if diff == 0:
            raise NitroError("duplicate name %r" % names[i])
        b = diff.bit_length() - 1
        # insert: descend while refBits are above b
        p, x = 0, nodes[0][1]
        while nodes[p][0] > nodes[x][0] and nodes[x][0] > b:
            p, x = x, nodes[x][1 + _bit(k, nodes[x][0])]
        t = len(nodes)
        if _bit(k, b):
            nodes.append([b, x, t, i])
        else:
            nodes.append([b, t, x, i])
        node_key.append(k)
        side = 1 if p == 0 else 1 + _bit(k, nodes[p][0])
        nodes[p][side] = t
    # The converter stores the nodes in pre-order (node, left subtree, right subtree)
    # rather than insertion order; a child link is a subtree only if its refBit is lower.
    order = [0]
    stack = [nodes[0][1]] if len(nodes) > 1 else []
    while stack:
        i = stack.pop()
        order.append(i)
        for c in (nodes[i][2], nodes[i][1]):
            if nodes[c][0] < nodes[i][0]:
                stack.append(c)
    new = {old: n for n, old in enumerate(order)}
    return [[nodes[i][0], new[nodes[i][1]], new[nodes[i][2]], nodes[i][3]] for i in order]


def dict_bytes(names, entries, size_unit=None):
    """NNSG3dResDict: header, tree, entry header, entries (equal size), names."""
    n = len(names)
    if len(entries) != n:
        raise NitroError("dictionary: %d names, %d entries" % (n, len(entries)))
    if size_unit is None:
        size_unit = len(entries[0]) if entries else 4
    tree = _tree(names) if n else [[127, 0, 0, 0]]
    ofs_entry = 8 + 4 * len(tree)
    size = ofs_entry + 4 + size_unit * n + 16 * n
    out = bytearray(struct.pack("<BBHHH", 0, n, size, 8, ofs_entry))
    for node in tree:
        out += bytes(node)
    out += struct.pack("<HH", size_unit, 4 + size_unit * n)
    for e in entries:
        if len(e) != size_unit:
            raise NitroError("dictionary entries differ in size")
        out += e
    for nm in names:
        out += _name16(nm)
    return bytes(out)


def read_dict(d, base):
    """-> (names, [entry bytes], dict size)."""
    num = d[base + 1]
    size = _u16(d, base + 2)
    hdr = base + _u16(d, base + 6)
    size_unit, ofs_name = _u16(d, hdr), _u16(d, hdr + 2)
    names, entries = [], []
    for i in range(num):
        raw = d[hdr + ofs_name + 16 * i:hdr + ofs_name + 16 * (i + 1)]
        names.append(raw.rstrip(b"\0").decode("ascii"))
        entries.append(bytes(d[hdr + 4 + size_unit * i:hdr + 4 + size_unit * (i + 1)]))
    return names, entries, size


# --- the model ---------------------------------------------------------------------------

class Material:
    """A material: its name and NNSG3dResMatData bytes (size given by its own `size`)."""

    def __init__(self, name, data):
        self.name, self.data = name, bytes(data)


class Shape:
    """A shape: name, NNSG3dShpFlag, display list (GX command words)."""

    def __init__(self, name, flag, dl):
        self.name, self.flag, self.dl = name, flag, bytes(dl)


class Model:
    """One model of an NSBMD's MDL0 block, kept as its parts.

    info: NNSG3dResMdlInfo bytes (0x2C); nodes: [(name, node data bytes)];
    sbc: structure byte code; materials, tex_map / pltt_map: [(texture or palette
    name, [material indexes], flag)]; shapes; evp: envelope matrices.
    """

    def __init__(self):
        self.name = ""
        self.info = bytes(0x2C)
        self.nodes = []
        self.sbc = b""
        self.materials = []
        self.tex_map = []
        self.pltt_map = []
        self.shapes = []
        self.evp = b""


def read(data):
    """NSBMD bytes -> [Model]. Files with a TEX0 block are not supported (terrain has none)."""
    d = data
    if d[:4] != b"BMD0":
        raise NitroError("not an NSBMD file")
    if _u16(d, 14) != 1:
        raise NitroError("NSBMD with %d blocks (only MDL0 is supported)" % _u16(d, 14))
    mdl0 = _u32(d, 16)
    if d[mdl0:mdl0 + 4] != b"MDL0":
        raise NitroError("first block is not MDL0")
    names, entries, _ = read_dict(d, mdl0 + 8)
    models = []
    for name, e in zip(names, entries):
        o = mdl0 + _u32(e, 0)
        m = Model()
        m.name = name
        size, ofs_sbc, ofs_mat, ofs_shp, ofs_evp = struct.unpack_from("<5I", d, o)
        m.info = bytes(d[o + 20:o + 20 + 0x2C])
        node_base = o + 20 + 0x2C
        nnames, nentries, _ = read_dict(d, node_base)
        offs = [node_base + _u32(e2, 0) for e2 in nentries]
        ends = offs[1:] + [o + ofs_sbc]
        m.nodes = [(n, bytes(d[a:b])) for n, a, b in zip(nnames, offs, ends)]
        m.sbc = bytes(d[o + ofs_sbc:o + ofs_mat])
        mb = o + ofs_mat
        ofs_tex, ofs_pltt = _u16(d, mb), _u16(d, mb + 2)
        mnames, mentries, _ = read_dict(d, mb + 4)
        for n, e2 in zip(mnames, mentries):
            p = mb + _u32(e2, 0)
            m.materials.append(Material(n, d[p:p + _u16(d, p + 2)]))
        for base, attr in ((ofs_tex, "tex_map"), (ofs_pltt, "pltt_map")):
            tnames, tentries, _ = read_dict(d, mb + base)
            lst = []
            for n, e2 in zip(tnames, tentries):
                p, num, flag = _u16(e2, 0), e2[2], e2[3]
                lst.append((n, list(d[mb + p:mb + p + num]), flag))
            setattr(m, attr, lst)
        sb = o + ofs_shp
        snames, sentries, _ = read_dict(d, sb)
        for n, e2 in zip(snames, sentries):
            p = sb + _u32(e2, 0)
            tag, ssize, flag, ofs_dl, size_dl = struct.unpack_from("<HHIII", d, p)
            if (tag, ssize) != (0, 16):
                raise NitroError("%s: unexpected shape header" % n)
            m.shapes.append(Shape(n, flag, d[p + ofs_dl:p + ofs_dl + size_dl]))
        m.evp = bytes(d[o + ofs_evp:o + size])
        models.append(m)
    return models


def _model_bytes(m):
    # nodes: dict, then each node's data
    node_dict_size = len(dict_bytes([n for n, _ in m.nodes], [b"\0" * 4] * len(m.nodes)))
    node_entries, node_data, p = [], b"", node_dict_size
    for _, nd in m.nodes:
        node_entries.append(struct.pack("<I", p))
        node_data += nd
        p += len(nd)
    nodes = dict_bytes([n for n, _ in m.nodes], node_entries) + node_data

    # materials: u16 ofsTex, u16 ofsPltt, material dict, tex dict, pltt dict, index lists, material data
    mat_names = [x.name for x in m.materials]
    mat_dict_size = len(dict_bytes(mat_names, [b"\0" * 4] * len(mat_names)))
    tex_dict_size = len(dict_bytes([t for t, _, _ in m.tex_map], [b"\0" * 4] * len(m.tex_map)))
    pltt_dict_size = len(dict_bytes([t for t, _, _ in m.pltt_map], [b"\0" * 4] * len(m.pltt_map)))
    ofs_tex = 4 + mat_dict_size
    ofs_pltt = ofs_tex + tex_dict_size
    p = ofs_pltt + pltt_dict_size
    idx_lists = b""
    tex_entries, pltt_entries = [], []
    for lst, entries in ((m.tex_map, tex_entries), (m.pltt_map, pltt_entries)):
        for _, idxs, flag in lst:
            entries.append(struct.pack("<HBB", p + len(idx_lists), len(idxs), flag))
            idx_lists += bytes(idxs)
    idx_lists += b"\0" * (_align(len(idx_lists)) - len(idx_lists))
    p += len(idx_lists)
    mat_entries, mat_data = [], b""
    for x in m.materials:
        mat_entries.append(struct.pack("<I", p + len(mat_data)))
        mat_data += x.data
    mats = (struct.pack("<HH", ofs_tex, ofs_pltt) + dict_bytes(mat_names, mat_entries) +
            dict_bytes([t for t, _, _ in m.tex_map], tex_entries) +
            dict_bytes([t for t, _, _ in m.pltt_map], pltt_entries) + idx_lists + mat_data)

    # shapes: dict, shape headers, display lists
    shp_names = [s.name for s in m.shapes]
    shp_dict_size = len(dict_bytes(shp_names, [b"\0" * 4] * len(shp_names)))
    hdr_start = shp_dict_size
    dl_start = hdr_start + 16 * len(m.shapes)
    shp_entries, headers, dls = [], b"", b""
    for i, s in enumerate(m.shapes):
        h = hdr_start + 16 * i
        shp_entries.append(struct.pack("<I", h))
        headers += struct.pack("<HHIII", 0, 16, s.flag, dl_start + len(dls) - h, len(s.dl))
        dls += s.dl
    shps = dict_bytes(shp_names, shp_entries) + headers + dls

    head = 20 + len(m.info)
    ofs_sbc = head + len(nodes)
    ofs_mat = ofs_sbc + len(m.sbc)
    ofs_mat_al = _align(ofs_mat)
    sbc = m.sbc + b"\0" * (ofs_mat_al - ofs_mat)
    ofs_shp = ofs_mat_al + len(mats)
    ofs_evp = ofs_shp + len(shps)
    size = ofs_evp + len(m.evp)
    return (struct.pack("<5I", size, ofs_sbc, ofs_mat_al, ofs_shp, ofs_evp) + m.info + nodes + sbc +
            mats + shps + m.evp)


def write(models):
    """[Model] -> NSBMD bytes (one MDL0 block)."""
    names = [m.name for m in models]
    dict_size = len(dict_bytes(names, [b"\0" * 4] * len(names)))
    bodies, entries, p = [], [], 8 + dict_size
    for m in models:
        b = _model_bytes(m)
        entries.append(struct.pack("<I", p))
        bodies.append(b)
        p += len(b)
    block = dict_bytes(names, entries) + b"".join(bodies)
    block = b"MDL0" + struct.pack("<I", 8 + len(block)) + block
    header = b"BMD0" + struct.pack("<HHIHH", 0xFEFF, 2, 16 + 4 + len(block), 16, 1) + struct.pack("<I", 20)
    return header + block


# --- building a terrain model ----------------------------------------------------------------
#
# What a new model looks like is copied from the retail terrain models (all 676 share it):
# one model, one node at the identity, no textures of its own (the area's NSBTX is bound by
# name when the map loads), structure byte code NODEDESC / NODE / POSSCALE, then MAT + SHP
# per shape, then POSSCALE (inverse) and RET. Lit materials send NORMAL per vertex (shape
# flag 5), unlit ones COLOR (flag 6); both send TEXCOORD in texels of the texture's size.

MAX_MODEL_SIZE = 0xF000     # MAP_LOAD_PRIMARY_BUFFER_SIZE: the buffer a map model is read into

CULL = {"back": 2, "front": 1, "none": 3}   # polygon attr bits 6-7: which faces are drawn (2 = front only)


class TerrainMaterial:
    """How a group of polygons is drawn.

    texture / palette: names in the area's map texture NSBTX (None for untextured);
    tex_size: that texture's (width, height); lit: lighting with normals, else vertex colors;
    alpha 0-31; cull "back" / "front" / "none"; fog; repeat / flip (s, t).
    """

    def __init__(self, name, texture=None, palette=None, tex_size=(0, 0), lit=True, alpha=31, cull="back",
                 fog=True, repeat=(True, True), flip=(False, False), diffuse=(25, 25, 25), ambient=(31, 31, 31)):
        self.name, self.texture, self.palette, self.tex_size = name, texture, palette, tuple(tex_size)
        self.lit, self.alpha, self.cull, self.fog = lit, alpha, cull, fog
        self.repeat, self.flip = tuple(repeat), tuple(flip)
        self.diffuse, self.ambient = tuple(diffuse), tuple(ambient)

    def data(self):
        if not 0 <= self.alpha <= 31:
            raise NitroError("material %s: alpha must be 0-31" % self.name)
        if self.cull not in CULL:
            raise NitroError("material %s: cull must be back, front or none" % self.name)
        c555 = lambda c: c[0] | c[1] << 5 | c[2] << 10   # noqa: E731
        diff_amb = c555(self.diffuse) | 0x8000 | c555(self.ambient) << 16   # bit 15: diffuse is the vertex color
        poly = (1 if self.lit else 0) | CULL[self.cull] << 6 | (0x8000 if self.fog else 0) | self.alpha << 16
        tex = 0
        if self.texture:
            tex = (self.repeat[0] << 16 | self.repeat[1] << 17 | self.flip[0] << 18 | self.flip[1] << 19)
        w, h = self.tex_size if self.texture else (0, 0)
        return struct.pack("<HHIIIIIIHHHHii", 0, 44, diff_amb, 0, poly, 0x3F1FF8FF, tex, 0xFFFFFFFF, 0, 0x1FCE,
                           w, h, 4096, 4096)


def _fx16(v, what):
    i = int(round(v * 4096))
    if not -0x8000 <= i <= 0x7FFF:
        raise NitroError("%s out of range" % what)
    return i


def _gx_pack(cmds):
    """[(cmd, [u32 params])] -> display list bytes (4 commands per word, then their params)."""
    out = bytearray()
    for i in range(0, len(cmds), 4):
        group = cmds[i:i + 4]
        ids = [c for c, _ in group] + [0] * (4 - len(group))
        out += bytes(ids)
        for _, params in group:
            for p in params:
                out += struct.pack("<I", p & 0xFFFFFFFF)
    return bytes(out)


def _vtx_cmd(v, prev):
    """Shortest GX command for vertex v (fx units, already divided by posScale)."""
    if prev is not None:
        d = [v[i] - prev[i] for i in range(3)]
        if all(-512 <= x <= 511 for x in d):
            return (0x28, [(d[0] & 0x3FF) | (d[1] & 0x3FF) << 10 | (d[2] & 0x3FF) << 20])
    if all(x % 64 == 0 and -512 <= x // 64 <= 511 for x in v):
        a = [x // 64 for x in v]
        return (0x24, [(a[0] & 0x3FF) | (a[1] & 0x3FF) << 10 | (a[2] & 0x3FF) << 20])
    if prev is not None:
        for cmd, keep, (i, j) in ((0x25, 2, (0, 1)), (0x26, 1, (0, 2)), (0x27, 0, (1, 2))):
            if v[keep] == prev[keep]:
                return (cmd, [(v[i] & 0xFFFF) | (v[j] & 0xFFFF) << 16])
    return (0x23, [(v[0] & 0xFFFF) | (v[1] & 0xFFFF) << 16, v[2] & 0xFFFF])


def _strips(polys, key):
    """Polygons of one size -> [(prim, [vertex])] GX blocks: strips where they chain, one list for the rest.

    Strip vertex order is what the hardware (and nitro.py) turns back into the same
    polygons: a quad strip a, b, c, e, ... draws (a, b, e, c), then (c, e, e', c');
    a triangle strip v0, v1, v2, v3, ... draws (v0, v1, v2), (v2, v1, v3), ...
    Vertices join a strip only when every attribute matches (`key`).
    """
    if not polys:
        return []
    size = len(polys[0])
    keys = [[key(v) for v in p] for p in polys]
    starts = {}   # (key a, key b) -> polygons with a rotation starting a, b
    for i, k in enumerate(keys):
        for r in range(size):
            starts.setdefault((k[r], k[(r + 1) % size]), []).append((i, r))
    used = [False] * len(polys)

    def take(a, b):
        for i, r in starts.get((a, b), ()):
            if not used[i]:
                return i, r
        return None

    def rot(i, r):
        return [polys[i][(r + j) % size] for j in range(size)]

    blocks, singles = [], []
    for i0 in range(len(polys)):
        if used[i0]:
            continue
        best = None
        for r0 in range(size):
            used[i0] = True
            q = rot(i0, r0)
            if size == 4:
                verts = [q[0], q[1], q[3], q[2]]
            else:
                verts = [q[0], q[1], q[2]]
            chain = [i0]
            while True:
                n = len(verts)
                if size == 4:
                    nxt = take(key(verts[-2]), key(verts[-1]))
                else:
                    a, b = (verts[-2], verts[-1]) if (n + 1) % 2 else (verts[-1], verts[-2])
                    nxt = take(key(a), key(b))
                if nxt is None:
                    break
                used[nxt[0]] = True
                chain.append(nxt[0])
                q2 = rot(*nxt)
                verts += [q2[3], q2[2]] if size == 4 else [q2[2]]
            for c in chain:
                used[c] = False
            if best is None or len(chain) > len(best[0]):
                best = (chain, verts)
        chain, verts = best
        for c in chain:
            used[c] = True
        if len(chain) == 1:
            singles += polys[i0]
        else:
            blocks.append((3 if size == 4 else 2, verts))
    if singles:
        blocks.append((1 if size == 4 else 0, singles))
    return blocks


def _normal10(n):
    """NORMAL fields (s0.9 each). Vectors already of unit length (within 1%, e.g. decoded
    ones) are kept as they are, so re-encoding a decoded model doesn't move them."""
    nx, ny, nz = n or (0.0, 1.0, 0.0)
    ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
    if abs(ln - 1.0) < 0.01:
        ln = 1.0
    return tuple(max(-512, min(511, int(round(c / ln * 512)))) for c in (nx, ny, nz))


def _vertex_key(mt, pos_scale):
    """A vertex as the display list will store it, for joining strips."""
    def key(v):
        pos, uv, nrm, col = v
        k = [tuple(int(round(c / pos_scale * 4096)) for c in pos)]
        if mt.texture:
            k.append(tuple(int(round(c * 16)) for c in (uv or (0, 0))))
        if mt.lit and nrm is not None:
            k.append(_normal10(nrm))
        else:
            k.append(tuple(int(round(c * 31 / 255)) for c in (col or (255, 255, 255))))
        return tuple(k)
    return key


def _pow2_scale(m, limit=7.99):
    s = 1
    while m / s > limit:
        s *= 2
    return s


def build_terrain(name, materials, polygons):
    """Materials [TerrainMaterial] and polygons [(material index, [vertex])] -> NSBMD bytes.

    A vertex is (pos (x, y, z) model units, uv (s, t) texels or None, normal (x, y, z)
    or None, color (r, g, b) 0-255 or None). A lit material's vertices send their normal
    (the hardware lights them); vertices without one, and all vertices of unlit
    materials, send their color (white if None). Polygons have 3 or 4 vertices; quads
    must be planar and convex. Raises NitroError if the model can't be stored.
    """
    if not polygons:
        raise NitroError("the model has no polygons")
    pts = [v[0] for _, vs in polygons for v in vs]
    m_abs = max(abs(c) for p in pts for c in p)
    pos_scale = _pow2_scale(m_abs)
    used = sorted({mi for mi, _ in polygons})
    by_mat = {mi: [vs for m2, vs in polygons if m2 == mi] for mi in used}
    model = Model()
    model.name = name
    model.nodes = [("terrain", struct.pack("<Hh", 0xF807, 4096))]
    mats = [materials[mi] for mi in used]
    model.materials = [Material(mt.name, mt.data()) for mt in mats]
    stats = {"vtx": 0, "tri": 0, "quad": 0}
    sbc = bytearray(b"\x26\x00\x00\x00\x00\x02\x00\x01\x0b")
    for si, mi in enumerate(used):
        mt = materials[mi]
        cmds = []
        last_uv = last_n = last_c = None
        sent = set()   # 1 NORMAL, 2 COLOR
        for size in (3, 4):
            group = [vs for vs in by_mat[mi] if len(vs) == size]
            stats["tri" if size == 3 else "quad"] += len(group)
            for prim, block in _strips(group, _vertex_key(mt, pos_scale)):
                cmds.append((0x40, [prim]))
                prev = None
                for pos, uv, nrm, col in block:
                    stats["vtx"] += 1
                    if mt.texture:
                        st = (int(round((uv or (0, 0))[0] * 16)), int(round((uv or (0, 0))[1] * 16)))
                        if not all(-0x8000 <= x <= 0x7FFF for x in st):
                            raise NitroError("material %s: texture coordinate %s is beyond +-2048 texels"
                                             % (mt.name, uv))
                        if st != last_uv:
                            cmds.append((0x22, [(st[0] & 0xFFFF) | (st[1] & 0xFFFF) << 16]))
                            last_uv = st
                    if mt.lit and nrm is not None:
                        q = _normal10(nrm)
                        if q != last_n:
                            cmds.append((0x21, [(q[0] & 0x3FF) | (q[1] & 0x3FF) << 10 | (q[2] & 0x3FF) << 20]))
                            last_n, last_c = q, None   # NORMAL sets the vertex color (lighting)
                            sent.add(1)
                    else:
                        r, g, b = col or (255, 255, 255)
                        c = (int(round(r * 31 / 255)) | int(round(g * 31 / 255)) << 5 |
                             int(round(b * 31 / 255)) << 10)
                        if c != last_c:
                            cmds.append((0x20, [c]))
                            last_c, last_n = c, None
                            sent.add(2)
                    v = tuple(_fx16(c / pos_scale, "vertex %s" % (pos,)) for c in pos)
                    cmds.append(_vtx_cmd(v, prev))
                    prev = v
                cmds.append((0x41, []))
        flag = (4 if mt.texture else 0) | (1 if 1 in sent else 0) | (2 if 2 in sent else 0)
        model.shapes.append(Shape("polygon%d" % si, flag, _gx_pack(cmds)))
        sbc += bytes((0x04, si, 0x05, si))
    sbc += b"\x2b\x01"
    model.sbc = bytes(sbc) + b"\0" * (-len(sbc) % 4)
    for attr, key in (("tex_map", "texture"), ("pltt_map", "palette")):
        names = sorted({getattr(mt, key) for mt in mats if getattr(mt, key)})
        setattr(model, attr, [(n, [i for i, mt in enumerate(mats) if getattr(mt, key) == n], 0) for n in names])
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    box = lo + [hi[i] - lo[i] for i in range(3)]
    box_scale = _pow2_scale(max(abs(c) for c in box))
    model.info = struct.pack("<BBBBBBBBiiHHHH6hii", 0, 0, 0, 1, len(mats), len(used), 1, 0,
                             pos_scale * 4096, int(4096 / pos_scale), stats["vtx"], stats["tri"] + stats["quad"],
                             stats["tri"], stats["quad"], *(_fx16(c / box_scale, "bounding box") for c in box),
                             box_scale * 4096, int(4096 / box_scale))
    data = write([model])
    if len(data) > MAX_MODEL_SIZE:
        raise NitroError("the model is 0x%X bytes; the game reads at most 0x%X (MAP_LOAD_PRIMARY_BUFFER_SIZE)"
                         % (len(data), MAX_MODEL_SIZE))
    return data
