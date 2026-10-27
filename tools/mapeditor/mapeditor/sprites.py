# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27
"""Overworld sprites of objects, for the map view: one frame of each object's
graphics_id, facing its facing_dir.

graphics_id -> gObjectEventGraphicsInfos -> MMODEL_ -> files/data/mmodel/mmodel NSBTX
(mapkit.sprites, docs/modding/overworld-sprites.md). The textures are named
<name>.1 ... <name>.N; in that order:

- 16 frames (standard NPCs; 17 with an extra pose): four per facing, north, south,
  west, east, the first of each four standing;
- 8 frames (follow-Pokémon): two per facing in the same order;
- anything else (still objects, trees, legendaries' poses): frame 1.

SPRITE_VAR_n objects take their sprite from VAR_OBJ_n when the map loads
(include/constants/vars.h), so they can't be drawn here.
"""

import os
import re

from PySide6.QtGui import QImage

from mapkit import nitro
from mapkit import sprites as mksprites

FACINGS = {"DIR_NORTH": 0, "DIR_SOUTH": 1, "DIR_WEST": 2, "DIR_EAST": 3}  # include/constants/global_fieldmap.h
FRAMES_PER_FACING = {16: 4, 17: 4, 8: 2}


def frame_for(frames, facing):
    """Index (0-based) of the standing frame for a facing (0-3) in a sheet of `frames`."""
    per = FRAMES_PER_FACING.get(frames)
    return facing * per if per and 0 <= facing <= 3 else 0


def facing_index(value):
    if isinstance(value, int):
        return value
    return FACINGS.get(value, 1)


class SpriteImages:
    def __init__(self, root):
        self.root = root
        self._paths = None
        self._sets = {}
        self._images = {}
        self.error = None     # why the sprite tables couldn't be read

    def paths(self):
        if self._paths is None:
            try:
                self._paths = mksprites.texture_paths(self.root)
            except (OSError, ValueError) as e:  # no sprite tables: every object stays a box
                self.error = str(e)
                self._paths = {}
        return self._paths

    def why_not(self, graphics_id):
        """None if the sprite can be drawn, else a short reason."""
        g = str(graphics_id)
        m = re.fullmatch(r"SPRITE_VAR_(\d+)", g)
        if m:
            return "set when the map loads, from VAR_OBJ_%s" % m.group(1)
        path = self.paths().get(g)
        if path is None:
            return self.error or "no row in gObjectEventGraphicsInfos"
        if self._texset(path) is None:
            return "no texture file %s" % os.path.relpath(path, self.root)
        return None

    def _texset(self, path):
        if path not in self._sets:
            try:
                with open(path, "rb") as f:
                    ts = nitro.load_nsbtx(f.read())
                names = sorted(ts.textures, key=lambda n: int(re.search(r"(\d+)$", n).group(1))
                               if re.search(r"(\d+)$", n) else 0)
                self._sets[path] = (ts, names, next(iter(ts.palettes), None)) if names else None
            except (OSError, nitro.NitroError):
                self._sets[path] = None
        return self._sets[path]

    def image(self, graphics_id, facing="DIR_SOUTH"):
        """QImage of the object's standing frame, or None (see why_not)."""
        key = (str(graphics_id), facing_index(facing))
        if key not in self._images:
            img = None
            path = self.paths().get(key[0]) if self.why_not(key[0]) is None else None
            if path:
                ts, names, palette = self._texset(path)
                decoded = ts.image(names[frame_for(len(names), key[1])], palette)
                if decoded:
                    w, h, rgba = decoded
                    img = QImage(bytes(rgba), w, h, w * 4, QImage.Format_RGBA8888).copy()
            self._images[key] = img
        return self._images[key]
