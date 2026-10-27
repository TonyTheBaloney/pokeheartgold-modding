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

Animation previews an object's movement_type in place (the editor never moves
objects: their position is what you edit): walkers play the four-frame walk
cycle (stand, step, stand, other step) and turn through the directions they
walk in, lookers and spinners turn, follow-Pokémon alternate their two frames,
the rest stand. The timing is the editor's, not the game's.
"""

import os
import re

from PySide6.QtGui import QImage

from mapkit import nitro
from mapkit import sprites as mksprites

FACINGS = {"DIR_NORTH": 0, "DIR_SOUTH": 1, "DIR_WEST": 2, "DIR_EAST": 3}  # include/constants/global_fieldmap.h
N, S, W, E = 0, 1, 2, 3
FRAMES_PER_FACING = {16: 4, 17: 4, 8: 2}

# movement_type -> ("walk" or "turn", directions in order); include/constants/map_object.h,
# src/map_object_movement.c. Types not listed stand still facing facing_dir.
TURN_TICKS, WALK_TICKS = 8, 16    # ticks per direction
MOVEMENTS = {
    "MOVEMENT_TYPE_LOOK_AROUND": ("turn", (S, W, N, E)),   # random in the game
    "MOVEMENT_TYPE_WANDER_AROUND": ("walk", (S, W, N, E)),
    "MOVEMENT_TYPE_WANDER_UP_DOWN": ("walk", (N, S)),
    "MOVEMENT_TYPE_WANDER_LEFT_RIGHT": ("walk", (W, E)),
    "MOVEMENT_TYPE_LOOK_UP_LEFT": ("turn", (N, W)),
    "MOVEMENT_TYPE_LOOK_UP_RIGHT": ("turn", (N, E)),
    "MOVEMENT_TYPE_LOOK_DOWN_LEFT": ("turn", (S, W)),
    "MOVEMENT_TYPE_LOOK_DOWN_RIGHT": ("turn", (S, E)),
    "MOVEMENT_TYPE_LOOK_UP_DOWN_LEFT": ("turn", (N, S, W)),
    "MOVEMENT_TYPE_LOOK_UP_DOWN_RIGHT": ("turn", (N, S, E)),
    "MOVEMENT_TYPE_LOOK_UP_LEFT_RIGHT": ("turn", (N, W, E)),
    "MOVEMENT_TYPE_LOOK_DOWN_LEFT_RIGHT": ("turn", (S, W, E)),
    "MOVEMENT_TYPE_LOOK_UP_DOWN": ("turn", (N, S)),
    "MOVEMENT_TYPE_LOOK_LEFT_RIGHT": ("turn", (W, E)),
    "MOVEMENT_TYPE_SPIN_COUNTERCLOCKWISE": ("turn", (N, W, S, E)),
    "MOVEMENT_TYPE_SPIN_CLOCKWISE": ("turn", (N, E, S, W)),
    "MOVEMENT_TYPE_ALTERNATING_SPIN": ("turn", (N, E, S, W)),
}
_PATH = re.compile(r"MOVEMENT_TYPE_PATH_((?:NORTH|SOUTH|EAST|WEST)(?:_(?:NORTH|SOUTH|EAST|WEST)){3})(?:_\d+)?$")
_DIRS = {"NORTH": N, "SOUTH": S, "WEST": W, "EAST": E}


def frame_for(frames, facing, step=0):
    """Index (0-based) of a frame in a sheet of `frames`: the standing frame for a facing
    (0-3), plus `step` into the walk cycle for sheets that have one."""
    per = FRAMES_PER_FACING.get(frames)
    return facing * per + step % per if per and 0 <= facing <= 3 else 0


def movement(movement_type):
    """("walk" | "turn", directions) for a movement type, or None if it stands still."""
    m = MOVEMENTS.get(str(movement_type))
    if m:
        return m
    p = _PATH.match(str(movement_type))
    if p:   # walks a rectangle, in the named directions
        return ("walk", tuple(_DIRS[d] for d in p.group(1).split("_")))
    if str(movement_type) == "MOVEMENT_TYPE_BACK_AND_FORTH":
        return ("walk", None)   # its own facing, then the opposite
    return None


def pose(movement_type, facing, frames, tick):
    """(facing 0-3, walk step) of an object at animation tick `tick`."""
    facing = facing_index(facing)
    per = FRAMES_PER_FACING.get(frames)
    m = movement(movement_type)
    if per == 2:            # follow-Pokémon: always stepping in place
        step = (tick // 2) % 2
    else:
        step = 0
    if m is None:
        return facing, step
    kind, dirs = m
    if dirs is None:
        dirs = (facing, {N: S, S: N, W: E, E: W}.get(facing, facing))
    facing = dirs[(tick // (WALK_TICKS if kind == "walk" else TURN_TICKS)) % len(dirs)]
    if kind == "walk" and per == 4:
        step = tick % 4
    return facing, step


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

    def frames(self, graphics_id):
        """How many frames the sprite has (0 if it can't be drawn)."""
        if self.why_not(graphics_id) is not None:
            return 0
        return len(self._texset(self.paths()[str(graphics_id)])[1])

    def image(self, graphics_id, facing="DIR_SOUTH", step=0):
        """QImage of the object's frame for a facing and walk step (0 = standing), or None
        (see why_not)."""
        key = (str(graphics_id), facing_index(facing), step)
        if key not in self._images:
            img = None
            path = self.paths().get(key[0]) if self.why_not(key[0]) is None else None
            if path:
                ts, names, palette = self._texset(path)
                decoded = ts.image(names[frame_for(len(names), key[1], step)], palette)
                if decoded:
                    w, h, rgba = decoded
                    img = QImage(bytes(rgba), w, h, w * 4, QImage.Format_RGBA8888).copy()
            self._images[key] = img
        return self._images[key]
