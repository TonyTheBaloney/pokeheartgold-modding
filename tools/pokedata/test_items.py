# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Run: python3 tools/pokedata/test_items.py"""

import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import items as I  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
INCLUDE = os.path.join(ROOT, "include")
ITEMS = os.path.join(ROOT, "data/items/items.json")

# sha1 of the generated files that build the retail ROM (both versions pass `meson test` with them)
RETAIL = {
    "item_data.csv": "9cd83572181068ed53b050adccddf05446679e8c",
    "msg_0222.json": "578e4e7c1117ace485948c66e486d6cfbe9e2f8b",
    "msg_0221.json": "8ef683dcb85e3cdcd657fbbe24c71fb7de87ed66",
    "item_narc_ids.h": "a1935b7ad55b8cefefc2680810880cec772188b8",
}


def build(doc=None, include=INCLUDE):
    tmp = tempfile.mkdtemp()
    src = ITEMS
    if doc is not None:
        src = os.path.join(tmp, "items.json")
        with open(src, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
    I.build(src, os.path.join(tmp, "out"), include)
    return tmp


class Retail(unittest.TestCase):
    def test_outputs_are_the_retail_ones(self):
        tmp = build()
        try:
            for fn, h in RETAIL.items():
                with open(os.path.join(tmp, "out", fn), "rb") as f:
                    self.assertEqual(hashlib.sha1(f.read()).hexdigest(), h, fn)
        finally:
            shutil.rmtree(tmp)

    def test_known_items(self):
        c = I.Constants(INCLUDE)
        items = dict(I.resolve(I.load(ITEMS), c))
        self.assertEqual(len(items), c.count)
        p = items["ITEM_POTION"]
        self.assertEqual((p["name"], p["price"], p["hp_restore_param"]), ("Potion", 300, 20))
        self.assertEqual(p["fieldUseFunc"], c.field_use["ITEM_FIELD_USE_HEALING"])
        self.assertTrue(items["ITEM_UNUSED_113"]["noData"])
        # Timer Ball is ball 9: the index byte is the first 8 party flags (1 + 8)
        t = items["ITEM_TIMER_BALL"]
        self.assertEqual((t["partyUse"], t["slp_heal"], t["frz_heal"], t["psn_heal"]), (0, 1, 1, 0))
        records, index = I.data_records(list(I.resolve(I.load(ITEMS), c)))
        self.assertEqual(len(records), 514)
        self.assertEqual(index["ITEM_EXPLORER_KIT"], 0)


class Mistakes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = I.Constants(INCLUDE)
        cls.doc = I.load(ITEMS)

    def fails(self, change, text):
        d = copy.deepcopy(self.doc)
        change(d)
        with self.assertRaises(I.ItemError) as e:
            I.resolve(d, self.c)
        self.assertIn(text, str(e.exception))

    def test_errors(self):
        self.fails(lambda d: d["ITEM_POTION"].update(price=70000), "price must be")
        self.fails(lambda d: d["ITEM_POTION"].update(colour="red"), "unknown key")
        self.fails(lambda d: d["ITEM_POTION"].update(fieldPocket="POCKET_SNACKS"), "not a known constant")
        self.fails(lambda d: d["ITEM_POTION"].update(battlePocket="BTLPOCKET_BALLS_F"), "must be a list")
        self.fails(lambda d: d["ITEM_POTION"]["partyUseParam"].update(hp_restore_param=300), "must be 0-255")
        self.fails(lambda d: d["ITEM_POTION"]["partyUseParam"].update(heal_everything=True), "unknown key")
        self.fails(lambda d: d["ITEM_UNUSED_113"].update(price=5), "noData")
        self.fails(lambda d: d["ITEM_POTION"].pop("icon"), "icon is required")
        self.fails(lambda d: d["ITEM_TIMER_BALL"].update(partyUseParam={"slp_heal": True}), "needs \"partyUse\": true")
        self.fails(lambda d: d["ITEM_POTION"].update(partyUseIndex=3), "only for items without party use")
        self.fails(lambda d: d["ITEM_TIMER_BALL"].update(partyUseIndex=300), "0-255")

        def swap(d):
            keys = list(d)
            keys[1], keys[2] = keys[2], keys[1]
            d2 = {k: d[k] for k in keys}
            d.clear()
            d.update(d2)
        self.fails(swap, "id order")

    def test_names_are_checked(self):
        d = copy.deepcopy(self.doc)
        d["ITEM_POTION"]["name"] = "Extraordinary Potion"
        self.assertTrue(any("ITEM_POTION" in w for w in I.check(I.resolve(d, self.c), self.c)))


class NewItem(unittest.TestCase):
    def test_add_an_item(self):
        tmp = tempfile.mkdtemp()
        try:
            inc = os.path.join(tmp, "include")
            shutil.copytree(INCLUDE, inc, ignore=shutil.ignore_patterns("*.c"))
            h = os.path.join(inc, "constants", "items.h")
            with open(h, encoding="utf-8") as f:
                text = f.read()
            text = text.replace("#define ITEM_ENIGMA_STONE 536\n", "#define ITEM_ENIGMA_STONE 536\n#define ITEM_TEST_GEM     537\n")
            text = text.replace("#define ITEMS_COUNT       537", "#define ITEMS_COUNT       538")
            with open(h, "w", encoding="utf-8") as f:
                f.write(text)
            c = I.Constants(inc)
            doc = I.load(ITEMS)
            with self.assertRaises(I.ItemError):     # the new constant has no entry yet
                I.resolve(doc, c)
            doc["ITEM_TEST_GEM"] = dict(doc["ITEM_SILK_SCARF"], name="Test Gem", description="A test.",
                                        gen3="AGB_ITEM_NONE")
            out = build(doc, inc)
            with open(os.path.join(out, "out", "msg_0222.json"), encoding="utf-8") as f:
                names = json.load(f)["messages"]
            self.assertEqual(names[537], {"id": "msg_0222_00537", "en_US": "Test Gem"})
            with open(os.path.join(out, "out", "item_data.csv"), encoding="utf-8") as f:
                self.assertEqual(len(f.read().splitlines()), 1 + 515)
            with open(os.path.join(out, "out", "item_narc_ids.h"), encoding="utf-8") as f:
                self.assertIn("[ITEM_TEST_GEM] = { NARC_item_data_0514_bin", f.read())
            shutil.rmtree(out)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
