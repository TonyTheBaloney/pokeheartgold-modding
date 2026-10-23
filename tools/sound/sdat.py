#!/usr/bin/env python3
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-23
"""The sound archive (SDAT) as files, rebuilt byte for byte.

The game keeps all music, sound effects and cries in one Nintendo SDK sound archive,
files/data/sound/gs_sound_data.sdat. `unpack` splits it into one file per sequence,
instrument bank and wave archive plus an index, sound/sound_data.json; `pack` builds
the archive back from them. Unchanged files give back the original archive exactly.

sound/sound_data.json is to the archive what pokeemerald's sound/song_table.inc plus
the voicegroup assignments are to the GBA sound data. Each list is in id order (a
sequence's SEQ_* value in include/constants/sndseq.h is its index in "sequences");
`null` keeps the id of an empty slot:

    "sequences": [
        {"name": "SEQ_GS_T_WAKABA", "file": "sequences/SEQ_GS_T_WAKABA.sseq",
         "bank": "BANK_BGM_FIELD", "volume": 127, "channelPriority": 64,
         "playerPriority": 64, "player": "PLAYER_FIELD"},
        ...
    ],
    "banks": [{"name": ..., "file": "banks/X.sbnk", "waveArchives": ["WAVE_ARC_X", null, null, null]}],
    "waveArchives": [{"name": ..., "file": "wave_archives/X.swar"}],
    "players": [{"name": "PLAYER_BGM", "maxSequences": 1, "channels": 65534, "heapSize": 0}],
    "groups": [{"name": "GROUP_GLOBAL", "entries": [{"type": "seq", "name": "SEQ_X", "load": 7}]}]

Entries that share a file name the same "file"; it is stored once. A "file" may also
be a source the pack step converts: a .mid for a sequence (sseq.py), a .json for a
bank (sbnk.py) or a wave archive (swar.py, with its WAV samples). See
docs/modding/music.md.

"constant" gives an entry a C name different from the name stored in the archive
(SEQ_SE_DP_NAGERU is SEQ_SE_DP_THROW in the C code); the archive keeps its own.

Usage:
    sdat.py unpack ARCHIVE.sdat OUT_DIR
    sdat.py pack SOUND_DATA.json OUT.sdat [--depfile F] [--check-header sndseq.h]
    sdat.py header SOUND_DATA.json OUT.h        (writes include/constants/sndseq.h)
"""

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbnk  # noqa: E402
import sseq  # noqa: E402
import swar  # noqa: E402

NUM_RECORDS = 8
REC_SEQ, REC_SEQARC, REC_BANK, REC_WAVEARC, REC_PLAYER, REC_GROUP, REC_PLAYER2, REC_STRM = range(NUM_RECORDS)
NO_WAVEARC = 0xFFFF
GROUP_TYPES = {0: "seq", 1: "bank", 2: "waveArchive", 3: "seqArchive"}
GROUP_TYPE_IDS = {v: k for k, v in GROUP_TYPES.items()}
FILE_ALIGN = 0x20
HEADER_SIZE = 0x40
BLOCK_HEADER_SIZE = 0x40  # SYMB and INFO: magic, size, 8 record offsets, 24 reserved


class SdatError(Exception):
    pass


def align(n, a):
    return (n + a - 1) // a * a


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


# ---------------------------------------------------------------- reading


