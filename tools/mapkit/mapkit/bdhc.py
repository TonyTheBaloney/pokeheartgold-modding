# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""BDHC: the heights the player and NPCs walk on, one file per terrain cell.

The game reads it in src/field/bdhc.c (structures in include/field/bdhc.h) and
queries it from src/field_terrain.c. A file is a list of **plates**: axis-aligned
rectangles over the x/z plane, each with a plane `normal . (x, y, z) + d = 0`
that gives the height inside it. **Strips** cut the cell along z so a lookup
only tests the plates that reach its z.

This module reads and writes the binary losslessly (`Bdhc.from_bytes`,
`to_bytes`), rebuilds the derived parts (pools, strips) from plates the way
the retail files were made (`build`), answers height queries exactly as the
game does (`height`), converts to and from the text form `heights.json`, and
generates plates from triangles (`generate`).

All values are model units (one tile = 16) relative to the cell's centre, x
east, z south, y up, stored as fx32 (4096 = 1.0).
"""

import json
import math
import struct

FX = 4096
MAX_BUFFER = 0x9000           # BDHC_BUFFER_SIZE / MAP_LOAD_SECONDARY_BUFFER_SIZE: everything after the header
MAX_CANDIDATES = 10           # BDHC_MAX_HEIGHT_CANDIDATES: plates tested per lookup that contain the point
HALF = 256 * FX               # a cell spans -256..256 in x and z

NEAREST, HIGHEST, LOWEST = 0, 1, 2   # enum BdhcHeightMode


class BdhcError(Exception):
    pass


# --- fixed point, as the NitroSDK does it ---------------------------------------------------

def fx_mul(a, b):
    """FX_MulInline: (a * b + 0x800) >> 12."""
    return (a * b + 0x800) >> 12


def fx_div(n, d):
    """FX_Div: the hardware divides (n << 32) by d (signed, truncating), then rounds to fx32."""
    if d == 0:
        raise BdhcError("division by zero (plate with normal y = 0)")
    q = abs(n << 32) // abs(d)
    if (n < 0) != (d < 0):
        q = -q
    return (q + (1 << 19)) >> 20


def to_fx(v):
    return int(round(v * FX))


# --- the file -------------------------------------------------------------------------------

class Plate:
    """A rectangle (fx32 corners, x0 <= x1, z0 <= z1) and its plane (fx32 normal, d)."""

    __slots__ = ("x0", "z0", "x1", "z1", "normal", "d")

    def __init__(self, x0, z0, x1, z1, normal, d):
        self.x0, self.z0, self.x1, self.z1 = x0, z0, x1, z1
        self.normal, self.d = tuple(normal), d

    def contains(self, x, z):
        return self.x0 <= x <= self.x1 and self.z0 <= z <= self.z1

    def height_at(self, x, z):
        nx, ny, nz = self.normal
        return fx_div(-(self.d + (fx_mul(nx, x) + fx_mul(nz, z))), ny)

    def __eq__(self, other):
        return all(getattr(self, k) == getattr(other, k) for k in self.__slots__)

    def __repr__(self):
        return "Plate(x=%g..%g z=%g..%g n=%s d=%g)" % (self.x0 / FX, self.x1 / FX, self.z0 / FX, self.z1 / FX,
                                                    tuple(v / FX for v in self.normal), self.d / FX)


class Bdhc:
    """The file's arrays as stored: pools, plates as indices, strips, access list."""

    def __init__(self):
        self.points = []      # (x, z)
        self.normals = []     # (x, y, z)
        self.constants = []   # d
        self.plates = []      # (point, point, normal, constant) indices
        self.strips = []      # (upper z bound, count, offset into access)
        self.access = []      # plate indices

    @classmethod
    def from_bytes(cls, data):
        if data[:4] != b"BDHC":
            raise BdhcError("not a BDHC file")
        counts = struct.unpack_from("<6H", data, 4)
        b = cls()
        o = 16
        for n, (attr, fmt) in zip(counts, (("points", "<2i"), ("normals", "<3i"), ("constants", "<i"),
                                           ("plates", "<4H"), ("strips", "<iHH"), ("access", "<H"))):
            size = struct.calcsize(fmt)
            items = [struct.unpack_from(fmt, data, o + size * i) for i in range(n)]
            if fmt in ("<i", "<H"):
                items = [v[0] for v in items]
            setattr(b, attr, items)
            o += size * n
        if o != len(data):
            raise BdhcError("BDHC is %d bytes but its arrays end at %d" % (len(data), o))
        return b

    def to_bytes(self):
        out = bytearray(b"BDHC")
        out += struct.pack("<6H", len(self.points), len(self.normals), len(self.constants), len(self.plates),
                           len(self.strips), len(self.access))
        for p in self.points:
            out += struct.pack("<2i", *p)
        for n in self.normals:
            out += struct.pack("<3i", *n)
        for c in self.constants:
            out += struct.pack("<i", c)
        for p in self.plates:
            out += struct.pack("<4H", *p)
        for s in self.strips:
            out += struct.pack("<iHH", *s)
        for a in self.access:
            out += struct.pack("<H", a)
        return bytes(out)

    def buffer_size(self):
        """Bytes the game's buffer needs (Bdhc_SetBuffers)."""
        return (8 * len(self.points) + 12 * len(self.normals) + 4 * len(self.constants) + 8 * len(self.plates)
                + 8 * len(self.strips) + 2 * len(self.access))

    def resolved_plates(self):
        out = []
        for a, b, n, c in self.plates:
            (x0, z0), (x1, z1) = self.points[a], self.points[b]
            out.append(Plate(x0, z0, x1, z1, self.normals[n], self.constants[c]))
        return out

    # -- the game's lookup (Bdhc_GetHeight) --

    def find_strip(self, z):
        """Bdhc_FindStrip, including its off-by-one search: index or None."""
        count = len(self.strips)
        if count == 0:
            return None
        if count == 1:
            return 0
        count -= 1
        lo, mid = 0, count // 2
        while True:
            if self.strips[mid][0] > z:
                count -= 1
                if count > lo:
                    count = mid
                    mid = (lo + count) // 2
                else:
                    return mid
            else:
                lo += 1
                if lo < count:
                    lo = mid
                    mid = (lo + count) // 2
                else:
                    return mid + 1

    def height(self, x, z, mode=NEAREST, current_y=0):
        """fx32 height at fx32 (x, z) as the game computes it, or None."""
        s = self.find_strip(z)
        if s is None:
            return None
        _, count, offset = self.strips[s]
        cands = []
        for i in range(count):
            a, b, n, c = self.plates[self.access[offset + i]]
            (x0, z0), (x1, z1) = self.points[a], self.points[b]
            if min(x0, x1) <= x <= max(x0, x1) and min(z0, z1) <= z <= max(z0, z1):
                nx, ny, nz = self.normals[n]
                if ny == 0:
                    # The DS divider's division-by-zero result; one retail plate is vertical. Skipped here.
                    continue
                cands.append(fx_div(-(self.constants[c] + (fx_mul(nx, x) + fx_mul(nz, z))), ny))
                if len(cands) >= MAX_CANDIDATES:
                    break
        if not cands:
            return None
        if mode == HIGHEST:
            return max(cands)
        if mode == LOWEST:
            return min(cands)
        best = cands[0]
        for y in cands[1:]:
            if abs(current_y - y) < abs(current_y - best):
                best = y
        return best


