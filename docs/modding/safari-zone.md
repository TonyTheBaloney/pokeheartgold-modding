<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Safari Zone: areas, objects and the Safari Game

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The Safari Zone west of Cianwood is one map, `MAP_SAFARI_ZONE_ENTRANCE_EXTERIOR`,
with a 3×2 grid of **areas** in the middle. There are 12 areas (Plains, Meadow,
Forest...) and the player chooses which six fill the grid, in the gate's **Area
Customizer**. Later the player can place up to 30 **objects** (shrubs, rocks,
puddles, fences...) in each area. Objects of four types (plains, forest, peak,
water) earn **points**, and enough points unlock **bonus Pokémon** in that area's
encounter table. Points per object grow with the number of days the area has been in
the layout.

The encounter JSON itself is described in
[wild-encounters.md](wild-encounters.md#safari-zone). This guide covers how the code
uses it.

## Where things are

| What | File |
|---|---|
| area ids, object ids, object types, limits | `include/constants/safari.h` |
| what is saved (`SafariZone`, `SafariZoneAreaSet`, `SAFARIZONE_AREA`, `SAFARIZONE_OBJECT`) | `include/safari_zone.h` |
| save helpers, the 10 default layouts | `src/safari_zone.c` |
| object table (model, size, type), bonus slots, object points | `src/safari_zone_encounters.c` |
| encounters per area | `files/arc/safari_enc.json` + `safari_enc.json.txt` → `safari_enc.narc` = `a/2/3/0` (`heartgold.us/filesystem.csv:329`) |
| putting the six area blocks into the map | `PlaceSafariZoneAreas`, `src/map_matrix.c:209` |
| drawing placed objects | `MapLoadManager_LoadSafariZoneProps`, `src/field/map_load_manager.c:451`; `MapPropManager_LoadFromSafariZone`, `src/field/map_prop_manager.c:140` |
| where an object may go, which area the player is in | `src/field/safari_zone_placement.c` |
| the object list screen (overlay 108) | `src/application/safari_decoration.c`; its data in `asm/safari_decoration_data.s` |
| the task that runs that screen | `src/safari_decoration_task.c` |
| the Area Customizer screen (overlay 108) | `src/application/safari_area_customizer.c` |
| script commands | `src/overlay_03/overlay_03_scrcmds.c`, `ScrCmd_SafariZoneAction` (`src/scrcmd_c.c:3397`) |
| gate scripts (fee, tests, customizer) | `data/maps/SafariZoneEntranceInterior/scripts.pory` |
| place / remove / game-over scripts | `files/fielddata/script/scr_seq/scr_seq_0262.s` (`std_safari_*`, `src/script_manager.c:56`) |
| Baoba's phone calls (object unlocks) | `src/application/pokegear/phone/scripts/phone_scripts_baoba.c`, `GearPhoneRingManager_CheckSafariCalls` (`src/gear_phone_ring_manager.c:156`) |
| Safari battle actions | `src/battle/battle_controller_player.c:1814-1867`, `Task_SafariSelectCommand` (`src/battle/battle_controller_opponent.c:4448`) |
| text: area names, object names, place/remove messages | `msg_0428.json`, `msg_0429.json`, `msg_0430.json`, `msg_0427.json` in `files/msgdata/msg/` |

## 1. Areas and the layout

### The 12 areas

`include/constants/safari.h` numbers the areas 0-11:

| Id | Constant | Map block (`data/landdata/`) |
|---:|---|---|
| 0 | `SAFARI_ZONE_AREA_PLAINS` | 0652 |
| 1 | `SAFARI_ZONE_AREA_MEADOW` | 0653 |
| 2 | `SAFARI_ZONE_AREA_SAVANNAH` | 0654 |
| 3 | `SAFARI_ZONE_AREA_PEAK` | 0655 |
| 4 | `SAFARI_ZONE_AREA_ROCKY_BEACH` | 0656 |
| 5 | `SAFARI_ZONE_AREA_WETLAND` | 0657 |
| 6 | `SAFARI_ZONE_AREA_FOREST` | 0658 |
| 7 | `SAFARI_ZONE_AREA_SWAMP` | 0659 |
| 8 | `SAFARI_ZONE_AREA_MARSHLAND` | 0660 |
| 9 | `SAFARI_ZONE_AREA_WASTELAND` | 0661 |
| 10 | `SAFARI_ZONE_AREA_MOUNTAIN` | 0662 |
| 11 | `SAFARI_ZONE_AREA_DESERT` | 0663 |

The block number is `652 + id` (`src/map_matrix.c:223`). Each block is one 32×32
cell with its own model, terrain and permissions; its `props.json` is empty, because
the placed objects are the props.

### The six slots

A **layout** (`SafariZoneAreaSet`, `include/safari_zone.h:23`) has six slots
(`SAFARI_ZONE_AREA_SET_COLS` 3 × `_ROWS` 2). Slot `i` is column `i % 3`, row `i / 3`:
slots 0-2 are the north row, west to east, and 3-5 the south row. Each slot is a
`SAFARIZONE_AREA`: the area id, the number of objects, and 30 objects. The layout also
has `areaLevels[12]`, one **age** per area id, in days ([§6](#6-object-points-area-age-and-bonus-pokémon)).

The save keeps two layouts (`SAFARI_ZONE_MAX_AREA_SETS`):

| Set | Is |
|---:|---|
| 0 | your own Safari Zone. Every editing function uses set 0 (`SafariZone_GetAreaSet(..., 0)`). |
| 1 | a friend's Safari Zone received over the Safari Zone Link (`CustomSafariLink_RecvAreaSet`, `src/overlay_03/custom_safari_zone.c:53`) |

`activeAreaSet` says which one you are playing in. Passing 3 to
`SafariZone_GetAreaSet` means "the active set" (`src/safari_zone.c:62-73`); the map,
the props and the encounters all ask for set 3.

### The default layout

A new game copies one of 10 preset layouts, `sSafariZoneDefaultAreaSets`
(`src/safari_zone.c:11-22`), into set 0. The preset is `rand % 10`
(`SafariZone_ResetAreaSetToDefaultSet`, `src/safari_zone.c:40`), where `rand` is the
same random number that becomes the 32-bit trainer id (`src/overlay_36.c:193-200`).
Every preset has Peak in slot 4. None has Rocky Beach or Desert. That is why Baoba's
second test (catch a Sandshrew, which "live in the desert") needs the customizer
(`scripts.pory:203-266`).

### How the map is assembled

The exterior's layout (`data/layouts/SafariZoneEntranceExterior/layout.json`) is 5×4
cells. The ring is block 211, the entrance is 666, and the six middle cells are
`null`. On every map load, `PlaceSafariZoneAreas` (`src/map_matrix.c:209`, called
from `src/field_warp_tasks.c:331`) checks that the matrix is the Safari Zone's
(`map_matrix_0212_D47R0102`) and writes `652 + area id` of slot
`row * 3 + col` into matrix cell `(col + 1, row + 1)` (`src/map_matrix.c:220-225`).

The Safari map uses its own loader (`MAP_LOAD_TYPE_SAFARI`,
`src/field_warp_tasks.c:174-175`; `sMapLoadFuncs_SafariZone`,
`src/field/map_load_manager.c:248`). For those six cells it doesn't read the block's
props. It builds them from the save instead ([§5](#5-how-placed-objects-are-saved-and-drawn)).

In map coordinates the areas cover x 32-127 and z 32-95, 32 tiles each
(`src/field/safari_zone_placement.c:22-26`). `SafariZone_GetAreaIndexAt` turns a
position into a slot: `(x - 32) / 32 + ((z - 32) / 32) * 3`, or 0 if outside
(`safari_zone_placement.c:46-52`). The encounter code uses the player's slot
(`FieldSystem_GetSafariAreaIndex`, line 54).

## 2. The Area Customizer

The machine at the gate is the map's `Sign` event
(`SafariZoneEntranceInterior_EventScript_Sign`, `scripts.pory:1275`). It prints "It
is still under development." while `VAR_UNK_4057` is 0-3 (`scripts.pory:1279-1282`),
and otherwise runs `launchsafariareacustomizer` (line 1290). If the layout changed,
the app sets `FLAG_UNK_99D` and the script shakes the screen (lines 1294-1300;
`ChangeFlag99D`, `safari_area_customizer.c:376`).

The app copies set 0, edits the copy, and writes it back on exit
(`SafariAreaCustomizer_InitFromArgs` / `_SaveResults`,
`src/application/safari_area_customizer.c:358-378`). The slot menu offers "Switch"
and "Sort" (`msg_0429_00007`, `_00008`). The code has two edits:

| Action | Code | Effect on objects |
|---|---|---|
| put another area in the slot | `SafariAreaCustomizer_ChooseArea` (line 880), `_HandleConfirmArea` (line 647) → `SafariZone_InitAreaInSet` | the slot is cleared: **its objects are deleted**. Once objects are unlocked the app asks first ("All placed objects will be removed", `msg_0429_00003`). |
| swap two slots | `SafariAreaCustomizer_SwapAreas` (line 721) → `SafariZone_SwapAreasInSet` | each area keeps its objects (the whole slot struct is swapped, `src/safari_zone.c:219-223`) |

Baoba tells the player that swapping areas removes all objects (`scripts.pory:570-571`).
In the code only replacing an area does.

**Area unlock conditions:** there are none in the code. The area list is two pages of
six, all 12 areas, and the only choice refused is the area already in that slot
(`safari_area_customizer.c:912`, `1012`). I found no check against the other five
slots, so the same area may be placeable twice; see [Not verified](#not-verified).
What gates areas is the customizer itself: `VAR_UNK_4057` must reach 4.

### Story progress: `VAR_UNK_4057`

| Value | Set by | Meaning |
|---:|---|---|
| 1 | Baoba's call in Olivine (`data/maps/Olivine/scripts.pory:33-35`) | invited |
| 2 | first gate visit, `GentlemanScene1` (`scripts.pory:185`) | test 1: catch a Geodude |
| 3 | showing it (`scripts.pory:405`, plus `updatesafarizoneigt`) | waiting for Baoba's call |
| 4 | Baoba's call `PHONE_SCRIPT_142` (`phone_scripts_baoba.c:22-24`), at least 3 play-time hours later | customizer works |
| 5 | next gate visit, `GentlemanScene2` (`scripts.pory:263`) | test 2: catch a Sandshrew |
| 6 | showing it (`scripts.pory:459-460`) | Safari Zone Owner |
| 7 | the "Object Arrangement" call (`phone_scripts_baoba.c:38`) | objects unlocked |

Test catches are checked by `ScrCmd_CheckSafariZoneChallengeCompleted`
(`src/overlay_03/overlay_03_scrcmds.c:111`): a party Pokémon of that species, your
OT id, not hatched (`MON_DATA_EGG_LOCATION` is 0), met in the Safari Zone's map
section.

## 3. Objects

### The list

`sObjects` (`src/safari_zone_encounters.c:41-66`) has one row per object id
(`SAFARI_ZONE_OBJECTID_*`). Names are `msg_0430` entries 14-37, descriptions 38-61.
"Group" is the unlock group ([below](#unlock-groups)).

| Id | Name | Type | W×H | Model | Group |
|---:|---|---|---|---|---:|
| 0 | Shrubbery | plains | 1×1 | `SAF_GO01` | 0 |
| 1 | Red Flower | plains | 1×1 | `SAF_GO02` | 0 |
| 2 | White Flower | plains | 1×1 | `SAF_GO03` | 0 |
| 3 | Tree | forest | 2×2 | `SAF_TO01` | 1 |
| 4 | Stump | forest | 2×2 | `SAF_TO02` | 1 |
| 5 | Branches | forest | 2×2 | `SAF_TO03` | 1 |
| 6 | Small Rock | peak | 1×1 | `SAF_RO01` | 2 |
| 7 | Big Rock | peak | 2×2 | `SAF_RO02` | 2 |
| 8 | Mossy Rock | peak | 2×2 | `SAF_RO03` | 2 |
| 9 | Puddle | water | 2×2 | `SAF_WO01` | 3 |
| 10 | Fountain | water | 2×2 | `SAF_WO02` | 3 |
| 11 | Water Hole | water | 2×2 | `SAF_WO03` | 3 |
| 12 | Bench | none | 2×1 | `SAF_EO01` | 0 |
| 13 | Short Fence1 | none | 1×1 | `SAF_EO02` | 1 |
| 14 | Short Fence2 | none | 1×1 | `SAF_EO03` | 1 |
| 15 | Long Fence1 | none | 2×1 | `SAF_EO04` | 3 |
| 16 | Long Fence2 | none | 1×2 | `SAF_EO05` | 3 |
| 17 | Signboard | none | 1×1 | `SAF_EO06` | 1 |
| 18 | Your Statue | none | 1×1 | `SAF_EO07M` / `F` | 3 |
| 19 | Your Flag | none | 1×1 | `SAF_EO08M` / `F` | 0 |
| 20 | Outside Lamp | none | 1×1 | `SAF_EO09` | 0 |
| 21 | Guidepost(R) | none | 1×1 | `SAF_EO10` | 2 |
| 22 | Guidepost(L) | none | 1×1 | `SAF_EO11` | 2 |
| 23 | Trash Can | none | 1×1 | `SAF_EO12` | 2 |

`SafariObjectConfig` (`include/safari_zone_encounters.h:15`) fields:

| Field | Meaning |
|---|---|
| `buildModel` | the 3D model (`BUILD_MODEL_*`, `include/constants/buildmodel.h`) |
| `isAnimated` | **misnamed: it means "placed on water"**. Only the Fountain has it, its description says "You can place it using Surf.", and the list screen compares it with "is the player surfing" (`safari_decoration.c:1377`). |
| `width`, `height` | footprint in tiles, 1 or 2 each |
| `hasGenderedLayout` | the model id + 1 is used for a female player (`GetSafariObjectConfig`, `safari_zone_encounters.c:69-80`) |
| `objectType` | `SAFARI_ZONE_OBJECT_TYPE_NONE` / `PLAINS` / `FOREST` / `PEAK` / `WATER`: which points the object earns |

**Costs:** objects cost nothing; the code has no price or stock for them. **Limits:**
30 objects per area (`SAFARI_ZONE_MAX_OBJECTS`), checked in
`FieldSystem_CheckSafariObjectPlacement` (`safari_zone_placement.c:216`) and by the
"N left to place" counter (`safari_decoration.c:408`). There is no limit for the whole
zone other than 6 × 30.

### Unlock groups

The objects come in four groups of six, `gSafariDecorationObjectGroups`
(`asm/safari_decoration_data.s:136-156`):

| Group | Objects |
|---:|---|
| 0 | Shrubbery, Red Flower, White Flower, Your Flag, Outside Lamp, Bench |
| 1 | Tree, Stump, Branches, Short Fence1, Short Fence2, Signboard |
| 2 | Small Rock, Big Rock, Mossy Rock, Guidepost(R), Guidepost(L), Trash Can |
| 3 | Puddle, Fountain, Water Hole, Long Fence1, Long Fence2, Your Statue |

The save's `objectUnlockLevel` (0-4, `SafariZone_SetObjectUnlockLevel` caps it at 4,
`src/safari_zone.c:139-145`) says how many groups you have. **Which** groups depends on
the last digit of the 32-bit trainer id: `gSafariDecorationTrainerGroups[tid % 10]`
(`asm/safari_decoration_data.s:158-161`) lists the order, and the list screen offers
the first `objectUnlockLevel` groups (`SafariDecoration_CreateObjectList`,
`safari_decoration.c:1424-1455`):

| `tid % 10` | Group order |
|---|---|
| 0, 1, 2 | 0, 1, 2, 3 |
| 3, 4, 5 | 1, 2, 3, 0 |
| 6, 7 | 2, 3, 0, 1 |
| 8, 9 | 3, 0, 1, 2 |

Placing from Surf has its own copy of this rule.
`SafariZone_IsWaterObjectPlacementUnlocked` (`safari_zone_placement.c:187-200`)
works out where group 3 sits in the order from the digit, and allows water placement
only once `objectUnlockLevel` reaches that position. It doesn't read the table, so
the two must be changed together.

`objectUnlockLevel` grows only through Baoba's calls. `GearPhoneRingManager_CheckSafariCalls`
(`src/gear_phone_ring_manager.c:156-202`) does nothing while a Baoba call is pending,
while `VAR_UNK_4057` < 3, or once the level is 4. From `VAR_UNK_4057` = 6 it also
needs the National Dex and 3 play-time hours since the last unlock time
(`SafariZone_CheckUnlockWaitPassed`, `src/safari_zone.c:151-164`):

| Level now | Call | Effect (`phone_scripts_baoba.c:25-33`) |
|---:|---|---|
| 0 | "Object Arrangement" (`PHONE_SCRIPT_143`) | +1, restart the 3 hours, `VAR_UNK_4057` = 7 |
| 1, 2 | "new objects" (`PHONE_SCRIPT_144`) | +1, restart the 3 hours |
| 3 | "so many objects" (`PHONE_SCRIPT_145`) | +4 (capped at 4) |
| 0-2, play time at 999:59 | "time loop" (`PHONE_SCRIPT_146`) | +4 (capped at 4) |

The calls are rows 7-11 of `sPhoneCallTriggers` (`src/field/gear_phone_calls.c:46-54`).
At `VAR_UNK_4057` = 7 the gate attendants send you to Baoba first, and talking to him
sets `FLAG_UNK_183` (`scripts.pory:474-475`, `650-656`).

### Where an object can go

Pressing A in the Safari Zone calls `std_safari_place_object` when
(`src/field/field_control.c:612-620`) `FieldSystem_CanPlaceSafariObject` is true
(`safari_zone_placement.c:59-123`):

- the map is `MAP_SAFARI_ZONE_ENTRANCE_EXTERIOR`, the Safari flag is set, you are in
  your own zone (active set 0), and `objectUnlockLevel` ≥ 1;
- the tile in front is inside the areas and at the same height as you;

and the tile in front can take an object: no collision and behavior
`TILE_BEHAVIOR_0`, `SAND` or `MUD` on foot (`MetatileBehavior_CanPlaceSafariObjectOnLand`,
`src/metatile_behavior.c:542-544`), or surfable water when surfing.

The script (`scr_seq_0262.s`, script 0) first runs `CheckSafariObjectPlacement`
(`FieldSystem_CheckSafariObjectPlacement`, `safari_zone_placement.c:203-229`): 1 if
the area has 30 objects, 2 if surfing and water objects aren't unlocked, 3 if surfing
and there is no 2×2 water spot. Then the list screen opens.

`SafariDecoration_CreateArgs` (`safari_zone_placement.c:139-185`) has already
looked for one spot per size class: 1×1 is the tile in front; 1×2, 2×1 and 2×2 are
searched around it (`SafariZone_FindSpotFor*Object`, lines 261-443, using
`gSafariZonePlacementOffsets`, `asm/field_move_effects_data.s:658`). A spot needs every
tile placeable and at the same height. On the list screen an object is refused
(`SafariDecoration_CheckObjectPlaceable`, `safari_decoration.c:1373-1386`) if the area
is full, if its "on water" flag doesn't match whether you are surfing ("Cannot place
on land." / "...on the waterside."), or if its size class has no spot.

## 4. The object screen and `safari_decoration_task.c`

`ScrCmd_StartSafariDecoration` (`overlay_03_scrcmds.c:25`) calls
`CallTask_SafariDecoration` with a script variable. `Task_SafariDecoration`
(`src/safari_decoration_task.c:17-43`) has four states: launch the app
(`SafariDecoration_LaunchApp`), wait until it closes and copy `placedObject` into the
variable, restore the overworld, free itself. `placedObject` is the placed object's id,
or 255 if nothing was placed (`safari_decoration.c:416`, `537`). The script uses it to
print "Placed {name}!" (`scr_seq_0262.s`, script 0).

The app works on a copy of set 0 and writes it back on exit
(`SafariDecoration_InitFromArgs` / `_SaveResults`, `safari_decoration.c:383-431`).
The list cursor position is kept in `fieldSystem->safariDecorationCursorPos` between
visits.

## 5. How placed objects are saved and drawn

`SafariDecoration_PlaceObject` (`safari_decoration.c:526-538`) stores a
`SAFARIZONE_OBJECT` (`include/safari_zone.h:10`):

| Field | Is |
|---|---|
| `id` | object id |
| `x` | spot x `% 32`: column inside the area |
| `y` | the player's height, whole units (`args->height`, `safari_zone_placement.c:165`) |
| `z` | spot z `% 32`: the object's **south** row inside the area |

An object covers columns `x .. x + width - 1` and rows `z - height + 1 .. z`
(`map_prop_manager.c:173-177`). `SafariZone_AddObjectToArea` appends it
(`src/safari_zone.c:229-242`).

When an area cell loads, `MapLoadManager_LoadSafariZoneProps`
(`map_load_manager.c:451-473`) takes the slot's objects from the active set, and the
link leader's gender for a friend's zone. `MapPropManager_LoadFromSafariZone`
(`map_prop_manager.c:140-184`) makes one prop per object:

- model `buildModel`; if that model isn't loaded for the area, model 0 is used
  (line 178);
- position x = `16x + 8·width - 256`, z = `16z + 8·(2 - height) - 256`, y = `y`;
- every tile of the footprint gets permission `0x8023`: collision plus behavior
  `0x23` (`TILE_BEHAVIOR_35`, `MetatileBehavior_IsSafariPlacedObject`,
  `metatile_behavior.c:550`).

Pressing A on such a tile in your own zone runs `std_safari_remove_object`
(`field_control.c:623-626`). `GetFacingSafariObject` finds the object
(`safari_zone_placement.c:232-259`). `ScrCmd_RemoveSafariObject`
(`overlay_03_scrcmds.c:44-103`) restores the footprint's permissions from the block's
own, hides the prop, and calls `SafariZone_RemoveObjectFromArea`, which shifts the
later objects down (`src/safari_zone.c:244-265`).

`FieldSystem_GetFacingSafariObject` has a bug: when nothing is found it writes
`*objectIndex` without the NULL check it uses above (`safari_zone_placement.c:256-257`).

## 6. Object points, area age and bonus Pokémon

Nothing in this code raises a wild Pokémon's level. What objects and days change is
**which species** appear: bonus entries replace base slots. Each bonus entry has its
own fixed level in the JSON.

### Area age

`areaLevels[area id]` in set 0 is the area's age in days (`u8`, capped at 255,
`SafariZone_AddToAllAreaLevels`, `src/safari_zone.c:102-128`). It grows in
`SaveData_SafariZone_CheckAreasWithUpdatedEncounters`
(`safari_zone_encounters.c:110-176`), which `FieldSystem_HandleDaysPassed` calls with
the number of days passed, unless the RTC penalty is active
(`src/field_time_events.c:89-91`; [day-night-and-rtc.md](day-night-and-rtc.md)):

- nothing happens while `objectUnlockLevel` is 0 (line 123);
- inside the Safari Game the days are added to `SafariZone.level` instead
  (lines 127-131), and applied when you leave (`ScrCmd_SafariZoneAction` 1,
  `src/scrcmd_c.c:3417-3420`);
- only the areas in the six slots age, each id once even if it is in two slots;
- the age belongs to the area id, not the slot. `SafariZone_InitAreaInSet` clears the
  slot, not `areaLevels`, so an area keeps its age when switched out and back in. Only
  a new game clears it (`src/safari_zone.c:46`).

### Points per object

`SafariZoneAreaSet_GetObjectsInArea` (`safari_zone_encounters.c:278-301`) adds up
points per type for one slot. Each object of a type adds
`getObjectLevelBoost(age / 10, type)` (lines 263-276, table `sObjectLevelBoosts`,
lines 255-260). Per object, by area age in days:

| Points | Plains | Forest | Peak | Water |
|---:|---|---|---|---|
| 1 | 0-9 | 0-19 | 0-29 | 0-39 |
| 2 | 10-49 | 20-59 | 30-69 | 40-79 |
| 3 | 50-99 | 60-109 | 70-119 | 80-129 |
| 4 | 100-149 | 110-159 | 120-169 | 130-179 |
| 5 | 150-199 | 160-209 | 170-219 | 180-229 |
| 6 | 200-249 | 210-249 | 220-249 | 230-249 |
| 7 | 250+ | 250+ | 250+ | 250+ |

Objects of type "none" earn nothing. The totals cap at 255.

### Bonus entries

`SafariZoneAreaSet_LoadAreaEncounters` (`safari_zone_encounters.c:178-252`) builds
the 10 slots for a slot, an encounter type and a time of day:

1. Fill with Rattata (land) or Magikarp (water), level 5 (lines 191-198).
2. Load the area's file from `a/2/3/0`, member = area id (line 200).
3. If the area has **no surf bonus entries**, return those placeholders for surf and
   all rods (lines 217-221). Every area has 3 surf bonuses today.
4. Copy the 10 base slots for the time of day (lines 222-227).
5. Walk the bonus list in order. An entry is on if the slot's points for
   `object_type` ≥ `count`, and, if it has a second condition, the same for that one
   (lines 235-240). The *n*-th entry that is on overwrites slot *n*, starting at slot 0
   (lines 241-246). At most 10 can be on.

So the JSON's `count` is a **point total**, not a number of objects. Plains'
first land bonus (`PLAINS`, 3) needs three plains objects in a new area, or two once
the area is 10 days old. Bonus entries fill from slot 0, so the order of the list
decides which base slots disappear first. `bonus_param` is not read by the template
(`files/arc/safari_enc.json.txt`).

Slots are equally likely ([§8](#encounters)), so each bonus that is on is a 1-in-10
slot.

## 7. Baoba's "new Pokémon" call

After aging the areas, `SaveData_SafariZone_CheckAreasWithUpdatedEncounters` compares
each slot's five morning tables before and after (lines 136-161). The areas that
changed are stored with `PhoneCallPersistentState_SafariZoneArrangement_Set`, and
`CALL_TRIGGER_BAOBA_NEW_POKEMON` is set (lines 169-175). `GearPhoneCall_Baoba`
(`phone_scripts_baoba.c:47-80`) names up to five areas, or uses a "many areas" line
for six. See [phone.md](phone.md) for how calls are triggered.

## 8. The Safari Game

### Entering and leaving

The attendant charges 500 (`scripts.pory:698-704`), refusing if the party and the PC
are full (lines 693-696). `SafariZoneAction 0, set` (`src/scrcmd_c.c:3408-3413`) sets
`FLAG_SYS_SAFARI`, makes `set` active (0 at line 729 for your zone, 1 at line 1166 for
the friend's), and gives **30 Safari Balls**. `SafariZoneAction 1` (lines 3414-3423)
clears the flag, makes set 1 active, applies the stored days and zeroes the balls.
A friend's zone expires after 24 hours or if the system clock offset changes
(`SafariZone_DeactivateLinkIfExpired`, `src/safari_zone.c:201-217`).

### Limits and game over

| Rule | Code |
|---|---|
| out of balls: "You've run out of Safari Balls." | `FieldSystem_UpdateSafari` (`field_control.c:814-824`), and after a battle (`src/encounter.c:457-460`) |
| party and PC full: "You're out of room" | after a battle (`encounter.c:461-466`); in battle, `BtlCmd_CheckSafariGameDone` (`src/battle/battle_command.c:5665`) |
| **no step limit** | `SafariZoneAction` zeroes `safariStepCounter`, but nothing else reads or counts it (`src/save_local_field_data.c:112`; no other callers). The "Time's up!" script `std_safari_steps_out` exists (`scr_seq_0262.s`, script 2) but no C code starts it. |

The start menu and field moves are limited separately
([start-menu.md](start-menu.md); `FieldMove_CheckSafariOrPalPark`, `src/field_move.c:89`).

### Encounters

`FieldSystem_GenerateSafariEncounter` (`src/field/encounter_check.c:934-977`) loads
the player's slot from the active set. The slot is Magnet Pull / Static's pick or
`LCRandom() % 10` (line 963); on land, Hustle/Pressure/Vital Spirit may switch to a
higher-level slot of the same species. The level is the slot's level (line 969). Repel
applies ([encounter-mechanics.md](encounter-mechanics.md)). The Pokémon is created
with `forceOnePerfectIV` = TRUE (line 975): up to four tries to get at least one IV of
31 (lines 857-871).

### Battle actions

The Safari battle has two stages, both starting at 6 (`src/battle/battle_util.c:1773-1774`):
a **catch stage** and a **flee stage**. Inputs (`battle_controller_player.c:346-372`):

| Input | Action | Handler | Effect |
|---:|---|---|---|
| 1 | Ball | `BattleControllerPlayer_SafariThrowBall` (1814) | subscript 275, one ball used |
| 2 | Bait | `BattleControllerPlayer_SafariThrowMud` (1828) | subscript 227 (Bait). Flee stage -1. 9 in 10: catch stage -1 ("is eating!"); else no change ("is busy eating!"). |
| 3 | Mud | `BattleControllerPlayer_SafariRun` (1846) | subscript 228 (Mud). Catch stage +1. 9 in 10: flee stage +1 ("is angry!"); else no change ("is beside itself with anger!"). |
| 4 | Run | `CONTROLLER_COMMAND_RUN_INPUT` | |

The two handler names are wrong: the scripts they run are `BATTLE_SUBSCRIPT_SAFARI_THROW_BAIT`
(227) and `_THROW_ROCK` (228) (`include/constants/battle_subscript.h:232-233`), whose
text is Bait and Mud (`subscript_0227_SafariThrowBait.s`, `subscript_0228_SafariThrowBall.s`).
Stages stay within 0-12.

**Catch:** with a Safari Ball, the species' catch rate is multiplied by
`sSafariCatchRateStages[catch stage]` (`battle_command.c:7158-7161`), a fraction from
10/40 (×0.25) through 10/10 (stage 6) to 40/10 (×4)
(`asm/overlay_12_battle_command.s:113-126`). The Safari Ball's own multiplier is 15
(×1.5, `sStandardBallCatchRates`, line 16; `battle_command.c:7297`). The rest is the
normal catch formula.

**Flee:** each turn the wild Pokémon picks in `Task_SafariSelectCommand`
(`battle_controller_opponent.c:4448-4463`): `chance = greatMarshRate × num / den` with
`gSafariFleeRates[flee stage]` (`asm/battle_controller_opponent_data.s:24-26`, the same
13 fractions). If `rand % 255 ≤ chance` it runs (input 4); otherwise it is "watching
carefully" (input 5, subscript 229). `greatMarshRate` is per species in
`files/poketool/personal/personal.json` ([pokemon.md](pokemon.md)).

## 9. How-tos

### Change an area's encounters

Edit the area's entry in `files/arc/safari_enc.json`
([wild-encounters.md](wild-encounters.md#safari-zone)). Rules from the code:

- keep the 12 entries in area-id order: the file for area *n* is NARC member *n*;
- keep 10 `mons` per time of day;
- keep at least one `surf` bonus entry, or the area's surf and rod tables become
  Magikarp 5 ([§6](#bonus-entries));
- `conditions` take one or two `{object_type, count}`; `count` is points;
- a bonus entry overwrites slot 0, 1, 2... in the order the entries are on.

```json
{
    "conditions": [
        {"object_type": "SAFARI_ZONE_OBJECT_TYPE_PLAINS", "count": 3},
        {"object_type": "SAFARI_ZONE_OBJECT_TYPE_WATER", "count": 2}
    ],
    "morn": {"species": "SPECIES_GIRAFARIG", "level": 40},
    "day":  {"species": "SPECIES_GIRAFARIG", "level": 40},
    "nite": {"species": "SPECIES_STANTLER", "level": 40}
}
```

To make bonuses easier to get, lower the `count`s, or change `sObjectLevelBoosts`
(`safari_zone_encounters.c:255-260`) so objects earn points faster.

### Change an object's type, size or group

- **Type or size:** its row in `sObjects`. Objects already in a save are redrawn with the
  new size.
- **Group:** move its id between the `gSafariDecorationObjectGroup0`-`3` byte lists
  (`asm/safari_decoration_data.s:136-150`), and fix the count word in
  `gSafariDecorationObjectGroups` (line 153-156) if a group's size changes.
- **Group order per trainer id:** `gSafariDecorationTrainerGroups` (line 158). If group 3
  moves, change `SafariZone_IsWaterObjectPlacementUnlocked` to match.

### Add an object

Every place that assumes 24 objects:

1. `include/constants/safari.h`: a new id, `NUM_SAFARI_ZONE_OBJECT_IDS` + 1. The list
   is built from a `u32` bit mask, so 32 at most (`safari_decoration.c:1427-1451`).
2. A row in `sObjects`.
3. Add the id to a group.
4. The loop `for (i = 0; i < 24; i++)` (`safari_decoration.c:1443`) and the `>= 24`
   check in `BufferSafariZoneObjectName` (`src/message_format.c:595`).
5. Text: names are read at `id + 14` and descriptions at `id + 38`
   (`safari_decoration.c:1256`, `1288`, `1319`, `1360`; `message_format.c:599`). They
   are back to back, so a 25th name would land on the first description. Move the
   descriptions or change the offsets.
6. A camera entry in `gSafariDecorationObjectCameraPositions`
   (`asm/safari_decoration_data.s:42`, read by id at `safari_decoration.c:648`).
7. The model: the preview loads it from `a/0/4/0` with info from `a/1/0/7`
   (`safari_decoration.c:565-566`, `624`, `635`). On the map, a model that isn't
   loaded for the area is drawn as model 0 (`map_prop_manager.c:178`). The area's
   prop list is `a/0/4/3` (`src/field/area_data.c:26`, `178`), so the new model
   probably has to be added there.

The save stores ids as `u8`, so it doesn't change.

### Change when objects and the customizer unlock

Give all four groups from the start, in `InitGameStateAfterOakSpeech_Internal`:

```diff
     SafariZone *safari_zone = Save_SafariZone_Get(saveData);
     SafariZone_ResetAreaSetToDefaultSet(safari_zone->area_sets, rand);
+    SafariZone_SetObjectUnlockLevel(safari_zone, 4);
```

That also starts area aging at once, and Baoba's object calls never ring (they stop at
level 4, `gear_phone_ring_manager.c:168`). Other knobs:

| To | Change |
|---|---|
| open the customizer earlier | the four `VAR_UNK_4057` checks in the `Sign` script (`scripts.pory:1279-1282`) |
| shorten Baoba's waits | the `3` (hours) in `gear_phone_ring_manager.c:172` and `183` |
| drop the National Dex requirement | `gear_phone_ring_manager.c:180-182` |
| unlock more per call | the `+1` / `+4` in `phone_scripts_baoba.c:27`, `32` |

### Change the limits

| To | Change |
|---|---|
| Safari Balls per game | `30` in `src/scrcmd_c.c:3411`; the text numbers at `scripts.pory:624`, `708`, `1147` |
| entry fee | `500` at `scripts.pory:669`, `679`, `698`, `700`, `704`, and `1137`, `1139`, `1143` for a friend's zone |
| fewer objects per area, same save | the literal `30` in `safari_zone_placement.c:216` and `SAFARI_ZONE_MAX_OBJECTS` in `safari_decoration.c:408`; leave the constant alone |
| catch / flee per stage | `sSafariCatchRateStages`, `gSafariFleeRates` (asm); start stages in `battle_util.c:1773-1774` |
| Bait / Mud odds | `% 10` in `battle_controller_player.c:1834`, `1852` |

```diff
-    if (areaSet->areas[areaIndex].active_object_count >= 30) {
+    if (areaSet->areas[areaIndex].active_object_count >= 20) {
         return 1;
```

with the same 20 in place of `SAFARI_ZONE_MAX_OBJECTS` at `safari_decoration.c:408`.

**More** than 30 per area is harder. `SAFARI_ZONE_MAX_OBJECTS` sizes the saved array,
so the save layout changes; the link packet size `744` is written out by hand
(`custom_safari_zone.c:43`, `50`); and one cell holds at most `MAP_PROP_MAX` (32)
props (`include/field/map_load_manager.h:8`).

## 10. Saves

`SAVE_SAFARI_ZONE` is 1532 bytes in block 0 ([save-data.md](save-data.md)):
two layouts of 744 bytes, the link leader, the stored days, `objectUnlockLevel`
(6 bits), `activeAreaSet` (2 bits), and `unlockTime` (play-time minutes). Changing
encounters, object types, groups, points or the unlock calls doesn't touch it.
Changing `SAFARI_ZONE_MAX_OBJECTS`, the number of areas per set, or the number of area
ids (`areaLevels[12]`) does, and old saves won't load.

## Not verified

- Nothing here was built or tried in game. All the diffs and recipes (unlock at new
  game, 20-object cap, new object checklist) are unbuilt.
- Which menu word ("Switch", "Sort") leads to which edit in §2.
- That the same area can be put in two slots: only the absence of a check was seen.
- That a new object's model must be in the area's `a/0/4/3` prop list; the code only
  shows that unloaded models fall back to model 0.
- Which menu buttons send inputs 2 and 3; the mapping to Bait and Mud comes from the
  scripts the handlers run, not from the battle menu code.
- That `BattleContext_Get(..., 5, ...)` in `BattleSystem_GetSafariRunAttempts` reads the
  flee stage (`safariRunAttempts`); it was assumed from the name.
- Why leaving the zone makes set 1 active (`src/scrcmd_c.c:3416`), and whether anything
  reads it outside the zone.
- What `data/maps/SafariZone01`-`14` are used for; the areas themselves are all part of
  `MAP_SAFARI_ZONE_ENTRANCE_EXTERIOR`.
- The Safari Zone Link exchange was only skimmed (`custom_safari_zone.c`).
- Object glow at night and the customizer's per-type object counts on the top screen
  (`SafariAreaCustomizer_PrintSlotInfo`, line 1634) were not traced.
