# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Per-map folders in the style of pret/pokeemerald:

    data/maps/<MapName>/
        map.json          header fields + object/warp/coord/bg events (pokeemerald keys)
        scripts.inc       event scripts (was scr_seq_NNNN_CODE.s)
        map_scripts.inc   on-load/on-transition/on-frame scripts (was scr_seq_NNNN_CODE_hdr.s;
                          a separate binary on DS, so a separate file)
        text.json         msg bank (msgenc JSON, unchanged; DS text isn't .inc)
        ids.h             script and object id defines (was event_CODE.h)

data/maps/maps.txt lists migrated maps, one per line, in a format meson's
fs.read() can parse (pokeemerald's map_groups.json plays this role there):

    <MapName> <MAP_ID> events=<zone_event base> scripts=<scr_seq base> init=<hdr base> text=<msg base>

At build time, data/maps/meson.build regenerates the zone_event JSON and the C
header entry from map.json and copies the scripts/text back to their original
base names, so every NARC member and .naix name is unchanged.
"""

import json
import os
import re
import subprocess

MAPS_DIR = "data/maps"
INDEX = "data/maps/maps.txt"

# MapHeader C field -> map.json key (pokeemerald names where one exists).
# The four bank fields are not stored: they follow from maps.txt.
HEADER_KEYS = [
    ("matrixId", "layout"),
    ("dayMusicId", "music_day"),
    ("nightMusicId", "music_night"),
    ("mapsec", "region_map_section"),
    ("weather", "weather"),
    ("mapType", "map_type"),
    ("battleBg", "battle_scene"),
    ("bikeAllowed", "allow_cycling"),
    ("escapeRopeAllowed", "allow_escaping"),
    ("runningAllowed_Unused", "allow_running"),
    ("flyAllowed", "allow_fly"),
    ("outgoingCalls", "allow_outgoing_calls"),
    ("incomingCalls", "allow_incoming_calls"),
    ("radioSignal", "radio_signal"),
    ("wildEncounterBank", "wild_encounters"),
    ("cameraType", "camera_type"),
    ("followMode", "follow_mode"),
    ("regionNo", "region"),
    ("areaIcon", "area_icon"),
    ("momCallIntroParam", "mom_call_intro"),
    ("worldMapX", "world_map_x"),
    ("worldMapY", "world_map_y"),
    ("areaDataBank", "area_data"),
    ("moveModelBank", "move_model_bank"),
]
BANK_FIELDS = ("scriptsBank", "scriptHeaderBank", "msgBank", "eventsBank")
BOOL_FIELDS = {"bikeAllowed", "escapeRopeAllowed", "runningAllowed_Unused", "flyAllowed",
               "outgoingCalls", "incomingCalls", "radioSignal"}

# zone_event template key -> map.json key, in template order
OBJECT_KEYS = [
    ("id", "local_id"), ("spriteId", "graphics_id"), ("movement", "movement_type"),
    ("type", "trainer_type"), ("eventFlag", "flag"), ("scriptId", "script"),
    ("facingDirection", "facing_dir"), ("param0", "trainer_sight_or_param0"),
    ("param1", "param1"), ("param2", "param2"), ("xRange", "movement_range_x"),
    ("yRange", "movement_range_y"), ("x", "x"), ("z", "y"), ("y", "elevation"),
]
WARP_KEYS = [("x", "x"), ("z", "y"), ("header", "dest_map"), ("anchor", "dest_warp_id"), ("y", "elevation")]
COORD_KEYS = [("scriptId", "script"), ("x", "x"), ("z", "y"), ("w", "width"), ("h", "height"),
              ("y", "elevation"), ("val", "var_value"), ("var", "var")]
BG_KEYS = [("scriptId", "script"), ("type", "type"), ("x", "x"), ("z", "y"), ("y", "elevation"),
           ("dir", "player_facing_dir")]
SECTIONS = [("objects", "object_events", OBJECT_KEYS), ("warps", "warp_events", WARP_KEYS),
            ("coords", "coord_events", COORD_KEYS), ("bgs", "bg_events", BG_KEYS)]
# pokeemerald field order inside each event, for writing map.json
EMERALD_ORDER = {
    "object_events": ["local_id", "graphics_id", "x", "y", "elevation", "movement_type", "movement_range_x",
                      "movement_range_y", "facing_dir", "trainer_type", "trainer_sight_or_param0", "param1",
                      "param2", "script", "flag"],
    "warp_events": ["x", "y", "elevation", "dest_map", "dest_warp_id"],
    "coord_events": ["x", "y", "elevation", "width", "height", "var", "var_value", "script"],
    "bg_events": ["type", "x", "y", "elevation", "player_facing_dir", "script"],
}


class MigrationError(Exception):
    pass


def folder_name(map_name, all_names=()):
    """MAP_CHERRYGROVE_POKECENTER_1F -> Cherrygrove_Pokecenter_1F, MAP_ROUTE_29 -> Route29."""
    name = map_name[4:] if map_name.startswith("MAP_") else map_name
    parent = max((n[4:] for n in all_names if n != map_name and name.startswith(n[4:] + "_")),
                 key=len, default=None)

    def camel(s):
        out = ""
        for w in s.split("_"):
            if re.fullmatch(r"B?\d+F", w):
                out += "_" + w
            else:
                out += w.capitalize()
        return out.lstrip("_")
    if parent:
        return folder_name("MAP_" + parent, all_names) + "_" + camel(name[len(parent) + 1:])
    return camel(name)


# --- index -------------------------------------------------------------------

def read_index(root):
    path = os.path.join(root, INDEX)
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            entry = {"dir": parts[0], "map": parts[1]}
            for kv in parts[2:]:
                k, v = kv.split("=", 1)
                entry[k] = v
            out.append(entry)
    return out


def write_index(root, entries):
    with open(os.path.join(root, INDEX), "w", encoding="utf-8") as f:
        f.write("# Maps migrated to data/maps/<MapName>/ (maintained by tools/mapkit, see layout.py)\n")
        for e in entries:
            f.write("%s %s events=%s scripts=%s init=%s text=%s\n" % (
                e["dir"], e["map"], e["events"], e["scripts"], e["init"], e["text"]))


def folder_paths(root, entry):
    d = os.path.join(root, MAPS_DIR, entry["dir"])
    return {
        "map.json": os.path.join(d, "map.json"),
        "eventsBank": os.path.join(d, "map.json"),
        "scriptsBank": os.path.join(d, "scripts.inc"),
        "scriptHeaderBank": os.path.join(d, "map_scripts.inc"),
        "msgBank": os.path.join(d, "text.json"),
        "ids.h": os.path.join(d, "ids.h"),
    }


# --- map.json <-> header / zone_event ---------------------------------------

def _from_c(field, v):
    if field in BOOL_FIELDS and v in ("TRUE", "FALSE"):
        return v == "TRUE"
    return int(v) if re.fullmatch(r"-?\d+", v) else v


def _to_c(v):
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return str(v)


def header_from_map_json(d, entry):
    """map.json -> {C field: C expression} as in src/data/map_headers.h."""
    h = {}
    for field, key in HEADER_KEYS:
        if key in d:
            h[field] = _to_c(d[key])
    h["scriptsBank"] = entry["scripts"] + "_bin"
    h["scriptHeaderBank"] = entry["init"] + "_bin"
    h["msgBank"] = entry["text"]
    h["eventsBank"] = "NARC_zone_event_%s_bin" % entry["events"]
    return h


def script_ref(v):
    """A map.json "script" value as the zone_event template needs it.

    pokeemerald style: a bare label (Cherrygrove_EventScript_MysticWaterMan) means
    that map script; it becomes `_EV_<label> + 1` (ids.h defines _EV_<label> as its
    ScrDef index). Numbers, std_* constants and expressions pass through."""
    if isinstance(v, str) and re.fullmatch(r"[A-Za-z_]\w*", v) and not v.startswith(("std_", "_EV_")):
        return "_EV_%s + 1" % v
    return v


def zone_event_from_map_json(d, ids_include):
    """map.json -> zone_event JSON dict in template key order."""
    out = {"header": ids_include}
    for tkey, ekey, keys in [("bgs", "bg_events", BG_KEYS), ("objects", "object_events", OBJECT_KEYS),
                             ("warps", "warp_events", WARP_KEYS), ("coords", "coord_events", COORD_KEYS)]:
        out[tkey] = [{t: (script_ref(ev[e]) if e == "script" else ev[e]) for t, e in keys}
                     for ev in d.get(ekey, [])]
    return out


def map_json_from(m_name, folder, code, header, zone_event):
    d = {"id": m_name, "name": folder, "code": code}
    for field, key in HEADER_KEYS:
        if field in header:
            d[key] = _from_c(field, header[field])
    extra = set(header) - {f for f, _ in HEADER_KEYS} - set(BANK_FIELDS)
    if extra:
        raise MigrationError("header fields with no map.json key: %s" % ", ".join(sorted(extra)))
    for tkey, ekey, keys in SECTIONS:
        events = []
        for rec in zone_event.get(tkey, []):
            if set(rec) != {t for t, _ in keys}:
                raise MigrationError("%s record has keys %s" % (tkey, sorted(rec)))
            conv = {e: rec[t] for t, e in keys}
            events.append({k: conv[k] for k in EMERALD_ORDER[ekey]})
        d[ekey] = events
    return d


# --- build-time generators ---------------------------------------------------

def _load_entry(root, map_json_path):
    folder = os.path.basename(os.path.dirname(os.path.abspath(map_json_path)))
    for e in read_index(root):
        if e["dir"] == folder:
            return e
    raise SystemExit("%s is not listed in %s" % (folder, INDEX))


def gen_header(root, map_json_path, out_path):
    """map.json -> C initializer included from src/data/map_headers.h."""
    entry = _load_entry(root, map_json_path)
    with open(map_json_path, encoding="utf-8") as f:
        h = header_from_map_json(json.load(f), entry)
    lines = ["// Generated by tools/mapkit from data/maps/%s/map.json. Do not edit." % entry["dir"], "{"]
    lines += ["    .%s = %s," % (k, v) for k, v in h.items()]
    lines.append("}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def gen_events(root, map_json_path, out_path):
    """map.json -> zone_event JSON for zone_event.json.txt."""
    entry = _load_entry(root, map_json_path)
    with open(map_json_path, encoding="utf-8") as f:
        ze = zone_event_from_map_json(json.load(f), "%s/%s/ids.h" % (MAPS_DIR, entry["dir"]))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(ze, indent=4, ensure_ascii=False) + "\n")


def header_include(map_name):
    return "data/maps/header_%s.h" % map_name


# --- migration ---------------------------------------------------------------

def _move(root, src, dst):
    os.makedirs(os.path.dirname(os.path.join(root, dst)), exist_ok=True)
    subprocess.run(["git", "mv", src, dst], cwd=root, check=True)


def _replace_once(path, old, new):
    """Replace one occurrence, keeping the file's line endings (some files are CRLF)."""
    with open(path, encoding="utf-8", newline="") as f:
        s = f.read()
    if "\r\n" in s:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    if s.count(old) != 1:
        raise MigrationError("%s: expected exactly one %r" % (path, old.strip()[:60]))
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(s.replace(old, new))


def plan(repo, m):
    """What migrating `m` touches; raises MigrationError if it can't be migrated."""
    if any(e["map"] == m.name for e in read_index(repo.root)):
        raise MigrationError("%s is already migrated" % m.name)
    files = {f: repo.bank_path(m, f) for f in BANK_FIELDS}
    for field, p in files.items():
        if p is None or not os.path.exists(p):
            raise MigrationError("%s file not found" % field)
        users = [o.name for o in repo.maps if o.header.get(field) == m.header.get(field)]
        if len(users) > 1:
            raise MigrationError("%s %s is shared with %s" % (field, m.header.get(field), ", ".join(users[1:4])))
    hdr = repo.events(m).header
    if not hdr or not hdr.startswith("fielddata/script/scr_seq/event_"):
        raise MigrationError("unexpected event header %r" % hdr)
    users = subprocess.run(["git", "grep", "-l", "-F", os.path.basename(hdr), "--", "files", "src", "include", "asm"],
                           cwd=repo.root, capture_output=True, text=True).stdout.split()
    own = {repo.rel(files["eventsBank"]), repo.rel(files["scriptsBank"]), repo.rel(files["scriptHeaderBank"]),
           "files/fielddata/script/scr_seq/meson.build"}
    if set(users) - own:
        raise MigrationError("%s is also used by %s" % (hdr, ", ".join(sorted(set(users) - own))))
    base = lambda p: os.path.splitext(os.path.basename(p))[0]
    return {
        "dir": folder_name(m.name, [o.name for o in repo.maps]), "map": m.name,
        "events": base(files["eventsBank"]), "scripts": base(files["scriptsBank"]),
        "init": base(files["scriptHeaderBank"]), "text": base(files["msgBank"]),
        "paths": files, "event_header": hdr,
    }


def migrate(repo, m):
    p = plan(repo, m)
    root = repo.root
    folder = "%s/%s" % (MAPS_DIR, p["dir"])
    if os.path.exists(os.path.join(root, folder)):
        raise MigrationError("%s already exists" % folder)
    ids_h = folder + "/ids.h"
    with open(p["paths"]["eventsBank"], encoding="utf-8") as f:
        zone_event = json.load(f)
    map_json = map_json_from(m.name, p["dir"], m.code, m.header, zone_event)

    # 1. scripts, text and ids move (content kept); events become map.json
    _move(root, repo.rel(p["paths"]["scriptsBank"]), folder + "/scripts.inc")
    _move(root, repo.rel(p["paths"]["scriptHeaderBank"]), folder + "/map_scripts.inc")
    _move(root, repo.rel(p["paths"]["msgBank"]), folder + "/text.json")
    _move(root, "files/" + p["event_header"], ids_h)
    subprocess.run(["git", "rm", "-q", repo.rel(p["paths"]["eventsBank"])], cwd=root, check=True)
    with open(os.path.join(root, folder, "map.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(map_json, indent=4, ensure_ascii=False) + "\n")

    # 2. scripts include ids.h from its new place (bytes unchanged)
    for f in ("scripts.inc", "map_scripts.inc"):
        _replace_once(os.path.join(root, folder, f), '"%s"' % p["event_header"], '"%s"' % ids_h)

    # 3. map_headers.h includes the entry generated from map.json
    hp = os.path.join(root, "src/data/map_headers.h")
    with open(hp, encoding="utf-8", newline="") as f:
        src = f.read()
    nl = "\r\n" if "\r\n" in src else "\n"
    mm = re.search(r"(    \[%s\] = )\{.*?\n\s*\}," % re.escape(m.name), src, re.S)
    if not mm:
        raise MigrationError("header entry for %s not found" % m.name)
    new = "%s%s#include \"%s\"%s    ," % (mm.group(1).rstrip(), nl, header_include(m.name), nl)
    with open(hp, "w", encoding="utf-8", newline="") as f:
        f.write(src[:mm.start()] + new + src[mm.end():])

    # 4. drop the moved files from the old meson lists
    _replace_once(os.path.join(root, "files/fielddata/eventdata/zone_event/meson.build"),
                  "    '%s.json',\n" % p["events"], "")
    sm = os.path.join(root, "files/fielddata/script/scr_seq/meson.build")
    for item in (p["scripts"] + ".s", p["init"] + ".s", os.path.basename(p["event_header"])):
        _replace_once(sm, "    '%s',\n" % item, "")

    # 5. index
    write_index(root, read_index(root) + [p])
    subprocess.run(["git", "add", INDEX, folder, "src/data/map_headers.h",
                    "files/fielddata/eventdata/zone_event/meson.build",
                    "files/fielddata/script/scr_seq/meson.build"], cwd=root, check=True)
    return p