def build(plates, normal_ids=None, constant_ids=None):
    """Plates -> Bdhc laid out like the retail files.

    Points, normals and constants are pooled in first-use order without
    duplicates. (Some retail files repeat a normal or constant: their converter
    merged values before rounding. `normal_ids` / `constant_ids` give explicit
    pool slots to reproduce that.) Strip k runs from the k-th to the (k+1)-th
    distinct plate z edge and stores the upper edge; it lists, in plate order,
    every plate with z0 <= upper and z1 > lower.
    """
    b = Bdhc()
    pidx, nidx, cidx = {}, {}, {}

    def pool(table, index, value):
        if value not in index:
            index[value] = len(table)
            table.append(value)
        return index[value]

    for i, p in enumerate(plates):
        if p.x0 > p.x1 or p.z0 > p.z1:
            raise BdhcError("plate %d: corners out of order" % i)
        a = pool(b.points, pidx, (p.x0, p.z0))
        c = pool(b.points, pidx, (p.x1, p.z1))
        if normal_ids is not None:
            n = normal_ids[i]
            while len(b.normals) <= n:
                b.normals.append(None)
            b.normals[n] = p.normal
        else:
            n = pool(b.normals, nidx, p.normal)
        if constant_ids is not None:
            k = constant_ids[i]
            while len(b.constants) <= k:
                b.constants.append(None)
            b.constants[k] = p.d
        else:
            k = pool(b.constants, cidx, p.d)
        b.plates.append((a, c, n, k))
    if None in b.normals or None in b.constants:
        raise BdhcError("explicit pool slots leave gaps")
    zs = sorted({p.z0 for p in plates} | {p.z1 for p in plates})
    for k in range(len(zs) - 1):
        lo, hi = zs[k], zs[k + 1]
        members = [i for i, p in enumerate(plates) if p.z0 <= hi and p.z1 > lo]
        b.strips.append((hi, len(members), len(b.access)))
        b.access += members
    return b


