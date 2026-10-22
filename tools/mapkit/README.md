<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21 -->

# mapkit

> AI-generated, local to this fork. Do not upstream.

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
| `pory init MAP` / `pory show MAP` / `pory sync MAP` | convert a map to `scripts.pory`, print its compiled output, sync `ids.h` ([SCRIPTING.md](../../docs/modding/SCRIPTING.md)) |

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
| `cli.py` | commands |

## Tests

```sh
python3 tools/mapkit/tests/test_mapkit.py
python3 tools/mapkit/tests/test_edit.py    # edits run on a temporary copy of the data
python3 tools/mapkit/tests/test_pory.py    # compiler, and pory init on every map
```

Checks the parsers against the real data (every matrix file round-trips; the
clean repo has no errors in either version) and that each check fires when the
data is broken on purpose.
