#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26
"""Battle animation scripts as text (docs/modding/move-animations.md).

    battleanim.py dis ARCHIVE MEMBER
        one script, printed as text
    battleanim.py export ARCHIVE DIR [--effects]
        every script as DIR/NNNN_NAME.anim (move names; --effects: BATTLE_ANIMATION_*
        names, for files/a/0/6/1)
    battleanim.py build DIR OUT [--depfile PATH]
        the archive from DIR/NNNN_*.anim; numbers must run from 0 without gaps (what the
        build runs on data/battle_anims/moves and data/battle_anims/effects)
    battleanim.py check ARCHIVE [--effects]
        export and build again in memory, and say whether it is byte for byte the same

ARCHIVE is a built a/0/1/0 (moves, member = move id; build/heartgold.us/files/a/0/1/0)
or a/0/6/1 (effect animations, member = BATTLE_ANIMATION_* id). A script is a list of u32 words run by
BattleAnimSystem_ExecuteCommands (src/battle/battle_anim_system.c): an opcode, then its
arguments. One command per line:

    CreateEmitter 0, 1, SetPositionAtDefender      ; comment
    PlaySEWithPan SEQ_SE_DP_030, -117
    JumpBySide 0, L12, L40
L12:
    End

Arguments are numbers (decimal, 0x hex, negative), labels (jumps), or names: SEQ_SE_*
sound effects, CallFunc functions (gBattleAnimFuncTable), CreateSpriteWithFunc
functions (gBattleAnimSpriteFuncTable) and emitter callbacks
(gBattleAnimEmitterCallbackTable), the last three without their C prefix and read from
asm/battle_anim_data.s. ".word N, ..." writes raw words.
"""

import argparse
import os
import re
import struct
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

# Operand kinds: n number, L jump offset (relative to its own word), se sound effect,
# f CallFunc function, sf sprite function, cb emitter callback, * the rest of the line
# (CallFunc / CreateSpriteWithFunc arguments, EmitterData values: the count is implicit)
COMMANDS = {
    0: ("Wait", "n"),
    1: ("WaitForTasks", ""),
    2: ("BeginLoop", "n"),
    3: ("EndLoop", ""),
    4: ("End", ""),
    5: ("PlaySE", "se"),
    8: ("SetSubScreenBlend", "n n"),
    10: ("Call", "L"),
    11: ("Return", ""),
    12: ("SetArg", "n n"),
    13: ("JumpByVariantBit0", "L L"),
    14: ("JumpIfVariantEqual", "n L"),
    15: ("Jump", "L"),
    16: ("SwitchBackground", "n n"),
    17: ("SetBgScroll", "n n"),
    18: ("RestoreBackground", "n n"),
    19: ("WaitForBackgroundLoaded", ""),
    20: ("WaitForBackgroundSwitch", ""),
    21: ("SetBackground", "n"),
    22: ("PlaySEWithPan", "se n"),
    23: ("SetSEPan", "n"),
    24: ("PanSweepSE", "se n n n n"),
    25: ("RepeatSE", "se n n n"),
    26: ("DelayedSE", "se n n"),
    29: ("WaitForSoundTasks", ""),
    31: ("CopyBattlerToBg", "n n"),
    32: ("ClearBattlerBg", "n"),
    34: ("SwitchBackgroundBySide", "n n n"),
    35: ("PanSweepSERaw", "se n n n n"),
    36: ("PanSweepSEConverted", "se n n n n"),
    44: ("StopSE", "se"),
    45: ("CallFunc", "f *"),
    46: ("CreateEmitter", "n n cb"),
    47: ("CreateEmitterInSlot", "n n n cb"),
    48: ("CreateEmitterByPosition6", "n n n n n n n cb"),
    49: ("CreateEmitterByPosition4", "n n n n n cb"),
    50: ("WaitForParticles", ""),
    51: ("LoadParticleSystem", "n n"),
    52: ("LoadParticleSystemEx", "n n n"),
    53: ("FreeParticleSystem", "n"),
    55: ("EmitterData", "*"),
    56: ("InitBattlerSpriteManager", ""),
    57: ("LoadBattlerSpriteResources", "n"),
    58: ("CreateBattlerSprite", "n n n n"),
    59: ("FreeBattlerSpriteManager", ""),
    60: ("DeleteBattlerSprite", "n"),
    61: ("StopFollowTask", "n"),
    62: ("SetParticlePerspective", "n n"),
    63: ("SetParticleFlipY", "n n"),
    64: ("JumpBySide", "n L L"),
    65: ("PlayCry", "n n n"),
    66: ("WaitForCry", "n"),
    67: ("ClearArgs", ""),
    68: ("ChangeBattlerPic", "n"),
    69: ("RestoreBattlerPic", "n"),
    70: ("JumpByWeather", "L L L L L"),
    71: ("JumpIfContest", "L"),
    72: ("JumpIfSameSide", "L"),
    73: ("InitSpriteManager", "n n n n n n n n"),
    74: ("LoadCharResource", "n n"),
    75: ("LoadPaletteResource", "n n n"),
    76: ("LoadCellResource", "n n"),
    77: ("LoadAnimResource", "n n"),
    78: ("CreateSpriteWithFunc", "n sf n n n n n n *"),
    79: ("CreateSprite", "n n n n n n n n"),
    80: ("FreeSpriteManager", "n"),
    81: ("SetBattlerSpriteVisible", "n n"),
    82: ("StartBattlerSpriteDraw", "n n n"),
    83: ("StopBattlerSpriteDraw", "n"),
    84: ("WaitForButtonCombo", ""),
    85: ("BrightnessFlash", "n"),
    86: ("SwitchBackgroundWithFadeWait", "n n n"),
    87: ("JumpIfAttackerActive", "L"),
}
# Left out on purpose: 6, 7, 9, 27, 28, 37-43 and 54 don't move past their opcode (the
# game hangs), 30 and 33 jump to an absolute address, 55 is only EmitterData (it asserts
# when run) and 88 is past the end of the table. Write them with .word if you must.
OPCODES = {name: (op, kinds.split()) for op, (name, kinds) in COMMANDS.items()}


