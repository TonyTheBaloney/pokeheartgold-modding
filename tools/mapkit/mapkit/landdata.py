# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Land data: one 32x32-tile cell of terrain, as text where it can be.

The game reads NARC_fielddata_landdata_land_data (files/a/0/6/5); each member is
(src/field/map_load_manager.c):

    u32 permissionsSize, propsSize, modelSize, bdhcSize
    u32 soundplateHeader   0x1234 | (soundplate bytes << 16)
    u8  soundplates[]
    u16 permissions[32 * 32]   behavior | attr << 8 (bits 8-14) | collision << 15
    MapPropArcData props[]     0x30 each (src/field/map_prop_manager.c)
    NSBMD model, BDHC heights

data/landdata/NNNN/ (NNNN = member number, which layout.json cells name):

    permissions.txt   collision, behavior and attribute grids
    props.json        placed props (models from the area's prop list)
    soundplates.bin   only if the cell has any
    model.nsbmd       3D terrain (binary; `mapkit terrain import` makes one from OBJ)
    terrain.bdhc      terrain heights (binary), or instead
    heights.json      the same as text (bdhc.py), compiled to BDHC here
"""

import json
import os
import struct

LANDDATA_DIR = "data/landdata"
SIZE = 32
SOUNDPLATE_MAGIC = 0x1234
PROP = struct.Struct("<i3i3i3i8s")
FX_ONE = 4096
MAX_SOUNDPLATES = 0x200  # MapSoundplates.data
MAX_PROPS = 32           # MAP_PROP_MAX, include/field/map_load_manager.h


class LandDataError(Exception):
    pass


def chunk_dirs(root):
    d = os.path.join(root, LANDDATA_DIR)
    names = sorted(n for n in os.listdir(d) if n.isdigit()) if os.path.isdir(d) else []
    for i, n in enumerate(names):
        if int(n) != i:
            raise LandDataError("%s: folders must be numbered 0000.. without gaps (found %s at %d)" % (d, n, i))
    return [os.path.join(d, n) for n in names]


# --- permissions.txt ---------------------------------------------------------------

class Permissions:
    def __init__(self, words=None):
        words = words or [0] * (SIZE * SIZE)
        self.collision = [w >> 15 & 1 for w in words]
        self.behavior = [w & 0xFF for w in words]
        self.attr = [w >> 8 & 0x7F for w in words]

    def words(self):
        return [b | a << 8 | c << 15 for b, a, c in zip(self.behavior, self.attr, self.collision)]

    def to_text(self):
        rows = range(SIZE)
        out = ["[collision]  # blocks movement, . is open"]
        out += ["".join("#" if self.collision[y * SIZE + x] else "." for x in range(SIZE)) for y in rows]
        out.append("[behavior]  TILE_BEHAVIOR_* value in hex (include/constants/metatile_behavior.h)")
        out += [" ".join("%02X" % self.behavior[y * SIZE + x] for x in range(SIZE)) for y in rows]
        if any(self.attr):
            out.append("[attr]  bits 8-14 of the permission word, hex (FieldSystem_GetTileAttrBits8To14)")
            out += [" ".join("%02X" % self.attr[y * SIZE + x] for x in range(SIZE)) for y in rows]
        return "\n".join(out) + "\n"

    @classmethod
    def from_text(cls, text, where="permissions.txt"):
        sections, cur = {}, None
        for n, line in enumerate(text.splitlines(), 1):
            if line.startswith("["):
                cur = line[1:].split("]")[0].strip()
                if cur not in ("collision", "behavior", "attr"):
                    raise LandDataError("%s:%d: unknown section %r" % (where, n, cur))
                sections[cur] = []
            elif line.strip():
                if cur is None:
                    raise LandDataError("%s:%d: grid before a [section] line" % (where, n))
                sections[cur].append((n, line.strip()))
        p = cls()
        for name in ("collision", "behavior"):
            if name not in sections:
                raise LandDataError("%s: missing [%s] section" % (where, name))
        for name, rows in sections.items():
            if len(rows) != SIZE:
                raise LandDataError("%s: %s has %d rows, not %d" % (where, name, len(rows), SIZE))
            values = []
            for n, row in rows:
                if name == "collision":
                    if len(row) != SIZE or set(row) - {"#", "."}:
                        raise LandDataError("%s:%d: expected %d of # or ." % (where, n, SIZE))
                    values += [ch == "#" for ch in row]
                else:
                    toks = row.split()
                    if len(toks) != SIZE:
                        raise LandDataError("%s:%d: expected %d hex values, got %d" % (where, n, SIZE, len(toks)))
                    try:
                        vals = [int(t, 16) for t in toks]
                    except ValueError:
                        raise LandDataError("%s:%d: not hex" % (where, n))
                    limit = 0xFF if name == "behavior" else 0x7F
                    if any(v > limit for v in vals):
                        raise LandDataError("%s:%d: %s values go up to %02X" % (where, n, name, limit))
                    values += vals
            setattr(p, name, [int(v) for v in values])
        return p


# --- props.json -----------------------------------------------------------------------

def _fx(v):
    return v / FX_ONE


def _to_fx(v, where):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise LandDataError("%s: %r is not a number" % (where, v))
    raw = round(v * FX_ONE)
    if raw / FX_ONE != v:
        raise LandDataError("%s: %r is not a multiple of 1/4096" % (where, v))
    if not -0x80000000 <= raw < 0x80000000:
        raise LandDataError("%s: %r is out of range" % (where, v))
    return raw


def props_from_bytes(data):
    out = []
    for i in range(len(data) // PROP.size):
        model, *vals, pad = PROP.unpack_from(data, i * PROP.size)
        if pad != bytes(8):
            raise LandDataError("prop %d: non-zero padding" % i)
        out.append({"model": model, "position": [_fx(v) for v in vals[0:3]],
                    "rotation": [_fx(v) for v in vals[3:6]], "scale": [_fx(v) for v in vals[6:9]]})
    return out


def props_to_bytes(props, where="props.json"):
    if not isinstance(props, list):
        raise LandDataError("%s: expected a list" % where)
    if len(props) > MAX_PROPS:
        raise LandDataError("%s: %d props; the game loads at most %d per cell" % (where, len(props), MAX_PROPS))
    out = b""
    for i, p in enumerate(props):
        w = "%s[%d]" % (where, i)
        if not isinstance(p, dict) or set(p) != {"model", "position", "rotation", "scale"}:
            raise LandDataError("%s: expected model, position, rotation, scale" % w)
        if isinstance(p["model"], bool) or not isinstance(p["model"], int) or p["model"] < 0:
            raise LandDataError("%s: model must be a prop number" % w)
        vals = []
        for key in ("position", "rotation", "scale"):
            if not isinstance(p[key], list) or len(p[key]) != 3:
                raise LandDataError("%s: %s must be [x, y, z]" % (w, key))
            vals += [_to_fx(v, "%s.%s" % (w, key)) for v in p[key]]
        out += PROP.pack(p["model"], *vals, bytes(8))
    return out


def write_props_json(path, props):
    lines = ["["]
    for i, p in enumerate(props):
        lines.append('    { "model": %d, "position": %s, "rotation": %s, "scale": %s }%s' % (
            p["model"], json.dumps(p["position"]), json.dumps(p["rotation"]), json.dumps(p["scale"]),
            "," if i < len(props) - 1 else ""))
    lines.append("]")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# --- whole member ---------------------------------------------------------------------

def split_member(data):
    perm, props, model, bdhc = struct.unpack_from("<4I", data)
    head = struct.unpack_from("<I", data, 16)[0]
    if head & 0xFFFF != SOUNDPLATE_MAGIC:
        raise LandDataError("soundplate header %08X has no 0x1234 magic" % head)
    pos = 20
    parts = {}
    for name, size in (("soundplates", head >> 16), ("permissions", perm), ("props", props),
                       ("model", model), ("bdhc", bdhc)):
        parts[name] = data[pos:pos + size]
        pos += size
    if pos != len(data):
        raise LandDataError("sections end at %d but the member is %d bytes" % (pos, len(data)))
    if perm != SIZE * SIZE * 2:
        raise LandDataError("permissions are %d bytes, not %d" % (perm, SIZE * SIZE * 2))
    return parts


def extract(data, out_dir):
    parts = split_member(data)
    os.makedirs(out_dir, exist_ok=True)
    words = list(struct.unpack("<%dH" % (SIZE * SIZE), parts["permissions"]))
    with open(os.path.join(out_dir, "permissions.txt"), "w", encoding="utf-8") as f:
        f.write(Permissions(words).to_text())
    write_props_json(os.path.join(out_dir, "props.json"), props_from_bytes(parts["props"]))
    if parts["soundplates"]:
        with open(os.path.join(out_dir, "soundplates.bin"), "wb") as f:
            f.write(parts["soundplates"])
    with open(os.path.join(out_dir, "model.nsbmd"), "wb") as f:
        f.write(parts["model"])
    with open(os.path.join(out_dir, "terrain.bdhc"), "wb") as f:
        f.write(parts["bdhc"])


def build(chunk_dir):
    """data/landdata/NNNN/ -> NARC member bytes."""
    def read(name, mode="rb"):
        with open(os.path.join(chunk_dir, name), mode, **({} if "b" in mode else {"encoding": "utf-8"})) as f:
            return f.read()
    where = os.path.relpath(chunk_dir)
    perms = Permissions.from_text(read("permissions.txt", "r"), os.path.join(where, "permissions.txt"))
    permissions = struct.pack("<%dH" % (SIZE * SIZE), *perms.words())
    try:
        props_doc = json.loads(read("props.json", "r"))
    except json.JSONDecodeError as e:
        raise LandDataError("%s/props.json:%d: %s" % (where, e.lineno, e.msg))
    props = props_to_bytes(props_doc, os.path.join(where, "props.json"))
    sp_path = os.path.join(chunk_dir, "soundplates.bin")
    soundplates = read("soundplates.bin") if os.path.exists(sp_path) else b""
    if len(soundplates) > MAX_SOUNDPLATES:
        raise LandDataError("%s: soundplates.bin is %d bytes; the game reads at most %d"
                            % (where, len(soundplates), MAX_SOUNDPLATES))
    model = read("model.nsbmd")
    has_json = os.path.exists(os.path.join(chunk_dir, "heights.json"))
    has_bin = os.path.exists(os.path.join(chunk_dir, "terrain.bdhc"))
    if has_json and has_bin:
        raise LandDataError("%s: both heights.json and terrain.bdhc; keep one" % where)
    if has_json:
        from . import bdhc as bdhc_mod
        try:
            heights = bdhc_mod.read_json(os.path.join(chunk_dir, "heights.json"))
        except bdhc_mod.BdhcError as e:
            raise LandDataError(str(e))
        problems = bdhc_mod.check(heights, os.path.join(where, "heights.json"))
        if any("buffer" in p or "65535" in p for p in problems):
            raise LandDataError(problems[0])
        bdhc = heights.to_bytes()
    else:
        bdhc = read("terrain.bdhc")
    return (struct.pack("<5I", len(permissions), len(props), len(model), len(bdhc),
                        SOUNDPLATE_MAGIC | len(soundplates) << 16)
            + soundplates + permissions + props + model + bdhc)


def load_chunk(chunk_dir):
    """For tools (the editor): permissions and props of one cell."""
    with open(os.path.join(chunk_dir, "permissions.txt"), encoding="utf-8") as f:
        perms = Permissions.from_text(f.read(), os.path.join(chunk_dir, "permissions.txt"))
    with open(os.path.join(chunk_dir, "props.json"), encoding="utf-8") as f:
        props = json.load(f)
    return perms, props


# --- NARC ------------------------------------------------------------------------------

def narc_members(data):
    if data[:4] != b"NARC":
        raise LandDataError("not a NARC")
    off, blocks = struct.unpack_from("<H", data, 12)[0], {}
    while off < len(data):
        blocks[data[off:off + 4]] = off
        off += struct.unpack_from("<I", data, off + 4)[0]
    fat, img = blocks[b"BTAF"], blocks[b"GMIF"] + 8
    n = struct.unpack_from("<H", data, fat + 8)[0]
    return [data[img + s:img + e] for s, e in (struct.unpack_from("<II", data, fat + 12 + 8 * i) for i in range(n))]


def narc_bytes(members):
    """A NARC like the retail ones: no file names, members 4-aligned, 0xFF padding."""
    fat, img = b"", b""
    for m in members:
        fat += struct.pack("<II", len(img), len(img) + len(m))
        img += m + b"\xff" * (-len(m) % 4)
    btaf = b"BTAF" + struct.pack("<IHH", 12 + len(fat), len(members), 0) + fat
    btnf = b"BTNF" + struct.pack("<IIHH", 16, 4, 0, 1)
    gmif = b"GMIF" + struct.pack("<I", 8 + len(img)) + img
    body = btaf + btnf + gmif
    return b"NARC" + struct.pack("<HHIHH", 0xFFFE, 0x0100, 16 + len(body), 16, 3) + body


# --- migration and packing -------------------------------------------------------------

PREBUILT = "files/a/0/6/5"


def migrate(root):
    """files/a/0/6/5 -> data/landdata/NNNN/ (checks the round trip first)."""
    src = os.path.join(root, PREBUILT)
    with open(src, "rb") as f:
        data = f.read()
    members = narc_members(data)
    out = os.path.join(root, LANDDATA_DIR)
    for i, m in enumerate(members):
        extract(m, os.path.join(out, "%04d" % i))
    if narc_bytes([build(d) for d in chunk_dirs(root)]) != data:
        raise LandDataError("data/landdata does not rebuild %s" % PREBUILT)
    os.remove(src)
    return len(members)


def pack(root, out_narc, depfile=None):
    dirs = chunk_dirs(root)
    data = narc_bytes([build(d) for d in dirs])
    with open(out_narc, "wb") as f:
        f.write(data)
    if depfile:
        # Every file read, plus the folders: a folder changes when a file is added or removed
        # (terrain.bdhc replaced by heights.json), so the build notices without reconfiguring.
        deps = [os.path.join(root, LANDDATA_DIR)] + dirs + file_list(root)
        esc = lambda p: p.replace("\\", "/").replace(" ", "\\ ")  # noqa: E731
        with open(depfile, "w", encoding="utf-8") as f:
            # the target exactly as the build named it (ninja matches it), dependencies absolute
            f.write("%s: \\\n" % esc(out_narc) + " \\\n".join("  " + esc(os.path.abspath(p)) for p in deps) + "\n")


def file_list(root):
    """Every source file, for the build's dependency list."""
    out = []
    for d in chunk_dirs(root):
        out += [os.path.join(d, n) for n in sorted(os.listdir(d))]
    return out
