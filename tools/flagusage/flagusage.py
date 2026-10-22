#!/usr/bin/env python3
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Find where every FLAG_UNK_* and VAR_UNK_* is used, and which are free.

    python3 tools/flagusage/flagusage.py            # summary
    python3 tools/flagusage/flagusage.py --free     # free flags and vars, as ranges
    python3 tools/flagusage/flagusage.py --markdown > docs/modding/unknown-flags-vars.md

A flag or var counts as used when any name with its value (aliases included)
appears outside include/constants/{flags,vars}.h, when C code reaches it as
BASE + offset (INDIRECT below), or when a following-Pokemon rule in
files/a/2/2/0 names it by number. "Write-only" means scripts set it but nothing
reads it. docs/modding/unknown-flags-vars.md explains the results.
"""

import collections
import json
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
FLAGS_H = "include/constants/flags.h"
VARS_H = "include/constants/vars.h"
SOURCE_EXT = (".c", ".h", ".s", ".inc", ".pory", ".json", ".txt", ".py", ".cpp")
FOLLOW_MON_RULES = "files/a/2/2/0"   # FollowMonRule, 20 bytes, flag at offset 18
FRONTIER_SCRIPTS = "files/a/1/8/2"   # compiled Battle Frontier scripts
FRONTIER_SET_SAVE_VAR = 61           # gFrontierCommandTable: FrtCmd_SetSaveVar, then
FRONTIER_GET_SAVE_VAR = 62           # FrtCmd_GetSaveVar; both opcode u16, var id u16

# Reached only as BASE + offset in C; value -> what it does. Checked by hand
# against the code named in each entry. Offsets no caller passes are left out
# (map event keys 2-3, event key 1).
INDIRECT = {}
for i in range(1, 6):
    INDIRECT[0x97B + i] = ("rematch tier %d unlocked: `EventFlagCheck_RematchGroup` checks FLAG_UNK_97B + tier "
                           "(src/trainer_rematch.c)" % i)
INDIRECT[0x97C] += "; nothing sets it"
INDIRECT[0x980] += "; nothing sets it"
for i in range(3):
    INDIRECT[0x96B + i] = ("Team Rocket HQ Electrode %d defeated: `CheckRocketHQElectrodeDefeated` "
                           "(FLAG_UNK_96B + index, src/sys_flags.c)" % (i + 1))
for i in range(1, 10):
    INDIRECT[0x988 + i] = ("Prof. Oak has called about %d Pokémon owned: `gear_phone_ring_manager.c` checks "
                           "FLAG_SYS_OAK_ACKNOWLEDGED_NATIONAL_DEX_COMPLETION + owned / 50" % (i * 50))
INDIRECT[0x9B0 + 25] = ("fly point 25 (`FLYPOINT_UNK25`, `FLAG_SYS_FLYPOINT_PALLET` + 25): checked by "
                        "`Save_VarsFlags_FlypointFlagAction` in pokemon_talk.c and phone_scripts_childhood_friend.c")
INDIRECT[0x4036] = ("map event key 0, Mahogany Town antenna tree removed: holds a magic number when set "
                    "(`mapeventkeyaction(0, 1)` in TeamRocketHeadquarters_B2F; read by "
                    "`Save_VarsFlags_CheckMapEventKey` in src/field_warp_tasks.c)")
INDIRECT[0x4037] = ("map event key 1, Lake of Rage water level and weather: set or cleared on every warp by "
                    "`ShouldUseAlternateLakeOfRage` (src/map_matrix.c)")
INDIRECT[0x4043] = ("event key 0, Enigma Stone Mystery Gift received: holds a magic number when set "
                    "(src/scrcmd_mystery_gift.c; `checkeventkey(0, ...)` in Pewter scripts)")


# What the C-side ones do, from reading their callers. (True = flag, value): text.
NOTES = {
    (True, 0x0EF): "Pokéathlon: holds every course record (set in `PokeathlonCourse_SaveResults`); 0x0EF-0x0F1 together set `allGoalsMet`",
    (True, 0x0F0): "Pokéathlon: one Pokémon has every medal (set in `PokeathlonCourse_SaveResults`)",
    (True, 0x0F1): "Pokéathlon: beat every event target on a solo course; also a Trainer Card star (src/trainer_card_data.c)",
    (True, 0x184): "Trainer Card star; set when Lyra gives the Shiny Leaf crown",
    (True, 0x960): "set at new game (`NewGame_InitSaveData`); script commands CheckFlagUnk960 and SetFlagUnk960 exist but no script uses them",
    (True, 0x966): "continue at the saved dynamic warp: set when saving after a link error, at game clear and when leaving the Frontier; cleared when continuing (src/field_warp_tasks.c)",
    (True, 0x96A): "Olivine Lighthouse Ampharos healed: switches the area lighting (src/field/fieldmap.c) and Irwin's call",
    (True, 0x970): "set after using the Wi-Fi Club with a Wi-Fi profile; nothing reads it",
    (True, 0x972): "cleared on every warp (src/field_warp_state.c); nothing sets or reads it",
    (True, 0x975): "set and cleared by script commands SetFlagUnk975/ClearFlagUnk975; nothing reads it",
    (True, 0x97B): "base of the rematch tier flags; tier 0 returns before the check, so this one is never read",
    (True, 0x982): "Pokéathlon unlocked: the summary screen shows Pokéathlon stats (`PokemonSummary_IsPokeathlonUnlocked`)",
    (True, 0x994): "Cerulean Gym plays the Team Rocket theme while set (`sMusicOverrideMap`); nothing sets it",
    (True, 0x995): "Route 24 plays the Team Rocket theme while set (`sMusicOverrideMap`); nothing sets it",
    (True, 0x996): "Bug-Catching Contest in progress: contest encounters and battles, phone (`Save_VarsFlags_CheckBugContestFlag`)",
    (True, 0x997): "allows Apricorn Box mode 1 (`ApricornBox_LaunchApp`)",
    (True, 0x998): "Irwin has news: set by badge and story scripts, cleared by `PhoneCall_Irwin_GetProgressScriptId` when he calls",
    (True, 0x999): "Pal Park plays the Safari theme while set (`sMusicOverrideMap`); only ever cleared",
    (True, 0x99A): "keeps the map music instead of the surf/bike theme (src/field_bgm.c, player_avatar_actions.c); set in Lugia's cave, cleared on warp",
    (True, 0x99C): "a following Pokémon has given a Shiny Leaf (src/field/follow_mon_interaction.c); nothing reads it",
    (True, 0x99D): "Safari Zone areas were changed in the area customizer (`ChangeFlag99D`)",
    (True, 0x99F): "Irwin has called about the Lighthouse (after FLAG_UNK_96A)",
    (True, 0x9A0): "Irwin has called about the Rocket Hideout being cleared",
    (True, 0x9A1): "Irwin has called about FLAG_UNK_087",
    (True, 0x9A2): "Irwin has called about meeting Snorlax",
    (True, 0x9A3): "Irwin has called about the Marsh Badge",
    (True, 0x9A4): "Irwin has called about 16 badges",
    (True, 0x9A5): "Irwin has called about the game being cleared",
    (False, 0x4041): "only accessed by script commands GetVar4041/RandomizeVar4041, which no script uses",
    (False, 0x4042): "counts Poké Mart purchases (src/overlay_03/shop_menu.c); read only by script command CheckVar4042AtLeast5, which no script uses",
    (False, 0x404C): "set once an event Arceus arrives (Mystery Gift, GTS, trade); only read to avoid setting it twice",
    (False, 0x4052): "Frontier link multi: partner has a win streak (written by Frontier script 10, read by each facility's setup)",
    (False, 0x4057): "Baoba / Safari Zone progress stage: Baoba's phone calls and the Safari Zone gate scripts",
}

# Referenced, but nothing reads them in a way that matters; listed with the write-only ones.
DEAD = {key for key, text in NOTES.items()
        if "nothing reads it" in text or "never read" in text or "no script uses" in text
        or "nothing sets or reads" in text or "only read to avoid" in text}


def defines(path, prefix):
    out = {}
    for name, value in re.findall(r"#define\s+(%s\w+)\s+(0x[0-9a-fA-F]+|\d+)\b" % prefix,
                                  open(os.path.join(ROOT, path)).read()):
        out[name] = int(value, 0)
    return out


def source_files():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                           check=True).stdout.split()
    return [f for f in files if f.endswith(SOURCE_EXT) and not f.startswith("docs/")
            and f not in (FLAGS_H, VARS_H)]


def narc_members(path):
    d = open(os.path.join(ROOT, path), "rb").read()
    n = struct.unpack_from("<I", d, 0x18)[0]
    fat = [struct.unpack_from("<II", d, 0x1C + 8 * i) for i in range(n)]
    p = 0x1C + 8 * n
    img = p + struct.unpack_from("<I", d, p + 4)[0] + 8
    return d, [(img + start, img + end) for start, end in fat]


def frontier_var_refs():
    """Save vars named by number in the compiled Frontier scripts. The scripts
    aren't disassembled, so this matches opcode + var id pairs anywhere."""
    d, members = narc_members(FRONTIER_SCRIPTS)
    out = collections.defaultdict(set)
    for i, (start, end) in enumerate(members):
        for o in range(start, end - 3):
            op, var = struct.unpack_from("<HH", d, o)
            if op in (FRONTIER_SET_SAVE_VAR, FRONTIER_GET_SAVE_VAR) and 0x4000 <= var < 0x4170:
                out[var].add(("set" if op == FRONTIER_SET_SAVE_VAR else "check", i))
    return out


