<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The summary screen

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The Pokémon summary screen: how it is opened, how it is put together, how the
nature colors on the stat labels work, and a worked example that shows IVs and EVs
on the stats page. [ui.md](ui.md) explains the general framework (applications,
BG layers, windows, text, sprites, input); this guide only covers what is specific
to this screen.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `ShowPokemonSummaryScreen(mode, mons, index, lastIndex, callback)` | fill a `PokemonSummaryArgs` and launch `gOverlayTemplate_PokemonSummary` (§1) |
| `SUMMARY_MODE_NORMAL`, `_LOCK_MOVES`, `_SELECT_MOVE` | `args->mode` 0, 1, 2 (§1) |
| `isBoxMon` | `args->monDataType == 2` (§1) |
| `sMonSummaryScreen->summary` (`struct PokeSummary`) | `summary->mon` (`PokemonSummaryMon`), read once per Pokémon (§2) |
| `PSS_PAGE_INFO`, `_SKILLS`, `_BATTLE_MOVES`, `_CONTEST_MOVES` | pages 0 (info), 1 (skills and moves), 2 (Pokéathlon and ribbons) (§1) |
| summary strings in `gText_*` | `files/msgdata/msg/msg_0302.json` (§5) |

The code is in [src/pokemon_summary.c](../../src/pokemon_summary.c) (states,
input, data, sprites), [src/pokemon_summary_text.c](../../src/pokemon_summary_text.c)
(windows and printing), [src/pokemon_summary_scene.c](../../src/pokemon_summary_scene.c)
(3D picture, tab buttons) and [asm/pokemon_summary_data.s](../../asm/pokemon_summary_data.s)
(BG templates, hitboxes). It is in the ARM9 static module, not an overlay
(`gOverlayTemplate_PokemonSummary` has overlay id `0xFFFFFFFF`).

## 1. Opening the screen

### The args struct

