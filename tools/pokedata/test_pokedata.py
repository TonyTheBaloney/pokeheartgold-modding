# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Run: python3 tools/pokedata/test_pokedata.py"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import pokedata as P  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
INCLUDE = os.path.join(ROOT, "include")
LEARNSETS = os.path.join(ROOT, "files/poketool/personal/level_up_learnsets.json")
EGG_MOVES = os.path.join(ROOT, "files/poketool/personal/egg_moves.json")
C = P.Constants(INCLUDE)

# sha1 of the retail archives' members, concatenated
RETAIL_WOTBL = "5a1b6074d217f41bfaab1c7015a4f4b3372838f4"
RETAIL_KOWAZA_LIST = "2df809628d8104903c359981dddd638fb286062b"


def sha1(members):
    return hashlib.sha1(b"".join(members)).hexdigest()


class Retail(unittest.TestCase):
    def test_learnsets_build_the_retail_archive(self):
        members = P.build_learnsets(LEARNSETS, C)
        self.assertEqual(len(members), 508)
        self.assertEqual(sha1(members), RETAIL_WOTBL)

    def test_egg_moves_build_the_retail_archive(self):
        self.assertEqual(sha1(P.build_egg_moves(EGG_MOVES, C)), RETAIL_KOWAZA_LIST)

    def test_member_format(self):
        # Bulbasaur: Tackle at 1, Growl at 3, ... 0xFFFF, padded to 4 bytes
        m = P.build_learnsets(LEARNSETS, C)[C.species["SPECIES_BULBASAUR"]]
        self.assertEqual(m[:4], bytes.fromhex("21022d06"))
        self.assertEqual(len(m) % 4, 0)


class Errors(unittest.TestCase):
    def build(self, fn, doc):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(doc if isinstance(doc, str) else json.dumps(doc))
        try:
            fn(f.name, C)
        finally:
            os.unlink(f.name)

    def assertFails(self, fn, doc, msg):
        with self.assertRaises(P.DataError) as cm:
            self.build(fn, doc)
        self.assertIn(msg, str(cm.exception))

    def test_learnset_errors(self):
        ok = {"level": 1, "move": "MOVE_TACKLE"}
        self.assertFails(P.build_learnsets, {"SPECIES_NOPE": []}, "unknown species")
        self.assertFails(P.build_learnsets, {"SPECIES_BULBASAUR": [{"level": 1, "move": "MOVE_NOPE"}]}, "unknown move")
        self.assertFails(P.build_learnsets, {"SPECIES_BULBASAUR": [{"level": 101, "move": "MOVE_TACKLE"}]}, "not 1-100")
        self.assertFails(P.build_learnsets, {"SPECIES_BULBASAUR": [ok] * 22}, "at most 21")
        self.assertFails(P.build_learnsets, {"SPECIES_BULBASAUR": [{"lvl": 1}]}, "expected")
        self.assertFails(P.build_learnsets, '{"SPECIES_BULBASAUR": [], "SPECIES_BULBASAUR": []}', "appears twice")
        self.build(P.build_learnsets, {"SPECIES_BULBASAUR": [ok] * 21})

    def test_egg_move_errors(self):
        self.assertFails(P.build_egg_moves, {"SPECIES_BULBASAUR": ["MOVE_TACKLE"] * 17}, "at most 16")
        self.assertFails(P.build_egg_moves, {"SPECIES_BULBASAUR": ["MOVE_NOPE"]}, "unknown move")
        full = {name: ["MOVE_TACKLE"] * 9 for name in list(C.species)[1:300]}
        self.assertFails(P.build_egg_moves, full, "only searches the first 2045")


if __name__ == "__main__":
    unittest.main()
