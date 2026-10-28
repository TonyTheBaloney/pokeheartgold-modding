# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
"""What tools outside Python need from the C sources, as one JSON document.

The Rust map editor (tools/mapeditor-rs) reads the text files in data/ itself, but
constant names come from include/constants/*.h through the C preprocessor rules in
cdefs.py, and the sprite table from asm/overlay_01_sprite_data.s. Rather than parse
C twice, `mapkit export-constants` writes:

    {
      "format": "mapkit-constants", "version": 1, "game": "HEARTGOLD",
      "constants": {"SPRITE_": [...], "FLAG_": [...], ...},   sorted names per prefix
      "behaviors": {"0": "TILE_BEHAVIOR_NONE", ...},          enum TILE_BEHAVIOR
      "sprites": {"SPRITE_GSMAN1": "files/data/mmodel/mmodel/mmodel_00000012.NSBTX", ...}
    }

Paths are relative to the repository root.
"""

import os
import re

from . import sprites

FORMAT_VERSION = 1

# Prefixes the editor completes and checks map.json fields against.
PREFIXES = ("SPRITE_", "MOVEMENT_TYPE_", "DIR_", "OBJECT_TYPE_", "FLAG_", "MAP_", "VAR_", "BG_TYPE_",
            "BG_DIR_", "SEQ_", "MAPSEC_", "WEATHER_", "MAP_TYPE_", "BATTLE_BG_", "CAMERA_TYPE_")

# Constants that are C enum members, not #defines: prefix -> header with the enum
ENUM_SOURCES = {"MAP_TYPE_": "include/map_header.h", "BATTLE_BG_": "include/constants/battle.h"}

BEHAVIORS_H = "include/constants/metatile_behavior.h"


def enum_names(root, path, prefix):
    """Members starting with prefix of the C enums in a header."""
    with open(os.path.join(root, path), encoding="utf-8") as f:
        text = re.sub(r"/\*.*?\*/", "", re.sub(r"//.*", "", f.read()), flags=re.S)
    out = set()
    for body in re.findall(r"\benum\b[^{;]*\{(.*?)\}", text, re.S):
        out.update(re.findall(r"^\s*(%s\w*)\b" % re.escape(prefix), body, re.M))
    return out


def behavior_names(root):
    """{value: name} from enum TILE_BEHAVIOR."""
    with open(os.path.join(root, BEHAVIORS_H), encoding="utf-8") as f:
        text = f.read()
    body = re.search(r"enum\s+TILE_BEHAVIOR\s*\{(.*?)\};", text, re.S).group(1)
    out, v = {}, 0
    for item in body.split(","):
        item = re.sub(r"//.*", "", item).strip()
        if not item:
            continue
        m = re.fullmatch(r"(\w+)(?:\s*=\s*(\w+))?", item)
        if m.group(2):
            v = int(m.group(2), 0)
        out[v] = m.group(1)
        v += 1
    return out


def constants(repo):
    consts = {}
    for prefix in PREFIXES:
        names = set(repo.defines.names(prefix))
        if prefix in ENUM_SOURCES:
            names |= enum_names(repo.root, ENUM_SOURCES[prefix], prefix)
        consts[prefix] = sorted(names)
    try:
        paths = sprites.texture_paths(repo.root)
    except (OSError, ValueError):
        paths = {}
    return {
        "format": "mapkit-constants",
        "version": FORMAT_VERSION,
        "game": repo.version,
        "constants": consts,
        "behaviors": {str(k): v for k, v in sorted(behavior_names(repo.root).items())},
        "sprites": {k: os.path.relpath(v, repo.root).replace(os.sep, "/") for k, v in sorted(paths.items())},
    }
