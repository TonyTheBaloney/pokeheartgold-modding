<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Breeding and the Day-Care

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers the Route 34 Day-Care: what it saves, how it decides whether two Pokémon
can make an egg, everything the egg inherits (species, nature and the Everstone, IVs and
the Power items, moves, form, shininess), how eggs hatch and at what level, and how to
change each rule. It also covers the Destiny Knot, which does **nothing** for breeding in
HGSS, and how to give it its Gen 6 effect.

If you know pokeemerald (`src/daycare.c`):

| pokeemerald | here |
|---|---|
| `gSaveBlock1Ptr->daycare` | `Daycare` (`SAVE_DAYCARE` in the save) |
| `GetDaycareCompatibilityScore` | `ComputeCompatibilityBetweenBoxMons` (§2) |
| `_TriggerPendingDaycareEgg` (Everstone: mother or Ditto, 50%) | `GenerateEggPID` (Everstone: **either** parent, 50%) (§3) |
| `InheritIVs` (3 IVs, can pick a stat twice) | `InheritIVs` (3 different stats, Power items force one) (§4) |
| `BuildEggMoveset` | `InheritMoves` (§5) |
| `GiveEggFromDaycare` | `GiveEggToPlayer` (`givedaycareegg`) |
| `ShouldEggHatch` | `HandleDaycareStep` (§6) |
| `EGG_HATCH_LEVEL` 5 | `EGG_HATCH_LEVEL` **1** (§6) |

The files:

| File | What |
|---|---|
| [include/daycare.h](../../include/daycare.h), [src/daycare.c](../../src/daycare.c) | the saved data, its getters and setters, the Masuda check |
| [include/constants/daycare.h](../../include/constants/daycare.h) | every breeding number: chances, steps, egg level, attempts |
| [src/get_egg.c](../../src/get_egg.c) | all the rules: deposit/withdraw, compatibility, the egg, hatching |
| [src/scrcmd_daycare.c](../../src/scrcmd_daycare.c) | the Day-Care script commands |
| [src/field/field_control.c](../../src/field/field_control.c) | `FieldSystem_UpdateDaycare`: runs §6 on every step |
| [src/hatch_egg_task.c](../../src/hatch_egg_task.c) | the hatching scene (calls `HatchEggMon`) |
| [files/poketool/personal/personal.json](../../files/poketool/personal/personal.json) | per species: `eggGroups`, `eggCycles`, `genderRatio` |
| [files/poketool/personal/egg_moves.json](../../files/poketool/personal/egg_moves.json) | egg moves ([pokemon.md](pokemon.md#egg-moves)) |
| `files/poketool/personal/pms.narc` | the species an egg hatches into (binary; [adding-a-species.md §4](adding-a-species.md#4-egg-species-pmsnarc)) |
| `files/fielddata/script/scr_seq/scr_seq_0265.s` | the Day-Care Man and Lady's scripts |
| [data/maps/Route34/scripts.pory](../../data/maps/Route34/scripts.pory) | the Day-Care Man's position (`checkdaycareegg` in `Route34_OnTransition`) |

Line numbers below are for `src/get_egg.c` unless another file is named.

## 1. The saved data

```c
typedef struct DaycareMon {
    BoxPokemon mon;
    DaycareMail mail;   // mail, OT name and nickname, if the mon held mail
    u32 steps;          // steps walked since it was left (= experience gained)
} DaycareMon;

typedef struct Daycare {
    DaycareMon mons[2];
    u32 egg_pid;        // 0 = no egg waiting; otherwise the egg's personality value
    u8 egg_cycles;      // step counter for egg cycles (§6), for every egg in the party
    u8 padding_1DD[3];
} Daycare;
```

There is no "egg waiting" flag: an egg exists when `egg_pid != 0`
(`Save_Daycare_HasEgg`). The personality value is rolled when the egg is made (§3) and
the rest of the egg is built only when the player takes it (`GiveEggToPlayer`, §3–5).
Changing these structs changes the save layout ([save-data.md](save-data.md)).

**Leaving a Pokémon** (`Save_Daycare_PutMonIn`, line 104): it goes into the first empty
slot. Its mood (`MON_DATA_MOOD`) is reset, Shaymin returns to Land Forme, the step count
starts at 0, and Chatot's recorded cry is cleared if no Chatot is left in the party. The
script first runs `DaycareSanitizeMon` (`src/scrcmd_daycare.c`), which moves a held
Griseous Orb to the bag and resets Giratina, Rotom and Shaymin to their base forms.

**While it stays**: every step adds 1 to `steps` for each mon in the Day-Care, and each step
is 1 experience point.

**Taking it back** (`Save_Daycare_MoveMonToParty`, line 141): `steps` is added to its
experience (unless it is level 100), it learns its level-up moves for every level gained
(if its moves are full, the first move is forgotten each time, with no prompt), and mail is
given back. The cost is `(levels gained + 1) * DAYCARE_PRICE_PER_LEVEL` (100). If slot 0
is emptied, slot 1 moves down to slot 0 (`Save_Daycare_Compaction`).

## 2. Can these two make an egg?

`ComputeCompatibilityBetweenBoxMons` (line 675) returns the percent chance of an egg at
each check. The rules, in order:

| Rule | Result |
|---|---|
| either is in `EGG_GROUP_UNDISCOVERED` (first egg group) | `PARENTS_INCOMPATIBLE` (0) |
| both are Ditto (`EGG_GROUP_DITTO`) | 0 |
| one is Ditto, same OT ID | `PARENTS_LOW_COMPATIBILITY` (20) |
| one is Ditto, different OT IDs | `PARENTS_MED_COMPATIBILITY` (50) |
| same gender | 0 |
| either is genderless | 0 |
| no egg group in common | 0 |
| same species, different OT IDs | `PARENTS_MAX_COMPATIBILITY` (70) |
| same species, same OT ID | 50 |
| different species, different OT IDs | 50 |
| different species, same OT ID | 20 |

Only the **first** egg group is checked for Undiscovered and Ditto; any of the two groups
can match for the "in common" rule. Egg groups and gender ratios come from
`personal.json` ([pokemon.md](pokemon.md)).

**When the check runs** (`HandleDaycareStep`, line 769): when both slots are full and no
egg is waiting, the game reads the **second** mon's step count as a `u8`. When it equals
`DAYCARE_BREED_CHECK_STEPS` (255), it rolls `LCRandom() * 100 / 0xFFFF` (0–100) and
makes an egg if the compatibility is greater. Because only the low byte is read, the check
runs when the count is 255, 511, 767…, so once every **256** steps, not 255.

When an egg is made, `FieldSystem_TryTriggerDaycareEggCall`
([src/gear_phone_ring_manager.c](../../src/gear_phone_ring_manager.c)) asks the Day-Care Man
to phone you, if his number is registered ([phone.md](phone.md)).

**What the Day-Care Man says** (`getdaycarecompatibility`): the script gets 0 for 70,
1 for 50, 2 for 20 and 3 for 0 (`ConvertDaycareCompatibilityScore`, line 883). If you add a
new chance value, add it there too or it will read as 0 ("they get along very well").

## 3. The egg's species, nature and personality

### Which parent is the mother

`Daycare_GetEggSpecies` (line 526) picks the **mother**, whose species and form the egg
takes, and the **father**, whose moves it can inherit (§5):

| Pair | Species from | Form from | Moves from (father) |
|---|---|---|---|
| female + male | female | female | male |
| female + Ditto | female | female | Ditto (so no egg or TM moves) |
| male + Ditto | male | **Ditto** (form 0) | male |
| genderless + Ditto | genderless mon | **Ditto** (form 0) | genderless mon |

So a male Shellos (East Sea) bred with Ditto gives a West Sea Shellos: form only passes
down through a female parent.

### Species

The mother's species is looked up in `pms.narc` (`ReadFromPersonalPmsNarc`), which gives
the lowest stage (Charizard → Charmander). Then, in this order:

1. **Nidoran♀ and Illumise.** If the table gives `SPECIES_NIDORAN_F` or `SPECIES_ILLUMISE`
   and bit 15 of the egg's personality (`EGG_GENDER_MALE`, 0x8000) is set, the egg becomes
   Nidoran♂ or Volbeat instead: a 50% chance.
2. **Manaphy** always gives Phione (hard-coded, not in `pms.narc`).
3. **Incense babies** (`Daycare_BreedingIncenseCheck`, line 490). `pms.narc` gives the baby
   (Wobbuffet → Wynaut), but `sIncenseMons` (line 478) turns it back into the parent
   species unless **either** parent holds the matching incense:

| Baby | Item | Without the item |
|---|---|---|
| Wynaut | Lax Incense | Wobbuffet |
| Azurill | Sea Incense | Marill |
| Mime Jr. | Odd Incense | Mr. Mime |
| Bonsly | Rock Incense | Sudowoodo |
| Munchlax | Full Incense | Snorlax |
| Mantyke | Wave Incense | Mantine |
| Budew | Rose Incense | Roselia |
| Happiny | Luck Incense | Chansey |
| Chingling | Pure Incense | Chimecho |

To add a baby that needs an item, set its `pms.narc` entry and add a row here. (Pichu has no
row: its baby is unconditional.)

### Nature: the Everstone

The egg's nature comes from its personality value, which is rolled when the egg is made:
`GenerateEggPID` (line 260), using `Daycare_EverstoneCheck` (line 226).

- **Neither parent holds an Everstone**: the personality is a random `MTRandom()`.
- **One parent holds an Everstone** (mother, father or Ditto, either slot): a 50% chance
  (exactly 32768 in 65536) that the egg gets that parent's nature.
- **Both hold one**: a random parent is chosen, then the same 50% chance.

If the Everstone applies, the game draws random personality values until one has the
parent's nature (and is not 0), at most `EGG_NATURE_PID_ATTEMPTS` (2400) times. With 25
natures this practically always succeeds; if it doesn't, the last value is kept with
whatever nature it has.

The Everstone only fixes the nature. Gender, ability slot and shininess all come from the
same personality value, so they are random too. The parents' abilities are not inherited.

### Shininess: the Masuda method

`SetBreedEggStats` (line 602): if the two parents have different `MON_DATA_LANGUAGE`
(`Save_Daycare_MasudaCheck` in `src/daycare.c`) and the egg is not already shiny, the
personality is rerolled up to `MASUDA_METHOD_REROLLS` (4) times with `PRandom` until one is
shiny for the player's OT. That is 5 chances in all, about 5/8192. Other odds and a Shiny
Charm: [shiny.md](shiny.md#6-recipes).

Rerolling changes the personality, so a Masuda reroll can undo the Everstone's nature (and
the Nidoran/Volbeat bit, which was already used in §3 to pick the species).

### Other fields

| Field | Value |
|---|---|
| level | `EGG_HATCH_LEVEL` (1) |
| Poké Ball | always Poké Ball (not inherited) |
| egg cycles | the species' `eggCycles` in `personal.json` |
| met level | 0 (this is what marks a Pokémon as hatched) |
| OT, trainer memo | the player; egg location "Day-Care couple" (`MAPSECTYPE_GIFT`, 0) |

## 4. IVs and the Power items

The egg first gets six random IVs (`CreateMon` with `USE_RANDOM_IVS`). Then `InheritIVs`
(line 297) overwrites `NUM_INHERITED_IVS` (3) of them:

1. If a parent holds a **Power item**, that parent's IV for the item's stat is always one
   of the three (`Daycare_TryGetForcedInheritedIV`, line 1005). If both parents hold one,
   a random parent's item counts and the other's is ignored.

   | Item | Stat |
   |---|---|
   | Power Weight | HP |
   | Power Bracer | Attack |
   | Power Belt | Defense |
   | Power Anklet | Speed |
   | Power Lens | Sp. Atk |
   | Power Band | Sp. Def |

2. The remaining stats are picked at random from the stats not chosen yet, so all three are
   different (unlike Emerald, where the same stat could be picked twice).
3. For each of those, a random parent (50/50) gives its IV.

The Everstone and the Power items don't interfere: one sets the nature, the other an IV.

## 5. Moves

`InheritMoves` (line 397). The egg starts with the moves its species knows at
`EGG_HATCH_LEVEL` (from `CreateMon`). Then these are added in order; each time the egg
already has four moves, its **first** move is dropped to make room:

1. **Egg moves**: each of the **father's** moves that is in the baby's list in
   `egg_moves.json`. Only the father's: the mother's moves never give egg moves.
2. **TM/HM moves**: each of the father's moves that is a TM or HM the baby can learn
   (the baby's `tms`/`hms` in `personal.json`).
3. **Shared level-up moves**: each move **both** parents know that is anywhere in the baby's
   level-up learnset, at any level.
4. **Volt Tackle**: if the egg is Pichu and either parent holds a Light Ball
   (`Daycare_LightBallCheck`, line 513).

"Father" is the male, or the non-Ditto parent when the other is Ditto, except that with a
female and a Ditto the father is Ditto (§3). So female + Ditto gives no egg moves.

Limits: a species can have at most `MAX_EGG_MOVES` (16) egg moves, and only the first
`EGG_MOVES_TABLE_SIZE` (2045) entries of the table are searched ([pokemon.md](pokemon.md#egg-moves),
[game-limits.md](game-limits.md)). The baby's level-up learnset is read into a 50-entry
buffer (`baby_learnset[50]` in `struct EggMoveSearch`); if you raise
`MAX_LEARNED_MOVES` past that, enlarge the buffer too.

## 6. Hatching and egg level

### Egg cycles

`HandleDaycareStep` (line 769) also counts every step in `Daycare.egg_cycles`, whether or
not anything is in the Day-Care. When it reaches the cycle length, it resets to 0 and
every egg in the party loses one cycle (two with Flame Body or Magma Armor, below). If an
egg already has 0 cycles, it hatches instead: `FieldSystem_UpdateDaycare` starts
`std_hatch_egg`, and `Party_GetMonToHatch` finds the egg.

Cycle length (`Daycare_GetEggCycleLength`, line 756):

- `EGG_CYCLE_STEPS` (255) normally;
- `EGG_CYCLE_STEPS_SPECIAL_DAY` (230) on the dates in `sEggCycleSpecialDates` (line 738:
  New Year's Day, Valentine's Day, Halloween, Christmas…), written as `month * 100 + day`;
- always 255 while the clock-change penalty is active
  ([day-night-and-rtc.md](day-night-and-rtc.md)).

**Flame Body and Magma Armor** (`GetEggCyclesToSubtract`, line 651): if any non-egg party
member has either ability, eggs lose 2 cycles at a time (1 if only 1 is left).

So an egg with `eggCycles` *N* hatches after about (*N* + 1) × 255 steps, or
(⌈*N*/2⌉ + 1) × 255 with Flame Body. The first cycle can be shorter, since the counter is
shared and doesn't restart when you get an egg.

### Egg level and the hatched Pokémon

`HatchEggMon` (line 989) calls `HatchEgg_RecreateMon` (line 902), which **creates the
Pokémon again** with `CreateMon` at `EGG_HATCH_LEVEL` (1), keeping from the egg:
personality, moves and PP, IVs, language, game of origin, markings, Pokérus, the fateful
encounter flag, OT, form, and the egg and met locations and dates. Then:

| Field | Value |
|---|---|
| level | `EGG_HATCH_LEVEL` (1), with the matching experience and stats |
| friendship | `EGG_HATCH_FRIENDSHIP` (120) |
| nickname | the species name (not nicknamed) |
| Poké Ball | Poké Ball |
| met level | 0 |

The Manaphy egg from Pokémon Ranger (egg location `MAPSECTYPE_EXTERNAL`, 1) is rerolled
until it is **not** shiny.

EVs, held item and contest stats are not kept: the new Pokémon starts with none.

## 7. Script commands

All in [src/scrcmd_daycare.c](../../src/scrcmd_daycare.c) except the party menu ones.
Arguments and numbers: [script-commands-list.md](script-commands-list.md).

| Command | Does |
|---|---|
| `getdaycarestate(var)` | `DAYCARE_NO_MONS` 0, `DAYCARE_EGG_WAITING` 1, `DAYCARE_ONE_MON` 2, `DAYCARE_TWO_MONS` 3 |
| `checkdaycareegg(var)` | 1 if an egg is waiting |
| `givedaycareegg` | builds the egg (§3–5) and adds it to the party; clears `egg_pid` |
| `resetdaycareegg` | throws away the waiting egg (when you refuse it) |
| `getdaycarecompatibility(var)` | 0 (best) to 3 (won't breed), §2 |
| `choosepartymonfordaycare`, `getdaycarepartyselection` | the party menu for choosing a mon |
| `daycaresanitizemon(slot, var)` | removes the Griseous Orb and resets forms (§1); `var` = 0xFF if the bag is full |
| `putmonindaycare(slot)` | deposits a party mon |
| `retrievedaycaremon(var, slot)` | withdraws; `var` = its species |
| `bufferdaycarewithdrawcost(var, slot)` | buffers nickname and price; `var` = price |
| `bufferdaycaremongrowth(var, slot)` | buffers nickname and levels gained; `var` = levels gained |
| `bufferdaycaremonnicks`, `bufferdaycaremonstats`, `gettaildaycaremonspeciesandnick` | buffer names, levels and genders for messages |
| `updatedaycaremonobjects` | shows the two Day-Care Pokémon walking in the yard (objects `obj_daycare_poke_1`/`2`) |

The Day-Care Man outside behaves differently when an egg is waiting: `Route34_OnTransition`
sets his movement type to 16 instead of 15 if `checkdaycareegg` returns 1.

## 8. Changing the rules

All of these are C changes; rebuild with `make release` ([README.md](README.md#building-a-modified-rom)).
None of them changes the save layout.

### Everstone always passes the nature (Gen 5+)

In `Daycare_EverstoneCheck` (line 226), remove the two 50% rolls:

```c
    if (num_everstones == 2) {
        everstone_idx = LCRandom() % 2;
        return everstone_idx;
    } else if (num_everstones == 1) {
        return everstone_idx;
    } else {
        return -1;
    }
```

To restrict it to the mother or Ditto (Emerald), check `GetBoxMonGender` / species there
before counting a parent's Everstone.

### Destiny Knot passes five IVs (Gen 6+)

In HGSS the Destiny Knot (`ITEM_DESTINY_KNOT`, 280) only has its battle effect (when the
holder is infatuated, the Pokémon that caused it is infatuated too). `src/get_egg.c` never
checks it. To make it pass five
IVs from the parents, add a count to `include/constants/daycare.h`:

```c
#define NUM_INHERITED_IVS_DESTINY_KNOT 5
```

and make `InheritIVs` (line 297) use a variable count:

```c
static void InheritIVs(Pokemon *egg, Daycare *dayCare) {
    u8 statsToInherit[NUM_INHERITED_IVS_DESTINY_KNOT];
    u8 statList[NUM_STATS];
    u8 monToInheritFrom[NUM_INHERITED_IVS_DESTINY_KNOT];
    BoxPokemon *parents[NUM_DAYCARE_MONS];
    u8 numInherited;
    ...

    Daycare_GetBothBoxMonsPtr(dayCare, parents);
    if (GetBoxMonData(parents[0], MON_DATA_HELD_ITEM, NULL) == ITEM_DESTINY_KNOT
        || GetBoxMonData(parents[1], MON_DATA_HELD_ITEM, NULL) == ITEM_DESTINY_KNOT) {
        numInherited = NUM_INHERITED_IVS_DESTINY_KNOT;
    } else {
        numInherited = NUM_INHERITED_IVS;
    }
```

then replace `NUM_INHERITED_IVS` with `numInherited` in the three `for` loops and delete the
three `GF_ASSERT` lines (they only compare the first three entries; the picking already
removes each chosen stat from `statList`, so stats can't repeat). A Power item still forces
its stat as one of the five. Update the Destiny Knot's description in
`data/items/items.json` ([items.md](items.md)).

### Egg level

Change `EGG_HATCH_LEVEL` in `include/constants/daycare.h`. It is used in three places:

- `SetBreedEggStats`: Day-Care eggs, so the egg starts with the moves the species knows at
  that level (§5);
- `SetEggStats`: gift eggs from scripts (`giveegg`, the Togepi egg from Mr. Pokémon);
- `HatchEgg_RecreateMon`: the level the Pokémon hatches at, with matching experience and
  stats.

Eggs already in a save hatch at the new level, but keep the moves they were created with.
Keep the met level 0: it is what marks a Pokémon as hatched.

### Other numbers

| Change | Where |
|---|---|
| egg chance per check | `PARENTS_*_COMPATIBILITY` in `constants/daycare.h`, or the table in `ComputeCompatibilityBetweenBoxMons` |
| how often eggs are rolled | `DAYCARE_BREED_CHECK_STEPS`; keep it ≤ 255, since it is compared with a `u8` (§2) |
| steps per egg cycle | `EGG_CYCLE_STEPS`, `EGG_CYCLE_STEPS_SPECIAL_DAY`, `sEggCycleSpecialDates`; `egg_cycles` is a `u8`, so keep them ≤ 255 |
| how long one species takes | its `eggCycles` in `personal.json` |
| Flame Body / Magma Armor | `GetEggCyclesToSubtract` |
| number of IVs passed | `NUM_INHERITED_IVS` (at most 6) |
| Masuda rerolls | `MASUDA_METHOD_REROLLS` |
| friendship on hatching | `EGG_HATCH_FRIENDSHIP` |
| Day-Care fee | `DAYCARE_PRICE_PER_LEVEL` |
| keep the mother's Poké Ball | set `pokeball` from the mother in `SetBreedEggStats` **and** stop `HatchEggMon` resetting it |
| incense babies | `sIncenseMons` |
| the species an egg hatches into | `pms.narc` ([adding-a-species.md §4](adding-a-species.md#4-egg-species-pmsnarc)) |

## Not verified

- The Day-Care Man and Lady's dialogue scripts (`scr_seq_0265.s`) were not read beyond
  their use of the commands above.
- Whether anything outside `src/get_egg.c` treats a level other than 1 as special for a
  freshly hatched Pokémon (only `EGG_HATCH_LEVEL`'s three uses were checked).
- The Destiny Knot change above has not been built or tested.
