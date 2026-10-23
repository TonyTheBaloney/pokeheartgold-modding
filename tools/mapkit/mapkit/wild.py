# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
"""Wild encounter tables: gs_enc_data.json + include/encounter_tables_narc.h."""

import json
import re

ENCDATA_NA = 255
_DEF_RE = re.compile(r"#define\s+(ENCDATA_\w+)\s+ENCDATA\(_(\d+)\)")

METHODS = ("land", "surf", "rock_smash")
ROD_METHODS = ("old_rod", "good_rod", "super_rod")
SLOT_COUNTS = {"land": 12, "surf": 5, "rock_smash": 2, "old_rod": 5, "good_rod": 5, "super_rod": 5}


def load_index(path):
    """ENCDATA_* name -> index into the encounters array."""
    out = {}
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for name, num in _DEF_RE.findall(src):
        out[name] = int(num, 10)
    return out


def load_tables(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["encounters"]


def pick_version(value, version):
    """Resolve {"HEARTGOLD": a, "SOULSILVER": b} for one version."""
    if isinstance(value, dict) and ("HEARTGOLD" in value or "SOULSILVER" in value):
        return value.get(version)
    return value


def iter_slots(table, version):
    """Yield (method, slot index, species, level text) for one table."""
    for method in METHODS:
        for i, mon in enumerate(table.get(method, {}).get("mons", [])):
            yield from _slot(method, i, mon, version)
    for rod in ROD_METHODS:
        for i, mon in enumerate(table.get("fishing", {}).get(rod, {}).get("mons", [])):
            yield from _slot(rod, i, mon, version)


def _slot(method, i, mon, version):
    level = pick_version(mon.get("level"), version)
    if isinstance(level, dict):
        level = "%s-%s" % (pick_version(level.get("min"), version), pick_version(level.get("max"), version))
    species = pick_version(mon.get("species"), version)
    if isinstance(species, dict) and "morn" in species:
        for tod in ("morn", "day", "nite"):
            yield method + "/" + tod, i, pick_version(species[tod], version), level
    else:
        yield method, i, species, level


def rates(table, version):
    out = {m: pick_version(table.get(m, {}).get("rate", 0), version) for m in METHODS}
    for rod in ROD_METHODS:
        out[rod] = pick_version(table.get("fishing", {}).get(rod, {}).get("rate", 0), version)
    return out