def follow_mon_flags():
    d, members = narc_members(FOLLOW_MON_RULES)
    out = collections.Counter()
    for start, end in members:
        for o in range(start, end, 20):
            flag = struct.unpack_from("<H", d, o + 18)[0]
            if flag:
                out[flag] += 1
    return out


# C calls that take a flag or var id; a number literal there is a reference too
# (src/trainer_card_data.c checks flags 0xF1 and 0x184 this way).
C_ID_CALL = re.compile(
    r"\b(\w*(?:FlagInArray|FlagAddr|ScriptFlag|FieldSystem_Flag(?:Set|Clear|Check)"
    r"|ScriptVar|VarAddr|FieldSystem_Var(?:Get|Set)|GetVarPointer))\s*\([^;()]*?,\s*"
    r"(0x[0-9A-Fa-f]+|\d+)\s*[,)]")


def c_literal_refs():
    out = collections.defaultdict(list)
    for f in source_files():
        if not f.endswith(".c"):
            continue
        for m in C_ID_CALL.finditer(open(os.path.join(ROOT, f), errors="ignore").read()):
            is_flag = "Flag" in m.group(1)
            out[(is_flag, int(m.group(2), 0))].append((f, m.group(1)))
    return out


class Ref:
    def __init__(self, kind, where, op, value=None):
        self.kind = kind    # "map" (scripts.pory / map.json), "std" (scr_seq), "c"
        self.where = where  # map name, scr_seq file or C file
        self.op = op        # set, clear, check, hide, trigger, other
        self.value = value


