# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""poryscript-style map scripts for HGSS: data/maps/<Map>/scripts.pory.

    compile_map(repo, entry)  -> Result (scripts.inc, map_scripts.inc, texts, script order)
    build(repo, entry, out)   -> writes the build inputs under their original bank names
    init(repo, map)           -> converts a map's .inc files to scripts.pory (ROM unchanged)
    sync_ids(repo, map)       -> rewrites the _EV_ block of ids.h from the script order
"""

import json
import os
import re
import subprocess

from .. import layout, scripts
from . import compiler, decompile
from .compiler import CompileError, compile_source, text_entry  # noqa: F401
from .parser import PoryError  # noqa: F401

PORY = "scripts.pory"


def pory_path(root, entry):
    return os.path.join(root, layout.MAPS_DIR, entry["dir"], PORY)


def context(repo, entry, macros=None):
    index = list(repo.migrated.values()) if hasattr(repo, "migrated") else layout.read_index(repo.root)
    ids = os.path.join(repo.root, layout.MAPS_DIR, entry["dir"], "ids.h")
    text_base = layout.resolve(index, entry, "msgBank")[1]
    if macros is None:
        macros = scripts.MacroTable()
        macros.load(os.path.join(repo.root, "asm/macros/script.inc"), "script")
        macros.load(os.path.join(repo.root, "asm/macros/movement.inc"), "movement")
    return compiler.Context(macros, compiler.load_config(), layout.ids_include(entry["dir"]) if os.path.exists(ids) else None,
                            "msgdata/msg/%s.h" % text_base, pory_path(repo.root, entry),
                            text_slots(repo.root, entry))


def text_slots(root, entry):
    """{"<Script>#<n>": message id} from the map's text.json (only if the map owns it)."""
    if entry["text"].startswith("@"):
        return {}
    path = os.path.join(root, layout.MAPS_DIR, entry["dir"], "text.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {m["from"]: m["id"] for m in json.load(f)["messages"] if "#" in m.get("from", "")}


def compile_map(repo, entry, switches=None, macros=None):
    path = pory_path(repo.root, entry)
    with open(path, encoding="utf-8") as f:
        src = f.read()
    return compile_source(src, context(repo, entry, macros), switches)


def merged_text(repo, entry, result, unfilled=None, bank=None):
    """The map's text bank: text.json, with the slots marked "from" filled by the .pory
    text of that id (inline strings or text blocks), then new .pory text appended.
    Existing message numbers never change; a slot with no text left becomes an empty
    message (listed in `unfilled`). Only for maps that own their text bank."""
    if bank is None:
        with open(os.path.join(repo.root, layout.MAPS_DIR, entry["dir"], "text.json"), encoding="utf-8") as f:
            bank = json.load(f)
    bank = dict(bank)
    texts = dict(result.texts)
    used = set()
    messages = []
    for m in bank["messages"]:
        if "from" not in m:
            if m.get("id") in texts:
                raise CompileError("text %s is already in text.json" % m["id"], pory_path(repo.root, entry))
            messages.append(m)
            continue
        if m["id"] in texts:
            used.add(m["id"])
            messages.append(text_entry(m["id"], texts[m["id"]]))
        else:
            if unfilled is not None:
                unfilled.append((m["id"], m["from"]))
            messages.append(text_entry(m["id"], ""))
    for tid, value in result.texts:
        if tid not in used:
            messages.append(text_entry(tid, value))
    bank["messages"] = messages
    return bank


def build(repo, entry, out_dir, game="HEARTGOLD"):
    for kind in ("scripts", "init"):
        if entry[kind].startswith("@"):
            raise CompileError("%s uses %s's %s bank; a map with scripts.pory needs its own"
                               % (entry["dir"], entry[kind][1:], kind), pory_path(repo.root, entry))
    r = compile_map(repo, entry, {"GAME": game})
    if entry["text"].startswith("@") and r.texts:
        raise CompileError("%s shares %s's text bank, so its scripts can't add text"
                           % (entry["dir"], entry["text"][1:]), pory_path(repo.root, entry))
    with open(os.path.join(out_dir, entry["scripts"] + ".s"), "w", encoding="utf-8") as f:
        f.write(r.scripts_inc)
    with open(os.path.join(out_dir, entry["init"] + ".s"), "w", encoding="utf-8") as f:
        f.write(r.map_scripts_inc)
    if not entry["text"].startswith("@"):
        with open(os.path.join(out_dir, entry["text"] + ".json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(merged_text(repo, entry, r), indent=2, ensure_ascii=False) + "\n")
    return r


# --- ids.h ---------------------------------------------------------------------

def sync_ids(repo, entry, public):
    """Make ids.h define _EV_<label> = ScrDef index for every script, in order."""
    path = os.path.join(repo.root, layout.MAPS_DIR, entry["dir"], "ids.h")
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    ev = [i for i, l in enumerate(lines) if re.match(r"#define\s+_EV_\w+", l)]
    block = ["#define _EV_%s %d" % (n, i) for i, n in enumerate(public)]
    if ev:
        lines[ev[0]:ev[-1] + 1] = block
    else:
        guard_end = max(i for i, l in enumerate(lines) if l.startswith("#define")) + 1 if any(
            l.startswith("#define") for l in lines) else 0
        lines[guard_end:guard_end] = [""] + block
    new = nl.join(lines)
    if new != text:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        return True
    return False


# --- converting existing maps -------------------------------------------------

_EV_REF = re.compile(r"^_EV_(\w+)\s*\+\s*1$")


def _init_target(expr, public):
    m = _EV_REF.match(expr.strip())
    if m and m.group(1) in public:
        return m.group(1)
    if expr.strip().isdigit() and 1 <= int(expr) <= len(public):
        return public[int(expr) - 1]
    return expr.strip()


def own_includes(repo, entry):
    """The includes the compiler writes itself."""
    text_base = layout.resolve(list(repo.migrated.values()), entry, "msgBank")[1]
    return {"constants/scrcmd.h", "macros/script.inc", layout.ids_include(entry["dir"]),
            "msgdata/msg/%s.h" % text_base}


def init_source(repo, m, raw=False, stats=None):
    """The scripts.pory text `init` would write (nothing is changed). By default the
    scripts are decompiled into structured `script` blocks (pory/decompile.py); with
    raw, scripts.inc goes into one `raw` block unchanged."""
    entry = repo.migrated.get(m.name)
    if entry is None:
        raise CompileError("%s is not in data/maps" % m.name)
    folder = os.path.join(repo.root, layout.MAPS_DIR, entry["dir"])
    for kind, fname in (("scripts", "scripts.inc"), ("init", "map_scripts.inc")):
        if entry[kind].startswith("@"):
            raise CompileError("%s uses %s's %s; only maps with their own banks can use scripts.pory"
                               % (entry["dir"], entry[kind][1:], fname))
    if os.path.exists(os.path.join(folder, PORY)):
        raise CompileError("%s already has scripts.pory" % entry["dir"])
    with open(os.path.join(folder, "scripts.inc"), encoding="utf-8") as f:
        src = f.read().replace("\r\n", "\n")
    # the compiler writes these includes itself
    own = own_includes(repo, entry)
    kept = [l for l in src.split("\n")
            if not (re.match(r'\s*#\s*include\s+"([^"]+)"', l) and re.match(r'\s*#\s*include\s+"([^"]+)"', l).group(1) in own)]
    src = "\n".join(kept).strip("\n")
    if "`" in src:
        raise CompileError("scripts.inc contains a backtick; can't wrap it in raw")
    public = [mm.group(1) for mm in map(compiler._SCRDEF_RE.match, src.splitlines()) if mm]
    if raw:
        scripts_part = ["raw `", src, "`", ""]
    else:
        with open(os.path.join(folder, "scripts.inc"), encoding="utf-8") as f:
            full = f.read()
        dec = decompile.Decompiler(context(repo, entry, repo.macros), entry["dir"], full)
        scripts_part, st = dec.run(own)
        if stats is not None:
            for k, v in st.items():
                stats[k] = stats.get(k, 0) + v

    sf = scripts.parse(os.path.join(folder, "map_scripts.inc"), repo.macros)
    entries, table, table_label = [], [], None
    kinds = {v: k for k, v in compiler.load_config()["init_script_types"].items() if k.startswith("INIT_")}
    for st in sf.statements:
        if st.macro.startswith("InitScriptEntry_") and st.macro != "InitScriptEntryEnd":
            if st.macro == "InitScriptEntry_OnFrameTable":
                table_label = st.args[0]
                entries.append("    %s [" % kinds[st.macro])
                entries.append(None)  # table goes here
            else:
                entries.append("    %s: %s" % (kinds[st.macro], _init_target(st.args[0], public)))
        elif st.macro == "InitScriptGoToIfEqual":
            if st.label != table_label:
                raise CompileError("frame table entry outside %s" % table_label)
            table.append("        %s, %s: %s" % (st.args[0], st.args[1], _init_target(st.args[2], public)))
        elif st.macro not in ("InitScriptEntryEnd", "InitScriptFrameTableEnd", "InitScriptEnd"):
            raise CompileError("map_scripts.inc: can't convert %s" % st.macro)
    ms = []
    for e in entries:
        ms += (table + ["    ]"]) if e is None else [e]

    name = entry["dir"]
    if raw:
        head = ["// Converted from scripts.inc / map_scripts.inc by `mapkit pory init --raw`.",
                "// Scripts inside raw keep their ScrDef order; new `script` blocks are numbered after them.", ""]
    else:
        head = ["// [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] Converted from scripts.inc /",
                "// map_scripts.inc by `mapkit pory init` (decompiler written by claude-opus-5-5).", ""]
    pory = head + scripts_part + ["mapscripts %s_MapScripts {" % name] + ms + ["}", ""]
    return "\n".join(pory)


def init(repo, m, raw=False, stats=None):
    """scripts.inc + map_scripts.inc -> scripts.pory (map scripts as a mapscripts
    block; scripts decompiled, or kept in a raw block with raw). Builds byte-identical."""
    text = init_source(repo, m, raw, stats)
    folder = os.path.join(repo.root, layout.MAPS_DIR, repo.migrated[m.name]["dir"])
    with open(os.path.join(folder, PORY), "w", encoding="utf-8") as f:
        f.write(text)
    subprocess.run(["git", "rm", "-q", os.path.join(folder, "scripts.inc"), os.path.join(folder, "map_scripts.inc")],
                   cwd=repo.root, check=True)
    subprocess.run(["git", "add", os.path.join(folder, PORY)], cwd=repo.root, check=True)
    return os.path.join(folder, PORY)
