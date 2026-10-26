# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25
"""Run: python3 tools/npctrade/test_npctrade.py"""

import copy
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import npctrade as N  # noqa: E402


class TestNpcTrade(unittest.TestCase):
    def test_retail_round_trip(self):
        # The JSON rebuilds the three game files byte for byte
        for rel, data in N.outputs(N.load_entries()).items():
            with open(N.path(rel), "rb") as f:
                self.assertEqual(f.read(), data, rel)

    def test_added_trade(self):
        entries = N.load_entries()
        new = copy.deepcopy(entries[0])
        new.update(id="NPC_TRADE_TEST", nickname="Test", ot_name="Tester", species="SPECIES_EEVEE")
        out = N.outputs(entries + [new])
        members = N.read_narc_bytes(out[N.NARC])
        self.assertEqual(len(members), len(entries) + 1)
        self.assertEqual(struct.unpack_from("<i", members[-1])[0], N.SPECIES["SPECIES_EEVEE"])
        msg = out[N.MSG].decode("utf-8")
        # nicknames first, then OT names: the new OT name is last, the new nickname at index 13
        self.assertIn('"msg_0200_00013",\n      "en_US": "Test"', msg)
        self.assertIn('"msg_0200_00027",\n      "en_US": "Tester"', msg)
        self.assertIn("    NPC_TRADE_TEST,\n    NPC_TRADE_MAX,", out[N.HEADER].decode("utf-8"))

    def test_pid_fits(self):
        species = N.SPECIES["SPECIES_EEVEE"]
        for pid in (15, 9711):
            d = N.describe({"species": species, "personality": pid, "ot_id": 0})
            self.assertEqual(d["nature"], N.NATURES[pid % 25])


if __name__ == "__main__":
    unittest.main()
