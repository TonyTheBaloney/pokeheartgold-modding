<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21 -->

# Design: per-map data and the `mapkit` tool

> AI-generated, local to this fork. Do not upstream.

## Goal

Make maps, events, NPCs, warps, wild data and species data editable by name,
in one place per thing, with a tool that can parse, validate and change them,
**without breaking the matching build**: before any mod, the migrated tree must
still produce the retail ROM, byte for byte.

## Where things were (before the migration)

One map's data is split across four places, keyed by bank numbers:

| What | File today (Cherrygrove, `MAP_CHERRYGROVE`, code `T21`) |
|---|---|
| Header (music, weather, banks, flags) | `src/data/map_headers.h`, entry `[MAP_CHERRYGROVE]` |
| Events: NPCs, warps, signs, triggers | `files/fielddata/eventdata/zone_event/064_T21.json` |
| Scripts | `files/fielddata/script/scr_seq/scr_seq_0850_T21.s` |
| Init/level scripts | `files/fielddata/script/scr_seq/scr_seq_0623_T21_hdr.s` |
| Script and object IDs | `files/fielddata/script/scr_seq/event_T21.h` |
| Text | `files/msgdata/msg/msg_NNNN_T21.json` |
| Wild encounters | `files/fielddata/encountdata/gs_enc_data.json` (position in array) + `include/encounter_tables_narc.h` |
| Map grid (matrix) | `files/fielddata/mapmatrix/map_matrix/NNNN_*.bin` (binary) |
| Terrain, collision, 3D model | `files/a/0/6/5` (one 19.5 MB prebuilt NARC) |

Measured facts that shape the design (from `map_headers.h`, 540 maps):

- Scripts, header scripts, text and events are **one-to-one with maps**, except
  the shared placeholders (`EVERYWHERE` scripts/text, `DUMMY` events) used by
  unused maps.
- Map matrices **are shared** (280 distinct; one is used by 97 maps). So the grid
  is a *layout* that maps point to, as in pokeemerald.
- Wild tables are one-to-one with maps (136 tables; 405 maps have none).
- Every bank is identified by its position in a NARC. Positions come from the
  number in the file name (`scr_seq_0850_…`, `064_T21`, `msg_0542_…`) and from
  file lists in `meson.build` / `NARC_msg.txt`.

## Target layout (pokeemerald style)

The layout follows pret/pokeemerald so it reads like the other pret repos.
Where the DS forces a difference, it's noted.

```
data/
  maps/
    maps.txt                 index of migrated maps (pokeemerald: map_groups.json)
    meson.build              reads maps.txt; regenerates/copies files for the build
    Cherrygrove/
      map.json               header fields + object/warp/coord/bg events
      scripts.inc            event scripts
      map_scripts.inc        on-load/on-transition/on-frame scripts (separate binary on DS)
      text.json              messages (msgenc JSON; DS text isn't .inc)
      ids.h                  script and object id defines (was event_T21.h)
    Cherrygrove_Pokecenter_1F/
      ...
  layouts/                   (later) map grids, pokeemerald's data/layouts
files/fielddata/encountdata/gs_enc_data.json   wild data stays central, like
                                               pokeemerald's src/data/wild_encounters.json
```

Folder names are CamelCase from the `MAP_*` constant, with `_` before a sub-map
and a floor: `MAP_CHERRYGROVE_POKECENTER_1F` -> `Cherrygrove_Pokecenter_1F`,
`MAP_ROUTE_29` -> `Route29`.

### map.json

Top-level keys follow pokeemerald (`id`, `name`, `layout`, `music_*`,
`region_map_section`, `weather`, `map_type`, `battle_scene`, `allow_cycling`,
`allow_escaping`, `allow_running`, ...), plus DS fields (`code`, `camera_type`,
`follow_mode`, `area_icon`, `mom_call_intro`, `allow_fly`, call/radio flags,
`wild_encounters`). The four bank fields aren't stored; they follow from
`maps.txt`. The C field names are in `HEADER_KEYS` in `tools/mapkit/mapkit/layout.py`.

Events use pokeemerald's section and field names:

| pokeemerald key | DS template field | Notes |
|---|---|---|
| `object_events[].local_id` | `id` | `obj_T21_*`, defined in `ids.h` |
| `graphics_id` | `spriteId` | `SPRITE_*` |
| `x`, `y`, `elevation` | `x`, `z`, `y` | global tiles; DS calls the north-south axis z |
| `movement_type`, `movement_range_x/y` | `movement`, `xRange`/`yRange` | `MOVEMENT_TYPE_*` |
| `facing_dir` | `facingDirection` | DS only (pokeemerald folds facing into the movement type) |
| `trainer_type`, `trainer_sight_or_param0`, `param1`, `param2` | `type`, `param0..2` | `OBJECT_TYPE_*` |
| `script`, `flag` | `scriptId`, `eventFlag` | |
| `warp_events[].dest_map`, `dest_warp_id` | `header`, `anchor` | |
| `coord_events[].width`, `height`, `var`, `var_value` | `w`, `h`, `var`, `val` | |
| `bg_events[].type`, `player_facing_dir` | `type`, `dir` | `BG_TYPE_*`, `BG_DIR_*` |

### Why bank numbers stay explicit

The ROM stores banks by position, and the `.naix` constants come from file
names. `maps.txt` keeps each map's original base names:

```
Cherrygrove MAP_CHERRYGROVE events=064_T21 scripts=scr_seq_0850_T21 init=scr_seq_0623_T21_hdr text=msg_0550_T21
```

Renaming or moving a folder never changes the ROM. A new map gets new names
appended at the end.

## How the build uses it

The existing pipeline stays. `data/maps/meson.build` runs before `files/` and,
for each line of `maps.txt`:

```
map.json        --mapkit gen-events-->  build/.../data/maps/064_T21.json  -> zone_event.narc
map.json        --mapkit gen-header-->  build/.../data/maps/header_MAP_CHERRYGROVE.h
                                        (#included in place of the entry in src/data/map_headers.h)
scripts.inc     --copy-->               scr_seq_0850_T21.s       -> scr_seq.narc
map_scripts.inc --copy-->               scr_seq_0623_T21_hdr.s   -> scr_seq.narc
text.json       --copy-->               msg_0550_T21.json        -> msg.narc
```

`files/.../zone_event/meson.build`, `scr_seq/meson.build` and the msg list skip
migrated maps and take these outputs instead. A bank written `@Folder` in
`maps.txt` belongs to that folder (the lowest map id using a shared bank owns it);
only the owner builds it. `data/` is on every include path, so all tools include
`"maps/<MapName>/ids.h"` (the Metrowerks tools ignore `-I../..`).

**Matching invariant:** for the unmodified tree, every generated file produces the
same bytes as the file it replaces. Checked by the four `meson test` checksums for
HG and SS after every migration (and the generated zone_event JSON is compared to
the original).

## Scripts and events

### Named script references

In `map.json`, `"script"` can be a script **label**, as in pokeemerald:

```json
"script": "Cherrygrove_EventScript_MysticWaterMan"
```

`ids.h` defines `_EV_<label>` as the label's index in the `ScrDef` table (true
for all 451 existing headers), and the build turns a bare label into
`_EV_<label> + 1`. `std_*` constants, numbers and expressions pass through.

`mapkit script rename` renames a label in `scripts.inc`, `map_scripts.inc`,
`ids.h` and `map.json` at once; `mapkit script add` appends a script, its
`ScrDef` entry and its `_EV_` define. Script labels follow pokeemerald:
`Cherrygrove_EventScript_*`, `Cherrygrove_OnTransition`. Internal jump labels
(`_005F`) can be renamed freely.

Not done yet: generating the `ScrDef` table and the `_EV_` block of `ids.h`
from the labels instead of keeping them by hand.

### Text

`text.json` keeps the msgenc JSON format. Possible later: map-scoped message
names (`Cherrygrove_Text_GuideGentIntro`) instead of `msg_0550_T21_00020`.

### Script parser

`mapkit` builds a command table from `asm/macros/script.inc` (name, arguments,
command ID, which arguments are jump targets). `show` lists each script's flags,
vars and text, following jumps; `validate` reports unknown commands, undefined
labels, text not in the bank and undefined symbols. A higher-level script
language (poryscript style) could sit on this parser later.

## Events, NPCs and warps

Constants in `include/constants/map_object.h`: `MOVEMENT_TYPE_*` (57 entries of
`gMapObjectMovementCallbacks`) and `OBJECT_TYPE_*`. All event files use names
instead of numbers.

### Validation (`mapkit validate`)

- every warp's destination map exists and has that warp index; one-way warps noted
- objects/bgs/coords sit inside the map grid
- each events binary stays under the engine's 0x800-byte buffer (`src/map_events.c`)
- object ids unique per map; flags, vars, sprites, scripts and text resolve

### Edit commands

