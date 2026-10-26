#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25
"""List every script command: its number, macro, arguments, C function and uses.

    python3 tools/scriptcmds/scriptcmds.py                 # summary
    python3 tools/scriptcmds/scriptcmds.py --find give     # commands whose name contains "give"
    python3 tools/scriptcmds/scriptcmds.py --markdown > docs/modding/script-commands-list.md

Reads asm/macros/script.inc (macros and their comments), gScriptCmdTable in
src/data/fieldmap/script_cmd_table.h (number -> C function), the ScrCmd_*
definitions under src/, include/constants/std_script.h, and counts direct uses
in data/maps/*/scripts.pory and files/fielddata/script/scr_seq/*.s.
docs/modding/script-commands.md explains the results.
"""

import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MACROS = "asm/macros/script.inc"
TABLE = "src/data/fieldmap/script_cmd_table.h"
STD = "include/constants/std_script.h"
CONFIG = "tools/mapkit/script_config.json"
PORY_GLOB = "data/maps/*/scripts.pory"
ASM_GLOB = "files/fielddata/script/scr_seq/*.s"

# Groups for the list, by words in the macro name; first match wins. A guide, not
# a classification: check the C function before relying on one.
GROUPS = [
    ("Script flow and waiting", r"^(Noop|Dummy|End|Wait|Return|Call|GoTo|RunScript|CallStd|RestartCurrentScript|ObjectGoTo|BGGoTo|DirectionGoTo|ScrDef|LockAll|ReleaseAll|Lock|Release|WaitFrames|CallIf|GoToIf)"),
    ("Flags, vars and comparisons", r"Flag|Var|Compare|LoadByte|LoadWord|CopyLocal|CopyByte|SetPtr|WriteByte|Random|Add\b|Sub\b"),
    ("Text and messages", r"Msg|Message|Text|Print|Signpost|TrainerTips|Window|Talk|Textbox|NPC"),
    ("String buffers", r"^Buffer|String|Strbuf|Nickname|Name"),
    ("Menus and choices", r"Menu|Multi|YesNo|Choice|List|Touchscreen"),
    ("Objects and movement", r"Movement|Person|Object|Obj|Follow|Facing|Face|Player|Camera|Position|Coord|Elevation|Warp|Teleport|Door"),
    ("Items, bag and money", r"Item|Bag|Money|Coin|Mart|Berry|Apricorn|Point|Prize|Shard|Fossil|Mail|Accessor|Seal|Gift"),
    ("Pokémon and party", r"Mon|Party|Poke|Egg|Daycare|Species|Move|Tutor|Relearn|Form|Shaymin|Unown|Dex|Friendship|Ribbon|Nature|Ability|Hatch|Evolv|Trade|Pokedex|Box|PC"),
    ("Battles and trainers", r"Battle|Trainer|Wild|Encounter|Rematch|Frontier|Hall|Castle|Arcade|Factory|Tower|Safari|Contest|Roamer"),
    ("Sound and music", r"Sound|Music|Song|BGM|SE\b|Fanfare|Cry|Play|Fade.*Music|Volume|Radio"),
    ("Screen, fades and effects", r"Fade|Screen|Flash|Shake|Anim|Effect|Brightness|Weather|Window|Scroll|Overworld|Pic|Sprite|Display"),
    ("Pokégear, phone and calendar", r"Gear|Phone|Call|Time|Day|Clock|RTC|Calendar|Map"),
    ("Saving, link and system", r"Save|Link|Wifi|WiFi|Comm|Union|Wireless|Record|Game|Stat|Version|System|Sys|Gts|Mystery"),
    ("Player progress", r"Badge|RunningShoes|Starter|HOF|Credits|Trcard|Escort|Avatar|Gender|Profile"),
    ("Gyms, puzzles and set pieces", r"Gym|Alph|Puzzle|Legend|Cutscene|Cinematic|Ecruteak|Azalea|Cianwood|Blackthorn|Fuchsia|Vermilion|Mystri|Primo|Buenas|Kenya|Lati|PalPark|Scratch|Loto|Photo|Cameron|Defog|RockClimb|Bank|Swarm|Outbreak|Pokeathlon|Athlete|Dress|Fashion|Mailbox|Wallpaper|Background"),
]


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def parse_macros():
    """Return a list of dicts: name, params, opcode (or None), comment, body_cmds."""
    macros = []
    comment = []
    lines = read(MACROS).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r"\.macro\s+(\w+)\s*(.*)$", line)
        if m:
            name, params = m.group(1), m.group(2).split("//")[0].strip()
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != ".endm":
                body.append(lines[i].strip())
                i += 1
            opcode = None
            for b in body:
                if not b or b.startswith("//"):
                    continue
                om = re.match(r"\.short\s+(\d+)\s*$", b)
                if om:
                    opcode = int(om.group(1))
                break
            cmds = []
            for b in body:
                w = re.match(r"([A-Za-z_]\w*)\b", b)
                if w and not b.startswith(".") and w.group(1) not in cmds:
                    cmds.append(w.group(1))
            macros.append({
                "name": name,
                "params": [p.strip() for p in params.split(",") if p.strip()],
                "opcode": opcode,
                "comment": " ".join(c.lstrip("/ ").strip() for c in comment).strip(),
                "body_cmds": cmds,
            })
            comment = []
        elif line.startswith("//"):
            comment.append(line)
        elif line:
            comment = []
        i += 1
    return macros


