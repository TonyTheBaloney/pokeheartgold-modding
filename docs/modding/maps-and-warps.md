<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21 -->

# Maps, warps, signs and trigger zones

> AI-generated, local to this fork. Do not upstream.

## Finding a map's files

Every map has a `MAP_*` ID in `include/constants/maps.h`. The comment on each line
gives Game Freak's code for it, which is what the data files are named after:

```c
#define MAP_CHERRYGROVE           67  // MAP_T21
#define MAP_CHERRYGROVE_POKEMART  68  // MAP_T21FS0101
```

Code letters: `T` towns and cities (228 maps), `D` dungeons and special areas (168),
`R` routes, `W` water routes, `P` ports/ships; a few others (`C`, `S`, ...) are rare
or unused leftovers. Suffixes: `PC` Pokémon Center, `FS` mart, `R0101` building/floor.

With the code, find the rest (example `T21`):

| File | Holds |
|---|---|
| `src/data/map_headers.h` `[MAP_CHERRYGROVE]` | header; names every bank below |
| `files/fielddata/eventdata/zone_event/064_T21.json` | NPCs, warps, signs, triggers |
| `files/fielddata/script/scr_seq/scr_seq_0850_T21.s` | event scripts |
| `files/fielddata/script/scr_seq/scr_seq_0623_T21_hdr.s` | init / level scripts |
| `files/fielddata/script/scr_seq/event_T21.h` | script and object IDs |
| `files/msgdata/msg/msg_NNNN_T21.json` | text (`.msgBank` gives NNNN) |

`tools/mapkit/mapkit.sh show Cherrygrove` prints all of these paths plus the map's
events, scripts and wild table. `tools/mapkit/mapkit.sh list goldenrod` finds maps by name.

### Maps in `data/maps/` (pokeemerald layout)

Migrated maps (so far: Cherrygrove; list in `data/maps/maps.txt`) keep everything
in one folder instead:

| File | Holds |
|---|---|
| `data/maps/Cherrygrove/map.json` | header **and** events (`object_events`, `warp_events`, `coord_events`, `bg_events`) |
| `data/maps/Cherrygrove/scripts.inc` | event scripts |
| `data/maps/Cherrygrove/map_scripts.inc` | init / level scripts |
| `data/maps/Cherrygrove/text.json` | text |
| `data/maps/Cherrygrove/ids.h` | script and object ids |

