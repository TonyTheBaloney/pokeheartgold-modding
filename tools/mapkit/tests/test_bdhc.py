# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""BDHC heights (bdhc.py) against the game's files and code."""

import glob
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import bdhc, landdata, nitro  # noqa: E402

FILES = sorted(glob.glob(os.path.join(ROOT, "data/landdata/*/terrain.bdhc")))
FX = bdhc.FX


def load(p):
    with open(p, "rb") as f:
        return f.read()


class Retail(unittest.TestCase):
    def test_round_trip_and_layout_rules(self):
        self.assertEqual(len(FILES), 676)
        exact = 0
        for p in FILES:
            d = load(p)
            b = bdhc.Bdhc.from_bytes(d)
            self.assertEqual(b.to_bytes(), d, p)
            plates = b.resolved_plates()
            # strips and pools follow from the plates (with the pool slots as stored)
            self.assertEqual(bdhc.build(plates, [q[2] for q in b.plates], [q[3] for q in b.plates]).to_bytes(), d, p)
            exact += bdhc.build(plates).to_bytes() == d
        self.assertEqual(exact, 624)   # the other 52 repeat a normal or constant in their pools

    def test_json_keeps_every_height(self):
        for p in FILES[::5]:
            b = bdhc.Bdhc.from_bytes(load(p))
            j = bdhc.from_json(bdhc.to_json(b))
            for z in range(-256, 257, 16):
                for x in range(-256, 257, 16):
                    for mode in (bdhc.NEAREST, bdhc.HIGHEST, bdhc.LOWEST):
                        self.assertEqual(b.height(x * FX, z * FX, mode), j.height(x * FX, z * FX, mode), (p, x, z))

    def test_find_strip_is_the_strip_containing_z(self):
        for p in FILES[::7]:
            b = bdhc.Bdhc.from_bytes(load(p))
            if len(b.strips) < 2:
                continue
            bounds = [s[0] for s in b.strips]
            for z in range(-256 * FX, 256 * FX + 1, 4 * FX):
                expect = next((i for i, ub in enumerate(bounds) if z <= ub), len(bounds) - 1)
                got = b.find_strip(z)
                # the game's search lands on the first strip whose upper bound is >= z
                self.assertTrue(got == expect or bounds[got] == z or (got and bounds[got - 1] == z), (p, z, got, expect))

    def test_check_finds_the_vertical_plate(self):
        problems = {os.path.basename(os.path.dirname(p)): bdhc.check(bdhc.Bdhc.from_bytes(load(p))) for p in FILES}
        self.assertEqual({k for k, v in problems.items() if v}, {"0464"})


class Arithmetic(unittest.TestCase):
    def test_fx(self):
        self.assertEqual(bdhc.fx_mul(FX, FX), FX)
        self.assertEqual(bdhc.fx_mul(3 * FX // 2, -2 * FX), -3 * FX)
        self.assertEqual(bdhc.fx_div(FX, 2 * FX), FX // 2)
        self.assertEqual(bdhc.fx_div(-3 * FX, 2 * FX), -3 * FX // 2)
        self.assertEqual(bdhc.fx_div(-16 * FX, FX), -16 * FX)

    def test_flat_and_ramp(self):
        doc = {"plates": [{"x": [-256, 256], "z": [-256, 0], "y": 16},
                          {"x": [-256, 256], "z": [0, 64], "ramp": {"along": "z", "y": [16, 48]}}]}
        b = bdhc.from_json(doc)
        self.assertEqual(b.height(0, -100 * FX), 16 * FX)
        for z, y in ((0, 16), (32, 32), (64, 48)):
            self.assertAlmostEqual(b.height(5 * FX, z * FX, bdhc.NEAREST, y * FX) / FX, y, delta=0.01)
        self.assertIsNone(b.height(0, 100 * FX))

    def test_bad_json(self):
        for doc in ({"plates": [{"x": [0, 16], "z": [0, 16]}]},
                    {"plates": [{"x": [16, 0], "z": [0, 16], "y": 0}]},
                    {"plates": [{"x": [0, 16], "z": [0, 16], "y": 0.1}]},
                    {"plates": [{"x": [0, 16], "z": [0, 16], "y": 0, "d": 1}]}):
            with self.assertRaises(bdhc.BdhcError):
                bdhc.from_json(doc)


class Generate(unittest.TestCase):
    def test_plateau_and_ramp(self):
        tris = []

        def quad(a, b, c, d):
            tris.extend([(a, b, c), (a, c, d)])
        quad((-256, 0, -256), (256, 0, -256), (256, 0, 256), (-256, 0, 256))          # ground
        quad((0, 32, -128), (128, 32, -128), (128, 32, 0), (0, 32, 0))                # plateau
        quad((-64, 0, -128), (0, 32, -128), (0, 32, -96), (-64, 0, -96))              # ramp up to it
        quad((0, 0, 0), (128, 0, 0), (128, 32, 0), (0, 32, 0))                        # a wall: not a height
        b = bdhc.build(bdhc.generate(tris))
        self.assertEqual(bdhc.check(b), [])
        h = lambda x, z, cur=0: b.height(x * FX, z * FX, bdhc.NEAREST, cur * FX) / FX  # noqa: E731
        self.assertEqual(h(-200, 200), 0)
        self.assertEqual(h(64, -64, 32), 32)
        self.assertEqual(h(64, -64, 0), 0)     # under the plateau too: the nearest height wins
        self.assertAlmostEqual(h(-32, -112, 16), 16, delta=0.01)

    def test_model_surface(self):
        """Generated heights are the model's own surface wherever one is under a tile centre."""
        for cell in ("0004", "0138", "0383"):
            d = os.path.join(ROOT, "data/landdata", cell)
            (m,), _ = nitro.load_nsbmd(load(os.path.join(d, "model.nsbmd")))
            tris = [t.pos for t in m.triangles()]
            b = bdhc.build(bdhc.generate(tris))
            for tz in range(32):
                for tx in range(32):
                    x, z = tx * 16 - 248, tz * 16 - 248
                    ys = []
                    for t in tris:
                        pl = bdhc._plane(t)
                        if pl and pl[0][1] >= 0.5 and bdhc._inside(x, z, t):
                            (nx, ny, nz), dd = pl
                            ys.append(-(dd + nx * x + nz * z) / ny)
                    for y in ys:
                        got = b.height(x * FX, z * FX, bdhc.NEAREST, int(y * FX))
                        self.assertIsNotNone(got, (cell, tx, tz))
                        self.assertAlmostEqual(got / FX, y, delta=0.3, msg=(cell, tx, tz))


class LandData(unittest.TestCase):
    def test_heights_json_builds_the_same_member(self):
        import shutil
        import tempfile
        src = os.path.join(ROOT, "data/landdata/0001")
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "0001")
            shutil.copytree(src, d)
            before = landdata.build(d)
            b = bdhc.Bdhc.from_bytes(load(os.path.join(d, "terrain.bdhc")))
            bdhc.write_json(os.path.join(d, "heights.json"), b)
            with self.assertRaises(landdata.LandDataError):   # both: ambiguous
                landdata.build(d)
            os.remove(os.path.join(d, "terrain.bdhc"))
            self.assertEqual(landdata.build(d), before)


if __name__ == "__main__":
    unittest.main()
