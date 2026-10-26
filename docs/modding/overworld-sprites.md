<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Overworld sprites, movement actions and movement types

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers three things:

- how an NPC's graphics are stored, and how to change or add one with
  `mapkit sprite`;
- how to add a **movement action**: a step such as `walk_up` in an `applymovement`
  script;
- how to add a **movement type**: an NPC's own behaviour, such as
  `MOVEMENT_TYPE_WANDER_AROUND`.

[npcs-and-scripts.md](npcs-and-scripts.md) covers placing NPCs and using the existing
sprites, movement types and movement scripts.
How the player moves (running, the bike, ledges, HMs) is in
[player-movement.md](player-movement.md).

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `graphics/object_events/pics/people/*.png` + `gObjectEventGraphicsInfo_*` | a texture file `files/data/mmodel/mmodel/mmodel_NNNNNNNN.NSBTX` + a row in `gObjectEventGraphicsInfos` (§1) |
| `OBJ_EVENT_GFX_*` | `SPRITE_*` (`include/constants/sprites.h`) |
| 2D sprite frames + `sAnimTable_*` | a 3D billboard: one texture per frame, animated by a shared sequence (§1) |
| `MOVEMENT_ACTION_*`, `gMovementActionFuncs_*` | movement commands 0-112, `gMovementCmdTable` (§3) |
| `MOVEMENT_TYPE_*`, `gMovementTypeFuncs_*` | `MOVEMENT_TYPE_*`, `gMapObjectMovementCallbacks` (§4) |

## 1. How an NPC sprite is drawn

The overworld is 3D, and each NPC is a **billboard**: a flat textured square that faces
the camera. A map object's `graphics_id` (`SPRITE_BOY1`) goes through one table to its
graphics:

```
map.json  "graphics_id": "SPRITE_BOY1"
   -> gObjectEventGraphicsInfos (asm/overlay_01_sprite_data.s)
        .short SPRITE_BOY1, MMODEL_BOY1, 0x000 | (0 << 10)
   -> MMODEL_BOY1 = 2 (include/constants/mmodel.h) = member 2 of files/data/mmodel/mmodel.narc
   -> files/data/mmodel/mmodel/mmodel_00000002.NSBTX   (16 textures, boy1.1 ... boy1.16, palette boy1)
```

The third value packs three indexes (`ObjectEventGraphicsInfo`, `include/map_object.h`):

| Bits | Field | Selects |
|---|---|---|
| 0-4 | `effectFlagsIdx` | `gSpriteEffectFlags` (`MapObjectEffectFlags`): draw type (1 = billboard), shadow, footprints, reflection |
| 5-9 | `drawCallbacksIdx` | `gMapObjectDrawCallbacks`: how it is drawn. 0 = an animated NPC billboard; others draw the player's states, follow-Pokémon, Apricorn trees, still objects |
| 10-15 | billboard info | `gSpriteBillboardInfos`: the billboard's square model and its animation sequence (index 0: the standard NPC) |

The square models (`mmodel_00000266`-`279.NSBMD`) and the animation sequences
(`mmodel_00000280`-`296`) are shared. A sprite's own data is only its NSBTX texture file.
A new NPC that copies a standard NPC's row therefore gets the standard animation.

### The texture

Every sprite texture is 16-colour (4 bits per pixel). The kinds:

| Frames × size | Palettes | Files | What |
|---|---|---|---|
| 16 × 32×32 | 1 | 193 | **standard NPCs** |
| 8 × 32×32 | 2 | 538 | follow-Pokémon (palette 0 normal, 1 shiny) |
| 8 × 64×64 | 2 | 34 | large follow-Pokémon |
| 32 × 32×32 | 1 | 10 | the player and others with extra poses |
| 1 × 32×32, 1 × 64×64, 1 × 16×16 | 1 | 24 | still objects |
| 2-24 frames | 1 | the rest | special objects |

