<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# How the UI works

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How menus and screens are built in HeartGold/SoulSilver: the application
lifecycle, backgrounds and windows, text, menus, sprites and input. The worked
example throughout is the Options menu, [src/options_app.c](../../src/options_app.c),
which is about 1,000 lines and uses every piece.

If you know pokeemerald, most ideas carry over:

| pokeemerald | here |
|---|---|
| `SetMainCallback2(CB2_...)` and a state switch | an **application**: `init` / `exec` / `exit` functions run by an `OverlayManager` |
| `gMain.newKeys`, `gMain.heldKeys` | `gSystem.newKeys`, `gSystem.heldKeys`, plus `gSystem.touchNew` / `touchX` / `touchY` |
| `InitBgsFromTemplates`, `BgTemplate` | `BgConfig_Alloc` + `InitBgFromTemplate` per layer, `BgTemplate` |
| `AddWindow`, `WindowTemplate`, `CopyWindowToVram` | the same names (`bg_window.h`) |
| `AddTextPrinterParameterized` | the same name (`text.h`), but it prints a `String`, not a `u8 *` |
| `ListMenuInit`, `ListMenuTemplate` | the same, ported from Gen 3 (`list_menu.h`) |
| `CreateSprite`, `SpriteTemplate`, `LoadSpriteSheet` | `SpriteSystem` / `SpriteManager` with NARC resources (`sprite_system.h`) |
| `gStringVar1`, `StringExpandPlaceholders` | `MessageFormat` + `BufferString` / `BufferSpeciesName` + `StringExpandPlaceholders` |
| text in `.inc` files | text in `files/msgdata/msg/*.json` (msgenc), read with `MsgData` |

What is different on the DS: there are **two screens**, each with its own 2D
engine (main = A, sub = B), its own four BG layers, its own sprites and palettes;
the bottom screen takes touch input; and screen code lives in **overlays** that
are loaded only while the screen is open.

## 1. Applications

An application (the game also calls it an "overlay" or a "proc") is three
functions and an overlay id ([include/overlay_manager.h](../../include/overlay_manager.h)):

```c
typedef int (*OverlayFunction)(OverlayManager *manager, int *state);

typedef struct OverlayManagerTemplate {
    OverlayFunction init;
    OverlayFunction exec;
    OverlayFunction exit;
    FSOverlayID ovy_id;   // FS_OVERLAY_ID(options_app), or FS_OVERLAY_ID_NONE
} OverlayManagerTemplate;
```

`OverlayManager_Run` ([src/overlay_manager.c](../../src/overlay_manager.c)) calls
them once per frame:

1. Loads the overlay `ovy_id`.
2. Calls `init` every frame until it returns `TRUE`.
3. Calls `exec` every frame until it returns `TRUE`.
4. Calls `exit` until it returns `TRUE`, then unloads the overlay.

Each function gets a `state` counter (reset to 0 between phases) that it can use
for its own `switch`. Returning `FALSE` means "call me again next frame". This is
the only way to wait: **never loop waiting for something inside one call**;
return `FALSE` and check again next frame.

Data an application needs:

- **Arguments** from whoever launched it: `OverlayManager_GetArgs(man)`. The caller
  owns them and reads results back from them after the app ends (the Options
  menu writes the new settings through `args->options`).
- **Its own state**: `OverlayManager_CreateAndGetData(man, sizeof(MyData), heapID)`
  in `init`, `OverlayManager_GetData(man)` afterwards,
  `OverlayManager_FreeData(man)` in `exit`.
- **A heap**: apps create their own heap in `init` and destroy it in `exit`, so
  that leaks can't outlive the screen:

  ```c
  Heap_Create(HEAP_ID_3, HEAP_ID_OPTIONS_APP, 0x30000);   // parent heap, new id, size
  ...
  Heap_Destroy(HEAP_ID_OPTIONS_APP);
  ```

  Heap ids are an enum in [include/constants/heap.h](../../include/constants/heap.h);
  a new app adds its own id there.

### The Options menu's three functions

- `OptionsMenu_Init`: creates the heap and data, copies the current options out
  of the save, sets both screens to black. Returns `TRUE` at once.