def parse_table():
    text = read(TABLE)
    body = text[text.index("gScriptCmdTable[] = {"):]
    body = body[body.index("{") + 1:body.index("};")]
    return re.findall(r"^\s*(\w+),", body, re.M)


READS = {
    "ScriptGetVarPointer": "var",     # a variable the command writes (or reads by address)
    "ScriptGetVar": "val",            # a number below 0x4000, or a variable's value
    "ScriptReadHalfword": "u16",      # a fixed number; a variable name here is its id, not its value
    "ScriptReadByte": "u8",
    "ScriptReadWord": "u32",          # a fixed 32-bit number, or a jump target
}


def find_functions():
    """function name -> (file, line, [argument kinds in the order the body reads them])."""
    found = {}
    for path in glob.glob(os.path.join(ROOT, "src/**/*.c"), recursive=True):
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        for n, line in enumerate(lines, 1):
            m = re.match(r"(?:static\s+)?BOOL\s+(\w+)\s*\(\s*ScriptContext\s*\*", line)
            if m and line.split("//")[0].rstrip().endswith("{") and m.group(1) not in found:
                body = []
                for b in lines[n:]:
                    if b.startswith("}"):
                        break
                    body.append(b.split("//")[0])
                kinds = [READS[r] for r in re.findall(r"\b(ScriptGetVarPointer|ScriptGetVar|ScriptReadHalfword|ScriptReadByte|ScriptReadWord)\s*\(", "\n".join(body))]
                found[m.group(1)] = (rel, n, kinds)
    return found


