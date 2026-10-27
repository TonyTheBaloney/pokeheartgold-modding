<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Berry pots

> AI-generated; not affiliated with pret. See AI.md at the repository root.

HeartGold and SoulSilver have no soft soil on the map. Berries grow only in the
**Berry Pots**, a key item that opens a screen with four pots. Each pot holds one
berry plant and, optionally, one mulch. Growth follows the real-time clock. The
growth code itself does not run on the map: when the screen opens, it works out how many
minutes passed since it last looked and plays them all at once.

Three things set how a berry grows:

- **its row in a small binary archive** (`a/0/6/6`): hours per growth stage, how fast
  the soil dries, a yield multiplier. These are **not** in `data/items/items.json`;
- **the pot's mulch**, through four small functions in `src/berry_growth.c`;
- **how much the player waters it**. Dry soil costs the plant health, and health sets
  the yield.

| pokeemerald | here |
|---|---|
| berry trees on the map (`gSaveBlock1Ptr->berryTrees`, `src/berry.c`) | 4 pots in `SAVE_MISC_DATA.berry_pots` (`include/save_misc_data.h:42`) |
| `gBerries[]` (`stageDuration`, `maxYield`, `minYield`) | the `a/0/6/6` archive, one 12-byte file per berry |
| `BerryTreeTimeUpdate` called from the overworld clock | `BerryPots_UpdateGrowth`, called only when the Berry Pots screen is open |
| watering 3 or 4 times raises the yield | the soil dries by the hour; each dry hour costs 1 of 5 health |
| no mulch | Growth, Damp, Stable and Gooey Mulch (items 95-98) |

## Where things are

| What | File |
|---|---|
| per-pot save struct `BerryPot`, `MAX_BERRY_POT`, growth stage constants | `include/save_misc_data.h:16-38` |
| the pots and their timestamp in the save | `berry_pots`, `berry_datetime` in `SAVE_MISC_DATA`, `include/save_misc_data.h:42-43` |
| new-game init of pots and timestamp | `Save_BerryPots_Init`, `Save_BerryPotRTC_Init`, `src/save_misc.c:11-23` |
| growth model: stages, moisture, yield, mulch | `src/berry_growth.c` |
| berry parameters (growth hours, drain rate, yield multiplier) | `files/a/0/6/6` (prebuilt binary), read by `BerryPots_LoadGrowthProperties`, `src/berry_growth.c:49` |
| berry/mulch id ↔ item id | `BerryIdToItemId` … `ItemIdToMulchId`, `src/berry_growth.c:332-362`; `FIRST_MULCH_IDX`, `MULCH_IDX`, `FIRST_BERRY_IDX`, `BERRY_IDX` in `include/constants/items.h:430-434, 547-551` |
| the key item opening the screen | `ItemMenuUseFunc_BerryPots`, `ItemFieldUseFunc_BerryPots`, `src/field_use_item.c:616-630`; `BerryPots_LaunchApp`, `src/launch_application.c:603-617` |
| outer overlay: switches between the pots screen and the bag | `src/berry_pots.c` |
| the pots screen | `src/berry_pots_app.c`, `src/berry_pots_app_tasks.c`, `include/berry_pots_app_internal.h` |
| catching up with the clock | `BerryPotsApp_UpdateGrowthFromRTC`, `src/berry_pots_app_tasks.c:149` |
| screen text (menu buttons, messages) | `files/msgdata/msg/msg_0248.json` |
| screen graphics, plant sprites (one per berry) | `files/a/2/1/6` ([graphics-sources.md](graphics-sources.md)) |
| where you get the pots | `data/maps/Route36/scripts.pory:153` |
| where you buy mulch | `Goldenrod_FlowerShop_EventScript_Woman`, `data/maps/Goldenrod_FlowerShop/scripts.pory:134` |

## 1. Getting the pots, berries and mulch

**The pots.** The only `ITEM_BERRY_POTS` in the scripts is on Route 36
(`data/maps/Route36/scripts.pory:153`). The script is the Sudowoodo tree
(`Route36_EventScript_Usokky`). It has two branches:

- If `FLAG_HIDE_GOLDENROD_FLOWERSHOP_GIRL` is clear (line 46), you fight Sudowoodo and
  get no gift.
- Otherwise, with the Squirtbottle (line 88), the branch from `_00E0` fights Sudowoodo
  (line 127). A loss whites out (`_0255`) and a `BATTLE_OUTCOME_DRAW` ends the script
  (`_0251`, line 132). In every other case the script sets `FLAG_UNK_0B5` (line 135),
  and the girl `obj_R36_gsgirl1_2` gives the Berry Pots (line 153), 3 Oran and 3 Pecha
  Berries (lines 161-162).

The item is a key item, `selectable` (it can be registered to Y), with field use
`ITEM_FIELD_USE_BERRY_POTS` (`data/items/items.json:9359`). Both ways of using it call
`BerryPots_LaunchApp` (`src/field_use_item.c:619, 629`).

**Mulch.** The Goldenrod Flower Shop woman sells the four mulches at 200 each, once
`FLAG_UNK_0B5` is set (`data/maps/Goldenrod_FlowerShop/scripts.pory:135`). The item
ids are hard-coded there as numbers: `setvar(VAR_SPECIAL_x8001, 95)` to `98`
(lines 177-186).

**Berries** come from scripts and phone calls, not trees (§10).

## 2. What is saved per pot

`BerryPot` is 12 bytes (`include/save_misc_data.h:23-33`). The save holds
`MAX_BERRY_POT` = 4 of them, then one shared timestamp (`berry_datetime`, line 43).

| Field | Type | Meaning |
|---|---|---|
| `berryId` | u8 | 1 = Cheri … 64 = Rowap; 0 = `BERRY_NONE`. Item id = `berryId + ITEM_CHERI_BERRY - 1` (`src/berry_growth.c:337`) |
| `growthStage` | u8 | `BERRY_POT_GROWTH_STAGE_NONE` (0), `PLANTED`, `SPROUTED`, `GROWING`, `BLOOM`, `BERRIES` (5) (`include/save_misc_data.h:16-21`) |
| `minutesToNextStage` | u16 | countdown to the next stage |
| `drainMinutes` | u16 | minutes left over after the last full hour of drying (0-59) |
| `yield` | u16 | berries to pick; set when the plant reaches `BERRIES`, else 0 |
| `regrowthCount` | u8 | how many times the berries fell off and the plant regrew |
| `moisture` | u8 | 0-100. Planting and watering set 100 (`src/berry_growth.c:162, 167`) |
| `health` | u8 | 0-5. 5 at planting and after each regrowth (lines 163, 208) |
| `mulch` | u8 | 0 = `MULCH_NONE`, 1 Growth, 2 Damp, 3 Stable, 4 Gooey (`MULCH_IDX(item)` = `item - ITEM_GROWTH_MULCH + 1`, `include/constants/items.h:433`) |

The timestamp is shared by all four pots. A new game sets it to the current RTC time
(`src/overlay_36.c:188`).

The screen shows the soil in three states, from `BerryPots_GetSoilState`
(`src/berry_growth.c:128-137`): 0 if moisture is 0, 1 if it is 1-50, 2 if above 50.

## 3. Berry data: the `a/0/6/6` archive

`BerryPots_LoadGrowthProperties` (`src/berry_growth.c:49-68`) opens `NARC_a_0_6_6`
and reads one file per berry, file *n* for berry *n*+1. Each file is a `BerryFile`
(`src/berry_growth.c:7-19`):

| Byte | Field | Used by the pots |
|---:|---|---|
| 0-1 | `sizeInMillimeters` | no |
| 2 | `firmness` | no |
| 3 | `yieldMultiplier` | yes: yield = health × this |
| 4 | `defaultGrowthInterval` | yes: **hours per stage** |
| 5 | `defaultDrainRate` | yes: moisture lost per hour |
| 6-10 | `spiciness`, `dryness`, `sweetness`, `bitterness`, `sourness` | no |
| 11 | `smoothness` | no |

