<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Player movement

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers how the player moves on the map: walking, running and the Running
Shoes, surfing, the Bicycle and Cycling Road, the tiles that change movement (ledges,
one-way edges, stairs and ladders, ice, spin tiles), and the field moves (HMs): what
each one checks and where. It ends with recipes: no running on chosen maps, Running
Shoes from the start, faster surfing, bike rule changes, and using HMs without a
Pokémon that knows the move.

NPC movement (movement types, `applymovement` steps) is in
[overworld-sprites.md](overworld-sprites.md). Which badge each HM needs is in
[gyms.md](gyms.md#what-badges-do). How running and the bike change the encounter rate is
in [encounter-mechanics.md](encounter-mechanics.md#2-the-step-encounter-roll).

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `MovePlayerAvatarUsingKeypadInput`, `PlayerNotOnBikeMoving` | `PlayerAvatar_MoveControl` → `PlayerAvatar_FootStep` (§1) |
| `FLAG_SYS_B_DASH` | `PlayerSaveData.hasRunningShoes`, set by `giverunningshoes` (§2) |
| `MAP_ALLOW_RUNNING` / `allow_running` | `allow_running` in `map.json`, which nothing reads (§2) |
| Mach and Acro Bike, `bike.c` | one Bicycle, `PlayerAvatar_MoveOnBike` (§4) |
| `MB_JUMP_*`, `GetLedgeJumpDirection` | `TILE_BEHAVIOR_JUMP_*`, `MapObject_IsLedgeInDirection` (§5) |
| `MB_*_EDGE` / impassable sides | `TILE_BEHAVIOR_48`-`55`, `73`, `74` (§5) |
| `EventScript_UseCut` and `PartyHasMonWithSurf` | `std_field_*` in `scr_seq_0146.s`, plus two checks in C (§6) |

The files:

| File | What |
|---|---|
| [src/player_avatar_movement.c](../../src/player_avatar_movement.c) | every step: input, collision, walk/run/surf/bike speed, ledges, ice, Cycling Road |
| [src/player_avatar.c](../../src/player_avatar.c) | the `PlayerAvatar` struct accessors, `PlayerSaveData` (Running Shoes) |
| [src/field/field_control.c](../../src/field/field_control.c) | the field's main input loop: pressing A on tiles, stairs/ladder/door warps, the Waterfall step |
| [src/field/player_avatar_actions.c](../../src/field/player_avatar_actions.c) | surfing on and off, Strength boulders, Waterfall, Whirlpool, Rock Climb |
| [src/field_move.c](../../src/field_move.c) | field moves from the party menu: the check for each move |
| [files/fielddata/script/scr_seq/scr_seq_0146.s](../../files/fielddata/script/scr_seq/scr_seq_0146.s) | the `std_field_*` and `std_menu_*` HM scripts |
| [src/field_use_item.c](../../src/field_use_item.c) | getting on and off the Bicycle |
| [src/map_object_movement_utilities.c](../../src/map_object_movement_utilities.c), [src/metatile_behavior.c](../../src/metatile_behavior.c) | which tile behaviors block, are water, are ledges |
| [include/constants/metatile_behavior.h](../../include/constants/metatile_behavior.h) | `TILE_BEHAVIOR_*` (numbers in §5) |

## 1. How a step happens

Every frame the field reads the D-pad (`FieldInput_Update`,
[field_control.c:121](../../src/field/field_control.c#L121)) and calls
`PlayerAvatar_MoveControl` ([player_avatar_movement.c:169](../../src/player_avatar_movement.c#L169)).
When the player is ready for a new step, it:

1. Picks one direction. With two held (up + left), it keeps the current one until one of
   the two keys changes (`PlayerAvatar_ChooseInputDirection`, [:1134](../../src/player_avatar_movement.c#L1134)).
2. Runs forced movement first: ice, and the Cycling Road slope (§4, §5).
3. Otherwise moves by state: on foot, surfing and in the Rocket disguise share
   `PlayerAvatar_MoveOnFoot`; the bike has `PlayerAvatar_MoveOnBike`.
4. On foot, a direction the player isn't facing is a **turn** in place first (`FOOT_STEP_TURN`).
   A held direction the player already faces is a **step**.
5. A step checks the tile ahead (`PlayerAvatar_CheckCollision`, [:927](../../src/player_avatar_movement.c#L927)) and
   gives the player's map object one movement command: a walk, a run, a ledge jump or a
   bump in place.

`PlayerAvatar_CheckCollision` returns bits:

| Bit | Name | Set when the tile ahead... |
|---|---|---|
| `0x01` | `PLAYER_COLLISION_BLOCKED` | has collision, is out of range or too high, blocks by behavior (§5), or the bike can't go there |
| `0x02` | `PLAYER_COLLISION_LINK_OCCUPIED` | has another player on it (Union Room, link) |
| `0x04` | `PLAYER_COLLISION_LEDGE` | is a ledge you jump in this direction |
| `0x08` | `PLAYER_COLLISION_WARP` | is a door or warp: the bump plays no sound |
| `0x20` | `PLAYER_COLLISION_WATER` | is water |

The speeds, in frames per tile (a tile is `0x10000`):

| How | Command | Frames |
|---|---|---|
| walking | `WalkNormal*` (12-15) | 8 |
| running | `Run*` (88-91) | 4 |
| surfing | `WalkFast*` (16-19) | 4 |
| bike, speed 0, 1, 2, 3 | 76, 16, 80, 20 | 6, 4, 3, 2 |
| sliding on ice, speed 0, 1, 2-3 | 16, 80, 20 | 4, 3, 2 |
| ledge jump | `JumpFar*` (56-59) | 16, for 2 tiles |

The command numbers are the ones in [overworld-sprites.md](overworld-sprites.md#3-movement-actions);
the code writes them as hex (`0x58` = 88, `0x38` = 56, `0x1C` = 28 the bump).

Each step that moves (not a bump or a turn) counts `GAME_STAT_STEPS_WALKED`, and on the
bike `GAME_STAT_STEPS_BIKED` too (`PlayerAvatar_CountStep`, [:1301](../../src/player_avatar_movement.c#L1301)).

## 2. Running and the Running Shoes

The whole rule is in `PlayerAvatar_FootStep` ([:695](../../src/player_avatar_movement.c#L695)):

```c
if (PlayerSaveData_CheckRunningShoes(PlayerAvatar_GetPlayerSaveData(avatar)) == TRUE && IsRunButtonHeld(avatar, heldKeys) == TRUE) {
    kind = 0x58; // Run
}
```

- **The shoes** are `hasRunningShoes` in `PlayerSaveData` (`include/player_avatar.h`),
  part of the saved local field data. `giverunningshoes` sets it; the Guide Gent in
  Cherrygrove runs it (`data/maps/Cherrygrove/scripts.pory`). `checkrunningshoes(VAR)`
  reads it.
- **The button** is B (`IsRunButtonHeld`, [:1186](../../src/player_avatar_movement.c#L1186)).
- **The touch-screen shoe button** toggles `runningShoesLock`, also saved. While it is
  on, `FieldInput_Update` ([field_control.c:124](../../src/field/field_control.c#L124)) adds B to the held keys
  every frame: that is HGSS's own auto-run. The button is drawn only once you have the
  shoes, and hidden on the bike (`TouchscreenMenu_HandleRunningShoesButton`,
  [touchscreen_menu.c:453](../../src/field/touchscreen_menu.c#L453); the Dowsing Machine screen has a copy). An options-menu
  AUTO-RUN is worked through in [options-menu.md](options-menu.md#3-worked-example-auto-run).
- **Where:** only `PlayerAvatar_FootStep`'s on-foot branch runs, so you run when walking
  or in the Rocket disguise. Surfing (§3) and the bike (§4) ignore B.
- **Indoors:** nothing checks the map. You can run in every building, cave and gym.
  The map header has a bit for it, `runningAllowed_Unused` (`allow_running` in
  `map.json`), but no code reads it. Retail sets it to `false` on 34 maps (the Safari Zone
  areas, the Union Room, the Wi-Fi battle rooms, the Underground and unused maps), and you
  can still run in all of them. The recipe in §7 makes the bit work.

What running changes besides speed: the encounter rate (running counts like cycling,
[encounter-mechanics.md](encounter-mechanics.md#2-the-step-encounter-roll)), and on a
plain tile the footstep sound (`PlayerAvatar_PlayFootstepSound`, [:275](../../src/player_avatar_movement.c#L275)). Union Room and
link movement use B the same way (`CommPlayerManager_UpdateLocalMoveSpeed`,
`src/comm_player_sync.c`).

## 3. Surfing

Getting on is a field move (§6). On the water, the step is `PlayerAvatar_FootStep`'s
surfing branch ([:702](../../src/player_avatar_movement.c#L702)): one speed (`WalkFast`, 4 frames), no
running, no ledges. A step toward land is blocked, and that bump starts
`Field_PlayerAvatar_TryStopSurfing` ([player_avatar_actions.c:693](../../src/field/player_avatar_actions.c#L693)): if the tile
ahead is open land, the player jumps off. That is the only way off besides a warp, and
a warp also clears surfing (`FieldSystem_ResetStateOnWarp`,
[field_warp_state.c:97](../../src/field_warp_state.c#L97)).

What counts as water is `MetatileBehavior_IsSurfableWater`: behaviors flagged
`TILE_BEHAVIOR_FLAG_SURFABLE` in `sMetatileBehaviorFlags`
([metatile_behavior.c](../../src/metatile_behavior.c)), such as `0x10` river and `0x15` sea.
Bridges over water (`0x73`) count as water unless the player is on the bridge level.

## 4. The Bicycle

### Getting on and off

`ItemCheckUseFunc_Bicycle` ([field_use_item.c:326](../../src/field_use_item.c#L326)) decides, for the bag and the
registered (Y) button alike:

| Refused when | Message |
|---|---|
| someone walks with you (escort) | `ITEMUSEERROR_NOFOLLOWER` |
| in the Rocket disguise | "not now" |
| the bike state is locked (Cycling Road) | "can't get off" |
| standing on very tall grass (`0x03`) or mud (`0xA4`) | Oak's words |
| the map has `"allow_cycling": false` | Oak's words |
| surfing | Oak's words |

`Task_MountOrDismountBicycle` ([:268](../../src/field_use_item.c#L268)) then switches the sprite and the music
(`SEQ_GS_BICYCLE`). Retail has `allow_cycling` false on 370 of the 540 maps: buildings,
caves, and some routes. A warp into such a map takes you off the bike
(`FieldSystem_ResetStateOnWarp`, [field_warp_state.c:121](../../src/field_warp_state.c#L121)). Walking across a map
border does not: the rule is read only on warps and when you get on.

### Riding

`PlayerAvatar_BikeRide` ([player_avatar_movement.c:842](../../src/player_avatar_movement.c#L842)):

- Speed goes up by one after each step, from 0 to 3 (6, 4, 3, then 2 frames a tile).
  A turn, a bump or stopping sets it back to 0.
- Let go at speed 2 or 3 and the bike rolls on, slowing (`PlayerAvatar_BikeCoast`).
- Ledges are jumped like on foot.
- The bike can't enter water, snow (`0xA8`), very tall grass or mud
  (`PlayerAvatar_IsBikeBlockedInDirection`, [:1078](../../src/player_avatar_movement.c#L1078)).
- There are no gears and no Acro tricks; `field_bgm.c` still tests the cycling state
  twice in one line, maybe left over from two bikes.

### Cycling Road

The gatehouse scripts (`Route16_Gatehouse`, `Route18_Gatehouse`) run
`setbikestatelock(1)` when you enter on a bike, and Routes 16-18 run it again on load.
The lock (`AVATAR_FLAG_LOCK_BIKE_STATE`) does two things:

- you can't get off the bike (the "can't get off" message above);
- standing on a bridge behavior (`0x71`-`0x73`) on the bridge level with no direction held,
  you roll south at top speed (`ForcedMovement_CyclingRoadSlope`, [:503](../../src/player_avatar_movement.c#L503), and
  `PlayerAvatar_IsOnCyclingRoadSlope`, [:1310](../../src/player_avatar_movement.c#L1310)).

The exit trigger runs `setbikestatelock(0)`. Without the bike, the gatehouse trigger
turns you back.

### Script commands

| Command | Does |
|---|---|
| `playeronbikecheck(VAR)` | VAR = 1 on the bike |
| `playeronbikeset(1)` / `(0)` | puts the player on or off the bike, with the music |
| `setbikestatelock(1)` / `(0)` | the Cycling Road lock |
| `getplayerstate(VAR)` | `PLAYER_STATE_*`: 0 walking, 1 cycling, 2 surfing, 3 Rocket disguise |

## 5. Tiles that change movement

Tile behaviors are painted in `permissions.txt` (hex, `[behavior]` grid) or with the map
editor: [maps-and-warps.md](maps-and-warps.md#terrain-datalanddata). The model has to
look right too: painting a ledge doesn't draw one ([terrain.md](terrain.md)).

| Hex | Behavior | Effect |
|---|---|---|
| `38` `39` `3A` `3B` | `JUMP_EAST`, `_WEST`, `_NORTH`, `_SOUTH` | ledge: walking that way jumps over it |
| `30`-`37`, `49`, `4A` | `TILE_BEHAVIOR_48`-`55`, `73`, `74` | one-way edges (below) |
| `3C` `3D` | `LADDER_NORTH`, `LADDER_SOUTH` | a ladder warp; also blocks that side |
| `5E` `5F` | `WARP_STAIRS_EAST`, `_WEST` | stairs to another map |
| `6A` `6B` | `ESCALATOR_FLIP_FACE`, `ESCALATOR` | escalator warps |
| `20` | `ICE` | slide until blocked |
| `40`-`43`, `4D` | `SLIDE_EAST`, `_WEST`, `_NORTH`, `_SOUTH`, `STOP_SLIDING` | spin tiles (Viridian Gym, Rocket Hideout) |
| `4B` `4C` | `ROCK_CLIMB_NORTH_SOUTH`, `_EAST_WEST` | Rock Climb walls (§6) |
| `03`, `A4`, `A8` | very tall grass, mud, snow | no bike (§4) |

### Ledges

`MapObject_IsLedgeInDirection` ([:982](../../src/player_avatar_movement.c#L982)) looks at the tile ahead: a
`JUMP_SOUTH` tile jumps you when you walk south into it, and so on. The jump is checked
before collision, so in retail every ledge tile has collision (`#`): it blocks you, and
NPCs, from every other side. The jump (`JumpFar`) carries you 2 tiles, over the ledge to
the tile beyond, and **the landing tile is not checked**: keep it open, or the player
lands inside a wall. `JUMP_NORTH` works but retail never paints it.

To add a ledge: paint the behavior and `#` on the ledge tile, and keep the tile past it
walkable. Surfing ignores ledges.

### One-way edges

These block crossing one side of a tile, in both directions, for the player and NPCs
(`MapObject_IsMoveBlockedByBehavior`, [map_object_movement_utilities.c:122](../../src/map_object_movement_utilities.c#L122), using
`MetatileBehavior_IsBlockedNorth` and the other three):

| Hex | Blocked sides |
|---|---|
| `30` | east |
| `31` | west |
| `32` | north |
| `33` | south |
| `34` | north, east |
| `35` | north, west |
| `36` | south, east |
| `37` | south, west |
| `49` | north, south |
| `4A` | west, east |
| `3C` / `3D` (ladders) | north / south |

### Stairs and ladders

HGSS has no in-map stairs behavior. Steps you walk up inside a map are terrain heights
([terrain.md](terrain.md#heights)). Stairs and ladders between maps are warps, checked in
`FieldSystem_CheckMapTransition` ([field_control.c:490](../../src/field/field_control.c#L490)):

| Tile | You warp when you... | Transition |
|---|---|---|
| `LADDER_NORTH` / `LADDER_SOUTH` | stand on it and press north / south | ladder |
| `WARP_STAIRS_EAST` / `_WEST` | stand on it and press east / west | stairs |
| `DOOR` (`69`) | walk into it | door |
| `WARP_ENTRANCE_*`, `WARP_*` | stand on it and press that way | by map type |

The tile also needs a warp event at that spot
([maps-and-warps.md](maps-and-warps.md#warps-warp_events)). Copy the collision and
behavior of a retail stairs tile: stairs tiles are open (`.`).

### Ice and spin tiles

- **Ice** (`20`, `ForcedMovement_Ice`, [:467](../../src/player_avatar_movement.c#L467)). Once on ice, you
  slide the way you face until something blocks you. Uphill slows the slide, downhill
  speeds it; uphill at speed 0 slides you back. A blocked slide tries to push an ice
  block (`FieldSystem_TryPushIceBlock`). Other forced-movement tiles can be added to
  `sPlayerForcedMovementBehaviors` ([:145](../../src/player_avatar_movement.c#L145)) with a function in
  `sPlayerForcedMovementFuncs`.
- **Spin tiles** (`src/field/spin_slide.c`). Stepping on a `SLIDE_*` tile spins the
  player and moves them that way, tile by tile, over plain tiles too, until a wall or a
  `STOP_SLIDING` tile. Another `SLIDE_*` tile on the way changes direction.

## 6. Field moves (HMs)

A field move is reached three ways, and each has its own checks.

**1. The party menu.** The menu lists only moves the Pokémon knows
([party-menu-and-item-use.md](party-menu-and-item-use.md)). Picking one calls its check in
`sFieldMoveFuncTable` ([field_move.c](../../src/field_move.c)): the badge, then what you face.
`FieldMove_InitCheckData` works out what you face: a tree, rock or boulder object (by
sprite), water, a waterfall, a whirlpool, a Rock Climb wall, a headbutt tree, a dark map.
If it passes, the `std_menu_*` script runs with that Pokémon's slot in `VAR_SPECIAL_x8000`.

**2. Pressing A at an obstacle.** This is the usual way, and it runs a `std_field_*` script
from [scr_seq_0146.s](../../files/fielddata/script/scr_seq/scr_seq_0146.s):

| Move | Obstacle | How it starts | Script | Checks |
|---|---|---|---|---|
| Cut | `SPRITE_TREE` object | its `"script": "std_field_cut"` | `scr_seq_0146_000` | move, Hive |
| Rock Smash | `SPRITE_BREAKROCK` object | `std_field_rock_smash` | `_001` | move, Zephyr |
| Strength | `SPRITE_ROCK` object | `std_field_strength` | `_002` | move, Plain |
| Rock Climb | tile `4B` / `4C`, matching the facing | `GetInteractedMetatileScript` | `_003` | move, Earth, no escort |
| Surf | water ahead, while on land | `GetInteractedMetatileScript` | `_004` | **C**: move and Fog ([field_control.c:610](../../src/field/field_control.c#L610)); script: no escort |
| Waterfall | tile `13` ahead, while surfing | `GetInteractedMetatileScript` | `_005` | move, Rising |
| Whirlpool | tile `11` ahead, while surfing | `GetInteractedMetatileScript` | `_016` | move, Glacier |
| Headbutt | a headbutt tile or tree model | `GetInteractedMetatileScript` / `GetInteractedHeadbuttTreeScript` | `_014` | move |
| Flash | (none: dark caves have no A prompt) | | `_006` is an empty `End` | |

`GetInteractedMetatileScript` is [field_control.c:577](../../src/field/field_control.c#L577). The scripts find the
Pokémon with `GetPartySlotWithMove VAR_SPECIAL_RESULT, MOVE_X`: the first non-egg that
knows it, or 6 if none. They show the "a Pokémon may be able to..." text when that is 6
or the badge is missing, else ask yes/no. The slot goes to `PlayFieldMoveCutIn`, or to the
`Surf`, `Waterfall`, `Whirlpool` and `RockClimb` commands, which show that Pokémon.
Cut and Rock Smash hide the object; tree and rock objects use `FLAG_MAPTEMP_*` flags,
so they come back when the map loads again.

**3. While moving.** Two effects are checked on every step, not by a script
(`Field_PlayerAvatar_TryFieldMoveInDirection`, [player_avatar_actions.c:449](../../src/field/player_avatar_actions.c#L449)):

- **Strength**: after you use it, `StrengthFlagAction` sets a system flag until the next
  warp. While it is set, walking into a `SPRITE_ROCK` pushes it.
- **Going down a waterfall**: surfing south into tile `13` rides down it, if any party
  Pokémon knows Waterfall. This is checked in C ([field_control.c:232](../../src/field/field_control.c#L232)), with
  no badge check. Going up is the A prompt above.

## 7. Recipes

All recipes here change C or scripts; rebuild with `make release`.

### No running on chosen maps

Make `allow_running` work. In [src/map_header.c](../../src/map_header.c), after
`MapHeader_IsBikeAllowed`:

```c
BOOL MapHeader_IsRunningAllowed(u32 mapId) {
    mapId = MapNumberBoundsCheck(mapId);
    return sMapHeaders[mapId].runningAllowed_Unused;
}
```

Declare it in `include/map_header.h`. In `src/player_avatar_movement.c`, add
`#include "map_header.h"` and change the run check in `PlayerAvatar_FootStep`:

```c
            FieldSystem *fieldSystem = MapObject_GetFieldSystem(mapObject);
            if (PlayerSaveData_CheckRunningShoes(PlayerAvatar_GetPlayerSaveData(avatar)) == TRUE && IsRunButtonHeld(avatar, heldKeys) == TRUE
                && MapHeader_IsRunningAllowed(fieldSystem->location->mapId)) {
                kind = 0x58;
            }
```

Then set `"allow_running": false` in the `map.json` of each map where running should
stop, and back to `true` on the retail maps you still want it on: the Safari Zone areas
are among the 34 that retail sets to `false` (§2). Find them with
`grep -l '"allow_running": false' data/maps/*/map.json`.

### Running Shoes from the start

Add `GiveRunningShoes` to the `init` script, `scr_seq_0149.s`
([new-game.md](new-game.md#the-init-script-flags-vars-items-pokémon)):

```asm
scr_seq_0149_000:
	GiveRunningShoes
	SetFlag FLAG_HIDE_ELMS_LAB_OFFICER
	...
```

The Guide Gent still gives them in Cherrygrove, which does nothing more. Edit his script if
the message should change.

### Faster surfing with B

In `PlayerAvatar_FootStep`'s surfing branch:

```c
    } else if (collision == 0 || collision == PLAYER_COLLISION_WATER) {
        int kind = MOVEMENT_RUN_UP;
        if (IsRunButtonHeld(avatar, heldKeys) == TRUE) {
            kind = 0x14; // WalkFaster: 2 frames a tile, the bike's top speed
        }
        movement = PlayerAvatar_AdjustMovementDummy(mapObject, (u8)MapObject_GetCurrentMetatileBehavior(mapObject), kind);
```

With the touch-screen shoe button on, B always counts as held, so surfing is always
fast. The encounter rate doesn't change: `PlayerAvatar_IsRunning` only matches the `Run`
commands.

### Bike rules

- **Allow the bike on a map**: `"allow_cycling": true` in its `map.json`. Do this for
  every map you can walk to across a border, or the player keeps the bike there (§4).
- **Bike through tall grass, mud or snow**: remove those tests from
  `PlayerAvatar_IsBikeBlockedInDirection` ([:1078](../../src/player_avatar_movement.c#L1078)), and the
  very-tall-grass/mud test from `ItemCheckUseFunc_Bicycle`.
- **Speeds**: `PlayerAvatar_GetBikeMovement` ([:735](../../src/player_avatar_movement.c#L735)) maps speed 0-3 to a command; the
  ceiling `3` is in `PlayerAvatar_AccelerateBike`. `MapObject_SetHeldMovement` asserts the
  command is below 113, so use an existing command or add one
  ([overworld-sprites.md](overworld-sprites.md#adding-one)).

### HMs without a Pokémon that knows the move

The goal: with the badge, Cut, Rock Smash, Strength, Rock Climb, Surf, Waterfall,
Whirlpool and Headbutt work from the A prompt even if nobody knows the move. The party's
lead Pokémon shows in the cut-in.

**1. The scripts.** In `scr_seq_0146.s`, after each of the 14 lines
`GetPartySlotWithMove VAR_SPECIAL_RESULT, MOVE_X`, add `Call _HMUserOrLead`:

```asm
scr_seq_0146_000:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	FacePlayer
	GetPartySlotWithMove VAR_SPECIAL_RESULT, MOVE_CUT
	Call _HMUserOrLead
	Compare VAR_SPECIAL_RESULT, 6
	GoToIfEq _009E
	...
```

and add the subroutine at the end of the file, before the last `.balign 4, 0`:

```asm
_HMUserOrLead:
	Compare VAR_SPECIAL_RESULT, 6
	GoToIfNe _HMUserOrLeadEnd
	GetPartyLeadAlive VAR_SPECIAL_RESULT
_HMUserOrLeadEnd:
	Return
```

`GetPartyLeadAlive` gives the first Pokémon that isn't an egg and isn't fainted. The slot
is never 6 afterwards, so the "a Pokémon may be able to..." branch now only runs without
the badge. Headbutt has no badge, so it always works. The `std_menu_*` scripts don't
change: the party menu still shows only known moves.

**2. Surf from the shore.** The A prompt only appears if a party Pokémon knows Surf. At
[field_control.c:610](../../src/field/field_control.c#L610), drop that part:

```c
        if (Field_PlayerCanSurfOnTile(fieldSystem->playerAvatar, standingTile, metatileBehavior) && PlayerProfile_TestBadgeFlag(profile, BADGE_FOG)) {
```

**3. Going down waterfalls.** At [field_control.c:232](../../src/field/field_control.c#L232), test the badge instead
of the move:

```c
    if (PlayerProfile_TestBadgeFlag(Save_PlayerData_GetProfile(fieldSystem->saveData), BADGE_RISING)) {
        playerEvent |= PLAYER_EVENT_USED_WATERFALL;
    }
```

**Variant: only with an item.** To need a key item (one you add,
[items.md](items.md)) as well as the badge, leave the slot at 6 when the item is
missing. The scripts' own `Compare VAR_SPECIAL_RESULT, 6` check then shows the usual
text:

```asm
_HMUserOrLead:
	Compare VAR_SPECIAL_RESULT, 6
	GoToIfNe _HMUserOrLeadEnd
	HasItem ITEM_X, 1, VAR_TEMP_x4003
	Compare VAR_TEMP_x4003, 0
	GoToIfEq _HMUserOrLeadEnd
	GetPartyLeadAlive VAR_SPECIAL_RESULT
_HMUserOrLeadEnd:
	Return
```

and, for Surf at [field_control.c:610](../../src/field/field_control.c#L610):

```c
        if (Field_PlayerCanSurfOnTile(fieldSystem->playerAvatar, standingTile, metatileBehavior) && PlayerProfile_TestBadgeFlag(profile, BADGE_FOG)
            && (GetIdxOfFirstPartyMonWithMove(SaveArray_Party_Get(fieldSystem->saveData), MOVE_SURF) != 0xFF || Bag_HasItem(Save_Bag_Get(fieldSystem->saveData), ITEM_X, 1, HEAP_ID_FIELD1))) {
```

Do the same in step 3 for waterfalls. For a different item per move, put the
`HasItem` test in each script instead of the shared subroutine.

**Flash** has no A prompt to change. Without a Pokémon that knows it, a dark cave
stays dark. To light caves another way, run `FlashAction 1` then `FlashEffect` from a
script, as the Flash script does (`_0909` in `scr_seq_0146.s`;
[weather.md](weather.md#5-changing-weather-from-a-script)), or remove the map's dark
weather.

## 8. Testing the recipes

These recipes, applied together, compile and link into a HeartGold ROM: no running on
chosen maps, Running Shoes from the start, faster surfing, and both versions of the HM
recipe (with and without the item). The bike rule changes were not built. Nothing here has
been played: no emulator was available when this was written. Check in a game:

| Recipe | Check |
|---|---|
| no running | B on a map set to `false` walks; on a `true` map it runs; the touch-screen shoe button does nothing there |
| shoes from the start | the shoe button shows in your room. The Guide Gent still talks normally |
| faster surfing | B on water is twice as fast. Getting off still works at speed |
| HMs | with the badge and nobody knowing the move: each obstacle asks and works, and the cut-in shows the lead Pokémon. Without the badge: the old text. Surf from the shore. Ride down a waterfall. With the item variant, the same without the item shows the old text |

## Where to look

| To change | Look at |
|---|---|
| walk, run or surf speed | `PlayerAvatar_FootStep`, [player_avatar_movement.c:669](../../src/player_avatar_movement.c#L669) |
| the run button or auto-run | `IsRunButtonHeld`, `FieldInput_Update` |
| bike speed and what the bike can't enter | `PlayerAvatar_GetBikeMovement`, `PlayerAvatar_IsBikeBlockedInDirection` |
| when the bike can be used | `ItemCheckUseFunc_Bicycle`, `allow_cycling` |
| ledges | `MapObject_IsLedgeInDirection`, behaviors `38`-`3B` |
| tiles that block a side | `MetatileBehavior_IsBlocked*`, [metatile_behavior.c](../../src/metatile_behavior.c) |
| stairs, ladders, door warps | `FieldSystem_CheckMapTransition`, [field_control.c:490](../../src/field/field_control.c#L490) |
| ice, sliding | `sPlayerForcedMovementBehaviors`, `src/field/spin_slide.c` |
| an HM's A prompt | `scr_seq_0146.s`, `GetInteractedMetatileScript` |
| an HM from the party menu | `sFieldMoveFuncTable`, [field_move.c](../../src/field_move.c) |
| which badge an HM needs | [gyms.md](gyms.md#what-badges-do) |
