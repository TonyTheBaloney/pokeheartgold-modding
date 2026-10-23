#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Species move data as JSON, built into the game's archives.

    level_up_learnsets.json  -> poketool/personal/wotbl.narc
    egg_moves.json           -> fielddata/sodateya/kowaza_list.narc
    battle_moves.json        -> poketool/waza/waza_tbl.narc

Formats follow pokeemerald's src/data/pokemon/level_up_learnsets.h
(LEVEL_UP_MOVE(level, MOVE_X)) and egg_moves.h (egg_moves(SPECIES, MOVE_X, ...)),
written as JSON keyed by species constant:

    "SPECIES_BULBASAUR": [ { "level": 1, "move": "MOVE_TACKLE" }, ... ]
    "SPECIES_BULBASAUR": [ "MOVE_LIGHT_SCREEN", "MOVE_SKULL_BASH", ... ]

battle_moves.json follows pokeemerald's src/data/battle_moves.h, keyed by move
constant: "MOVE_POUND": { "effect": "MOVE_EFFECT_HIT", "power": 40, ... }.

Usage:
    pokedata.py learnsets IN.json OUT.narc --nitroarc PATH --include DIR --work DIR
    pokedata.py egg-moves IN.json OUT.narc --nitroarc PATH --include DIR --work DIR
    pokedata.py moves IN.json OUT.narc --nitroarc PATH --include DIR --work DIR
    pokedata.py extract-learnsets wotbl.narc OUT.json --include DIR
    pokedata.py extract-egg-moves kowaza_list.narc OUT.json --include DIR
    pokedata.py extract-moves waza_tbl.narc OUT.json --include DIR
"""

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys

# Format and limits come from the game's headers (Limits), so they can't drift from the C:
# wotbl member: u16 move | level << LEVEL_UP_LEARNSET_LEVEL_SHIFT, ..., LEVEL_UP_LEARNSET_END,
# zero-padded to 4 bytes. kowaza_list: one list of u16; EGG_MOVES_SPECIES_OFFSET + species starts
# a species' moves, EGG_MOVES_TERMINATOR ends it.
LIMITS = {
    "constants/pokemon.h": ("MAX_LEVEL", "MAX_LEARNED_MOVES"),
    "pokemon.h": ("LEVEL_UP_LEARNSET_END", "LEVEL_UP_LEARNSET_LEVEL_SHIFT", "LEVEL_UP_LEARNSET_MOVEID_MASK"),
    "constants/daycare.h": ("MAX_EGG_MOVES", "EGG_MOVES_SPECIES_OFFSET", "EGG_MOVES_TERMINATOR",
                            "EGG_MOVES_TABLE_SIZE"),
}


class DataError(Exception):
    pass


# --- constants ---------------------------------------------------------------------

def read_defines(path, prefix):
    """{NAME: int} for `#define PREFIX... <int, (1 << n) or earlier name>` lines, in file order."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*#define\s+(%s\w+)\s+(\w+|\(\s*1\s*<<\s*\d+\s*\))\s*(?://.*)?$" % prefix, line)
            if not m:
                continue
            v = m.group(2)
            shift = re.fullmatch(r"\(\s*1\s*<<\s*(\d+)\s*\)", v)
            if shift:
                out[m.group(1)] = 1 << int(shift.group(1))
            elif re.fullmatch(r"0[xX][0-9a-fA-F]+|\d+", v):
                out[m.group(1)] = int(v, 0)
            elif v in out:
                out[m.group(1)] = out[v]
    return out