# What Names reads (the build depends on them too)
NAME_SOURCES = ["asm/battle_anim_data.s", "include/constants/sndseq.h", "include/constants/moves.h",
                "include/constants/battle_subscript.h"]


def _read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def _asm_table(text, label, prefix):
    m = re.search(r"^%s:\n((?:\t\.word .*\n)+)" % label, text, re.M)
    return [w.split()[1].replace(prefix, "") for w in m.group(1).splitlines()]


class Names:
    def __init__(self, effects=False):
        data = _read("asm/battle_anim_data.s")
        self.tables = {
            "f": _asm_table(data, "gBattleAnimFuncTable", "BattleAnimFunc_"),
            "sf": _asm_table(data, "gBattleAnimSpriteFuncTable", "BattleAnimSpriteFunc_"),
            "cb": _asm_table(data, "gBattleAnimEmitterCallbackTable", "BattleAnimEmitterCb_"),
        }
        self.se = {}
        for name, value in re.findall(r"^#define (SEQ_SE_\w+)\s+(\d+)", _read("include/constants/sndseq.h"), re.M):
            self.se.setdefault(int(value), name)
        self.se_values = {name: value for value, name in self.se.items()}
        if effects:
            found = re.findall(r"^#define BATTLE_ANIMATION_(\w+)\s+(\d+)", _read("include/constants/battle_subscript.h"), re.M)
        else:
            found = re.findall(r"^#define MOVE_(\w+)\s+(\d+)", _read("include/constants/moves.h"), re.M)
        self.members = {}
        for name, value in found:
            self.members.setdefault(int(value), name)

    def name(self, kind, value):
        if kind == "se":
            return self.se.get(value)
        if kind in self.tables and value < len(self.tables[kind]):
            return self.tables[kind][value]
        return None

    def value(self, kind, text):
        if kind == "se" and text in self.se_values:
            return self.se_values[text]
        if kind in self.tables and text in self.tables[kind]:
            return self.tables[kind].index(text)
        return None


def _num(value):
    if value >= 0x80000000:
        return str(value - 0x100000000)
    if value >= 0x10000:
        return "0x%X" % value
    return str(value)


def decode(words):
    """[(start, opcode, [words])] for the whole script; ValueError on an unknown opcode."""
    out = []
    i = 0
    while i < len(words):
        op = words[i]
        if op not in COMMANDS:
            raise ValueError("unknown opcode %d at word %d" % (op, i))
        kinds = COMMANDS[op][1].split()
        fixed = len([k for k in kinds if k != "*"])
        n = 1 + fixed
        if op == 45:
            n += 1 + words[i + 2]
        elif op == 78:
            n += 1 + words[i + 9]
        elif op == 55:
            n = 2 + words[i + 1]
        if i + n > len(words):
            raise ValueError("%s at word %d runs past the end" % (COMMANDS[op][0], i))
        out.append((i, op, list(words[i + 1:i + n])))
        i += n
    return out


