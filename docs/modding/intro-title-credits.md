<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Intro, title screen, Professor Oak's speech and credits

> AI-generated; not affiliated with pret. See AI.md at the repository root.

What runs from power-on to the first map, and what runs after the Hall of Fame: the
opening movie, the title screen, Professor Oak's New Game speech (gender, name), and
the staff credits. For each one: where it is, what it loads, how it can be skipped,
and how to change it. Each screen is an application (`init` / `exec` / `exit`); read
[ui.md](ui.md) first for layers, windows, sprites and fades. What New Game sets up
around Oak's speech is in [new-game.md](new-game.md); the keyboard screen Oak opens
is in [naming-screen.md](naming-screen.md).

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `CB2_InitCopyrightScreenAfterBootup`, `intro.c` (copyright, Game Freak logo, the fight) | `gApplication_IntroMovie`, [src/intro_movie.c](../../src/intro_movie.c) and five scene files (§2) |
| `title_screen.c` (`CB2_InitTitleScreen`) | `gApplication_TitleScreen`, [src/title_screen.c](../../src/title_screen.c) (§3) |
| B + Select + Up on the title screen: clear save | the same buttons (`CLEAR_SAVE_KEY_COMBO`) |
| `main_menu.c`: `Task_NewGameBirchSpeech_*` | `gApplication_OakSpeech`, [src/oaks_speech.c](../../src/oaks_speech.c) (§4) |
| `NewGameBirchSpeech_SetDefaultPlayerName` | none in Oak's speech; the naming screen picks a default when the name is left empty ([naming-screen.md §8](naming-screen.md#8-how-to-change-the-default-names)) |
| `CB2_StartCreditsSequence`, `sCreditsEntries` | `Credits_LaunchApp`, [src/credits/credits.c](../../src/credits/credits.c) and the tables in [include/credits/data.h](../../include/credits/data.h) (§5) |
| `gTasks[...]` timing in frames | the same: everything is counted in frames (60 a second) |

## 1. The order of screens

After boot, [src/main.c](../../src/main.c) runs one "main overlay" at a time. Each
one's `exit` function registers the next with `RegisterMainOverlay(overlay, template)`.

```
power on ─▶ IntroMovie ─▶ TitleScreen ─A/Start/touch─▶ CheckSave ─▶ MainMenu
   (main.c:75)    │  ▲          │  │  │                               │
                  │  └─timeout──┘  │  └─X+Y+Down─▶ MicTest ─▶ TitleScreen
                  │                └─B+Select+Up─▶ DeleteSave
                  └─ (A/Start/touch skips the rest of the movie)

MainMenu ─New Game─▶ ov36 NewGame ─▶ OakSpeech ─▶ ov36 AfterOakSpeech ─▶ field
         ─Continue─▶ ov36 Continue ──────────────────────────────────────▶ field
```

