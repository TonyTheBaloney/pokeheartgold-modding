<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# The naming screen

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The keyboard screen used to name the player, the rival, Pokémon, PC boxes, groups and
Pal Pad friends. All of it is in [src/naming_screen.c](../../src/naming_screen.c)
(about 2,000 lines) and [include/naming_screen.h](../../include/naming_screen.h). It is
an ordinary application (`init` / `exec` / `exit`), so read [ui.md](ui.md) first for
applications, layers, windows, text and sprites; this guide covers only what is
specific to this screen.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `DoNamingScreen(template, dest, species, gender, personality, callback)` | `NamingScreen_CreateArgs(heapID, kind, param, maxLen, options, menuInputState)`, then run `gOverlayTemplate_NamingScreen` with those args |
| `NAMING_SCREEN_PLAYER`, `_BOX`, `_CAUGHT_MON`, `_NICKNAME`, `_WALDA` | `NAME_SCREEN_PLAYER`, `_POKEMON`, `_BOX`, `_RIVAL`, `_GROUP`, `_UNK4`, `_UNK6`, `_UNK7` |
| `sNamingScreenTemplates` (length, icon, title per type) | the length comes from the caller; icon and title are `switch`es / tables on the kind in `naming_screen.c` |
| the screen writes into `dest` | the screen fills `args->nameInputString`; the **caller** copies it into the save |
| keyboard character tables in `naming_screen.c` | the same: `sKeyboardRow_*` arrays, `sKeyboardLayoutPtrs` |
| preset names when the player enters nothing | a random name from `msg_0254` (§8) |

The screen lives in the ARM9 binary, not an overlay (`FS_OVERLAY_ID_NONE` in
`gOverlayTemplate_NamingScreen`; [main.lsf](../../main.lsf) lists it under `Static main`).

## 1. Kinds

