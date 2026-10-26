<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# How the engine works

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers what runs underneath every screen: the boot sequence, the main loop and
its frame rate, the two kinds of tasks, overlays (code that is loaded only while it is
needed), and heaps (how memory is allocated). [ui.md](ui.md) builds on this: it covers
applications, graphics and menus.

If you know pokeemerald:

| pokeemerald | here |
|---|---|
| `SetMainCallback2(CB2_...)` | `RegisterMainOverlay(overlay, &template)`: the next top-level **application** (§2) |
| `CreateTask(func, priority)`, `gTasks[16]`, `data[16]` | `SysTask_CreateOnMainQueue(func, data, priority)`: up to 160, with a `void *` to your own struct (§3) |
| `ScriptContext`, `LockPlayerFieldControls` | a **field task** (`FieldSystem_CreateTask`): one chain, and the player can't move while it runs (§4) |
| `SetVBlankCallback`, `SetHBlankCallback` | `Main_SetVBlankIntrCB`, `Main_SetHBlankIntrCB` (§1) |
| everything is in ROM and always callable | most code is in **overlays** and can only be called while its overlay is loaded (§5) |
| `Alloc` / `AllocZeroed` / `Free` from one heap | `Heap_Alloc(heapID, size)` / `Heap_Free` from one of many **heaps** (§6) |
| 60 frames per second | game logic runs at **30**; a few jobs run at 60 (§1) |

## 1. The main loop

`NitroMain` in [src/main.c](../../src/main.c) initializes the system and then loops
forever. A pass through the loop:

```
ReadKeypadAndTouchpad()                      buttons and touch -> gSystem
soft reset check (START+SELECT+L+R)
Comm_Update()                                wireless / Wi-Fi
Main_RunOverlayManager()                     the current application (one frame of it)
SysTaskQueue_RunTasks(mainTaskQueue)         main SysTasks
SysTaskQueue_RunTasks(printTaskQueue)        text printers
if no VBlank has happened yet: wait for one
GF_RTC_UpdateOnFrame(), IGTCounter_Update()  clock and play time
Handle3DBufferSwapRequest()
SysTaskQueue_RunTasks(printTaskQueue)        text printers again
wait for the next VBlank
brightness and fade steps
gSystem.vBlankIntr(arg)                      the screen's VBlank callback
DoSoundUpdateFrame()
SysTaskQueue_RunTasks(vwaitTaskQueue)        "after VBlank" SysTasks
```

Separately, the **VBlank interrupt** itself (`VBlankCB_DmaTasksFramecounter` in
[src/system.c](../../src/system.c)) runs every 1/60 s. It waits for DMA, runs the
VBlank SysTask queue and increments `gSystem.frameCounter`.

Each pass waits for VBlank twice, so it takes at least two frames. That sets the speed of
everything:

| Runs at | What |
|---|---|
| 30 per second (once per pass) | the application's `init`/`exec`/`exit`, main SysTasks, the VBlank callback, sound, VWait SysTasks |
| 60 per second | VBlank-queue SysTasks (in the interrupt), text printers (twice per pass) |

When an application counts "frames" (`timer < 30` and so on), those are passes of 1/30 s.
If one pass of work takes longer than a frame, the first wait is skipped, so the game
slows down instead of skipping frames.