def disassemble(data, names, title=None):
    if len(data) % 4:
        raise ValueError("size %d is not a multiple of 4" % len(data))
    words = struct.unpack("<%dI" % (len(data) // 4), data)
    try:
        cmds = decode(words)
    except ValueError as e:
        lines = ["# %s" % title] if title else []
        lines.append("# not decoded (%s): raw words" % e)
        lines += [".word " + ", ".join(_num(w) for w in words[i:i + 8]) for i in range(0, len(words), 8)]
        return "\n".join(lines) + "\n"
    starts = {start for start, _, _ in cmds}
    labels = set()
    for start, op, args in cmds:
        for j, kind in enumerate(COMMANDS[op][1].split()):
            if kind == "L":
                target = start + 1 + j + struct.unpack("<i", struct.pack("<I", args[j]))[0]
                if target in starts or target == len(words):
                    labels.add(target)
    lines = ["# %s" % title] if title else []
    for start, op, args in cmds:
        if start in labels:
            lines.append("L%d:" % start)
        name, kinds = COMMANDS[op][0], COMMANDS[op][1].split()
        if op == 55:
            text = [_num(a) for a in args[1:]]
        else:
            text = []
            for j, kind in enumerate(kinds):
                if kind == "*":
                    count_at = 1 if op == 45 else 8
                    text += [_num(a) for a in args[count_at + 1:]]
                    break
                value = args[j]
                if kind == "L":
                    target = start + 1 + j + struct.unpack("<i", struct.pack("<I", value))[0]
                    text.append("L%d" % target if target in labels else "%+d" % (target - start - 1 - j))
                else:
                    text.append(names.name(kind, value) or _num(value))
        lines.append("    " + name + (" " + ", ".join(text) if text else ""))
    if len(words) in labels:
        lines.append("L%d:" % len(words))
    return "\n".join(lines) + "\n"


def _int(text, where):
    try:
        return int(text, 0) & 0xFFFFFFFF
    except ValueError:
        raise ValueError("%s: %r is not a number" % (where, text))


def assemble(text, names, where="script"):
    """Words of a script; labels may be used before they are defined."""
    items = []  # (line number, kind, payload)
    labels = {}
    pos = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.split(";")[0].split("#")[0].strip()
        if not line:
            continue
        here = "%s:%d" % (where, lineno)
        if line.endswith(":") and " " not in line:
            labels[line[:-1]] = pos
            continue
        mnemonic, _, rest = line.partition(" ")
        args = [a.strip() for a in rest.split(",")] if rest.strip() else []
        if mnemonic == ".word":
            items.append((here, None, [_int(a, here) for a in args]))
            pos += len(args)
            continue
        if mnemonic not in OPCODES:
            raise ValueError("%s: unknown command %s" % (here, mnemonic))
        op, kinds = OPCODES[mnemonic]
        fixed = [k for k in kinds if k != "*"]
        if len(args) < len(fixed) or ("*" not in kinds and len(args) != len(fixed)):
            raise ValueError("%s: %s takes %s%d arguments, got %d" % (here, mnemonic, "at least " if "*" in kinds else "", len(fixed), len(args)))
        items.append((here, op, args))
        pos += 1 + len(args) + (1 if "*" in kinds else 0)
    words = []
    for here, op, args in items:
        if op is None:
            words += args
            continue
        kinds = OPCODES[COMMANDS[op][0]][1]
        start = len(words)
        out = [op]
        for j, kind in enumerate(kinds):
            if kind == "*":
                rest = [_int(a, here) for a in args[j:]]
                out += [len(rest)] + rest
                break
            a = args[j]
            if kind == "L":
                if a in labels:
                    out.append((labels[a] - (start + 1 + j)) & 0xFFFFFFFF)
                elif re.fullmatch(r"[+-]\d+", a):
                    out.append(int(a) & 0xFFFFFFFF)
                else:
                    raise ValueError("%s: unknown label %s" % (here, a))
            elif kind in ("se", "f", "sf", "cb") and names.value(kind, a) is not None:
                out.append(names.value(kind, a))
            else:
                out.append(_int(a, here))
        words += out
    return words


def read_narc(path):
    with open(path, "rb") as f:
        b = f.read()
    if b[:4] != b"NARC" or b[16:20] != b"BTAF":
        raise ValueError("%s is not a NARC" % path)
    count = struct.unpack_from("<H", b, 24)[0]
    fat = [struct.unpack_from("<II", b, 28 + 8 * i) for i in range(count)]
    btnf = 28 + 8 * count
    gmif = btnf + struct.unpack_from("<I", b, btnf + 4)[0]
    base = gmif + 8
    return [b[base + s:base + e] for s, e in fat]


def write_narc(members):
    fat = b""
    data = b""
    for m in members:
        fat += struct.pack("<II", len(data), len(data) + len(m))
        data += m + b"\xff" * (-len(m) % 4)
    btaf = b"BTAF" + struct.pack("<IHH", 12 + len(fat), len(members), 0) + fat
    btnf = b"BTNF" + struct.pack("<IIHH", 16, 4, 0, 1)
    gmif = b"GMIF" + struct.pack("<I", 8 + len(data)) + data
    body = btaf + btnf + gmif
    return b"NARC" + struct.pack("<HHIHH", 0xFFFE, 0x0100, 16 + len(body), 16, 3) + body


def _filename(index, names):
    name = names.members.get(index, "%d" % index)
    return "%04d_%s.anim" % (index, name)


def export(members, out_dir, names):
    os.makedirs(out_dir, exist_ok=True)
    for i, m in enumerate(members):
        title = "member %d: %s" % (i, names.members.get(i, "spare"))
        with open(os.path.join(out_dir, _filename(i, names)), "w", encoding="utf-8") as f:
            f.write(disassemble(m, names, title))


def build(src_dir, names, read=None):
    """The archive; the paths of the files it read are appended to read."""
    files = {}
    for fn in os.listdir(src_dir):
        m = re.match(r"(\d+)_.*\.anim$", fn)
        if m:
            index = int(m.group(1))
            if index in files:
                raise ValueError("two files for member %d: %s and %s" % (index, files[index], fn))
            files[index] = fn
    if not files:
        raise ValueError("no NNNN_*.anim files in %s" % src_dir)
    if sorted(files) != list(range(len(files))):
        missing = sorted(set(range(max(files) + 1)) - set(files))
        raise ValueError("members missing: %s" % missing[:10])
    members = []
    for i in range(len(files)):
        path = os.path.join(src_dir, files[i])
        with open(path, encoding="utf-8") as f:
            words = assemble(f.read(), names, files[i])
        if read is not None:
            read.append(path)
        members.append(struct.pack("<%dI" % len(words), *words))
    return write_narc(members)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dis")
    d.add_argument("archive")
    d.add_argument("member", type=int)
    d.add_argument("--effects", action="store_true")
    e = sub.add_parser("export")
    e.add_argument("archive")
    e.add_argument("dir")
    e.add_argument("--effects", action="store_true")
    b = sub.add_parser("build")
    b.add_argument("dir")
    b.add_argument("out")
    b.add_argument("--depfile")
    c = sub.add_parser("check")
    c.add_argument("archive")
    c.add_argument("--effects", action="store_true")
    args = p.parse_args(argv)

    try:
        names = Names(getattr(args, "effects", False))
        if args.cmd == "dis":
            members = read_narc(args.archive)
            sys.stdout.write(disassemble(members[args.member], names, "member %d: %s" % (args.member, names.members.get(args.member, "spare"))))
        elif args.cmd == "export":
            export(read_narc(args.archive), args.dir, names)
        elif args.cmd == "build":
            read = []
            data = build(args.dir, names, read)
            with open(args.out, "wb") as f:
                f.write(data)
            if args.depfile:
                # every file read, plus the folder: it changes when a script is added or
                # removed, so the build notices without reconfiguring
                deps = [args.dir] + read + [os.path.join(ROOT, n) for n in NAME_SOURCES]
                esc = lambda p: p.replace("\\", "/").replace(" ", "\\ ")  # noqa: E731
                with open(args.depfile, "w", encoding="utf-8") as f:
                    f.write("%s: \\\n" % esc(args.out) + " \\\n".join("  " + esc(os.path.abspath(d)) for d in deps) + "\n")
        elif args.cmd == "check":
            members = read_narc(args.archive)
            again = [struct.pack("<%dI" % len(w), *w) for w in (assemble(disassemble(m, names), names, "member %d" % i) for i, m in enumerate(members))]
            with open(args.archive, "rb") as f:
                same = write_narc(again) == f.read()
            print("%s: %d scripts, %s" % (args.archive, len(members), "byte for byte the same" if same else "DIFFERENT"))
            return 0 if same else 1
    except (ValueError, OSError) as err:
        print("battleanim: %s" % err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
