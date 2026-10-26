# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""NSBMD / NSBTX decoding against the game's own models and textures."""

import collections
import glob
import os
import struct
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import areatex, landdata, layouts, nitro  # noqa: E402


def narc(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        return landdata.narc_members(f.read())


class Models(unittest.TestCase):
    def test_every_terrain_and_prop_model_decodes(self):
        sources = [open(p, "rb").read() for p in sorted(glob.glob(os.path.join(ROOT, "data/landdata/*/model.nsbmd")))]
        sources += narc("files/a/0/4/0") + narc("files/a/1/4/8")
        self.assertEqual(len(sources), 676 + 340 + 222)
        total = 0
        for i, d in enumerate(sources):
            models, _ = nitro.load_nsbmd(d)
            for m in models:
                total += len(m.triangles())
        self.assertGreater(total, 800000)

    def test_cherrygrove_cell(self):
        lay = layouts.load(ROOT, "Overworld")
        land = lay.land_ids[12 * lay.width + 16]
        with open(os.path.join(ROOT, landdata.LANDDATA_DIR, "%04d" % land, "model.nsbmd"), "rb") as f:
            (model,), own = nitro.load_nsbmd(f.read())
        self.assertIsNone(own)  # map models take their textures from the area
        tris = model.triangles()
        xs = [p[0] for t in tris for p in t.pos]
        zs = [p[2] for t in tris for p in t.pos]
        # a cell is 512 units (32 tiles of 16) around its centre
        self.assertLessEqual(max(map(abs, xs + zs)), 300)
        self.assertGreater(max(xs) - min(xs), 500)
        # every texture the model names is in Cherrygrove's area texture set (area 2 -> set 2)
        _prop, tex_id, _anim, _kind, _light = struct.unpack("<HHHBB", narc("files/a/0/4/2")[2])
        texset = areatex.texture_set(ROOT, tex_id)
        names = {m.texture for m in model.materials if m.texture}
        self.assertTrue(names)
        self.assertEqual(names - set(texset.textures), set())

    def test_skinned_prop_stays_in_place(self):
        # Ecruteak Gym's floor (room prop 146) blends joints with NODEMIX and scales in its display lists
        (model,), _ = nitro.load_nsbmd(narc("files/a/1/4/8")[146])
        ys = [p[1] for t in model.triangles() for p in t.pos]
        self.assertLess(max(ys) - min(ys), 64)


class Textures(unittest.TestCase):
    def test_every_texture_decodes(self):
        formats = collections.Counter()
        sets = [areatex.texture_set(ROOT, i) for i in range(len(areatex.set_dirs(ROOT)))]
        sets += [nitro.load_nsbtx(d) for d in narc("files/a/0/7/0") if d[:4] == b"BTX0"]
        for ts in sets:
            for name, t in ts.textures.items():
                pal = next(iter(ts.palettes.values()), [])
                rgba = t.decode(pal)
                self.assertEqual(len(rgba), t.width * t.height * 4, name)
                formats[t.format] += 1
        # A3I5, 4-, 16- and 256-color and A5I3 occur (no 4x4-compressed in these sets; test_formats covers it)
        for fmt in (1, 2, 3, 4, 6):
            self.assertIn(fmt, formats, nitro.FMT_NAMES[fmt])

    def test_formats(self):
        def tex(fmt, data, w=8, h=8, idx=b"", tr=False):
            param = (fmt << 26) | (int(tr) << 29)
            t = nitro.Texture("t", param, 0, len(data), data + idx)
            return t
        pal = [0x001F, 0x03E0, 0x7C00, 0x7FFF]                      # red, green, blue, white
        # 4-color, color 0 transparent: first texel index 1 -> green
        t = tex(2, bytes([0b11100101]) + bytes(15), tr=True)
        rgba = t.decode(pal)
        self.assertEqual(rgba[0:4], bytes((0, 255, 0, 255)))
        self.assertEqual(rgba[8:12], bytes((0, 0, 255, 255)))
        self.assertEqual(rgba[4:8], bytes((0, 255, 0, 255)))
        t0 = tex(2, bytes(16), tr=True).decode(pal)
        self.assertEqual(t0[3], 0)
        # A3I5: alpha 7 (opaque), index 3 -> white
        self.assertEqual(tex(1, bytes([0xE3]) * 64).decode(pal)[0:4], bytes((255, 255, 255, 255)))
        # direct: bit 15 = opaque
        self.assertEqual(tex(7, struct.pack("<H", 0x801F) * 64).decode([])[0:4], bytes((255, 0, 0, 255)))
        # 4x4 mode 1: index 2 is the average of colors 0 and 1
        blocks_ = struct.pack("<I", 0xAAAAAAAA) * 4
        idx = struct.pack("<H", 1 << 14) * 4
        rgba = tex(5, blocks_, idx=idx).decode(pal)
        self.assertEqual(rgba[0:4], bytes((127, 127, 0, 255)))


if __name__ == "__main__":
    unittest.main()
