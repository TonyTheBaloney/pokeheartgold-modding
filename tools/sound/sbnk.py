#!/usr/bin/env python3
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-23
"""Instrument banks (SBNK): to and from JSON.

A bank is the DS's voicegroup (pokeemerald's sound/voicegroups/*.inc): for each
program number, which sample to play and how. A sequence's program change (MIDI
program change) picks the instrument; the bank's wave archives (up to 4, set in
sound/sound_data.json) hold the samples.

    {
        "instruments": [
            {"program": 0, "type": "pcm", "archive": 0, "sample": 0, "key": 60},
            {"program": 1, "type": "psg", "duty": 3, "key": 69, "release": 100},
            {"program": 2, "type": "noise", "key": 60},
            {"program": 3, "type": "keySplit", "regions": [
                {"upTo": 59, "type": "pcm", "archive": 0, "sample": 1, "key": 48},
                {"upTo": 127, "type": "pcm", "archive": 0, "sample": 2, "key": 72}]},
            {"program": 4, "type": "drumSet", "first": 36, "keys": [
                {"type": "pcm", "archive": 1, "sample": 0, "key": 60},
                {"type": "pcm", "archive": 1, "sample": 1, "key": 60, "pan": 40}]}
        ]
    }

type        "pcm" (a sample), "psg" (square wave, "duty" 0-7 = 12.5%-87.5%), "noise",
            "keySplit" (up to 8 regions; a note plays the first region whose "upTo"
            is at least the note, so list them low to high and end with 127),
            "drumSet" (one instrument per key from "first" on).
archive     which of the bank's wave archives (0-3); sample: index in it.
key         the note at which the sample plays at its own pitch (MIDI number; 60 = C4).
attack, decay, sustain, release   envelope, 0-127 (default 127, 127, 127, 120).
pan         0 left, 64 centre, 127 right (default 64).
Programs not listed are empty.

Usage:
    sbnk.py build BANK.json OUT.sbnk
    sbnk.py to-json IN.sbnk [OUT.json]
"""

import argparse
import json
import struct
import sys

TYPES = {"pcm": 1, "psg": 2, "noise": 3, "drumSet": 0x10, "keySplit": 0x11}
TYPE_NAMES = {v: k for k, v in TYPES.items()}
SIMPLE = (1, 2, 3)
DEFAULTS = {"key": 60, "attack": 127, "decay": 127, "sustain": 127, "release": 120, "pan": 64}
ENVELOPE = ("attack", "decay", "sustain", "release", "pan")
MAX_REGIONS = 8


class SbnkError(Exception):
    pass


def _byte(inst, k, where):
    v = inst.get(k, DEFAULTS[k])
    if not 0 <= v <= 127:
        raise SbnkError(f"{where}: {k} {v} is out of range (0-127)")
    return v


def encode_simple(inst, where):
    """10 bytes: wave[2], key, attack, decay, sustain, release, pan."""
    t = inst.get("type", "pcm")
    if t == "pcm":
        if inst.get("archive", 0) not in range(4):
            raise SbnkError(f"{where}: archive must be 0-3")
        w0, w1 = inst["sample"], inst.get("archive", 0)
    elif t == "psg":
        if inst.get("duty", 3) not in range(8):
            raise SbnkError(f"{where}: duty must be 0-7")
        w0, w1 = inst.get("duty", 3), 0
    elif t == "noise":
        w0, w1 = 0, 0
    else:
        raise SbnkError(f"{where}: type must be pcm, psg or noise here, not {t!r}")
    return TYPES[t], struct.pack("<HHBBBBBB", w0, w1, _byte(inst, "key", where),
                                 *(_byte(inst, k, where) for k in ENVELOPE))


def decode_simple(typ, raw):
    w0, w1, key, *env = struct.unpack("<HHBBBBBB", raw)
    name = TYPE_NAMES.get(typ)
    if name is None or typ not in SIMPLE:
        return {"type": "null", "raw": raw.hex()} if typ == 0 else {"type": typ, "raw": raw.hex()}
    e = {"type": name}
    if name == "pcm":
        e.update(archive=w1, sample=w0)
    elif name == "psg":
        e["duty"] = w0
    e["key"] = key
    for k, v in zip(ENVELOPE, env):
        if v != DEFAULTS[k]:
            e[k] = v
    if name != "pcm" and (w1 or (name == "noise" and w0)):
        e["wave"] = [w0, w1]  # unused fields that weren't 0: keep them
    return e


def _encode_entry(inst, where):
    """12 bytes inside a drum set or key split: type, 0, then the 10-byte instrument."""
    if inst is None or inst.get("type") == "null":
        raw = bytes.fromhex(inst["raw"]) if inst and "raw" in inst else b"\0" * 10
        return b"\0\0" + raw
    typ, raw = encode_simple(inst, where)
    if "wave" in inst:
        raw = struct.pack("<HH", *inst["wave"]) + raw[4:]
    return bytes([typ, 0]) + raw


