<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Changing and adding moves

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Moves are numbered by `MOVE_*` in `include/constants/moves.h`: `MOVE_NONE` is 0,
then 1 (`MOVE_POUND`) to 467 (`MOVE_SHADOW_FORCE`). `NUM_MOVES` is the last move,
not a count. Every per-move file below is indexed by that number.

## Where a move lives

| What | File | Editable? |
|---|---|---|
| Power, type, accuracy, PP, effect, target, flags... | `files/poketool/waza/battle_moves.json` | yes |
| Name | `files/msgdata/msg/msg_0750.json` (and `msg_0751.json`, upper case) | yes |
| Description | `files/msgdata/msg/msg_0749.json` | yes |
| What the move does in battle | effect script `files/battledata/script/effect_script/effect_script_NNNN.s`, chosen by `effect` | yes (battle script) |
| Text before the effect (charge turns, traps) | `files/battledata/script/move_script/move_script_NNNN_*.s` | yes (battle script) |
| Animation | `data/battle_anims/moves/NNNN_<MOVE>.anim` | yes ([move-animations.md](move-animations.md)) |
| Who learns it | learnsets, egg moves, TMs, tutors: [pokemon.md](pokemon.md#moves) | yes |
| Trainer movesets | `files/poketool/trainer/trainers.json` (`"moves"`) | yes |
| Special cases | lists in C, see [Moves named in C](#moves-named-in-c) | C |

## Move data: battle_moves.json

One entry per move, keyed by its constant, laid out like pokeemerald's
`src/data/battle_moves.h`. `tools/pokedata/pokedata.py moves` builds
`waza_tbl.narc` from it, and checks every name and range at build time with an
error that names the move.

```json
"MOVE_FLAMETHROWER": {
    "effect": "MOVE_EFFECT_BURN_HIT",
    "category": "CATEGORY_SPECIAL",
    "power": 95,
    "type": "TYPE_FIRE",
    "accuracy": 100,
    "pp": 15,
    "secondaryEffectChance": 10,
    "target": "RANGE_SINGLE_TARGET",
    "priority": 0,
    "flags": ["MOVE_FLAG_CAN_PROTECT", "MOVE_FLAG_CAN_MIRROR_MOVE", "MOVE_FLAG_KEEP_HP_BAR"],
    "contestEffect": 17,
    "contestCategory": "CONTEST_CATEGORY_BEAUTY"
}
```

| Field | Values | Notes |
|---|---|---|
| `effect` | `MOVE_EFFECT_*` (`include/constants/move_effects.h`) | picks the effect script; see [Effects](#effects) |
| `category` | `CATEGORY_PHYSICAL`, `CATEGORY_SPECIAL`, `CATEGORY_STATUS` | the physical/special split is per move |
| `power` | 0-255 | 0 for status moves and moves whose power is computed (Low Kick, Return...) |
| `type` | `TYPE_*` (`include/constants/pokemon.h`) | `TYPE_MYSTERY` is the "???" type (Curse) |
| `accuracy` | 0-100 | **0 never misses** (shown as "---"), e.g. Swift, Swords Dance |
| `pp` | 0-255 | PP Ups add 20% each (`GetMoveMaxPP`); retail tops out at 40 |
| `secondaryEffectChance` | 0-100 | percent chance of the added effect (burn, flinch, stat drop...); Serene Grace doubles it. See below |
| `target` | one `RANGE_*` (`include/constants/moves.h`) | table below |
| `priority` | -128-127 | retail: -7 Trick Room, -6 Roar, -5 Counter, -1 Vital Throw, +1 Quick Attack, +3 Protect, +4 Magic Coat, +5 Helping Hand |
| `flags` | list of `MOVE_FLAG_*` | table below |
| `contestEffect` | 0-255 | Super Contest appeal from Diamond/Pearl; nothing reads it in HGSS |
| `contestCategory` | `CONTEST_CATEGORY_COOL`/`BEAUTY`/`CUTE`/`SMART`/`TOUGH` | only shown as an icon (Move Relearner, battle party menu) |

**When `secondaryEffectChance` matters.** Effect scripts hand the added effect
to the engine as "direct" (always happens) or "indirect" side effects
(`BattleSystem_TryIndirectSideEffect`, `src/battle/battle_util.c`). An indirect
side effect flagged only `MOVE_SIDE_EFFECT_TO_DEFENDER` or `_TO_ATTACKER` is
rolled against this chance, so a "hit with a chance to burn" effect with chance 0
never burns. Effects whose side effect is `MOVE_SIDE_EFFECT_ON_HIT` or one of the
`_CHECK_*` flags (recoil, draining, binding, Pay Day) ignore it; retail leaves
those at 0. Copy the chance from a retail move with the same effect.

### Targets

| `target` | Who the move hits | Example |
|---|---|---|
| `RANGE_SINGLE_TARGET` | one Pokémon the player picks | Tackle, Curse (335 moves) |
| `RANGE_SINGLE_TARGET_SPECIAL` | decided by the move itself | Counter, Mirror Coat, Metronome, Sleep Talk |
| `RANGE_RANDOM_OPPONENT` | a random foe | Thrash, Outrage, Uproar |
| `RANGE_ADJACENT_OPPONENTS` | both foes | Growl, Blizzard, Rock Slide |
| `RANGE_ALL_ADJACENT` | everyone else, partner included | Surf, Earthquake, Explosion |
| `RANGE_USER` | the user | Swords Dance |
| `RANGE_USER_SIDE` | the user's side | Reflect, Heal Bell |
| `RANGE_FIELD` | the whole field | Rain Dance, Haze |
| `RANGE_OPPONENT_SIDE` | the foes' side | Spikes, Stealth Rock |
| `RANGE_ALLY` | the partner | Helping Hand |
| `RANGE_SINGLE_TARGET_USER_SIDE` | user or partner | Acupressure |
| `RANGE_FRONT` | the foe in front | Me First |

### Flags

| Flag | Meaning (where the game checks it) |
|---|---|
| `MOVE_FLAG_MAKES_CONTACT` | contact: Static, Rough Skin, Effect Spore, Poison Point, Flame Body, Cute Charm, Aftermath, Sticky Barb (`battle_util.c`) |
| `MOVE_FLAG_CAN_PROTECT` | blocked by Protect / Detect |
| `MOVE_FLAG_CAN_MAGIC_COAT` | bounced back by Magic Coat |
| `MOVE_FLAG_CAN_SNATCH` | stolen by Snatch |
| `MOVE_FLAG_CAN_MIRROR_MOVE` | remembered for Mirror Move |
| `MOVE_FLAG_CAN_KINGS_ROCK` | King's Rock / Razor Fang can make the target flinch |
| `MOVE_FLAG_KEEP_HP_BAR` | HP bars stay on screen during the animation (most damaging moves) |
| `MOVE_FLAG_ANIM_G3_MASK` | sets a 3D-sprite update mask during the animation; copy it from moves with similar animations |

## Effects

`effect` is what the move does. A move's battle script (`move_script_NNNN`) is
almost always just `GoToEffectScript`, which jumps to
`effect_script_<effect>.s` (`BtlCmd_GoToEffectScript`,
`src/battle/battle_command.c`). The effect script sets up damage and side
effects, which run shared subscripts in `files/battledata/script/subscript/`.
[battle-engine.md](battle-engine.md#5-battle-scripts) explains the script format,
variables and commands, and when in the turn each part runs.

```
_000:   // effect_script_0004.s, MOVE_EFFECT_BURN_HIT
    UpdateVar OPCODE_SET, BSCRIPT_VAR_SIDE_EFFECT_FLAGS_INDIRECT, MOVE_SIDE_EFFECT_TO_DEFENDER|MOVE_SUBSCRIPT_PTR_BURN
    CalcCrit
    CalcDamage
    End
```

- **Changing what a move does** = picking another existing `MOVE_EFFECT_*`
  (277 of them, 0-276). Check a retail move with that effect for the right
  `power`, `secondaryEffectChance`, `target` and `flags`.
- The trainer AI judges moves by effect (its scripts are still raw data in
  `asm/trainer_ai_data.s`; `src/battle/trainer_ai.c` also has effect lists such
  as `sAltPowerMoveEffects`), so a move with an existing effect is played like
  the retail moves that share it.
- Some effects need more than the effect script: their move script prints a
  message first (charge turns, traps), or C checks the move by name. The 21 move scripts
  with extra lines are Razor Wind, Fly, Bind, Wrap, Solar Beam, Fire Spin, Dig,
  Clamp, Skull Bash, Sky Attack, Future Sight, Whirlpool, Dive, Sand Tomb,
  Bounce, Doom Desire, Magma Storm and Shadow Force (a message), and
  Selfdestruct, Explosion and Splash (a game stat). A move that reuses one of
  those effects needs the same lines in its own move script.
- **A new effect**: add `effect_script_0277.s` (start from a similar one), list
  it in `files/battledata/script/effect_script/meson.build`, and add
  `#define MOVE_EFFECT_X 277` to `move_effects.h`. Behaviour the battle script
  commands (`asm/macros/btlcmd.inc`) can't express needs C in `src/battle/`.

## Names and descriptions

`msg_0750.json` (name), `msg_0751.json` (name in capitals) and `msg_0749.json`
(description) have one message per move, by number. Change the text in place;
to add a move, append a message to all three, so message N is move N.

- Retail names are at most 12 characters; longer ones may not fit the menus.
- Descriptions are 4 or 5 lines of up to about 20 characters, each line but the
  last ending in `\n`, like the existing ones.

## Moves named in C

These special cases list moves by constant. Add a new move to the ones it
belongs to, and check them when you change what an existing move does.

| List | File | Meaning |
|---|---|---|
| `sSoundMoves` | `src/battle/battle_util.c` | blocked by Soundproof |
| `sPunchingMoves` | `src/battle/battle_util.c` | boosted by Iron Fist |
| `sMetronomeUnuseableMoves` | `src/battle/battle_util.c` | Metronome never calls these; Mimic can't copy the ones before the `0xFFFE` marker |
| `sEncoreFailMoves`, `sMeFirstUnuseableMoves` | `src/battle/battle_util.c` | Encore / Me First fail |
| `sGravityUnusableMoves`, `sHealBlockUnusableMoves` | `src/battle/battle_util.c` | can't be used under Gravity / Heal Block |
| `sBattleAnimWeatherMasks` | `src/battle/battle_anim_system.c` | animations that change with the weather |
| `sTMHMMoves` | `src/item.c` | the move each TM/HM teaches (TM01 = index 0); compatibility is `tms`/`hms` in `personal.json` |
| `sTutorMoves` | `src/field/scrcmd_move_tutor.c` | move tutor moves and their cost; who learns them is `waza_oshie.json` ([move-tutors.md](move-tutors.md)) |
| `sFieldMoves` | `src/party_menu.c` | moves usable from the party menu |
| `sECMenu_Move_AtoL` / `_MtoZ` | `src/easy_chat_menu.c` | moves offered as easy-chat words |

Many single moves are also tested with `== MOVE_X` or `case MOVE_X` in
`src/battle/` (Struggle, Curse, Secret Power, Knock Off...). `grep -rn MOVE_X src`
before changing one of those.

## Adding a new move

The tables already have spare slots after Shadow Force: `battle_moves.json`
entries `"468"`-`"470"`, move scripts and animations up to 500. So the first
three new moves only need these steps:

1. **Constant.** In `include/constants/moves.h` add
   `#define MOVE_FLAME_BURST 468` after `MOVE_SHADOW_FORCE` and change
   `#define NUM_MOVES MOVE_FLAME_BURST`.
2. **Data.** In `battle_moves.json` rename the key `"468"` to `"MOVE_FLAME_BURST"`
   and fill in the fields. Keys stay in number order; entries past `NUM_MOVES`
   are numbers.
3. **Text.** Append message 468 to `msg_0750.json`, `msg_0751.json` and
   `msg_0749.json`.
4. **Battle script.** `move_script_0468.s` already does `GoToEffectScript`;
   rename it (and its line in `move_script/meson.build`) if you like. Add lines
   only if the effect needs them (see [Effects](#effects)).
5. **Animation.** The spare animations only play a sound. Reuse an existing one: in
   `BattleAnimSystem_StartMove` (`src/battle/battle_anim_system.c`), next to the
   Secret Power case, add
   `if (animId == MOVE_FLAME_BURST) { animId = MOVE_FLAMETHROWER; }`. Or copy and
   change a script in `data/battle_anims/moves/`
   ([move-animations.md §8](move-animations.md#8-recipes)).
6. **Learners.** Add it to learnsets, egg moves, a TM or tutor, or a trainer's
   moveset ([pokemon.md](pokemon.md#moves)), and to the
   [lists in C](#moves-named-in-c) it belongs in.

Past 470, add new `battle_moves.json` entries too (the build wants every number
from 0 to `NUM_MOVES`). Past 500, also add `move_script_0501.s` and so on to
`move_script/meson.build`, and an animation member for each new move
([move-animations.md §8.3](move-animations.md#83-a-move-past-500)): only ids above
`NUM_MOVES` fall back to Pound's animation, a missing member fails to load.

**Limits.**

- **511 moves.** Level-up learnsets store the move in 9 bits
  (`LEVEL_UP_LEARNSET_MOVEID_MASK`); `pokedata.py` refuses bigger ids there.
- The battle keeps a copy of the whole table (`moveData[NUM_MOVES + 1]` in
  `BattleContext`, `include/battle/battle.h`): 16 bytes of battle heap per move.
- Battle videos reject Pokémon with a move above `NUM_MOVES` (`src/battle_record.c`),
  so a hack's videos won't play on retail games.
- Moves are saved as numbers, so changing a move's data is save-safe; **don't
  renumber** existing moves.

## Checking your edits

- `python3 tools/pokedata/test_pokedata.py`: the unmodified JSON still builds
  the retail `waza_tbl.narc`, and bad input gives clear errors.
- `make release` builds the ROM. `make` also runs the checksum tests, which fail
  after any data change; that is expected.
- `python3 tools/pokedata/pokedata.py extract-moves <waza_tbl.narc> out.json --include include`
  turns a NARC back into JSON (for example to compare with another ROM).
