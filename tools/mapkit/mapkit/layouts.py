# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Map layouts (map matrices), in the style of pokeemerald's data/layouts.

A layout is the grid of 32x32-tile cells a map is made of. Each cell names a
land data chunk (data/landdata/NNNN/, see landdata.py) and, in outdoor layouts,
the map header that applies there and an altitude.

    data/layouts/layouts.txt         <Folder> <original matrix base name>, in NARC order
    data/layouts/<Folder>/layout.json

layout.json:

    {
        "name": "m_dun0101_",                 the name stored in the matrix
        "width": 2, "height": 3,
        "land_data": [[12, 13], ...],         one row per line; null = no cell
        "maps": [["MAP_X", ...], ...],        only if the matrix has per-cell headers
        "altitudes": [[0, 2], ...]            only if it has altitudes
    }

map.json's "layout" is the folder name. The build writes each layout back to
files/fielddata/mapmatrix/map_matrix/<base>.bin, so .naix names are unchanged.
"""

import json
import os
import re

from .matrix import Matrix

LAYOUTS_DIR = "data/layouts"
INDEX = "data/layouts/layouts.txt"
NO_CELL = 0xFFFF
_MAP_RE = re.compile(r"^#define\s+(MAP_\w+)\s+(\d+)", re.M)


class LayoutError(Exception):
    pass


def read_index(root):
    out = []
    path = os.path.join(root, INDEX)
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                folder, base = line.split()
                out.append({"dir": folder, "base": base})
    return out


def write_index(root, entries):
    with open(os.path.join(root, INDEX), "w", encoding="utf-8") as f:
        f.write("# Layouts in data/layouts/<Folder>/ (tools/mapkit/mapkit/layouts.py), in map_matrix NARC order.\n")
        f.write("# <Folder> <original matrix file base name, which the .naix constant comes from>\n")
        for e in entries:
            f.write("%s %s\n" % (e["dir"], e["base"]))


def naix_name(base):
    return "NARC_map_matrix_%s_bin" % base


def map_ids(root):
    with open(os.path.join(root, "include/constants/maps.h"), encoding="utf-8") as f:
        by_name = {n: int(v) for n, v in _MAP_RE.findall(f.read())}
    by_id = {}
    for n, v in by_name.items():
        by_id.setdefault(v, n)
    return by_name, by_id


def _grid(values, width):
    return [values[i:i + width] for i in range(0, len(values), width)]


def to_json(m, root):
    _, by_id = map_ids(root)
    d = {"name": m.name, "width": m.width, "height": m.height,
         "land_data": _grid([None if v == NO_CELL else v for v in m.land_ids], m.width)}
    if m.header_ids:
        d["maps"] = _grid([by_id.get(v, v) for v in m.header_ids], m.width)
    if m.altitudes:
        d["altitudes"] = _grid(m.altitudes, m.width)
    return d


def write_json(path, d):
    """One grid row per line, so diffs show the cells that changed."""
    lines = ["{", '    "name": %s,' % json.dumps(d["name"]), '    "width": %d,' % d["width"],
             '    "height": %d,' % d["height"]]
    grids = [k for k in ("land_data", "maps", "altitudes") if k in d]
    for gi, key in enumerate(grids):
        rows = d[key]
        lines.append('    "%s": [' % key)
        for i, row in enumerate(rows):
            lines.append("        %s%s" % (json.dumps(row), "," if i < len(rows) - 1 else ""))
        lines.append("    ]%s" % ("," if gi < len(grids) - 1 else ""))
    lines.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def from_json(d, root, where="layout.json"):
    by_name, _ = map_ids(root)
    if not isinstance(d, dict):
        raise LayoutError("%s: expected an object" % where)
    unknown = set(d) - {"name", "width", "height", "land_data", "maps", "altitudes"}
    if unknown:
        raise LayoutError("%s: unknown key %s" % (where, ", ".join(sorted(unknown))))
    w, h = d.get("width"), d.get("height")
    if not all(isinstance(v, int) and 1 <= v <= 255 for v in (w, h)):
        raise LayoutError("%s: width and height must be 1-255" % where)
    name = d.get("name", "")
    if not isinstance(name, str) or not name.isascii() or len(name) > 255:
        raise LayoutError("%s: name must be ASCII, at most 255 characters" % where)

    def cells(key, conv):
        rows = d[key]
        if not isinstance(rows, list) or len(rows) != h or any(not isinstance(r, list) or len(r) != w for r in rows):
            raise LayoutError("%s: %s must be %d rows of %d" % (where, key, h, w))
        return [conv(v, "%s: %s[%d][%d]" % (where, key, i // w, i % w))
                for i, v in enumerate(v for r in rows for v in r)]

    def land(v, at):
        if v is None:
            return NO_CELL
        if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < NO_CELL:
            raise LayoutError("%s: %r is not a land data number or null" % (at, v))
        return v

    def map_id(v, at):
        if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 0xFFFF:
            return v
        if v not in by_name:
            raise LayoutError("%s: unknown map %r" % (at, v))
        return by_name[v]

    def alt(v, at):
        if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255:
            raise LayoutError("%s: altitude %r is not 0-255" % (at, v))
        return v

    if "land_data" not in d:
        raise LayoutError("%s: missing land_data" % where)
    return Matrix(w, h, name,
                  cells("maps", map_id) if "maps" in d else [],
                  cells("altitudes", alt) if "altitudes" in d else [],
                  cells("land_data", land))


def load(root, folder):
    path = os.path.join(root, LAYOUTS_DIR, folder, "layout.json")
    with open(path, encoding="utf-8") as f:
        try:
            d = json.load(f)
        except json.JSONDecodeError as e:
            raise LayoutError("%s:%d: %s" % (path, e.lineno, e.msg))
    return from_json(d, root, os.path.relpath(path, root))


def save(root, folder, m):
    d = os.path.join(root, LAYOUTS_DIR, folder)
    os.makedirs(d, exist_ok=True)
    write_json(os.path.join(d, "layout.json"), to_json(m, root))


def folder_for_base(root, base):
    for e in read_index(root):
        if e["base"] == base:
            return e["dir"]
    return None


def base_for_folder(root, folder):
    for e in read_index(root):
        if e["dir"] == folder:
            return e["base"]
    raise LayoutError("layout %r is not listed in %s" % (folder, INDEX))


def gen_matrix(root, layout_json, out_path):
    """Build step: layout.json -> the matrix .bin it came from."""
    folder = os.path.basename(os.path.dirname(os.path.abspath(layout_json)))
    with open(out_path, "wb") as f:
        f.write(load(root, folder).to_bytes())


# --- migration and packing -------------------------------------------------------------

MATRIX_DIR = "files/fielddata/mapmatrix/map_matrix"
OVERWORLD_BASE = "map_matrix_0000_EVERYWHERE"


def plan_folders(root, users):
    """{matrix base: layout folder}. users: {base: [map folders using it]}.

    pokeemerald names a layout after its map; shared layouts take the first map's
    name, the big outdoor matrix is Overworld, unused ones Unused_NNNN."""
    bases = sorted(os.path.splitext(n)[0] for n in os.listdir(os.path.join(root, MATRIX_DIR)) if n.endswith(".bin"))
    out = {}
    for base in bases:
        if base == OVERWORLD_BASE:
            out[base] = "Overworld"
        elif users.get(base):
            out[base] = sorted(users[base])[0]
        else:
            out[base] = "Unused_%s" % base.split("_")[2]
    if len(set(out.values())) != len(out):
        raise LayoutError("layout folder names collide")
    return out


def migrate(root):
    """files/fielddata/mapmatrix/map_matrix/*.bin -> data/layouts; map.json "layout" -> folder."""
    from . import layout as maps_layout, matrix as matrix_mod
    entries = maps_layout.read_index(root)
    map_json = {e["dir"]: os.path.join(root, maps_layout.MAPS_DIR, e["dir"], "map.json") for e in entries}
    users = {}
    for folder, path in map_json.items():
        with open(path, encoding="utf-8") as f:
            v = json.load(f)["layout"]
        m = re.fullmatch(r"NARC_map_matrix_(\w+)_bin", v)
        if not m:
            raise LayoutError("%s: layout %r is not a matrix constant" % (path, v))
        users.setdefault(m.group(1), []).append(folder)
    folders = plan_folders(root, users)
    index = []
    for base, folder in folders.items():
        src = os.path.join(root, MATRIX_DIR, base + ".bin")
        with open(src, "rb") as f:
            data = f.read()
        mx = matrix_mod.parse(data)
        save(root, folder, mx)
        if load(root, folder).to_bytes() != data:
            raise LayoutError("%s does not round-trip" % src)
        index.append({"dir": folder, "base": base})
    write_index(root, index)
    for base, maps in users.items():
        for folder in maps:
            path = map_json[folder]
            with open(path, encoding="utf-8") as f:
                text = f.read()
            new = text.replace('"layout": "%s"' % naix_name(base), '"layout": "%s"' % folders[base], 1)
            if new == text:
                raise LayoutError("%s: no layout line to update" % path)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new)
    for base in folders:
        os.remove(os.path.join(root, MATRIX_DIR, base + ".bin"))
    return index


def pack(root, out_narc, nitroarc, work):
    """Build step: every layout -> <base>.bin in work/, then nitroarc -> map_matrix.narc/.naix."""
    import shutil
    import subprocess
    d = os.path.join(work, "map_matrix")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for e in read_index(root):
        with open(os.path.join(d, e["base"] + ".bin"), "wb") as f:
            f.write(load(root, e["dir"]).to_bytes())
    subprocess.run([os.path.abspath(nitroarc), "--create", "--index-namespace", "--file",
                    os.path.abspath(out_narc), d], check=True)


def rename(root, old, new):
    """Rename a layout folder and every map.json "layout" that names it. ROM unchanged."""
    from . import layout as maps_layout
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", new):
        raise LayoutError("%r is not a valid folder name" % new)
    index = read_index(root)
    if not any(e["dir"] == old for e in index):
        raise LayoutError("no layout %r" % old)
    if any(e["dir"] == new for e in index):
        raise LayoutError("layout %r already exists" % new)
    os.rename(os.path.join(root, LAYOUTS_DIR, old), os.path.join(root, LAYOUTS_DIR, new))
    for e in index:
        if e["dir"] == old:
            e["dir"] = new
    write_index(root, index)
    changed = []
    for e in maps_layout.read_index(root):
        path = os.path.join(root, maps_layout.MAPS_DIR, e["dir"], "map.json")
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        new_text = text.replace('"layout": "%s"' % old, '"layout": "%s"' % new)
        if new_text != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_text)
            changed.append(e["dir"])
    return changed