def read_sdat(data):
    """Return (doc, files): doc as in sound_data.json but with "file" = FAT index, files = list of bytes."""
    if data[:4] != b"SDAT" or u16(data, 4) != 0xFEFF:
        raise SdatError("not an SDAT file")
    symb, _, info, _, fat, _, fil, _ = struct.unpack_from("<8I", data, 16)
    if not symb:
        raise SdatError("archive has no symbol block; names are needed")

    srec = [u32(data, symb + 8 + 4 * i) for i in range(NUM_RECORDS)]
    irec = [u32(data, info + 8 + 4 * i) for i in range(NUM_RECORDS)]
    for i in (REC_SEQARC, REC_PLAYER2, REC_STRM):
        if u32(data, info + irec[i]) or u32(data, symb + srec[i]):
            raise SdatError("sequence archives, PLAYER2 and streams are not supported")

    def string(off):
        return data[symb + off:data.index(b"\0", symb + off)].decode("ascii") if off else None

    def names(rec):
        base = symb + srec[rec]
        return [string(u32(data, base + 4 + 4 * j)) for j in range(u32(data, base))]

    def entries(rec):
        base = info + irec[rec]
        return [u32(data, base + 4 + 4 * j) for j in range(u32(data, base))]

    def entry_name(rec, idx, table):
        if idx >= len(table) or table[idx] is None:
            raise SdatError(f"record {rec} entry {idx} has no name")
        return table[idx]

    nseq, nbank, nwa, nply, ngrp = (names(r) for r in (REC_SEQ, REC_BANK, REC_WAVEARC, REC_PLAYER, REC_GROUP))
    doc = {"sequences": [], "banks": [], "waveArchives": [], "players": [], "groups": []}

    def check_null(rec, j, name, off):
        if (name is None) != (off == 0):
            raise SdatError(f"record {rec} entry {j}: a name without info or info without a name")

    for j, off in enumerate(entries(REC_WAVEARC)):
        check_null(REC_WAVEARC, j, nwa[j], off)
        if not off:
            doc["waveArchives"].append(None)
            continue
        fid = u32(data, info + off)
        e = {"name": nwa[j], "file": fid & 0xFFFFFF}
        if fid >> 24:
            e["flags"] = fid >> 24
        doc["waveArchives"].append(e)

    for j, off in enumerate(entries(REC_BANK)):
        check_null(REC_BANK, j, nbank[j], off)
        if not off:
            doc["banks"].append(None)
            continue
        fid, unk = struct.unpack_from("<HH", data, info + off)
        was = struct.unpack_from("<4H", data, info + off + 4)
        e = {"name": nbank[j], "file": fid,
             "waveArchives": [None if w == NO_WAVEARC else entry_name(REC_WAVEARC, w, nwa) for w in was]}
        if unk:
            e["unk2"] = unk
        doc["banks"].append(e)

    for j, off in enumerate(entries(REC_PLAYER)):
        check_null(REC_PLAYER, j, nply[j], off)
        if not off:
            doc["players"].append(None)
            continue
        maxseq, pad, chans, heap = struct.unpack_from("<BBHI", data, info + off)
        e = {"name": nply[j], "maxSequences": maxseq, "channels": chans, "heapSize": heap}
        if pad:
            e["unk1"] = pad
        doc["players"].append(e)

    for j, off in enumerate(entries(REC_SEQ)):
        check_null(REC_SEQ, j, nseq[j], off)
        if not off:
            doc["sequences"].append(None)
            continue
        fid, unk, bank, vol, cpr, ppr, ply, unk2 = struct.unpack_from("<HHHBBBBH", data, info + off)
        e = {"name": nseq[j], "file": fid, "bank": entry_name(REC_BANK, bank, nbank), "volume": vol,
             "channelPriority": cpr, "playerPriority": ppr, "player": entry_name(REC_PLAYER, ply, nply)}
        if unk:
            e["unk2"] = unk
        if unk2:
            e["unk10"] = unk2
        doc["sequences"].append(e)

    tables = {"seq": (REC_SEQ, nseq), "bank": (REC_BANK, nbank), "waveArchive": (REC_WAVEARC, nwa)}
    for j, off in enumerate(entries(REC_GROUP)):
        check_null(REC_GROUP, j, ngrp[j], off)
        if not off:
            doc["groups"].append(None)
            continue
        items = []
        for k in range(u32(data, info + off)):
            typ, load, pad, idx = struct.unpack_from("<BBHI", data, info + off + 4 + 8 * k)
            tname = GROUP_TYPES.get(typ)
            if tname not in tables or pad:
                raise SdatError(f"group {ngrp[j]}: unsupported entry type {typ}")
            items.append({"type": tname, "name": entry_name(*tables[tname][:1], idx, tables[tname][1]), "load": load})
        doc["groups"].append({"name": ngrp[j], "entries": items})

    if data[fil:fil + 4] != b"FILE" or data[fat:fat + 4] != b"FAT ":
        raise SdatError("bad FAT or FILE block")
    files = []
    for k in range(u32(data, fat + 8)):
        o, size = struct.unpack_from("<II", data, fat + 12 + 16 * k)
        files.append(data[o:o + size])
    return doc, files


