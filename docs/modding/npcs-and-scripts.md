<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# NPCs, trainers, event scripts and text

> AI-generated, local to this fork. Do not upstream.

Read [maps-and-warps.md](maps-and-warps.md) first for how to find a map's files
and how coordinates work.

## NPC records

NPCs are the `object_events` of the map's `map.json`
(`data/maps/<MapName>/map.json`; field names follow pokeemerald):

```json
{ "local_id": "obj_T21_gsoldman1", "graphics_id": "SPRITE_GSOLDMAN1",
  "x": 566, "y": 396, "elevation": 0,
  "movement_type": "MOVEMENT_TYPE_FACE_DOWN", "movement_range_x": 0, "movement_range_y": 0,
  "facing_dir": "DIR_SOUTH", "trainer_type": "OBJECT_TYPE_NORMAL",
  "trainer_sight_or_param0": 0, "param1": 0, "param2": 0,
  "script": "Cherrygrove_EventScript_GuideGent", "flag": "FLAG_HIDE_CHERRYGROVE_GUIDE_GENT" }
```

| Field | Meaning |
|---|---|
| `local_id` | object id, `#define`d in the map's `ids.h`; scripts use it (`ApplyMovement obj_T21_gsoldman1, ...`). Should be unique in the map |
| `graphics_id` | `SPRITE_*` from `include/constants/sprites.h` |
| `x`, `y`, `elevation` | position in global tiles ([maps-and-warps.md](maps-and-warps.md#coordinates)) |
| `movement_type` | `MOVEMENT_TYPE_*` (see below) |
| `movement_range_x`, `movement_range_y` | how far a wandering NPC may move from its start |
| `facing_dir` | `DIR_NORTH`, `DIR_SOUTH`, `DIR_WEST`, `DIR_EAST` (`include/constants/global_fieldmap.h`) |
| `trainer_type` | `OBJECT_TYPE_NORMAL`, `OBJECT_TYPE_TRAINER` (sees along its facing direction), `OBJECT_TYPE_TRAINER_ALL_DIRECTIONS`, or a trainer variant (`include/constants/map_object.h`) |
| `trainer_sight_or_param0` | for trainers: sight range in tiles; otherwise depends on the movement type |
| `script` | script run when you talk to it: a script label in this map, a `std_*` constant, or `0` for none (see "Script IDs") |
| `flag` | hide flag: the NPC is not spawned while this flag is set. `FLAG_NOTHING` = always shown |

### Movement types

`MOVEMENT_TYPE_*` in `include/constants/map_object.h` (an index into
`gMapObjectMovementCallbacks`, `asm/map_object_movement_tables.s`). The common ones:

| Constant | NPC |
|---|---|
| `MOVEMENT_TYPE_NONE` | stands still, keeps `facing_dir` |
| `MOVEMENT_TYPE_FACE_UP` / `_DOWN` / `_LEFT` / `_RIGHT` | stands still facing that way |
| `MOVEMENT_TYPE_LOOK_AROUND` | stands still, turns randomly |
| `MOVEMENT_TYPE_LOOK_UP_DOWN`, `MOVEMENT_TYPE_LOOK_LEFT_RIGHT`, `MOVEMENT_TYPE_LOOK_DOWN_LEFT`, ... | turns randomly between those directions |
| `MOVEMENT_TYPE_WANDER_AROUND` | walks randomly within `movement_range_x/y` |
| `MOVEMENT_TYPE_WANDER_UP_DOWN`, `MOVEMENT_TYPE_WANDER_LEFT_RIGHT` | walks randomly along one axis |
| `MOVEMENT_TYPE_SPIN_CLOCKWISE` / `_COUNTERCLOCKWISE` | turns in a circle |
| `MOVEMENT_TYPE_PATH_*` | walks a fixed loop; the name is the order of directions |

Don't use `MOVEMENT_TYPE_INVALID_47` (empty slot) or `MOVEMENT_TYPE_PLAYER`.
`mapkit validate` catches both.

## Checking your edits

`tools/mapkit/mapkit.sh show <map>` lists a map's NPCs, warps, signs and triggers
with the script each one runs; `tools/mapkit/mapkit.sh validate <map>` reports broken
references (bad script ids, unknown flags, warps to missing warps, oversized events).
See [tools/mapkit/README.md](../../tools/mapkit/README.md).

## Editing with mapkit

The commands below edit the right file for both layouts and keep its formatting.
A full example, adding a fisherman who says one line:

```sh
M=tools/mapkit/mapkit.sh
msg=$($M text add Cherrygrove 'The sea breeze here\nis so refreshing!')   # prints msg_0550_T21_00025
$M script add Cherrygrove Cherrygrove_EventScript_Fisher --msg $msg     # talk-to-NPC script
$M npc add Cherrygrove fisher SPRITE_FISHING_2 532 404 \
    --movement MOVEMENT_TYPE_LOOK_AROUND --script Cherrygrove_EventScript_Fisher
$M npc move Cherrygrove gsboy1 556 400
$M validate Cherrygrove
make release
```

`npc set Cherrygrove gsboy1 flag=FLAG_X movement_type=MOVEMENT_TYPE_FACE_UP` changes
any field; `script rename` renames a script and every reference to it.

## Moving an NPC

Change `x` and `y` (and `facing_dir` if needed), or
`tools/mapkit/mapkit.sh npc move Cherrygrove gsboy1 556 400`. If it wanders, check
`movement_range_x/y` still fit. If a script walks the NPC somewhere with
`ApplyMovement`, that movement is relative to where it starts, so check the path
still works.

## Hiding / showing an NPC

Set `flag` to a flag. In scripts: `SetFlag FLAG_X` + `HidePerson obj_...` removes it
now and keeps it gone; `ClearFlag FLAG_X` + `ShowPerson obj_...` brings it back
(`Cherrygrove_EventScript_GuideGentMapCard` does this for the Guide Gent). Unique hide
flags are `FLAG_HIDE_*` in `include/constants/flags.h`.

## Adding an NPC

`mapkit npc add` does all of this:

1. Append an object to `object_events` with a new `local_id`.
2. Add `#define obj_CODE_name N` to the map's `ids.h` with a number no other object
   in the map uses.
3. Give it a `script` (existing or new, below).
4. Keep the events under 0x800 bytes (each object is 32 bytes; `mapkit validate` checks).

## Trainers

A trainer NPC is an object with a trainer `trainer_type` (usually
`OBJECT_TYPE_TRAINER`), `trainer_sight_or_param0` = sight range, and `script` =
`std_trainer(TRAINER_X)` (or `std_trainer_2(...)` for the second trainer of a double
battle pair), from `data/maps/Route30/map.json`:

```json
{ "local_id": "obj_R30_gsboy3", "graphics_id": "SPRITE_GSBOY3", "x": 550, "y": 298, "elevation": 0,
  "movement_type": "MOVEMENT_TYPE_FACE_RIGHT", "facing_dir": "DIR_EAST",
  "trainer_type": "OBJECT_TYPE_TRAINER", "trainer_sight_or_param0": 3,
  "script": "std_trainer(TRAINER_BUG_CATCHER_DON)", "flag": "FLAG_NOTHING", ... }
```

Parties, class, AI flags and items: `files/poketool/trainer/trainers.json`
(constants in `include/constants/trainers.h`). The `messages` in that JSON are
**not** used by the build; trainer battle text is `msg_0728.json` indexed through
the binary `files/poketool/trmsg/trtbl.narc`. Changing which lines a trainer uses
isn't possible as text yet.

## Event scripts

Scripts can also be written in `scripts.pory` with `if`/`while`/`switch` and inline
text: see [SCRIPTING.md](SCRIPTING.md). This section covers the `.inc` form.

`data/maps/<MapName>/scripts.inc` is an assembly file made of script-command macros
from `asm/macros/script.inc`. From Cherrygrove, the man who gives Mystic Water:

```asm
	ScrDef Cherrygrove_EventScript_GuideGent        @ script 1
	...
	ScrDef Cherrygrove_EventScript_MysticWaterMan   @ script 5
	...
	ScrDefEnd

Cherrygrove_EventScript_MysticWaterMan:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	FacePlayer
	GoToIfSet FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN, _0903
	NPCMsg msg_0550_T21_00020
	GoToIfNoItemSpace ITEM_MYSTIC_WATER, 1, _090E
	CallStd std_give_item_verbose
	SetFlag FLAG_GOT_MYSTIC_WATER_FROM_CHERRYGROVE_CITY_MAN
_0903:
	NPCMsg msg_0550_T21_00021
	WaitButton
	CloseMsg
	ReleaseAll
	End
```

Most maps still use their original labels (`scr_seq_T21_004`); Cherrygrove's were
renamed pokeemerald-style with `mapkit script rename`.

Common commands: `LockAll`/`ReleaseAll`, `FacePlayer`, `NPCMsg`, `WaitButton`,
`CloseMsg`, `GoTo`, `GoToIfSet FLAG, label`, `Compare VAR, n` + `GoToIfEq label`,
`SetFlag`/`ClearFlag`, `SetVar`, `ShowPerson`/`HidePerson`,
`ApplyMovement obj, label` + `WaitMovement`, `CallStd std_*`, `End`.
Labels like `_0903` are internal jump targets; rename them freely.
`grep -n '\.macro <Name>' asm/macros/script.inc` shows a command's arguments.
852 commands exist and all have names; some arguments are still `argN`.

### Script IDs

Events refer to scripts in one of three ways:

- **A label** of a script in this map (`"script": "Cherrygrove_EventScript_MysticWaterMan"`),
  as in pokeemerald. The build turns it into `_EV_<label> + 1`: the script's `ScrDef`
  index plus one (`ids.h` defines `_EV_<label>`). The same expression works too.
- **`std_*` constants** (`include/constants/std_script.h`, ids 2000 and up): shared
  scripts such as `std_trainer(...)`, signposts and hidden items. Routing:
  `sScriptBankMapping` in `src/script_manager.c`.
- `0`: no script.

### Adding a script

`tools/mapkit/mapkit.sh script add <map> <Label> [--msg <msg id>]` does this:

1. Add `ScrDef <Label>` as the **last** line before `ScrDefEnd` (appending keeps
   every existing number the same).
2. Add the labeled script body after the table.
3. Add `#define _EV_<Label> <index>` to `ids.h`.
4. Point the object/sign/trigger at `"script": "<Label>"`.

Never insert into the middle of the `ScrDef` table: it renumbers every later script.
`mapkit script rename <map> <old> <new>` renames a script everywhere in the map.

### Init / level scripts (`map_scripts.inc`)

`map_scripts.inc` declares scripts the engine runs by itself. Cherrygrove runs
`Cherrygrove_OnTransition` on every entry:

```asm
	InitScriptEntry_OnTransition _EV_Cherrygrove_OnTransition + 1
	InitScriptEntryEnd

	InitScriptEnd
```

Mount Moon (`data/maps/MountMoon/map_scripts.inc`) checks a var every frame:

```asm
	InitScriptEntry_OnFrameTable scr_seq_D02R0101_map_scripts_2
	InitScriptEntryEnd

scr_seq_D02R0101_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_40F5, 0, _EV_scr_seq_D02R0101_000 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
```

Script ids here use the `_EV_<label> + 1` form. `InitScriptEntry_OnLoad` and
`InitScriptEntry_OnResume` also exist. Macros: `asm/macros/script.inc`; types:
`include/constants/init_script_types.h`.

### Movement scripts

Inline data after `.balign 4` in the script file, macros from
`asm/macros/movement.inc`:

```asm
	.balign 4
_walkToPlayer:
	WalkNormalNorth 2
	FaceEast
	EndMovement
```

Run with `ApplyMovement obj_T21_gsoldman1, _walkToPlayer` then `WaitMovement`.

## Text

`data/maps/<MapName>/text.json`:

```json
{ "key": 20267, "messages": [
  { "id": "msg_0550_T21_00020", "en_US": ["first line\n", "second line"] } ] }
```

- `\n` ends a line; the files also use `\r` and `\f` for scrolling/new boxes
  (copy an existing message that behaves the way you want). Inline codes like
  `{STRVAR_1 3, 0, 0}` insert names/numbers; `{YESNO 0}` for prompts.
- A message's number is its position. **Append** new messages at the end
  (`mapkit text add` does); inserting renumbers every later message.
- The build (msgenc) writes `msg_NNNN_CODE.h` defining each `id` as its number.
  The `id` can be any name, e.g. `Cherrygrove_Text_Fisher`.

## Flags and vars

`include/constants/flags.h` (2250 flags; 1137 still `FLAG_UNK_*`) and
`include/constants/vars.h` (386 vars; 251 still `VAR_UNK_*`).

- Temporary vars `VAR_TEMP_x4000`.. are cleared on every warp
  (`ClearTempFieldEventData`, `src/script_manager.c`); `VAR_SPECIAL_x8000`..
  pass arguments to and from commands and std scripts.
- To use a new persistent flag, prefer renaming an unused `FLAG_UNK_*` you've
  confirmed is never referenced (`grep -rn FLAG_UNK_123 files src`).
