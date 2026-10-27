<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Apricorns and Kurt

> AI-generated; not affiliated with pret. See AI.md at the repository root.

There are 31 Apricorn trees in Johto and Kanto. Each tree always gives the same colour.
You shake it, get one Apricorn, and it grows back the next day. Apricorns go into the
**Apricorn Box**, which holds up to 99 of each colour. Kurt in Azalea Town turns one
colour of Apricorn into balls, one ball per Apricorn, ready the next day. The seven
**Apricorn balls** have their own catch-rate rules in battle. Apricorns can also be
blended into Aprijuice for the Pokéathlon, which this guide only touches on.

| pokeemerald | here |
|---|---|
| berry trees (`gBerryTrees`, `src/berry.c`) | Apricorn trees: one colour table in C plus one save flag per tree |
| berry tree id in an object's `trainer_range_berry_tree_id` | tree index in the object's `trainer_sight_or_param0` |
| `EventScript_BerryTree` (shared script) | `std_apricorn_tree`, `files/fielddata/script/scr_seq/scr_seq_0150.s` |
| berries in the Bag's berry pocket | Apricorns in the Apricorn Box save chunk, not in the Bag |
| ball catch-rate switch in `Cmd_handleballthrow` | `BattleSystem_CalculateBallShakes`, `src/battle/battle_command.c:7150` |

## Where things are

| What | File |
|---|---|
| Apricorn colours (`APRICORN_RED` ... `APRICORN_BLK`, 1-7; 0 = none) | `include/constants/apricorns.h:4` |
| which colour each tree gives (`sTreeApricorns`) | `src/apricorn_tree_sys.c:8` |
| number of trees, save slots (`NUM_APRICORN_TREE` 31, `MAX_APRICORN_TREE` 128) | `include/save_misc_data.h:35` |
| tree save struct (`APRICORN_TREE`) | `include/save_misc_data.h:10` |
| the shared tree script | `files/fielddata/script/scr_seq/scr_seq_0150.s`, text `files/msgdata/msg/msg_0023.json` |
| `std_apricorn_tree` = 2800 → `scr_seq_0150` | `include/constants/std_script.h:79`, `src/script_manager.c:61` |
| shaking and picking (the animation task) | `Task_AnimApricornTree`, `src/field/apricorn_tree_anim.c:77` |
| tree script commands | `src/scrcmd_apricorn.c` |
| field helpers (`FieldSystem_ApricornTree_*`) and daily regrowth | `src/field_time_events.c:156`-`203` |
| tree sprite (full or empty) | `ApricornTreeObject_Update`, `src/map_object_behavior.c:355` |
| Apricorn Box save data (`SaveApricornBox`) | `include/apricorn_internal.h:56` |
| Apricorn Box logic: counts, Kurt, juice | `src/apricorn_box.c` |
| Apricorn → ball table (`sApricornBallItems`) | `src/apricorn_box.c:33` |
| Kurt's house | `data/maps/Azalea_KurtHouse/scripts.pory` |
| Kurt script commands | `src/field/scrcmd_pokemon_misc.c:840`-`878` |
| Kurt on the phone | `src/application/pokegear/phone/scripts/phone_scripts_kurt.c` |
| ball catch rates | `src/battle/battle_command.c:7150`; Moon Ball list `asm/overlay_12_battle_command.s:130` |

**Three numberings.** Be careful which one a function wants:

| Numbering | Red ... Black | Used by |
|---|---|---|
| `APRICORN_*` constants | 1 ... 7 (0 = none) | `sTreeApricorns`, `ApricornTrees_TryGetApricorn` |
| box index | 0 ... 6 | `SaveApricornBox.apricorns[]`, `sApricornBallItems`, `ApricornBox_*`, `BufferApricornName`, script variables |
| items | `ITEM_RED_APRICORN` (485) ... `ITEM_BLK_APRICORN` (491) | shops; box index = item − `ITEM_RED_APRICORN` (`src/overlay_03/shop_menu.c:770`) |