- `OptionsMenu_Main` (the `exec`): a state machine in `data->exitState`:

  | State | What happens |
  |---|---|
  | 0 | `OptionsApp_Setup` (itself 3 frames: hardware, graphics, windows/text/sprites); start a fade in |
  | 1 | wait for the fade |
  | 2 | handle input each frame until the player confirms or cancels |
  | 3 | wait for the button animation; start a fade out |
  | 4 | wait for the fade |
  | 5 | `OptionsApp_Free`; return `TRUE` |

- `OptionsMenu_Exit`: on confirm, writes the settings back to the save; frees the
  data and destroys the heap.

Setup and teardown are split over several frames on purpose: loading graphics
and building windows takes time, and spreading it out keeps each frame short.

### Launching an application

**From the field.** The field runs at most one application at a time "on top of"
the overworld ([src/field_system.c](../../src/field_system.c)). The overworld map
itself is an application (`parent`); a launched screen is the `child`. Launching
sets `runningFieldMap = FALSE`, the map's `exec` sees that and closes, and only
then does the child start. After the child ends, the caller reloads the map with
`FieldSystem_LoadFieldOverlay`.

Each screen has a launcher in [src/launch_application.c](../../src/launch_application.c):

```c
static void OptionsMenu_LaunchApp_Impl(FieldSystem *fieldSystem, OptionsMenuArgs *args) {
    static const OverlayManagerTemplate sOverlayTemplate_OptionsMenu = {
        OptionsMenu_Init, OptionsMenu_Main, OptionsMenu_Exit, FS_OVERLAY_ID(options_app)
    };
    FieldSystem_LaunchApplication(fieldSystem, &sOverlayTemplate_OptionsMenu, args);
}

OptionsMenuArgs *OptionsMenu_LaunchApp(FieldSystem *fieldSystem) {
    OptionsMenuArgs *args = Heap_AllocAtEnd(HEAP_ID_FIELD2, sizeof(OptionsMenuArgs));
    args->options = Save_PlayerData_GetOptionsAddr(FieldSystem_GetSaveData(fieldSystem));
    args->menuInputStatePtr = &fieldSystem->menuInputState;
    OptionsMenu_LaunchApp_Impl(fieldSystem, args);
    return args;
}
```

The caller is a field **task** (a function run every frame by the field's task
manager, `TaskManager_Call` / `FieldSystem_CreateTask` in
[src/task.c](../../src/task.c)). The start menu's sequence for Options
([src/start_menu.c](../../src/start_menu.c)):

1. `FieldMap_FadeScreen(FADE_TYPE_BRIGHTNESS_OUT)`, wait for the fade.
2. `OptionsMenu_LaunchApp(fieldSystem)`.
3. Wait until `!FieldSystem_ApplicationIsRunning(fieldSystem)`.
4. Free the args, `FieldSystem_LoadFieldOverlay(fieldSystem)`, wait for
   `FieldSystem_IsOverworldRestored`, fade back in.

For a task that only needs to run a screen and wait,
`CallApplicationAsTask(taskManager, &template, args)` does steps 2-3.

**From a script.** A script command calls a launcher and then waits, usually
with `SetupNativeScript` and a function that returns `TRUE` when the app is done.
`ScrCmd_*` functions in [src/scrcmd*.c](../../src/) that call `*_LaunchApp` show
the pattern.

**Outside the field** (title screen, intro, new game): `RegisterMainOverlay` in
[src/main.c](../../src/main.c) queues the next top-level application; the field
itself is one (`Field_NewGame_AppInit` / `Field_AppExec` / `Field_AppExit`).

### Adding a new application

1. Write `MyApp_Init`, `MyApp_Main`, `MyApp_Exit` in a new `src/my_app.c`.
2. Give it an overlay: add the file to [src/meson.build](../../src/meson.build),
   an `Overlay my_app { After main  Object main.nef.p/src_my_app.c.o }` block to
   [main.lsf](../../main.lsf) (next to `options_app`), and `my_app.sbin_LZ` to
   the overlay list in [meson.build](../../meson.build). `FS_OVERLAY_ID(my_app)`
   then names it. A small screen can skip this and use `FS_OVERLAY_ID_NONE`,
   at the cost of ARM9 space that is always loaded.
3. Add a heap id to `include/constants/heap.h`.
4. Add a launcher to `src/launch_application.c` and call it from a task or
   script command.

## 2. One frame

The main loop in [src/main.c](../../src/main.c) does, every frame:

1. Read buttons and the touch screen into `gSystem` (§7).
2. Run the current application (`OverlayManager_Run`).
3. Run the system task queues (`SysTask`: small per-frame jobs such as text
   printers and fades).
