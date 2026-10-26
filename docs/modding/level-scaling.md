<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Level scaling: wild and trainer Pokémon

> AI-generated; not affiliated with pret. See AI.md at the repository root.

HeartGold and SoulSilver have no level scaling. Every wild and trainer level is set
in the data. This page shows where each level comes from, what else reads that level
afterwards, and how to make levels follow the player in C. Both examples below were
built with `make release`. Neither was tried in game.

| pokeemerald | here |
|---|---|
| `ChooseWildMonLevel` (`src/wild_encounter.c`) | `EncounterSlot_WildMonLevelRoll` (`src/field/encounter_check.c:745`) |
| `CreateNPCTrainerParty` (`src/battle_setup.c`) | `CreateNPCTrainerParty` (`src/trainer_data.c:274`) |
| `GetHighestLevelInPlayerParty` | `Party_GetMaxLevel` (`src/pokemon.c:3251`; skips eggs) |
| `GetNumOwnedBadges`-style flag counts | `PlayerProfile_CountBadges` (`src/player_data.c:144`; Johto + Kanto, 0-16) |

## Where levels come from

| Source | Data | Code that picks the level |
|---|---|---|
| Grass | one `level` per slot in `gs_enc_data.json` ([wild-encounters.md](wild-encounters.md)) | `FieldSystem_GenerateRegularEncounter` (`encounter_check.c:881`) uses the slot's level as it is |
| Surf, Rock Smash, fishing | `level.min` / `level.max` per slot | `EncounterSlot_WildMonLevelRoll`: a random level in the range |
| Headbutt | `minLevel` / `maxLevel` in `files/arc/headbutt.json` | as surf |
| Swarms, radio sounds, night fishing | change only the species; the slot keeps its level | as above |
| Safari Zone | `files/arc/safari_enc.json`, plus boosts from placed objects | `FieldSystem_GenerateSafariEncounter` (`encounter_check.c:934`) |
| Bug-Catching Contest | `lvlmin`, `lvlmax` in `mushi_encount.csv` | `BugContest_GetEncounterSlot` (`src/overlay_bug_contest.c:186`) |
| Roamers | hard-coded 40 / 35 | `Save_CreateRoamerByID` (`src/field_roamer.c:177`); the level is saved and kept between battles ([roamers.md](roamers.md)) |
| Scripted wild battles (legendaries, Sudowoodo, ...) | `WildBattle species, level, shiny` in the map script | `FieldSystem_GenerateSingleWildPokemon` (`encounter_check.c:992`) |
| Gift Pokémon, eggs | the script command's argument; eggs hatch at 1 | not a battle; [breeding.md](breeding.md) |
| Trainers | `level` per party member in `trainers.json` | `CreateNPCTrainerParty`, the four `CreateMon` calls |
| Rematches | the rematch trainer's own party | `sTrainerRematchSets` picks the trainer ([trainers.md](trainers.md#rematches)) |

### How a wild level is rolled

- **Range slots** (surf, Rock Smash, fishing, headbutt): uniform in `min..max`. The
  two values may be in either order.
- **Hustle, Vital Spirit or Pressure** on the lead Pokémon (not an egg): for range
  slots, half the time the level is the slot's maximum. For grass and Safari land,
  half the time the slot is swapped for the slot of the same species with the highest
  level (`ApplyAbilityEffectToSlotLevel`, `encounter_check.c:1362`).

### What reads the level after it is picked

These checks run **after** the level is chosen. If a scaled level is set in a later
step, they still see the old level.