def build_sbnk(doc):
    insts = doc.get("instruments", [])
    by_prog = {}
    for i, inst in enumerate(insts):
        p = inst.get("program")
        if not isinstance(p, int) or not 0 <= p < 0x10000:
            raise SbnkError(f"instrument {i}: needs a \"program\" number")
        if p in by_prog:
            raise SbnkError(f"program {p} is listed twice")
        by_prog[p] = inst
    count = max(by_prog) + 1 if by_prog else 0
    table_end = 0x3C + 4 * count
    # data: simple instruments, then drum sets, then key splits (the order Nintendo's tool used)
    order = sorted(by_prog, key=lambda p: ({1: 0, 2: 0, 3: 0, 0x10: 1, 0x11: 2}[TYPES.get(by_prog[p].get("type", "pcm"), 1)], p))
    data, offsets = bytearray(), {}
    for p in order:
        inst = by_prog[p]
        where = f"program {p}"
        t = inst.get("type", "pcm")
        if t not in TYPES:
            raise SbnkError(f"{where}: unknown type {t!r}")
        offsets[p] = (TYPES[t], table_end + len(data))
        if t == "keySplit":
            regions = inst.get("regions", [])
            if not 1 <= len(regions) <= MAX_REGIONS:
                raise SbnkError(f"{where}: a key split has 1-{MAX_REGIONS} regions")
            keys = [r["upTo"] for r in regions]
            if not all(0 < k <= 127 for k in keys):
                raise SbnkError(f"{where}: region \"upTo\" keys must be 1-127")
            data += bytes(keys + [0] * (MAX_REGIONS - len(keys)))
            for j, r in enumerate(regions):
                data += _encode_entry(r, f"{where} region {j}")
        elif t == "drumSet":
            keys = inst.get("keys", [])
            first = inst.get("first", 0)
            if not keys or not 0 <= first <= first + len(keys) - 1 <= 127:
                raise SbnkError(f"{where}: a drum set needs keys within 0-127")
            data += bytes([first, first + len(keys) - 1])
            for j, k in enumerate(keys):
                data += _encode_entry(k, f"{where} key {first + j}")
        else:
            typ, raw = encode_simple(inst, where)
            data += raw
    table = b"".join(struct.pack("<I", offsets[p][0] | offsets[p][1] << 8) if p in offsets else b"\0\0\0\0"
                     for p in range(count))
    body = table + data
    size = 0x3C + len(body)
    pad = (-size) % 4
    body += b"\0" * pad
    size += pad
    return (b"SBNK" + struct.pack("<HHIHH", 0xFEFF, 0x0100, size, 0x10, 1)
            + b"DATA" + struct.pack("<I", size - 0x10) + b"\0" * 32 + struct.pack("<I", count) + body)


def parse_sbnk(data):
    if data[:4] != b"SBNK" or data[16:20] != b"DATA":
        raise SbnkError("not an SBNK file")
    n = struct.unpack_from("<I", data, 0x38)[0]
    insts = []
    for p in range(n):
        o = struct.unpack_from("<I", data, 0x3C + 4 * p)[0]
        typ, off = o & 0xFF, o >> 8
        if typ == 0:
            continue
        if typ in SIMPLE:
            e = decode_simple(typ, data[off:off + 10])
        elif typ == 0x10:
            first, last = data[off], data[off + 1]
            keys = [_decode_entry(data, off + 2 + 12 * k) for k in range(last - first + 1)]
            e = {"type": "drumSet", "first": first, "keys": keys}
        elif typ == 0x11:
            ks = [k for k in data[off:off + 8] if k]
            regions = []
            for j, k in enumerate(ks):
                r = {"upTo": k}
                r.update(_decode_entry(data, off + 8 + 12 * j))
                regions.append(r)
            e = {"type": "keySplit", "regions": regions}
        else:
            raise SbnkError(f"program {p}: unknown instrument type {typ}")
        insts.append({"program": p, **e})
    return {"instruments": insts}


def _decode_entry(data, o):
    return decode_simple(data[o], data[o + 2:o + 12])


def dump_json(doc):
    lines = ["{", '    "instruments": [']
    insts = doc["instruments"]
    for i, inst in enumerate(insts):
        comma = "," if i < len(insts) - 1 else ""
        if inst["type"] in ("keySplit", "drumSet"):
            key = "regions" if inst["type"] == "keySplit" else "keys"
            head = {k: v for k, v in inst.items() if k != key}
            s = json.dumps(head)[:-1] + f', "{key}": ['
            subs = inst[key]
            lines.append("        " + s)
            for j, r in enumerate(subs):
                lines.append("            " + json.dumps(r) + ("," if j < len(subs) - 1 else ""))
            lines.append("        ]}" + comma)
        else:
            lines.append("        " + json.dumps(inst) + comma)
    lines += ["    ]", "}"]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("json")
    p.add_argument("out")
    p = sub.add_parser("to-json")
    p.add_argument("sbnk")
    p.add_argument("out", nargs="?")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "build":
            with open(a.json, encoding="utf-8") as f:
                data = build_sbnk(json.load(f))
            with open(a.out, "wb") as f:
                f.write(data)
        else:
            with open(a.sbnk, "rb") as f:
                text = dump_json(parse_sbnk(f.read()))
            if a.out:
                with open(a.out, "w") as f:
                    f.write(text)
            else:
                sys.stdout.write(text)
    except SbnkError as e:
        sys.exit(f"sbnk.py: {e}")


if __name__ == "__main__":
    main()