Only those three bytes are copied into `BerryGrowthProperties` (`include/berry_pots.h:15-19`).
No other code opens this archive (`NARC_a_0_6_6` appears only in `src/berry_growth.c:292`).
The file is copied into the ROM as is (`files/a/0/6/6`, listed in
`files/a/0/6/meson.build`).

Retail values, decoded from `files/a/0/6/6`. "To berries" is 4 stages (§4). The last
column is 5 × the multiplier:

| Berry ids | Berries | Hours per stage | To berries (h) | Drain per hour | Yield mult. | Max yield |
|---|---|---:|---:|---:|---:|---:|
| 1-5 | Cheri, Chesto, Pecha, Rawst, Aspear | 3 | 12 | 15 | 1 | 5 |
| 6-8 | Leppa, Oran, Persim | 4 | 16 | 15 | 1 | 5 |
| 9 | Lum | 12 | 48 | 8 | 1 | 5 |
| 10 | Sitrus | 8 | 32 | 7 | 1 | 5 |
| 11-15 | Figy, Wiki, Mago, Aguav, Iapapa | 5 | 20 | 10 | 1 | 5 |
| 16-20 | Razz, Bluk, Nanab, Wepear, Pinap | 2 | 8 | 35 | 2 | 10 |
| 21-26 | Pomeg, Kelpsy, Qualot, Hondew, Grepa, Tamato | 8 | 32 | 8 | 1 | 5 |
| 27-30 | Cornn, Magost, Rabuta, Nomel | 6 | 24 | 10 | 2 | 10 |
| 31-35 | Spelon, Pamtre, Watmel, Durin, Belue | 15 | 60 | 8 | 3 | 15 |
| 36-52 | Occa … Chilan (the type-resist berries) | 18 | 72 | 6 | 1 | 5 |
| 53-59 | Liechi, Ganlon, Salac, Petaya, Apicot, Lansat, Starf | 24 | 96 | 4 | 1 | 5 |
| 60-64 | Enigma, Micle, Custap, Jaboca, Rowap | 24 | 96 | 7 | 1 | 5 |

## 4. The growth cycle

`BerryPots_PlantBerry` (`src/berry_growth.c:155-164`) sets stage `PLANTED`, moisture
100, health 5, and `minutesToNextStage` = one growth interval. The mulch is kept, so
mulch laid on the empty pot applies.

The **growth interval** comes from `CalculateBerryPotGrowthInterval` (lines 86-94):
hours × 60, changed by Growth or Damp Mulch (§7).

Each time `minutesToNextStage` runs out, `BerryPot_AdvanceGrowthStage` (lines 188-215)
runs:

| From | To | Also |
|---|---|---|
| `PLANTED` | `SPROUTED` | |
| `SPROUTED` | `GROWING` | |
| `GROWING` | `BLOOM` | |
| `BLOOM` | `BERRIES` | `yield` is computed (§6) |
| `BERRIES` | `SPROUTED` | berries lost: `yield` = 0, health = 5, `regrowthCount`++; at the max regrowth count the pot is emptied |

`BerryPots_UpdateGrowth` (lines 247-279) then sets the next countdown to one interval.
The `BERRIES` stage is longer: interval × the "ripe factor" (4, or 6 with Stable
Mulch), lines 274-276.

So a plant takes 4 intervals to give berries. If you don't pick them, they stay for 4
intervals, then fall off, and the plant regrows from `SPROUTED`. A regrown plant takes
3 intervals to fruit again. The max regrowth count is 10, or 15 with Gooey Mulch
(`BerryPot_GetMaxRegrowths`, lines 110-112). Moisture is not refilled on regrowth.

**Lifetime.** `BerryPot_GetLifetimeInIntervals` (lines 114-118) returns
`(ripeFactor + 3) × maxRegrowths + 1`: 71 intervals normally, 91 with Stable, 106 with
Gooey. For a Cheri Berry that is 71 × 3 h = 213 hours. If more minutes than
interval × lifetime have passed since the screen last looked, the pot is emptied at once
(lines 256-259). Mulch and all are gone. It is the same result as stepping through
every stage.

