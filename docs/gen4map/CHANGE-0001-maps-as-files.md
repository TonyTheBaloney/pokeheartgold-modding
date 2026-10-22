<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Change 0001: map data as text files, a map editor and an NSBMD renderer

> AI-generated, local to this fork. Do not upstream.

| | |
|---|---|
| Status | Done (2026-10-22), on branch `ai-local/battle-mart-names` |
| Format | gen4map 1.0 ([FORMAT.md](FORMAT.md)) |
| ROM | unchanged: HeartGold and SoulSilver pass all four `meson test` checksums after every step |

This record collects what changed, why, and how it was verified, so it can be
turned into a reviewed change (pull request, release note) or carried over to a
standalone tool.

## Motivation

A Gen 4 map was spread over a dozen places addressed by archive position: a C
header table, a zone event JSON, two script files, a text bank, a binary map
matrix and a 19.5 MB prebuilt archive of terrain. Nothing could be edited by
name, collision and props could not be edited at all, and there was no way to see
a map. Goals:

1. Every part of a map editable as text, by name, in one place per thing, in the
   style of pret/pokeemerald (`data/maps`, `data/layouts`).
2. The unmodified tree still builds the retail ROM byte for byte.
3. A porymap-style editor that shows maps as the game draws them.
4. A documented, versioned format, so the files and tools can later serve other
   Gen 4 games outside this repository.

## What changed

| Area | Before | After | Commits |
|---|---|---|---|
| Map headers and events | `src/data/map_headers.h`, `files/fielddata/eventdata/zone_event/NNN_CODE.json` | `data/maps/<Map>/map.json` (header + events, pokeemerald keys, names instead of numbers) | `2cd2add2a`, `3d8237e23`, `2fa403b5a`, `f45cbc60c`, `ff1acf9fc` |
| Scripts and text | `files/fielddata/script/scr_seq/*.s`, `files/msgdata/msg/msg_*.json` | `data/maps/<Map>/scripts.pory` (compiled by mapkit), `text.json`, `ids.h` | `47013228d`, `0d50fd018`, `9a0d35ffb`, `5c05419fb`, `dae99516b` |
| Map grids | `files/fielddata/mapmatrix/map_matrix/*.bin` (288) | `data/layouts/<Layout>/layout.json` + `layouts.txt` | `d19f28bd2` |
| Terrain | `files/a/0/6/5` (one prebuilt NARC) | `data/landdata/NNNN/` (676): `permissions.txt`, `props.json`, `soundplates.bin`, `model.nsbmd`, `terrain.bdhc` | `d19f28bd2` |
| Editor | none | `tools/mapeditor` (PySide6): events, header, collision, behaviors, undo | `d19f28bd2` |
| Rendering | none | `tools/mapkit/mapkit/nitro.py` (NSBMD/NSBTX), top-down and 3D views | `a4c5cfee3` |
| Format | implicit | gen4map 1.0: `docs/gen4map/`, manifest `data/gen4map.json`, JSON Schemas, `mapkit format check` | this change |

Build integration: `data/maps/meson.build` generates the zone event JSON and the
header entry per map; `files/fielddata/mapmatrix/meson.build` packs the layouts
(`mapkit layouts pack`); `files/a/0/6/meson.build` packs the land data (`mapkit
landdata pack`). Every generated file keeps its original name and position, so
`.naix` constants and NARC indices don't move.

## Decisions

- **pokeemerald conventions where the DS allows.** Folder names, `map.json` keys
  and the layout/map split follow pokeemerald so pret users recognise them. DS
  differences are explicit: separate init-script bank, msgenc text, matrix cells
  instead of metatiles.
- **Index files keep binary identity.** `maps.txt` and `layouts.txt` record
  original bank names; folders can be renamed freely (`mapkit layouts rename`).
- **Land data by number.** Cells are shared between layouts (sea, Pokémon
  Centers), so they have no single owner to be named after.
- **Text where it's editable, binary where it isn't yet.** Collision, behaviors and
  props are text; NSBMD and BDHC stay binary until there are tools to produce them.
- **Closed JSON keys.** Unknown keys are errors in 1.x, so a typo can't silently
  drop a field.
- **Draw like the game.** The renderer follows the game and NITRO-System code
  (one area per loaded map, altitude for terrain only), not a guess at what looks
  right.

## Verification

- Every migration step: HG and SS `meson test` (Main, Sub, Filesystem, ROM checksums).
- `tools/mapkit/tests` (58 tests): layouts rebuild the retail matrices
  (sha1 `a1c8aafc…`), land data rebuilds the retail `a/0/6/5` (sha1 `e98a8d14…`),
  every NSBMD/NSBTX decodes, the permissions text round-trips.
- `tools/mapeditor/tests` (8 tests, offscreen Qt): edits and undo, saving, top-down
  and OpenGL rendering.
- `mapkit format check`: 540 maps, 288 layouts, 676 cells, 0 problems.
- `mapkit validate`: 0 errors (6 warnings are duplicate object ids in retail data).

## Compatibility and rollback

- ROM output is identical, so saves and the game are unaffected.
- Modders who edited `files/a/0/6/5` or the matrix `.bin` files directly must
  move their edits to `data/landdata` / `data/layouts` (`mapkit landdata migrate` and
  `layouts migrate` show how the conversion works).
- Rollback: revert the commits above; each one builds and matches on its own.

## Open questions

- The meaning of permission bits 8-14 (`[attr]`).
- Text forms for BDHC (heights could be generated from the model) and sound plates.
- Per-game map header keys for Diamond/Pearl and Platinum (FORMAT.md §9).
- Whether wild encounters, area data and the event script language become part of
  the format (they're outside 1.0).

## Follow-up

[ROADMAP.md](ROADMAP.md): extracting a standalone Gen 4 tool.
