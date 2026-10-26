<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# PC storage

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the Pokémon Storage System works: the box data in the save, how a Pokémon Center
PC opens the box screen, and how that screen is put together. The screen uses the
framework described in [ui.md](ui.md) (applications, BG layers, windows, sprites, grid
input); this guide only covers what is specific to the PC.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `struct PokemonStorage`, `gPokemonStoragePtr` | `PCStorage` (`struct PokemonStorageSystem`), the save chunk `SAVE_PCSTORAGE`, got with `SaveArray_PCStorage_Get(saveData)` |
| `TOTAL_BOXES_COUNT` (14), `IN_BOX_COUNT` (30) | `NUM_BOXES` (18), `MONS_PER_BOX` (30) |
| `GetBoxMonDataAt`, `GetBoxedMonPtr` | `PCStorage_GetMonDataByIndexPair`, `PCStorage_GetMonByIndexPair` |
| `SendMonToPC` | `PCStorage_PlaceMonInFirstEmptySlotInAnyBox` |
| `StorageGetCurrentBox`, `GetBoxNamePtr`, `SetBoxWallpaper` | `PCStorage_GetActiveBox`, `PCStorage_GetBoxName`, `PCStorage_SetBoxWallpaper` |
| `pokemon_storage_system.c` (data helpers and the UI in one file) | data: [src/pokemon_storage_system.c](../../src/pokemon_storage_system.c); UI: [src/application/pc_box/](../../src/application/pc_box/) (overlay 14) |
| `EnterPokeStorage(OPTION_*)` | script command `OpenPCBox mode` → `PCBox_LaunchApp` |

