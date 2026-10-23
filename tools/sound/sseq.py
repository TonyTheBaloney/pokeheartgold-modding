#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-23
"""Sequences (SSEQ): read, write, and convert to and from MIDI.

An SSEQ is the DS's MIDI: one stream of commands for up to 16 tracks. Track 0
starts at the top, allocates the other tracks (0xFE) and opens each at its own
address (0x93); every track then runs its own commands. Time is in ticks, 48 per
quarter note. A note command (0x00-0x7F) has a velocity and a length; with note-wait
off (0xC7 0) a note doesn't hold up its track, so chords are notes followed by a
rest (0x80) that moves time on.

Usage:
    sseq.py from-midi IN.mid OUT.sseq [--volume-scale N]   (pokeemerald's mid2agb)
    sseq.py to-midi IN.sseq OUT.mid
    sseq.py dump IN.sseq                                     (one command per line)

MIDI to SSEQ keeps: notes (with velocity and length), program change, volume (CC7),
pan (CC10), expression (CC11), modulation (CC1), pitch bend and bend range (RPN 0),
tempo, and a loop marked by MIDI markers or text events "loopStart" and "loopEnd"
(as in many GBA/DS conversions; "[" and "]" also work). Each MIDI channel becomes one
track (channel 10 is not special: give drums their own bank instrument).
"""

import argparse
import struct
import sys

TICKS_PER_QUARTER = 48
MAX_TRACKS = 16


class SseqError(Exception):
    pass


# ---------------------------------------------------------------- command table

# argument kinds: u8, s8, u16, s16, u24, var (MIDI-style variable length)
U8_COMMANDS = {
    0xC0: "pan", 0xC1: "volume", 0xC2: "master_volume", 0xC3: "transpose", 0xC4: "pitch_bend",
    0xC5: "bend_range", 0xC6: "priority", 0xC7: "note_wait", 0xC8: "tie", 0xC9: "portamento",
    0xCA: "mod_depth", 0xCB: "mod_speed", 0xCC: "mod_type", 0xCD: "mod_range", 0xCE: "portamento_on",
    0xCF: "portamento_time", 0xD0: "attack", 0xD1: "decay", 0xD2: "sustain", 0xD3: "release",
    0xD4: "loop_start", 0xD5: "expression", 0xD6: "print_var", 0xD7: "mute",
}
SIGNED_U8 = {0xC3, 0xC4}
VAR_OPS = {0xB0: "set_var", 0xB1: "add_var", 0xB2: "sub_var", 0xB3: "mul_var", 0xB4: "div_var",
           0xB5: "shift_var", 0xB6: "rand_var", 0xB7: "unk_b7", 0xB8: "cmp_eq", 0xB9: "cmp_ge",
           0xBA: "cmp_gt", 0xBB: "cmp_le", 0xBC: "cmp_lt", 0xBD: "cmp_ne"}
OTHER = {
    0x80: ("rest", ["var"]), 0x81: ("program", ["var"]),
    0x93: ("open_track", ["u8", "u24"]), 0x94: ("jump", ["u24"]), 0x95: ("call", ["u24"]),
    0xE0: ("mod_delay", ["u16"]), 0xE1: ("tempo", ["u16"]), 0xE3: ("sweep_pitch", ["s16"]),
    0xFC: ("loop_end", []), 0xFD: ("return", []), 0xFE: ("alloc_tracks", ["u16"]), 0xFF: ("end", []),
}
PREFIX_RANDOM, PREFIX_VAR, PREFIX_IF = 0xA0, 0xA1, 0xA2
NAME_TO_OP = {v: k for k, v in U8_COMMANDS.items()}
NAME_TO_OP.update({v: k for k, v in VAR_OPS.items()})
NAME_TO_OP.update({v[0]: k for k, v in OTHER.items()})


def arg_kinds(op):
    if op < 0x80:
        return ["u8", "var"]  # velocity, length
    if op in U8_COMMANDS:
        return ["s8" if op in SIGNED_U8 else "u8"]
    if op in VAR_OPS:
        return ["u8", "s16"]
    if op in OTHER:
        return OTHER[op][1]
    raise SseqError(f"unknown command 0x{op:02X}")


def read_var(d, o):
    v = 0
    start = o
    while True:
        b = d[o]
        o += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, o, o - start
        if o - start > 4:
            raise SseqError("variable-length number too long")


def write_var(v, size=None):
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append(0x80 | (v & 0x7F))
        v >>= 7
    while size is not None and len(out) < size:
        out.append(0x80)  # keep a non-minimal encoding as it was
    return bytes(reversed(out))


