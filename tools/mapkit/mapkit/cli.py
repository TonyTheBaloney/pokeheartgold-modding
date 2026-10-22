# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Command line: mapkit {list,show,validate,refs}."""

import argparse
import json
import os
import re
import sys

from . import events as ev_mod
from . import edit, landdata, layout, layouts, scripts, wild
from .matrix import CELL_SIZE
from .repo import Repo, VERSIONS
from .validate import ERROR, INFO, WARNING, Validator


def _name_for(defs, prefix, value):
    """Reverse-lookup a constant name for display (first match by sorted name)."""
    v = defs.eval(value)
    if v is None or not isinstance(value, int):
        return str(value)
    for n in sorted(defs.names(prefix)):
        if defs.eval(n) == v:
            return n
    return str(value)


def _map_name(repo, map_id):
    m = next((m for m in repo.maps if m.id == map_id), None)
    return m.name if m else str(map_id)


def cmd_list(repo, args):
    pat = re.compile(args.filter, re.I) if args.filter else None
    for m in repo.maps:
        line = "%4d  %-45s %-12s %s" % (m.id, m.name, m.code, m.header.get("mapsec", ""))
        if pat is None or pat.search(line):
            print(line)
    return 0


def cmd_show(repo, args):
    m = repo.find_map(args.map)
    if m is None:
        print("no map matches %r (try `mapkit list %s`)" % (args.map, args.map), file=sys.stderr)
        return 2
    defs = repo.event_defines(m)
    print("%s (id %d, code %s)" % (m.name, m.id, m.code))
    for k in ("mapsec", "mapType", "dayMusicId", "nightMusicId", "weather", "battleBg", "wildEncounterBank"):
        print("  %-18s %s" % (k, m.header.get(k)))
    print("files:")
    for field in ("eventsBank", "scriptsBank", "scriptHeaderBank", "msgBank", "matrixId"):
        p = repo.bank_path(m, field)
        print("  %-18s %s%s" % (field, repo.rel(p) if p else "-", "" if p and os.path.exists(p) else "  (missing)"))

    mx = repo.matrix(m)
    if mx:
        print("matrix: %s, %dx%d cells" % (mx.name, mx.width, mx.height))

    ev = repo.events(m)
    sf = repo.script_file(m)

    def script_desc(value):
        sid = defs.eval(value)
        if sid == 0:
            return "(none)"
        if sid is not None and sf is not None and 1 <= sid <= 1999:
            return "%s (%s)" % (value, sf.script_label(sid) or "?")
        return str(value)

    def pos(o):
        x, z = defs.eval(o.get("x")), defs.eval(o.get("z"))
        if x is None or z is None:
            return "?"
        return "%d,%d (cell %d,%d +%d,%d)" % (x, z, x // CELL_SIZE, z // CELL_SIZE, x % CELL_SIZE, z % CELL_SIZE)

    if ev:
        print("events: %s, %d/%d bytes" % (repo.rel(ev.path), ev.binary_size, ev_mod.EVENT_BUFFER_SIZE))
        print("objects (%d):" % len(ev.objects))
        for o in ev.objects:
            print("  %-28s %-22s at %-26s %-34s %s %s" % (
                o.get("id"), o.get("spriteId"), pos(o), o.get("movement"),
                o.get("type") if o.get("type") != "OBJECT_TYPE_NORMAL" else "",
                "hide=" + str(o.get("eventFlag")) if o.get("eventFlag") != "FLAG_NOTHING" else ""))
            print("  %-28s script %s" % ("", script_desc(o.get("scriptId"))))
        print("warps (%d):" % len(ev.warps))
        for i, w in enumerate(ev.warps):
            if ev_mod.is_dynamic_warp(w, defs):
                dest = "dynamic (returns to saved location)"
            else:
                dest = "%s warp %s" % (_map_name(repo, defs.eval(w.get("header"))), w.get("anchor"))
            print("  [%d] at %-26s -> %s" % (i, pos(w), dest))
        print("bgs (%d):" % len(ev.bgs))
        for b in ev.bgs:
            print("  %-20s at %-26s %-18s script %s" % (b.get("type"), pos(b), b.get("dir"), script_desc(b.get("scriptId"))))
        print("coords (%d):" % len(ev.coords))
        for c in ev.coords:
            print("  at %-26s size %sx%s when %s == %s -> script %s" % (
                pos(c), c.get("w"), c.get("h"), c.get("var"), c.get("val"), script_desc(c.get("scriptId"))))

    if sf:
        tb = repo.text_bank(m)
        print("scripts (%d) in %s:" % (len(sf.scrdefs), repo.rel(sf.path)))
        for i, label in enumerate(sf.scrdefs):
            body = scripts.reachable(sf, repo.macros, label)
            used = sorted({sym for st, sym in scripts.symbol_refs(scripts_view(sf, body))
                           if sym.startswith(("FLAG_", "VAR_", "msg_"))})
            print("  %3d %-24s %3d cmds  %s" % (i + 1, label, len(body), " ".join(used)[:110]))
            if args.text and tb:
                for sym in used:
                    if sym.startswith("msg_"):
                        msg = tb.get(sym)
                        if msg:
                            flat = re.sub(r"\s+", " ", re.sub(r"[\n\r\f]", " ", tb.text_of(msg)))
                            print("        %s: %s" % (sym, flat[:100]))

    i, table = repo.wild_table(m)
    if table:
        print("wild (%s, index %d):" % (m.header.get("wildEncounterBank"), i))
        for method, rate in wild.rates(table, repo.version).items():
            if rate:
                slots = [s for s in wild.iter_slots(table, repo.version) if s[0].split("/")[0] == method]
                species = []
                for s in slots:
                    if s[2] not in species:
                        species.append(s[2])
                print("  %-10s rate %-3s %s" % (method, rate, ", ".join(x.replace("SPECIES_", "") for x in species)))
    return 0


def scripts_view(sf, body):
    view = scripts.ScriptFile(sf.path)
    view.statements = body
    return view


def cmd_validate(repo, args):
    maps = None
    if args.maps:
        maps = []
        for q in args.maps:
            m = repo.find_map(q)
            if m is None:
                print("no map matches %r" % q, file=sys.stderr)
                return 2
            maps.append(m)
    issues = Validator(repo).run(maps)
    show = {ERROR}
    if args.warnings or args.all:
        show.add(WARNING)
    if args.all:
        show.add(INFO)
    for i in issues:
        if i.severity in show:
            print(i)
    counts = {s: sum(1 for i in issues if i.severity == s) for s in (ERROR, WARNING, INFO)}
    print("%d errors, %d warnings, %d notes (%s)" % (counts[ERROR], counts[WARNING], counts[INFO], repo.version),
          file=sys.stderr)
    return 1 if counts[ERROR] else 0


def cmd_refs(repo, args):
    sym = args.symbol
    pat = re.compile(r"\b%s\b" % re.escape(sym))
    seen = set()
    for m in repo.maps:
        ev = repo.events(m)
        if ev and ev.path not in seen:
            seen.add(ev.path)
            for kind in ("objects", "bgs", "warps", "coords"):
                for i, rec in enumerate(getattr(ev, kind)):
                    for k, v in rec.items():
                        if pat.search(str(v)):
                            print("%s %s[%d].%s = %s" % (repo.rel(ev.path), kind, i, k, v))
        for field in ("scriptsBank", "scriptHeaderBank"):
            sf = repo.script_file(m, field)
            if sf and sf.path not in seen:
                seen.add(sf.path)
                for st in sf.statements:
                    if any(pat.search(a) for a in st.args):
                        print("%s:%d %s: %s %s" % (repo.rel(sf.path), st.line, st.label, st.macro, ", ".join(st.args)))
    where = repo.defines.where(sym)
    if where:
        print("defined in %s = %s" % (repo.rel(where), repo.defines.eval(sym)))
    return 0


def cmd_migrate(repo, args):
    for q in args.maps:
        m = repo.find_map(q)
        if m is None:
            print("no map matches %r" % q, file=sys.stderr)
            return 2
        if m.name in repo.migrated:
            print("%s is already in %s/%s/" % (m.name, layout.MAPS_DIR, repo.migrated[m.name]["dir"]))
            continue
        try:
            if args.dry_run:
                p = layout.plan(repo, m)
                print("%s -> %s/%s/" % (m.name, layout.MAPS_DIR, p["dir"]))
                for field, path in p["paths"].items():
                    print("  %-18s %s" % (field, repo.rel(path)))
                print("  %-18s files/%s" % ("event header", p["event_header"]))
                print("  %-18s src/data/map_headers.h [%s]" % ("header", m.name))
                continue
            p = layout.migrate(repo, m)
        except layout.MigrationError as e:
            print("%s: %s" % (m.name, e), file=sys.stderr)
            return 1
        print("migrated %s -> %s/%s/" % (m.name, layout.MAPS_DIR, p["dir"]))
        repo = type(repo)(repo.root, repo.version)  # reload after files moved
    return 0


def _value(v):
    return int(v, 0) if re.fullmatch(r"-?(0x[0-9a-fA-F]+|\d+)", v) else v


def _map(repo, q):
    m = repo.find_map(q)
    if m is None:
        raise edit.EditError("no map matches %r (try `mapkit list`)" % q)
    return m


def _map_warp(repo, spec):
    name, _, idx = spec.rpartition(":")
    if not name or not idx.isdigit():
        raise edit.EditError("expected MAP:WARP_INDEX, got %r" % spec)
    return _map(repo, name), int(idx)


def cmd_edit(repo, args):
    try:
        if args.cmd == "npc":
            m = _map(repo, args.map)
            if args.action == "move":
                fields = {"x": args.x, "y": args.y}
                if args.elevation is not None:
                    fields["elevation"] = args.elevation
                if args.facing:
                    fields["facing_dir"] = args.facing
                rec = edit.npc_set(repo, m, args.npc, **fields)
            elif args.action == "set":
                fields = {}
                for kv in args.fields:
                    k, _, v = kv.partition("=")
                    fields[k] = _value(v)
                rec = edit.npc_set(repo, m, args.npc, **fields)
            else:
                rec = edit.npc_add(repo, m, args.name, args.graphics, args.x, args.y, movement=args.movement,
                                   facing=args.facing or "DIR_SOUTH", script=_value(args.script), flag=args.flag,
                                   trainer_type=args.trainer_type, sight=args.sight)
            print(json.dumps(rec, ensure_ascii=False))
        elif args.cmd == "warp":
            if args.action == "link":
                a, ai = _map_warp(repo, args.a)
                b, bi = _map_warp(repo, args.b)
                edit.warp_link(repo, a, ai, b, bi)
                print("%s warp %d <-> %s warp %d" % (a.name, ai, b.name, bi))
            else:
                m = _map(repo, args.map)
                dest, di = _map_warp(repo, args.to)
                i = edit.warp_add(repo, m, args.x, args.y, dest.name, di)
                print("%s warp %d -> %s warp %d" % (m.name, i, dest.name, di))
        elif args.cmd == "wild":
            m = _map(repo, args.map)
            print(json.dumps(edit.wild_set(repo, m, args.method, args.slot, args.species, args.level, args.time)))
        elif args.cmd == "text":
            print(edit.text_add(repo, _map(repo, args.map), args.text))
        elif args.cmd == "script":
            m = _map(repo, args.map)
            if args.action == "add":
                sid = edit.script_add(repo, m, args.label, args.msg)
                print("%s is script %d; use \"script\": \"%s\"" % (args.label, sid, args.label))
            else:
                edit.script_rename(repo, m, args.old, args.new)
                print("renamed %s -> %s" % (args.old, args.new))
    except edit.EditError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


def cmd_pory(repo, args):
    from . import pory
    try:
        if args.action == "build":
            folder = os.path.basename(os.path.dirname(os.path.abspath(args.pory_file)))
            entry = next(e for e in repo.migrated.values() if e["dir"] == folder)
            pory.build(repo, entry, args.out_dir, args.game)
            return 0
        if args.action == "init":
            if args.all:
                maps = [m for m in repo.maps if m.name in repo.migrated
                        and not repo.migrated[m.name]["scripts"].startswith("@")
                        and not repo.migrated[m.name]["init"].startswith("@")
                        and repo.pory_entry(m) is None]
            elif args.maps:
                maps = [_map(repo, q) for q in args.maps]
            else:
                raise edit.EditError("name the maps to convert, or pass --all")
            stats = {}
            outside = None
            for m in maps:
                print("wrote %s" % repo.rel(pory.init(repo, m, args.raw, stats)))
                repo = type(repo)(repo.root, repo.version)
                e = repo.migrated[m.name]
                if not args.raw and not e["text"].startswith("@"):
                    from .pory import inline_text
                    outside = outside if outside is not None else inline_text.outside_refs(repo.root)
                    n_in, n_blk = inline_text.convert(repo, e, outside)
                    stats["inline text"] = stats.get("inline text", 0) + n_in
                    stats["text blocks"] = stats.get("text blocks", 0) + n_blk
                    repo = type(repo)(repo.root, repo.version)
            if stats:
                print("scripts: " + ", ".join("%d %s" % (v, k) for k, v in sorted(stats.items(), key=lambda kv: -kv[1])))
            return 0
        if args.action == "name-scripts":
            from .pory import naming
            maps = None if args.all else [_map(repo, q) for q in args.maps]
            if maps == []:
                raise edit.EditError("name the maps, or pass --all")
            plans = naming.plan_all(repo, maps)
            for d, p in plans.items():
                for old, new in p.items():
                    print("%s: %s -> %s" % (d, old, new))
            n = sum(len(p) for p in plans.values())
            if args.dry_run:
                print("%d renames (dry run)" % n)
                return 0
            changed = naming.apply(repo, plans)
            print("%d renames; %d files changed" % (n, len(changed)))
            return 0
        if args.action == "inline-text":
            from .pory import inline_text
            if args.all:
                maps = [m for m in repo.maps if m.name in repo.migrated]
            elif args.maps:
                maps = [_map(repo, q) for q in args.maps]
            else:
                raise edit.EditError("name the maps to convert, or pass --all")
            outside = inline_text.outside_refs(repo.root)
            total = [0, 0, 0]
            for m in maps:
                e = repo.migrated[m.name]
                if e["scripts"].startswith("@") or e["text"].startswith("@") or repo.pory_entry(m) is None:
                    continue
                try:
                    n_in, n_blk = inline_text.convert(repo, e, outside)
                except pory.CompileError as ex:
                    print("skipped: %s" % ex, file=sys.stderr)
                    total[2] += 1
                    continue
                if n_in or n_blk:
                    print("%s: %d inline, %d text blocks" % (e["dir"], n_in, n_blk))
                total[0] += n_in
                total[1] += n_blk
                repo._cache.clear()
            print("messages: %d inline, %d text blocks; %d maps skipped" % tuple(total))
            return 1 if total[2] else 0
        m = _map(repo, args.map)
        res = repo.pory_result(m)
        if res is None:
            raise edit.EditError("%s has no scripts.pory (create one with `mapkit pory init %s`)" % (m.name, args.map))
        if args.action == "show":
            print(res.scripts_inc)
            print(res.map_scripts_inc)
            for tid, v in res.texts:
                print("%s: %r" % (tid, v))
        else:
            changed = pory.sync_ids(repo, repo.migrated[m.name], res.public)
            print("ids.h %s" % ("updated" if changed else "already up to date"))
    except (pory.PoryError, edit.EditError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mapkit", description="Read and check pokeheartgold map data.")
    ap.add_argument("--root", help="repo root (default: search upward from the current directory)")
    ap.add_argument("--version", choices=VERSIONS, default="HEARTGOLD", help="game version for version-specific data")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="list maps (id, name, code, map section)")
    p.add_argument("filter", nargs="?", help="regex filter")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="show one map's header, events, scripts and wild data")
    p.add_argument("map", help="MAP_CHERRYGROVE, Cherrygrove, T21 or 67")
    p.add_argument("--text", action="store_true", help="print the text each script uses")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("validate", help="check maps for broken references (exit 1 on errors)")
    p.add_argument("maps", nargs="*", help="maps to check (default: all)")
    p.add_argument("-w", "--warnings", action="store_true", help="also print warnings")
    p.add_argument("-a", "--all", action="store_true", help="also print warnings and notes")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("refs", help="find where a constant (flag, var, object, sprite, ...) is used")
    p.add_argument("symbol")
    p.set_defaults(func=cmd_refs)

    p = sub.add_parser("migrate", help="move maps into data/maps/<Folder>/ (keeps the ROM identical)")
    p.add_argument("maps", nargs="+")
    p.add_argument("--dry-run", action="store_true", help="only show what would move")
    p.set_defaults(func=cmd_migrate)

    # --- editing (phase 3) ---
    npc = sub.add_parser("npc", help="move, change or add an NPC (object event)")
    npcs = npc.add_subparsers(dest="action", required=True)
    p = npcs.add_parser("move", help="set an NPC's position")
    p.add_argument("map"); p.add_argument("npc", help="local id (obj_T21_gsboy1), its suffix (gsboy1) or index")
    p.add_argument("x", type=int); p.add_argument("y", type=int)
    p.add_argument("--elevation", type=int); p.add_argument("--facing", help="DIR_NORTH/SOUTH/WEST/EAST")
    p = npcs.add_parser("set", help="set fields: movement_type=MOVEMENT_TYPE_WANDER_AROUND flag=FLAG_X ...")
    p.add_argument("map"); p.add_argument("npc"); p.add_argument("fields", nargs="+")
    p = npcs.add_parser("add", help="add an NPC (and its #define in ids.h)")
    p.add_argument("map"); p.add_argument("name", help="local id or suffix, e.g. fisher -> obj_T21_fisher")
    p.add_argument("graphics", help="SPRITE_*"); p.add_argument("x", type=int); p.add_argument("y", type=int)
    p.add_argument("--movement", default="MOVEMENT_TYPE_LOOK_AROUND"); p.add_argument("--facing")
    p.add_argument("--script", default="0", help="script label, std_* or number")
    p.add_argument("--flag", default="FLAG_NOTHING"); p.add_argument("--trainer-type", default="OBJECT_TYPE_NORMAL")
    p.add_argument("--sight", type=int, default=0)
    for p in npcs.choices.values():
        p.set_defaults(func=cmd_edit)

    warp = sub.add_parser("warp", help="link or add warps")
    warps = warp.add_subparsers(dest="action", required=True)
    p = warps.add_parser("link", help="make two warps lead to each other: Cherrygrove:0 Cherrygrove_Pokecenter_1F:0")
    p.add_argument("a"); p.add_argument("b")
    p = warps.add_parser("add", help="add a warp tile leading to MAP:WARP")
    p.add_argument("map"); p.add_argument("x", type=int); p.add_argument("y", type=int)
    p.add_argument("--to", required=True, help="MAP:WARP_INDEX")
    for p in warps.choices.values():
        p.set_defaults(func=cmd_edit)

    p = sub.add_parser("wild", help="set a wild encounter slot: wild Route29 land 0 SPECIES_PIDGEY --level 3")
    p.add_argument("action", choices=["set"]); p.add_argument("map")
    p.add_argument("method", choices=["land", "surf", "rock_smash", "old_rod", "good_rod", "super_rod"])
    p.add_argument("slot", type=int); p.add_argument("species", nargs="?")
    p.add_argument("--level", help="5, or 5-8 for surf/rock smash/fishing")
    p.add_argument("--time", choices=["morn", "day", "nite"], help="grass only; default all three")
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("text", help='append a message to the map\'s text bank (use \\n for new lines)')
    p.add_argument("action", choices=["add"]); p.add_argument("map"); p.add_argument("text")
    p.set_defaults(func=cmd_edit)

    script = sub.add_parser("script", help="add or rename event scripts")
    scs = script.add_subparsers(dest="action", required=True)
    p = scs.add_parser("add", help="append a script (talk-to-NPC stub with --msg)")
    p.add_argument("map"); p.add_argument("label"); p.add_argument("--msg", help="msg id to show")
    p = scs.add_parser("rename", help="rename a script label everywhere in the map")
    p.add_argument("map"); p.add_argument("old"); p.add_argument("new")
    for p in scs.choices.values():
        p.set_defaults(func=cmd_edit)

    pory_p = sub.add_parser("pory", help="poryscript-style scripts (docs/modding/SCRIPTING.md)")
    ps = pory_p.add_subparsers(dest="action", required=True)
    p = ps.add_parser("init", help="convert a map's scripts.inc/map_scripts.inc to scripts.pory (ROM unchanged)")
    p.add_argument("maps", nargs="*")
    p.add_argument("--all", action="store_true", help="every map that has its own scripts and no scripts.pory yet")
    p.add_argument("--raw", action="store_true", help="keep scripts.inc as one raw block instead of decompiling it")
    p = ps.add_parser("inline-text", help="move dialog from text.json into scripts.pory (ROM unchanged)")
    p.add_argument("maps", nargs="*")
    p.add_argument("--all", action="store_true")
    p = ps.add_parser("name-scripts", help="pokeemerald-style names for generated script and movement labels")
    p.add_argument("maps", nargs="*")
    p.add_argument("--all", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="print the renames only")
    p = ps.add_parser("show", help="print what a map's scripts.pory compiles to")
    p.add_argument("map")
    p = ps.add_parser("sync", help="update the _EV_ defines in ids.h to the compiled script order")
    p.add_argument("map")
    p = ps.add_parser("build", help="(used by the build)")
    p.add_argument("pory_file"); p.add_argument("out_dir"); p.add_argument("--game", default="HEARTGOLD")
    for p in ps.choices.values():
        p.set_defaults(func=cmd_pory)

    lay = sub.add_parser("layouts", help="map grids in data/layouts (docs/modding/maps-and-warps.md)")
    ls_ = lay.add_subparsers(dest="action", required=True)
    p = ls_.add_parser("migrate", help="one-time: map_matrix/*.bin -> data/layouts (ROM unchanged)")
    p.set_defaults(func=lambda repo, a: print("%d layouts" % len(layouts.migrate(repo.root))) or 0)
    p = ls_.add_parser("rename", help="rename a layout folder and update the maps that use it")
    p.add_argument("old"); p.add_argument("new")
    p.set_defaults(func=lambda repo, a: print("%s -> %s (%d maps)" % (
        a.old, a.new, len(layouts.rename(repo.root, a.old, a.new)))) or 0)
    p = ls_.add_parser("pack", help="(used by the build)")
    p.add_argument("out"); p.add_argument("--nitroarc", required=True); p.add_argument("--work", required=True)
    p.set_defaults(func=lambda repo, a: layouts.pack(repo.root, a.out, a.nitroarc, a.work) or 0)

    land = sub.add_parser("landdata", help="terrain cells in data/landdata")
    lds = land.add_subparsers(dest="action", required=True)
    p = lds.add_parser("migrate", help="one-time: files/a/0/6/5 -> data/landdata (ROM unchanged)")
    p.set_defaults(func=lambda repo, a: print("%d land data cells" % landdata.migrate(repo.root)) or 0)
    p = lds.add_parser("pack", help="(used by the build)")
    p.add_argument("out")
    p.set_defaults(func=lambda repo, a: landdata.pack(repo.root, a.out) or 0)
    p = lds.add_parser("files", help="(used by the build) list every source file")
    p.set_defaults(func=lambda repo, a: print("\n".join(landdata.file_list(repo.root))) or 0)

    # build-time generators (called from data/maps/meson.build)
    for name, fn in (("gen-header", layout.gen_header), ("gen-events", layout.gen_events)):
        p = sub.add_parser(name, help="(used by the build)")
        p.add_argument("map_json")
        p.add_argument("out")
        p.set_defaults(func=lambda repo, a, fn=fn: fn(repo.root, a.map_json, a.out) or 0)

    args = ap.parse_args(argv)
    repo = Repo(args.root, args.version)
    try:
        return args.func(repo, args)
    except (layouts.LayoutError, landdata.LandDataError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
