# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""The editor's data layer, without Qt: one open map, its layout cells, their
permissions and props, and its events. Edits change these objects; save()
writes map.json and the permissions.txt of every changed cell.

Coordinates are global tiles in the layout (map.json "x"/"y"), as in the game.
"""

import copy
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import edit, landdata, layouts  # noqa: E402
from mapkit.repo import Repo  # noqa: E402

CELL = landdata.SIZE          # tiles per layout cell side
PROP_UNITS_PER_TILE = 16      # MapPropArcData positions: 16 units per tile, cell centre at 0
EVENT_SECTIONS = ("object_events", "warp_events", "coord_events", "bg_events")

# Defaults for new events, pokeemerald key order
NEW_EVENT = {
    "object_events": {"local_id": "", "graphics_id": "SPRITE_GSMAN1", "x": 0, "y": 0, "elevation": 0,
                      "movement_type": "MOVEMENT_TYPE_FACE_DOWN", "movement_range_x": 0, "movement_range_y": 0,
                      "facing_dir": "DIR_SOUTH", "trainer_type": "OBJECT_TYPE_NORMAL", "trainer_sight_or_param0": 0,
                      "param1": 0, "param2": 0, "script": 0, "flag": "FLAG_NOTHING"},
    "warp_events": {"x": 0, "y": 0, "elevation": 0, "dest_map": "MAP_NOTHING", "dest_warp_id": 0},
    "coord_events": {"x": 0, "y": 0, "elevation": 0, "width": 1, "height": 1, "var": "VAR_TEMP_x4000",
                     "var_value": 0, "script": 0},
    "bg_events": {"type": "BG_TYPE_SIGNPOST", "x": 0, "y": 0, "elevation": 0, "player_facing_dir": "BG_DIR_ALL",
                  "script": 0},
}


class ProjectError(Exception):
    pass


def behavior_names(root=ROOT):
    """{value: name} from enum TILE_BEHAVIOR in include/constants/metatile_behavior.h."""
    with open(os.path.join(root, "include/constants/metatile_behavior.h"), encoding="utf-8") as f:
        text = f.read()
    body = re.search(r"enum\s+TILE_BEHAVIOR\s*\{(.*?)\};", text, re.S).group(1)
    out, v = {}, 0
    for item in body.split(","):
        item = re.sub(r"//.*", "", item).strip()
        if not item:
            continue
        m = re.fullmatch(r"(\w+)(?:\s*=\s*(\w+))?", item)
        if m.group(2):
            v = int(m.group(2), 0)
        out[v] = m.group(1)
        v += 1
    return out


class Chunk:
    """One land data cell: data/landdata/NNNN/."""

    def __init__(self, root, number):
        self.number = number
        self.dir = os.path.join(root, landdata.LANDDATA_DIR, "%04d" % number)
        self.permissions, self.props = landdata.load_chunk(self.dir)
        self.dirty = False

    def tile(self, tx, ty):
        i = ty * CELL + tx
        p = self.permissions
        return p.collision[i], p.behavior[i], p.attr[i]

    def set_tile(self, tx, ty, collision=None, behavior=None, attr=None):
        i = ty * CELL + tx
        p = self.permissions
        old = (p.collision[i], p.behavior[i], p.attr[i])
        if collision is not None:
            p.collision[i] = int(bool(collision))
        if behavior is not None:
            p.behavior[i] = behavior
        if attr is not None:
            p.attr[i] = attr
        if (p.collision[i], p.behavior[i], p.attr[i]) != old:
            self.dirty = True
        return old

    def save(self):
        if self.dirty:
            with open(os.path.join(self.dir, "permissions.txt"), "w", encoding="utf-8") as f:
                f.write(self.permissions.to_text())
            self.dirty = False


class MapDoc:
    """An open map: map.json, its layout and the land data of its cells."""

    def __init__(self, repo, query):
        self.repo = repo
        self.map = repo.find_map(query)
        if self.map is None:
            raise ProjectError("no map matches %r" % query)
        folder = repo.map_dir(self.map)
        if folder is None:
            raise ProjectError("%s is not in data/maps" % self.map.name)
        self.folder = os.path.basename(folder)
        self.map_json = os.path.join(folder, "map.json")
        self.data, self.style = edit.load_json(self.map_json)
        self.layout_name = repo.layout_folder(self.map)
        if self.layout_name is None:
            raise ProjectError("%s has no layout in data/layouts" % self.map.name)
        self.layout = layouts.load(repo.root, self.layout_name)
        self.chunks = {}
        self.dirty = False
        self._ids = None

    # --- layout ------------------------------------------------------------------

    @property
    def width(self):
        return self.layout.width

    @property
    def height(self):
        return self.layout.height

    def cell_land(self, cx, cy):
        v = self.layout.land_ids[cy * self.width + cx]
        return None if v == layouts.NO_CELL else v

    def cell_map(self, cx, cy):
        if not self.layout.header_ids:
            return self.map.id
        return self.layout.header_ids[cy * self.width + cx]

    def own_cells(self):
        """Cells this map's header covers (all of them in single-map layouts)."""
        return [(cx, cy) for cy in range(self.height) for cx in range(self.width)
                if self.cell_land(cx, cy) is not None and self.cell_map(cx, cy) == self.map.id]

    def bounds(self):
        """(x0, y0, x1, y1) in cells around own_cells, inclusive."""
        cells = self.own_cells() or [(cx, cy) for cy in range(self.height) for cx in range(self.width)]
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        return min(xs), min(ys), max(xs), max(ys)

    def chunk(self, cx, cy):
        n = self.cell_land(cx, cy)
        if n is None:
            return None
        if n not in self.chunks:
            self.chunks[n] = Chunk(self.repo.root, n)
        return self.chunks[n]

    def chunk_users(self, number):
        """Layout cells (in this layout) that use land data `number`: edits show in all of them."""
        return [(i % self.width, i // self.width) for i, v in enumerate(self.layout.land_ids) if v == number]

    def tile(self, x, y):
        """(collision, behavior, attr) at global tile x, y, or None outside the layout."""
        cx, cy = x // CELL, y // CELL
        if not (0 <= cx < self.width and 0 <= cy < self.height):
            return None
        c = self.chunk(cx, cy)
        return c.tile(x % CELL, y % CELL) if c else None

    def set_tile(self, x, y, **kw):
        c = self.chunk(x // CELL, y // CELL)
        if c is None:
            return None
        return c.set_tile(x % CELL, y % CELL, **kw)

    def props(self):
        """[(cx, cy, index, prop, tile_x, tile_y)] for the cells in bounds()."""
        x0, y0, x1, y1 = self.bounds()
        out = []
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                c = self.chunk(cx, cy)
                if c is None:
                    continue
                for i, p in enumerate(c.props):
                    tx = cx * CELL + CELL / 2 + p["position"][0] / PROP_UNITS_PER_TILE
                    ty = cy * CELL + CELL / 2 + p["position"][2] / PROP_UNITS_PER_TILE
                    out.append((cx, cy, i, p, tx, ty))
        return out

    # --- events -----------------------------------------------------------------

    def events(self, section):
        return self.data.setdefault(section, [])

    def set_event_field(self, section, index, key, value):
        ev = self.events(section)[index]
        old = ev.get(key)
        if old != value:
            ev[key] = value
            self.dirty = True
        return old

    def move_event(self, section, index, x, y):
        ev = self.events(section)[index]
        old = (ev["x"], ev["y"])
        if old != (x, y):
            ev["x"], ev["y"] = x, y
            self.dirty = True
        return old

    def add_event(self, section, x, y, template=None, index=None):
        ev = copy.deepcopy(template or NEW_EVENT[section])
        ev["x"], ev["y"] = x, y
        if section == "object_events" and not ev.get("local_id"):
            ev["local_id"] = self._new_local_id()
        lst = self.events(section)
        index = len(lst) if index is None else index
        lst.insert(index, ev)
        self.dirty = True
        return index

    def remove_event(self, section, index):
        ev = self.events(section).pop(index)
        self.dirty = True
        return ev

    def _new_local_id(self):
        used = {e.get("local_id") for e in self.events("object_events")}
        base = "obj_%s_new" % (self.data.get("code") or self.folder)
        n = 1
        while "%s%d" % (base, n) in used:
            n += 1
        return "%s%d" % (base, n)

    # --- header -------------------------------------------------------------------

    def header_fields(self):
        return [(k, v) for k, v in self.data.items() if k not in EVENT_SECTIONS]

    def set_header_field(self, key, value):
        old = self.data.get(key)
        if old != value:
            self.data[key] = value
            self.dirty = True
        return old

    # --- saving -----------------------------------------------------------------

    def modified(self):
        return self.dirty or any(c.dirty for c in self.chunks.values())

    def save(self):
        if self.dirty:
            edit.save_json(self.map_json, self.data, self.style)
            self.dirty = False
        for c in self.chunks.values():
            c.save()
        self.repo._cache.clear()


def open_repo(root=ROOT):
    return Repo(root)


def map_list(repo):
    """[(folder, MAP_* name, map id)] for every map in data/maps."""
    out = []
    for m in repo.maps:
        d = repo.map_dir(m)
        if d:
            out.append((os.path.basename(d), m.name, m.id))
    return sorted(out)


def constant_names(repo, prefix):
    return sorted(repo.defines.names(prefix))
