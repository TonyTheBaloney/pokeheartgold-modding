#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26
"""Graphics archives as editable files: PNG, JASC .pal and JSON (docs/modding/graphics-sources.md).

    narcgfx.py build DIR/members.json OUT.narc --nitrogfx PATH --nitroarc PATH --work DIR
                     [--depfile PATH]
        the archive from its sources (what the build runs)
    narcgfx.py flags ARCHIVE --nitrogfx PATH
        one line per member: type, compression, the nitrogfx flags that rebuild it,
        and whether they rebuild it byte for byte
    narcgfx.py export ARCHIVE DIR --nitrogfx PATH
        every member as a numbered file in DIR, plus DIR/members.json
    narcgfx.py move DIR/members.json OLD NEW
        rename a source file and its entry (to give exported files names)
    narcgfx.py cells DIR/members.json SPRITE.png CELLS.NCER.json --nitrogfx PATH
        redraw a sprite's PNG as the picture its cells show, instead of a strip of tiles
    narcgfx.py color DIR/members.json
    narcgfx.py color PNG PAL [OUT]
        give PNGs the colors of their palette (the "palette" of each entry), to see
        them as the game does; the build only reads the indices (needs Pillow)

members.json lists the members in archive order. The position in the list is the
member number; the file's extension says what it becomes:

    .png          NCGR   indices; color 0 transparent
    .pal          NCLR   JASC
    .NCER.json    NCER   cells
    .NANR.json    NANR   cell animations
    anything else copied as it is (NSCR tilemaps, 3D files, data, and the few
                  graphics nitrogfx can't rebuild byte for byte)

    {
      "formats": {
        "ncgr_v101_sopc_8bpp_cut_lz": {"flags": ["-version101", "-sopc", "-bitdepth", "8"],
                                       "truncate": 65584, "lz": []}
      },
      "members": [
        {"file": "backgrounds/general/tiles.png", "format": "ncgr_v101_sopc_8bpp_cut_lz",
         "palette": "backgrounds/general/day.pal"},
        {"file": "backgrounds/tilemap.NSCR"}
      ]
    }

A format is the header the retail file had, as nitrogfx flags; "lz" compresses the
result ([] pads to 4 bytes, ["-nopad"] doesn't, ["-nopad", "-extfmt"] is the 0x11
header); "truncate" cuts the NCGR before compressing (retail files that announce a SOPC
section but stop before it). "cell" on a sprite's PNG means it is drawn as the picture
those cells show. "palette" (and "palette_row", the 16-color row of it a 4bpp graphic
uses) is only for `color`: it records which colors the game shows the picture with.
"""

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pokedata"))
from pokedata import narc_members, pack  # noqa: E402

MAGIC = {
    b"RGCN": "NCGR", b"RLCN": "NCLR", b"RCSN": "NSCR", b"RECN": "NCER", b"RNAN": "NANR",
    b"RCMN": "NMCR", b"RAMN": "NMAR", b"BMD0": "NSBMD", b"BTX0": "NSBTX", b"BCA0": "NSBCA",
    b"BTP0": "NSBTP", b"BTA0": "NSBTA", b"BMA0": "NSBMA", b"BVA0": "NSBVA",
}
MAPPING = {0x10: "32", 0x100010: "64", 0x200010: "128", 0x300010: "256"}
LZ_VARIANTS = ([], ["-nopad"], ["-nopad", "-extfmt"], ["-extfmt"])
EXPORT_EXT = {"NCGR": ".png", "NCLR": ".pal", "NCER": ".NCER.json", "NANR": ".NANR.json"}


def source_type(path):
    for kind, ext in EXPORT_EXT.items():
        if path.endswith(ext):
            return kind
    return None


def ncgr_flags(data):
    flags = []
    if data[6:8] == b"\x01\x01":
        flags.append("-version101")
    if struct.unpack_from("<H", data, 14)[0] == 2:
        flags.append("-sopc")
    if struct.unpack_from("<H", data, 0x18)[0] == 0xFFFF:
        flags.append("-clobbersize")
    if struct.unpack_from("<I", data, 0x1C)[0] == 4:
        flags += ["-bitdepth", "8"]
    mapping = MAPPING.get(struct.unpack_from("<I", data, 0x20)[0])
    if mapping:
        flags += ["-mappingtype", mapping]
    if data[0x24] == 1:
        flags.append("-scan")  # stored as a bitmap, not as 8x8 tiles
    return flags


