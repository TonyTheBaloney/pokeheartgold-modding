# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25
#
# gdb setup for debugging the ROM through an emulator's GDB stub
# (docs/modding/debugging.md). From the repository root:
#
#   gdb -x tools/debug/pokeheartgold.gdb build/heartgold.us/main.nef
#   (gdb) target remote localhost:3333
#
# Adds:
#   $loaded("field")   1 if that overlay is loaded, else 0 (for breakpoint conditions)
#   debuglog           print what DebugPrintf wrote to gDebugLog, oldest first
#   whereis ADDR       every function at ADDR, one per overlay, from main.nef.xMAP

set architecture armv5te
set pagination off
set confirm off
set print pretty on

python
import os
import re
import subprocess

# mwcc writes Windows-style paths into the debug info, so gdb can't open the
# sources by name. It does find them by file name in a "directory" list.
for top in ("src", "lib/src", "asm"):
    for path, _, _ in os.walk(top):
        gdb.execute("directory " + os.path.abspath(path), to_string=True)


def _elf():
    return gdb.current_progspace().filename


_overlay_ids = None


def overlay_ids():
    # SDK_OVERLAY_<name>_ID are absolute symbols. gdb reads odd ones as Thumb
    # addresses and drops bit 0, so take them from nm instead.
    global _overlay_ids
    if _overlay_ids is None:
        _overlay_ids = {}
        out = subprocess.run(["nm", _elf()], capture_output=True, text=True).stdout
        for m in re.finditer(r"^([0-9a-f]+) \S SDK_OVERLAY_(\w+)_ID$", out, re.M):
            _overlay_ids[m.group(2)] = int(m.group(1), 16)
    return _overlay_ids


class OverlayLoaded(gdb.Function):
    """$loaded("name"): 1 if overlay NAME (as in main.lsf: field, OVY_12...) is loaded."""

    def __init__(self):
        super().__init__("loaded")

    def invoke(self, name):
        ovy_id = overlay_ids()[name.string()]
        regions = gdb.parse_and_eval("sOverlayRegions")
        for region in range(3):
            for i in range(8):
                ovy = regions[region][i]
                if int(ovy["active"]) and int(ovy["id"]) == ovy_id:
                    return 1
        return 0


class DebugLog(gdb.Command):
    """Print what DebugPrintf wrote to gDebugLog, oldest first."""

    def __init__(self):
        super().__init__("debuglog", gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        size = int(gdb.parse_and_eval("sizeof(gDebugLog)"))
        pos = int(gdb.parse_and_eval("gDebugLogPos"))
        addr = int(gdb.parse_and_eval("(unsigned long)&gDebugLog"))
        buf = gdb.selected_inferior().read_memory(addr, size).tobytes()
        text = bytes(buf[i % size] for i in range(max(0, pos - size), pos))
        gdb.write(text.decode("latin-1"))


class WhereIs(gdb.Command):
    """whereis ADDR: every function containing ADDR, with its object file (overlays share addresses)."""

    def __init__(self):
        super().__init__("whereis", gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        value = gdb.parse_and_eval(arg)
        if value.type.code == gdb.TYPE_CODE_FUNC:
            value = value.address
        addr = int(value) & ~1
        xmap = _elf() + ".xMAP"
        line_re = re.compile(r"^  ([0-9A-F]{8}) ([0-9A-F]{8}) \.text\s+(\S+)\t\((\S+)\)")
        with open(xmap) as f:
            for line in f:
                m = line_re.match(line)
                if not m or m.group(3).startswith("$"):
                    continue
                start, size = int(m.group(1), 16), int(m.group(2), 16)
                if start <= addr < start + size:
                    gdb.write("0x%08x  %s+%d  (%s)\n" % (addr, m.group(3), addr - start, m.group(4)))


OverlayLoaded()
DebugLog()
WhereIs()
end