4. Wait for **VBlank**, then call the VBlank callback, update sound, run the
   VBlank task queue.

Changing video memory is only safe during VBlank. So screens prepare changes in
RAM buffers during the frame, and copy them in their VBlank callback, installed
with `Main_SetVBlankIntrCB(callback, data)` and removed with
`Main_SetVBlankIntrCB(NULL, NULL)`. The Options menu's callback:

```c
static void OptionsApp_OnVBlank(OptionsApp_Data *data) {
    ...
    SpriteSystem_TransferOam();             // sprite attributes -> OAM
    NNS_GfdDoVramTransfer();                // queued graphics transfers
    DoScheduledBgGpuUpdates(data->bgConfig); // scheduled tilemap / scroll updates
    OS_SetIrqCheckFlag(OS_IE_V_BLANK);
}
```

## 3. Video setup

Each screen starts by taking over the hardware, because the previous screen left
it in its own state (`OptionsApp_Setup`, case 0):

```c
Main_SetVBlankIntrCB(NULL, NULL);
HBlankInterruptDisable();
GfGfx_DisableEngineAPlanes();
GfGfx_DisableEngineBPlanes();
GX_SetVisiblePlane(GX_PLANEMASK_NONE);
GXS_SetVisiblePlane(GX_PLANEMASK_NONE);
GfGfx_SetBanks(&banks);                 // which VRAM banks hold BG / OBJ data
GX_SetDispSelect(GX_DISP_SELECT_SUB_MAIN);
```

- **VRAM banks** (`GraphicsBanks`): which of the DS's banks A-I back the main and
  sub BG and sprite memory. Options: BG main 128 KB (bank A), BG sub 128 KB
  (C), sprites main 16 KB (G), sprites sub 16 KB (I).
- **Which screen is "main"**: `GX_SetDispSelect`. `GX_DISP_SELECT_SUB_MAIN`
  puts the main engine on the bottom screen (the touch screen). Options does
  this, so its interactive layers are on the bottom.
- **Modes** (`GraphicsModes` + `SetBothScreensModesAndDisable`): BG mode 0 is
  four text (tile) layers per screen. `_2d3dMode` says whether main BG0 is a 2D
  layer or the 3D output; screens with 3D (the starter choice, the field) use
  `GX_BG0_AS_3D`.

Teardown does the same steps in reverse (`OptionsApp_Free`).

## 4. Backgrounds and windows

### BG layers

`BgConfig` ([include/bg_window.h](../../include/bg_window.h)) holds up to eight
layers: `GF_BG_LYR_MAIN_0..3` and `GF_BG_LYR_SUB_0..3`. Each is set up from a
`BgTemplate`:

| Field | Meaning |
|---|---|
| `size` | `GF_BG_SCR_SIZE_256x256` etc. |
| `colorMode` | `GX_BG_COLORMODE_16` (4bpp, 16-color palettes) or 256 |
| `screenBase`, `charBase` | where the tilemap and tiles sit in BG VRAM |
| `bufferSize` | RAM copy of the tilemap (0x800 for 256×256) |
| `priority` | 0 drawn on top |
| `x`, `y` | scroll |

```c
data->bgConfig = BgConfig_Alloc(heapID);
InitBgFromTemplate(data->bgConfig, GF_BG_LYR_MAIN_1, &template, GF_BG_TYPE_TEXT);
BgClearTilemapBufferAndCommit(data->bgConfig, GF_BG_LYR_MAIN_1);
...
FreeBgTilemapBuffer(data->bgConfig, GF_BG_LYR_MAIN_1);   // on teardown, each layer
Heap_Free(data->bgConfig);
```

Two layers on the same screen must not overlap in VRAM: give each its own
`screenBase`, and a `charBase` that leaves room for the tiles of the layers
below it.

Useful calls: `ToggleBgLayer(layer, GF_PLANE_TOGGLE_ON/OFF)`,
`BgSetPosTextAndCommit(bgConfig, layer, BG_POS_OP_SET_Y, y)` (scroll; Options
moves its selection border this way), `ScheduleBgTilemapBufferTransfer` (copy
the RAM tilemap at the next VBlank).

### Loading graphics

Background art is in NARC archives (`files/a/...`), addressed by archive and
member number. `gf_gfx_loader.h`:

```c
GfGfxLoader_GXLoadPal(NARC_a_0_7_2, 3, GF_PAL_LOCATION_SUB_BG, GF_PAL_SLOT_0_OFFSET, 0x40, heapID); // palette
GfGfxLoader_LoadCharData(NARC_a_0_7_2, 8, bgConfig, GF_BG_LYR_SUB_0, 0, 0, FALSE, heapID);          // tiles
GfGfxLoader_LoadScrnData(NARC_a_0_7_2, 19, bgConfig, GF_BG_LYR_SUB_0, 0, 0, FALSE, heapID);         // tilemap
```

The `FALSE` is "compressed". Many archives have a generated `.naix` header with
names for their members; `a/0/7/2` here uses bare numbers.

### Windows

A window is a rectangle of a BG layer, in tiles, with its own pixel buffer in RAM.
Text and pictures are drawn into the buffer and then copied to VRAM.

```c
AddWindowParameterized(bgConfig, &window, GF_BG_LYR_MAIN_1,
                       1, 3,        // left, top (tiles)
                       30, 18,      // width, height (tiles)
                       13,          // palette slot
                       0x2E);       // first tile in the layer's char data
// or AddWindow(bgConfig, &window, &windowTemplate)

FillWindowPixelBuffer(&window, 0x00);   // clear to color 0
/* print text (§5) */
CopyWindowToVram(&window);              // tiles + tilemap now
// or ScheduleWindowCopyToVram(&window) to copy at the next VBlank
...
RemoveWindow(&window);
```

**Tile budget.** `baseTile` is where the window's tiles start in the layer;
each window needs `width × height` tiles, and windows on the same layer must not
overlap. Options' windows on `MAIN_1`: title at 0x0A (12×3 = 36 tiles, to 0x2E),
options list at 0x2E (30×18 = 540, to 0x24A), quit button at 0x24A (7×3 = 21, to
0x25F), confirm at 0x25F. Laying these out by hand is the most common source of
garbled menus.

### Frames

The bordered boxes around menus and dialogue are frame graphics loaded into a
layer, then drawn around a window ([include/render_window.h](../../include/render_window.h)):

- `LoadUserFrameGfx1` / `LoadUserFrameGfx2(bgConfig, layer, baseTile, palSlot, frameId, heapID)`
  load the frame the player chose in Options (`frameId`) or a fixed one.
- `DrawFrameAndWindow1` / `DrawFrameAndWindow2(&window, dontCopyToVram, baseTile, palSlot)`
  draw it; `ClearFrameAndWindow*` / `EraseFrameAndWindow*` remove it.

Type 1 is the menu frame; type 2 is the message box frame in the style the
player picked in Options ("WINDOW TYPE"). Both load from NARC 0x26.

## 5. Text

### Strings and message files

All text is in message files, `files/msgdata/msg/msg_NNNN.json` (msgenc JSON),
built into the `msgdata/msg` NARC. Each has a generated header with names for its
messages (`msgdata/msg/msg_0045.h`: `msg_0045_00000` ...).

```c
MsgData *msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0045, heapID);
String *str = String_New(40, heapID);          // capacity in characters
ReadMsgDataIntoString(msgData, msg_0045_00000, str);
// or: String *str = NewString_ReadMsgData(msgData, msg_0045_00000);
...
String_Delete(str);
DestroyMsgData(msgData);
```

`MSGDATA_LOAD_LAZY` reads each message from the file when asked;
`MSGDATA_LOAD_DIRECT` loads the whole file at once.

Placeholders (`{STRVAR_1 ...}` in the JSON) are filled with a `MessageFormat`
([include/message_format.h](../../include/message_format.h)):

```c
MessageFormat *fmt = MessageFormat_New(heapID);
BufferSpeciesName(fmt, 0, SPECIES_PIKACHU);
BufferIntegerAsString(fmt, 1, 42, 3, PRINTING_MODE_LEFT_ALIGN, TRUE);
String *out = ReadMsgData_ExpandPlaceholders(fmt, msgData, msgId, heapID);
...
MessageFormat_Delete(fmt);
```

### Printing

[include/text.h](../../include/text.h):

```c
u8 printerId = AddTextPrinterParameterizedWithColor(&window, fontId, str,
    x, y,                         // pixels inside the window
    TEXT_SPEED_INSTANT,           // or a delay in frames per character
    MAKE_TEXT_COLOR(1, 2, 15),    // foreground, shadow, background palette indexes
    NULL);                        // callback (dialogue uses it for button prompts)
```

