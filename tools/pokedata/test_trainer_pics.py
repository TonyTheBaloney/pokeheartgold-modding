# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Run: python3 tools/pokedata/test_trainer_pics.py   (after a build, which makes nitrogfx and nitroarc)"""

import copy
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.dirname(__file__))
import trainer_pics as T  # noqa: E402
from pokedata import DataError, narc_members  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
INCLUDE = os.path.join(ROOT, "include")
GRAPHICS = os.path.join(ROOT, "graphics/trainers")
TABLES = {k: os.path.join(ROOT, "data/trainer_graphics/%s_pics.json" % k) for k in ("front", "back")}
TOOLS = os.path.join(ROOT, "build/heartgold.us/tools")
NITROGFX, NITROARC = os.path.join(TOOLS, "nitrogfx/nitrogfx"), os.path.join(TOOLS, "nitroarc/nitroarc")

# sha1 of the retail files/a/0/5/8 and files/a/0/0/6
RETAIL = {"front": "8c2d084a49e190b19f9111c944f88bf341bd930e", "back": "bfc7fd85c7255b8502d54722ea14b3c7ffd85a6e"}


def have_tools():
    return os.path.exists(NITROGFX) and os.path.exists(NITROARC)


class Sandbox:
    """A copy of the tables, graphics and include/ to change."""

    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        self.graphics = os.path.join(self.dir, "graphics")
        shutil.copytree(GRAPHICS, self.graphics)
        self.include = os.path.join(self.dir, "include")
        os.makedirs(os.path.join(self.include, "constants"))
        shutil.copy(os.path.join(INCLUDE, "constants/trainer_class.h"), os.path.join(self.include, "constants"))
        self.docs = {k: json.load(open(p, encoding="utf-8")) for k, p in TABLES.items()}
        return self

    def __exit__(self, *a):
        shutil.rmtree(self.dir)

    def table(self, kind):
        p = os.path.join(self.dir, kind + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.docs[kind], f)
        return p

    def build(self, kind):
        out = os.path.join(self.dir, kind + ".narc")
        T.build(kind, self.table(kind), out, self.graphics, self.include, NITROGFX, NITROARC, self.dir)
        return out

    def check(self, kind):
        return T.check(kind, self.table(kind), self.graphics, self.include)


@unittest.skipUnless(have_tools(), "build first (make) for nitrogfx and nitroarc")
class Retail(unittest.TestCase):
    def test_archives_are_the_retail_ones(self):
        with Sandbox() as s:
            for kind, h in RETAIL.items():
                with open(s.build(kind), "rb") as f:
                    self.assertEqual(hashlib.sha1(f.read()).hexdigest(), h, kind)

    def test_a_changed_pixel_reaches_the_archive(self):
        with Sandbox() as s:
            png = os.path.join(s.graphics, "front_pics/youngster.png")
            w, h, rows = T.read_png(png)
            rows[40][40] = 5
            T.write_png(png, rows, T.read_pal(os.path.join(s.graphics, "palettes/youngster.pal")))
            m = narc_members(s.build("front"))
            img = T.decode_frame(m[2 * 5][0x30:], T.frame_objs(T.LAYOUTS["80x80"]))
            self.assertEqual(img[40][40], 5)
            flat, _ = T.unflat(m[2 * 5 + 4][0x30:])
            self.assertEqual(flat[40][40], 5)


class Tables(unittest.TestCase):
    def test_retail_tables(self):
        front, _ = T.load_table("front", TABLES["front"], INCLUDE)
        back, _ = T.load_table("back", TABLES["back"], INCLUDE)
        self.assertEqual((len(front), len(back)), (129, 17))
        falkner = front[66]
        self.assertEqual((falkner["name"], len(falkner["seqs"])), ("TRAINERCLASS_LEADER_FALKNER", 3))
        self.assertIn(1, [f["attr"] for f in falkner["seqs"][1]["frames"]])   # the flash
        self.assertEqual(T.check("front", TABLES["front"], GRAPHICS, INCLUDE), 129)

    def test_png_filters(self):
        # editors save PNGs with any row filter; check each against the unfiltered rows
        rows = [[(x * 3 + y * 5) % 16 for x in range(80)] for y in range(4)]
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, "a.png")
            T.write_png(p, rows, [(i, i, i) for i in range(16)])
            for ftype in range(5):
                raw, prev = bytearray(), bytearray(40)
                for r in rows:
                    line = bytes(r[x] << 4 | r[x + 1] for x in range(0, 80, 2))
                    out = bytearray()
                    for i, v in enumerate(line):
                        a = line[i - 1] if i else 0
                        b, c = prev[i], prev[i - 1] if i else 0
                        pr = [0, a, b, (a + b) // 2,
                              min((a, b, c), key=lambda q: (abs(a + b - c - q), (a, b, c).index(q)))][ftype]
                        out.append((v - pr) & 0xFF)
                    raw += bytes([ftype]) + out
                    prev = bytearray(line)
                with open(p, "rb") as f:
                    d = f.read()
                i = d.index(b"IDAT") - 4
                n = struct.unpack(">I", d[i:i + 4])[0]
                body = zlib.compress(bytes(raw))
                idat = struct.pack(">I", len(body)) + b"IDAT" + body + struct.pack(">I", zlib.crc32(b"IDAT" + body))
                with open(p + "2", "wb") as f:
                    f.write(d[:i] + idat + d[i + 12 + n:])
                self.assertEqual(T.read_png(p + "2")[2], rows, "filter %d" % ftype)
        finally:
            shutil.rmtree(tmp)


