<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Map sections, the Town Map and Fly

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A **map section** (`MAPSEC_*`) is a named place: "Cherrygrove City", "Route 30".
Every map belongs to one. The name pops up when you enter, appears on the Town Map,
and is stored as a Pokémon's met location.

The **Town Map** is one screen in three places: the Pokégear's map card, the Town
Map item, and the Fly screen. It shows the Overworld at one tile per 32×32 cell.

**Fly points** are where Fly can take you. Each town has a flag that is set when you
visit it, a spot on the Town Map, and a landing tile. The same table also says where
you wake up after a blackout and where Teleport takes you.

| pokeemerald | here |
|---|---|
| `include/constants/region_map_sections.h` (`MAPSEC_*`) | `include/constants/map_sections.h` (`MAPSEC_*`, the same numbers are met locations) |
| map section names (`region_map_sections.json`, older `region_map_entries.h`) | `files/msgdata/msg/msg_0279.json`, message N = section N |
| region map section `x`, `y`, `width`, `height` | `sLocationSpecs` in `src/application/pokegear/map/pokegear_map.c`, one row **per map**, not per section ([2](#2-the-town-map)) |
| `map_name_popup.c`, popup theme per section | `src/field/draw_map_name.c`, frame chosen by each map's `area_icon` ([1](#popup-on-entry)) |
| `graphics/pokenav/region_map/map.png` + tilemap, porymap's region map editor | `pgmap_gra_00000010.png` + `pgmap_gra_00000011.NSCR`; no editor, `tools/townmap/townmap.py render` draws it ([3](#3-changing-the-town-map-picture)) |
| heal locations (`HEAL_LOCATION_*`, `heal_locations.json`): fly spot and respawn spot | `sSpawnPoints` in `src/spawn_warp.c` ([4](#4-fly-points)) |
| `sMapHealLocations` (which heal location a map section flies to) | `gMapFlypointParams` in `src/application/pokegear/map/pokegear_map_flypoints.c` |
| `FLAG_VISITED_*`, set by `setflag` in each town's `OnTransition` | `FLAG_SYS_FLYPOINT_*`, set by the engine on entering the town |

## 1. Map sections

Map sections are numbers from `include/constants/map_sections.h`, in three ranges:

| Range | What | Names in |
|---|---|---|
| 0-234 (`MAPSEC_MYSTERY_ZONE` ... `MAPSEC_CLIFF_EDGE_GATE`) | places in a game: 1-125 are Diamond/Pearl/Platinum's, 126 on are HGSS's (`MAPSEC_NEW_BARK_TOWN` = 126) | `msg_0279.json` |
| 2000-2014 (`METLOC_DAY_CARE_COUPLE` ...) | gift met locations ("Link trade", "Day-Care Couple") | `msg_0281.json` |
| 3000-3076 (`METLOC_LOVELY_PLACE` ...) | event met locations ("Pokémon Movie 08") | `msg_0280.json` |

`src/map_section.c` splits a number into range and index; `BufferLandmarkName`
(`src/message_format.c`) picks the bank. Only the first range can be given to a map.

A map's section is `region_map_section` in its `map.json`. All maps of a town share
one: `Cherrygrove`, `Cherrygrove_Pokecenter_1F` and `Cherrygrove_Pokemart` are all
`MAPSEC_CHERRYGROVE_CITY`. On the Overworld, the section of the cell you stand in
comes from the layout's `maps` grid, which names a map for each cell
([maps-and-warps.md](maps-and-warps.md#map-grid-datalayouts)).

What reads the section:

| Use | Where |
|---|---|
| the name popup on entry | `src/field/draw_map_name.c` |
| the name on the Town Map, the phone ("I'm on Route 30"), radio shows, the Pokédex area screen | `MapID_GetLandmarkName` (`src/map_landmark_name.c`) and `BufferLandmarkName` |
| met location of caught, hatched and gift Pokémon | `src/battle/battle_setup.c`, `src/hatch_egg_task.c`, `src/scrcmd_party.c` |
| following Pokémon: 30 rules per section (what it says, where) | `files/a/2/2/0`, member section + 1 (`src/field/follow_mon_interaction.c`) |
| the Start menu: it **doesn't open** in `MAPSEC_MYSTERY_ZONE` (0), so give every playable map a real section | `FieldSystem_MapIsNotMysteryZone` (`src/start_menu.c`), checked in `src/field/field_control.c` |

### Renaming a section

Edit its message in `files/msgdata/msg/msg_0279.json`; message N is section N. The new
name shows everywhere at once, including on Pokémon already caught there.

### Adding a section

1. Add the constant after the last one, in `include/constants/map_sections.h`:
   ```c
   #define MAPSEC_CLIFF_EDGE_GATE  234
   #define MAPSEC_SEAFOAM_TOWN     235
   ```
   Stay below 2000, where the gift range starts. Don't renumber existing sections:
   they are saved in every Pokémon's met location.
2. Add its name as the **last** message of `msg_0279.json`:
   ```json
   { "id": "msg_0279_00235", "en_US": "Seafoam Town" }
   ```
3. Give it following-Pokémon rules. The game reads member `section + 1` of
   `files/a/2/2/0` with no bounds check, so a section past the end reads the wrong data.
   This appends one empty member (no special rules) per new section:
   ```sh
   python3 tools/townmap/townmap.py follow-rules        # 1 section; follow-rules 3 for three
   ```
4. Set `"region_map_section": "MAPSEC_SEAFOAM_TOWN"` in the maps that belong to it.
5. To show it on the Town Map, give one of its maps a location ([2](#adding-a-place-to-the-town-map)).

Steps 1-4 were built with `make release`.

### Popup on entry

The name slides in at the top of the screen (`FieldSystem_DrawMapNameAnimation`):

- after a warp, Fly or a fade back to the field;
- when you walk across a cell border into a different section.

It doesn't show in buildings (`MAP_TYPE_INTERIOR` and `MAP_TYPE_POKEMON_CENTER`)
or when the map's `area_icon` is 0. Otherwise `area_icon` picks the frame:
`files/data/gs_areawindow/areawindow_<area_icon - 1>.png`.

| `area_icon` | Used by |
|---|---|
| 1 | most towns and cities (Blackthorn, Bellchime Trail...) |
| 2 | seaside towns (Azalea, Cinnabar) |
| 3 | land routes, Indigo Plateau, Mt. Silver |
| 4 | caves and towers |
| 5 | forests (Ilex, Viridian) |
| 6 | sea routes |
| 7 | parks (National Park, Pal Park) |
| 8 | Lake of Rage |
| 9 | buildings (never shown, since buildings skip the popup) |

## 2. The Town Map

### Coordinates

A Town Map square is one cell of the `Overworld` layout (47×17 cells,
`data/layouts/Overworld/layout.json`). The picture has two extra rows at the top, so
cell (x, y) is tile (x, y + 2) of the tilemap, and the tables don't agree on which
row number they use:

| Uses Overworld cell rows | Uses tile rows (cell + 2) |
|---|---|
| fly point icons (`gMapFlypointParams`), `Pokegear_RegionFromCoords`, `world_map_x/y` | places (`sLocationSpecs`), the cursor and player icon (the code adds 2), the tilemap, `PokegearMap_SelectLocationAtCoord` |

Cherrygrove's cells are x 16-17, y 12: its fly point says `16, 12`, its place says
`.x = 16, .y = 14`.

The player's square:

- on the Overworld: the cell the player stands in;
- elsewhere: the map's `world_map_x` / `world_map_y` from `map.json`, or, when both
  are 0, the cell of the last Overworld spot (the "special spawn" saved on leaving the
  Overworld, `src/gear_phone_ring_manager.c`). The Pokédex area screen uses the same
  rule (`src/start_menu.c`).

So an indoor map shows up in the right place if `world_map_x/y` names its town's cell,
or if they are 0 and the only way in is from that town.

To read squares off the picture:

```sh
python3 tools/townmap/townmap.py render townmap.png     # grid; cell rows on the left, tile rows (t) on the right
```

### Regions and Kanto

`setpokegearmapunlocklevel(n)` sets how much of the map is shown (saved in the
Pokégear data):

| Level | Shows | Set by |
|---|---|---|
| 0 | Johto (x ≤ 21) and Mt. Silver | New Game |
| 1 | adds the Indigo Plateau column | `Route27_OnTransition`, until Kanto is reached |
| 2 | all of Kanto | `SsAquaVermilionPortExterior_OnTransition` |

The region is decided from coordinates, in C: `Pokegear_RegionFromCoords`
(`src/application/pokegear/main/pokegear_app_ui.c`, cell rows) says x > 21 is Kanto,
except Mt. Silver (25, 8) and Indigo Plateau / Victory Road (column 28). Fly only
offers points in the region you are in, plus Indigo Plateau and Victory Road from
anywhere (`PokegearMap_IsFlyDestinationReachable`). A layout that moves the border
needs these functions changed too, and the `x >= 22` and Mt. Silver `(25, 10)` checks
(tile rows) in `PokegearMap_SelectLocationAtCoord` (`pokegear_map_view.c`).

### The location table

The squares you can point at are `sLocationSpecs` in
`src/application/pokegear/map/pokegear_map.c`, one entry per place (100 entries):

```c
{
 .mapId = MAP_ICE_PATH_1F,
 .x = 21, .y = 6, .width = 1, .height = 1,       // squares it covers (tile rows: cell 21, 4)
 .objXoffset = 0, .objYoffset = 0,                // marking icon offset from the square's center, pixels (×2 zoomed in)
 .flavorText = msg_0273_00055,                    // "A cave that connects Route 44 to..."
 .subBg3BlockID = 0,                              // picture on the info panel, 0 = none
 .tilemapCopyRectSrcX = 5, .tilemapCopyRectSrcY = 40,
 .tilemapCopyRectWidth = 1, .tilemapCopyRectHeight = 1,  // highlight drawn over it
},
```

| Field | Meaning |
|---|---|
| `mapId` | the place. Its **name** is its map's section (`msg_0279`), its phone-rematch icon comes from phone book entries on this map, and markings are saved by this map id |
| `x`, `y`, `width`, `height` | squares, in **tile rows** (Overworld cell y + 2). The first entry that contains the cursor wins |
| `flavorText` | description under the name, from `files/msgdata/msg/msg_0273.json` |
| `subBg3BlockID` | 1-20: a 7×7-tile picture from `pgmap_gra_00000012.png` / `00000013.NSCR` (block N - 1, 4 per row) on the touch screen panel |
| `tilemapCopyRect*` | the orange highlight: a rectangle copied from the Town Map tilemap (the shapes from row 40 down) to (`x`, `y`), or to (`x` - 1, `y` - 1) when it is 9 tiles or more |
| `unk_8` ... `unk_B` | unused |

Hard-coded exceptions (`pokegear_map_view.c`): Routes 47 and 48 and the Safari Zone
Gate are hidden until `canSeeSafariZone` (always TRUE in this version); the Sinjoh
Ruins and S.S. Aqua entries only appear while you are on those maps, and can't be
marked (`PokegearMap_ShouldLocationBeHidden`, `PokegearMap_CanMarkLocation`).

### Moving or editing a place

Change its row: `x`/`y`/`width`/`height` to move where it can be selected, the
highlight rectangle to match, `flavorText` for the description (edit the text in
`msg_0273.json`, or add a message at the end and point to it). The name follows the
map's section, so rename the section to rename the place.

### Adding a place to the Town Map

The table is full: `PGMAP_NUM_LOCATIONS` is 100 and so is the number of entries.
Two ways:

- **Replace an entry** your hack doesn't need (a place you removed). Nothing else
  changes. Saved markings are keyed by map id, so markings on the old place are
  ignored.
- **Raise the count.** `PGMAP_NUM_LOCATIONS`
  (`include/application/pokegear/map/pokegear_map_internal.h`) also sizes the
  marking sprites, so `PGMAP_SPRITE_MAX` grows with it, and the Pokégear allows 128
  sprites (`sPokegearObjResSpecs`, `src/application/pokegear/main/pokegear_sprites.c`):
  11 + the count must stay under that. Markings are saved in a fixed
  `MapMarkingsSave list[100]` (`include/map_markings_ram.h`), but
  `pokegear_map_markings.c` loops up to `PGMAP_NUM_LOCATIONS` over both the save list
  and `mapMarkingsHeap[100]`. Cap those loops at 100 (or grow the save, which breaks
  old saves; [save-compatibility.md](save-compatibility.md)). Not tried.

Then add the row, a flavor text at the end of `msg_0273.json`, and if you want a
highlight, draw its shape into the tilemap below row 40 ([3](#3-changing-the-town-map-picture)).

## 3. Changing the Town Map picture

Files in `files/application/pokegear/map/pgmap_gra/`:

| File | Holds | Edit with |
|---|---|---|
| `pgmap_gra_00000010.png` | the tiles: 8bpp, 64×12 tiles (768) | any editor that keeps indexed color (Aseprite, GIMP in indexed mode) |
| `pgmap_gra_00000011.NSCR` | the tilemap: 64×64 tiles, which tile goes where (with flips) | a DS tilemap editor such as NitroPaint; binary |
| `pgmap_gra_00000020.NCLR`-`00000025.NCLR` | the colors, one file per Pokégear skin | NitroPaint; binary |

The PNG's palette matches `00000020.NCLR`, but the game uses the NCLR files. Draw only
with the colors already in the PNG (indices 0-49), or change all six NCLR files the
same way.

Tiles are shared: a sea tile is used in dozens of places, so painting over it changes
all of them. To change one spot, draw a new tile in an unused slot of the PNG and
point that tilemap entry at it.

`python3 tools/townmap/townmap.py render --sheet sheet.png` draws the whole tilemap with
tile numbers. What is where:

| Tiles (x, y) | What | Copied by |
|---|---|---|
| 0-46, 0-19 | the map (row = Overworld y + 2) | `PokegearMap_DrawMapTilemap` |
| 48-53, 0-19 | Johto's east edge with Kanto hidden (unlock level 0), copied to x 22 | same |
| 54-56, 0-19 | the edge at unlock level 1, copied to x 29 | same |
| 0-40, 20-32 | grey "not visited" towns, copied over each fly point not yet visited | same, with the `patch*` fields of the fly point table |
| 41-52, 20-32 | Cianwood's corner, three versions (visited, not, Safari Zone shown), copied to (1, 9) | same |
| 55-57, 20-23 / 24-26 | Sinjoh Ruins and S.S. Aqua, shown while on them | same |
| from row 40 | orange highlight shapes, one per place | `PokegearMap_HighlightSelectedLocation` |

A changed coast or a new town needs the map area, then any patch that is copied over
that spot (grey version, highlight) redrawn to match.

## 4. Fly points

Two tables make a fly point.

**Spawn points** (`sSpawnPoints`, `src/spawn_warp.c`, 30 entries) are the
equivalent of pokeemerald's heal locations:

```c
//  flag index           blackout fly  unused  map where you wake up       x  y   fly: map         x    y    special spawn: map  x    y
{ FLYPOINT_CHERRYGROVE,  TRUE,    TRUE, 0,     MAP_CHERRYGROVE_POKECENTER_1F, 8, 13, MAP_CHERRYGROVE, 564, 392, MAP_CHERRYGROVE,   564, 392 },
```

| Field | Meaning |
|---|---|
| `flypoint` | which flag is set on visiting: `FLAG_SYS_FLYPOINT_PALLET + flypoint` (0x9B0 + n, at most 37) |
| `isBlackoutSpawn` | entering `deathMap` makes this the place you wake up after a blackout, and where Teleport goes |
| `isFlyPoint` | entering `flyMap` sets the flag |
| `deathMap`, `deathX`, `deathY` | where you wake up (facing north) |
| `flyMap`, `flyX`, `flyY` | where Fly and Teleport land (facing south); global Overworld tile coordinates, like `map.json` events |
| `specialMap`, `specialX`, `specialY` | saved as the "special spawn" on landing: where Escape Rope and Dig lead, and the Town Map position inside buildings with no `world_map_x/y` |

The spawn id saved for blackouts is the row number + 1, so add rows at the end.

**Fly map icons** (`gMapFlypointParams`, `pokegear_map_flypoints.c`, 27 entries):

```c
//  name map        warp map        flag index           grey  x   y   gx  gy  w  h  gw gh ox oy
{ MAP_CHERRYGROVE, MAP_CHERRYGROVE, FLYPOINT_CHERRYGROVE, 11,  16, 12, 15, 24, 2, 1, 4, 3, 1, 1 },
```

| Field | Meaning |
|---|---|
| `mapIDforName` | the place whose name and highlight show when the cursor is on it |
| `mapIDforWarp` | the map passed to Fly; it must be some spawn point's `flyMap` (`GetSpawnIdForFlyMap`, an assert otherwise) |
| `flypoint` | the flag: the icon shows and can be picked once it is set |
| `unk_05` | 0xFF = no grey "not visited" patch; any other value draws one |
| `x`, `y`, `width`, `height` | squares the icon covers (Overworld cells) |
| `patchSrcX/Y`, `patchWidth/Height`, `patchOffsetX/Y` | the grey patch: copied from tilemap (`patchSrcX`, `patchSrcY`) to (`x` - `patchOffsetX`, `y` - `patchOffsetY` + 2) while the town is unvisited |

How Fly runs: the field move checks `allow_fly` of the current map
(`src/field_move.c`), the Fly screen (`FlyMap_*`, the same app as the Town Map)
returns `mapIDforWarp`, and `src/field_warp_state.c` finds the spawn point whose
`flyMap` matches and lands on `flyX`, `flyY`.

**Flags.** Entering a spawn point's `flyMap` sets its flag (`FlypointFlagAction`,
called after every warp in `src/field_warp_state.c`). Some are set by scripts instead:
Battle Frontier (`FLAG_SYS_FLYPOINT_UNION_CAVE`, see below), Pokéathlon Dome,
Victory Road gate and the Vermilion port. Scripts can also give one early with
`setflag(FLAG_SYS_FLYPOINT_...)`.

**The names don't match the towns for 15-18 and 27.** The flag indices are right; the
constant names are not:

| Index | Constant | Actually |
|---|---|---|
| 15 | `FLYPOINT_GOLDENROD` | Cianwood (also `canFlyToGoldenrod`, which draws Cianwood's corner) |
| 16 | `FLYPOINT_ECRUTEAK` | Goldenrod |
| 17 | `FLYPOINT_OLIVINE` | Olivine |
| 18 | `FLYPOINT_CIANWOOD` | Ecruteak |
| 27 | `FLYPOINT_UNION_CAVE` | Battle Frontier (also unlocks Frontier pages in the Pal Pad and the VS Recorder) |

Radio and phone code checks some of these by the wrong name (`commercials.c`,
`that_town_these_people.c`), so check the table before using one. Union Cave, Mt.
Moon and Rock Tunnel rows are blackout spawns only (the Route 32, 3 and 10 Pokémon
Centers); their `isFlyPoint` is FALSE.

### Changing a fly point

- **Landing spot:** `flyX`, `flyY` (and usually `specialX`, `specialY`) in
  `sSpawnPoints`. Global tile coordinates: `mapkit show <Map>` prints events this
  way, so a warp tile next to the spot is a good reference.
- **Blackout spot:** `deathMap`, `deathX`, `deathY`.
- **Icon position:** `x`, `y`, `width`, `height` in `gMapFlypointParams`, and the
  grey patch if it has one.
- **Unlocking it another way:** set `isFlyPoint` to FALSE and `setflag` the flag from
  a script.

### Adding a fly point

For a new town on the Overworld, with its Pokémon Center:

1. **Pick a flag index.** Free ones (nothing sets or checks them):
   23, 24, 26, 28, 32, 34 ([unknown-flags-vars.md](unknown-flags-vars.md)). 25 and
   29 are used. Optionally name it in `include/constants/flypoints.h` and
   `include/constants/flags.h`.
2. **Spawn point:** add a row at the end of `sSpawnPoints` and raise
   `NUM_SPAWN_POINTS`:
   ```c
   #define NUM_SPAWN_POINTS 31
   ...
   { FLYPOINT_UNK23, TRUE, TRUE, 0, MAP_SEAFOAM_TOWN_POKECENTER_1F, 8, 13, MAP_SEAFOAM_TOWN, 1100, 480, MAP_SEAFOAM_TOWN, 1100, 480 },
   ```
3. **Fly map icon:** add a row at the end of `gMapFlypointParams` and raise
   `PGMAP_NUM_FLYPOINTS` in `pokegear_map_internal.h`:
   ```c
   #define PGMAP_NUM_FLYPOINTS 28
   ...
   { MAP_SEAFOAM_TOWN, MAP_SEAFOAM_TOWN, FLYPOINT_UNK23, 0xFF, 34, 15, 0, 0, 1, 1, 0, 0, 0, 0 },
   ```
4. **Sprite count:** the Fly screen makes exactly 42 sprites (15 fixed + 27 icons).
   In `src/application/pokegear/map/fly_map_gfx.c`, change
   `PokegearObjectsManager_Create(42, mapApp->heapID)` to
   `PokegearObjectsManager_Create(PGMAP_SPRITE_FLY_MENU_WARPS_END, mapApp->heapID)`.
   Without this, the new icon is written past the end of the sprite list.
5. **Town Map:** a location entry for the town ([2](#adding-a-place-to-the-town-map)),
   so its name shows, and its picture on the map ([3](#3-changing-the-town-map-picture)).
6. If the town is east of x = 21 or the regions change, see
   [Regions and Kanto](#regions-and-kanto).

Steps 1-4 were built with `make release`. **Saves:** the flags already exist in the
save, and new spawn ids come after the old ones, so old saves keep working.

## Not verified

- Built, not run in an emulator: a new section with its name and follow rules, a new
  fly point (spawn point, icon, sprite count). Expected but not seen: the popup, the
  icon on the Fly screen, landing.
- Raising `PGMAP_NUM_LOCATIONS` (not built).
- Editing the NSCR and NCLR files with NitroPaint.