class Constants:
    def __init__(self, include):
        for header, names in LIMITS.items():
            d = read_defines(os.path.join(include, header), "")
            for n in names:
                if n not in d:
                    raise DataError("%s doesn't define %s" % (header, n))
                setattr(self, n, d[n])
        self.species = read_defines(os.path.join(include, "constants/species.h"), "SPECIES_")
        moves_h = os.path.join(include, "constants/moves.h")
        moves = {k: v for k, v in read_defines(moves_h, "MOVE_").items()
                 if not k.startswith(("MOVE_ATTRIBUTE_", "MOVE_FLAG_"))}
        num = re.search(r"^\s*#define\s+NUM_MOVES\s+(\w+)", open(moves_h, encoding="utf-8").read(), re.M)
        if not num:
            raise DataError("constants/moves.h doesn't define NUM_MOVES")
        self.num_moves = moves[num.group(1)] if num.group(1) in moves else int(num.group(1), 0)
        self.moves = {k: v for k, v in moves.items() if v <= self.num_moves}
        self.num_species = max(self.species.values()) + 1
        self.species_name = {}
        for k, v in self.species.items():
            self.species_name.setdefault(v, k)
        self.move_name = {}
        for k, v in self.moves.items():
            self.move_name.setdefault(v, k)
        # names for the fields of battle_moves.json: {field: {NAME: value}}
        types = read_defines(os.path.join(include, "constants/pokemon.h"), "TYPE_")
        self.move_fields = {
            "effect": read_defines(os.path.join(include, "constants/move_effects.h"), "MOVE_EFFECT_"),
            "category": read_defines(moves_h, "CATEGORY_"),
            "type": {k: v for k, v in types.items() if k not in ("TYPE_NONE", "TYPE_FORESIGHT", "TYPE_ENDTABLE")
                     and not k.startswith("TYPE_MUL_")},
            "target": read_defines(moves_h, "RANGE_"),
            "flags": read_defines(moves_h, "MOVE_FLAG_"),
            "contestCategory": read_defines(moves_h, "CONTEST_CATEGORY_"),
        }

    def species_id(self, name, where):
        if name not in self.species:
            raise DataError("%s: unknown species %r" % (where, name))
        return self.species[name]

    def move_id(self, name, where):
        if name not in self.moves:
            raise DataError("%s: unknown move %r" % (where, name))
        return self.moves[name]


# --- JSON ------------------------------------------------------------------------------

def load_json(path):
    def no_dupes(pairs):
        seen = {}
        for k, v in pairs:
            if k in seen:
                raise DataError("%s: %s appears twice" % (path, k))
            seen[k] = v
        return seen
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f, object_pairs_hook=no_dupes)
        except json.JSONDecodeError as e:
            raise DataError("%s:%d: %s" % (path, e.lineno, e.msg))


def write_learnsets_json(path, sets):
    """One move per line, like pokeemerald's LEVEL_UP_MOVE lines."""
    out = ["{"]
    for i, (species, moves) in enumerate(sets):
        comma = "," if i < len(sets) - 1 else ""
        if not moves:
            out.append('    "%s": []%s' % (species, comma))
            continue
        out.append('    "%s": [' % species)
        for j, (level, move) in enumerate(moves):
            out.append('        { "level": %d, "move": "%s" }%s' % (level, move, "," if j < len(moves) - 1 else ""))
        out.append("    ]%s" % comma)
    out.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def write_egg_moves_json(path, lists):
    out = ["{"]
    for i, (species, moves) in enumerate(lists):
        comma = "," if i < len(lists) - 1 else ""
        if not moves:
            out.append('    "%s": []%s' % (species, comma))
            continue
        out.append('    "%s": [' % species)
        out += ['        "%s"%s' % (m, "," if j < len(moves) - 1 else "") for j, m in enumerate(moves)]
        out.append("    ]%s" % comma)
    out.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def write_moves_json(path, moves):
    """One move per block, fields in MOVE_FIELDS order; flags on one line."""
    out = ["{"]
    for i, (key, fields) in enumerate(moves):
        out.append('    "%s": {' % key)
        items = list(fields.items())
        for j, (k, v) in enumerate(items):
            out.append('        "%s": %s%s' % (k, json.dumps(v), "," if j < len(items) - 1 else ""))
        out.append("    }%s" % ("," if i < len(moves) - 1 else ""))
    out.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


# --- binary --------------------------------------------------------------------------

def learnset_member(moves, c):
    data = b"".join(struct.pack("<H", move | level << c.LEVEL_UP_LEARNSET_LEVEL_SHIFT) for level, move in moves)
    data += struct.pack("<H", c.LEVEL_UP_LEARNSET_END)
    return data + b"\0" * (-len(data) % 4)


def build_learnsets(path, c):
    doc = load_json(path)
    members = [learnset_member([], c)] * c.num_species
    for species, moves in doc.items():
        sid = c.species_id(species, path)
        if not isinstance(moves, list):
            raise DataError("%s: %s: expected a list of { level, move }" % (path, species))
        if len(moves) > c.MAX_LEARNED_MOVES - 1:
            raise DataError("%s: %s has %d moves; the game reads at most %d"
                            % (path, species, len(moves), c.MAX_LEARNED_MOVES - 1))
        out = []
        for i, m in enumerate(moves):
            where = "%s: %s[%d]" % (path, species, i)
            if not isinstance(m, dict) or set(m) != {"level", "move"}:
                raise DataError("%s: expected { \"level\": n, \"move\": \"MOVE_X\" }" % where)
            level, move = m["level"], c.move_id(m["move"], where)
            if not isinstance(level, int) or not 1 <= level <= c.MAX_LEVEL:
                raise DataError("%s: level %r is not 1-%d" % (where, level, c.MAX_LEVEL))
            # Levels should go up: the game stops at the first move above the Pokémon's
            # level. Not enforced, because retail Banette's don't.
            if move > c.LEVEL_UP_LEARNSET_MOVEID_MASK:
                raise DataError("%s: %s doesn't fit in a learnset entry" % (where, m["move"]))
            out.append((level, move))
        members[sid] = learnset_member(out, c)
    return members


