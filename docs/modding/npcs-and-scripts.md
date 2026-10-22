<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21 -->

# NPCs, trainers, event scripts and text

> AI-generated, local to this fork. Do not upstream.

Read [maps-and-warps.md](maps-and-warps.md) first for how to find a map's files
and how coordinates work.

## NPC records

NPCs are the `objects` array of the map's zone_event JSON
(`files/fielddata/eventdata/zone_event/NNN_CODE.json`):

```json
{ "id": "obj_T21_gsoldman1", "spriteId": "SPRITE_GSOLDMAN1",
  "movement": "MOVEMENT_TYPE_FACE_DOWN", "type": "OBJECT_TYPE_NORMAL",
  "eventFlag": "FLAG_HIDE_CHERRYGROVE_GUIDE_GENT",
  "scriptId": "_EV_scr_seq_T21_000 + 1", "facingDirection": "DIR_SOUTH",
  "param0": 0, "param1": 0, "param2": 0, "xRange": 0, "yRange": 0,
  "x": 566, "z": 396, "y": 0 }
```

| Field | Meaning |
|---|---|
| `id` | object ID, `#define`d in `event_CODE.h`; scripts use it (`ApplyMovement obj_T21_gsoldman1, ...`). Must be unique in the map |
| `spriteId` | `SPRITE_*` from `include/constants/sprites.h` |
| `movement` | `MOVEMENT_TYPE_*` (see below) |
| `type` | `OBJECT_TYPE_NORMAL`, `OBJECT_TYPE_TRAINER` (sees along its facing direction), `OBJECT_TYPE_TRAINER_ALL_DIRECTIONS`, or a trainer variant; all in `include/constants/map_object.h` |
| `eventFlag` | hide flag: the NPC is not spawned while this flag is set. `FLAG_NOTHING` = always shown |
| `scriptId` | script run when you talk to it (see "Script IDs") |
| `facingDirection` | `DIR_NORTH`, `DIR_SOUTH`, `DIR_WEST`, `DIR_EAST` (`include/constants/global_fieldmap.h`) |
| `param0` | for trainers: sight range in tiles. Other uses depend on movement type |
| `xRange`, `yRange` | how far a wandering NPC may move from its start |
| `x`, `z`, `y` | position in global tiles |

### Movement types

`MOVEMENT_TYPE_*` in `include/constants/map_object.h` (an index into
`gMapObjectMovementCallbacks`, `asm/map_object_movement_tables.s`). The common ones:

| Constant | NPC |
|---|---|
| `MOVEMENT_TYPE_NONE` | stands still, keeps `facingDirection` |
| `MOVEMENT_TYPE_FACE_UP` / `_DOWN` / `_LEFT` / `_RIGHT` | stands still facing that way |
| `MOVEMENT_TYPE_LOOK_AROUND` | stands still, turns randomly |
| `MOVEMENT_TYPE_LOOK_UP_DOWN`, `MOVEMENT_TYPE_LOOK_LEFT_RIGHT`, `MOVEMENT_TYPE_LOOK_DOWN_LEFT`, ... | turns randomly between those directions |
| `MOVEMENT_TYPE_WANDER_AROUND` | walks randomly within `xRange`/`yRange` |
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

## Moving an NPC

Change `x` and `z` (and `facingDirection` if needed). If it wanders, check
`xRange`/`yRange` still fit. If a script walks the NPC somewhere with
`ApplyMovement`, that movement is relative to where it starts, so check the
path still works.

## Hiding / showing an NPC