```
mapkit npc move    Cherrygrove gsboy1 556 400
mapkit npc set     Cherrygrove gsboy1 movement_type=MOVEMENT_TYPE_LOOK_AROUND
mapkit npc add     Cherrygrove fisher SPRITE_FISHING_2 532 404 --script Cherrygrove_EventScript_Fisher
mapkit warp link   Cherrygrove:1 Cherrygrove_Pokemart:0      # both directions
mapkit warp add    Cherrygrove 540 390 --to Route30:2
mapkit wild set    Cherrygrove surf 0 SPECIES_MARILL --level 10-15
mapkit text add    Cherrygrove 'Hello!\nNice day.'
mapkit script add  Cherrygrove Cherrygrove_EventScript_Fisher --msg msg_0550_T21_00025
mapkit script rename Cherrygrove Cherrygrove_EventScript_Boy Cherrygrove_EventScript_TiredBoy
```

These work on migrated maps and on maps still in `files/`. Edits keep each file's indentation and line endings, so diffs show only the change.

## Wild data

Like pokeemerald's `wild_encounters.json`, wild data stays in one file,
`gs_enc_data.json`. Its order must still match `encounter_tables_narc.h`; a
later step can key entries by map id and generate that header. `mapkit wild set`
finds a map's table through its `wild_encounters` header field.

Headbutt, Safari Zone, Bug Contest and Pal Park data are already JSON/CSV and
stay where they are. Roamers and swarm locations are C tables; documenting them
is enough for now (see `wild-encounters.md`).

## Species data: blobs to extract

Most species data is already JSON/CSV/PNG. These are still prebuilt binaries
and block common edits. Each gets a text source plus a round-trip check (text ->
binary must equal the current file):

| Priority | Blob | Becomes |
|---|---|---|
| 1 | `files/poketool/personal/wotbl.narc` (level-up moves) | `learnsets.json` |
| 1 | `files/fielddata/sodateya/kowaza_list.narc` (egg moves) | `egg_moves.json` |
| 2 | `files/poketool/trmsg/trtbl.narc`, `trtblofs.narc` (trainer text tables) | generated from `trainers.json` |
| 2 | `files/poketool/personal/pms.narc` (base/egg species) | field in `evo.json` or `pms.json` |
| 3 | `files/poketool/personal/performance.narc` (Pokéathlon stats) | `performance.json` |
| 3 | `files/poketool/pokegra/height*.narc`, `johtozukan.narc` | JSON |
| later | `files/a/0/6/5` land data (collision, heights, props, models) | per-layout files; needs a parser |

Adding new species is out of scope for now: the count is fixed in the save
layout (`NUM_DEX_FLAG_WORDS`), in many file-index-based archives and in about
15 C files. `pokemon.md` lists what would have to change.

## Phases

1. **Foundation. Done (2026-10-21).** `tools/mapkit` Python package (stdlib only),
   read-only parsers for map headers, zone events, scripts (via `script.inc`), text,
   wild data and matrices; `list`, `show`, `validate`, `refs`. `MOVEMENT_TYPE_*` /
   `OBJECT_TYPE_*` in `include/constants/map_object.h`, and the zone_event JSON
   now uses them (plus `DIR_*`, `BG_TYPE_*`, `BG_DIR_*`) instead of numbers.
2. **Migration. Done (2026-10-22)** for all 540 maps; both ROMs match. Placeholder
   maps borrow the `Everywhere` folder's banks (`@Everywhere` in `maps.txt`). C, asm
   and script includes of event headers point at `maps/<MapName>/ids.h`. Map grids
   (`data/layouts`) not started.
3. **Editing.** Done for the pilot (2026-10-21): `npc`, `warp`, `wild`, `text` and
   `script add/rename` commands; label references in `map.json`. Not done: generate
   the `ScrDef` table and `ids.h` from labels; map-scoped text names.
4. **Blobs.** Learnsets and egg moves first, then trainer text, then the rest.
5. **Later.** Land data parsing, a map viewer, new species.

## Building a modified ROM

Any data change makes the checksum tests fail, which is expected. Build with
`make release` (or `make rom`): it builds the ROM without running `check`.
Keep a clean checkout or the `ai-local/*` base commit to compare against.

## Open questions

- Folder naming for maps whose `MAP_*` names are still `MAP_UNK_*` or near-duplicates.
- Whether `text.json` should hold all languages present in the bank or just `en_US`.
- Whether to keep `files/fielddata/...` copies during a transition period or delete
  them in the same commit as the migration (recommended: delete; git keeps history).
