# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Shared by the tests: compile `mapkit pory init`'s output for a map in memory and
compare it, command by command, with the map's current scripts.inc/map_scripts.inc."""

import os

from mapkit import layout, scripts
from mapkit.pory import compiler, init_source, context


def _stmts(sf, defs, label_args):
    out = []
    for st in sf.statements:
        args = []
        for i, a in enumerate(st.args):
            v = defs.eval(a)
            args.append(("label",) if i in label_args(st.macro) else (v if v is not None else a))
        out.append((st.macro, tuple(args)))
    return out


def roundtrip(repo, m):
    """None if equivalent, else a description of the first difference."""
    entry = repo.migrated[m.name]
    folder = os.path.join(repo.root, layout.MAPS_DIR, entry["dir"])
    src = init_source(repo, m)
    res = compiler.compile_source(src, context(repo, entry, repo.macros))
    defs = repo.event_defines(m)
    la = lambda macro: repo.macros.label_arg_indexes(macro) | ({0} if macro == "InitScriptEntry_OnFrameTable" else set())
    for fname, text in (("scripts.inc", res.scripts_inc), ("map_scripts.inc", res.map_scripts_inc)):
        orig = scripts.parse(os.path.join(folder, fname), repo.macros)
        new = scripts.parse(os.path.join(folder, fname), repo.macros, text)
        a, b = _stmts(orig, defs, la), _stmts(new, defs, la)
        if a != b:
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    return "%s: command %d: %s != %s" % (fname, i, x, y)
            return "%s: %d vs %d commands" % (fname, len(a), len(b))
        if [l for l in orig.scrdefs] != [l for l in new.scrdefs]:
            return "%s: ScrDef order differs" % fname
    return None