**Picking.** `BerryPots_HarvestPot` (lines 182-186) returns `yield` and empties the
pot with `BerryPot_Clear` (lines 70-80), **mulch included**.

## 5. Moisture and health

`BerryPot_DrainMoisture` (`src/berry_growth.c:217-245`) runs on every stretch of
minutes that `BerryPots_UpdateGrowth` passes through:

1. Nothing drains while the plant is in `BERRIES` (line 218).
2. Minutes add up in `drainMinutes`, and only whole hours count (lines 223-227).
3. Each hour removes the drain rate from `moisture`. The rate comes from
   `CalculateBerryPotDrainRate` (lines 96-104), the berry's drain changed by mulch
   (§7).
4. When moisture runs out, the hours still left after it hit 0 each take 1 health
   (lines 234-244). Health stops at 0.

A Cheri Berry (drain 15) watered to 100 is dry after 7 hours. Five more hours without
water bring its health to 0.

A drain rate of 0 never takes moisture away. Line 229 is then always true, so the
division at line 235 is never reached.

**Watering.** `BerryPotsApp_WaterPot` (`src/berry_pots_app.c:1027`) calls
`BerryPots_ResetPotMoisture` (moisture = 100). It does not check the stage. Watering
leaves health alone, so lost health comes back only when the plant regrows (line 208).

## 6. Yield

The yield is computed when the plant goes from `BLOOM` to `BERRIES`
(`src/berry_growth.c:198-204`):

```c
berryPot->yield = BerryPot_CalcYield(berryPot, growthProperties);   // health * yieldMultiplier (line 83)
if (berryPot->yield < 2) {
    berryPot->yield = 2;
}
```

So the yield is 2 to 5 × the multiplier. It depends on health at that moment, and
health depends on how many hours the soil was dry since the last planting or regrowth.

What the player receives is a **u8 copy**. `BerryPotsApp_RefreshPotData` copies
`yield` into `BerryPotsAppPot.quantityOrYieldMaybe`, a `u8`
(`include/berry_pots_app_internal.h:52`, `src/berry_pots_app_tasks.c:186`).
`BerryPotsApp_HarvestBerries` adds that copy to the bag (`src/berry_pots_app.c:1040`).
The message prints it with 2 digits (`src/berry_pots_app_tasks.c:127`). Keep yields
under 100.

If the bag has no room (`Bag_HasSpaceForItem`, `src/berry_pots_app.c:606`), the
message says "Gave up on the … Berries", but `BerryPotsApp_HarvestBerries` isn't
called. The pot keeps its berries.

## 7. Mulch

Mulch can be laid only on an **empty pot with no mulch**. `BerryPotsApp_GetPotMenuState`
(`src/berry_pots_app_tasks.c:428-444`) offers "FERTILIZE / PLANT BERRY / EXIT" only
then. An empty pot that already has mulch gets "PLANT BERRY / EXIT". The mulch stays
through regrowths and goes when the pot is picked or emptied.

| Mulch | `mulch` | Effect | Code (`src/berry_growth.c`) |
|---|---:|---|---|
| Growth | 1 | interval × 3/4 (integer); drain × 1.5 (`rate + rate/2`) | lines 88-89, 100-101 |
| Damp | 2 | interval × 1.5 (`t + t/2`); drain ÷ 2 (integer) | lines 90-91, 98-99 |
| Stable | 3 | berries stay 6 intervals instead of 4 | line 107 |
| Gooey | 4 | 15 regrowths instead of 10 | line 111 |

With Damp Mulch a drain rate of 1 becomes 0, so the soil never dries.

Item checks:

- the bag, in Berry Pots mode (`mode == 6`), lets you choose only berries or items
  `ITEM_GROWTH_MULCH`-`ITEM_GOOEY_MULCH` (`IsBerryOrMulch`,
  `src/application/bag/bag_app.c:2758`);
- the screen accepts up to `ITEM_ROOT_FOSSIL` (`ItemIdIsMulch`,
  `src/berry_pots_app.c:687-694`, marked "BUG"). The bag never offers it, so
  this can't be reached as shipped.