A **standard NPC's 16 frames**, in name order (`.1` to `.16`):

| Frames | Facing | Within each group of four |
|---|---|---|
| 1-4 | up (away) | stand, step, stand, other step |
| 5-8 | down (toward the camera) | the same |
| 9-12 | left | the same |
| 13-16 | right | the same |

## 2. Changing or adding a sprite: `mapkit sprite`

```sh
M=tools/mapkit/mapkit.sh
$M sprite export SPRITE_BOY1 boy1.png          # all frames in a row: a 512×32 indexed PNG
# ... edit boy1.png ...
$M sprite import boy1.png SPRITE_BOY1          # write the pixels and palette back
```

A sprite is named by `SPRITE_X`, `MMODEL_X`, its member number, or a path to an `.NSBTX`
file.

**The sheet** is every frame side by side, as an indexed PNG with the sprite's palette.
Index 0 is transparent.

- **Keep the size**: frame count × frame width by frame height, for example 512×32 for a
  standard NPC.
- **Colours**: at most 15 plus transparency.
  - An **indexed** PNG is written as is: its indices and palette.
  - An **RGB or RGBA** PNG is fine too. Transparent pixels (alpha below 128) become index
    0. If every colour is already in the sprite's palette, the palette is kept; otherwise
    a new one is built from the image's colours.
- Colours are stored as 15-bit (5 bits per channel), so close colours may merge.
- `--palette 1` exports and imports a follow-Pokémon's shiny palette.

`import` only replaces pixels and one palette. The file keeps its frame count, sizes,
format and internal names, so the game loads it exactly as before. To make a sprite with a
different number of frames, copy one that already has that layout.
`python3 tools/mapkit/tests/test_sprites.py` checks that export then import leaves all
832 sprite files byte for byte unchanged.

### Adding a new sprite

```sh
$M sprite add CAMPER_RED --like SPRITE_BOY1 --png camper_red.png
```

This makes four one-line changes and one new file:

| Where | What |
|---|---|
| `files/data/mmodel/mmodel/mmodel_00000863.NSBTX` | a copy of `--like`'s texture (then `--png` imported into it). The next free member number |
| `files/data/mmodel/mmodel/meson.build` | the file added to the NSBTX list |
| `include/constants/mmodel.h` | `#define MMODEL_CAMPER_RED 863` |
| `include/constants/sprites.h` | `#define SPRITE_CAMPER_RED 1050`: the first free id from 1050, clear of every retail id except `SPRITE_CAMERA_FOCUS` (8192) |
| `asm/overlay_01_sprite_data.s` | a row in `gObjectEventGraphicsInfos` with `--like`'s packed value, so it gets the same shadow, drawing and animation |

Then use it like any sprite:
`$M npc set Route30 obj_R30_gsboy3 graphics_id=SPRITE_CAMPER_RED`, or
`"graphics_id": "SPRITE_CAMPER_RED"` in `map.json`. Build with `make release`.

Pick `--like` from a sprite of the same kind: a standard NPC (`SPRITE_BOY1`, `SPRITE_MAN1`,
`SPRITE_WOMAN1`...) for people.

**Limits and notes:**

- **32 sprites per map.** The overworld loads at most 32 different sprite textures at once
  (`MapObjectManager_InitRender(..., 32, ...)` in
  [src/field/fieldmap.c](../../src/field/fieldmap.c)). That covers the player, the
  follow-Pokémon and every distinct NPC look on screen. NPCs that share a sprite share a
  texture.
- **Free sprite ids.** `SPRITE_VAR_0`-`15` (100-115) are not real sprites. Such an
  object's sprite is read from the variable `VAR_OBJ_GFX_BASE + n` (0x4020 + n), so a
  script can choose it. The retail ids have gaps (26-28, 46-49...), but nothing guarantees
  they're unused; `add` stays above them.
