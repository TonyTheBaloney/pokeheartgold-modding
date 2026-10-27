# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25
"""Overworld sprite PNG export/import (mapkit/sprites.py), on copies of the game's files."""

import glob
import os
import shutil
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/mapkit"))

from mapkit import sprites  # noqa: E402


def rgba_png(path, w, h, rgba):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class RoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def roundtrip(self, src, palette=0):
        orig = open(src, "rb").read()
        copy = os.path.join(self.tmp, "copy.NSBTX")
        shutil.copyfile(src, copy)
        png = os.path.join(self.tmp, "sheet.png")
        sprites.export(ROOT, copy, png, palette)
        sprites.import_png(ROOT, png, copy, palette)
        return orig, open(copy, "rb").read()

    def test_every_sprite_survives_export_and_import(self):
        paths = sorted(glob.glob(os.path.join(ROOT, sprites.MMODEL_DIR, "*.NSBTX")))
        self.assertEqual(len(paths), 832)
        for p in paths:
            pals = len(sprites.Layout(open(p, "rb").read()).palettes)
            for pal in range(pals):
                orig, back = self.roundtrip(p, pal)
                self.assertEqual(orig, back, "%s palette %d" % (os.path.basename(p), pal))

    def test_rgba_sheet_keeps_the_palette_order(self):
        src = sprites.resolve(ROOT, "SPRITE_BOY1")
        copy = os.path.join(self.tmp, "boy.NSBTX")
        shutil.copyfile(src, copy)
        png = os.path.join(self.tmp, "boy.png")
        sprites.export(ROOT, copy, png)
        w, h, kind, rows, pal, alpha = sprites.read_png(png)
        rgba = bytearray()
        for r in rows:
            for i in r:
                rgba += bytes(pal[i]) + bytes([0 if i == 0 else 255])
        rgba_path = os.path.join(self.tmp, "rgba.png")
        rgba_png(rgba_path, w, h, rgba)
        sprites.import_png(ROOT, rgba_path, copy)
        self.assertEqual(open(src, "rb").read(), open(copy, "rb").read())

    def test_wrong_size_is_refused(self):
        copy = os.path.join(self.tmp, "boy.NSBTX")
        shutil.copyfile(sprites.resolve(ROOT, "SPRITE_BOY1"), copy)
        png = os.path.join(self.tmp, "small.png")
        rgba_png(png, 32, 32, bytes(32 * 32 * 4))
        with self.assertRaises(sprites.SpriteError):
            sprites.import_png(ROOT, png, copy)

    def test_too_many_colours_is_refused(self):
        copy = os.path.join(self.tmp, "boy.NSBTX")
        shutil.copyfile(sprites.resolve(ROOT, "SPRITE_BOY1"), copy)
        w, h = 32 * 16, 32
        rgba = bytearray()
        for y in range(h):
            for x in range(w):
                rgba += bytes([(x * 8) & 255, y * 8, 0, 255])
        png = os.path.join(self.tmp, "many.png")
        rgba_png(png, w, h, rgba)
        with self.assertRaises(sprites.SpriteError):
            sprites.import_png(ROOT, png, copy)


class Lookups(unittest.TestCase):
    def test_names_resolve_to_files(self):
        self.assertTrue(sprites.resolve(ROOT, "SPRITE_BOY1").endswith("mmodel_00000002.NSBTX"))
        self.assertTrue(sprites.resolve(ROOT, "MMODEL_BOY1").endswith("mmodel_00000002.NSBTX"))
        self.assertTrue(sprites.resolve(ROOT, "2").endswith("mmodel_00000002.NSBTX"))
        with self.assertRaises(sprites.SpriteError):
            sprites.resolve(ROOT, "266")   # an NSBMD member, not a texture

    def test_texture_paths_agree_with_resolve(self):
        paths = sprites.texture_paths(ROOT)
        self.assertGreater(len(paths), 800)
        for name in ("SPRITE_BOY1", "SPRITE_GSMAN1", "SPRITE_FOLLOWER_MON_STATIC_PIKACHU"):
            self.assertEqual(paths[name], sprites.resolve(ROOT, name))


if __name__ == "__main__":
    unittest.main()