# ---------------------------------------------------------------- writing


def _index(table, name, what):
    if name is None:
        return None
    for i, e in enumerate(table):
        if e is not None and e["name"] == name:
            return i
    raise SdatError(f"unknown {what} {name!r}")


def write_sdat(doc, load_file):
    """Build the archive. load_file(key) returns the bytes of the file an entry names."""
    seqs, banks, was, plys, grps = (doc[k] for k in ("sequences", "banks", "waveArchives", "players", "groups"))

    # files, numbered in order of first use: sequences, banks, wave archives
    file_ids, files = {}, []

    def file_id(key):
        if key not in file_ids:
            file_ids[key] = len(files)
            files.append(load_file(key))
        return file_ids[key]

    seq_info, bank_info, wa_info = [], [], []
    for e in seqs:
        if e is None:
            seq_info.append(None)
            continue
        fid = file_id(e["file"])
        ply = plys[_index(plys, e["player"], "player")]
        # a player with its own heap loads the sequence into it (every retail sequence fits)
        if ply["heapSize"] and len(files[fid]) > ply["heapSize"]:
            raise SdatError(f"{e['name']}: {len(files[fid])} bytes doesn't fit {ply['name']}'s "
                            f"{ply['heapSize']}-byte heap; shorten it or use PLAYER_BGM")
        seq_info.append(struct.pack("<HHHBBBBH", fid, e.get("unk2", 0), _index(banks, e["bank"], "bank"),
                                    e["volume"], e["channelPriority"], e["playerPriority"],
                                    _index(plys, e["player"], "player"), e.get("unk10", 0)))
    for e in banks:
        if e is None:
            bank_info.append(None)
            continue
        wl = list(e.get("waveArchives", [])) + [None] * 4
        if len(e.get("waveArchives", [])) > 4:
            raise SdatError(f"{e['name']}: a bank uses at most 4 wave archives")
        ids = [NO_WAVEARC if w is None else _index(was, w, "wave archive") for w in wl[:4]]
        bank_info.append(struct.pack("<HH4H", file_id(e["file"]), e.get("unk2", 0), *ids))
    for e in was:
        wa_info.append(None if e is None else struct.pack("<I", file_id(e["file"]) | e.get("flags", 0) << 24))
    ply_info = [None if e is None else struct.pack("<BBHI", e["maxSequences"], e.get("unk1", 0), e["channels"], e["heapSize"])
                for e in plys]
    tables = {"seq": seqs, "bank": banks, "waveArchive": was}
    grp_info = []
    for e in grps:
        if e is None:
            grp_info.append(None)
            continue
        b = struct.pack("<I", len(e["entries"]))
        for it in e["entries"]:
            b += struct.pack("<BBHI", GROUP_TYPE_IDS[it["type"]], it["load"], 0,
                             _index(tables[it["type"]], it["name"], it["type"]))
        grp_info.append(b)

    records = [seq_info, [], bank_info, wa_info, ply_info, grp_info, [], []]
    record_names = [[None if e is None else e["name"] for e in r]
                    for r in (seqs, [], banks, was, plys, grps, [], [])]

    # SYMB: header, each record's table, then every name in record order
    symb = bytearray(BLOCK_HEADER_SIZE)
    strings = bytearray()
    tables_size = sum(4 + 4 * len(r) for r in record_names)
    str_base = BLOCK_HEADER_SIZE + tables_size
    for i, rn in enumerate(record_names):
        struct.pack_into("<I", symb, 8 + 4 * i, len(symb))
        symb += struct.pack("<I", len(rn))
        for n in rn:
            if n is None:
                symb += b"\0\0\0\0"
            else:
                symb += struct.pack("<I", str_base + len(strings))
                strings += n.encode("ascii") + b"\0"
    symb += strings
    symb_size = len(symb)
    symb += b"\0" * (align(symb_size, 4) - symb_size)
    symb[0:8] = b"SYMB" + struct.pack("<I", len(symb))

    # INFO: each record's table followed by its entries
    info = bytearray(BLOCK_HEADER_SIZE)
    for i, r in enumerate(records):
        struct.pack_into("<I", info, 8 + 4 * i, len(info))
        table_at = len(info)
        info += struct.pack("<I", len(r)) + b"\0" * (4 * len(r))
        for j, e in enumerate(r):
            if e is not None:
                struct.pack_into("<I", info, table_at + 4 + 4 * j, len(info))
                info += e
    info += b"\0" * (align(len(info), 4) - len(info))
    info[0:8] = b"INFO" + struct.pack("<I", len(info))

    symb_off = HEADER_SIZE
    info_off = symb_off + len(symb)
    fat_off = info_off + len(info)
    fat_size = 12 + 16 * len(files)
    file_off = fat_off + fat_size

    fat = bytearray(b"FAT " + struct.pack("<II", fat_size, len(files)))
    body = bytearray()
    pos = align(file_off + 16, FILE_ALIGN)
    first = pos - file_off
    for f in files:
        fat += struct.pack("<IIII", pos, len(f), 0, 0)
        body += f
        nxt = align(pos + len(f), FILE_ALIGN)
        body += b"\0" * (nxt - pos - len(f))
        pos = nxt
    file_size = pos - file_off
    fileblk = b"FILE" + struct.pack("<III", file_size, len(files), 0) + b"\0" * (first - 16) + body

    header = struct.pack("<4sHHIHH8I", b"SDAT", 0xFEFF, 0x0100, file_off + file_size, HEADER_SIZE, 4,
                         symb_off, symb_size, info_off, len(info), fat_off, fat_size, file_off, file_size)
    header += b"\0" * (HEADER_SIZE - len(header))
    return bytes(header + symb + info + fat + fileblk)


