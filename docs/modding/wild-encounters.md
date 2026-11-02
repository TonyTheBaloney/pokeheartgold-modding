<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Wild encounters

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How often encounters happen, Repel, the Cleanse Tag, flutes, abilities, fishing bite
chance, swarms, the radio, and switching tables from a script:
[encounter-mechanics.md](encounter-mechanics.md).

## Grass, surfing, Rock Smash, fishing

File: `files/fielddata/encountdata/gs_enc_data.json`, array `encounters`
(142 tables). Built twice by `files/fielddata/encountdata/meson.build`: once for
HeartGold (`g_enc_data.narc`), once for SoulSilver (`s_enc_data.narc`).
Binary layout: `EncounterData` in `include/wild_encounter.h`.

### Which table a map uses

1. The map's `data/maps/<Map>/map.json` sets `"wild_encounters": "ENCDATA_R29"`; the
   build turns it into the header's `.wildEncounterBank`.
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

Overrides applied in the same file
([encounter-mechanics.md §3](encounter-mechanics.md#3-slots) has what each is worth):

- During a grass swarm, `landSwarm` replaces grass slots 0–1; during a surf swarm,
  `surfSwarm` replaces surf slot 0.
- Pokégear radio Hoenn/Sinnoh sound replaces grass slots 2–3 with the first `hoenn` /
  `sinnoh` species and 4–5 with the second.
- `nightFish` replaces Good Rod slot 3 and Super Rod slot 1 at night.
- During a fishing swarm, `fishSwarm` replaces Old Rod slot 2, Good Rod slots 0, 2, 3
  and all Super Rod slots (after `nightFish`).

Put a species in slots 0–1 to make it common; slots 10–11 for rare.

### Editing a table by hand

Any text editor will do; the build reads `gs_enc_data.json` directly. Slots are
numbered from 0, the position in the `mons` array (as in `mapkit` and the map editor).

**1. Find the map's table.**

```sh
tools/mapkit/mapkit.sh show Route29 | grep -A3 '^wild'
# wild (ENCDATA_R29, index 1):
```

Or by hand: `"wild_encounters"` in `data/maps/Route29/map.json`, then that name in
`include/encounter_tables_narc.h` (`ENCDATA(_00000001)` is index 1). Count entries
from 0: index 1 is the second `{ "map": ... }` object. The `"map"` label usually
matches the name, but only the position counts. In the map editor's *Wild encounters*
tab, *Open in text editor* jumps to the table.

**2. Change a slot.** Species are `SPECIES_*` names from `include/constants/species.h`;
levels are 1–100. Grass has one level and a species per time of day:

```json
{
    "level": 3,
    "species": {
        "morn": "SPECIES_PIDGEY",
        "day": "SPECIES_PIDGEY",
        "nite": "SPECIES_HOOTHOOT"
    }
}
```

Surfing, Rock Smash and the rods have a range (`min` ≤ `max`) and one species:

```json
{ "level": { "min": 15, "max": 20 }, "species": "SPECIES_TENTACOOL" }
```

The same edit from the command line: `tools/mapkit/mapkit.sh wild set Route29 land 0
SPECIES_NIDORAN_F --level 3` (`--time nite` for one time of day only; `--level 5-8` for
a range).

**3. Make one version different.** Replace a level or species with an object naming
both versions: `"day": { "HEARTGOLD": "SPECIES_MANKEY", "SOULSILVER": "SPECIES_VULPIX" }`.
Inside a range, split `min` or `max`, not `level`. Rates can't differ.

**4. Turn a method on.** Set `rate` (1–255; higher means more encounters per step;
vanilla grass uses 5–25, surfing 5–15, Rock Smash 5–50, the Old/Good/Super Rod 25/50/75)
and give it **exactly** its
number of slots (12 grass, 5 surfing, 2 Rock Smash, 5 per rod). Fewer slots build as
species 0 with level 0. Turning on the Good or Super Rod also needs `nightFish` (below):
at night it replaces a slot whatever its value, and a missing one is no Pokémon.

**5. Turn a method off.** `{"rate": 0, "mons": []}`, as maps without it are written.

**6. Radio, swarms, night fishing.** `"hoenn"` and `"sinnoh"` hold 2 species each; a
grass table needs both, or Hoenn/Sinnoh Sound turns slots 2–5 into no species.
`landSwarm`, `surfSwarm`, `fishSwarm` and `nightFish` are single species and may be left
out (a missing key builds as no species).

**7. Give a map a table of its own.** Two ways:

- Reuse a table no map uses: `ENCDATA_UNUSED_045`, `_047`, `_049`, `_050`, `_064`,
  `_090`, `_138` are all-zero tables. Fill one in and set the map's
  `"wild_encounters"` to its name.
- Append one: add a table at the **end** of `encounters` (copy an existing one and
  change `"map"`), then a name for its index in `encounter_tables_narc.h` after the
  last `ENCDATA_` line. With 142 tables the new one is index 142:

  ```c
  #define ENCDATA_MY_ROUTE   ENCDATA(_00000142)
  ```

  (`ENCDATA_UNUSED_142` already names index 142 and works too.) Then
  `"wild_encounters": "ENCDATA_MY_ROUTE"` in the map's `map.json`.

Never insert or delete in the middle of `encounters`: every later table would move to
another map.

**8. Check and build.**

```sh
tools/mapkit/mapkit.sh validate Route29   # unknown species, wrong slot counts, missing table
make
```

A JSON syntax error stops the build at `gs_enc_data.json`. Levels and rates are bytes
in the ROM (`EncounterData`), so a value over 255 is cut down, at most with a compiler
warning.

### In the map editor

[tools/mapeditor-rs](../../tools/mapeditor-rs/README.md) has a *Wild encounters* tab
(`tools/mapeditor-rs/mapeditor-rs.sh Route29 --wild`): the open map's table with its
rates, every slot and its odds, the radio species, swarms and night fishing, edited with
species completion and undo. *Version* switches between the values as written (an edit
sets both versions) and HeartGold or SoulSilver alone (an edit splits the value, and
joins it again when both sides agree). *Table* picks which table the map uses; *New
empty table* and *Copy into a new table* append one and point the map at it. Problems
from the list above (slot counts, levels, unknown species, missing radio or night
fishing species) are listed at the top. Saving writes `gs_enc_data.json` with the same
formatting, plus the new `ENCDATA_` line when a table was added. A table shared by
several maps says so.

## Swarms

Which map has today's swarm and whether it is grass, surf or fishing:
`sSwarmMapLUT` in `src/swarm.c`. The species comes from that map's
`landSwarm` / `surfSwarm` / `fishSwarm` in `gs_enc_data.json`. Only the 20 maps in
`sSwarmMapLUT` use them; tables of other maps may have them or not (a missing key builds
as no species).

[encounter-mechanics.md §8](encounter-mechanics.md#8-swarms) covers how swarms are turned
on (`enablemassoutbreaks`), how the day's swarm is picked, the full list of swarm maps and
species, and how to choose a swarm from a script.

## Headbutt trees

`files/arc/headbutt.json` (+ `.json.txt` template), one table per map ID:
`CommonMons`, `RareMons`, `SecretMons` (`{species, minLevel, maxLevel}`; species may
be `{gold, silver}`), plus `Trees` / `SecretTrees` coordinates. Odds per slot
(50, 15, 15, 10, 5, 5) and the rare-tree lookup tables are in `src/field/headbutt.c`.

## Safari Zone

`files/arc/safari_enc.json` (+ template). Per area: `land`, `surf`, `oldrod`,
`goodrod`, `superrod`, each with `mons` by time of day, `bonus_mons` that appear
once enough objects of a type are placed, and `bonus_param`. All slots are equally
likely. Each placed object adds points that grow with the area's age
(`sObjectLevelBoosts` in `src/safari_zone_encounters.c`; despite the name, no Pokémon's
level changes), and a bonus entry turns on once its type's points reach its `count`.
[safari-zone.md](safari-zone.md#6-object-points-area-age-and-bonus-pokémon) explains the rules.

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

In map scripts: `wildbattle(species, level, shiny)` (and `fatefulwildbattle`, which no
script uses). Search: `grep -rn 'wildbattle(' data/maps`.
[static-encounters.md](static-encounters.md) lists all of them and covers what happens
after the battle, bringing one back, changing its level or moves, and adding one. Gifts
are in [gift-pokemon-and-trades.md](gift-pokemon-and-trades.md).

## Pal Park / Catching Show

`files/arc/ppark.json` (`species, area, score, encounter_rate`, plus two
fields not yet understood), used by `src/catching_show.c`.

## Level scaling

Wild levels are fixed in these tables. To make them follow the player's party, see
[level-scaling.md](level-scaling.md), which also covers what Repel and Keen Eye do
with the new levels.

## Pokéwalker courses

The Pokémon and items of each Pokéwalker course are raw bytes in `sPokewalkerCourses`
(`asm/pokewalker_data.s`). [pokewalker.md](pokewalker.md#change-a-courses-pokémon) gives
the layout and how to edit them.
