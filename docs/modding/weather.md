<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Weather

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers the weather ids and what each one looks like, how a map's weather is
chosen (including the special cases: Flash, Diamond Dust, Lake of Rage), what weather
changes outside the field (battles, encounters, Sweet Scent), and how to give a map
weather, change it from a script, or add a new kind.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `"weather": "WEATHER_RAIN"` in `map.json` | `"weather": 1` in `map.json` (a number, §3) |
| `gSaveBlock1Ptr->weather`, `SetSavedWeather` | `LocalFieldData.weather` (`LocalFieldData_SetWeatherType`) |
| `SetWeather` / `DoCurrentWeather` | `WeatherManager_SetWeather` (at once) / `WeatherManager_ChangeWeather` (with a fade) |
| `setweather` + `doweather` script commands | none; only `FlashEffect` (§5) |
| `sWeatherFuncs` table | `sWeatherEntries` in [src/field/weather_manager.c](../../src/field/weather_manager.c) |
| `WEATHER_ROUTE119_CYCLE` etc. | none; Diamond Dust by date and Lake of Rage by weekday are hard-coded (§2) |

The files:

| File | What |
|---|---|
| [include/constants/weather.h](../../include/constants/weather.h) | the `WEATHER_*` ids |
| [src/field/weather_manager.c](../../src/field/weather_manager.c), [include/field/weather_manager.h](../../include/field/weather_manager.h) | drawing and switching weather |
| `data/maps/<Map>/map.json` `"weather"` | each map's weather |
| `FieldSystem_InitMapOnEnter` in [src/field_warp_tasks.c](../../src/field_warp_tasks.c) | picks the weather on entering a map |
| [src/field_system_rtc_weather.c](../../src/field_system_rtc_weather.c) | Diamond Dust dates |
| `TryAbilityOnEntry` in [src/battle/battle_util.c](../../src/battle/battle_util.c) | field weather → battle weather |
| `files/a/0/6/3` (NARC) | weather graphics (binary) |

## 1. The weather ids

`sWeatherEntries[]` has one entry per id. Several ids share a task, so they **look the
same** in the field and differ only in battle:

| Id | Constant | In the field | In battle | Retail maps |
|---|---|---|---|---|
| 0 | `WEATHER_SUNNY` | nothing (clear) | none | almost all |
| 1 | `WEATHER_RAIN` | rain, rain sound (`SEQ_SE_DP_T_AME`), grey fog | rain | Route 33, Lake of Rage |
| 2 | `WEATHER_HEAVY_RAIN` | same as 1 | rain | none |
| 3 | `WEATHER_THUNDERSTORM` | same as 1 | rain | none |
| 4 | `WEATHER_UNKNOWN_4` | snow, as 5 | hail | none |
| 5 | `WEATHER_SNOW` | snow, light fog | hail | Mt. Silver summit, Sinjoh Ruins exterior |
| 6 | `WEATHER_BLIZZARD` | same as 5 | hail | none |
| 7 | `WEATHER_SANDSTORM` | **nothing** (uses the clear task) | sandstorm | none |
| 8 | `WEATHER_DIAMOND_DUST` | sparkles, white fog | none | Mt. Silver summit on certain dates (§2) |
| 9 | `WEATHER_UNKNOWN_9` | mist: white fog plus a blended BG layer | fog | none; cleared by Defog (§2) |
| 10 | `WEATHER_UNKNOWN_10` | same as 9 | fog | none |
| 11 | `WEATHER_FLASH` | dark cave: black except a circle around the player | none | Dark Cave, Rock Tunnel, Whirl Islands 1F/B1F, Cerulean Cave |
| 12 | `WEATHER_FLASH_2` | the same circle, widened: after Flash | none | set by Flash (§2) |
| 13 | `WEATHER_LOW_LIGHT` | dark fog | none | Battle Arcade |

`WEATHER_MAX` is 14. Names like `HEAVY_RAIN`, `THUNDERSTORM` and `BLIZZARD` come from
Diamond/Pearl, where those looked different. In HGSS the rain task (`WeatherTask_Rain`)
and the snow task (`WeatherTask_Snow`) don't check which id they were started for, so they
look the same.

