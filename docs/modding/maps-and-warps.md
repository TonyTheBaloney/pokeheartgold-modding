<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Maps, warps, signs and trigger zones

> AI-generated, local to this fork. Do not upstream.

## Finding a map's files

Every map has a folder in `data/maps/`, laid out like pret/pokeemerald:

| File | Holds |
|---|---|
| `data/maps/Cherrygrove/map.json` | header **and** events (`object_events`, `warp_events`, `coord_events`, `bg_events`) |
| `data/maps/Cherrygrove/scripts.inc` | event scripts |
| `data/maps/Cherrygrove/map_scripts.inc` | init / level scripts (on load, on transition, frame table) |
| `data/maps/Cherrygrove/text.json` | text |
| `data/maps/Cherrygrove/ids.h` | script and object ids |

`tools/mapkit/mapkit.sh list goldenrod` finds maps by name;
`tools/mapkit/mapkit.sh show Cherrygrove` prints a map's files, events, scripts and
wild table.

Folder names are CamelCase from the `MAP_*` constant (`include/constants/maps.h`),
with `_` before a sub-map or floor: `MAP_CHERRYGROVE_POKECENTER_1F` ->
`Cherrygrove_Pokecenter_1F`, `MAP_ROUTE_29` -> `Route29`. `map.json`'s `code` is Game
Freak's name for the map (`T21`); the original file names (`scr_seq_0850_T21.s`, ...)
are kept in `data/maps/maps.txt`.

Some unused maps have no scripts, text or events of their own. In `maps.txt` their
banks read `@Everywhere`: they use `data/maps/Everywhere/`'s files, and their own
folder holds only the header part of `map.json`.

## Map header (top of `map.json`)

Key names follow pokeemerald where one exists:

| Key | Meaning |
|---|---|
| `music_day`, `music_night` | `SEQ_*` from `include/constants/sndseq.h` |
| `weather` | weather id |
| `region_map_section` | name shown on entry and on the Town Map (`MAPSEC_*`) |
| `map_type` | `MAP_TYPE_*` (town, route, building, ...) |
| `battle_scene` | `BATTLE_BG_*` used for battles here |
| `camera_type` | camera preset |
| `allow_cycling`, `allow_escaping`, `allow_fly`, `allow_running` | permissions (`allow_running` is unused by the game) |
| `allow_outgoing_calls`, `allow_incoming_calls`, `radio_signal` | Pokégear |
| `wild_encounters` | `ENCDATA_*` table, or `ENCDATA_NA` ([wild-encounters.md](wild-encounters.md)) |
| `layout` | map grid used (see below) |
| `area_data`, `move_model_bank`, `area_icon`, `mom_call_intro`, `follow_mode`, `region`, `world_map_x/y` | DS-specific; copy from a similar map |

The C field each key becomes is listed in `HEADER_KEYS`,
`tools/mapkit/mapkit/layout.py`. The build generates the `MapHeader` entry from
these keys.

## Coordinates

Event coordinates are **global tile** coordinates over the map grid (matrix):
`global = cell * 32 + local`, where a cell is one 32×32-tile block.
`src/field/field_control.c` converts with `globalX % 32`.

`map.json` uses pokeemerald's names: `x` east-west, `y` north-south, `elevation`
height (the DS code calls these `x`, `z`, `y`).

To find the coordinates of a spot, stand there in an emulator and read the player
position from RAM, or copy a nearby object's or warp's coordinates.
`mapkit show` prints every event as `global (cell cx,cz +local)`.

The whole events section must stay under 0x800 bytes in the ROM (assert in
`src/map_events.c`): 16 bytes of counts + 20 per bg + 32 per object + 12 per warp +
16 per coord. `mapkit validate` checks it.

## Warps (`warp_events`)

```json
{ "x": 564, "y": 391, "elevation": 0, "dest_map": "MAP_CHERRYGROVE_POKECENTER_1F", "dest_warp_id": 0 }
```

- `x`, `y`: the tile that triggers the warp (door, stairs, cave mouth).
- `dest_map`: destination `MAP_*`.
- `dest_warp_id`: index of the **destination map's** warp to land on (0 = its first
  warp). The player appears on that warp's tile.

Warps are one-way records. A door needs two: A's warp pointing at B's warp, and
B's warp pointing back. If you reorder a map's `warp_events`, every warp elsewhere
that lands on it by index has to change too.

**Dynamic warp:** `"dest_map": 4095, "dest_warp_id": 256` (0xFFF / 0x100) returns the
player to the location the game saved as the dynamic warp. Used for exits that
depend on where you came from.

With mapkit:

```sh
tools/mapkit/mapkit.sh warp link Cherrygrove:1 Cherrygrove_Pokemart:0   # both directions
tools/mapkit/mapkit.sh warp add Cherrygrove 540 390 --to Route30:2       # new warp tile
tools/mapkit/mapkit.sh validate -a Cherrygrove   # missing targets (error), one-way warps (note)
```

## Signs and hidden items (`bg_events`)

```json
{ "type": "BG_TYPE_SIGNPOST", "x": 556, "y": 401, "elevation": 0,
  "player_facing_dir": "BG_DIR_ALL", "script": "Cherrygrove_EventScript_GuideGentsHouseSign" }
```

`type` is `BG_TYPE_NORMAL`, `BG_TYPE_SIGNPOST` or `BG_TYPE_HIDDEN_ITEM`
(`include/constants/global_fieldmap.h`); `player_facing_dir` is the side you must
face it from (`BG_DIR_*`). Hidden items use `std_hiddenitem_*` scripts.

## Trigger zones (`coord_events`)

```json
{ "x": 566, "y": 397, "elevation": 0, "width": 1, "height": 4,
  "var": "VAR_SCENE_CHERRYGROVE_CITY_OW", "var_value": 0, "script": "Cherrygrove_EventScript_GuideGentTour" }
```

Runs `script` when the player steps into the `width`×`height` rectangle **and**
`var == var_value`. The script usually changes `var` so it fires once. Many of these
vars are still `VAR_UNK_*`.

## Map grid (matrix)

`files/fielddata/mapmatrix/map_matrix/map_matrix_NNNN_NAME.bin`, binary, one per
grid, parsed in `src/map_matrix.c`; `map.json`'s `layout` names it.

```
u8 width, height, hasHeaders, hasAltitudes, nameLen; char name[nameLen];
[u16 mapHeaderIds[w*h]]   if hasHeaders   -> which MAP_* owns each cell
[u8  altitudes[w*h]]      if hasAltitudes
u16  landDataIds[w*h]                     -> block in the land-data archive
```

Many maps share one grid (the outdoor grid holds most routes and towns; each
cell's `mapHeaderIds` says which map you're in). `mapkit` reads these
(`matrix.py`); moving them to pokeemerald-style `data/layouts/` is a later step.

## Terrain, collision, buildings, 3D models

All in `files/a/0/6/5`, one prebuilt 19.5 MB archive. Each block has
permissions/collision, building placements, an NSBMD model and height data
(header read by `ReadMapFileHeader` in `src/field/map_load_manager.c`). There is no
editor for these in the repo yet.

## Adding a new map

Not covered yet. It needs a `MAP_*` id in `maps.h`, a folder, a `maps.txt` line
with new bank names after the existing ones, and an entry in
`src/data/map_headers.h` that includes the generated header.
