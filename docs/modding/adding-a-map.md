<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Adding a map, and changing one

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A map is a `MAP_*` id, a folder in `data/maps/`, a line in `data/maps/maps.txt`, and an
entry in `src/data/map_headers.h`. It draws a **layout** (its grid of terrain cells), which
can be shared with other maps or new. There is no "new map" command yet: this guide does
by hand what porymap's New Map does in pokeemerald.

The steps below were built together with `make release` for a house with its own layout
and terrain cell; see [Not verified](#not-verified).

| pokeemerald (porymap "New Map") | here |
|---|---|
| `data/maps/<Map>/map.json` | `data/maps/<Map>/map.json` (same keys where they exist; [maps-and-warps.md](maps-and-warps.md#map-header-top-of-mapjson)) |
| `data/maps/<Map>/scripts.inc`, `text.inc` | `scripts.pory`, `text.json`, `ids.h` ([SCRIPTING.md](SCRIPTING.md)) |
| `data/maps/map_groups.json` (generates `MAP_*`) | `include/constants/maps.h` (by hand) + `data/maps/maps.txt` (bank names) + `src/data/map_headers.h` |
| `data/layouts/layouts.json` + `data/layouts/<Layout>/` | `data/layouts/layouts.txt` + `data/layouts/<Layout>/layout.json` |
| tilesets (`data/tilesets/`) | terrain cells (`data/landdata/NNNN/`): collision, behaviors, props, a 3D model ([terrain.md](terrain.md)) |
| `region_map_section`, heal location | the same key; fly points in C ([town-map-and-fly.md](town-map-and-fly.md)) |

## What to change

| Step | File | Needed? |
|---|---|---|
| [1. Id](#1-the-id) | `include/constants/maps.h` | yes |
| [2. Folder](#2-the-folder) | `data/maps/<Map>/` | yes |
| [3. Banks](#3-the-banks-mapstxt) | `data/maps/maps.txt` | yes |
| [4. Header entry](#4-the-header-entry) | `src/data/map_headers.h` | yes |
| [5. Layout](#5-the-layout) | `data/layouts/`, `data/landdata/` | only for a new grid; indoor maps can share one |
| [6. Getting there](#6-getting-there) | warps in both maps | yes |
| [7. Section, Town Map, Fly](#7-name-town-map-and-fly) | `map.json`, [town-map-and-fly.md](town-map-and-fly.md) | a section yes; the rest optional |

## 1. The id

Add it **after the last map**, and raise `MAP_ID_MAX`:

```c
#define MAP_POKEMON_LEAGUE_ENTRANCE_WIFI_ROOM             539 // MAP_T10R0801
#define MAP_SEAFOAM_HOUSE                                 540
#define MAP_ID_MAX                                        541
```

Map ids are saved (the player's position, the Escape Rope spot, Town Map markings,
roamers' locations), so inserting in the middle moves every later map in old saves.

## 2. The folder

The folder name is the id in CamelCase, with `_` before a sub-map:
`MAP_SEAFOAM_HOUSE` → `data/maps/SeafoamHouse/`
([maps-and-warps.md](maps-and-warps.md#finding-a-maps-files)). Copy a map like the one you
want (a house, a cave) and change it:

**`map.json`**

```json
{
    "id": "MAP_SEAFOAM_HOUSE",
    "name": "SeafoamHouse",
    "code": "SEAFOAMHOUSE",
    "layout": "House1",
    "region_map_section": "MAPSEC_SEAFOAM_TOWN",
    "world_map_x": 34,
    "world_map_y": 15,
    ...
    "object_events": [
        { "local_id": "obj_SEAFOAMHOUSE_old_man", "graphics_id": "SPRITE_OLD_MAN", ...,
          "script": "SeafoamHouse_EventScript_OldMan", "flag": "FLAG_NOTHING" }
    ],
    "warp_events": [ { "x": 4, "y": 8, "elevation": 0, "dest_map": "MAP_SEAFOAM_TOWN", "dest_warp_id": 2 } ],
    "coord_events": [],
    "bg_events": []
}
```

- `id`, `name` (the folder) and `code` must be new. `code` is Game Freak's short name;
  for a new map anything unique works.
- `region_map_section` must not be `MAPSEC_MYSTERY_ZONE`: the Start menu doesn't open
  in that section. A new section: [town-map-and-fly.md](town-map-and-fly.md#adding-a-section).
- `world_map_x/y`: the Town Map square of an indoor map (Overworld cell). 0, 0 uses the
  last outdoor spot ([town-map-and-fly.md](town-map-and-fly.md#coordinates)).
- The other header keys: [maps-and-warps.md](maps-and-warps.md#map-header-top-of-mapjson).
  `area_data` and `move_model_bank` decide which textures and props the terrain and
  NPCs can use: keep a map whose layout you share.

**`scripts.pory`**

```
script SeafoamHouse_EventScript_OldMan {
    lockall
    faceplayer
    npcmsg("The sea was calm today.")
    waitbuttonpress
    closemessage
    releaseall
    end
}
```

**`text.json`**: the text bank. With all text inline in `scripts.pory`, it is just a key
(any 16-bit number) and no messages:

```json
{
  "key": 12345,
  "messages": []
}
```

**`ids.h`**: the script numbers (`_EV_<script>`, in the order scripts appear) and object ids:

```c
#ifndef SCR_SEQ_SEAFOAMHOUSE_H_
#define SCR_SEQ_SEAFOAMHOUSE_H_

#define _EV_SeafoamHouse_EventScript_OldMan 0

#define obj_SEAFOAMHOUSE_old_man 0

#endif // SCR_SEQ_SEAFOAMHOUSE_H_
```

`tools/mapkit/mapkit.sh pory sync SeafoamHouse` rewrites the `_EV_` lines when you add
scripts later. Objects and scripts in more detail: [npcs-and-scripts.md](npcs-and-scripts.md),
[scripting-basics.md](scripting-basics.md).

## 3. The banks: maps.txt

Each map has four files in the ROM: its events, scripts, map scripts and text. The
archives store them by position, in **file name order**, and `maps.txt` keeps their
names. A new map gets new names that sort after all existing ones, so nothing moves:

```
SeafoamHouse MAP_SEAFOAM_HOUSE events=491_SEAFOAMHOUSE scripts=scr_seq_0965_SEAFOAMHOUSE init=scr_seq_0966_SEAFOAMHOUSE_hdr text=msg_0829_SEAFOAMHOUSE
```

The numbers are the next free index of each archive. After a build, the counts are in the
generated `.naix` files:

```sh
grep -h _COUNT build/heartgold.us/files/fielddata/eventdata/zone_event.naix \
               build/heartgold.us/files/fielddata/script/scr_seq.naix \
               build/heartgold.us/files/msgdata/msg.naix
# zone_event_COUNT 491 -> events=491_...   scr_seq_COUNT 965 -> scripts=scr_seq_0965_..., init=scr_seq_0966_..._hdr
# msg_COUNT 829 -> text=msg_0829_...
```

- Keep the digit count (3 for events, 4 for the others), or `1000_X` sorts before `101_Y`.
- Another new bank (a phone contact's text in `NARC_msg.txt`, a second new map) takes a
  number too; use the counts from a build that has them.
- A map without text or scripts of its own can share another map's with `@Folder`
  (`text=@Everywhere`), as the unused maps do. It can't add text then.

The build turns `map.json` into the events file and the header, compiles `scripts.pory`,
and packs everything (`data/maps/meson.build`).

## 4. The header entry

`src/data/map_headers.h` lists every map in id order. Add yours at the end:

```c
    [MAP_POKEMON_LEAGUE_ENTRANCE_WIFI_ROOM] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_ENTRANCE_WIFI_ROOM.h"
    ,
    [MAP_SEAFOAM_HOUSE] =
#include "data/maps/header_MAP_SEAFOAM_HOUSE.h"
    ,
};
```

The build generates `header_MAP_SEAFOAM_HOUSE.h` from `map.json`. A missing entry builds
anyway (the array is just one shorter), but the game then reads every lookup of your map
as `MAP_NOTHING`.

## 5. The layout

**Sharing one.** Indoor maps usually do: `House1`-`House4`, `PokemonCenter_1F`,
`Pokemart`, `Gatehouse_EastWest`... Set `"layout"` and you are done. Warps and NPCs are
yours; collision and props belong to the shared cells, so don't change those for one map.

**A new one.**

1. Make `data/layouts/<Layout>/layout.json` ([maps-and-warps.md](maps-and-warps.md#map-grid-datalayouts)):
   ```json
   {
       "name": "m_seafoam_house_",
       "width": 1,
       "height": 1,
       "land_data": [
           [676]
       ]
   }
   ```
2. Add a line at the end of `data/layouts/layouts.txt`, with the next matrix number
   (`map_matrix_COUNT` in `build/heartgold.us/files/fielddata/mapmatrix/map_matrix.naix`):
   ```
   SeafoamHouse map_matrix_0288_SEAFOAMHOUSE
   ```
3. Each new cell is a folder `data/landdata/NNNN/` with the next number (folders must be
   numbered without gaps; there are 676, `0000`-`0675`). Start from a copy of a cell like it:
   ```sh
   cp -r data/landdata/0212 data/landdata/0676     # 0212 is House1's cell
   ```
   Then edit collision and behaviors (`tools/mapeditor/mapeditor.sh SeafoamHouse`), props
   (`props.json`) and the 3D model and heights ([terrain.md](terrain.md)).
4. `tools/mapkit/mapkit.sh format check` checks the layout and cells.

A new **outdoor** area on the Overworld isn't a new layout: it is cells of the
`Overworld` layout, with your map named in its `maps` grid. That grid is also the Town
Map's grid ([town-map-and-fly.md](town-map-and-fly.md#coordinates)); resizing it moves
squares that C tables hard-code, so prefer free cells inside the 47×17 grid.

## 6. Getting there

Warps are one-way: add a warp in the new map and one in the map it connects to, each
pointing at the other ([maps-and-warps.md](maps-and-warps.md#warps-warp_events)):

```sh
tools/mapkit/mapkit.sh warp link SeafoamTown:2 SeafoamHouse:0
tools/mapkit/mapkit.sh validate -a SeafoamHouse
```

A script can also move the player there: `warp(MAP_SEAFOAM_HOUSE, 0, 4, 7, DIR_NORTH)`
([script-commands.md](script-commands.md)).

## 7. Name, Town Map and Fly

- The popup and the name everywhere come from `region_map_section`; the popup frame from
  `area_icon` (none in buildings) — [town-map-and-fly.md](town-map-and-fly.md#popup-on-entry).
- A new town: a section, a Town Map place, and a fly point —
  [town-map-and-fly.md](town-map-and-fly.md).
- Wild Pokémon: `wild_encounters` ([wild-encounters.md](wild-encounters.md)). Weather and
  music: [weather.md](weather.md), [music.md](music.md).

## Changing a map

| To change | Edit | Note |
|---|---|---|
| music, weather, map type, battle background, bike / Fly / Escape Rope | `map.json` header keys | [maps-and-warps.md](maps-and-warps.md#map-header-top-of-mapjson) |
| NPCs, warps, signs, triggers | `map.json` events, `mapkit npc/warp` | [maps-and-warps.md](maps-and-warps.md), [npcs-and-scripts.md](npcs-and-scripts.md) |
| scripts and text | `scripts.pory`, `text.json` | [SCRIPTING.md](SCRIPTING.md) |
| the name it shows | its `region_map_section`, or the section's name in `msg_0279.json` (renames it for every map of that section) | [town-map-and-fly.md](town-map-and-fly.md#1-map-sections) |
| where it is on the Town Map | `world_map_x/y` (indoors), or the place's row in `sLocationSpecs` | [town-map-and-fly.md](town-map-and-fly.md#2-the-town-map) |
| its grid or which cells it uses | `data/layouts/<Layout>/layout.json` | shared layouts change every map using them |
| collision, behaviors, props, 3D terrain | `data/landdata/NNNN/` | cells can be shared; the map editor shows how many use one |
| the folder's name | rename the folder and its first word in `maps.txt` | the ROM doesn't change |
| a layout's name | `mapkit layouts rename OLD NEW` | updates every map using it |
| where Fly lands, or where you wake up after a blackout | `sSpawnPoints` in `src/spawn_warp.c` | [town-map-and-fly.md](town-map-and-fly.md#changing-a-fly-point) |

Don't renumber map ids or reorder `maps.txt` bank names: both are positions the ROM and
saves rely on.

**Removing a map**: see [removing-a-map.md](removing-a-map.md). **Renaming its banks**:
the build doesn't drop the old files from the archives it packs from a folder. Delete the
archives so they are rebuilt:

```sh
rm build/heartgold.us/files/fielddata/eventdata/zone_event.narc \
   build/heartgold.us/files/fielddata/script/scr_seq.narc \
   build/heartgold.us/files/msgdata/msg.narc \
   build/heartgold.us/files/fielddata/mapmatrix/map_matrix.narc
```

Without this the old map's banks stay in the ROM. (Seen while testing this guide: the
counts in the `.naix` files stayed one too high until the archives were deleted.)

## Not verified

- Built, not run in an emulator: the map, its own layout and copied terrain cell.
  Expected: entering by warp, the NPC talks, the name popup.
- An outdoor map in the `Overworld` layout's free cells, and resizing the Overworld.