The caller allocates a `PokemonSummaryArgs`
([include/pokemon_summary.h:12](../../include/pokemon_summary.h#L12)), fills it,
and launches `gOverlayTemplate_PokemonSummary` with it: `FieldSystem_LaunchApplication`
from the field, `OverlayManager_New` from inside another application (see
[ui.md §1](ui.md#launching-an-application)). The screen writes its results into
the same struct, and the caller frees it.

| Field | In/out | Meaning |
|---|---|---|
| `party` | in | the Pokémon list; what it points to depends on `monDataType` |
| `monDataType` | in | 0: an array of `Pokemon`; 1: a `Party *`; 2: an array of `BoxPokemon` |
| `partyCount` | in | number of entries in the list (`MONS_PER_BOX` for a box) |
| `partySlot` | in/out | the Pokémon shown first; on exit, the one shown last |
| `mode` | in | see the next table |
| `pageFlags` | in | one bit per page that may be shown; set with `PokemonSummary_SetPages` |
| `moveToLearn` | in | mode 2: the new move, shown as a fifth slot; `MOVE_NONE` for none |
| `options` | in | for the message box frame style |
| `playerName`, `playerId`, `playerGender` | in | set by `PokemonSummaryArgs_SetPlayer`; compared with the OT to pick the trainer memo wording |
| `natDexEnabled` | in | the Dex number shown is national or Johto |
| `ribbons` | in | `SaveSpecialRibbons`, for the descriptions of some ribbons |
| `isFlag982Set` | in | Pokéathlon unlocked (`PokemonSummary_IsPokeathlonUnlocked`): shows the Performance stars |
| `menuInputStatePtr` | in | `MenuInputStateMgr` to update on B or touch; may be `NULL` |
| `chatot` | in | Chatot's recorded cry, passed to `Chatot_PlayCryWithDelayedFallback`; 0 in most callers |
| `exitedWithB` | out | 1 when the player left with B or the cancel button |
| `selectedMoveSlot` | out | mode 2: the move slot to forget (0-3), or 4 for "don't learn" |
| `monModified` | out | set to 1 when moves were reordered (`PokemonSummary_SwapMoves`); the PC uses it to mark the box modified |
| `unk1A`, `unk24`, `unk2C` | | not understood; most callers fill `unk2C` from `PokemonSummary_GetDefaultUnk2C`, which returns 1 |

### Modes

| `mode` | Used by | Behaviour |
|---|---|---|
| 0 | party menu, PC, scripts, Colosseum, Battle Frontier party select, Castle/Hall/Arcade script commands | normal: page tabs, A on the moves opens move info, moves can be reordered |
| 1 | GTS, wireless trade, Battle Factory and Battle Hall apps, Colosseum | view only: move info opens, but A does not start a move swap and the Switch button is not drawn |
| 2 | learning a move: party menu (TM or level up), evolution, move relearner, `PokemonSummaryScreen` script command | starts on page 1 in `POKEMON_SUMMARY_STATE_FORGET_MOVE_INPUT`; picking a move fills `selectedMoveSlot` and exits |
| 3, 4 | no caller found | contest condition modes kept from Diamond/Pearl: page 3 (favorite flavor) and the condition update (`POKEMON_SUMMARY_STATE_UPDATE_CONDITION`, mode 4) |

### Pages

| Page | Top screen (main engine) | Bottom screen (sub engine, touch) |
|---|---|---|
| 0 | **TRAINER MEMO** (every page also shows the picture, nickname, level, item) | **INFO**: Dex No., name, types, OT, ID No., Exp. Points, To Next Lv., EXP bar |
| 1 | **SKILLS**: HP and its bar, the five stats, ability and description | **BATTLE MOVES**: four moves with type and PP; move info slides in on A or touch |
| 2 | **PERFORMANCE**: Pokéathlon stars (only when `isFlag982Set`) | **RIBBONS**: count and a 3×3 grid; A opens the ribbon list |
| 3 | condition chart and favorite flavor, from Diamond/Pearl (modes 3/4 only) | |

`PokemonSummary_SetPages` takes a list of page numbers ended by 4 and turns it
into `pageFlags` ([src/pokemon_summary.c:1432](../../src/pokemon_summary.c#L1432)).
The party menu passes `{ 0, 1, 2, 3, 4 }`, move learning `{ 1, 4 }`, the
Battle Factory app `{ 0, 1, 3, 4 }` (no ribbons page). Left/Right
(`PokemonSummary_ScrollPage`) and the three tabs on the bottom screen
(`PokemonSummary_HandleTouchInput`) only go to pages 0-2, skipping pages whose
bit is clear; I found no input that reaches page 3. Eggs stay on page 0.

Up/Down move to the previous/next Pokémon in the list (`PokemonSummary_ChangeMon`),
skipping empty slots, and skipping eggs unless the current page is 0 or 3
(`PokemonSummary_CanShowEgg`). For a list of Pokémon (not box Pokémon) the party
icons on the bottom screen can be touched; for box Pokémon there are previous/next
buttons instead.

### Who opens it

| Caller | Where |
|---|---|
| Party menu from the start menu (Summary, or replacing a move) | `Task_StartMenu_HandleReturn_Pokemon`, [src/start_menu.c:814](../../src/start_menu.c#L814); the result is read in `Task_StartMenu_HandleReturn_Summary` |
| Party menu in other field contexts, spin trade | `PokemonSummary_CreateArgs`, [src/launch_application.c:358](../../src/launch_application.c#L358) |
| `PokemonSummaryScreen` script command | `ScrCmd_PokemonSummaryScreen`, [src/scrcmd_c.c:1730](../../src/scrcmd_c.c#L1730), calls `PokemonSummary_LaunchApp` or `LearnForgetMove_LaunchApp` |
| PC | `PCBox_StartSummaryApp`, [src/application/pc_box/pc_box_ui.c:711](../../src/application/pc_box/pc_box_ui.c#L711) |
| Evolution, move relearner | [src/evolution_scene.c](../../src/evolution_scene.c), [src/application/move_relearner/move_relearner_app.c](../../src/application/move_relearner/move_relearner_app.c) (both `monDataType = 0`) |
| GTS, wireless trade, Colosseum, Frontier | `src/gts/gts_avatars.c`, `src/wireless_trade_select_mon.c`, `src/colosseum.c`, `src/frontier_field_support.c`, `src/frontier/*.c`, `src/scrcmd_battle_*.c` |

Box Pokémon (`monDataType = 2`) come from the PC, which passes the box's
`BoxPokemon` array with `partyCount = MONS_PER_BOX`, and from the GTS. No battle
code opens this screen.

## 2. Structure

### The data

`PokemonSummary` ([include/pokemon_summary_internal.h:99](../../include/pokemon_summary_internal.h#L99))
is the application's data. The parts that matter for edits:

| Field | Meaning |
|---|---|
| `windows[34]` | windows that exist for the whole screen (labels, nickname, level, item) |
| `pageWindows`, `numPageWindows` | the current page's windows, created and freed on each page change |
| `mon` | `PokemonSummaryMon`: everything shown about the current Pokémon |
| `sprites[115]` | every sprite, created once from `sPokemonSummarySpriteTemplates` |
| `msgData`, `msgFormat`, `buffer` | `msg_0302`, a `MessageFormat`, and a 128-character scratch `String` |
| `page` | current page, 0-3 |

`PokemonSummaryMon` ([include/pokemon_summary_internal.h:49](../../include/pokemon_summary_internal.h#L49))
is a cache. `PokemonSummary_ReadMon`
([src/pokemon_summary.c:1274](../../src/pokemon_summary.c#L1274)) fills it with
`GetMonData` when the screen opens and each time the shown Pokémon changes. A box
Pokémon is first copied into a temporary `Pokemon` (`PokemonSummary_ReadBoxMon`,
`CopyBoxPokemonToPokemon`), so its stats are calculated the same way. The print
functions read `summary->mon`, not the Pokémon (the trainer memo is the
exception). **To show a new value, add it to `PokemonSummaryMon` and read it in
`PokemonSummary_ReadMon`.**

```c
out->hp = GetMonData(mon, MON_DATA_HP, NULL);
out->maxHp = GetMonData(mon, MON_DATA_MAX_HP, NULL);
out->attack = GetMonData(mon, MON_DATA_ATK, NULL);
...
out->nature = GetMonNature(mon);
```

### The state machine

`PokemonSummary_Main` switches on `enum PokemonSummaryState`
([include/pokemon_summary_internal.h:22](../../include/pokemon_summary_internal.h#L22));
each handler returns the next state.

`INPUT` (`PokemonSummary_HandleInput`) is the page view: Left/Right pages,
Up/Down Pokémon, A on page 1 opens move info (`SLIDE_IN_MOVE_INFO`,
`MOVE_SELECT_INPUT`, `MOVE_SWAP_INPUT`), A on page 2 opens the ribbon list
(`OPEN_RIBBON_LIST`, `RIBBON_INPUT`), B goes to `START_FADE_OUT`. Mode 2 starts
in `FORGET_MOVE_INPUT`, mode 4 in `UPDATE_CONDITION`. A touched button goes
through `FLASH_BUTTON`, which flashes its palette and then returns
`flashNextState`.

Every frame, after the switch, it updates sprite animations, draws the sprites and
draws the 3D picture.

### Drawing a page

A page change goes through `PokemonSummary_SetPage`
([src/pokemon_summary.c:1445](../../src/pokemon_summary.c#L1445)):

1. `PokemonSummary_RemovePageWindows` frees the old page's windows.
2. Sprites are hidden or shown for the new page (type icons, Pokéathlon stars,
   Shiny Leaves, ribbons).
3. `PokemonSummary_AddPageWindows` creates the page's windows from one of three
   template arrays ([src/pokemon_summary_text.c:143](../../src/pokemon_summary_text.c#L143)):
   `sPokemonSummaryInfoWindowTemplates` (page 0, 8 windows),
   `sPokemonSummaryStatsWindowTemplates` (page 1, 18),
   `sPokemonSummaryRibbonWindowTemplates` (page 2, 8).
4. `PokemonSummary_PrintPage` prints the page ([src/pokemon_summary_text.c:380](../../src/pokemon_summary_text.c#L380)).
5. `PokemonSummary_LoadPageBgs` loads the page's tilemaps from `a/1/6/2`. Row
   `page` of `gPokemonSummaryPageScreens` gives the members for the top screen,
   the bottom screen, and the bottom screen for eggs and mode 2. It also draws
   the HP bar (page 1) or the EXP bar (page 0) as tiles.

A Pokémon change (`PokemonSummary_ShowMon`) keeps the page windows, rereads
`summary->mon`, updates the sprites and calls `PokemonSummary_PrintPage` again.

Layers: text is on `GF_BG_LYR_MAIN_1` and `GF_BG_LYR_SUB_0`, every window with
palette slot 13; the page art is on `MAIN_3` and `SUB_2`; the move info and
ribbon list panels slide in on `MAIN_2` and `SUB_1`; the Pokémon picture is 3D.

### The stats page

`PokemonSummary_PrintStats`
([src/pokemon_summary_text.c:535](../../src/pokemon_summary_text.c#L535)) prints
it. The labels are fixed windows and the values are page windows, all on the top
screen:

| Row | Label window | Message | Value window | Value |
|---|---|---|---|---|
| HP | `windows[15]` | `msg_0302_00110` | `pageWindows[0]` (7 tiles wide) | `mon.hp` / `mon.maxHp`, by `PokemonSummary_PrintValuePair` |
| Attack | `windows[16]` | `msg_0302_00111` | `pageWindows[1]` (3 tiles) | `mon.attack` |
| Defense | `windows[17]` | `msg_0302_00112` | `pageWindows[2]` (3 tiles) | `mon.defense` |
| Sp. Atk | `windows[18]` | `msg_0302_00113` | `pageWindows[3]` (3 tiles) | `mon.spAttack` |
| Sp. Def | `windows[19]` | `msg_0302_00114` | `pageWindows[4]` (3 tiles) | `mon.spDefense` |
| Speed | `windows[20]` | `msg_0302_00115` | `pageWindows[5]` (3 tiles) | `mon.speed` |
| Ability | `windows[21]` | `msg_0302_00116` | `pageWindows[6]`, `[7]` | name; description from `msg_0722` |

Each value is formatted, then printed right-aligned:

```c
PokemonSummary_FormatNumber(summary, msg_0302_00120, summary->mon.attack, 3, PRINTING_MODE_LEFT_ALIGN);
PokemonSummary_PrintBuffer(summary, &summary->pageWindows[1], MAKE_TEXT_COLOR(1, 2, 0), 1);
```

`PokemonSummary_FormatNumber` reads a message that is only a number placeholder
(`msg_0302_00118` to `00124` are all `{STRVAR_1 52, 0, 0}`), fills it with
`BufferIntegerAsString` and expands it into `summary->buffer`.
`PokemonSummary_PrintBuffer` prints `summary->buffer` with alignment 0 (left),
1 (right), 2 (centered) or, for any other value, at that x.

## 3. Nature colors

The stat labels show the nature: the label of the boosted stat and of the lowered
stat get a different shadow color. This is `PokemonSummary_PrintStatLabel`
([src/pokemon_summary_text.c:294](../../src/pokemon_summary_text.c#L294)):

```c
// The stat's label, coloured by the nature's effect on it.
static void PokemonSummary_PrintStatLabel(PokemonSummary *summary, int window, int msgNo, int stat, int alignment) {
    u32 color = MAKE_TEXT_COLOR(14, 15, 0);
    int mod = gNatureStatMods[summary->mon.nature][stat];
    if (mod < 0) {
        color = MAKE_TEXT_COLOR(14, 8, 0);
    } else if (mod > 0) {
        color = MAKE_TEXT_COLOR(14, 7, 0);
    }
    ReadMsgDataIntoString(summary->msgData, msgNo, summary->buffer);
    ...
}
```

- `summary->mon.nature` comes from `GetMonNature` in `PokemonSummary_ReadMon`.
- `gNatureStatMods` ([src/pokemon.c:1966](../../src/pokemon.c#L1966)) is the table
  the stat formula uses too (`ModifyStatByNature`). It has a row per nature
  (`NATURE_HARDY` ... `NATURE_QUIRKY`) and five columns: **Attack, Defense, Speed,
  Sp. Atk, Sp. Def** (`STAT_*` minus 1). Values are 1, -1 or 0.
- The callers pass the column as `stat`, so the screen order (Atk, Def, Sp. Atk,
  Sp. Def, Speed) uses columns 0, 1, 3, 4, 2:

```c
PokemonSummary_PrintStatLabel(summary, 16, msg_0302_00111, 0, 0); // Attack
PokemonSummary_PrintStatLabel(summary, 17, msg_0302_00112, 1, 0); // Defense
PokemonSummary_PrintStatLabel(summary, 18, msg_0302_00113, 3, 0); // Sp. Atk
PokemonSummary_PrintStatLabel(summary, 19, msg_0302_00114, 4, 0); // Sp. Def
PokemonSummary_PrintStatLabel(summary, 20, msg_0302_00115, 2, 0); // Speed
```

These five calls are in two places: `PokemonSummary_PrintLabels` (once, when the
windows are created) and `PokemonSummary_PrintStats` (each time the stats page is
drawn). Change both. HP is printed with `PokemonSummary_PrintMessage` and is never
colored.

The numbers in `MAKE_TEXT_COLOR(fg, shadow, bg)` are indexes into BG palette 13.
It comes from member 0 of `a/1/6/2`, loaded whole (16 palettes) by
`PokemonSummary_LoadBgGraphics`. The colors, read from that file:

| Index | Color | Used for |
|---|---|---|
| 1, 2 | `#404040`, `#b0b0b0` | values (dark text, light shadow) |
| 3, 4 | `#1870d8`, `#88a8d0` | ♂, male OT name |
| 5, 6 | `#f83820`, `#e09890` | ♀, female OT name, a shiny's Dex No. |
| 7 | `#886048` | shadow of the boosted stat's label |
| 8 | `#407898` | shadow of the lowered stat's label |
| 14, 15 | `#f8f8f8`, `#686868` | labels (white text, grey shadow) |

So the label text stays white and only the shadow changes, to a brown-red or a
blue.

**To change the colors**, either edit palette 13 indexes 7 and 8 in `a/1/6/2`
(a binary NARC; see [graphics.md §4](graphics.md#4-changing-a-binary-archive)),
or change the indexes in `PokemonSummary_PrintStatLabel`. For example, to color
the text itself with the palette's gender colors:

```c
if (mod < 0) {
    color = MAKE_TEXT_COLOR(3, 4, 0);  // blue
} else if (mod > 0) {
    color = MAKE_TEXT_COLOR(5, 6, 0);  // red
}
```

The labels are printed white on the page art, so check the contrast of other
colors in an emulator. **To change the rule**, change the condition. To color the
value too, compute the same `mod` in `PokemonSummary_PrintStats` and pass that color to
`PokemonSummary_PrintBuffer` instead of `MAKE_TEXT_COLOR(1, 2, 0)`; values are
printed dark (1/2), so the dark pairs 3/4 and 5/6 are the safe choices.

The nature *name* in the trainer memo is separate: `msg_0302_00024` + nature
("{COLOR 2}Hardy{COLOR 0} nature."), read by `FormatNature` in
[src/trainer_memo.c](../../src/trainer_memo.c).

## 4. Showing IVs and EVs

This adds a toggle on the stats page: Select cycles HP and the five stats between
the normal values, the IVs and the EVs, in a different text color for each so the
player can tell which is shown. It reuses the value windows, so it needs no new
windows, tiles or graphics. The code below compiles with `make release`; it was
not run in an emulator.

**1. Cache the values.** In `PokemonSummaryMon`
([include/pokemon_summary_internal.h](../../include/pokemon_summary_internal.h)),
after `shinyLeaves`:

```c
    u8 shinyLeaves[6];
    u8 ivs[6]; // HP, Atk, Def, Speed, Sp. Atk, Sp. Def: the STAT_* order
    u8 evs[6];
} PokemonSummaryMon;
```

and at the end of `PokemonSummary`:

```c
    u32 boxIconSprite; // which of sprites 73/74 shows the box Pokemon's icon next
    u8 statView;       // stats page: 0 stats, 1 IVs, 2 EVs
} PokemonSummary;
```

`PokemonSummary_Init` zeroes the struct, so `statView` starts at 0.

**2. Read them.** In `PokemonSummary_ReadMon`, after the `out->speed` line (that
is inside the `AcquireMonLock`/`ReleaseMonLock` pair, and `i` is already declared):

```c
    for (i = 0; i < 6; i++) {
        out->ivs[i] = GetMonData(mon, MON_DATA_HP_IV + i, NULL);
        out->evs[i] = GetMonData(mon, MON_DATA_HP_EV + i, NULL);
    }
```

`MON_DATA_HP_IV` ... `MON_DATA_SPDEF_IV` (70-75) and `MON_DATA_HP_EV` ...
`MON_DATA_SPDEF_EV` (13-18) are consecutive, in the same order as `STAT_HP` ...
`STAT_SPDEF` ([include/constants/pokemon.h](../../include/constants/pokemon.h)):
HP, Atk, Def, **Speed**, Sp. Atk, Sp. Def, which is not the screen order. Box
Pokémon work too, because `ReadMon` always gets a `Pokemon`.

**3. Print them.** In [src/pokemon_summary_text.c](../../src/pokemon_summary_text.c),
add two helpers above `PokemonSummary_PrintStats`:

```c
// The number shown for a stat: the stat itself, its IV or its EV.
static u16 PokemonSummary_GetShownStat(PokemonSummary *summary, int stat, u16 value) {
    switch (summary->statView) {
    case 1:
        return summary->mon.ivs[stat];
    case 2:
        return summary->mon.evs[stat];
    default:
        return value;
    }
}

// Dark grey for stats, blue for IVs, red for EVs (palette 13 indexes, as the gender symbols use).
static u32 PokemonSummary_GetStatValueColor(PokemonSummary *summary) {
    switch (summary->statView) {
    case 1:
        return MAKE_TEXT_COLOR(3, 4, 0);
    case 2:
        return MAKE_TEXT_COLOR(5, 6, 0);
    default:
        return MAKE_TEXT_COLOR(1, 2, 0);
    }
}
```

In `PokemonSummary_PrintStats`, replace the lines from
`PokemonSummary_PrintValuePair` to the `mon.speed` print with:

```c
    if (summary->statView == 0) {
        PokemonSummary_PrintValuePair(summary, 0, 117, 119, 118, summary->mon.hp, summary->mon.maxHp, 3, (u8)(GetWindowWidth(summary->pageWindows) * 4), 0);
    } else {
        PokemonSummary_FormatNumber(summary, msg_0302_00119, PokemonSummary_GetShownStat(summary, STAT_HP, 0), 3, PRINTING_MODE_LEFT_ALIGN);
        PokemonSummary_PrintBuffer(summary, &summary->pageWindows[0], PokemonSummary_GetStatValueColor(summary), 2);
    }
    PokemonSummary_FormatNumber(summary, msg_0302_00120, PokemonSummary_GetShownStat(summary, STAT_ATK, summary->mon.attack), 3, PRINTING_MODE_LEFT_ALIGN);
    PokemonSummary_PrintBuffer(summary, &summary->pageWindows[1], PokemonSummary_GetStatValueColor(summary), 1);
    PokemonSummary_FormatNumber(summary, msg_0302_00121, PokemonSummary_GetShownStat(summary, STAT_DEF, summary->mon.defense), 3, PRINTING_MODE_LEFT_ALIGN);
    PokemonSummary_PrintBuffer(summary, &summary->pageWindows[2], PokemonSummary_GetStatValueColor(summary), 1);
    PokemonSummary_FormatNumber(summary, msg_0302_00122, PokemonSummary_GetShownStat(summary, STAT_SPATK, summary->mon.spAttack), 3, PRINTING_MODE_LEFT_ALIGN);
    PokemonSummary_PrintBuffer(summary, &summary->pageWindows[3], PokemonSummary_GetStatValueColor(summary), 1);
    PokemonSummary_FormatNumber(summary, msg_0302_00123, PokemonSummary_GetShownStat(summary, STAT_SPDEF, summary->mon.spDefense), 3, PRINTING_MODE_LEFT_ALIGN);
    PokemonSummary_PrintBuffer(summary, &summary->pageWindows[4], PokemonSummary_GetStatValueColor(summary), 1);
    PokemonSummary_FormatNumber(summary, msg_0302_00124, PokemonSummary_GetShownStat(summary, STAT_SPEED, summary->mon.speed), 3, PRINTING_MODE_LEFT_ALIGN);
    PokemonSummary_PrintBuffer(summary, &summary->pageWindows[5], PokemonSummary_GetStatValueColor(summary), 1);
```

`STAT_*` come from `constants/pokemon.h`, which the file already includes. In the
IV and EV views the HP window shows one centered number instead of "current /
max". `PokemonSummary_PrintStats` already clears every value window first and
schedules the copies to VRAM after, so nothing else changes there.

**4. Toggle it.** In `PokemonSummary_HandleInput`
([src/pokemon_summary.c:696](../../src/pokemon_summary.c#L696)), before the
`PAD_BUTTON_A` check:

```c
    if ((gSystem.newKeys & PAD_BUTTON_SELECT) && summary->page == 1) {
        PlaySE(SEQ_SE_DP_SELECT);
        summary->statView = (summary->statView + 1) % 3;
        PokemonSummary_PrintPage(summary);
        return POKEMON_SUMMARY_STATE_INPUT;
    }
```

`PokemonSummary_PrintPage` is what `PokemonSummary_ShowMon` calls when the
Pokémon changes, so redrawing this way follows an existing path. It also reprints
the moves on the bottom screen, which does no harm. The view stays when the
player changes Pokémon or page, because `PrintStats` reads `statView` each time.
Eggs never reach page 1, and in mode 2 `HandleInput` is not used.

Pitfalls:

- **Width.** The five stat value windows are 3 tiles (24 px) wide: three digits.
  EVs go up to 255 and IVs to 31, so they fit. "31/252" would not; for that,
  widen the windows in `sPokemonSummaryStatsWindowTemplates` and move their
  `baseTile` values.
- **Tile budget.** On `MAIN_1` the fixed windows use tiles 0x001-0x212 and the
  stats page windows 0x21F-0x2A8; the message frame for condition mode is loaded
  at 0x3E2. Other pages' windows reuse 0x21F onward (they are freed on a page
  change), so a new stats-page window can start at 0x2A9. See
  [ui.md §4](ui.md#windows).
- **Number format.** `PokemonSummary_FormatNumber` calls `BufferIntegerAsString`.
  `PRINTING_MODE_LEFT_ALIGN` adds no padding and the window alignment (1 = right)
  lines the digits up; `PRINTING_MODE_LEADING_ZEROS` would print "007".
- **Labels.** `PokemonSummary_PrintStatLabel` does not clear its window; it
  relies on printing the same text in the same place. To print other label text
  per view ("Atk IV"), `FillWindowPixelBuffer(&summary->windows[16], 0)` (and so on)
  first and `ScheduleWindowCopyToVram` after. The label windows are 6 tiles wide.
- **Telling the views apart** is by color only. To print the view's name,
  reprint `windows[2]` ("SKILLS", `msg_0302_00109`; clear it first) with a new
  message. A touch toggle would need a free hitbox and art on the bottom screen;
  see `sTouchButtonHitboxes` and `PokemonSummary_HandleTouchInput`.

### Simpler variants

- **IVs always shown.** Skip `statView` and print `mon.ivs[...]` in new windows
  next to the values. The page area is tile columns 0-17 (what
  `PokemonSummary_PrintPage` clears) and the stat value windows end at column 15,
  so only columns 16-17 (16 px) are free on those rows.
- **Hidden Power type.** The formula is `GetHiddenPowerPowerType`
  ([src/field/scrcmd_pokemon_misc.c:570](../../src/field/scrcmd_pokemon_misc.c#L570)),
  which is `static` and takes a `Pokemon *`: make it public and call it in
  `PokemonSummary_ReadMon` (where the `Pokemon` is at hand), caching the type in
  `PokemonSummaryMon`, or copy its formula to work on `summary->mon.ivs`. Print it with `BufferTypeName` into a new `msg_0302`
  message with a placeholder. The ability description window (`pageWindows[7]`,
  19×4 tiles) is one candidate place, if the description leaves a line free.

## 5. Other edits

### Text and labels

The screen's text is `files/msgdata/msg/msg_0302.json` (header
`msgdata/msg/msg_0302.h`). The same file holds the trainer memo strings (natures,
met lines, characteristics, Egg Watch) used by `src/trainer_memo.c`. Other banks:

| Bank | Loaded in | Content |
|---|---|---|
| `msg_0302` | `PokemonSummary_InitText` | labels, number templates, memo |
| `msg_0424` | `PokemonSummary_InitText` | ribbon names and descriptions |
| `msg_0750` | `PokemonSummary_InitText` | move names |
| `msg_0749` | `PokemonSummary_PrintMoveInfo` | move descriptions |
| `msg_0722` | `PokemonSummary_PrintStats` | ability descriptions |

Some `msg_0302` ids: 7 "INFO", 23 "TRAINER MEMO", 109 "SKILLS", 110-115 the stat
names, 116 "Ability", 128 "BATTLE MOVES", 157 "PERFORMANCE", 179 "RIBBONS",
182 "No. of Ribbons:", 187-191 the Pokéathlon stats, 192 "Shiny Leaf",
193 "Forget!", 194 "Switch". Many ids from 126 to 186 are empty in the English
file. Editing a string is a JSON edit
([text-and-messages.md](text-and-messages.md)); a longer label must still fit its
window.

### Adding a page

Possible, but pages are hard-coded in many places:

- `pageFlags` is a `u8`, and `PokemonSummary_SetPages` reads at most 4 entries
  with 4 as the terminator; `PokemonSummary_ScrollPage` wraps between 0 and 2.
- The tabs: `sTouchButtonHitboxes` and `gTouchButtons` (`pokemon_summary_scene.c`),
  and the tab art inside the bottom-screen tilemaps of `a/1/6/2`.
- One case per page in `PokemonSummary_AddPageWindows`,
  `PokemonSummary_RemovePageWindows`, `PokemonSummary_PrintPage`, and a row in
  `gPokemonSummaryPageScreens` with new tilemaps.
- Sprite code that checks `summary->page` (`PokemonSummary_UpdateTypeSprites`,
  `_ShowRibbonSprites`, `_UpdatePokeathlonStars`, `_UpdateShinyLeafSprites`) and
  `PokemonSummary_CanShowEgg`.

Page 3 has a slot in all of these but no way to reach it, and its windows and art
belong to the condition mode; its case in `PokemonSummary_AddPageWindows` even
sets `numPageWindows = 3` without choosing a template array. For a few extra
values, a toggle like §4 is much less work.

### Moves, ribbons, Pokéathlon

- Moves: `PokemonSummary_PrintMoveSlot` prints one move (slot 4 is
  `args->moveToLearn`), `PokemonSummary_PrintMoveInfo` the power, accuracy and
  description. Type icons are sprites 13-17, the category icon 18. Reordering
  calls `MonSwapMoves` or `BoxMonSwapMoves`, then swaps `moves`, `pp`, `maxPP` in
  the cache.
- Ribbons: `ReadMon` checks the 80 ribbons with
  `GetRibbonAttr(i, RIBBONDAT_MONDATNO)` into `mon.ribbons` and
  `summary->ribbonCount`. Ribbon sprites 54-62 take graphics from `a/0/3/9`
  (`RIBBONDAT_NCGR`, `RIBBONDAT_NCLR`).
- Pokéathlon: sprites 79-103 are the stars and 104-108 the per-stat modifiers, set by `PokemonSummary_UpdatePokeathlonStars`
  only when `isFlag982Set`; otherwise the top screen uses tilemap 11.

### Markings, shiny star, Pokérus, status, item

`PokemonSummary_UpdateMarkingSprites`
([src/pokemon_summary.c:2757](../../src/pokemon_summary.c#L2757)) sets all three:

| What | Sprite | Rule |
|---|---|---|
| Markings | 23-28 | bit `i` of `mon.markings` (`MON_DATA_MARKINGS`): animation 1 when set, 0 when not. Display only; this screen does not edit them. |
| Shiny star | 52 | shown when `mon.shiny` (`MonIsShiny`) and not an egg |
| Cured Pokérus | 53 | shown when `mon.pokerus == 2` (`Pokemon_IsImmuneToPokerus`) |

A shiny's Dex number on the info page is also printed in red
(`PokemonSummary_PrintInfo`, colors 5/6 instead of 1/2).

The status icon is `PokemonSummary_UpdateStatusSprite`. `Pokemon_GetStatusIconId`
returns 1 paralysis, 2 freeze, 3 sleep, 4 poison, 5 burn, 6 fainted, 7 none, and
`ReadMon` turns 7 into 0 when the Pokémon has active Pokérus. Ids 1-6 show
sprite 20 with that animation; 0 shows sprite 72 at about the same position; 7
shows neither. So sprite 72 is the Pokérus icon, although the code comment calls it
the "no status" sprite; I did not check the graphic.

The held item is text only: `PokemonSummary_PrintHeldItem`
([src/pokemon_summary_text.c:245](../../src/pokemon_summary_text.c#L245)) prints
`msg_0302_00005` (item name) or `00006` ("None") into `windows[31]`, on every page.

## 6. Pitfalls

- **Read into the cache**, in `PokemonSummary_ReadMon`. In box mode the shown
  entry is a `BoxPokemon` (`PokemonSummary_GetShownMon` returns `void *`), so
  `GetMonData` on it is wrong.
- **Redraw on change.** Text printed from `PokemonSummary_PrintPage` is redrawn
  on page and Pokémon changes; a new sprite must be updated in both
  `PokemonSummary_SetPage` and `PokemonSummary_ShowMon`.
- **`pageWindows[n]` is a different window on each page**; check `summary->page`.
- **Writing to the Pokémon**: handle `monDataType == 2` with the `BoxMon`
  function and set `monModified`, as `PokemonSummary_SwapMoves` does.
- **Non-matching.** These edits change the ROM; build with `make release`, not
  `make` (which also runs the checksum check).

## Where to look

| File | What |
|---|---|
| [src/pokemon_summary.c](../../src/pokemon_summary.c) | init/exit, states, input, `PokemonSummary_ReadMon`, page changes, sprites |
| [src/pokemon_summary_text.c](../../src/pokemon_summary_text.c) | window templates, `PokemonSummary_PrintStats`, `PokemonSummary_PrintStatLabel` |
| [src/pokemon_summary_scene.c](../../src/pokemon_summary_scene.c) | Pokémon picture, condition chart, tab hitboxes |
| [include/pokemon_summary.h](../../include/pokemon_summary.h) | `PokemonSummaryArgs` |
| [include/pokemon_summary_internal.h](../../include/pokemon_summary_internal.h) | `PokemonSummary`, `PokemonSummaryMon`, states |
| [asm/pokemon_summary_data.s](../../asm/pokemon_summary_data.s) | BG templates, hitboxes, `gPokemonSummaryPageScreens` |
| [src/pokemon.c](../../src/pokemon.c#L1966) | `gNatureStatMods` |
| [include/constants/pokemon.h](../../include/constants/pokemon.h) | `NATURE_*`, `STAT_*`, `MON_DATA_*_IV`, `MON_DATA_*_EV` |
| [src/start_menu.c](../../src/start_menu.c), [src/application/pc_box/pc_box_ui.c](../../src/application/pc_box/pc_box_ui.c) | callers (party menu, PC) |
| `files/msgdata/msg/msg_0302.json` | the screen's text |
| `files/a/1/6/2` | BG graphics, palettes, tilemaps, ball sprites |
| `files/a/0/3/9` | ribbon sprites |
