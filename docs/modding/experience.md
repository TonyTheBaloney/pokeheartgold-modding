<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Experience and leveling

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers how Pokémon gain experience and levels: the growth rate tables, who
gets experience in battle and how much, the Exp. Share and Lucky Egg, how a level-up
runs, and the other ways experience changes (Rare Candy, the Day-Care, hatching). It ends
with four recipes: a party-wide Exp. Share, Gen 5 level scaling, experience for catching,
and level caps by badge count.

Obedience (traded Pokémon disobeying above a badge level) is in
[gyms.md](gyms.md#what-badges-do). The maximum level itself (`MAX_LEVEL`) is in
[game-limits.md](game-limits.md).

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `gExperienceTables` (`src/data/pokemon/experience_tables.h`) | `files/poketool/personal/growtbl.csv`, read from a NARC (§1) |
| `Cmd_getexp` | `BtlCmd_CalcExpGain` (the amounts) + `Task_GetExp` (giving them out) (§2) |
| `gSentPokesToOpponent` | `ctx->expEarnFlags` |
| `HOLD_EFFECT_LUCKY_EGG` | `HOLD_EFFECT_EXP_UP` |
| `MonGainEVs` | `BattleScript_CalcEffortValues` |
| `TryIncrementMonLevel` | `Pokemon_TryLevelUp` |
| expansion's `B_SCALED_EXP`, `B_EXP_CATCH`, `B_SPLIT_EXP` | not in HGSS: §5, §6, §7 |

The files:

| File | What |
|---|---|
| [files/poketool/personal/growtbl.csv](../../files/poketool/personal/growtbl.csv) | the 8 growth rate tables: total experience for each level |
| [files/poketool/personal/personal.json](../../files/poketool/personal/personal.json) | per species: `growthRate`, `expYield` |
| [include/constants/pokemon.h](../../include/constants/pokemon.h) | `GROWTH_*`, `MAX_LEVEL` |
| [src/pokemon.c](../../src/pokemon.c) | table lookups, level from experience, `Pokemon_TryLevelUp` |
| [src/battle/battle_command.c](../../src/battle/battle_command.c) | `BtlCmd_CalcExpGain`, `Task_GetExp` (messages, level-ups, moves), `Task_GetPokemon` (catching) |
| [src/battle/battle_util.c](../../src/battle/battle_util.c) | `BattleSystem_SetExperienceEarnFlags`: who took part |
| `files/battledata/script/subscript/subscript_0276_GrantExp.s` | the battle script run after each enemy faints |
| [src/use_item_on_mon.c](../../src/use_item_on_mon.c) | Rare Candy |
| [src/get_egg.c](../../src/get_egg.c) | Day-Care experience, hatching |

## 1. Growth rates

A Pokémon stores only its **total experience**. Its level is looked up from that total in
its species' growth rate table: the level is the highest one whose entry is not above the
total (`CalcLevelBySpeciesAndExp_PreloadedPersonal`,
[pokemon.c:1938](../../src/pokemon.c#L1938)).

The tables are `growtbl.csv`: one row per growth rate, columns `lv000` to `lv100`. The build
turns the CSV into `poketool/personal/growtbl.narc` (one member per row) with `csv2bin`;
the column types are in `growtbl.txt`. The first column is only a label (`growtbl.txt`
skips it): a row's position is its growth rate number. `lv000` is never read.

| Constant | Value | Lv. 100 total | Formula (n = level) | Species |
|---|---:|---:|---|---:|
| `GROWTH_MEDIUM_FAST` | 0 | 1,000,000 | n³ | 191 |
| `GROWTH_ERRATIC` | 1 | 600,000 | piecewise | 22 |
| `GROWTH_FLUCTUATING` | 2 | 1,640,000 | piecewise | 14 |
| `GROWTH_MEDIUM_SLOW` | 3 | 1,059,860 | 6/5·n³ − 15n² + 100n − 140 | 125 |
| `GROWTH_FAST` | 4 | 800,000 | 4/5·n³ | 46 |
| `GROWTH_SLOW` | 5 | 1,250,000 | 5/4·n³ | 110 |
| `GROWTH_UNUSED_6` | 6 | 1,000,000 | copy of Medium Fast | 0 |
| `GROWTH_UNUSED_7` | 7 | 1,000,000 | copy of Medium Fast | 0 |

Every table has 0 at level 1. (Medium Slow's formula is negative there.)

A species picks its table with `"growthRate"` in `personal.json`, written without the
`GROWTH_` prefix (`"MEDIUM_SLOW"`). The template `personal.json.txt` adds it back.

The functions, all in [src/pokemon.c](../../src/pokemon.c):

| Function | Line | Returns |
|---|---|---|
| `GetExpByGrowthRateAndLevel(rate, level)` | [:1906](../../src/pokemon.c#L1906) | the total for a level (asserts `rate < 8`) |
| `GetMonExpBySpeciesAndLevel(species, level)` | [:1897](../../src/pokemon.c#L1897) | the same, by species |
| `CalcBoxMonLevel` | [:1922](../../src/pokemon.c#L1922) | the level from the stored experience |
| `CalcMonExpToNextLevel` | [:1879](../../src/pokemon.c#L1879) | experience still needed for the next level |
| `Pokemon_GetPercentToNextLevel` | [:1868](../../src/pokemon.c#L1868) | progress through the current level, 0-100 (the exp bar) |

### Changing a curve

Edit the numbers in `growtbl.csv` and rebuild. Each row must go up, or levels are
skipped. To change one species, set its `growthRate` instead.

### Adding a curve

Rows 6 and 7 are free. To use one:

1. Rename it in [include/constants/pokemon.h](../../include/constants/pokemon.h)
   (`#define GROWTH_VERY_FAST 6`) and, to keep the CSV readable, in its first column.
   Don't move the row.
2. Fill in its 101 numbers. To make a row from a formula:

   ```sh
   python3 -c "print(','.join(['GROWTH_VERY_FAST','0','0'] + [str(n**3 * 3 // 5) for n in range(2, 101)]))"
   ```

3. Set `"growthRate": "VERY_FAST"` on the species in `personal.json`.

A ninth table needs more than a row: `LoadGrowthTable` and `GetExpByGrowthRateAndLevel`
assert `growthRate < 8`.

### Effect on saves

A Pokémon in the party saves its level as well as its experience. A boxed Pokémon
saves only experience, and its level is worked out again when it is read. After a curve
changes, a party Pokémon keeps its old level until it next levels up, and a boxed one
shows its new level right away. The experience total itself does not change.

## 2. Experience in battle

When an enemy faints, `BtlCmd_PlayFaintAnimation`
([battle_command.c:996](../../src/battle/battle_command.c#L996)) sets its bit in
`BATTLE_STATUS2_EXP_GAIN`. Later in the turn, `BattleControllerPlayer_TryGrantExp`
([battle_controller_player.c:3689](../../src/battle/battle_controller_player.c#L3689))
runs subscript 276, `GrantExp`, once for each fainted enemy:

```
CalcExpGain _005      // work out the amounts, or jump to _005 (End) if this battle gives none
StartGetExpTask       // start Task_GetExp
WaitGetExpTask        // wait for it to finish
```

### Who takes part

`ctx->expEarnFlags[side]` holds one bit per party slot. A slot's bit is set when that
Pokémon is on the field while the enemy is out (`BattleSystem_SetExperienceEarnFlags`,
[battle_util.c:1246](../../src/battle/battle_util.c#L1246), called when either side sends a
Pokémon out). When a new enemy comes out, its flags are cleared first. So the participants
are the Pokémon that faced this enemy, including one that was switched out later.

### The amount

`BtlCmd_CalcExpGain` ([battle_command.c:1225](../../src/battle/battle_command.c#L1225)):

```
total = expYield × level ÷ 7            (of the fainted Pokémon)
```

`expYield` is the species' `"expYield"` in `personal.json`. It is a `u8`, so it can't go
above 255 (Gen 4's highest is Blissey's, 255; later games use bigger numbers).

The total is then split. A party Pokémon counts only if it is alive:

| Case | Each participant | Each Exp. Share holder |
|---|---|---|
| no one alive holds an Exp. Share | total ÷ participants | — |
| someone alive holds one | (total ÷ 2) ÷ participants | (total ÷ 2) ÷ holders |

Each share is at least 1. A holder that also took part gets both shares. Pokémon at
Lv. 100 still count when the total is split, but get nothing.

`Task_GetExp` ([battle_command.c:5995](../../src/battle/battle_command.c#L5995)) then goes
through the party one Pokémon at a time. Each one that is alive, below Lv. 100, and took
part or holds an Exp. Share gets its share, multiplied by each of these in turn (each
result rounded down):

| Condition | × | Code |
|---|---|---|
| holds a Lucky Egg (`HOLD_EFFECT_EXP_UP`) | 1.5 | `totalExp * 150 / 100` |
| trainer battle | 1.5 | `BATTLE_TYPE_TRAINER` |
| another player's Pokémon (`BattleSystem_IsPlayerOT` false) | 1.5 | and the message says "a boosted" |
| ... and its language differs from the game's | 1.7 instead | `MON_DATA_LANGUAGE != gGameLanguage` |

The same pass gives the Pokémon EVs for the fainted species
(`BattleScript_CalcEffortValues`). So an Exp. Share holder gets EVs too, and a Lv. 100
Pokémon gets none.

**Worked example.** A wild Lv. 3 Pidgey (`expYield` 55) gives 55 × 3 ÷ 7 = 23. One
participant gets 23. Two participants get 11 each. A trainer's Lv. 3 Pidgey gives
23 × 1.5 = 34, and 51 with a Lucky Egg.

### Battles that give none

`CalcExpGain` jumps to the end when the fainted battler is not an enemy, or the battle
type has any of `BATTLE_TYPE_NO_EXP` ([constants/battle.h](../../include/constants/battle.h)):
link, Safari, Battle Frontier (including the Trainer House) and Pal Park. The Bug-Catching
Contest gives experience as normal.

## 3. Levelling up

### In battle

After adding the experience, `Task_GetExp` calls `Pokemon_TryLevelUp`
([pokemon.c:2765](../../src/pokemon.c#L2765)). It raises the level by **one** if the
experience reaches the next entry in the table, and caps the experience at the Lv. 100
total. For each level gained, `Task_GetExp`:

1. Adds friendship (`MON_MOOD_MODIFIER_LEVEL_UP_IN_BATTLE`) and recalculates stats.
2. Prints "{0} grew to Lv. {1}!" and the stat window (old stats, then the gains).
3. Teaches each level-up move for the new level (`MonTryLearnMoveOnLevelUp`), asking
   which move to forget when there are already four.
4. Animates the exp bar again and goes back to `Pokemon_TryLevelUp` for the next level.

The party slot's bit is added to `ctx->levelUpMons`. After the battle,
`BattleSystem_CheckEvolution` ([battle_system.c:704](../../src/battle/battle_system.c#L704))
checks those Pokémon for a level-up evolution. That happens if the battle was won, the
Pokémon was caught, or the player ran away, but not after a loss. Only the active
Pokémon's exp bar and level-up animation are shown. The others get a small name plate
over the stat window.

### Outside battle

| Where | What it does | Code |
|---|---|---|
| A new Pokémon (`givemon`, wild, trainer, a hatched egg at `EGG_HATCH_LEVEL`) | experience = the table entry for its level | `CreateBoxMon`, [pokemon.c:212](../../src/pokemon.c#L212) |
| Rare Candy | adds `CalcMonExpToNextLevel`, so the Pokémon lands at the **start** of the next level (progress into the current level is lost), then `CalcMonLevelAndStats`. Allowed below `MAX_LEVEL` | [use_item_on_mon.c:297](../../src/use_item_on_mon.c#L297) |
| Day-Care | 1 experience per step (`DaycareMon_AddSteps`, [get_egg.c:778](../../src/get_egg.c#L778)). Added when you take it back, then it learns each level-up move it passed (`Daycare_LearnLevelUpMoves`). Not capped at the Lv. 100 total | `Save_Daycare_MoveMonToParty`, [get_egg.c:149](../../src/get_egg.c#L149) |
| Trainer House | sets experience to `MAX_TRAINER_HOUSE_LEVEL` on a copy of the party | [overlay_25.c:284](../../src/overlay_25.c#L284) |

There is no script command that gives experience or levels. To add one, follow
[script-commands.md](script-commands.md#6-adding-a-command) and copy the Rare Candy code.
A level-up outside battle doesn't check for evolution. Call `GetMonEvolution` yourself
([evolutions.md](evolutions.md)).

**Setting experience from C.** `SetMonData(mon, MON_DATA_EXPERIENCE, &exp)` stores the
value as given. `AddMonData(mon, MON_DATA_EXPERIENCE, n)` caps it at the Lv. 100 total.
Neither changes the level: call `CalcMonLevelAndStats(mon)` afterwards
([pokemon.c:309](../../src/pokemon.c#L309)).

## 4. Changing the numbers

| To change | Edit |
|---|---|
| how much a species gives | `"expYield"` in `personal.json` (0-255) |
| experience for everything | the `/ 7` in `BtlCmd_CalcExpGain`. `/ 5` is 40% more |
| the trainer, Lucky Egg or traded bonus | the `* 150 / 100` and `* 170 / 100` lines in `Task_GetExp` |
| how the Exp. Share splits | the `if (expShareMonsCnt)` block in `BtlCmd_CalcExpGain`, or §5 |
| how fast species level | §1 |

## 5. Recipe: party-wide Exp. Share

This makes every Pokémon in the party gain experience, as the Exp. Share does from Gen 6:
each participant gets the full amount and every other Pokémon gets half. It is always
on.

**1.** In `BtlCmd_CalcExpGain`, replace the whole `if (expShareMonsCnt) { ... } else { ... }`
block after the `totalExp` lines with:

```c
        // Party-wide Exp. Share: each participant gets the full amount, everyone else half.
        ctx->gainedExp = totalExp;
        ctx->partyGainedExp = totalExp / 2;
        if (ctx->partyGainedExp == 0) {
            ctx->partyGainedExp = 1;
        }
```

**2.** In `Task_GetExp`, the loop at the top picks the next Pokémon to handle. Make it take
every Pokémon except eggs:

```c
        if (!GetMonData(mon, MON_DATA_IS_EGG, NULL)) { // was: itemEffect == HOLD_EFFECT_EXP_SHARE || participant
            break;
        }
```

Fainted Pokémon and Lv. 100 Pokémon are still skipped further down.

**3.** Under `case STATE_GET_EXP_START:`, give non-participants the half share:

```c
            if (data->ctx->expEarnFlags[side] & MaskOfFlagNo(slot)) {
                totalExp = data->ctx->gainedExp;
            } else {
                totalExp = data->ctx->partyGainedExp;
            }
```

This replaces the participant check and the `HOLD_EFFECT_EXP_SHARE` check after it.

Each Pokémon still gets its own "gained ... Exp. Points!" message. The held Exp. Share no
longer does anything. Change its description in `data/items/items.json`, or make it a key
item ([items.md](items.md)). To make the party-wide share switchable, wrap step 1 in a
check such as `Bag_HasItem(BattleSystem_GetBag(battleSystem), ITEM_EXP__SHARE, 1, HEAP_ID_BATTLE)`
and keep the old block as the `else`. Steps 2 and 3 then need the same check, so that
Pokémon without an Exp. Share get nothing when it is off.

## 6. Recipe: Gen 5 level scaling

From Gen 5, a Pokémon gets more experience for beating a higher-level Pokémon and less for
a lower-level one:

```
exp × ((2L + 10) ÷ (L + Lp + 10))^2.5 + 1      L = fainted Pokémon's level, Lp = this Pokémon's level
```

Add above `Task_GetExp` in `battle_command.c` (integer only; 4096 means 1.0):

```c
static u32 Sqrt32(u32 x) {
    u32 root = 0;
    u32 bit = 1 << 30;
    while (bit > x) {
        bit >>= 2;
    }
    while (bit != 0) {
        if (x >= root + bit) {
            x -= root + bit;
            root = (root >> 1) + bit;
        } else {
            root >>= 1;
        }
        bit >>= 2;
    }
    return root;
}

// Gen 5 scaling: exp * ((2L + 10) / (L + Lp + 10))^2.5 + 1,
// L = the fainted Pokémon's level, Lp = the level of the Pokémon getting the experience.
static u32 ScaleExpByLevel(u32 exp, int faintedLevel, int monLevel) {
    if (exp == 0) {
        return 0;
    }
    u32 ratio = ((2 * faintedLevel + 10) << 12) / (faintedLevel + monLevel + 10); // 1.0 = 4096
    u32 root = Sqrt32(ratio << 12);                                                // sqrt(ratio), 1.0 = 4096
    u64 scaled = ((u64)exp * ratio * ratio) >> 12;                                 // exp * ratio^2, 1.0 = 4096
    return (u32)((scaled * root) >> 24) + 1;
}
```

In `Task_GetExp`, under `case STATE_GET_EXP_START:`, after the share is chosen and before
the Lucky Egg line:

```c
            totalExp = ScaleExpByLevel(totalExp, data->ctx->battleMons[data->ctx->battlerIdFainted].level, GetMonData(mon, MON_DATA_LEVEL, NULL));
```

Gen 5 also uses `/ 5` instead of `/ 7` in `BtlCmd_CalcExpGain`. With `/ 7` kept, the
Pidgey from §2 (23 before scaling) gives:

| Pidgey | Your Pokémon | Before | After |
|---|---|---:|---:|
| Lv. 3 | Lv. 3 | 23 | 24 |
| Lv. 3 | Lv. 10 | 23 | 10 |
| Lv. 10 | Lv. 3 | 78 | 152 |

The results are within 1 of the exact formula.

## 7. Recipe: experience for catching

HGSS gives no experience for catching. From Gen 6, the Pokémon that took part get the
same experience as for a knockout. This recipe gives it after "Gotcha!", before the
Pokédex entry and the nickname prompt, with the normal messages, level-ups and new moves.
It also gives EVs, since `Task_GetExp` does.

The catch runs as `Task_GetPokemon`. It starts `Task_GetExp` and waits for it.
`Task_GetExp` frees `ctx->getterWork` when it ends, and the battle script continues as soon
as that is `NULL`. So the exp task hands the pointer back to the catch task instead.

**1.** Give `GetterWork` a field ([include/battle/battle.h](../../include/battle/battle.h),
`struct GetterWork`). It is only allocated on the heap, so its size can change:

```c
    void *tempPointers[2];
    GetterWork *resumeWork; // a task to hand ctx->getterWork back to when this one ends
};
```

**2.** In `battle_command.c`, split `BtlCmd_CalcExpGain` into a helper that can be called
without a battle script:

```c
// Sets ctx->gainedExp and ctx->partyGainedExp for ctx->battlerIdFainted.
// Returns FALSE if this battle gives no experience.
static BOOL BattleContext_CalcExpGain(BattleSystem *battleSystem, BattleContext *ctx) {
    u32 battleType = BattleSystem_GetBattleType(battleSystem);
    OpponentData *opponentData = BattleSystem_GetOpponentData(battleSystem, ctx->battlerIdFainted);

    if (!(opponentData->battlerType & BATTLER_TYPE_IS_ENEMY) || (battleType & BATTLE_TYPE_NO_EXP)) {
        return FALSE;
    }

    int expMonsCnt = 0;
    // ... the rest of the old if-block, unchanged, up to ctx->partyGainedExp = 0; } ...

    return TRUE;
}

BOOL BtlCmd_CalcExpGain(BattleSystem *battleSystem, BattleContext *ctx) {
    BattleScriptIncrementPointer(ctx, 1);

    int adrs = BattleScriptReadWord(ctx);

    if (!BattleContext_CalcExpGain(battleSystem, ctx)) {
        BattleScriptIncrementPointer(ctx, adrs);
    }

    return FALSE;
}
```

**3.** In `BtlCmd_StartGetExpTask`, after `tempData[DATA_GET_EXP_PARTY_SLOT] = 0;`:

```c
    ctx->getterWork->resumeWork = NULL;
```

and in `Task_GetExp`:

```c
    case STATE_GET_EXP_DONE:
        data->ctx->getterWork = data->resumeWork; // was NULL
```

**4.** Add two states at the end of the `STATE_GET_POKEMON_*` enum:

```c
    STATE_GET_POKEMON_GRANT_EXP,
    STATE_GET_POKEMON_WAIT_FOR_EXP,
```

**5.** In `Task_GetPokemon`, `case STATE_GET_POKEMON_BALL_FADE:`
([battle_command.c:6785](../../src/battle/battle_command.c#L6785)) goes to
`STATE_GET_POKEMON_CHECK_MON_DATA`. Send it to the new state, and add the two cases after
it:

```c
    case STATE_GET_POKEMON_BALL_FADE:
        if (!TextPrinterCheckActive(data->tempData[DATA_GET_POKEMON_PRINTER_ID])) { // Wait for the text box to finish printing.
            data->state = STATE_GET_POKEMON_GRANT_EXP;
            BallThrow_SetBallAnimation(data->ballData, BALL_ANIM_FADE);
        }
        break;
    case STATE_GET_POKEMON_GRANT_EXP:
        data->ctx->battlerIdFainted = battlerId;
        if (!(BattleSystem_GetBattleType(data->battleSystem) & BATTLE_TYPE_TUTORIAL)
            && BattleContext_CalcExpGain(data->battleSystem, data->ctx)) {
            GetterWork *expWork = Heap_Alloc(HEAP_ID_BATTLE, sizeof(GetterWork));
            expWork->battleSystem = data->battleSystem;
            expWork->ctx = data->ctx;
            expWork->state = 0;
            expWork->tempData[DATA_GET_EXP_PARTY_SLOT] = 0;
            expWork->resumeWork = data; // Task_GetExp hands ctx->getterWork back to us
            data->ctx->getterWork = expWork;
            SysTask_CreateOnMainQueue(Task_GetExp, expWork, 0);
            data->state = STATE_GET_POKEMON_WAIT_FOR_EXP;
        } else {
            data->state = STATE_GET_POKEMON_CHECK_MON_DATA;
        }
        break;
    case STATE_GET_POKEMON_WAIT_FOR_EXP:
        if (data->ctx->getterWork == data) {
            data->state = STATE_GET_POKEMON_CHECK_MON_DATA;
        }
        break;
```

Notes:

- The caught Pokémon is not in the party yet at this point, so it gets nothing.
- Safari Zone and Pal Park catches give nothing (`BATTLE_TYPE_NO_EXP`), and neither does
  the catching tutorial (`BATTLE_TYPE_TUTORIAL`).
- A Pokémon that levels up here can evolve after the battle: `BattleSystem_CheckEvolution`
  runs after a catch.
- This must not run after `STATE_GET_POKEMON_CHECK_MON_DATA`. From there the screen fades
  out for the Pokédex and naming screen, and the naming screen frees the battle graphics.

## 8. Recipe: level caps by badge count

A level cap here stops a Pokémon gaining experience past a level set by the badges you
have. It can still be traded in, or given, above the cap. Obedience (traded Pokémon) is a
separate rule in [gyms.md](gyms.md#what-badges-do).

**1. The caps.** In [src/pokemon.c](../../src/pokemon.c), above `Pokemon_TryLevelUp`. The
numbers are each next leader's highest level in `trainers.json`, in the usual gym order:

```c
// Highest level a Pokémon can reach by experience, by badge count (Johto + Kanto).
// Each entry is the highest level on the next leader's team.
static const u8 sLevelCapByBadges[] = {
    13, // Falkner
    17, // Bugsy
    19, // Whitney
    25, // Morty
    31, // Chuck
    35, // Jasmine
    35, // Pryce (34)
    41, // Clair
    50, // the League (Lance)
    60, // Kanto leaders: 53-60, any order
    60,
    60,
    60,
    60,
    60,
    60,
    MAX_LEVEL, // all 16 badges
};

int GetLevelCap(int badges) {
    if (badges >= NELEMS(sLevelCapByBadges)) {
        return MAX_LEVEL;
    }
    return sLevelCapByBadges[badges];
}
```

and declare it at the end of [include/pokemon.h](../../include/pokemon.h):

```c
int GetLevelCap(int badges);
```

The count includes Kanto badges (`PlayerProfile_CountBadges`). To cap by story events
instead, read a var or flag (see [level-scaling.md](level-scaling.md), which picks levels
the same ways).

**2. Battle.** In `Task_GetExp`, under `case STATE_GET_EXP_START:`, just above
`u32 newExp = GetMonData(mon, MON_DATA_EXPERIENCE, NULL);`:

```c
            int levelCap = GetLevelCap(PlayerProfile_CountBadges(BattleSystem_GetPlayerProfile(data->battleSystem, BATTLER_PLAYER)));
            u32 capExp = GetMonExpBySpeciesAndLevel(GetMonData(mon, MON_DATA_SPECIES, NULL), levelCap);
            u32 curExp = GetMonData(mon, MON_DATA_EXPERIENCE, NULL);
            if (curExp >= capExp) {
                totalExp = 0;
            } else if (curExp + totalExp > capExp) {
                totalExp = capExp - curExp;
            }
```

A Pokémon at the cap then gets no message. One just below it gets only enough to reach the
cap. For a softer cap, reduce the experience instead of removing it: replace
`totalExp = 0;` with `totalExp /= 10;`, and drop the `else if`.

**3. Rare Candy.** In [src/party_menu.c](../../src/party_menu.c), replace the
`if (CanUseItemOnMonInParty(...) == TRUE) {` line
([:2429](../../src/party_menu.c#L2429)) with:

```c
    BOOL overLevelCap = partyMenu->args->itemId == ITEM_RARE_CANDY
        && GetMonData(Party_GetMonByIndex(partyMenu->args->party, partyMenu->partyMonIndex), MON_DATA_LEVEL, NULL)
            >= GetLevelCap(PlayerProfile_CountBadges(Save_PlayerData_GetProfile(partyMenu->args->fieldSystem->saveData)));
    if (!overLevelCap && CanUseItemOnMonInParty(partyMenu->args->party, partyMenu->args->itemId, partyMenu->partyMonIndex, 0, HEAP_ID_PARTY_MENU) == TRUE) {
```

The Rare Candy is then refused with "It won't have any effect." and not used up.

**4. Day-Care (optional).** Day-Care experience is added in
`Save_Daycare_MoveMonToParty` ([get_egg.c:149](../../src/get_egg.c#L149)), and the level
the Day-Care Man quotes comes from `GetDaycareUpdatedLevel`
([get_egg.c:172](../../src/get_egg.c#L172)). Neither has the save at hand. Pass the badge
count down from the script command, or leave the Day-Care uncapped as a paid way around
the cap.

## 9. Testing the recipes

All four recipes (§5-§8), applied together to this tree, compile and link into a
HeartGold ROM. They have not been played: no emulator was available when they were
written. Check them in a game before relying on them:

| Recipe | Check |
|---|---|
| §5 | a fainted Pokémon and an egg in the party get nothing. A Lv. 100 Pokémon gets nothing |
| §6 | the §6 table, with one Pokémon facing a wild Pidgey |
| §7 | catch with the active Pokémon one level from a level-up and a move: level-up, move prompt, then the Pokédex entry and nickname. Catch with a full party (the PC message) and in the Bug-Catching Contest |
| §8 | a Pokémon at the cap gets no message. One just below it stops exactly at the cap. Rare Candy is refused at the cap |

To see the values while testing, print `totalExp` with `DebugPrintf`
([debugging.md](debugging.md#3-printf)).
