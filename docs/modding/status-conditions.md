<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Adding a status condition

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A Pokémon has one major status at a time: sleep, poison, bad poison, burn, freeze or
paralysis. It is kept after battle and shown as an icon (PSN, BRN...). Confusion,
infatuation, Leech Seed and the like are *volatile*. They are separate bits in
`status2` and `moveEffectFlags` that are cleared on switching out, and this guide
doesn't cover them.

The guide adds **Frostbite**, from Legends: Arceus:

- 1/16 of max HP lost at the end of each turn.
- The Pokémon's special moves do half damage.
- Ice types can't get it.
- The items that cure freeze also cure frostbite.

Nothing else in the game knows about a new status. You write the battle scripts that
inflict it and hurt with it, and then add it to each list of statuses: icons, curing
items, berries, abilities, the catch rate.

Steps 1-9 (all but the Facade/Refresh change) were built together with `make release`.
[Not verified](#not-verified) lists what wasn't tried in game.

| pokeemerald | here |
|---|---|
| `STATUS1_*` in `include/constants/battle.h` | `STATUS_*` in `include/constants/battle.h`, plus `MON_STATUS_*_MASK` in `include/constants/pokemon.h` (the same bits under other names) |
| `BattleScript_MoveEffectBurn` and friends in `data/battle_scripts_1.s` | one subscript per status in `files/battledata/script/subscript/` |
| `gStatusConditionString_*`, `gText_*` | `files/msgdata/msg/msg_0197.json` (battle text), `msg_0044.json` (status names) |
| `gStatusIcons` sprite sheets | the `a/0/3/9` archive (party, summary) and a C byte array (battle HP bar) |

## How status is stored

A Pokémon's status is a `u32` in its party data (`include/pokemon_types_def.h:200`).
In battle it is copied to `battleMons[i].status` and written back afterwards. The
bits (`include/constants/battle.h:296`):

| Bits | Constant | Meaning |
|---|---|---|
| 0-2 | `STATUS_SLEEP` | turns of sleep left (1-7) |
| 3 | `STATUS_POISON` | poison |
| 4 | `STATUS_BURN` | burn |
| 5 | `STATUS_FREEZE` | freeze |
| 6 | `STATUS_PARALYSIS` | paralysis |
| 7 | `STATUS_BAD_POISON` | bad poison (Toxic) |
| 8-11 | `STATUS_POISON_COUNT` | Toxic's turn counter |
| 12-31 | | free |

**The new status has to be bit 12 or higher**, because bits 0-11 are all used. That
has consequences:

- Three places keep only the low 8 bits. Quick Feet (`battle_util.c:1059` and
  `:1118`) and Hydration (`battle_command.c:3438`) test `status & 0xFF` or
  `(u8)status`, so they ignore bit 12. [Step 8](#8-the-places-that-would-miss-it)
  fixes them.
- A roamer saves its status as a `u8` (`include/roamer.h:31`, written at
  `src/field/field_move_cut_in_effects.c:1044`). A frostbitten Raikou is healthy the
  next time you meet it. Widening the field changes the save layout
  ([save-compatibility.md](save-compatibility.md)), so this guide leaves it.

**Saves.** Party data already has room for all 32 bits, so a new status keeps saves
compatible. Box Pokémon have no status: `CopyBoxPokemonToPokemon` sets it to 0
(`src/pokemon.c:3239`), and so do the Pokémon Center, the Day-Care, the PC and the
Battle Frontier.

There is also a small number for each status, `CONDITION_*`
(`include/constants/battle.h:318`): 0 none, 1 sleep, 2 poison, 3 burn, 4 freeze,
5 paralysis. `Battler_GetStatusCondition` (`src/battle/battle_util.c:1582`) turns
the bits into it, and the battle HP bar draws its icon from it. The status animation
ids `BATTLE_ANIMATION_ASLEEP` ... `_PARALYZED`
(`include/constants/battle_subscript.h:450`) have the same numbers, so the battle
scripts pass `BATTLE_ANIMATION_BURNED` where they mean `CONDITION_BURN`.

## What to change

| Step | Files | Needed? |
|---|---|---|
| [1. Constants](#1-constants) | `include/constants/battle.h`, `pokemon.h` | yes |
| [2. Text](#2-text) | `msg_0197.json`, `msg_0044.json` | yes |
| [3. Inflicting it](#3-inflicting-it-a-subscript-and-a-move-effect) | a subscript, an effect script, `battle_util.c`, `battle_moves.json` | yes |
| [4. End-of-turn damage](#4-end-of-turn-damage) | a subscript, `battle_controller_player.c` | for a status that does damage |
| [5. What it does in battle](#5-what-it-does-in-battle-special-damage) | `battle_util.c` | yes, or it only does damage |
| [6. Icons](#6-icons) | `pokemon_summary.c`, `battle_hp_bar.c` | yes: otherwise the party shows no icon and the HP bar shows none |
| [7. Curing it](#7-curing-it) | `use_item_on_mon.c`, `battle_system.c`, `trainer_ai.c`, `battle_util.c`, `battle_command.c` | yes, or only the Pokémon Center cures it |
| [8. Places that would miss it](#8-the-places-that-would-miss-it) | `follow_mon_interaction.c`, `battle_util.c`, `battle_command.c`, Psycho Shift | yes: following Pokémon hits an assert |
| [9. Optional](#9-optional) | catch rate, Synchronize, Facade/Refresh | your choice |

Asserts are compiled out of `make release` (`include/assert.h`), so a missing case
gives a wrong icon or message, not an error.

## 1. Constants

`include/constants/battle.h`, after `STATUS_POISON_COUNT` (line 305), and in
`STATUS_ALL` (line 311):

```c
#define STATUS_POISON_COUNT (15 << 8)
#define STATUS_FROSTBITE    (1 << 12)
...
#define STATUS_ALL             (STATUS_SLEEP | STATUS_POISON | STATUS_BURN | STATUS_FREEZE | STATUS_PARALYSIS | STATUS_BAD_POISON | STATUS_FROSTBITE)
```

and after `CONDITION_PARALYSIS` (line 323):

```c
#define CONDITION_FROSTBITE 6
```

`STATUS_ALL` means "has a status". Lum Berry, Shed Skin, Psycho Shift and the
disobedience nap use it, so they handle frostbite once it is in there.

`include/constants/pokemon.h`, after `MON_STATUS_PRZ_SHIFT` (line 86). Code
outside battle uses these names:

```c
#define MON_STATUS_FRB_MASK  0x1000
#define MON_STATUS_FRB_SHIFT 12
```

`Battler_GetStatusCondition` (`src/battle/battle_util.c:1582`) needs the new
number at the end of its chain:

```c
    } else if (ctx->battleMons[battlerId].status & STATUS_BAD_POISON) {
        return CONDITION_POISON;
    } else if (ctx->battleMons[battlerId].status & STATUS_FROSTBITE) {
        return CONDITION_FROSTBITE;
    }
```

## 2. Text

**Battle messages** are in `files/msgdata/msg/msg_0197.json`. A message about one
Pokémon comes in three versions: yours, "The wild …" and "The foe's …"
(`BattleSystem_AdjustMessageForSide`, `src/battle/battle_system.c:1453`, adds 0, 1
or 2). Scripts name the first one. Append nine messages at the end; the file ends
at `msg_0197_01275`:

```json
    {
      "id": "msg_0197_01276",
      "en_US": "{STRVAR_1 1, 0, 0} was frostbitten!"
    },
    {
      "id": "msg_0197_01277",
      "en_US": [
        "The wild {STRVAR_1 1, 0, 0}\n",
        "was frostbitten!"
      ]
    },
    {
      "id": "msg_0197_01278",
      "en_US": [
        "The foe’s {STRVAR_1 1, 0, 0}\n",
        "was frostbitten!"
      ]
    },
```

01279-01281 are the same three with "is hurt\n" / "by its frostbite!" (copy
`msg_0197_00095`-`00097`). 01282-01284 are "already\n" / "has frostbite." (copy
`00098`-`00100`).

**The status name** is in `files/msgdata/msg/msg_0044.json`: sleep, poison, burn,
paralysis, frozen, confusion, infatuation (0-6). `BufferStatusName`
(`src/message_format.c:247`) reads it for messages such as "{0}'s Shed Skin cured
its {2} status!". Append the new one as 7:

```json
    {
      "id": "msg_0044_00007",
      "en_US": "frostbite"
    }
```

## 3. Inflicting it: a subscript and a move effect

A status is given by a **subscript**, one per status: `subscript_0025_Burn.s`,
`subscript_0027_Freeze.s`... The same subscript runs for every way of getting the
status: a move's added effect, a status move, an ability (Flame Body), a held item
(Flame Orb), Synchronize and Psycho Shift. It checks immunities, plays the animation,
sets the bit, prints the message and sets the HP bar icon.
[battle-engine.md](battle-engine.md#5-battle-scripts) explains the script commands.

### The subscript

Copy `subscript_0025_Burn.s` to `subscript_0297_Frostbite.s` and change it:

- `STATUS_BURN` to `STATUS_FROSTBITE` and `TYPE_FIRE` to `TYPE_ICE` (the immunity)
  everywhere.
- Delete the two Water Veil checks and the block they jump to (`_264`, "prevents
  burns"). No ability blocks frostbite. To add one, copy how Water Veil is checked
  and give your ability's message.
- Use `BATTLE_ANIMATION_FROZEN` for the animation (there is no frostbite animation).
- Replace the three messages at `_152`-`_185` with one, and give `SetHealthbarStatus`
  the new number:

```
_141:
    PlayBattleAnimation BATTLER_CATEGORY_SIDE_EFFECT_MON, BATTLE_ANIMATION_FROZEN
    Wait 
    UpdateMonData OPCODE_FLAG_ON, BATTLER_CATEGORY_SIDE_EFFECT_MON, BMON_DATA_STATUS, STATUS_FROSTBITE
    // {0} was frostbitten!
    PrintMessage msg_0197_01276, TAG_NICKNAME, BATTLER_CATEGORY_SIDE_EFFECT_MON
    Wait 
    SetHealthbarStatus BATTLER_CATEGORY_SIDE_EFFECT_MON, CONDITION_FROSTBITE
    WaitButtonABTime 30

_211:
    End 
```

- In `_228`, print `msg_0197_01282` ("already has frostbite").

The burn subscript's held-item and ability branches print "got a burn from the
{item}" and "{ability} burned {Pokémon}". Without them, an item or ability that gives
frostbite prints the plain message. The Synchronize lines at `_190` are dropped too;
[step 9](#9-optional) puts Synchronize back.

### The side-effect pointer

Moves don't call the subscript by number. Their effect scripts set a
`MOVE_SUBSCRIPT_PTR_*`, an index into `sMoveStatusChangeScripts`
(`src/battle/battle_util.c:6287`). Add the subscript and the pointer in
`include/constants/battle_subscript.h`:

```c
#define BATTLE_SUBSCRIPT_GIRATINA_FORM_CHANGE             296
#define BATTLE_SUBSCRIPT_FROSTBITE                        297
...
#define MOVE_SUBSCRIPT_PTR_GIVE_TARGET_OWN_STATUS           144
#define MOVE_SUBSCRIPT_PTR_FROSTBITE                        145
```

then make the table one longer and add the subscript at the end:

```c
static const int sMoveStatusChangeScripts[146] = {
    ...
    BATTLE_SUBSCRIPT_GIVE_TARGET_OWN_STATUS,
    BATTLE_SUBSCRIPT_FROSTBITE
};
```

and add `'subscript_0297_Frostbite.s',` at the end of
`files/battledata/script/subscript/meson.build` (its position is its id). That file
uses Windows line endings (CRLF), so keep them.

### The move effect

`effect_script_0004.s` (`MOVE_EFFECT_BURN_HIT`, Ember) is three lines. Copy it to
`effect_script_0277.s` with the new pointer:

```
_000:
    UpdateVar OPCODE_SET, BSCRIPT_VAR_SIDE_EFFECT_FLAGS_INDIRECT, MOVE_SIDE_EFFECT_TO_DEFENDER|MOVE_SUBSCRIPT_PTR_FROSTBITE
    CalcCrit 
    CalcDamage 
    End 
```

List it at the end of `files/battledata/script/effect_script/meson.build` (CRLF too)
and add `#define MOVE_EFFECT_FROSTBITE_HIT 277` to
`include/constants/move_effects.h`. Then give it to moves in
`files/poketool/waza/battle_moves.json`:

```json
    "MOVE_ICE_BEAM": {
        "effect": "MOVE_EFFECT_FROSTBITE_HIT",
```

`secondaryEffectChance` is the chance (Ice Beam keeps 10%;
[moves.md](moves.md#move-data-battle_movesjson)). For a status move that always
frostbites (like Will-O-Wisp), use `SIDE_EFFECT_FLAGS_DIRECT` instead and leave out
`CalcCrit`/`CalcDamage`; `effect_script_0167.s` (`MOVE_EFFECT_STATUS_BURN`) is the
model.

The trainer AI judges moves by effect. It doesn't know effect 277, so it uses
Ice Beam only for its damage.

## 4. End-of-turn damage

At the end of each turn, `BattleControllerPlayer_UpdateMonCondition`
(`src/battle/battle_controller_player.c`) goes through the states of
`UpdateMonConditionState` (line 1140) for each battler: Ingrain, Aqua Ring, ...,
poison, bad poison, burn, Nightmare, ... The order of the states is the order of the
effects. Add a state after burn:

```c
    UMC_STATE_BURN,
    UMC_STATE_FROSTBITE,
    UMC_STATE_NIGHTMARE,
```

and its case after `case UMC_STATE_BURN:` (line 1292), copied from burn:

```c
        case UMC_STATE_FROSTBITE:
            if ((ctx->battleMons[battlerId].status & STATUS_FROSTBITE) && ctx->battleMons[battlerId].hp != 0) {
                ctx->battlerIdTemp = battlerId;
                ReadBattleScriptFromNarc(ctx, NARC_a_0_0_1, BATTLE_SUBSCRIPT_FROSTBITE_DAMAGE);
                ctx->commandNext = ctx->command;
                ctx->command = CONTROLLER_COMMAND_RUN_SCRIPT;
                flag = 1;
            }
            ctx->stateUpdateMonCondition++;
            break;
```

The damage itself is `subscript_0298_FrostbiteDamage.s`, a copy of
`subscript_0026_BurnDamage.s` that divides by 16 and has no Heatproof check:

```
_000:
    CheckAbility CHECK_OPCODE_HAVE, BATTLER_CATEGORY_MSG_TEMP, ABILITY_MAGIC_GUARD, _041
    UpdateMonDataFromVar OPCODE_GET, BATTLER_CATEGORY_MSG_TEMP, BMON_DATA_MAXHP, BSCRIPT_VAR_HP_CALC
    DivideVarByValue BSCRIPT_VAR_HP_CALC, 16
    UpdateVar OPCODE_MUL, BSCRIPT_VAR_HP_CALC, -1
    // {0} is hurt by its frostbite!
    PrintMessage msg_0197_01279, TAG_NICKNAME, BATTLER_CATEGORY_MSG_TEMP
    Wait 
    WaitButtonABTime 30
    PlayBattleAnimation BATTLER_CATEGORY_MSG_TEMP, BATTLE_ANIMATION_FROZEN
    Wait 
    UpdateVar OPCODE_FLAG_ON, BSCRIPT_VAR_BATTLE_STATUS, BATTLE_STATUS_NO_BLINK
    GoToSubscript BATTLE_SUBSCRIPT_UPDATE_HP

_041:
    End 
```

Add `'subscript_0298_FrostbiteDamage.s',` after the first one in `meson.build`, and
`#define BATTLE_SUBSCRIPT_FROSTBITE_DAMAGE 298` after `BATTLE_SUBSCRIPT_FROSTBITE`.
`DivideVarByValue` never gives less than 1 for a positive number, as with burn.

The state number isn't saved and nothing compares it, so a new state can go
anywhere in the list.

## 5. What it does in battle: special damage

Burn halves physical damage in `CalcMoveDamage` (`src/battle/battle_util.c:5864`),
after the attack / defense division. Frostbite does the same for special moves, in
the `CATEGORY_SPECIAL` branch, before the Light Screen check (line 5902):

```c
        dmg /= dmg2;
        dmg /= 50;

        if (calcAttacker.status & STATUS_FROSTBITE) {
            dmg /= 2;
        }

        if ((sideCondition & SIDE_CONDITION_LIGHT_SCREEN) && crit == 1 && ...
```

The same function is used for confusion self-hits
(`battle_controller_player.c:2003`) and the AI's damage estimates
(`trainer_ai.c:2923`), so both see the halving. Burn skips the halving for Guts.
For a status that changes something else, other places to change:

| Effect | Where |
|---|---|
| a stat (like paralysis's speed) | `CheckSortSpeed`, `battle_util.c:966` (paralysis at lines 1061 and 1120) |
| losing turns (sleep, freeze, full paralysis) | `BattleControllerPlayer_CheckAttackerStatus`, `battle_controller_player.c:2106` (freeze at lines 2158 and 2342); thawing when hit by a Fire move is in `BattleControllerPlayer_AfterMoveEffects` (line 3117) |
| a counter in the bits (sleep turns, Toxic's count) | use more than one bit and mask it, as `STATUS_SLEEP` does |

## 6. Icons

Two separate icon sets show status.

### Party, summary, battle party menu

`Pokemon_GetStatusIconId` (`src/pokemon_summary.c:2173`) picks an icon from the
status bits: 1 PAR, 2 FRZ, 3 SLP, 4 PSN, 5 BRN, 6 FNT, 7 none
(`PartyMonStatusIconId`, `include/party_menu.h:219`). The party menu, the summary
screen, item use in the party menu, the battle party menu and the link battle screen
all use it. Each icon is an animation in archive `a/0/3/9` (members 62-65:
animation, cells, tiles, palette; `StatusIcon_Get*Naix`, line 2157).

That archive is still a prebuilt binary, so there is no PNG to draw on. The quick
way is to **show the freeze icon**:

```c
    if (status & 0x40) { // paralysis
        return 1;
    }
    if (status & MON_STATUS_FRB_MASK) { // frostbite: the freeze icon
        return 2;
    }
    return 7;
```

Without this, a frostbitten Pokémon would show no icon (7), as if it were healthy.

**Your own icon** means converting `a/0/3/9` to sources first
([graphics-sources.md](graphics-sources.md#8-converting-another-archive); the
appendix lists it as convertible). Then:

1. Add three 8×8 tiles to member 64 (the tiles; each icon is 24×8, three tiles).
2. Add a cell to member 63 that places them like the others (a 16×8 piece and an
   8×8 piece).
3. Add an animation to member 62 that shows that cell. The animation number is the
   icon id.
4. Give the icon a number. 7 is "none" and is written as a bare `7` in
   `pokemon_summary.c:1359` and `:2458` and `battle_party_menu.c:2408`. Either make
   frostbite 8 (and put a dummy animation at 7) or make it 7 and move "none" to 8 in
   all four places.

The palette (member 65) has no unused colors. Each icon has its own three shades.
Reuse FRZ's colors or change one that only one icon uses.

### The battle HP bar

The HP bar draws its icon from the `CONDITION_*` number with a switch
(`src/battle/battle_hp_bar.c:557`). Each case copies three tiles from
`gBattleHpBar_RawGraphicComponents` in `src/battle/battle_hp_bar_data.h`: tiles 38
(blank), 41 PAR, 44 FRZ, 47 SLP, 50 PSN, 53 BRN. A missing case falls to
`default` and draws a blank. To reuse FRZ's tiles:

```c
        case 5:
            BattleHpBar_DrawStatusIcon(hpBar, 41);
            break;
        case CONDITION_FROSTBITE:
            BattleHpBar_DrawStatusIcon(hpBar, 44);
            break;
```

**Your own HP bar icon.** The tiles are a C array (78 tiles, 0x00-0x4D, each with a
`// 0xNN` comment), not a PNG. Append three tiles after 0x4D, so they become 78-80,
and draw component 78. Appending keeps every other tile's number. The colors are the
HP box palette, `graphics/battle_sprites/hp_boxes/palette.pal`. It also has no free
colors, so reuse FRZ's.

This script turns three tiles into a 24×8 PNG to draw on and prints a PNG back as
C bytes. Run it from the repository root. It needs Pillow:

```python
# hpicon.py: python3 hpicon.py dump 44 frz.png | pack frb.png
import re, sys
from PIL import Image

DATA = "src/battle/battle_hp_bar_data.h"
PAL = "graphics/battle_sprites/hp_boxes/palette.pal"

def tiles():
    text = open(DATA).read().split("{", 1)[1]
    return [bytes(int(b, 16) for b in re.findall(r"0x([0-9A-Fa-f]{2})", row))
            for row in re.split(r"// 0x[0-9a-f]+\n", text)[1:]]

def dump(first, dst):
    img = Image.new("P", (24, 8))
    rgb = [int(v) for line in open(PAL).read().split("\n")[3:19] for v in line.split()]
    img.putpalette(rgb)
    for t, tile in enumerate(tiles()[first:first + 3]):
        for i, byte in enumerate(tile):  # 4 bytes per row, left pixel in the low nibble
            x, y = t * 8 + (i % 4) * 2, i // 4
            img.putpixel((x, y), byte & 0xF)
            img.putpixel((x + 1, y), byte >> 4)
    img.save(dst)

def pack(src):
    img = Image.open(src)
    assert img.mode == "P" and img.size == (24, 8), "needs a 24x8 indexed PNG"
    for t in range(3):
        out = [img.getpixel((t * 8 + x, y)) | img.getpixel((t * 8 + x + 1, y)) << 4
               for y in range(8) for x in range(0, 8, 2)]
        print("    " + " ".join("0x%02X," % b for b in out))

{"dump": lambda: dump(int(sys.argv[2]), sys.argv[3]), "pack": lambda: pack(sys.argv[2])}[sys.argv[1]]()
```

`dump 44` gives the FRZ icon. Redraw the letters with the same color indexes, then
`pack` prints three rows. Paste them after 0x4D with `// 0x4e`, `// 0x4f` and
`// 0x50` comments. Dumping FRZ and packing it again gives the original bytes.

## 7. Curing it

The items that cure a status are flagged in `data/items/items.json`
(`"partyUseParam"`: `slp_heal`, `psn_heal`, `brn_heal`, `frz_heal`, `prz_heal`,
`cfs_heal`). There is no spare flag. `ItemPartyParam` (`include/item.h:22`) fills
its first byte with those six plus two more, and the party menu treats "all six" as
Full Heal (`case 63`, `src/party_menu_items.c:125`). So this guide makes **`frz_heal`
cure frostbite too**, as Legends: Arceus does. That covers Ice Heal, Aspear Berry,
Full Heal, Full Restore and Lum Berry with no data change. Add `STATUS_FROSTBITE`
(or `MON_STATUS_FRB_MASK`) wherever a freeze cure is checked:

| Where | Line | Change |
|---|---|---|
| out of battle: can the item be used | `src/use_item_on_mon.c:51` | `(status & (MON_STATUS_FRZ_MASK \| MON_STATUS_FRB_MASK))` |
| out of battle: cure | `src/use_item_on_mon.c:266` | `sp58 &= ~(MON_STATUS_FRZ_MASK \| MON_STATUS_FRB_MASK);` |
| bag item in battle | `BattleSystem_RecoverStatus`, `src/battle/battle_system.c:404` | the `STATUS_FREEZE` test and both `&= ~STATUS_FREEZE` |
| trainer uses an item | `TrainerAI_ShouldUseItem`, `src/battle/trainer_ai.c:3963` | `status & (STATUS_FREEZE \| STATUS_FROSTBITE)` |
| held Aspear / Lum Berry | `TryUseHeldItem` `battle_util.c:3901`, `:3943`; `CheckUseHeldItem` `:4232`, `:4274` | same |
| Pluck / Bug Bite eats it | `TryEatOpponentBerry` `:4704`, `:4752` | same |
| Fling throws it | `TryFling` `:4948`, `:4994` | same |

All eight `battle_util.c` lines are an `if (... status & STATUS_FREEZE) {` followed by
a `HELD_ITEM_FRZ_RESTORE` script or `flingScript = 203`. Don't change the other
`STATUS_FREEZE` lines in that file: Magma Armor, Flash Fire and the freeze status
itself.

The messages say what the item normally cures. Ice Heal on a frostbitten Pokémon
prints "… was thawed out." in the party menu and in battle, and Aspear Berry
"defrosted it". Changing that means a message case for each of them
(`PartyMenu_GetItemUseMessage`, `party_menu_items.c:219`; the bag message in
`battle_controller_opponent.c:5131`; `subscript_0203_HeldItemThawOut.s`).

A cure item of its own (a "Frost Heal") needs a seventh flag in `ItemPartyParam`. You
would move fields into the two padding bytes at its end and update
`files/itemtool/itemdata/item_data.txt`, `PARTY` in `tools/pokedata/items.py` and the
`case 63` test. [items.md](items.md) covers the item data.

**Abilities that cure any status** print the status name from step 2. Shed Skin
(`battle_util.c:3082`) and Hydration (`battle_command.c:3438`) pick the name with a
chain that ends in `else { msgTemp = 4; }`, "frozen". Add a case before it in both:

```c
            } else if (ctx->battleMons[battlerId].status & STATUS_PARALYSIS) {
                ctx->msgTemp = 3;
            } else if (ctx->battleMons[battlerId].status & STATUS_FROSTBITE) {
                ctx->msgTemp = 7;
            } else {
```

**What cures it with no change:**

- the Pokémon Center, whiting out, Heal Bell and Aromatherapy (`battle_command.c:3049`),
  Rest and Natural Cure, which clear the whole status;
- Lum Berry and Full Heal, through `STATUS_ALL` and `frz_heal`;
- depositing in the PC.

## 8. The places that would miss it

**Following Pokémon.** `FollowMonSituation_SetMonCondition`
(`src/field/follow_mon_interaction.c:502`, the status part at 534-550) sorts the lead Pokémon's status for
its lines and hits `GF_ASSERT(FALSE)` (line 548) for a status it doesn't know. Treat
frostbite as freeze:

```c
    } else if (status & (MON_STATUS_FRZ_MASK | MON_STATUS_FRB_MASK)) {
        situation->status = FOLLOW_MON_STATUS_FREEZE;
```

**Quick Feet and Hydration** test only the low byte (see
[How status is stored](#how-status-is-stored)). Use `STATUS_ALL` instead:

- `battle_util.c:1059`: `ctx->battleMons[battlerId1].status & STATUS_ALL`
- `battle_util.c:1118`: `ctx->battleMons[battlerId2].status & STATUS_ALL`
- `battle_command.c:3438`: `(ctx->battleMons[battlerId].status & STATUS_ALL) && GetBattlerAbility(...) == ABILITY_HYDRATION`

Guts and Marvel Scale (`battle_util.c:5708`, `:5712`) test the whole status, so they
already work.

**Psycho Shift** (`subscript_0118_PsychoShift.s`) passes the user's status to the
target with a chain whose last case is "badly poisoned". A frostbitten user would
badly poison the target. Add a case before it (line 25):

```
_039:
    CompareMonDataToValue OPCODE_FLAG_NOT, BATTLER_CATEGORY_ATTACKER, BMON_DATA_STATUS, STATUS_FROSTBITE, _badly_poison
    Call BATTLE_SUBSCRIPT_FROSTBITE
    GoTo _041

_badly_poison:
    Call BATTLE_SUBSCRIPT_BADLY_POISON
```

## 9. Optional

**Catch rate.** `BattleSystem_CalculateBallShakes`
(`src/battle/battle_command.c:7309`) multiplies by 2 for sleep and freeze and by 1.5
for the others. With nothing changed frostbite gives no bonus. Legends: Arceus gives
1.5:

```c
    if ((STATUS_BURN | STATUS_PARALYSIS | STATUS_BAD_POISON | STATUS_POISON | STATUS_FROSTBITE) & status) {
```

**Synchronize.** `TrySyncronizeStatus` (`battle_util.c:3790`) passes poison, burn
and paralysis back to the attacker. To include frostbite, add a branch after
paralysis (`script = BATTLE_SUBSCRIPT_FROSTBITE;`), and keep the burn subscript's
four Synchronize lines (`_190` to `_207`) in yours.

**Facade and Refresh** both use `STATUS_FACADE_BOOST` (`include/constants/battle.h:312`):
Facade doubles its power (`effect_script_0169.s`) and Refresh cures
(`subscript_0145_CurePoisonParalysisBurn.s`). Adding frostbite there does both.

**Other lists** of statuses, checked:

| Feature | Where | With frostbite |
|---|---|---|
| Gracidea (Shaymin's Sky Forme) | `Mon_CanUseGracidea`, `src/pokemon.c:3561` | allowed; only freeze blocks it |
| Shaymin reverting in battle | `subscript_0293_CheckShayminForm.s` | doesn't revert; only freeze does |
| Battle Arcade | `src/frontier/battle_arcade_data.c` | its events give only the five retail statuses; it counts frostbite as "has a status" |
| Roamers | `include/roamer.h:31` | lost between battles (u8) |
| Trainer AI scripts | `asm/trainer_ai_data.s` (raw bytes, [trainers.md](trainers.md#the-ai-scripts)) | the status checks in them use fixed bits; not checked for frostbite |

## Checklist

- [ ] `STATUS_FROSTBITE (1 << 12)` and in `STATUS_ALL`; `CONDITION_FROSTBITE 6`;
      `MON_STATUS_FRB_MASK`
- [ ] the frostbite case in `Battler_GetStatusCondition`
- [ ] nine messages (`msg_0197_01276`-`01284`) and `msg_0044_00007`
- [ ] `subscript_0297_Frostbite.s`, `subscript_0298_FrostbiteDamage.s` in
      `meson.build`; `BATTLE_SUBSCRIPT_FROSTBITE`, `_DAMAGE`
- [ ] `MOVE_SUBSCRIPT_PTR_FROSTBITE 145`; `sMoveStatusChangeScripts[146]`
- [ ] `effect_script_0277.s` in `meson.build`; `MOVE_EFFECT_FROSTBITE_HIT`; the
      effect on moves in `battle_moves.json`
- [ ] `UMC_STATE_FROSTBITE` and its case
- [ ] special damage halved in `CalcMoveDamage`
- [ ] icon in `Pokemon_GetStatusIconId` and the HP bar switch
- [ ] freeze cures cure frostbite (`use_item_on_mon.c` ×2, `battle_system.c`,
      `trainer_ai.c`, `battle_util.c` ×8); Shed Skin and Hydration names
- [ ] following Pokémon, Quick Feet ×2, Hydration, Psycho Shift
- [ ] optional: catch rate, Synchronize, `STATUS_FACADE_BOOST`
- [ ] `make release`

## Not verified

- Steps 1-9 were applied together, with Ice Beam given the new effect, and built
  into a HeartGold ROM with `make release`. The changes were then reverted, and all
  four checksums matched afterwards. Nothing was tried in game: not the messages,
  the damage, the icons, the curing, or the order of the end-of-turn effects. The
  Facade/Refresh change was not built.
- The `hpicon.py` script was checked by dumping FRZ (tiles 44-46) and packing it
  back to the same bytes. No new icon was drawn.
- Converting `a/0/3/9` for a new party icon was not tried.
- The Legends: Arceus details (1/16 damage, half special damage, Ice immunity, Ice
  Heal cures it, 1.5× catch rate) are from memory of that game, not from its code.