- **Member numbers.** Members 266-296 are the shared models and sequences, and the code
  refers to them by number (`gBillboardModelNarcMembers`). Always **append** new
  textures, as `add` does; never renumber.
- **Undoing an add.** Revert the four files and delete the NSBTX, then **also delete**
  `build/heartgold.us/files/data/mmodel/mmodel.narc.p/mmodel_00000863.NSBTX` and
  `build/heartgold.us/files/data/mmodel/mmodel.narc` (and the same under
  `soulsilver.us`). The NARC is packed from everything in that build folder, so a stale
  copy stays in the ROM, and `make` then fails its checksum test.

**Not covered:** sprites with a different animation (a new sequence file), new draw
callbacks, and the player's own sprites. Copying an existing kind covers people and
objects.

## 3. Movement actions

A movement script, the block that `applymovement` runs, is a list of
`{u16 command, u16 count}` pairs ending with `EndMovement` (`MOVEMENT_STEP_END`, 254).
The macros are in [asm/macros/movement.inc](../../asm/macros/movement.inc). In `.pory`,
write them by macro name or pokeemerald-style (`WalkNormalNorth` = `walk_up`,
[SCRIPTING.md](SCRIPTING.md#movement)).

Each command number indexes `gMovementCmdTable`
([asm/map_object_movement_tables.s](../../asm/map_object_movement_tables.s)), giving a list
of **step functions** (`gMovementCmdSteps_NNN` in
[asm/map_object_movement_command_steps.s](../../asm/map_object_movement_command_steps.s)).
The object runs the current step every frame:

- A step returns `TRUE` to go on to the next step in the same frame. It moves to the next
  step by calling `MapObject_IncrementMovementStep`.
- It returns `FALSE` to run again next frame.
- The last step is usually `MapObjectMovementCmd098_Step2`, which marks the command
  finished.

A normal step up (`WalkNormalNorth`, command 12):

```
gMovementCmdSteps_012:
    .word MapObjectMovementCmd012_Step0    // start: direction, speed, animation
    .word MapObjectMovementCmd090_Step1    // every frame: move; when done, stand
    .word MapObjectMovementCmd098_Step2    // finished
```

```c
BOOL MapObjectMovementCmd012_Step0(LocalMapObject *object) {
    MapObject_StartWalkMovement(object, DIR_NORTH, 0x2000, 8, 3);  // per frame, frames, animation
    return TRUE;
}
```

One tile is 0x10000, so `distance × frames` must equal 0x10000. The retail speeds:

| Distance | Frames | Animation | Commands |
|---|---|---|---|
| 0x800 | 32 | 1 | `WalkSlower*` (4-7) |
| 0x1000 | 16 | 2 | `WalkSlow*` (8-11) |
| 0x2000 | 8 | 3 | `WalkNormal*` (12-15) |
| 0x4000 | 4 | 4 | `WalkFast*` (16-19) |
| 0x8000 | 2 | 5 | `WalkFaster*` (20-23) |
| 0x10000 | 1 | 0 | `WalkFastest*` (84-87) |
| 0x4000 | 4 | 9 (running) | `Run*` (88-91) |

The others are jumps (`MapObject_StartJumpByOffsetMovement`), walking in place, delays,
emotes, `WarpOut`/`WarpIn` and `SetInvisible`/`SetVisible`. They are all in
[src/map_object_movement_commands.c](../../src/map_object_movement_commands.c).

### Adding one

Example: a step up at normal speed with the running animation, as command 113.

1. The step function, in `src/map_object_movement_commands.c`, where the
   `MapObject_Start*Movement` helpers are:

   ```c
   // Walk one tile north at normal speed with the running animation
   BOOL MapObjectMovementCmd113_Step0(LocalMapObject *object) {
       MapObject_StartWalkMovement(object, DIR_NORTH, 0x2000, 8, 9);
       return TRUE;
   }
   ```

2. Its step list, at the end of `asm/map_object_movement_command_steps.s`, reusing the
   shared walk steps:

   ```
       .public gMovementCmdSteps_113
   gMovementCmdSteps_113:
       .word MapObjectMovementCmd113_Step0
       .word MapObjectMovementCmd090_Step1
       .word MapObjectMovementCmd098_Step2
   ```

   Add `.public MapObjectMovementCmd113_Step0` to
   `asm/include/map_object_movement_command_steps.inc`.
3. **Append** `.word gMovementCmdSteps_113` at the end of `gMovementCmdTable` in
   `asm/map_object_movement_tables.s`. Its position is its number. Add
   `.public gMovementCmdSteps_113` to `asm/include/map_object_movement_tables.inc`.
4. The macro, in `asm/macros/movement.inc`:

   ```
       .macro RunAnimWalkNorth length=1
       .short 113
       .short \length
       .endm
   ```

5. Use it: `run_anim_walk_up` or `RunAnimWalkNorth` in a `.pory` movement block.

This example, together with the movement type in §4, builds (`make release`); neither was
tried in-game.

**Limits:**

- Commands are numbered 0-112. 254 (`MOVEMENT_STEP_END`) and 255 (`MOVEMENT_NONE`) are
  reserved, so new ones can use 113-253.
- Per-command work data is 16 bytes (`MapObject_InitMovementCmdData` asserts).
- `EmoteExclamation2` in `movement.inc` is numbered **153**, past the end of the table.
  Using it reads garbage; use `EmoteExclamationMark` (75).

## 4. Movement types

An object's `movement_type` (`MOVEMENT_TYPE_*`, `include/constants/map_object.h`) indexes
`gMapObjectMovementCallbacks` (`asm/map_object_movement_tables.s`). Each entry is a
`MapObjectMovementCallbacks` (`include/map_object.h`):

```c
typedef struct MapObjectMovementCallbacks {
    u32 unk0;                         // the movement type's own number
    LocalMapObject_Callback init;     // when the object is created
    LocalMapObject_Callback update;   // every frame
    LocalMapObject_Callback delete;
    LocalMapObject_Callback restore;  // MapObject_CallMovementRestore (src/map_object.c)
} MapObjectMovementCallbacks;
```

The implementations are in [src/map_object_movement.c](../../src/map_object_movement.c).
An `update` usually works like `RandomWalkMovement_Update`: a small state machine that
starts one movement command at a time, then waits for it to finish. The building blocks:

| Call | Does |
|---|---|
| `MapObject_InitMovementData(obj, size)` / `MapObject_GetMovementData(obj)` | the type's own state, **16 bytes at most** |
| `MapObject_ForceSetHeldMovement(obj, command)` | start a movement command (§3) |
| `MapObject_RunForcedMovement(obj)` | run it; `TRUE` when it has finished |
| `GetMovementForDirection(dir, MOVEMENT_STEP_UP)` | the same command family in another direction (`DIR_*`) |
| `MapObject_CheckCollisionInDirection(obj, dir)` | non-zero if the next tile is blocked |
| `MapObject_GetFacingDirection`, `GetOppositeDirection` | directions |
| `MapObject_SetSingleMovement` / `ClearSingleMovement` | mark a step in progress (the random walk does this around each step) |
| `MapObject_GetInitialX/Z`, `GetXRange/GetYRange` | the object's home position and `movement_range_x/y` |

### Adding one

Example: `MOVEMENT_TYPE_PACE`, which walks two tiles, turns round, and walks back.

1. The constant, in `include/constants/map_object.h`. Use the next number and raise the
   count:

   ```c
   #define MOVEMENT_TYPE_PACE                     57
   #define MOVEMENT_TYPE_COUNT                    58
   ```

2. Size the table from the count, in `src/map_object.c`, which declares it as `[57]`:

   ```c
   #include "constants/map_object.h"   // add near the top
   extern MapObjectMovementCallbacks *gMapObjectMovementCallbacks[MOVEMENT_TYPE_COUNT];
   ```

3. The functions and callbacks, at the end of `src/map_object_movement.c` (also add
   `#include "constants/map_object.h"` there):

   ```c
   typedef struct PaceMovementState {
       s16 state;
       s16 steps;
   } PaceMovementState;

   enum PaceMovementStates {
       PACE_START_STEP,
       PACE_WAIT_STEP,
   };

   void PaceMovement_Init(LocalMapObject *object) {
       MapObject_InitMovementData(object, sizeof(PaceMovementState));
       MapObject_SetAnimation(object, 0);
       MapObject_ClearSingleMovement(object);
   }

   void PaceMovement_Update(LocalMapObject *object) {
       PaceMovementState *state = (PaceMovementState *)MapObject_GetMovementData(object);
       u32 direction = MapObject_GetFacingDirection(object);

       switch (state->state) {
       case PACE_START_STEP:
           if (state->steps >= 2 || MapObject_CheckCollisionInDirection(object, direction)) {
               direction = GetOppositeDirection(direction);
               state->steps = 0;
           }
           if (MapObject_CheckCollisionInDirection(object, direction)) {
               break; // boxed in: try again next frame
           }
           MapObject_ForceSetHeldMovement(object, GetMovementForDirection(direction, MOVEMENT_STEP_UP));
           MapObject_SetSingleMovement(object);
           state->state = PACE_WAIT_STEP;
           // fallthrough
       case PACE_WAIT_STEP:
           if (MapObject_RunForcedMovement(object)) {
               MapObject_ClearSingleMovement(object);
               state->steps++;
               state->state = PACE_START_STEP;
           }
           break;
       }
   }

   const MapObjectMovementCallbacks gPaceMovementCallbacks = {
       MOVEMENT_TYPE_PACE,
       PaceMovement_Init,
       PaceMovement_Update,
       MapObjectMovement_NoOpDelete,
       MapObjectMovement_NoOpRestore,
   };
   ```

4. **Append** `.word gPaceMovementCallbacks` after the last entry of
   `gMapObjectMovementCallbacks` (`sFollowPlayer56MovementCallbacks`) in
   `asm/map_object_movement_tables.s`, and `.public gPaceMovementCallbacks` to
   `asm/include/map_object_movement_tables.inc`.
5. Use it: `$M npc set <Map> <obj> movement_type=MOVEMENT_TYPE_PACE`.

The facing it starts with is the object's `facing_dir`. Slot 47 (`MOVEMENT_TYPE_INVALID_47`)
is an empty entry (`.word 0`). Don't reuse it unless you also rename it:
[npcs-and-scripts.md](npcs-and-scripts.md#movement-types) says it is rejected.

This movement code, the tables and the sprite data are all in static ARM9
(`main.lsf`), so they work on every map. They add to ARM9's size
([engine.md §5](engine.md#5-overlays)).

## Where to look

| To change | Look in |
|---|---|
| which file a sprite uses, its shadow and drawing | `gObjectEventGraphicsInfos`, `gSpriteEffectFlags`, `gMapObjectDrawCallbacks` in [asm/overlay_01_sprite_data.s](../../asm/overlay_01_sprite_data.s) |
| a sprite's pixels | `mapkit sprite export` / `import` ([tools/mapkit/mapkit/sprites.py](../../tools/mapkit/mapkit/sprites.py)) |
| how billboards are loaded and animated | [src/field/map_object_render.c](../../src/field/map_object_render.c), [src/field/map_object_billboard_motion.c](../../src/field/map_object_billboard_motion.c) |
| a movement action | its `MapObjectMovementCmdNNN_Step*` in [src/map_object_movement_commands.c](../../src/map_object_movement_commands.c) |
| a movement type | [src/map_object_movement.c](../../src/map_object_movement.c) |
| where a sprite or movement type is used | `$M refs SPRITE_X`, `$M refs MOVEMENT_TYPE_X` |
