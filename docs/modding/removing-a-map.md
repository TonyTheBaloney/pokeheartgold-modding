<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Removing a map

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The reverse of [adding-a-map.md](adding-a-map.md). A map is an id, a folder, a line in
`data/maps/maps.txt` and an entry in `src/data/map_headers.h`, and the id and the banks are
**positions**: the map id is saved and compared in C, and each bank is a file in an
archive packed in name order. Taking one out of the middle moves everything after it.
So for a map of the original game, don't delete it: cut it off, or reuse its slot.

| You want to | Do | Saves | Section |
|---|---|---|---|
| make a map unreachable | remove every way in, keep the map | kept | [1](#1-cut-it-off) |
| also drop its content | stub its events, scripts and text | kept | [2](#2-empty-it) |
| put a different map there | reuse the id and folder | kept, if no one is saved inside | [3](#3-reuse-the-slot) |
| delete a map you added | delete it, if it is the last id | kept, if no one is saved inside | [4](#4-delete-a-map-you-added) |
| delete an original map | — renumbers ids and banks | broken | [Why not](#why-not-delete-an-original-map) |

## 1. Cut it off

Find every reference to its id and its folder name:

```sh
grep -rnw MAP_VIOLET_GYM --exclude-dir=build --exclude-dir=.git --exclude-dir=docs .
tools/mapkit/mapkit.sh refs MAP_VIOLET_GYM     # map data only
```

Where map ids show up:

| Where | What | Change |
|---|---|---|
| `data/maps/*/map.json` | other maps' `warp_events` (`dest_map`) | remove the warp, or point it elsewhere: `mapkit warp` ([maps-and-warps.md](maps-and-warps.md#warps-warp_events)) |
| `data/maps/*/scripts.pory`, `files/fielddata/script/scr_seq/*.s` | `warp(MAP_..., ...)` and map checks in scripts | the script |
| `data/layouts/*/layout.json` | the `maps` grid (Overworld, Safari Zone) | give its cells to a neighbor ([maps-and-warps.md](maps-and-warps.md#map-grid-datalayouts)) |
| `src/spawn_warp.c` | `sSpawnPoints`: Fly and blackout targets | [town-map-and-fly.md](town-map-and-fly.md#changing-a-fly-point) |
| `src/field_roamer.c` | roamers' routes | [roamers.md](roamers.md) |
| `src/application/pokedex/`, `src/application/pokegear/map/` | area map and Town Map tables | [pokedex.md](pokedex.md), [town-map-and-fly.md](town-map-and-fly.md) |
| `files/tel/pmtel_book.json` | a phone contact's map | [phone.md](phone.md) |
| `files/data/photo_data.json`, other `src/` files | photo spots, special cases | case by case |

Then check the warps:

```sh
tools/mapkit/mapkit.sh validate -a
```

**Keep a warp out of the map.** A save made inside it still loads there; with no way
out the player is stuck. Leaving the map's own exit warp costs nothing.

## 2. Empty it

To drop the NPCs, scripts and text but keep the files where they are, stub them, as the
original game does for its unused maps:

- `map.json`: empty `object_events`, `coord_events` and `bg_events`. Keep one entry in
  `warp_events` (the exit, see above), and keep the header keys.
- `scripts.pory`: one script that just ends, and empty map scripts (the original
  game's empty maps, such as `Union_Cave_1F`, have exactly this):
  ```
  script Violet_Gym_EventScript_Unused {
      end
  }

  mapscripts Violet_Gym_MapScripts {
  }
  ```
  and `mapkit pory sync Violet_Gym` to rewrite `ids.h`.
- `text.json`: keep the `key`, empty `messages`.

Keep the bank names in `maps.txt`. Changing them to `@Everywhere` (sharing another
map's files, like `RuinsOfAlph_Unused`) takes this map's files out of the archives, and
every later file moves ([why that matters](#why-not-delete-an-original-map)).

The layout and terrain cells can stay: unused cells are only space in the ROM. A layout
used by other maps must stay.

## 3. Reuse the slot

To replace a map, keep its id and change the rest:

- Rewrite `map.json`, `scripts.pory`, `text.json` as for a new map
  ([adding-a-map.md](adding-a-map.md#2-the-folder)). Keep `"id"`.
- Rename the folder: the folder and the first word of its `maps.txt` line. The ROM
  doesn't change.
- Renaming the constant (`MAP_VIOLET_GYM` → `MAP_MY_MAP`, same number): change it in
  `include/constants/maps.h`, `maps.txt`, the `map_headers.h` entry (both the `[MAP_...]`
  and the `header_MAP_....h` include), the map's `"id"`, and every reference from the
  grep in [1](#1-cut-it-off).
- Keep the bank names in `maps.txt`.

A save made inside the old map loads at the same coordinates in the new one, which may
be inside a wall.

## 4. Delete a map you added

Only for maps **after the last original id** (`MAP_POKEMON_LEAGUE_ENTRANCE_WIFI_ROOM`,
539) whose banks you numbered after all original ones, as
[adding-a-map.md](adding-a-map.md#3-the-banks-mapstxt) does. Work backwards through
that guide:

1. Remove every reference ([1](#1-cut-it-off)).
2. Delete `data/maps/<Map>/` and its line in `maps.txt`.
3. Delete its entry in `src/data/map_headers.h`.
4. In `include/constants/maps.h`, delete the `#define`, and if it was the last id,
   lower `MAP_ID_MAX` by one. If it **wasn't** the last id, don't delete it: the
   later ids would have to move down, or the header array keeps a gap of zeros that
   the game reads as a map whose banks are file 0 of each archive. Stub it
   ([2](#2-empty-it)) instead.
5. Its own layout: delete `data/layouts/<Layout>/` and its `layouts.txt` line. Its own
   terrain cells: delete them only if they are the highest numbers
   (`data/landdata/` must stay numbered without gaps) and no other map uses them (the
   map editor shows how many maps use a cell). Otherwise leave them.
6. The build doesn't drop old files from the archives it packs from a folder. Delete
   them so they are rebuilt:
   ```sh
   rm build/heartgold.us/files/fielddata/eventdata/zone_event.narc \
      build/heartgold.us/files/fielddata/script/scr_seq.narc \
      build/heartgold.us/files/msgdata/msg.narc \
      build/heartgold.us/files/fielddata/mapmatrix/map_matrix.narc
   ```
   then build. The `_COUNT` lines in the `.naix` files
   ([adding-a-map.md](adding-a-map.md#3-the-banks-mapstxt)) should be one lower.
7. `tools/mapkit/mapkit.sh validate -a`.

If you delete one of two maps you added, the other one's banks move down by one. That is
fine: everything refers to them by name.

## Why not delete an original map

- **Map ids are saved**: the player's position, the Escape Rope spot, Town Map markings,
  roamer locations. Removing an id moves every later map, so old saves load the wrong
  maps.
- **C compares ranges of ids**, for example `MAP_ICE_PATH_B1F`..`MAP_ICE_PATH_B3F` in
  `pokedex_area_sprites.c`. These depend on the order, not just the names.
- **Banks are positions.** Code that names a bank (`msg_0550_T21` in a map header,
  `scr_seq_0003_bin` in `script_manager.c`) follows when files move, but some code uses
  the number: `NewMsgDataFromNarc(..., NARC_msgdata_msg, 723, ...)` in
  `src/field/scrcmd_message.c`, also `237` (`scrcmd_pokemon_misc.c`) and `0x1b8`
  (`credits.c`). Dropping an original text bank before one of these shows the wrong
  text there. Packed data files may hold more such numbers.

## Not verified

- None of these steps was built for this guide. The archive deletion in step 4.6 was
  seen while testing [adding-a-map.md](adding-a-map.md#changing-a-map).
- The list of places that reference map ids comes from a grep for a few maps; a map
  you remove may also be named somewhere else. The grep in [1](#1-cut-it-off) is the
  check.
