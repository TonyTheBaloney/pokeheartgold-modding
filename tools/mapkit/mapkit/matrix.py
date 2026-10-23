# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
"""Map matrix (.bin) reader. Layout from src/map_matrix.c:

u8 width, height, hasHeaders, hasAltitudes, nameLen; char name[nameLen]
[u16 mapHeaderIds[w*h]] [u8 altitudes[w*h]] u16 landDataIds[w*h]
"""

import struct
from dataclasses import dataclass, field

CELL_SIZE = 32  # tiles per matrix cell side


@dataclass
class Matrix:
    width: int
    height: int
    name: str
    header_ids: list = field(default_factory=list)  # empty if the matrix has none
    altitudes: list = field(default_factory=list)
    land_ids: list = field(default_factory=list)

    def cell(self, x, z):
        """Cell index for global tile coordinates, or None if outside."""
        cx, cz = x // CELL_SIZE, z // CELL_SIZE
        if 0 <= cx < self.width and 0 <= cz < self.height:
            return cz * self.width + cx
        return None

    def to_bytes(self):
        name = self.name.encode("ascii")
        out = struct.pack("<5B", self.width, self.height, bool(self.header_ids),
                          bool(self.altitudes), len(name)) + name
        if self.header_ids:
            out += struct.pack("<%dH" % len(self.header_ids), *self.header_ids)
        if self.altitudes:
            out += bytes(self.altitudes)
        return out + struct.pack("<%dH" % len(self.land_ids), *self.land_ids)


def parse(data):
    w, h, has_headers, has_alt, name_len = struct.unpack_from("<5B", data, 0)
    pos = 5
    name = data[pos:pos + name_len].decode("ascii", "replace")
    pos += name_len
    n = w * h
    headers, alts = [], []
    if has_headers:
        headers = list(struct.unpack_from("<%dH" % n, data, pos))
        pos += 2 * n
    if has_alt:
        alts = list(data[pos:pos + n])
        pos += n
    land = list(struct.unpack_from("<%dH" % n, data, pos))
    return Matrix(w, h, name, headers, alts, land)


def load(path):
    with open(path, "rb") as f:
        return parse(f.read())
