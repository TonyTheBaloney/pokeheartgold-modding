# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""The repository as a set of maps, each tied to its data files."""

import glob
import json
import os
import re
from dataclasses import dataclass

from . import cdefs, events, layout, matrix, scripts, text, wild

VERSIONS = ("HEARTGOLD", "SOULSILVER")

_MAP_DEFINE_RE = re.compile(r"^#define\s+(MAP_\w+)\s+(\d+)\s*(?://\s*MAP_(\w+))?", re.M)
_HEADER_ENTRY_RE = re.compile(r"\[(MAP_\w+)\]\s*=\s*\{(.*?)\n\s*\},", re.S)
_HEADER_FIELD_RE = re.compile(r"\.(\w+)\s*=\s*([^,\n]+),")


def find_root(start=None):
    d = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.exists(os.path.join(d, "include/constants/maps.h")) and \
                os.path.isdir(os.path.join(d, "files/fielddata")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise FileNotFoundError("not inside a pokeheartgold checkout")
        d = parent


@dataclass
class MapInfo:
    id: int
    name: str      # MAP_CHERRYGROVE
    code: str      # T21 (Game Freak's code, from the maps.h comment)
    header: dict   # field -> C expression text from src/data/map_headers.h

    @property
    def short_name(self):
        return self.name[4:] if self.name.startswith("MAP_") else self.name


class Repo:
    def __init__(self, root=None, version="HEARTGOLD"):
        if version not in VERSIONS:
            raise ValueError("version must be one of %s" % (VERSIONS,))
        self.root = find_root(root)
        self.version = version
        self._defines = None
        self._maps = None
        self._macros = None
        self._cache = {}

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def rel(self, path):
        return os.path.relpath(path, self.root)

    # --- constants -------------------------------------------------------

    @property
    def defines(self):
        if self._defines is None:
            d = cdefs.Defines(defined={self.version, "ENGLISH"})
            for h in sorted(glob.glob(self.path("include/constants/*.h"))):
                d.load(h)
            self._defines = d
        return self._defines

    @property
    def macros(self):
        if self._macros is None:
            t = scripts.MacroTable()
            t.load(self.path("asm/macros/script.inc"), "script")
            t.load(self.path("asm/macros/movement.inc"), "movement")
            self._macros = t
        return self._macros

    # --- maps ------------------------------------------------------------

    @property
    def maps(self):
        if self._maps is None:
            ids = {}
            with open(self.path("include/constants/maps.h"), encoding="utf-8") as f:
                maps_h = f.read()
            for name, num, code in _MAP_DEFINE_RE.findall(maps_h):
                ids[name] = (int(num), code or "")
            headers = {}
            with open(self.path("src/data/map_headers.h"), encoding="utf-8") as f:
                src = f.read()
            for name, body in _HEADER_ENTRY_RE.findall(src):
                headers[name] = {k: v.strip() for k, v in _HEADER_FIELD_RE.findall(body)}
            for entry in self.migrated.values():  # data/maps/<MapName>/map.json
                with open(layout.folder_paths(self.root, entry)["map.json"], encoding="utf-8") as f:
                    headers[entry["map"]] = layout.header_from_map_json(json.load(f), entry)
            out = []
            for name, (num, code) in sorted(ids.items(), key=lambda kv: kv[1][0]):
                if name in headers:
                    out.append(MapInfo(num, name, code, headers[name]))
            self._maps = out
        return self._maps

    def map_by_name(self, name):
        for m in self.maps:
            if m.name == name:
                return m
        return None

    def find_map(self, query):
        """Accepts MAP_CHERRYGROVE, CHERRYGROVE, cherrygrove, Cherrygrove_PokeMart, T21 or 67."""
        q = str(query).strip()
        if q.isdigit():
            for m in self.maps:
                if m.id == int(q):
                    return m
        norm = re.sub(r"[^a-z0-9]", "", q.lower())
        for m in self.maps:
            if q == m.name or q.upper() == m.code or norm == re.sub(r"[^a-z0-9]", "", m.short_name.lower()):
                return m
        return None

    # --- per-map files ---------------------------------------------------

    @property
    def migrated(self):
        """MAP_* name -> data/maps/maps.txt entry, for maps that live in data/maps."""
        return self._cached("migrated", lambda: {e["map"]: e for e in layout.read_index(self.root)})

    def map_dir(self, m):
        e = self.migrated.get(m.name)
        return self.path(layout.MAPS_DIR, e["dir"]) if e else None

    def bank_path(self, m, field):
        e = self.migrated.get(m.name)
        if e and field in layout.BANK_FIELDS:
            return layout.folder_paths(self.root, e)[field]
        v = m.header.get(field, "")
        if field in ("scriptsBank", "scriptHeaderBank"):
            mm = re.match(r"(scr_seq_\w+?)_bin$", v)
            return self.path("files/fielddata/script/scr_seq", mm.group(1) + ".s") if mm else None
        if field == "msgBank":
            return self.path("files/msgdata/msg", v + ".json") if v.startswith("msg_") else None
        if field == "eventsBank":
            mm = re.match(r"NARC_zone_event_(\w+?)_bin$", v)
            return self.path("files/fielddata/eventdata/zone_event", mm.group(1) + ".json") if mm else None
        if field == "matrixId":
            mm = re.match(r"NARC_map_matrix_(\w+?)_bin$", v)
            return self.path("files/fielddata/mapmatrix/map_matrix", mm.group(1) + ".bin") if mm else None
        raise KeyError(field)

    def _cached(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def events(self, m):
        p = self.bank_path(m, "eventsBank")
        if not p or not os.path.exists(p):
            return None
        e = self.migrated.get(m.name)
        if e:
            def from_map_json():
                with open(p, encoding="utf-8") as f:
                    ze = layout.zone_event_from_map_json(json.load(f), "%s/%s/ids.h" % (layout.MAPS_DIR, e["dir"]))
                return events.Events(p, ze["header"], ze["bgs"], ze["objects"], ze["warps"], ze["coords"])
            return self._cached(("events", p), from_map_json)
        return self._cached(("events", p), lambda: events.load(p))

    def text_bank_path(self, base):
        """msg_NNNN[_CODE] -> its JSON, in data/maps/<MapName>/ if the map was migrated."""
        for e in self.migrated.values():
            if e["text"] == base:
                return layout.folder_paths(self.root, e)["msgBank"]
        return self.path("files/msgdata/msg", base + ".json")

    def include_path(self, inc):
        """Resolve an include as the build does (files/ or the repo root)."""
        for p in (self.path("files", inc), self.path(inc)):
            if os.path.exists(p):
                return p
        return None

    def event_defines(self, m):
        """Repo constants plus the map's event_CODE.h (script and object ids)."""
        ev = self.events(m)
        hdr = ev.header if ev else None

        def build():
            d = self.defines.child()
            p = self.include_path(hdr) if hdr else None
            if p:
                d.load(p)
            return d
        return self._cached(("evdefs", hdr), build)

    def script_file(self, m, field="scriptsBank"):
        p = self.bank_path(m, field)
        if not p or not os.path.exists(p):
            return None
        return self._cached(("script", p), lambda: scripts.parse(p, self.macros))

    def text_bank(self, m):
        p = self.bank_path(m, "msgBank")
        return self._cached(("text", p), lambda: text.load(p)) if p and os.path.exists(p) else None

    def matrix(self, m):
        p = self.bank_path(m, "matrixId")
        return self._cached(("matrix", p), lambda: matrix.load(p)) if p and os.path.exists(p) else None

    # --- wild ------------------------------------------------------------

    @property
    def wild_index(self):
        return self._cached("wild_index", lambda: wild.load_index(self.path("include/encounter_tables_narc.h")))

    @property
    def wild_tables(self):
        return self._cached("wild_tables", lambda: wild.load_tables(
            self.path("files/fielddata/encountdata/gs_enc_data.json")))

    def wild_table(self, m):
        """(index, table) for the map, or (None, None) if it has none."""
        bank = m.header.get("wildEncounterBank", "ENCDATA_NA")
        if bank == "ENCDATA_NA":
            return None, None
        i = self.wild_index.get(bank)
        if i is None or i >= len(self.wild_tables):
            return i, None
        return i, self.wild_tables[i]