# ---------------------------------------------------------------- unpack / pack

DIRS = {"sequences": ("sequences", ".sseq"), "banks": ("banks", ".sbnk"), "waveArchives": ("wave_archives", ".swar")}


def unpack(sdat_path, out_dir):
    with open(sdat_path, "rb") as f:
        doc, files = read_sdat(f.read())
    paths = {}
    for key, (sub, ext) in DIRS.items():
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)
        for e in doc[key]:
            if e is None:
                continue
            fid = e["file"]
            if fid not in paths:
                paths[fid] = f"{sub}/{e['name']}{ext}"
                with open(os.path.join(out_dir, paths[fid]), "wb") as f:
                    f.write(files[fid])
            e["file"] = paths[fid]
    with open(os.path.join(out_dir, "sound_data.json"), "w") as f:
        f.write(dump_json(doc))


def dump_json(doc):
    """One entry per line, so a diff shows which sound changed."""
    out = ["{"]
    keys = list(doc)
    for i, k in enumerate(keys):
        out.append(f'    "{k}": [')
        items = doc[k]
        for j, e in enumerate(items):
            comma = "," if j < len(items) - 1 else ""
            out.append("        " + json.dumps(e, ensure_ascii=False) + comma)
        out.append("    ]" + ("," if i < len(keys) - 1 else ""))
    out.append("}")
    return "\n".join(out) + "\n"


