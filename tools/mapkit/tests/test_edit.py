# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Edit commands, run on a temporary copy of the data. Run: python3 tools/mapkit/tests/test_edit.py"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mapkit import Repo, edit, layout  # noqa: E402
from mapkit.validate import ERROR, Validator  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
COPY = ["include", "asm/macros", "data/maps", "src/data/map_headers.h", "files/fielddata/eventdata",
        "files/fielddata/script", "files/fielddata/mapmatrix", "files/fielddata/encountdata", "files/msgdata/msg"]


class EditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="mapkit-test-")
        for rel in COPY:
            src, dst = os.path.join(ROOT, rel), os.path.join(cls.tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, dst)
        subprocess.run(["git", "init", "-q"], cwd=cls.tmp, check=True)
        subprocess.run(["git", "add", "-A"], cwd=cls.tmp, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"],
                       cwd=cls.tmp, check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def setUp(self):
        subprocess.run(["git", "checkout", "-q", "--", "."], cwd=self.tmp, check=True)
        self.repo = Repo(self.tmp)
        self.m = self.repo.find_map("Cherrygrove")

    def changed_files(self):
        out = subprocess.run(["git", "diff", "--numstat"], cwd=self.tmp, capture_output=True, text=True).stdout
        return {line.split("\t")[2]: (int(line.split("\t")[0]), int(line.split("\t")[1])) for line in out.splitlines()}

    def assert_valid(self, maps=None):
        errors = [str(i) for i in Validator(Repo(self.tmp)).run(maps) if i.severity == ERROR]
        self.assertEqual(errors, [])

    def test_npc_move_changes_only_two_lines(self):
        edit.npc_set(self.repo, self.m, "gsboy1", x=560, y=400)
        self.assertEqual(self.changed_files(), {"data/maps/Cherrygrove/map.json": (2, 2)})
        o = Repo(self.tmp).events(self.m).objects[1]
        self.assertEqual((o["x"], o["z"]), (560, 400))

    def test_npc_move_unmigrated_map(self):
        m = self.repo.find_map("MAP_ROUTE_30")
        edit.npc_set(self.repo, m, "0", x=551, y=300)
        files = self.changed_files()
        self.assertEqual(list(files.values()), [(2, 2)])
        self.assertTrue(list(files)[0].startswith("files/fielddata/eventdata/zone_event/"))

    def test_add_npc_with_new_script_and_text(self):
        msg = edit.text_add(self.repo, self.m, "Hello!\\nNice day.")
        self.assertEqual(msg, "msg_0550_T21_00025")
        sid = edit.script_add(self.repo, self.m, "Cherrygrove_EventScript_Fisher", msg)
        self.assertEqual(sid, 12)
        rec = edit.npc_add(self.repo, self.m, "fisher", "SPRITE_FISHING", 560, 400,
                           script="Cherrygrove_EventScript_Fisher")
        self.assertEqual(rec["local_id"], "obj_T21_fisher")
        repo = Repo(self.tmp)
        defs = repo.event_defines(self.m)
        self.assertEqual(defs.eval("obj_T21_fisher"), 6)
        self.assertEqual(defs.eval(repo.events(self.m).objects[-1]["scriptId"]), 12)
        self.assertEqual(repo.script_file(self.m).script_label(12), "Cherrygrove_EventScript_Fisher")
        self.assert_valid([self.m])

    def test_warp_link_sets_both_sides(self):
        pc = self.repo.find_map("MAP_CHERRYGROVE_POKECENTER_1F")
        edit.warp_link(self.repo, self.m, 1, pc, 0)
        repo = Repo(self.tmp)
        self.assertEqual(repo.events(self.m).warps[1]["header"], "MAP_CHERRYGROVE_POKECENTER_1F")
        self.assertEqual(repo.events(pc).warps[0]["header"], "MAP_CHERRYGROVE")
        self.assertEqual(repo.events(pc).warps[0]["anchor"], 1)

    def test_wild_set(self):
        r29 = self.repo.find_map("MAP_ROUTE_29")
        edit.wild_set(self.repo, r29, "land", 0, "SPECIES_PIKACHU", 4, time="day")
        _, t = Repo(self.tmp).wild_table(r29)
        self.assertEqual(t["land"]["mons"][0]["species"]["day"], "SPECIES_PIKACHU")
        self.assertNotEqual(t["land"]["mons"][0]["species"]["morn"], "SPECIES_PIKACHU")
        self.assertEqual(t["land"]["mons"][0]["level"], 4)
        self.assertEqual(list(self.changed_files()), ["files/fielddata/encountdata/gs_enc_data.json"])

    def test_script_rename_updates_references(self):
        edit.script_rename(self.repo, self.m, "Cherrygrove_EventScript_Boy", "Cherrygrove_EventScript_TiredBoy")
        repo = Repo(self.tmp)
        self.assertIn("Cherrygrove_EventScript_TiredBoy", repo.script_file(self.m).scrdefs)
        self.assertEqual(repo.event_defines(self.m).eval(repo.events(self.m).objects[1]["scriptId"]), 8)
        self.assert_valid([self.m])

    def test_bad_script_label_is_caught(self):
        edit.npc_set(self.repo, self.m, "gsboy1", script="Cherrygrove_EventScript_Missing")
        errors = [i for i in Validator(Repo(self.tmp)).run([self.m]) if i.severity == ERROR]
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
