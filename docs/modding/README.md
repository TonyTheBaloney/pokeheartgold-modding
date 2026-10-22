<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21 -->

# Modding guides

> AI-generated, local to this fork. Do not upstream.

These guides describe how to change game data in this fork. Maps live in
pokeemerald-style folders (`data/maps/<MapName>/`); `tools/mapkit` reads, checks and
edits them ([tools/mapkit/README.md](../../tools/mapkit/README.md)).

| Guide | Covers |
|---|---|
| [pokemon.md](pokemon.md) | Base stats, evolutions, moves, Pokédex data, sprites, names |
| [maps-and-warps.md](maps-and-warps.md) | Map headers, map grids, warps, signs, trigger zones |
| [npcs-and-scripts.md](npcs-and-scripts.md) | Moving/adding NPCs, trainers, event scripts, text, flags |
| [wild-encounters.md](wild-encounters.md) | Grass/surf/fishing tables, headbutt, Safari, Bug Contest, roamers |
| [DESIGN.md](DESIGN.md) | Plan for per-map folders and the `mapkit` tool |
| [SCRIPTING.md](SCRIPTING.md) | Proposal: poryscript-style language for map scripts |

## Building a modified ROM

- `make release` (or `make rom`) builds the ROM **without** the checksum tests.
- `make` also runs `check`, which compares against the retail SHA-1s. Any data
  change makes it fail; that is expected for a mod.
- SoulSilver: add `GAME_VERSION=SOULSILVER`.
- Output: `build/heartgold.us/pokeheartgold.us.nds`.

Keep an unmodified commit to diff against. Before changing data, confirm `make`
passes on that commit so you know any later mismatch comes from your edit.

## Status of each data type

| Data | Editable as text? |
|---|---|
| Base stats, types, abilities, TM/HM compatibility | yes (`personal.json`) |
| Evolutions | yes (`evo.json`) |
| Tutor moves | yes (`waza_oshie.json`) |
| Pokédex height/weight/text | yes (JSON) |
| Sprites, icons, footprints | yes (PNG) |
| **Level-up moves** | **no**, binary `wotbl.narc` |
| **Egg moves** | **no**, binary `kowaza_list.narc` |
| Map headers | yes (`data/maps/<MapName>/map.json`) |
| NPCs, warps, signs, triggers | yes (`data/maps/<MapName>/map.json`) |
| Event scripts and text | yes (`scripts.inc`, `map_scripts.inc`, `text.json` in the map folder) |
| Map grid (matrix) | binary per file, no tool yet |
| Terrain, collision, 3D models | **no**, one prebuilt archive |
| Wild encounters | yes (`gs_enc_data.json` etc.) |
| Trainers' parties | yes (`trainers.json`) |
| Trainers' battle text tables | **no**, binary `trtbl.narc` |
