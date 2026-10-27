<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Following Pokémon

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The first healthy Pokémon in the party walks behind the player. It is one map object
(id `obj_partner_poke`, 253, `include/constants/scrcmd.h:41`). Its model comes from a
per-species table, the map header decides whether it may come out, and talking to it
runs a small rule engine that picks one of 1,023 "interaction scripts" from binary
tables. pokeemerald has no following Pokémon, so there is no counterpart to compare
with.

Giving a new species a follower model (`sModelIndexLUT`, `tp_param.csv`, a texture of
its own) is in [adding-a-species.md](adding-a-species.md#10-following-pokémon). This
guide covers everything else.

## Where things are

| What | File |
|---|---|
| create / change / permission checks, mood helpers | `src/follow_mon.c` (from line 1508) |
| species → model tables | `sModelIndexLUT`, `sFormMaxLUT`, `sFemaleFlagLUT`, `src/follow_mon.c:19`, `:516`, `:1012` |
| per-model parameters (large, hover...) | `files/fielddata/tsurepoke/tp_param.csv` (columns in `tp_param.csv.txt`) |
| per-map permission | `follow_mode` in each `data/maps/<Map>/map.json` (`MapHeader.followMode`, `include/map_header.h:33`) |
| re-create on map load, hop into ball, recall, flash | `src/field/field_follow_mon.c` |
| how it walks after the player | `src/map_object_follow.c:49-420` (movement types 48, 55, 56) |
| Poké Ball effects | `src/field/field_follow_mon_ball.c`, kinds in `include/field_follow_mon_ball.h` |
| talking to it: rule engine, scripts, gifts | `src/field/follow_mon_interaction.c` |
| rule / script structs | `FollowMonRule`, `FollowMonInteractionStep`, `FollowMonMovementStep`, `include/field_system.h:126-175` |
| interaction rules (binary) | `files/a/2/2/0`: member 0 = 70 global rules, member *mapsec* + 1 = 30 rules per map section |
| interaction scripts (binary) | `files/a/2/2/1`: 1,023 members of 52 bytes |
| interaction movements (binary) | `files/a/2/2/2`: 108 members of 80 bytes |
| species attribute byte | `files/a/2/3/1`, member 0, one byte per species |
| what it says | `files/msgdata/msg/msg_0265.json` (759 messages); gift lines in `msg_0040.json` |
| the "talk to it" script | `std_following_mon` (9700) → `files/fielddata/script/scr_seq/scr_seq_0163.s` (`src/script_manager.c:48`) |
| script commands | `src/scrcmd_c.c:4383-4935`, `:5242`, `:5397` ([§6](#6-script-commands)) |
| what is saved | `SaveFollowMon`, `include/save_follow_mon.h`; `src/save_follow_mon.c` |
| mood value | `mood` (s8) in the Pokémon's data, `include/pokemon_types_def.h:142` |

## 1. When it follows

### Which Pokémon

The follower is always the first party member that is neither fainted nor an egg
(`GetFirstAliveMonInParty_CrashIfNone`, `src/script_pokemon_util.c:112`, used by
`FollowMon_ChangeMon`, `src/follow_mon.c:1570`, and by the draw code that reloads the
sprite, `FollowMonDraw_Resume`, `src/field/map_object_billboard_motion.c:372`). An egg
never follows. If every Pokémon has fainted, `FollowMon_IsActive` returns FALSE
(`src/follow_mon.c:1773`), so nothing that checks it moves or shows the follower.

The sprite is `SPRITE_FOLLOWER_MON_BULBASAUR + sModelIndexLUT[species]`, plus one for a
female with its own model, or plus the form for species with form models
(`FollowMon_GetSpriteID`, `src/follow_mon.c:1642`). A form past `sFormMaxLUT` falls
back to form 0, and a species outside 1-`NATIONAL_DEX_COUNT` shows Bulbasaur.

### The permission check

Everything asks one function, `FollowMon_GetPermissionBySpeciesAndMap(species, mapNo)`
(`src/follow_mon.c:1804`):

1. Diglett and Dugtrio never follow in Bell Tower (`MAP_BELL_TOWER_1F` ... `_10F`,
   `_ROOF`; `FollowMon_DiglettPermissionCheck`, `src/follow_mon.c:1860`).
2. Then the map's `follow_mode`:

| `follow_mode` | Meaning | Maps in retail (`data/maps/*/map.json`) |
|---|---|---|
| `MAP_FOLLOWMODE_ALLOW` (2) | any species | 178: towns, routes, most caves |
| `MAP_FOLLOWMODE_HEIGHT_RESTRICT` (1) | only species whose model is **not** large | 320: every building interior except those below, plus Olivine Lighthouse, Ruins of Alph chambers, Rocket HQ, the Embedded Tower rooms, Celadon Condominiums roof |
| `MAP_FOLLOWMODE_PREVENT` (0) | nobody | 42: Battle Frontier and its buildings, Battle Tower rooms, Global Terminal, Magnet Train platforms, Union Room, Underground, Hall of Fame, Bell Tower roof, Lugia's chamber (Whirl Islands B3F), Trainer House B1F, unused maps |

"Large" is the `too_tall` column of `tp_param.csv` (`FollowMon_GetSizeParamBySpecies`
reads its byte 1, `src/follow_mon.c:1762`). In retail it is set for Steelix (both),
Lugia, Ho-Oh, Wailord, Kyogre, Groudon, Rayquaza, Dialga, Palkia, Regigigas, both
Giratina formes and all 17 Arceus models: the 64×64 sprites. So these stay in their
ball indoors. **There is no other species exclusion.**

The `follow_mode` key is in the header part of `map.json` (line 21 in
`data/maps/Route29/map.json`); the build turns it into `followMode`
([maps-and-warps.md](maps-and-warps.md#map-header-top-of-mapjson)).

### Bike, Surf, script inhibit

When the follower is created while the player is cycling or surfing, it is hidden and
given movement type 56, which copies the player's moves from the player's tile
(`src/follow_mon.c:1541-1548`). Getting on the bike recalls it into its ball and
switches it to type 56; getting off sets "release pending", so it pops out of its ball
on the next step (`Task_MountOrDismountBicycle`, `src/field_use_item.c:268`, lines
275-311). Surfing hides it the same way, and stopping surfing puts it back on type 48
(`Task_StopSurfing`, `src/field/player_avatar_actions.c:741-746`).

A saved **inhibit** bit hides it on creation (`src/follow_mon.c:1553`, `:1613`).
Scripts set it with `setfollowmoninhibitstate(1)` ([§6](#6-script-commands)). It is
cleared on every map entry (`FieldSystem_InitMapOnEnter`, `src/field_warp_tasks.c:272`),
before the follower is created, so in practice it only matters when the game is saved
and reloaded on the same map.

### Created, re-created, removed

| When | What happens | Code |
|---|---|---|
| a warp / map change | all map objects are rebuilt; `FollowMon_InitMapObject` creates the follower next to the player if the permission check passes | `Task_ChangeMap` → `FieldSystem_CreatePlayerAndMapObjects`, `src/field_warp_tasks.c:288` |
| continue from a save | `FollowMon_ChangeMon` reuses the restored object, updates species, form, shiny, gender | `src/field_warp_tasks.c:314` |
| leaving the overworld (menu, battle...) | `recreatePending` is set | `FollowMon_MarkForRecreate`, `src/field/fieldmap.c:308` |
| coming back to the overworld | `FollowMon_RecreateForMap`: if there was no follower, try to create one; if there is one that may not be here, remove it | `src/field/field_follow_mon.c:429`, called at `src/field/fieldmap.c:734` |
| the sprite is drawn again after that | reloads the current lead's sprite; if the lead changed, it faces south | `FollowMonDraw_Resume`, `src/field/map_object_billboard_motion.c:372-405` |

So swapping the lead in the party menu changes the follower when you close the menu.
A new follower starts **hidden until its first step** (`FollowMon_CreateMapObject`
calls `FollowMon_HideUntilStep(..., TRUE)`, `src/follow_mon.c:1913`).

**A naming trap.** `MAPOBJECTFLAG_VISIBLE` set means the object is *hidden*: movement
command 69 (`SetInvisible`, `asm/macros/movement.inc:351`) sets it
(`src/map_object_movement_commands.c:961`). So `FollowMon_SetVisibleFlag(obj, TRUE)`
and `FollowMon_CheckVisibleFlag` mean "hidden", while `FollowMon_IsVisible`
(`src/follow_mon.c:1785`) returns TRUE when it is shown.

## 2. Model parameters: `tp_param.csv`

One row per follower model, in `FOLLOWER_MON_*` order (row = model index, not species).
The first column is only a label.

| Column | Byte | Read by | Effect |
|---|---|---|---|
| `unk0` | 0 | nothing found | 0 in every row |
| `too_tall` | 1 | `FollowMon_GetSizeParamBySpecies` (`src/follow_mon.c:1762`), and as "large" via `FollowMonObject_IsLarge` (`src/field/field_follow_mon.c:221`) | kept out of `HEIGHT_RESTRICT` maps; also: blocks two tiles (`src/map_object_movement_utilities.c:79`), grass effects on the tile behind it (`src/map_object_follow.c:693`), only turns to face you if two tiles are free (`ScrCmd_FollowMonFacePlayer`, `src/scrcmd_c.c:4470`), pulled sideways into the ball (`src/field/field_follow_mon_ball.c:361`), Friendship Room statue size (`src/field/scrcmd_pokemon_misc.c:980`) |
| `unk2_0` | 2, low nibble | `FollowMon_GetShapeParamLow` (`src/field/field_follow_mon.c:212`) | which walk frames make the sprite dip (`FollowMonBillboard_IsBobFrame`, `src/field/map_object_models.c:189`) |
| `hover` | 2, high nibble | `FollowMon_GetShapeParamHigh` (`src/field/field_follow_mon.c:204`) | when set, no extra hop height while it catches up after a ledge (`FollowMon_GetHopHeight`, line 172) |
| `unk3` | 3 | nothing found | 0 in every row |

`FollowMon_SetObjectForm` stores bytes 1 and 2 in the object's parameter 1
(`src/follow_mon.c:1879-1896`), which is where the "large" and nibble readers get them.
**`too_tall` is not only a permission flag**: it is the flag that tells the engine the
sprite is 64×64. Don't clear it on a big model to let it indoors; see
[§8.1](#81-let-a-large-species-follow-indoors).

## 3. Movement

### Walking after the player

The follower uses movement type 48 (`MOVEMENT_TYPE_FOLLOW_PLAYER_48`,
`include/constants/map_object.h:59`; callbacks `sFollowPlayer48MovementCallbacks`,
`asm/map_object_movement_tables.s:451`). It does not path-find. Each time the player
starts a step, the player code queues that step's movement and the tile the player is
leaving (`FollowMon_QueuePlayerStep`, `src/field/field_follow_mon.c:417`, called from
`src/player_avatar_movement.c:586` and `:720`). The follower then walks onto that tile
at the player's speed (`FollowPlayerMovement_StartFollowMonStep`,
`src/map_object_follow.c:343`). Run movements under the alternate ids 0x58-0x5B are
mapped to the plain run movements (`FollowMon_GetMovement`, line 308).

Two other follow types exist:

| Type | Callback | Does | Used |
|---|---|---|---|
| 48 | `FollowPlayerMovement_UpdateFollowMon` | repeats queued player steps | normal walking |
| 55 | `FollowPlayerMovement_Update` (`src/map_object_follow.c:66`) | steps onto the player's previous tile whenever the player's coordinates change | cutscenes where the player is moved by `applymovement` (no queued steps), warp stairs (`src/field_transition_effects.c:341`) |
| 56 | `FollowPlayerMovement_UpdateMirror` (line 74) | copies the player's movement command | while hidden on the player's tile: bike, Surf, "keep it in its ball" scripts |

**Ledges.** When the player's queued movement is a far jump (movements 56-59, the
`JumpFar*` commands, `IsMovement56To59`, `src/map_object_movement_commands.c:317`), the
follower records a pending hop (`src/map_object_follow.c:184`). On its next step it uses
a faster movement and plays it twice to catch up (`FollowPlayerState_Hop`, line 242;
speed from `GetMovementSpeed`, line 656), with an extra height from
`gFollowMonHopHeights` unless `hover` is set.

**First step.** If it is hidden until its first step, that step either opens its Poké
Ball (when "release pending" is set) or simply shows it, and spawns tall-grass effects
under it (`FollowMon_SpawnStepEffects`, `src/map_object_follow.c:157`).

### Doors, stairs, warps

`Task_FieldTransition` (`src/field_transition_effects.c:173`) handles the follower on a
warp:

1. If it is out and will not be allowed on the destination, it is recalled with the
   white-flash ball (kind 1) before the screen fades (lines 186-191).
2. The map being left is saved in `SaveFollowMon.mapNo` (line 204).
3. After arrival, if it was not allowed on the map it left (it was in its ball), it is
   placed on the player and set to come out of its ball on the first step
   (lines 246-251, `FollowMon_GetPermission` reads `mapNo`, `src/follow_mon.c:1797`).

Rising and sinking warps put it on the player, hidden until its first step
(`src/field_transition_tasks.c:207-210`, `:262-265`). Warp panels recall it and release
it again on arrival if allowed (`Task_WarpPanel`, `src/field_warp_tasks.c:888-891`,
`:923-927`).

### Poké Ball effects

`FollowMonBall_Spawn(obj, kind)` (`src/field/field_follow_mon_ball.c:169`):

| Kind | Effect | Used by |
|---|---|---|
| 0 `FOLLOW_MON_BALL_RELEASE` | ball opens, Pokémon appears | first step with release pending (`src/map_object_follow.c:159`) |
| 1 `FOLLOW_MON_BALL_RECALL_WHITE` | Pokémon turns white and shrinks into the ball | `FollowMon_StartRecall` (`src/field/field_follow_mon.c:659`), warps |
| 2 `FOLLOW_MON_BALL_BURST` | burst only | hiding after doing a field move itself (`FollowMon_StartHideForFieldMove`, line 724) |
| 3 `FOLLOW_MON_BALL_RECALL` | shrink without the white palette | `FollowMon_StartHopIntoBall` (line 540), used when the nurse heals (`scr_seq_0003.s:131`) |

### Field moves

If the follower is next to the player and is the one using Surf or Rock Climb, it
does its own animation (jump, cry, burst) instead of the cut-in
(`CallFieldTask_Surf`, `src/field/player_avatar_actions.c:568-580`; Rock Climb at line
810). With the cut-in, it is recalled (`FieldMove_WaitCutIn`,
`src/field/field_move_warp_tasks.c:361`; `src/field/player_avatar_actions.c:647`). Fly
recalls it if another party member flies (`FieldTask_Fly`, `src/field_warp_state.c:183`).

## 4. Talking to it

The follower's script is `std_following_mon` (`src/follow_mon.c:1905`), which is
`scr_seq_0163.s`:

```
PlaySE SEQ_SE_DP_SELECT
LockAll
FollowMonFacePlayer
FollowMonInteract
ReleaseAll
```

Everything after line 15 of that file is unreachable. `FollowMonInteract` starts
`Task_FollowMonInteract` (`src/field/follow_mon_interaction.c:1188`): pick a script,
run it, then handle a yes/no question or a gift.

### 4.1 How a script is picked

`FollowMon_SelectInteraction` (`src/field/follow_mon_interaction.c:323`) loads 100
rules: the current **map section's** 30 rules (member `mapsec + 1` of `files/a/2/2/0`)
into slots 0-29, and the 70 **global** rules (member 0) into slots 30-99. It tries them
in this order:

1. global slots 30-41 (status, HP, extreme mood, water tiles),
2. the map section's 0-29,
3. global slots 42-99 (mood and friendship chit-chat, ending in a catch-all).

The first rule whose `script` is nonzero and whose conditions all hold wins. **Each rule
rolls its own chance** first: it fails when `LCRandom() % 100 >= chance` (line 395), so
`chance` 100 always passes and 0 never does. Global slot 99 is `script 254, chance 100`
with no condition, so something is always picked. The map section comes from the map
header (`MapHeader_GetMapSec`); [town-map-and-fly.md](town-map-and-fly.md) lists the
sections. 129 of the 235 section members have no rules at all.

### 4.2 The conditions

`FollowMon_GetSituation` (line 374) describes the lead and its surroundings, and
`FollowMonRule_Matches` (line 391) compares. A rule field of 0 means "any".

| Rule field | Situation value | Values |
|---|---|---|
| `flag` | `Save_VarsFlags_CheckFlagInArray` | flag must be set (208 retail rules use one, see [unknown-flags-vars.md](unknown-flags-vars.md)) |
| `heldItem` | pocket of the held item | 1 Balls, 2 Medicine, 3 Battle items, 4 Items, 5 Mail, 6 Berries, 7 TMs/HMs, 8 none, **9 any held item** |
| `hp` | HP percent | 1 full, 2 ≥75, 3 ≥50, 4 ≥25, 5 below |
| `status` | status (line 534) | 1 none, 2 burn, 3 freeze, 4 paralysis, 5 poison/toxic, **7 any**. Sleep is 8, which the 3-bit field can't hold, so only "any" catches sleep |
| `nearbyObjects` | objects in the 3×3 around the player, not the player or follower | exact count; 5 = five or more |
| `hiddenItems` | hidden items on the map not yet found | exact count; 4 = four or more |
| `level` | from the level (line 552) | 4 if level ≥ 48, else 6. 5 is never produced. No retail rule uses it |
| `nearbyRock` | rock / breakable rock nearby | **any nonzero value makes the rule fail** (line 444-455); no retail rule uses it |
| `type` | either type | `FOLLOW_MON_TYPE_*`: 1 Normal, 2 Fire, 3 Water, 4 Electric, 5 Grass, 6 Ice, 7 Fighting, 8 Poison, 9 Ground, 10 Flying, 11 Psychic, 12 Bug, 13 Rock, 14 Ghost, 15 Dragon, 16 Dark, 17 Steel (line 172) |
| `weather` | saved weather | 1 sunny, 3 rain, else 0 ([weather.md](weather.md)) |
| `metatileBehavior` | behaviour of the follower's tile | exact `TILE_BEHAVIOR_*` ([terrain.md](terrain.md)) |
| `encounterTile` | follower's tile | 1 can have wild encounters, 2 cannot |
| `mapId` | current map | stored as map id + 1 |
| `timeOfDay` | `Field_GetTimeOfDay` | 1 morning, 2 day, 3 evening, 4 night, 5 late night ([day-night-and-rtc.md](day-night-and-rtc.md)) |
| `mood` | mood | range 1-10 ([§5](#5-mood)) |
| `pokeathlonStat` | best Pokéathlon star stat (ties: power, stamina, jump, skill, speed) | 1 power, 2 stamina, 3 skill, 4 jump, 5 speed |
| `friendship` | friendship | 1 = 255, 2 = 200-254, 3 = 150-199, 4 = 90-149, 5 = 60-89, 6 = 30-59, 7 = 1-29, 8 = 0, 9 = ≥90, 10 = <60 (`FollowMonRule_CheckFriendship`, line 1360) |
| `natureGroup` | `gNatureGroups[nature]` (`asm/field_move_effects_data.s:676`) | 1-6 |
| `speciesAttr` | byte `species - 1` of `files/a/2/3/1` | ≤249 exact; 250 = ≤19, 251 = ≤130, 252 = 140-149, 253 = ≥160, 254 = ≥220 (`FollowMonRule_CheckSpeciesAttr`, line 1509) |
| `shinyLeaf` | Shiny Leaves owned | 1-5: passes while the lead does **not** have that leaf |
| `gender` | gender | 1 male, 2 not male |
| `facing` | follower's facing | 1 east, 2 west, 3 north, 4 south |

What the species attribute values mean was not worked out. Many species have a value
of their own (Bulbasaur 20, Pikachu 23, Chikorita 30), and 130 is shared by many.

### 4.3 Rule format (20 bytes)

`FollowMonRule`, `include/field_system.h:126`. Bitfields start at the low bit.

| Offset | Bits |
|---|---|
| 0 | `hp` |
| 1 | `mood` 0-3, `friendship` 4-7 |
| 2 | `natureGroup` 0-2, `gender` 3-4, `status` 5-7 |
| 3 | `heldItem` 0-4 |
| 4 | `type` 0-4, `pokeathlonStat` 5-7 |
| 5, 6, 7 | `encounterTile`, `speciesAttr`, `shinyLeaf` |
| 8 (u16) | `weather` 0-2, `facing` 13-15 |
| 10 (u16) | `nearbyObjects` 0-2, `timeOfDay` 3-5, **`script` 6-15** |
| 12 (u16) | `mapId` (+1) |
| 14 (u16) | `metatileBehavior` |
| 16 | `level` 1-2, `nearbyRock` 3-4, `hiddenItems` 5-7 |
| 17 | `chance` |
| 18 (u16) | `flag` |

Member 0 is 1,400 bytes (70 rules) and each section member 600 bytes (30 rules). They
are read with `ReadWholeNarcMemberByIdPair` into a fixed `rules[100]` array
(`include/field_system.h:180`), so **a member must not grow**: a longer one overwrites
what follows. The Python helper in [§8.3](#83-add-an-interaction) packs and unpacks
rules; it round-trips all 7,120 retail rules.

### 4.4 Interaction scripts (`files/a/2/2/1`)

Member `script - 1` (`FollowMonInteraction_LoadScript`, line 822), 52 bytes:

| Offset | Field |
|---|---|
| 0-39 | 5 steps of 8 bytes: `movement` (+1, 0 none, 0xFFFF ends), `message` (+1), `sound`, `emote` (+1), `wait` (frames) |
| 40 | `askQuestion` (u32) |
| 44, 46 | `yesScript`, `noScript` (u16, 0 = end) |
| 48 | `friendshipChange` (s8) |
| 49 | `moodChange` (s8) |
| 50 | `accessory` (+1) |
| 51 | `shinyLeaf` (1-5) |

Each step (`FollowMonInteraction_Run`, line 867) plays its movement, shows its emote,
prints its message, then waits. Details:

- **Emote** 1-14 shows emote bubble `emote - 1` above the follower (14 animations,
  `src/field/field_emote_bubble.c`), except on tile behaviours 46, 113 and 114
  (`FollowMonInteraction_TryShowEmote`, line 945).
- **Sound** is played only on movement steps whose `playSound` byte is set
  (`FollowMonMovement_PlaySound`, line 1052). Above `SEQ_SE_END` (2378) it is the
  Pokémon's cry: 2379 normal, 2380 another cry variant (`PlayCryEx` mode 11); otherwise a
  sound effect.
- **Movement** member `movement - 1` of `files/a/2/2/2` is up to 10 steps of 8 bytes:
  facing (+1, 0xFF ends), duration (frames), dx, dy, dz, playSound. The follower is put
  back where it started afterwards (`FollowMonInteraction_RunMovement`, line 1141).
  Diglett and Dugtrio ignore dy.
- After the last step the mood and friendship changes are applied, clamped to ±127 and
  0-255 (`FollowMon_ApplyInteractionEffects`, line 1338). Then, if `askQuestion` is set,
  the touch-screen yes/no menu opens and `yesScript` or `noScript` runs; else a gift.

Retail examples (decoded from the archive):

| Script | Steps | Effect |
|---|---|---|
| 1 | movement 3, "It's facing this way and nodding.", emote 5 | none |
| 905 | "Huh? ... is holding something... Would you like to take it?" | question: yes → 907 ("too important to let go", mood -80), no → 906 ("seems happy to have found something", mood +80) |
| 909 | the same question | yes → 964, which gives accessory 2, friendship +1, mood +81 |
| 1018 | a few movements, "...holding some kind of strange, Shiny Leaf" | Shiny Leaf 1, friendship +5, mood +120 |

The `script` field is 10 bits, so ids 1-1023 are all there is, and the archive already
has 1,023 members. A scan of all rules and questions found 16 scripts nothing points to:
82, 124, 136, 184, 415, 507, 656, 665, 815, 816, 838, 845, 897, 903, 904 and 1023.
These are the ones to overwrite.

### 4.5 Text

Step messages are `msg_0265.json`, message `message - 1`
(`FollowMon_ExpandInteractionMessage`, line 992). Placeholders
(`FollowMon_PlaceholdersSet`, line 1328):

| Buffer | Holds | In retail text |
|---|---|---|
| 0 | nickname | `{STRVAR_1 1, 0, 0}` (583 uses) |
| 1 | species name | not used |
| 2 | player's name | `{STRVAR_1 3, 2, 0}` |
| 3 | location (map section) | not used |
| 4 | held item | `{STRVAR_1 8, 4, 0}` |

A question message ends with `{YESNO 0}` (message 0). See
[text-and-messages.md](text-and-messages.md) for editing text banks.

### 4.6 Gifts: accessories and Shiny Leaves

Retail followers never put an item in the bag. The "found something" interactions give:

- **Accessories.** Scripts 963-1017 give accessories 1-55 (`accessory - 1`) to the
  Fashion Case if there is room, with fanfare `SEQ_ME_ACCE` and `msg_0040` 32 or 95
  (`src/field/follow_mon_interaction.c:1266-1278`, text at line 1005). They are only
  reached through yes-answers from scripts 908-962, which map-section rules pick.
- **Shiny Leaves.** Scripts 1018-1022 give leaves A-E to the lead, set flag `0x99C`
  (`SetFlag99C`) and print `msg_0040` 97, or 98 if it already has that leaf (line 1280).

## 5. Mood

Mood is a signed byte kept in each Pokémon's data (`include/pokemon_types_def.h:142`),
-127 to 127. `FollowMonMood` (`include/field_system.h:117`) points at the lead's.

**Reset.** `FollowMonMood_SetMon` sets mood to 0 whenever the lead's species or
personality differs from the one registered (`src/follow_mon.c:1967`). It runs when the
follower is created or changed and when its sprite reloads. The registration is on the
heap (`FollowMonMood_New`, `src/overlay_124.c:41`), so the first lead after loading a
save also starts at 0.

**Decay.** Every step while the follower is shown, mood moves 1 towards 0
(`FieldSystem_ProcessStep`, `src/field/field_control.c:687-689`;
`FollowMonMood_MoveTowardsNeutral`, `src/follow_mon.c:1979`).

**What changes it:**

| Event | Change | Code |
|---|---|---|
| interaction scripts | `moodChange` (retail -80 to +120) | `src/field/follow_mon_interaction.c:1338` |
| `followmonaddmood(n)` | n (a signed byte) | `src/scrcmd_c.c:4910` |
| the follower uses Cut / Rock Smash | +20, and +1 more if Grass / Fighting type | `scr_seq_0146.s:164-169`, `:324-329` |
| the follower uses Strength | +1 if Normal type | `scr_seq_0146.s:490-495` |
| Fly / Dig / Teleport / Surf / Rock Climb / Sweet Scent by the follower | +1 if Flying / Ground / Psychic / Water / Normal / Grass type (it also jumps twice instead of once) | `src/field_warp_state.c:191`, `src/field/field_move_warp_tasks.c:317`, `:405`, `src/field/player_avatar_actions.c:623`, `:878`, `src/field/field_move_sweet_scent.c:110` |
| level up in battle | +40 | `sMoodModifiers`, `src/pokemon_mood.c:9`; `src/battle/battle_command.c:6164` |
| beating League trainers | +50 | `src/battle/battle_main.c:893` |
| fainting | -80, or -100 against a foe 30+ levels higher | `src/battle/battle_command.c:8072-8080` |
| learning a TM/HM | +40 | `src/party_menu_items.c:911` |
| surviving poison in the field | -50 | `src/script_pokemon_util.c:190` |
| Aprijuice | +30 | `src/application/apricorn_box/apricorn_box_overlay.c:164` |
| some items (Rare Candy +40, vitamins +8, X items +10, bitter herbs -20 to -40) | as listed | `ItemIdGetMoodEffect`, `src/pokemon_mood.c:38` |

Battle and item changes apply to whichever Pokémon is involved, not only the lead.

**Mood ranges in rules** (`FollowMonRule_CheckMood`, line 1434):

| `mood` | Range |
|---:|---|
| 1 | 127 |
| 2 | 100-126 |
| 3 | 50-99 |
| 4 | 30-49 |
| 5 | -29 to 29 |
| 6 | -49 to -30 |
| 7 | -126 to -50 |
| 8 | -127 |
| 9 | ≥ 0 |
| 10 | < 0 |

## 6. Script commands

Names as written in `scripts.pory` ([script-commands.md](script-commands.md)); the full
list with numbers is in [script-commands-list.md](script-commands-list.md). Most do
nothing when `FollowMon_IsActive` is FALSE.

| Command | Does | Code |
|---|---|---|
| `followmonisactive(var)` | TRUE if there is a follower and a healthy Pokémon | `src/scrcmd_c.c:4883` |
| `followmonisinactiveorvisible(var)` | TRUE if inactive **or hidden** (see the naming trap in §1) | `:4893` |
| `followmonislarge(var)` | the `too_tall` flag of its model | `:4426` |
| `followmonisnexttoplayer(var)` | shown and on a tile next to the player | `:5397` |
| `getfollowpokepartyindex(var)` | party slot of the first healthy Pokémon | `:4867` |
| species | no command; `getpartyleadalive(var)` then `getpartymonspecies(slot, var)` | `scr_seq_0163.s:18-19` |
| `followmonfaceplayer` | face the player (large: only if two tiles are free) | `:4470` |
| `followmonrecall` | white flash into the ball; just hides it if already hidden | `:4462` |
| `followmonhopintoball` | hop beside the player into the ball | `:4457` |
| `followmonmovetoplayer` | put it on the player's tile (if allowed here) | `:4555` |
| `followmonreleasenexttoplayer` | put it on the player, come out of the ball on the next step | `:4543` |
| `followmonspawnreleaseball` | ball-opening effect only | `:4565` |
| `followmonsetpositionnexttoplayer(dir, facing)` | put it next to the player | `:4532` |
| `swapplayerandfollowmonpositions(mode)` | swap places (field moves) | `:4439` |
| `togglefollowingpokemonmovement(on)` | 1 pause, 0 unpause | `:4495` |
| `waitfollowingpokemonmovement` | wait until its movement is done | `:4509` |
| `followingpokemonmovement(type)` | change its movement type (48, 55, 56) | `:4516` |
| `followmonresetmovement` | clear its movement and the step queue | `:4573` |
| `followmonshowemotebubble` | emote bubble 0 | `:4433` |
| `followmonjumponspot(n)` | jump n times (not Diglett/Dugtrio) | `:4927` |
| `followmonflash(step, period)` | fade to white and back | `:4873` |
| `followmongrowandshrink` | grow to 1.5× and back | `:4905` |
| `followmonaddmood(n)` | add to mood | `:4910` |
| `followmoninteract` | the talk interaction | `:4803` |
| `setfollowmoninhibitstate(0/1)` | the saved inhibit bit | `:5242` |
| `followerpokeiseventtrigger(event, slot, var)` | event-Pokémon check (Spiky-eared Pichu, Arceus, Celebi) | `:4383` |

**Cutscene pattern** (233 times in map scripts). Type 48 only follows steps the player
takes by input, so a script that moves the player switches to type 55 and back:

```
togglefollowingpokemonmovement(0)
waitfollowingpokemonmovement
followingpokemonmovement(55)
applymovement(obj_player, ...)
waitmovement
waitfollowingpokemonmovement
togglefollowingpokemonmovement(1)
followingpokemonmovement(48)
```

(`data/maps/Viridian_TrainerHouse_B1F/scripts.pory:19-26`.)

**Keep it in its ball for this map** (Blackthorn and Viridian Gyms, "unstable footing"):

```
followmonrecall
setfollowmoninhibitstate(1)
followmonmovetoplayer
changeobjectmovement(253, 56)
```

(`data/maps/Blackthorn_Gym/scripts.pory:211-214`.) The Trainer House sets the inhibit bit
before its save prompt so that a reloaded game keeps it hidden
(`Viridian_TrainerHouse_B1F/scripts.pory:80-82`). Maps whose scripts recall it:
BattleFrontier, Blackthorn_Gym, Fuchsia_PalParkEntrance, NewBark, Route10, Route34,
SafariZoneEntranceInterior, Saffron_Gym, Viridian_Gym, Viridian_TrainerHouse_B1F.

## 7. What is saved

`SaveFollowMon` (save block `SAVE_FOLLOW_MON`, 33, 8 bytes;
[save-data.md](save-data.md)):

| Field | Meaning |
|---|---|
| `mapNo` (u32) | the map left at the last warp (`src/field_transition_effects.c:204`), read by `FollowMon_GetPermission` |
| `unused : 2` | written 0 / 1 walking / 2 cycling or surfing (`src/follow_mon.c:1514-1546`); its getter is dead-stripped, nothing reads it |
| `inhibitFlag : 1` | the inhibit bit ([§1](#bike-surf-script-inhibit)) |

Mood, friendship and Shiny Leaves are saved in the Pokémon itself. The follower's
position is saved with the other map objects. Changing rules, scripts, text or
`follow_mode` doesn't change the save layout.

## 8. How-tos

All code changes below were written from the code and **not built**.

### 8.1 Let a large species follow indoors

Don't clear `too_tall`: it also makes the engine treat the 64×64 sprite as two tiles
long ([§2](#2-model-parameters-tp_paramcsv)). Change the permission instead, in
`FollowMon_GetPermissionBySpeciesAndMap` (`src/follow_mon.c:1814`):

```diff
     case MAP_FOLLOWMODE_HEIGHT_RESTRICT:
-        if (FollowMon_GetSizeParamBySpecies(species)) {
+        if (FollowMon_GetSizeParamBySpecies(species) && species != SPECIES_STEELIX) {
             ret = FALSE;
```

Removing the whole `if` lets every large Pokémon in. Whether the big sprites look
right under interior cameras and ceilings was not checked.

### 8.2 Enable or disable following on a map

Set `follow_mode` in that map's `map.json` to `MAP_FOLLOWMODE_ALLOW`,
`MAP_FOLLOWMODE_HEIGHT_RESTRICT` or `MAP_FOLLOWMODE_PREVENT`, and rebuild. For one
species on some maps, copy the Diglett check: a `switch (mapNo)` like
`FollowMon_DiglettPermissionCheck` (`src/follow_mon.c:1860`) called at the top of
`FollowMon_GetPermissionBySpeciesAndMap`. For one scene only, use the "keep it in its
ball" pattern from [§6](#6-script-commands).

### 8.3 Add an interaction

Example: on Route 29 (any map in section `MAPSEC_ROUTE_29`, 177), a happy follower
says something new.

**1. The message.** Append to `files/msgdata/msg/msg_0265.json`:

```json
{"id": "msg_0265_00759", "en_US": "{STRVAR_1 1, 0, 0} is sniffing the flowers."}
```

**2. The script.** Overwrite an unreferenced script, here 82 (member 81). Unpack the
archives as in [adding-a-species.md](adding-a-species.md#0-before-you-start) (the
round trip gives back `files/a/2/2/0` byte for byte):

```sh
NARC=build/heartgold.us/tools/nitroarc/nitroarc
mkdir -p /tmp/narc && cp files/a/2/2/0 /tmp/narc/rules.narc && cp files/a/2/2/1 /tmp/narc/scripts.narc
$NARC -xf /tmp/narc/rules.narc && $NARC -xf /tmp/narc/scripts.narc
```

```python
import struct
END = (0xFFFF, 0xFFFF, 0xFFFF, 0xFF, 0xFF)
steps = [(3, 759 + 1, 2379, 1 + 0, 0)] + [END] * 4      # movement 3, message 759, cry, emote 0
body = b''.join(struct.pack('<3H2B', *s) for s in steps)
body += struct.pack('<I2H2b2B', 0, 0, 0, 0, 10, 0, 0)   # no question, mood +10
assert len(body) == 52
open('/tmp/narc/scripts.narc.d/00081.bin', 'wb').write(body)
```

**3. The rule.** Put it in an empty slot of section member 178 (177 + 1). Slots are
tried in order, so an earlier slot wins over later ones:

```python
import struct
def pack_rule(script, chance=100, hp=0, mood=0, friendship=0, nature=0, gender=0, status=0,
              held=0, type=0, stat=0, enc=0, sattr=0, leaf=0, weather=0, facing=0,
              nearby=0, time=0, map=None, behavior=0, level=0, rock=0, hidden=0, flag=0):
    return struct.pack('<8B4H2BH', hp, mood | friendship << 4, nature | gender << 3 | status << 5,
        held, type | stat << 5, enc, sattr, leaf, weather | facing << 13,
        nearby | time << 3 | script << 6, 0 if map is None else map + 1, behavior,
        level << 1 | rock << 3 | hidden << 5, chance, flag)

p = '/tmp/narc/rules.narc.d/00178.bin'
b = bytearray(open(p, 'rb').read())
slot = next(i for i in range(30) if struct.unpack_from('<H', b, 20 * i + 10)[0] >> 6 == 0)
b[20 * slot:20 * slot + 20] = pack_rule(script=82, chance=50, mood=9)   # mood >= 0, 50%
assert len(b) == 600
open(p, 'wb').write(b)
```

Then pack both back:

```sh
for a in rules scripts; do
  ls /tmp/narc/$a.narc.d | sort > /tmp/narc/order.txt
  $NARC -cf /tmp/narc/$a.out -T /tmp/narc/order.txt /tmp/narc/$a.narc.d
done
cp /tmp/narc/rules.out files/a/2/2/0 && cp /tmp/narc/scripts.out files/a/2/2/1
```

The global rules (member 0) have no empty slot; to add a global condition, change an
existing rule or use a chance-0 rule. **A new condition type** (say, "holding a
specific item") needs code: a value in `FollowMonSituation`
(`src/field/follow_mon_interaction.c:62`) filled in `FollowMon_GetSituation`, and a test
in `FollowMonRule_Matches` that reads one of the unused rule bits (`unused_3`,
`unused_8`, `unused_10`, `include/field_system.h:134`, `:141`, `:148`). A new species also needs
an entry in `files/a/2/3/1`: `FollowMonSituation_SetSpeciesAttr` asserts on species
past Arceus and leaves `speciesAttr` unset (line 742).

### 8.4 Change the mood rules

| To | Change |
|---|---|
| make mood last longer | in `FieldSystem_ProcessStep` (`src/field/field_control.c:687`), call `FollowMonMood_MoveTowardsNeutral` only every n steps |
| keep mood when the lead changes | remove the `SetMonData(mon, MON_DATA_MOOD, &mood)` in `FollowMonMood_SetMon` (`src/follow_mon.c:1975`) |
| move the mood bands | the limits in `FollowMonRule_CheckMood` (`src/field/follow_mon_interaction.c:1434`) |
| change field-move bonuses | the `FollowMonMood_Add(..., 1)` calls listed in [§5](#5-mood), and `followmonaddmood 20` in `scr_seq_0146.s` |
| change battle/item effects | `sMoodModifiers` and `ItemIdGetMoodEffect` in `src/pokemon_mood.c` |
| change one interaction's effect | its `moodChange` / `friendshipChange` bytes (offsets 48-49, [§4.4](#44-interaction-scripts-filesa221)) |

### 8.5 Make following toggleable

A flag that turns following off everywhere. Pick a free flag
([unknown-flags-vars.md](unknown-flags-vars.md#free-flags)), for example
`#define FLAG_FOLLOWER_OFF 0x040` in `include/constants/flags.h`. Then at the top of
`FollowMon_GetPermissionBySpeciesAndMap` (`src/follow_mon.c:1804`), which has no
`FieldSystem`, read the flag through the global save pointer (`SaveData_Get`,
`src/save.c:123`):

```diff
+#include "constants/flags.h"
+#include "save_vars_flags.h"
 ...
 BOOL FollowMon_GetPermissionBySpeciesAndMap(int species, u32 mapNo) {
     BOOL ret;
+    if (Save_VarsFlags_CheckFlagInArray(Save_VarsFlags_Get(SaveData_Get()), FLAG_FOLLOWER_OFF)) {
+        return FALSE;
+    }
```

Every place that decides whether it may come out now says no while the flag is set.
A script to toggle it:

```
if (flag(FLAG_FOLLOWER_OFF)) {
    clearflag(FLAG_FOLLOWER_OFF)
} else {
    followmonrecall
    setflag(FLAG_FOLLOWER_OFF)
}
```

When turned off, `followmonrecall` hides it at once and `FollowMon_RecreateForMap`
removes it the next time the overworld reloads. When turned on, it appears after the
next warp or menu (`FollowMon_RecreateForMap` creates it when there is none). To show it
at once, the object must still exist; `followmonreleasenexttoplayer` only works on an
existing follower.

## Not verified

Nothing in this guide was tried in the game. In particular:

- None of the recipes in §8 were built or played.
- The rule and script layouts were decoded from the code and checked by round-tripping
  the archives in Python, and the retail examples were decoded the same way; the
  messages actually shown for them were not watched in game.
- The 16 "unreferenced" scripts come from a scan of rules and yes/no answers only;
  something else could still load them.
- What `unk2_0` and `hover` look like in game; the nibble order of byte 2 is assumed
  from the CSV manifest (low nibble first).
- That the mood registration is lost on reloading a save (inferred from
  `FollowMonMood_New` running at field start).
- The meaning of the species attribute values and of the nature groups.
- Whether a hidden follower can still be talked to or blocks the player.
- The exact sequence of `Task_WarpPanel`, `Task_FieldDig`/`Task_FieldTeleport` and the
  photo and cutscene code (`field_take_photo.c`, `event_cutscene_*.c`) that also move or
  hide the follower; only the lines cited were read.
