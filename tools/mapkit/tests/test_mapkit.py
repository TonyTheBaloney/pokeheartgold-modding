# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Run: python3 tools/mapkit/tests/test_mapkit.py"""

import glob
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mapkit import Repo, cdefs, matrix, scripts  # noqa: E402
from mapkit.validate import ERROR, Validator  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


class TestDefines(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".h", delete=False)
        self.tmp.write(
            "#ifndef GUARD\n#define GUARD\n"
            "#define A 0x10 // comment\n"
            "#define B (A + 2) /* c */\n"
            "#define F(x) ((x) - A + 3000)\n"
            "#ifdef HEARTGOLD\n#define V 1\n#else\n#define V 2\n#endif\n"
            "#endif\n")
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_eval(self):
        d = cdefs.Defines({"HEARTGOLD"}).load(self.tmp.name)
        self.assertEqual(d.eval("A"), 16)
        self.assertEqual(d.eval("B * 2"), 36)
        self.assertEqual(d.eval("F(B)"), 3002)
        self.assertEqual(d.eval("V"), 1)
        self.assertIsNone(d.eval("UNKNOWN + 1"))

    def test_version(self):
        d = cdefs.Defines({"SOULSILVER"}).load(self.tmp.name)
        self.assertEqual(d.eval("V"), 2)


class TestRepoData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repo(ROOT)

    def test_matrix_round_trip(self):
        files = glob.glob(os.path.join(ROOT, "files/fielddata/mapmatrix/map_matrix/*.bin"))
        self.assertGreater(len(files), 200)
        for p in files:
            with open(p, "rb") as f:
                data = f.read()
            self.assertEqual(matrix.parse(data).to_bytes(), data, p)

    def test_find_map(self):
        r = self.repo
        self.assertEqual(r.find_map("T21").name, "MAP_CHERRYGROVE")
        self.assertEqual(r.find_map("cherrygrove").name, "MAP_CHERRYGROVE")
        self.assertEqual(r.find_map("Cherrygrove_PokeMart").name, "MAP_CHERRYGROVE_POKEMART")
        self.assertEqual(r.find_map("67").name, "MAP_CHERRYGROVE")

    def test_event_constants(self):
        r = self.repo
        m = r.find_map("T21")
        d = r.event_defines(m)
        self.assertEqual(d.eval("_EV_Cherrygrove_EventScript_MysticWaterMan + 1"), 5)
        self.assertEqual(d.eval("std_trainer(TRAINER_BUG_CATCHER_DON)"), 3000 + 249 - 1)
        self.assertEqual(r.script_file(m).script_label(5), "Cherrygrove_EventScript_MysticWaterMan")

    def test_macros(self):
        mt = self.repo.macros
        self.assertEqual(mt.get("NPCMsg").command_id, 45)
        self.assertEqual(mt.label_arg_indexes("GoTo"), {0})
        self.assertEqual(mt.label_arg_indexes("ApplyMovement"), {1})
        self.assertEqual(mt.get("WalkNormalNorth").kind, "movement")

    def test_clean_repo_has_no_errors(self):
        for version in ("HEARTGOLD", "SOULSILVER"):
            issues = Validator(Repo(ROOT, version)).run()
            errors = [str(i) for i in issues if i.severity == ERROR]
            self.assertEqual(errors, [], version)


class TestValidatorCatches(unittest.TestCase):
    """Break data in memory (cached objects) and check the validator notices."""

    def setUp(self):
        self.repo = Repo(ROOT)
        self.m = self.repo.find_map("T21")
        self.ev = self.repo.events(self.m)

    def errors(self, check):
        issues = Validator(self.repo).run([self.m])
        return [i for i in issues if i.severity == ERROR and i.check == check]

    def test_bad_warp_anchor(self):
        self.ev.warps[0]["anchor"] = 99
        self.assertTrue(self.errors("warp-dest"))

    def test_bad_movement(self):
        self.ev.objects[0]["movement"] = "MOVEMENT_TYPE_INVALID_47"
        self.assertTrue(self.errors("movement"))

    def test_script_id_out_of_range(self):
        self.ev.objects[0]["scriptId"] = "_EV_Cherrygrove_OnTransition + 2"
        self.assertTrue(self.errors("script-id"))

    def test_unresolved_flag(self):
        self.ev.objects[0]["eventFlag"] = "FLAG_DOES_NOT_EXIST"
        self.assertTrue(self.errors("unresolved"))

    def test_events_too_big(self):
        self.ev.objects.extend([dict(self.ev.objects[1]) for _ in range(60)])
        self.assertTrue(self.errors("events-size"))

    def test_script_problems(self):
        sf = self.repo.script_file(self.m)
        sf.statements.append(scripts.Statement(9999, "GoTo", ["_NOWHERE"], "Cherrygrove_EventScript_GuideGent"))
        sf.statements.append(scripts.Statement(10000, "NPCMsg", ["msg_0550_T21_99999"], "Cherrygrove_EventScript_GuideGent"))
        sf.statements.append(scripts.Statement(10001, "SetFlag", ["FLAG_DOES_NOT_EXIST"], "Cherrygrove_EventScript_GuideGent"))
        self.assertTrue(self.errors("missing-label"))
        self.assertTrue(self.errors("missing-text"))
        self.assertTrue(self.errors("unresolved"))


if __name__ == "__main__":
    unittest.main()
