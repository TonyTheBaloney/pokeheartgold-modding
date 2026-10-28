# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
"""What the Python tools compute, as JSON on stdout, for the Rust tests to compare
with (tools/mapeditor-rs/crates/*/tests). Usage: python3 oracle.py ROOT WHAT [ARGS]

    maps                    [[folder, MAP_*, id, ids.h path, layout folder]] for every map
    layouts                 {folder: {width, height, land, maps, altitudes}}
    land-index              {land number: [map folders]}
    mesh LAND               the triangles of a cell's model.nsbmd
    prop-mesh KIND N        the triangles of a prop model (KIND 0 room, 1 field)
    texture SET NAME PAL    a map texture's RGBA (hex), from data/area_textures
    nsbtx PATH NAME PAL     a texture's RGBA (hex) from an NSBTX file
    area ID                 [prop id, texture id, kind] from the area header
    heights LAND            the BDHC height (fx32 or null) at every tile centre of a cell, nearest to 0
"""

import json
import os
import struct
import sys

ROOT = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))
sys.path.insert(0, os.path.join(ROOT, "tools/mapeditor"))

from mapkit import areatex, edit, landdata, layouts, nitro  # noqa: E402
from mapkit.repo import Repo  # noqa: E402

# as tools/mapeditor/mapeditor/terrain.py (which needs Qt)
AREA_HEADERS = "files/a/0/4/2"
PROP_MODELS = {0: "files/a/1/4/8", 1: "files/a/0/4/0"}


def tris(models):
    out = []
    for m in models:
        for t in m.triangles():
            out.append({"pos": t.pos, "uv": t.uv, "color": t.color,
                        "material": t.material.name if t.material else None})
    return out


def main(what, *args):
    repo = Repo(ROOT)
    if what == "maps":
        out = []
        for m in repo.maps:
            d = repo.map_dir(m)
            if d is None:
                continue
            ids = os.path.relpath(edit._ids_path(repo, m), ROOT)
            out.append([os.path.basename(d), m.name, m.id, ids, repo.layout_folder(m)])
        return out
    if what == "layouts":
        out = {}
        for e in layouts.read_index(ROOT):
            m = layouts.load(ROOT, e["dir"])
            out[e["dir"]] = {"width": m.width, "height": m.height,
                             "land": [None if v == layouts.NO_CELL else v for v in m.land_ids],
                             "maps": list(m.header_ids), "altitudes": list(m.altitudes)}
        return out
    if what == "land-index":
        from mapeditor import project
        return {str(k): sorted(v) for k, v in project._land_index(repo).items()}
    if what == "mesh":
        with open(os.path.join(ROOT, "data/landdata/%04d/model.nsbmd" % int(args[0])), "rb") as f:
            return tris(nitro.load_nsbmd(f.read())[0])
    if what == "prop-mesh":
        with open(os.path.join(ROOT, PROP_MODELS[int(args[0])]), "rb") as f:
            data = landdata.narc_members(f.read())[int(args[1])]
        return tris(nitro.load_nsbmd(data)[0])
    if what == "texture":
        ts = areatex.texture_set(ROOT, int(args[0]))
        w, h, rgba = ts.image(args[1], args[2])
        return {"width": w, "height": h, "rgba": rgba.hex()}
    if what == "nsbtx":
        with open(os.path.join(ROOT, args[0]), "rb") as f:
            ts = nitro.load_nsbtx(f.read())
        w, h, rgba = ts.image(args[1], args[2] if args[2] != "-" else next(iter(ts.palettes), None))
        return {"width": w, "height": h, "rgba": bytes(rgba).hex()}
    if what == "area":
        with open(os.path.join(ROOT, AREA_HEADERS), "rb") as f:
            member = landdata.narc_members(f.read())[int(args[0])]
        prop_id, tex_id, _anim, kind, _light = struct.unpack("<HHHBB", member)
        return [prop_id, tex_id, kind]
    if what == "heights":
        from mapkit import bdhc
        with open(os.path.join(ROOT, "data/landdata/%04d/terrain.bdhc" % int(args[0])), "rb") as f:
            b = bdhc.Bdhc.from_bytes(f.read())
        at = lambda t: (t * 16 + 8 - 256) * bdhc.FX  # noqa: E731
        return [b.height(at(x), at(z), bdhc.NEAREST, 0) for z in range(32) for x in range(32)]
    raise SystemExit("unknown: %s" % what)


if __name__ == "__main__":
    json.dump(main(*sys.argv[2:]), sys.stdout)