## 8. Real time: when growth happens

Growth is computed **only by the Berry Pots screen**. The only call to
`BerryPots_UpdateGrowth` is in `BerryPotsApp_UpdateGrowthFromRTC`
(`src/berry_pots_app_tasks.c:166`), and that runs:

- when the screen is drawn (`BerryPotsApp_InitDisplay`, `src/berry_pots_app.c:808`), and
- every frame while you pick a pot (`BerryPotsApp_MainSeq_SelectPot`, line 444). This
  also plays the growth animation for pots that changed stage.

`BerryPotsApp_UpdateGrowthFromRTC` (`src/berry_pots_app_tasks.c:149-173`):

1. Reads the RTC and the saved `berry_datetime`, both as seconds
   (`RTC_ConvertDateTimeToSecond`, lines 156-158).
2. If the clock is **behind** the saved time, it saves the current time and stops. There
   is no growth and no loss (lines 159-162).
3. Otherwise `minutesDelta = seconds / 60` (line 164). If that is at least 1, it runs
   `BerryPots_UpdateGrowth(minutesDelta)` and saves the current time (lines 165-168).
   Up to 59 leftover seconds are dropped each time.

Nothing on the map advances the pots. Moisture is checked the same way, so a pot left
alone for a week loses its moisture and health all at once when you open the screen.

