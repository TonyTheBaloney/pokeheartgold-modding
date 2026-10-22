<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21 -->

# Design: per-map data and the `mapkit` tool

> AI-generated, local to this fork. Do not upstream.

## Goal

Make maps, events, NPCs, warps, wild data and species data editable by name,
in one place per thing, with a tool that can parse, validate and change them,
**without breaking the matching build**: before any mod, the migrated tree must
still produce the retail ROM, byte for byte.

## Where things are today

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

## Target layout

```
data/
  maps/
    Cherrygrove/
      map.json        header fields + bank numbers + map code
      events.json     objects, warps, bgs, coords (names instead of numbers)
      scripts.s       event scripts with named labels
      init.s          on-load / on-transition / on-frame scripts (was _hdr.s)
      text.json       messages (msgenc JSON, unchanged format)
      wild.json       optional; this map's wild table
    Cherrygrove_PokeMart/
      ...
  layouts/
    0064_T21/
      layout.json     matrix (width, height, header ids, altitudes, land ids)
  maps.json           ordered index: map id -> folder, and every bank number
```

Folder names come from the `MAP_*` constant (`MAP_CHERRYGROVE_POKEMART` ->
`Cherrygrove_PokeMart`). `map.json` keeps the original Game Freak code (`T21FS0101`).

### Why bank numbers stay explicit

The ROM stores banks by position, so `maps.json` records each map's
`scriptBank`, `initBank`, `textBank`, `eventsBank`, `wildBank` numbers. The
generator writes members back in that order. Renaming or moving a folder never
changes the ROM. Adding a map appends new bank numbers at the end.

## How the build uses it

The existing pipeline stays. A new generator step (`tools/mapkit gen`) runs
first and writes the same intermediate files the build reads today, into the
build directory:

```
data/maps/*  --mapkit gen-->  build/<game>/gen/
                                zone_event/NNN_CODE.json   -> json2bin.sh -> zone_event.narc
                                scr_seq_NNNN_CODE.s, _hdr.s, event_CODE.h -> makescript.sh -> scr_seq.narc
                                msg_NNNN_CODE.json          -> msgenc -> msg.narc
                                map_headers.h, encounter_tables_narc.h
                                gs_enc_data.json            -> jsonproc -> g/s_enc_data.narc
                                map_matrix/NNNN_*.bin       -> nitroarc
```

The meson file lists that are hand-written today (`zone_event/meson.build`,
`scr_seq/meson.build`, `NARC_msg.txt`) are produced from `maps.json` instead.

**Matching invariant:** for the unmodified tree, every generated file is
byte-identical to the file it replaces. The migration is checked in two ways:
`mapkit gen` output diffed against the current files, then the four
`meson test` checksums for HG and SS.

## Scripts and events

### Named script references

Today an object points at its script with `"scriptId": "_EV_scr_seq_T21_000 + 1"`,
and `event_T21.h` plus the `ScrDef` table at the top of the `.s` file must be
kept in sync by hand, by position.

In `scripts.s` the `ScrDef` table and `event_*.h` go away. Each public script is
a labeled entry:

```asm
	.script Cherrygrove_EventScript_GuideGent
	LockAll
	FacePlayer
	NPCMsg Cherrygrove_Text_GuideGentIntro
	...
```

`mapkit gen` collects `.script` labels in file order, writes the `ScrDef`
table and `event_*.h` (keeping the old `_EV_scr_seq_*` names as aliases), and
resolves `"script": "Cherrygrove_EventScript_GuideGent"` in `events.json` to the
right numeric ID (index + 1 for map scripts; the std ranges 2000+ stay as
`std_*` constants). For the migration, labels are seeded from the current names
(`scr_seq_T21_000`) and renamed over time.

Internal jump labels (`_005F`) can be renamed freely; they don't affect the ROM.

### Text

`text.json` keeps the msgenc JSON format. Message IDs become map-scoped names
(`Cherrygrove_Text_GuideGentIntro`); `mapkit gen` writes the numeric
`msg_NNNN_*.h` in the existing order.

### Script parser

`mapkit` reads `asm/macros/script.inc` and builds a command table from the
`.macro` definitions (name, arguments, byte widths, command ID). That table is
used to:

- list each map's scripts, the text, flags, vars and objects they touch, and
  where they jump (`mapkit show-scripts Cherrygrove`)
- validate: unknown macros, missing labels, message IDs that don't exist,
  `ApplyMovement` on objects that aren't on the map
- later, decompile a `.bin` back to `.s` for round-trip tests

The script text stays GAS macros. A higher-level script language (in the style
of poryscript) is possible later on top of the same parser, but is not part of
this design.

## Events, NPCs and warps

`events.json` is the current zone_event JSON with names instead of raw numbers:

| Field today | In `events.json` |
|---|---|
| `"movement": 15` | `"movement": "MOVEMENT_TYPE_FACE_DOWN"` (done in phase 1) |
| `"facingDirection": 1` | `"facingDirection": "DIR_SOUTH"` (done in phase 1) |
| `"type": 1` | `"type": "OBJECT_TYPE_TRAINER"` (done in phase 1) |
| `"scriptId": "_EV_scr_seq_T21_000 + 1"` | `"script": "Cherrygrove_EventScript_GuideGent"` |
| `"x": 566, "z": 396` (global tiles) | `"x": 566, "z": 396` plus `mapkit` can show/accept local `(cell, x, z)` |
| warp `"header"`, `"anchor"` | `"dest": "MAP_CHERRYGROVE_POKECENTER_1F"`, `"destWarp": 0` |

Unknown or still-numeric values are allowed as plain numbers, so the migration
never blocks on naming.

The constants live in `include/constants/map_object.h` (headers only; the binary
doesn't change): `MOVEMENT_TYPE_*` for the 57 entries of
`gMapObjectMovementCallbacks`, `OBJECT_TYPE_*` for `ObjectEvent.type`.

### Validation (`mapkit validate`)

- every warp's destination map exists and has that warp index; report one-way warps
- coord triggers name a var; objects/bgs sit inside the map's layout
- each events binary stays under the engine's 0x800-byte buffer (`src/map_events.c`)
- object IDs unique per map; hide flags exist; scripts and text resolve

### Edit commands

```
mapkit npc move  Cherrygrove gsoldman1 --x 570 --z 398
mapkit npc add   Cherrygrove --sprite SPRITE_GSBOY1 --at 570,398 --script ...
mapkit warp link Cherrygrove:0 Cherrygrove_PokeCenter_1F:0   # sets both directions
mapkit wild set  Route29 land 0 --species SPECIES_PIDGEY --level 3
```

## Wild data

`gs_enc_data.json` is one array whose order must match `encounter_tables_narc.h`.
After migration each map's table lives in its folder's `wild.json` (same schema,
including the `{"HEARTGOLD": x, "SOULSILVER": y}` form). `mapkit gen` rebuilds the
array in `maps.json` order and writes `encounter_tables_narc.h`, so tables are
found by map, not by position.

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
2. **Migration.** `mapkit migrate` writes `data/maps`, `data/layouts`,
   `maps.json` from the current files. `mapkit gen` + meson wiring. Done when
   generated files diff clean and HG/SS checksums pass.
3. **Editing.** `npc`, `warp`, `wild` commands; named script references and
   `.script` labels.
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
