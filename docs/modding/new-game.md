<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# New game: start location, starting state, starter choice

> AI-generated; not affiliated with pret. See AI.md at the repository root.

What the game sets up when you pick New Game, in order, and how to change the start
location, what the player starts with (money, items, Pokémon, flags), and the three
starters.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `NewGameInitData()` in `src/new_game.c` | `NewGame_InitSaveData` and `InitGameStateAfterOakSpeech_Internal` in [src/overlay_36.c](../../src/overlay_36.c) |
| `WarpToTruck()` / `SetWarpDestination(MAP_INSIDE_OF_TRUCK, ...)` | `sLocation_PlayerRoom` in [src/location_backup.c](../../src/location_backup.c) |
| `SetMoney(&gSaveBlock1Ptr->money, 3000)` | `PlayerProfile_SetMoney(..., 3000)` in `NewGame_InitSaveData` |
| `ScriptContext_SetupScript(EventScript_ResetAllMapFlags)` | the `init` script, [files/fielddata/script/scr_seq/scr_seq_0149.s](../../files/fielddata/script/scr_seq/scr_seq_0149.s) |
| `sStarterMon[]` in `src/starter_choose.c` | `species[]` in [src/choose_starter.c](../../src/choose_starter.c) **and** `sSpecies[]` in [src/choose_starter_app.c](../../src/choose_starter_app.c) |
| `VAR_STARTER_MON` (0, 1, 2) | `VAR_PLAYER_STARTER` (the starter's **species number**) |

## 1. What happens on New Game

| Step | Where | What it does |
|---|---|---|
| 1 | `NewGame_InitSaveData`, [src/overlay_36.c:251](../../src/overlay_36.c#L251) | wipes the save (`Save_InitDynamicRegion`: every save chunk's init function), puts you in your room, sets ¥3000, the Magikarp length record to 56150 (3'6"), and `FLAG_UNK_960` |
| 2 | Prof. Oak's intro, [src/oaks_speech.c](../../src/oaks_speech.c) (overlay 53) | gender and name (`OakSpeech_Exit`, line 643). The greeting depends on the DS clock (`OakSpeech_GetTimeOfDayIntroMsg`, line 1477). Text is `msg_0219`. Changing or skipping it: [intro-title-credits.md](intro-title-credits.md#4-professor-oaks-speech) |
| 3 | `InitGameStateAfterOakSpeech_Internal`, [src/overlay_36.c:180](../../src/overlay_36.c#L180) | RTC, random trainer id (32 bits: TID and SID), Safari Zone default areas, a random Union Room avatar, grows every Apricorn tree, Pokéwalker seeds, the welcome mail in the PC (below); starts the play-time counter |
| 4 | `CallFieldTask_NewGame`, [src/field_warp_tasks.c:410](../../src/field_warp_tasks.c#L410) | runs the `init` script once (§3), then loads the map you start on |
| 5 | `NewBark_PlayerHouse_1F` | Mom's intro and the rest of the story; see [story-progression.md](story-progression.md#story-beats) |

Continue takes another path (`ov36_App_MainMenu_SelectOption_Continue`), so nothing in
steps 1, 3 and 4 runs again on a loaded save.

Defaults that come from the save chunks' init functions, not from the new-game code:

| What | Value | Where |
|---|---|---|
| Options | text speed mid, stereo, battle style Shift, animations on, frame 1 | `Options_Init`, [src/options.c:18](../../src/options.c#L18) |
| Whiteout point | your house (spawn id 1, `GetMomSpawnId`) | `Save_LocalFieldData_Init`, [src/save_local_field_data.c:46](../../src/save_local_field_data.c#L46) |
| Party, bag, PC, Pokédex | empty | each chunk's init clears it |
| Rival's name | empty until you name him at Elm's lab (`namerival`, `NewBark_ElmsLab_1F:869`) | |
| Vars | all 0 (the new-game code sets none) | |

The welcome mail is built in C (`overlay_36.c:211-240`): Air Mail from your friend
(Lyra or Ethan, from `msg_0445`, chosen by your gender) with a Marill picture and two
easy-chat lines, `sMailMsgTemplates`.

## 2. Start location

`NewGame_InitSaveData` calls `Save_SetPositionToPlayerRoom`, which copies
`sLocation_PlayerRoom` ([src/location_backup.c:10](../../src/location_backup.c#L10)) into
the saved current position:

```c
static const Location sLocation_PlayerRoom = {
    .mapId = MAP_NEW_BARK_PLAYER_HOUSE_2F,
    .warpId = 0xFFFFFFFF,   // -1: use x/y, not a warp
    .x = 0x00000006,
    .y = 0x00000006,
    .direction = 0x00000001, // DIR_SOUTH
};
```

To start somewhere else, change `mapId`, `x`, `y` and `direction`. Coordinates are
global tiles over the map's matrix ([maps-and-warps.md](maps-and-warps.md#coordinates));
for a one-cell interior they equal the local ones. `mapkit show <Map>` prints them for
every event, so copying a warp's or an object's coordinates is the easy way. Directions
are `DIR_NORTH` 0, `DIR_SOUTH` 1, `DIR_WEST` 2, `DIR_EAST` 3
([include/constants/global_fieldmap.h](../../include/constants/global_fieldmap.h)).

The same table is used after the credits: `game_clear.c:290` sets the warp to
`sLocation_PlayerRoom` and the whiteout spawn to `sLocation_OutsidePlayerHome` (New Bark,
695, 397). Changing `sLocation_PlayerRoom` therefore also changes where you wake up after
the Hall of Fame. If you only want the new-game start to move, write a new `Location`
and use it in `Save_SetPositionToPlayerRoom` only.

Things that assume you start at home:

- Mom's intro runs as a frame script on `NewBark_PlayerHouse_1F`
  (`VAR_SCENE_PLAYERS_HOUSE_1F == 0`). It gives the Bag, Trainer Card, Save and Options
  (`FLAG_GOT_BAG` and the others): without them the start menu has none of those
  entries. Starting elsewhere means setting those flags yourself (§3).
- The whiteout point stays your house until you enter a Pokémon Center.

## 3. Starting flags, items, money and Pokémon

There are two places to set up the starting state. Both run once, only on New Game.

### The `init` script (flags, vars, items, Pokémon)

`RunInitScript` ([src/script_manager.c:576](../../src/script_manager.c#L576)) runs
standard script `_std_init` (9600), which is
[files/fielddata/script/scr_seq/scr_seq_0149.s](../../files/fielddata/script/scr_seq/scr_seq_0149.s).
It is written in assembler macros (`asm/macros/script.inc`), not poryscript. Retail sets
143 flags in it, nearly all `FLAG_HIDE_*` for characters who appear later (the rival in
Cherrygrove, the Bell Tower Ho-Oh, Lance at the Lake of Rage...), plus `LotoIDSet` (picks
the first Lucky Number) and a few story flags (`FLAG_AZALEA_ROCKET_HARASSING_CIVILIAN`,
`FLAG_UNK_1A0`, `FLAG_UNK_229`, `FLAG_UNK_2DE`).

Add your own lines before `End`:

```asm
scr_seq_0149_000:
	SetFlag FLAG_HIDE_ELMS_LAB_OFFICER
	...
	SetFlag FLAG_GOT_BAG                    ; example: any flag
	SetVar VAR_SCENE_PLAYERS_HOUSE_1F, 1    ; example: skip Mom's intro
	GiveItem ITEM_POTION, 5, VAR_SPECIAL_RESULT
	GiveMon SPECIES_PIKACHU, 5, ITEM_NONE, 0, 0, VAR_SPECIAL_RESULT
	End
```

`GiveItem` is `(item, count, result var)`; `GiveMon` is `(species, level, held item, form,
ability, result var)`. Each command's arguments are in
[script-commands-list.md](script-commands-list.md).

Only use commands that finish at once. `StartMapLoadScript` runs the script to the end in
one loop, with no frames in between ([src/script_manager.c:580](../../src/script_manager.c#L580)),
so messages, movements, fades, `wait` and anything that opens a screen never finish.
Flags, vars, `GiveItem`, `GiveMon`, `AddMoney` and other plain data commands are fine.

Skipping Mom's intro this way also skips its flags; set `FLAG_GOT_BAG`,
`FLAG_GOT_TRAINER_CARD`, `FLAG_GOT_SAVE_BUTTON` and `FLAG_GOT_OPTIONS_BUTTON` too
(`NewBark_PlayerHouse_1F:51-64`), or the start menu is nearly empty.

### C (money and anything without a script command)

Change `NewGame_InitSaveData` ([src/overlay_36.c:251](../../src/overlay_36.c#L251)):

- money: the `3000` in `PlayerProfile_SetMoney`;
- anything else on the save: get its block with the `Save_*_Get` functions, as the code
  already does for the PC mail and the Apricorn trees in
  `InitGameStateAfterOakSpeech_Internal`.

`NewGame_InitSaveData` runs before Oak's intro, so the player's name, gender and trainer
id are not set yet. Anything that records the OT (a Pokémon) belongs in
`InitGameStateAfterOakSpeech_Internal` or in the `init` script.

`FLAG_UNK_960` is set here and by script command 298 (`SetFlagUnk960`); command 297
reads it. No retail script uses either command, so it appears to be unused.

## 4. The starter

### How it is chosen

1. The lab machine (`NewBark_ElmsLab_1F_EventScript_PC1`,
   [data/maps/NewBark_ElmsLab_1F/scripts.pory:192](../../data/maps/NewBark_ElmsLab_1F/scripts.pory#L192))
   runs `choosestarter`, then sets `FLAG_GOT_STARTER`.
2. `choosestarter` → `LaunchStarterChoiceScene` →
   `CreateStarter` ([src/choose_starter.c:31](../../src/choose_starter.c#L31)) builds the
   three Pokémon: level 5, random IVs, no held item, Poké Ball, met here
   (`MonSetCatchData`; its `12` is the encounter type, not a level).
3. The selection screen ([src/choose_starter_app.c](../../src/choose_starter_app.c),
   overlay 61) shows them on a turntable and returns the cursor position.
4. The chosen one goes into the party and is marked caught in the Pokédex.
5. Back in the script: `getpartymonspecies(0, VAR_TEMP_x4001)` and
   `setstarterchoice(VAR_TEMP_x4001)` store the starter's **species** in
   `VAR_PLAYER_STARTER`; then the nickname prompt. `VAR_SCENE_ELMS_LAB` becomes 1 at
   line 274.

`placestarterballsinelmslab` (`ScrCmd_PlaceStarterBallsInElmsLab`,
[src/scrcmd_c.c:4765](../../src/scrcmd_c.c#L4765)) draws 3, 2, 1 or 0 balls on the
machine (before the starter, after it, after meeting the rival, after Falkner's TM51).
They are decoration; the species are not read from them.

### Changing the three species

Change **both** lists, in the same order (left, right, back):

| File | Table | Used for |
|---|---|---|
| [src/choose_starter.c:48](../../src/choose_starter.c#L48) | `species[]` in `CreateStarter` | the Pokémon you get, and the front sprites on the screen (read from the Pokémon) |
| [src/choose_starter_app.c:307](../../src/choose_starter_app.c#L307) | `sSpecies[]` | the cry when you touch a ball |

To change the level, IVs or held item, edit the `CreateMon(mon, species[i], 5, USE_RANDOM_IVS, ...)`
call and the `ITEM_NONE` below it in `CreateStarter`.

The species names in the selection text are written into `msg_0190`
([files/msgdata/msg/msg_0190.json](../../files/msgdata/msg/msg_0190.json)), not looked
up: entries 1-3 are Elm's question ("So, you like CHIKORITA, the Grass-type Pokémon?"),
4-6 the label shown while a ball is highlighted. Edit them to match. `{COLOR n}` picks
the name's color (retail uses 3, 1, 2 to match each type); see
[text-and-messages.md](text-and-messages.md).

The ball models and turntable are fixed 3D models
(`files/application/choose_starter/choose_starter_main_res`); the screen always has
three slots.

### The rival's team

`VAR_PLAYER_STARTER` holds a species number, and the rival scripts compare it against
numbers written in the scripts: 152 (Chikorita) and 155 (Cyndaquil), with "anything else"
meaning Totodile. The rival takes the starter strong against yours:

| Your starter | Rival's | Trainer picked |
|---|---|---|
| 152 Chikorita | Cyndaquil line | the `== 152` branch |
| 155 Cyndaquil | Totodile line | the `== 155` branch |
| other (Totodile) | Chikorita line | the `else` branch |

Every place that does this (they read the var through `getstarterchoice`, so search for
that, not for the var name):

| Map script | Battle |
|---|---|
| `Cherrygrove:511` | first battle (`TRAINER_PASSERBY_BOY`, `_2`, `_3`) |
| `Azalea:103` | `TRAINER_RIVAL_SILVER_7` / `_10` / `TRAINER_RIVAL_SILVER` |
| `BurnedTower_1F:31` | `TRAINER_RIVAL_SILVER_8` / `_11` / `_4` |
| `Goldenrod_Tunnel_B2F:326` | `TRAINER_RIVAL_SILVER_18` / `_12` / `_17` |
| `VictoryRoad_3F:44` | `TRAINER_RIVAL_SILVER_9` / `_13` / `_5` |
| `MountMoon:27` | `TRAINER_RIVAL_SILVER_15` / `_16` / `_14` |
| `PokemonLeagueEntrance:108` | `TRAINER_RIVAL_SILVER_20` / `_21` / `_19` |
| `DragonsDen:32` | the Lance/Clair multi battle; sets the rival's follower sprite (`VAR_OBJ_0` = `SPRITE_FOLLOWER_MON_STATIC_MEGANIUM`/`TYPHLOSION`/`FERALIGATR`) and the partner trainer (line 408) |

If you change the starters, change the 152 and 155 in each of these to your first two
species, and the rival's parties in
[files/poketool/trainer/trainers.json](../../files/poketool/trainer/trainers.json)
([trainers.md](trainers.md)). If you only reorder the three, the comparisons still work
by species.

Other users of `VAR_PLAYER_STARTER`:

- `bufferstarterspeciesname` (command 203) puts your starter's species name in a string
  buffer.
- `DPPtLeftover_GetRivalSpecies` / `DPPtLeftover_GetFriendStarterSpecies`
  ([src/sys_vars.c:63](../../src/sys_vars.c#L63)) and their buffer commands (204, 205,
  847) are Diamond/Pearl leftovers that compare against Turtwig, Chimchar and Piplup; with
  Johto starters they always give Turtwig and Chimchar. No HGSS script uses them.

### Kanto starters

Oak's Kanto starter after Red is a separate gift in
`data/maps/Pallet_TownOaksLab/scripts.pory` (`showpokemonpicwindow` for each of the
three at lines 713-774, then `givemon(VAR_SPECIAL_x8004, 5, ...)` at line 815; gated by
`VAR_UNK_4131`, see [story-progression.md](story-progression.md#elite-four-and-game-clear)).
It doesn't use this screen or `VAR_PLAYER_STARTER`.

## Not verified

- `GiveMon` and `GiveItem` in the `init` script: they finish at once (both return
  `FALSE`), and the profile is set by then, but whether `GiveMon` sees the right met
  location before the first map is loaded was not checked in game.
- That the Pokédex counts a Pokémon given in the `init` script as seen and caught (the
  starter code marks it by hand with `Pokedex_SetMonCaughtFlag`).
- Starting on a map other than your house was only read in the code, not tried.