`ApricornTrees_GetApricorn` converts the first to the second by subtracting 1
(`src/apricorn_tree_sys.c:86`).

## 1. Apricorn trees

### Where they are and what they give

A tree is a map object with `graphics_id` `SPRITE_BONGURI`, script `std_apricorn_tree`,
and its **tree index** in `trainer_sight_or_param0`. Route 30's first tree
(`data/maps/Route30/map.json:217`):

```json
{
    "local_id": "obj_R30_bonguri",
    "graphics_id": "SPRITE_BONGURI",
    "x": 553, "y": 355, ...
    "trainer_sight_or_param0": 6,
    "script": "std_apricorn_tree",
    "flag": "FLAG_NOTHING"
}
```

The game reads the index with `MapObject_GetParam(mapObj, 0)` (`src/field_time_events.c:193`)
and looks it up in `sTreeApricorns` (`src/apricorn_tree_sys.c:8`). The colour is in that
table, not on the map. All 31 trees, from the `map.json` files and the table:

| Index | Map | Colour | Index | Map | Colour |
|---:|---|---|---:|---|---|
| 0 | Route1 | Black | 16 | Route38 | White |
| 1 | Route2_East (the table says "Route 2 North") | Pink | 17 | Route39 | Green |
| 2 | Route8 | Yellow | 18 | Route42 | Pink |
| 3 | Route11 | Green | 19 | Route42 | Green |
| 4 | Route26 | Blue | 20 | Route42 | Yellow |
| 5 | Route29 | Green | 21 | Route43 | Black |
| 6 | Route30 | Green | 22 | Route44 | Red |
| 7 | Route30 | Pink | 23 | Route45 | Green |
| 8 | Route31 | Black | 24 | Route46 | Green |
| 9 | Route33 | Pink | 25 | Route46 | Yellow |
| 10 | Route33 | Black | 26 | Pewter | Blue |
| 11 | Route35 | Green | 27 | Pewter | White |
| 12 | Route36 | Blue | 28 | Fuchsia | Red |
| 13 | Route37 | Red | 29 | Violet | Yellow |
| 14 | Route37 | Blue | 30 | Azalea | White |
| 15 | Route37 | Black | | | |

**The sprite.** Every tree is placed as `SPRITE_BONGURI` (262, the empty tree). The
tree objects are drawn by the Apricorn-tree callbacks (`gApricornTreeDrawCallbacks`,
`asm/overlay_01_sprite_data.s:115`, listed in `gMapObjectDrawCallbacks` at line 1363).
The `SPRITE_BONGURI*` rows of the sprite table are at line 1226. Each frame
`ApricornTreeObject_Update` swaps the sprite: the coloured tree from
`gApricornTreeSpriteIds` (`asm/overlay_01_sprite_data.s:319`) if the tree has an
Apricorn, `SPRITE_BONGURI` if not (`GetApricornTreeSpriteId`,
`src/map_object_behavior.c:463`). When a tree regrows while on screen, a small effect
plays (`ApricornRegrowth_Spawn`, `src/map_object_behavior.c:372`).

### Shaking a tree

`std_apricorn_tree` (`scr_seq_0150.s`) does this:

1. "It's an Apricorn Tree!" (line 14).
2. **No Apricorn Box**: "Since there's nothing to put it in..." and stop (lines 16-18,
   56). The tree is not shaken and keeps its Apricorn.
3. `AnimApricornTree` (line 19) runs `Task_AnimApricornTree`. If the tree is empty, the
   result is 0 and you get "There are no Apricorns..." (line 48). Otherwise the player
   shakes the tree, the tree is **marked picked** (`FieldSystem_ApricornTree_PickApricorn`,
   `src/field/apricorn_tree_anim.c:117`), and an Apricorn object of the right colour
   (`SPRITE_BONMI_R` + colour) jumps out (line 150).
