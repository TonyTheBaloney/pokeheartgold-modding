<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Maps, warps, signs and trigger zones

> AI-generated, local to this fork. Do not upstream.

## Finding a map's files

Every map has a folder in `data/maps/`, laid out like pret/pokeemerald:

| File | Holds |
|---|---|
| `data/maps/Cherrygrove/map.json` | header **and** events (`object_events`, `warp_events`, `coord_events`, `bg_events`) |
| `data/maps/Cherrygrove/scripts.pory` | event scripts, movement and init / level scripts (`mapscripts`) |
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

## Map grid: data/layouts

A map's grid of 32×32-tile cells is its **layout**, as in pokeemerald:
`data/layouts/<Layout>/layout.json`, named by `map.json`'s `layout`.

```json
{
    "name": "m_dun0101_",
    "width": 2,
    "height": 3,
    "land_data": [
        [383, 384],
        [385, 386],
        [387, 388]
    ]
}
```

| Key | Meaning |
|---|---|
| `land_data` | one row per line; each cell's terrain, `data/landdata/NNNN/` (below); `null` = no cell |
| `maps` | outdoor layouts only: which `MAP_*` header applies in each cell (where you are for music, wild data, the name popup) |
| `altitudes` | outdoor layouts only: per-cell altitude |
| `name` | the name stored in the file; not used by the game |

- Layouts are shared. `Overworld` (47×17) holds every town and route: Cherrygrove
  is the two cells whose `maps` entry is `MAP_CHERRYGROVE`. Indoor layouts are
  named after their map, or after what they are when several maps use them
  (`PokemonCenter_1F`, `Pokemart`, `House1`-`House4`, `Gatehouse_EastWest`, ...).
- `mapkit layouts rename OLD NEW` renames a layout and the maps that use it.
- `data/layouts/layouts.txt` keeps each layout's original file name
  (`map_matrix_0002_D01R0101`), so the ROM's file order doesn't depend on folder
  names. The build writes every layout back to its matrix (`mapkit layouts pack`,
  `src/map_matrix.c` reads it).

## Terrain: data/landdata

Each cell's terrain is one folder, `data/landdata/NNNN/` (NNNN is the number
`land_data` uses; the build packs them in that order into `files/a/0/6/5`).

| File | Holds | Editable? |
|---|---|---|
| `permissions.txt` | per tile: collision, behavior, attribute | yes (text, or the map editor) |
| `props.json` | placed props (buildings, trees, signs...) | yes |
| `soundplates.bin` | sound plates, only in cells that have them | binary |
| `model.nsbmd` | the 3D terrain model | binary |
| `terrain.bdhc` | terrain heights the player walks on | binary |

`permissions.txt` is three 32×32 grids (row = north to south):

```
[collision]  # blocks movement, . is open
######......##########..........
...
[behavior]  TILE_BEHAVIOR_* value in hex (include/constants/metatile_behavior.h)
00 00 02 02 ...
[attr]  bits 8-14 of the permission word, hex (FieldSystem_GetTileAttrBits8To14)
00 00 ...
```

- **Behavior** is what the tile does: `02` tall grass, `10` river water, `15` sea,
  `20` ice, door and warp tiles, ledges... (`enum TILE_BEHAVIOR`; checks in
  `src/metatile_behavior.c`). Painting water behavior doesn't draw water: the
  look comes from `model.nsbmd`, so keep behavior and model in step.
- **Collision** blocks walking (`FieldSystem_CheckTileCollision`, `src/field_terrain.c`).
  Copy a nearby door or warp tile's collision and behavior when adding one.
- `[attr]` is written only for cells that use it; its meaning isn't decoded yet
  (map object movement reads it).
- Cells can be **shared**: one land data folder can appear in several layout
  cells (repeating sea, every Pokémon Center). Editing it changes all of them;
  the map editor's status bar says how many cells use the one under the cursor.

`props.json`, one prop per line:

```json
{ "model": 29, "position": [-88.0, 17.0, -56.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0] }
```

`model` is a prop number from the area's prop list (`area_data` in the header,
`src/field/area_data.c`); `position` is in 1/16 tile from the cell's centre
(x east, y height, z south), in steps of 1/4096. At most 32 props per cell
(`MAP_PROP_MAX`, `include/field/map_load_manager.h`).

The terrain model's textures aren't in `model.nsbmd`: they come from the map's
area (`area_data` in `map.json` -> area header `files/a/0/4/2` -> textures in
`files/a/0/4/4`), and props use the area's prop models and textures
(`src/field/area_data.c`). The game loads one area at a time, the current map's,
and draws the cells it can see with it. In outdoor layouts each cell's terrain
is raised by its `altitudes` value × 8 units (half a tile).

`tools/mapkit/mapkit.sh landdata pack` rebuilds `files/a/0/6/5`; the unmodified
folders give the retail archive (checked by `tools/mapkit/tests`).

## Map editor

`tools/mapeditor/mapeditor.sh Cherrygrove` opens a porymap-style editor that
draws the map from its 3D models (top-down and in a 3D tab) and edits collision,
behaviors and events; see
[tools/mapeditor/README.md](../../tools/mapeditor/README.md).

## Adding a new map

Not covered yet. It needs a `MAP_*` id in `maps.h`, a folder, a `maps.txt` line
with new bank names after the existing ones, and an entry in
`src/data/map_headers.h` that includes the generated header.
