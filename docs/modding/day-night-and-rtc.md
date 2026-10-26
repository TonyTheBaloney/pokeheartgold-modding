<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Day and night, and the real-time clock

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers how the game reads the DS clock (the RTC), the five times of day and
their hours, everything that changes with the time (lighting, music, encounters,
evolutions, scripts...), what happens when a day or a minute passes, and the penalty for
changing the clock. It ends with recipes for common changes.

HGSS has no in-game clock setting: the time is always the DS system clock.

If you know pokeemerald (`src/rtc.c`, `gLocalTime`, which only counts days for berries and
daily events):

| pokeemerald | here |
|---|---|
| `RtcCalcLocalTime`, `gLocalTime` | `GF_RTC_CopyDateTime` (the hardware clock) and `SysInfo_RTC` (a copy in the save) |
| no day/night | five times of day, `RTC_TIMEOFDAY_*` (§2) |
| `DoTimeBasedEvents` → `UpdatePerDay` / `UpdatePerMinute` | `FieldSystem_StartBugContestTimer` → `FieldSystem_HandleDaysPassed` / `FieldSystem_HandleMinutesPassed` (§5) |
| `ClearDailyFlags` (`DAILY_FLAGS_START`) | `ClearDailyFlags` (`DAILY_FLAG_BASE`, 192 flags) |
| time-of-day tints (later pokeemerald hacks) | 3D lighting from a text file per hour range (§4) |

The files:

| File | What |
|---|---|
| [include/gf_rtc.h](../../include/gf_rtc.h), [src/gf_rtc.c](../../src/gf_rtc.c) | reading the hardware clock, the hour → time of day table |
| [include/sav_system_info.h](../../include/sav_system_info.h), [src/sav_system_info.c](../../src/sav_system_info.c) | the clock saved in the save file (`SysInfo_RTC`), the penalty |
| [src/field_time_events.c](../../src/field_time_events.c) | syncing the saved clock, day-change and minute events, `Field_GetTimeOfDay` |
| [src/field/area_light.c](../../src/field/area_light.c) | the 3D lighting by time |
| `files/data/area00light.txt` and the other `*light.txt` | the lighting data (§4) |
| [src/field/map_prop_render.c](../../src/field/map_prop_render.c), [src/field/field_shadow.c](../../src/field/field_shadow.c) | props and shadows that change with the time |
| [src/overlay_36.c](../../src/overlay_36.c) | new game and Continue: initialising the saved clock, the penalty |

## 1. Two clocks: the hardware and the save

**The hardware clock.** `GF_InitRTCWork` (called once from `main.c`) starts it, and
`GF_RTC_UpdateOnFrame` (every frame in `main.c`) asks the DS for the date and time every
10 frames, asynchronously. The result sits in `sRTCWork`. These read it:

| Function | Returns |
|---|---|
| `GF_RTC_CopyDateTime`, `GF_RTC_CopyDate`, `GF_RTC_CopyTime` | `RTCDate` (year 0-99 = 2000-2099, month, day, `week` 0 = Sunday), `RTCTime` (hour, minute, second) |
| `GF_RTC_TimeToSec` | seconds since midnight |
| `GF_RTC_DateTimeToSec` | seconds since 2000-01-01 |
| `GF_RTC_GetTimeOfDay`, `GF_RTC_GetTimeOfDayWildParam`, `IsNighttime` | the time of day from the current hour (§2) |

**The saved clock.** `SysInfo_RTC`, inside the `SAVE_SYSINFO` block
([save-data.md](save-data.md)), keeps:

| Field | Meaning |
|---|---|
| `initialized` | set at new game |
| `date`, `time` | the last time the field synced (below) |
| `days_since_nitro_epoch` | the last day number seen (days since 2000-01-01); a larger one means a new day |
| `seconds_since_nitro_epoch` | when the adventure started (the Trainer Card's "Adventure Started"; `FieldSystem_GetAdventureStartTime`) |
| `seconds_at_game_clear` | when the player entered the Hall of Fame (`FieldSystem_SetGameClearTime`) |
| `penaltyInMinutes` | the clock-change penalty (§6) |

`FieldSystem_StartBugContestTimer` (misnamed: it syncs the saved clock and has nothing
specific to do with the Bug Contest) copies the hardware clock into `date` and `time` and
runs the day and minute events (§5). It is called:

- every field frame while no field task is running (`FieldMap_UpdateFrame` in
  [src/field/fieldmap.c](../../src/field/fieldmap.c)), so not while a script, a menu or a
  warp is running;
- on warps (not on walking across a map connection), in
  [src/field_warp_tasks.c](../../src/field_warp_tasks.c);
- when the Bug Contest starts.

These read the **saved** clock instead of the hardware:

| Function | Returns |
|---|---|
| `Field_GetTimeOfDay`, `Field_GetTimeOfDayWildParam` | the time of day from the saved hour |
| `Field_GetHour`, `Field_GetDay`, `Field_GetMonth` | the saved hour, day of month, month |

The two agree except while a field task runs: a script that starts at 19:59 still reads
`EVE` from `getcurrenttimeofday` at 20:01, until it ends. Most of the time the difference
doesn't matter; pick either.

## 2. The times of day

`GF_RTC_GetTimeOfDayByHour` ([src/gf_rtc.c](../../src/gf_rtc.c)) maps each hour through
`sTimeOfDayByHour[24]`:

| `TIMEOFDAY` | Value | Hours | `TimeOfDayWildParam` | `IsNighttime()` |
|---|---|---|---|---|
| `RTC_TIMEOFDAY_MORN` | 0 | 4:00-9:59 | `TIMEOFDAY_WILD_MORN` (0) | FALSE |
| `RTC_TIMEOFDAY_DAY` | 1 | 10:00-16:59 | `TIMEOFDAY_WILD_DAY` (1) | FALSE |
| `RTC_TIMEOFDAY_EVE` | 2 | 17:00-19:59 | `TIMEOFDAY_WILD_DAY` (1) | FALSE |
| `RTC_TIMEOFDAY_NITE` | 3 | 20:00-23:59 | `TIMEOFDAY_WILD_NITE` (2) | TRUE |
| `RTC_TIMEOFDAY_LATE` | 4 | 0:00-3:59 | `TIMEOFDAY_WILD_NITE` (2) | TRUE |

So there are three views of the same table: five periods, three for wild Pokémon
(morning/day/night) and two (day/night) for `IsNighttime`. Changing
`sTimeOfDayByHour` changes all three.

Not everything uses the table. These have their own hours and **won't follow** a change
to it:

- the outdoor lighting, whose times are in `area00light.txt` (§4);
- Shaymin's Sky Forme, which reverts when a sync (§1) finds the clock has passed 20:00,
  or that the time skipped since the last sync reaches back into 20:00-3:59
  (`Party_TryResetShaymin` in [src/pokemon.c](../../src/pokemon.c), hard-coded `20` and `4`).

## 3. What changes with the time

| What | Reads | Where | How it varies |
|---|---|---|---|
| Wild grass Pokémon | hardware, 5 periods | `EncSlotArray_Init_Land` in [src/field/encounter_check.c](../../src/field/encounter_check.c) | `morn` / `day` (day and evening) / `nite` species in the encounter table ([wild-encounters.md](wild-encounters.md)) |
| Night fishing | hardware | `EncSlotArray_Update_NightFishing` | `nightFish` replaces Good Rod slot 3 and Super Rod slot 1 at night and late night |
| Safari Zone encounters | hardware, wild param | `FieldSystem_GenerateSafariEncounter` | morning / day / night slots |
| Map music | hardware, `IsNighttime` | `FieldBGM_GetForMapHeader` in [src/field_bgm.c](../../src/field_bgm.c) | `music_day` / `music_night` in `map.json` ([music.md](music.md)); chosen when entering a map |
| 3D lighting | hardware, seconds | [src/field/area_light.c](../../src/field/area_light.c) | §4; changes while you stand still |
| Props (lit windows etc.) | hardware, 4 states | `TimeOfDayPropAnimManager_Update` in [src/field/map_prop_render.c](../../src/field/map_prop_render.c) | §4 |
| Shadows under people | hardware, 5 periods | `sShadowAlphaByTimeOfDay`, `sShadowScaleByTimeOfDay` in [src/field/field_shadow.c](../../src/field/field_shadow.c) | darker and longer by day, faint at night; fades over |
| Map name image on entering | hardware, 4 states | `MapPreviewGraphic_BeginShowImage` in [src/map_preview_graphic.c](../../src/map_preview_graphic.c) | a picture per period |
| Battle background | saved, 3 states | `setup->timeOfDay` in [src/battle/battle_setup.c](../../src/battle/battle_setup.c); `BattleSystem_GetBgTimeOfDay` in [src/battle/battle_system.c](../../src/battle/battle_system.c) | day / evening / night palette, only for backgrounds 0-5 (`BATTLE_BG_GENERAL` to `BATTLE_BG_SNOW`) |
| Dusk Ball | saved | `ITEM_DUSK_BALL` in [src/battle/battle_command.c](../../src/battle/battle_command.c) | bonus at night, late night or in a cave |
| Evolutions | hardware, `IsNighttime` | `GetMonEvolution` in [src/pokemon.c](../../src/pokemon.c) | `EVO_FRIENDSHIP_DAY/_NIGHT`, `EVO_ITEM_DAY/_NIGHT` ([evolutions.md](evolutions.md)) |
| Phone rematches, calls | saved / call time | `ScrCmd_GetPhoneBookRematch`, [src/application/pokegear/phone/](../../src/application/pokegear/phone/) | which trainers want a rematch, what they say ([trainers.md](trainers.md)) |
| Pokégear map | hardware, wild param | `PokegearMap_MapHasPhoneRematchOrGift` in [pokegear_map_view.c](../../src/application/pokegear/map/pokegear_map_view.c) | which maps are marked for a rematch or gift |
| Following Pokémon | saved | `FollowMonSituation_SetTimeOfDay` in [src/field/follow_mon_interaction.c](../../src/field/follow_mon_interaction.c) | what it says when you talk to it |
| In-game and wireless trades | saved | [src/npc_trade.c](../../src/npc_trade.c), `launch_application.c` | the trade screen's background |
| Legendary cinematics, Magnet Train, ship | saved | [legendary_cinematic_task.c](../../src/legendary_cinematic_task.c), [magnet_train_ride.c](../../src/magnet_train_ride.c), [ship_voyage.c](../../src/ship_voyage.c) | lighting of the scene |
| Map scripts | see below | `scripts.pory` | anything (§7) |

By date rather than time:

| What | Where |
|---|---|
| Diamond Dust on Mt. Silver's summit on 8 dates | `DiamondDustDates` in [src/field_system_rtc_weather.c](../../src/field_system_rtc_weather.c); off during the penalty |
| Shorter egg cycles on 12 dates | `sEggCycleSpecialDates` in [src/get_egg.c](../../src/get_egg.c); off during the penalty |
| Player's birthday | `CheckIsPlayerBirthday(VAR)` (`ScrCmd_CheckIsPlayerBirthday`), compares with the DS profile's birthday |
| Pokéathlon Dome shop by weekday | `sDecorationMartItems[date.week]` in [src/scrcmd_mart.c](../../src/scrcmd_mart.c) |
| Bug Contest days, weekday siblings, Mt. Moon Square... | scripts, with `getweekday` |

## 4. Lighting and time-of-day props

### The light files

Each area (map.json `area_data` → area header `files/a/0/4/2`, see
[maps-and-warps.md](maps-and-warps.md)) has a `lightKind` byte that picks a light file:

| `lightKind` | File | Used by | Changes with time? |
|---|---|---|---|
| 1 | `files/data/area00light.txt` | outdoor areas (133 maps: towns, routes, Ilex Forest...) | yes, 14 periods |
| 0 | `files/data/area01light.txt` | indoor areas and caves (406 maps) | no: every entry is the same |
| 2 | `files/data/dun20_01light.txt`, or `dun20_02light.txt` once `FLAG_UNK_96A` is set | Olivine Lighthouse top (Amphy's room) | no, one entry. `LighthouseLightUp` in [src/field/script_field_effects.c](../../src/field/script_field_effects.c) switches to `_02` when Amphy is healed |
| (none) | `files/data/area02light.txt` | unused | |

`AreaDataManager_GetAreaLightArchiveID` ([src/field/area_data.c](../../src/field/area_data.c))
does the mapping. The lighthouse swap is in `FieldMap_InitCameraAndEnvironment`
([src/field/fieldmap.c](../../src/field/fieldmap.c)). The area header is binary; nothing
in this repo edits `lightKind` yet.

The files are plain text built into the ROM as they are (`prebuilt_files` in
`files/data/meson.build`), so editing them is enough.

**Format.** A list of entries, then a line `EOF`. Each entry is 10 lines:

```
7200,                            end time, in units of 2 seconds since midnight (7200 = 4:00, 43200 = 24:00)
1,11,11,16,-1914,-3548,-296,     light 0: on (1/0), colour r,g,b (0-31), direction x,y,z (4096 = 1.0)
0,0,0,0,0,0,0,                   light 1 (off)
1,0,0,6,0,0,4096,                light 2
0,0,0,0,0,0,0,                   light 3
14,14,16,                        material diffuse r,g,b
10,10,10,                        ambient
14,14,16,                        specular
8,8,11,                          emission
                                 (blank)
```

- Lines must end in CR (`\r`); the parser (`AreaLight_LoadEntries`, `Ascii_GetDelim`)
  splits on it. The files are CRLF now. An editor that saves LF only breaks them.
- Each entry applies **until** its end time, from the previous entry's end time. The game
  uses the first entry whose end time is after now (`GF_RTC_TimeToSec() / 2`), and moves
  to the next while the field runs (`AreaLightManager_UpdateActiveTemplate`, every frame).
- The entries must be in increasing order and the last should end at `43200`.
- The first entry of `area00light.txt` (end time `0`) is never used, apart from one frame
  after midnight. Leave it in place.
- Light directions are clamped to ±4096. A light that is off has colour and direction 0.
- There is no fading between entries: area00 uses short entries (30 minutes) around dawn
  and dusk to make the change gradual.

The outdoor schedule, from `area00light.txt` (light 0's colour, the "sun"):

| Hours | Light 0 r,g,b |
|---|---|
| 0:00-4:00 | 11,11,16 (night) |
| 4:00-4:30, 4:30-5:00 | 12,12,18; 12,12,22 |
| 5:00-8:00 | 15,15,22 (morning) |
| 8:00-11:30, 11:30-12:00 | 18,18,21; 22,22,20 |
| 12:00-15:00 | 24,24,20 (noon) |
| 15:00-15:30, 15:30-17:00 | 22,22,18; 20,18,16 |
| 17:00-18:00, 18:00-18:30, 18:30-19:00 | 19,16,12; 17,13,10; 16,13,10 (evening) |
| 19:00-20:00 | 11,12,15 |
| 20:00-24:00 | 11,11,16 (night) |

`LoadAreaOrDungeonLightTxt` lights the Magnet Train and ship cutscenes once from
`area00light.txt`.

### Props that change with the time

Some props (building windows, lamps) play one of four animations by time: morning, day,
evening, night (night and late night share one; `sTimeOfDayVisualState` in
[src/field/map_prop_render.c](../../src/field/map_prop_render.c)). A prop does this when
its animation list file (NARC `a/1/0/7` outdoors, `a/1/0/8` indoors) has `flags == 8`
and four animations (`MapPropAnimationManager_LoadPropAnimations` in
[src/field/map_prop_animation.c](../../src/field/map_prop_animation.c)). At most 4 such
props per area. These files are binary.

## 5. When a day or minutes pass

Each sync (§1) compares the hardware clock with the saved one
(`FieldSystem_CheckDayChange`, `FieldSystem_CheckTimeAdvance` in
[src/field_time_events.c](../../src/field_time_events.c)):

- **Day number larger** than the saved one: `FieldSystem_HandleDaysPassed(days)` runs
  once, with the number of days. A new day is a new calendar date at midnight, not 24
  hours of play.
- **At least a minute later**: `FieldSystem_HandleMinutesPassed(minutes)`, and the penalty
  goes down by that many minutes (§6).
- **Clock earlier** than the saved one (the player set it back): the saved values are
  overwritten and nothing runs. Setting the clock back and then forward again replays the
  days.

`FieldSystem_HandleDaysPassed` does, in order:

| Call | Effect |
|---|---|
| `ClearDailyFlags` ([src/script_manager.c](../../src/script_manager.c)) | clears the 192 daily flags, `0xAA0`-`0xB5F` (`DAILY_FLAG_BASE`, `FLAG_DAILY_*`) |
| `Save_DullBadges` | badges lose shine (polishing them in the Trainer Card) |
| `Save_FriendGroup_AdvanceSeeds`, `Roamers_SetRand` | the daily random numbers, which pick the day's swarm ([roamers.md](roamers.md)) |
| `Party_UpdatePokerus` | Pokérus counts down |
| `Save_LCRNGAdvanceLotoID` | the Lucky Number Show number |
| `Save_VarsFlags_RandomizeVar4041` | `VAR_UNK_4041` (unused by scripts) |
| `BattleTower_InitSeed` | Battle Frontier seed |
| `WiFiHistory_UpgradeAllLocationsState` | GTS / Wi-Fi location history |
| `FieldSystem_RegrowApricornTrees` | Apricorns regrow |
| `PhoneCallPersistentState_BlackBeltKenji_UpdateWaitDays` | Kenji's training trip |
| `ApricornBox_AddJuiceMildnessForDays` | Apricorn juice (**skipped during the penalty**) |
| `SaveData_SafariZone_CheckAreasWithUpdatedEncounters` | Safari Zone block counts (**skipped during the penalty**) |
| `PokeathlonSave_ResetDailyItemsBought` | Pokéathlon daily shop |
| `Save_VarsFlags_UpdateBuenasPasswordSet` | Buena's password |

`FieldSystem_HandleMinutesPassed` advances the phone's ring timer, the Bug Contest timer,
and reverts Sky Forme Shaymin (§2).

Berry pots keep their own timestamp (`Save_BerryPotRTC_Get`) and catch up only when their
screen opens (`BerryPotsApp_UpdateGrowthFromRTC` in
[src/berry_pots_app_tasks.c](../../src/berry_pots_app_tasks.c)).

## 6. Changing the clock: the penalty

The save records the console's MAC address and its **RTC offset**
(`OS_GetOwnerRtcOffset`, which the DS changes whenever the user sets the date or time in
the system settings). On Continue
(`ov36_App_MainMenu_SelectOption_Continue_AppExec` in [src/overlay_36.c](../../src/overlay_36.c)),
if either differs:

- `SysInfoRTC_HandleContinueOnNewConsole` sets `penaltyInMinutes` to 1440 (24 hours) and
  resets the saved date, time and day number to now, so no days are counted;
- the berry pots' timestamp is reset;
- every Shaymin in the party returns to Land Forme;
- the new MAC and offset are saved.

The penalty counts down by the real minutes that pass during field syncs (§5), so 24
hours of clock time, while the game is running in the field. While it is non-zero
(`FieldSystem_HasPenalty`):

- no Diamond Dust;
- no special-date egg cycles;
- days passing don't add Apricorn juice mildness or update the Safari Zone.

Daily flags, swarms, Apricorn trees and the rest still reset. To remove the penalty, make
`Save_SysInfo_RTC_HasPenalty` return `FALSE`, or remove the line that sets 1440.

## 7. Recipes

### Change the hours of morning, day and night

Edit `sTimeOfDayByHour` in [src/gf_rtc.c](../../src/gf_rtc.c). Then, to keep things
consistent:

- the lighting: move the end times in `files/data/area00light.txt` (§4);
- Shaymin: the `20` and `4` in `Party_TryResetShaymin`;
- nothing else: encounters, music, evolutions, battles and scripts all go through the table.

### Make something happen only at night, or on certain days, in a script

```
script MyMap_OnLoad {
    getcurrenttimeofday(VAR_TEMP_x4000)     // 0 morn, 1 day, 2 eve, 3 nite, 4 late
    if (var(VAR_TEMP_x4000) >= 3) {
        // night: show an NPC, move a warp...
    }
}
```

`getcurrenthour(VAR)` (0-23) and `getweekday(VAR)` (0 = Sunday) work the same way
([script-commands.md](script-commands.md#time)). `getweekday` reads the hardware clock; the
other two read the saved one (§1). For an NPC that is only there at certain times, check
in the map's `OnLoad` or `OnTransition` and `setflag` / `clearflag` the NPC's flag
([npcs-and-scripts.md](npcs-and-scripts.md)). A real one:
`data/maps/MountMoon_Square_Entrance/scripts.pory` moves its warps (`movewarp`) from
Monday 20:00 to Tuesday 3:59, so Mt. Moon Square opens only then.

### Once per day

Use a daily flag: set it when the event happens and check it before. The game clears all
of them at the next date change.

```
if (flag(FLAG_DAILY_MY_EVENT)) { ... already done today ... }
setflag(FLAG_DAILY_MY_EVENT)
```

Daily flags are `0xAA0`-`0xB5F` in [include/constants/flags.h](../../include/constants/flags.h).
Give a name to one of the `FLAG_UNK_*` in that range that nothing uses
([unknown-flags-vars.md](unknown-flags-vars.md) lists which are free). For something that must
happen in C on every new day, add a call to `FieldSystem_HandleDaysPassed`.

### Change night music

Set `music_night` in the map's `map.json` ([music.md](music.md#changing-which-music-plays)).

### Change wild Pokémon by time

`morn`, `day` and `nite` in each grass slot of the encounter JSON, and `nightFish`
([wild-encounters.md](wild-encounters.md)). Surfing and other fishing slots don't vary.

### Test at another time

- On an emulator, set the emulated clock (most emulators take it from the host clock or
  let you set an offset).
- In code, `GF_RTC_SetAndFreezeTime(hour, minute)` makes every hardware read return that
  hour and minute until `GF_RTC_UnfreezeTime()`. It is what the photo album uses to show a
  photo at the time it was taken (`src/field_take_photo.c`). The date isn't frozen, and the
  next sync copies the frozen time into the save.

## Not verified

- Whether changing an emulator's clock changes the RTC offset, and so triggers the
  penalty (§6); it depends on the emulator.
- That the map music only changes on entering a map: it is chosen in
  `FieldBGM_GetForMapHeader`, which is called from warps and map changes; no per-frame
  check was found.
- What `files/data/arealight.narc` is: no code in `src/` refers to it.
- What each of the four lights in the light files lights (light 0 looks like the sun,
  light 2 like a sky or fill light); only the parsing was read.