**Changing the system clock.** On Continue, if the save's MAC address or RTC offset
doesn't match the console, `Save_BerryPotRTC_Init` sets the berry timestamp to now
(`src/overlay_36.c:160-162`). The time in between doesn't count. See
[day-night-and-rtc.md §6](day-night-and-rtc.md#6-changing-the-clock-the-penalty).
The 24-hour penalty described there is not checked by any berry code.

## 9. The Berry Pots screen

You need this section only to change the screen.

**Overlays.** The key item launches overlay 16 with `BerryPots_Init` /
`BerryPots_Main` / `BerryPots_Exit` (`src/launch_application.c:604`). `BerryPots_Init`
loads overlay 17 (the screen, `src/berry_pots.c:77`).
`BerryPots_Main` (`src/berry_pots.c:91-112`) alternates between two sub-apps:

1. the pots screen (`BerryPotsApp_Initialize` / `_Run` / `_Exit`);
2. when the player chose FERTILIZE (`itemAction` 1) or PLANT BERRY (2), the bag in
   mode 6. It shows the Items pocket for mulch and the Berries pocket for berries
   (`BerryPots_MainSeq_StartBag`, lines 154-177);
3. back to the screen. `BerryPotsApp_ApplyChosenItem` (`src/berry_pots_app.c:696-727`)
   lays the mulch or plants the berry, adds to `GAME_STAT_BERRIES_PLANTED` for a berry
   (line 722), and takes 1 of the item (line 726).

The screen keeps a copy of each pot (`BerryPotsAppPot`,
`include/berry_pots_app_internal.h:46-60`), refreshed by `BerryPotsApp_RefreshPotData`.

**States** of `BerryPotsApp_Run` (`src/berry_pots_app.c:305-341`): 0 fade in, 1 fade
out, 2 select a pot, 3 empty-pot menu, 4 mulched-pot menu, 5 water menu (stages 1-4),
6 harvest menu (stage 5), 7 "item used" message, 8 wait for a message, 9 done.

**Menus** are `sBerryPotsMenus` (`src/berry_pots_app.c:228-238`), built from
`msg_0248` messages 1-5. The status messages are `msg_0248` 6-22, in the order of
`enum BerryPotsAppMessage` (`include/berry_pots_app_internal.h:10-28`). The water
menu prints `BERRY_POTS_APP_MSG_MULCH_LAID + growthStage`
(`src/berry_pots_app.c:537`), so messages 12-15 must stay in stage order.

**Layout.** Pots are 27 pixels apart. These places hard-code the spacing and the count:

| What | Where |
|---|---|
| sprites: `sprites[0]` cancel, `[1]` cursor, `[2]` watering can, `[3+i]` soil, `[7+i]` growth sparkle | `Sprite *sprites[11]`, `include/berry_pots_app_internal.h:103`; `BerryPotsApp_SetupSprites`, `src/berry_pots_app.c:1247-1272`; also `index + 3` at lines 995, 1024, 1031, 1044 and `3 + i` / `7 + potIndex` at `src/berry_pots_app_tasks.c:207, 231, 244` |
| plant sprite x = `(index + 1) * 27`, cursor x the same | `src/berry_pots_app.c:1001, 929` |
| watering can x = `pot * 27 + 31`, and the pot under it `(x - 31) / 27` | `src/berry_pots_app_tasks.c:55, 65`; `src/berry_pots_app.c:821` |
| picked-berry icon x = `pot * 27 + 35` | `src/berry_pots_app_tasks.c:97` |
| touch boxes: x from 16, every 28, 22 wide | `BerryPotsApp_GetTouchedPot`, `src/berry_pots_app_tasks.c:392-411` |
| left/right wrap with `% MAX_BERRY_POT` | `src/berry_pots_app_tasks.c:318-321, 355-358` |
| plant graphics: resource set `index + 1` | `src/berry_pots_app.c:1010, 1288-1289` |
| plant graphics per berry: tiles `a/2/1/6` member `berryId - 1 + 76`, palette member `berryId - 1 + 12` | `BerryPotsApp_LoadPlantGfx`, `src/berry_pots_app.c:1282-1290` |
| the pots drawn in the background | `a/2/1/6` members 3-5 (main screen BG), `BerryPotsApp_SetupNarc`, line 1109 |

**Sound.** The screen sets sound scene `0x45` (`src/berry_pots_app.c:390`). Picking
berries plays `SEQ_ME_KINOMI` (line 628) and counts `SCORE_EVENT_BERRY_PICKED`
(line 1045).

## 10. Berries in the overworld

There are no berry trees or soil patches. Using a berry from the bag goes to the
healing-item handler (`ItemMenuUseFunc_Berry`, `src/field_use_item.c:385-389`).
`Leftover_CanPlantBerry` always returns `FALSE` (line 392). Scripts give berries
directly:

| Source | Where |
|---|---|
| Route 36, with the pots: 3 Oran, 3 Pecha | `data/maps/Route36/scripts.pory:161-162` |
| Juggler in Violet City: berry sets A-D for shards | `Violet_EventScript_Juggler`, `data/maps/Violet/scripts.pory:464` (sets from line 504) |
| Juggler in Fuchsia City: berry sets E-H for shards | `Fuchsia_EventScript_Juggler`, `data/maps/Fuchsia/scripts.pory:121` (sets from line 161) |
| phone trainers' gifts; `ITEM_CHERI_BERRY` in the phone book means a random one of the first 10 berries | `ScrCmd_GetPhoneContactRandomGiftBerry`, `src/scrcmd_c.c:4718`; [phone.md](phone.md#1-the-phone-book) |

To hand out other berries, use `giveitem` in any script
([npcs-and-scripts.md](npcs-and-scripts.md)). Hidden items and wild Pokémon's held
items are not covered here.

## 11. How-tos

### Change one berry's growth time, drain or yield

**In the data.** Edit bytes 3-5 of the berry's file in `files/a/0/6/6`. Every file is
12 bytes. This script reads the archive's header and changes one byte. Run it on a
copy, check it, then copy the archive back:

```python
# berry_param.py FILE BERRY FIELD [VALUE]   (BERRY: 1 = Cheri ... 64 = Rowap)
import struct, sys
FIELDS = {"yield": 3, "hours": 4, "drain": 5}   # byte offsets in BerryFile (src/berry_growth.c:7)
path, berry, field = sys.argv[1], int(sys.argv[2]), sys.argv[3]
b = bytearray(open(path, "rb").read())
fat = struct.unpack_from("<H", b, 0xC)[0]                 # BTAF block
fat_size, count = struct.unpack_from("<IH", b, fat + 4)
start, _ = struct.unpack_from("<II", b, fat + 12 + 8 * (berry - 1))
fnt = fat + fat_size
gmif = fnt + struct.unpack_from("<I", b, fnt + 4)[0]
pos = gmif + 8 + start + FIELDS[field]
if len(sys.argv) > 4:
    b[pos] = int(sys.argv[4])
    open(path, "wb").write(b)
print(field, "of berry", berry, "=", b[pos])
```

```sh
cp files/a/0/6/6 /tmp/berry.narc
python3 berry_param.py /tmp/berry.narc 10 hours        # Sitrus: 8
python3 berry_param.py /tmp/berry.narc 10 hours 4      # 16 h to berries instead of 32
python3 berry_param.py /tmp/berry.narc 10 yield 2      # up to 10 per harvest
cp /tmp/berry.narc files/a/0/6/6
make release
```

**In C**, without touching the archive. Overwrite the loaded values at the end of
the loop in `BerryPots_LoadGrowthProperties` (`src/berry_growth.c:56-63`):

```c
    FreeBerryInfoNarc(narc);

    growthProperties[BERRY_IDX(ITEM_SITRUS_BERRY) - 1].defaultGrowthTimeInHours = 4;
    growthProperties[BERRY_IDX(ITEM_SITRUS_BERRY) - 1].yieldMultiplier = 2;

    return growthProperties;
```

Limits:

- Hours are a u8. Times shorter than an hour need a change to the `* 60` in
  `CalculateBerryPotGrowthInterval` (line 87).
- `minutesToNextStage` is a u16 (max 65535). The longest countdown is the `BERRIES`
  stage: interval × 4 with Damp (1.5 × 60 × h × 4) or × 6 with Stable (60 × h × 6).
  Both are 360 × hours, so keep hours at 182 or less.
- Max yield is 5 × the multiplier, and should stay under 100 (§6).
- A pot that is already growing keeps its current countdown. The new interval applies
  from its next stage (line 273).

### Change moisture or mulch behaviour

All of it is in `src/berry_growth.c`, lines 86-118 and 217-245. Examples:

```c
// Growth Mulch halves the interval instead of 3/4 (line 89)
-        return (growthTimeInMinutes * 3) / 4;
+        return growthTimeInMinutes / 2;

// Gooey Mulch: 30 regrowths (line 111)
-    return (berryPot->mulch == MULCH_IDX(ITEM_GOOEY_MULCH)) ? 15 : 10;
+    return (berryPot->mulch == MULCH_IDX(ITEM_GOOEY_MULCH)) ? 30 : 10;

// soil never dries: first line of BerryPot_DrainMoisture (line 218)
-    if (berryPot->growthStage == BERRY_POT_GROWTH_STAGE_BERRIES) {
+    if (TRUE) {
```

- **Health.** The full value 5 is written in `BerryPots_PlantBerry` (line 163) and on
  regrowth (line 208). The minimum yield of 2 is at lines 200-202.
- **Mulch on a planted pot.** The screen doesn't offer it. You would need a FERTILIZE
  entry in the water menu (`sMenu_Water_Exit`, `src/berry_pots_app.c:230`) and its
  handling in `BerryPotsApp_MainSeq_WaterMenu`.
- **A fifth mulch.** Mulch ids are offsets from `ITEM_GROWTH_MULCH`, and item 99 is
  `ITEM_ROOT_FOSSIL` (`include/constants/items.h:411-415`). A new mulch item can't sit
  next to the others. You would replace `MulchIdToItemId` / `ItemIdToMulchId`
  (`src/berry_growth.c:348-362`), `GetTotalMulchQuantity` (line 373), `IsBerryOrMulch`
  and `ItemIdIsMulch` with checks that know the new id, then add its effect to the
  functions above. See [items.md](items.md#adding-an-item).

### Make berries grow faster globally

There are two ways. Either is one line.

**Speed up the clock for the pots** (`src/berry_pots_app_tasks.c:164`). This scales
everything: stages, drying, ripe time, lifetime.

```c
-    u32 minutesDelta = (timestamp1 - timestamp2) / 60;
+    u32 minutesDelta = (timestamp1 - timestamp2) / 60 * 4;   // 4 pot-minutes per real minute
```

**Or shorten only the stages** (`src/berry_growth.c:87`). Drying stays per real hour,
so watering matters less.

```c
-    s32 growthTimeInMinutes = growthProperties[berryId - 1].defaultGrowthTimeInHours * 60;
+    s32 growthTimeInMinutes = growthProperties[berryId - 1].defaultGrowthTimeInHours * 15;
```

With the first, the lifetime shrinks too. At ×4, an unwatched Cheri plant is gone
after about 53 real hours (213 / 4) instead of 213.

### Add more pots

This is a save-layout change and a screen change.

1. **Save.** `MAX_BERRY_POT` (`include/save_misc_data.h:38`) sizes `berry_pots` inside
   `SAVE_MISC_DATA`. Raising it moves every field after it (`berry_datetime`,
   `gymmick`, the rival's name...), so **old saves break**. See
   [save-compatibility.md §2](save-compatibility.md#2-two-kinds-of-break) and
   [§6](save-compatibility.md#6-when-the-layout-has-to-change). The 16 free bytes in
   `filler_0288` (line 47) would hold one more 12-byte pot. They aren't next to the
   array, though, and every function here indexes `berryPots[i]` up to
   `MAX_BERRY_POT`.
2. **Growth code** loops over `MAX_BERRY_POT` (`src/berry_growth.c:248`) and needs
   no other change.
3. **Screen.** Change every row of the layout table in §9: grow `sprites[11]` to
   `3 + 2 × pots`, and move the sparkle sprites from `7 + i` to `3 + pots + i`. Choose
   a spacing that fits; at 27 px the pots sit at x = 27-108 now. Then redraw the
   background (`a/2/1/6` members 3-5, [graphics.md](graphics.md#4-changing-a-binary-archive)).
   You also need more sprite resource sets: `BerryPotsApp_LoadPlantGfx` replaces sets
   1-4, from `sBerryPotsResdatIdList`'s header (`resdat_00000079_bin`,
   `src/berry_pots_app.c:121-129`). The sprite count is 25
   (`SpriteSystem_InitSprites`, line 1200). Neither was traced.

## 12. Saves

- Changing `a/0/6/6`, mulch effects or the clock scaling doesn't change the save
  layout. Pots already growing pick up the new values at their next stage.
- Changing `MAX_BERRY_POT` or `BerryPot` changes `SAVE_MISC_DATA` and breaks old saves
  (above).
- A save from before a "faster clock" mod catches up with the new speed the first time
  the screen opens: all the real time since the last visit counts at the new rate.

## Not verified

Nothing in this guide was tried in the game, and none of the code changes were built.

- The `berry_param.py` script was run only on a copy of `files/a/0/6/6`. Changing
  Cheri's hours from 3 to 1 changed exactly byte 568 (`cmp -l`), and writing 3 back gave
  an identical file. A ROM was not built with a changed archive.
- The retail table in §3 was decoded from `files/a/0/6/6` with the `BerryFile` layout.
  The growth times ("to berries") are computed from the code, not timed in game.
- The diffs in §11 (mulch, global speed, more pots) and the C override were not
  compiled.
- Adding pots: the sprite resource header (`resdat_00000079_bin`), the background
  art, and whether more plant sprites fit in VRAM were not looked at.
- Route 36: the meaning of the two branches (`FLAG_HIDE_GOLDENROD_FLOWERSHOP_GIRL`) and
  what a `BATTLE_OUTCOME_DRAW` there is (fleeing?) were not traced. Whether the pots
  can be had any other way after that was not checked beyond searching the scripts for
  `ITEM_BERRY_POTS`.
- After a regrowth reaches the max and empties the pot, `BerryPots_UpdateGrowth`
  recomputes the interval with `berryId` 0 (line 273). That reads
  `growthProperties[-1]`. The loop then stops, because the stage is `NONE`, and the
  next planting overwrites the value. It looks harmless but wasn't tested.
- What `BerryPots_DeadstrippedFunction` and its table `ov17_02203D60`
  (`src/berry_pots_app.c:89, 1321`) were for.
