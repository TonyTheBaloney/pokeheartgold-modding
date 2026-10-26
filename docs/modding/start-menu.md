<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The start menu

> AI-generated; not affiliated with pret. See AI.md at the repository root.

What X opens in the overworld: which entries it has and when, what each one does, and
how to rename, hide, replace or add one. The code is
[src/start_menu.c](../../src/start_menu.c) (the menu's logic, a field task) and
[src/field/touchscreen_menu.c](../../src/field/touchscreen_menu.c) (the icons on the
bottom screen). How screens are launched from the field and how the field comes back
is in [ui.md §1](ui.md#launching-an-application); field tasks are in
[engine.md §4](engine.md#4-field-tasks). Neither is repeated here.

The main difference from Gen 3: HeartGold has **no menu window**. The menu is the
icon grid that is always on the bottom screen. X (or touching MENU) puts that grid into
"cursor mode": the D-pad moves a highlight, A picks. Touching an icon picks it directly,
with or without X. So "a start menu entry" and "a touch-screen icon" are the same thing,
described by two sets of tables that must agree.

| pokeemerald | here |
|---|---|
| `sStartMenuItems[]` (text, callback) | `sStartMenuActions[]`, indexed by `StartMenuAction` (msg id, `TaskFunc`) |
| `BuildStartMenuActions`, `AddStartMenuAction` | `StartMenu_BuildActionLists` plus the inhibit masks of `FieldSystem_GetStartMenuButtonInhibitFlags_*` |
| `FlagGet(FLAG_SYS_POKEDEX_GET)` in the builder | `FieldSystem_ShouldDrawStartMenuIcon` (`CheckGotPokedex`, ...) |
| `BuildSafariZoneStartMenu` and other variants | a different inhibit mask and touch layout per mode (Safari, Bug Contest, Pal Park, ...) |
| `StartMenuPokedexCallback` etc. | `Task_StartMenu_HandleSelection_*` → `Task_StartMenu_*` → `Task_StartMenu_HandleReturn_*` |
| `sStartMenuCursorPos` | `fieldSystem->startMenuCursorPos` |
| the list window, `PrintStartMenuActions` | the bottom-screen icons, labels and highlight (`touchscreen_menu.c`) |
| `CB2_ReturnToFieldWithOpenMenu` | `START_MENU_STATE_RETURN`: reload the map, draw the menu again |

## 1. Opening and closing

**Opening.** `FieldInput_Update` in
[src/field/field_control.c](../../src/field/field_control.c) sets `fieldInput->menu` when
X is pressed or the touch menu has reported a touch (`fieldSystem->lastTouchMenuInput != 0`),
**but only if the Bag icon is unlocked** (`FieldSystem_ShouldDrawStartMenuIcon(fieldSystem, START_MENU_ICON_BAG)`).
If the Dowsing MCHN is on the bottom screen, X switches back to the icons and opens the menu.
`FieldInput_Process` then plays `SEQ_SE_DP_WIN_OPEN` and calls `StartMenu_Init`, unless the
map is in the Mystery Zone. The Union Room and Colosseum use `StartMenu_InitUnionRoom` /
`StartMenu_InitColosseum`.

`StartMenu_Init` ([src/start_menu.c:216](../../src/start_menu.c#L216)) allocates a
`StartMenuTaskData` (`include/start_menu.h`), picks the inhibit mask for the current
mode (§2), stops the player if mid-step, and starts the field task `Task_StartMenu`.
While it runs, map objects are paused and the player can't move.

**What gets drawn.** The start menu itself draws little:

- `Task_StartMenu_DrawCursor` loads a small graphic into the top screen's BG layer
  `GF_BG_LYR_MAIN_3` (`a/0/1/4` members 12 and 13, palette 15), and
  `StartMenu_CreateCursor` makes one animated sprite on the top screen at (100, 144)
  from members 61-64. Member 64 is a small down-arrow; despite the names, neither is a
  cursor or the icons.
- Everything else (icons, labels, the highlighted icon, the dimmed background) is the
  touch menu reacting to `fieldSystem->startMenuState`:

| `startMenuState` | Meaning |
|---|---|
| 0 | menu closed; the icons act as field buttons |
| 1 | `Task_StartMenu` has just drawn; the touch menu highlights the selection, turns off the registered-item buttons, and sets 2 |
| 2 | menu open: the touch menu reads the D-pad and touches for it |
| 3, 4 | handing back from the save screen or the touch choice menu (`TouchscreenMenu_SyncStartMenuState`) |

**Input.** Split between the two files:

- D-pad: `TouchscreenMenu_HandleDpadInput` moves the highlight between icons through the
  neighbour table `gTouchscreenMenuIconNeighbors` and writes the new position to
  `fieldSystem->startMenuCursorPos`.
- A: `StartMenu_HandleKeyInput` runs the entry at `startMenuCursorPos`.
- Touch: `TouchscreenMenu_HandleTouchInput` writes the touched entry to
  `lastTouchMenuInput`; `StartMenu_HandleTouchInput` reads it and runs the entry.
- B or X: `Task_StartMenu_HandleInput` plays `SEQ_SE_GS_GEARCANCEL` and goes to
  `START_MENU_STATE_CLOSE`, which removes the top-screen graphic, sets `startMenuState`
  to 2 (the touch menu then restores itself and sets 0), frees the data and ends the task.

**Cursor memory.** `fieldSystem->startMenuCursorPos` is the position among the *shown*
icons, counted in slot order (`TouchscreenMenu_GetMenuIndex`). It lives in `FieldSystem`,
so it survives closing the menu and leaving to a screen, but not a reset (it is not in
the save). It is set back to 0 when a new icon appears (`TouchscreenMenu_ShowNewIcons`).
(`StartMenuTaskData.lastButtonSelected` is computed but never read.)

**Coming back.** After a screen closes, the return handler reloads the map and sets
`START_MENU_STATE_RETURN`, which redraws the menu and fades in. If the entry was picked
by touch (`MenuInputStateMgr_GetState(&fieldSystem->menuInputState)` is
`MENU_INPUT_STATE_TOUCH`), `Task_StartMenu_WaitApp` goes to `START_MENU_STATE_10`
instead: fade in and close, so the player is back on the field.

## 2. The entries

### Actions

`enum StartMenuAction` and `sStartMenuActions[]` are at the top of
[src/start_menu.c](../../src/start_menu.c#L49). The `.ident` message ids are not used
for display; the labels come from the touch menu (§5).

| Action | Entry | Selection function |
|---|---|---|
| `START_MENU_ACTION_POKEDEX` | Pokédex | `Task_StartMenu_HandleSelection_Pokedex` |
| `START_MENU_ACTION_POKEMON` | Pokémon | `Task_StartMenu_HandleSelection_Pokemon` |
| `START_MENU_ACTION_BAG` | Bag | `Task_StartMenu_HandleSelection_Bag` |
| `START_MENU_ACTION_TRAINER_CARD` | Trainer Card | `Task_StartMenu_HandleSelection_TrainerCard` |
| `START_MENU_ACTION_SAVE` | Save | `Task_StartMenu_HandleSelection_Save` |
| `START_MENU_ACTION_OPTIONS` | Options | `Task_StartMenu_HandleSelection_Options` |
| `START_MENU_ACTION_RUNNING_SHOES` | "EXIT" (never selectable) | `STARTMENUTASKFUNC_CANCEL` |
| `START_MENU_ACTION_7` | Union Room CHAT | `Task_StartMenu_HandleSelection_RemovedEasyChatThing` |
| `START_MENU_ACTION_RETIRE` | Retire | `Task_StartMenu_HandleSelection_Retire` |
| `START_MENU_ACTION_9`, `_10` | placeholders at positions 7 and 8 (see below) | `Task_StartMenu_HandleSelection_Pokegear` |
| `START_MENU_ACTION_POKEGEAR` | Pokégear | `Task_StartMenu_HandleSelection_Pokegear` |
| `START_MENU_ACTION_12` | Union Room LOG | `StartMenu_SelectUnionChatLog` |

`sActionToIconIndex[]` maps an action to the `StartMenuIcon` whose unlock condition
gates it (`FieldSystem_StartMenuActionIsAvailable`); 100 means "always available".

### Order and visibility

`StartMenu_BuildActionLists` ([src/start_menu.c:483](../../src/start_menu.c#L483))
builds `selectionToAction[]`, the action for each position, by appending every action
whose bit is **not** set in `startMenu->inhibitIconFlags`, in this order:

Retire, CHAT (`_7`), Pokédex, Pokémon, Bag, Pokégear (LOG `_12` in the Union Room),
Trainer Card, Save, Options, Running Shoes; then `_9` and `_10` are written at positions 7
and 8.

Position 7 and 8 never correspond to an icon: the touch menu only reports icon slots
0-6 as positions, so as far as the code shows, `_9`, `_10` and the Running Shoes entry
can't be chosen. They do make `numActiveButtons` larger than the number of icons.

The bits are `enum StartMenuActionDisable` (`START_MENU_ACTION_DISABLE_*`). Which mask is
used depends on the mode. `StartMenu_Init` checks Safari, Bug Contest, Pal Park, the
Battle Tower partner room, then Normal; Colosseum and Union Room have their own entry
points (`StartMenu_InitColosseum`, `StartMenu_InitUnionRoom`), and only
`StartMenu_ReopenAfterScript` checks them by `mapLoadType`:

| Mode (checked with) | Hidden |
|---|---|
| Safari Zone (`Save_VarsFlags_CheckSafariSysFlag`) | Save, CHAT |
| Bug Contest (`Save_VarsFlags_CheckBugContestFlag`) | Bag, Save, CHAT |
| Pal Park (`Save_VarsFlags_CheckPalParkSysFlag`) | Bag, Save, CHAT |
| Battle Tower partner room (`FieldSystem_MapIsBattleTowerMultiPartnerSelectRoom`) | Pokédex, Bag, Save, CHAT, Retire, Pokégear |
| Colosseum | Pokédex, Save, CHAT, Retire, Pokégear |
| Union Room | Save, Retire |
| anything else (`..._Normal`) | CHAT, Retire, and each of Pokédex / Pokémon / Bag / Pokégear not yet obtained |

The "obtained" checks are in `FieldSystem_GetStartMenuButtonInhibitFlags_Normal` and
in `FieldSystem_ShouldDrawStartMenuIcon`
([src/start_menu.c:535](../../src/start_menu.c#L535)), which the touch menu also uses:

| `StartMenuIcon` | Shown when | Flag |
|---|---|---|
| `START_MENU_ICON_POKEDEX` | `CheckGotPokedex` | `FLAG_GOT_POKEDEX` |
| `START_MENU_ICON_POKEMON` | `CheckGotStarter` | `FLAG_GOT_STARTER` |
| `START_MENU_ICON_BAG` | `CheckGotMenuIconI(..., START_MENU_ICON_UNLOCK_BAG)` | `FLAG_GOT_BAG` |
| `START_MENU_ICON_POKEGEAR` | `CheckGotPokegear` | `FLAG_GOT_POKEGEAR` |
| `START_MENU_ICON_TRAINER_CARD` | `CheckGotMenuIconI(..., START_MENU_ICON_UNLOCK_TRAINER_CARD)` | `FLAG_GOT_TRAINER_CARD` |
| `START_MENU_ICON_SAVE` | `CheckGotMenuIconI(..., START_MENU_ICON_UNLOCK_SAVE_BUTTON)` | `FLAG_GOT_SAVE_BUTTON` |
| `START_MENU_ICON_OPTIONS` | `CheckGotMenuIconI(..., START_MENU_ICON_UNLOCK_OPTIONS_BUTTON)` | `FLAG_GOT_OPTIONS_BUTTON` |
| `START_MENU_ICON_RUNNING_SHOES` | `PlayerSaveData_CheckRunningShoes` | (the running-shoes button, not an icon slot) |

Trainer Card, Save and Options are not in the Normal mask: retail sets their flags
together with `FLAG_GOT_BAG` ([story-progression.md](story-progression.md)), and without
the Bag the menu doesn't open at all. Setting one of these flags in a script makes the
icon appear with an animation (`TouchscreenMenu_ShowNewIcons`).

## 3. What each entry does

All app entries follow the same three-step pattern, run by `Task_StartMenu`'s states:

1. **Selection** (`Task_StartMenu_HandleSelection_X`, called on A or touch): fade out with
   `FieldMap_FadeScreen(FADE_TYPE_BRIGHTNESS_OUT)`, store the launch step in
   `startMenu->exitTaskFunc`, set `START_MENU_STATE_WAIT_FADE`, return `TRUE`.
2. **Launch** (`Task_StartMenu_WaitFade` calls `exitTaskFunc` after the fade): remove the
   top-screen graphic, call the app's launcher, store its args in
   `startMenu->exitTaskEnvironment` and the return step in `exitTaskFunc`. The state
   becomes `START_MENU_STATE_WAIT_APP`.
3. **Return** (`Task_StartMenu_WaitApp` calls `exitTaskFunc` once
   `!FieldSystem_ApplicationIsRunning`): read the results, free the args,
   `FieldSystem_LoadFieldOverlay`, set `START_MENU_STATE_RETURN`. Or launch the next
   screen instead and call `StartMenu_SetExitTaskFunc` with the next return step (the
   party menu → summary → party menu chains do this).

| Entry | Launch step → launcher | Return step |
|---|---|---|
| Pokédex | `Task_StartMenu_OpenPokedex` → `Pokedex_LaunchApp` | `Task_StartMenu_HandleReturn_Pokedex` |
| Pokémon | `Task_StartMenu_Pokemon` → `PartyMenu_LaunchApp_Field` | `Task_StartMenu_HandleReturn_Pokemon`: summary, mail, evolution, field moves ([party-menu-and-item-use.md](party-menu-and-item-use.md)) |
| Bag | `Task_StartMenu_Bag` → `Bag_LaunchApp_AllPockets` | `Task_StartMenu_HandleReturn`: item use, Berry tag, give item |
| Pokégear | `Task_StartMenu_Pokegear` → `PokegearPhone_LaunchApp` | `Task_StartMenu_HandleReturn_Pokegear` |
| Trainer Card | `Task_StartMenu_TrainerCard` → `TrainerCard_LaunchApp` | `Task_StartMenu_HandleReturn_TrainerCard` |
| Options | `Task_StartMenu_Options` → `OptionsMenu_LaunchApp` | `Task_StartMenu_HandleReturn_Options` |
| CHAT (Union Room) | `Task_StartMenu_RemovedEasyChatThing` → `EasyChat_LaunchApp` | `Task_StartMenu_HandleReturn_RemovedEasyChatThing` |

The others don't launch an application:

- **Save** (`Task_StartMenu_HandleSelection_Save`): switches the bottom screen to
  `BOTTOM_SCREEN_APP_TOUCH_SAVE` ([src/touch_save_app.c](../../src/touch_save_app.c)) with
  `FieldSystem_SwitchBottomScreenApp(fieldSystem, 1, NULL)`. `START_MENU_STATE_SAVE` waits
  for it to open, state 7 for the touch menu to be back; then the menu returns to input,
  or closes if the save screen left `lastTouchMenuInput == 1`. The map keeps running.
- **LOG** (`StartMenu_SelectUnionChatLog`): switches the bottom screen to app 8
  (`BOTTOM_SCREEN_APP_UNION_CHAT_LOG`) and closes the menu through states 19 and 20.
- **Retire** (`Task_StartMenu_HandleSelection_Retire`,
  [src/start_menu.c:1252](../../src/start_menu.c#L1252)): runs a script in place of the
  menu:

  ```c
  StartMenu_RemoveCursorAndIcons(startMenu, fieldSystem);
  fieldSystem->startMenuState = 0;
  if (Save_VarsFlags_CheckSafariSysFlag(Save_VarsFlags_Get(fieldSystem->saveData)) == TRUE) {
      StartScriptFromMenu(taskManager, std_safari_exit, NULL);
  } else if (Save_VarsFlags_CheckBugContestFlag(Save_VarsFlags_Get(fieldSystem->saveData)) == TRUE) {
      StartScriptFromMenu(taskManager, std_bug_contest_retire, NULL);
  } else {
      StartScriptFromMenu(taskManager, 4, NULL);   // Pal Park: the current map's script 4
  }
  Heap_Free(startMenu);
  return FALSE;
  ```

  `StartScriptFromMenu` ([src/script_manager.c](../../src/script_manager.c)) replaces the
  start menu task with `Task_RunScripts` (`TaskManager_Jump`). The menu data is freed, and
  the function returns `FALSE` so `Task_StartMenu` returns at once without touching it.

A script can bring the menu back when it ends with the `ReopenStartMenuOnEnd` command
(`Script_ReopenStartMenuOnEnd` → `StartMenu_ReopenAfterScript`); signposts use it.

## 4. How-to

The icon art and label belong to the touch menu (§5); the action and its condition belong
to the start menu. Most changes touch both.

### Renaming an entry

Edit the label in [files/msgdata/msg/msg_0196.json](../../files/msgdata/msg/msg_0196.json):
`msg_0196_00000` POKéDEX, `_00001` POKéMON, `_00002` BAG, `_00003` the player's name
(Trainer Card), `_00004` SAVE, `_00005` OPTIONS, `_00008` RETIRE, `_00014` POKéGEAR,
`_00034` CHAT, `_00035` LOG, `_00012` MENU. Labels are printed in a 9×2-tile window
centered in 72 pixels (`TouchscreenMenu_PrintIconLabels`); keep them that short.

### Changing when an entry appears

Change its case in `FieldSystem_ShouldDrawStartMenuIcon`. If the entry can be hidden
while an entry after it in `StartMenu_BuildActionLists` is shown, also set its
`START_MENU_ACTION_DISABLE_*` bit in the inhibit mask under the same condition (as
`..._Normal` does for the Pokédex). Otherwise the two lists disagree: the touch menu
counts the hidden icon out, the start menu counts it in, and every later icon runs the
action of the one before it.

### Removing an entry

Delete its block from `StartMenu_BuildActionLists` and make its case in
`FieldSystem_ShouldDrawStartMenuIcon` return `FALSE`. That hides it in every mode. The
slot stays empty on the bottom screen. This only covers icons 0-6: Retire, CHAT and LOG
are shown from the `0x8000` enabled bit in `gTouchscreenMenuIcons`
(`TouchscreenMenu_InitIconFlags`), so clear that bit for them. The Pokégear block in
`StartMenu_BuildActionLists` also adds LOG in the Union Room; deleting it removes both.

### Reordering

There is no single order table. The position on screen is the slot in
`gTouchscreenMenuLayouts` ([asm/touchscreen_menu_data.s](../../asm/touchscreen_menu_data.s)),
and the start menu's order is the code order in `StartMenu_BuildActionLists`; both must
change together. In the normal layout, slot *n* holds icon *n*, and
`TouchscreenMenu_ShowNewIcons`, `TouchscreenMenu_CopyIconLabelsToVram` and the
Pokégear ring animation (`sprites[3]`) rely on that. Moving icons in the normal layout
means fixing those too; this guide hasn't done it.

### Worked example: an entry that runs a script

The normal layout's seven slots are all used, so this replaces Options with an entry
that runs a shared script. Six files. These exact edits compile and assemble; they
have not been run in an emulator.

**1. The script id**, in [include/constants/std_script.h](../../include/constants/std_script.h)
after `std_fade_end_rival_outro_music`:

```c
#define std_menu_my_script             2072
```

(2072 is the first free `std_misc` id. [debugging.md §6](debugging.md#6-a-debug-menu)
uses it for `std_debug_menu`; with both, use 2073, `_073` and the next free
`msg_0040` number below. Or skip steps 1-3 and
use `std_debug_menu` itself, which puts the debug menu on the start menu.)

**2. The script**, in
[files/fielddata/script/scr_seq/scr_seq_0003.s](../../files/fielddata/script/scr_seq/scr_seq_0003.s):
`ScrDef scr_seq_0003_072` before `ScrDefEnd`, `#define _EV_scr_seq_0003_072 72` in
`event_0003.h`, and before the final `.balign 4, 0`:

```
scr_seq_0003_072:
	LockAll
	TouchscreenMenuHide
	NPCMsg msg_0040_00117
	WaitButton
	CloseMsg
	TouchscreenMenuShow
	ReleaseAll
	End
```

**3. The text**: `msg_0040_00117` at the end of
[files/msgdata/msg/msg_0040.json](../../files/msgdata/msg/msg_0040.json), as in
debugging.md §6.

`TouchscreenMenuHide` / `TouchscreenMenuShow` swap the bottom screen to the choice menu
and back, which rebuilds the touch menu. Keep them: picking an entry sets the touch
menu's `selectedIconAnim`, and from reading the code nothing else clears it, so without
a rebuild the icon would stay highlighted and ignore touches. The Bug Contest's retire
script brackets its question the same way.

**4. The action**, in [src/start_menu.c](../../src/start_menu.c). A prototype next to the
others, the function after `Task_StartMenu_HandleSelection_Retire` (it is the Retire
pattern), and Options' table entry pointed at it:

```c
static BOOL Task_StartMenu_HandleSelection_MyScript(TaskManager *taskManager) {
    FieldSystem *fieldSystem = TaskManager_GetFieldSystem(taskManager);
    StartMenuTaskData *startMenu = (StartMenuTaskData *)TaskManager_GetEnvironment(taskManager);

    StartMenu_RemoveCursorAndIcons(startMenu, fieldSystem);
    fieldSystem->startMenuState = 0;
    StartScriptFromMenu(taskManager, std_menu_my_script, NULL);
    Heap_Free(startMenu);
    return FALSE;
}
```

```c
    [START_MENU_ACTION_OPTIONS] = { .ident = msg_0196_00005, .func = Task_StartMenu_HandleSelection_MyScript },
```

**5. Label, condition, icon.** Change `msg_0196_00005` (Renaming, above). To show the
entry only after a flag, change the `START_MENU_ICON_OPTIONS` case of
`FieldSystem_ShouldDrawStartMenuIcon` to
`return CheckScriptFlag(Save_VarsFlags_Get(fieldSystem->saveData), FLAG_X);` with a free
flag ([unknown-flags-vars.md](unknown-flags-vars.md#free-flags)); Options is the last
entry, so no inhibit bit is needed. The picture is `a/0/1/4` member 39 (the wrench). It
uses the shared icon palette, member 14, and the cells and animations of members 16
and 17; [graphics.md §4](graphics.md#4-changing-a-binary-archive) shows the
unpack/convert/repack steps (`-palette` with member 14, `-cell` with member 16). Every
icon shares that one 16-color palette (and its highlighted copy in the same file), so
new art must use its colors.

Build with `make release`. Icon 6 is in every layout, so the entry replaces Options in the
Safari Zone, Bug Contest, Pal Park and Union Room too.

### Opening a screen instead

Copy the Options trio. `MyApp_LaunchApp` is your launcher
([ui.md §1](ui.md#launching-an-application), "Adding a new application"):

```c
static BOOL Task_StartMenu_HandleSelection_MyApp(TaskManager *taskManager) {
    StartMenuTaskData *startMenu = (StartMenuTaskData *)TaskManager_GetEnvironment(taskManager);

    FieldMap_FadeScreen(FADE_TYPE_BRIGHTNESS_OUT);
    startMenu->exitTaskFunc = Task_StartMenu_MyApp;
    startMenu->state = START_MENU_STATE_WAIT_FADE;
    return TRUE;
}

static BOOL Task_StartMenu_MyApp(TaskManager *taskManager) {
    FieldSystem *fieldSystem = TaskManager_GetFieldSystem(taskManager);
    StartMenuTaskData *startMenu = (StartMenuTaskData *)TaskManager_GetEnvironment(taskManager);

    startMenu->exitTaskEnvironment = MyApp_LaunchApp(fieldSystem);
    startMenu->exitTaskFunc = Task_StartMenu_HandleReturn_MyApp;
    return FALSE;
}

static BOOL Task_StartMenu_HandleReturn_MyApp(TaskManager *taskManager) {
    FieldSystem *fieldSystem = TaskManager_GetFieldSystem(taskManager);
    StartMenuTaskData *startMenu = (StartMenuTaskData *)TaskManager_GetEnvironment(taskManager);

    Heap_Free(startMenu->exitTaskEnvironment);
    FieldSystem_LoadFieldOverlay(fieldSystem);
    startMenu->state = START_MENU_STATE_RETURN;
    return FALSE;
}
```

`Task_StartMenu_WaitFade` and `Task_StartMenu_WaitApp` call the launch and return steps
as plain functions and ignore what they return. The touch/button check on return (§1)
reads `fieldSystem->menuInputState`; the retail apps update it through the
`menuInputStatePtr` in their args.

### A true eighth entry

Not attempted here. The free spot on the normal bottom screen is under Options (where the
Safari ball sits), but the numbers 7 and 8 are taken throughout: sprites 7/8, touch
resources 7/8, hitboxes 8/9 and menu positions 7/8 are the registered-item buttons, and
`lastTouchMenuInput` values 9, 10 and 11 mean "registered item 1/2" and "close the Dowsing
MCHN" to `FieldInput_Update`. Adding a slot means renumbering all of those, raising
`TOUCHSCREEN_MENU_NUM_ICONS`, and adding a row to `gTouchscreenMenuIconPositions`,
`gTouchscreenMenuIconHitboxes`, `gTouchscreenMenuIconNeighbors` and
`gTouchscreenMenuIconAnims`, an icon to `gTouchscreenMenuIcons`, and a palette slot in
`TouchscreenMenu_HighlightIcon`, plus the start-menu side (§2).

## 5. The touch-screen menu

[src/field/touchscreen_menu.c](../../src/field/touchscreen_menu.c) is the field's default
bottom-screen app (`BOTTOM_SCREEN_APP_TOUCHSCREEN_MENU`, one of the apps in
[src/field/bottom_screen_app.c](../../src/field/bottom_screen_app.c)). It runs as a
SysTask beside the field, not as a field task, and owns the bottom screen: the icons, their
labels, the MENU button, the two registered-item buttons, the running-shoes button, the
action button, and the Pokégear ring. It never launches anything. It reports what was
touched in `fieldSystem->lastTouchMenuInput`:

| Value | Touched |
|---|---|
| 1 | MENU |
| 2 + *n* | the icon at menu position *n* (the *n*-th shown icon) |
| 9, 10 | registered item 1, 2 |
| 11 | (set by the Dowsing MCHN) close the Dowsing MCHN |

In the field, a nonzero value opens the start menu (`fieldInput->menu`), and
`StartMenu_HandleTouchInput` then runs the touched entry in the same task. So a new
start-menu entry is a new icon; there is no separate button to wire up.

Its data, in [asm/touchscreen_menu_data.s](../../asm/touchscreen_menu_data.s):

- `gTouchscreenMenuIcons`: per icon id, `.short charFileId, msgId | 0x8000`. The high
  bit is "enabled", used for icons 7 and up; icons 0-6 use
  `FieldSystem_ShouldDrawStartMenuIcon` instead. Ids: 0 Pokédex, 1 Pokémon, 2 Bag
  (member 27 instead of 24 for a girl), 3 Pokégear, 4 Trainer Card, 5 Save, 6 Options,
  7 Retire, 10 the Bug Contest Pokémon, 11 CHAT,
  12 LOG; 13 is `TOUCHSCREEN_MENU_ICON_NONE`. 8 and 9 are disabled "BALL" placeholders.
- `gTouchscreenMenuLayouts`: per layout (`TouchscreenMenuLayout`, chosen by
  `TouchscreenMenu_GetLayout`), the icon in each slot. Normal: `0 1 2 3 4 5 6`. Safari:
  `7 0 1 2 3 4 6`. Bug Contest: `7 0 1 3 4 6 10`. Pal Park: `7 0 1 3 4 6 9`. Union Room
  (`TOUCHSCREEN_MENU_LAYOUT_4`, judging by its icons): `11 0 1 2 12 4 6`. Colosseum (`_5`): `1 2 4 6`. Battle
  Tower partner room: `1 4 6`.
- Slots 0-3 are the left column, 4-6 the right (`gTouchscreenMenuIconPositions`,
  `gTouchscreenMenuIconHitboxes`; hitbox 0 is MENU).

Each layout row lists, in order, exactly the entries the matching start-menu mask leaves
in, which is what keeps menu position *n* the same entry on both sides.

## 6. Pitfalls

- **The two lists must agree.** Position *n* is "the *n*-th shown icon" to the touch menu
  and "the *n*-th uninhibited action" to the start menu. Any change to one (an icon
  hidden by condition, an action added to the builder, a new layout) needs the matching
  change in the other.
- **`sActionToIconIndex` has 12 entries for 13 actions.** `START_MENU_ACTION_12` (LOG)
  reads past its end in retail. Give any new action its own entry; use 100 for "always
  available".
- **Returning `FALSE` after freeing.** A selection function that frees `startMenu` (the
  Retire pattern) must return `FALSE`; returning `TRUE` lets `Task_StartMenu` read the
  freed data.
- **Hidden ≠ inhibited.** `FieldSystem_ShouldDrawStartMenuIcon` hides an icon; it does
  not remove the action from `selectionToAction`. See "Changing when an entry appears".
- **Nothing opens before the Bag flag.** `FieldInput_Update` won't set `menu` until
  `FLAG_GOT_BAG` is set, whatever else is unlocked ([new-game.md](new-game.md)).
- **Member 64 is not the icons.** `start_menu.c` loads `a/0/1/4` member 64 for its
  cursor sprite, the top-screen arrow. The icons are members 18-48, loaded by
  `touchscreen_menu.c`.

## Where to look

| What | Where |
|---|---|
| menu task, states, entries, launch/return functions | [src/start_menu.c](../../src/start_menu.c) |
| `StartMenuTaskData`, `StartMenuIcon`, `StartMenuState` | [include/start_menu.h](../../include/start_menu.h) |
| unlock flags | `CheckGotMenuIconI` etc. in [src/sys_flags.c](../../src/sys_flags.c) |
| X and touch → `StartMenu_Init` | `FieldInput_Update`, `FieldInput_Process` in [src/field/field_control.c](../../src/field/field_control.c) |
| bottom-screen icons, D-pad, touch | [src/field/touchscreen_menu.c](../../src/field/touchscreen_menu.c) |
| icon, layout, hitbox and neighbour tables | [asm/touchscreen_menu_data.s](../../asm/touchscreen_menu_data.s) |
| bottom-screen apps, save screen | [src/field/bottom_screen_app.c](../../src/field/bottom_screen_app.c), [src/touch_save_app.c](../../src/touch_save_app.c) |
| labels | [files/msgdata/msg/msg_0196.json](../../files/msgdata/msg/msg_0196.json) |
| graphics | `files/a/0/1/4` ([graphics.md §4](graphics.md#4-changing-a-binary-archive)) |
| scripts from the menu | `StartScriptFromMenu`, `Script_ReopenStartMenuOnEnd` in [src/script_manager.c](../../src/script_manager.c) |
| launchers | [src/launch_application.c](../../src/launch_application.c) |
