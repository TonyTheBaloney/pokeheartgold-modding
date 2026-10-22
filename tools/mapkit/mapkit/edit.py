# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Edits to map data. Every write keeps the file's existing JSON indentation,
trailing newline and line endings, so a diff shows only the change.

Events are addressed with pokeemerald keys (object_events, x/y/elevation,
graphics_id, ...) for both migrated maps (data/maps/<MapName>/map.json) and
maps still in files/fielddata/eventdata/zone_event/.
"""

import json
import os
import re

from . import layout

SECTION_KEYS = {ekey: keys for _, ekey, keys in layout.SECTIONS}
TEMPLATE_SECTION = {ekey: tkey for tkey, ekey, _ in layout.SECTIONS}


class EditError(Exception):
    pass


# --- file helpers ------------------------------------------------------------

def _read_text(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def load_json(path):
    raw = _read_text(path)
    m = re.match(r"\{\r?\n( +)", raw)
    style = {"indent": len(m.group(1)) if m else 4, "newline": raw.endswith("\n"), "crlf": "\r\n" in raw}
    return json.loads(raw), style


def save_json(path, data, style):
    out = json.dumps(data, indent=style["indent"], ensure_ascii=False)
    if style["newline"]:
        out += "\n"
    if style["crlf"]:
        out = out.replace("\n", "\r\n")
    _write_text(path, out)


# --- events ------------------------------------------------------------------

class EventsDoc:
    """A map's events as lists of dicts with pokeemerald keys."""

    def __init__(self, repo, m):
        self.repo, self.map = repo, m
        self.migrated = m.name in repo.migrated
        self.path = repo.bank_path(m, "eventsBank")
        self.data, self.style = load_json(self.path)

    def section(self, ekey):
        if self.migrated:
            return self.data.setdefault(ekey, [])
        keys = SECTION_KEYS[ekey]
        return [{e: rec[t] for t, e in keys} for rec in self.data.get(TEMPLATE_SECTION[ekey], [])]

    def set_section(self, ekey, records):
        if self.migrated:
            self.data[ekey] = records
            return
        keys = SECTION_KEYS[ekey]
        self.data[TEMPLATE_SECTION[ekey]] = [{t: rec[e] for t, e in keys} for rec in records]

    def save(self):
        save_json(self.path, self.data, self.style)
        self.repo._cache.clear()


def find_object(objects, query):
    for i, o in enumerate(objects):
        lid = str(o["local_id"])
        if query in (lid, str(i)) or lid.endswith("_" + query):
            return i
    raise EditError("no object %r (have: %s)" % (query, ", ".join(str(o["local_id"]) for o in objects)))


def npc_set(repo, m, query, **fields):
    doc = EventsDoc(repo, m)
    objs = doc.section("object_events")
    i = find_object(objs, query)
    for k, v in fields.items():
        if k not in objs[i]:
            raise EditError("objects have no field %r (fields: %s)" % (k, ", ".join(objs[i])))
        objs[i][k] = v
    doc.set_section("object_events", objs)
    doc.save()
    return objs[i]


def _ids_path(repo, m):
    ev = repo.events(m)
    p = repo.include_path(ev.header) if ev and ev.header else None
    if not p:
        raise EditError("%s: event header %r not found" % (m.name, ev.header if ev else None))
    return p


def _add_define(path, name, value, after_prefix):
    """Add `#define name value` after the last define starting with after_prefix."""
    text = _read_text(path)
    nl = "\r\n" if "\r\n" in text else "\n"
    if re.search(r"#define\s+%s\b" % re.escape(name), text):
        raise EditError("%s already defines %s" % (os.path.basename(path), name))
    lines = text.split(nl)
    last = max((i for i, l in enumerate(lines) if re.match(r"#define\s+%s" % re.escape(after_prefix), l)), default=None)
    if last is None:  # before the closing #endif
        last = max(i for i, l in enumerate(lines) if l.startswith("#endif")) - 1
    lines.insert(last + 1, "#define %s %s" % (name, value))
    _write_text(path, nl.join(lines))


def npc_add(repo, m, name, graphics, x, y, elevation=0, movement="MOVEMENT_TYPE_NONE", facing="DIR_SOUTH",
            script=0, flag="FLAG_NOTHING", trainer_type="OBJECT_TYPE_NORMAL", sight=0, range_x=0, range_y=0):
    doc = EventsDoc(repo, m)
    objs = doc.section("object_events")
    defs = repo.event_defines(m)
    used = {defs.eval(o["local_id"]) for o in objs}
    num = next(n for n in range(256) if n not in used)
    prefix = re.match(r"(obj_[A-Za-z0-9]+_)", str(objs[0]["local_id"])) if objs else None
    local_id = name if name.startswith("obj_") else (prefix.group(1) if prefix else "obj_%s_" % m.code) + name
    _add_define(_ids_path(repo, m), local_id, num, "obj_")
    rec = {"local_id": local_id, "graphics_id": graphics, "x": x, "y": y, "elevation": elevation,
           "movement_type": movement, "movement_range_x": range_x, "movement_range_y": range_y,
           "facing_dir": facing, "trainer_type": trainer_type, "trainer_sight_or_param0": sight,
           "param1": 0, "param2": 0, "script": script, "flag": flag}
    objs.append(rec)
    doc.set_section("object_events", objs)
    doc.save()
    return rec


def warp_set(repo, m, index, dest_map, dest_warp):
    doc = EventsDoc(repo, m)
    warps = doc.section("warp_events")
    if not 0 <= index < len(warps):
        raise EditError("%s has %d warps" % (m.name, len(warps)))
    warps[index]["dest_map"] = dest_map
    warps[index]["dest_warp_id"] = dest_warp
    doc.set_section("warp_events", warps)
    doc.save()