def build_egg_moves(path, c):
    doc = load_json(path)
    words = []
    for species, moves in doc.items():
        sid = c.species_id(species, path)
        if not isinstance(moves, list):
            raise DataError("%s: %s: expected a list of moves" % (path, species))
        if len(moves) > c.MAX_EGG_MOVES:
            raise DataError("%s: %s has %d egg moves; the game takes at most %d"
                            % (path, species, len(moves), c.MAX_EGG_MOVES))
        if len(words) >= c.EGG_MOVES_TABLE_SIZE:
            raise DataError("%s: %s starts at entry %d, but the game only searches the first %d "
                            "(src/get_egg.c); the table is full" % (path, species, len(words), c.EGG_MOVES_TABLE_SIZE))
        words.append(c.EGG_MOVES_SPECIES_OFFSET + sid)
        words += [c.move_id(m, "%s: %s" % (path, species)) for m in moves]
    words.append(c.EGG_MOVES_TERMINATOR)
    return [b"".join(struct.pack("<H", w) for w in words)]


# waza_tbl member: struct MoveTbl (include/move.h). LoadMoveTbl reads all of them at once
# from member 0, so every member must be exactly this size.
MOVE_TBL = struct.Struct("<HBBBBBBHbBBBH")
MOVE_FIELDS = (  # (JSON key, MoveTbl field, named by c.move_fields?, lo, hi)
    ("effect", "effect", True, 0, 0xFFFF),
    ("category", "category", True, 0, 0xFF),
    ("power", "power", False, 0, 0xFF),
    ("type", "type", True, 0, 0xFF),
    ("accuracy", "accuracy", False, 0, 100),
    ("pp", "pp", False, 0, 0xFF),
    ("secondaryEffectChance", "effectChance", False, 0, 100),
    ("target", "range", True, 0, 0xFFFF),
    ("priority", "priority", False, -128, 127),
    ("flags", "flags", True, 0, 0xFF),
    ("contestEffect", "unkC", False, 0, 0xFF),
    ("contestCategory", "contestType", True, 0, 0xFF),
)


def move_member(key, fields, c, where):
    if not isinstance(fields, dict):
        raise DataError("%s: expected an object" % where)
    unknown = set(fields) - {f[0] for f in MOVE_FIELDS}
    if unknown:
        raise DataError("%s: unknown field %s" % (where, ", ".join(sorted(unknown))))
    values = []
    for name, _, named, lo, hi in MOVE_FIELDS:
        if name not in fields:
            raise DataError("%s: missing %r" % (where, name))
        v = fields[name]
        if name == "flags":
            if not isinstance(v, list):
                raise DataError("%s: flags: expected a list of MOVE_FLAG_* names" % where)
            bits = 0
            for flag in v:
                if flag not in c.move_fields["flags"]:
                    raise DataError("%s: unknown flag %r" % (where, flag))
                bits |= c.move_fields["flags"][flag]
            v = bits
        elif named and isinstance(v, str):
            if v not in c.move_fields[name]:
                raise DataError("%s: %s: unknown %r" % (where, name, v))
            v = c.move_fields[name][v]
        if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
            raise DataError("%s: %s %r is not %d-%d" % (where, name, fields[name], lo, hi))
        values.append(v)
    return MOVE_TBL.pack(*values, 0)


def build_moves(path, c):
    """Keys are MOVE_* constants, or a number for the spare entries past NUM_MOVES."""
    doc = load_json(path)
    by_id = {}
    for key, fields in doc.items():
        if re.fullmatch(r"\d+", key):
            mid = int(key)
            if mid <= c.num_moves:
                raise DataError("%s: %s: use the move's name (%s)" % (path, key, c.move_name[mid]))
        else:
            mid = c.move_id(key, path)
        if mid in by_id:
            raise DataError("%s: %s and %s are the same move (%d)" % (path, by_id[mid][0], key, mid))
        by_id[mid] = (key, move_member(key, fields, c, "%s: %s" % (path, key)))
    missing = [c.move_name.get(i, str(i)) for i in range(max(by_id) + 1) if i not in by_id]
    if missing:
        raise DataError("%s: missing %s (moves are stored by number, so every one needs an entry)"
                        % (path, ", ".join(missing[:5]) + (" ..." if len(missing) > 5 else "")))
    if max(by_id) < c.num_moves:
        raise DataError("%s: NUM_MOVES is %d but the last entry is %d" % (path, c.num_moves, max(by_id)))
    return [by_id[i][1] for i in range(len(by_id))]