SCRIPT_OPS = {
    "setflag": "set", "clearflag": "clear", "flag": "check", "callifset": "check",
    "callifunset": "check", "SetFlag": "set", "ClearFlag": "clear", "CheckFlag": "check",
    "CallIfSet": "check", "CallIfUnset": "check", "GoToIfSet": "check", "GoToIfUnset": "check",
    "setvar": "set", "SetVar": "set", "addvar": "set", "AddVar": "set", "random": "set",
    "var": "check", "compare": "check", "Compare": "check", "Switch": "check",
    "copyvar": "other", "CopyVar": "other",
}
WRITES = {"set", "clear"}
MAX_LISTED = 4


def scan(names):
    pat = re.compile(r"\b(%s)\b" % "|".join(sorted(names, key=len, reverse=True)))
    refs = collections.defaultdict(list)
    for f in source_files():
        try:
            text = open(os.path.join(ROOT, f), errors="ignore").read()
        except OSError:
            continue
        if not pat.search(text):
            continue
        m = re.match(r"data/maps/([^/]+)/", f)
        if m:
            kind, where = "map", m.group(1)
        elif f.startswith("files/fielddata/script/scr_seq/"):
            kind, where = "std", os.path.splitext(os.path.basename(f))[0]
        else:
            kind, where = "c", f
        if m and f.endswith("/map.json"):
            data = json.loads(text)
            for obj in data.get("object_events", []):
                if obj.get("flag") in names:
                    r = Ref(kind, where, "hide")
                    script = obj.get("script")
                    r.context = script if isinstance(script, str) else obj.get("local_id")
                    refs[obj["flag"]].append(r)
            for ev in data.get("coord_events", []):
                if ev.get("var") in names:
                    r = Ref(kind, where, "trigger", ev.get("var_value"))
                    r.context = ev.get("script")
                    refs[ev["var"]].append(r)
            continue
        context = None
        for line in text.splitlines():
            # in scripts.pory, _XXXX: labels are local to the enclosing script
            c = (re.match(r"(?:script|mapscripts|movement)\s+(\w+)", line)
                 or (not f.endswith(".pory") and re.match(r"(\w+):\s*$", line))
                 or re.match(r"(?:static\s+)?[A-Za-z_][\w \*]*?\b(\w+)\s*\([^;]*\)\s*\{?\s*$", line)
                 or re.match(r"(?:static\s+)?const\s+[\w ]+?\b(\w+)\s*\[", line))
            if c and not line.startswith((" ", "\t")):
                context = c.group(1)
            for nm in pat.finditer(line):
                name = nm.group(1)
                op, value = "other", None
                before = line[:nm.start()]
                cmd = re.search(r"(\w+)\s*\(?\s*(?:[\w ]+,\s*)?$", before)
                if cmd and cmd.group(1) in SCRIPT_OPS:
                    op = SCRIPT_OPS[cmd.group(1)]
                    v = re.match(r"\s*[,)]?\s*(?:==|!=|>=|<=|<|>|,)\s*(\d+|0x[0-9A-Fa-f]+)", line[nm.end():])
                    if v:
                        value = int(v.group(1), 0)
                elif re.match(r"\s*,\s*\d+\s*:", line[nm.end():]):
                    op = "check"   # mapscripts frame/transition table entry
                    value = int(re.match(r"\s*,\s*(\d+)", line[nm.end():]).group(1))
                r = Ref(kind, where, op, value)
                r.context = context
                refs[name].append(r)
    return refs


