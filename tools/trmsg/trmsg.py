#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25
"""Trainer battle text: show it, check it, and rebuild the binary tables from trainers.json.

    python3 tools/trmsg/trmsg.py show TRAINER_YOUNGSTER_JOEY    # a trainer's lines
    python3 tools/trmsg/trmsg.py check                          # do the files agree?
    python3 tools/trmsg/trmsg.py build                          # trainers.json -> tables

The game reads trainer text from three files:
  files/poketool/trmsg/trtbl.narc     (trainer, message type) pairs, 4 bytes each
  files/poketool/trmsg/trtblofs.narc  per trainer, the byte offset of its first pair
  files/msgdata/msg/msg_0728.json     the text; message N belongs to pair N
`build` regenerates all three from the "messages" lists in
files/poketool/trainer/trainers.json. Trainers keep their place in the table
(read from the current trtbl.narc); trainers that are new to the table go at the
end. On unmodified data the output is byte-identical to the retail files.
docs/modding/trainer-text.md explains the format and the lookups.
"""

import json
import os
import re
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TRAINERS = "files/poketool/trainer/trainers.json"
TBL = "files/poketool/trmsg/trtbl.narc"
OFS = "files/poketool/trmsg/trtblofs.narc"
MSG = "files/msgdata/msg/msg_0728.json"
HEADER = "include/constants/trainers.h"

# Retail trainer count. Above it, every trainer gets an offset entry; at or
# below it, the table keeps its retail length (735 entries: the three partner
# trainers 735-737 have none, and nothing asks for their text).
RETAIL_TRAINERS = 738


def path(rel):
    return os.path.join(ROOT, rel)


def read_narc(rel):
    """The single member of a one-file NARC."""
    data = open(path(rel), "rb").read()
    start, end = struct.unpack_from("<II", data, 0x1C)
    gmif = data.index(b"GMIF")
    return data[gmif + 8 + start:gmif + 8 + end]


def write_narc(rel, member):
    """A one-file NARC laid out like the retail ones (no names, 0xFF padding)."""
    padded = member + b"\xff" * (-len(member) % 4)
    btaf = b"BTAF" + struct.pack("<IHHII", 0x14, 1, 0, 0, len(member))
    btnf = b"BTNF" + struct.pack("<IIHH", 0x10, 4, 0, 1)
    gmif = b"GMIF" + struct.pack("<I", 8 + len(padded)) + padded
    body = btaf + btnf + gmif
    head = b"NARC" + struct.pack("<HHIHH", 0xFFFE, 0x0100, 0x10 + len(body), 0x10, 3)
    open(path(rel), "wb").write(head + body)


def constants():
    text = open(path(HEADER)).read()
    trainers = {k: int(v) for k, v in re.findall(r"#define\s+(TRAINER_\w+)\s+(\d+)\b", text)}
    types = {k: int(v) for k, v in re.findall(r"#define\s+(TRMSG_\w+)\s+(\d+)\b", text)}
    return trainers, types


def trainer_id(name, trainers):
    if name.isdigit():
        return int(name)
    if name not in trainers:
        sys.exit("%s is not in %s" % (name, HEADER))
    return trainers[name]


def to_game(text):
    """trainers.json spells line breaks as \\n, \\r, \\f; msg_0728.json uses the characters."""
    return text.replace("\\n", "\n").replace("\\r", "\r").replace("\\f", "\f")


def to_msg_entry(text):
    """msg_0728.json splits a message after each break; one piece is a plain string."""
    pieces = re.findall(r"[^\n\r\f]*(?:[\n\r\f]|$)", text)
    pieces = [p for p in pieces if p]
    return pieces if len(pieces) > 1 else (pieces[0] if pieces else "")


def flatten(entry):
    value = entry["en_US"]
    return "".join(value) if isinstance(value, list) else value


def load_tables():
    tbl = read_narc(TBL)
    ofs = read_narc(OFS)
    pairs = [struct.unpack_from("<HH", tbl, i) for i in range(0, len(tbl), 4)]
    offsets = [struct.unpack_from("<H", ofs, i)[0] for i in range(0, len(ofs) - 1, 2)]
    msg = json.load(open(path(MSG), encoding="utf-8"))
    return pairs, offsets, msg


def load_trainers():
    return json.load(open(path(TRAINERS), encoding="utf-8"))["trainers"]