def nclr_flags(data):
    section = struct.unpack_from("<I", data, 0x14)[0]
    colors = (section - 0x18) // 2
    flags = ["-bitdepth", "4" if data[0x18] == 3 else "8"]
    if colors != 256:
        flags.append("-nopad")
    if data[0x1A]:
        flags += ["-comp", str(data[0x1A])]
    if struct.unpack_from("<I", data, 0x20)[0] == 0x200 - colors * 2 != colors * 2:
        flags.append("-invertsize")
    if data[0x28 + colors * 2 - 2:0x28 + colors * 2] == b"IR":
        flags.append("-ir")
    if struct.unpack_from("<H", data, 14)[0] == 2:
        flags.append("-pcmp")
        pcmp = 0x10 + section
        start = struct.unpack_from("<H", data, pcmp + 16)[0]
        if start:
            flags += ["-start", str(start)]
    return flags


def format_name(kind, fmt):
    """A name for a set of flags, like the flag sets in files/meson.build."""
    words = {"-version101": "v101", "-sopc": "sopc", "-clobbersize": "sprite", "-scan": "bitmap",
             "-nopad": "nopad", "-invertsize": "invsize", "-pcmp": "pcmp", "-ir": "ir"}
    flags, parts, i = fmt.get("flags", []), [kind.lower()], 0
    while i < len(flags):
        f = flags[i]
        if f in ("-bitdepth", "-mappingtype", "-start", "-comp"):
            value = flags[i + 1]
            parts.append({"-bitdepth": value + "bpp", "-mappingtype": value + "k",
                          "-start": "start" + value, "-comp": "comp" + value}[f])
            i += 2
            continue
        parts.append(words.get(f, f.lstrip("-")))
        i += 1
    if "truncate" in fmt:
        parts.append("cut")
    if "lz" in fmt:
        parts.append({(): "lz", ("-nopad",): "lznopad", ("-nopad", "-extfmt"): "lzext"}.get(tuple(fmt["lz"]), "lzother"))
    return "_".join(parts)


