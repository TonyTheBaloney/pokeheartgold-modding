# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""poryscript-style compiler. Run: python3 tools/mapkit/tests/test_pory.py"""

import os
import sys
import unittest

sys.path[:0] = [os.path.join(os.path.dirname(__file__), ".."), os.path.dirname(__file__)]

from mapkit import Repo  # noqa: E402
from mapkit.pory import compiler, PoryError  # noqa: E402
from pory_roundtrip import roundtrip  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
REPO = Repo(ROOT)


def compile_(src, switches=None):
    ctx = compiler.Context(REPO.macros, compiler.load_config(), None, None, "test.pory")
    return compiler.compile_source(src, ctx, switches)


def body(src, name="S"):
    """Lines of script `name` (up to the next top-level label/blank+label)."""
    out = compile_(src).scripts_inc.split("\n")
    i = out.index(name + ":")
    lines = []
    for l in out[i + 1:]:
        if l and not l.startswith("\t") and not l.startswith(name + "_"):
            break
        if l:
            lines.append(l.strip())
    return lines


class Lowering(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(body("script S { lockall faceplayer waitbuttonpress closemessage releaseall }"),
                         ["LockAll", "FacePlayer", "WaitButton", "CloseMsg", "ReleaseAll", "End"])
        self.assertEqual(body("script S { LockAll }"), ["LockAll", "End"])

    def test_if_early_exit_goes_after_end(self):
        self.assertEqual(body("script S { if (flag(F)) { npcmsg(M) end } setflag(G) }"), [
            "GoToIfSet F, S_If_1", "SetFlag G", "End", "S_If_1:", "NPCMsg M", "End"])

    def test_if_else(self):
        self.assertEqual(body("script S { if (!flag(F)) { setflag(A) } else { setflag(B) } }"), [
            "GoToIfSet F, S_Else_2", "SetFlag A", "GoTo S_EndIf_1", "S_Else_2:", "SetFlag B",
            "S_EndIf_1:", "End"])

    def test_elif_and_or(self):
        self.assertEqual(body("script S { if (var(V) == 1 || flag(F)) { setflag(A) } "
                              "elif (var(V) >= 3 && !defeated(T)) { setflag(B) } }"), [
            "Compare V, 1", "GoToIfEq S_Skip_3", "GoToIfUnset F, S_Else_2", "S_Skip_3:",
            "SetFlag A", "GoTo S_EndIf_1", "S_Else_2:",
            "Compare V, 3", "GoToIfLt S_EndIf_1", "GoToIfDefeated T, S_EndIf_1", "SetFlag B",
            "S_EndIf_1:", "End"])

    def test_flag_compared_with_false(self):
        self.assertEqual(body("script S { if (flag(F) == FALSE) { setflag(F) } }")[0], "GoToIfSet F, S_EndIf_1")

    def test_one_sided_condition_is_inverted(self):
        # itemspace only has a "no space" jump; jumping on "has space" goes around a GoTo
        self.assertEqual(body("script S { if (itemspace(ITEM_X, 1)) { setflag(A) } else { end } }")[:2],
                         ["GoToIfNoItemSpace ITEM_X, 1, S_Else_2", "SetFlag A"])
        self.assertEqual(body("script S { while (itemspace(ITEM_X, 1)) { addvar(V, 1) } }")[:3],
                         ["S_While_1:", "GoToIfNoItemSpace ITEM_X, 1, S_EndWhile_2", "AddVar V, 1"])

    def test_autovar(self):
        self.assertEqual(body("script S { if (getmenuchoice(VAR_SPECIAL_RESULT) == 1) { end } }")[:3],
                         ["GetMenuChoice VAR_SPECIAL_RESULT", "Compare VAR_SPECIAL_RESULT, 1", "GoToIfEq S_If_1"])

    def test_loops(self):
        self.assertEqual(body("script S { while (var(V) < 3) { addvar(V, 1) if (flag(F)) { break } } }"), [
            "S_While_1:", "Compare V, 3", "GoToIfGe S_EndWhile_2", "AddVar V, 1",
            "GoToIfSet F, S_EndWhile_2", "GoTo S_While_1", "S_EndWhile_2:", "End"])
        self.assertEqual(body("script S { if (flag(F)) { goto(Elsewhere) } end }"),
                         ["GoToIfSet F, Elsewhere", "End"])
        self.assertEqual(body("script S { do { addvar(V, 1) } while (var(V) != 5) }"), [
            "S_Do_1:", "AddVar V, 1", "S_DoCond_2:", "Compare V, 5", "GoToIfNe S_Do_1", "S_EndDo_3:", "End"])

    def test_switch(self):
        self.assertEqual(body("script S { switch (var(V)) { case 0: case 1: setflag(A) case 2: end default: setflag(B) } }"), [
            "Compare V, 0", "GoToIfEq S_Case_2", "Compare V, 1", "GoToIfEq S_Case_2",
            "Compare V, 2", "GoToIfEq S_Case_3", "GoTo S_Default_4",
            "S_Case_2:", "SetFlag A", "GoTo S_EndSwitch_1", "S_Case_3:", "End",
            "S_Default_4:", "SetFlag B", "S_EndSwitch_1:", "End"])

    def test_text_and_movement(self):
        r = compile_('script S { npcmsg("Hi!\\nBye.") applymovement(obj_player, moves(walk_up * 2, face_left)) }\n'
                     'text S_Text_Other { "a" "b" }\nmovement M { walk_in_place_fast_down jump_far_right * 2 }')
        self.assertEqual(r.texts, [("S_Text_0", "Hi!\nBye."), ("S_Text_Other", "ab")])
        inc = r.scripts_inc
        self.assertIn("\tNPCMsg S_Text_0", inc)
        self.assertIn("S_Movement_0:\n\tWalkNormalNorth 2\n\tFaceWest\n\tEndMovement", inc)
        self.assertIn("M:\n\tWalkOnSpotFastSouth\n\tJumpFarEast 2\n\tEndMovement", inc)
        self.assertEqual(compiler.text_entry("x", "Hi!\nBye.\r"), {"id": "x", "en_US": ["Hi!\n", "Bye.\r"]})

    def test_const_and_poryswitch(self):
        src = ("const F = FLAG_REAL\nscript S { setflag(F) "
               "poryswitch(GAME) { HEARTGOLD: setflag(HG) SOULSILVER: setflag(SS) } }")
        self.assertEqual(body(src)[:2], ["SetFlag FLAG_REAL", "SetFlag HG"])
        r = compile_(src, {"GAME": "SOULSILVER"})
        self.assertIn("SetFlag SS", r.scripts_inc)

    def test_script_numbers_and_mapscripts(self):
        r = compile_("raw `\n\tScrDef Old_A\n\tScrDef Old_B\n\tScrDefEnd\nOld_A:\n\tEnd\n`\n"
                     "script Old_B { end }\nscript New_C { end }\nscript(local) Helper { return }\n"
                     "mapscripts MS { INIT_SCRIPT_ON_TRANSITION: New_C\n"
                     "INIT_SCRIPT_ON_FRAME_TABLE [ VAR_X, 1 { end } ] }")
        self.assertEqual(r.public, ["Old_A", "Old_B", "New_C", "MS_FrameTable_0"])
        self.assertIn("\tInitScriptEntry_OnTransition 3  // New_C", r.map_scripts_inc)
        self.assertIn("\tInitScriptGoToIfEqual VAR_X, 1, 4  // MS_FrameTable_0", r.map_scripts_inc)
        self.assertEqual(r.scripts_inc.count("ScrDefEnd"), 1)

    def test_errors(self):
        for src, msg in [("script S { nosuchcommand }", "unknown command"),
                         ("script S { break }", "outside a loop"),
                         ("script S { end }\nscript S { end }", "defined twice"),
                         ("script S { if (flag(F) { end } }", "expected"),
                         ("script S { if (bogus(X)) { end } }", "unknown command"),
                         ("script S { if (lockall() == 1) { end } }", "not a condition")]:
            with self.assertRaises(PoryError) as cm:
                compile_(src)
            self.assertIn(msg, str(cm.exception), src)


class Conversion(unittest.TestCase):
    def test_every_map_converts_without_changing_commands(self):
        checked = 0
        for m in REPO.maps:
            e = REPO.migrated[m.name]
            if e["scripts"].startswith("@") or e["init"].startswith("@") or REPO.pory_entry(m):
                continue
            self.assertIsNone(roundtrip(REPO, m), m.name)
            checked += 1
        self.assertGreater(checked, 400)

    def test_cherrygrove_pory_validates(self):
        m = REPO.find_map("Cherrygrove")
        self.assertIsNotNone(REPO.pory_result(m))
        from mapkit.validate import ERROR, Validator
        self.assertEqual([str(i) for i in Validator(REPO).run([m]) if i.severity == ERROR], [])


if __name__ == "__main__":
    unittest.main()
