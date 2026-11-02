<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-11-02 -->

# Change 0006: wild encounters in the Rust map editor

> AI-generated; not affiliated with pret. See AI.md at the repository root.

| | |
|---|---|
| Status | done (2026-11-02) |
| Format | 1.2 unchanged (two optional `paths` keys, allowed by §2) |
| ROM | unchanged until a table is edited: an unedited `gs_enc_data.json` writes back byte for byte; HeartGold and SoulSilver build and match their SHA-1s |

## Motivation

A map's wild Pokémon were the one per-map thing [mapeditor-rs](../../tools/mapeditor-rs/README.md)
couldn't show. They live outside the map files, in
`files/fielddata/encountdata/gs_enc_data.json`, addressed by an `ENCDATA_` define, so
they had to be edited by hand or one slot at a time with `mapkit wild set`.

## Decisions

- **The tables stay one file.** The editor opens `gs_enc_data.json` with the map and
  saves it with the map's other files, under the same undo stack and the same check for
  files changed outside. Splitting it per map would change the build and the format.
- **Edits are JSON pointer writes.** One command sets or removes a value at a pointer
  inside a table; undo writes the old value back where it was, so the file returns to
  the same bytes.
- **Versions are a view.** A value written `{"HEARTGOLD": a, "SOULSILVER": b}` is shown
  as written (*Both*) or one side at a time; writing one side splits a plain value,
  and sides that agree are joined back. Rates are never split
  (`gs_enc_data.json.txt` doesn't allow it).
- **mapkit still reads the headers.** `export-constants` now also exports `SPECIES_`
  and `ENCDATA_` names and `"wild"`, each table name's index. The editor writes one
  line to `encounter_tables_narc.h` for a table it adds, as it writes `ids.h` for
  objects.
- **Slots numbered from 0**, the array position, as in `mapkit` and
  [wild-encounters.md](../modding/wild-encounters.md).
- **Warnings come from the game code.** Beyond slot counts and levels, a table is
  flagged when `nightFish` is missing while a Good or Super Rod is on, or radio species
  are missing while grass is: `src/field/encounter_check.c` writes those values into
  slots unconditionally. All 142 vanilla tables pass.

## What was built

| Where | |
|---|---|
| `tools/mapkit/mapkit/export.py` | `SPECIES_`, `ENCDATA_` and `"wild"` in the constants export |
| `data/gen4map.json` | `paths.wild_encounters`, `paths.wild_tables` |
| `gen4map-format/src/wild.rs` | methods and slot odds, `pick`/`put` for per-version values, `issues`, empty tables and slots, the `ENCDATA_` define writer |
| `mapeditor/src/doc.rs` | `WildDoc`: the tables file in the open document |
| `mapeditor/src/commands.rs` | `SetWild`, `AddWildTable` |
| `mapeditor/src/wild.rs`, `app.rs` | the *Wild encounters* tab; `--wild` starts in it |
| `mapeditor/src/forms.rs` | `FieldForm::field`, one completing field placed anywhere (the key/value form uses it too) |
| [wild-encounters.md](../modding/wild-encounters.md#editing-a-table-by-hand) | how to make the same edits by hand |

## Verification

- `cargo test` (all crates): the new tests in `crates/mapeditor/tests/doc.rs` and
  `gen4map-format/src/wild.rs`; `mapkit format check` reports 0 problems.
- `make check` for HeartGold and SoulSilver with no table edited: all four checksums
  (main, sub, filesystem, ROM) match.
- An edit made through the editor's commands, then built: Route 29's slot 0 night
  species set to Noctowl in SoulSilver only, and a copy of its table added with slot 0
  at level 77. In `g_enc_data.narc` no existing member changed; in `s_enc_data.narc`
  only member 1 byte 0x44 (`species_nite[0]`, 0xA3 → 0xA4); both gained member 142,
  member 1 with byte 0x08 (`levels[0]`) 2 → 77. Every member stays 0xC4 bytes,
  `sizeof(EncounterData)`. The edit was then reverted and the checksums match again.
- The tab, by `MAPEDITOR_RS_SCREENSHOT` on Route 29 (grass, per-version slots, radio,
  swarm) and Cherrygrove (surfing and three rods).

## Not done

- The Python editor doesn't have the tab.
- Headbutt, Safari Zone, Bug-Catching Contest and swarm map tables are separate files
  and aren't in the editor.
- Removing a table: positions are what maps refer to, so only the last one could go;
  undoing a saved *New table* leaves its `ENCDATA_` line pointing past the end (like
  `ENCDATA_UNUSED_142`), which builds.
