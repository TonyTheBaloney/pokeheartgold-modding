# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
"""Run: python3 tools/mapkit/tests/test_mapkit.py"""

import glob
import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mapkit import Repo, cdefs, landdata, layouts, matrix, scripts, text  # noqa: E402
from mapkit.validate import ERROR, WARNING, Validator  # noqa: E402

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

    # sha1 of the retail map matrices (in NARC order, concatenated) and land data NARC
    RETAIL_MATRICES = "a1c8aafcef52db5d7466f5f37d678dd0519262be"
    RETAIL_LAND_DATA = "e98a8d144035f8b8f4373d203aab62c04d7c05f7"

    def test_layouts_build_the_retail_matrices(self):
        entries = layouts.read_index(ROOT)
        self.assertEqual(len(entries), 288)
        h = hashlib.sha1()
        for e in entries:
            m = layouts.load(ROOT, e["dir"])
            data = m.to_bytes()
            self.assertEqual(matrix.parse(data).to_bytes(), data, e["dir"])
            h.update(data)
        self.assertEqual(h.hexdigest(), self.RETAIL_MATRICES)

    def test_land_data_builds_the_retail_narc(self):
        data = landdata.narc_bytes([landdata.build(d) for d in landdata.chunk_dirs(ROOT)])
        self.assertEqual(hashlib.sha1(data).hexdigest(), self.RETAIL_LAND_DATA)

    def test_permissions_text_round_trip(self):
        p = landdata.Permissions([0x8000 | 0x0412, 0x0006] + [0] * 1022)
        q = landdata.Permissions.from_text(p.to_text())
        self.assertEqual(q.words()[:2], [0x8412, 0x0006])
        bad = p.to_text().replace("[behavior]", "[nope]")
        with self.assertRaises(landdata.LandDataError):
            landdata.Permissions.from_text(bad)

    def test_layout_errors(self):
        d = layouts.to_json(layouts.load(ROOT, "DiglettCave"), ROOT)
        d["land_data"][0][0] = "x"
        with self.assertRaises(layouts.LayoutError):
            layouts.from_json(d, ROOT)
        d = layouts.to_json(layouts.load(ROOT, "Overworld"), ROOT)
        d["maps"][0][0] = "MAP_NOPE"
        with self.assertRaises(layouts.LayoutError):
            layouts.from_json(d, ROOT)

    def test_map_layout_resolves(self):
        m = self.repo.find_map("Cherrygrove")
        self.assertEqual(m.header["matrixId"], "NARC_map_matrix_map_matrix_0000_EVERYWHERE_bin")
        self.assertEqual(self.repo.layout_folder(m), "Overworld")
        self.assertEqual(self.repo.matrix(m).width, 47)

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


class TestTextWidth(unittest.TestCase):
    """Lines wider than the 216 px dialogue box (mapkit validate -w, text-width)."""

    def setUp(self):
        self.repo = Repo(ROOT)
        self.m = self.repo.find_map("T21")
        self.tb = self.repo.text_bank(self.m)  # its messages list is the cached bank

    def warnings(self):
        issues = Validator(self.repo).run([self.m])
        return [i for i in issues if i.severity == WARNING and i.check == "text-width"]

    def test_retail_text_fits(self):
        self.assertEqual(self.warnings(), [])

    def test_long_line(self):
        self.tb.messages.append({"id": "msg_test", "en_US": "Fits on this line.\n" + "A" * 37})
        w = self.warnings()
        self.assertEqual(len(w), 1)
        self.assertIn("222 px", w[0].message)
        self.assertTrue(w[0].where.endswith("text.json msg_test"), w[0].where)

    def test_placeholder_counts_as_longest_name(self):
        line = "A" * 30 + " {STRVAR_1 3, 0, 0}"  # 186 px of text + a 42 px player name
        self.tb.messages.append({"id": "msg_test", "en_US": line})
        self.assertEqual(len(self.warnings()), 1)

    def test_points_at_scripts_pory(self):
        res = self.repo.pory_result(self.m)
        mid = next(i for i in res.text_lines if self.tb.get(i))
        self.tb.get(mid)["en_US"] = "W" * 40
        w = self.warnings()
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0].where, "data/maps/Cherrygrove/scripts.pory:%d" % res.text_lines[mid])

    def test_widths(self):
        w = text.Widths(os.path.join(ROOT, text.CHARMAP), os.path.join(ROOT, text.MESSAGE_FONT))
        self.assertEqual(w.lines("il"), [("il", 7)])
        self.assertEqual(w.lines("ab\nc{COLOR 1}d{COLOR 0}"), [("ab", 12), ("c{COLOR 1}d{COLOR 0}", 12)])
        self.assertEqual(w.lines("x{CURSOR_X 90}Lv."), [("x{CURSOR_X 90}Lv.", 90 + 17)])
        self.assertEqual(w.lines("{STRVAR_1 3, 0, 0}"), [("{STRVAR_1 3, 0, 0}", 0)])
        w.add_slot_widths({})
        self.assertEqual(w.lines("{STRVAR_1 3, 0, 0}")[0][1], text.NAME_PX)


if __name__ == "__main__":
    unittest.main()
