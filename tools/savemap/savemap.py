#!/usr/bin/env python3
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Print the save file layout of a build: every chunk's size and offset, how full
each block is, and the extra chunks. docs/modding/save-data.md explains it.

    python3 tools/savemap/savemap.py [build/heartgold.us]

Sizes are read from the built game: each chunk's *_sizeof function (named in
src/save_arrays.c) is found in main.nef's symbols and evaluated from main.sbin,
so the numbers are what the game uses. The layout follows src/save.c
(SaveData_InitSubstructs, SaveData_InitSlotSpecs).
"""

import os
import re
import struct
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CHUNK_FOOTER = 16           # struct SaveChunkFooter
ARRAY_FOOTER = 16           # struct SaveArrayFooter (extra chunks)
HALF = 0x40000              # second copy of everything starts here (64 sectors)
ARM9_BASE = 0x02000000


def defines(path):
    out = {}
    for name, value in re.findall(r"#define\s+(\w+)\s+(0x[0-9a-fA-F]+|\d+)", open(path).read()):
        out[name] = int(value, 0)
    return out


class Build:
    def __init__(self, build):
        self.syms = {}
        nm = subprocess.run(["arm-none-eabi-nm", os.path.join(build, "main.nef")],
                            capture_output=True, text=True, check=True).stdout
        for line in nm.splitlines():
            p = line.split()
            if len(p) == 3:
                self.syms.setdefault(p[2], int(p[0], 16))
        with open(os.path.join(build, "main.sbin"), "rb") as f:
            self.main = f.read()

    def u16(self, a):
        return struct.unpack_from("<H", self.main, a - ARM9_BASE)[0]

    def u32(self, a):
        return struct.unpack_from("<I", self.main, a - ARM9_BASE)[0]

    def constant_function(self, name):
        """Value returned by a small Thumb function that only builds a constant."""
        pc, r = self.syms[name] & ~1, {}
        for _ in range(12):
            h = self.u16(pc)
            if h == 0x4770:                                   # bx lr
                return r[0]
            if h >> 11 == 0b01001:                            # ldr rd, [pc, #imm]
                r[(h >> 8) & 7] = self.u32(((pc + 4) & ~3) + (h & 0xFF) * 4)
            elif h >> 11 == 0b00100:                          # movs rd, #imm
                r[(h >> 8) & 7] = h & 0xFF
            elif h >> 11 == 0b00000:                          # lsls rd, rm, #imm
                r[h & 7] = r[(h >> 3) & 7] << ((h >> 6) & 31)
            elif h >> 11 == 0b00110:                          # adds rd, #imm
                r[(h >> 8) & 7] += h & 0xFF
            elif h >> 9 == 0b0001110:                         # adds rd, rn, #imm3
                r[h & 7] = r[(h >> 3) & 7] + ((h >> 6) & 7)
            else:
                raise ValueError("%s: can't evaluate instruction %04x" % (name, h))
            pc += 2
        raise ValueError("%s: no return found" % name)


def chunk_tables():
    src = open(os.path.join(ROOT, "src/save_arrays.c")).read()
    main, extra = src.split("gExtraSaveChunkHeaders[] = {")
    chunks = re.findall(r"\{\s*(SAVE_\w+),\s*(\d+),\s*\(SAVESIZEFN\)(\w+)", main)
    extras = re.findall(r"\{\s*(\d+),\s*SAVE_PAGE_MAX(?:\s*\+\s*(\d+))?,\s*\(SAVESIZEFN\)(\w+)", extra)
    return chunks, extras


def layout(build_dir):
    b = Build(build_dir)
    consts = defines(os.path.join(ROOT, "include/constants/save_arrays.h"))
    page_max, sector = consts["SAVE_PAGE_MAX"], consts["SAVE_SECTOR_SIZE"]
    chunks, extras = chunk_tables()
    rows, blocks, adrs = [], {}, 0
    for i, (cid, block, fn) in enumerate(chunks):
        raw = b.constant_function(fn)
        size = ((raw + 3) & ~3) + 4                          # GetSaveChunkSizePlusCRC
        rows.append((cid, int(block), fn, raw, size, adrs))
        blocks[int(block)] = blocks.get(int(block), 0) + size
        adrs += size
        nxt = chunks[i + 1][1] if i + 1 < len(chunks) else None
        if nxt != block:
            adrs += CHUNK_FOOTER
            if nxt is not None and adrs % 0x100:
                adrs += 0x100 - adrs % 0x100
    specs, off, page = [], 0, 0
    for blk in sorted(blocks):
        size = blocks[blk] + CHUNK_FOOTER
        pages = -(-size // sector)
        specs.append((blk, off, size, page, pages))
        page += pages
        off += size
        if off % 0x100:
            off += 0x100 - off % 0x100
    ex = [(int(i), page_max + int(k or 0), fn, b.constant_function(fn)) for i, k, fn in extras]
    return rows, specs, ex, page_max, sector


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    build = argv[0] if argv else os.path.join(ROOT, "build/heartgold.us")
    rows, specs, extras, page_max, sector = layout(build)
    print("Save layout of %s (sizes from the built game)\n" % os.path.relpath(build, ROOT))
    print("%-36s %5s %7s %7s  %s" % ("chunk", "block", "size", "offset", "size function"))
    for cid, blk, fn, raw, size, adrs in rows:
        print("%-36s %5d %7d %#07x  %s" % (cid, blk, raw, adrs, fn))
    print()
    used_pages = 0
    for blk, off, size, page, pages in specs:
        room = pages * sector - size
        used_pages += pages
        print("block %d: bytes %#07x-%#07x (%d incl. footer); counts as %d sectors; can grow %d bytes "
              "before it counts as %d" % (blk, off, off + size - 1, size, pages, room, pages + 1))
    print("sector budget: %d of SAVE_PAGE_MAX %d (each block's size rounded up to whole sectors)"
          % (used_pages, page_max))
    print("\nextra chunks (outside the main save; also at +%#x):" % HALF)
    for idx, first, fn, raw in extras:
        n = -(-(raw + ARRAY_FOOTER) // sector)
        print("  %d: sectors %d-%d  %6d bytes  %s" % (idx, first, first + n - 1, raw, fn))
    last = max(first + -(-(raw + ARRAY_FOOTER) // sector) for _, first, _, raw in extras)
    print("sectors %d-%d of each half (%d KiB) are unused" % (last, HALF // sector - 1,
                                                            (HALF // sector - last) * sector // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
