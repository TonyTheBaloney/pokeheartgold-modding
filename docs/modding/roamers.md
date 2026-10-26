<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Roaming Pokémon

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers how the four roaming Pokémon (Raikou, Entei, Latias, Latios) are
created, where they are stored, how they move, how an encounter with one is picked, what a
battle does to them, and how to change or add one.

If you know pokeemerald (`src/roamer.c`, one roamer at a time):

| pokeemerald | here |
|---|---|
| one roamer, `gSaveBlock1Ptr->roamer` | four slots, `RoamerSaveData` (`SAVE_ROAMER` in the save) |
| `InitRoamer()` from a special | `createroamer(id)` in a map script |
| `RoamerMoveToOtherLocationSet` / `RoamerMove` on map change | `Save_UpdateRoamersLocation` on every map connection |
| `sRoamerLocations` (sets of neighbouring maps) | `sRoamerLocations` (the maps) plus `sRoamerAdjacencyTable` (each map's neighbours) |
| `TryStartRoamerEncounter`: 1 in 4 if on the map | 1 in 2 of the encounters on that map (§4) |
| `UpdateRoamerHPStatus`, `SetRoamerInactive` | `Roamers_UpdateAfterBattle` (§5) |

The files:

| File | What |
|---|---|
| [include/roamer.h](../../include/roamer.h), [src/roamer.c](../../src/roamer.c) | the saved data and its getters and setters |
| [src/field_roamer.c](../../src/field_roamer.c) | the species and levels, the map lists, the movement rules, `createroamer` |
| [include/constants/roamer.h](../../include/constants/roamer.h) | roamer ids (`ROAMER_RAIKOU` 0, `ROAMER_ENTEI` 1, `ROAMER_LATIAS` 2, `ROAMER_LATIOS` 3) and location indexes (`ROAMER_LOC_*`) |
| [src/field_warp_state.c](../../src/field_warp_state.c) | when they move |
| [src/field/encounter_check.c](../../src/field/encounter_check.c) | meeting one |
| `Roamers_UpdateAfterBattle` in [src/field/field_move_cut_in_effects.c](../../src/field/field_move_cut_in_effects.c) | after the battle |

## 1. The saved data

`RoamerSaveData` ([include/roamer.h](../../include/roamer.h)) is one block of the save
(`SAVE_ROAMER`, [save-data.md](save-data.md)). Each of the four slots is a `Roamer`:

| Field | Meaning |
|---|---|
| `active` | roaming now. 0 before it is released, and after it is caught or knocked out |
| `species`, `level` | set by `createroamer` |
| `ivs`, `personality` | rolled once by `createroamer`, so its nature, gender and shininess are fixed from then on |
| `hp`, `status` | carried from battle to battle |
| `met_location` | **the map it is on now** (a `MAP_*` id), despite the name. The Pokégear map reads it to show the roamer's marker |

The block also has `locations[4]`, each roamer's position as a `ROAMER_LOC_*` index into
`sRoamerLocations`. `playerLocationHistory[2]` holds the map the player is on and the one
they were on before.

The block also holds things that have nothing to do with roamers. Changing its layout
breaks saves ([save-data.md](save-data.md)):

- `rand[2]`: two daily random numbers. `rand[1]` picks the day's swarm
  ([encounter-mechanics.md](encounter-mechanics.md#8-swarms)), and it is reseeded each day in
  [src/field_time_events.c](../../src/field_time_events.c).
- `outbreak`: whether swarms have been enabled (`ScrCmd_EnableMassOutbreaks`).
- `repelSteps`: the Repel step counter.
- `flutePlayed`: the Black or White Flute in effect on this map.

## 2. Releasing a roamer

The script command **`createroamer(id)`** (`ScrCmd_CreateRoamer` → `Save_CreateRoamerByID`)
does the following:

1. Sets the species and level from a `switch` on the id: Raikou and Entei level 40,
   Latias and Latios level 35.
2. Makes a temporary Pokémon with random IVs and personality, and stores its IVs,
   personality and full HP.
3. Sets `active`.
4. Moves it to a random map in its region (§3).

The retail scripts that call it:

| Script | Releases |
|---|---|
| `data/maps/BurnedTower_B1F/scripts.pory` (the beasts flee) | `createroamer(0)` Raikou, `createroamer(1)` Entei |
| `data/maps/Vermilion/scripts.pory` (Steven, after the Lost Item) | `createroamer(3)` Latios in SoulSilver, `createroamer(2)` Latias in HeartGold (`getgameversion`) |
| `data/maps/PokemonLeagueHallOfFame/scripts.pory` | releases again any roamer whose status variable is 2 (knocked out) and sets it back to 0 |

The status variables `VAR_ROAMER_RAIKOU_STATUS`, `_ENTEI_`, `_LATIAS_` and `_LATIOS_`
(`0x4045`-`0x4048`) are set after battle: **1 = caught, 2 = knocked out**. A knocked-out
roamer comes back after the next Hall of Fame; a caught one doesn't.
[story-progression.md](story-progression.md) has the surrounding story flags.

## 3. How they move

**Regions.** Raikou and Entei roam the 16 Johto routes in `sRoamerLocations` (index 0-15:
Routes 29-39 and 42-46). Latias and Latios roam the 25 Kanto routes (16-40: Routes 1-22,
24, 26, 28). The split is by roamer id, in `RoamerLocationSetRandom`.

**When:**

| Event | Function | Effect |
|---|---|---|
| walking across a map connection (not in the Safari Zone) | `FieldSystem_ResetStateOnMapConnection` | records the map, then **every active roamer moves** (`Save_UpdateRoamersLocation`) |
| going through a door or other warp | `FieldSystem_ResetStateOnWarp` | records the map; **nobody moves** |
| Fly | `FieldSystem_ResetStateOnFlyWarp` | every active roamer jumps to a random map |
| Teleport (`Task_FieldMoveWarp` with `FIELD_MOVE_WARP_TELEPORT`) | `FieldSystem_ClearSafariAndRandomizeRoamers` | every active roamer jumps to a random map. Escape Rope and Dig only clear the Safari flag; they don't move roamers |
| continuing a saved game | `FieldTask_ContinueGame_Normal` | every active roamer jumps to a random map |
| after a wild battle | `Roamers_UpdateAfterBattle` | see §5 |

"Records the map" means `UpdatePlayerLocationHistoryIfAnyRoamersActive`. It pushes the
current map into `playerLocationHistory` (only if it changed and a roamer is active), so
`playerLocationHistory[1]` is the map the player just left.

**A move** (`Save_UpdateRoamersLocation`), for each active roamer:

- With a 1 in 16 chance it **jumps** (`RoamerLocationSetRandom`): to any map in its
  region except its own map and the map the player just left.
- Otherwise it **steps** (`RoamerLocationUpdateEx`) to a random neighbour from
  `sRoamerAdjacencyTable`, again never onto the map the player just left. If its only
  neighbour is that map (Route 39 has one neighbour, Route 38), it jumps instead.

The player's *current* map is allowed, which is how you meet one. Stepping onto a roamer's
map doesn't mean it's there when you arrive: everything moves on the same map change.

## 4. Meeting one

Roamers only appear in **random encounters**, in grass or water:
`FieldSystem_PerformLandOrSurfEncounterCheck` (walking or surfing) and
`FieldSystem_PerformSweetScentEncounterCheck` in
[src/field/encounter_check.c](../../src/field/encounter_check.c). Fishing, Headbutt and
Rock Smash never give one. When an encounter happens on a map that has an active roamer:

1. `getRandomActiveRoamerInCurrMap` collects the active roamers on this map. With a 1 in
   2 chance it picks one of them; otherwise the encounter is a normal one.
2. **Repel** blocks it only if the first healthy Pokémon's level is above the roamer's
   level (`EncounterGen_DoesRepelSuppressEncounter`). Unlike a normal encounter, a blocked
   roamer encounter means no encounter at all.
3. `initRoamingWildmon` builds the Pokémon with the stored species, level, IVs,
   personality, HP and status, and starts a battle with `BATTLE_TYPE_ROAMER`.

The encounter rate is the map's usual rate, after abilities, flutes and the lead's held
item. A roamer doesn't raise it.

## 5. The battle and after

`BATTLE_TYPE_ROAMER` makes the battle use only the AI routine for flag bit 29
(`AI_ROAMING_POKEMON`, `trainer_ai.c`), which picks "run away"
([trainers.md](trainers.md#ai-flags)). The routine's script is still raw bytes in
`asm/trainer_ai_data.s`.

When the battle ends, `Roamers_UpdateAfterBattle` runs from the wild-encounter task in
[src/encounter.c](../../src/encounter.c). That task is used by random encounters, Sweet
Scent, fishing, Headbutt and Rock Smash. Scripted `WildBattle`s use a different path and
don't run it. It looks at the enemy Pokémon:

| Enemy is an active roamer, and | Result |
|---|---|
| the player won and its HP is 0 | the slot is cleared, status var = 2 (knocked out) |
| it was caught | the slot is cleared, status var = 1 (caught) |
| anything else (it fled, the player ran) | its HP and status are saved |

In all three cases, every active roamer on this map then **jumps** somewhere else. After a
battle with something else, the same jump happens with a 30% chance. That is why a roamer
is never on the map just after you met it.

Clearing the slot (`RoamerMon_Init`) zeroes it, including `active`.

## 6. Changing roamers

**Species and level.** Edit the `switch` in `Save_CreateRoamerByID` and the reverse one
in `SpeciesToRoamerIdx` (both in `src/field_roamer.c`). `Roamers_UpdateAfterBattle` finds
a roamer **by species**: after a battle it looks for an active slot whose species matches
the enemy. Two roamers with the same species would confuse it.

**Which maps.** Edit `sRoamerLocations`, `sRoamerAdjacencyTable` and the `ROAMER_LOC_*`
constants together:

- Each table has one row per location, in the same order.
- Each row of `sRoamerAdjacencyTable` is a neighbour count followed by up to 6
  (`MAX_ROAM_NEIGHBOR`) `ROAMER_LOC_*` indexes. Unused entries are `-1`.
- A location should list at least one neighbour. For a map with exactly one neighbour,
  movement falls back to a random jump when that neighbour is the player's previous map. A
  row with a count of 0 would make `LCRandRange(0)` pick from nothing.
- The regions are the ranges `ROAMER_LOC_JOHTO_START`-`_END` and `ROAMER_LOC_KANTO_START`-`_END`.
  A jump picks within the roamer's range, so keep each region's maps contiguous.
- The map must have land or water encounters, or nothing can trigger one there (§4).
- `ROAMER_LOC_COUNT` sizes the tables. `locations[]` in the save stores a `u8` index, so
  adding maps doesn't change the save layout.

**Which region a roamer uses.** `RoamerLocationSetRandom` gives Johto to `ROAMER_RAIKOU`
and `ROAMER_ENTEI` and Kanto to everyone else.

**Encounter chance.** Change `LCRandRange(2)` in `getRandomActiveRoamerInCurrMap` (1 in
2) or the 1 in 16 jump in `Save_UpdateRoamersLocation`.

**Adding a fifth roamer.** `ROAMER_MAX` sizes `data[]` and `locations[]` inside
`RoamerSaveData`, so raising it **changes the save layout**. It moves `outbreak`,
`repelSteps` and `flutePlayed`, and breaks existing saves. You would also need:

- a `ROAMER_*` id;
- cases in `Save_CreateRoamerByID` and `SpeciesToRoamerIdx`;
- a status variable. `Save_VarsFlags_SetRoamerStatus` writes `VAR_ROAMER_RAIKOU_STATUS + id`
  and only accepts ids below 4: it checks against the size of an unrelated 4-entry table,
  `_020FE4A8` in `src/sys_vars.c`;
- the Pokégear map's marker, which keeps one entry per roamer (`roamerLocations[ROAMER_MAX]`
  in `pokegear_map.c`). How each marker is drawn is not checked.

Replacing one of the four is much simpler than adding one.

## Not verified

- Whether a roamer under Mean Look, Shadow Tag or Arena Trap stays in battle: it depends on
  the AI routine for bit 29, which is still raw data.
- How the Pokégear map draws each roamer's marker (only reading `met_location` was checked).
