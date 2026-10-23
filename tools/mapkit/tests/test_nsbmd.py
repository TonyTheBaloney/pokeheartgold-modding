# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""NSBMD reading and writing (nsbmd.py) against the game's terrain models."""

import collections
import glob
import os
import random
import struct
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import nitro, nsbmd  # noqa: E402

MODELS = sorted(glob.glob(os.path.join(ROOT, "data/landdata/*/model.nsbmd")))


def nns_lookup(d, base, name):
    """NNS_G3dGetResDictIdxByName (res_struct_accessor.c), tree branch included."""
    num = d[base + 1]
    hdr = base + struct.unpack_from("<H", d, base + 6)[0]
    ofs_name = struct.unpack_from("<H", d, hdr + 2)[0]
    key = nsbmd._name16(name)
    vals = struct.unpack("<4I", key)
    names = [d[hdr + ofs_name + 16 * i:hdr + ofs_name + 16 * (i + 1)] for i in range(num)]
    if num < 16:
        return next((i for i, n in enumerate(names) if n == key), -1)
    node = lambda i: d[base + 8 + 4 * i:base + 12 + 4 * i]  # noqa: E731 refBit, left, right, entry
    p = node(0)
    if p[1] == 0:
        return -1
    x = node(p[1])
    while p[0] > x[0]:
        p = x
        bit = (vals[x[0] >> 5] >> (x[0] & 31)) & 1
        x = node(x[1 + bit])
    return x[3] if names[x[3]] == key else -1


def material_of(mt):
    c5 = lambda v: (v & 31, (v >> 5) & 31, (v >> 10) & 31)  # noqa: E731
    cull = {2: "back", 1: "front", 3: "none", 0: "none"}[(mt.poly_attr >> 6) & 3]
    return nsbmd.TerrainMaterial(mt.name, mt.texture, mt.palette, (mt.orig_w, mt.orig_h), bool(mt.poly_attr & 0xF),
                                 mt.alpha, cull, bool(mt.poly_attr & 0x8000), mt.repeat, mt.flip,
                                 c5(mt.diff_amb), c5(mt.diff_amb >> 16))


def same_polygons(p1, p2):
    """Same polygons (any starting vertex), within the precision the display list stores.
    Colors of lit vertices are not compared: build_terrain sends NORMAL for them."""
    def close(p, q, r):
        n = len(p.pos)
        for k in range(n):
            j = (k + r) % n
            if any(abs(a - b) > 0.02 for a, b in zip(p.pos[k], q.pos[j])):
                return False
            if any(abs(a - b) > 1 / 16 + 1e-9 for a, b in zip(p.uv[k], q.uv[j])):
                return False
            if (p.normal[k] is None) != (q.normal[j] is None):
                return False
            if p.normal[k] and any(abs(a - b) > 1 / 512 + 1e-9 for a, b in zip(p.normal[k], q.normal[j])):
                return False
            if not p.material.poly_attr & 0xF and any(abs(a - b) > 9 for a, b in zip(p.color[k], q.color[j])):
                return False
        return True
    if len(p1) != len(p2):
        return "polygon count %d vs %d" % (len(p1), len(p2))
    buckets = collections.defaultdict(list)
    key = lambda p: (p.material.name, len(p.pos), round(sum(c for v in p.pos for c in v)))  # noqa: E731
    for q in p2:
        buckets[key(q)].append(q)
    for p in p1:
        k = key(p)
        for kk in (k, (k[0], k[1], k[2] - 1), (k[0], k[1], k[2] + 1)):
            hit = next((q for q in buckets[kk] if any(close(p, q, r) for r in range(len(p.pos)))), None)
            if hit:
                buckets[kk].remove(hit)
                break
        else:
            return "no match for %s %s" % (p.material.name, p.pos)
    return None


class ReadWrite(unittest.TestCase):
    def test_every_terrain_model_rebuilds_byte_for_byte(self):
        self.assertEqual(len(MODELS), 676)
        for p in MODELS:
            with open(p, "rb") as f:
                d = f.read()
            self.assertEqual(nsbmd.write(nsbmd.read(d)), d, p)

    def test_dictionary_trees_find_every_name(self):
        rng = random.Random(4)
        for n in (1, 2, 15, 16, 17, 40, 200):
            names = ["".join(rng.choice("abcdefghij_0123") for _ in range(rng.randint(1, 16))) for _ in range(n)]
            names = list(dict.fromkeys(names))
            d = nsbmd.dict_bytes(names, [struct.pack("<I", i) for i in range(len(names))])
            for i, nm in enumerate(names):
                self.assertEqual(nns_lookup(d, 0, nm), i)
            self.assertEqual(nns_lookup(d, 0, "not_there"), -1)


class BuildTerrain(unittest.TestCase):
    def test_retail_geometry_rebuilds(self):
        sizes = []
        for p in MODELS[::15]:
            with open(p, "rb") as f:
                d = f.read()
            (m,), _ = nitro.load_nsbmd(d)
            index = {id(x): i for i, x in enumerate(m.materials)}
            polys = [(index[id(q.material)], list(zip(q.pos, q.uv, q.normal, q.color))) for q in m.polygons()]
            out = nsbmd.build_terrain(m.name, [material_of(x) for x in m.materials], polys)
            self.assertLessEqual(len(out), nsbmd.MAX_MODEL_SIZE)
            (m2,), own = nitro.load_nsbmd(out)
            self.assertIsNone(own)
            self.assertIsNone(same_polygons(m.polygons(), m2.polygons()), p)
            sizes.append(len(out) / len(d))
        self.assertLess(sum(sizes) / len(sizes), 1.0)   # strips: no bigger than the converter's on average

    def test_structure_matches_retail(self):
        mat = nsbmd.TerrainMaterial("grass", "grass01gs", "grass01", (32, 32))
        quad = [((x, 0.0, z), (u, v), (0.0, 1.0, 0.0), None)
                for (x, z, u, v) in ((-8, 8, 0, 32), (8, 8, 32, 32), (8, -8, 32, 0), (-8, -8, 0, 0))]
        (m,) = nsbmd.read(nsbmd.build_terrain("test", [mat], [(0, quad)]))
        self.assertEqual(m.sbc[:9], b"\x26\x00\x00\x00\x00\x02\x00\x01\x0b")
        self.assertEqual(m.nodes[0][1], b"\x07\xf8\x00\x10")
        self.assertEqual(m.tex_map, [("grass01gs", [0], 0)])
        self.assertEqual(m.pltt_map, [("grass01", [0], 0)])
        self.assertEqual(m.shapes[0].flag, 5)   # NORMAL | TEXCOORD, like the retail lit shapes

    def test_too_big(self):
        mat = nsbmd.TerrainMaterial("m", lit=False)
        rng = random.Random(1)
        tris = [(0, [((rng.uniform(-250, 250), rng.uniform(0, 100), rng.uniform(-250, 250)), None, None,
                      (rng.randrange(256),) * 3) for _ in range(3)]) for _ in range(6000)]
        with self.assertRaises(nitro.NitroError):
            nsbmd.build_terrain("big", [mat], tris)


if __name__ == "__main__":
    unittest.main()
