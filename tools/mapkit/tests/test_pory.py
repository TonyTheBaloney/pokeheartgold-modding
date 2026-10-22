# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""poryscript-style compiler. Run: python3 tools/mapkit/tests/test_pory.py"""

import os
import sys
import unittest

sys.path[:0] = [os.path.join(os.path.dirname(__file__), ".."), os.path.dirname(__file__)]

from mapkit import Repo  # noqa: E402
from mapkit import pory  # noqa: E402
from mapkit.pory import compiler, decompile, inline_text, naming, PoryError  # noqa: E402
from pory_roundtrip import roundtrip  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
REPO = Repo(ROOT)


def compile_(src, switches=None, slots=None):
    ctx = compiler.Context(REPO.macros, compiler.load_config(), None, None, "test.pory", slots)
    return compiler.compile_source(src, ctx, switches)


def body(src, name="S"):
    """Lines of script `name` (up to the next top-level label/blank+label)."""
    out = compile_(src).scripts_inc.split("\n")
    i = out.index(name + ":")
    lines = []
    for l in out[i + 1:]:
        if l and not l.startswith("\t") and not l.startswith(name + "_"):
            break
        if l and not l.strip().startswith("."):
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

    def test_scrdefs(self):
        r = compile_("scrdefs { B, A }\nscript A { end }\nscript B { end }\nscript New { end }\n"
                     "script(local) L { inner: return }")
        self.assertEqual(r.public, ["B", "A", "New"])
        self.assertIn("\tScrDef B\n\tScrDef A\n\tScrDef New\n\tScrDefEnd", r.scripts_inc)
        self.assertEqual(compile_("scrdefs { inner }\nscript(local) L { inner: return }").public, ["inner"])

    def test_errors(self):
        for src, msg in [("script S { nosuchcommand }", "unknown command"),
                         ("script S { break }", "outside a loop"),
                         ("script S { end }\nscript S { end }", "defined twice"),
                         ("script S { if (flag(F) { end } }", "expected"),
                         ("script S { if (bogus(X)) { end } }", "unknown command"),
                         ("script S { if (lockall() == 1) { end } }", "not a condition"),
                         ("scrdefs { S, Missing }\nscript S { end }", "no script or label named Missing"),
                         ("scrdefs { S }\nscrdefs { S }\nscript S { end }", "only one scrdefs"),
                         ("scrdefs { S, S }\nscript S { end }", "defined twice")]:
            with self.assertRaises(PoryError) as cm:
                compile_(src)
            self.assertIn(msg, str(cm.exception), src)


def decompiled(inc):
    """scripts.inc text -> (pory lines, stats) for a test map."""
    ctx = compiler.Context(REPO.macros, compiler.load_config(), None, None, "test.pory")
    d = decompile.Decompiler(ctx, "Test", inc)
    lines, stats = d.run(set())
    res = compiler.compile_source("\n".join(lines) + "\n", ctx)
    assert decompile.fingerprint(inc, REPO.macros) == decompile.fingerprint(res.scripts_inc, REPO.macros), \
        "\n".join(lines)
    return "\n".join(lines), stats


HEAD = "\tScrDef A\n\tScrDefEnd\n\nA:\n"


class InlineText(unittest.TestCase):
    SRC = 'script S { npcmsg("a") if (flag(F)) { npcmsg("b") end } npcmsg("c") }'

    def test_strings_fill_slots_in_source_order(self):
        # "b" is emitted last (after End) but is still the script's string 1
        r = compile_(self.SRC, slots={"S#1": "msg_X_00001"})
        self.assertEqual(r.texts, [("S_Text_0", "a"), ("S_Text_2", "c"), ("msg_X_00001", "b")])
        self.assertIn("NPCMsg msg_X_00001", r.scripts_inc)

    def test_merged_bank_keeps_numbers(self):
        r = compile_(self.SRC, slots={"S#1": "msg_X_00001"})
        bank = {"key": 1, "messages": [{"id": "msg_X_00000", "en_US": "kept"},
                                       {"id": "msg_X_00001", "from": "S#1"},
                                       {"id": "msg_X_00002", "from": "Gone#0"}]}
        unfilled = []
        out = pory.merged_text(REPO, {"dir": "X"}, r, unfilled, bank)["messages"]
        self.assertEqual([(m["id"], m["en_US"]) for m in out], [
            ("msg_X_00000", "kept"), ("msg_X_00001", "b"), ("msg_X_00002", ""),
            ("S_Text_0", "a"), ("S_Text_2", "c")])
        self.assertEqual(unfilled, [("msg_X_00002", "Gone#0")])

    def test_literals(self):
        self.assertEqual(inline_text.literal_parts('Say "hi"\\\rNext {STRVAR_1 3, 0, 0}\n'),
                         ['"Say \\"hi\\"\\\\\\r"', '"Next {STRVAR_1 3, 0, 0}\\n"'])
        self.assertEqual(compile_('script S { npcmsg(%s) }' % " ".join(
            inline_text.literal_parts('Say "hi"\\\rNext\n'))).texts, [("S_Text_0", 'Say "hi"\\\rNext\n')])

    def test_every_dialog_matches_text_json_order(self):
        # every slot is filled and every map's bank has its messages in the original order
        for m in REPO.maps:
            e = REPO.migrated[m.name]
            if e["text"].startswith("@") or REPO.pory_entry(m) is None or REPO.pory_entry(m)["dir"] != e["dir"]:
                continue
            unfilled = []
            out = pory.merged_text(REPO, e, REPO.pory_result(m), unfilled)["messages"]
            self.assertEqual(unfilled, [], e["dir"])
            for i, msg in enumerate(out[:len(REPO.text_bank(m).messages)]):
                if msg["id"].startswith("msg_"):
                    self.assertTrue(msg["id"].endswith("_%05d" % i), (e["dir"], msg["id"], i))