def load_doc(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def file_loader(doc, base, inputs):
    """load(key) for write_sdat: reads a binary, or builds one from a source file:
    a sequence from .mid, a bank or wave archive from .json. Every file read is
    added to `inputs` (for the depfile)."""
    kinds = {}
    for key in ("sequences", "banks", "waveArchives"):
        for e in doc[key]:
            if e is not None:
                kinds.setdefault(e["file"], key)

    def read(path):
        inputs.append(path)
        with open(path, "rb") as f:
            return f.read()

    def load(key):
        path = os.path.join(base, key)
        if not os.path.exists(path):
            raise SdatError(f"file not found: {key}")
        kind, ext = kinds.get(key), os.path.splitext(key)[1].lower()
        try:
            if kind == "sequences" and ext in (".mid", ".midi"):
                return sseq.midi_to_sseq(read(path))
            if kind == "banks" and ext == ".json":
                return sbnk.build_sbnk(json.loads(read(path)))
            if kind == "waveArchives" and ext == ".json":
                return swar.build_bytes(path, inputs)
        except (sseq.SseqError, sbnk.SbnkError, swar.SwarError, ValueError, KeyError) as e:
            raise SdatError(f"{key}: {e}") from None
        return read(path)
    return load


def pack(json_path, out_path, depfile=None, check_header=None):
    doc = load_doc(json_path)
    if check_header:
        with open(check_header) as f:
            if f.read() != header_text(doc):
                raise SdatError(f"{check_header} doesn't match {json_path}; run "
                                f"tools/sound/sdat.py header {json_path} {check_header}")
    inputs = [os.path.abspath(json_path)]
    data = write_sdat(doc, file_loader(doc, os.path.dirname(os.path.abspath(json_path)), inputs))
    with open(out_path, "wb") as f:
        f.write(data)
    if depfile:
        with open(depfile, "w") as f:
            deps = " ".join(os.path.abspath(p).replace(" ", "\\ ") for p in dict.fromkeys(inputs))
            f.write(f"{out_path}: {deps}\n")


HEADER_TAIL = [  # not archive entries; values the field sound code uses
    ("ENVIRONMENT_SOUND_NONE", -1),
    ("ENVIRONMENT_SOUND_NONE_UNK2", -2),
    ("ENVIRONMENT_SOUND_NONE_UNK3", -3),
]


def constant(e):
    """The C name: "constant" when the source renamed it, else the archive's name."""
    return e.get("constant", e["name"])


def header_text(doc):
    """include/constants/sndseq.h: SEQ_*, BANK_*, WAVE_ARC_*, PLAYER_*, GROUP_* in id order."""
    sections = []
    for key in ("sequences", "banks", "waveArchives", "players", "groups"):
        named = [(constant(e), i) for i, e in enumerate(doc[key]) if e is not None]
        if key == "sequences":
            named.insert(0, ("SEQ_NONE", 0))
        sections.append(named)
    sections.append(HEADER_TAIL)
    lines = ["#ifndef POKEHEARTGOLD_CONSTANTS_SNDSEQ_H", "#define POKEHEARTGOLD_CONSTANTS_SNDSEQ_H", ""]
    for named in sections:
        width = max(len(n) for n, _ in named) + 1
        lines += [f"#define {n:<{width}}{v}" for n, v in named] + [""]
    lines.append("#endif // POKEHEARTGOLD_CONSTANTS_SNDSEQ_H")
    return "\n".join(lines) + "\n"


def write_header(json_path, out_path):
    with open(out_path, "w") as f:
        f.write(header_text(load_doc(json_path)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("unpack")
    p.add_argument("sdat")
    p.add_argument("out_dir")
    p = sub.add_parser("pack")
    p.add_argument("json")
    p.add_argument("out")
    p.add_argument("--depfile", help="write a Makefile-style list of every file read")
    p.add_argument("--check-header", help="fail if this sndseq.h doesn't match the JSON")
    p = sub.add_parser("header")
    p.add_argument("json")
    p.add_argument("out")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "unpack":
            unpack(a.sdat, a.out_dir)
        elif a.cmd == "pack":
            pack(a.json, a.out, a.depfile, a.check_header)
        else:
            write_header(a.json, a.out)
    except SdatError as e:
        sys.exit(f"sdat.py: {e}")


if __name__ == "__main__":
    main()