Set `eventFlag` to a flag. In scripts: `SetFlag FLAG_X` + `HidePerson obj_...`
removes it now and keeps it gone; `ClearFlag FLAG_X` + `ShowPerson obj_...`
brings it back (Cherrygrove's `scr_seq_T21_002` does exactly this for the Guide Gent). Unique hide flags are `FLAG_HIDE_*` in
`include/constants/flags.h`.

## Adding an NPC

1. Append an object to `objects` with a new `id`.
2. Add `#define obj_CODE_name N` to `event_CODE.h` with a number no other object
   in the map uses.
3. Give it a `scriptId` (existing or new, below).
4. Keep the events file under 0x800 bytes (each object is 32 bytes).

## Trainers

A trainer NPC is an object with a trainer `type` (usually `OBJECT_TYPE_TRAINER`),
`param0` = sight range, and
`scriptId` = `std_trainer(TRAINER_X)` (or `std_trainer_2(...)` for the second
trainer of a double battle pair):

```json
{ "id": "obj_R30_gsboy3", "spriteId": "SPRITE_GSBOY3",
  "movement": "MOVEMENT_TYPE_FACE_RIGHT", "type": "OBJECT_TYPE_TRAINER",
  "eventFlag": "FLAG_NOTHING", "scriptId": "std_trainer(TRAINER_BUG_CATCHER_DON)",
  "facingDirection": "DIR_EAST", "param0": 3, ... }
```

Parties, class, AI flags and items: `files/poketool/trainer/trainers.json`
(constants in `include/constants/trainers.h`). The `messages` in that JSON are
**not** used by the build; trainer battle text is `msg_0728.json` indexed through
the binary `files/poketool/trmsg/trtbl.narc`. Changing which lines a trainer uses
isn't possible as text yet.

## Event scripts

`files/fielddata/script/scr_seq/scr_seq_NNNN_CODE.s` are assembly files made of
script-command macros from `asm/macros/script.inc`.

From `scr_seq_0850_T21.s` (Cherrygrove), the man who gives Mystic Water:

```asm
	ScrDef scr_seq_T21_000      @ index 0
	...
	ScrDef scr_seq_T21_004      @ index 4
	...
	ScrDefEnd

scr_seq_T21_004:
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

Common commands: `LockAll`/`ReleaseAll`, `FacePlayer`, `NPCMsg`, `WaitButton`,
`CloseMsg`, `GoTo`, `GoToIfSet FLAG, label`, `Compare VAR, n` + `GoToIfEq label`,
`SetFlag`/`ClearFlag`, `SetVar`, `ShowPerson`/`HidePerson`,
`ApplyMovement obj, label` + `WaitMovement`, `CallStd std_*`, `End`.
Labels like `_0903` are internal jump targets; rename them freely.
`grep -n '\.macro <Name>' asm/macros/script.inc` shows a command's arguments.
852 commands exist and all have names; some arguments are still `argN`.

### Script IDs

Objects, signs and triggers refer to scripts by number:

- `1`–`1999`: this map's scripts. Script at `ScrDef` index *i* is
  `_EV_scr_seq_CODE_i + 1`, with `#define _EV_scr_seq_CODE_i i` in `event_CODE.h`.
- `2000`+: shared scripts, as `std_*` constants (`include/constants/std_script.h`),
  e.g. `std_trainer(...)`, signposts, hidden items. Routing:
  `sScriptBankMapping` in `src/script_manager.c`.

### Adding a script

1. In the `.s` file, add `ScrDef scr_seq_CODE_NNN` as the **last** line before
   `ScrDefEnd` (appending keeps every existing index the same).
2. Add the labeled script body anywhere after the table.
3. In `event_CODE.h`, add `#define _EV_scr_seq_CODE_NNN NNN`.
4. Point the object/sign/trigger at `_EV_scr_seq_CODE_NNN + 1`.

Never insert into the middle of the `ScrDef` table: it renumbers every later script.

### Init / level scripts (`_hdr.s`)

`scr_seq_NNNN_CODE_hdr.s` declares scripts the engine runs by itself:

Cherrygrove (`scr_seq_0623_T21_hdr.s`) runs script 10 on every entry:

```asm
	InitScriptEntry_OnTransition _EV_scr_seq_T21_010 + 1
	InitScriptEntryEnd

	InitScriptEnd
```

Dark Cave (`scr_seq_0268_D02R0101_hdr.s`) checks a var every frame:

```asm
	InitScriptEntry_OnFrameTable scr_seq_D02R0101_map_scripts_2
	InitScriptEntryEnd

scr_seq_D02R0101_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_40F5, 0, _EV_scr_seq_D02R0101_000 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
```

Script IDs here use the same `_EV_... + 1` form. `InitScriptEntry_OnLoad` also exists.

Macros: `asm/macros/script.inc`; types: `include/constants/init_script_types.h`.

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

`files/msgdata/msg/msg_NNNN_CODE.json`:

```json
{ "key": 20267, "messages": [
  { "id": "msg_0550_T21_00020", "en_US": ["first line\n", "second line"] } ] }
```

- `\n` ends a line; the files also use `\r` and `\f` for scrolling/new boxes
  (copy an existing message that behaves the way you want). Inline codes like
  `{STRVAR_1 3, 0, 0}` insert names/numbers; `{YESNO 0}` for prompts.
- Message IDs are generated from position. **Append** new messages at the end;
  inserting renumbers every later message used by scripts.
- The build (msgenc) writes `msg_NNNN_CODE.h` with the IDs scripts use.

## Flags and vars

`include/constants/flags.h` (2250 flags; 1137 still `FLAG_UNK_*`) and
`include/constants/vars.h` (386 vars; 251 still `VAR_UNK_*`).

- Temporary vars `VAR_TEMP_x4000`.. are cleared on every warp
  (`ClearTempFieldEventData`, `src/script_manager.c`); `VAR_SPECIAL_x8000`..
  pass arguments to and from commands and std scripts.
- To use a new persistent flag, prefer renaming an unused `FLAG_UNK_*` you've
  confirmed is never referenced (`grep -rn FLAG_UNK_123 files src`).
