<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Adding and changing options

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the player's options are saved, how the Options screen builds its rows from tables,
and how to add an option or change one. The worked example adds an **AUTO-RUN: OFF / ON**
row that makes the player run without holding B.

The screen framework (lifecycle, BG layers, windows, sprites, touch) is not repeated here:
[ui.md](ui.md#1-applications) explains it using this same screen,
[src/options_app.c](../../src/options_app.c).

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `gSaveBlock2Ptr->optionsTextSpeed` etc. | `Options`, a 16-bit bitfield in the player data chunk |
| read the field directly | `Options_Get*(Save_PlayerData_GetOptionsAddr(saveData))` |
| `MENUITEM_*`, a `*_ProcessInput` / `*_DrawChoices` pair per row | one enum of rows; per-row **tables** read by shared loops |
| `sOptionMenuItemsNames[]` | consecutive messages in `msg_0045` |
| `SetDefaultOptions` | `Options_Init` |
| `GetPlayerTextSpeedDelay` | `Options_GetTextFrameDelay` |

## 1. Where options are stored

[include/options.h](../../include/options.h#L7):

```c
typedef struct Options {
    u16 textSpeed : 4;
    u16 soundMethod : 2;
    u16 battleStyle : 1;
    u16 battleScene : 1;
    u16 buttonMode : 2;
    u16 frame : 5;
    u16 dummy : 1;
} Options;
```

| Field | Bits | Values | Default |
|---|---|---|---|
| `textSpeed` | 4 | 0 SLOW, 1 MID, 2 FAST | 1 |
| `soundMethod` | 2 | 0 STEREO, 1 MONO | 0 |
| `battleStyle` | 1 | 0 SHIFT, 1 SET | 0 |
| `battleScene` | 1 | 0 ON, 1 OFF | 0 |
| `buttonMode` | 2 | 0 NORMAL, 1 L=A | 0 |
| `frame` | 5 | 0–19 (TYPE 1–20) | 0 |
| `dummy` | 1 | unused | 0 |

[src/options.c](../../src/options.c) has a getter and setter per field
(`Options_GetTextSpeed` / `Options_SetTextSpeed` … `Options_GetFrame` / `Options_SetFrame`)
and two helpers:

- `Options_GetTextFrameDelay`: text speed → frames per character, 0 → 8, 1 → 4, else 1
  ([src/options.c:53](../../src/options.c#L53)).
- `Options_SetButtonModeOnMain(saveData, mode)`: sets `gSystem.buttonMode`, value 1 →
  `BUTTONMODE_LEQUALSA`, else `BUTTONMODE_NORMAL`. A non-NULL `saveData` overrides `mode`
  with the saved value ([src/options.c:29](../../src/options.c#L29)).

### In the save

`Options` is the first member of `PLAYERDATA` ([include/player_data.h](../../include/player_data.h#L27)),
the 44-byte chunk `SAVE_PLAYERDATA` ([save-data.md](save-data.md)).
`Save_PlayerData_GetOptionsAddr` returns a pointer into the live save.

- **New game**: `Save_PlayerData_Init` clears the chunk and calls `Options_Init`
  ([src/options.c:18](../../src/options.c#L18)).
- **Boot**: `InitSoundData` ([src/sound.c:97](../../src/sound.c#L97), from
  [src/main.c:64](../../src/main.c#L64)) applies `soundMethod` with `GF_SndSetMonoFlag`.
- **Continue**: `Options_SetButtonModeOnMain(saveData, 0)`
  ([src/overlay_36.c:158](../../src/overlay_36.c#L158)); from then on
  `ApplyButtonModeToInput` ([src/system.c:331](../../src/system.c#L331)) rewrites the keys
  every frame.
- **Copies**: battles get one (`Options_New` + `Options_Copy` in
  [src/battle/battle_setup.c](../../src/battle/battle_setup.c)), and battle videos store one
  (`BattleRecordData.options`, [include/battle_recording.h:63](../../include/battle_recording.h#L63)).

### Free space

| Space | Size | Notes |
|---|---|---|
| `Options.dummy` | 1 bit | one ON/OFF option; copied into battles and videos with the rest |
| unused values | `textSpeed` 3–15, `soundMethod` 2–3, `buttonMode` 2–3, `frame` 20–31 | more choices for an existing row (§4) |
| `PLAYERDATA` padding after `options` | 2 bytes | `PlayerProfile` contains a `u32`, so it starts at offset 4; a `u16 modOptions;` between `options` and `profile` keeps the chunk at 44 bytes |

[save-compatibility.md](save-compatibility.md#2-two-kinds-of-break): "add fields where padding
was; never reorder". In an old save such space holds "whatever was there, usually 0. Treat 0
as 'not set yet'" ([§4](save-compatibility.md#4-free-space-inside-the-current-layout)), so make
0 the default of a new option.

Don't widen `Options` to `u32`: `PLAYERDATA` would stay 44 bytes, but `BattleRecordData`
has `Options options;` followed by `u16 magic, crc;`, so the battle video layout would move
under saved videos. A `modOptions` field avoids that, but battles and videos don't get it.

### Who reads each option

| Option | Read by |
|---|---|
| text speed | `Options_GetTextFrameDelay`, about 50 call sites: dialogue (`DialogBox_PrintMessage` in [src/dialog_box.c](../../src/dialog_box.c)), script messages ([src/field/scrcmd_message.c](../../src/field/scrcmd_message.c)), battle (`BattleSystem_GetTextFrameDelay`: always 1 in live link battles, not recordings), most apps. The raw `Options_GetTextSpeed` is only stored, never used, by the two Safari Zone apps. |
| battle scene | `BattleSystem_AreBattleAnimationsOn` ([src/battle/battle_system.c:751](../../src/battle/battle_system.c#L751)); always on in live link battles |
| battle style | `BattleSystem_GetBattleStyle`, once: the switch offer after a KO in single, non-Frontier, non-link battles ([src/battle/battle_controller_player.c:3482](../../src/battle/battle_controller_player.c#L3482)) |
| sound | boot, and the menu's preview |
| button mode | Continue; [src/application/palpad/palpad.c:190](../../src/application/palpad/palpad.c#L190) disables L/R paging when it is 1 |
| frame | `Options_GetFrame`, about 120 call sites, nearly all passed to `LoadUserFrameGfx2` |

## 2. How the menu is driven by data

### Rows and tables

Rows are an enum ([src/options_app.c:45](../../src/options_app.c#L45)); the last,
`MENU_ENTRY_6`, is the CONFIRM/QUIT row, so "option rows" loops run to `MENU_ENTRY_COUNT - 1`.

| Id | Row | Choices | Shown by |
|---|---|---|---|
| 0 | `MENU_ENTRY_TEXT_SPEED` | 3 | sprite 0 |
| 1 | `MENU_ENTRY_BATTLE_SCENE` | 2 | sprite 1 |
| 2–4 | `..._BATTLE_STYLE`, `..._SOUND_METHOD`, `..._BUTTON_MODE` | 2 | sprites 2–4 |
| 5 | `MENU_ENTRY_FRAME` | 20, one at a time | text, arrow sprites 5 and 6 |
| 6 | `MENU_ENTRY_6` | CONFIRM / QUIT | sprites 8 and 7 |

Each row is an `OptionsApp_MenuEntry` (`numStrings`, `value`, `String *strings[20]`). Row *i*
covers screen y `24 + 24*i` to `48 + 24*i`; its text goes at `i*24 + 5` in the
`selectedOption` window, which starts at y 24. The tables ([:94](../../src/options_app.c#L94)):

| Table | Holds |
|---|---|
| `sNumChoicesPerMenuEntry` | `{ 3, 2, 2, 2, 2, 20, 2 }` |
| `sOptionChoiceLabelXCoords[row][choice]` | x of the **centre** of each choice's text, window pixels |
| `sOptionsApp_ClearRectXOffsets` | where clearing the row starts before a redraw (FRAME: 16 px further left, for its wider text) |
| `sMenuEntryBorderYCoords` | `MAIN_0` y scroll that moves the selection border to the row: `-8 - 24*row`, except the last (CONFIRM) entry, -156 |
| `sActiveButtonXCoords[sprite][value]` | highlight sprite x per value, sprites 0–4 |
| `sOptionsAppTouchscreenHitboxes` | 15 rectangles + end marker |
| `sOptionsAppHitboxEntryValues[hitbox]` | `{ row, value }` per rectangle; on FRAME, 3 / 4 mean "carousel left / right" |
| `sOptionsAppSpriteTemplates` | the 9 sprites |

### Messages

`msg_0045` ([files/msgdata/msg/msg_0045.json](../../files/msgdata/msg/msg_0045.json)) is read
**by offset**:

| Ids | Text | Read as |
|---|---|---|
| 0 | OPTIONS | title |
| 1–6 | row names | `msg_0045_00001 + i` (`OptionsApp_SetupInterfaceText`) |
| 7, 8 | CONFIRM, QUIT | |
| 9–39 | all choices, row after row: SLOW MID FAST, ON OFF, SHIFT SET, STEREO MONO, NORMAL L=A, TYPE 1–20 | `msg_0045_00009 + msgNum++` (`OptionsApp_LoadMenuEntriesData`, [:759](../../src/options_app.c#L759)) |
| 40–59 | WINDOW TYPE 1–20 | top-screen preview, `msg_0045_00040 + frame` |

New messages go at the end of the file ([text-and-messages.md](text-and-messages.md)), where
the counting can't find them. §3.3 replaces it with tables.

### Graphics

NARC `a/0/7/2`, a binary archive ([graphics.md](graphics.md#4-changing-a-binary-archive)):
member 17 is the `MAIN_2` backdrop with every row band and its **unselected** button shapes
drawn in; 18 is the selection border (`MAIN_0`, 256×56, moved by scrolling); 7 is the tiles
for both. The selected choice is a sprite from resdat list `resdat_00000077_bin`
([files/data/resdat/resdat_00000077.json](../../files/data/resdat/resdat_00000077.json)):

| Set | Char / cell / anim member | Used for |
|---|---|---|
| 0 | 4 / 9 / 13 | choice highlight; animation 0 is 40 px wide, animation 1 is 56 px |
| 1, 2 | 5 / 10 / 14, 5 / 11 / 15 | FRAME left and right arrows |
| 3 | 6 / 12 / 16 | CONFIRM and QUIT buttons |

The highlight is drawn about 2 to 21 px below the sprite's y, so sprites sit at each row's
top y (24, 48, 72…).

### Data flow

1. `OptionsMenu_Init` ([:329](../../src/options_app.c#L329)) copies the save into
   `data->options`, an `OptionsApp_Options` (the same fields, `battleScene` and
   `battleStyle` swapped, no `dummy`).
2. `OptionsApp_LoadMenuEntriesData` sets each row's `value` from it.
3. Left/right change `value` (`OptionsApp_UpdateMenuEntryCarousel`, wrapping), redraw the row
   (`OptionsApp_UpdateMenuEntry`) and move sprites 0–4 (`OptionsApp_SetActiveButtonsXPosition`).
   Up/down change `currentMenuEntryId` and scroll the border
   (`OptionsApp_UpdateSelectionHighlight`). Touch looks up `{ row, value }` and does the same.
4. `OptionsMenu_Exit` ([:359](../../src/options_app.c#L359)): CONFIRM (`exitChoice == 1`)
   writes every row with the setters; QUIT or B (`exitChoice == 2`) undoes the live previews
   from `data->options`.

Live previews, in `OptionsApp_UpdateMenuEntry` ([:778](../../src/options_app.c#L778)):

| Row | Preview |
|---|---|
| TEXT SPEED | `Options_SetTextSpeed` on the **save's** options, then reprints "WINDOW TYPE n" on the top screen at that speed |
| SOUND | `GF_SndSetMonoFlag(value)` |
| BUTTON MODE | `Options_SetButtonModeOnMain(NULL, value)`: applies to the menu itself at once |
| FRAME | sets `reloadFrameGfx`; the VBlank callback reloads the frame with `LoadUserFrameGfx2` |

## 3. Worked example: AUTO-RUN

AUTO-RUN, OFF (0) / ON (1). One bit, so it takes `dummy`; old saves read OFF.

### 3.1 Does a seventh row fit?

No. The bottom screen is 192 px: title tab 0–24, six rows 24–168, CONFIRM/QUIT bar 168–192.

| Approach | Cost |
|---|---|
| **Title to the top screen, rows from y 0** (used below) | y tables shift 24; backdrop (member 17) changes; sprite, border and button art unchanged. The border's top edge on row 0 falls off screen (it sits 3–4 px above the row). |
| 20-px rows | y tables, backdrop, border and highlight art all redrawn |
| Replace a row, or add a second page | lose an option, or write paging code |

### 3.2 Save bit, getter and setter

```c
// include/options.h
    u16 frame : 5;
    u16 autoRun : 1;   // was: u16 dummy : 1;
} Options;
...
u32 Options_GetAutoRun(Options *options);
void Options_SetAutoRun(Options *options, u32 autoRun);
```

In [src/options.c](../../src/options.c) add the two functions like the others, and
`options->autoRun = 0; // off` to `Options_Init` (0 already; the line documents it).

### 3.3 Messages

Append to `msg_0045.json` after `msg_0045_00059`:

```json
    { "id": "msg_0045_00060", "en_US": "AUTO-RUN" },
    { "id": "msg_0045_00061", "en_US": "OFF" },
    { "id": "msg_0045_00062", "en_US": "ON" }
```

In `src/options_app.c`, after the sprite templates, add tables, then use them in place of the
offsets (and delete the unused `u16 msgNum = 0;`):

```c
static const u16 sMenuEntryNameMsgIds[MENU_ENTRY_COUNT - 1] = {
    msg_0045_00001, msg_0045_00002, msg_0045_00003, msg_0045_00004,
    msg_0045_00005, msg_0045_00006, msg_0045_00060,
};

static const u16 sMenuEntryFirstChoiceMsgIds[MENU_ENTRY_COUNT - 1] = {
    msg_0045_00009, msg_0045_00012, msg_0045_00014, msg_0045_00016,
    msg_0045_00018, msg_0045_00020, msg_0045_00061,
};

// OptionsApp_SetupInterfaceText
ReadMsgDataIntoString(data->msgData, sMenuEntryNameMsgIds[i], tmpString);
// OptionsApp_LoadMenuEntriesData
data->menuEntries[i].strings[j] = NewString_ReadMsgData(data->msgData, sMenuEntryFirstChoiceMsgIds[i] + j);
```

A row's choices must still be consecutive messages. These tables have seven entries, so
they compile only once §3.4 has added `MENU_ENTRY_AUTO_RUN`; build after §3.4, not here.

### 3.4 The row

Insert it before the CONFIRM/QUIT row (up/down then reach it between FRAME and CONFIRM),
add `u16 autoRun : 1;` after `frame` in `OptionsApp_Options`, and give every
`[MENU_ENTRY_COUNT]` table an entry, with the y values moved up 24:

```c
    MENU_ENTRY_FRAME,
    MENU_ENTRY_AUTO_RUN,
    MENU_ENTRY_6,          // now 7, still CONFIRM/QUIT

static const s8 sOptionsApp_ClearRectXOffsets[MENU_ENTRY_COUNT] = { 0, 0, 0, 0, 0, -0x10, 0, 0 };
static const int sNumChoicesPerMenuEntry[MENU_ENTRY_COUNT] = { 3, 2, 2, 2, 2, 20, 2, 2 };
static const int sMenuEntryBorderYCoords[MENU_ENTRY_COUNT] = { 16, -8, -32, -56, -80, -104, -128, -156 };

static const u16 sOptionChoiceLabelXCoords[MENU_ENTRY_COUNT][3] = {
    ...
    { 172, 0,   0   },   // FRAME
    { 132, 212, 0   },   // AUTO-RUN: the wide two-choice layout of rows 2-4
    { 0,   0,   0   },
};
```

The value goes in and out at the three places that list every field:

```c
// OptionsMenu_Init
data->options.autoRun = Options_GetAutoRun(args->options);
// OptionsApp_LoadMenuEntriesData
data->menuEntries[MENU_ENTRY_AUTO_RUN].value = data->options.autoRun;
// OptionsMenu_Exit, exitChoice == 1
data->options.autoRun = data->menuEntries[MENU_ENTRY_AUTO_RUN].value;
Options_SetAutoRun(data->playerOptions, data->options.autoRun);
```

Text needs nothing else: it is printed at `i * 24 + 5` inside the window, which moves with
the rows (§3.7).

### 3.5 Sprites

Append the highlight as sprite 9, so 5–8 keep their meaning:

- `Sprite *sprites[9]` → `[10]`; `sOptionsAppSpriteTemplates[9]` → `[10]`, the new entry a
  copy of entry 2 (`.resourceSet = 0`, `.animation = 1`, `.x = 112`) with `.y = 144`;
- `SpriteSystem_InitSprites(..., 9)` → `10` (`maxTasks = 9` beside it counts char
  transfers, leave it);
- existing template y: 24, 48, 72, 96, 120 → 0, 24, 48, 72, 96; FRAME arrows 144 → 120;
  CONFIRM/QUIT stay at 170.

`OptionsApp_SetActiveButtonsXPosition` only loops over 0–4; after the loop:

```c
    s16 x, y;
    Sprite_GetPositionXY(data->sprites[9], &x, &y);
    x = sActiveButtonXCoords[2][data->menuEntries[MENU_ENTRY_AUTO_RUN].value];  // { 112, 192 }
    Sprite_SetPositionXY(data->sprites[9], x, y);
```

### 3.6 Touch

Hitboxes 13 and 14 are CONFIRM and QUIT as `case 13:` / `case 14:` in
`OptionsApp_HandleInput`. Append after them, and subtract 24 from `top`/`bottom` of 0–12:

```c
static const TouchscreenHitbox sOptionsAppTouchscreenHitboxes[18] = {
    { .rect = { .top = 2, .bottom = 22, .left = 112, .right = 151 } },     // 0: was 26-46
    ...
    { .rect = { .top = 172, .bottom = 191, .left = 183, .right = 255 } },  // 14: quit, unchanged
    { .rect = { .top = 146, .bottom = 166, .left = 112, .right = 167 } },  // 15: auto-run OFF
    { .rect = { .top = 146, .bottom = 166, .left = 192, .right = 247 } },  // 16: auto-run ON
    { TOUCHSCREEN_RECTLIST_END },
};

static const u32 sOptionsAppHitboxEntryValues[17][2] = {
    ...
    { MENU_ENTRY_AUTO_RUN, 0 },
    { MENU_ENTRY_AUTO_RUN, 1 },
};
```

The `default:` case handles 15 and 16.

### 3.7 Windows

```c
// OptionsApp_SetupWindows
AddWindowParameterized(data->bgConfig, &data->windows.optionsTitle, GF_BG_LYR_SUB_1, 1, 1, 12, 3, 13, 0x7F);
AddWindowParameterized(data->bgConfig, &data->windows.selectedOption, GF_BG_LYR_MAIN_1, 1, 0, 30, 21, 13, 0x0A);
AddWindowParameterized(data->bgConfig, &data->windows.quitButton, GF_BG_LYR_MAIN_1, 24, 21, 7, 3, 13, 0x280);
AddWindowParameterized(data->bgConfig, &data->windows.confirmButton, GF_BG_LYR_MAIN_1, 15, 21, 7, 3, 13, 0x295);
```

| Layer | Window | Tiles |
|---|---|---|
| `MAIN_1` | `selectedOption` 30×21 = 630 | 0x0A–0x27F |
| `MAIN_1` | `quitButton`, `confirmButton` 7×3 = 21 each | 0x280–0x294, 0x295–0x2A9 |
| `SUB_1` | `frameAndTextSpeedTest` 27×4 = 108 | 0x01–0x6C |
| `SUB_1` | frame graphics, loaded at 0x6D (18 tiles) | 0x6D–0x7E |
| `SUB_1` | `optionsTitle` 12×3 = 36 | 0x7F–0xA2 |

`MAIN_1`'s tiles start at 0x4000 and may run to tile 0x53F, where `MAIN_2`'s tilemap
(0xE800) begins. The sub screen's palette slot 13 already holds font palette 0.

### 3.8 The backdrop

Member 17 is 32×32 cells: rows 0–2 the title tab, 3–20 six bands of three cell rows (light
and dark alternating; panel corners in rows 3 and 20), 21 a separator, 22–23 the bottom bar.
Move rows 3–20 up to 0–17, add a light two-choice band (a copy of rows 9–11) as rows 18–20,
and give FRAME's last row the plain side edges of row 14:

```python
import struct, sys
b = bytearray(open(sys.argv[1], 'rb').read())        # 00017.NSCR: 0x24-byte header, 1024 entries
e = list(struct.unpack('<1024H', b[0x24:0x24 + 2048]))
row = lambda r: e[r * 32:(r + 1) * 32]
new = [row(r) for r in range(3, 20)]
r20 = row(20); r20[0] = row(14)[0]; r20[31] = row(14)[31]
new += [r20, row(9), row(10), row(11)]
new += [row(r) for r in range(21, 32)]
b[0x24:] = struct.pack('<1024H', *[v for r in new for v in r])
open(sys.argv[2], 'wb').write(b)
```

Unpack and repack `files/a/0/7/2` as in [graphics.md §4](graphics.md#4-changing-a-binary-archive).
Rendered offline, the result has seven alternating bands whose buttons line up with the
sprite positions and hitboxes above.

### 3.9 The read site

`IsRunButtonHeld` ([src/player_avatar_movement.c:1186](../../src/player_avatar_movement.c#L1186))
checks B in the held keys (after `PlayerSaveData_CheckRunningShoes`). The keys come from
`FieldInput_Update` ([src/field/field_control.c:121](../../src/field/field_control.c#L121)),
which already forces B for the running-shoes lock. Flip B before that:

```c
#include "options.h"
#include "player_data.h"
...
    FieldInput_Clear(fieldInput);

    if (Options_GetAutoRun(Save_PlayerData_GetOptionsAddr(fieldSystem->saveData))) {
        heldKeys ^= PAD_BUTTON_B;
    }
    if (PlayerAvatar_CheckRunningShoesLock(FieldSystem_GetPlayerAvatar(fieldSystem))) {
        heldKeys |= PAD_BUTTON_B;
    }
```

The `^=` inverts B rather than adding it: with AUTO-RUN on, holding B walks. Nothing runs
before the player has the Running Shoes, since `IsRunButtonHeld` checks them first.

Held B has no other use in `field_control.c` or the bike code. Link rooms read held B
separately: `CommPlayerManager_UpdateLocalMoveSpeed` sets the synced speed from
`gSystem.heldKeys`, and the movement itself goes through
`PlayerAvatar_GetMovementFromInput` with running allowed (both in
[src/comm_player_sync.c](../../src/comm_player_sync.c)); add the check there too if wanted.

Files touched: `include/options.h`, `src/options.c`, `msg_0045.json`, `src/options_app.c`,
`files/a/0/7/2`, `src/field/field_control.c`.

## 4. Changing existing options

### Adding a choice to a row

Example: BUTTON MODE START=X. `ApplyButtonModeToInput` already implements
`BUTTONMODE_STARTEQUALSX` (and `BUTTONMODE_SWAPXY`); `buttonMode` has two bits.

1. Keep the old values (0 NORMAL, 1 L=A) and make the new one 2, so old saves and
   palpad's `== 1` check keep their meaning.
2. `Options_SetButtonModeOnMain`: `case 2: gSystem.buttonMode = BUTTONMODE_STARTEQUALSX; break;`
3. Append NORMAL, L=A, START=X as three new messages and point the row's
   `sMenuEntryFirstChoiceMsgIds` entry at the first (§3.3).
4. `sNumChoicesPerMenuEntry[MENU_ENTRY_BUTTON_MODE] = 3`.
5. Three 56-px buttons don't fit in 112–256, so use row 0's layout: labels `{ 124, 172, 220 }`,
   `sActiveButtonXCoords[4] = { 112, 160, 208 }`, template 4 `.animation = 0`, row 0's
   hitbox x ranges, and the band redrawn with row 0's three small buttons (cell columns
   14–30 of rows 3–5).

More choices than fit need the carousel; `OptionsApp_UpdateMenuEntry` treats only
`MENU_ENTRY_FRAME` that way. A row holds at most 20 strings.

### Text speeds

Change the numbers in `Options_GetTextFrameDelay`; every reader goes through it.

- 1 is the fastest the printer goes: one character per call, then `speed - 1` calls of
  waiting (`RenderText`, [src/render_text.c](../../src/render_text.c)).
- Don't return 0: `AddTextPrinter` ([src/text.c:171](../../src/text.c#L171)) treats it as
  `TEXT_SPEED_INSTANT`, draws the whole string at once and returns no running printer, which
  dialogue that waits for a button or scrolls isn't written for.
- A fourth speed fits in `textSpeed`; add it there and as a choice (above). Link battles
  still use 1.

### Defaults

Edit `Options_Init`. Only new games see it ([new-game.md](new-game.md)).

### Frames

`LoadUserFrameGfx2` loads tiles from `a/0/3/8` member `frame + 2` and the palette from
`frame + 0x1A` ([src/render_window.c:73](../../src/render_window.c#L73)): frames 0–19 use
members 2–21 and 26–45. Member 22 is another graphic and 46 (0x2E) is a palette
`LoadUserFrameGfx1` uses, so a frame 20 needs new members at the end and a case for
`frame >= 20` in `GetUserFrameGfx2TilesMember` / `GetUserFrameGfx2PaletteMember`. The
preview reads `msg_0045_00040 + frame`, so "WINDOW TYPE 21" must be message 60 (append it
before §3.3's messages) or get its own table. `frame` has room for 32.

## 5. Pitfalls

- **`currentMenuEntryId` is 3 bits**: at most 8 rows including CONFIRM/QUIT, which §3 uses
  up. One more needs `currentMenuEntryId : 4` and `unk10_5 : 15` in `OptionsApp_Data`.
- **Hard-coded indices**: sprites 5–8, the 0–4 loop, hitbox cases 13/14. Append, don't
  insert.
- **New rows go before `MENU_ENTRY_6`**: loops use `MENU_ENTRY_COUNT - 1` for option rows.
- **Live previews change global state**: the save's text speed, the sound mode, the button
  mode. Undo yours on QUIT like `OptionsMenu_Exit` does.
- **Button mode applies everywhere**, Options included: in L=A mode, L and R are removed
  from `newKeys`, `heldKeys` and `newAndRepeatedKeys` (only the `Raw` fields keep them).
- **Save layout**: use `dummy`, unused values or the padding; check `SAVE_PLAYERDATA` is still
  44 bytes with `tools/savemap/savemap.py` ([save-compatibility.md](save-compatibility.md#3-rules-for-save-safe-updates)).
- **Battles get `Options` only**: a battle option in a separate field must be passed in
  another way.

## Where to look

| What | File |
|---|---|
| The saved struct and accessors | [include/options.h](../../include/options.h), [src/options.c](../../src/options.c) |
| Its place in the save | [include/player_data.h](../../include/player_data.h), [src/player_data.c](../../src/player_data.c) |
| The screen | [src/options_app.c](../../src/options_app.c) |
| Launching it | `OptionsMenu_LaunchApp` in [src/launch_application.c](../../src/launch_application.c), from [src/start_menu.c](../../src/start_menu.c) |
| Text | [files/msgdata/msg/msg_0045.json](../../files/msgdata/msg/msg_0045.json) |
| Graphics | `files/a/0/7/2`, frames in `files/a/0/3/8`, [resdat_00000077.json](../../files/data/resdat/resdat_00000077.json) |
| Button mode | [src/system.c](../../src/system.c), `BUTTONMODE_*` in [include/system.h](../../include/system.h) |
| Battle readers | [src/battle/battle_system.c](../../src/battle/battle_system.c) |
| Running | [src/field/field_control.c](../../src/field/field_control.c), [src/player_avatar_movement.c](../../src/player_avatar_movement.c) |

## Not verified

- The §3 code was built with `make release` but not run. The §3.8 tilemap was rendered
  offline, not seen in game; neither was the title on the top screen.
- That widening `Options` breaks saved battle videos is read from the struct, not tested.
- §4's START=X and extra-frame steps were not built.