def read_arg(d, o, kind):
    if kind == "u8":
        return d[o], o + 1, None
    if kind == "s8":
        return struct.unpack_from("<b", d, o)[0], o + 1, None
    if kind == "u16":
        return struct.unpack_from("<H", d, o)[0], o + 2, None
    if kind == "s16":
        return struct.unpack_from("<h", d, o)[0], o + 2, None
    if kind == "u24":
        return d[o] | d[o + 1] << 8 | d[o + 2] << 16, o + 3, None
    if kind == "var":
        v, o2, n = read_var(d, o)
        return v, o2, n
    raise ValueError(kind)


def write_arg(v, kind, size=None):
    if kind == "u8":
        return bytes([v & 0xFF])
    if kind == "s8":
        return struct.pack("<b", v)
    if kind == "u16":
        return struct.pack("<H", v)
    if kind == "s16":
        return struct.pack("<h", v)
    if kind == "u24":
        return bytes([v & 0xFF, v >> 8 & 0xFF, v >> 16 & 0xFF])
    if kind == "var":
        return write_var(v, size)
    raise ValueError(kind)


class Command:
    """One command. args are the plain values; `prefix` is a list of A0/A1/A2 bytes in front."""
    __slots__ = ("op", "args", "prefix", "sizes", "offset")

    def __init__(self, op, args, prefix=(), sizes=None, offset=None):
        self.op, self.args, self.prefix, self.sizes, self.offset = op, list(args), list(prefix), sizes, offset

    def name(self):
        if self.op < 0x80:
            return "note"
        return (U8_COMMANDS.get(self.op) or VAR_OPS.get(self.op) or OTHER[self.op][0])

    def kinds(self):
        """The argument kinds as stored: a random or var prefix replaces the last argument."""
        k = arg_kinds(self.op)
        for p in self.prefix:
            if p == PREFIX_RANDOM:
                k = k[:-1] + ["s16", "s16"]
            elif p == PREFIX_VAR:
                k = k[:-1] + ["u8"]
        return k

    def encode(self):
        out = bytes(self.prefix) + bytes([self.op])
        for i, (v, kind) in enumerate(zip(self.args, self.kinds())):
            out += write_arg(v, kind, (self.sizes or {}).get(i))
        return out

    def __repr__(self):
        p = "".join(f"{x:02X}:" for x in self.prefix)
        return f"{p}{self.name()}({', '.join(map(str, self.args))})"


def decode_command(d, o):
    try:
        return _decode_command(d, o)
    except IndexError:
        raise SseqError(f"command at 0x{o:X} runs past the end of the data") from None


def _decode_command(d, o):
    start = o
    prefix = []
    while d[o] in (PREFIX_RANDOM, PREFIX_VAR, PREFIX_IF):
        prefix.append(d[o])
        o += 1
    op = d[o]
    o += 1
    cmd = Command(op, [], prefix, offset=start)
    sizes = {}
    for i, kind in enumerate(cmd.kinds()):
        v, o, n = read_arg(d, o, kind)
        if n is not None and write_var(v) != d[o - n:o]:
            sizes[i] = n
        cmd.args.append(v)
    cmd.sizes = sizes or None
    return cmd, o


# ---------------------------------------------------------------- file


def parse_sseq(data):
    """Return (commands, data_start): every command in the data block, in address order."""
    if data[:4] != b"SSEQ" or data[16:20] != b"DATA":
        raise SseqError("not an SSEQ file")
    size = struct.unpack_from("<I", data, 8)[0]
    start = struct.unpack_from("<I", data, 24)[0]
    cmds = []
    o = start
    while o < size:
        if size - o < 4 and not any(data[o:size]):
            break  # the file is zero-padded to 4 bytes
        cmd, o = decode_command(data, o)
        cmds.append(cmd)
    if o > size:
        raise SseqError("last command runs past the end of the file")
    return cmds, start


def build_sseq(body):
    """Wrap command bytes (addresses relative to the data start) into an SSEQ file."""
    data_start = 0x1C
    size = data_start + len(body)
    pad = (-size) % 4
    body += b"\0" * pad
    size += pad
    return (b"SSEQ" + struct.pack("<HHIHH", 0xFEFF, 0x0100, size, 0x10, 1)
            + b"DATA" + struct.pack("<II", size - 0x10, data_start) + body)


# ---------------------------------------------------------------- playback model