4. `ApricornTreeGetApricorn` reads the colour as a box index (line 22).
5. `GiveApricornFromTree VAR_SPECIAL_x8000, 1, VAR_SPECIAL_RESULT` (line 31) adds **one**
   Apricorn, but only if the count stays at 99 or below (`src/scrcmd_apricorn.c:32`).
6. The game stat `SCORE_EVENT_APRICORN_HARVESTED` goes up (line 32).
7. If the box had 99 of that colour, you get "The Apricorn Box is full! ... gave up on
   the Apricorn" (line 41, `msg_0023_00006`). The tree was already picked in step 3, so
   **that Apricorn is lost** until tomorrow.

`msg_0023_00005` ("there's no Apricorn Box yet!") is not used by this script.

The tree has to look like an Apricorn tree for step 3 to work:
`FieldSystem_ApricornTreeObject_HasApricorn` returns FALSE unless the object's sprite is
one of `SPRITE_BONGURI_R` ... `_BK` (`src/field_time_events.c:177`).

### How picking is saved

`SAVE_MISC` holds `APRICORN_TREE apricorn_trees[MAX_APRICORN_TREE]`, 128 entries of 4
bytes (`include/save_misc_data.h:41`):

| Field | Use |
|---|---|
| `hasApricorn` | 1 = the tree has an Apricorn. The only field that is read (`ApricornTrees_HasApricorn`, `src/apricorn_tree_sys.c:66`). |
| `unk_1` | set to 1 with `hasApricorn` and to 0 when picked; never read |
| `unk_2` | never written after the save is cleared; free |

Only the first 31 entries belong to a tree. The other 97 are free save space that the
game fills anyway (see below).

### Daily regrowth

- **New game:** `ApricornTrees_GrowAll` (`src/overlay_36.c:204`) fills **all 128**
  entries, so every tree starts full (`src/apricorn_tree_sys.c:52`).
- **Each new day:** `FieldSystem_HandleDaysPassed` calls `FieldSystem_RegrowApricornTrees`
  (`src/field_time_events.c:87`), which calls `ApricornTrees_RegrowEmpty`
  (`src/apricorn_tree_sys.c:93`). Every empty entry, all 128, becomes full.