**The VBlank callback is not an interrupt handler.** `Main_SetVBlankIntrCB` stores a
function that the main loop calls just after VBlank starts. Use it to copy prepared data
into VRAM and OAM (see [ui.md §2](ui.md#2-one-frame)). Only one can be installed at a
time, and a new screen replaces the old one's. The VBlank **SysTask queue** does run
inside the interrupt, so it must not allocate memory or create heaps.

**HBlank** (between scanlines, for raster effects such as wavy screens):
`Main_SetHBlankIntrCB(cb, arg)` runs in the interrupt. It returns `FALSE` and does
nothing if a callback is already installed. Remove it with
`Main_SetHBlankIntrCB(NULL, NULL)` before your screen ends.
[scanline-effects.md](scanline-effects.md) covers HBlank effects in full, including HBlank
DMA and the field's shared `HBlankSystem`.

**System-wide switches** in `gSystem` ([include/system.h](../../include/system.h)). The
first two take bit flags, so several systems can each hold one; pick a bit nobody else
uses:

| Call | Effect |
|---|---|
| `Sys_SetSoftResetDisableFlag(bit)` / `Sys_ClearSoftResetDisableFlag(bit)` | turn off the START+SELECT+L+R reset (the link code uses bit 1) |
| `Sys_SetSleepDisableFlag(bit)` / `Sys_ClearSleepDisableFlag(bit)` | closing the lid only turns the backlight off instead of sleeping (wireless uses bit 4) |
| `SetKeyRepeatTimers(cont, start)` | held-button repeat speed for `gSystem.newAndRepeatedKeys` |

## 2. Boot and the top-level applications

`NitroMain` sets up, in order: the hardware and file system, the heaps and SysTask
queues (`InitSystemForTheGame`), VRAM, input, the clock, three fonts, an empty
`SaveData` (filled by loading the save), sound, and then the first application.

At any moment one **main application** is running. It is an `OverlayManagerTemplate`
(`init`/`exec`/`exit`, see [ui.md §1](ui.md#1-applications)) started with:

```c
RegisterMainOverlay(FS_OVERLAY_ID(intro_title), &gApplication_TitleScreen);
```

The first argument is an overlay to keep loaded while the application runs
(`FS_OVERLAY_ID_NONE` for none). Usually the outgoing application registers its successor
in its `exit`, and the next one starts on the following frame. Only one can be queued at
a time (a second call asserts). The chain from power-on:

```
intro movie  ->  title screen  ->  save check  ->  main menu (OVY_74)
                    ^                                   |  Continue / New Game
                    |                                   v
                    |               OVY_36  ->  (Oak's speech, new game only)
                    |                                   v
                    +----------  the field system  (gApplication_ContinueFieldsys / _NewGameFieldsys)
```

Where each step is registered:

| Step | Registered in |
|---|---|
| intro → title | [src/intro_movie.c](../../src/intro_movie.c) |
| title → save check, delete save, mic test, intro | [src/title_screen.c](../../src/title_screen.c) |
| save check → main menu | [src/application/check_savedata.c](../../src/application/check_savedata.c) |
| main menu → each option | [src/application/main_menu/main_menu.c](../../src/application/main_menu/main_menu.c) |
| → Oak's speech or the field | [src/overlay_36.c](../../src/overlay_36.c), [src/oaks_speech.c](../../src/oaks_speech.c) |
| field → title (only after the field system ends) | `Field_AppExit`, [src/field_system.c](../../src/field_system.c) |

`OS_GetResetParameter()` picks the first application: 0 (power-on) plays the intro; 1
(reset after a communication error) skips straight to Continue.

**The field system is one main application that never ends** during normal play. Battles,
the bag, the Pokédex and everything else run as *its* children
([ui.md: launching](ui.md#launching-an-application)). Its `exec`, `FieldSystem_Main`,
does three things each frame:

1. `FieldSystem_Control`: if the player may move, read field input, start events
   (talking, warps, the start menu) and move the player.
2. `FieldSystem_RunTaskFrame`: run the current field task, if any (§4).
3. Run **either** the overworld map application (`processManager->parent`) **or** a
   child screen (`processManager->child`), never both. A child only starts after the map
   has closed.

The player can move only when no field task is running, the map is running, and the
field isn't paused (`FieldSystem_IsPlayerMovementAllowed`).

## 3. SysTasks

A SysTask is a function the main loop calls every frame until you destroy it. Use one for
anything that should keep running alongside other code: an animation, a fade, a cursor
blink, a sprite that follows another. Its signature
([include/sys_task.h](../../include/sys_task.h)):

```c
typedef void (*SysTaskFunc)(SysTask *task, void *data);
```

There are four queues, made in `InitSystemForTheGame`:

| Create with | Slots | Runs | Use it for |
|---|---|---|---|
| `SysTask_CreateOnMainQueue` | 160 | each pass, after the application | almost everything (285 uses) |
| `SysTask_CreateOnVWaitQueue` | 32 | each pass, after the VBlank callback | work that must follow the VRAM copy, e.g. queuing next frame's transfer (68 uses) |
| `SysTask_CreateOnVBlankQueue` | 32 | 60 times a second, **inside the interrupt** | short register or VRAM writes that must land during VBlank (52 uses) |
| `SysTask_CreateOnPrintQueue` | 4 | twice per pass | text printers (`text.c`); leave it to them |

The headers are [include/sys_task_api.h](../../include/sys_task_api.h) and
[include/systask_environment.h](../../include/systask_environment.h).

**Priority.** Lower numbers run first. Tasks with the same priority run in the order
they were created. A task created while its queue is running starts on the next frame,
not later in the same pass.

**Data.** The queue stores only your pointer. `SysTask_Destroy` does **not** free it. The
helpers allocate it for you (zeroed) and free it with the task:

```c
typedef struct BlinkTask {
    Window *window;
    int timer;
} BlinkTask;

static void Task_Blink(SysTask *task, void *data) {
    BlinkTask *blink = data;

    if (++blink->timer >= 60) {
        DestroySysTaskAndEnvironment(task); // frees `blink` too; safe inside the task itself
        return;
    }
    // ... toggle the window every few frames ...
}

SysTask *task = CreateSysTaskAndEnvironment(Task_Blink, sizeof(BlinkTask), 10, HEAP_ID_MY_APP);
BlinkTask *blink = SysTask_GetData(task);
blink->window = &data->windows[0];
```

Other calls: `SysTask_SetFunc(task, func)` switches the function (a simple state
machine), and `SysTask_GetPriority(task)` reads the priority back.

**Rules:**

- Destroy every task you created before your screen's heap is destroyed. A task left
  behind keeps running with a pointer into freed memory.
- A full queue returns `NULL`. Check for it if your screen creates many tasks.
- SysTasks keep running while the screen changes. Most screens own their tasks and
  destroy them in `exit`. A task that should outlive a screen must keep its data in a heap
  that outlives that screen.

## 4. Field tasks

The field has its own, separate kind of task: a `TaskManager`
([include/task.h](../../include/task.h), [src/task.c](../../src/task.c)). Field tasks are
for **events**: something that takes over from the player for a while. Every script runs
as one (`Task_RunScripts` in [src/script_manager.c](../../src/script_manager.c)), and so do
warps, battles started from the field, the start menu and its screens, and Fly.

```c
typedef BOOL (*TaskFunc)(TaskManager *taskman);   // return TRUE when finished
```

The differences from SysTasks:

| | SysTask | field task |
|---|---|---|
| how many | many, in parallel | **one chain**, a call stack |
| player movement | unaffected | blocked while any field task exists |
| exists | always | only while the field system runs |
| state | your own data | `*TaskManager_GetStatePtr(taskman)` (starts at 0) plus an `env` pointer |
| memory | your heap | the task record is in `HEAP_ID_FIELD3` (16 KB) |

The calls:

| Call | Effect |
|---|---|
| `FieldSystem_CreateTask(fieldSystem, func, env)` | start a chain. **Only when none is running**: it asserts, and then replaces the running task |
| `TaskManager_Call(taskman, func, env)` | push `func`. The current task resumes after `func` returns `TRUE` |
| `TaskManager_Jump(taskman, func, env)` | replace the current task's function, state reset to 0 |
| `CallApplicationAsTask(taskman, &template, args)` | push a task that launches a screen and waits until it closes |
| `FieldSystem_TaskIsRunning(fieldSystem)` | is any field task running? |

When a task returns `TRUE`, it is freed and its caller runs again **in the same frame**.

A task that opens a screen and returns to the map (fades left out; see
[ui.md](ui.md#launching-an-application) for the full start-menu version):

```c
static BOOL Task_ShowMyScreen(TaskManager *taskman) {
    FieldSystem *fieldSystem = TaskManager_GetFieldSystem(taskman);
    u32 *state = TaskManager_GetStatePtr(taskman);

    switch (*state) {
    case 0:
        CallApplicationAsTask(taskman, &sMyAppTemplate, TaskManager_GetEnvironment(taskman));
        (*state)++;
        break;
    case 1: // the screen has closed; the map is not running
        FieldSystem_LoadFieldOverlay(fieldSystem);
        (*state)++;
        break;
    case 2:
        if (FieldSystem_IsOverworldRestored(fieldSystem)) {
            return TRUE;
        }
        break;
    }
    return FALSE;
}
```

From a script, don't create a field task: one (the script) is already running. Use
`TaskManager_Call` on the script's task (`fieldSystem->taskman`), or make the script
command wait with `SetupNativeScript` (see [npcs-and-scripts.md](npcs-and-scripts.md)
and [ui.md](ui.md#launching-an-application)).

## 5. Overlays

The DS loads the ARM9 program ("static", always in RAM) from the cartridge at boot.
Everything else is in **overlays**: blocks of code and data, each linked to a fixed RAM
address and copied from the ROM when loaded. HeartGold has 129 of them. Two overlays
whose address ranges overlap cannot both be loaded, and calling into an overlay that isn't
loaded runs whatever bytes happen to be at that address.

### The layout

[main.lsf](../../main.lsf) lists every overlay and the object files in it. `After X`
places an overlay right where `X` ends, so overlays form a tree. Siblings (overlays with
the same parent) share an address and replace each other. From the HeartGold US build
(`build/heartgold.us/main.nef.xMAP`):

```
0x02000000  static ARM9 (main) ............................. 0x021E5900
0x021E5900  +- field (overworld map)  385 KB
            |    +- OVY_2 (field effects, encounters, phone)  57 KB
            |         +- OVY_3 (marts, Safari, most maps)  or  OVY_4 (gym puzzles)
            |              +- npc_trade, bug_contest, OVY_19-26 (field extras)
            |                   +- OVY_27 (touch menus) +- OVY_31 ...
            +- OVY_0 (Wi-Fi libraries)  216 KB
            |    +- OVY_6 +- OVY_7 (battle animations) +- OVY_12 (battle)  ... 0x0226EC40
            |           +- OVY_8 (battle party menu)
            |           +- OVY_10 (trainer AI)
            +- intro_title, OVY_14 (PC) + OVY_15 (bag), options_app, pokegear,
               trainer_card, OVY_61 (starter), credits, ... (every full screen)
0x0226EC40  heaps start here (end of the longest chain: the battle)
0x023E0000  end of main RAM
```

This layout explains two things the game does:

- **A screen closes the map before it opens.** Most screens sit "After main", at the
  same address as `field`. The map overlay must be unloaded first.
- **Field-only extras sit after `OVY_3`** (the NPC trade, the Bug Contest, Pokéathlon
  records), so they can be loaded while the map is running.

The battle shows how siblings are swapped by hand. `OVY_7` (animations), `OVY_8` (the
party menu and bag) and `OVY_10` (trainer AI) all start after `OVY_6`, so only one is in
RAM at a time. The battle swaps `OVY_7` and `OVY_10` as it needs them, and opening a menu
unloads whichever one is loaded, loads `OVY_8`, and reverses that afterwards
(`BattleSystem_FreeInputForSubMenu` / `BattleSystem_RestoreInputAfterSubMenu` in
[src/battle/battle_022378C0.c](../../src/battle/battle_022378C0.c)).

To print every overlay's range, use the `SDK_OVERLAY.<name>.START` and `.BSS_END`
symbols in the `.xMAP`:

```sh
grep -E 'SDK_OVERLAY\.[A-Za-z0-9_]+\.(START|BSS_END) ' build/heartgold.us/main.nef.xMAP
```

### Loading and unloading

[include/poke_overlay.h](../../include/poke_overlay.h):

```c
FS_EXTERN_OVERLAY(my_app);                                 // at the top of the .c file
HandleLoadOverlay(FS_OVERLAY_ID(my_app), OVY_LOAD_ASYNC);  // load; runs its static initializers
UnloadOverlayByID(FS_OVERLAY_ID(my_app));
```

Usually you don't call these. An application's template names its overlay, and
`OverlayManager_Run` loads it before `init` and unloads it after `exit`. The field map
application loads and unloads `OVY_2`/`OVY_3`/`OVY_4` itself
([src/field/fieldmap.c](../../src/field/fieldmap.c)).

**Rules:**

- **A load that overlaps a loaded overlay does nothing.** `HandleLoadOverlay` returns
  `FALSE` without loading or printing anything. Your code is then not in RAM, and the
  first call into it crashes. When a new screen crashes at once, check this first.
- At most 8 overlays can be loaded at once (in main RAM; ITCM and DTCM have 8 each).
- Static ARM9 code can call into an overlay, but only while it is loaded. It is safer to
  call from the overlay out to static code, which is always there.
- **Pointers into an overlay die with it.** That includes `const` tables, strings and
  templates. If something that outlives the overlay keeps such a pointer (a SysTask, a
  field task, the args of a screen launched from it), copy the data to a heap first, or
  put it in static ARM9.

### Adding to or growing an overlay

The steps for a new overlay are in [ui.md](ui.md#adding-a-new-application). To choose
its parent:

| Your code runs | Put it |
|---|---|
| as a full screen that replaces the map | `After main` (like `options_app`) |
| while the map is open (a field effect, a script command's helper) | after `OVY_3`, next to `npc_trade` |
| inside a battle | in `OVY_12`'s chain, keeping clear of the `OVY_7`/`OVY_8`/`OVY_10` swap |
| from anywhere, small | static ARM9 (`FS_OVERLAY_ID_NONE`) |

**Watch the end address.** Main RAM ends at `0x023E0000`, and the heaps are carved from
whatever is left after the longest overlay chain, today the battle ending at `0x0226EC40`.
That leaves 0x1713C0 bytes, and the four fixed heaps (§6) take 0x14D810, so the spare
room is under 0x23BB0 (about 140 KB). It is less in practice, because the heap tables,
SysTask queues and file table come out of the same space. Two kinds of change use it up:

- **anything added to static ARM9**, which moves every overlay up;
- **anything added to an overlay on the longest chain** (`OVY_0`, `OVY_6`, `OVY_7`,
  `OVY_12`).

An overlay that grows past its siblings' ends, or a chain that ends past `0x0226EC40`,
pushes the heaps up. When they no longer fit, the game breaks at boot. Code added to an
overlay that isn't on the longest chain is free until its chain becomes the longest.

## 6. Heaps

There is no single `malloc`. Memory comes from numbered **heaps**
([include/heap.h](../../include/heap.h), [src/heap.c](../../src/heap.c), ids in
[include/constants/heap.h](../../include/constants/heap.h)).

### The fixed heaps

Created at boot from main RAM (`sDefaultHeapSpec` in [src/system.c](../../src/system.c)):

| Id | Size | Holds |
|---|---|---|
| `HEAP_ID_DEFAULT` (0) | 0xD200 (52 KB) | small long-lived things: application managers, the CRC table |
| `HEAP_ID_1` | 0x23600 (141 KB) | the save data (`SaveData`) |
| `HEAP_ID_2` | 0x10 | nothing |
| `HEAP_ID_3` | 0x11D000 (1.1 MB) | the parent of nearly every other heap (137 of 160 `Heap_Create` calls) |

Every other id is a **child heap**, created inside a parent for as long as a screen or
system needs it:

```c
Heap_Create(HEAP_ID_3, HEAP_ID_MY_APP, 0x30000);   // parent, new id, size; from the parent's start
Heap_CreateAtEnd(HEAP_ID_3, HEAP_ID_MY_APP, 0x30000); // the same, from the parent's end
...
Heap_Destroy(HEAP_ID_MY_APP);
```

At most **24 child heaps** can exist at once, and a heap id must stay below 256. To add
an id, add a name before `HEAP_ID_MAX` in `constants/heap.h`.

### Allocating

| Call | Notes |
|---|---|
| `Heap_Alloc(heapID, size)` | from the low end. **Not zeroed**: follow with `MI_CpuFill8(p, 0, size)` or `memset` |
| `Heap_AllocAtEnd(heapID, size)` | from the high end. The game uses it for short-lived things (launch args, field tasks) so they don't split up the low end |
| `Heap_Free(ptr)` | the heap is found from a 16-byte header before each block |
| `Heap_Realloc(ptr, newSize)` | **can only shrink** |
| `HeapExp_FndGetTotalFreeSize(heapID)` | bytes free, for checking your budget |

Each block is 4-byte aligned and costs its size plus the game's 16-byte header plus the
NitroSDK heap's own block header. Many tiny allocations add up.

**Running out returns `NULL`.** The game doesn't check, and outside a link session nothing
reports it (see the note on asserts below), so the crash happens later, wherever the
pointer is first used.

**`Heap_Destroy` frees everything left in the heap at once.** Screens rely on it: a
screen that creates its heap in `init` and destroys it in `exit` cannot leak past itself.
The cost is that any pointer into that heap held by something else (a SysTask, the caller's
args, a sprite system) is now dangling.

### The field's memory budget

The field system creates its heaps out of `HEAP_ID_3`:

| Heap | Size | Lives | Holds |
|---|---|---|---|
| `HEAP_ID_FIELD2` | 0x1C000 (112 KB) | the whole field system | `FieldSystem`, child screens' managers and launch args |
| `HEAP_ID_FIELD3` | 0x4000 (16 KB) | the whole field system | field tasks |
| `HEAP_ID_FIELD1` | 0xC4000 (784 KB) on normal maps (`fieldHeapSize` in `sMapLoadModes`, [src/field_warp_tasks.c](../../src/field_warp_tasks.c)) | **only while the map is open** | map, 3D, sprites, events |

With the map open, at most 0x39000 bytes (228 KB) of `HEAP_ID_3` are free. With it
closed there are 0xFD000 (about 1 MB), and the battle's heap alone is 0xB0000. That is
why screens close the map: it frees memory as well as the overlay address. A small helper
that must run *with* the map open (a field effect, a small window) has to fit in about
200 KB. Allocate from `HEAP_ID_FIELD1` if it should disappear with the map, or from
`HEAP_ID_FIELD2` if it must survive a screen change.

### Asserts

`GF_ASSERT` is compiled in (`-DPM_KEEP_ASSERTS` in [meson.build](../../meson.build)), but
`GF_AssertFail` ([src/error_handling.c](../../src/error_handling.c)) acts only during a
wireless or Wi-Fi session, where it shows the error screen and resets. In single-player
it **returns and the game carries on**. A failed assert, such as a heap that didn't fit, a
second field task, or a duplicate heap id, gives no message. To catch these while
developing, put a breakpoint on `GF_AssertFail` in an emulator with a debugger
(melonDS, DeSmuME). Its caller is the failing check.

## Where to look

| Topic | File |
|---|---|
| boot, main loop, soft reset, lid | [src/main.c](../../src/main.c) |
| `gSystem`, interrupts, the fixed heaps, input | [src/system.c](../../src/system.c), [include/system.h](../../include/system.h) |
| SysTasks | [src/sys_task.c](../../src/sys_task.c), [src/sys_task_api.c](../../src/sys_task_api.c), [src/systask_environment.c](../../src/systask_environment.c) |
| applications | [src/overlay_manager.c](../../src/overlay_manager.c) |
| overlays | [src/poke_overlay.c](../../src/poke_overlay.c), [main.lsf](../../main.lsf), `build/heartgold.us/main.nef.xMAP` |
| heaps | [src/heap.c](../../src/heap.c), [include/constants/heap.h](../../include/constants/heap.h) |
| the field system, its heaps and frame | [src/field_system.c](../../src/field_system.c) |
| field tasks | [src/task.c](../../src/task.c) |
| the map opening and closing | [src/field/fieldmap.c](../../src/field/fieldmap.c) |
| a battle swapping overlays | [src/battle/battle_022378C0.c](../../src/battle/battle_022378C0.c) |