class Naming(unittest.TestCase):
    def test_camel(self):
        self.assertEqual([naming.camel(x) for x in ("Professor Elm", "Mr. Pokémon", "Lt. Surge", "FARFETCHD", "DJ Mary")],
                         ["ProfElm", "MrPokemon", "LtSurge", "Farfetchd", "DJMary"])

    def test_movement_actions(self):
        a = naming.action
        self.assertEqual(a([("walk_in_place_up", 1)]), "FaceUp")
        self.assertEqual(a([("walk_down", 2), ("walk_in_place_left", 1), ("delay_8", 2), ("walk_left", 2)]), "WalkDownLeft")
        self.assertEqual(a([("walk_up", 1), ("set_invisible", 1)]), "Exit")
        self.assertEqual(a([("emote_exclamation_mark", 1), ("walk_in_place_fast_down", 1)]), "Exclamation")
        self.assertEqual(a([("face_down", 1), ("face_left", 1), ("face_up", 1), ("face_right", 1)]), "Spin")
        self.assertEqual(a([("WalkNormalNorth", 2)]), "WalkUp")

    def test_numbering(self):
        self.assertEqual(naming.number("M", {"a": "EventScript_Man", "b": "EventScript_Man", "c": "EventScript_Girl"},
                                       ["b", "a", "c"], set()),
                         {"b": "M_EventScript_Man1", "a": "M_EventScript_Man2", "c": "M_EventScript_Girl"})
        self.assertEqual(naming.number("M", {"a": "EventScript_Girl"}, ["a"], {"M_EventScript_Girl"}),
                         {"a": "M_EventScript_Girl1"})

    def test_all_names_are_given_and_stable(self):
        self.assertEqual(sum(len(p) for p in naming.plan_all(REPO).values()), 0)  # nothing left to rename


class Decompile(unittest.TestCase):
    def test_elif_chain(self):
        src, st = decompiled(HEAD + "\tCompare V, 1\n\tGoToIfNe _1\n\tSetFlag F1\n\tGoTo _3\n\n"
                             "_1:\n\tCompare V, 2\n\tGoToIfNe _2\n\tSetFlag F2\n\tGoTo _3\n\n"
                             "_2:\n\tSetFlag F3\n_3:\n\tEnd\n\t.balign 4, 0\n")
        self.assertIn("if (var(V) == 1) {\n        setflag(F1)\n    } elif (var(V) == 2) {\n"
                      "        setflag(F2)\n    } else {\n        setflag(F3)\n    }\n    end", src)
        self.assertEqual(st, {"structured": 1})

    def test_early_exit_and_movement(self):
        src, st = decompiled(HEAD + "\tGoToIfSet F, _1\n\tApplyMovement obj_player, _0010\n\tEnd\n\n"
                             "_1:\n\tNPCMsg M\n\tEnd\n\n\t.balign 4, 0\n_0010:\n\tWalkNormalNorth 2\n"
                             "\tFaceWest\n\tEndMovement\n\n\t.balign 4, 0\n")
        self.assertIn("if (flag(F)) {\n        npcmsg(M)\n        end\n    }\n"
                      "    applymovement(obj_player, Test_Movement_0010)", src)
        self.assertIn("movement Test_Movement_0010 {\n    walk_up * 2\n    face_left\n}", src)
        self.assertNotIn("raw", src)

    def test_shared_numbers_and_fallthrough(self):
        # two numbers for one script, a script that runs on into the next, ScrDef order != file order
        src, st = decompiled("\tScrDef B\n\tScrDef A\n\tScrDef C\n\tScrDefEnd\n\n"
                             "A:\nB:\n\tSetFlag F\nC:\n\tEnd\n\t.balign 4, 0\n")
        self.assertIn("scrdefs {\n    B\n    A\n    C\n}", src)
        self.assertIn("script A {\nB:\n    setflag(F)\nC:\n    end\n}", src)

    def test_dead_goto_is_kept(self):
        src, st = decompiled(HEAD + "\tCompare V, 1\n\tGoToIfNe _1\n\tGoTo _X\n\n_0:\n\tGoTo _2\n\n"
                             "_1:\n\tSetFlag F\n_2:\n\tEnd\n\n_X:\n\tReturn\n\t.balign 4, 0\n")
        self.assertEqual(st, {"structured": 1})


class Conversion(unittest.TestCase):
    def test_every_map_decompiles_to_the_same_commands(self):
        checked, stats = 0, {}
        for m in REPO.maps:
            e = REPO.migrated[m.name]
            if e["scripts"].startswith("@") or e["init"].startswith("@"):
                continue
            self.assertIsNotNone(REPO.pory_entry(m), m.name)
            self.assertIsNone(roundtrip(REPO, m, stats), m.name)
            checked += 1
        self.assertGreater(checked, 450)
        self.assertNotIn("raw", stats)

    def test_cherrygrove_pory_validates(self):
        m = REPO.find_map("Cherrygrove")
        self.assertIsNotNone(REPO.pory_result(m))
        from mapkit.validate import ERROR, Validator
        self.assertEqual([str(i) for i in Validator(REPO).run([m]) if i.severity == ERROR], [])


if __name__ == "__main__":
    unittest.main()
