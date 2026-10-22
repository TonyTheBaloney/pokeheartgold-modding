#!/usr/bin/env python3
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Species move data as JSON, built into the game's archives.

    level_up_learnsets.json  -> poketool/personal/wotbl.narc
    egg_moves.json           -> fielddata/sodateya/kowaza_list.narc

Formats follow pokeemerald's src/data/pokemon/level_up_learnsets.h
(LEVEL_UP_MOVE(level, MOVE_X)) and egg_moves.h (egg_moves(SPECIES, MOVE_X, ...)),
written as JSON keyed by species constant:

    "SPECIES_BULBASAUR": [ { "level": 1, "move": "MOVE_TACKLE" }, ... ]
    "SPECIES_BULBASAUR": [ "MOVE_LIGHT_SCREEN", "MOVE_SKULL_BASH", ... ]

Usage:
    pokedata.py learnsets IN.json OUT.narc --nitroarc PATH --include DIR --work DIR
    pokedata.py egg-moves IN.json OUT.narc --nitroarc PATH --include DIR --work DIR
    pokedata.py extract-learnsets wotbl.narc OUT.json --include DIR
    pokedata.py extract-egg-moves kowaza_list.narc OUT.json --include DIR
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
    """{NAME: int} for `#define PREFIX... <int or earlier name>` lines, in file order."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*#define\s+(%s\w+)\s+(\w+)\s*(?://.*)?$" % prefix, line)
            if not m:
                continue
            v = m.group(2)
            if re.fullmatch(r"0[xX][0-9a-fA-F]+|\d+", v):
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
        moves = read_defines(os.path.join(include, "constants/moves.h"), "MOVE_")
        last = moves.get("NUM_MOVES") or max(v for k, v in moves.items() if not k.startswith("MOVE_ATTRIBUTE_"))
        self.moves = {k: v for k, v in moves.items() if not k.startswith("MOVE_ATTRIBUTE_") and v <= last}
        self.num_species = max(self.species.values()) + 1
        self.species_name = {}
        for k, v in self.species.items():
            self.species_name.setdefault(v, k)
        self.move_name = {}
        for k, v in self.moves.items():
            self.move_name.setdefault(v, k)

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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=("learnsets", "egg-moves", "extract-learnsets", "extract-egg-moves"))
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
        else:
            members = (build_learnsets if a.action == "learnsets" else build_egg_moves)(a.input, c)
            pack(members, a.output, a.nitroarc, a.work or os.path.dirname(os.path.abspath(a.output)))
    except DataError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
