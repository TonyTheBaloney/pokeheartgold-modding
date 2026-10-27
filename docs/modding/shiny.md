<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27 -->

# Shiny Pokémon

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the game decides a Pokémon is shiny, where every Pokémon's chance comes from (wild,
static, roaming, gifts, eggs, trades, trainers, the Frontier), the forced-shiny Red
Gyarados, how a shiny looks different, and the usual changes: other odds, a Shiny Charm,
forced or shiny-locked encounters, and shiny trainer or trade Pokémon.

| pokeemerald | here |
|---|---|
| `IsMonShiny`, `GET_SHINY_VALUE` | `MonIsShiny`, `BoxMonIsShiny`, `CalcShininessByOtIdAndPersonality`, macro `SHINY_CHECK` (`src/pokemon.c:71`) |
| `SHINY_ODDS` (`include/constants/pokemon.h`) | `SHINY_ODDS` exists but **nothing reads it**; the `8u` is written into `SHINY_CHECK` ([§6.1](#61-change-the-odds)) |
| `I_SHINY_CHARM_ADDITIONAL_ROLLS` (expansion) | no Shiny Charm; [§6.2](#62-a-shiny-charm) |
| `FLAG_SHINY_CREATION` / `P_FLAG_FORCE_SHINY` (expansion) | `wildbattle(species, level, 1)` for one battle; [§6.3](#63-force-every-wild-pokémon-shiny-with-a-flag) for a flag |
| `P_FLAG_FORCE_NO_SHINY` (expansion) | `OT_ID_RANDOM_NO_SHINY` in C; nothing for scripts; [§6.4](#64-shiny-locked-static-encounters) |

## 1. What makes a Pokémon shiny

Shininess is **not stored**. It is worked out each time from two 32-bit values saved in the
Pokémon: its personality value (PID) and its original trainer's id (OT id, visible id in
the low 16 bits, secret id in the high 16):

```c
// src/pokemon.c:71
#define SHINY_CHECK(otid, pid) ((otid >> 16) ^ (otid & 0xFFFF) ^ (pid >> 16) ^ (pid & 0xFFFF)) < 8u
```

(Simplified; the real macro masks each half.) That is 8 values out of 65536, **1 in 8192**.
`BoxMonIsShiny` (`:2125`) reads both fields and calls `CalcShininessByOtIdAndPersonality`,
which is the macro. Every screen and the battle engine go through these.

Consequences:

- A traded Pokémon stays shiny (or not): its OT id travels with it.
- Writing `MON_DATA_OT_ID` or `MON_DATA_PERSONALITY` can change shininess. Wild Pokémon are
  built with OT id 0 and given yours afterwards (`SetMonData(wildMon, MON_DATA_OT_ID, ...)`),
  so the check that counts is against your id.
- Changing the formula or the odds changes **existing** Pokémon in a save too
  ([§6.1](#61-change-the-odds)).

The player's id is one `MTRandom()` at New Game (`src/overlay_36.c:193-196`,
`PlayerProfile_SetTrainerID`).

### Making a shiny PID: `GenerateShinyPersonality`

`GenerateShinyPersonality(otid)` (`src/pokemon.c:2135`) builds a PID that is always shiny
for that OT id: bits 3-15 of the two PID halves are chosen so their XOR equals the OT id's,
and bits 0-2 are random, so the final XOR is 0-7. Nature, gender and ability slot come out
random. IVs are separate from the PID in this game (`CreateBoxMon` rolls them with their own
`LCRandom` calls), so a forced shiny has ordinary random IVs.

`ChangePersonalityToNatureGenderAndAbility(otid, species, nature, gender, ability, shiny)`
(`:3867`) also takes a shiny switch. With `shiny` TRUE the PID's high half is the low half
XOR the OT id's XOR (always shiny); with FALSE its top byte is chosen to be never shiny. The
Pokéwalker uses it ([pokewalker.md](pokewalker.md)), and so does the spiky-eared Pichu gift,
with FALSE.

## 2. Who can be shiny, and how

| Source | Chance | Code |
|---|---|---|
| Wild: grass, surf, fishing, Rock Smash, Headbutt, swarms, sounds | 1/8192 | `generateWildNonShinyAndAddToParty` (`src/field/encounter_check.c:825`). **Despite its name, it doesn't prevent shinies**; it just doesn't force one |
| Wild with a Cute Charm lead (2 times in 3) | 0, or up to about 1 in 5 (see below) | same, `CreateMonWithGenderNatureLetter` |
| Safari Zone, Bug-Catching Contest | 1/8192 | same function, `forceOnePerfectIV` TRUE: up to 4 tries for a 31 IV, each its own PID |
| Static encounters (`wildbattle(..., 0)`) | 1/8192 | `FieldSystem_GenerateSingleWildPokemon` (`:992`) |
| Red Gyarados (`wildbattle(..., 1)`) | always | `generateWildShinyAndAddToParty` (`:769`) |
| Roamers | 1/8192, **rolled once** | PID made when the roamer is set up (`src/field_roamer.c:213`), saved as `ROAMER_DATA_PERSONALITY`; `initRoamingWildmon` (`:1202`) reuses it each time you meet it |
| `givemon` (starters, Eevee, Dratini, Sinjoh legendaries...) | 1/8192 | `GiveMon`, `src/script_pokemon_util.c:24`; the starters, `src/choose_starter.c:62` |
| `givecustommon` (not retail) | chosen | [gift-pokemon-and-trades.md §3](gift-pokemon-and-trades.md#3-custom-gifts-givecustommon) |
| Gift eggs (`giveegg`) | 1/8192 | `SetEggStats`, `src/get_egg.c:567` |
| Day-Care eggs | 1/8192; about 5/8192 with parents of two languages (Masuda) | `SetBreedEggStats` (`get_egg.c:602`); [breeding.md](breeding.md#shininess-the-masuda-method) |
| Manaphy egg from Pokémon Ranger | never: rerolled while shiny when it hatches | `get_egg.c:942` |
| Pokéwalker catches and gifts | as the walker's data says | [pokewalker.md](pokewalker.md) |
| In-game trades | fixed by `personality` + `ot_id` in `data/npc_trades.json`; none of the retail ones is shiny | `src/npc_trade.c`; `GF_ASSERT(!MonIsShiny(mon))` at `:236` (only in builds with asserts) |
| Spiky-eared Pichu (`givespikyearpichu`) | never | `ScrCmd_GiveSpikyEarPichu` (`src/field/scrcmd_pokemon_misc.c:1102`), `ChangePersonalityToNatureGenderAndAbility(..., FALSE)` |
| Trainers' Pokémon | never | `OT_ID_RANDOM_NO_SHINY` in `src/trainer_data.c:337`, `:370`, `:397`, `:422` |
| Battle Frontier trainers, Battle Hall | never | `src/frontier/frontier_trainers.c:141`, `:199`; `BattleHall_RerollPersonality` (`src/frontier/battle_hall_setup.c:312`) |
| Catching-tutorial Marill and Rattata, the Dragonite in Lance's fly-away scene | never | `src/battle/battle_setup.c:130-132`, `src/field/script_field_effects.c:876` |

### `CreateMon`'s OT id argument

| `otIdType` | Name | OT id given |
|---|---|---|
| 0 | `OT_ID_PLAYER_ID` | **0**, despite the name. Callers set the real one later (`MonSetCatchData`, `SetMonData`) |
| 1 | `OT_ID_PRESET` | `fixedOtId` |
| 2 | `OT_ID_RANDOM_NO_SHINY` | random, re-rolled until the Pokémon isn't shiny (`src/pokemon.c:202-204`) |

Trainer Pokémon get a random OT id that isn't shiny for their (fixed) PID. That's the
whole shiny lock for trainers.

### Synchronize and Cute Charm with a forced shiny

`generateWildShinyAndAddToParty` respects the lead: with Synchronize (half the time) it
calls `GenerateShinyPersonality` until the nature matches; with Cute Charm (2 times in 3,
only for species with both genders) until the gender is the opposite of the lead's. So the
Red Gyarados can be Synchronized.

### The Cute Charm quirk

With a Cute Charm lead, the 2-in-3 forced-gender branch uses
`GenPersonalityByGenderAndNature` (`src/pokemon.c:283`): the PID is just the nature for a
female, or a small number above the gender threshold plus the nature for a male. Its high
half is always 0 and it never goes above 224. The PID no longer depends on the RNG, only on
the nature, so for most players those encounters are **never** shiny, while a player whose
visible id XOR secret id is below about 232 gets a shiny every time the right nature comes
up: up to 8 of the 25 natures, about 1 encounter in 5. This is the well-known Gen 4 Cute
Charm glitch, left as in retail.

## 3. The Red Gyarados

`LakeOfRage_EventScript_Gyarados1` (`data/maps/LakeOfRage/scripts.pory:248`):

```
setflag(FLAG_ENGAGING_STATIC_POKEMON)
wildbattle(SPECIES_GYARADOS, 30, 1)      // 1 = shiny
clearflag(FLAG_ENGAGING_STATIC_POKEMON)
```

- It is the only `wildbattle` that passes 1 (`grep -rn 'wildbattle(' data/maps | grep -v ', 0)'`).
- The overworld object is its own sprite, `SPRITE_RGYARADOSU` (`obj_T29_rgyaradosu` in
  `data/maps/LakeOfRage/map.json`), already red. It isn't a palette swap of the follower.
- Shiny is the only thing special about the Pokémon. It is level 30 with random IVs,
  nature and moves, exactly like any static ([static-encounters.md §1](static-encounters.md#1-the-wildbattle-command)).
- After the battle, unless you lost, the script gives the Red Scale (`FLAG_GOT_RED_SCALE`),
  and a catch sets `FLAG_CAUGHT_RED_GYARADOS`. It is hidden by
  `FLAG_HIDE_LAKE_OF_RAGE_RED_GYARADOS` and comes back after the Hall of Fame if not caught
  ([static-encounters.md §3](static-encounters.md#3-the-static-encounters)).

To make it an ordinary Gyarados, change the 1 to 0 (and, for a blue overworld object,
the sprite to `SPRITE_FOLLOWER_MON_GYARADOS`). To make any other static shiny,
pass 1.

The `shiny` byte is read with `ScriptReadByte` (`src/scrcmd_c.c:2587`), so it must be a
number, not a variable, and `FieldSystem_GenerateSingleWildPokemon` treats any non-zero
value as shiny.

## 4. How a shiny looks

| Where | What changes | Code / data |
|---|---|---|
| Battle sprites | the second palette of the species: palette member `species * 6 + 4 + shiny` in `pokegra.narc`; the back picture's palette is the shiny one ([pokemon.md](pokemon.md#graphics)). Forms use their own pairs ([forms.md](forms.md)) | `GetMonSpriteCharAndPlttNarcIdsEx`, `src/pokemon.c:2189` |
| Battle entry | the sparkle, effect animation 11, after the Pokémon's own animation, on wild encounter, send-out and trainer slide-in | `data/battle_anims/effects/0011_SHINY.anim`; `BATTLE_ANIMATION_SHINY`; the `*_SHINY_ANIM` states in `src/battle/battle_controller_opponent.c` (`:3045`, `:3246`, `:3347`, `:3478`, `:3560`), which also handles the player's side |
| In battle | `BattleMon.shiny`, set on switch-in (`src/battle/battle_util.c:100`), readable as `BMON_DATA_IS_SHINY` | [battle-engine.md](battle-engine.md) adds a `CheckIsShiny` command as an example |
| Summary | the shiny star (sprite 52, not for eggs) and the Dex number in red | [summary-screen.md](summary-screen.md#markings-shiny-star-pokérus-status-item) |
| Following Pokémon | the follower's second palette: bit 0 of object parameter 2 | `FollowMon_SetObjectShiny`, `src/follow_mon.c:1850`; [following-pokemon.md](following-pokemon.md), [adding-a-species.md](adding-a-species.md) (`--palette 1`) |
| Day-Care, photos, Hall of Fame, Pokéathlon, VS Recorder, main menu, certificates, the Arceus cinematic | shiny palette or follower palette | `MonIsShiny` / `CalcShininessByOtIdAndPersonality` callers |
| Party and PC icons | **nothing**: Gen 4 icons have no shiny palette | [ideas/shiny-icons.md](../ideas/shiny-icons.md) |

## 5. Other things that check shininess

- The spiky-eared Pichu event (`EVENT_SPIKY_EARED_PICHU`, `src/scrcmd_c.c:4405`): the
  Ilex Forest shrine scene needs a **shiny** Pichu, Pikachu or Raichu from the matching
  distribution in the party. The Pichu it then gives is never shiny.
- Masuda method and the Manaphy egg (above).
- Nothing in battle damage, catch rate or experience looks at shininess.

## 6. Recipes

Recipes 6.1-6.4 were built together with `make heartgold`, then reverted (all 4 HeartGold
checksums OK afterwards). They were **not play-tested**. 6.5 and 6.6 were not built.

### 6.1 Change the odds

Make `SHINY_CHECK` use the constant, then change the constant. In `src/pokemon.c`:

```diff
 #define SHINY_CHECK(otid, pid) ((                                                                                                              \
                                     (((otid) & 0xFFFF0000u) >> 16u) ^ ((otid) & 0xFFFFu) ^ (((pid) & 0xFFFF0000u) >> 16u) ^ ((pid) & 0xFFFFu)) \
-    < 8u)
+    < SHINY_ODDS)
```

With `SHINY_ODDS` still 8 this builds the retail ROM byte for byte (checked). Then, in
`include/constants/pokemon.h`, `#define SHINY_ODDS 16` gives 1/4096 (Gen 6+), 64 gives
1/1024, and so on: the chance is `SHINY_ODDS / 65536`.

Everything that tests shininess goes through the macro, so the Masuda rerolls, the trainer
and Frontier no-shiny loops and `givecustommon` all follow. Two things to know:

- **Existing Pokémon change.** Since shininess isn't stored, raising the odds turns some of
  the player's current Pokémon (and Pokémon in old saves) shiny. Lowering it does the
  opposite.
- **Values below 8 break forced shinies.** `GenerateShinyPersonality` makes the XOR 0-7, so
  with `SHINY_ODDS` 1-7 the Red Gyarados is shiny only sometimes. Keep it at 8 or more, or
  clear `pidLow`'s random low bits in `GenerateShinyPersonality`.
- Other games (link trades, the Pokéwalker, Poké Transfer to Black and White) still use 8.

### 6.2 A Shiny Charm

Gen 5's Shiny Charm gives wild Pokémon 2 extra rolls. Add the key item first
([items.md](items.md#adding-an-item)), as `ITEM_SHINY_CHARM`. Then:

`include/constants/pokemon.h`:

```c
#define SHINY_CHARM_REROLLS 2 // extra rolls for wild Pokemon while the Shiny Charm is in the bag
```

`src/field/encounter_check.c`: include `bag.h` and `constants/items.h`, and add a field to
`EncounterGenState`:

```diff
     u8 unownPuzzleFlags[ALPH_PUZZLE_MAX];
     Pokedex *pokedex;
+    u8 shinyRerolls;
 } EncounterGenState;
```

At the end of `EncounterGenState_Init`:

```c
    encounterGen->shinyRerolls = Bag_HasItem(Save_Bag_Get(fieldSystem->saveData), ITEM_SHINY_CHARM, 1, HEAP_ID_FIELD1) ? SHINY_CHARM_REROLLS : 0;
```

Above `generateWildNonShinyAndAddToParty`, a helper that rebuilds the Pokémon until it's
shiny or the rolls run out:

```c
static void createWildMonWithNature(Pokemon *wildMon, u16 species, u8 level, u8 nature, EncounterGenState *encounterGen) {
    CreateMonWithNature(wildMon, species, level, USE_RANDOM_IVS, nature);
    for (int i = 0; i < encounterGen->shinyRerolls; i++) {
        if (CalcShininessByOtIdAndPersonality(encounterGen->playerId, GetMonData(wildMon, MON_DATA_PERSONALITY, NULL))) {
            return;
        }
        CreateMonWithNature(wildMon, species, level, USE_RANDOM_IVS, nature);
    }
}
```

and use it for both `CreateMonWithNature` calls in `generateWildNonShinyAndAddToParty`:

```diff
-            CreateMonWithNature(wildMon, species, level, USE_RANDOM_IVS, getWildMonNature(leadMon, encounterGen));
+            createWildMonWithNature(wildMon, species, level, getWildMonNature(leadMon, encounterGen), encounterGen);
```

The check uses `encounterGen->playerId` because the wild Pokémon's own OT id is still 0
at that point. This covers every wild, Safari, Bug Contest and static encounter. It doesn't
cover:

- the Cute Charm branch (its PID can't be rerolled, [§2](#the-cute-charm-quirk));
- roamers (their PID is made in `src/field_roamer.c:213`: reroll there the same way if you
  want it);
- eggs: for those, run the Masuda loop in `SetBreedEggStats` (`src/get_egg.c:607`) also
  when the player has the charm, adding `SHINY_CHARM_REROLLS` to the loop count.

### 6.3 Force every wild Pokémon shiny with a flag

For a "shiny event" or a debug switch. Pick a free flag
([unknown-flags-vars.md](unknown-flags-vars.md#free-flags)); here `0x40`, renamed in
`include/constants/flags.h`:

```diff
-#define FLAG_UNK_040      0x40
+#define FLAG_FORCE_SHINY  0x40
```

In `src/field/encounter_check.c`, add `BOOL forceShiny;` to `EncounterGenState`, set it at
the end of `EncounterGenState_Init` (`saveVarsFlags` is already there):

```c
    encounterGen->forceShiny = Save_VarsFlags_CheckFlagInArray(saveVarsFlags, FLAG_FORCE_SHINY);
```

and send the normal path to the forced one, at the top of
`generateWildNonShinyAndAddToParty`, before `AllocMonZeroed`:

```c
    if (encounterGen->forceShiny) {
        generateWildShinyAndAddToParty(species, level, battler, encounterGen->playerId, encounterGen, leadMon, battleSetup);
        return;
    }
```

`setflag(FLAG_FORCE_SHINY)` in a script then makes every wild and static Pokémon shiny
until `clearflag`. Roamers keep their own PID. Safari and Bug Contest Pokémon lose their
perfect-IV tries while it's on.

### 6.4 Shiny-locked static encounters

`wildbattle(..., 0)` still allows a 1/8192 shiny. To lock one, give the `shiny` byte a
third value, 2. Add `BOOL noShiny;` to `EncounterGenState`, `encounterGen->noShiny = FALSE;`
in `EncounterGenState_Init`, and in `FieldSystem_GenerateSingleWildPokemon`:

```diff
     EncounterGenState_Init(fieldSystem, leadMon, NULL, &encounterGen);
-    if (shiny) {
+    encounterGen.noShiny = (shiny == 2);
+    if (shiny == 1) {
```

At the end of `createWildMonWithNature` from [§6.2](#62-a-shiny-charm) (add that helper
even without the charm):

```c
    while (encounterGen->noShiny && CalcShininessByOtIdAndPersonality(encounterGen->playerId, GetMonData(wildMon, MON_DATA_PERSONALITY, NULL))) {
        CreateMonWithNature(wildMon, species, level, USE_RANDOM_IVS, nature);
    }
```

and skip the Cute Charm branch for locked Pokémon, since its PID can't be rerolled:

```diff
-    if (canCoerceGender && !encounterGen->isEgg && encounterGen->ability == ABILITY_CUTE_CHARM && LCRandRange(3) != 0) {
+    if (canCoerceGender && !encounterGen->noShiny && !encounterGen->isEgg && encounterGen->ability == ABILITY_CUTE_CHARM && LCRandRange(3) != 0) {
```

Then `wildbattle(SPECIES_MEWTWO, 70, 2)` is never shiny. With 6.3 too, the flag wins
(it returns before the lock is looked at).

### 6.5 A shiny trainer Pokémon (not built)

Trainer PIDs are fixed per trainer, and `OT_ID_RANDOM_NO_SHINY` then picks a non-shiny OT
id. To make one shiny, give it an OT id that matches its PID. In each of the four
`CreateMon` calls in `src/trainer_data.c` (`:337`...), for the Pokémon you want:

```c
if (enemies->trainerId[partyIndex] == TRAINER_LEADER_CLAIR && i == 0) {
    u32 otId = ((personality & 0xFFFF) ^ (personality >> 16)) << 16; // XOR of the halves is 0
    CreateMon(mon, species, monSpecies[i].level, iv, TRUE, (s32)personality, OT_ID_PRESET, otId);
} else {
    CreateMon(mon, species, monSpecies[i].level, iv, TRUE, (s32)personality, OT_ID_RANDOM_NO_SHINY, 0);
}
```

Nature, gender and ability stay what they were, because the PID doesn't change. The
sparkle plays on the trainer's slide-in and send-out. `TRAINER_LEADER_CLAIR` is an
example; use the `TRAINER_*` from `include/constants/trainers.h`.

### 6.6 A shiny in-game trade (not built)

A trade's shininess comes from `personality` and `ot_id` in `data/npc_trades.json`.
`npctrade.py pid` avoids shiny values, so find one by hand: the PID's high half must be
its low half XOR `(ot_id >> 16) ^ (ot_id & 0xFFFF)` (give or take the low 3 bits), and
`personality % 25` is the nature:

```sh
python3 -c "
ot=48926; tsv=(ot>>16)^(ot&0xFFFF); nature=3   # Adamant
print(next(p for lo in range(65536) for p in [((lo^tsv)<<16)|lo] if p%25==nature))"
```

Check the gender (low byte against the species' gender ratio) and the ability slot (bit
0) the same way, then `python3 tools/npctrade/npctrade.py build`. The
`GF_ASSERT(!MonIsShiny(mon))` in `src/npc_trade.c:236` only exists in builds with
`PM_KEEP_ASSERTS`; remove it if you build that way.

## 7. Legitimacy outside the hack

Players call a Pokémon *legitimate* when an unmodified game could have made it. Checkers
such as PKHeX test this when Pokémon leave a game (link trades with retail cartridges,
Poké Transfer to Black and White, then on to Pokémon HOME). They compare the species,
level, met location and ball with a known encounter, and check that the PID and IVs could
have come from the game's RNG the way that encounter uses it. Inside the hack nothing
checks any of this.

| Shiny | Detectable outside the hack? |
|---|---|
| Red Gyarados as shipped | No. Its `GenerateShinyPersonality` PID is the pattern checkers expect for that encounter (level 30, Lake of Rage) |
| Wild shinies at other odds ([§6.1](#61-change-the-odds)) | No, each one is an ordinary roll that looks lucky. But with `SHINY_ODDS` above 8, a Pokémon whose XOR is 8 or more is shiny in the hack and **not shiny** in every other game |
| Shiny Charm ([§6.2](#62-a-shiny-charm)) | No, each reroll is a normal fresh roll |
| Force-shiny flag ([§6.3](#63-force-every-wild-pokémon-shiny-with-a-flag)) | Probably. A wild species with the forced-shiny PID pattern matches no retail encounter |
| Shiny-locked statics ([§6.4](#64-shiny-locked-static-encounters)) | Nothing to detect |
| Shiny trainer Pokémon ([§6.5](#65-a-shiny-trainer-pokémon-not-built)) | Trainer Pokémon can't be caught, so they never leave the game |
| Shiny in-game trade ([§6.6](#66-a-shiny-in-game-trade-not-built)) | Yes. Its PID or OT id no longer matches the retail trade data |

Strictly, nothing made by a modified ROM is legitimate, even when no checker can tell. If
players will move Pokémon out, prefer recipes that keep each roll ordinary (6.1, 6.2) and
keep `SHINY_ODDS` at 8 if shininess should look the same in other games.

## Not verified

- None of the recipes were play-tested. 6.1-6.4 were built (HeartGold), 6.5 and 6.6 were not.
- The Cute Charm numbers (PID at most 224, up to 8 of 25 natures) come from reading
  `GenPersonalityByGenderAndNature`, not from a test.
- That the spiky-eared Pichu scene needs the shiny distribution Pichu comes from the code
  (`src/scrcmd_c.c:4405`); the Ilex Forest script around it wasn't traced.
- Whether the sparkle plays when a Pokémon comes back in after Baton Pass or U-turn wasn't
  traced; only the states listed in §4 were read.
- §7 comes from how PKHeX is known to check Gen 4 Pokémon, not from running it on Pokémon
  made with these recipes.