def count_uses():
    pory = collections.Counter()
    for path in glob.glob(os.path.join(ROOT, PORY_GLOB)):
        with open(path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s.startswith("//") or s.startswith("#"):
                    continue
                for w in re.findall(r"([A-Za-z_]\w*)\s*\(", s):
                    pory[w.lower()] += 1
                m = re.match(r"([A-Za-z_]\w*)\s*$", s)
                if m:
                    pory[m.group(1).lower()] += 1
    asm = collections.Counter()
    for path in glob.glob(os.path.join(ROOT, ASM_GLOB)):
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s+([A-Za-z_]\w*)\b", line)
                if m:
                    asm[m.group(1)] += 1
    return pory, asm


def parse_std():
    out = []
    for m in re.finditer(r"^#define\s+(std_\w+)\s+(\d+)\s*$", read(STD), re.M):
        out.append((m.group(1), int(m.group(2))))
    return out


def group_of(name):
    for title, pattern in GROUPS:
        if re.search(pattern, name):
            return title
    return "Other"


def build():
    macros = parse_macros()
    table = parse_table()
    funcs = find_functions()
    pory, asm = count_uses()
    aliases = json.loads(read(CONFIG)).get("command_aliases", {})
    alias_of = collections.defaultdict(list)
    for short, target in aliases.items():
        alias_of[target].append(short)

    def uses(name):
        n = pory[name.lower()] + asm[name]
        for a in alias_of.get(name, []):
            n += pory[a.lower()]
        return n

    by_op = collections.defaultdict(list)
    composites = []
    for m in macros:
        if m["opcode"] is not None:
            by_op[m["opcode"]].append(m)
        else:
            composites.append(m)
    commands = []
    for op, func in enumerate(table):
        # Descriptive names first; placeholders such as ScrCmd_048 last.
        ms = sorted(by_op.get(op, []), key=lambda m: bool(re.match(r"ScrCmd_\d+$", m["name"])))
        names = [m["name"] for m in ms]
        primary = next((m for m in ms if m["params"]), ms[0] if ms else None)
        info = funcs.get(func)
        commands.append({
            "opcode": op,
            "func": func,
            "where": info[:2] if info else None,
            "kinds": info[2] if info else [],
            "names": names,
            "params": primary["params"] if primary else [],
            "comment": next((m["comment"] for m in ms if m["comment"]), ""),
            "aliases": [a for n in names for a in alias_of.get(n, [])],
            "uses": sum(uses(n) for n in names),
            "group": group_of(names[0] if names else func.replace("ScrCmd_", "")),
        })
    for m in composites:
        m["uses"] = uses(m["name"])
    std = [(name, value, pory[name.lower()] + sum(1 for _ in ())) for name, value in parse_std()]
    return commands, composites, std


def std_uses():
    counts = collections.Counter()
    files = glob.glob(os.path.join(ROOT, PORY_GLOB)) + glob.glob(os.path.join(ROOT, ASM_GLOB))
    for path in files:
        with open(path, encoding="utf-8") as f:
            for w in re.findall(r"\b(std_\w+)", f.read()):
                counts[w] += 1
    return counts


def md_escape(s):
    return s.replace("|", "\\|")


def markdown(commands, composites, std):
    out = []
    w = out.append
    w("<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->")
    w("<!-- Generated by tools/scriptcmds/scriptcmds.py --markdown; edit the tool, not this file. -->")
    w("")
    w("# Script command list")
    w("")
    w("> AI-generated; not affiliated with pret. See AI.md at the repository root.")
    w("")
    w("Every script command, generated from `asm/macros/script.inc` and `gScriptCmdTable`. "
      "[script-commands.md](script-commands.md) explains how commands work and picks out the useful ones.")
    w("")
    named = sum(1 for c in commands if c["names"])
    w("- **%d commands** (numbers 0-%d); %d have a macro, %d have a comment in `script.inc`." %
      (len(commands), len(commands) - 1, named, sum(1 for c in commands if c["comment"])))
    w("- **%d helper macros** that expand to several commands (at the end)." % len(composites))
    w("- **Uses** counts direct uses in `data/maps/*/scripts.pory` and `files/fielddata/script/scr_seq/*.s`, "
      "by macro name, lowercased name or pokeemerald alias. Commands that `if`, `while` and the other "
      "control-flow forms generate (`GoToIf`, `CompareVarToValue`...) are mostly not counted.")
    w("- **Read as** is how the C function reads each argument, in the order it reads them: "
      "`val` = a number below 0x4000 or a variable (its value is used); `var` = a variable the command "
      "writes or reads by name; `u8`/`u16`/`u32` = a fixed number (a variable name there is taken as "
      "its id, not its value). Empty when the arguments are read by a helper function.")
    w("- **Group** is a guess from the name. The C function is the authority.")
    w("- In a `.pory` file, write a command lowercased (`lockall`) or as its macro (`LockAll`); "
      "arguments in parentheses, in the order shown.")
    w("")
    groups = collections.OrderedDict((g, []) for g, _ in GROUPS)
    groups["Other"] = []
    for c in commands:
        groups[c["group"]].append(c)
    w("## Groups")
    w("")
    for g, cs in groups.items():
        anchor = re.sub(r"[^\w -]", "", g.lower()).replace(" ", "-")
        w("- [%s](#%s) (%d)" % (g, anchor, len(cs)))
    w("")
    for g, cs in groups.items():
        w("## %s" % g)
        w("")
        w("| # | Command | Arguments | Read as | Uses | C function | Notes |")
        w("|---|---|---|---|---|---|---|")
        for c in sorted(cs, key=lambda c: (c["names"][0] if c["names"] else c["func"]).lower()):
            name = " / ".join("`%s`" % n for n in c["names"]) if c["names"] else "*(no macro)*"
            if c["aliases"]:
                name += " (alias %s)" % ", ".join("`%s`" % a for a in c["aliases"])
            where = ""
            if c["where"]:
                where = "`%s` ([%s:%d](../../%s#L%d))" % (c["func"], os.path.basename(c["where"][0]), c["where"][1], c["where"][0], c["where"][1])
            else:
                where = "`%s`" % c["func"]
            params = ", ".join(c["params"])
            kinds = " ".join(c["kinds"])
            w("| %d | %s | %s | %s | %d | %s | %s |" % (c["opcode"], name, md_escape(params), kinds, c["uses"], where, md_escape(c["comment"])))
        w("")
    w("## Helper macros")
    w("")
    w("These aren't commands: each expands to the commands listed.")
    w("")
    w("| Macro | Arguments | Expands to | Uses | Notes |")
    w("|---|---|---|---|---|")
    for m in sorted(composites, key=lambda m: m["name"].lower()):
        if m["name"].startswith(("Scr", "_")):
            continue
        w("| `%s` | %s | %s | %d | %s |" % (m["name"], md_escape(", ".join(m["params"])),
                                          ", ".join("`%s`" % c for c in m["body_cmds"][:6]), m["uses"], md_escape(m["comment"])))
    w("")
    counts = std_uses()
    w("## Standard scripts (`CallStd`)")
    w("")
    w("`CallStd std_x` runs a shared script and waits for it (`include/constants/std_script.h`). "
      "Only the named ones in the 2000-2999 range are listed; trainer, item-ball and hidden-item ids are "
      "computed per trainer or item.")
    w("")
    w("| Id | Name | Uses |")
    w("|---|---|---|")
    for name, value in std:
        if 2000 <= value < 3000:
            w("| %d | `%s` | %d |" % (value, name, counts[name]))
    w("")
    return "\n".join(out)


def main(argv):
    commands, composites, std = build()
    std = [(n, v) for n, v, _ in std]
    if "--markdown" in argv:
        print(markdown(commands, composites, std))
        return
    if "--find" in argv:
        needle = argv[argv.index("--find") + 1].lower()
        for c in commands:
            label = c["names"][0] if c["names"] else c["func"]
            if needle in label.lower() or needle in c["func"].lower():
                where = "%s:%d" % c["where"] if c["where"] else "?"
                print("%4d  %-36s %-40s [%s] uses %4d  %s" % (c["opcode"], label, ", ".join(c["params"]), " ".join(c["kinds"]), c["uses"], where))
        return
    named = sum(1 for c in commands if c["names"])
    unused = [c for c in commands if c["names"] and c["uses"] == 0]
    print("%d commands, %d with a macro, %d never used directly in map scripts; %d helper macros; %d std ids" %
          (len(commands), named, len(unused), len(composites), len(std)))


if __name__ == "__main__":
    main(sys.argv[1:])
