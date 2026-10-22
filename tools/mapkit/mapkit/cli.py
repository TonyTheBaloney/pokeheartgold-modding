# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Command line: mapkit {list,show,validate,refs}."""

import argparse
import os
import re
import sys

from . import events as ev_mod
from . import scripts, wild
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

    args = ap.parse_args(argv)
    repo = Repo(args.root, args.version)
    return args.func(repo, args)
