<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21 -->

# Wild encounters

> AI-generated; not affiliated with pret. See AI.md at the repository root.

## Grass, surfing, Rock Smash, fishing

File: `files/fielddata/encountdata/gs_enc_data.json`, array `encounters`
(142 tables). Built twice by `files/fielddata/encountdata/meson.build`: once for
HeartGold (`g_enc_data.narc`), once for SoulSilver (`s_enc_data.narc`).
Binary layout: `EncounterData` in `include/wild_encounter.h`.

### Which table a map uses

1. The map's header sets `.wildEncounterBank = ENCDATA_R29` (`src/data/map_headers.h`).
2. `include/encounter_tables_narc.h` maps `ENCDATA_R29` to a position:
   `ENCDATA(_00000001)` is the table at index 1 of the `encounters` array.
3. `ENCDATA_NA` means no wild encounters.

The `"map"` field inside each JSON entry is only a label. The **array position**
decides which map gets it. Don't reorder or delete entries; append new ones and add
a matching `ENCDATA_*` define with the next index.

### One table

| Key | Slots | Slot format |
|---|---|---|
| `land` | `rate`, 12 `mons` | `{ "level": 3, "species": { "morn": ..., "day": ..., "nite": ... } }` |
| `surf` | `rate`, 5 `mons` | `{ "level": { "min": 15, "max": 20 }, "species": ... }` |
| `rock_smash` | `rate`, 2 `mons` | as surf |
| `fishing.old_rod` / `good_rod` / `super_rod` | `rate`, 5 `mons` each | as surf |
| `hoenn`, `sinnoh` | 2 species each | radio replacements (below) |
| `landSwarm`, `surfSwarm`, `fishSwarm`, `nightFish` | optional | species |

- `rate` is the encounter rate for that method. A method the map doesn't have is
  `{"rate": 0, "mons": []}`; to add one, set a rate and fill **all** of its slots.
- Grass slots share one level across morning/day/night; only the species changes.
- Any value can differ between versions:
  `"species": { "HEARTGOLD": "SPECIES_MANKEY", "SOULSILVER": "SPECIES_VULPIX" }`.

### Slot odds (hard-coded)

In `src/field/encounter_check.c`:

| Method | Odds per slot (%) |
|---|---|
| Grass (12) | 20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1 |
| Surf (5) | 60, 30, 5, 4, 1 |
| Fishing, each rod (5) | 40, 30, 15, 10, 5 |
| Rock Smash (2) | 80, 20 |

Overrides applied in the same file:

- Pokégear radio Hoenn/Sinnoh sound replaces grass slots 2–5 with `hoenn` / `sinnoh`.
- `nightFish` replaces Good Rod slot 3 and Super Rod slot 1 at night.
- During a fishing swarm, `fishSwarm` replaces Old Rod slot 2, Good Rod slots 0, 2, 3
  and all Super Rod slots.

Put a species in slots 0–1 to make it common; slots 10–11 for rare.

## Swarms

Which map has today's swarm and whether it is grass, surf or fishing:
`sSwarmMapLUT` in `src/swarm.c`. The species comes from that map's
`landSwarm` / `surfSwarm` / `fishSwarm` in `gs_enc_data.json`.

## Headbutt trees

`files/arc/headbutt.json` (+ `.json.txt` template), one table per map ID:
`CommonMons`, `RareMons`, `SecretMons` (`{species, minLevel, maxLevel}`; species may
be `{gold, silver}`), plus `Trees` / `SecretTrees` coordinates. Odds per slot
(50, 15, 15, 10, 5, 5) and the rare-tree lookup tables are in `src/field/headbutt.c`.

## Safari Zone

`files/arc/safari_enc.json` (+ template). Per area: `land`, `surf`, `oldrod`,
`goodrod`, `superrod`, each with `mons` by time of day, `bonus_mons` that appear
once enough objects of a type are placed, and `bonus_param`. All slots are equally
likely. Level boosts from placed objects: `sObjectLevelBoosts` in
`src/safari_zone_encounters.c`.

The build generates `safari_enc.narc` from the JSON (`files/arc/meson.build`).

## Bug-Catching Contest

`files/data/mushi/mushi_encount.csv`: `species, lvlmin, lvlmax, rate, score`,
40 rows = 4 sets of 10. The set used depends on the day of the week
(`BugContest_InitEncounters`, `src/overlay_bug_contest.c`). Opponents:
`mushi_trainer.csv`.

## Roaming Pokémon

Species and levels are hard-coded in `src/field_roamer.c` (Raikou and Entei 40,
Latias/Latios 35), together with the routes they move between
(`sRoamerLocations`, `sRoamerAdjacencyTable`). Scripts start them with `createroamer`.
[roamers.md](roamers.md) explains how they move, when you meet one, what a battle does to
them, and how to change them.

## Static and gift encounters

In map scripts: `WildBattle species, level, shiny` and `FatefulWildBattle ...`
(`files/fielddata/script/scr_seq/*.s`). Search:
`grep -rn "WildBattle" files/fielddata/script/scr_seq/`.

## Pal Park / Catching Show

`files/arc/ppark.json` (`species, area, score, encounter_rate`, plus two
fields not yet understood), used by `src/catching_show.c`.

## Level scaling

Wild levels are fixed in these tables. To make them follow the player's party, see
[level-scaling.md](level-scaling.md), which also covers what Repel and Keen Eye do
with the new levels.

## Not found yet

Pokéwalker route Pokémon: only the `WALKER_COURSE_*` constants
(`include/constants/pokewalker_courses.h`) are readable; the route data is likely
in an unnamed binary archive.
