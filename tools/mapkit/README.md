<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21 -->

# mapkit

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Reads, checks and edits map data: headers, events (NPCs, warps, signs,
triggers), scripts, text, map grids and wild encounters, and migrates maps into
pokeemerald-style `data/maps/<MapName>/` folders. See
[docs/modding/DESIGN.md](../../docs/modding/DESIGN.md). Python 3.10+, standard
library only. Edits keep each file's indentation and line endings.

## Run

From anywhere in the checkout:

```sh
tools/mapkit/mapkit.sh <command> ...
# or
PYTHONPATH=tools/mapkit python3 -m mapkit <command> ...
```

`--version SOULSILVER` switches version-specific data (default HEARTGOLD).

## Commands

| Command | Does |
|---|---|
| `list [regex]` | maps with id, `MAP_*` name, code and map section |
| `show MAP [--text]` | header, file paths, NPCs/warps/signs/triggers with local cell coordinates, scripts (with the flags, vars and text each one reaches), wild table |
| `validate [MAP ...] [-w] [-a]` | broken references; exit code 1 on errors. `-w` adds warnings, `-a` adds notes |
| `refs SYMBOL` | every event field and script line using a flag, var, object, sprite, ... |
| `npc move/set/add` | move an NPC, change any field, add one (and its `#define` in `ids.h`) |
| `warp link A:i B:j` / `warp add` | point two warps at each other / add a warp tile |
| `wild set MAP METHOD SLOT SPECIES` | change a wild slot (`--level`, `--time` for grass) |
| `text add MAP 'text'` | append a message; prints its id |
| `script add MAP LABEL [--msg ID]` / `script rename MAP OLD NEW` | add a script / rename one everywhere |
| `migrate MAP [--dry-run]` | move a map into `data/maps/<MapName>/` (pokeemerald layout); ROM unchanged |
| `pory init MAP\|--all [--raw]` / `pory show MAP` / `pory sync MAP` | decompile a map's `.inc` scripts to `scripts.pory`, print its compiled output, sync `ids.h` ([SCRIPTING.md](../../docs/modding/SCRIPTING.md)) |
| `pory name-scripts MAP\|--all [--dry-run]` | pokeemerald-style names for generated script/movement labels (`npc_names.json`) |
| `pory inline-text MAP\|--all` | move dialog from `text.json` into `scripts.pory` as inline strings (ROM unchanged) |
| `sprite export SPRITE PNG` / `sprite import PNG SPRITE` / `sprite add NAME --like SPRITE_X [--png PNG]` | overworld sprites as PNG sheets and back; a new sprite with its constants, table row and file ([overworld-sprites.md](../../docs/modding/overworld-sprites.md)) |
| `terrain export CELL DIR` / `terrain import CELL OBJ` / `terrain check [CELL...]` | a cell's model and heights as OBJ/MTL/PNG and back, game limits ([terrain.md](../../docs/modding/terrain.md)) |
| `heights decompile/compile/show/at/generate CELL...` | a cell's BDHC heights as `heights.json`, queries, generation from the model |
| `areatex list SET` / `areatex add SET PNG` / `areatex color [SET]` | map texture sets in `data/area_textures`: list, add a texture from an indexed PNG, refresh PNG colors ([area-textures.md](../../docs/modding/area-textures.md)) |

`MAP` can be `MAP_CHERRYGROVE`, `Cherrygrove`, `cherrygrove`, the code `T21`, or the id `67`.

```sh
tools/mapkit/mapkit.sh show Cherrygrove --text
tools/mapkit/mapkit.sh refs FLAG_HIDE_CHERRYGROVE_GUIDE_GENT
tools/mapkit/mapkit.sh validate          # whole game
```

## What validate checks

| Check | Severity |
|---|---|
| a bank file named in `map_headers.h` is missing | error |
| events binary not under 0x800 bytes | error |
| an event value doesn't resolve to a constant | error |
| movement type out of range or the null slot 47 | error |
| object/sign/trigger points at a script number the map doesn't have | error |
| warp to a map that doesn't exist, or to a warp index it doesn't have | error |
| script uses an unknown command, an undefined label, text not in its bank, or an undefined flag/var/object | error |
| wild table missing, unknown species, a method with a rate but the wrong slot count | error |
| two objects in a map share an id (retail does this for NPCs never shown together) | warning |
| event outside the map grid | warning |
| a line of map text is wider than the 216 px dialogue box (`text-width`; each `{STRVAR_1 ...}` counts as the longest name it can hold, numbers as 0; points at the `scripts.pory` line) | warning |
| warp lands on a warp that leads somewhere else | note |
| event sits in a grid cell owned by another map | note |

On the unmodified repo, both versions report 0 errors.

## Layout

| Module | Reads |
|---|---|
| `cdefs.py` | `#define`s from `include/constants/*.h` and `event_*.h`; evaluates expressions like `std_trainer(TRAINER_X)` |
| `repo.py` | `maps.h`, `map_headers.h`; finds each map's files |
| `events.py` | zone_event JSON, binary size |
| `scripts.py` | `script.inc`/`movement.inc` macro table; `.s` files (ScrDef table, labels, commands); jump following |
| `text.py` | msg JSON banks |
| `matrix.py` | map grid `.bin` (round-trips byte for byte) |
| `wild.py` | `gs_enc_data.json`, `encounter_tables_narc.h` |
| `validate.py` | the checks above |
| `layout.py` | `data/maps` folders: migration, `map.json` <-> header/zone_event, build generators |
| `edit.py` | the edit commands |
| `pory/` | `scripts.pory` parser and compiler; target config in `tools/mapkit/script_config.json` |
| `nitro.py` | NSBMD/NSBTX decoding (triangles, polygons, textures) |
| `nsbmd.py` | NSBMD read/write, building terrain models |
| `bdhc.py` | BDHC heights: codec, the game's lookup, `heights.json`, generation |
| `terrain.py` | OBJ export/import of a cell's terrain, checks |
| `sprites.py` | overworld sprite NSBTX <-> PNG sheets (in place, same layout); adding a sprite |
| `nsbtx.py` | NSBTX read/write (every retail map and prop texture file rebuilds byte for byte) |
| `areatex.py` | `data/area_textures` folders <-> the map texture archive `a/0/4/4`; adding textures |
| `cli.py` | commands |

## Tests

```sh
python3 tools/mapkit/tests/test_mapkit.py
python3 tools/mapkit/tests/test_edit.py    # edits run on a temporary copy of the data
python3 tools/mapkit/tests/test_pory.py    # compiler, decompiler, round trip on every map
python3 tools/mapkit/tests/test_nsbmd.py   # every retail model rebuilds byte for byte; terrain models
python3 tools/mapkit/tests/test_bdhc.py    # every BDHC round-trips; heights.json; the game's lookup; generation
python3 tools/mapkit/tests/test_terrain.py # OBJ export -> import changes nothing
python3 tools/mapkit/tests/test_sprites.py # every overworld sprite: PNG export -> import changes nothing
python3 tools/mapkit/tests/test_areatex.py # map texture sets rebuild a/0/4/4; adding textures
```

Checks the parsers against the real data (every matrix file round-trips; the
clean repo has no errors in either version) and that each check fires when the
data is broken on purpose.