`NameScreenType` is in [include/launch_application.h:53](../../include/launch_application.h#L53):

| Kind | Prompt (`msg_0249`) | Icon (anim in member 14) | Callers' `maxLen` | Launched by |
|---|---|---|---|---|
| `NAME_SCREEN_PLAYER` (0) | `00000` "Your name?" | 48 boy, 49 girl | `PLAYER_NAME_LENGTH` (7); 8 in the Frontier command | Oak's intro ([src/oaks_speech.c:2012](../../src/oaks_speech.c#L2012)), script `nameplayer` (command 172), `FrtCmd_LaunchNamingScreen` ([src/frontier/frontier_script_commands_ext.c:514](../../src/frontier/frontier_script_commands_ext.c#L514)) |
| `NAME_SCREEN_POKEMON` (1) | `00001` "{species}’s nickname?" | 50, replaced by the Pokémon's icon; ♂/♀ sprite (45/46) | `POKEMON_NAME_LENGTH` (10); a literal 10 in battle | catching ([src/battle/battle_command.c:6943](../../src/battle/battle_command.c#L6943)), egg hatching ([src/hatch_egg_task.c:58](../../src/hatch_egg_task.c#L58)), script `nicknameinput` (command 173) |
| `NAME_SCREEN_BOX` (2) | `00002` "Box name?" | 47 | 8 | PC ([src/application/pc_box/pc_box_ui.c:778](../../src/application/pc_box/pc_box_ui.c#L778)) |
| `NAME_SCREEN_RIVAL` (3) | `00003` "This boy’s name?" | 51 | `PLAYER_NAME_LENGTH` | script `namerival` (command 143) |
| `NAME_SCREEN_UNK4` (4) | `00004`, no English text | 53 | none | no caller found. Shows the number pad (page 4, §4) |
| `NAME_SCREEN_GROUP` (5) | `00005` "Group name?", plus the label `00007` "Group" right of the entry field | 54 | `PLAYER_NAME_LENGTH` | script `FriendGroupAction 4` (command 465, [src/scrcmd_8.c:49](../../src/scrcmd_8.c#L49)) |
| `NAME_SCREEN_UNK6` (6) | `00006`, no English text | 55 | none | no caller found |
| `NAME_SCREEN_UNK7` (7) | `00008` "Your friend’s name?" | 53 | 7 | Pal Pad, registering or renaming a friend ([src/application/palpad/palpad_friend_code.c:121](../../src/application/palpad/palpad_friend_code.c#L121)) |

The prompt id is `_021020B4[data->type]` ([src/naming_screen.c:457](../../src/naming_screen.c#L457));
the icon is chosen in `NamingScreen_CreateIconSprite`. Trades do not open the naming
screen: in-game trade Pokémon come with a fixed nickname
([gift-pokemon-and-trades.md](gift-pokemon-and-trades.md#5-in-game-trades)). Oak's intro
also creates `NAME_SCREEN_RIVAL` args but never shows them (the struct comment calls it a
leftover from DPPt), so the rival's name stays empty until Elm's lab
([new-game.md](new-game.md#1-what-happens-on-new-game)).

### The arguments

`NamingScreenArgs` ([include/naming_screen.h](../../include/naming_screen.h)), allocated
by `NamingScreen_CreateArgs` and freed by `NamingScreen_DeleteArgs`:

| Field | In / out | Meaning |
|---|---|---|
| `kind` | in | the `NameScreenType` |
| `playerGenderOrMonSpecies` | in | player gender (`PLAYER`: icon and default-name list) or species (`POKEMON`: icon and the species name in the prompt) |
| `monForm` | in | form, for the icon |
| `maxLen` | in | maximum characters (§7) |
| `monGender` | in | `MON_MALE` / `MON_FEMALE` / `MON_GENDERLESS`; `CreateArgs` sets 0, so a caller that forgets shows ♂ |
| `noInput` | out | `TRUE` if the name was left empty or unchanged (see below) |
| `nameInputString` | in / out | a `String` of capacity 32. In: text already in the field (box name, friend name). Out: the result |
| `nameInputFlat[20]` | out | the result as a flat `u16` array |
| `battleMsgId` | in | a `msg_0197` message printed on the top screen after OK (party full when catching); 0 = none |
| `pcStorage` | in | for that message's box names |
| `options` | in | message frame style (`Options_GetFrame`) |
| `pMenuInputState` | in | set to buttons or touch on OK; may be `NULL` |

### The result

On exit ([src/naming_screen.c:696](../../src/naming_screen.c#L696)):

```c
data->entryBuf[data->textCursorPos] = EOS;
...
if (data->textCursorPos == 0 || !StringNotEqual(data->entryBuf, data->entryBufBak) || NamingScreen_PMCharArrayIsAllSpaces(data->entryBuf)) {
    NamingScreen_SetDefaultName(data, args);
} else {
    CopyU16StringArray(data->entryBufBak, data->entryBuf);
    CopyU16StringArray(args->nameInputFlat, data->entryBuf);
    CopyU16ArrayToString(args->nameInputString, data->entryBuf);
}
```

So an empty field, all spaces (`CHAR_SPACE`), or the text it started with all go to
`NamingScreen_SetDefaultName`: the player and rival get a default name (§8) and
`noInput` stays `FALSE`; every other kind gets `noInput = TRUE` and `nameInputString`
is left as it was. There is no cancel button: B is backspace.

The caller saves the name. For the script commands, `Task_NamingScreen` and `SetName`
([src/launch_application.c:1030](../../src/launch_application.c#L1030)) do it and write
`noInput` into the script's variable:

| Value | Meaning |
|---|---|
| 0 | a name was stored |
| 1 | nothing stored: empty field, or (`POKEMON`) the new text equals the current nickname |
| 2 | (`GROUP`) the name is already used by a group, `Save_FriendGroup_IsGroupNameTaken` |

For `POKEMON`, `SetName` writes `MON_DATA_NICKNAME_FLAT_COMPARE`, which also clears the
"has nickname" flag if the text equals the species name. For the player and rival the
variable is always 0, so loops like `if (var(VAR_SPECIAL_RESULT) == 1) { goto(_0904) }`
after `namerival` in [data/maps/NewBark_ElmsLab_1F/scripts.pory](../../data/maps/NewBark_ElmsLab_1F/scripts.pory)
never repeat.

`CallTask_NamingScreen(taskman, type, species, maxLen, partyIdx, defaultStr, retVar)`
([src/launch_application.c:1107](../../src/launch_application.c#L1107)) is the field
launcher. For `POKEMON` and `GROUP`, `defaultStr` is only kept for the comparison
above; the field starts empty. For other kinds it is pre-filled. `partyIdx` 0xFF means
the Bug-Catching Contest Pokémon (`NicknameInput 255` in
[files/fielddata/script/scr_seq/scr_seq_0151.s:349](../../files/fielddata/script/scr_seq/scr_seq_0151.s#L349)).

## 2. Lifecycle

`NamingScreenApp_Init` builds the whole screen in one frame (state
`NS_INIT_STATE_LOAD_GFX`): heap `HEAP_ID_NAMING_SCREEN` (0x28000 bytes), message banks
`msg_0249` (prompts), `msg_0254` (default names) and `msg_0197` (battle text), graphics,
sprites and windows. The next frame (`NS_INIT_STATE_LOAD_MON_ICON`) copies the Pokémon
icon into sprite VRAM (`NamingScreen_LoadMonIcon`).

`NamingScreenApp_Main` runs `NamingScreenMainState`:

| State | What happens |
|---|---|
| `NS_MAIN_STATE_WAIT_FADE_IN` | wait for the fade |
| `NS_MAIN_STATE_FINISH_INIT` | place the cursor; 6 frames |
| `NS_MAIN_STATE_INPUT_LOOP` | per `data->pageSwitchState`, below |
| `NS_MAIN_STATE_WAIT_FADE_OUT` | wait, then return `TRUE` |

Inside the input loop, `pageSwitchState` (`NamingScreenPageSwitchState`) decides:
`NS_PAGESWITCH_STATE_DRAW_NEW_PAGE` to `_FINISH_BGS` animate a page change (input
ignored), `_IDLE` reads input, and `_PRINT_BATTLE_MESSAGE` to `_DELAY_AND_FADE_OUT` run
after OK when `battleMsgId != 0`: "{name} was transferred to {box}…" on the top screen,
30 frames, fade.

(`NamingScreen_PrepareBattleMessage` adds 2 to `battleMsgId` when the current box is
full. The comment on `printedFromBattleGMM` says it is never set; it is, whenever
`battleMsgId != 0`.)

## 3. What is on screen

`GfGfx_SetMainDisplay(PM_LCD_BOTTOM)` puts the main engine on the touch screen, so
"main" layers are the bottom screen here.

| Layer | Screen | Contents |
|---|---|---|
| `GF_BG_LYR_MAIN_0`, `MAIN_1` | bottom | the two keyboard pages, windows 0 and 1 (26×12 tiles), 512×256; one is shown, the other slides in on a page change |
| `GF_BG_LYR_MAIN_2` | bottom | background art (member 4), the entry field (window 3), the label right of it (window 8) |
| `GF_BG_LYR_SUB_0` | top | the prompt in a message frame (window 9, 27×4 at 2,19); the battle message reuses it |

A hardware window hides `MAIN_0`/`MAIN_1` in the top 64 pixels of the bottom screen
(`G2_SetWnd0Position(0, 0, 255, 64)`). Windows 4-7 draw large glyphs into top-screen
sprite tiles, but no sprite uses them (none is made from `spriteResHdr_Sub`, and
`NamingScreen_ToggleGfxPlanes` leaves that sprite layer off); window 2 is never drawn.
Both look like Japanese leftovers.

**Sprites** (all on the bottom screen):

| Array | What |
|---|---|
| `uiSprites[0..2]` | page tabs (upper, lower, symbols) |
| `uiSprites[5]`, `[6]` | Back and OK; their press animation is the anim id + 1 |
| `uiSprites[7]` | the parent of 0-6: a `SysTask` per sprite keeps them at its x, so they all wiggle after a page change |
| `uiSprites[8]` | the keyboard cursor; `NamingScreen_PaletteGlowEffect` pulses one sprite palette color |
| `textEntrySprites[maxLen]` | the underline under each character slot (anim 43, current slot 44) |
| `iconSprites[0]` | the kind's icon (§1) at (24, 8) |
| `iconSprites[1]` | `POKEMON` only, unless genderless: ♂/♀ at x = 13 × `maxLen` + 80, y 27 |

Positions and anims of `uiSprites` are in `sUISpritesParam` ([src/naming_screen.c:207](../../src/naming_screen.c#L207)).
The Pokémon icon works by loading anim 50 and then overwriting its tiles (VRAM offset
0x57E0) and palette 6 with the species' icon (`GetMonIconNaixEx`, `GetMonIconPaletteEx`).

**Graphics** are the `data/namein` NARC, loose files in
[files/data/namein/](../../files/data/namein/) with names from `data/namein.naix`
(edit as in [graphics.md](graphics.md#2-where-graphics-live)):

| Member | Used for |
|---|---|
| 0 NCLR | bottom BG palettes (3) |
| 1 NCLR | sprite palettes |
| 2 NCGR | bottom BG tiles (`MAIN_1`, `MAIN_2`) |
| 4 NSCR | `MAIN_2` background |
| 6, 7, 8 NSCR | keyboard frame for pages 0, 1, 2 (member 6 + page) |
| 9 NSCR | number pad frame (`NAME_SCREEN_UNK4`) |
| 10 / 12 / 14 | bottom sprites: NCGR / NCER / NANR (tabs, buttons, cursor, icons, underlines) |
| 11 / 13 / 15 | top-screen sprite resources (loaded, unused, see above) |
| 16 NCGR | read raw; only used for the Japanese dakuten / handakuten / space keys |
| 3, 5, 17, 18 | not loaded by `naming_screen.c` |

The top screen's palette is member 71 of `a/0/1/4`.

## 4. Keyboard pages and input

The keyboard is `data->keyboard[6][13]`: row 0 is the **home row** (tabs, Back, OK),
rows 1-5 are keys, 13 columns each. `NamingScreen_LoadKeyboardLayout`
([src/naming_screen.c:1632](../../src/naming_screen.c#L1632)) fills it from two tables:

```c
keyboard[0][i]     = sKeyboardHomeRowLayoutPtrs[pageNum][i];
keyboard[j + 1][i] = sKeyboardLayoutPtrs[pageNum][j][i];   // j = 0..4
```

| `pageNum` | Rows (`sKeyboardLayoutPtrs`, [line 300](../../src/naming_screen.c#L300)) | Home row | Reached by |
|---|---|---|---|
| 0 | `sKeyboardRow_Upper_1..5`: A-J , . / K-T ’ - / U-Z ♂ ♀ / blank / 0-9 | `sKeyboardHomeRow_All` | default; tab; SELECT |
| 1 | `sKeyboardRow_Lower_1..5`: the same in lower case | `sKeyboardHomeRow_All` | tab; SELECT |
| 2 | `sKeyboardRow_Symbols_1..5`: punctuation, quotes, math, card suits, faces, arrows | `sKeyboardHomeRow_All` | tab; SELECT |
| 3 | `sKeyboardRow_JPMisc_1..5`: Japanese full-width symbols | `sKeyboardHomeRow_All` | nothing (no tab on the English home row; SELECT wraps at 3) |
| 4 | `sKeyboardRow_Numpad_*`: 0-9 | `sKeyboardHomeRow_Numpad` (Back, OK only) | `NAME_SCREEN_UNK4` only |

The home row `sKeyboardHomeRow_All` ([line 219](../../src/naming_screen.c#L219)) is
columns 0-1 upper tab, 2-3 lower tab, 4-5 symbols tab, 6-7 `NAME_SCREEN_CONTROL_SKIP`,
8-10 Back, 11-12 OK. A button that spans several columns repeats its code.

**A cell holds a character code or a control code.** Pressing A calls
`NamingScreen_HandleCharacterInput(data, data->keyboard[y][x], TRUE)`
([line 1646](../../src/naming_screen.c#L1646)):

| Code | Effect |
|---|---|
| `NAME_SCREEN_BUTTON_PAGE_UPPER` / `_LOWER` / `_SYMBOLS` (0xE002-0xE004) | switch to page `code - 0xE002` |
| `NAME_SCREEN_BUTTON_PAGE_JP_UNUSED` (0xE005) | page 3; no English key has it |
| `NAME_SCREEN_BUTTON_PAGE_JP_UNUSED_2` (0xE006) | sent by R: swaps kana size / full-width letter case via `sJpCharConvTable`; does nothing to English letters |
| `NAME_SCREEN_BUTTON_BACK` (0xE007) | delete the last character |
| `NAME_SCREEN_BUTTON_OK` (0xE008) | finish (fade out, or the battle message first) |
| `NAME_SCREEN_CONTROL_SKIP` (0xD004) | the cursor jumps over it; if pressed anyway it types `CHAR_JP_SPACE` |
| `NAME_SCREEN_CONTROL_DAKU` / `_HANDAKU` / `_SPACE` (0xD001-0xD003) | Japanese keys, unused in English |
| anything else | appended to `entryBuf` if `textCursorPos != maxLen` |

So a `CHAR_SPACE` key types a space, and every blank key on the English pages is one.

**Buttons** (`NamingScreen_HandleInput`, `NamingScreen_GetPlayerInput`):

| Input | Effect |
|---|---|
| D-pad | move, with repeat (`SetKeyRepeatTimers(4, 8)`); wraps at the edges; skips `NAME_SCREEN_CONTROL_SKIP` and the other columns of a wide button (`NamingScreen_MoveKeyboardCursor`) |
| A | press the key under the cursor |
| B | Back |
| SELECT | next page, 0 → 1 → 2 → 0 (not for `UNK4`) |
| START | cursor to OK (column 12, row 0) |
| R | `NAME_SCREEN_BUTTON_PAGE_JP_UNUSED_2` |

If the cursor is hidden (after touch input), the first button press only shows it.
When the field is full, `kbCursor.ignoreInput` is set and the cursor moves to OK.

**Touch** uses its own table, `sTouchHitboxDef` ([line 1913](../../src/naming_screen.c#L1913)):
`{x, y, sizeParam, cursorX, cursorY}` = top-left corner, size (0: 31×22, 1: 32×22,
2: a 16×19 key) and the cell it selects. `NamingScreen_HandleTouchInput` moves the cursor
there and the key is pressed as if by A (`isButtonInput = FALSE`). Entries 0-5 are the
home row (entry 3, at y 0xC0, is off screen; `UNK4` starts at 4), then 13×5 keys.

**Drawing.** `NamingScreen_DrawKeyboardOnWindow` prints each row in `FONT_SYSTEM`, each
character centred in a 16 px cell. A page change draws the new page on the hidden layer,
which slides in while the old one scrolls up (`NamingScreen_HandlePageSwitch`).

## 5. The entry field

`entryBuf` (`u16[0x20]`) holds the characters, `textCursorPos` the count. Window 3 on
`MAIN_2` at tile (10, 3) is `(maxLen * 12) / 8 + 1` tiles wide; after every change it is
cleared and redrawn with `NamingScreen_BlitRawCharactersToWindow(..., spacing 12, ...)`,
each character centred in a 12 px slot. The underline sprites sit at x = 80 + 12 × i.
`entryBufBak` holds the starting text (from `nameInputString`), which is shown at start
and compared on exit.

## 6. How to change a keyboard page

Edit the `sKeyboardRow_*` arrays in [src/naming_screen.c](../../src/naming_screen.c#L254).
Character constants are in [include/constants/charcode.h](../../include/constants/charcode.h);
the code-to-glyph map and the range font 0 can draw are in
[text-and-messages.md](text-and-messages.md#2-characters). For example, to put accented
capitals on the empty fourth row of the upper-case page:

```c
static const u16 sKeyboardRow_Upper_4[] = { CHAR_Agrave, CHAR_Aacute, CHAR_Acarat, CHAR_Aumlaut, CHAR_Ccedilla, CHAR_Egrave, CHAR_Eacute, CHAR_Ecarat, CHAR_Ntilde, CHAR_Oumlaut, CHAR_Uumlaut, CHAR_SPACE, CHAR_SPACE, EOS };
```

Rules:

- **Exactly 13 keys, then `EOS`.** `NamingScreen_LoadKeyboardLayout` copies 13 entries
  without looking for `EOS`; drawing stops at `EOS`.
- The glyph must exist in font 0 and look right centred in a 16 px key and a 12 px
  entry slot ([text-and-messages.md](text-and-messages.md#7-fonts)).
- Don't put `NAME_SCREEN_CONTROL_SKIP` in a key row: touch can still press it, and it
  types the Japanese full-width space.
- The tabs' labels ("ABC" and so on) are sprite art (member 10), not text. Renaming or
  re-purposing a page means editing that art.
- The name will be shown elsewhere in other fonts (font 1 in dialogue), so check those
  have the glyph too.

Adding a fourth reachable page would need a tab code in `sKeyboardHomeRow_All` (for
example `NAME_SCREEN_BUTTON_PAGE_JP_UNUSED` in columns 6-7), tab art, a hitbox in
`sTouchHitboxDef`, the SELECT wrap (`if (data->pageNum >= 3)`, line 621) and a frame
tilemap: page 3 would load member 9, which is the number pad's. Not tried.

## 7. How to change the maximum length

`maxLen` is an argument, so change it at the call site of the kind you want (§1). The
screen itself is fine up to 10. Past that:

- **12 is a hard limit.** `textEntrySprites[12]` gets one sprite per character; a
  larger `maxLen` writes past the array into `iconSprites` and `tasks`.
- At 11 and 12, window 8 (`x = win3Width + 9`, 7 tiles wide) runs past the right edge of
  the 32-tile layer, and the ♂/♀ sprite moves to x 223 / 236. What that looks like is
  untested.

Then make sure the destination holds the longer name. `CopyStringToU16Array`
([src/pm_string.c:358](../../src/pm_string.c#L358)) copies nothing (only a `GF_ASSERT`)
when the string doesn't fit, so a name that is too long is silently not saved:

| Kind | Saved by | Destination | Max |
|---|---|---|---|
| `PLAYER` | `PlayerName_StringToFlat` (Oak), `Save_Profile_PlayerName_Set` (script) | `PlayerProfile.name[PLAYER_NAME_LENGTH + 1]` | 7 |
| `RIVAL` | `Save_Misc_RivalName_Set` | `rivalName[PLAYER_NAME_LENGTH + 1]` ([include/save_misc_data.h](../../include/save_misc_data.h)) | 7 |
| `POKEMON` | `SetMonData(..., MON_DATA_NICKNAME_*)` | `nickname[11]` in BoxPokemon block C ([include/pokemon_types_def.h:111](../../include/pokemon_types_def.h#L111)) | 10 |
| `BOX` | `PCStorage_SetBoxName` | `box_names[NUM_BOXES][BOX_NAME_LENGTH]` (20) | 19 |
| `GROUP` | `Save_FriendGroup_SetName` | `FRIEND_GROUP.groupName[8]` ([include/friend_group.h](../../include/friend_group.h)) | 7 |
| `UNK7` | `FriendRoster_SetPlayerName` ([src/friend_roster.c:147](../../src/friend_roster.c#L147)), after a check through a temporary `PlayerProfile` (`Save_Profile_PlayerName_Set` in [src/application/palpad/palpad_menu.c:113](../../src/application/palpad/palpad_menu.c#L113)) | roster `name2`, copied with a limit of 16 | 7 (the profile check) |

So **box names** are the one kind you can lengthen (to 10) without touching the save:
change the 8 in `PCBox_StartNamingScreenApp`. Shortening any kind is always safe.

Raising `PLAYER_NAME_LENGTH` or `POKEMON_NAME_LENGTH`
([include/constants/global.h](../../include/constants/global.h)) is a different job.
They size the player profile, the rival name, the OT name inside every BoxPokemon
(block D), trainer data, the day care, the Hall of Fame, battle packets and the
Pokéwalker and link formats; the nickname in block C is a literal 11. Every BoxPokemon
block is a fixed 32 bytes, so a longer name changes the Pokémon format, breaks old saves
([save-compatibility.md](save-compatibility.md#6-when-the-layout-has-to-change)) and
trading with retail games. Smaller fixed buffers on the way also assume the current
lengths: `nameInputFlat[20]`, `CopyStringToU16Array(..., 10)` in
`NamingScreen_SetDefaultName`, and `String_New(12, ...)` for `defaultName` in
`CallTask_NamingScreen`.

## 8. How to change the default names

`NamingScreen_SetDefaultName` ([src/naming_screen.c:656](../../src/naming_screen.c#L656))
reads [files/msgdata/msg/msg_0254.json](../../files/msgdata/msg/msg_0254.json), with
the start ids per version in macros just above it:

```c
#ifdef HEARTGOLD
#define FIRST_DEFAULT_NAME_MALE   msg_0254_00000
#define FIRST_DEFAULT_NAME_FEMALE msg_0254_00018
#define FIRST_DEFAULT_NAME_RIVAL  msg_0254_00084
#else
#define FIRST_DEFAULT_NAME_MALE   msg_0254_00042
#define FIRST_DEFAULT_NAME_FEMALE msg_0254_00060
#define FIRST_DEFAULT_NAME_RIVAL  msg_0254_00085
#endif // HEARTGOLD
```

| Ids | Used for |
|---|---|
| 00000-00017 / 00018-00035 | HeartGold boy / girl: one of 18 at random, `LCRandom() % 18` |
| 00042-00059 / 00060-00077 | SoulSilver boy / girl |
| 00084 / 00085 | HeartGold / SoulSilver rival: one fixed name |
| 00036-00041, 00078-00083 | not read by `naming_screen.c` |

The rival names in this file read "Soul" and "Heart"; there is no random rival name.
To change a name, edit its text in place. Keep every name at most 7 characters: the
player's goes through `PlayerName_StringToFlat`, which drops a longer one (§7). Don't
insert or delete entries: ids are positions, so every id after the change would point
at a different name. For more names per gender, append them at the end and change
both the start macro and the `% 18`. For a random rival, write
`FIRST_DEFAULT_NAME_RIVAL + (LCRandom() % n)` over a block of `n` names.

The default is used when the player leaves the field empty, all spaces, or unchanged
from the text it started with (`NamingScreenApp_Exit`, line 707, see §1). In the retail
game the player and rival fields always start empty (Oak's intro clears
`nameInputString`; `nameplayer` and `namerival` pass no starting text), so only the
first two cases happen. A pre-filled name the player accepts as is gets replaced by a
random default (pre-filling one, or naming the player without the keyboard:
[intro-title-credits.md §9](intro-title-credits.md#9-how-to-change-professor-oaks-speech)).

`nameplayer` always passes gender 0 (`ScrCmd_NamePlayer`,
[src/scrcmd_c.c:2108](../../src/scrcmd_c.c#L2108)), so a girl renamed from a script
gets the boy icon and the boy name list. No retail script uses it; pass the player's
gender (`PlayerProfile_GetTrainerGender`) if you add one.

## 9. How to skip or force the nickname prompt

- **Script gifts and the starter**: the script asks first, then calls
  `nicknameinput(slot, VAR)` (for example [data/maps/NewBark_ElmsLab_1F/scripts.pory:283](../../data/maps/NewBark_ElmsLab_1F/scripts.pory#L283)).
  Remove the question to skip it, or call `nicknameinput` without asking to force it
  ([gift-pokemon-and-trades.md](gift-pokemon-and-trades.md#1-givemon)).
- **Catching**: the question is state `STATE_GET_POKEMON_ASK_FOR_NICKNAME` in
  [src/battle/battle_command.c:6922](../../src/battle/battle_command.c#L6922). Answering
  No goes to `STATE_GET_POKEMON_STORE_MON_NO_NAMING_SCREEN`; to never ask, send the
  previous state there:

  ```c
  case STATE_GET_POKEMON_FADE_TO_NICKNAME_ASK:
      if (!PaletteData_GetSelectedBuffersBitmask(paletteData)) {
          data->state = STATE_GET_POKEMON_STORE_MON_NO_NAMING_SCREEN; // was STATE_GET_POKEMON_ASK_FOR_NICKNAME
  ```

  To force naming, skip the question the same way but do what the Yes branch of
  `STATE_GET_POKEMON_WAIT_FOR_YESNO` does (start the fade-out, then
  `STATE_GET_POKEMON_PREPARE_NAMING_SCREEN`). Neither change is tested in game.
- **Hatching**: the yes/no is in [src/application/hatch_egg_app.c](../../src/application/hatch_egg_app.c)
  (`HatchEggYesNoMenu_Show`), which sets `wantToNameNewMon`;
  [src/hatch_egg_task.c:45](../../src/hatch_egg_task.c#L45) acts on it. Replacing
  `data->wantToNameNewMon == TRUE` with `TRUE` or `FALSE` forces or skips the screen, but
  the question is still asked.

## 10. How to show more about the Pokémon

Retail shows only the icon and the gender. For level and shiny (and the IV idea), see
[../ideas/shiny-icons.md](../ideas/shiny-icons.md#related-naming-screen-details-also-not-built);
the steps are: new fields in `NamingScreenArgs`, set by the three Pokémon callers, drawn
by the screen. The top screen is empty above the prompt, so a window there is easiest.
This example compiles (each changed file built against the HeartGold flags; not linked
or run):

```c
// include/naming_screen.h, at the end of NamingScreenArgs
    int monLevel;    // 0 = show nothing
    BOOL monIsShiny;

// src/naming_screen.c, NamingScreen_CreateArgs
    ret->monLevel = 0;
    ret->monIsShiny = FALSE;

// CallTask_NamingScreen (launch_application.c), next to monForm; the same in
// hatch_egg_task.c and battle_command.c with their variable names
    data->args->monLevel = GetMonData(mon, MON_DATA_LEVEL, NULL);
    data->args->monIsShiny = MonIsShiny(mon);
```

Add `Window infoWindow;` at the end of `NamingScreenAppData`, two messages at the end of
[files/msgdata/msg/msg_0249.json](../../files/msgdata/msg/msg_0249.json) (they become
`msg_0249_00010` and `msg_0249_00011`):

```json
    {
      "id": "msg_0249_00010",
      "en_US": "Lv. {STRVAR_1 52, 3, 0}"
    },
    {
      "id": "msg_0249_00011",
      "en_US": "Lv. {STRVAR_1 52, 3, 0} ★"
    }
```

and draw it in `NamingScreen_InitWindows`, after the prompt (window 9):

```c
    NamingScreenArgs *args = OverlayManager_GetArgs(ovyMan);
    if (data->type == NAME_SCREEN_POKEMON && args->monLevel != 0) {
        AddWindowParameterized(data->bgConfig, &data->infoWindow, GF_BG_LYR_SUB_0, 2, 2, 12, 2, 12, 0x001);
        FillWindowPixelBuffer(&data->infoWindow, 15);
        BufferIntegerAsString(data->msgFormat, 3, args->monLevel, 3, PRINTING_MODE_LEFT_ALIGN, TRUE);
        String *str = ReadMsgData_ExpandPlaceholders(data->msgFormat, data->msgData_249,
            args->monIsShiny ? msg_0249_00011 : msg_0249_00010, HEAP_ID_NAMING_SCREEN);
        AddTextPrinterParameterized(&data->infoWindow, FONT_SYSTEM, str, 0, 0, TEXT_SPEED_INSTANT, NULL);
        String_Delete(str);
    }
```

and free it in `NamingScreenApp_Exit`, before `NamingScreen_UnloadBgGfx`:

```c
    if (WindowIsInUse(&data->infoWindow)) {
        RemoveWindow(&data->infoWindow);
    }
```

Why these numbers: on `SUB_0`, window 9 uses tiles 0x084-0x0EF and the message frame
starts at 0x100, so 0x001-0x083 are free (12×2 = 24 tiles); palette 12 is the font
palette the prompt uses. Slot 3 avoids slots 0-2, which the prompt and the battle message
fill. `RemoveWindow` frees the pixel buffer unconditionally, hence the
`WindowIsInUse` check for kinds that never created the window.

## 11. Pitfalls

- **Writing the result is the caller's job.** Launching the app with
  `OverlayManager_New` and not reading `nameInputString` / `noInput` afterwards does
  nothing. `FrtCmd_LaunchNamingScreen` is an example: its callback only frees the args.
- **`noInput` means "nothing to store"**, not "cancelled". For `BOX` it also covers
  "cleared the field": an empty box name keeps the old one.
- **Player kind with a gender other than 0 or 1**: `NamingScreen_SetDefaultName` uses an
  uninitialised `String *` (the code's own "UB" comment).
- **`monGender` defaults to 0** (male) in `NamingScreen_CreateArgs`; set it for every
  Pokémon caller.
- **The prompt table is indexed by kind.** `_021020B4` has 8 entries; a ninth
  `NameScreenType` needs a ninth entry there and a `case` in
  `NamingScreen_CreateIconSprite` (otherwise the prompt is read past the table and the icon keeps animation 0).
- **Spaces**: a name of only `CHAR_SPACE` counts as empty, but `CHAR_JP_SPACE` (what a
  pressed skip cell types) does not.

## Where to look

| File | What |
|---|---|
| [src/naming_screen.c](../../src/naming_screen.c) | the whole screen: keyboard tables (lines 219-306), prompts (457), default names (646), result (696), input (1396-1747), touch hitboxes (1913) |
| [include/naming_screen.h](../../include/naming_screen.h) | `NamingScreenArgs`, `NamingScreen_CreateArgs` |
| [include/launch_application.h](../../include/launch_application.h#L53) | `NameScreenType`, `CallTask_NamingScreen` |
| [src/launch_application.c](../../src/launch_application.c#L1030) | the field launcher and `SetName` (where script results are saved) |
| [src/scrcmd_c.c](../../src/scrcmd_c.c#L2106) | `nameplayer`, `namerival`, `nicknameinput` |
| [src/oaks_speech.c](../../src/oaks_speech.c#L2009) | naming the player on New Game; saved in `OakSpeech_Exit` (line 643) |
| [src/battle/battle_command.c](../../src/battle/battle_command.c#L6915) | nickname after catching |
| [src/hatch_egg_task.c](../../src/hatch_egg_task.c#L53) | nickname after hatching |
| [files/msgdata/msg/msg_0249.json](../../files/msgdata/msg/msg_0249.json) | prompts |
| [files/msgdata/msg/msg_0254.json](../../files/msgdata/msg/msg_0254.json) | default player and rival names |
| [files/data/namein/](../../files/data/namein/) | graphics |
| [include/constants/charcode.h](../../include/constants/charcode.h) | `CHAR_*` codes for the keyboard |