In `map.json` the event fields use pokeemerald names: `x`/`y`/`elevation` are the
DS `x`/`z`/`y`, a warp's `dest_map`/`dest_warp_id` are `header`/`anchor`, and a
`script` can be a script label. The full table is in [DESIGN.md](DESIGN.md#mapjson).

## Map header

`src/data/map_headers.h`, struct in `include/map_header.h`. Fields you'll edit
most:

| Field | Meaning |
|---|---|
| `dayMusicId`, `nightMusicId` | `SEQ_*` from `include/constants/sndseq.h` |
| `weather` | weather ID |
| `mapsec` | name shown on entry and on the Town Map (`include/constants/map_sections.h`) |
| `mapType` | `MAP_TYPE_*` (town, route, building, ...) |
| `battleBg` | `BATTLE_BG_*` used for battles here |
| `cameraType` | camera preset |
| `bikeAllowed`, `escapeRopeAllowed`, `flyAllowed` | permissions |
| `wildEncounterBank` | `ENCDATA_*` table, or `ENCDATA_NA` ([wild-encounters.md](wild-encounters.md)) |
| `matrixId` | map grid used (see below) |
| `scriptsBank`, `scriptHeaderBank`, `msgBank`, `eventsBank` | the files above |

## Coordinates

Event coordinates are **global tile** coordinates over the map's grid (matrix):
`global = cell * 32 + local`, where a cell is one 32×32-tile block of the matrix.
`src/field/field_control.c` converts with `globalX % 32`. Height is `y`
(usually 0).

To find the coordinates of a spot, stand there in an emulator and read the
player position from RAM, or copy the coordinates of a nearby object/warp from the
same JSON. `mapkit show` prints every event as `global (cell cx,cz +local)`.

## Events file (zone_event JSON)

```json
{
  "header": "fielddata/script/scr_seq/event_T21.h",
  "bgs":     [ ... signs, hidden items ... ],
  "objects": [ ... NPCs, see npcs-and-scripts.md ... ],
  "warps":   [ ... ],
  "coords":  [ ... trigger zones ... ]
}
```

Values can be numbers or any C constant/expression visible to the template
(`MAP_*`, `FLAG_*`, `VAR_*`, `SPRITE_*`, `_EV_scr_seq_T21_003 + 1`).

The whole events binary must fit in 0x800 bytes (assert in `src/map_events.c`).
Sizes: 16 bytes of counts + 20 per bg + 32 per object + 12 per warp + 16 per coord.

### Warps (teleport events)

```json
{ "x": 564, "z": 391, "header": "MAP_CHERRYGROVE_POKECENTER_1F", "anchor": 0, "y": 0 }
```

- `x`, `z`: tile that triggers the warp (door, stairs, cave mouth).
- `header`: destination `MAP_*`.
- `anchor`: index of the **destination map's** warp to land on (0 = its first warp).
  The player appears on that warp's tile.
- `y`: unused, 0.

Warps are one-way records. A door needs two: map A's warp pointing to B's warp
index, and B's warp pointing back to A's. If you reorder a map's `warps` array,
every warp elsewhere that lands on it by index has to change too.

**Dynamic warp:** `"header": 4095, "anchor": 256` (0xFFF / 0x100) sends the player
back to the location the game saved as the dynamic warp, instead of a fixed map.
Used for exits that depend on where you came from.

Changing where a door leads:
1. Edit `header` and `anchor` on the source warp.
2. In the destination map's JSON, make sure warp `anchor` exists and points back.

Or with mapkit, which sets both sides: `tools/mapkit/mapkit.sh warp link Cherrygrove:1 Cherrygrove_Pokemart:0`.
`warp add Cherrygrove 540 390 --to Route30:2` adds a new warp tile.
3. `tools/mapkit/mapkit.sh validate -a <map>` reports warps to missing warp indexes
   (error) and warps whose landing spot leads somewhere else (note).

### Signs and hidden items (`bgs`)

`scriptId`, `type` (`BG_TYPE_NORMAL`, `BG_TYPE_SIGNPOST`, `BG_TYPE_HIDDEN_ITEM`
from `include/constants/global_fieldmap.h`), `x`, `z`, `y`, `dir` (the side
you must face it from; `BG_DIR_*` in the same header).

### Trigger zones (`coords`)

```json
{ "scriptId": ..., "x": ..., "z": ..., "w": 1, "h": 3, "y": 0, "val": 0, "var": "VAR_UNK_40A2" }
```

Runs `scriptId` when the player steps inside the `w`×`h` rectangle at
(`x`, `z`) **and** `var == val`. The script usually sets `var` to something else
so it fires once. Many of these vars are still `VAR_UNK_*`.

## Map grid (matrix)

`files/fielddata/mapmatrix/map_matrix/NNNN_NAME.bin`, binary, one per grid,
parsed in `src/map_matrix.c`:

```
u8 width, height, hasHeaders, hasAltitudes, nameLen; char name[nameLen];
[u16 mapHeaderIds[w*h]]   if hasHeaders   -> which MAP_* owns each cell
[u8  altitudes[w*h]]      if hasAltitudes
u16  landDataIds[w*h]                     -> block in the land-data archive
```

Several maps share one grid (the outdoor Johto/Kanto grid holds most routes and
towns; each cell's `mapHeaderIds` says which map you're in). No tool edits these
yet; `mapkit` will convert them to JSON ([DESIGN.md](DESIGN.md)).

## Terrain, collision, buildings, 3D models

All in `files/a/0/6/5`, one prebuilt 19.5 MB archive. Each block has
permissions/collision, building placements, an NSBMD model and height data
(header read by `ReadMapFileHeader` in `src/field/map_load_manager.c`).
There is no editor for these in the repo. Changing terrain needs an external
map editor or a new parser (listed as a later phase in the design).

## Adding a new map

Not covered yet. It touches `maps.h`, `map_headers.h`, and new banks appended to
`zone_event/meson.build`, `scr_seq/meson.build` and `NARC_msg.txt`. The per-map
layout in [DESIGN.md](DESIGN.md) is meant to make this one folder plus one index line.