@unittest.skipUnless(have_tools(), "build first (make) for nitrogfx and nitroarc")
class Mistakes(unittest.TestCase):
    def fails(self, change, text, kind="front"):
        with Sandbox() as s:
            change(s)
            with self.assertRaises(DataError) as e:
                s.check(kind)
            self.assertIn(text, str(e.exception))

    def test_errors(self):
        def pic(s, name="TRAINERCLASS_YOUNGSTER"):
            return s.docs["front"]["pics"][name]
        self.fails(lambda s: pic(s).update(colour="red"), "unknown key")
        self.fails(lambda s: pic(s).update(anims=[[[3, 4]]]), "shows frame 3; there are 1")
        self.fails(lambda s: pic(s).update(anims=[[[0, 4, "wave"]]]), "unknown tag")
        self.fails(lambda s: pic(s).update(anims=[[[0, 4], [0, 4, 1, 0]]]), "every frame, or for none")
        self.fails(lambda s: pic(s).update(anims=[[[0, 4, "play 3"]]]), "doesn't exist")
        self.fails(lambda s: pic(s).update(layout="tiny"), "unknown layout")
        self.fails(lambda s: pic(s).update(pic="nobody"), "is missing")
        self.fails(lambda s: pic(s).update(flat=[2]), "uses frame 2")
        self.fails(lambda s: s.docs["front"]["pics"].pop("TRAINERCLASS_LASS"), "no entry for TRAINERCLASS_LASS")

        def swap(s):
            p = s.docs["front"]["pics"]
            keys = list(p)
            keys[1], keys[2] = keys[2], keys[1]
            s.docs["front"]["pics"] = {k: p[k] for k in keys}
        self.fails(swap, "number order")

        def bad_size(s):
            T.write_png(os.path.join(s.graphics, "front_pics/youngster.png"), [[0] * 64 for _ in range(64)],
                        [(0, 0, 0)] * 16)
        self.fails(bad_size, "must be 80 wide")

        def outside(s):
            # the Poké Fan's layout is 72 wide: column 75 isn't in any sprite
            png = os.path.join(s.graphics, "front_pics/pokefan.png")
            w, h, rows = T.read_png(png)
            rows[10][75] = 1
            T.write_png(png, rows, [(0, 0, 0)] * 16)
        self.fails(outside, "outside the frame's sprites")

        def corner(s):
            png = os.path.join(s.graphics, "front_pics/youngster.png")
            w, h, rows = T.read_png(png)
            rows[79][79] = 1
            T.write_png(png, rows, [(0, 0, 0)] * 16)
            pic(s)["flat"] = [0, 0]     # frame 0 on both halves, so (79, 79) is the picture's corner
        self.fails(corner, "bottom-right 4 pixels")


@unittest.skipUnless(have_tools(), "build first (make) for nitrogfx and nitroarc")
class NewClass(unittest.TestCase):
    def test_add_a_class(self):
        with Sandbox() as s:
            h = os.path.join(s.include, "constants/trainer_class.h")
            with open(h, encoding="utf-8") as f:
                text = f.read()
            text = text.replace("#define TRAINERCLASS_PKMN_TRAINER_DAWN_PT   128\n",
                                "#define TRAINERCLASS_PKMN_TRAINER_DAWN_PT   128\n#define TRAINERCLASS_SURFER 129\n")
            with open(h, "w", encoding="utf-8") as f:
                f.write(text)
            # two frames: the Youngster, and the Youngster one pixel lower; waves once when he arrives
            w, hh, rows = T.read_png(os.path.join(s.graphics, "front_pics/youngster.png"))
            lower = [[0] * 80] + rows[:79]
            T.write_png(os.path.join(s.graphics, "front_pics/surfer.png"), rows + lower,
                        T.read_pal(os.path.join(s.graphics, "palettes/youngster.pal")))
            shutil.copy(os.path.join(s.graphics, "palettes/youngster.pal"), os.path.join(s.graphics, "palettes/surfer.pal"))
            s.docs["front"]["pics"]["TRAINERCLASS_SURFER"] = {
                "pic": "surfer", "anims": [[[0, 4], "loop"], [[0, 10], [1, 10, "flash"], [0, 20]]]}
            m = narc_members(s.build("front"))
            self.assertEqual(len(m), 650)
            self.assertEqual(len(m[645]) - 0x30, 2 * 3200)
            flat, _ = T.unflat(m[649][0x30:])
            self.assertEqual([r[80:] for r in flat], lower)
            self.assertEqual(m[646], narc_members(s.build("front"))[11])   # same palette as the Youngster


if __name__ == "__main__":
    unittest.main()