class Entry:
    def __init__(self, name, value, is_flag):
        self.name, self.value, self.is_flag = name, value, is_flag
        self.refs = []
        self.indirect = None
        self.follow = 0
        self.aliases = []

    @property
    def used(self):
        return bool(self.refs or self.indirect or self.follow)

    @property
    def write_only(self):
        if (self.is_flag, self.value) in DEAD:
            return True
        if not self.refs or self.indirect or self.follow:
            return False
        return all(r.op in WRITES for r in self.refs)


def collect():
    flags = defines(FLAGS_H, "FLAG_")
    vars_ = defines(VARS_H, "VAR_")
    unk = {n: v for n, v in list(flags.items()) + list(vars_.items()) if "_UNK_" in n}
    # every name sharing a value with an UNK name, so aliases count
    by_value = collections.defaultdict(list)
    for table in (flags, vars_):
        for n, v in table.items():
            by_value[(table is flags, v)].append(n)
    wanted = {n for n, v in unk.items() for n in by_value[(n.startswith("FLAG_"), v)]}
    refs = scan(wanted)
    follow = follow_mon_flags()
    literals = c_literal_refs()
    frontier = frontier_var_refs()
    entries = []
    for name, value in sorted(unk.items(), key=lambda kv: (not kv[0].startswith("FLAG_"), kv[1])):
        is_flag = name.startswith("FLAG_")
        e = Entry(name, value, is_flag)
        for other in by_value[(is_flag, value)]:
            e.refs += refs.get(other, [])
            if other != name:
                e.aliases.append(other)
        for f, func in literals.get((is_flag, value), []):
            r = Ref("c", f, "other")
            r.context = "%s(0x%X)" % (func, value)
            e.refs.append(r)
        if not is_flag:
            for op, member in sorted(frontier.get(value, ())):
                r = Ref("std", "Frontier script %d (%s)" % (member, FRONTIER_SCRIPTS), op)
                e.refs.append(r)
        e.indirect = INDIRECT.get(value)
        e.follow = follow.get(value, 0) if is_flag else 0
        entries.append(e)
    # an UNK alias of a used named constant is not an entry of its own
    return [e for e in entries if not any("_UNK_" not in a for a in e.aliases)] , \
           [e for e in entries if any("_UNK_" not in a for a in e.aliases)]


def ranges(values):
    out = []
    for v in sorted(values):
        if out and v == out[-1][1] + 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return out


