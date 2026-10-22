# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Zone event JSON (files/fielddata/eventdata/zone_event/NNN_CODE.json).

Binary layout (files/fielddata/eventdata/zone_event.json.txt): four sections,
each a u32 count followed by records of 20 (bg), 32 (object), 12 (warp) and
16 (coord) bytes. The engine reads the file into a 0x800-byte buffer and
asserts the size is strictly smaller (src/map_events.c).
"""

import json
from dataclasses import dataclass

EVENT_BUFFER_SIZE = 0x800
BG_SIZE, OBJECT_SIZE, WARP_SIZE, COORD_SIZE = 20, 32, 12, 16
DYNAMIC_WARP_ANCHOR = 0x100
DYNAMIC_WARP_HEADER = 0xFFF


@dataclass
class Events:
    path: str
    header: str
    bgs: list
    objects: list
    warps: list
    coords: list

    @property
    def binary_size(self):
        return (16 + BG_SIZE * len(self.bgs) + OBJECT_SIZE * len(self.objects)
                + WARP_SIZE * len(self.warps) + COORD_SIZE * len(self.coords))


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return Events(path, d.get("header"), d.get("bgs", []), d.get("objects", []),
                  d.get("warps", []), d.get("coords", []))


def is_dynamic_warp(warp, defines):
    return (defines.eval(warp.get("anchor")) == DYNAMIC_WARP_ANCHOR
            and defines.eval(warp.get("header")) == DYNAMIC_WARP_HEADER)