def pack(members, out, nitroarc, work):
    d = os.path.join(work, os.path.basename(out) + ".d")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for i, data in enumerate(members):
        with open(os.path.join(d, "%05d.bin" % i), "wb") as f:
            f.write(data)
    subprocess.run([os.path.abspath(nitroarc), "-cf", os.path.abspath(out), "."], cwd=d, check=True)


# --- extracting the retail archives (one-time) ----------------------------------------

def narc_members(path):
    with open(path, "rb") as f:
        d = f.read()
    if d[:4] != b"NARC":
        raise DataError("%s is not a NARC" % path)
    off, blocks = struct.unpack_from("<H", d, 12)[0], {}
    while off < len(d):
        size = struct.unpack_from("<I", d, off + 4)[0]
        blocks[d[off:off + 4]] = off
        off += size
    fat, img = blocks[b"BTAF"], blocks[b"GMIF"] + 8
    n = struct.unpack_from("<H", d, fat + 8)[0]
    spans = [struct.unpack_from("<II", d, fat + 12 + 8 * i) for i in range(n)]
    return [d[img + s:img + e] for s, e in spans]


def extract_learnsets(narc, c):
    sets = []
    for sid, data in enumerate(narc_members(narc)):
        moves = []
        for (v,) in struct.iter_unpack("<H", data):
            if v == c.LEVEL_UP_LEARNSET_END:
                break
            moves.append((v >> c.LEVEL_UP_LEARNSET_LEVEL_SHIFT, c.move_name[v & c.LEVEL_UP_LEARNSET_MOVEID_MASK]))
        sets.append((c.species_name[sid], moves))
    return sets


def extract_egg_moves(narc, c):
    (data,) = narc_members(narc)
    lists = []
    for (v,) in struct.iter_unpack("<H", data):
        if v == c.EGG_MOVES_TERMINATOR:
            break
        if v > c.EGG_MOVES_SPECIES_OFFSET:
            lists.append((c.species_name[v - c.EGG_MOVES_SPECIES_OFFSET], []))
        else:
            lists[-1][1].append(c.move_name[v])
    return lists


def extract_moves(narc, c):
    names = {field: {} for field in c.move_fields}
    for field, table in c.move_fields.items():
        for k, v in table.items():
            names[field].setdefault(v, k)
    moves = []
    for mid, data in enumerate(narc_members(narc)):
        values = MOVE_TBL.unpack(data)
        if values[-1]:
            raise DataError("move %d: padding is %d, not 0" % (mid, values[-1]))
        fields = {}
        for (name, _, named, _, _), v in zip(MOVE_FIELDS, values):
            if name == "flags":
                fields[name] = [k for k, bit in c.move_fields["flags"].items() if v & bit]
                if sum(c.move_fields["flags"][k] for k in fields[name]) != v:
                    raise DataError("move %d: unnamed flag bits in 0x%X" % (mid, v))
            elif named:
                fields[name] = names[name].get(v, v)
            else:
                fields[name] = v
        moves.append((c.move_name.get(mid, str(mid)), fields))
    return moves


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=("learnsets", "egg-moves", "moves",
                                       "extract-learnsets", "extract-egg-moves", "extract-moves"))
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--include", required=True, help="the repo's include/ directory")
    ap.add_argument("--nitroarc", help="nitroarc program (building)")
    ap.add_argument("--work", help="scratch directory for archive members (building)")
    a = ap.parse_args(argv)
    try:
        c = Constants(a.include)
        if a.action == "extract-learnsets":
            write_learnsets_json(a.output, extract_learnsets(a.input, c))
        elif a.action == "extract-egg-moves":
            write_egg_moves_json(a.output, extract_egg_moves(a.input, c))
        elif a.action == "extract-moves":
            write_moves_json(a.output, extract_moves(a.input, c))
        else:
            build = {"learnsets": build_learnsets, "egg-moves": build_egg_moves, "moves": build_moves}[a.action]
            members = build(a.input, c)
            pack(members, a.output, a.nitroarc, a.work or os.path.dirname(os.path.abspath(a.output)))
    except DataError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