def check(b, where="terrain.bdhc"):
    """Problems the game would hit, as messages."""
    out = []
    if b.buffer_size() > MAX_BUFFER:
        out.append("%s: needs 0x%X bytes; the game's buffer is 0x%X" % (where, b.buffer_size(), MAX_BUFFER))
    for name in ("points", "normals", "constants", "plates", "strips", "access"):
        if len(getattr(b, name)) > 0xFFFF:
            out.append("%s: more than 65535 %s" % (where, name))
    plates = b.resolved_plates()
    for i, p in enumerate(plates):
        if p.normal[1] == 0:
            out.append("%s: plate %d is vertical (normal y = 0); the height can't be computed" % (where, i))
    # where more than MAX_CANDIDATES plates hold a point the game ignores the rest (sampled every 4 units)
    crowded, worst = 0, 0
    for zi in range(-256, 257, 4):
        z = zi * FX
        row = [p for p in plates if p.z0 <= z <= p.z1]
        if len(row) <= MAX_CANDIDATES:
            continue
        for xi in range(-256, 257, 4):
            x = xi * FX
            k = sum(1 for p in row if p.x0 <= x <= p.x1)
            if k > MAX_CANDIDATES:
                crowded += 1
                worst = max(worst, k)
    if crowded:
        out.append("%s: at %d points up to %d plates overlap; the game only considers the first %d it finds there"
                   % (where, crowded, worst, MAX_CANDIDATES))
    return out


# --- heights.json -----------------------------------------------------------------------------

UP = (0, FX, 0)


def _num(v):
    f = v / FX
    return int(f) if f == int(f) else f


def to_json(b):
    """Bdhc -> heights.json document. Flat plates are {"x", "z", "y"}; others carry "normal" and "d"."""
    plates = []
    for p in b.resolved_plates():
        e = {"x": [_num(p.x0), _num(p.x1)], "z": [_num(p.z0), _num(p.z1)]}
        if p.normal == UP:
            e["y"] = _num(-p.d)
        else:
            e["normal"] = [_num(v) for v in p.normal]
            e["d"] = _num(p.d)
        plates.append(e)
    return {"plates": plates}


def _fx_exact(v, where):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise BdhcError("%s: %r is not a number" % (where, v))
    f = v * FX
    if abs(f - round(f)) > 1e-6:
        raise BdhcError("%s: %r is not a multiple of 1/4096" % (where, v))
    return int(round(f))


