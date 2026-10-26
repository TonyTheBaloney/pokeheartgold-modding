# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26
"""Map texture sets (areatex.py) and NSBTX writing (nsbtx.py)."""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import areatex, landdata, nitro, nsbtx  # noqa: E402


def retail_sha1(rel):
    with open(os.path.join(ROOT, "heartgold.us", "filesystem.sha1")) as f:
        for line in f:
            sha, path = line.split()
            if path == "*files/" + rel:
                return sha


class Retail(unittest.TestCase):
    def test_folders_rebuild_the_archive(self):
        # data/area_textures gives back the retail a/0/4/4 byte for byte
        data = landdata.narc_bytes([areatex.build_set(d) for d in areatex.set_dirs(ROOT)])
        self.assertEqual(hashlib.sha1(data).hexdigest(), retail_sha1("a/0/4/4"))

    def test_prop_textures_round_trip(self):
        # the writer also lays out the map prop textures (a/0/7/0) exactly
        with open(os.path.join(ROOT, "files/a/0/7/0"), "rb") as f:
            members = [m for m in landdata.narc_members(f.read()) if m[:4] == b"BTX0"]
        self.assertEqual(len(members), 94)
        for i, m in enumerate(members):
            self.assertEqual(nsbtx.write(*nsbtx.read(m)), m, i)

    def test_check_passes(self):
        count, problems = areatex.check(ROOT)
        self.assertEqual((count, problems), (106, []))


class Editing(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "data", "area_textures"))
        with open(os.path.join(self.root, "data", "gen4map.json"), "w") as f:
            json.dump({"paths": {"area_textures": "data/area_textures"}}, f)
        shutil.copytree(os.path.join(ROOT, "data", "area_textures", "002"),
                        os.path.join(self.root, "data", "area_textures", "000"))
        self.set = os.path.join(self.root, "data", "area_textures", "000")

    def tearDown(self):
        shutil.rmtree(self.root)

    def png(self, name, w, h, values, colors, transparent0=False):
        entries = [areatex.rgb(c) + (0 if transparent0 and i == 0 else 255,) for i, c in enumerate(colors)]
        path = os.path.join(self.root, name)
        with open(path, "wb") as f:
            f.write(areatex.png_bytes(w, h, values, entries))
        return path

    def test_add_texture(self):
        before = len(areatex.load_doc(self.set)["textures"])
        values = [(x + y) % 16 for y in range(32) for x in range(32)]
        colors = [i * 0x842 & 0x7FFF for i in range(16)]
        e = areatex.add(self.root, 0, self.png("stone_new.png", 32, 32, values, colors, True))
        self.assertEqual(e, {"name": "stone_new", "format": "palette16", "transparent": True, "palette": "stone_new_pl"})
        textures, palettes = nsbtx.read(areatex.build_set(self.set))
        self.assertEqual(len(textures), before + 1)
        t = textures[-1]
        self.assertEqual((t.name, t.format, t.width, t.height, t.color0_transparent), ("stone_new", "palette16", 32, 32, True))
        self.assertEqual(t.indices(), values)
        self.assertEqual(palettes[-1].name, "stone_new_pl")
        self.assertEqual(palettes[-1].colors, colors)
        # the game's decoder sees it
        img = nitro.load_nsbtx(areatex.build_set(self.set)).image("stone_new", "stone_new_pl")
        self.assertEqual(img[:2], (32, 32))

    def test_add_small_texture_and_shared_palette(self):
        e = areatex.add(self.root, 0, self.png("dots.png", 16, 8, [i % 4 for i in range(128)], [0, 0x1F, 0x3E0, 0x7C00]))
        self.assertEqual((e["format"], e["palette"]), ("palette4", "dots_pl"))
        doc = areatex.load_doc(self.set)
        self.assertEqual(doc["palettes"][-1], {"name": "dots_pl", "four_color": True})
        e = areatex.add(self.root, 0, self.png("dots2.png", 8, 8, [1] * 64, [0, 0x1F]), palette="dots_pl")
        self.assertEqual(e["palette"], "dots_pl")
        self.assertEqual(len(areatex.load_doc(self.set)["palettes"]), len(doc["palettes"]))
        areatex.build_set(self.set)

    def test_add_refuses(self):
        with self.assertRaises(areatex.AreaTexError):   # name taken
            areatex.add(self.root, 0, self.png("road01.png", 8, 8, [0] * 64, [0]))
        with self.assertRaises(areatex.AreaTexError):   # not a power of two
            areatex.add(self.root, 0, self.png("odd.png", 24, 8, [0] * 192, [0]))
        with self.assertRaises(areatex.AreaTexError):   # 17 colors don't fit palette16
            areatex.add(self.root, 0, self.png("many.png", 8, 8, [i % 17 for i in range(64)], [0] * 17),
                        fmt="palette16")

    def test_edit_keeps_alpha_textures(self):
        # an a5i3 texture's PNG holds index and opacity; rewriting its colors keeps the texels
        doc = areatex.load_doc(self.set)
        entry = next(t for t in doc["textures"] if t["format"] == "a5i3")
        path = areatex.tex_path(self.set, entry["name"])
        before = areatex.read_texture(path, entry).texels
        areatex.color(self.root, 0)
        self.assertEqual(areatex.read_texture(path, entry).texels, before)

    def test_check_finds_stray_files(self):
        open(os.path.join(self.set, "textures", "stray.png"), "wb").close()
        _, problems = areatex.check(self.root)
        self.assertTrue(any("stray.png" in msg for _, msg in problems))

    def test_palette_files_are_exact(self):
        path = os.path.join(self.root, "p.pal")
        colors = list(range(0, 0x8000, 0x111))
        areatex.write_pal(path, colors)
        self.assertEqual(areatex.read_pal(path), colors)


if __name__ == "__main__":
    unittest.main()