- `TEXT_SPEED_INSTANT` (0) draws the whole string and copies the window to VRAM.
- `TEXT_SPEED_NOTRANSFER` (0xFF) draws it but doesn't copy; print several
  strings, then `CopyWindowToVram` once. This is the usual way to fill a menu.
- Any other value prints one character per that many frames, as dialogue does.
  `Options_GetTextFrameDelay(options)` gives the player's text speed. Check
  `TextPrinterCheckActive(printerId)`, and `RemoveTextPrinter` before reusing the
  window.

**Fonts.** Fonts 0, 1 and 3 are loaded at boot ([src/main.c](../../src/main.c));
2 and 4 are loaded by the screens that use them (`FontID_Alloc(4, heapID)`, and
`FontID_Release` when done). Font 0 is the one most menus use, font 1 the one
dialogue uses (`src/dialog_box.c`, and the text box of `src/field/script_menu.c`). The font's colors come from a palette loaded into the window's
palette slot: `LoadFontPal0` / `LoadFontPal1(location, slot, heapID)`.

**Layout helpers** (`font.h`): `FontID_String_GetWidth(fontId, str, 0)` for
centring or right-aligning (Options centres each choice on an x position),
`FontID_String_GetCenterAlignmentX(fontId, str, 0, windowWidthPx)`.

## 6. Menus

| Kind | API | Used for |
|---|---|---|
| Vertical scrolling list | `ListMenuInit` (`list_menu.h`) | bag, PC, shops, long script lists |
| Grid / short vertical menu | `Create2dMenu` (`list_menu_2d.h`) | multichoice boxes, yes/no |
| Yes/No | `Std_CreateYesNoMenu` (`list_menu_2d.h`), or `YesNoPrompt` (`yes_no_prompt.h`, touch buttons) | confirmations |
| Custom | hand-written, like Options | full screens |

**List menu.** Items are a `ListMenuItem` array of (string, value):

```c
ListMenuItem *items = ListMenuItems_New(count, heapID);
ListMenuItems_AppendFromMsgData(items, msgData, msgId, value);   // per item
// or ListMenuItems_AddItem(items, string, value)

ListMenuTemplate template = {
    .items = items, .window = &window,
    .totalItems = count, .maxShowed = 6,
    .item_X = 12, .cursor_X = 2, .upText_Y = 1,
    .cursorPal = 1, .fillValue = 15, .cursorShadowPal = 2,
    .fontId = 0, .itemVerticalPadding = 0, .scrollMultiple = 0,
    .moveCursorFunc = NULL, .itemPrintFunc = NULL,
};
ListMenu *menu = ListMenuInit(&template, scroll, cursorRow, heapID);

// each frame:
s32 result = ListMenu_ProcessInput(menu);
if (result == LIST_NOTHING_CHOSEN) { /* keep waiting */ }
else if (result == LIST_CANCEL)   { /* B pressed */ }
else                               { /* the chosen item's value */ }

DestroyListMenu(menu, &scroll, &cursorRow);   // saves the position for next time
ListMenuItems_Delete(items);
```

`moveCursorFunc` runs when the cursor moves (to update a description box or
play a sound); `itemPrintFunc` runs per visible row (to draw a price or count
beside the item).

### Menus from scripts

Scripts build menus in the field's shared menu window
([src/field/script_menu.c](../../src/field/script_menu.c)). In `scripts.pory`:

```
multichoiceinit(x, y, cursor, cancellable, VAR_SPECIAL_RESULT)   // texts from the map's message file
multichoiceitemadd(msg, value)                                   // per item
multichoiceexec                                                  // show and wait
switch (VAR_SPECIAL_RESULT) { ... }
```

- The `...stdgmm` variants (`multichoiceinitstdgmm`) take texts from the shared
  message file `msg_0191` instead of the map's own.
- `scriptlistmenuinit` / `scriptlistmenuitemadd(msg, help_msg, value)` /
  `scriptlistmenuexec` make a scrolling list with a help line per item.
- `multichoicegridexec(columns)` shows the items in a grid.
- `multichoiceadditemvar(msg_var, value_var)` takes message and value from vars, so a script can
  build the list at run time. This is the closest thing to pokeemerald's
  "dynamic multichoice".
