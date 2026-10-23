<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Abilities

> AI-generated, local to this fork. Do not upstream.

An ability is a number. Its name and description are text, and what it does is
C code that compares a Pokémon's ability against that number at the right moment
in battle (or in the field). There is no ability table to fill in: adding one means
a constant, three text entries, the species that get it, and code.

| pokeemerald | here |
|---|---|
| `include/constants/abilities.h` | `include/constants/abilities.h` |
| `src/data/text/abilities.h` (names, descriptions) | `files/msgdata/msg/msg_0720.json` (names), `msg_0722.json` (descriptions), `msg_0721.json` (Easy Chat names) |
| `.abilities = { ... }` in `src/data/pokemon/species_info.h` | `"abilities"` in `files/poketool/personal/personal.json` |
| `src/battle_util.c` `AbilityBattleEffects` (one big switch) | several functions in `src/battle/battle_util.c`, one per moment ([where an ability can act](#where-an-ability-can-act)) |
| `data/battle_scripts_1.s` | `files/battledata/script/subscript/*.s` |

## Limits

- An ability is a `u8` everywhere it's stored (box data, `BattleMon`, personal
  data, Trainer House), so ids go up to 255. 124 are used (0-123).
- `NUM_ABILITIES` is defined as the **last** ability (`ABILITY_BAD_DREAMS`, 123),
  not the count. It's only used as "no ability" when the party lead is an egg
  (`src/field/encounter_check.c:1384`, `src/field/rock_smash_item.c:149`). You can
  leave it alone. If you move it to your new ability and that ability has a field
  effect, an egg in the lead would trigger it.
- Easy Chat only offers abilities 0-123 (`EC_WORDS_ABILITY_COUNT` in
  `include/constants/easy_chat.h`). Don't raise it: every Easy Chat word after the
  abilities would get a new id, which breaks saved mail, Trainer Card messages and
  the hard-coded `EC_WORD_*` values. New abilities just aren't Easy Chat words.

## Adding an ability

### 1. The constant

`include/constants/abilities.h`, after the last one:

```c
#define ABILITY_BAD_DREAMS     123
#define ABILITY_STRONG_JAW     124
#define ABILITY_INTREPID_SWORD 125
```

### 2. The text

Add one entry to the end of each of the three files, in id order. The entry's
position is the ability id; the `id` string is only a label.

`files/msgdata/msg/msg_0720.json`, the name (summary screen, battle messages):

```json
    {
      "id": "msg_0720_00124",
      "en_US": "Strong Jaw"
    }
```

`files/msgdata/msg/msg_0721.json`, the name in capitals (Easy Chat's word list;
add it anyway so the files stay the same length):

```json
    {
      "id": "msg_0721_00124",
      "en_US": "STRONG JAW"
    }
```

`files/msgdata/msg/msg_0722.json`, the description (summary screen, battle party
menu), two lines:

```json
    {
      "id": "msg_0722_00124",
      "en_US": [
        "Boosts the power of\n",
        "biting moves."
      ]
    }
```

The longest existing name is 12 characters ("Wonder Guard") and the longest
description line is 26; staying within those is safe.

### 3. Give it to a Pokémon

In `files/poketool/personal/personal.json`, each species has two slots:

```json
      "abilities": [
        "ABILITY_STRONG_JAW",
        "ABILITY_NONE"
      ],
```

A Pokémon's slot comes from its personality value (odd or even), and the
ability is stored in the Pokémon when it's created. **Pokémon that already exist
in a save keep their old ability.** Trainer Pokémon pick a slot with
`"abilityOverride"` (`TRPOKE_ABILITY_OVERRIDE_OFF`, `_FIRST`, `_SECOND`) in
`files/poketool/trainer/trainers.json`. See [pokemon.md](pokemon.md#base-stats-types-abilities-items-tmhm).

At this point the build works, the ability shows on the summary screen, and it
does nothing.

### 4. Make it do something

Find the existing ability that works most like yours, and add your case next to
it. The next section lists where each kind lives.

### 5. Build

`make release`. The two examples below were built this way and the ROM built
cleanly; they were not playtested.

## Where an ability can act

All in `src/battle/` unless noted. Line numbers are approximate.

| Kind of ability | Function | Copy from |
|---|---|---|
| boosts move power or a stat in the damage formula | `CalcMoveDamage` (`battle_util.c:5540`) | Technician, Iron Fist, Huge Power, Blaze/Torrent, Guts |
| changes type effectiveness | `BattleSystem_ApplyTypeEffectiveness` (`battle_util.c:2231`), `CalcTypeEffectivenessFlags` (:2334) | Levitate, Wonder Guard, Filter, Tinted Lens, Scrappy |
| absorbs or blocks a move | `BattleContext_CheckMoveImmunityFromAbility` (`battle_util.c:3020`) | Volt Absorb, Flash Fire, Motor Drive, Soundproof |
| does something on switch-in | `TryAbilityOnEntry` (`battle_util.c:3135`) | Intimidate, Drizzle, Download, Pressure |
| does something at end of turn | `BattleContext_TryEndOfTurnAbility` (`battle_util.c:3068`) | Speed Boost, Shed Skin |
| reacts to being hit | `CheckAbilityEffectOnHit` (`battle_util.c:3580`) | Static, Rough Skin, Color Change |
| prevents a status | `CheckStatusHealAbility` (`battle_util.c:3688`), `CheckStatusHealSwitch` (:3755) | Limber, Insomnia, Water Veil |
| prevents stat drops | `BtlCmd_ChangeStatStage` (`battle_command.c:1570`) | Clear Body, Hyper Cutter, Keen Eye |
| changes speed / turn order | `CheckSortSpeed` (`battle_util.c:966`) | Swift Swim, Chlorophyll, Quick Feet |
| changes accuracy or evasion | `BattleSystem_CheckMoveHit` (`battle_controller_player.c:2419`) | Compound Eyes, Hustle, Sand Veil |
| changes critical hits | `TryCriticalHit` (`battle_util.c:5967`) | Super Luck, Battle Armor |
| changes secondary effect chance | `BattleSystem_TryIndirectSideEffect` (`battle_util.c:1281`), `BtlCmd_CheckEffectActivation` | Serene Grace |
| traps the foe | `CantEscape` (`battle_util.c:2719`), `BattlerCanSwitch` (:4632) | Shadow Tag, Arena Trap |
| changes weather damage or healing | `BtlCmd_EndOfTurnWeatherEffect` (`battle_command.c:3391`) | Rain Dish, Ice Body, Dry Skin |
| changes recoil, OHKO, multi-hit | battle scripts with `CheckAbility` (`effect_script_0045.s`), `BtlCmd_TryOHKOMove`, `BtlCmd_SetMultiHit` | Reckless, Sturdy, Skill Link |
| works in the field | `src/field/encounter_check.c` (encounter rate, wild level, nature, gender, type), `src/field/rock_smash_item.c`, `src/get_egg.c:656` (hatching) | Stench, Hustle, Synchronize, Magnet Pull, Flame Body |
| after battle | `BtlCmd_GenerateEndOfBattleItem` (`battle_command.c:4749`) | Pickup, Honey Gather |

To see every place an existing ability is handled:
`grep -rn ABILITY_IRON_FIST src files/battledata`.

### Reading a battler's ability

- `GetBattlerAbility(ctx, battlerId)` returns `ABILITY_NONE` while Gastro Acid is
  active (and for Levitate under Gravity or Ingrain). Use it, not
  `ctx->battleMons[i].ability`, so suppression works.
- For abilities that **protect the target**, use
  `CheckBattlerAbilityIfNotIgnored(ctx, attacker, target, ABILITY_X)`, which
  returns FALSE when the attacker has Mold Breaker.
- `CheckAbilityActive(battleSystem, ctx, CHECK_ABILITY_*, battlerId, ABILITY_X)`
  asks whether anyone on a side, or on the field, has it (Cloud Nine, Damp,
  Pressure). The `CHECK_ABILITY_*` modes are in `include/constants/battle.h`.
- In `CalcMoveDamage`, `calcAttacker.ability` and `calcTarget.ability` already
  come from `GetBattlerAbility`.

## Example 1: a damage boost (Strong Jaw)

Biting moves get 1.5× power. Iron Fist does the same for punches, so copy it in
`src/battle/battle_util.c`. Add a move list after `sPunchingMoves`:

```c
static const u16 sBitingMoves[] = {
    MOVE_BITE,
    MOVE_CRUNCH,
    MOVE_HYPER_FANG,
    MOVE_POISON_FANG,
    MOVE_FIRE_FANG,
    MOVE_ICE_FANG,
    MOVE_THUNDER_FANG
};
```

and in `CalcMoveDamage`, after the Iron Fist loop:

```c
    for (i = 0; i < NELEMS(sBitingMoves); i++) {
        if (sBitingMoves[i] == moveNo && calcAttacker.ability == ABILITY_STRONG_JAW) {
            movePower = movePower * 15 / 10;
            break;
        }
    }
```

That's all. The trainer AI estimates damage with the same `CalcMoveDamage`
(`trainer_ai.c:2923`), so it takes the boost into account too.

## Example 2: a switch-in effect (Intrepid Sword)

Raise Attack one stage when the Pokémon enters battle, once per switch-in.
Switch-in abilities need a "done" bit per battler, or they would fire again
every time `TryAbilityOnEntry` runs.

**The bit.** `BattleMon` in `include/battle/battle.h` has 21 unused bits after the
switch-in flags; take one:

```c
    u32 pressureFlag : 1;
    u32 intrepidSwordFlag : 1;
    u32 unk28_C : 20;
```

**Clear it on switch-in and on Transform.** Two places clear the other flags; add
yours to both: the battler loader near the top of `battle_util.c` (after
`pressureFlag = 0`, around line 95) and Transform in `battle_command.c` (around
line 3290):

```c
    ctx->battleMons[battlerId].intrepidSwordFlag = 0;
```

**The trigger.** `TryAbilityOnEntry` is a state machine: `ctx->sendOutState`
steps through cases 0-15 (weather, Trace, Intimidate, Download, ..., held items)
and each case either starts a battle script or moves on. Add a case before the
last one and renumber the end:

```c
        case 15: // Intrepid Sword
            for (i = 0; i < maxBattlers; i++) {
                battlerId = ctx->turnOrder[i];
                if (!ctx->battleMons[battlerId].intrepidSwordFlag && ctx->battleMons[battlerId].hp && GetBattlerAbility(ctx, battlerId) == ABILITY_INTREPID_SWORD) {
                    ctx->battleMons[battlerId].intrepidSwordFlag = TRUE;
                    if (ctx->battleMons[battlerId].statChanges[STAT_ATK] < MAX_STAT_STAGE) {
                        ctx->statChangeParam = MOVE_SUBSCRIPT_PTR_ATTACK_UP_1_STAGE;
                        ctx->statChangeType = 3;
                        ctx->battlerIdStatChange = battlerId;
                        script = BATTLE_SUBSCRIPT_UPDATE_STAT_STAGE;
                        flag = TRUE;
                        break;
                    }
                }
            }
            if (i == maxBattlers) {
                ctx->sendOutState++;
            }
            break;
        case 16: // end
            ctx->sendOutState = 0;
```

The order of the cases is the order effects happen when several Pokémon come out
at once.

**Why no text was needed.** `BATTLE_SUBSCRIPT_UPDATE_STAT_STAGE` with
`statChangeType = 3` prints "{Pokémon}'s {ability} raised its {stat}!" using the
ability's name (`BtlCmd_ChangeStatStage`, `battle_command.c:1616`). Speed Boost and
Download use it the same way.

| `statChangeType` | Message |
|---:|---|
| 3 | "X's *ability* raised its *stat*!" (failures are silent) |
| 5 | "The *item* raised X's *stat*!" |
| 2 | silent on failure (secondary effects) |
| other | "X's *stat* rose!" |

`statChangeParam` is a `MOVE_SUBSCRIPT_PTR_*` from
`include/constants/battle_subscript.h`: `…_ATTACK_UP_1_STAGE` (15) through
`…_EVASION_UP_1_STAGE` (21), `…_DOWN_1_STAGE` (22-28), `…_UP_2_STAGES` (39-45),
`…_DOWN_2_STAGES` (46-52).

## When you need your own message or script

Most abilities can reuse an existing subscript. Some that take a parameter:

| Subscript | Does | Set first |
|---|---|---|
| `BATTLE_SUBSCRIPT_UPDATE_STAT_STAGE` | raise or lower a stat | `statChangeParam`, `statChangeType`, `battlerIdStatChange` |
| `BATTLE_SUBSCRIPT_ABILITY_RESTORES_HP` | heal, "restored HP using its *ability*" | `hpCalc` |
| `BATTLE_SUBSCRIPT_PARALYZE` (and the other status ones) | inflict a status | `battlerIdStatChange`, `battlerIdTemp`, `statChangeType = 3` |
| `BATTLE_SUBSCRIPT_ABILITY_RESTORE_STATUS` | cure the user's status | `battlerIdTemp`, `msgTemp` |

Look at how the ability you copied fills these in.

**A new message.** Battle text is `files/msgdata/msg/msg_0197.json`. Messages that
name a Pokémon come in threes: yours, "The wild …", "The foe's …"
(`BattleSystem_AdjustMessageForSide`, `src/battle/battle_system.c:1453`, adds 0, 1
or 2). Append all three to the end of the file and refer to the first as
`msg_0197_NNNNN`. Placeholders: `{STRVAR_1 1, 0, 0}` is the Pokémon's name,
`{STRVAR_1 5, 1, 0}` an ability, `{STRVAR_1 13, 2, 0}` a stat; copy them from a
similar message such as `msg_0197_00622`.

**A new subscript.**

1. Write `files/battledata/script/subscript/subscript_0297_YourName.s`, copying a
   similar one (`subscript_0190_*.s` prints a message with `TAG_NICKNAME_ABILITY_*`).
   The commands are macros in `asm/macros/btlcmd.inc`.
2. Add it at the end of the list in `files/battledata/script/subscript/meson.build`.
   Its position in the list is its id.
3. Add `#define BATTLE_SUBSCRIPT_YOUR_NAME 297` after the last
   `BATTLE_SUBSCRIPT_*` in `include/constants/battle_subscript.h`.
4. From C: `script = BATTLE_SUBSCRIPT_YOUR_NAME`, as in the examples above.

[moves.md](moves.md) covers the other battle scripts (move effects), which use the
same commands.

## Things that check for specific abilities

Other mechanics have their own lists. Decide whether your ability belongs in them:

| Mechanic | Where | Current list |
|---|---|---|
| Mold Breaker ignores it | use `CheckBattlerAbilityIfNotIgnored` for target-side checks | |
| Skill Swap fails | `subscript_0143_SwapAbility.s` | Wonder Guard, Multitype |
| Trace can't copy it | `ChooseTraceTarget` (`battle_util.c:6589`) | Trace, Forecast, Multitype |
| Worry Seed, Knock Off, Trick fail | `subscript_0167_WorrySeed.s`, `_0142_`, `_0134_` | Multitype |
| Gastro Acid can't suppress it | `GetBattlerAbility` | Multitype |
| AI avoids attacking into it | `AI_HasAbsorbAbilityInParty`, `AI_CannotDamageWonderGuard` and the AI scripts (`trainer_ai.c`) | absorb abilities, Wonder Guard |

## Checklist

- [ ] `ABILITY_*` in `include/constants/abilities.h`
- [ ] one entry at the end of `msg_0720.json`, `msg_0721.json`, `msg_0722.json`
- [ ] the ability in `personal.json` for each species that has it
- [ ] the effect in the right function, using `GetBattlerAbility` /
      `CheckBattlerAbilityIfNotIgnored`
- [ ] for a once-per-switch-in effect: a `BattleMon` bit, cleared in both places
- [ ] any new message (three versions) or subscript (file, `meson.build`, constant)
- [ ] the ability lists above, if they apply
- [ ] `make release`

## Not verified

- Neither example was tested in game, only built.
- Where the trainer AI's script data (the code that scores moves) checks abilities;
  `asm/trainer_ai_data.s` only holds the command table.
- Whether any link or Battle Frontier code assumes 124 abilities. Nothing found by
  grep, but both players in a link battle need the same ROM anyway.
