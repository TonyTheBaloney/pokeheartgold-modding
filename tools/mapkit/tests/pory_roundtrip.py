# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Shared by the tests: decompile what a map's scripts.pory compiles to, compile
that again and compare the two, command by command with jump targets resolved
to positions (mapkit/pory/decompile.py's fingerprint)."""

from mapkit.pory import compiler, context, decompile, own_includes


def roundtrip(repo, m, stats=None):
    """None if equivalent, else a description of the first difference."""
    entry = repo.pory_entry(m)
    first = repo.pory_result(m)
    ctx = context(repo, entry, repo.macros)
    dec = decompile.Decompiler(ctx, entry["dir"], first.scripts_inc)
    lines, st = dec.run(own_includes(repo, entry))
    if stats is not None:
        for k, v in st.items():
            stats[k] = stats.get(k, 0) + v
    second = compiler.compile_source("\n".join(lines) + "\n", ctx)
    a = decompile.fingerprint(first.scripts_inc, repo.macros)
    b = decompile.fingerprint(second.scripts_inc, repo.macros)
    if a != b:
        i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        return "command %d: %s != %s" % (i, a[i] if i < len(a) else None, b[i] if i < len(b) else None)
    if first.public != second.public:
        return "script numbers differ"
    return None
