<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Move animations

> AI-generated; not affiliated with pret. See AI.md at the repository root.

What plays when a Pokémon uses a move, and the status, weather and item effects that
play the same way. Every animation is a small script of 32-bit words; the game reads
them from two archives, `a/0/1/0` for moves and `a/0/6/1` for the others. Here the
scripts are text, one file per script, in
[`data/battle_anims/moves/`](../../data/battle_anims/moves/) and
[`data/battle_anims/effects/`](../../data/battle_anims/effects/), and the build makes
the two archives from them with
[`tools/battleanim/battleanim.py`](../../tools/battleanim/battleanim.py)
(`files/a/0/1/meson.build`, `files/a/0/6/meson.build`). Unchanged, they build the
retail archives byte for byte.

| pokeemerald | here |
|---|---|
| `data/battle_anim_scripts.s`, macros in `asm/macros/battle_anim_script.inc` | `data/battle_anims/moves/NNNN_<MOVE>.anim`, one file per move, one command per line; built into `a/0/1/0` |
| `gBattleAnims_Moves[]` (a pointer per move) | the member number **is** the move id (`BattleAnimSystem_StartMove`, `src/battle/battle_anim_system.c:656`) |
| `gBattleAnims_General` / `_Special` / `_StatusConditions` | `data/battle_anims/effects/` → `a/0/6/1`, member = `BATTLE_ANIMATION_*` (`include/constants/battle_subscript.h:449`) |
| `createvisualtask` + `gTasks` functions | `CallFunc` + `gBattleAnimFuncTable` (`asm/battle_anim_data.s:756`, 84 functions) |
| `createsprite` + `gBattleAnimSpriteTemplate_*` | particles: `LoadParticleSystem` + `CreateEmitter` (Nintendo's SPL particle files in `files/a/0/2/9`); 2D sprites: `InitSpriteManager` … `CreateSpriteWithFunc` (rare, 33 scripts) |
| `loadspritegfx ANIM_TAG_*` | the particle file id or the sprite resource ids, given in the script |
| `fadetobg BG_*` | `SwitchBackground id, ...` / `RestoreBackground`; ids in [graphics-sources.md §5](graphics-sources.md#5-graphicsbattle_backgrounds-a007) |
| `playsewithpan SE_*, SOUND_PAN_ATTACKER` | `PlaySEWithPan SEQ_SE_*, -117` (pan as a number, see [Sound](#sound)) |

## 1. When an animation plays

A battle script plays the current move's animation with `PlayMoveAnimation`
(`BtlCmd_PlayMoveAnimation`, `src/battle/battle_command.c:882`), or another move's with
`PlayMoveAnimationOnMons`; the effect animations with `PlayBattleAnimation battler,
BATTLE_ANIMATION_*`. With **Battle Scene off** in the options nothing plays, except
Transform's move animation (it changes the sprite) and the Substitute effects
(`BATTLE_ANIMATION_SUB_OUT`, `SUB_IN`, `SUBSTITUTE_IN`, `SUBSTITUTE_OUT`;
`battle_command.c:2267`). The controller copies what the script may want to
know into a `MoveAnimData` (`BattleController_SetMoveAnimation`,
`src/battle/battle_controller.c:1215`): attacker, defender, damage, power, the
attacker's friendship, the weather (zero under Cloud Nine / Air Lock), the battle
terrain, and a **variant** number. `OpponentData_StartMoveAnimation`
(`src/battle/battle_controller_opponent.c:6906`) picks the archive, and
`BattleAnimSystem_StartMove` loads the member:

- **Secret Power** plays another move's animation by battle terrain
  (`sSecretPowerTerrainAnims`, `battle_anim_system.c:369`).
- Move 0, or a move above `NUM_MOVES`, plays **Pound**'s (`:720`). The same check runs
  for the effect archive, so effect animation 0 can't play (it becomes member 1).
- The **variant** is the battle script variable `BSCRIPT_VAR_MOVE_EFFECT_CHANCE` (58),
  which is really `ctx->moveAnimVariant` (`battle_command.c:5912`), reset to 0 for
  every move (`battle_util.c:1705`). Scripts set it to 1 for the second half of a
  move: the attack turn of charge moves (`subscript_0259_ChargeMoveCleanup.s`), Future
  Sight's hit, Bide's release, Snatch... The animation reads it with
  `JumpByVariantBit0` / `JumpIfVariantEqual`.

`BattleAnimSystem_ExecuteCommands` (`:560`) then runs commands until one asks to wait
(`Wait`, `WaitForTasks`, `WaitForParticles`...), and continues on the next frame. Most
effects run as tasks in the background, so a script usually starts several things,
waits, and cleans up. `End` itself waits until every particle, task and sound effect
is done (a sound effect for 90 frames at most), then frees everything.

## 2. The file format

A member is a list of little-endian u32 words: an opcode, then its arguments. The
opcode indexes `sBattleAnimScriptCmdTable` (`battle_anim_system.c:399`, 88 entries).
There is no header and no length; a script stops at `End`.

- **Jumps** are relative, in words, from the word that holds the offset:
  `Jump +3` at word 10 goes to word 11 + 3 = 14. `JumpBySide` and friends hold
  several offsets, each relative to its own word.
- **`CallFunc f, a, b, c`** is stored as `45, f, 3, a, b, c`: the count comes first.
  The function reads its arguments from `args[0..9]`; the rest are zeroed.
  `CreateSpriteWithFunc` ends the same way.
- **`EmitterData`** (opcode 55) is not a command. Some emitter callbacks read their
  settings from the words that follow the `CreateEmitter`, as blocks of
  `55, count, values...` (`BattleAnimSystem_ReadScriptArgs`, `:3231`). Running opcode
  55 asserts.
- `Wait` and `BeginLoop` keep only the low 8 bits (`delay` and `count` are `u8`).

`a/0/1/0` has 501 members: 0 to 467 are the moves, 468 to 500 are spares that
play a sound and wait 60 frames. The biggest script is 7936 bytes.
`a/0/6/1` has 50; the names are the `BATTLE_ANIMATION_*` constants (23, 24 and
41-49 have none).

## 3. Reading and editing them

Edit the file and run `make`:

```
data/battle_anims/moves/0000_NONE.anim ... 0467_SHADOW_FORCE.anim, 0468_468.anim ... 0500_500.anim
data/battle_anims/effects/0000_NONE.anim, 0001_ASLEEP.anim ... 0049_49.anim
```

The member number is the number at the start of the file name; the rest of the name
is free, and the numbers must run from 0 without a gap (the build stops with an error
naming the missing ones). The build reads every `NNNN_*.anim` in the folder, so adding,
renaming or deleting a file needs no change to `meson.build`. An error in a script
stops the build with the file and line: `0052_EMBER.anim:21: unknown command Frobnicate`.

Unchanged, the folders build the retail archives; `make` checks that, as for
everything else, and so does `python3 tools/battleanim/test_battleanim.py` (both fail
once you change a script). The tool also works on any archive:

```bash
A=tools/battleanim/battleanim.py
python3 $A dis build/heartgold.us/files/a/0/1/0 52       # one script from a built archive
python3 $A export SOME_ARCHIVE DIR [--effects]           # an archive as NNNN_*.anim files
python3 $A build DIR OUT                                 # what the build runs
python3 $A check SOME_ARCHIVE                            # disassemble + assemble, compare
```

Ember (`data/battle_anims/moves/0052_EMBER.anim`):

```
# member 52: EMBER
    InitBattlerSpriteManager
    LoadBattlerSpriteResources 0
    LoadBattlerSpriteResources 1
    LoadBattlerSpriteResources 2
    LoadBattlerSpriteResources 3
    CreateBattlerSprite 4, 0, 0, 0
    CreateBattlerSprite 5, 0, 1, 1
    CreateBattlerSprite 6, 0, 2, 2
    CreateBattlerSprite 7, 0, 3, 3
    CallFunc AnimateSprites, 0
    LoadParticleSystem 0, 83
    WaitForTasks
    FreeBattlerSpriteManager
    DeleteBattlerSprite 0
    DeleteBattlerSprite 1
    DeleteBattlerSprite 2
    DeleteBattlerSprite 3
    CreateEmitter 0, 0, ConfigureFromScript
    EmitterData 0, 2, 2, 0, 0, 0
    CallFunc BattlerPaletteFade, 8, 0, 1, 31, 10, 0
    CallFunc ShakeTargets, 1, 0, 1, 2, 264
    RepeatSE SEQ_SE_DP_W052, 117, 3, 4
    WaitForParticles
    FreeParticleSystem 0
    End
```

- The first ten lines are in 406 of the 501 move scripts: sprite copies of the four
  battlers, drawn for 3 frames (`AnimateSprites` with 0), then removed. Keep them when
  you write a new script.
- `LoadParticleSystem 0, 83` loads particle file 83 of `files/a/0/2/9` into slot 0;
  `CreateEmitter 0, 0, ConfigureFromScript` starts emitter 0 of that file, placed by
  the `EmitterData` below it.
- The defender (`8`) flashes red (`31`), the defender shakes (`264` = defender's
  picture), and the burn sound plays 4 times, 3 frames apart, on the defender's side.

Syntax: one command per line, arguments separated by commas; `;` or `#` starts a
comment; `name:` defines a label (the files call them `L<word>`, the position in
words; rename them as you like); `.word 1, 2, 3` writes raw words. Numbers can be decimal, `0x` hex or negative.
Names are accepted where the files use them: `SEQ_SE_*` for sound effects, the
functions of `gBattleAnimFuncTable` (`CallFunc`), of `gBattleAnimSpriteFuncTable`
(`CreateSpriteWithFunc`) and of `gBattleAnimEmitterCallbackTable` (the last argument
of the `CreateEmitter` commands), without their `BattleAnimFunc_` /
`BattleAnimSpriteFunc_` / `BattleAnimEmitterCb_` prefix. The tool reads those three
tables from `asm/battle_anim_data.s`, so functions you add there get names too.

The `# member 52: EMBER` line at the top is a comment.

## 4. The commands

Names are those of the C functions (`BattleAnimScriptCmd_<name>`). "Role" and "flags"
are explained after the table.

| Op | Command | Arguments | What it does |
|---|---|---|---|
| **Flow** | | | |
| 0 | `Wait` | frames | wait (0-255) |
| 2, 3 | `BeginLoop` / `EndLoop` | count | repeat the commands between them; 3 levels at most |
| 4 | `End` | | wait for particles, tasks and sounds, free everything, stop |
| 10, 11 | `Call` / `Return` | label | subroutine; 3 levels at most (used once) |
| 15 | `Jump` | label | |
| 13 | `JumpByVariantBit0` | label0, label1 | by bit 0 of the variant |
| 14 | `JumpIfVariantEqual` | value, label | |
| 64 | `JumpBySide` | 0 attacker / 1 defender, labelPlayer, labelEnemy | by the side of that battler |
| 70 | `JumpByWeather` | none, rain, sand, sun, hail | five labels (Weather Ball) |
| 71, 72, 87 | `JumpIfContest` / `JumpIfSameSide` / `JumpIfAttackerActive` | label | never in a contest here; same side = attacker and defender are allies |
| 12, 67 | `SetArg` / `ClearArgs` | index, value | set `args[index]` for the background commands (`CallFunc` overwrites them) |
| **Waiting** | | | |
| 1 | `WaitForTasks` | | until every `CallFunc` effect is done |
| 50 | `WaitForParticles` | | until every emitter is done |
| 29 | `WaitForSoundTasks` | | until the sound tasks are done and no sound effect plays (no time limit, unlike `End`) |
| 19, 20 | `WaitForBackgroundLoaded` / `WaitForBackgroundSwitch` | | after `SwitchBackground` |
| 84 | `WaitForButtonCombo` | | until L+R+X (a debug leftover, in one script) |
| **Sound** | | | |
| 5 | `PlaySE` | se | |
| 22 | `PlaySEWithPan` | se, pan | the usual one |
| 23 | `SetSEPan` | pan | all playing sound effects |
| 24 | `PanSweepSE` | se, from, to, step, interval | pan moves every `interval` frames |
| 35, 36 | `PanSweepSERaw` / `PanSweepSEConverted` | the same | no side flip / step flipped too |
| 25 | `RepeatSE` | se, pan, interval, count | |
| 26 | `DelayedSE` | se, pan, delay | |
| 44 | `StopSE` | se | |
| 65, 66 | `PlayCry` / `WaitForCry` | mode, pan, param / param | the attacker's cry (Chatot's recorded one too) |
| **Particles** | | | |
| 51 | `LoadParticleSystem` | slot 0-15, file | particle file from `files/a/0/2/9`; the slot must be free |
| 52 | `LoadParticleSystemEx` | slot, unused, file | from `files/a/0/9/6` (unused) |
| 46 | `CreateEmitter` | slot, emitter, callback | start emitter number `emitter` of the slot's file |
| 47 | `CreateEmitterInSlot` | slot, emitterSlot, emitter, callback | the same, kept in `emitters[emitterSlot]` for functions that move it (`MoveEmitter`...) |
| 48, 49 | `CreateEmitterByPosition6` / `4` | slot, 6 or 4 emitters, callback | the emitter chosen by the attacker/defender positions (doubles) |
| 55 | `EmitterData` | values... | settings for the callback, see [§5](#5-particles) |
| 53 | `FreeParticleSystem` | slot | |
| 62, 63 | `SetParticlePerspective` / `SetParticleFlipY` | slot, value | before `CreateEmitter` |
| **Battler copies** | | | |
| 56, 59 | `InitBattlerSpriteManager` / `FreeBattlerSpriteManager` | | |
| 57 | `LoadBattlerSpriteResources` | index | |
| 58 | `CreateBattlerSprite` | role, follow, slot 0-4, index | an OBJ copy of a battler's picture; follow 1 keeps it on the battler |
| 60, 61 | `DeleteBattlerSprite` / `StopFollowTask` | slot | |
| 81 | `SetBattlerSpriteVisible` | slot, 0/1 | |
| 82, 83 | `StartBattlerSpriteDraw` / `StopBattlerSpriteDraw` | role, drawIndex, slot / drawIndex | draw it in front of or behind the other battlers (doubles) |
| 31, 32 | `CopyBattlerToBg` / `ClearBattlerBg` | role, follow / unused | a battler's picture on BG2 |
| 68, 69 | `ChangeBattlerPic` / `RestoreBattlerPic` | 0-3 | the attacker's picture becomes the defender's (0), the Substitute doll (2) or itself facing the other way (3); and back |
| **Sprites** (`files/a/0/2/2`-`5`) | | | |
| 73 | `InitSpriteManager` | manager 0-3, maxSprites, 6 capacities | |
| 74-77 | `LoadCharResource` / `LoadPaletteResource` / `LoadCellResource` / `LoadAnimResource` | manager, member (palette: + count) | member of `a/0/2/2`, `3`, `4`, `5`; its resource id becomes member + 5000 |
| 78 | `CreateSpriteWithFunc` | manager, function, 6 resource ids, args... | sprite on the defender, run by a sprite function |
| 79 | `CreateSprite` | manager, index 0-9, 6 resource ids | for a later `CallFunc` |
| 80 | `FreeSpriteManager` | manager | |
| **Background and screen** | | | |
| 16 | `SwitchBackground` | id, how | a move background on BG3, see [§6](#6-backgrounds) |
| 18 | `RestoreBackground` | id, how | back to the battle background |
| 86 | `SwitchBackgroundWithFadeWait` | id, how, kind \| amount << 16 | with a longer or shorter fade |
| 34 | `SwitchBackgroundBySide` | idPlayer, idEnemy, idContest | by the defender's side |
| 21 | `SetBackground` | id | at once, no fade |
| 17 | `SetBgScroll` | 0 dx / 1 dy / 2 x / 3 x, value | change a running scroll (3 sets x as well) |
| 8 | `SetSubScreenBlend` | eva, evb | touch screen BG0/BG1 blend |
| 85 | `BrightnessFlash` | steps | the top screen to white and back |
| **Effects** | | | |
| 45 | `CallFunc` | function, args... | [§7](#7-callfunc-functions) |

**Unusable opcodes.** 6, 7, 9 (`ResetBlend`), 27, 28, 37-43 and 54 don't move past
their own word, so the game runs them forever. 30 (`JumpIfArgEqual`) and 33 jump to an
absolute address, which a script loaded on the heap can't know. 88 reads past the end
of the table (`BattleAnimSystem_GetScriptCmd`, `:3188`, refuses only opcodes above
0x58 = 88). None of them is in the data; the tool refuses them except as `.word`.

**Roles** (`CreateBattlerSprite`, `CopyBattlerToBg`, `StartBattlerSpriteDraw`;
`BattleAnimSystem_GetBattlerByRole`, `:1553`): 0 attacker, 1 defender, 2 the
attacker's partner, 3 the defender's partner, 4 the player's first Pokémon, 5 the
enemy's first, 6 the player's second, 7 the enemy's second.

**Flags** of most `CallFunc` functions (`include/battle/battle_anim_battler_util.h:36`,
`src/battle/battle_anim_funcs.c:28`): `0x002` attacker, `0x004` attacker's partner,
`0x008` defender, `0x010` defender's partner, `0x020` all but the attacker, `0x040`
all; plus what to move: `0x100` the battlers' pictures, `0x200` sprites, `0x400` the
background. 264 = `0x108` = the defender's picture.

### Sound

Sound effects are `SEQ_SE_*` (`include/constants/sndseq.h`). A **pan** is -128 to 127
and is written for the player's Pokémon attacking: -117 is the attacker's side (left),
117 the defender's (right). `BattleAnimSystem_ConvertPan` (`:3198`) mirrors it when the
enemy attacks, and keeps it on one side when both are on the same side.

## 5. Particles

Most of what you see is particles: `files/a/0/2/9` has 486 SPA files (Nintendo's
SPL particle format, the same as the Poké Ball particles in `files/a/0/9/5`), loaded
with `ParticleSystem_LoadResourceFile` (`BattleAnimSystem_NewParticleSystem`,
`:3484`). The 501 move scripts use 419 of them; 13 are shared by several moves. A file
holds several emitters, numbered from 0; `CreateEmitter slot, emitter, callback`
starts one. **There is no converter for SPA here**, so a new effect reuses an
existing file, or a file made with an outside SPA editor.

The callback (`gBattleAnimEmitterCallbackTable`, `asm/battle_anim_data.s:325`) places
the emitter. The ones the scripts use:

| Callback | Uses | Places it |
|---|---|---|
| `SetPositionAtDefender` | 602 | on the defender |
| `ConfigureFromScript` | 556 | from the `EmitterData` that follows (below) |
| `SetPositionAtAttacker` | 508 | on the attacker |
| `None` | 38 | where the file says |
| `SetPositionAtDefenderSide` / `AtAttackerSide` | 30 / 14 | on that side's first position |
| `SetPositionByBattlerTypes` | 6 | |

`AttackerToDefender`, `ConvergeTo*` and `MagnetTo*` (5-16) are unused; they read eight
`EmitterData 3`-word blocks (an axis per pair of positions, then the start) and, for
`*FromScript`, a 4-word target (`battle_anim_emitter.c:395`).

`ConfigureFromScript` (`battle_anim_emitter.c:1036`) reads one block of 6:
`EmitterData zMode, battlerOrder, positionMode, axisMode, flags, cameraMode`.
`battlerOrder` 0/2 makes battler A the attacker and B the defender, 1/3 the reverse.
`positionMode` 1 is battler A, 2 battler B (6-27 are other heights and offsets on
them, `BattleAnimEmitter_ApplyConfiguredPosition`); 3, 4, 5, 12 and 13 read one more
block of 4 (an offset), 100 and 101 six of them (one per battler position), and most
bits of `flags` a block of 5 (`BattleAnimEmitter_ReadFlagCbParams`). So copy the
`EmitterData` lines together with their `CreateEmitter`.

Effects that move an emitter after it starts are `CallFunc MoveEmitter`,
`MoveEmitterArc`, `MoveEmitterVertical` and `EmitterSinMotion` on an emitter made by
`CreateEmitterInSlot`.

## 6. Backgrounds

`SwitchBackground id, how` shows background `id`, a row of
`sBattleAnimBackgroundFiles` (`:490`; 59 rows, the pictures and which move uses each
are in [graphics-sources.md §5](graphics-sources.md#5-graphicsbattle_backgrounds-a007)).
`how` is `effects << 16 | kind`:

| kind | `SwitchBackground` | `RestoreBackground` |
|---|---|---|
| 0 | blend in over the battle background | blend out |
| 1 | fade the battle background to black (white if `args[4]` is 1), show the new one | fade back |
| 2 | only start/stop the effects | the same |

| effects bit | |
|---|---|
| `0x2` | scroll BG3 by (`args[0]`, `args[1]`) per frame from (`args[2]`, `args[3]`), mirrored when the defender is the player's (`args[6]`) |
| `0x4` | stop the scroll (on restore) |
| `0x20` / `0x40` | a wave on BG3 / stop it |
| `0x80` / `0x100` | cycle the background's palettes / stop it |

So the common pair is `SetArg 0, -32` … `SwitchBackground 36, 0x20001` …
`RestoreBackground 36, 0x40001` (Agility: fade in, scroll left; fade out, stop).
`args[5]` picks the blend strength (1 or 2; kind 0 only). With `args[6]` (the scroll)
or `args[7]` (the picture) not 0, the background is mirrored when the defender is on
the player's side (`BattleAnimBackground_ShouldFlip`). Wait with
`WaitForBackgroundSwitch` before restoring.

## 7. CallFunc functions

`CallFunc name, args...` runs entry `name` of `gBattleAnimFuncTable`
(`asm/battle_anim_data.s:756`; the bound, 0x54, is in `BattleAnimSystem_GetFunc`,
`src/battle/battle_anim_util.c:753`). The code is in `src/battle/battle_anim_funcs.c`
and `battle_anim_move_effects.c`, with a comment on most of them. The common ones:

| Function | Uses | Arguments |
|---|---|---|
| `AnimateSprites` | 477 | frames (0 = 3); the opening of every script |
| `ShakeTargets` | 398 | ampX, ampY, interval, count, flags |
| `FadeBgPalette` | 274 | 0 battle background / 1 BG palette 8 / 2 BG palette 9, wait, from, to (0-16), color |
| `BattlerPaletteFade` | 270 | flag (`8` defender...), framesPer, count, color, strength (0-16), hold |
| `MoveBattlerBy` | 129 | frames, dx, dy, flags (`0x100` + role) |
| `EmitterSinMotion` | 105 | 10 values |
| `SlideBattler2` | 86 | 3 |
| `MoveEmitterArc` | 73 | 6 or 7 |
| `StretchBattler` | 53 | 8 |
| `SetBattlerVanished` | 51 | flags, 1 hide / 0 show |
| `MoveEmitter` | 46 | 6, 8 or 9 |
| `ShakeBg` | 43 | ampX, ampY, interval, count, repeats, 0 BG3 / 1 BG2 |
| `SetBgPaletteGrayscale` | 18 | 1 gray / 0 back |

Colors are 15-bit BGR: 31 red, `0x3E0` green, `0x7C00` blue, `0x7FFF` white. 49
functions are called three times or fewer, usually for the move they are named
after (`AttackerHop` is Splash). Seven are never used: `ShowAttackerObjWindowSprites`,
`ShakeSpritePair`, `ShootSpriteFromAttacker`, `ShakeAndScaleBattlerXY`,
`ChangeBattlerHeight`, `ObjWindowBgScrollUp`, `ObjWindowBgScrollDown`. To learn one,
find a move that uses it:

```bash
grep -l "CallFunc AttackerHop" data/battle_anims/moves/*.anim
```

## 8. Recipes

### 8.1 A new move with an existing animation

Two ways; both use a spare member (468-500) or a new one ([8.3](#83-a-move-past-500)).

- **Copy the script.** In `data/battle_anims/moves/`, delete the spare
  `0468_468.anim` and `cp 0053_FLAMETHROWER.anim 0468_FLAME_BURST.anim`, then `make`.
  The new member can then be changed on its own. Tested: member 468 of the built
  archive equals member 53 and the other 500 are unchanged; the ROM built.
- **Point to it in C.** In `BattleAnimSystem_StartMove`, next to the Secret Power case:
  `if (animId == MOVE_FLAME_BURST) { animId = MOVE_FLAMETHROWER; }`. No archive change.

### 8.2 Change a color, sound or timing

Edit the line and `make`. Ember with a blue flash instead of red
(`0052_EMBER.anim`):

```
    CallFunc BattlerPaletteFade, 8, 0, 1, 0x7C00, 10, 0
```

or with Flamethrower's sound: `RepeatSE SEQ_SE_DP_W053, 117, 3, 4`. A longer pause
is a bigger `Wait`. Change `EmitterData` only together with its `CreateEmitter`.

### 8.3 A move past 500

`NUM_MOVES` above 500 needs a member for each new id: with `NUM_MOVES` at 501 the
game reads member 501, and a missing member fails the read (`GF_ASSERT` in
`src/filesystem.c`), it does not fall back to Pound. Add `0501_<NAME>.anim`
to `data/battle_anims/moves/` (numbers without gaps). Only ids above `NUM_MOVES` play
Pound.

### 8.4 A new effect function

1. Write `void BattleAnimFunc_MyEffect(BattleAnimSystem *system)` in
   `src/battle/battle_anim_funcs.c`, reading its arguments with
   `BattleAnimSystem_GetArg(system, i)`; long effects start a task with
   `BattleAnimSystem_CreateTaskDefaultPriority` and destroy it with
   `BattleAnimSystem_DestroyTask` so `WaitForTasks` waits for them (copy
   `BattleAnimFunc_ShakeBg`).
2. Declare it in `include/battle/battle_anim_funcs.h`; add
   `.word BattleAnimFunc_MyEffect` at the end of `gBattleAnimFuncTable` and
   `.extern` it at the top of `asm/battle_anim_data.s`.
3. Raise the bound in `BattleAnimSystem_GetFunc` (`id >= 0x54`) to 0x55.
4. Use it: `CallFunc MyEffect, ...` (the tool finds the name in the table).

Not tested.

### 8.5 A new command

Add the function to `sBattleAnimScriptCmdTable` as entry 88 (the bound `cmd > 0x58`
already allows 88; raise it for more), read its arguments by advancing
`system->scriptPtr` past the opcode and each argument, and add it to `COMMANDS` in
`battleanim.py` with its argument kinds. Not tested.

## 9. Traps

- A command that doesn't advance `scriptPtr` (the unusable opcodes, or a new one
  written wrong) freezes the battle.
- `LoadParticleSystem` into a used slot asserts; free it first.
- `JumpByWeather` skips the first label whenever any field condition is set, and
  only matches rain, sand, sun or hail; with fog, Gravity, Trick Room or Uproar alone
  it reads the word after the five labels as an offset (`:1453`).
- `Call` and loops nest 3 deep. A fourth level isn't refused: the command skips only
  its opcode, and its argument is then run as a command.
- `CallFunc` clears `args`, so set `SetArg` values right before the background
  command that reads them.
- An effect function that never destroys its task makes `WaitForTasks` and `End`
  wait forever.

## Where to look

| What | File |
|---|---|
| the interpreter and every command | `src/battle/battle_anim_system.c` (table `:399`, start `:656`) |
| the `CallFunc` functions | `src/battle/battle_anim_funcs.c`, `battle_anim_move_effects.c` |
| emitter callbacks | `src/battle/battle_anim_emitter.c` |
| sprite functions | `src/battle/battle_anim_effects.c` |
| function, callback and sprite tables | `asm/battle_anim_data.s:325`, `:721`, `:756` |
| who starts an animation | `src/battle/battle_controller_opponent.c:6906`, `battle_command.c:882` |
| effect animation ids | `include/constants/battle_subscript.h:449` |
| scripts | `data/battle_anims/moves/` (`a/0/1/0`), `data/battle_anims/effects/` (`a/0/6/1`) |
| build rules | `files/a/0/1/meson.build`, `files/a/0/6/meson.build` |
| resources | particles `files/a/0/2/9`, sprites `files/a/0/2/2`-`5`, backgrounds `graphics/battle_backgrounds/move_backgrounds/` |
| the tool | `tools/battleanim/battleanim.py`, test `test_battleanim.py` |

## Not verified

- Both folders build the retail archives (HeartGold and SoulSilver: all 4 checksums
  OK), and every member decodes without unknown opcodes (`test_battleanim.py`).
  Editing a script, adding `0501_*.anim` and deleting it again each rebuilt the
  archive without reconfiguring. Recipe 8.1 (Flamethrower's script copied to member
  468) was built into a HeartGold ROM with `make release` and then reverted. **No animation was watched in game**: not
  the copy, not the blue Ember, not a new function or command.
- The meaning of arguments comes from reading the code. The table in §7 covers the
  common functions; the others are only named. The `EmitterData` fields beyond the
  first six and the `flags` blocks were not traced one by one.
- What the shared opening (`AnimateSprites` on four battler copies) is for was not
  checked on screen.
- That `WaitForButtonCombo` is a debug leftover is a guess from what it does.
