# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Terrain export to OBJ and import back (terrain.py)."""

import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))
sys.path.insert(0, os.path.dirname(__file__))

from mapkit import bdhc, nitro, terrain  # noqa: E402
from test_nsbmd import same_polygons  # noqa: E402

FX = bdhc.FX


class RoundTrip(unittest.TestCase):
    def test_export_then_import_changes_nothing(self):
        for cell in (4, 138, 383, 600):
            with tempfile.TemporaryDirectory() as tmp:
                terrain.export(ROOT, cell, tmp)
                for name in ("model.obj", "model.mtl", "terrain.json"):
                    self.assertTrue(os.path.exists(os.path.join(tmp, name)))
                s = terrain.import_obj(ROOT, cell, os.path.join(tmp, "model.obj"), dry_run=True)
            d = terrain.cell_dir(ROOT, cell)
            with open(os.path.join(d, "model.nsbmd"), "rb") as f:
                (m1,), _ = nitro.load_nsbmd(f.read())
            (m2,), _ = nitro.load_nsbmd(s["model_data"])
            self.assertIsNone(same_polygons(m1.polygons(), m2.polygons()), cell)
            h1, h2 = terrain._load_heights(d), s["heights_data"]
            for z in range(-252, 256, 8):
                for x in range(-252, 256, 8):
                    a = h1.height(x * FX, z * FX)
                    b = h2.height(x * FX, z * FX, bdhc.NEAREST, a or 0)
                    self.assertEqual(a is None, b is None, (cell, x, z))
                    if a is not None:
                        self.assertLessEqual(abs(a - b), 8, (cell, x, z))

    def test_new_model_from_obj_alone(self):
        """An OBJ with no terrain.json: materials come from the texture file names."""
        with tempfile.TemporaryDirectory() as tmp:
            terrain.export(ROOT, 4, os.path.join(tmp, "ref"))
            os.makedirs(os.path.join(tmp, "new", "textures"))
            shutil.copy(os.path.join(tmp, "ref", "textures", "grass01gs-grass01.png"),
                        os.path.join(tmp, "new", "textures"))
            lines = ["mtllib model.mtl", "o terrain", "usemtl grass",
                     "v -256 0 256", "v 256 0 256", "v 256 0 -256", "v -256 0 -256",
                     "v 0 32 0", "v 64 32 0", "v 64 32 -64", "v 0 32 -64",
                     "vt 0 0", "vt 16 0", "vt 16 16", "vt 0 16", "vt 0 0", "vt 2 0", "vt 2 2", "vt 0 2",
                     "f 1/1 2/2 3/3 4/4", "f 5/5 6/6 7/7 8/8"]
            with open(os.path.join(tmp, "new", "model.obj"), "w") as f:
                f.write("\n".join(lines) + "\n")
            with open(os.path.join(tmp, "new", "model.mtl"), "w") as f:
                f.write("newmtl grass\nmap_Kd textures/grass01gs-grass01.png\n")
            s = terrain.import_obj(ROOT, 4, os.path.join(tmp, "new", "model.obj"), dry_run=True)
        (m,), _ = nitro.load_nsbmd(s["model_data"])
        self.assertEqual([(x.name, x.texture, x.palette) for x in m.materials], [("grass", "grass01gs", "grass01")])
        self.assertFalse(m.materials[0].poly_attr & 1)   # no normals in the OBJ: unlit, white vertex color
        self.assertEqual(len(m.polygons()), 2)
        h = s["heights_data"]
        self.assertEqual(h.height(-100 * FX, 100 * FX), 0)
        self.assertEqual(h.height(32 * FX, -32 * FX, bdhc.NEAREST, 30 * FX), 32 * FX)

    def test_check_retail_cells(self):
        for cell in (0, 4, 383):
            self.assertEqual(terrain.check(ROOT, cell), [])


if __name__ == "__main__":
    unittest.main()