def wanted(trainers_json, types):
    """trainer id -> [(type, text)] from trainers.json."""
    out = {}
    for tid, trainer in enumerate(trainers_json):
        lines = []
        for m in trainer.get("messages", []):
            t = m["type"]
            if t not in types:
                sys.exit("trainer %d: unknown message type %s" % (tid, t))
            if any(types[t] == other for other, _ in lines):
                sys.exit("trainer %d: two %s lines; the game only finds the first" % (tid, t))
            lines.append((types[t], to_game(m["message"])))
        if lines:
            out[tid] = lines
    return out


def build_tables(want, old_pairs, old_offsets, ntrainers):
    order = []
    for t, _ in old_pairs:
        if t in want and t not in order:
            order.append(t)
    order += sorted(t for t in want if t not in order)

    pairs, texts, first = [], [], {}
    for t in order:
        first[t] = len(pairs) * 4
        for mtype, text in want[t]:
            pairs.append((t, mtype))
            texts.append(text)
    count = max(len(old_offsets), max(want, default=-1) + 1)
    if ntrainers > RETAIL_TRAINERS:
        count = max(count, ntrainers)
    if len(pairs) * 4 > 0xFFFF:
        sys.exit("the table is over 64 KB; offsets are 16-bit")
    # A trainer with no lines points at 0: the exists-check stops at once (a
    # different trainer's pair), and the text lookup scans to the end and prints
    # an empty box.
    offsets = [first.get(t, 0) for t in range(count)]
    return pairs, offsets, texts


def cmd_build():
    trainers, types = constants()
    tj = load_trainers()
    old_pairs, old_offsets, msg = load_tables()
    pairs, offsets, texts = build_tables(wanted(tj, types), old_pairs, old_offsets, len(tj))
    write_narc(TBL, b"".join(struct.pack("<HH", *p) for p in pairs))
    write_narc(OFS, b"".join(struct.pack("<H", o) for o in offsets))
    msg["messages"] = [{"id": "msg_0728_%05d" % i, "en_US": to_msg_entry(t)} for i, t in enumerate(texts)]
    with open(path(MSG), "w", encoding="utf-8") as f:
        f.write(json.dumps(msg, indent=2, ensure_ascii=False) + "\n")
    print("%d lines for %d trainers" % (len(pairs), len({t for t, _ in pairs})))


def cmd_check():
    trainers, types = constants()
    tj = load_trainers()
    pairs, offsets, msg = load_tables()
    problems = []
    if len(msg["messages"]) != len(pairs):
        problems.append("msg_0728.json has %d messages, trtbl.narc %d pairs" % (len(msg["messages"]), len(pairs)))
    have = {}
    for i, (t, m) in enumerate(pairs):
        if t in have and pairs[i - 1][0] != t:
            problems.append("trainer %d's lines are split; the exists-check stops at the first gap" % t)
        text = flatten(msg["messages"][i]) if i < len(msg["messages"]) else None
        have.setdefault(t, []).append((m, text))
    for t, lines in have.items():
        first = next(i for i, p in enumerate(pairs) if p[0] == t) * 4
        if t >= len(offsets):
            problems.append("trainer %d has lines but no trtblofs entry" % t)
        elif offsets[t] != first:
            problems.append("trtblofs[%d] is %d, its lines start at %d" % (t, offsets[t], first))
    if len(tj) > max(len(offsets), RETAIL_TRAINERS):
        problems.append("trainers %d-%d have no trtblofs entry; run build" % (len(offsets), len(tj) - 1))
    want = wanted(tj, types)
    for t in sorted(set(want) | set(have)):
        if want.get(t, []) != have.get(t, []):
            problems.append("trainer %d: trainers.json differs from the tables; run build" % t)
    for p in problems:
        print(p)
    if problems:
        sys.exit(1)
    print("ok: %d lines for %d trainers" % (len(pairs), len(have)))


def cmd_show(names):
    trainers, types = constants()
    type_names = {v: k for k, v in types.items()}
    trainer_names = {v: k for k, v in trainers.items()}
    pairs, offsets, msg = load_tables()
    for name in names:
        t = trainer_id(name, trainers)
        print("%d %s" % (t, trainer_names.get(t, "")))
        lines = [(i, m) for i, (tt, m) in enumerate(pairs) if tt == t]
        if not lines:
            print("  (no lines)")
        for i, m in lines:
            text = flatten(msg["messages"][i])
            print("  %-32s msg_0728_%05d  %s" % (type_names.get(m, str(m)), i, json.dumps(text, ensure_ascii=False)))


def main(argv):
    if len(argv) >= 2 and argv[1] == "show" and len(argv) > 2:
        cmd_show(argv[2:])
    elif argv[1:] == ["check"]:
        cmd_check()
    elif argv[1:] == ["build"]:
        cmd_build()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
