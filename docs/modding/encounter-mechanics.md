<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Wild encounter mechanics

> AI-generated; not affiliated with pret. See AI.md at the repository root.

[wild-encounters.md](wild-encounters.md) covers the tables (what is in each map's
grass, surf and fishing slots). This guide covers what the game does with them: how
often an encounter happens, how a slot and level are picked, what Repel, the Cleanse Tag,
flutes, abilities and the radio change, how fishing decides on a bite, how swarms work, and
how to switch a map's Pokémon from a script.

Almost everything is in [src/field/encounter_check.c](../../src/field/encounter_check.c).
Rolls use `LCRandRange(100)`, a number from 0 to 99, so "roll < 25" is a 25% chance.

## 1. Which check runs

| Way | Function | Uses the table's |
|---|---|---|
| Walking, running, cycling on an encounter tile | `FieldSystem_PerformLandOrSurfEncounterCheck` ([:218](../../src/field/encounter_check.c#L218)) | `land.rate` |
| Surfing on an encounter tile | same function | `surf.rate` |
| Using a rod | `FieldSystem_PerformFishEncounterCheck` ([:333](../../src/field/encounter_check.c#L333)) | `fishing.<rod>.rate` |
| Rock Smash | `FieldSystem_PerformRockSmashEncounterCheck` ([:380](../../src/field/encounter_check.c#L380)) | `rock_smash.rate` |
| Sweet Scent, Honey | `FieldSystem_PerformSweetScentEncounterCheck` ([:413](../../src/field/encounter_check.c#L413)) | none: always an encounter |
| Headbutt | `FieldSystem_PerformHeadbuttEncounterCheck` ([:496](../../src/field/encounter_check.c#L496)) | `headbutt.json` ([wild-encounters.md](wild-encounters.md#headbutt-trees)) |

**Encounter tiles.** The step check runs when the player finishes a step
(`FieldSystem_CheckWildEncounter`, [field_control.c:471](../../src/field/field_control.c#L471))
on a map whose header has a table. The tile's behavior must have the "walking encounters" bit
(`MetatileBehavior_CanGenerateWalkingEncounters`, bit `2` of `sMetatileBehaviorFlags` in
[src/metatile_behavior.c](../../src/metatile_behavior.c)). Surfable water uses the surf
table; any other encounter tile (grass, cave floor...) uses the land table.

**Grace steps.** `fieldSystem->encounterInhibitSteps` counts steps; no step check happens
until it is above 3. It is reset to 0 after a battle, a warp and crossing into a connected
map, so the first three steps after any of those are always safe.

## 2. The step encounter roll

A step encounter needs **two** rolls to pass (`FieldSystem_EncounterRateRoll`,
[:568](../../src/field/encounter_check.c#L568)):

```
chance per step = movement% × rate%
```

### Movement factor

Built from 40 in a `u8`, then capped at 100:

| Condition | Change | Walking | Running | Cycling | Surfing |
|---|---|---:|---:|---:|---:|
| start | 40 | | | | |
| walking (not running, cycling or surfing) | −20 | 20 | 40 | 40 | 40 |
| very tall grass (`MetatileBehavior_IsVeryTallGrass`) | +40 | 60 | 80 | | |
| cycling, outside very tall grass | +30 | | | 70 | |
| turnaround counter 2 / 3 / 4+ | +30 / +40 / +60 | | | | |
| radio: Pokémon March | +25 | | | | |
| radio: Pokémon Lullaby | −25 | (see below) | | | |

**Turnaround counter.** `fieldSystem->reverseTurnFrameSteps`
(`FieldSystem_UpdateTurnFrameCounter`, [:1400](../../src/field/encounter_check.c#L1400)).
Every time a step check runs, it goes up by one if the player now faces the opposite way from
the previous check, for example when walking back and forth in a patch of grass. It resets
to 0 after a battle, a warp or crossing into a connected map. So pacing over the same grass
makes encounters come faster: walking with 4 or more turnarounds is 20 + 60 = 80.

**Lullaby while walking.** The factor is a `u8`, so walking (20) with the Lullaby
(−25) wraps around to 251, which the cap turns into **100**. As the code reads, the Lullaby
makes encounters *more* frequent when walking without turnarounds, and less frequent in
every other case (running 15, cycling 45, surfing 15). To fix it, make `modifiedRate` an
`int` and clamp it to 0 before the cap of 100.

### Rate

The table's `rate` (0-255 in the file; 0 means no step encounters on this kind of tile),
changed in this order:

1. **Lead Pokémon's ability** (`ApplyAbilityEffectToEncounterRate`,
   [:1123](../../src/field/encounter_check.c#L1123)), then capped at 100. See §6.
2. **Flute** (`ApplyFluteEffectToEncounterRate`, [:728](../../src/field/encounter_check.c#L728)):
   Black Flute ÷2, White Flute ×1.5 (rounded down).
3. **Lead Pokémon's held item** (`ApplyLeadMonHeldItemEffectToEncounterRate`,
   [:721](../../src/field/encounter_check.c#L721)): Cleanse Tag or Pure Incense ×2/3,
   rounded down.
4. Capped at 100 again, then rolled: `roll < rate`.

"Lead" here means **party slot 0**, even if it has fainted. If slot 0 holds an egg, abilities
are skipped, and so is the first cap: a table rate above 170 with the White Flute then
overflows the `u8`. Keep table rates at 100 or below.

### Examples

Route 29 has `land.rate` 25:

| Situation | Movement | Rate | Per step |
|---|---:|---:|---:|
| walking | 20 | 25 | 5% |
| running | 40 | 25 | 10% |
| cycling | 70 | 25 | 17.5% |
| walking, 2 turnarounds | 50 | 25 | 12.5% |
| walking, Cleanse Tag | 20 | 16 | 3.2% |
| walking, Black Flute + Cleanse Tag | 20 | 8 | 1.6% |
| running, Arena Trap lead | 40 | 50 | 20% |
| running, March | 65 | 25 | 16.25% |

Rates in the original tables: grass 5-25, surf 5-15, Rock Smash 5-50; rod rates are
25 / 50 / 75 on 70 tables and 100 on one.

### After the roll

If both rolls pass:

1. **Roamer**: if an active roamer is on this map, a 1 in 2 chance the encounter is the
   roamer ([roamers.md](roamers.md#4-meeting-one)).
2. **Slot**: the slot roll for the method (§3), or an ability's pick (§6).
3. **Level**: grass slots have one level; other methods roll between `min` and `max`.
4. **Cancel checks** (`FieldSystem_GenerateRegularEncounter`,
   [:881](../../src/field/encounter_check.c#L881)), in order: an Unown slot before any Ruins
   of Alph puzzle is solved; Keen Eye / Intimidate (§6); Repel (§4). A cancelled encounter is
   simply no encounter this step. The game does **not** roll another slot, so Repel makes
   encounters rarer and never makes them stronger.

## 3. Slots

The slot roll for each method, and the table slots changed before it (in this order):

| Method | Slot odds (%) | Changed before the roll |
|---|---|---|
| Grass, 12 slots | 20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1 | time of day picks `morn` / `day` / `nite` species (Evening uses `day`, Late Night uses `nite`); swarm: slots 0-1; radio Hoenn/Sinnoh sound: slots 2-5 |
| Surf, 5 | 60, 30, 5, 4, 1 | swarm: slot 0 |
| Old Rod, 5 | 40, 30, 15, 10, 5 | swarm: slot 2 |
| Good Rod, 5 | 40, 30, 15, 10, 5 | at night `nightFish`: slot 3; then swarm: slots 0, 2, 3 |
| Super Rod, 5 | 40, 30, 15, 10, 5 | at night `nightFish`: slot 1; then swarm: all 5 |
| Rock Smash, 2 | 80, 20 | — |
| Headbutt, 6 | 50, 15, 15, 10, 5, 5 | — |

What each replacement is worth:

| Replacement | Share of encounters |
|---|---|
| grass swarm (slots 0-1) | 40% |
| radio sound, first species (slots 2-3) / second species (slots 4-5) | 20% / 20% |
| surf swarm | 60% |
| fishing swarm: Old / Good / Super Rod | 15% / 65% / 100% |
| `nightFish`: Good / Super Rod | 10% / 30% |

A replacement only changes the species; the slot keeps its level. The Bug-Catching Contest
and the Safari Zone use their own tables ([wild-encounters.md](wild-encounters.md)). In the
contest the `rate` column is a running threshold, so its ten slots are 20/20/10/10/10/10/5/5/5/5%
([bug-catching-contest.md](bug-catching-contest.md)); in the Safari Zone all ten slots are equally likely
([safari-zone.md](safari-zone.md#encounters)).

## 4. Repel

| | |
|---|---|
| Steps | `holdEffectParam` in `data/items/items.json`: Repel 100, Super Repel 200, Max Repel 250 |
| Counter | `repelSteps` in the roamer save block (a `u8`, so at most 255) |
| Using one | `BagApp_TryUseRepel` ([bag_app.c:1833](../../src/application/bag/bag_app.c#L1833)): refused while one is active |
| Counting down | `PlayerStepEvent_RepelCounterDecrement` ([field_move_cut_in_effects.c:1084](../../src/field/field_move_cut_in_effects.c#L1084)): one per step; at 0 runs `std_repel_wore_off` |
| The rule | `EncounterGen_DoesRepelSuppressEncounter` ([:1184](../../src/field/encounter_check.c#L1184)): no battle if the **first healthy** party Pokémon's level is **above** the wild level. Same level still battles |

Repel applies to step encounters in grass and water, including roamers, the Safari Zone and
the Bug-Catching Contest. It does **not** apply to fishing, Rock Smash, Headbutt or Sweet
Scent: those never set `isRepel`.

With Repel on, the chance per step is the chance from §2 times the share of slots whose level
is at least the first healthy Pokémon's. On a route of level 2-4 Pokémon with a level 5
leader, that share is zero.

For a longer Repel, raise `holdEffectParam` (up to 255). For more, `repelSteps` has to
become a `u16`, which changes the save layout ([save-data.md](save-data.md)).

## 5. Cleanse Tag, Pure Incense and flutes

| Effect | Where | Applies to |
|---|---|---|
| Cleanse Tag, Pure Incense held by party slot 0: rate ×2/3 | `ApplyLeadMonHeldItemEffectToEncounterRate` | step encounters only (not fishing or Rock Smash) |
| Black Flute: rate ÷2 | `ApplyFluteEffectToEncounterRate` | step encounters only |
| White Flute: rate ×1.5 | same | step encounters only |

The two items check `ITEM_CLEANSE_TAG` and `ITEM_PURE_INCENSE` by name. A new item with
the same effect has to be added to that `if`. The held item's `holdEffect` in `items.json`
is not read here.

A flute is stored in `flutePlayed` in the roamer save block (`BagApp_SetFlute`,
[bag_app.c:1814](../../src/application/bag/bag_app.c#L1814)). It is cleared on every warp and
map connection (`FieldSystem_ResetStateOnWarp` and `FieldSystem_ResetStateOnMapConnection`
in [src/field_warp_state.c](../../src/field_warp_state.c)), so it lasts until the player
leaves the map.

## 6. Abilities of the lead Pokémon

The lead is party slot 0. An egg there turns all of these off.

| Ability | Effect | Where |
|---|---|---|
| Arena Trap, No Guard, Illuminate | rate ×2 (steps, Rock Smash) | `ApplyAbilityEffectToEncounterRate` |
| Stench, White Smoke, Quick Feet | rate ÷2 (steps, Rock Smash) | same |
| Snow Cloak | rate ÷2 in `WEATHER_SNOW` only | same |
| Sticky Hold, Suction Cups | bite chance ×2 (fishing) | same |
| Keen Eye, Intimidate | half the time, no encounter if the wild level ≤ lead level − 5 (lead above level 5; not with Sweet Scent). Fishing too: the bite turns into "not even a nibble" | `DoesAbilitySuppressEncounter` ([:1148](../../src/field/encounter_check.c#L1148)) |
| Magnet Pull / Static | half the time, the slot is picked evenly from the slots holding a Steel / Electric species (not used when none or all slots qualify) | `EncounterSlot_AbilityInfluenceOnSlotChoiceCheck` |
| Hustle, Vital Spirit, Pressure | half the time, the highest level: in grass, the same species' highest-level slot; elsewhere the slot's `max` | `ApplyAbilityEffectToSlotLevel`, `EncounterSlot_WildMonLevelRoll` |
| Synchronize | half the time, the wild Pokémon gets the lead's nature | `getWildMonNature` |
| Cute Charm | 2 in 3 chance of the opposite gender | `generateWildNonShinyAndAddToParty` |
| Compound Eyes | better held-item odds | `WildMonSetRandomHeldItem` |

Adding an ability that changes the encounter rate means adding a branch to
`ApplyAbilityEffectToEncounterRate`. See [abilities.md](abilities.md).

## 7. Fishing

Fishing decides everything **before** the cast animation
(`Task_OverworldFish`, [fishing.c](../../src/field/fishing.c)):
`FieldSystem_PerformFishEncounterCheck` picks whether something bites, and which Pokémon it
is. The animation only plays out a result that is already known.

### Bite chance

```
bite% = rod rate + follower bonus, ×2 for Sticky Hold / Suction Cups, capped at 100
```

1. **Rod rate**: `fishing.old_rod.rate` / `good_rod.rate` / `super_rod.rate`. 0 means
   that rod never bites here, and nothing below applies.
2. **Follower bonus** (`getFriendshipBoostToFishingBiteRate`,
   [:1071](../../src/field/encounter_check.c#L1071)): only while a Pokémon is following the
   player. It reads the first healthy party Pokémon's friendship:

   | Friendship | 0-99 | 100-149 | 150-199 | 200-249 | 250-255 |
   |---|---:|---:|---:|---:|---:|
   | bonus | 0 | +20 | +30 | +40 | +50 |

3. **Ability**: Sticky Hold and Suction Cups double it. Repel, Cleanse Tag, flutes, the
   radio and the turnaround counter do nothing for fishing.
4. Roll: `roll < bite%`. Then the slot (§3) and level are picked, and Keen Eye /
   Intimidate can still cancel it. A failed roll or a cancel shows "Not even a nibble...".

With the original rates (25 / 50 / 75), a Good Rod with a very friendly follower always
bites: 50 + 50 = 100.

### Reeling in

When there is a bite (`FishingRodState_SetupBite`,
[fishing.c:298](../../src/field/fishing.c#L298)):

1. The player waits 30, 60, 90 or 120 frames (1 in 4 each). Pressing A during the wait
   loses the Pokémon ("Reeled it in too quickly...").
2. A "!" appears. The player has a window to press A: `sReelWindow`
   ([fishing.c:144](../../src/field/fishing.c#L144)), **45 / 30 / 15 frames** for the Old /
   Good / Super Rod. A following Pokémon adds frames by its mood (`sMoodReelBonus`):

   | Mood | ≤ −10 | −9 to 9 | 10-49 | 50-99 | 100+ |
   |---|---:|---:|---:|---:|---:|
   | Old / Good / Super Rod | +0 / +0 / +0 | +9 / +6 / +3 | +15 / +12 / +6 | +21 / +18 / +9 | +30 / +24 / +12 |

3. Missing the window: "The Pokémon got away...".

When not surfing, the follower may show the "!" instead of the player, with the same
friendship chances as the bite bonus (20-50%). This only changes who shows it.

To make fishing easier, raise the rod rates in the tables, or widen `sReelWindow`.

## 8. Swarms

Swarm data:

| Data | Where |
|---|---|
| The 20 swarm maps, and grass / surf / fishing for each | `sSwarmMapLUT` in [src/swarm.c](../../src/swarm.c) (`0` grass, `1` surf, `2` fishing) |
| The species | that map's table: `landSwarm`, `surfSwarm` or `fishSwarm` in `gs_enc_data.json` |
| Swarms on or off | `outbreak` in the roamer save block |
| Today's swarm | `rand[1]` in the roamer save block |

**Turning swarms on.** `enablemassoutbreaks` sets `outbreak`; nothing turns it off. The
original game runs it when Professor Oak gives the National Dex on the S.S. Aqua
(`data/maps/SsAquaOlivinePortInterior/scripts.pory`).

**Picking the day's swarm.** Every day change, `FieldSystem_HandleDaysPassed`
([src/field_time_events.c](../../src/field_time_events.c)) reseeds `rand[1]`
(`Roamers_SetRand`). Today's swarm is entry `rand[1] % 20` of `sSwarmMapLUT`. There is always
exactly one swarm, at one place, for the whole day.

**Applying it.** Every encounter on that map with that method gets the swarm species in
the slots from §3 (`EncSlots_Update_LandSwarm`, `_SurfingSwarm`, `_FishingSwarm`,
[:169](../../src/field/encounter_check.c#L169)). The check is by **map id**, not by table:
another map that shares the same table doesn't get the swarm.

**Telling the player.** The Pokémon Talk radio show
([pokemon_talk.c](../../src/application/pokegear/radio/shows/pokemon_talk.c)) names the
map and species. Scripts can read them with `getswarmmapandspecies(VAR_MAP, VAR_SPECIES)`
(`ScrCmd_GetSwarmMapAndSpecies`), then `bufferspeciesname`. No original script uses it.

The original swarms, from the current tables:

| # | Map | Method | Species (HG / SS) |
|---:|---|---|---|
| 0 | `MAP_ROUTE_1` | grass | Poochyena |
| 1 | `MAP_ROUTE_3` | grass | Baltoy / Gulpin |
| 2 | `MAP_ROUTE_9` | grass | Sableye / Mawile |
| 3 | `MAP_ROUTE_12` | fishing | Relicanth |
| 4 | `MAP_ROUTE_13` | grass | Chansey |
| 5 | `MAP_ROUTE_19` | surf | Clamperl |
| 6 | `MAP_ROUTE_32` | fishing | Qwilfish |
| 7 | `MAP_ROUTE_25` | grass | Buneary |
| 8 | `MAP_ROUTE_27` | surf | Luvdisc |
| 9 | `MAP_ROUTE_34` | grass | Ralts |
| 10 | `MAP_ROUTE_35` | grass | Yanma |
| 11 | `MAP_ROUTE_38` | grass | Snubbull |
| 12 | `MAP_ROUTE_44` | fishing | Remoraid |
| 13 | `MAP_ROUTE_45` | grass | Swablu |
| 14 | `MAP_ROUTE_47` | grass | Ditto |
| 15 | `MAP_MOUNT_MORTAR_1F_ENTRANCE` | grass | Marill |
| 16 | `MAP_DARK_CAVE_ROUTE_31_SIDE` | grass | Dunsparce |
| 17 | `MAP_VIRIDIAN_FOREST` | grass | Kricketot |
| 18 | `MAP_VERMILION` | surf | Wingull |
| 19 | `MAP_VIOLET` | fishing | Whiscash |

Every table has `landSwarm` etc., but only these 20 maps ever use them.

### Changing swarms

- **Species**: edit `landSwarm` / `surfSwarm` / `fishSwarm` in that map's entry of
  `gs_enc_data.json`.
- **Map or method**: edit the entry in `sSwarmMapLUT`. The map's table must have a species
  in the matching key: `GetSwarmInfoFromRand` asserts it isn't `SPECIES_NONE`.
- **More or fewer swarm maps**: add or remove entries and change `SWARM_MAP_COUNT`. Saves
  stay valid; the day's swarm just moves to `rand[1] % new count`.
- **How strong a swarm is**: the slot lists in `EncSlots_Update_*Swarm` (§3). For example,
  `EncSlots_Update_LandSwarm` gets slots 0 and 1; pass more slots to make a grass swarm
  stronger.

## 9. The radio

The Pokégear radio sets a global sequence number (`SndRadio_StartSeq`,
[src/sound_radio_sys.c](../../src/sound_radio_sys.c)), and `GetRadioMusicPlayingSeq`
([src/field/gear_phone_calls.c:276](../../src/field/gear_phone_calls.c#L276)) turns it into:

| Value | Song | Effect on encounters |
|---:|---|---|
| 1 | Pokémon March (or its GB Sounds version) | movement factor +25 |
| 2 | Pokémon Lullaby (or its GB Sounds version) | movement factor −25 (see §2) |
| 3 | Hoenn Sound | grass slots 2-3 → `hoenn[0]`, 4-5 → `hoenn[1]` |
| 4 | Sinnoh Sound | grass slots 2-3 → `sinnoh[0]`, 4-5 → `sinnoh[1]` |
| 5 | Poké Flute | none here |
| 6 | Unown radio | an Unown encounter is, half the time, a letter not yet caught |

The song keeps playing after the Pokégear closes, and the effect lasts until the field
music restarts (`SndRadio_StopSeq` is called from the BGM functions in
[src/sound_playback.c](../../src/sound_playback.c)).

The songs come from the Pokémon Music show
(`RadioShow_PokemonMusic_Setup`,
[pokemon_music.c:96](../../src/application/pokegear/radio/shows/pokemon_music.c#L96)), by
day of the week:

| Day | Song |
|---|---|
| Monday, Friday | March |
| Tuesday, Saturday | Lullaby |
| Wednesday | Hoenn Sound with the National Dex, else March |
| Thursday | Sinnoh Sound with the National Dex, else Lullaby |
| Sunday | a random GB Sounds song with the GB Sounds item, else March |

Hoenn and Sinnoh Sound replace grass slots only, never surf or fishing. They also apply in
the Safari Zone and the Bug-Catching Contest. Those use their own tables, so there the change
does nothing.

Scripts can read the song with `radiomusicisplaying(value, VAR)` (value from the table
above). No script command starts a radio song.

## 10. Switching tables from a script

What a script can already do, with no new C code:

| Goal | How |
|---|---|
| turn on daily swarms | `enablemassoutbreaks` |
| find today's swarm | `getswarmmapandspecies(VAR_A, VAR_B)` |
| check the radio | `radiomusicisplaying(3, VAR_SPECIAL_RESULT)` |
| change the time-of-day species | nothing; they follow the clock ([day-night-and-rtc.md](day-night-and-rtc.md)) |

Anything else needs a small change in C. The three recipes below add script commands as
described in [script-commands.md §6](script-commands.md#6-adding-a-command). 853 is the
next free command number in the original table; use whatever is next in yours.

### Recipe A: choose today's swarm

A command that sets the swarm to entry `n` of `sSwarmMapLUT` and turns swarms on. Useful
for a story event ("Yanma are swarming on Route 35!"). It lasts until the next day change
picks a new swarm.

```c
// src/roamer.c (declare in include/roamer.h)
void Roamers_SetSwarmRand(RoamerSaveData *roamer, u32 value) {
    roamer->rand[1] = value;
}

// src/scrcmd_c.c (declare in include/scrcmd.h)
BOOL ScrCmd_SetSwarm(ScriptContext *ctx) {
    u16 index = ScriptGetVar(ctx);
    RoamerSave_SetOutbreakActive(ctx->fieldSystem->saveData);
    Roamers_SetSwarmRand(Save_Roamers_Get(ctx->fieldSystem->saveData), index);
    return FALSE;
}
```

```
    // Makes entry INDEX of sSwarmMapLUT today's swarm, and turns swarms on
    .macro SetSwarm index
    .short 853
    .short \index
    .endm
```

`setswarm(10)` puts the swarm on Route 35. Nothing else reads `rand[1]`, so this has no
side effects. To make swarms stop, add a matching command that sets `outbreak` back to
`FALSE`.

### Recipe B: Hoenn/Sinnoh slots without the radio

To use the `hoenn` / `sinnoh` species as an event table (after a story flag), check a
flag next to the radio in `EncSlotArray_Update_HoennSinnohSounds`
([:155](../../src/field/encounter_check.c#L155)):

```c
static void EncSlotArray_Update_HoennSinnohSounds(FieldSystem *fieldSystem, const EncounterData *encData, EncounterSlot *encSlots) {
    SaveVarsFlags *varsFlags = Save_VarsFlags_Get(fieldSystem->saveData);
    if (GetRadioMusicPlayingSeq() == RADIO_MUSIC_SEQ_HOENN_SOUNDS || Save_VarsFlags_CheckFlagInArray(varsFlags, FLAG_EVENT_HOENN_MONS)) {
        ...
```

`FLAG_EVENT_HOENN_MONS` is a free flag you define in `include/constants/flags.h`
([unknown-flags-vars.md](unknown-flags-vars.md#free-flags)). Scripts then use
`setflag` / `clearflag`. Since the flag is saved, the change applies on every map, every day,
until it is cleared. Edit `hoenn` in a map's table to choose what appears.

### Recipe C: give a map a different table

A map's table is read once, when the map loads (`Field_InitMapEvents`,
[src/map_events.c:24](../../src/map_events.c#L24)), into
`fieldSystem->mapEvents->wildEncounters`. Every check reads that copy. To swap it, store
the replacement in two saved vars and read them on load:

1. Append a new table to `gs_enc_data.json` (for example, Route 36 after the Sudowoodo is
   gone) and note its array index ([wild-encounters.md](wild-encounters.md#which-table-a-map-uses)).
2. Define two free vars in `include/constants/vars.h`
   ([unknown-flags-vars.md](unknown-flags-vars.md#free-vars)):

   ```c
   #define VAR_ENC_OVERRIDE_MAP  0x4059 // map id that gets the table below
   #define VAR_ENC_OVERRIDE_BANK 0x405A // table index + 1; 0 = off
   ```

3. In `src/map_events.c` (add `#include "constants/vars.h"` and
   `#include "script_manager.h"`):

   ```c
   void Field_LoadWildEncounters(FieldSystem *fieldSystem, u32 mapno) {
       EncounterData *encData = &fieldSystem->mapEvents->wildEncounters;
       u16 overrideBank = FieldSystem_VarGet(fieldSystem, VAR_ENC_OVERRIDE_BANK);

       if (overrideBank != 0 && FieldSystem_VarGet(fieldSystem, VAR_ENC_OVERRIDE_MAP) == mapno) {
           memset(encData, 0, sizeof(EncounterData));
           ReadWholeNarcMemberByIdPair(encData, ENCDATA_NARC, overrideBank - 1);
       } else {
           WildEncounters_ReadFromNarc(encData, mapno);
       }
   }
   ```

   In `Field_InitMapEvents`, replace the `WildEncounters_ReadFromNarc` line with
   `Field_LoadWildEncounters(work, mapno);`, and declare the function in
   `include/map_events.h`.

4. A command to reload it on the spot, for a script that runs on the map itself:

   ```c
   BOOL ScrCmd_ReloadWildEncounters(ScriptContext *ctx) {
       Field_LoadWildEncounters(ctx->fieldSystem, ctx->fieldSystem->location->mapId);
       return FALSE;
   }
   ```

   ```
       // Rereads the current map's wild encounter table (after changing VAR_ENC_OVERRIDE_*)
       .macro ReloadWildEncounters
       .short 854
       .endm
   ```

5. In the script:

   ```
   setvar(VAR_ENC_OVERRIDE_MAP, MAP_ROUTE_36)
   setvar(VAR_ENC_OVERRIDE_BANK, 143)   // table 142 + 1
   reloadwildencounters
   ```

The map still needs a table of its own in its header (`MapHeader_HasWildEncounters`), or
the step check never runs. The map needs grass, water or both on tiles that allow
encounters, and the replacement needs a non-zero rate for each.

The Pokémon Talk radio show and trainers' phone calls read tables straight from the archive
by map (`WildEncounters_ReadFromNarc`), so they still describe the original table. For more
than one swapped map, use more var pairs, or a small array in a free save area
([save-compatibility.md](save-compatibility.md)).

## 11. Quick reference: what affects what

| | Steps (grass/surf) | Fishing | Rock Smash | Sweet Scent |
|---|:-:|:-:|:-:|:-:|
| Table rate | ✓ | ✓ | ✓ | — |
| Movement, turnarounds, March/Lullaby | ✓ | — | — | — |
| Ability rate changes | ✓ | Sticky Hold, Suction Cups | ✓ | — |
| Flutes, Cleanse Tag, Pure Incense | ✓ | — | — | — |
| Follower friendship | — | ✓ | — | — |
| Repel | ✓ | — | — | — |
| Keen Eye, Intimidate | ✓ | ✓ | ✓ | — |
| Roamers | ✓ | — | — | ✓ |
| Swarm slots | ✓ | ✓ | — | ✓ |
| Radio Hoenn/Sinnoh slots | grass | — | — | grass |

## Not verified

These come from reading the code, not from testing in an emulator:

- The Lullaby wrap-around in §2. The code is a byte-for-byte match, so the arithmetic is
  what the cartridge does, but nobody has measured it in game.
- Exactly when turning in place, without taking a step, counts as a turnaround.
  The header comment on `reverseTurnFrameSteps` says it does; the counter only changes
  when a step check runs.
- Which events stop the radio song (only that `SndRadio_StopSeq` runs from the field BGM
  functions).
- The recipes in §10 have not been built or tested.
