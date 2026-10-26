# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26
"""Run: python3 tools/narcgfx/test_narcgfx.py (after a build, for nitrogfx and nitroarc)"""

import hashlib
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narcgfx as N  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
TOOLS = os.path.join(ROOT, "build", "heartgold.us", "tools")
GFX = os.path.join(TOOLS, "nitrogfx", "nitrogfx")
ARC = os.path.join(TOOLS, "nitroarc", "nitroarc")
FOLDERS = {"a/0/0/7": "battle_backgrounds", "a/0/0/8": "battle_sprites"}


def retail_sha1(name):
    with open(os.path.join(ROOT, "heartgold.us", "filesystem.sha1")) as f:
        for line in f:
            sha, path = line.split()
            if path == "*files/" + name:
                return sha


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


@unittest.skipUnless(os.path.exists(GFX) and os.path.exists(ARC), "build first (make)")
class TestNarcGfx(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def build(self, manifest, name="out.narc"):
        out = os.path.join(self.work, name)
        N.main(["build", manifest, out, "--nitrogfx", GFX, "--nitroarc", ARC,
                "--work", os.path.join(self.work, "w")])
        return out

    def test_folders_rebuild_retail(self):
        # graphics/battle_backgrounds and battle_sprites give back the retail archives
        for archive, folder in FOLDERS.items():
            manifest = os.path.join(ROOT, "graphics", folder, "members.json")
            self.assertEqual(sha1(self.build(manifest)), retail_sha1(archive), archive)

    def test_folders_hold_only_their_members(self):
        # every file is in members.json once, and members.json names only files that exist
        for folder in FOLDERS.values():
            base = os.path.join(ROOT, "graphics", folder)
            doc = N.load(os.path.join(base, "members.json"))
            listed = [m["file"] for m in doc["members"]]
            self.assertEqual(len(listed), len(set(listed)), folder)
            on_disk = {os.path.relpath(os.path.join(d, f), base) for d, _, fs in os.walk(base) for f in fs}
            self.assertEqual(on_disk - {"members.json"}, set(listed), folder)
            for m in doc["members"]:
                self.assertTrue(m.get("format") in doc["formats"] or N.source_type(m["file"]) is None, m)

    def test_export_round_trip(self):
        # a prebuilt archive exports to numbered files that build back byte for byte
        archive = os.path.join(ROOT, "files", "a", "0", "1", "4")
        folder = os.path.join(self.work, "export")
        N.main(["export", archive, folder, "--nitrogfx", GFX])
        self.assertEqual(sha1(self.build(os.path.join(folder, "members.json"))), sha1(archive))

    def test_move_and_cells(self):
        folder = os.path.join(self.work, "sprites")
        shutil.copytree(os.path.join(ROOT, "graphics", "battle_sprites"), folder)
        manifest = os.path.join(folder, "members.json")
        before = sha1(self.build(manifest, "before.narc"))
        N.main(["move", manifest, "type_icons/cells.NCER.json", "type_icons/shared/cells.NCER.json"])
        N.main(["move", manifest, "type_icons/fire.png", "type_icons/fire_renamed.png"])
        doc = N.load(manifest)
        fire = next(m for m in doc["members"] if m["file"] == "type_icons/fire_renamed.png")
        self.assertEqual(fire["cell"], "type_icons/shared/cells.NCER.json")
        self.assertEqual(sha1(self.build(manifest, "after.narc")), before)

    def test_format_names(self):
        self.assertEqual(N.format_name("NCGR", {"flags": ["-version101", "-sopc", "-bitdepth", "8"],
                                                "truncate": 65584, "lz": []}), "ncgr_v101_sopc_8bpp_cut_lz")
        self.assertEqual(N.format_name("NCLR", {"flags": ["-bitdepth", "4", "-nopad", "-pcmp", "-start", "9"]}),
                         "nclr_4bpp_nopad_pcmp_start9")


if __name__ == "__main__":
    unittest.main()
