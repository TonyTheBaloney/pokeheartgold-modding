# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""The gen4map format checker (docs/gen4map/FORMAT.md)."""

import copy
import json
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import formats  # noqa: E402


class ProjectConforms(unittest.TestCase):
    def test_whole_project(self):
        counts, problems = formats.check(ROOT)
        self.assertEqual([str(p) for p in problems], [])
        self.assertEqual(counts, {"layouts": 288, "land data cells": 676, "maps": 540})


class Schemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.map_schema = formats.load_schema(ROOT, "map")
        cls.layout_schema = formats.load_schema(ROOT, "layout")
        with open(os.path.join(ROOT, "data/maps/Cherrygrove/map.json"), encoding="utf-8") as f:
            cls.cherrygrove = json.load(f)

    def errors(self, doc, schema=None):
        return formats.validate(doc, schema or self.map_schema)

    def test_good_map(self):
        self.assertEqual(self.errors(self.cherrygrove), [])

    def test_map_mistakes(self):
        def changed(fn):
            d = copy.deepcopy(self.cherrygrove)
            fn(d)
            return [m for _, m in self.errors(d)]
        self.assertIn("unknown key 'colour'", changed(lambda d: d.update(colour=1)))
        self.assertIn("missing 'weather'", changed(lambda d: d.pop("weather")))
        self.assertTrue(any("above 127" in m for m in changed(lambda d: d.update(weather=200))))
        self.assertTrue(any("expected boolean" in m for m in changed(lambda d: d.update(allow_fly=1))))
        self.assertTrue(any("does not match" in m for m in changed(
            lambda d: d["object_events"][0].update(graphics_id="SPRITE GSBOY"))))
        self.assertTrue(any("above 65535" in m for m in changed(lambda d: d["warp_events"][0].update(x=70000))))
        # scripts: labels, std_* constants, one-argument macros and numbers are all fine
        for script in ("Cherrygrove_EventScript_GuideGent", "std_colosseum_exit", "std_trainer(TRAINER_X)", 7):
            self.assertEqual(changed(lambda d: d["object_events"][0].update(script=script)), [])

    def test_layout_grid(self):
        good = {"name": "x", "width": 2, "height": 1, "land_data": [[1, None]]}
        self.assertEqual(formats.validate(good, self.layout_schema), [])
        bad = dict(good, land_data=[[1, "a"]])
        self.assertTrue(formats.validate(bad, self.layout_schema))

    def test_manifest_version(self):
        with open(os.path.join(ROOT, formats.MANIFEST), encoding="utf-8") as f:
            m = json.load(f)
        self.assertEqual(m["format"], "gen4map")
        self.assertTrue(m["version"].startswith("1."))
        self.assertEqual(formats.validate(m, formats.load_schema(ROOT, "manifest")), [])


if __name__ == "__main__":
    unittest.main()