def warp_link(repo, a, ai, b, bi):
    """Make a's warp ai lead to b's warp bi and back."""
    warp_set(repo, a, ai, b.name, bi)
    warp_set(repo, b, bi, a.name, ai)


def warp_add(repo, m, x, y, dest_map, dest_warp, elevation=0):
    doc = EventsDoc(repo, m)
    warps = doc.section("warp_events")
    warps.append({"x": x, "y": y, "elevation": elevation, "dest_map": dest_map, "dest_warp_id": dest_warp})
    doc.set_section("warp_events", warps)
    doc.save()
    return len(warps) - 1


# --- text --------------------------------------------------------------------

def text_add(repo, m, text):
    path = repo.bank_path(m, "msgBank")
    data, style = load_json(path)
    msgs = data["messages"]
    base = os.path.splitext(os.path.basename(path))[0]
    if base == "text":
        base = repo.migrated[m.name]["text"]
    nums = [int(x.group(1)) for x in (re.search(r"_(\d+)$", str(mm.get("id", ""))) for mm in msgs) if x]
    msg_id = "%s_%05d" % (base, (max(nums) + 1) if nums else 0)
    parts = text.split("\\n")
    lines = [p + "\n" for p in parts[:-1]] + [parts[-1]]
    msgs.append({"id": msg_id, "en_US": lines if len(lines) > 1 else lines[0]})
    save_json(path, data, style)
    repo._cache.clear()
    return msg_id


# --- scripts -----------------------------------------------------------------

def script_add(repo, m, label, msg_id=None):
    """Append a script (and its ScrDef entry and _EV_ id). With msg_id, a talk-to-NPC stub."""
    path = repo.bank_path(m, "scriptsBank")
    text = _read_text(path)
    nl = "\r\n" if "\r\n" in text else "\n"
    if re.search(r"^%s:" % re.escape(label), text, re.M):
        raise EditError("label %s already exists" % label)
    sf = repo.script_file(m)
    index = len(sf.scrdefs)
    lines = text.split(nl)
    end = next((i for i, l in enumerate(lines) if l.strip() == "ScrDefEnd"), None)
    if end is None:
        raise EditError("no ScrDefEnd in %s" % path)
    lines.insert(end, "\tScrDef %s" % label)
    text = nl.join(lines)
    body = ["", "%s:" % label]
    if msg_id:
        body += ["\tPlaySE SEQ_SE_DP_SELECT", "\tLockAll", "\tFacePlayer", "\tNPCMsg %s" % msg_id,
                 "\tWaitButton", "\tCloseMsg", "\tReleaseAll"]
    body += ["\tEnd", ""]
    if not text.endswith(nl):
        text += nl
    _write_text(path, text + nl.join(body))
    _add_define(_ids_path(repo, m), "_EV_" + label, index, "_EV_")
    repo._cache.clear()
    return index + 1


def script_rename(repo, m, old, new):
    """Rename a script label everywhere in the map (labels, ScrDef, _EV_ ids, events)."""
    if not re.fullmatch(r"[A-Za-z_]\w*", new):
        raise EditError("%r is not a valid label" % new)
    sf = repo.script_file(m)
    if old not in sf.scrdefs:
        raise EditError("%s is not a script in %s (have: %s)" % (old, m.name, ", ".join(sf.scrdefs)))
    if new in sf.labels:
        raise EditError("label %s already exists" % new)
    files = [repo.bank_path(m, "scriptsBank"), repo.bank_path(m, "scriptHeaderBank"), _ids_path(repo, m)]
    pat = re.compile(r"\b(_EV_)?%s\b" % re.escape(old))
    for p in files:
        _write_text(p, pat.sub(lambda mm: (mm.group(1) or "") + new, _read_text(p)))
    doc = EventsDoc(repo, m)
    for ekey in ("object_events", "bg_events", "coord_events"):
        recs = doc.section(ekey)
        for r in recs:
            if isinstance(r.get("script"), str) and pat.search(r["script"]):
                # pokeemerald style: refer to the script by its label
                r["script"] = new if doc.migrated else pat.sub(lambda mm: (mm.group(1) or "") + new, r["script"])
        doc.set_section(ekey, recs)
    doc.save()
    repo._cache.clear()


# --- wild --------------------------------------------------------------------

def wild_set(repo, m, method, slot, species=None, level=None, time=None):
    i, table = repo.wild_table(m)
    if table is None:
        raise EditError("%s has no wild table (wildEncounterBank %s)" % (m.name, m.header.get("wildEncounterBank")))
    path = repo.path("files/fielddata/encountdata/gs_enc_data.json")
    data, style = load_json(path)
    t = data["encounters"][i]
    group = t["fishing"].get(method) if method.endswith("_rod") else t.get(method)
    if group is None:
        raise EditError("unknown method %r (land, surf, rock_smash, old_rod, good_rod, super_rod)" % method)
    if not 0 <= slot < len(group["mons"]):
        raise EditError("%s %s has %d slots" % (m.name, method, len(group["mons"])))
    mon = group["mons"][slot]
    if species is not None:
        if isinstance(mon["species"], dict) and "morn" in mon["species"]:
            for tod in ([time] if time else ["morn", "day", "nite"]):
                mon["species"][tod] = species
        else:
            mon["species"] = species
    if level is not None:
        if isinstance(mon["level"], dict):
            lo, _, hi = str(level).partition("-")
            mon["level"] = {"min": int(lo), "max": int(hi or lo)}
        else:
            mon["level"] = int(level)
    save_json(path, data, style)
    repo._cache.clear()
    return mon