def track_starts(cmds, data_start):
    by_off = {c.offset: i for i, c in enumerate(cmds)}
    starts = {0: 0}
    for c in cmds:
        if c.op == 0x93 and not c.prefix:
            starts[c.args[0]] = by_off.get(c.args[1] + data_start)
    return starts, by_off


def play_track(cmds, by_off, start_index, data_start, max_ticks=1 << 20):
    """Follow one track the way the sound driver does (NitroSDK snd_seq.c): jumps,
    calls, loops, note-wait (on by default: a note holds the track for its length).
    A jump backwards, or an endless loop, ends the walk.
    Returns (events, end_tick, loop): events are (tick, Command) in play order, loop is
    (loop_start_tick, loop_end_tick) or None."""
    i = start_index
    tick = 0
    note_wait = True
    stack = []
    loops = []
    seen_at = {}
    events = []
    loop = None
    steps = 0
    while i is not None and i < len(cmds):
        steps += 1
        if steps > 200000 or tick > max_ticks:
            break
        c = cmds[i]
        if c.prefix:  # random / var / if: depends on the game at run time
            events.append((tick, c))
            if PREFIX_RANDOM not in c.prefix and PREFIX_VAR not in c.prefix:
                if c.op == 0x80 or (c.op < 0x80 and note_wait):
                    tick += c.args[-1]
            i += 1
            continue
        if c.op == 0x94:  # jump
            target = by_off.get(c.args[0] + data_start)
            if target is not None and target <= i and not stack:
                loop = (seen_at.get(target, 0), tick)
                break
            i = target
            continue
        if c.op == 0x95:  # call
            stack.append(i + 1)
            i = by_off.get(c.args[0] + data_start)
            continue
        if c.op == 0xFD:  # return
            if not stack:
                break
            i = stack.pop()
            continue
        if c.op == 0xD4:  # loop start (count 0 = forever)
            loops.append([i + 1, c.args[0]])
            i += 1
            continue
        if c.op == 0xFC:  # loop end
            if loops:
                lp = loops[-1]
                if lp[1] == 0:
                    loop = (seen_at.get(lp[0], 0), tick)
                    break
                lp[1] -= 1
                if lp[1] > 0:
                    i = lp[0]
                    continue
                loops.pop()
            i += 1
            continue
        if c.op == 0xFF:
            break
        seen_at.setdefault(i, tick)
        events.append((tick, c))
        if c.op == 0x80:
            tick += c.args[0]
        elif c.op == 0xC7:
            note_wait = bool(c.args[0])
        elif c.op < 0x80 and note_wait:
            tick += c.args[1]
        i += 1
    return events, tick, loop


# ---------------------------------------------------------------- MIDI files


def _midi_var(v):
    return write_var(v)


def read_midi(data):
    """Return (division, tracks): tracks are lists of (abs_tick, bytes_event)."""
    if data[:4] != b"MThd":
        raise SseqError("not a MIDI file")
    hlen, fmt, ntrk, division = struct.unpack_from(">IHHH", data, 4)
    if division & 0x8000:
        raise SseqError("SMPTE time division is not supported")
    o = 8 + hlen
    tracks = []
    for _ in range(ntrk):
        if data[o:o + 4] != b"MTrk":
            raise SseqError("bad MIDI track")
        tlen = struct.unpack_from(">I", data, o + 4)[0]
        p, end = o + 8, o + 8 + tlen
        tick, running, evs = 0, None, []
        while p < end:
            dt, p, _ = read_var(data, p)
            tick += dt
            st = data[p]
            if st == 0xFF:
                typ = data[p + 1]
                ln, q, _ = read_var(data, p + 2)
                evs.append((tick, ("meta", typ, data[q:q + ln])))
                p = q + ln
                continue
            if st in (0xF0, 0xF7):
                ln, q, _ = read_var(data, p + 1)
                p = q + ln
                continue
            if st & 0x80:
                running = st
                p += 1
            elif running is None:
                raise SseqError("MIDI running status without a status byte")
            st = running
            n = 1 if st >> 4 in (0xC, 0xD) else 2
            evs.append((tick, ("ch", st >> 4, st & 0xF, tuple(data[p:p + n]))))
            p += n
        tracks.append(evs)
        o = end
    return division, tracks


def write_midi(tracks, division=TICKS_PER_QUARTER):
    out = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), division)
    for evs in tracks:
        body = b""
        last = 0
        # at the same tick: tempo/meta first, then note-offs, then the rest
        for tick, raw in sorted(evs, key=lambda e: (e[0], 0 if e[1][0] == 0xFF else 1 if e[1][0] >> 4 == 0x8 else 2)):
            body += _midi_var(tick - last) + raw
            last = tick
        body += b"\x00\xFF\x2F\x00"
        out += b"MTrk" + struct.pack(">I", len(body)) + body
    return out


