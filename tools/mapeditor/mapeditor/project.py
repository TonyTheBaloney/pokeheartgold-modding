# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""The editor's data layer, without Qt: one open map, its layout cells, their
permissions and props, and its events. Edits change these objects; save()
writes map.json and the permissions.txt of every changed cell.

Coordinates are global tiles in the layout (map.json "x"/"y"), as in the game.
"""

import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import bdhc, edit, landdata, layouts, terrain  # noqa: E402
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


# Constants that are C enum members, not #defines: prefix -> header with the enum
ENUM_SOURCES = {"MAP_TYPE_": "include/map_header.h", "BATTLE_BG_": "include/constants/battle.h"}


class ProjectError(Exception):
    pass


class ChangedOnDisk(ProjectError):
    """save() found files changed by something else since the map was opened."""

    def __init__(self, paths):
        super().__init__("changed outside the editor: " + ", ".join(paths))
        self.paths = paths


def _mtime(path):
    try:
        return os.stat(path).st_mtime_ns
    except FileNotFoundError:
        return None


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
        self.path = os.path.join(self.dir, "permissions.txt")
        self.mtime = _mtime(self.path)
        self.dirty = False
        self._heights = False   # not read yet

    @property
    def heights(self):
        """The cell's heights (mapkit.bdhc.Bdhc), or None if it has none."""
        if self._heights is False:
            try:
                self._heights = terrain._load_heights(self.dir)
            except (OSError, ValueError, bdhc.BdhcError):
                self._heights = None
        return self._heights

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
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(self.permissions.to_text())
            self.mtime = _mtime(self.path)
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
        self.map_json_mtime = _mtime(self.map_json)
        self.layout_name = repo.layout_folder(self.map)
        if self.layout_name is None:
            raise ProjectError("%s has no layout in data/layouts" % self.map.name)
        self.layout = layouts.load(repo.root, self.layout_name)
        self.chunks = {}
        self.dirty = False
        self._land_index = None
        self._editable = None

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

    def editable_cells(self):
        """Cells whose tiles and events belong to this map: own_cells, or every cell when
        the map's header covers none (a layout without a maps grid naming it)."""
        if self._editable is None:  # the layout doesn't change while the map is open
            own = self.own_cells()
            self._editable = frozenset(own or ((cx, cy) for cy in range(self.height) for cx in range(self.width)
                                               if self.cell_land(cx, cy) is not None))
        return self._editable

    def on_map(self, x, y):
        """True if global tile x, y is in one of editable_cells()."""
        return (x // CELL, y // CELL) in self.editable_cells() if x >= 0 and y >= 0 else False

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

    def area_for_cell(self, cx, cy):
        """Area data id to draw a cell with. The game loads one area at a time, the
        current map's (src/field/area_data.c), and draws every visible cell with it."""
        return int(self.data.get("area_data", 0))

    def cell_altitude(self, cx, cy):
        return self.layout.altitudes[cy * self.width + cx] if self.layout.altitudes else 0

    def land_users(self, number):
        """Folders of every map that shows land data `number`, across all layouts: an edit
        to it changes all of them."""
        if self._land_index is None:
            self._land_index = _land_index(self.repo)
        return sorted(self._land_index.get(number, ()))

    def ground(self, x, y, elevation=0):
        """World height (model units) an object standing on global tile x, y is drawn at:
        the cell's heights at the tile's centre, nearest `elevation` (map.json's, fx32) where
        plates overlap, as src/field_terrain.c finds it. The cell's altitude when it has
        no height there."""
        cx, cy = x // CELL, y // CELL
        c = self.chunk(cx, cy) if 0 <= cx < self.width and 0 <= cy < self.height else None
        if c is None:
            return 0.0
        h = c.heights.height(((x % CELL) * 16 + 8 - 256) * bdhc.FX, ((y % CELL) * 16 + 8 - 256) * bdhc.FX,
                             bdhc.NEAREST, int(elevation or 0)) if c.heights else None
        return h / bdhc.FX if h is not None else self.cell_altitude(cx, cy) * 8.0

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
        """The section's events; a map without the section reads as empty and keeps not
        having it (adding an event creates it)."""
        return self.data.get(section, [])

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
        lst = self.data.setdefault(section, [])
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

    def changed_on_disk(self):
        """Files this save would write that something else changed since they were read."""
        out = []
        if self.dirty and _mtime(self.map_json) != self.map_json_mtime:
            out.append(os.path.relpath(self.map_json, self.repo.root))
        out += [os.path.relpath(c.path, self.repo.root) for c in self.chunks.values()
                if c.dirty and _mtime(c.path) != c.mtime]
        return out

    def missing_object_ids(self):
        """local_ids of objects that ids.h doesn't define (objects added in the editor)."""
        defs = self.repo.event_defines(self.map)
        return [e["local_id"] for e in self.events("object_events")
                if isinstance(e.get("local_id"), str) and defs.eval(e["local_id"]) is None]

    def save(self, force=False):
        """Write what changed. Raises ChangedOnDisk instead, unless force, when a file to
        be written was changed by something else since it was read."""
        if not force:
            changed = self.changed_on_disk()
            if changed:
                raise ChangedOnDisk(changed)
        if self.dirty:
            self._define_object_ids()
            edit.save_json(self.map_json, self.data, self.style)
            self.map_json_mtime = _mtime(self.map_json)
            self.dirty = False
        for c in self.chunks.values():
            c.save()
        self.repo._cache.clear()

    def _define_object_ids(self):
        """Give new objects a #define in ids.h, as `mapkit npc add` does: the lowest
        number no object of the map uses."""
        missing = self.missing_object_ids()
        if not missing:
            return
        defs = self.repo.event_defines(self.map)
        used = {defs.eval(e["local_id"]) for e in self.events("object_events")}
        path = edit._ids_path(self.repo, self.map)
        for name in missing:
            num = next(n for n in range(256) if n not in used)
            edit._add_define(path, name, num, "obj_")
            used.add(num)
        self.repo._cache.clear()


def _land_index(repo):
    """{land data number: {map folder}} over every layout and the maps that use it."""
    by_layout = {}
    for m in repo.maps:
        d = repo.map_dir(m)
        lay = repo.layout_folder(m) if d else None
        if lay:
            by_layout.setdefault(lay, []).append((m.name, os.path.basename(d)))
    out = {}
    for lay, maps in by_layout.items():
        with open(os.path.join(repo.root, layouts.LAYOUTS_DIR, lay, "layout.json"), encoding="utf-8") as f:
            d = json.load(f)
        folders = dict(maps)
        cell_maps = [n for row in d["maps"] for n in row] if d.get("maps") else None
        for i, v in enumerate(n for row in d["land_data"] for n in row):
            if v is None:
                continue
            if cell_maps is None:
                out.setdefault(v, set()).update(folders.values())
            elif cell_maps[i] in folders:
                out.setdefault(v, set()).add(folders[cell_maps[i]])
    return out


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


def enum_names(root, path, prefix):
    """Members starting with prefix of the C enums in a header."""
    with open(os.path.join(root, path), encoding="utf-8") as f:
        text = re.sub(r"/\*.*?\*/", "", re.sub(r"//.*", "", f.read()), flags=re.S)
    out = set()
    for body in re.findall(r"\benum\b[^{;]*\{(.*?)\}", text, re.S):
        out.update(re.findall(r"^\s*(%s\w*)\b" % re.escape(prefix), body, re.M))
    return out


def constant_names(repo, prefix):
    names = set(repo.defines.names(prefix))
    if prefix in ENUM_SOURCES:
        names |= enum_names(repo.root, ENUM_SOURCES[prefix], prefix)
    return sorted(names)
