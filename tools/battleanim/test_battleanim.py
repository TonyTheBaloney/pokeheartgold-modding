# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26
"""Run: python3 tools/battleanim/test_battleanim.py

The round trip compares data/battle_anims with the retail archives, so like `make`'s
checksums it fails once you change a script."""

import hashlib
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import battleanim as B  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
MOVES = os.path.join(ROOT, "data", "battle_anims", "moves")
EFFECTS = os.path.join(ROOT, "data", "battle_anims", "effects")
# SHA-1 of the retail archives (the prebuilt files/a/0/1/0 and files/a/0/6/1 they replaced)
SHA1 = {MOVES: "6aca26a5b2acbb8174bfcbfe870c84e879e22a8d", EFFECTS: "5cdcc9ae6349056f5437f6ebeabffd0ed0f89626"}


class RoundTrip(unittest.TestCase):
    def check_archive(self, src, effects):
        names = B.Names(effects)
        built = B.build(src, names)
        self.assertEqual(hashlib.sha1(built).hexdigest(), SHA1[src])
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "archive")
            with open(path, "wb") as f:
                f.write(built)
            members = B.read_narc(path)
            self.assertEqual(B.write_narc(members), built)
            B.export(members, os.path.join(d, "again"), names)
            for i, m in enumerate(members):
                self.assertNotIn("not decoded", B.disassemble(m, names), "member %d" % i)
            self.assertEqual(B.build(os.path.join(d, "again"), names), built)

    def test_moves(self):
        self.check_archive(MOVES, False)

    def test_effects(self):
        self.check_archive(EFFECTS, True)


class Assembler(unittest.TestCase):
    names = B.Names()

    def test_names_and_varargs(self):
        w = B.assemble("CallFunc ShakeTargets, 1, 0, 1, 2, 264\nCreateEmitter 0, 1, SetPositionAtDefender\n"
                       "EmitterData 0, 2, 2, 0, 0, 0\nPlaySEWithPan SEQ_SE_DP_030, -117\nEnd\n", self.names)
        self.assertEqual(w, [45, 36, 5, 1, 0, 1, 2, 264, 46, 0, 1, 4, 55, 6, 0, 2, 2, 0, 0, 0,
                             22, 1827, 0xFFFFFF8B, 4])

    def test_labels_are_relative_to_their_word(self):
        w = B.assemble("JumpBySide 0, a, b\nEnd\na:\nWait 1\nb:\nEnd\n", self.names)
        # offsets sit at words 2 and 3; a = word 5, b = word 7
        self.assertEqual(w, [64, 0, 3, 4, 4, 0, 1, 4])
        self.assertIn("L5:", B.disassemble(struct.pack("<8I", *w), self.names))

    def test_errors(self):
        for text in ("Jump nowhere\n", "Wait\n", "Wait 1, 2\n", "Frobnicate 1\n", "Wait x\n"):
            with self.assertRaises(ValueError, msg=text):
                B.assemble(text, self.names)

    def test_spare_moves_play_nothing(self):
        with open(os.path.join(MOVES, "0468_468.anim"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("CallFunc None", text)
        self.assertNotIn("Emitter", text)

    def test_gaps_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ("0000_A.anim", "0002_C.anim"):
                with open(os.path.join(d, n), "w") as f:
                    f.write("End\n")
            with self.assertRaises(ValueError):
                B.build(d, self.names)


if __name__ == "__main__":
    unittest.main()