def grouped(spans, note):
    out = []
    for a, b in spans:
        n = note(a, b)
        if out and out[-1][1] == n:
            out[-1][0].append((a, b))
        else:
            out.append(([(a, b)], n))
    return out


def fmt_range(a, b, width):
    f = "0x%%0%dX" % width
    return f % a if a == b else (f % a) + "-" + (f % b)


def nice_map(name):
    return name.replace("_", " ")


def describe(e):
    parts = []
    if (e.is_flag, e.value) in NOTES:
        parts.append(NOTES[(e.is_flag, e.value)])
    if e.indirect:
        parts.append(e.indirect)
    if e.follow:
        parts.append("required by %d following-Pokémon interaction rule%s (`%s`)"
                     % (e.follow, "s" if e.follow > 1 else "", FOLLOW_MON_RULES))
    ops = collections.OrderedDict()
    values = collections.defaultdict(set)
    c_funcs = collections.OrderedDict()
    for r in e.refs:
        if r.kind == "c":
            c_funcs.setdefault("`%s` (%s)" % (r.context, r.where) if r.context else r.where, None)
            continue
        if r.kind == "map":
            who = "`%s`" % r.context if r.context else nice_map(r.where)
        else:
            who = "`%s`" % r.where
        ops.setdefault(r.op, collections.OrderedDict()).setdefault(who, None)
        if r.value is not None:
            values[r.op].add(r.value)
    labels = {"hide": "hides the object run by", "set": "set by" if e.is_flag else "written by",
              "clear": "cleared by", "check": "checked by", "trigger": "gates coord trigger",
              "other": "used by"}
    for op in ("hide", "set", "clear", "check", "trigger", "other"):
        if op in ops:
            who = list(ops[op])
            text = "%s %s" % (labels[op], ", ".join(who[:MAX_LISTED]))
            if len(who) > MAX_LISTED:
                text += " and %d more" % (len(who) - MAX_LISTED)
            if values.get(op):
                text += " (%s)" % ", ".join(str(v) for v in sorted(values[op]))
            parts.append(text)
    if c_funcs:
        parts.append("C: " + ", ".join(c_funcs))
    return "; ".join(parts)


def markdown(entries, aliased):
    flags = [e for e in entries if e.is_flag]
    vars_ = [e for e in entries if not e.is_flag]
    w = print
    w("<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->")
    w("<!-- Generated by tools/flagusage/flagusage.py --markdown; edit the tool, not this file. -->")
    w()
    w("# Unnamed flags and vars")
    w()
    w("> AI-generated, local to this fork. Do not upstream.")
    w()
    for label, group, width in (("Flags", flags, 3), ("Vars", vars_, 4)):
        free = [e for e in group if not e.used]
        wo = [e for e in group if e.write_only]
        w("- **%s:** %d `%s_UNK_*`: **%d never referenced**, %d referenced but never read"
          " (write-only), %d in use."
          % (label, len(group), "FLAG" if label == "Flags" else "VAR",
             len(free), len(wo), len(group) - len(free) - len(wo)))
    if aliased:
        w("- Not counted: %s, old names kept as aliases of named constants."
          % ", ".join("`%s`" % e.name for e in aliased))
    w()
    w("## How this was checked")
    w()
    w("A flag or var is **used** if any name with its value appears in a script")
    w("(`data/maps/*/scripts.pory`, `files/fielddata/script/scr_seq/*.s`), a `map.json`,")
    w("C or assembly. Names are not the only way in, so these were also checked:")
    w()
    w("- C that adds an offset to a base (`FLAG_UNK_97B + n`, `VAR_UNK_4036 + key`, ...);")
    w("  the values it can reach count as used (listed in `INDIRECT` in the tool).")
    w("- Following-Pokémon interaction rules (`files/a/2/2/0`), which store flag numbers.")
    w("- Script commands that take a flag number from a var (`SetFlagVar`,")
    w("  `ClearFlagVar`, `CheckFlagVar`): the three std scripts that use them loop over")
    w("  named ranges (Bug Contest contestants, Trainer House, item balls).")
    w("- Ranges the engine handles as a block: map-temporary flags `0x00`-`0x3F` and")
    w("  temp vars are cleared on every warp, daily flags `0xAA0`-`0xB5F` at midnight,")
    w("  trainer flags are `0x550` + trainer id, hidden items `0x320` + index.")
    w()
    w("**Write-only** entries are set or cleared but nothing reads them (or only a")
    w("script command no script uses does), so they do nothing. They can be reused")
    w("after removing the writes.")
    w()
    w("Regenerate after renaming or reusing any of these:")
    w("`python3 tools/flagusage/flagusage.py --markdown > docs/modding/unknown-flags-vars.md`.")
    w()
    w("## Free flags")
    w()
    w("Grouped by the area of `include/constants/flags.h` they sit in. Where a")
    w("block borders an engine range, using it is safe only while that range does not grow.")
    w()
    w("| Flags | Count | Notes |")
    w("|---|---:|---|")
    for spans, note in grouped(ranges(e.value for e in flags if not e.used), flag_area):
        w("| %s | %d | %s |" % (", ".join("`%s`" % fmt_range(a, b, 3) for a, b in spans),
                                sum(b - a + 1 for a, b in spans), note))
    w()
    w("## Free vars")
    w()
    w("| Vars | Count | Notes |")
    w("|---|---:|---|")
    for spans, note in grouped(ranges(e.value for e in vars_ if not e.used), var_area):
        w("| %s | %d | %s |" % (", ".join("`%s`" % fmt_range(a, b, 4) for a, b in spans),
                                sum(b - a + 1 for a, b in spans), note))
    for label, group in (("flags", flags), ("vars", vars_)):
        wo = [e for e in group if e.write_only]
        w()
        w("## Write-only %s" % label)
        w()
        if not wo:
            w("None.")
            continue
        w("| Name | Notes |")
        w("|---|---|")
        for e in wo:
            w("| `%s` | %s |" % (e.name, describe(e)))
    for label, group in (("flags", flags), ("vars", vars_)):
        w()
        w("## Used %s" % label)
        w()
        w("Names of objects and scripts usually say what the %s is for. \"Hides\" means the"
          % label[:-1] if label == "flags" else
          "Values are those scripts write or compare against.")
        if label == "flags":
            w("object is not shown while the flag is set.")
        w()
        w("| Name | What uses it |")
        w("|---|---|")
        for e in group:
            if e.used and not e.write_only:
                w("| `%s` | %s |" % (e.name, describe(e)))