- `yesno(VAR)` is the yes/no box.

The result var holds 0xEEEE while the menu is open; the `exec` commands wait
until it changes. Pressing B on a menu made with `cancellable = 1` writes 0xFFFE.

## 7. Input

`gSystem` ([include/system.h](../../include/system.h)), filled once per frame
before the application runs:

| Field | Meaning |
|---|---|
| `newKeys` | buttons pressed this frame (`PAD_BUTTON_A`, `PAD_KEY_UP`...) |
| `heldKeys` | buttons held |
| `newAndRepeatedKeys` | pressed, plus auto-repeat while held (use for cursor movement in lists) |
| `touchNew`, `touchHeld` | the screen was touched this frame / is being touched |
| `touchX`, `touchY` | touch position, bottom screen pixels |

The non-`Raw` fields have the player's **button mode** applied (Options "L=A" etc.,
`ApplyButtonModeToInput`); screens read those, not the `Raw` ones.

**Touch hitboxes** ([include/touchscreen.h](../../include/touchscreen.h)): a list of
rectangles ended by `TOUCHSCREEN_RECTLIST_END`; `TouchscreenHitbox_FindRectAtTouchNew(list)`
returns the index touched this frame, or -1.

```c
static const TouchscreenHitbox sHitboxes[] = {
    { .rect = { .top = 172, .bottom = 191, .left = 128, .right = 180 } },  // 0: confirm
    { .rect = { .top = 172, .bottom = 191, .left = 183, .right = 255 } },  // 1: quit
    { TOUCHSCREEN_RECTLIST_END },
};

if (gSystem.touchNew) {
    switch (TouchscreenHitbox_FindRectAtTouchNew(sHitboxes)) { ... }
} else if (gSystem.newKeys) { ... }
```

**Keys or touch.** The game remembers whether the player last used buttons or the
touch screen (`MenuInputStateMgr`, `fieldSystem->menuInputState`) and draws a
cursor only in button mode. Screens set it when the player uses one or the other:
`MenuInputStateMgr_SetState(mgr, MENU_INPUT_STATE_BUTTONS / MENU_INPUT_STATE_TOUCH)`.

**Sound feedback**: `PlaySE(SEQ_SE_DP_SELECT)` on cursor moves,
`SEQ_SE_DP_DECIDE` / `SEQ_SE_DP_SAVE` on confirm, `SEQ_SE_GS_GEARCANCEL` on cancel
(the ones Options uses).

## 8. Sprites

Sprites (OBJs) are used for cursors, buttons, icons and anything that animates
over the backgrounds. [include/sprite_system.h](../../include/sprite_system.h):

```c
// setup
SpriteSystem *sys = SpriteSystem_Alloc(heapID);
SpriteManager *man = SpriteManager_New(sys);
SpriteSystem_Init(sys, &oamManagerParam, &oamTransferParam, 32);   // OAM slots, char transfer, palettes
SpriteSystem_InitSprites(sys, man, maxSprites);

// resources: tiles (char), palette (pltt), cells, animations
SpriteSystem_LoadResourceDataFromFileIdList(sys, man, &resdatIdList);
// or one by one: SpriteSystem_LoadCharResObj / LoadPlttResObj / LoadCellResObj / LoadAnimResObj

// a sprite
Sprite *s = SpriteSystem_CreateSpriteFromResourceHeader(sys, man, &unmanagedSpriteTemplate);
Sprite_SetAnimCtrlSeq(s, animIndex);     // pick an animation
Sprite_SetPositionXY(s, x, y);
Sprite_SetDrawFlag(s, TRUE);

// every frame (in exec)
SpriteSystem_DrawSprites(man);
// in VBlank
SpriteSystem_TransferOam();

// teardown
SpriteSystem_DestroySpriteManager(sys, man);
SpriteSystem_Free(sys);
```

A sprite's graphics are four NARC resources: **char** (tiles), **pltt**
(palette), **cell** (how tiles form the sprite, NCER) and **anim** (frame
sequences, NANR). A **resdat** list names a set of them
(`data/resdat.naix`); Options uses one and picks entries with
`UnmanagedSpriteTemplate.resourceSet`.

The `ManagedSprite` API (`SpriteSystem_NewSprite` with a `ManagedSpriteTemplate`
listing resource ids per sprite) is the other style; many screens use it instead
of a resdat list.