def plate_from_json(e, where):
    known = {"x", "z", "y", "normal", "d", "ramp"}
    extra = set(e) - known
    if extra:
        raise BdhcError("%s: unknown key %s" % (where, sorted(extra)[0]))
    for k in ("x", "z"):
        if not (isinstance(e.get(k), list) and len(e[k]) == 2):
            raise BdhcError("%s: \"%s\" must be [min, max]" % (where, k))
    x0, x1 = (_fx_exact(v, where + ".x") for v in e["x"])
    z0, z1 = (_fx_exact(v, where + ".z") for v in e["z"])
    if x0 > x1 or z0 > z1:
        raise BdhcError("%s: \"x\" and \"z\" must be [min, max]" % where)
    forms = [k for k in ("y", "normal", "ramp") if k in e]
    if len(forms) != 1 or ("d" in e) != (forms == ["normal"]):
        raise BdhcError("%s: give exactly one of \"y\", \"normal\" + \"d\", \"ramp\"" % where)
    if "y" in e:
        return Plate(x0, z0, x1, z1, UP, -_fx_exact(e["y"], where + ".y"))
    if "normal" in e:
        if "d" not in e or not (isinstance(e["normal"], list) and len(e["normal"]) == 3):
            raise BdhcError("%s: \"normal\" needs three numbers and a \"d\"" % where)
        n = tuple(_fx_exact(v, where + ".normal") for v in e["normal"])
        return Plate(x0, z0, x1, z1, n, _fx_exact(e["d"], where + ".d"))
    r = e["ramp"]
    if not (isinstance(r, dict) and r.get("along") in ("x", "z") and isinstance(r.get("y"), list)
            and len(r["y"]) == 2):
        raise BdhcError("%s: \"ramp\" is {\"along\": \"x\" or \"z\", \"y\": [height at min, height at max]}" % where)
    lo, hi = (x0, x1) if r["along"] == "x" else (z0, z1)
    y0, y1 = (_fx_exact(v, where + ".ramp.y") for v in r["y"])
    if hi == lo:
        raise BdhcError("%s: a ramp needs a non-zero length" % where)
    return ramp_plate(x0, z0, x1, z1, r["along"], y0, y1)


def ramp_plate(x0, z0, x1, z1, along, y0, y1):
    """A plate rising linearly from y0 at the low edge to y1 at the high edge (fx32 inputs)."""
    lo, hi = (x0, x1) if along == "x" else (z0, z1)
    slope = (y1 - y0) / (hi - lo)                    # dy / d(along)
    inv = 1.0 / math.sqrt(1.0 + slope * slope)
    na, ny = -slope * inv, inv
    n = (to_fx(na), to_fx(ny), 0) if along == "x" else (0, to_fx(ny), to_fx(na))
    # d so that the plane passes through (lo, y0); y = -(d + n_a * a) / n_y
    d = -(n[1] * y0 + (n[0] if along == "x" else n[2]) * lo) // FX
    return Plate(x0, z0, x1, z1, n, d)


def from_json(doc, where="heights.json"):
    if not isinstance(doc, dict) or set(doc) != {"plates"} or not isinstance(doc["plates"], list):
        raise BdhcError("%s: expected {\"plates\": [...]}" % where)
    return build([plate_from_json(e, "%s: plates[%d]" % (where, i)) for i, e in enumerate(doc["plates"])])


