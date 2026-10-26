<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Gift Pokémon, gift eggs and in-game trades

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers every way a script hands the player a Pokémon: `givemon` (what it
sets and what it can't), changing the Pokémon afterwards, a `givecustommon` command for
fully specified gifts (IVs, nature, shiny, ball, moves, met location, eggs), `giveegg`,
in-game trades (the trade table, its tool, the scripts, adding a trade), and loaned
Pokémon (Kenya, Shuckie).

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `givemon SPECIES, level, item` | `givemon(SPECIES, level, item, form, ability, VAR)` (§1) |
| `ScriptGiveMonParameterized` (IVs, nature, shiny, ball, moves) | nothing built in; add `givecustommon` (§3) |
| `giveegg SPECIES` | `giveegg(SPECIES, MAPLOC(METLOC_X))` (§4) |
| `sIngameTrades[]` in `trade.c` | `data/npc_trades.json`, built by `tools/npctrade/npctrade.py` (§5) |
| `special CreateInGameTradePokemon` + `DoInGameTradeScene` | `loadnpctrade(n)` ... `npctradeexec(slot)` `npctradeend` (§5) |
| `setmonmove` | `setmonmove(slot, move slot, MOVE_X)` (§2) |

The files:

| File | What |
|---|---|
| [src/scrcmd_party.c](../../src/scrcmd_party.c) | `givemon`, `giveegg`, `setmonmove` and most party commands |
| [src/script_pokemon_util.c](../../src/script_pokemon_util.c) | `GiveMon`, `GiveEgg` (the C behind them) |
| [src/pokemon.c](../../src/pokemon.c) | `CreateMon`, `MonSetCatchData`, personality and shininess helpers |
| [src/trainer_memo.c](../../src/trainer_memo.c) | `MonSetTrainerMemo`: OT, met date and location for each way of obtaining |
| [data/npc_trades.json](../../data/npc_trades.json) | the 13 in-game trades (source for the three files below) |
| `files/a/1/1/2`, [files/msgdata/msg/msg_0200.json](../../files/msgdata/msg/msg_0200.json), [include/constants/npc_trade.h](../../include/constants/npc_trade.h) | the trade table, nicknames and OT names, `NPC_TRADE_*` ids (all generated) |
| [src/npc_trade.c](../../src/npc_trade.c) | building the traded Pokémon (`_CreateTradeMon`), loans |
| [tools/npctrade/npctrade.py](../../tools/npctrade/npctrade.py) | show, check and build the trades |

## 1. `givemon`

```
givemon(SPECIES_EEVEE, 5, ITEM_NONE, 0, 0, VAR_SPECIAL_RESULT)
```

| Argument | Meaning |
|---|---|
| species | `SPECIES_*`, or a var |
| level | 1-100, or a var |
| held item | `ITEM_*` or 0 |
| form | 0 for the normal form (Giratina's Origin Forme is 1...) |
| ability | `ABILITY_*`, or 0 for the usual one (from the personality, see below) |
| result var | 1 if it was added, 0 if the party was full |

All the number arguments can be vars (`VAR_TEMP_x4002` in the Game Corner prize
scripts). What you get (`GiveMon` in
[src/script_pokemon_util.c](../../src/script_pokemon_util.c)):

| Field | Value |
|---|---|
| IVs | random |
| personality | random, so nature, gender, ability slot and shininess are random (shiny 1 in 8192) |
| moves | the last four it learns by level-up at that level |
| ball | **always a Poké Ball** |
| OT | the player (name, ID, gender) |
| met location / level / date | the current map's section, the given level, today |
| encounter type | 24 (the value retail gifts use) |
| friendship | the species' base friendship |
| Pokédex | marked seen and caught |

**A full party is not handled.** The command adds nothing (the Pokémon doesn't go to
the PC) and sets the result var to 0. Every retail gift checks first:

```
getpartycount(VAR_SPECIAL_x8005)
if (var(VAR_SPECIAL_x8005) == 6) {
    npcmsg("Your party is full.")
    ...
}
givemon(SPECIES_DRATINI, 15, 0, 0, 0, VAR_SPECIAL_RESULT)
```

A whole gift, from Bill's Eevee
([data/maps/Goldenrod_BillsHouse/scripts.pory](../../data/maps/Goldenrod_BillsHouse/scripts.pory)),
shortened:

```
getpartycount(VAR_SPECIAL_x8005)
if (var(VAR_SPECIAL_x8005) == 6) { goto(PartyFull) }
givemon(SPECIES_EEVEE, 5, 0, 0, 0, VAR_SPECIAL_RESULT)
setflag(FLAG_GOT_EEVEE_FROM_BILL)
bufferplayersname(0)
npcmsg("{STRVAR_1 3, 0, 0} received\nthe EEVEE!")
playfanfare(SEQ_ME_POKEGET)
waitfanfare
npcmsg("Give a nickname to the EEVEE? {YESNO 0}")
getmenuchoice(VAR_SPECIAL_RESULT)
if (var(VAR_SPECIAL_RESULT) == 0) {
    closemessage
    fadescreen(6, 1, 0, RGB_BLACK)
    waitfade
    nicknameinput(VAR_SPECIAL_x8005, VAR_SPECIAL_RESULT)
    fadescreen(6, 1, 1, RGB_BLACK)
    waitfade
}
```

`getpartycount` before `givemon` also gives you the new Pokémon's party slot (a party of
3 puts it in slot 3, counting from 0), which `nicknameinput` and the commands in §2 need.

Notes:

- The form is set after the stats are calculated, so a form with different base stats
  has the base form's stats until they are recalculated (on level-up). The Sinjoh
  Ruins Giratina (`givemon(SPECIES_GIRATINA, 1, ITEM_GRISEOUS_ORB, 1, ABILITY_LEVITATE, ...)`)
  is level 1, where it barely matters. `givecustommon` (§3) recalculates.
- The ability argument is stored as one byte (`u8 ability` in `GiveMon`). That covers all
  retail abilities; a new ability numbered above 255 would need that changed.
- Species, items and abilities can be named (`SPECIES_X`, `ITEM_X`, `ABILITY_X`) because
  every map script includes their headers (through `constants/scrcmd.h`).

## 2. Changing the Pokémon afterwards

These commands work on a party slot, so keep the slot from `getpartycount` (§1):

| Command | Does |
|---|---|
| `setmonmove(slot, moveSlot, MOVE_X)` | replaces move 0-3, PP full, PP Ups reset |
| `nicknameinput(slot, VAR)` | the nickname screen |
| `monaddfriendship(...)`, `monsubtractfriendship(...)` | friendship |
| `bufferpartymonnick(n, slot)` | the nickname into a string buffer |

The Dragon's Den Dratini gets Extreme Speed only if you passed the quiz
([data/maps/DragonsDen_Shrine/scripts.pory](../../data/maps/DragonsDen_Shrine/scripts.pory)):

```
getpartycount(VAR_SPECIAL_x8005)
...
givemon(SPECIES_DRATINI, 15, 0, 0, 0, VAR_SPECIAL_RESULT)
if (!flag(FLAG_FAILED_DRAGONS_DEN_QUIZ)) {
    setmonmove(VAR_SPECIAL_x8005, 0, MOVE_EXTREME_SPEED)
}
```

There is no script command to set IVs, nature, shininess, the ball or the met location
of a party Pokémon. Those need C, which is §3. ([script-commands.md](script-commands.md)
lists every command; [script-commands-list.md](script-commands-list.md) has the
arguments.)

## 3. Custom gifts: `givecustommon`

This adds a command that gives a Pokémon described by a table in C: species, level,
form, item, **ball, ability, moves, each IV, nature, gender, ability slot, shiny,
met location, the fateful-encounter flag, and egg or not**. A script names an entry:

```
givecustommon(GIFT_MON_SHINY_EEVEE, VAR_SPECIAL_RESULT)
```

and gets 1 in the var, or 0 if the party was full (nothing is given then, as with
`givemon`).

### Adding the command

Seven files, following [script-commands.md](script-commands.md#6-adding-a-command).

**1. `include/constants/gift_mons.h`** (new): the ids, usable in scripts.

```c
#ifndef POKEHEARTGOLD_CONSTANTS_GIFT_MONS_H
#define POKEHEARTGOLD_CONSTANTS_GIFT_MONS_H

// Ids for the givecustommon script command: entries of sGiftMons in src/data/gift_mons.h
#define GIFT_MON_SHINY_EEVEE 0
#define GIFT_MON_DRATINI_EGG 1
#define GIFT_MON_COUNT       2

// Pick nature, gender, ability slot, shininess or an IV at random
#define GIFT_MON_RANDOM 0xFF

#endif // POKEHEARTGOLD_CONSTANTS_GIFT_MONS_H
```

and in [include/constants/scrcmd.h](../../include/constants/scrcmd.h), with the other
includes (every map script includes this file, which is what lets `scripts.pory` say
`GIFT_MON_SHINY_EEVEE`):

```c
#include "constants/gift_mons.h"
```

**2. `include/gift_mon.h`** (new): one entry.

```c
#ifndef POKEHEARTGOLD_GIFT_MON_H
#define POKEHEARTGOLD_GIFT_MON_H

#include "constants/gift_mons.h"
#include "constants/pokemon.h"

typedef struct GiftMon {
    u16 species;
    u8 level;                 // 1 for an egg
    u8 form;
    u16 heldItem;
    u16 ball;                 // ITEM_*_BALL; ITEM_NONE = Poke Ball
    u16 ability;              // ABILITY_*; ABILITY_NONE = the one abilitySlot picks
    u16 moves[MAX_MON_MOVES]; // all MOVE_NONE = the level-up moves
    u8 ivs[NUM_STATS];        // HP, Atk, Def, Speed, SpAtk, SpDef; GIFT_MON_RANDOM = roll
    u8 nature;                // NATURE_*, or GIFT_MON_RANDOM
    u8 gender;                // MON_MALE / MON_FEMALE, or GIFT_MON_RANDOM
    u8 abilitySlot;           // 0 or 1, or GIFT_MON_RANDOM
    u8 shiny;                 // TRUE / FALSE, or GIFT_MON_RANDOM (1 in 8192)
    u8 fatefulEncounter;      // TRUE: "obtained in a fateful encounter"
    u8 isEgg;                 // TRUE: give it as an egg
    u16 metLocation;          // MAPSEC_* / METLOC_*; MAPSEC_MYSTERY_ZONE = the current map
                              // (an egg: where it came from; MAPSEC_MYSTERY_ZONE = Day-Care Couple)
} GiftMon;

#endif // POKEHEARTGOLD_GIFT_MON_H
```

**3. `src/data/gift_mons.h`** (new): the table. Fields you leave out are 0.

```c
#include "gift_mon.h"

static const GiftMon sGiftMons[GIFT_MON_COUNT] = {
    [GIFT_MON_SHINY_EEVEE] = {
        .species = SPECIES_EEVEE,
        .level = 5,
        .form = 0,
        .heldItem = ITEM_NONE,
        .ball = ITEM_LUXURY_BALL,
        .ability = ABILITY_NONE,
        .moves = { MOVE_TACKLE, MOVE_TAIL_WHIP, MOVE_WISH, MOVE_NONE },
        .ivs = { 31, 31, 31, 31, 31, 31 },
        .nature = NATURE_MODEST,
        .gender = MON_FEMALE,
        .abilitySlot = 1,
        .shiny = TRUE,
        .fatefulEncounter = FALSE,
        .isEgg = FALSE,
        .metLocation = MAPSEC_MYSTERY_ZONE,
    },
    [GIFT_MON_DRATINI_EGG] = {
        .species = SPECIES_DRATINI,
        .level = 1,
        .ball = ITEM_NONE,
        .ability = ABILITY_NONE,
        .moves = { MOVE_WRAP, MOVE_LEER, MOVE_EXTREME_SPEED, MOVE_NONE },
        .ivs = { GIFT_MON_RANDOM, 31, GIFT_MON_RANDOM, 31, GIFT_MON_RANDOM, GIFT_MON_RANDOM },
        .nature = NATURE_ADAMANT,
        .gender = GIFT_MON_RANDOM,
        .abilitySlot = GIFT_MON_RANDOM,
        .shiny = GIFT_MON_RANDOM,
        .isEgg = TRUE,
        .metLocation = METLOC_PRIMO,
    },
};
```

**4. The command**, at the end of [src/scrcmd_party.c](../../src/scrcmd_party.c). Add these
includes after the existing ones:

```c
#include "gift_mon.h"
#include "map_section.h"
#include "math_util.h"
#include "msgdata.h"
#include "trainer_memo.h"
#include "update_dex_received.h"

#include "constants/abilities.h"
#include "constants/items.h"
#include "constants/map_sections.h"
#include "constants/moves.h"
#include "constants/species.h"

#include "data/gift_mons.h"
```

and the code:

```c
static u32 GiftMon_MakePersonality(const GiftMon *gift, u32 otId) {
    u32 pid;
    u8 genderRatio = GetMonBaseStat(gift->species, BASE_GENDER_RATIO);
    BOOL checkGender = gift->gender != GIFT_MON_RANDOM && genderRatio != MON_RATIO_MALE && genderRatio != MON_RATIO_FEMALE && genderRatio != MON_RATIO_UNKNOWN;

    while (TRUE) {
        if (gift->shiny == TRUE) {
            pid = GenerateShinyPersonality(otId);
        } else {
            pid = LCRandom() | (LCRandom() << 16);
            if (gift->shiny == FALSE && CalcShininessByOtIdAndPersonality(otId, pid)) {
                continue;
            }
        }
        if (gift->nature != GIFT_MON_RANDOM && GetNatureFromPersonality(pid) != gift->nature) {
            continue;
        }
        if (checkGender && (genderRatio > (u8)pid ? MON_FEMALE : MON_MALE) != gift->gender) {
            continue;
        }
        if (gift->abilitySlot != GIFT_MON_RANDOM && (pid & 1) != gift->abilitySlot) {
            continue;
        }
        return pid;
    }
}

BOOL ScrCmd_GiveCustomMon(ScriptContext *ctx) {
    FieldSystem *fieldSystem = ctx->fieldSystem;
    u16 id = ScriptGetVar(ctx);
    u16 *retPtr = ScriptGetVarPointer(ctx);
    PlayerProfile *profile = Save_PlayerData_GetProfile(fieldSystem->saveData);
    Party *party = SaveArray_Party_Get(fieldSystem->saveData);
    const GiftMon *gift;
    Pokemon *mon;
    String *name;
    u32 value;
    int i;

    *retPtr = FALSE;
    GF_ASSERT(id < GIFT_MON_COUNT);
    if (id >= GIFT_MON_COUNT || Party_GetCount(party) >= PARTY_SIZE) {
        return FALSE;
    }
    gift = &sGiftMons[id];

    mon = AllocMonZeroed(HEAP_ID_FIELD2);
    CreateMon(mon, gift->species, gift->level, USE_RANDOM_IVS, TRUE, GiftMon_MakePersonality(gift, PlayerProfile_GetTrainerID(profile)), OT_ID_PLAYER_ID, 0);

    for (i = 0; i < NUM_STATS; i++) {
        if (gift->ivs[i] != GIFT_MON_RANDOM) {
            value = gift->ivs[i];
            SetMonData(mon, MON_DATA_HP_IV + i, &value);
        }
    }
    if (gift->moves[0] != MOVE_NONE) {
        for (i = 0; i < MAX_MON_MOVES; i++) {
            value = gift->moves[i];
            SetMonData(mon, MON_DATA_MOVE1 + i, &value);
            value = GetMonData(mon, MON_DATA_MOVE1_MAX_PP + i, NULL);
            SetMonData(mon, MON_DATA_MOVE1_PP + i, &value);
        }
    }
    value = gift->form;
    SetMonData(mon, MON_DATA_FORM, &value);
    value = gift->heldItem;
    SetMonData(mon, MON_DATA_HELD_ITEM, &value);
    if (gift->ability != ABILITY_NONE) {
        value = gift->ability;
        SetMonData(mon, MON_DATA_ABILITY, &value);
    }

    if (gift->isEgg) {
        // What SetEggStats in src/get_egg.c does
        value = GetMonBaseStat(gift->species, BASE_EGG_CYCLES);
        SetMonData(mon, MON_DATA_EGG_CYCLES, &value);
        value = 0;
        SetMonData(mon, MON_DATA_MET_LEVEL, &value);
        value = TRUE;
        SetMonData(mon, MON_DATA_IS_EGG, &value);
        name = GetSpeciesName(SPECIES_EGG, HEAP_ID_FIELD2);
        SetMonData(mon, MON_DATA_NICKNAME_STRING, name);
        String_Delete(name);
        // Sets the player as OT, today's date and the egg location
        MonSetTrainerMemo(mon, profile, 3, gift->metLocation != MAPSEC_MYSTERY_ZONE ? gift->metLocation : METLOC_DAY_CARE_COUPLE, HEAP_ID_FIELD2);
    } else {
        // Sets the player as OT, the ball, today's date and the current map as met location
        MonSetCatchData(mon, profile, gift->ball != ITEM_NONE ? gift->ball : ITEM_POKE_BALL, MapHeader_GetMapSec(fieldSystem->location->mapId), 24, HEAP_ID_FIELD2);
        if (gift->metLocation != MAPSEC_MYSTERY_ZONE) {
            value = gift->metLocation;
            SetMonData(mon, MON_DATA_MET_LOCATION, &value);
        }
    }
    if (gift->fatefulEncounter) {
        value = TRUE;
        SetMonData(mon, MON_DATA_FATEFUL_ENCOUNTER, &value);
    }
    CalcMonLevelAndStats(mon);

    *retPtr = Party_AddMon(party, mon);
    if (*retPtr && !gift->isEgg) {
        UpdatePokedexWithReceivedSpecies(fieldSystem->saveData, mon);
    }
    Heap_Free(mon);

    return FALSE;
}
```

**5.** Declare it in [include/scrcmd.h](../../include/scrcmd.h), after
`ScrCmd_BufferDeptStoreFloorNo`:

```c
BOOL ScrCmd_GiveCustomMon(ScriptContext *ctx);
```

**6.** Append it to `gScriptCmdTable` in
[src/data/fieldmap/script_cmd_table.h](../../src/data/fieldmap/script_cmd_table.h), after
`ScrCmd_BufferDeptStoreFloorNo,` (so it is command 853; if you already added commands,
it is the next free number):

```c
    ScrCmd_GiveCustomMon,
```

**7.** The macro, in [asm/macros/script.inc](../../asm/macros/script.inc) after
`BufferDeptStoreFloorNo`:

```
	// Gives the Pokemon sGiftMons[id] describes (src/data/gift_mons.h); RESULT = 1, or 0 if the party is full
	.macro GiveCustomMon id, result
	.short 853
	.short \id
	.short \result
	.endm
```

Build with `make release`. In a script:

```
getpartycount(VAR_SPECIAL_x8005)
if (var(VAR_SPECIAL_x8005) == 6) { goto(PartyFull) }
givecustommon(GIFT_MON_SHINY_EEVEE, VAR_SPECIAL_RESULT)
```

### How the fields work

- **Nature, gender, ability slot and shininess all come from the personality value**
  (a 32-bit number fixed when the Pokémon is made; it also encrypts the Pokémon's data, so
  it can't be changed later). `GiftMon_MakePersonality` draws random values until one
  fits everything you fixed. Shiny is checked against the player's trainer ID, which is
  why it has to happen here and not in the table. Asking for an impossible gender (a
  female Tauros) is ignored for species with one gender.
- **Ability**: `abilitySlot` picks the species' first or second ability, as in the wild.
  Set `ability` to give any ability regardless (Giratina's Origin Forme needs
  `ABILITY_LEVITATE` this way, because the slots come from the base form).
- **Ball**: any `ITEM_*_BALL` from Master to Cherish, and Fast to Sport. The Park Ball
  can't be stored (the setter in `pokemon.c` asserts). The Heal Ball also heals.
- **Moves**: all four as listed (a `MOVE_NONE` slot is empty), PP full. All `MOVE_NONE`
  keeps the level-up moves.
- **Met location**: `MAPSEC_*` (a place, [town-map-and-fly.md](town-map-and-fly.md#1-map-sections))
  or `METLOC_*` from
  [include/constants/map_sections.h](../../include/constants/map_sections.h) ("a lovely
  place", "a faraway place"...). The summary shows the location's name.
- **Egg**: level 1, hatch time from the species' egg cycles, Poké Ball, OT the player,
  `metLocation` is where the egg is from (the 2000s `METLOC_*`: Primo, Mr. Pokémon, the
  Day-Care Couple...). Hatching sets the met location to where it hatches, as for any
  egg. Moves, IVs, nature and shininess carry over to the hatched Pokémon.
- **No fixed nickname**: offer `nicknameinput` after it, as retail does.
- **Cost**: the code is about 600 bytes and each entry 40 bytes, in the static ARM9 (always
  loaded).

The two retail gifts written in C are the models for this:
`ScrCmd_GiveSpikyEarPichu` (fixed nature, gender, form, moves, item) and
`ScrCmd_GiveTogepiEgg` (an egg with an extra move), both in
[src/field/scrcmd_pokemon_misc.c](../../src/field/scrcmd_pokemon_misc.c). If you copy
them, note that both read the Pokémon after `Heap_Free(mon)` (Pichu's Pokédex update,
Togepi's personality record). In retail this happens to work: nothing allocates from
`HEAP_ID_FIELD2` between the free and the reads, and the retail heap doesn't wipe freed
memory. Any allocation added in between could reuse that memory. Move those lines above
the free.

## 4. Gift eggs: `giveegg`

```
giveegg(SPECIES_MAREEP, MAPLOC(METLOC_PRIMO))
```

| Argument | Meaning |
|---|---|
| species | the species that hatches |
| location | `MAPLOC(METLOC_X)` for one of the 2000s locations in [map_sections.h](../../include/constants/map_sections.h) (`METLOC_PRIMO`, `METLOC_MR_POKEMON`, `METLOC_DAY_CARE_COUPLE`...). The summary shows "obtained from" that |

What you get (`ScrCmd_GiveEgg` and `SetEggStats` in
[src/get_egg.c](../../src/get_egg.c)): level 1, random IVs and personality (shiny 1 in
8192), the level-1 moves, the species' egg cycles, Poké Ball, the player as OT, today
as the egg date. There is **no result var**: a full party gets nothing, silently.
Primo's eggs in Violet City
([data/maps/Violet_Pokecenter_1F/scripts.pory](../../data/maps/Violet_Pokecenter_1F/scripts.pory))
check first:

```
getpartycount(VAR_SPECIAL_RESULT)
if (var(VAR_SPECIAL_RESULT) == 6) { goto(PartyFull) }
setflag(FLAG_GOT_MAREEP_EGG_FROM_PRIMO)
giveegg(SPECIES_MAREEP, MAPLOC(METLOC_PRIMO))
```

For an egg with fixed IVs, moves, nature or shiny, use `givecustommon` with
`.isEgg = TRUE` (§3). The Togepi egg (`givetogepiegg`) adds Extrasensory to the level-1
moves. A new "obtained from" place needs a new `METLOC_*` and its name
([town-map-and-fly.md](town-map-and-fly.md#1-map-sections)).

## 5. In-game trades

### What happens in a trade

From the Violet City Onix-for-Bellsprout trade
([data/maps/Violet_BellsproutOnyxTradeHouse/scripts.pory](../../data/maps/Violet_BellsproutOnyxTradeHouse/scripts.pory)):

```
choosepartymonfortrade                   // the party screen
getpartyselection(VAR_SPECIAL_RESULT)    // the slot, or 255 if cancelled
restoreoverworld
...
if (var(VAR_SPECIAL_RESULT) == 255) { goto(Declined) }
loadnpctrade(0)                          // trade 0 = NPC_TRADE_ROCKY_ONIX
copyvar(VAR_SPECIAL_x8004, VAR_SPECIAL_RESULT)
getpartymonspecies(VAR_SPECIAL_x8004, VAR_SPECIAL_x8005)   // SPECIES_NONE for an egg
npctradegetreqspecies(VAR_SPECIAL_RESULT)
if (var(VAR_SPECIAL_x8005) != VAR_SPECIAL_RESULT) { goto(WrongMon) }
npctradeexec(VAR_SPECIAL_x8004)          // the trade animation; the slot gets the new Pokémon
npctradeend
setflag(FLAG_TRADE_VIOLET_CITY_BELLSPROUT_ONIX)
...
WrongMon:
npctradeend
```

| Command | Does |
|---|---|
| `loadnpctrade(n)` | loads the `npc_trade` overlay and trade `n` |
| `npctradegetreqspecies(VAR)` | the species the NPC wants |
| `getofferedspecies(VAR)` | the species the NPC gives |
| `npctradeexec(slot)` | swaps the party slot for the NPC's Pokémon, with the animation |
| `npctradeend` | frees the trade and unloads the overlay. Call it on every path after `loadnpctrade`, including "wrong Pokémon" |

**The script decides what is accepted.** The game only compares species in the script,
so a trade can check more (`mongetlevel`, `mongetgender`...) before `npctradeexec`, or skip
the check. Only the NPC's side is in the data.

`n` is a number in scripts (`loadnpctrade(13)`), because `NPC_TRADE_*` is a C `enum`,
which the script assembler can't read.

The NPC's Pokémon (`_CreateTradeMon` in [src/npc_trade.c](../../src/npc_trade.c)):

| Field | Value |
|---|---|
| species, held item | from the table |
| level | **the level of the Pokémon you gave** |
| nickname | from `msg_0200` (it counts as nicknamed; you can't rename it) |
| IVs, personality | from the table, so nature, gender, ability and shininess are fixed |
| OT name, ID, gender, language | from the table |
| contest stats | from the table (all 0 in retail) |
| moves | its level-up moves at that level; Hornlette's Thunder Fang comes from `setmonmove` in the script ([data/maps/DiglettCave/scripts.pory](../../data/maps/DiglettCave/scripts.pory)) |
| met location, level, date | "link trade", the level, today |
| ball | Poké Ball |
| Pokédex | marked seen and caught |

Because its OT isn't the player, it gains 1.5× experience (1.7× if its language differs
from the game's, like Volty from France) and may disobey without enough badges.
**An in-game trade never triggers a trade evolution** (only wireless trades check;
`launch_application.c`). A Kadabra from an NPC stays a Kadabra.

### The trade table: `data/npc_trades.json`

One entry per trade, in `NPC_TRADE_*` order (the position is the number scripts use):

```json
{
    "id": "NPC_TRADE_ROCKY_ONIX",
    "species": "SPECIES_ONIX",
    "nickname": "Rocky",
    "requested_species": "SPECIES_BELLSPROUT",
    "ivs": { "hp": 25, "atk": 20, "def": 25, "speed": 15, "spatk": 15, "spdef": 15 },
    "personality": 9711,
    "held_item": "ITEM_PERSIM_BERRY",
    "ot_name": "Rudy",
    "ot_id": 48926,
    "ot_gender": "male",
    "language": "LANGUAGE_ENGLISH",
    "contest": { "cool": 0, "beauty": 0, "cute": 0, "smart": 0, "tough": 0 },
    "sheen": 0,
    "ability": "ABILITY_STURDY",
    "unused_flag": 0
}
```

| Field | Meaning |
|---|---|
| `id` | the `NPC_TRADE_*` name (C only) |
| `species`, `requested_species` | given and asked for. `requested_species` is only read by `npctradegetreqspecies` |
| `nickname` | up to 10 characters |
| `ivs` | 0-31 each |
| `personality` | sets nature (`personality % 25`), gender (low byte against the species' gender ratio), ability slot (bit 0), Unown letter, Spinda's spots, and with `ot_id` shininess. `npctrade.py pid` finds one |
| `held_item` | `ITEM_*` |
| `ot_name` | up to 7 characters |
| `ot_id` | the full 32-bit ID; the summary shows the low 16 bits |
| `ot_gender` | `male` / `female` (the OT name's color) |
| `language` | `LANGUAGE_*` from [include/config.h](../../include/config.h) |
| `contest` | the five contest stats |
| `sheen`, `ability`, `unused_flag` | **not used** by the code. `ability` matches what the personality gives in every retail entry; keep it as a note. `unused_flag` is read only by `getnpctradeunusedflag`, which no script uses |

`python3 tools/npctrade/npctrade.py build` writes the three game files from it: the
binary table (`files/a/1/1/2`, 84 bytes per trade), the names (`msg_0200`: nicknames
first, then OT names; trade `n`'s OT name is message `n + NPC_TRADE_MAX`), and the enum
in [include/constants/npc_trade.h](../../include/constants/npc_trade.h). On the retail
JSON it writes the retail files byte for byte. Don't edit those three by hand; `build`
overwrites them.

| Command | Does |
|---|---|
| `npctrade.py show [NPC_TRADE_X]` | each trade, with the nature, gender and ability its personality gives |
| `npctrade.py check` | do the files match the JSON? Is any trade shiny? |
| `npctrade.py build` | write the files |
| `npctrade.py pid SPECIES_X --nature NATURE_X [--gender male] [--ability 0] [--ot-id N]` | a personality value with that nature, gender and ability slot, not shiny for that OT ID |
| `npctrade.py dump` | rewrite the JSON from the game files (to start over) |

```
$ python3 tools/npctrade/npctrade.py show NPC_TRADE_ROCKY_ONIX
 0 NPC_TRADE_ROCKY_ONIX           SPECIES_ONIX "Rocky" for SPECIES_BELLSPROUT
   OT Rudy (male, id 48926), LANGUAGE_ENGLISH, item ITEM_PERSIM_BERRY
   IVs 25/20/25/15/15/15 (HP/Atk/Def/Spe/SpA/SpD), personality 9711: HASTY, male, ABILITY_STURDY (slot 1)
```

**Shiny trades.** `_CreateTradeMon` ends with `GF_ASSERT(!MonIsShiny(mon))`. Outside a
link session a failed assert does nothing ([debugging.md](debugging.md#5-assertions)), so
a shiny trade works, but `check` warns because retail avoids it. To make one on purpose,
choose `personality` and `ot_id` so that they give a shiny value
(`(ot_id >> 16) ^ (ot_id & 0xFFFF) ^ (pid >> 16) ^ (pid & 0xFFFF) < 8`).

### Changing a trade

Edit the entry, then:

```sh
python3 tools/npctrade/npctrade.py build
python3 tools/npctrade/npctrade.py check
make release
```

Change `requested_species` and the NPC's text in the map's `scripts.pory` together (the
text names the species). For a new nature, gender or ability:

```sh
$ python3 tools/npctrade/npctrade.py pid SPECIES_ONIX --nature ADAMANT --gender male --ability 1 --ot-id 48926
```

prints a personality value to paste in.

### Adding a trade

1. Append an entry to `data/npc_trades.json` with a new `id` (`NPC_TRADE_EVA_EEVEE`).
   Its number is its position: the 14th entry is 13.
2. `python3 tools/npctrade/npctrade.py build`. This adds the enum value, the nickname
   (as message 13) and OT name (moving the OT names up by one; the code finds them by
   `n + NPC_TRADE_MAX`, so that is expected).
3. A script, copying the Violet one with `loadnpctrade(13)` and a flag of its own
   ([story-progression.md](story-progression.md) explains flags; free ones are in
   [unknown-flags-vars.md](unknown-flags-vars.md)).
4. `make release`.

### Loaned Pokémon: Kenya and Shuckie

Two trade entries are not trades. Kenya (Spearow, trade 7) and Shuckie (Shuckle, 6) are
given with:

```
giveloanmon(6, 20, MAP_CIANWOOD)      // trade, level, map whose section is the met location
```

which builds the trade's Pokémon (nickname, OT, IVs, personality from the table) and adds
it to the party without the animation; Kenya also gets her mail. All three arguments are
fixed numbers, not vars. To take it back:

```
checkreturnloanmon(6, VAR_TEMP_x4000, VAR_SPECIAL_RESULT)   // slot in VAR_TEMP_x4000
returnloanmon(VAR_TEMP_x4000)                                // removes that slot
```

`checkreturnloanmon` returns 0 if it can be returned, 1 if it isn't the loaned Pokémon,
2 if it holds an item, 3 if it has a ball capsule, 4 if it is the last Pokémon that can
battle ([data/maps/Cianwood_KirksHouse/scripts.pory](../../data/maps/Cianwood_KirksHouse/scripts.pory)).

"Is it the loaned Pokémon" compares species, OT ID, personality, OT gender, language and
the game it came from with the table (`MonIsInGameTradePoke` in
[src/field_misc_events.c](../../src/field_misc_events.c)). **Changing Kenya's or Shuckie's
entry means a Kenya or Shuckie already in a save is no longer recognised**: the player
can't deliver or return it. Change those two only before a release, or not at all.

## 6. Saves

Nothing here changes the save layout. A gift or trade already received is an ordinary
Pokémon in the save; changing the data later only affects new ones. The exception is the
loans above. Each gift is guarded by a flag in its script; reuse a flag and the gift
can't be received ([save-compatibility.md](save-compatibility.md)).

## Not verified

- Nothing here was run in an emulator.
- `givecustommon` (§3, both table entries, egg and non-egg) was added to the US HeartGold
  ROM, used from two map scripts in place of Bill's Eevee and Primo's Mareep egg, built
  with `make release`, and then removed. Whether the summary screen shows every field as
  intended (ball, met location, shiny, the egg's "obtained from") was not seen.
- A 14th trade (`NPC_TRADE_EVA_EEVEE`) was added with `npctrade.py build` and used from the
  Violet trade script, built, and removed. The trade itself was not run.
- `npctrade.py build` on the retail JSON writes all three files byte for byte (checked
  with `check` and a full `make`, which passes the checksum tests).
- The experience boost and the absence of trade evolution after an NPC trade come from
  reading the code (`battle_command.c`, `launch_application.c`).
- Whether a form set by `givemon` keeps the base form's stats until a level-up was read
  in the code, not seen.