| Step | Template | File | Overlay | Next |
|---|---|---|---|---|
| boot | — | `NitroMain`, [src/main.c:73](../../src/main.c#L73) | — | the intro movie (reset parameter 0) or Continue (1, after some link errors) |
| opening movie | `gApplication_IntroMovie` | [src/intro_movie.c](../../src/intro_movie.c) | `intro_title` | title screen (`IntroMovie_Exit`, line 163) |
| title screen | `gApplication_TitleScreen` | [src/title_screen.c](../../src/title_screen.c) | `intro_title` | `TitleScreen_Exit`, line 234 (§3) |
| save check | `gApplication_CheckSave` | [src/application/check_savedata.c](../../src/application/check_savedata.c) | none | main menu |
| main menu | `gApp_MainMenu` | [src/application/main_menu/](../../src/application/main_menu/) | `OVY_74` | `MainMenu_QueueSelectedApp`, `main_menu.c:1446` |
| New Game | `ov36_App_MainMenu_SelectOption_NewGame` | [src/overlay_36.c:93](../../src/overlay_36.c#L93) | `OVY_36` | wipes the save, then Oak's speech |
| Oak's speech | `gApplication_OakSpeech` | [src/oaks_speech.c](../../src/oaks_speech.c) | `OVY_53` | `ov36_App_InitGameState_AfterOakSpeech` |
| after the speech | `ov36_App_InitGameState_AfterOakSpeech` | [src/overlay_36.c:117](../../src/overlay_36.c#L117) | `OVY_36` | `gApplication_NewGameFieldsys`: the field and the `init` script ([new-game.md](new-game.md#1-what-happens-on-new-game)) |

The credits are not in this chain: they run from the field after the Hall of Fame
(§5) and end with a reset, which starts the chain again from the intro movie.

The intro movie and the title screen are in one overlay, `intro_title`
([main.lsf](../../main.lsf), `Overlay intro_title`), so switching between them is cheap.
The main menu's own "back to title" choice (`APPOPTION_TITLE_SCREEN`) and the mic test's
exit ([src/overlay_mic_test.c:436](../../src/overlay_mic_test.c#L436)) both go back to
the title screen, not the movie.

## 2. The opening movie

`IntroMovie_Main` ([src/intro_movie.c:79](../../src/intro_movie.c#L79)) starts
`SEQ_GS_TITLE` and runs five scenes in turn from `sIntroMovieSceneFuncs` (line 39).
Each scene is a small state machine that returns `TRUE` when it is done.

| Scene | File | What it shows |
|---|---|---|
| 1 | [intro_movie_scene_1.c](../../src/intro_movie_scene_1.c) | copyright (30 frames, then a 60-frame fade), Game Freak logo (110 frames), a sunrise (HG) or sunset (SS) with Ho-Oh / Lugia flying across, fade to white |
| 2 | [intro_movie_scene_2.c](../../src/intro_movie_scene_2.c) | Ethan and Lyra: fly-in, slow pans, circle wipe |
| 3 | [intro_movie_scene_3.c](../../src/intro_movie_scene_3.c) | 3D flyovers of New Bark, Goldenrod and Ecruteak, the rival, Entei/Raikou/Suicune, Eusine, the Unown, Team Rocket's admins |
| 4 | [intro_movie_scene_4.c](../../src/intro_movie_scene_4.c) | the players slide in and out, then Chikorita (grass), Cyndaquil (fire), Totodile (water), a sparkle |
| 5 | [intro_movie_scene_5.c](../../src/intro_movie_scene_5.c) | a wipe and a scrolling background, fade out to the title |

Each scene's state names (`INTRO_SCENE1_WAIT_GAMEFREAK`, ...) and the comments next to
them give the frame counts.

**Graphics.** Everything is in one archive built from loose files,
[files/demo/opening/gs_opening/](../../files/demo/opening/gs_opening/) (106 members,
`NARC_demo_opening_gs_opening`): backgrounds (`.NCGR`/`.NCLR`/`.NSCR`), sprites
(`.NCER`/`.NANR`), and the three town models of scene 3 (`.NSBMD` members 97, 100 and
103, with their `.NSBCA`/`.NSBTA` animations). None of them are PNG; convert one with
`nitrogfx`, edit, convert back over the same file ([graphics.md](graphics.md#4-changing-a-binary-archive)).
The code names members by their `.naix` constants
(`NARC_gs_opening_gs_opening_00000033_NCGR_lz`), so the number in the file name is the
number to look for. Scene 1 picks HeartGold or SoulSilver members with `#ifdef
HEARTGOLD` (lines 258-284).

The starters in scene 4 are pictures (members 85-96), not species: changing the
starters ([new-game.md §4](new-game.md#4-the-starter)) doesn't change the movie.

**Skipping.** A, Start or a touch ends the movie and goes to the title screen, but only
once `data->skipAllowed` is set. Scene 1 sets it when the Game Freak logo appears
(`INTRO_SCENE1_WAIT_APPEAR_GAMEFREAK`, line 114), so the copyright screen can't be
skipped. The skip check is at line 81.

**Random numbers.** `IntroMovie_Init` saves the game's LC random seed and sets it to 0,
so the movie looks the same every time; `IntroMovie_Exit` puts the old seed back.

## 3. The title screen

`TitleScreen_Main` ([src/title_screen.c:137](../../src/title_screen.c#L137)) loads the
graphics, waits 30 frames, starts `SEQ_GS_POKEMON_THEME`, then waits for input:

| Input | Constant (line) | What happens | `TitleScreen_Exit` goes to |
|---|---|---|---|
| A, Start or a touch | — (162) | plays the cry of `TITLE_SCREEN_SPECIES` (Ho-Oh / Lugia, line 36), white flash, music fades | `gApplication_CheckSave`, then the main menu |
| hold B + Select + Up | `CLEAR_SAVE_KEY_COMBO` (41) | fade to black | `gApplication_DeleteSave` (the "delete all saved data?" screen) |
| hold X + Y + Down | `MIC_TEST_KEY_COMBO` (42) | fade to black | `gApplication_MicTest` (overlay 62), which comes back here |
| nothing for `TITLE_SCREEN_DURATION` frames | (43), 2340 = 39 s | music fades | the intro movie again |

**Layout.** The screens are swapped (`gSystem.screensFlipped = TRUE`), so the 2D
"sub" engine is the **top** screen and the 3D "main" engine is the **bottom** one.

| Screen | Layer | What | File (`files/demo/title/titledemo/`) |
|---|---|---|---|
| top | sub BG 2 | the logo, 256 colors, fades in (`TitleScreenAnim_FadeInGameTitleLayer`) | `titledemo_00000003.png` (HG), `_00000001.png` (SS) |
| top | sub BG 3 | the glowing background | `titledemo_00000034.png` (HG), `_00000036.png` (SS) |
| top | sub BG 1 | "Developed by GAME FREAK inc." strip | `titledemo_00000015.png` |
| bottom | main BG 0 (3D) | Ho-Oh / Lugia and sparkles; models, animations, texture and material animations | `.NSBMD` 25-29 and 38-40 (HG), 20-24 and 41-43 (SS) |
| bottom | main BG 3 | "TOUCH TO START" | text, [files/msgdata/msg/msg_0719.json](../../files/msgdata/msg/msg_0719.json) |

The logo, background and strip are PNG sources: edit them and build (the tile flags
are in [files/demo/title/titledemo/meson.build](../../files/demo/title/titledemo/meson.build)).
The palettes beside them (`.NCLR`) and the tilemaps (`.NSCR`) stay binary; a redrawn
logo has to keep the PNG's size and color count, or the tilemap and palette won't match
it ([graphics.md](graphics.md)). Which file each version uses is chosen at run time from
`gGameVersion` in `TitleScreenAnim_Load2dBgGfx` (line 593), and the "TOUCH TO START"
text color by the two `RGB(...)` values at line 648.

The camera drifts between points in `sCameraScript_HG` / `sCameraScript_SS` (lines
721 and 764): each entry is a position and how long to stay (`duration * 30` frames),
and an entry with `x == 0` ends the list and loops back.

## 4. Professor Oak's speech

[src/oaks_speech.c](../../src/oaks_speech.c) (overlay 53, about 2,200 lines) is one
big state machine, `OakSpeech_DoMainTask` (line 1526). The states are named in the
`OakSpeechMainState` enum at the top of the file. Its text is
[files/msgdata/msg/msg_0219.json](../../files/msgdata/msg/msg_0219.json); ids below are
`msg_0219_000NN`.

### What it does, in order

| Part | States | Text | Notes |
|---|---|---|---|
| music | `START_TUTORIAL_MUSIC` | | `SEQ_GS_STARTING` |
| info menu | `FADE_IN_TUTORIAL_MENU` … `WAIT_FADE_OUT_TUTORIAL_MENU_BGS` | 07, choices 44-46 | CONTROL INFO, ADVENTURE INFO, NO INFO NEEDED; the first two come back to this menu |
| CONTROL INFO | `FADE_IN_CONTROL_INFO` … `CONTROL_INFO_UNDERSTOOD_NO` | 09-17, 23, 25-26 | "Do you understand?" No repeats it |
| ADVENTURE INFO | `FADE_IN_ADVENTURE_INFO` … | 28 | only page 28 is shown: `ADVENTURE_INFO_1` (line 1733) jumps straight to the fade-out, so pages 29-33 never appear |
| greeting | `NO_INFO_NEEDED_FADE_IN`, `PRINT_TIME_OF_DAY_MSG` | 01-05 | Oak waking up / reading, chosen by the DS clock (below) |
| Oak appears | `SHOW_OAK` … `WELCOME_TO_WORLD` | 06 | music changes to `SEQ_GS_STARTING2` |
| Marill | `SLIDE_OAK_RIGHT` … `SLIDE_OAK_LEFT` | 34, 35 | Poké Ball flash, `PlayCry(SPECIES_MARILL)` (line 1859) |
| gender | `TELL_ME_ABOUT_YOURSELF` … `CONFIRM_GENDER_YESNO_HANDLE_RESULT` | 36, 37, 38/39, 47-48 | the cursor starts on `lastChosenGender` (0, the boy; line 559) |
| name | `CONFIRM_GENDER_YES` … `CONFIRM_NAME_YESNO_HANDLE_RESULT` | 40, 41/42 | launches the naming screen (line 2009); **No goes back to the gender question**, not the keyboard |
| send-off | `YOUR_ADVENTURE_UNFOLDS` … `RUN_SHRINK_ANIM` | 43 | the player picture shrinks away (`SEQ_SE_GS_HERO_SHUKUSHOU`) |

The greeting (`OakSpeech_GetTimeOfDayIntroMsg`, line 1477) uses its own hours, not the
game's five times of day ([day-night-and-rtc.md](day-night-and-rtc.md)):

| DS clock | Message |
|---|---|
| 4:00-10:59 | 01 ("already become so bright outside!") |
| 11:00-15:59 | 02 ("I overslept!") |
| 16:00-18:59 | 03 ("twilight") |
| 19:00-23:59 | 04 (reading a book) |
| 0:00-3:59 | 05 ("A guest? At this hour?") |

### What it saves

Nothing is saved until `OakSpeech_Exit` ([line 639](../../src/oaks_speech.c#L639)):

| Saved | From |
|---|---|
| player name | `PlayerName_StringToFlat(profile, namingScreenArgs_Player->nameInputString)` |
| player gender | `PlayerProfile_SetTrainerGender(profile, namingScreenArgs_Player->playerGenderOrMonSpecies)` |
| rival name | `Save_Misc_RivalName_Set(..., namingScreenArgs_Rival->nameInputString)`: the rival naming args are created but never shown, so this writes an **empty** name. The rival is named later at Elm's lab (`namerival`) |

Then it registers `ov36_App_InitGameState_AfterOakSpeech`, which reads the gender (the
welcome mail is from Lyra or Ethan) and sets up the rest ([new-game.md](new-game.md#1-what-happens-on-new-game)).

### Default names

Oak's speech has no name list of its own. It empties the name (line 2010) and opens the
naming screen; if the player confirms an empty (or all-space) name, the naming screen
fills in one of 18 random names for the chosen gender from `msg_0254`. Changing those
names: [naming-screen.md §8](naming-screen.md#8-how-to-change-the-default-names).

### Graphics

| What | Where |
|---|---|
| Oak, Ethan and Lyra pictures (main BG 1) | [files/demo/intro/intro/](../../files/demo/intro/intro/) (`NARC_demo_intro_intro`), members listed in `sBgPicNCGR_NCLR` (line 496): Oak 10/11, Ethan 12-15 with palette 16, Lyra 17-20 with palette 21 (only Oak, Ethan's first and Lyra's first are drawn). The shrink at the end uses `sPlayerPicShrinkGfx_Male` / `_Female` (line 333): 12, 22-25 and 17, 26-29 |
| bottom-screen backgrounds and menus | the same archive: `sSubScreenBackgroundNSCR`, `sButtonTutorialNSCR`, `sSubScreenMenuGraphics` (lines 301-318) |
| sprites: Marill and its ball, gender cursors, the Touch button | resource lists `resdat_00000024`-`27` and `78`, loaded in [src/oaks_speech_obj.c:130](../../src/oaks_speech_obj.c#L130) |
| the yes/no buttons | [src/oaks_speech_yesnomenu.c](../../src/oaks_speech_yesnomenu.c) |

All of `files/demo/intro/intro/` is loose binary files, converted and replaced one at a
time like the movie's.

## 5. The credits

### How they start

The Hall of Fame script calls `hofcredits(0)`
([data/maps/PokemonLeagueHallOfFame/scripts.pory:104](../../data/maps/PokemonLeagueHallOfFame/scripts.pory#L104));
beating Red calls `hofcredits(1)`
([data/maps/MountSilver_CaveSummit/scripts.pory:52](../../data/maps/MountSilver_CaveSummit/scripts.pory#L52)).
Both reach `CallTask_GameClear` ([src/game_clear.c:263](../../src/game_clear.c#L263)):

1. Remembers whether the game was **already** cleared (`creditsArgs.gameCleared`),
   then sets `FLAG_GAME_CLEAR`, the continue point (your room) and, the first time,
   the clear time. What the flag unlocks: [story-progression.md](story-progression.md#elite-four-and-game-clear).
2. `hofcredits(0)` only: the Hall of Fame "congratulations" screen
   ([src/register_hall_of_fame.c](../../src/register_hall_of_fame.c)) and a League win
   in the game stats.
3. Heals the party and saves ("Saving... don't turn off the power"), and with
   `hofcredits(0)` adds the party to the Hall of Fame records. A save that belongs to
   another player is not written.
4. Fades the music out and launches the credits (`Credits_LaunchApp`, overlay
   `credits`).
5. After the credits: `OS_ResetSystem(0)`, a soft reset to the intro movie.

### What plays

`Credits_Main` ([src/credits/credits.c:306](../../src/credits/credits.c#L306)) counts
frames in `work->timer` and runs four things from tables in
[include/credits/data.h](../../include/credits/data.h):

| Thing | Table | What it is |
|---|---|---|
| text pages | `sPageTimings[43]` (line 191), `sCreditMsgLines[251]` (line 282) | page `n` appears at frame `startTime` and stays `duration` frames; each line is `{ page, x, y, msgno }` |
| background scenes | `sSceneTransitionTimings` (line 70), `NUM_SCENES` 6 | at each listed frame, clouds cover the dancing Pokémon and the background and dancers change |
| screen swaps | `sScreenFlipTimings` (line 72) | the top and bottom screens trade places |
| cutscenes | `sCutscenes[16]` (line 536) | sprite scenes in the middle: up to 6 graphics and 16 sprites each, each sprite with an animation, position and start frame |

The text is [files/msgdata/msg/msg_0440.json](../../files/msgdata/msg/msg_0440.json)
(00000 / 00001: the HG / SS title page; 00003 on: roles in `{COLOR 2}` and names).
The music is `SEQ_GS_ENDING` (`0x3f8` at line 258). At frame `CREDITS_FRAMES` (4976,
about 83 s; line 37) the credits fade to "The End"
(`a/2/6/3` members 6 and 19); after 380 frames there, `SEQ_GS_ENDING2` (the music box)
starts. A, Start or a touch on "The End" leaves.

The cutscene that shows the player picks Ethan or Lyra from `creditsArgs.gender`
(`LoadCutsceneSpriteGfx`, line 942), and the friend is the other one.

**Graphics.** Backgrounds, dancing Pokémon, clouds, cutscene sprites and "The End" are
all in [files/a/2/6/3](../../files/a/2/6/3), a prebuilt archive of 192 members;
`sCutsceneSpriteGfxFileIds` (data.h:237) lists the palette, tiles, cells and animation
for each of the 42 cutscene graphics. Export it to PNG with `narcgfx`
([graphics-sources.md](graphics-sources.md#8-converting-another-archive)).

**Skipping.** Start or a touch skips to "The End", but only if the game had been
cleared **before** this run (`work->args->gameCleared`, line 318). The first credits
can't be skipped.

## 6. How to skip the intro movie

Boot straight to the title screen. In [src/main.c](../../src/main.c), line 75:

```c
// before
RegisterMainOverlay(FS_OVERLAY_ID(intro_title), &gApplication_IntroMovie);
// after
RegisterMainOverlay(FS_OVERLAY_ID(intro_title), &gApplication_TitleScreen);
```

and add `#include "title_screen.h"` at the top (it declares `gApplication_TitleScreen`).
The title screen's timeout still goes back to the movie; to keep it on the title
screen instead, change the `TITLESCREEN_EXIT_TIMEOUT` case in `TitleScreen_Exit`
([src/title_screen.c:253](../../src/title_screen.c#L253)) to register
`gApplication_TitleScreen`.

To keep the movie but let the player skip it from the first frame, set
`data->skipAllowed = TRUE;` in `IntroMovie_Init` instead of `FALSE`
([src/intro_movie.c:68](../../src/intro_movie.c#L68)). That also makes the copyright
screen skippable.

To drop one scene, remove it from `sIntroMovieSceneFuncs` and change the `5` in
`data->sceneNumber >= 5` (line 99) to the new count. Scene 1 also enables skipping
(above), so if you drop it, set `skipAllowed` in `IntroMovie_Init`.

## 7. How to skip the title screen

To go from the movie straight to the save check and main menu, change the end of
`IntroMovie_Exit` ([src/intro_movie.c:163](../../src/intro_movie.c#L163)):

```c
// before
RegisterMainOverlay(FS_OVERLAY_ID(intro_title), &gApplication_TitleScreen);
// after
RegisterMainOverlay(FS_OVERLAY_ID_NONE, &gApplication_CheckSave);
```

with `#include "application/check_savedata.h"`. The title screen normally fades its
music out before the menu; the movie's music (`SEQ_GS_TITLE`) would still be playing,
so stop it first (`StopBGM(SEQ_GS_TITLE, 0);`). The clear-save and mic-test button
combinations live on the title screen and go with it.

## 8. How to change the title screen

| Change | Where |
|---|---|
| the cry when you press Start | `TITLE_SCREEN_SPECIES` (line 36) |
| the music | `SEQ_GS_POKEMON_THEME` in `TITLESCREEN_MAIN_START_MUSIC` and the three `StopBGM` calls (lines 150-218); see [music.md](music.md) |
| how long before it goes back to the movie | `TITLE_SCREEN_DURATION` (frames) |
| the hidden button combinations | `CLEAR_SAVE_KEY_COMBO`, `MIC_TEST_KEY_COMBO` (they are checked against *held* keys) |
| the logo, background, Game Freak strip | the PNGs in §3 |
| "TOUCH TO START" | `msg_0719.json`; colors at line 648 |
| the camera path | `sCameraScript_HG` / `_SS` |
| the flying Pokémon | the `.NSBMD` model and its animations in §3; a different model must keep the same animation types, or pass `-1` for the ones it lacks in `TitleScreen_Load3DObjects` (line 493) |

## 9. How to change Professor Oak's speech

**Text.** Edit `msg_0219.json` in place; don't insert or delete entries, since ids are
positions. Message 43 uses `{STRVAR_1 3, 0, 0}` for the player's name; buffer 1 holds
the (empty) rival name ([text-and-messages.md](text-and-messages.md)).

**Greeting times.** Change the `time_hhmm` ranges in `OakSpeech_GetTimeOfDayIntroMsg`.

**The Pokémon Oak shows.** The cry is `SPECIES_MARILL` at line 1859; the picture is a
sprite in the resource lists of `oaks_speech_obj.c`, so a different species needs new
sprite graphics too. The welcome mail's Marill is separate
([new-game.md](new-game.md#1-what-happens-on-new-game)).

**Skip the info menu.** Make the first state go straight to the greeting. In
`OAK_SPEECH_MAIN_STATE_START_TUTORIAL_MUSIC` (line 1530):

```c
    case OAK_SPEECH_MAIN_STATE_START_TUTORIAL_MUSIC:
        ToggleBgLayer(GF_BG_LYR_SUB_2, GF_PLANE_TOGGLE_OFF);
        Sound_SetSceneAndPlayBGM(2, SEQ_GS_POKEMON_THEME, 1);
        StopBGM(SEQ_GS_POKEMON_THEME, 0);
        PlayBGM(SEQ_GS_STARTING);
        OakSpeech_LoadSubScreenBackground(data, 0); // was loaded by the menu
        data->state = OAK_SPEECH_MAIN_STATE_NO_INFO_NEEDED_FADE_IN;
        break;
```

The menu state normally loads the bottom-screen background; the extra line loads it
here instead.

**Show the ADVENTURE INFO pages that are cut.** In `ADVENTURE_INFO_1` (line 1733),
delete the second assignment, `data->state = OAK_SPEECH_MAIN_STATE_ADVENTURE_INFO_FADE_OUT;`.
States `ADVENTURE_INFO_2` to `_6` already exist and print messages 29-33.

**Fixed gender.** Skip the question by going from `TELL_ME_ABOUT_YOURSELF` straight to
the name, with the gender set:

```c
    case OAK_SPEECH_MAIN_STATE_TELL_ME_ABOUT_YOURSELF:
        if (OakSpeech_PrintDialogMsg(data, msg_0219_00036, 1) == TRUE) {
            data->playerGender = PLAYER_GENDER_MALE;
            OakSpeech_TouchToAdvanceButtonAction(data, TOUCHTOADVANCE_HIDE);
            data->state = OAK_SPEECH_MAIN_STATE_CONFIRM_GENDER_YES;
        }
        break;
```

Message 36 ("tell me about yourself") then leads to 40 ("Please tell me your name");
change its wording to fit. The name screen's "No" also goes back through the gender
question (`CONFIRM_GENDER_NO_WAIT_FADE_OUT` → `ARE_YOU_A_GENDER`); point it at
`CONFIRM_GENDER_YES` too, or the question comes back.

**Pre-filled name.** Replace `String_SetEmpty(...)` in
`PROMPT_NAME_LAUNCH_NAMING_SCREEN` (line 2010) with a copy of the name you want (for
example read from `msg_0254`). The keyboard opens with it typed in. But the naming
screen treats "confirmed without changes" like "left empty" and replaces it with a
random default (`NamingScreenApp_Exit`, `naming_screen.c:707`, the
`!StringNotEqual(entryBuf, entryBufBak)` test). To keep a pre-filled name the player
accepts as is, drop that test for `NAME_SCREEN_PLAYER`.

**Fixed name, no keyboard.** In `PROMPT_NAME_LAUNCH_NAMING_SCREEN`, fill
`namingScreenArgs_Player->nameInputString` yourself, set
`namingScreenArgs_Player->playerGenderOrMonSpecies = data->playerGender;`, and go to
`OAK_SPEECH_MAIN_STATE_CONFIRM_NAME_YES` without creating `data->overlayManager`. Oak
then says message 43 with that name.

**A rival name here.** The rival args already exist (`namingScreenArgs_Rival`, with
`NAME_SCREEN_RIVAL`). Open them the same way as the player's (`OverlayManager_New(&gOverlayTemplate_NamingScreen,
data->namingScreenArgs_Rival, data->heapID)`) from a new state after the player's
name; `OakSpeech_Exit` already saves the result. Then remove the `namerival` scene at
Elm's lab (`NewBark_ElmsLab_1F`), or it asks again.

## 10. How to skip Oak's speech entirely

Go from the New Game setup straight to the after-speech step, and set what the speech
would have set. In [src/overlay_36.c](../../src/overlay_36.c):

```c
#include "msgdata/msg/msg_0254.h"

BOOL ov36_TitleScreen_NewGame_AppExec(OverlayManager *man, int *state) {
#pragma unused(state)
    SaveData *saveData = ((struct MainOverlayArgs *)OverlayManager_GetArgs(man))->saveData;
    NewGame_InitSaveData(HEAPID_OV36, saveData);

    // What Oak's speech would have saved
    PlayerProfile *profile = Save_PlayerData_GetProfile(saveData);
    MsgData *msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0254, HEAPID_OV36);
    String *name = NewString_ReadMsgData(msgData, msg_0254_00000);
    PlayerName_StringToFlat(profile, name);
    PlayerProfile_SetTrainerGender(profile, PLAYER_GENDER_MALE);
    String_Delete(name);
    DestroyMsgData(msgData);

    return TRUE;
}

BOOL ov36_TitleScreen_NewGame_AppExit(OverlayManager *man, int *state) {
#pragma unused(man, state)
    Heap_Destroy(HEAPID_OV36);
    RegisterMainOverlay(FS_OVERLAY_ID(OVY_36), &ov36_App_InitGameState_AfterOakSpeech);

    return TRUE;
}
```

The gender has to be set here, before `InitGameStateAfterOakSpeech_Internal` runs: it
picks the welcome mail's sender from it. The rival name stays empty, as it is after the
normal speech. `msg_0254_00000` is the first HeartGold boy name; use any message, or
build the name another way.

## 11. How to change the credits

**Text.** Edit `msg_0440.json` in place (ids are positions). Ids 00253-00300 are
`"garbage": 0` placeholders that no line uses; replace one with an `en_US` string for a
new line.

**Where a line goes.** `sCreditMsgLines` entries are `{ page, x, y, msgno }`, in pixels
in a 24×24-tile window; the lines of one page must be next to each other and pages in
order, since `LoadPage` (credits.c:901) reads forward until the page number changes.
Page 0 is the title page, printed from `GAME_TITLE_MSG_NO` at start.

**Timing.** `sPageTimings[n] = { startTime, duration }` in frames since the credits
began. A page shows only if the previous page has finished (its `startTime + duration`
plus a frame or two to hide) **before** this page's `startTime`; the check is an exact
`==` on the frame (`HandlePageDisplay`, line 663), so a late page and every page after
it are never shown. The original gaps are 3-10 frames.

**Adding pages.** Raise `NUM_CREDIT_PAGES` ([include/credits/credits.h](../../include/credits/credits.h)),
add a timing, add the lines, and fix the array size of `sCreditMsgLines`. Keep the last
page ending before `CREDITS_FRAMES`, or raise `CREDITS_FRAMES`. The page timings,
scene changes and cutscene start frames were all set to `SEQ_GS_ENDING`; if the
credits run longer than the song, the song ends first.

**Always skippable.** Remove `work->args->gameCleared &&` from the skip check at
line 318.

**No credits at all.** In `Task_GameClear` ([src/game_clear.c:240](../../src/game_clear.c#L240)),
state 10, skip `Credits_LaunchApp` and go to the reset. The save, Hall of Fame entry and
`FLAG_GAME_CLEAR` happen before, so they are kept.

## 12. Pitfalls

- **The screens are swapped** in the movie, the title screen and the credits
  (`gSystem.screensFlipped`). On the title screen the "sub" layers are the top screen.
- **Oak's speech saves nothing until its `exit`.** If you leave it early (a new path, a
  crash), the name and gender in the save are the wiped values.
- **The rival name is overwritten with an empty string** by `OakSpeech_Exit`. A rival
  name set in `NewGame_InitSaveData` is lost; set it after the speech (in
  `InitGameStateAfterOakSpeech_Internal`) or in the `init` script.
- **`TOUCHTOADVANCE_SHOW` / `_HIDE` assert** that the button is in the other state.
  When you skip states, keep the shows and hides paired; asserts are silent in a
  release build ([debugging.md](debugging.md)), so a mismatch shows as a missing or
  stuck Touch button, not a crash.
- **Credits pages time out silently**: a page that can't start on its exact frame is
  skipped with every page after it (§11).
- **Changing the starters doesn't change the movie** (pictures, §2), and the title
  screen's Ho-Oh / Lugia is a 3D model, not the species.
- The credits always reset the console at the end. Code that expects to come back to
  the field after `hofcredits` never runs.

## Where to look

| File | What |
|---|---|
| [src/main.c](../../src/main.c#L73) | boot: the first application |
| [src/intro_movie.c](../../src/intro_movie.c) | the movie driver, skip check, scene list |
| [src/intro_movie_scene_1.c](../../src/intro_movie_scene_1.c) … [_5.c](../../src/intro_movie_scene_5.c), [intro_movie_scenes_lib.c](../../src/intro_movie_scenes_lib.c) | the scenes and their shared effects |
| [files/demo/opening/gs_opening/](../../files/demo/opening/gs_opening/) | movie graphics and 3D towns |
| [src/title_screen.c](../../src/title_screen.c), [include/title_screen.h](../../include/title_screen.h) | title screen; exit modes |
| [files/demo/title/titledemo/](../../files/demo/title/titledemo/) | title graphics (PNG logo and backgrounds) and 3D models |
| [src/overlay_36.c](../../src/overlay_36.c) | New Game, after Oak, Continue |
| [src/oaks_speech.c](../../src/oaks_speech.c), [oaks_speech_obj.c](../../src/oaks_speech_obj.c), [oaks_speech_yesnomenu.c](../../src/oaks_speech_yesnomenu.c) | Oak's speech |
| [files/demo/intro/intro/](../../files/demo/intro/intro/) | Oak's speech graphics |
| [files/msgdata/msg/msg_0219.json](../../files/msgdata/msg/msg_0219.json) | Oak's speech text |
| [src/game_clear.c](../../src/game_clear.c#L156) | Hall of Fame → save → credits → reset |
| [src/credits/credits.c](../../src/credits/credits.c), [include/credits/data.h](../../include/credits/data.h) | the credits and their tables |
| [files/msgdata/msg/msg_0440.json](../../files/msgdata/msg/msg_0440.json) | credits text |
| [files/a/2/6/3](../../files/a/2/6/3) | credits graphics |

## Not verified

The recipes in §6-§11 were written from the code; none of them was built or tried in
game. In particular:

- Skipping the title screen (§7): whether the main menu starts its own music, and
  whether anything there expects the title screen's fade state.
- Skipping the info menu (§9): whether the bottom screen looks right with only the
  background loaded.
- The fixed-name path (§9): going from the gender confirmation to `CONFIRM_NAME_YES`
  without the naming screen's teardown and rebuild of the graphics.
- Skipping Oak's speech (§10): that nothing else in the speech's `exit` path is needed
  (for example `TextFlags_SetCanTouchSpeedUpPrint`).
- The fixed-gender path (§9): the bottom screen after the naming screen still loads
  the gender-select background (`OakSpeech_CreateMultichoiceYesNoMenu`), which may
  look odd when the gender was never asked.
- Which sprite resources in `resdat` hold Marill.
