#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-23
"""Wave archives (SWAR): samples to and from WAV files.

A wave archive is a list of samples (SWAV): format, loop, sample rate, data. A bank's
instruments name a sample by its index in one of the bank's wave archives.

Like pokeemerald's sound/direct_sound_samples/*.wav, new samples are WAV files. A
wave archive is described by a JSON file listing them:

    {
        "waves": [
            {"file": "samples/flute_c5.wav", "format": "adpcm"},
            {"file": "samples/strings.wav", "format": "pcm8", "loopStart": 1200}
        ]
    }

file        WAV, PCM 8/16/24/32-bit, any rate, mono (stereo is mixed down). Path is
            relative to the JSON file.
format      "adpcm" (IMA-ADPCM, 4 bits a sample: the game's choice for most music),
            "pcm8" or "pcm16". Default "adpcm".
loopStart   sample where the loop starts; the loop runs to the end. Default: the WAV's
            own loop ("smpl" chunk) if it has one, else no loop. "loop": false turns
            a WAV's loop off.
rate        override the WAV's sample rate (Hz, at most 65535).

The loop start moves to a 4-byte boundary (8 samples for ADPCM, 4 for pcm8, 2 for
pcm16), as the hardware needs.

Usage:
    swar.py build ARCHIVE.json OUT.swar
    swar.py extract IN.swar OUT_DIR      (WAVs + archive JSON; ADPCM decoded to 16-bit)
"""

import argparse
import json
import os
import struct
import sys
import wave

TIMER_CLOCK = 16756991  # SND_TIMER_CLOCK: the sound timer runs at the bus clock / 2
FORMATS = {"pcm8": 0, "pcm16": 1, "adpcm": 2}
FORMAT_NAMES = {v: k for k, v in FORMATS.items()}
SAMPLES_PER_WORD = {0: 4, 1: 2, 2: 8}

ADPCM_STEPS = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97,
    107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
    876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871,
    5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623,
    27086, 29794, 32767,
]
ADPCM_INDEX = [-1, -1, -1, -1, 2, 4, 6, 8]


class SwarError(Exception):
    pass


# ---------------------------------------------------------------- IMA-ADPCM, as the DS decodes it (GBATEK)


def _adpcm_step(pcm, index, nib):
    step = ADPCM_STEPS[index]
    diff = step >> 3
    if nib & 1:
        diff += step >> 2
    if nib & 2:
        diff += step >> 1
    if nib & 4:
        diff += step
    pcm = max(pcm - diff, -0x7FFF) if nib & 8 else min(pcm + diff, 0x7FFF)
    index = min(max(index + ADPCM_INDEX[nib & 7], 0), 88)
    return pcm, index


def adpcm_decode(data, count=None):
    pcm, index = struct.unpack_from("<hB", data, 0)
    index = min(index, 88)
    out = []
    for b in data[4:]:
        for nib in (b & 0xF, b >> 4):
            pcm, index = _adpcm_step(pcm, index, nib)
            out.append(pcm)
    return out[:count] if count is not None else out


def adpcm_encode(samples):
    """samples: list of ints (-32768..32767). Returns header + nibble bytes; each nibble is
    the one whose decoded value lands closest to the input (the decoder runs alongside)."""
    first = max(-0x7FFF, min(0x7FFF, samples[0] if samples else 0))
    # the starting step size matters for a sharp attack: try them all on the opening
    start_index = min(range(89), key=lambda i: _adpcm_run(samples[:64], first, i)[0])
    _, nibs = _adpcm_run(samples, first, start_index)
    if len(nibs) % 2:
        nibs.append(0)
    body = bytes(nibs[i] | nibs[i + 1] << 4 for i in range(0, len(nibs), 2))
    return struct.pack("<hBB", first, start_index, 0) + body


def _adpcm_run(samples, pcm, index):
    """Greedy encode: (total squared error, nibbles)."""
    nibs, total = [], 0
    for s in samples:
        best = None
        for nib in range(16):
            p, _ = _adpcm_step(pcm, index, nib)
            err = abs(p - s)
            if best is None or err < best[0]:
                best = (err, nib)
                if err == 0:
                    break
        pcm, index = _adpcm_step(pcm, index, best[1])
        nibs.append(best[1])
        total += best[0] * best[0]
    return total, nibs