**Both screens.** Sprites are placed in one tall coordinate space; Options puts
the sub screen 256 pixels below the main one with
`G2dRenderer_SetSubSurfaceCoords(SpriteSystem_GetRenderer(sys), 0, FX32_CONST(256))`.
`vram = NNS_G2D_VRAM_TYPE_2DMAIN` / `2DSUB` in the template says which engine's
memory a sprite uses.

Options builds its whole visible "menu" from sprites: the highlighted choice on
each row is a sprite moved to the chosen x (`OptionsApp_SetActiveButtonsXPosition`),
and the confirm/quit buttons are sprites whose animations show pressed and
released states.

## 9. Palettes and fades

- Load palettes into slots (16 per BG engine, 16 colors each in 4bpp):
  `GfGfxLoader_GXLoadPal(narc, member, GF_PAL_LOCATION_MAIN_BG, GF_PAL_SLOT_N_OFFSET, size, heapID)`.
  Plan the slots: Options uses 0-1 for its art, 12-13 for the fonts, 15 for the
  frame.
- **Fades**: `BeginNormalPaletteFade(FADE_BOTH_SCREENS, FADE_TYPE_BRIGHTNESS_IN, FADE_TYPE_BRIGHTNESS_IN, RGB_BLACK, steps, framesPerStep, heapID)`,
  then wait for `IsPaletteFadeFinished()`. Use `_OUT` to fade to black before
  leaving. Screens start black (`SetMasterBrightnessByColor(PM_LCD_TOP, RGB_BLACK)`
  in `init`) and fade in once everything is drawn, so the player never sees a
  half-built screen.
- **PaletteData** (`palette.h`): screens that animate palettes (blinking,
  tinting) keep a RAM copy with `PaletteData_*` and transfer it at VBlank.

## 10. Smaller things

- **Wireless icon**: `WirelessStatusIcon_CreateIfConnected()` in setup, so the
  icon stays while connected.
- **Text speed-up**: `TextFlags_SetCanABSpeedUpPrint(FALSE)` stops A/B from
  skipping text (Options turns it off so its text-speed preview is accurate, and
  back on in `exit`).
- **VRAM transfer manager**: `GF_CreateVramTransferManager(n, heapID)` before using
  queued graphics transfers, `GF_DestroyVramTransferManager()` on teardown;
  `NNS_GfdDoVramTransfer()` in VBlank does the queued copies.
- **The field's own bottom screen** (Pokégear, the touch menu,
  [src/field/touchscreen_menu.c](../../src/field/touchscreen_menu.c)) is not a
  separate application: it runs inside the field as a "bottom screen app"
  (`FieldSystem_SwitchBottomScreenApp`). The start menu closes it first.

## 11. Checklist for a new screen

1. Application functions, overlay, heap id, launcher (§1).
2. In setup: VBlank off, planes off, banks, display select, modes, BG layers,
   sprite system (§3, §4, §8).
3. Load palettes, tiles, tilemaps; message file; windows; print text; sprites.
4. Install the VBlank callback; turn on the layers you use; fade in.
5. Each frame: read input, update, `SpriteSystem_DrawSprites`.
6. On exit: fade out, wait, then free in reverse order: windows, strings and
   message data, BG layers, sprites; VBlank callback off; planes off.
7. Return results through the args struct; the caller frees it and reloads the
   field.

Things that go wrong:

- Garbled or flickering windows: tile ranges overlap (§4 tile budget) or a
  palette slot is reused.
- Nothing appears: the layer isn't toggled on, the plane mask is still
  `GX_PLANEMASK_NONE`, or the window was never copied to VRAM.
- A crash after leaving: something wasn't freed and the heap was destroyed with
  it in use, or the VBlank callback still points at freed data.
- Input handled twice: reading `newKeys` in two places in the same frame.

## Where to look

| Screen | File | Shows |
|---|---|---|
| Options | [src/options_app.c](../../src/options_app.c) | a whole small app: windows, sprites, touch, keys |
| Start menu | [src/start_menu.c](../../src/start_menu.c) | launching apps from the field, returning |
| Script menus | [src/field/script_menu.c](../../src/field/script_menu.c) | multichoice and list menus in the field |
| Yes/no buttons | [src/yes_no_prompt.c](../../src/yes_no_prompt.c) | a touch button prompt |
| List menu | [src/list_menu.c](../../src/list_menu.c) | the Gen 3 list menu |
