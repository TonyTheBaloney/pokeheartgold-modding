<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27 -->

# Faster battles: text, waits, bars and animations

> AI-generated; not affiliated with pret. See AI.md at the repository root.

What makes a battle slow, where each part is timed, and how to make it faster: battle
text speed, the pause after each message, the HP and EXP bars, and which animations
the **Battle Scene** option skips. Everything here is in C under `src/battle/` or in
the battle scripts under `files/battledata/script/`. The Options menu itself (the
TEXT SPEED and BATTLE SCENE rows, defaults, a new choice) is in
[options-menu.md](options-menu.md); the animation scripts themselves are in
[move-animations.md](move-animations.md).

| pokeemerald | here |
|---|---|
| `GetPlayerTextSpeedDelay` | `Options_GetTextFrameDelay` (`src/options.c:53`); battles go through `BattleSystem_GetTextFrameDelay` (`src/battle/battle_system.c:762`) |
| `waitmessage B_WAIT_TIME_LONG` (64 frames) after battle messages | `WaitButtonABTime 30` after nearly every message (`BtlCmd_WaitButtonABTime`, `src/battle/battle_command.c:1010`) |
| fast HP drain (a common patch; an option in pokeemerald-expansion) | `FAST_HP_BARS`, already in the code, off (`src/battle/battle_hp_bar.c:25`) |
| fast EXP bar (same) | none; loop the step in `Task_ExpBarUpdate` ([4.4](#44-a-faster-exp-bar)) |
| `gSaveBlock2Ptr->optionsBattleSceneOff` | `Options_GetBattleScene`, read through `BattleSystem_AreBattleAnimationsOn` (`src/battle/battle_system.c:751`) |

All times below are in frames: one call of the battle loop or of a task.

## 1. Where the time goes

One use of a move, as the battle scripts run it
(`files/battledata/script/subscript/`):

1. "X used Y!" is printed one character at a time ([section 2](#2-battle-text)), then
   `WaitButtonABTime 30` ([section 3](#3-the-pause-after-each-message)).
2. The move animation plays, if Battle Scene is on ([section 5](#5-what-battle-scene-off-skips)).
3. The target blinks (`FlickerMon` in `subscript_0002_UpdateHp.s`), then the HP bar
   drains ([section 4](#4-hp-and-exp-bars)).
4. "It's super effective!", stat changes, status, abilities, items: each is another
   message with another wait, and stat and status changes play an effect animation.

A wild battle's win adds the EXP bar, and a level-up adds a fanfare and the stat
boxes.

## 2. Battle text

Every battle message is printed by `BattleSystem_PrintBattleMessage`
(`src/battle/battle_system.c:1424`) or `BattleSystem_PrintTrainerMessage` (`:1366`)
with the delay from `BattleSystem_GetTextFrameDelay`:

```c
u8 BattleSystem_GetTextFrameDelay(BattleSystem *battleSystem) {
    if ((battleSystem->battleType & BATTLE_TYPE_LINK) && !(battleSystem->battleSpecial & BATTLE_SPECIAL_RECORDING)) {
        return 1;
    }
    return Options_GetTextFrameDelay(battleSystem->options);
}
```

`Options_GetTextFrameDelay` (`src/options.c:53`) turns SLOW / MID / FAST into 8 / 4 /
1 frames per character. The bag and party screens in battle use the same function
(`battle_bag_menu.c:1068`, `battle_party_menu.c:2754`).

- **1 is the fastest a printer goes**: one character per frame (`RunTextPrinter`,
  `src/text.c:200`, calls `RenderFont` once per frame). FAST is already that speed.
- **Holding A or B** (or touching the screen, outside link battles) also prints one
  character per frame once the first press has been seen
  (`src/render_text.c:87-102`); `BattleSystem_SetupTextFlags`
  (`src/battle/battle_main.c:1645`) turns this on for every battle. So the option only
  matters for players who don't press anything.
- The controller waits for the printer to finish (`Task_WaitBattleMessage`,
  `src/battle/battle_controller_opponent.c:5954`) before the script goes on.

### 2.1 Fast text in battle, whatever the option

```c
u8 BattleSystem_GetTextFrameDelay(BattleSystem *battleSystem) {
    return 1;
}
```

Text outside battle keeps the player's setting. To change every text in the game, edit
`Options_GetTextFrameDelay` instead ([options-menu.md](options-menu.md#text-speeds)).

### 2.2 Faster than one character per frame

There is no setting for it. Two ways, neither built here:

- **Instant (`TEXT_SPEED_INSTANT`, 0)**: `AddTextPrinter` (`src/text.c:171`) draws the
  whole string at once and returns no printer, which `Task_WaitBattleMessage` treats
  as finished. But it never calls the printer callback, and battle messages use it:
  `{WAIT 5}` in "grew to Lv. X!" and "learned Y!" (`msg_0197`) plays the level-up
  fanfare and waits for it (`BattleSystem_TextPrinterCallback`,
  `src/battle/battle_system.c:1938`: 1 waits for a sound effect, 2 for a fanfare, 3
  plays the catch fanfare, 4 a sound, 5 the level-up fanfare). With instant text those
  are silent and don't wait. Messages that wait for a button or scroll aren't written
  for it either.
- **Several characters per frame**: call `RenderFont` more than once in
  `RunTextPrinter` while the printer's delay is 0. That changes every printer in the
  game, so check `printer->textSpeedBottom` (0 only at speed 1) and stop at
  `RENDER_FINISH` and at any `RENDER_UPDATE` that set `callbackParam` or a wait state.

## 3. The pause after each message

Most messages are followed by

```
    PrintMessage ...
    Wait
    WaitButtonABTime 30
```

`Wait` waits until the message has finished printing. `WaitButtonABTime n`
(`src/battle/battle_command.c:1010`) then waits `n` frames, or less if A, B, X or Y
(`0xC03`) or the touch screen is **newly** pressed. In live link battles the counter
goes up by 2, so the wait is half as long, and buttons don't skip it.

In the battle scripts:

| Command | Uses | Where |
|---|---|---|
| `WaitButtonABTime 30` | 397 | after almost every message |
| `WaitButtonABTime 15` | 30 | ability and item messages (Intimidate, Trace, Flash Fire, X items, Potions), disobedience |
| `WaitButtonABTime 60` | 9 | win and loss messages, a trainer's mid-battle message |
| `WaitButtonABTime 7` | 2 | battle start (`subscript_0000_StartEncounter.s`) |
| `WaitTime 96` / `112` / `122` | 10 | battle start: after the trainer slides in, after each send-out; **can't be skipped** |
| `WaitTime 72` | 6 | switching in (switch, replace a fainted Pokémon, Roar/Whirlwind, Healing Wish, Lunar Dance); **can't be skipped** |

`WaitTime` (`battle_command.c:5677`) is the same loop without the button check. The
script interpreter (`RunBattleScript`, `:89`) runs commands until one of them asks for
the next frame; both wait commands do that.

### 3.1 Shorter pauses everywhere

Divide in the command, so the scripts stay as they are:

```c
    int waitFrames = BattleScriptReadWord(ctx) / 2;
```

Do the same in `BtlCmd_WaitTime` if those feel long. `0` is fine: the command ends on
its first frame.

### 3.2 Hold A to skip the pauses

Change `newKeys` to `heldKeys` in `BtlCmd_WaitButtonABTime`:

```c
        if (gSystem.heldKeys & 0xC03 || System_GetTouchNew()) {
```

With A held, text prints at one character per frame (section 2) and each pause ends
at once, so a battle runs as fast as the animations allow. Yes/no prompts, the move
menu and the party screen read their own input and aren't affected.

### 3.3 One message's pause

Edit the number in that script under `files/battledata/script/` (subscripts, and
`effect_script_*.s` for move effects) and run `make`.

### 3.4 Messages while choosing

Messages shown while you pick an action ("There's no running from a Trainer battle!",
a move you can't select, "Items can't be used here.";
`BattleController_EmitSetAlertMessage` in `src/battle/battle_controller_player.c`)
wait a fixed 40 frames after printing (`work->timer == 40` in
`Task_PrintSelectionMessage`, `src/battle/battle_controller_opponent.c:5967`).

## 4. HP and EXP bars

Both bars are stepped once per frame by a controller task:
`Task_HealthbarUpdate` and `Task_ExpBarUpdate`
(`src/battle/battle_controller_opponent.c:5709`, `:5728`). The step is
`BattleHpBar_CalculatePixelsChangeFrame` (`src/battle/battle_hp_bar.c:1193`).

| Bar | Width | Speed in retail |
|---|---|---|
| HP, max HP below 48 | 48 px | one pixel per frame (at most 48 frames) |
| HP, max HP 48 or more | 48 px | **one HP per frame**: 200 damage takes 200 frames |
| EXP | 96 px | one pixel per frame (at most 96 frames per level), the step is `gainedExp / pixels` (`BattleHpBar_StepGauge`, `:1110`) |

### 4.1 Fast HP bars

pret left a switch for this at the top of `src/battle/battle_hp_bar.c`:

```c
#ifdef FAST_HP_BARS
#define USE_SUBPIXELS_TEST (TRUE)
#else
#define USE_SUBPIXELS_TEST (maxHp < pixelsWide)
#endif // FAST_HP_BARS
```

Add `#define FAST_HP_BARS` above it. Every HP bar then moves one pixel per frame, so
no change takes more than 48 frames. The player's HP numbers jump by about
`maxHp / 48` each frame instead of counting down by 1. The EXP bar goes through the
same test; it already moves about one pixel per frame either way.

### 4.2 Even faster, or no drain at all

Step more than once per frame in `Task_HealthbarUpdate`, the way 4.4 does for the EXP
bar. With a count of 48 or more (with `FAST_HP_BARS`) the bar reaches its end value in
one frame. Don't skip the steps by moving `hpBar->script` on: the bar's `hp` is only
updated when a step returns `-1` (`BattleHpBar_UpdateHpChange`, `:708`).

### 4.4 A faster EXP bar

In `Task_ExpBarUpdate`, step 4 times per frame:

```c
    case EXP_BAR_UPDATE_STATE_UPDATE:
        if (hpBar->expSoundTimer < 8) {
            hpBar->expSoundTimer++;
        }
        int expRet;
        for (int i = 0; i < 4; i++) {
            expRet = BattleHpBar_UpdateExpChange(hpBar);
            if (expRet == -1) {
                break;
            }
        }
        if (expRet == -1) {
            if (hpBar->expSoundTimer >= 8) {
```

The rest of the case is unchanged. The EXP sound plays at least 8 frames
(`expSoundTimer`), so a short fill still sounds the same. Each step redraws the
gauge; more than a few per frame only costs time.

## 5. What Battle Scene off skips

`BattleSystem_AreBattleAnimationsOn` (`src/battle/battle_system.c:751`) is TRUE when
the option is ON, and always in live link battles. Where it is read:

| What | Where | With Battle Scene off |
|---|---|---|
| Move animations | `BtlCmd_PlayMoveAnimation`, `BtlCmd_PlayMoveAnimationOnMons` (`battle_command.c:894`, `:923`) | skipped, except Transform (it changes the sprite) |
| Effect animations: status, stat up/down, weather, held items, healing, Leech Seed... (`BATTLE_ANIMATION_*`, `include/constants/battle_subscript.h`) | `BtlCmd_PlayBattleAnimation`, `...OnMons`, `...FromVar` (`battle_command.c:2267`, `:2284`, `:2304`) | skipped, except Substitute in and out (15, 16, 25, 26) |
| Bag items used in battle (Potion, Full Restore, X items, Guard Spec.) | `Task_PlayerSelectItem` (`battle_controller_opponent.c:4897-4939`) | the animation is replaced by a heal sound |
| Pokémon cry animations on send-out | `BattleControllerOpponent_PlayMonAnimAndCry` (`battle_controller_opponent.c:7102`) | the sprite doesn't animate, the cry plays at once |

Not affected: the battle intro (transition, trainer slide, ball throw, send-out),
Poké Ball catches, the target blinking when hit, fainting, the HP and EXP bars, the
level-up stat boxes.

`BtlCmd_PlayBattleAnimationFromVar` compares the **var number**, not its value, with
15 and 16 (`status == 15 || status == 16 || *data == 25 || *data == 26`); it is
`*data` in the other two. With Battle Scene off this only matters for a script that
plays animation 15 or 16 from a var.

### 5.1 Skip only some animations

Add the exception to the condition. For example, keep move animations but never play
stat changes, in `BtlCmd_PlayBattleAnimation` (and the `OnMons` and `FromVar` versions
if you want them everywhere):

```c
    if ((BattleSystem_AreBattleAnimationsOn(battleSystem) == TRUE && status != BATTLE_ANIMATION_STAT_BOOST && status != BATTLE_ANIMATION_STAT_DROP) || status == 15 || status == 16 || status == 25 || status == 26) {
```

The stat message still prints. To shorten one animation instead of skipping it, edit
its script in `data/battle_anims/effects/`
([move-animations.md](move-animations.md#3-reading-and-editing-them)).

### 5.2 Battle Scene off by default, or always

Default: `Options_Init` ([options-menu.md](options-menu.md#defaults)), new games
only. Always (and remove the row's effect): return `FALSE` from
`BattleSystem_AreBattleAnimationsOn` outside link battles. Keep the link check:
link battles assume both sides play the animations.

## 6. Link battles and recordings

Every function above checks `BATTLE_TYPE_LINK` without `BATTLE_SPECIAL_RECORDING`:
live link battles always use text delay 1, always play animations, and can't skip
pauses with a button (but the pauses are half as long). Keep those checks in your
changes: both DSes run the battle together, and two builds with different timings in
a link battle haven't been tried. Battle Video playback uses the player's own
options.

## Not verified

- Recipes 2.1, 3.1, 3.2, 4.1, 4.4 and 5.1 were applied together and built into a
  HeartGold ROM with `make`; it compiled, and the main checksum changed as expected.
  They were reverted and all four checksums matched again. Nothing was played in
  game, so how fast each one feels, and whether the HP numbers look right with
  `FAST_HP_BARS`, wasn't seen.
- 2.2 and 4.2 are read from the code, not built.
- That holding A through a whole battle (3.2) never skips something the player needed
  to see, such as a prompt, wasn't checked beyond the commands named above.
- Link battles between builds with different settings (section 6) weren't tried.
