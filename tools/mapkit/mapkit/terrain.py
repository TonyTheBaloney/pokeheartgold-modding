# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Terrain cells as editable 3D files: export to OBJ, import from OBJ.

    mapkit terrain export 0383 out/      model.obj, model.mtl, textures/*.png, terrain.json
    mapkit terrain import 0383 out/model.obj
    mapkit terrain check 0383

Export writes the cell's model (and its heights, as an object named "heights")
with the textures of the area the cell is shown in. Import turns an OBJ back into
model.nsbmd (nsbmd.build_terrain) and, unless told otherwise, generates the
heights (bdhc.generate) into heights.json.

Textures stay in the area's map texture set (data/area_textures/NNN, built into NARC
a/0/4/4; areatex.py): a material names a texture and palette there, and the game binds
them by name when the map loads.
terrain.json records, per material, the texture, palette and drawing settings that
OBJ/MTL can't hold, so a model can go through Blender and come back unchanged.

Units: one OBJ unit = one model unit (a tile is 16) unless --scale says otherwise.
Axes are the game's: x east, y up, z south (OBJ's usual y-up).
"""

import json
import math
import os
import struct
import zlib

from . import areatex, bdhc, landdata, layouts, nitro, nsbmd

MANIFEST = "data/gen4map.json"


class TerrainError(Exception):
    pass


# --- where things are -----------------------------------------------------------------------

def manifest(root):
    with open(os.path.join(root, MANIFEST), encoding="utf-8") as f:
        return json.load(f)


def cell_dir(root, cell):
    return os.path.join(root, manifest(root)["paths"]["landdata"], "%04d" % int(cell))


class Area:
    """An area header (NARC a/0/4/2) and its map textures (a/0/4/4, from data/area_textures)."""

    _cache = {}

    def __init__(self, root, area_id):
        b = manifest(root)["binaries"]
        files = os.path.join(root, "files")   # this repository keeps the ROM file system under files/
        headers = self._narc(os.path.join(files, b["area_headers"]))
        if not 0 <= area_id < len(headers):
            raise TerrainError("no area %d (there are %d)" % (area_id, len(headers)))
        self.id = area_id
        (self.prop_id, self.texture_id, self.prop_anim, self.build_model_kind,
         self.light_kind) = struct.unpack("<HHHBB", headers[area_id])
        self.textures = areatex.texture_set(root, self.texture_id)   # data/area_textures

    @classmethod
    def _narc(cls, path):
        if path not in cls._cache:
            with open(path, "rb") as f:
                cls._cache[path] = landdata.narc_members(f.read())
        return cls._cache[path]


def areas_of_cell(root, cell):
    """{area id: [map folder]} for the maps whose area includes the cell."""
    paths = manifest(root)["paths"]
    maps_dir = os.path.join(root, paths["maps"])
    by_layout = {}
    for name in sorted(os.listdir(maps_dir)):
        p = os.path.join(maps_dir, name, "map.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                m = json.load(f)
            by_layout.setdefault(m["layout"], []).append((name, m["id"], m["area_data"]))
    by_name, _ = layouts.map_ids(root)
    out = {}
    for lay_name, users in by_layout.items():
        lay = layouts.load(root, lay_name)
        for i, land in enumerate(lay.land_ids):
            if land != int(cell):
                continue
            owner = lay.header_ids[i] if lay.header_ids else None   # layout.json "maps"
            for name, map_id, area in users:
                if owner is None or by_name.get(map_id) == owner:
                    out.setdefault(area, [])
                    if name not in out[area]:
                        out[area].append(name)
    return out


def pick_area(root, cell, area=None):
    if area is not None:
        return Area(root, int(area))
    found = areas_of_cell(root, cell)
    if not found:
        raise TerrainError("no map shows land data %04d; give --area" % int(cell))
    tex = {}
    for a in sorted(found):
        tex.setdefault(Area(root, a).texture_id, a)
    if len(tex) > 1:
        raise TerrainError("land data %04d is shown with different map textures (areas %s); give --area"
                           % (int(cell), ", ".join(str(a) for a in sorted(found))))
    return Area(root, min(found))


# --- PNG ----------------------------------------------------------------------------------------

def png_bytes(w, h, rgba):
    raw = b"".join(b"\0" + rgba[y * w * 4:(y + 1) * w * 4] for y in range(h))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# --- materials ------------------------------------------------------------------------------------

def _c5(v):
    return [v & 31, (v >> 5) & 31, (v >> 10) & 31]


def material_settings(mt):
    """nitro.Material -> the terrain.json entry."""
    return {
        "texture": mt.texture, "palette": mt.palette,
        "lit": bool(mt.poly_attr & 0xF), "alpha": mt.alpha,
        "cull": {2: "back", 1: "front", 3: "none", 0: "none"}[(mt.poly_attr >> 6) & 3],
        "fog": bool(mt.poly_attr & 0x8000),
        "repeat": list(mt.repeat), "flip": list(mt.flip),
        "diffuse": _c5(mt.diff_amb), "ambient": _c5(mt.diff_amb >> 16),
    }


SETTING_KEYS = {"texture", "palette", "lit", "alpha", "cull", "fog", "repeat", "flip", "diffuse", "ambient"}


def terrain_material(name, settings, area, where):
    extra = set(settings) - SETTING_KEYS
    if extra:
        raise TerrainError("%s: material %s: unknown key %s" % (where, name, sorted(extra)[0]))
    tex, pal = settings.get("texture"), settings.get("palette")
    size = (0, 0)
    if tex:
        t = area.textures.textures.get(tex)
        if t is None:
            raise TerrainError("%s: material %s: area %d's map textures have no texture %r"
                               % (where, name, area.id, tex))
        if pal is None or pal not in area.textures.palettes:
            if t.format == 7:
                pal = None
            else:
                raise TerrainError("%s: material %s: area %d's map textures have no palette %r"
                                   % (where, name, area.id, pal))
        size = (t.width, t.height)
    return nsbmd.TerrainMaterial(
        name, tex, pal, size, bool(settings.get("lit", True)), int(settings.get("alpha", 31)),
        settings.get("cull", "back"), bool(settings.get("fog", True)),
        tuple(settings.get("repeat", (True, True))), tuple(settings.get("flip", (False, False))),
        tuple(settings.get("diffuse", (25, 25, 25))), tuple(settings.get("ambient", (31, 31, 31))))


# --- export -----------------------------------------------------------------------------------------

def _f(v):
    s = "%.6f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def export(root, cell, out_dir, area=None, scale=1.0):
    d = cell_dir(root, cell)
    ar = pick_area(root, cell, area)
    with open(os.path.join(d, "model.nsbmd"), "rb") as f:
        (model,), _ = nitro.load_nsbmd(f.read())
    heights = _load_heights(d)
    os.makedirs(os.path.join(out_dir, "textures"), exist_ok=True)

    mats = {}
    for mt in model.materials:
        mats[mt.name] = material_settings(mt)
    images = {}
    for mt in model.materials:
        if mt.texture and (mt.texture, mt.palette) not in images:
            img = ar.textures.image(mt.texture, mt.palette)
            if img is None:
                continue
            w, h, rgba = img
            fn = "%s-%s.png" % (mt.texture, mt.palette) if mt.palette else "%s.png" % mt.texture
            with open(os.path.join(out_dir, "textures", fn), "wb") as f:
                f.write(png_bytes(w, h, rgba))
            images[(mt.texture, mt.palette)] = (fn, w, h)

    vs, vts, vns = {}, {}, {}
    vlines, vtlines, vnlines, flines = [], [], [], []

    def idx(table, lines, key, text):
        if key not in table:
            table[key] = len(table) + 1
            lines.append(text)
        return table[key]

    flines.append("o terrain")
    by_mat = {}
    for p in model.polygons():
        by_mat.setdefault(p.material.name, []).append(p)
    for mt in model.materials:
        polys = by_mat.get(mt.name)
        if not polys:
            continue
        flines.append("usemtl %s" % mt.name)
        lit = bool(mt.poly_attr & 0xF)
        im = images.get((mt.texture, mt.palette))
        for p in polys:
            refs = []
            for k in range(len(p.pos)):
                x, y, z = (c / scale for c in p.pos[k])
                if lit and p.normal[k] is not None:
                    vi = idx(vs, vlines, (x, y, z), "v %s %s %s" % (_f(x), _f(y), _f(z)))
                else:
                    r, g, b = (c / 255 for c in p.color[k])
                    vi = idx(vs, vlines, (x, y, z, r, g, b), "v %s %s %s %s %s %s"
                             % (_f(x), _f(y), _f(z), _f(r), _f(g), _f(b)))
                ref = str(vi)
                if im:
                    u, v = p.uv[k][0] / im[1], 1.0 - p.uv[k][1] / im[2]
                    ref += "/%d" % idx(vts, vtlines, (u, v), "vt %s %s" % (_f(u), _f(v)))
                elif lit and p.normal[k] is not None:
                    ref += "/"
                if lit and p.normal[k] is not None:
                    n = p.normal[k]
                    ref += "/%d" % idx(vns, vnlines, n, "vn %s %s %s" % tuple(_f(c) for c in n))
                refs.append(ref)
            flines.append("f " + " ".join(refs))

    if heights is not None:
        flines.append("o heights")
        flines.append("usemtl heights")
        for pl in heights.resolved_plates():
            if pl.normal[1] == 0:
                continue
            nx, ny, nz = (c / bdhc.FX for c in pl.normal)
            dd = pl.d / bdhc.FX
            refs = []
            for x, z in ((pl.x0, pl.z0), (pl.x0, pl.z1), (pl.x1, pl.z1), (pl.x1, pl.z0)):
                x, z = x / bdhc.FX, z / bdhc.FX
                y = -(dd + nx * x + nz * z) / ny
                refs.append(str(idx(vs, vlines, (x / scale, y / scale, z / scale, "h"),
                                    "v %s %s %s" % (_f(x / scale), _f(y / scale), _f(z / scale)))))
            flines.append("f " + " ".join(refs))

    with open(os.path.join(out_dir, "model.obj"), "w", encoding="utf-8") as f:
        f.write("# land data %04d, area %d (map textures %d); exported by mapkit terrain export\n"
                % (int(cell), ar.id, ar.texture_id))
        f.write("# units: %s model units per OBJ unit (16 = one tile); x east, y up, z south\n" % _f(scale))
        f.write("mtllib model.mtl\n")
        f.write("\n".join(vlines + vtlines + vnlines + flines) + "\n")
    with open(os.path.join(out_dir, "model.mtl"), "w", encoding="utf-8") as f:
        for mt in model.materials:
            f.write("newmtl %s\nKd 1 1 1\nd %s\n" % (mt.name, _f(mt.alpha / 31)))
            im = images.get((mt.texture, mt.palette))
            if im:
                f.write("map_Kd textures/%s\n" % im[0])
            f.write("\n")
        f.write("newmtl heights\nKd 1 0 1\nd 0.5\n")
    side = {"cell": int(cell), "area": ar.id, "scale": scale, "model_name": model.name, "materials": mats}
    with open(os.path.join(out_dir, "terrain.json"), "w", encoding="utf-8") as f:
        json.dump(side, f, indent=4)
        f.write("\n")
    return {"area": ar.id, "materials": len(model.materials), "textures": len(images),
            "plates": len(heights.plates) if heights else 0}


def _load_heights(d):
    hj, hb = os.path.join(d, "heights.json"), os.path.join(d, "terrain.bdhc")
    if os.path.exists(hj):
        return bdhc.read_json(hj)
    if os.path.exists(hb):
        with open(hb, "rb") as f:
            return bdhc.Bdhc.from_bytes(f.read())
    return None


# --- OBJ reading -------------------------------------------------------------------------------------

class Obj:
    def __init__(self):
        self.v, self.vt, self.vn = [], [], []
        self.faces = []        # (object, material, [(v, vt, vn) indices, 0-based or None])
        self.mtllibs = []


def read_obj(path):
    o = Obj()
    obj, mat = "", None
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            parts = line.split("#", 1)[0].split()
            if not parts:
                continue
            k = parts[0]
            try:
                if k == "v":
                    vals = [float(x) for x in parts[1:]]
                    o.v.append((tuple(vals[:3]), tuple(vals[3:6]) if len(vals) >= 6 else None))
                elif k == "vt":
                    o.vt.append(tuple(float(x) for x in parts[1:3]))
                elif k == "vn":
                    o.vn.append(tuple(float(x) for x in parts[1:4]))
                elif k in ("o", "g"):
                    obj = " ".join(parts[1:])
                elif k == "usemtl":
                    mat = " ".join(parts[1:])
                elif k == "mtllib":
                    o.mtllibs.append(" ".join(parts[1:]))
                elif k == "f":
                    refs = []
                    for r in parts[1:]:
                        bits = (r.split("/") + ["", ""])[:3]
                        ids = []
                        for b, table in zip(bits, (o.v, o.vt, o.vn)):
                            if b == "":
                                ids.append(None)
                            else:
                                i = int(b)
                                ids.append(i - 1 if i > 0 else len(table) + i)
                        refs.append(tuple(ids))
                    o.faces.append((obj, mat, refs))
            except ValueError:
                raise TerrainError("%s:%d: can't read %r" % (path, n, line.strip()))
    return o


def read_mtl(path):
    """{material: {"map_Kd": path, "d": alpha}}"""
    out, cur = {}, None
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split("#", 1)[0].split()
            if not parts:
                continue
            if parts[0] == "newmtl":
                cur = out.setdefault(" ".join(parts[1:]), {})
            elif cur is not None and parts[0] == "map_Kd":
                cur["map_Kd"] = parts[-1]
            elif cur is not None and parts[0] == "d":
                cur["d"] = float(parts[1])
    return out


def _is_heights(name):
    n = name.lower()
    return n.startswith("heights") or n.startswith("collision")


def _convex_planar(pts):
    """Is the quad convex (every corner turns the same way)? The hardware draws quads that
    are a little out of flat (retail models have them), but not concave ones."""
    def sub(a, b):
        return tuple(a[i] - b[i] for i in range(3))

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    ns = [cross(sub(pts[(i + 1) % 4], pts[i]), sub(pts[(i + 2) % 4], pts[(i + 1) % 4])) for i in range(4)]
    ref = ns[0]
    lr = math.sqrt(sum(c * c for c in ref))
    if lr == 0:
        return False
    for n in ns[1:]:
        ln = math.sqrt(sum(c * c for c in n))
        if ln == 0 or sum(a * b for a, b in zip(ref, n)) / (lr * ln) <= 0.5:
            return False
    return True


# --- import ------------------------------------------------------------------------------------------

def import_obj(root, cell, obj_path, area=None, heights="auto", scale=None, grid=8.0, dry_run=False,
               walkable_only=False):
    """OBJ -> model.nsbmd (and heights.json). Returns a summary dict."""
    d = cell_dir(root, cell)
    base = os.path.dirname(os.path.abspath(obj_path))
    side_path = os.path.join(base, "terrain.json")
    side = {}
    if os.path.exists(side_path):
        with open(side_path, encoding="utf-8") as f:
            side = json.load(f)
    if area is None and "area" in side:
        area = side["area"]
    if scale is None:
        scale = float(side.get("scale", 1.0))
    ar = pick_area(root, cell, area)
    o = read_obj(obj_path)
    mtl = {}
    for lib in o.mtllibs:
        mtl.update(read_mtl(os.path.join(base, lib)))

    materials, mat_index, warnings = [], {}, []
    tex_by_file = {}
    for (t, p), _ in {(mt.get("texture"), mt.get("palette")): 1 for mt in side.get("materials", {}).values()}.items():
        if t:
            tex_by_file[("%s-%s.png" % (t, p)) if p else "%s.png" % t] = (t, p)

    def material(name):
        if name in mat_index:
            return mat_index[name]
        settings = dict(side.get("materials", {}).get(name, {}))
        if not settings:
            m = mtl.get(name, {})
            fn = os.path.basename(m.get("map_Kd", "")) if m.get("map_Kd") else ""
            if fn:
                if fn in tex_by_file:
                    settings["texture"], settings["palette"] = tex_by_file[fn]
                else:
                    stem = os.path.splitext(fn)[0]
                    tex, _, pal = stem.partition("-")
                    if not pal:
                        pal = next((pn for pn in (tex + "_pl", tex) if pn in ar.textures.palettes), None)
                    settings["texture"], settings["palette"] = tex, pal
            if "d" in m:
                settings["alpha"] = max(0, min(31, int(round(m["d"] * 31))))
            settings["lit"] = None   # decided from the faces: normals -> lit
        mat_index[name] = len(materials)
        materials.append([name, settings])
        return mat_index[name]

    polys, height_tris, height_rects = [], [], []
    for obj, mat, refs in o.faces:
        if len(refs) < 3:
            continue
        pts = [tuple(c * scale for c in o.v[r[0]][0]) for r in refs]
        if _is_heights(obj):
            rect = _rect_plate(pts)
            if rect is not None:
                height_rects.append(rect)
            else:
                for i in range(1, len(pts) - 1):
                    height_tris.append((pts[0], pts[i], pts[i + 1]))
            continue
        if mat is None:
            raise TerrainError("%s: faces without a material (usemtl)" % obj_path)
        mi = material(mat)
        verts = []
        for r, p in zip(refs, pts):
            uv = o.vt[r[1]] if r[1] is not None else None
            nrm = o.vn[r[2]] if r[2] is not None else None
            col = o.v[r[0]][1]
            verts.append([p, uv, nrm, tuple(int(round(c * 255)) for c in col) if col else None])
        if len(verts) == 4 and not _convex_planar(pts):
            polys.append((mi, [verts[0], verts[1], verts[2]]))
            polys.append((mi, [verts[0], verts[2], verts[3]]))
        elif len(verts) > 4:
            for i in range(1, len(verts) - 1):
                polys.append((mi, [verts[0], verts[i], verts[i + 1]]))
        else:
            polys.append((mi, verts))

    # settle materials
    tms = []
    for i, (name, settings) in enumerate(materials):
        if settings.get("lit") is None:
            has_n = any(v[2] is not None for mi, vs in polys if mi == i for v in vs)
            settings["lit"] = has_n
        tms.append(terrain_material(name, settings, ar, obj_path))

    # texture coordinates: OBJ (0..1, v up) -> texels (t down). The hardware stores them in
    # +-2048 texels; a polygon beyond that is moved by whole periods where the texture repeats.
    out = []
    for mi, verts in polys:
        tm = tms[mi]
        vs = []
        w, h = tm.tex_size
        st = []
        for p, uv, nrm, col in verts:
            if tm.texture:
                u, v = uv if uv else (0.0, 0.0)
                st.append([u * w, (1.0 - v) * h])
            else:
                st.append(None)
        if tm.texture:
            for axis, size in ((0, w), (1, h)):
                if tm.repeat[axis] and size and any(not -2047 <= s[axis] <= 2047 for s in st):
                    period = size * (2 if tm.flip[axis] else 1)
                    shift = math.floor(min(s[axis] for s in st) / period) * period
                    for s in st:
                        s[axis] -= shift
        for (p, uv, nrm, col), s in zip(verts, st):
            if tm.lit and nrm is None:
                nrm = _face_normal([v[0] for v in verts])
            vs.append((p, tuple(s) if s else None, nrm, col))
        out.append((mi, vs))

    name = side.get("model_name") or "land%04d" % int(cell)
    data = nsbmd.build_terrain(name[:16], tms, out)

    summary = {"area": ar.id, "model_bytes": len(data), "model_limit": nsbmd.MAX_MODEL_SIZE,
               "polygons": len(out), "materials": len(tms), "warnings": warnings}
    new_heights = None
    if heights == "auto":
        if height_tris or height_rects:
            plates = height_rects + (bdhc.generate(height_tris, grid=grid) if height_tris else [])
            summary["heights_from"] = "the heights object (%d rectangles as they are, %d other faces sampled)" % (
                len(height_rects), len(height_tris))
        else:
            walk = _walkable(d) if walkable_only else None
            tris = [tuple(v[0] for v in t) for mi, vs in out
                    for t in ([vs] if len(vs) == 3 else [[vs[0], vs[1], vs[2]], [vs[0], vs[2], vs[3]]])]
            plates = bdhc.generate(tris, grid=grid, walkable=walk)
            summary["heights_from"] = "the model's upward faces" + (" over walkable tiles" if walk else "")
        new_heights = bdhc.build(plates)
        summary["plates"] = len(new_heights.plates)
        warnings += bdhc.check(new_heights, "heights")
    summary["model_data"], summary["heights_data"] = data, new_heights
    if not dry_run:
        with open(os.path.join(d, "model.nsbmd"), "wb") as f:
            f.write(data)
        if new_heights is not None:
            bdhc.write_json(os.path.join(d, "heights.json"), new_heights)
            old = os.path.join(d, "terrain.bdhc")
            if os.path.exists(old):
                os.remove(old)
    return summary


def _rect_plate(pts):
    """A face of the heights object that is a rectangle along x and z -> its Plate, else None."""
    if len(pts) != 4:
        return None
    xs = sorted({round(p[0], 4) for p in pts})
    zs = sorted({round(p[2], 4) for p in pts})
    if len(xs) != 2 or len(zs) != 2 or {(round(p[0], 4), round(p[2], 4)) for p in pts} != {
            (x, z) for x in xs for z in zs}:
        return None
    y = {(round(p[0], 4), round(p[2], 4)): p[1] for p in pts}
    y00, y10, y01, y11 = y[(xs[0], zs[0])], y[(xs[1], zs[0])], y[(xs[0], zs[1])], y[(xs[1], zs[1])]
    gx = (y10 - y00) / (xs[1] - xs[0])          # dy/dx
    gz = (y01 - y00) / (zs[1] - zs[0])          # dy/dz
    if abs((y00 + gx * (xs[1] - xs[0]) + gz * (zs[1] - zs[0])) - y11) > 0.05:
        return None                             # not flat: sample it instead
    ln = math.sqrt(gx * gx + gz * gz + 1.0)
    n = (-gx / ln, 1.0 / ln, -gz / ln)
    nfx = bdhc.UP if (gx == 0 and gz == 0) else tuple(bdhc.to_fx(c) for c in n)
    # d from the stored (rounded) normal, so the plane passes through the corner's height
    d = -(nfx[0] * xs[0] + nfx[1] * y00 + nfx[2] * zs[0])
    return bdhc.Plate(bdhc.to_fx(xs[0]), bdhc.to_fx(zs[0]), bdhc.to_fx(xs[1]), bdhc.to_fx(zs[1]), nfx, int(round(d)))


def _face_normal(pts):
    a, b, c = pts[0], pts[1], pts[2]
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    ln = math.sqrt(sum(x * x for x in n)) or 1.0
    return tuple(x / ln for x in n)


def _walkable(d):
    p = os.path.join(d, "permissions.txt")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        words = landdata.Permissions.from_text(f.read(), p).words()
    return [[not (w & 0x8000) for w in words[r * 32:(r + 1) * 32]] for r in range(32)]


# --- check --------------------------------------------------------------------------------------------

def check(root, cell):
    """Problems the game would have with a cell's model and heights, as messages."""
    d = cell_dir(root, cell)
    out = []
    with open(os.path.join(d, "model.nsbmd"), "rb") as f:
        data = f.read()
    if len(data) > nsbmd.MAX_MODEL_SIZE:
        out.append("model.nsbmd is 0x%X bytes; the game reads at most 0x%X" % (len(data), nsbmd.MAX_MODEL_SIZE))
    try:
        models = nsbmd.read(data)
        if len(models) != 1:
            out.append("model.nsbmd has %d models; the game uses exactly one" % len(models))
        (model,), _ = nitro.load_nsbmd(data)
    except nitro.NitroError as e:
        return out + ["model.nsbmd: %s" % e]
    for a, users in sorted(areas_of_cell(root, cell).items()):
        tex = Area(root, a).textures
        for mt in model.materials:
            if mt.texture and mt.texture not in tex.textures:
                out.append("material %s: texture %r is not in area %d's map textures (maps %s)"
                           % (mt.name, mt.texture, a, ", ".join(users[:3])))
            elif mt.palette and mt.palette not in tex.palettes:
                out.append("material %s: palette %r is not in area %d's map textures" % (mt.name, mt.palette, a))
    hj, hb = os.path.exists(os.path.join(d, "heights.json")), os.path.exists(os.path.join(d, "terrain.bdhc"))
    if hj and hb:
        out.append("both heights.json and terrain.bdhc exist; keep one")
    try:
        h = _load_heights(d)
    except bdhc.BdhcError as e:
        return out + [str(e)]
    if h is None:
        out.append("no heights (heights.json or terrain.bdhc)")
    else:
        out += bdhc.check(h, "heights.json" if hj else "terrain.bdhc")
    return out