| Check | Rule | Where |
|---|---|---|
| Repel | no encounter if the first healthy party Pokémon's level is **above** the wild level | `EncounterGen_DoesRepelSuppressEncounter` (`encounter_check.c:1184`) |
| Keen Eye, Intimidate lead | half the time, no encounter if the wild level ≤ lead level − 5 (not with Sweet Scent) | `DoesAbilitySuppressEncounter` (`encounter_check.c:1148`) |
| Bug Contest score | `level × 100 / lvlmax` is part of the score | `src/overlay_bug_contest.c:337` |
| Trainer natures | the personality seed includes the data `level` | `CreateNPCTrainerParty` ([trainers.md](trainers.md#a-trainer-in-trainersjson)) |
| Prize money | class rate × 4 × level of the trainer's **last** Pokémon | [trainer-classes.md](trainer-classes.md#what-a-class-is-made-of) |
| Moves | without custom moves, a Pokémon gets the last four moves it learns by its level | `CreateMon` |

## Choosing a rule

All the values a rule can use are already in the `BattleSetup` when the level is
picked. `BattleSetup_InitFromFieldSystem` (`src/battle/battle_setup.c:264`) runs first
for every wild and trainer battle from the field:

| Rule | Code | Notes |
|---|---|---|
| Highest level in the party | `Party_GetMaxLevel(setup->party[BATTLER_PLAYER])` | Follows the player closely. One over-leveled Pokémon raises everything. |
| Badge count | `PlayerProfile_CountBadges(setup->profile[BATTLER_PLAYER])` | Follows story progress, not grinding. Needs a table of levels per badge. |
| Both | the higher of the two | Badges set a minimum; the party raises it. |

**Keep the data level as a minimum.** The examples return `max(data level, scaled
level)`, so early areas still scale up and late-game data levels are never lowered.
To also scale levels down, return the scaled level alone.

**Stay a little below the party.** Scaling to exactly the highest level, with
experience from Pokémon at that level, keeps the strongest Pokémon level with the
wild ones. A margin (−2 to −5) keeps the player ahead. For a hard mode, use a
positive offset instead.

## Wild Pokémon

All regular encounters (grass, surf, Rock Smash, fishing, headbutt, Sweet Scent)
go through `FieldSystem_GenerateRegularEncounter`. One line there covers them all.

Add this above `FieldSystem_GenerateRegularEncounter` in `src/field/encounter_check.c`:

```c
// Level scaling: never weaker than the player's strongest Pokémon minus 5..2.
static u8 WildMon_ScaleLevel(BattleSetup *battleSetup, u8 level) {
    int scaled = Party_GetMaxLevel(battleSetup->party[BATTLER_PLAYER]) - 5 + LCRandRange(4);

    if (scaled > MAX_LEVEL) {
        scaled = MAX_LEVEL;
    }
    return scaled > level ? scaled : level;
}
```

Call it right after the `switch` that picks the slot, **before** the Unown, ability
and Repel checks, so that they see the new level:

```c
    default:
        GF_ASSERT(FALSE);
    }
    level = WildMon_ScaleLevel(battleSetup, level);

    if (encSlots[slot].species == SPECIES_UNOWN && !EncounterGen_CanGenerateUnownEncounter(encounterGen)) {
```

`LCRandRange(4)` gives 0-3, so the level is spread over four values. The grass slot
levels in the data are no longer used once the party is above them.

**Safari Zone**: in `FieldSystem_GenerateSafariEncounter`, change
`level = encSlots[slot].maxLevel;` to
`level = WildMon_ScaleLevel(battleSetup, encSlots[slot].maxLevel);`. Level boosts
from placed objects only matter when they lift the data level above the scaled
level.

**Leave out:**

- **Bug-Catching Contest**: a level above `lvlmax` gives a level score above 100, so
  scaling changes who wins the contest. If you scale it, also change the score in
  `src/overlay_bug_contest.c:337`.
- **Roamers**: their level is saved when they are released and stays the same
  between battles. To scale them, change `level` in `Save_CreateRoamerByID`. That
  scales them only once, at release.
- **Scripted battles** (`WildBattle`): legendaries and story battles. Raise the
  level in the script, or add the same call to `FieldSystem_GenerateSingleWildPokemon`
  if you want it everywhere.

### Repel and Keen Eye after scaling

Repel blocks a wild Pokémon whose level is below the first healthy party Pokémon.
With the rule above, every wild Pokémon is 2-5 levels below the strongest one. If
that Pokémon leads, Repel blocks almost every encounter. Keen Eye and Intimidate
work the same way, at 5 levels or more below. This is how those items and abilities
work in retail, applied to the new levels. If you don't want it, compare against
the unscaled data level in those two checks.

## Trainer Pokémon

Add this above `CreateNPCTrainerParty` in `src/trainer_data.c`. It uses both rules:
a minimum level per badge count, raised by the party's highest level minus 2:

```c
static const u8 sBadgeLevelFloor[] = { 0, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72 };

// Level scaling: never weaker than the player's strongest Pokémon minus 2.
static u8 TrMon_ScaleLevel(BattleSetup *enemies, int partyIndex, u8 level) {
    int scaled;

    // Leave the player's partner in a multi battle as it is.
    if (partyIndex == BATTLER_PLAYER2) {
        return level;
    }
    scaled = Party_GetMaxLevel(enemies->party[BATTLER_PLAYER]) - 2;
    if (scaled < sBadgeLevelFloor[PlayerProfile_CountBadges(enemies->profile[BATTLER_PLAYER])]) {
        scaled = sBadgeLevelFloor[PlayerProfile_CountBadges(enemies->profile[BATTLER_PLAYER])];
    }
    if (scaled > MAX_LEVEL) {
        scaled = MAX_LEVEL;
    }
    return scaled > level ? scaled : level;
}
```

`sBadgeLevelFloor` has 17 entries, for 0 to 16 badges. The values here are an
example. Set them to the levels your game should have at each point.

Then change only the level argument of the four `CreateMon` calls, one per trainer
type (`src/trainer_data.c:337`, `:370`, `:397`, `:422`):

```c
CreateMon(mon, species, TrMon_ScaleLevel(enemies, partyIndex, monSpecies[i].level), iv, TRUE, (s32)personality, OT_ID_RANDOM_NO_SHINY, 0);
```

The other three use `monSpeciesMoves`, `monSpeciesItem` and `monSpeciesItemMoves`.

- **Leave the `personality = ... + level + ...` lines alone.** They use the data
  level, so a trainer's natures stay the same at any player level.
- Trainers with `TRTYPE_MON` or `TRTYPE_MON_ITEM` get the moves of the new level.
  Trainers with custom moves keep their moves.
- Prize money follows the scaled level of the last Pokémon.
- Every trainer battle from the field builds parties here, including double, tag and
  multi battles. One exception is the link multi battle against the rival
  (`src/encounter.c:789`): it builds the rival's party before the player's party is
  copied in, so `Party_GetMaxLevel` returns 1 there and only the badge minimum
  applies.

**Keeping a party's level spread.** The function above raises every Pokémon to the
same level once the player is above the trainer. To keep the ace higher than the
rest, add the difference instead of taking the maximum: find the party's highest
data level once, and return `level + (scaled - highestDataLevel)` when that is
positive.

**Leaving some trainers out.** The trainer class is
`enemies->trainer[partyIndex].data.trainerClass`. Return `level` unchanged for
classes you want to keep at their data levels, such as gym leaders or Red
(`TRAINERCLASS_*`, [trainer-classes.md](trainer-classes.md)). The trainer id is
`enemies->trainerId[partyIndex]`.

## Evolving scaled Pokémon

Scaling doesn't change species, so a level 40 wild Rattata stays a Rattata. This
helper follows plain level-up evolutions (`EVO_LEVEL`) until none applies:

```c
static u16 Species_EvolveForLevel(u16 species, u8 level) {
    struct Evolution evos[MAX_EVOS_PER_POKE];
    BOOL evolved;

    do {
        evolved = FALSE;
        LoadMonEvolutionTable(species, evos);
        for (int i = 0; i < MAX_EVOS_PER_POKE; i++) {
            if (evos[i].method == EVO_LEVEL && evos[i].param <= level) {
                species = evos[i].target;
                evolved = TRUE;
                break;
            }
        }
    } while (evolved);
    return species;
}
```

For wild Pokémon, pass the result to `generateWildNonShinyAndAddToParty` at the end
of `FieldSystem_GenerateRegularEncounter` instead of `encSlots[slot].species`. For
trainers, set `species = Species_EvolveForLevel(species, scaledLevel);` before
`CreateMon` in each case. Keep the scaled level in a local variable so it is only
calculated once.

Only `EVO_LEVEL` is handled. Gender, stat and personality variants (Tyrogue,
Wurmple, Burmy, ...), friendship, stones and trades are not
([evolutions.md](evolutions.md) lists the methods). To evolve those too, add
`EVO_LEVEL_MALE` and the other methods to the `if`, or set a level for each one,
such as stones at 30 and friendship at 25.

## Other things to check

- **Obedience.** Traded Pokémon disobey above the badge level
  ([gyms.md](gyms.md#what-badges-do)). Caught Pokémon always obey, so scaled wild
  Pokémon are safe to catch.
- **The RNG.** `LCRandRange` in the wild example uses the same random generator as
  the encounter rolls, so the encounters that follow change too. This has no effect
  on play.
- **Level 100.** Both examples cap at `MAX_LEVEL`. A party at 100 meets only level
  95-98 wild Pokémon.
- **Saves.** Nothing is added to the save, so old saves keep working
  ([save-compatibility.md](save-compatibility.md)).

## Checklist

- [ ] wild: `WildMon_ScaleLevel` called before the Unown, ability and Repel checks
- [ ] Safari, Bug Contest, roamers, scripted battles: scale them or leave them out
- [ ] trainers: all four `CreateMon` calls; personality lines unchanged
- [ ] badge table has 17 entries (0-16 badges)
- [ ] optional: evolution helper, classes to leave out
- [ ] `make release`, then test in game: an early route with a high-level party,
      Repel on and off, a gym leader, a double battle

## Not verified

- Neither example was tested in game. Both were built with `make release`, then
  removed from the source.
- Whether the AI's switching and damage scoring behave as expected with all
  party members at the same level.