A "new day" is a new calendar date on the DS clock, checked on map loads and warps; it
is not 24 hours of play. Skipping five days still regrows each tree once, because there
is only one Apricorn per tree. Setting the clock back does nothing. Regrowth happens even
during the clock-change penalty (the call is before the `if (!hasPenalty)` at line 89).
See [day-night-and-rtc.md](day-night-and-rtc.md#5-when-a-day-or-minutes-pass).

## 2. The Apricorn Box

`SaveApricornBox` is save array `SAVE_APRICORN_BOX` (38, `include/constants/save_arrays.h:44`;
struct at `include/apricorn_internal.h:56`):

| Field | Meaning |
|---|---|
| `apricorns[7]` | how many of each colour, by box index |
| `kurtQuantity` | Apricorns Kurt is working on (0 = none) |
| `kurtApricorn` | their colour (box index) |
| `juiceServings`, `queuedApricorns`, `juice`, `mixStartSteps`, `juiceAgingSteps`, `mixWord` | the Aprijuice being blended |
| `juiceRecords[3]` | juice of other players, from the Pokéathlon |

**Capacity: 99 per colour.** `ApricornBox_GiveApricorn` clamps at 99
(`src/apricorn_box.c:101`). The tree command refuses instead of clamping
(`src/scrcmd_apricorn.c:32`), and the Pokéathlon shop won't sell a colour you have 99 of
(`src/overlay_03/shop_menu.c:883`). The counts are `u8`, so raising the limit above 255
needs a wider type, which changes the save layout
([save-compatibility.md](save-compatibility.md)).

Ways Apricorns arrive or leave:

| | Function |
|---|---|
| tree | `GiveApricornFromTree` (above) |
| Pokéathlon daily shop | `MartData_Inventory_AddApricornOrItem`, `shop_menu.c:941` |
| given to Kurt | `ApricornBox_SetKurtApricorn`, `apricorn_box.c:130` |
| put in the blender | `ApricornBox_QueueApricorn`, `apricorn_box.c:175` |

You get the Apricorn Box from a script on Route 30 (`giveitemnocheck(ITEM_APRICORN_BOX, 1)`,
`data/maps/Route30/scripts.pory:109` and `data/maps/Route30_ApricornHouse/scripts.pory:32`).
Using it from the Bag opens the box in blender mode (`ApricornBox_LaunchApp(fieldSystem, 1)`,
`src/field_use_item.c:603`).

### Aprijuice, briefly

The blender takes up to five queued Apricorns (`APRICORN_QUEUE_SLOT_COUNT`,
`include/apricorn_internal.h:33`). Each colour moves the five flavour values
(`sApricornFlavorDeltas`, `src/apricorn_box.c:43`). Mixing advances with steps walked
(`ApricornBox_UpdateSteps`, from `src/field/field_control.c:852`) and mildness grows by
day (`ApricornBox_AddJuiceMildnessForDays`, `src/field_time_events.c:90`, skipped during
the penalty). The juice is fed to Pokémon to raise their Pokéathlon stats; see
[pokeathlon.md](pokeathlon.md).

## 3. Kurt

### Kurt's script

`Azalea_KurtHouse_EventScript_Kurt` (`data/maps/Azalea_KurtHouse/scripts.pory:51`). Before
the Slowpoke Well, Kurt runs off (until `FLAG_UNK_07C`). Afterwards
`Azalea_KurtHouse_EventScript_KurtScene` gives item 492, which is `ITEM_FAST_BALL`
(`include/constants/items.h:954`), and sets `FLAG_UNK_07C` (lines 42-45). From then on
talking to Kurt goes to `_011A` (line 105):

```
getkurtapricornquantity(VAR_SPECIAL_x8000)
├─ not 0, FLAG_DAILY_KURT_MAKING_BALLS set → "I'm working! Don't bother me!"   (line 111, 133)
├─ not 0, flag clear → give the balls                                          (lines 113-127)
└─ 0:
   ├─ no Apricorns at all → "I make Poké Balls from Apricorns..."             (lines 139-144)
   └─ otherwise → open the Apricorn Box in Kurt mode                           (line 206)
        ├─ nothing chosen → "Oh... That's a letdown."                          (line 212)
        └─ chosen → setflag(FLAG_DAILY_KURT_MAKING_BALLS)                      (line 215)
                    "It'll take a day to make you a Poké Ball."
```

### What you can hand over

In Kurt mode the box lets you pick **one colour** you have at least one of, then a
quantity from 1 to everything you have of that colour (`ApricornBoxScreen_KurtSelect`,
`src/application/apricorn_box/apricorn_box_input.c:282`; `maxQuantity` at line 291).
On "yes", `ApricornBox_SetKurtApricorn` stores the colour and quantity and takes the
Apricorns out of the box (`src/application/apricorn_box/apricorn_box_screens.c:432`,
`src/apricorn_box.c:130`). The save has room for one colour only (`kurtApricorn` is one
byte).

### How long it takes

`FLAG_DAILY_KURT_MAKING_BALLS` (`0xAA2`, `include/constants/flags.h:2032`) is a daily
flag. `ClearDailyFlags` clears it at the next calendar date
(`src/script_manager.c:410`, called from `src/field_time_events.c:78`). So "a day" means
**after midnight**, not 24 hours: hand over Apricorns at 23:59 and they are ready at
00:00.

### What you get

- **Quantity:** one ball per Apricorn. The script copies `kurtQuantity` into the
  give-item count (`copyvar(VAR_SPECIAL_x8005, VAR_SPECIAL_x8000)`, line 117).
- **Type:** `getkurtball` → `ApricornBox_GetKurtBall` → `sApricornBallItems[kurtApricorn]`
  (`src/apricorn_box.c:144`). An out-of-range colour gives a Poké Ball (line 146).

| Box index | Apricorn | Ball (`src/apricorn_box.c:33`) |
|---:|---|---|
| 0 | Red | Level Ball |
| 1 | Yellow | Moon Ball |
| 2 | Blue | Lure Ball |
| 3 | Green | Friend Ball |
| 4 | Pink | Love Ball |
| 5 | White | Fast Ball |
| 6 | Black | Heavy Ball |

After handing them over, `clearkurtapricorn` sets colour and quantity to 0
(`ScrCmd_ClearKurtApricorn`, `src/field/scrcmd_pokemon_misc.c:846`).

**Full bag.** The script runs `hasspaceforitem` (line 116) but never looks at the result.
`std_give_item_verbose` (`scr_seq_0003_033`, `files/fielddata/script/scr_seq/scr_seq_0003.s:643`)
calls `GiveItem` without checking either, and `clearkurtapricorn` runs after it. The
"Your Bag is full!" text (lines 129-130) comes right after a `goto ... end`, so it can
never be shown. The original `scripts.inc` (before the `.pory` conversion,
commit `0d50fd018^`) has the same order. What happens to the balls when the Poké Ball
pocket can't take them was not tried; from the code, they are probably lost.
[§4](#4-how-tos) has a fix.

### Kurt counter and phone

- `VAR_UNK_413B` counts completed orders up to 10; at 10 the script sets `FLAG_UNK_127`
  (lines 120-124, 152).
- On the phone (`GearPhoneCall_Kurt`, `phone_scripts_kurt.c:18`) the first line is
  `msg_0643_00002`, or `msg_0643_00006` once `FLAG_UNK_127` is set. Then: no order →
  message 5; order not ready (daily flag set) → message 4; ready → message 3, with the
  ball name and `kurtQuantity` filled in (lines 37-47). Calling from Azalea gives
  `PHONE_SCRIPT_083` instead (line 10). See [phone.md](phone.md).

## 4. How-tos

### Add an Apricorn tree to a map

The save already has 128 tree slots and the game regrows all of them, so adding trees up
to 128 doesn't change the save layout, and old saves see the new tree as full.

1. **Colour and count.** Append a colour to `sTreeApricorns` and raise the count:

   ```diff
   --- a/include/save_misc_data.h
   -#define NUM_APRICORN_TREE 31
   +#define NUM_APRICORN_TREE 32
   --- a/src/apricorn_tree_sys.c
        APRICORN_WHT, // Azalea Town
   +    APRICORN_RED, // Route 29 (new)
    };
   ```

   `ApricornTrees_TryGetApricorn` does no bounds check (`src/apricorn_tree_sys.c:73`), so a
   map object with an index past the end of the table reads whatever follows it.

2. **The object.** Place a `SPRITE_BONGURI` with the shared script and index 31:

   ```sh
   M=tools/mapkit/mapkit.sh       # in fish: set M tools/mapkit/mapkit.sh
   $M npc add Route29 bonguri_2 SPRITE_BONGURI 600 392 --script std_apricorn_tree --sight 31
   ```

   `--sight` writes `trainer_sight_or_param0` (`tools/mapkit/mapkit/edit.py:136`). The tile
   (600, 392) is an example; pick a free one with `$M show Route29`. Leave
   `movement_type` as `MOVEMENT_TYPE_NONE` and `flag` as `FLAG_NOTHING`, like the
   existing trees. Each tree needs its **own** index: two objects with the same index
   share one save flag.

### Change a tree's colour

Change its entry in `sTreeApricorns` (`src/apricorn_tree_sys.c:8`); the index is the
object's `trainer_sight_or_param0` ([§1](#where-they-are-and-what-they-give)). Nothing on
the map changes. Save-compatible.

### Change regrowth

**Every N days instead of daily.** Use the free `unk_2` field as a day counter. Old saves
have 0 there, so this is save-compatible.

```diff
--- a/src/apricorn_tree_sys.c
-void ApricornTrees_RegrowEmpty(APRICORN_TREE *trees) {
+void ApricornTrees_RegrowEmpty(APRICORN_TREE *trees, int days) {
     int i;
     for (i = 0; i < MAX_APRICORN_TREE; i++) {
         if (!trees[i].hasApricorn) {
-            trees[i].hasApricorn = 1;
-            trees[i].unk_1 = 1;
+            trees[i].unk_2 += days;
+            if (trees[i].unk_2 >= 3) { // regrow after 3 days
+                trees[i].hasApricorn = 1;
+                trees[i].unk_1 = 1;
+                trees[i].unk_2 = 0;
+            }
         }
     }
 }
--- a/src/field_time_events.c
-    FieldSystem_RegrowApricornTrees(fieldSystem);
+    FieldSystem_RegrowApricornTrees(fieldSystem, days);
 ...
-void FieldSystem_RegrowApricornTrees(FieldSystem *fieldSystem) {
+void FieldSystem_RegrowApricornTrees(FieldSystem *fieldSystem, int days) {
     APRICORN_TREE *trees = Save_FieldApricornTrees_Get(fieldSystem->saveData);
-    ApricornTrees_RegrowEmpty(trees);
+    ApricornTrees_RegrowEmpty(trees, days);
 }
```

Update both prototypes: `include/apricorn_tree.h:14` (declared twice, lines 14 and 15)
and `include/field_time_events.h:32`. These are the only callers (one each).

**Never regrow:** delete the `FieldSystem_RegrowApricornTrees(fieldSystem);` line
(`src/field_time_events.c:87`). New games still start with every tree full.

**More Apricorns per shake:** change the `1` in
`GiveApricornFromTree VAR_SPECIAL_x8000, 1, VAR_SPECIAL_RESULT`
(`scr_seq_0150.s:31`). The messages say "the Apricorn" without a number. The 99 check
uses the new amount, so near the cap you get nothing rather than fewer.

### Kurt: faster, more balls, other balls

All in `data/maps/Azalea_KurtHouse/scripts.pory` unless noted.

**Ready right away.** Remove `setflag(FLAG_DAILY_KURT_MAKING_BALLS)` (line 215) and
change the "It'll take a day" text (lines 216-217). The phone also reads this flag
(`phone_scripts_kurt.c:41`), so it will say the balls are ready.

**Two balls per Apricorn.** Double the count before giving, and check space for the
doubled count:

```diff
             getkurtball(VAR_SPECIAL_x8004)
-            hasspaceforitem(VAR_SPECIAL_x8004, VAR_SPECIAL_x8000, VAR_SPECIAL_RESULT)
             copyvar(VAR_SPECIAL_x8005, VAR_SPECIAL_x8000)
+            addvar(VAR_SPECIAL_x8005, VAR_SPECIAL_x8000)
+            hasspaceforitem(VAR_SPECIAL_x8004, VAR_SPECIAL_x8005, VAR_SPECIAL_RESULT)
             callstd(std_give_item_verbose)
```

`addvar` takes a number or a variable (`ScrCmd_AddVar`, `src/scrcmd_c.c:549`). The phone
message still shows `kurtQuantity`, the number of Apricorns
(`phone_scripts_kurt.c:45`); multiply there too if you want it to match.

**Don't lose balls on a full bag.** Check the result before giving:

```diff
             hasspaceforitem(VAR_SPECIAL_x8004, VAR_SPECIAL_x8000, VAR_SPECIAL_RESULT)
+            if (var(VAR_SPECIAL_RESULT) == 0) {
+                npcmsg("Kurt: Your Bag is full!\n"
+                       "Come back when it’s lighter.")
+                goto(_021F)
+            }
             copyvar(VAR_SPECIAL_x8005, VAR_SPECIAL_x8000)
```

Kurt's "I just finished your Poké Ball. Here!" line (lines 113-114) still prints first;
move it below the check if you want. The order stays saved, so you can come back.

**A different ball from a colour.** Edit `sApricornBallItems` (`src/apricorn_box.c:33`),
in box-index order (Red first). Any item id works, e.g. `ITEM_ULTRA_BALL` for Black. The
script and the phone both read this table.

### Change a ball's effect

All Apricorn balls are in `BattleSystem_CalculateBallShakes`
(`src/battle/battle_command.c:7150`); see [§5](#5-apricorn-balls-in-battle). Examples:

**Heavy Ball, check the weight as the comment says.** Line 7260 tests `catchRate < 1024`.
`catchRate` is the base catch rate (at most 255 here), so the test is always true and
every Pokémon under 204.8 kg gets −20. The comment says weight was meant:

```diff
-            } else if (catchRate < 1024) {
+            } else if (weight < 1024) { // under 102.4 kg
                 catchRate -= 20;
             }
```

With this, Pokémon from 102.4 kg to 204.7 kg get no change instead of −20.

**Moon Ball, more species.** Add to the list in `asm/overlay_12_battle_command.s:130` and
raise the size in the `extern` at `battle_command.c:7148`, which `NELEMS` uses (line 7273):

```diff
--- a/asm/overlay_12_battle_command.s
 	.short SPECIES_DELCATTY
+	.short SPECIES_LUNATONE
--- a/src/battle/battle_command.c
-extern u16 sMoonBallPokemon[14];
+extern u16 sMoonBallPokemon[15];
```

The list is followed by `sPickupTable1` in the same section; adding entries moves it,
which is fine since it is referenced by name.

**Past the 255 cap.** Apricorn balls multiply `catchRate`, which is then capped at 255
(lines 7290-7294), so for Pokémon whose catch rate is already high they help little.
Setting `ballMultiplier` instead has no cap. For example a stronger Lure Ball:

```diff
         case ITEM_LURE_BALL:
             if (BattleSystem_IsFishing(bsys)) {
-                catchRate *= 3;
+                ballMultiplier = 50; // x5, uncapped
             }
             break;
```

**Friend Ball friendship.** Change `FRIENDSHIP_TIER_HI_MIN` (200,
`include/constants/pokemon.h:402`) at `battle_command.c:7338` to the value you want, e.g.
`255`. Don't change the constant itself: other code uses it.

## 5. Apricorn balls in battle

`BattleSystem_CalculateBallShakes` (`src/battle/battle_command.c:7150`). `catchRate`
starts as the target's base catch rate (line 7163) and `ballMultiplier` as 10 (×1,
line 7166). Every ball after `ITEM_SAFARI_BALL` goes through the `switch` at line 7171.
The Apricorn balls change `catchRate` and leave the multiplier at ×1. After the switch,
`catchRate` is clamped to 255, and to 1 if negative (lines 7290-7294).

| Ball | Condition | Effect | Lines |
|---|---|---|---|
| Fast Ball | target's **base Speed** ≥ 100 | catch rate ×4 | 7226-7232 |
| Level Ball | compares `battlerIdAttacker`'s level (yours) with the target's | yours ≤ theirs: ×1; yours/2 ≤ theirs: ×2; yours/4 ≤ theirs: ×4; else ×8 (integer halves) | 7233-7245 |
| Lure Ball | `BattleSystem_IsFishing` (a battle started by fishing, `src/battle/battle_system.c:251`) | ×3 | 7246-7250 |
| Heavy Ball | Pokédex weight (kg × 10, from the zukan data, `GetMonWeight` line 7344) | ≥ 409.6 kg +40; ≥ 307.2 kg +30; ≥ 204.8 kg +20; otherwise −20 | 7251-7264 |
| Love Ball | your battler and the target are the **same species** and their genders **differ** | ×8 | 7265-7270 |
| Moon Ball | target species in `sMoonBallPokemon` | ×4 | 7271-7280 |
| Friend Ball | none | ×1; on a successful catch, friendship set to 200 | 7284-7288, 7337-7340 |

**Moon Ball list** (`asm/overlay_12_battle_command.s:131`-`144`): Nidoran♀, Nidorina,
Nidoqueen, Nidoran♂, Nidorino, Nidoking, Cleffa, Clefairy, Clefable, Igglybuff,
Jigglypuff, Wigglytuff, Skitty, Delcatty. These are the Moon Stone families, and the
check compares species directly, so it works as described. There is no Moon Ball bug in
this code.

**Love Ball** compares species and `gender`. It needs an opposite-gender pair of the same
species. A genderless pair has the same gender value, so it gets nothing. Nidoran♀ and
Nidoran♂ are different species, so they get nothing either. There is no Love Ball bug in
this code.

**Heavy Ball** has the odd condition described in [§4](#change-a-balls-effect).
Because of the −20, a Pokémon with a base catch rate of 20 ends at exactly 0, which the
clamp leaves at 0 (it only fixes values below 0). `modifiedCatchRate` can then be 0, and
line 7320 divides by it. At full HP, line 7306 works out to about `catchRate / 3`, so a
catch rate of 1 or 2 (which the Heavy Ball's −20 and clamp can produce) also rounds
to 0. What the DS division routine does with a 0 divisor was not
checked.

**Friend Ball** writes friendship to the target's party slot
(`BattleSystem_GetPartyMon(bsys, ctx->battlerIdTarget, 0)`) only when all shakes pass;
a failed throw changes nothing.

The ball the Pokémon is caught in is saved as a ball id: items `ITEM_FAST_BALL` ...
`ITEM_SPORT_BALL` map to `BALL_FAST` ... (`src/item.c:454`, constants in
`include/constants/balls.h:25`).

## 6. Quick changes

| To | Change |
|---|---|
| a tree's colour | `sTreeApricorns`, `src/apricorn_tree_sys.c:8` |
| Apricorns per shake | the `1` in `GiveApricornFromTree`, `scr_seq_0150.s:31` |
| no regrowth / every N days | `src/field_time_events.c:87`; [§4](#change-regrowth) |
| box limit (≤ 255) | the `99`s in `src/apricorn_box.c:101`, `src/scrcmd_apricorn.c:32`, `src/overlay_03/shop_menu.c:883`; the box screen may assume 2 digits (not checked) |
| which ball each colour makes | `sApricornBallItems`, `src/apricorn_box.c:33` |
| Kurt's wait | `setflag(FLAG_DAILY_KURT_MAKING_BALLS)`, `Azalea_KurtHouse/scripts.pory:215` |
| balls per Apricorn | `copyvar`/`addvar` at `scripts.pory:117` |
| a ball's catch bonus | `src/battle/battle_command.c:7226`-`7288` |
| Moon Ball species | `asm/overlay_12_battle_command.s:130` + size at `battle_command.c:7148` |

## Not verified

- Nothing in this guide was built or tried in game. Every diff and recipe in §4 is
  untested: the new tree, the every-N-days regrowth, more Apricorns per shake, Kurt's
  instant/double/full-bag changes, the ball-table change, and all ball-effect changes.
- What happens when Kurt hands over balls the Bag can't hold (lost, partly added, or
  something else). Only the scripts were read, not `GiveItem`/`Bag_AddItem`.
- Whether a new `SPRITE_BONGURI` object on a map that never had a tree loads and draws
  correctly; the existing trees were the only model. How a sprite-table row
  (`asm/overlay_01_sprite_data.s:1226`) picks its draw callbacks was not traced.
- Which battler `battlerIdAttacker` is when a ball is thrown, especially in double
  battles. The Level Ball and Love Ball read it.
- The division by a zero `modifiedCatchRate` (§5) and whether it can happen in
  practice.
- What `msg_0643_00006` (the phone greeting after 10 orders) leads to in game; only the
  greeting switch was read.
- The Apricorn Box screens (quantity panel, digits shown) beyond the Kurt selection and
  quantity code cited above, and the Aprijuice mixing details.
- The tree map names come from the `map.json` files; the table in
  `apricorn_tree_sys.c` calls index 1 "Route 2 North" while the map is `Route2_East`.
- [pokeathlon.md](pokeathlon.md) is linked but was being written separately at the
  time.