class Gfx:
    def __init__(self, exe, work):
        self.exe = os.path.abspath(exe)
        self.work = work

    def run(self, src, dst, *flags):
        r = subprocess.run([self.exe, src, dst, *flags], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("nitrogfx %s %s %s: %s" % (src, dst, " ".join(flags), r.stderr.strip()))

    def path(self, name):
        return os.path.join(self.work, name)

    def write(self, name, data):
        with open(self.path(name), "wb") as f:
            f.write(data)
        return self.path(name)

    def read(self, name):
        with open(self.path(name), "rb") as f:
            return f.read()

    def decompress(self, raw):
        self.run(self.write("m.bin.lz", raw), self.path("m.bin"))
        return self.read("m.bin")

    def compress(self, data, flags):
        self.run(self.write("c.bin", data), self.path("c.lz"), *flags)
        return self.read("c.lz")

    def export(self, kind, data, dst, *flags):
        self.run(self.write("e." + kind, data), dst, *flags)

    def build(self, kind, src, flags, truncate=None):
        self.run(src, self.path("b." + kind), *flags)
        data = self.read("b." + kind)
        return data[:truncate] if truncate else data

    def member(self, base, entry, fmt):
        """The archive member for one entry of members.json."""
        src = os.path.join(base, entry["file"])
        kind = source_type(entry["file"])
        if kind is None:
            with open(src, "rb") as f:
                return f.read()
        flags = list(fmt.get("flags", []))
        if "cell" in entry:
            flags += ["-cell", os.path.join(base, entry["cell"])]
        data = self.build(kind, src, flags, fmt.get("truncate"))
        if "lz" in fmt:
            data = self.compress(data, fmt["lz"])
        return data


def analyze(gfx, raw):
    """How to export a member and the format that rebuilds it, or (format, None) to keep it raw."""
    fmt = {"type": "bin"}
    data = raw
    if len(raw) > 4 and raw[0] in (0x10, 0x11):
        try:
            data = gfx.decompress(raw)
        except RuntimeError:
            data = raw
    kind = MAGIC.get(data[:4])
    if kind:
        fmt["type"] = kind
    if kind not in EXPORT_EXT:
        return fmt, None
    if data is not raw:
        lz = next((v for v in LZ_VARIANTS if gfx.compress(data, v) == raw), None)
        if lz is None:
            fmt["fail"] = "LZ"
            return fmt, None
        fmt["lz"] = lz
    src = gfx.path("x" + EXPORT_EXT[kind])
    try:
        gfx.export(kind, data, src)
        if kind == "NCGR":
            fmt["flags"] = ncgr_flags(data)
            built = gfx.build(kind, src, fmt["flags"])
            if len(built) > len(data) and built[:len(data)] == data:
                fmt["truncate"] = len(data)
                built = built[:len(data)]
        elif kind == "NCLR":
            fmt["flags"] = nclr_flags(data)
            built = gfx.build(kind, src, fmt["flags"])
        else:
            built = gfx.build(kind, src, [])
    except RuntimeError as e:
        fmt["fail"] = str(e).splitlines()[0]
        return fmt, None
    if built != data:
        fmt["fail"] = "differs"
        return fmt, None
    return fmt, src


def load(manifest):
    with open(manifest) as f:
        return json.load(f)


def save(manifest, doc):
    """One line per format and per member, so diffs stay readable."""
    lines = ["{", '  "formats": {']
    names = sorted(doc["formats"])
    for i, name in enumerate(names):
        fmt = {k: doc["formats"][name][k] for k in ("flags", "truncate", "lz") if k in doc["formats"][name]}
        lines.append("    %s: %s%s" % (json.dumps(name), json.dumps(fmt), "," if i < len(names) - 1 else ""))
    lines += ["  },", '  "members": [']
    for i, m in enumerate(doc["members"]):
        lines.append("    %s%s" % (json.dumps(m), "," if i < len(doc["members"]) - 1 else ""))
    lines += ["  ]", "}"]
    with open(manifest, "w") as f:
        f.write("\n".join(lines) + "\n")


def cmd_flags(args):
    with tempfile.TemporaryDirectory() as work:
        gfx = Gfx(args.nitrogfx, work)
        for i, raw in enumerate(narc_members(args.archive)):
            fmt, _ = analyze(gfx, raw)
            lz = ""
            if "lz" in fmt:
                lz = "lz " + (" ".join(fmt["lz"]) or "(padded)")
            flags = " ".join(fmt.get("flags", []))
            if "truncate" in fmt:
                flags += " (cut to %d bytes)" % fmt["truncate"]
            state = "FAIL " + fmt["fail"] if "fail" in fmt else ("ok" if fmt["type"] in EXPORT_EXT else "")
            print("%5d  %-5s %-22s %-48s %s" % (i, fmt["type"], lz, flags, state))


def cmd_export(args):
    os.makedirs(args.dir, exist_ok=True)
    doc = {"formats": {}, "members": []}
    with tempfile.TemporaryDirectory() as work:
        gfx = Gfx(args.nitrogfx, work)
        for i, raw in enumerate(narc_members(args.archive)):
            fmt, src = analyze(gfx, raw)
            kind = fmt.pop("type")
            if src:
                entry = {"file": "%05d%s" % (i, EXPORT_EXT[kind])}
                name = format_name(kind, fmt)
                if doc["formats"].get(name, fmt) != fmt:
                    sys.exit("two formats named %s" % name)
                doc["formats"][name] = fmt
                entry["format"] = name
                shutil.copy(src, os.path.join(args.dir, entry["file"]))
            else:
                entry = {"file": "%05d.%s" % (i, kind)}
                with open(os.path.join(args.dir, entry["file"]), "wb") as f:
                    f.write(raw)
            doc["members"].append(entry)
    save(os.path.join(args.dir, "members.json"), doc)


def cmd_build(args):
    base = os.path.dirname(os.path.abspath(args.manifest))
    doc = load(args.manifest)
    os.makedirs(args.work, exist_ok=True)
    gfx = Gfx(args.nitrogfx, args.work)
    out, deps = [], [args.manifest]
    for m in doc["members"]:
        deps.append(os.path.join(base, m["file"]))
        if "cell" in m:
            deps.append(os.path.join(base, m["cell"]))
        out.append(gfx.member(base, m, doc["formats"].get(m.get("format"), {})))
    pack(out, args.out, args.nitroarc, args.work)
    if args.depfile:
        with open(args.depfile, "w") as f:
            f.write("%s: %s\n" % (args.out, " ".join(deps)))


def find_entry(doc, path):
    for m in doc["members"]:
        if m["file"] == path:
            return m
    sys.exit("%s is not in members.json" % path)


def cmd_move(args):
    base = os.path.dirname(os.path.abspath(args.manifest))
    doc = load(args.manifest)
    if source_type(args.old) != source_type(args.new) or os.path.splitext(args.old)[1] != os.path.splitext(args.new)[1]:
        sys.exit("keep the extension: it says what the file becomes")
    if os.path.exists(os.path.join(base, args.new)):
        sys.exit("%s already exists" % args.new)
    find_entry(doc, args.old)
    for m in doc["members"]:
        for key in ("file", "cell", "palette"):  # an entry can name other files
            if m.get(key) == args.old:
                m[key] = args.new
    os.makedirs(os.path.dirname(os.path.join(base, args.new)) or base, exist_ok=True)
    os.rename(os.path.join(base, args.old), os.path.join(base, args.new))
    save(args.manifest, doc)


def cmd_cells(args):
    base = os.path.dirname(os.path.abspath(args.manifest))
    doc = load(args.manifest)
    entry = find_entry(doc, args.png)
    if "cell" in entry:
        sys.exit("%s is already drawn with cells" % args.png)
    fmt = doc["formats"][entry["format"]]
    with tempfile.TemporaryDirectory() as work:
        gfx = Gfx(args.nitrogfx, work)
        before = gfx.member(base, entry, fmt)
        ncgr = gfx.build("NCGR", os.path.join(base, args.png), fmt.get("flags", []))
        picture = gfx.path("p.png")
        gfx.export("NCGR", ncgr, picture, "-cell", os.path.join(base, args.cells), "-object")
        new = dict(entry, cell=args.cells)
        shutil.copy(os.path.join(base, args.png), gfx.path("strip.png"))
        shutil.copy(picture, os.path.join(base, args.png))
        if gfx.member(base, new, fmt) != before:
            shutil.copy(gfx.path("strip.png"), os.path.join(base, args.png))
            sys.exit("%s: the picture doesn't give back the same tiles with these cells" % args.png)
    entry["cell"] = args.cells
    save(args.manifest, doc)


def color(png, pal, out=None, row=0):
    from PIL import Image

    with open(png, "rb") as f:
        depth = f.read(25)[24]
    image = Image.open(png)
    with open(pal) as f:
        lines = f.read().split("\n")
    colors = [int(x) for line in lines[3:3 + int(lines[2])] for x in line.split()][row * 48:]
    if image.mode == "L":
        # nitrogfx writes a grayscale PNG with the indices reversed (index 0 is white)
        top = (1 << depth) - 1
        gray = image.point(lambda v: top - v * top // 255)
        image = Image.frombytes("P", gray.size, gray.tobytes())
    image.putpalette(colors[:768] + [0] * (768 - len(colors[:768])))
    image.save(out or png, bits=depth)


def cmd_color(args):
    if args.pal is None:
        base = os.path.dirname(os.path.abspath(args.png))
        for m in load(args.png)["members"]:
            if "palette" in m and not m["palette"].endswith(".pal"):
                print("%s: %s is kept binary, left as it is" % (m["file"], m["palette"]))
            elif "palette" in m:
                color(os.path.join(base, m["file"]), os.path.join(base, m["palette"]), row=m.get("palette_row", 0))
    else:
        color(args.png, args.pal, args.out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("build")
    s.add_argument("manifest")
    s.add_argument("out")
    s.add_argument("--nitrogfx", required=True)
    s.add_argument("--nitroarc", required=True)
    s.add_argument("--work", required=True)
    s.add_argument("--depfile")
    s.set_defaults(func=cmd_build)
    s = sub.add_parser("flags")
    s.add_argument("archive")
    s.add_argument("--nitrogfx", required=True)
    s.set_defaults(func=cmd_flags)
    s = sub.add_parser("export")
    s.add_argument("archive")
    s.add_argument("dir")
    s.add_argument("--nitrogfx", required=True)
    s.set_defaults(func=cmd_export)
    s = sub.add_parser("move")
    s.add_argument("manifest")
    s.add_argument("old")
    s.add_argument("new")
    s.set_defaults(func=cmd_move)
    s = sub.add_parser("cells")
    s.add_argument("manifest")
    s.add_argument("png")
    s.add_argument("cells")
    s.add_argument("--nitrogfx", required=True)
    s.set_defaults(func=cmd_cells)
    s = sub.add_parser("color")
    s.add_argument("png", help="a PNG, or members.json to color every entry that has a palette")
    s.add_argument("pal", nargs="?")
    s.add_argument("out", nargs="?")
    s.set_defaults(func=cmd_color)
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