def flag_area(a, b):
    if b < 0x40:
        return "map-temporary (cleared on warp)"
    if a == 0x40:
        return "just past the map-temporary flags; not cleared on warp"
    if a < 0x320:
        return "story/event and hide flags"
    if a < 0x407:
        return "hidden items"
    if a < 0x420:
        return "after the 231 hidden-item flags (`0x320` + index): taken if hidden items are added"
    if a < 0x550:
        return "item-ball and event flags" if b < 0x51F else "just below `TRAINER_FLAG_BASE`"
    if a < 0x960:
        return "trainer range past the last trainer (0x550 + 737 = 0x821): taken if trainers are added"
    if 0x9B0 <= a <= 0x9D5:
        return ("fly point %d (`FLAG_SYS_FLYPOINT_PALLET` + n): no spawn point in src/spawn_warp.c "
                "has it and nothing checks it" % (a - 0x9B0))
    if a < 0xAA0:
        return "system flags"
    return "daily flags: cleared every day, so only usable as once-a-day flags"


def var_area(a, b):
    if a >= 0x4152:
        return "end of the saved vars (`NUM_VARS` = 0x170 -> last is 0x416F)"
    return "persistent var"


def main():
    entries, aliased = collect()
    if "--markdown" in sys.argv:
        markdown(entries, aliased)
        return
    if "--free" in sys.argv:
        for label, is_flag, width in (("flags", True, 3), ("vars", False, 4)):
            vals = [e.value for e in entries if e.is_flag == is_flag and not e.used]
            print("free %s (%d): %s" % (label, len(vals),
                  " ".join(fmt_range(a, b, width) for a, b in ranges(vals))))
        return
    for label, is_flag in (("FLAG_UNK", True), ("VAR_UNK", False)):
        group = [e for e in entries if e.is_flag == is_flag]
        print("%s: %d total, %d never referenced, %d write-only, %d in use" % (
            label, len(group), sum(not e.used for e in group), sum(e.write_only for e in group),
            sum(e.used and not e.write_only for e in group)))
    if aliased:
        print("aliases of named constants (not counted): " + " ".join(e.name for e in aliased))


if __name__ == "__main__":
    main()