def write_json(path, b):
    doc = to_json(b)
    lines = ["{", "    \"plates\": ["]
    for i, e in enumerate(doc["plates"]):
        lines.append("        " + json.dumps(e, separators=(", ", ": ")) + ("," if i + 1 < len(doc["plates"]) else ""))
    lines += ["    ]", "}"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def read_json(path):
    with open(path, encoding="utf-8") as f:
        try:
            doc = json.load(f)
        except json.JSONDecodeError as e:
            raise BdhcError("%s:%d: %s" % (path, e.lineno, e.msg))
    return from_json(doc, path)


# --- generating plates from triangles -------------------------------------------------------------

def _plane(tri):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0:
        return None
    nx, ny, nz = nx / length, ny / length, nz / length
    if ny < 0:  # face the plane upward whatever the winding
        nx, ny, nz = -nx, -ny, -nz
    return (nx, ny, nz), -(nx * ax + ny * ay + nz * az)


def _inside(px, pz, tri):
    (ax, _, az), (bx, _, bz), (cx, _, cz) = tri
    d1 = (px - bx) * (az - bz) - (ax - bx) * (pz - bz)
    d2 = (px - cx) * (bz - cz) - (bx - cx) * (pz - cz)
    d3 = (px - ax) * (cz - az) - (cx - ax) * (pz - az)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def generate(triangles, grid=8.0, walkable=None, min_normal_y=0.5):
    """Triangles [((x, y, z) * 3)] in cell model units -> [Plate].

    Upward faces (normal y >= min_normal_y) are grouped by their plane as it will be
    stored (normal in 1/4096, d to 1/16 unit), so a plate is exact wherever it reaches. Each
    group covers the cells of a `grid`-unit lattice whose centre or a corner lies on one of
    its faces, and the covered cells are merged into rectangles (runs along x, extended
    along z). A plate can so reach up to half a cell past a face's edge.
    `walkable` (32 rows of 32 booleans, north to south) limits plates to those
    tiles, which keeps backdrops and roofs out of the heights.
    """
    if 512.0 / grid != int(512.0 / grid) or 16.0 / grid != int(16.0 / grid):
        raise BdhcError("grid must divide 16")
    n = int(512 / grid)
    per_tile = int(16 / grid)
    groups = {}   # (normal fx, d in 1/16) -> [normal, d, [tris]]
    for tri in triangles:
        pl = _plane(tri)
        if pl is None or pl[0][1] < min_normal_y:
            continue
        (nx, ny, nz), d = pl
        key = (to_fx(nx), to_fx(ny), to_fx(nz), int(round(d * 16)))
        groups.setdefault(key, [(nx, ny, nz), d, []])[2].append(tri)
    glist = list(groups.values())
    blocked = [[walkable is not None and not walkable[j // per_tile][i // per_tile] for i in range(n)]
               for j in range(n)]

    def cells_of(tris):
        for tri in tris:
            xs = [p[0] for p in tri]
            zs = [p[2] for p in tri]
            i0 = max(0, int(math.floor((min(xs) + 256) / grid)) - 1)
            i1 = min(n - 1, int(math.floor((max(xs) + 256) / grid)) + 1)
            j0 = max(0, int(math.floor((min(zs) + 256) / grid)) - 1)
            j1 = min(n - 1, int(math.floor((max(zs) + 256) / grid)) + 1)
            yield tri, i0, i1, j0, j1

    # pass 1: cells whose centre lies on a face of the group
    centre = []
    for (nx, ny, nz), d, tris in glist:
        cov = {}
        for tri, i0, i1, j0, j1 in cells_of(tris):
            for j in range(j0, j1 + 1):
                pz = -256 + (j + 0.5) * grid
                for i in range(i0, i1 + 1):
                    if (i, j) not in cov and not blocked[j][i] and _inside(-256 + (i + 0.5) * grid, pz, tri):
                        cov[(i, j)] = True
        centre.append(cov)

    # pass 2: faces too thin to hold a cell centre still reach the tile centres and edges
    # (with a grid dividing 16, cell corners are where walkers stand)
    plates = []
    for g, ((nx, ny, nz), d, tris) in enumerate(glist):
        covered = [[False] * n for _ in range(n)]
        for (i, j) in centre[g]:
            covered[j][i] = True
        for tri, i0, i1, j0, j1 in cells_of(tris):
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    if covered[j][i] or blocked[j][i]:
                        continue
                    x0, z0 = -256 + i * grid, -256 + j * grid
                    if not any(_inside(px, pz, tri) for px, pz in ((x0, z0), (x0 + grid, z0), (x0, z0 + grid),
                                                                  (x0 + grid, z0 + grid))):
                        continue
                    covered[j][i] = True
        nfx = (to_fx(nx), to_fx(ny), to_fx(nz))
        dfx = to_fx(d)
        for x0, z0, x1, z1 in _rectangles(covered):
            plates.append(Plate(to_fx(-256 + x0 * grid), to_fx(-256 + z0 * grid),
                                to_fx(-256 + x1 * grid), to_fx(-256 + z1 * grid), nfx, dfx))
    # stable order: by z, then x (as many retail files are)
    plates.sort(key=lambda p: (p.z0, p.x0, -p.normal[1], p.d))
    return plates


def _rectangles(covered):
    """Grid of booleans (rows = z) -> [(i0, j0, i1, j1)] in grid steps, i1/j1 exclusive."""
    n = len(covered)
    used = [[False] * n for _ in range(n)]
    out = []
    for j in range(n):
        i = 0
        while i < n:
            if not covered[j][i] or used[j][i]:
                i += 1
                continue
            i1 = i
            while i1 < n and covered[j][i1] and not used[j][i1]:
                i1 += 1
            j1 = j + 1
            while j1 < n and all(covered[j1][k] and not used[j1][k] for k in range(i, i1)):
                j1 += 1
            for jj in range(j, j1):
                for k in range(i, i1):
                    used[jj][k] = True
            out.append((i, j, i1, j1))
            i = i1
    return out