The battle mapping is the `switch` at `case 0: // field weather` in `TryAbilityOnEntry`:
1-3 rain, 4-6 hail, 7 sandstorm, 9-10 fog. The Battle Arcade also passes 1001 (sun) and
1002 (Trick Room) through the same field, from `src/frontier/battle_arcade_data.c`. The
weather reaches the battle as `setup->weatherType`, copied from the current field weather by
`BattleSetup_InitFromFieldSystem` ([src/battle/battle_setup.c](../../src/battle/battle_setup.c)),
so wild and trainer battles both get it.

## 2. How a map's weather is chosen

On entering a map, `FieldSystem_InitMapOnEnter`
([src/field_warp_tasks.c](../../src/field_warp_tasks.c)) works out the weather and
stores it in the save (`LocalFieldData_SetWeatherType`):

1. start from `map.json` `"weather"` (`MapHeader_GetWeatherType`);
2. on Mt. Silver's summit (`MAP_MOUNT_SILVER_CAVE_SUMMIT`) on one of the
   `DiamondDustDates` (1 Jan, 31 Jan, 1 Feb, 29 Feb, 15 Mar, 10 Oct, 3 Dec, 31 Dec), make
   it 8, unless the clock-change penalty is on
   ([day-night-and-rtc.md](day-night-and-rtc.md#6-changing-the-clock-the-penalty));
3. in Lake of Rage, make it 0 when map event key 1 is set. The key is set on Wednesdays
   once `FLAG_ROCKET_HIDEOUT_CLEARED` is set, when the lake is also drawn with low water
   (`ShouldUseAlternateLakeOfRage` in [src/map_matrix.c](../../src/map_matrix.c));
4. if it is 9 (mist) and the Defog flag is set, make it 0;
5. if it is 11 (dark) and the Flash flag is set, make it 12.

Then the field shows it:

- **After a warp** or when the game loads, `WeatherManager_SetWeather` starts it at full
  strength (`FieldMap_Init` in [src/field/fieldmap.c](../../src/field/fieldmap.c)).
- **Walking across a map connection**, `FieldMap_ChangeZone` calls
  `WeatherManager_ChangeWeather`: the old weather fades out, then the new one fades in.
  A change requested while another runs is queued (`queuedWeather`).

Because the weather is saved, a script or field move that changes it lasts until the
next map change.

**Flash.** In a dark cave (11), `FIELD_MOVE_CHECK_FLASH` makes Flash usable
(`src/field_move.c`). The Flash script (`scr_seq_0146.s`) runs `FlashAction 1` (sets the
Flash flag) and `FlashEffect`, which sets the weather to 12 and changes to it at once.
The flag stays on while you warp between cave maps, and is cleared on warping to a
non-cave map (`FieldSystem_ResetStateOnWarp` in
[src/field_warp_state.c](../../src/field_warp_state.c), `MapHeader_IsCave`).

**Defog.** `DefogAction` and the step-4 check are left over from Diamond/Pearl. No HGSS
map uses weather 9, so nothing uses them.

## 3. Giving a map weather

Set `"weather"` in the map's `data/maps/<Map>/map.json` to the id from §1, as a number:

```json
"weather": 1,
```

Then rebuild. `mapkit` copies the value into the generated header as it is. A name like
`"WEATHER_RAIN"` would not compile: `src/data/map_headers.h` doesn't include
`constants/weather.h`. Adding that include to it would make names work. The header field
is 7 bits (`weather : 7` in [include/map_header.h](../../include/map_header.h)), so values
up to 127 fit.

Things to know:

- Weather is per map. Two maps joined by a connection with different weather fade between
  them as you walk across.
- Weather 11 is how a cave is made dark; give the cave weather 11 for Flash to be needed
  and usable. `map_type` should be a cave type for the Flash flag to persist between
  floors (`MapHeader_IsCave`).
- Weather changes battles (§1): rain on a route means rain in every battle there.

## 4. What else reads the weather

| What | Where | Effect |
|---|---|---|
| Battles | `TryAbilityOnEntry` | §1 |
| Snow Cloak | `ApplyAbilityEffectToEncounterRate` in [src/field/encounter_check.c](../../src/field/encounter_check.c) | halves the encounter rate, only with weather 5 |
| Sweet Scent and Honey | `gHoneySweetScentBlockingWeather` in [src/field/honey_sweet_scent.c](../../src/field/honey_sweet_scent.c) | fail with "the weather is not suitable" (script 2019) in weather 1, 5 or 9; only those three, so 2-4 and 6 don't block |
| Flash | `src/field_move.c` | usable only with weather 11 |
| Following Pokémon | `FollowMonSituation_SetWeather` in [src/field/follow_mon_interaction.c](../../src/field/follow_mon_interaction.c) | sunny, rain, or other; changes what it says |
| Scripts | `GetWeatherType(VAR)` (`ScrCmd_GetWeatherType`) | reads the current weather id |

## 5. Changing weather from a script

There is no general set-weather command. `GetWeatherType(VAR)` reads it and
`FlashEffect` only sets 12. To change the weather from a script (a storm that starts after
an event, for instance), add a command modelled on `ScrCmd_FlashEffect`
([src/scrcmd_c.c](../../src/scrcmd_c.c)) that takes the id:

```c
BOOL ScrCmd_SetWeather(ScriptContext *ctx) {
    u16 weather = ScriptGetVar(ctx);
    LocalFieldData *localFieldData = Save_LocalFieldData_Get(ctx->fieldSystem->saveData);
    LocalFieldData_SetWeatherType(localFieldData, weather);
    WeatherManager_ChangeWeather(ctx->fieldSystem->mapSystems->weatherManager, weather);
    return FALSE;
}
```

[script-commands.md](script-commands.md#6-adding-a-command) explains how to register
it. `WeatherManager_ChangeWeather` fades; use `WeatherManager_SetWeather` to switch at
once. `WeatherManager_SetWeather` asserts that no change is running.

The new weather lasts until the next map change, when §2 recomputes it from the header.
To make it stick (rain on a route after some event), add a check in
`FieldSystem_InitMapOnEnter` next to the Lake of Rage one, for example:

```c
if (mapId == MAP_ROUTE_32 && Save_VarsFlags_CheckFlagInArray(varsFlags, FLAG_MY_STORM)) {
    weather = WEATHER_RAIN;
}
```

## 6. Changing or adding a weather

**Tuning an existing one.** Each task in [src/field/weather_manager.c](../../src/field/weather_manager.c)
sets its own numbers:

- `WeatherSpawnRamp_Init(..., count, interval, targetCount, targetInterval, ...)`: how
  many particles spawn and how often, at the start and at full strength;
- `WeatherFog_Start` and `Weather_SetFog`: the fog slope, offset and colour;
- `Weather_SetBlendAlpha`: how strongly mist's BG layer shows;
- `Rain_UpdateDrop`, `Snow_UpdateFlake`, `DiamondDust_UpdateSparkle`: particle movement.

Changing these changes every id that shares the task.

**Making the duplicate ids different.** To give heavy rain (2) more drops than rain (1),
copy `WeatherTask_Rain` to a new task with other numbers and point entry 2 in
`sWeatherEntries` at it. This needs no new graphics.

**A new id.** Add an entry to `sWeatherEntries` and raise `WEATHER_MAX`.
`WeatherSystem_Delete` also loops over a hard-coded `14`; change it to `WEATHER_MAX`.
Each entry has:

| Field | Meaning |
|---|---|
| `spriteResId` | sprite graphics for the particles (0 rain, 1 snow, 4 sparkles; from `a/0/6/3`), or `0xFFFF` for none |
| `bgGfxId` | index into `sWeatherBgGfx` (palette, chars and screen in `a/0/6/3`; mist uses 6), or `0xFFFF` |
| `taskDataSize` | size of the task's work data: `sizeof` the struct the task uses (`WeatherParticleTaskData` 0xDC, `WeatherMistTaskData` 0xAC...) |
| `taskFunc` | the task, a state machine over `WEATHER_STATE_FADE_IN_INIT` ... `WEATHER_STATE_END` |

A task must reach `WEATHER_STATE_END` and call `WeatherEntry_EndTask` after a stop request,
or the next change waits forever. Copy an existing task and keep its state handling. Also
add the new id to the battle `switch` (§1) if it should do something there.

A real field sandstorm (7) would need new sand graphics in `a/0/6/3`, which is a binary
NARC with no PNG tooling here yet.

## Not verified

- What the unused `sWeatherBgGfx` entries 0-5, 7 and 8, and the unused `spriteResId` values, in
  `a/0/6/3` show; they may be Diamond/Pearl leftovers (fog, sandstorm, darkness).
- How fog (9/10) works in an HGSS battle (`BATTLE_SUBSCRIPT_OVERWORLD_FOG`).
- That weather 1-3 and 4-6 look identical in game; only the code was read.
- Whether weather on an indoor map draws correctly.
- The `SetWeather` command and the map-entry check in §5 are examples, not built or tried.
