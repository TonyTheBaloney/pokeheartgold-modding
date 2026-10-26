# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
"""Consistency checks across headers, events, scripts, text and wild data."""

import json
import os
import re
from dataclasses import dataclass

from . import events as ev_mod
from . import scripts, text
from .matrix import CELL_SIZE

ERROR, WARNING, INFO = "error", "warning", "info"
LOCAL_SCRIPT_MAX = 1999  # ids 1..1999 are map scripts; 2000+ are std banks
INVALID_MOVEMENTS = {47}
NUM_MOVEMENTS = 57
_SYMBOL_PREFIXES = ("FLAG_", "VAR_", "obj_", "ITEM_", "SPECIES_", "TRAINER_", "MAP_", "SPRITE_")


@dataclass
class Issue:
    severity: str
    check: str
    where: str
    message: str

    def __str__(self):
        return "%s: %s [%s] %s" % (self.where, self.severity, self.check, self.message)


class Validator:
    def __init__(self, repo):
        self.repo = repo
        self.issues = []
        self._done_files = set()
        self._widths = None

    def add(self, severity, check, where, message):
        self.issues.append(Issue(severity, check, where, message))

    def run(self, maps=None):
        maps = maps if maps is not None else self.repo.maps
        for m in maps:
            self.check_map(m)
        return self.issues

    # --- per map ---------------------------------------------------------

    def check_map(self, m):
        r = self.repo
        for field in ("eventsBank", "scriptsBank", "scriptHeaderBank", "msgBank", "matrixId"):
            p = r.bank_path(m, field)
            if p is None or not os.path.exists(p):
                self.add(ERROR, "bank-file", m.name, "%s %s: file not found" % (field, m.header.get(field)))
        ev = r.events(m)
        if ev is not None and ev.path not in self._done_files:
            self._done_files.add(ev.path)
            self.check_events(m, ev)
        if ev is not None:
            self.check_warps(m, ev)
        for field in ("scriptsBank", "scriptHeaderBank"):
            sf = r.script_file(m, field)
            if sf is not None and sf.path not in self._done_files:
                self._done_files.add(sf.path)
                self.check_script_file(m, sf)
        self.check_wild(m)
        self.check_text_slots(m)
        self.check_text_width(m)

    def check_text_slots(self, m):
        """text.json slots ("from") that scripts.pory no longer fills build as empty messages."""
        r = self.repo
        e = r.migrated.get(m.name)
        pe = r.pory_entry(m)
        if not e or e["text"].startswith("@") or pe is None or pe["dir"] != e["dir"]:
            return
        from . import pory
        unfilled = []
        pory.merged_text(r, e, r.pory_result(m), unfilled)
        for mid, src in unfilled:
            where = "%s/text.json" % e["dir"]
            if "#" in src:
                self.add(WARNING, "empty-text", where, "%s: %s has no string %s (renamed or removed?); "
                         "it builds as an empty message" % (mid, src.split("#")[0], src.split("#")[1]))
            else:
                self.add(WARNING, "empty-text", where, "%s: no `text %s` block in scripts.pory; "
                         "it builds as an empty message" % (mid, mid))

    def check_text_width(self, m):
        """Lines wider than the dialogue box (216 px in the dialogue font) run past its edge."""
        r = self.repo
        tb = r.text_bank(m)
        if tb is None or ("text-width", tb.path) in self._done_files:
            return
        self._done_files.add(("text-width", tb.path))
        if self._widths is None:
            try:
                self._widths = text.Widths(r.path(text.CHARMAP), r.path(text.MESSAGE_FONT))
                banks = {}
                for base in set(text.SLOT_BANKS.values()):
                    p = r.path("files/msgdata/msg", base + ".json")
                    if os.path.exists(p):
                        banks[base] = text.load(p)
                items = r.path("data/items/items.json")
                names = []
                if os.path.exists(items):
                    with open(items, encoding="utf-8") as f:
                        names = [v.get("name") or "" for v in json.load(f).values()]
                self._widths.add_slot_widths(banks, names)
            except OSError:
                self._widths = False
        if not self._widths:
            return
        owner = r.text_owner(m)
        res = r.pory_result(owner) if owner is not None and r.pory_entry(owner) is not None else None
        lines = res.text_lines if res is not None else {}
        pory_path = res is not None and r.rel(r.bank_path(owner, "scriptsBank"))
        for msg in tb.messages:
            mid = msg.get("id")
            for line, px in self._widths.lines(text.TextBank.text_of(msg)):
                if px <= text.DIALOG_WIDTH:
                    continue
                where = ("%s:%d" % (pory_path, lines[mid]) if mid in lines
                         else "%s %s" % (r.rel(tb.path), mid))
                self.add(WARNING, "text-width", where, "line is %d px (names counted at their longest), the text box is %d: %r"
                         % (px, text.DIALOG_WIDTH, line))

    def _eval(self, defs, value, where, what):
        v = defs.eval(value)
        if v is None:
            self.add(ERROR, "unresolved", where, "%s: cannot resolve %r" % (what, value))
        return v

    def check_events(self, m, ev):
        r = self.repo
        defs = r.event_defines(m)
        where = r.rel(ev.path)
        if ev.binary_size >= ev_mod.EVENT_BUFFER_SIZE:
            self.add(ERROR, "events-size", where, "events binary is %d bytes; must be < %d"
                     % (ev.binary_size, ev_mod.EVENT_BUFFER_SIZE))
        sf = r.script_file(m)
        nscripts = len(sf.scrdefs) if sf else 0
        mx = r.matrix(m)

        def check_script_id(value, w):
            sid = self._eval(defs, value, w, "scriptId")
            if sid is not None and 1 <= sid <= LOCAL_SCRIPT_MAX and sid > nscripts:
                self.add(ERROR, "script-id", w, "script id %d but %s has %d scripts"
                         % (sid, os.path.basename(sf.path) if sf else "the script bank", nscripts))

        def check_pos(obj, w):
            if mx is None:
                return
            x, z = defs.eval(obj.get("x")), defs.eval(obj.get("z"))
            if x is None or z is None:
                return
            cell = mx.cell(x, z)
            if cell is None:
                self.add(WARNING, "outside-matrix", w, "(%d, %d) is outside the %dx%d-cell matrix"
                         % (x, z, mx.width, mx.height))
            elif mx.header_ids and mx.header_ids[cell] != m.id and mx.width * mx.height > 1:
                owner = next((o.name for o in r.maps if o.id == mx.header_ids[cell]), mx.header_ids[cell])
                self.add(INFO, "other-map-cell", w, "(%d, %d) lies in a cell owned by %s" % (x, z, owner))

        seen = {}
        for i, o in enumerate(ev.objects):
            w = "%s objects[%d] %s" % (where, i, o.get("id"))
            for k in ("id", "spriteId", "movement", "type", "eventFlag", "facingDirection", "x", "z"):
                self._eval(defs, o.get(k), w, k)
            oid = defs.eval(o.get("id"))
            if oid is not None:
                if oid in seen:
                    # Retail maps do this for NPCs that are never shown at the same time.
                    self.add(WARNING, "object-id", w, "id %d already used by objects[%d]" % (oid, seen[oid]))
                seen[oid] = i
            mv = defs.eval(o.get("movement"))
            if mv is not None and (mv >= NUM_MOVEMENTS or mv in INVALID_MOVEMENTS or mv < 0):
                self.add(ERROR, "movement", w, "movement %d is not a valid movement type" % mv)
            check_script_id(o.get("scriptId"), w)
            check_pos(o, w)
        for i, b in enumerate(ev.bgs):
            w = "%s bgs[%d]" % (where, i)
            for k in ("type", "x", "z", "dir"):
                self._eval(defs, b.get(k), w, k)
            check_script_id(b.get("scriptId"), w)
            check_pos(b, w)
        for i, c in enumerate(ev.coords):
            w = "%s coords[%d]" % (where, i)
            for k in ("x", "z", "w", "h", "val", "var"):
                self._eval(defs, c.get(k), w, k)
            check_script_id(c.get("scriptId"), w)
            check_pos(c, w)

    def check_warps(self, m, ev):
        r = self.repo
        defs = r.event_defines(m)
        where = r.rel(ev.path)
        for i, wp in enumerate(ev.warps):
            w = "%s warps[%d] (%s)" % (where, i, m.name)
            if ev_mod.is_dynamic_warp(wp, defs):
                continue
            dest_id = self._eval(defs, wp.get("header"), w, "header")
            anchor = self._eval(defs, wp.get("anchor"), w, "anchor")
            if dest_id is None or anchor is None:
                continue
            dest = next((d for d in r.maps if d.id == dest_id), None)
            if dest is None:
                self.add(ERROR, "warp-dest", w, "destination map id %d does not exist" % dest_id)
                continue
            dev = r.events(dest)
            if dev is None or anchor >= len(dev.warps):
                self.add(ERROR, "warp-dest", w, "%s has %d warps; anchor %d does not exist"
                         % (dest.name, len(dev.warps) if dev else 0, anchor))
                continue
            back = dev.warps[anchor]
            back_id = r.event_defines(dest).eval(back.get("header"))
            if back_id != m.id and not ev_mod.is_dynamic_warp(back, r.event_defines(dest)):
                self.add(INFO, "warp-one-way", w, "lands on %s warp %d, which leads to %s"
                         % (dest.name, anchor, next((d.name for d in r.maps if d.id == back_id), back_id)))

    def check_script_file(self, m, sf):
        r = self.repo
        macros = r.macros
        where = r.rel(sf.path)
        defs = r.defines.child()
        msg_ids = set()
        for inc in sf.includes:
            p = r.include_path(inc)
            if p and (inc.startswith("fielddata/script/scr_seq/event_") or inc.endswith("/ids.h")):
                defs.load(p)
            mm = re.match(r"msgdata/msg/(msg_\w+)\.h$", inc)
            if mm:
                msg_ids |= r.text_ids(mm.group(1))
        for label in sf.scrdefs:
            if label not in sf.labels:
                self.add(ERROR, "scrdef-label", where, "ScrDef %s has no label" % label)
        for n, s in sf.unknown:
            self.add(ERROR, "unknown-macro", "%s:%d" % (where, n), "unknown command: %s" % s)
        for st, label in scripts.label_refs(sf, macros):
            base = re.split(r"[\s+\-]", label.strip())[0]
            if base not in sf.labels:
                self.add(ERROR, "missing-label", "%s:%d" % (where, st.line), "%s refers to undefined label %s"
                         % (st.macro, base))
        reported = set()
        for st, sym in scripts.symbol_refs(sf):
            if sym.startswith("msg_"):
                if msg_ids and sym not in msg_ids and sym not in reported:
                    reported.add(sym)
                    self.add(ERROR, "missing-text", "%s:%d" % (where, st.line), "%s not in the included text bank" % sym)
            elif sym.startswith(_SYMBOL_PREFIXES) and defs.eval(sym) is None and sym not in reported:
                reported.add(sym)
                self.add(ERROR, "unresolved", "%s:%d" % (where, st.line), "undefined symbol %s" % sym)
        # init-script entries name script ids directly
        for st in sf.statements:
            if st.macro.startswith("InitScript") and st.args:
                sid_text = st.args[-1] if st.macro == "InitScriptGoToIfEqual" else st.args[0]
                if "_EV_" in sid_text:
                    sid = defs.eval(sid_text)
                    if sid is None:
                        self.add(ERROR, "unresolved", "%s:%d" % (where, st.line), "cannot resolve %s" % sid_text)

    def check_wild(self, m):
        r = self.repo
        bank = m.header.get("wildEncounterBank", "ENCDATA_NA")
        if bank == "ENCDATA_NA":
            return
        i, table = r.wild_table(m)
        if i is None:
            self.add(ERROR, "wild-bank", m.name, "%s is not defined in encounter_tables_narc.h" % bank)
            return
        if table is None:
            self.add(ERROR, "wild-bank", m.name, "%s is index %d but gs_enc_data.json has %d tables"
                     % (bank, i, len(r.wild_tables)))
            return
        key = ("wild", i)
        if key in self._done_files:
            return
        self._done_files.add(key)
        from . import wild
        for method, slot, species, level in wild.iter_slots(table, r.version):
            if species is not None and r.defines.eval(species) is None:
                self.add(ERROR, "wild-species", "%s %s[%d]" % (bank, method, slot), "unknown species %r" % species)
        for method, rate in wild.rates(table, r.version).items():
            mons = table.get("fishing", {}).get(method) if method.endswith("_rod") else table.get(method)
            n = len((mons or {}).get("mons", []))
            if rate and n != wild.SLOT_COUNTS[method]:
                self.add(ERROR, "wild-slots", "%s %s" % (bank, method), "rate %s but %d slots (need %d)"
                         % (rate, n, wild.SLOT_COUNTS[method]))