# ---------------------------------------------------------------- MIDI -> SSEQ

LOOP_START_TEXT = {"loopstart", "[", "loop_start"}
LOOP_END_TEXT = {"loopend", "]", "loop_end"}


def midi_to_sseq(midi_bytes, volume_scale=1.0, note_wait_off=True):
    division, mtracks = read_midi(midi_bytes)

    def scale(t):
        return (t * TICKS_PER_QUARTER + division // 2) // division

    # gather per-channel events and global ones (tempo, loop markers)
    chans = {}
    tempos, loop_start, loop_end = [], None, None
    for evs in mtracks:
        active = {}
        for tick, ev in evs:
            t = scale(tick)
            if ev[0] == "meta":
                typ, payload = ev[1], ev[2]
                if typ == 0x51 and len(payload) == 3:
                    us = payload[0] << 16 | payload[1] << 8 | payload[2]
                    tempos.append((t, max(1, min(0xFFFF, round(60_000_000 / us)))))
                elif typ in (0x01, 0x06):
                    txt = payload.decode("latin-1").strip().lower()
                    if txt in LOOP_START_TEXT:
                        loop_start = t
                    elif txt in LOOP_END_TEXT:
                        loop_end = t
                continue
            _, kind, ch, args = ev
            c = chans.setdefault(ch, {"notes": [], "ctrl": []})
            if kind == 0x9 and args[1] > 0:
                active.setdefault((ch, args[0]), []).append((t, args[1]))
            elif kind == 0x8 or (kind == 0x9 and args[1] == 0):
                st = active.get((ch, args[0]))
                if st:
                    t0, vel = st.pop(0)
                    c["notes"].append((t0, args[0], vel, max(1, t - t0)))
            elif kind == 0xC:
                c["ctrl"].append((t, 0x81, args[0]))
            elif kind == 0xB:
                cc, val = args
                if cc == 7:
                    c["ctrl"].append((t, 0xC1, min(127, round(val * volume_scale))))
                elif cc == 10:
                    c["ctrl"].append((t, 0xC0, val))
                elif cc == 11:
                    c["ctrl"].append((t, 0xD5, val))
                elif cc == 1:
                    c["ctrl"].append((t, 0xCA, val))
                elif cc in (100, 101):
                    c.setdefault("rpn", {})[cc] = val
                elif cc == 6 and c.get("rpn", {}).get(100) == 0 and c.get("rpn", {}).get(101) == 0:
                    c["ctrl"].append((t, 0xC5, val))
            elif kind == 0xE:
                bend = (args[1] << 7 | args[0]) - 8192
                c["ctrl"].append((t, 0xC4, max(-128, min(127, bend // 64))))
    used = sorted(ch for ch, c in chans.items() if c["notes"])
    if not used:
        raise SseqError("the MIDI file has no notes")
    if len(used) > MAX_TRACKS:
        raise SseqError(f"{len(used)} channels with notes; a sequence has at most {MAX_TRACKS} tracks")

    song_end = max(n[0] + n[3] for ch in used for n in chans[ch]["notes"])
    if loop_end is None and loop_start is not None:
        loop_end = song_end
    if loop_start is not None and loop_end is not None and loop_end <= loop_start:
        raise SseqError("loop end is not after loop start")
    end_tick = loop_end if loop_end is not None else song_end

    # each track: (bytes, offset of the loop start in them or None)
    tracks = []
    for n, ch in enumerate(used):
        items = []  # (tick, order, bytes); order puts setup before notes at the same tick
        if n == 0:
            for t, bpm in tempos or [(0, 120)]:
                items.append((t, 0, bytes([0xE1]) + struct.pack("<H", bpm)))
        if note_wait_off:
            items.append((0, -1, bytes([0xC7, 0])))
        for t, op, val in chans[ch]["ctrl"]:
            items.append((t, 1, bytes([op]) + (write_var(val) if op == 0x81 else bytes([val & 0xFF]))))
        for t, key, vel, length in chans[ch]["notes"]:
            if t >= end_tick:
                continue
            if loop_end is not None:
                length = max(1, min(length, loop_end - t))
            items.append((t, 2, bytes([key, vel]) + write_var(length)))
        if loop_start is not None:
            items.append((loop_start, -2, None))
        items.sort(key=lambda x: (x[0], x[1]))
        out, loop_at, now = bytearray(), None, 0
        for t, _, raw in items:
            if t > end_tick:
                continue
            if t > now:
                out += bytes([0x80]) + write_var(t - now)
                now = t
            if raw is None:
                loop_at = len(out)
            else:
                out += raw
        if end_tick > now:
            out += bytes([0x80]) + write_var(end_tick - now)
        tracks.append((out, loop_at))

    # track 0 starts with: allocate tracks, open each other track at its address
    n = len(tracks)
    head = 3 + 5 * (n - 1)
    addrs, pos = [], head
    for out, loop_at in tracks:
        addrs.append(pos)
        pos += len(out) + (4 if loop_at is not None else 1)  # jump (4) or end (1)
    body = bytearray([0xFE]) + struct.pack("<H", (1 << n) - 1)
    for i in range(1, n):
        body += bytes([0x93, i]) + write_arg(addrs[i], "u24")
    for (out, loop_at), addr in zip(tracks, addrs):
        body += out
        body += (bytes([0x94]) + write_arg(addr + loop_at, "u24")) if loop_at is not None else bytes([0xFF])
    return build_sseq(bytes(body))


# ---------------------------------------------------------------- SSEQ -> MIDI


def sseq_to_midi(data):
    cmds, start = parse_sseq(data)
    starts, by_off = track_starts(cmds, start)
    mtracks = []
    for tr in sorted(starts):
        if starts[tr] is None:
            continue
        events, end, loop = play_track(cmds, by_off, starts[tr], start)
        ch = tr % 16
        evs = []
        transpose = 0
        first = tr == 0
        if first and loop:
            evs.append((loop[0], b"\xFF\x06" + _midi_var(9) + b"loopStart"))
            evs.append((loop[1], b"\xFF\x06" + _midi_var(7) + b"loopEnd"))
        for tick, c in events:
            if c.prefix:
                continue
            op = c.op
            if op < 0x80:
                vel, length = c.args
                key = max(0, min(127, op + transpose))
                evs.append((tick, bytes([0x90 | ch, key, max(1, vel)])))
                evs.append((tick + max(1, length), bytes([0x80 | ch, key, 0])))
            elif op == 0xC3:
                transpose = c.args[0]
            elif op == 0x81:
                evs.append((tick, bytes([0xC0 | ch, c.args[0] & 0x7F])))
            elif op == 0xE1:
                us = round(60_000_000 / max(1, c.args[0]))
                evs.append((tick, b"\xFF\x51\x03" + us.to_bytes(3, "big")))
            elif op in (0xC1, 0xC0, 0xD5, 0xCA):
                cc = {0xC1: 7, 0xC0: 10, 0xD5: 11, 0xCA: 1}[op]
                evs.append((tick, bytes([0xB0 | ch, cc, c.args[0] & 0x7F])))
            elif op == 0xC5:
                evs += [(tick, bytes([0xB0 | ch, 101, 0])), (tick, bytes([0xB0 | ch, 100, 0])),
                        (tick, bytes([0xB0 | ch, 6, c.args[0] & 0x7F]))]
            elif op == 0xC4:
                v = max(0, min(16383, c.args[0] * 64 + 8192))
                evs.append((tick, bytes([0xE0 | ch, v & 0x7F, v >> 7])))
        mtracks.append(evs)
    return write_midi(mtracks)


# ---------------------------------------------------------------- main


def dump(data):
    cmds, start = parse_sseq(data)
    return "\n".join(f"{c.offset - start:06X}  {c!r}" for c in cmds)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("from-midi")
    p.add_argument("midi")
    p.add_argument("out")
    p.add_argument("--volume-scale", type=float, default=1.0)
    p = sub.add_parser("to-midi")
    p.add_argument("sseq")
    p.add_argument("out")
    p = sub.add_parser("dump")
    p.add_argument("sseq")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "from-midi":
            with open(a.midi, "rb") as f:
                out = midi_to_sseq(f.read(), a.volume_scale)
            with open(a.out, "wb") as f:
                f.write(out)
        elif a.cmd == "to-midi":
            with open(a.sseq, "rb") as f:
                out = sseq_to_midi(f.read())
            with open(a.out, "wb") as f:
                f.write(out)
        else:
            with open(a.sseq, "rb") as f:
                print(dump(f.read()))
    except SseqError as e:
        sys.exit(f"sseq.py: {e}")


if __name__ == "__main__":
    main()