Differences: the screen spans both DS screens (box grid and buttons on the touch screen,
the selected Pokémon's details on the top screen), the box header opens a two-entry
menu (Wallpaper, Name), boxes are jumped to through a "box tray" of thumbnails, and
releasing a Pokémon scans every box for certain HM moves.

## 1. Storage data

Constants ([include/constants/pokemon.h](../../include/constants/pokemon.h)):

| Constant | Value | Meaning |
|---|---|---|
| `NUM_BOXES` | 18 | boxes |
| `MONS_PER_BOX` | 30 | slots per box (6 × 5) |
| `BOX_NAME_LENGTH` | 20 | `u16` characters stored per name (the naming screen allows 8) |

The struct ([include/pokemon_storage_system.h](../../include/pokemon_storage_system.h)):

```c
typedef struct PC_Box {
    BoxPokemon mons[MONS_PER_BOX];   // 30 × 136 bytes
    u8 unk_FF0[16];                  // padding: one box = 0x1000 bytes = one flash sector
} PC_BOX;

struct PokemonStorageSystem {
    /* 00000 */ PC_BOX boxes[NUM_BOXES];
    /* 12000 */ int curBox;
    /* 12004 */ u32 boxModifiedFlag;              // one bit per box, see "save" below
    /* 12008 */ u16 box_names[NUM_BOXES][BOX_NAME_LENGTH];
    /* 122D8 */ u8 wallpapers[NUM_BOXES];
    /* 122EA */ u8 unlockedWallpapers;            // bit n = bonus wallpaper n unlocked
    /* 122EB */ u8 filler_122EB[0x11];
};                                                // 0x122FC = 74,492 bytes
```

### Functions

All in [src/pokemon_storage_system.c](../../src/pokemon_storage_system.c). In most
functions that take `boxno`, `-1` means the current box (`curBox`); not all:
`PCStorage_SwapMonsInBoxByIndexPair` indexes `boxes[boxno]` directly, and
`PCStorage_GetBoxWallpaper` / `PCStorage_SetActiveBox` assert on anything ≥ `NUM_BOXES`.

| Function | Does |
|---|---|
| `PCStorage_PlaceMonInFirstEmptySlotInAnyBox(storage, boxMon)` | first empty slot, starting at the current box and wrapping; `FALSE` if all full ([:54](../../src/pokemon_storage_system.c#L54)) |
| `PCStorage_PlaceMonInBoxFirstEmptySlot(storage, box, boxMon)` | first empty slot of one box |
| `PCStorage_PlaceMonInBoxByIndexPair(storage, box, slot, boxMon)` | overwrite a slot |
| `PCStorage_SwapMonsInBoxByIndexPair`, `PCStorage_DeleteBoxMonByIndexPair` | swap two slots of a box; zero a slot |
| `PCStorage_GetMonByIndexPair`, `PCStorage_GetMonDataByIndexPair` | `BoxPokemon *` of a slot; `GetBoxMonData` on it |
| `PCStorage_FindFirstBoxWithEmptySlot` | box index, or `NUM_BOXES` if every box is full |
| `PCStorage_CountEmptySpotsInAllBoxes`, `PCStorage_CountEmptySpotsInBox` | free slots |
| `PCStorage_CountMonsAndEggsInBox`, `PCStorage_CountMonsInBox`, `PCStorage_CountMonsInAllBoxes` | occupied slots (the last two skip Eggs) |
| `PCStorage_GetActiveBox`, `PCStorage_SetActiveBox` | `curBox` |
| `PCStorage_GetBoxName`, `PCStorage_SetBoxName` | to and from a `String` |
| `PCStorage_GetBoxWallpaper`, `PCStorage_SetBoxWallpaper` | the box's wallpaper id (validated by `PCStorage_IsValidWallpaperId`) |
| `PCStorage_UnlockBonusWallpaper`, `PCStorage_IsBonusWallpaperUnlocked` | bit `n` of `unlockedWallpapers` |

All the place functions call `RestoreBoxMonPP` (a Pokémon put in a box gets full PP) and
mark the box modified. `PCStorage_FindFirstEmptySlot` returns `NUM_BOXES` instead of
`FALSE` when nothing is free (commented in the source; no caller uses the result).

### Box names and wallpapers

New-game names come from `msg_0024_00006 + i` ("BOX 1" to "BOX 18") in
[files/msgdata/msg/msg_0024.json](../../files/msgdata/msg/msg_0024.json)
(`PCStorage_InitializeBoxes`, [:23](../../src/pokemon_storage_system.c#L23)). Box `i`
starts with wallpaper `i % 16`.

Wallpaper ids ([include/constants/box_wallpaper.h](../../include/constants/box_wallpaper.h)):

| Ids | Wallpapers | Available |
|---|---|---|
| 0-15 (`WALLPAPER_FOREST` … `WALLPAPER_SIMPLE`) | 16 default | always |
| 32-39 (`WALLPAPER_HEART` … `WALLPAPER_REVIVAL`) | 8 bonus | when bit `id - 32` of `unlockedWallpapers` is set |

The only thing that unlocks bonus wallpapers is Primo's password in the Violet City
Pokémon Center: script command 498, `PrimoPasswordCheck1` (`ScrCmd_PrimoPasswordCheck1`,
[src/scrcmd_c.c:3588](../../src/scrcmd_c.c#L3588)) decodes four Easy Chat words with
`PrimoPassword_CheckWallpaper` ([src/field/primo_password.c](../../src/field/primo_password.c))
and calls `PCStorage_UnlockBonusWallpaper`. The `BONUS_WALLPAPER(name)` macro gives the
bit number (`BONUS_WALLPAPER(HEART)` is 0).

### Who puts Pokémon in the PC

| Caller | How |
|---|---|
| a catch with a full party (`Task_GetPokemon`, [src/battle/battle_command.c](../../src/battle/battle_command.c)) | `PCStorage_FindFirstBoxWithEmptySlot`, makes that box current, `PCStorage_PlaceMonInBoxFirstEmptySlot` |
| the Bug-Catching Contest ([src/overlay_bug_contest.c](../../src/overlay_bug_contest.c)) | `PCStorage_PlaceMonInFirstEmptySlotInAnyBox` |
| Pal Park migration (`ScrCmd_MoveMigratedPokemonToPC`, [src/scrcmd_12.c](../../src/scrcmd_12.c)) | the same, asserting it fits |
| the Pokéwalker (stroll and erase; [src/application/pokewalker/](../../src/application/pokewalker/)) | `PCStorage_FindFirstEmptySlot` |
| the GTS (trades and taking a Pokémon back; [src/gts/gts_trade.c](../../src/gts/gts_trade.c), [gts_transaction.c](../../src/gts/gts_transaction.c)) | `PCStorage_FindFirstEmptySlot` |
| script gifts (`givemon`) | **not** the PC: see [gift-pokemon-and-trades.md](gift-pokemon-and-trades.md) |

Scripts can read the free space with `CountPCEmptySpace VAR` (`ScrCmd_CountPCEmptySpace`).
When the boxes become completely full, `FieldSystem_TryTriggerBillPCFullCall`
([src/gear_phone_ring_manager.c:279](../../src/gear_phone_ring_manager.c#L279)) queues
Bill's phone call once (it needs Bill registered and `FLAG_SYS_GOT_BILL_PC_FULL_CALL`
clear). It is tried when the PC screen closes, after wild battles
([src/encounter.c](../../src/encounter.c)), when the Bug-Catching Contest ends
([src/field/scrcmd_pokemon_misc.c:1469](../../src/field/scrcmd_pokemon_misc.c#L1469)) and after migration.

### In the save

The PC is chunk 41 (`SAVE_PCSTORAGE`), alone in save block 1. Each `PC_BOX` is exactly one
4 KiB sector, and only boxes whose `boxModifiedFlag` bit is set are rewritten
(`Save_WriteNextPCBox` in [src/save.c](../../src/save.c)); the names, wallpapers and
flags after the boxes share the last sector with the block footer. Sizes, offsets and the
sector budget are in [save-data.md](save-data.md); what a layout change does to old
saves is in [save-compatibility.md](save-compatibility.md). Code that writes box data
directly (not through the `PCStorage_*` setters) must call `PCStorage_SetBoxModified`,
or the change is lost on the next save.

## 2. Opening the PC

1. Facing north at a tile whose behavior passes `MetatileBehavior_IsPC` returns
   `std_pokecenter_pc` (2010) from `GetInteractedMetatileScript` in
   [src/field/field_control.c](../../src/field/field_control.c). There is no
   per-map script.
2. 2010 is `scr_seq_0003_010` in
   [files/fielddata/script/scr_seq/scr_seq_0003.s](../../files/fielddata/script/scr_seq/scr_seq_0003.s).
   It builds the first menu: "SOMEONE'S PC" or "BILL'S PC" (`FLAG_SYS_MET_BILL`), the
   player's own PC (Mailbox, Ball Capsules, Photo Album), "HALL OF FAME" (only with `FLAG_GAME_CLEAR`), "SWITCH OFF".
   Texts are `msg_0191_00061`-`00066` and `msg_0040_00033`-`00036`.
3. The storage branch (label `_0B17`) adds DEPOSIT, WITHDRAW, MOVE POKéMON, MOVE ITEMS and
   SEE YA! (`msg_0191_00067`-`00072`), and each choice runs `OpenPCBox n`, then
   `RestoreOverworld`, then shows the menu again.
4. `ScrCmd_OpenPCBox` ([src/scrcmd_c.c:1994](../../src/scrcmd_c.c#L1994)) allocates the
   args with `PCBoxAppData_New` ([include/launch_application.h:100](../../include/launch_application.h#L100)),
   calls `PCBox_LaunchApp` ([src/launch_application.c:406](../../src/launch_application.c#L406))
   and waits in `ScrNative_WaitPCBox` ([:1772](../../src/scrcmd_c.c#L1772)), which then
   tries Bill's call and frees the args.

The args ([include/overlay_14.h](../../include/overlay_14.h)):

```c
typedef struct PCBoxArgs {
    SaveData *saveData;
    MenuInputStateMgr *menuInputStatePtr;   // buttons vs touch, kept between screens
    int mode;                               // the byte after OpenPCBox
} PCBoxArgs;
```

| `mode` | Constant ([pc_box_internal.h](../../include/application/pc_box/pc_box_internal.h)) | Starts in |
|---|---|---|
| 0 | `PC_BOX_MODE_DEPOSIT` | the party panel; pick a Pokémon, then a box from the tray |
| 1 | `PC_BOX_MODE_WITHDRAW` | the box; the chosen Pokémon goes to the end of the party |
| 2 | `PC_BOX_MODE_MOVE_POKEMON` | the box, with the party button and box tray tab |
| 3 | `PC_BOX_MODE_MOVE_ITEMS` | the box; held items are moved instead of Pokémon |

The script has a `Case 4` that runs `OpenPCBox 4`, but no menu entry ever returns 4, and
the screen has no mode 4 (for example `PCBox_CreateModeGridInput` has no case for it).
There is no "compare" mode.

Nothing comes back through the args: the screen edits the party, bag and `PCStorage` in
the save directly. On exit `PCBox_Exit` stores the box the player was looking at with
`PCStorage_SetActiveBox`. `PCBox_SaveMenuInputState` (called from `PCBox_State_Exit`,
the view teardown, which also runs before every sub-app) records whether the player was
using buttons or touch.

## 3. The screen

### Data and heaps

`PCBox_Init` ([src/application/pc_box/pc_box.c:77](../../src/application/pc_box/pc_box.c#L77))
creates `HEAP_ID_9` (64 KiB) and `PCBoxWork`: pointers to the args, `PCStorage`, `Party`,
`Bag` and options, plus game state: `activeBox`, `selectedSlot`, `trayBox`,
`partyPanelOpen`, `trayOpen`, the sub-app in progress. All graphics state is in
`PCBoxView` (`work->view`), allocated in `PCBox_State_Init` on `HEAP_ID_10` (512 KiB):
BG config, message data (`msg_0024`), 44 windows, the `BgCellManager` panels, 69 sprites,
the grid input handler, the icon cache and 18 box thumbnails. Both structs are in
[include/application/pc_box/pc_box_internal.h](../../include/application/pc_box/pc_box_internal.h).

The summary screen, the bag (to give an item) and the naming screen (to rename a box) are
run inside the PC as sub-apps (`gPCBoxSubApps`): the PC fades out, frees its whole view
(`PCBox_State_Exit`), runs the other overlay, then rebuilds everything from
`PCBox_State_Init`.

### The state machine

`PCBox_Main` calls `PCBox_RunStateMachine` ([pc_box_ui.c:2270](../../src/application/pc_box/pc_box_ui.c#L2270))
once per frame:

```c
*state = gPCBoxStateTable[*state](work);
if (*state == PC_BOX_STATE_EXIT) {
    return FALSE;
}
```

`enum PCBoxState` names the 179 entries of `gPCBoxStateTable`; each state function
returns the next state. The table itself is still assembly, in
[asm/overlay_14_state_dispatch_rodata_67.s](../../asm/overlay_14_state_dispatch_rodata_67.s),
together with the menus, window templates and grid layouts. The states fall into groups:

| Group | Examples | Role |
|---|---|---|
| plumbing | `INIT`, `TEARDOWN`, `WAIT_FADE`, `WAIT_UPDATE_FUNC`, `WAIT_BUTTON`, `HANDLE_YES_NO`, `START_SUB_APP` | build/free, wait for a fade, an animation, a key, a yes/no answer; jump to `work->nextState` |
| input, one per mode and panel | `MOVE_MODE_INPUT`, `MOVE_MODE_PARTY_INPUT`, `BOX_TRAY_INPUT`, `WITHDRAW_INPUT`, `DEPOSIT_INPUT`, `ITEM_MODE_INPUT`, `BOX_MENU_INPUT`, `WALLPAPER_MENU_INPUT` | read the grid input and pick the next state |
| `CHOOSE_*` | `CHOOSE_SUMMARY`, `CHOOSE_ITEM`, `CHOOSE_MARKING`, `CHOOSE_RELEASE`, `CHOOSE_WITHDRAW`, `CHOOSE_DEPOSIT` | an action-menu entry was picked |
| flows | `TRY_RELEASE` … `CANCEL_RELEASE`, the marking menu, the wallpaper menu, deposit box select, item swaps | multi-step actions |
| `END_CURSOR_SLIDE_TO_*`, `RESUME_*` | | return to an input state after an animation |

Animations run from VBlank: a state sets `view->updateFunc` (through
`PCBox_WaitForUpdateFunc`) and goes to `PC_BOX_STATE_WAIT_UPDATE_FUNC`, which continues
with `work->nextState` once the function returns `FALSE`. A yes/no prompt sets
`view->yesNoHandler`, a row of `gPCBoxYesNoHandlers` (`{yes, no}` functions): 0 take item,
1 release, 2 put item away, 3 exit, 4 continue.

### Slots, grid and cursor

One numbering is used everywhere for "slot": 0-29 the current box, 30-35 the party
(`PC_BOX_SLOT_PARTY_START`), `PC_BOX_SLOT_NONE` (0xFF) for nothing.
`PCBox_GetSlotBoxMon` / `PCBox_GetSlotMonData` / `PCBox_SetSlotMonData` hide the
difference. A target with bit 7 set means "column N of the box tray" (another box;
`PCBox_GetTargetBoxId`).

Input goes through a `GridInputHandler` built from `gPCBoxGridLayouts` (one layout per
mode and panel, chosen in `PCBox_CreateModeGridInput` and `PCBox_CreateGridInput`). In
Move Pokémon mode the positions are: 0-29 box slots, 30 the box header (opens the box
menu), 31/32 the arrows, 33 the party button, 34 the box tray tab, 35 exit, 36-40 the
action menu. Touch drags (`PCBox_FindTouchedBoxSlot` and friends) are checked before the
grid. The hand cursor is sprite 9; a picked-up Pokémon follows it
(`PCBox_AttachIconToCursor`, `view->cursorHolding`), and drops are done by
`PCBox_SetupMonMove` / `PCBox_ApplyMonMove`, which call the `PCStorage_*` functions
and `Party_*`.

There is no multi-select: one Pokémon at a time. To move a Pokémon to another box, open
the box tray (6 boxes per page) and drop it on a box.

### Pokémon icons

Sprites 25-60 are the 36 slot icons (`view->slotIcons[slot]` gives the sprite index,
which changes as icons move). Each has its own tile resource; the icon's frame is copied
in with `PCBox_LoadSpriteCharsMain` from `poketool/icongra/poke_icon` (`Boxmon_GetIconNaix`).
The three shared icon palettes are loaded once from the same archive
(`GetMonIconPlttNaix`, `PCBox_LoadMonIconResources`,
[pc_box_sprites.c:225](../../src/application/pc_box/pc_box_sprites.c#L225)), and each icon
picks one with `ManagedSprite_SetPaletteOverride(sprite, Boxmon_GetIconPalette(boxMon) + 3)`.
`PCBox_LoadBoxIconImages` caches a whole box's icon frames (`view->iconChars`) for the
scroll animation between boxes.

### The top screen: info panel

`PCBox_ShowSlotMonInfo` ([pc_box.c:1199](../../src/application/pc_box/pc_box.c#L1199))
fills a `PCBoxMonInfo` (`PCBox_CreateMonInfo`, [:1129](../../src/application/pc_box/pc_box.c#L1129):
species, held item, personality, types, ability, nature, markings, level, egg, gender,
moves) and draws it. `PCBox_PrintMonInfo` ([pc_box_text.c:404](../../src/application/pc_box/pc_box_text.c#L404))
prints into windows on `GF_BG_LYR_SUB_0`:

| Window | Shows | Text |
|---|---|---|
| 0 | species name | `msg_0024_00000` |
| 1 | nickname | `msg_0024_00001` |
| 2 | a glyph + level | `msg_0024_00090` |
| 4 | gender symbol | `msg_0024_00082` / `00083` |
| 5 | a glyph + regional or National Dex number | `msg_0024_00091` |
| 6, 7, 8 | nature, ability, held item (labels in 17-19) | `msg_0024_00085`, `00084`, `00086` |

Eggs show `???` (`msg_0024_00093`) for nature and ability. The picture
(sprites 2/3, double-buffered, `PCBox_ShowMonPic`), type icons (sprites 13/14) and
markings (`PCBox_DrawMarkings`) complete it. Below, a panel on `GF_BG_LYR_SUB_2` shows the
four moves (`PCBox_DrawMoveWindows`, windows 9-12 or 13-16); in Move Items mode it shows
the item's name and description instead (`PCBox_PrintItemNameAndDesc`). Window 3 is the
mode title (`msg_0025_00050 + mode`).

### The box: header, wallpaper, tray

The box grid is on `GF_BG_LYR_MAIN_3`. The wallpaper is loaded by
`PCBox_LoadScrolledWallpaper` from `a/0/1/9`: tiles from member `16 + n`, palette from
`40 + n`, and one tilemap (member 15) shared by every wallpaper; the box name is printed
onto the wallpaper's tiles (`PCBox_DrawBoxNameOnWallpaper`). `n` is the UI index
from `PCBox_GetWallpaperGfxIndex`: 0-15 for default wallpapers, 16-23 for bonus ids 32-39.

Touching the header opens the box menu: WALLPAPER (`msg_0024_00026`) and NAME (`00027`).
The wallpaper list (`PCBox_State_OpenWallpaperMenu` …) shows 4 per page, 24 in all;
locked bonus wallpapers show `－` (`msg_0024_00059`), a gray thumbnail, and can't be
picked (`PCBox_ConfirmWallpaperChoice`). NAME runs the naming screen sub-app
(`PCBox_StartNamingScreenApp`, 8 characters). The box tray shows 6 thumbnails per page
(`view->boxThumbnails`, drawn by `PCBox_DrawBoxThumbnail`) with the name and an
"n/30" count.

### The action menu

Picking a Pokémon slides in up to 5 buttons, drawn by `PCBox_DrawActionMenu(work, list, count)`
([pc_box_text.c:708](../../src/application/pc_box/pc_box_text.c#L708)) from a list of
`PCBoxMenuEntry { u16 msgId; u16 kind; }` (`kind` 1 = tab style). The last entry goes in
window `0x21`, the one before in `0x20`, and so on; unused windows are cleared. The three lists are in the
assembly file:

| List | Entries (`msg_0024_*`) |
|---|---|
| `gPCBoxMoveMenu` (5) | MOVE (`00061`, tab), SUMMARY (`00065`), HELD ITEMS (`00066`), MARKING (`00067`), RELEASE (`00068`) |
| `gPCBoxWithdrawMenu` (4) | WITHDRAW (`00069`), SUMMARY, MARKING, RELEASE |
| `gPCBoxDepositMenu` (4) | DEPOSIT (`00070`), SUMMARY, MARKING, RELEASE |

The list only draws the buttons. What a button does is decided by its grid position in
the mode's input state; for Move Pokémon, `PCBox_State_MoveModeInput`
([pc_box_states.c:306](../../src/application/pc_box/pc_box_states.c#L306)):

```c
case 37:
    PlaySE(SEQ_SE_DP_DECIDE);
    work->returnCursorPos = 0x25;
    return PCBox_FlashPanel(work, 4, PC_BOX_STATE_CHOOSE_SUMMARY);
...
case 40:
    PlaySE(SEQ_SE_DP_DECIDE);
    return PCBox_FlashPanel(work, 7, PC_BOX_STATE_CHOOSE_RELEASE);
```

Move Items mode has no action menu: the item itself is picked up and dropped, and a
BAG/GIVE button (`PCBox_DrawBagGiveButton`) handles the bag.

### Move and release rules

`PCBox_CanMoveMon` ([pc_box.c:666](../../src/application/pc_box/pc_box.c#L666)) refuses a
move that would leave the party without a non-Egg Pokémon with HP
(`PCBox_PartyHasOtherUsableMon`), or put a Pokémon holding Mail or a Ball Capsule into a
box. A Shaymin put into a box reverts to Land Forme. Item swaps
(`PCBox_CanSwapHeldItems`) refuse Eggs, Mail, and the Griseous Orb on anything but
Giratina. A party Pokémon put into a box has its mood (`MON_DATA_MOOD`) reset to 0.

Release (`PCBox_State_TryRelease`, [pc_box_states.c:774](../../src/application/pc_box/pc_box_states.c#L774)):

| Check | Message (`msg_0025`) |
|---|---|
| party Pokémon and no other usable party member | "That's your last Pokémon!" (`00006`) |
| party Pokémon holding Mail / a Ball Capsule | `00030` / `00029` |
| an Egg | "You can't release an Egg." (`00031`) |
| otherwise | "Release this Pokémon?" (`00002`), yes/no |

On yes, `PCBox_ConfirmRelease` starts the icon shrinking and `PCBox_StartReleaseMoveCheck`
([pc_box.c:1052](../../src/application/pc_box/pc_box.c#L1052)). The moves checked are
`gPCBoxReleaseCheckMoves`: `MOVE_SURF`, `MOVE_ROCK_CLIMB`, `MOVE_WATERFALL`, `MOVE_FLY`.
Only the **first** of these in the Pokémon's move list is recorded (the loop returns after
one). `PCBox_RunReleaseMoveCheck` then scans every box slot and the party, 15 per frame,
clearing the bit when another Pokémon knows that move. If the bit is still set when the
40-frame shrink ends, the Pokémon "came back!" and "Was it worried about you?". Otherwise
it is deleted with `PCBox_DeleteSlotMon`; its held item is lost with it.

## 4. How-tos

### Changing the number of boxes

It is possible, but it changes the save layout (old saves won't load without a migration,
[save-compatibility.md](save-compatibility.md) §6). What has to change:

1. `NUM_BOXES` in [include/constants/pokemon.h](../../include/constants/pokemon.h).
2. **Save sectors.** Each box is one more 4 KiB sector in block 1. The current layout
   fills `SAVE_PAGE_MAX` (35, [include/constants/save_arrays.h](../../include/constants/save_arrays.h))
   and the last PC sector only has 3,312 bytes free, so even one more box needs
   `SAVE_PAGE_MAX` raised: see "Raising `SAVE_PAGE_MAX`" in [save-data.md](save-data.md)
   (at most 52, i.e. 17 more boxes, with heap costs).
3. **Modified flags.** `boxModifiedFlag` is a `u32`, and `BOX_ALL_MODIFIED_FLAG` is
   `(1 << NUM_BOXES) - 1`: keep `NUM_BOXES` at 31 or below.
4. **Default names.** `PCStorage_InitializeBoxes` reads `msg_0024_00006 + i`; message 24
   onward is other text, so box 19 would get the wrong name. Append new names at the end
   of `msg_0024.json` (don't insert: `PCBox_DrawWallpaperName` uses `wallpaperSelection + 0x23`
   as a raw id) and read them from there for `i >= 18`.
5. **The screen.** `PCBoxView.boxThumbnails[18][0x400]` → `[NUM_BOXES]` (1 KiB each, on
   `HEAP_ID_10`). The tray works in pages of 6, so keep `NUM_BOXES` a multiple of 6;
   `PCBox_ChangeTrayPage` ([pc_box_states.c:3748](../../src/application/pc_box/pc_box_states.c#L3748))
   wraps with the literal `0x12` and must use `NUM_BOXES`.
6. **Release check.** 15 slots per frame × 40 frames = 600 slots, and the scan covers
   `NUM_BOXES * MONS_PER_BOX + PARTY_SIZE`. Above 19 boxes the check ends unfinished and
   a Pokémon may "come back" wrongly; raise the `15` in `PCBox_RunReleaseMoveCheck`.
7. **Other code with 18 written out:** `BtlCmd_CheckSafariGameDone`
   ([src/battle/battle_command.c:5665](../../src/battle/battle_command.c#L5665)) compares
   with `18`; `BOX_MON_SELECTOR_PARTY_PAGE` is 18
   ([include/box_mon_selector.h:20](../../include/box_mon_selector.h#L20), Pokéwalker and
   Pokéathlon box pickers). `grep -rn 'NUM_BOXES'` for the rest (GTS, Pokéwalker, VS
   Recorder, lottery); they use the constant but check that their own screens can page
   through more boxes.

Fewer boxes is the same list in reverse, and frees sectors.

### Adding a wallpaper

There is room for none without code changes. The 24 wallpapers (16 + 8 bonus) are
assumed in several places:

- **Graphics**, `a/0/1/9`: tiles `16 + n` and palettes `40 + n` are contiguous and
  followed by other members (64 and 65 are window graphics), so a 25th wallpaper has to be
  appended at the end of the archive (member 87 on), and `PCBox_LoadWallpaperChars`,
  `PCBox_LoadWallpaperPalette` and `PCBox_SwapWallpaper` need a lookup instead of
  `member + 0x10` / `member + 0x28`. The new tiles must fit the shared tilemap (member 15),
  with the name area at byte `0x2A0` of the tiles. The archive is prebuilt; unpack and
  repack it as in [graphics.md](graphics.md) §4.
- **Thumbnails**: `PCBox_ColorWallpaperThumbnail` colors 8-bit thumbnail pixels with
  index `n + 16` of the thumbnail palettes (members 71 and 75); index 40 is the gray of a
  locked wallpaper, so UI index 24 would collide with it.
- **Menu**: `PCBox_WallpaperGridOnKeyMove` and `PCBox_ChangeWallpaperPage` wrap at 24
  (`23`, `0x18`); keep the count a multiple of 4.
- **Name**: `PCBox_DrawWallpaperName` prints `msg_0024` id `n + 0x23`; message 59 follows
  REVIVAL, so new names need their own ids.
- **Ids**: add `WALLPAPER_*` in [box_wallpaper.h](../../include/constants/box_wallpaper.h)
  and extend `PCStorage_IsValidWallpaperId`; `PCStorage_SetBoxWallpaper` asserts on
  anything else. The UI maps index ≥ 16 to id `index + 16` (`PCBox_State_ApplyWallpaper`)
  and back (`PCBox_GetWallpaperGfxIndex`). Up to 8 bonus wallpapers fit
  `unlockedWallpapers` (a `u8`).

Replacing an existing wallpaper's picture is only the graphics step.
Unlocking a bonus wallpaper from a script needs a new script command calling
`PCStorage_UnlockBonusWallpaper` ([script-commands.md](script-commands.md)).

### Showing more in the info panel

Example: show the sum of the six IVs. Data goes in `PCBoxMonInfo`, printing in
`PCBox_PrintMonInfo`, and the text needs a window. This was compiled (not run); the
window position is an example to adjust on screen.

1. In [pc_box_internal.h](../../include/application/pc_box/pc_box_internal.h): add
   `u16 ivTotal;` at the end of `PCBoxMonInfo`, make `Window windows[0x2C]` `[0x2D]`, and
   `#define PC_BOX_WINDOW_IV_TOTAL 44`.
2. In `PCBox_CreateMonInfo` (pc_box.c), after the moves loop:

   ```c
   monInfo->ivTotal = 0;
   for (i = 0; i < NUM_STATS; i++) {
       monInfo->ivTotal += GetBoxMonData(boxMon, MON_DATA_HP_IV + i, NULL);
   }
   ```

3. In pc_box_text.c: create the window after the template loop in `PCBox_AddWindows`
   and remove it in `PCBox_RemoveWindows`. The `GF_BG_LYR_SUB_0` windows use tiles
   `0x0F`-`0x120`, so start at `0x121`:

   ```c
   AddWindowParameterized(work->view->bgConfig, &work->view->windows[PC_BOX_WINDOW_IV_TOTAL],
       GF_BG_LYR_SUB_0, 16, 21, 10, 2, 15, 0x121);   // x, y, width, height (tiles), palette, base tile
   ```

4. A print function, called at the end of `PCBox_PrintMonInfo`; also add the window to
   `PCBox_ClearMonInfoWindows`:

   ```c
   static void PCBox_PrintIvTotal(PCBoxView *view, PCBoxMonInfo *monInfo, u32 win) {
       FillWindowPixelBuffer(&view->windows[win], 0);
       if (!monInfo->isEgg) {
           BufferIntegerAsString(view->msgFormat, 0, monInfo->ivTotal, 3, PRINTING_MODE_LEFT_ALIGN, TRUE);
           PCBox_PrintExpandedMsg(view, view->msgData, win, msg_0024_00094, 0, 0, FONT_SYSTEM, 0x10200, 0);
       }
       ScheduleWindowCopyToVram(&view->windows[win]);
   }
   ```

5. Append `{"id": "msg_0024_00094", "en_US": "IVs {STRVAR_1 52, 0, 0}"}` to
   [msg_0024.json](../../files/msgdata/msg/msg_0024.json) (`STRVAR_1 52` is the number
   format the level line uses; see [text-and-messages.md](text-and-messages.md)).

Nature is already shown (window 6). For something that belongs with the moves, the moves
panel windows on `GF_BG_LYR_SUB_2` are filled in `PCBox_DrawMoveWindows`.

### Adding or changing an action-menu entry

The menu has 5 button windows (`0x1D`-`0x21`), 5 panel cells and grid positions 36-40 in
Move Pokémon mode, and Move Pokémon already uses all five. So:

- **Replacing** an entry needs no assembly. Write your own list in C and pass it instead
  of `gPCBoxMoveMenu` (it is drawn from `PCBox_State_MoveModeInput`,
  `PCBox_State_ReturnToActionMenu`, `PCBox_State_ReturnFromSummary` and others: grep
  `gPCBoxMoveMenu`), then change what that grid position does in
  `PCBox_State_MoveModeInput`:

  ```c
  static const PCBoxMenuEntry sMoveMenu[] = {
      { msg_0024_00061, 1 },   // MOVE (tab)
      { msg_0024_00065, 0 },   // SUMMARY
      { msg_0024_00066, 0 },   // HELD ITEMS
      { msg_0024_00094, 0 },   // your entry, in place of MARKING (grid position 39)
      { msg_0024_00068, 0 },   // RELEASE
  };
  ```

- **A new state** for the action: add a name at the end of `enum PCBoxState`, append
  the function to `gPCBoxStateTable` in the assembly file, and raise `PC_BOX_STATE_EXIT`
  (0xB3 = 179, which is the table's length, so the new state would otherwise be read as
  "exit"). Declare the function returning `u32` and return a state; several retail
  `CHOOSE_*` functions are `void` and only work because of what is left in `r0`.
- **A sixth entry**, or a fifth in Withdraw/Deposit (their layouts only have positions
  for 4), needs a new window template, a new panel cell (`PCBox_InitPanels`), new
  positions in `gPCBoxGridLayouts` and changes to `PCBox_GetMoveModeMenuInput`'s ranges.
  This is all in the assembly data and is not worked through here.

### Changing release rules

- **Allow releasing Eggs**: remove the `MON_DATA_IS_EGG` block in `PCBox_State_TryRelease`.
- **Drop the HM check**: return from `PCBox_StartReleaseMoveCheck` with `r->moveFlags = 0`
  (keep the allocation; the shrink animation uses `releaseWork`).
- **Other moves**: `gPCBoxReleaseCheckMoves` is four `u16` in the assembly file
  (`.byte 0x39, 0x00, 0xAF, 0x01, ...`). Edit them there, or move the list to C and
  change `PCBox_GetReleaseCheckMoveIndex`'s `4`; `moveFlags` is a `u8`, so at most 8.
  To check every listed move rather than the first, remove the `return` in the loop of
  `PCBox_StartReleaseMoveCheck`.
- **Return the held item**: call `Bag_AddItem` with the slot's `MON_DATA_HELD_ITEM`
  before `PCBox_DeleteSlotMon` in `PCBox_State_RemoveReleasedMon` (and decide what happens
  when the bag is full).

## 5. Pitfalls

- Writing `storage->boxes[...]` directly without `PCStorage_SetBoxModified`: the
  change is in RAM but the next save skips that box.
- Many arrays and literals assume 18 boxes, 30 slots, 24 wallpapers, 4 menu entries per
  page, 6 boxes per tray page; see §4. Grep for `NUM_BOXES`, `18`, `0x12`, `24`, `0x18`
  in `src/application/pc_box/`.
- The menus, window templates, grid layouts and state table are bytes in
  [asm/overlay_14_state_dispatch_rodata_67.s](../../asm/overlay_14_state_dispatch_rodata_67.s);
  enum values and table rows must stay in step by hand.
- Adding fields to `PCBoxView` is fine (it is allocated with `sizeof`), but `HEAP_ID_10`
  is 512 KiB and also holds the graphics loaded while the screen runs.
- `msg_0024` and `msg_0025` ids are partly computed (`n + 0x23` for wallpaper names,
  `mode + 0x32` for titles): append messages, never insert.
- After a summary/bag/naming sub-app the whole view is rebuilt from `PCBox_State_Init`; any
  state you keep across it must live in `PCBoxWork`, not `PCBoxView`.
- Not verified here: the exact screen positions of free space on the top screen, and
  which `a/0/1/9` members are the thumbnail palettes beyond what the loaders show.

## Where to look

| What | File | Shows |
|---|---|---|
| Box data | [src/pokemon_storage_system.c](../../src/pokemon_storage_system.c), [include/pokemon_storage_system.h](../../include/pokemon_storage_system.h) | struct, place/find/count, names, wallpapers |
| Constants | [include/constants/pokemon.h](../../include/constants/pokemon.h), [include/constants/box_wallpaper.h](../../include/constants/box_wallpaper.h) | box counts, wallpaper ids |
| PC menu script | [files/fielddata/script/scr_seq/scr_seq_0003.s](../../files/fielddata/script/scr_seq/scr_seq_0003.s) (`scr_seq_0003_010`) | the PC menus, `OpenPCBox` |
| Launch | [src/scrcmd_c.c](../../src/scrcmd_c.c) (`ScrCmd_OpenPCBox`), [src/launch_application.c](../../src/launch_application.c), [include/overlay_14.h](../../include/overlay_14.h) | args and waiting |
| App entry, data access, moves, release, info, wallpaper loading | [src/application/pc_box/pc_box.c](../../src/application/pc_box/pc_box.c) | `PCBox_Init`, `PCBox_CanMoveMon`, `PCBox_RunReleaseMoveCheck`, `PCBox_CreateMonInfo` |
| States | [src/application/pc_box/pc_box_states.c](../../src/application/pc_box/pc_box_states.c) | every `PCBox_State_*` |
| Panels, sub-apps, drags | [src/application/pc_box/pc_box_ui.c](../../src/application/pc_box/pc_box_ui.c) | `PCBox_InitPanels`, `PCBox_StartNamingScreenApp` |
| Sprites | [src/application/pc_box/pc_box_sprites.c](../../src/application/pc_box/pc_box_sprites.c) | icons, picture, thumbnails, release animation |
| Text | [src/application/pc_box/pc_box_text.c](../../src/application/pc_box/pc_box_text.c) | info panel, action menu, messages |
| Grid callbacks | [src/application/pc_box/pc_box_grid_input.c](../../src/application/pc_box/pc_box_grid_input.c) | per-mode input, tray and wallpaper paging |
| Structs, enums | [include/application/pc_box/pc_box_internal.h](../../include/application/pc_box/pc_box_internal.h) | `PCBoxWork`, `PCBoxView`, `enum PCBoxState` |
| Tables | [asm/overlay_14_state_dispatch_rodata_67.s](../../asm/overlay_14_state_dispatch_rodata_67.s) | state table, menus, windows, grid layouts, release moves |
| Text | [msg_0024.json](../../files/msgdata/msg/msg_0024.json), [msg_0025.json](../../files/msgdata/msg/msg_0025.json), [msg_0191.json](../../files/msgdata/msg/msg_0191.json) | labels, box messages, PC menu |
| Save | [save-data.md](save-data.md), [save-compatibility.md](save-compatibility.md), [game-limits.md](game-limits.md) | chunk size, sectors, migrating |