# ---------------------------------------------------------------- WAV files


def read_wav(path):
    """Return (samples as 16-bit ints, rate, loop_start or None)."""
    with open(path, "rb") as f:
        raw = f.read()
    loop = None
    if raw[:4] == b"RIFF" and raw[8:12] == b"WAVE":
        o = 12
        while o + 8 <= len(raw):
            cid, size = raw[o:o + 4], struct.unpack_from("<I", raw, o + 4)[0]
            if cid == b"smpl" and size >= 36:
                nloops = struct.unpack_from("<I", raw, o + 8 + 28)[0]
                if nloops and size >= 36 + 24:
                    loop = struct.unpack_from("<I", raw, o + 8 + 36 + 8)[0]
            o += 8 + size + (size & 1)
    try:
        w = wave.open(path, "rb")
    except wave.Error as e:
        raise SwarError(f"{path}: {e} (use 8/16/24/32-bit PCM WAV)") from None
    with w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        frames = w.readframes(n)
    vals = []
    for i in range(n * ch):
        b = frames[i * width:(i + 1) * width]
        if width == 1:
            v = (b[0] - 128) << 8
        else:
            v = int.from_bytes(b, "little", signed=True) >> (8 * (width - 2))
        vals.append(v)
    if ch > 1:
        vals = [sum(vals[i:i + ch]) // ch for i in range(0, len(vals), ch)]
    return vals, rate, loop


def write_wav(path, samples, rate, width, loop=None):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(width)
        w.setframerate(rate)
        if width == 1:
            w.writeframes(bytes((s + 128) & 0xFF for s in samples))
        else:
            w.writeframes(b"".join(struct.pack("<h", s) for s in samples))
    if loop is not None:  # add a "smpl" chunk so the loop survives a round trip
        with open(path, "r+b") as f:
            data = bytearray(f.read())
            smpl = struct.pack("<9I", 0, 0, 1_000_000_000 // rate, 60, 0, 0, 0, 1, 0)
            smpl += struct.pack("<6I", 0, 0, loop, len(samples) - 1, 0, 0)
            data += b"smpl" + struct.pack("<I", len(smpl)) + smpl
            struct.pack_into("<I", data, 4, len(data) - 8)
            f.seek(0)
            f.write(data)


# ---------------------------------------------------------------- SWAV / SWAR


def make_swav(samples, rate, fmt, loop_start=None):
    """Return the SWAV bytes (12-byte header + data)."""
    if not 0 < rate <= 0xFFFF:
        raise SwarError(f"sample rate {rate} is out of range (1-65535)")
    spw = SAMPLES_PER_WORD[fmt]
    if loop_start is not None:
        if not 0 <= loop_start < len(samples):
            raise SwarError(f"loop start {loop_start} is outside the sample ({len(samples)} samples)")
        loop_start -= loop_start % spw
    # pad to whole words; a looped sample continues from its loop start so the seam stays clean
    pad = (-len(samples)) % spw
    if pad:
        samples = samples + (samples[loop_start:loop_start + pad] if loop_start is not None else [0] * pad)
        samples += [0] * ((-len(samples)) % spw)
    if fmt == 0:
        data = bytes((max(-128, min(127, (s + 128) >> 8))) & 0xFF for s in samples)
        head_words = 0
    elif fmt == 1:
        data = b"".join(struct.pack("<h", s) for s in samples)
        head_words = 0
    else:
        data = adpcm_encode(samples)
        data += b"\0" * ((-len(data)) % 4)
        head_words = 1
    words = len(data) // 4
    ls = head_words + (loop_start // spw if loop_start is not None else 0)
    if ls > 0xFFFF:
        raise SwarError("loop start is too far into the sample")
    header = struct.pack("<BBHHHI", fmt, 1 if loop_start is not None else 0, rate, TIMER_CLOCK // rate,
                         ls, words - ls)
    return header + data


def build_swar(swavs):
    n = len(swavs)
    pos = 0x3C + 4 * n
    offs, body = [], b""
    for s in swavs:
        offs.append(pos + len(body))
        body += s
    size = pos + len(body)
    return (b"SWAR" + struct.pack("<HHIHH", 0xFEFF, 0x0100, size, 0x10, 1)
            + b"DATA" + struct.pack("<I", size - 0x10) + b"\0" * 32
            + struct.pack("<I", n) + b"".join(struct.pack("<I", o) for o in offs) + body)


def parse_swar(data):
    """Return a list of dicts: format, loop, rate, timer, loopStart (words), loopLength (words), data."""
    if data[:4] != b"SWAR" or data[16:20] != b"DATA":
        raise SwarError("not an SWAR file")
    n = struct.unpack_from("<I", data, 0x38)[0]
    out = []
    for i in range(n):
        o = struct.unpack_from("<I", data, 0x3C + 4 * i)[0]
        fmt, loop, rate, timer, ls, ll = struct.unpack_from("<BBHHHI", data, o)
        out.append({"format": fmt, "loop": loop, "rate": rate, "timer": timer, "loopStart": ls,
                    "loopLength": ll, "data": data[o + 12:o + 12 + 4 * (ls + ll)]})
    return out


def decode_swav(w):
    """Samples as 16-bit ints (8-bit for pcm8), and the loop start in samples or None."""
    fmt, d = w["format"], w["data"]
    if fmt == 0:
        s = [b - 256 if b > 127 else b for b in d]
        ls = w["loopStart"] * 4
    elif fmt == 1:
        s = list(struct.unpack(f"<{len(d) // 2}h", d))
        ls = w["loopStart"] * 2
    else:
        s = adpcm_decode(d)
        ls = (w["loopStart"] - 1) * 8
    return s, (ls if w["loop"] else None)


# ---------------------------------------------------------------- build / extract


def build(json_path, out_path):
    data = build_bytes(json_path)
    with open(out_path, "wb") as f:
        f.write(data)


def build_bytes(json_path, inputs=None):
    """The SWAR for a wave archive JSON. Files read are appended to `inputs`."""
    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)
    if inputs is not None:
        inputs.append(os.path.abspath(json_path))
    base = os.path.dirname(os.path.abspath(json_path))
    swavs = []
    for i, w in enumerate(doc.get("waves", [])):
        try:
            fmt = FORMATS[w.get("format", "adpcm")]
        except KeyError:
            raise SwarError(f"wave {i}: format must be one of {', '.join(FORMATS)}") from None
        wav_path = os.path.join(base, w["file"])
        if inputs is not None:
            inputs.append(wav_path)
        samples, rate, wav_loop = read_wav(wav_path)
        if not samples:
            raise SwarError(f"wave {i}: {w['file']} is empty")
        loop = w.get("loopStart", wav_loop)
        if w.get("loop") is False:
            loop = None
        swavs.append(make_swav(samples, w.get("rate", rate), fmt, loop))
    return build_swar(swavs)


def extract(swar_path, out_dir):
    with open(swar_path, "rb") as f:
        waves = parse_swar(f.read())
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(swar_path))[0]
    entries = []
    for i, w in enumerate(waves):
        samples, loop = decode_swav(w)
        name = f"{stem}_{i:03d}.wav"
        if w["format"] == 0:
            write_wav(os.path.join(out_dir, name), samples, w["rate"], 1, loop)
        else:
            write_wav(os.path.join(out_dir, name), samples, w["rate"], 2, loop)
        e = {"file": name, "format": FORMAT_NAMES[w["format"]]}
        if loop is not None:
            e["loopStart"] = loop
        entries.append(e)
    with open(os.path.join(out_dir, stem + ".json"), "w") as f:
        json.dump({"waves": entries}, f, indent=4)
        f.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("json")
    p.add_argument("out")
    p = sub.add_parser("extract")
    p.add_argument("swar")
    p.add_argument("out_dir")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "build":
            build(a.json, a.out)
        else:
            extract(a.swar, a.out_dir)
    except SwarError as e:
        sys.exit(f"swar.py: {e}")


if __name__ == "__main__":
    main()
