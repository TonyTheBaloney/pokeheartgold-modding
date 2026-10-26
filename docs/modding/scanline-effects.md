<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Scanline (HBlank) effects

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This guide covers effects that change a display register between scanlines, so that each
line of the screen is drawn differently: waves, wipes, ripples, the poison shudder,
line-by-line masks. [engine.md](engine.md) covers the main loop and interrupts they build
on; [ui.md](ui.md) covers backgrounds and windows.

If you know pokeemerald (`src/scanline_effect.c`):

| pokeemerald | here |
|---|---|
| `ScanlineEffect_SetParams` + `gScanlineEffectRegBuffers[2][960]`, DMA every HBlank | `ScanlineEffect` / `HBlankDma_Start`: a 192-entry double buffer, DMA every HBlank (§2) |
| `ScanlineEffect_InitWave` | `ScanlineEffect_StartWave` (§2) |
| `ScanlineEffect_InitHBlankDmaTransfer` in the VBlank callback | `ScanlineEffect_RestartDma` from a VBlank-queue SysTask (§2) |
| `SetHBlankCallback` | `Main_SetHBlankIntrCB` (§3), **one at a time** |
| none | the field's `HBlankSystem`: two HBlank callbacks at once while the map is open (§4) |

## 1. Two ways to change a register per line

The DS draws each screen top to bottom, 192 visible lines. Between two lines there is a
short pause, **HBlank**. Anything written to a display register during HBlank applies to
the lines below it. There are two ways to do that:

| | HBlank DMA (§2) | HBlank interrupt (§3, §4) |
|---|---|---|
| what runs | the DMA controller copies the next table entry to a register | your function, in an interrupt, once per line |
| CPU cost | none per line | an interrupt for each of the 192 lines |
| can do | write 4 (or 8) bytes per line to one fixed address: BG offsets, affine parameters | anything short: several registers, conditions, windows |
| used by | waves in battle animations, encounter effects and Battle Frontier transitions; card scrolls in the main menu | the poison shudder, encounter wipes, screen fades with masks, the battle menu slide, Easy Chat, Plaza games, the intro's circle wipe |

Both need a **per-line table** that is filled during the frame and **double-buffered**:
the DMA or interrupt reads one buffer while the game writes the other, and they swap once
per frame. The helper for that is `DoubleBuffer`
([include/scanline_effect.h](../../include/scanline_effect.h)):

| Call | Effect |
|---|---|
| `DoubleBuffer_New(heap, a, b)` | wrap two buffers you own |
| `DoubleBuffer_GetCurrent(db)` | the one to **write** this frame |
| `DoubleBuffer_GetOther(db)` | the one being **shown** |
| `DoubleBuffer_Swap(db)` | swap them (does nothing while disabled) |
| `DoubleBuffer_SetEnabled(db, 0/1)` | hold the swap, for example until the first table is ready |

**Line timing.** The HBlank after line *N* is when line *N + 1* is prepared. HBlank
callbacks read the current line with `GX_GetVCount()` and write the value for the **next**
line, wrapping 191 → 0. `PoisonEffect_ApplyNextLineOffset`, `LineMask_HBlankCallback` and
`ScreenWipeScanlines_HBlankCallback` all do this. HBlank DMA copies one entry per HBlank
from the start of the table, which it is restarted at in VBlank. So entry *i* takes effect
one line below line *i*. That is invisible for waves, but matters for a sharp edge.

## 2. HBlank DMA: `ScanlineEffect`

[src/scanline_effect.c](../../src/scanline_effect.c). The DMA copies one `u32` per line from
the shown buffer to `destination`. Pointed at a **BG offset register**
(`REG_BGnHOFS_ADDR`), one write sets both the horizontal (low 16 bits) and vertical (high
16 bits) offset, because `BGnHOFS` and `BGnVOFS` are next to each other. A wave is that
offset changing line by line.

```c
typedef struct ScanlineEffect {
    u32 buffers[2][192];        // one u32 per line: (y << 16) | x
    DoubleBuffer *doubleBuffer;
    SysTask *task;              // the wave task
    s16 wave[192];              // precomputed sine values
    u8 first, last;             // lines the wave applies to
    void *destination;          // the register
    u32 fill;                   // value for every line before the wave is added
    s16 phase, speed;           // position in the wave, in hundredths of a line
} ScanlineEffect;
```

### The calls

| Call | Does |
|---|---|
| `ScanlineEffect_New(heap)` | allocate (≈2 KB) |
| `ScanlineEffect_StartWave(effect, first, last, step, amplitude, speed, destination, fill, priority)` | build the sine table and start the wave task on the main SysTask queue at `priority` |
| `ScanlineEffect_SwapBuffers(effect)` | swap, and refill the new write buffer with `fill` |
| `ScanlineEffect_RestartDma(effect)` | stop DMA 0 and start it again from line 0 of the shown buffer |
| `ScanlineEffect_GetBuffer(effect)` | the write buffer, to fill your own table instead of a wave |
| `ScanlineEffect_Stop(effect)` | stop the wave task and fill the write buffer with `fill` |
| `ScanlineEffect_Delete(effect)` | stop the task and the DMA, free it |

The wave parameters:

- `step`: how far the sine angle moves per line, in `FX_SinIdx` units (0x10000 = a full
  turn). 0x2AA gives one wave every 96 lines.
- `amplitude`: the peak offset in pixels, as `fx32` (0x1000 = 1 pixel; 0x12000 = 18).
- `speed`: how many hundredths of a line the wave moves each main-loop pass (30 per
  second). 400 = 4 lines per pass. Negative moves it the other way.
- `fill`: the base value for every line, `(y << 16) | x`. The wave is added to the low
  half (x) only, so a `ScanlineEffect` wave is always horizontal.

### The per-frame driver

`ScanlineEffect` doesn't drive its own swap and DMA restart. Every user adds a small
SysTask that does it in VBlank, so the DMA starts from line 0 of a complete table. The
field's version ([src/field/encounter_effect_particles.c](../../src/field/encounter_effect_particles.c)):

```c
static void Task_EncounterEffectHBlankWave(SysTask *task, void *data) {   // on the VBlank queue
    EncounterEffectHBlankWave *wave = data;
    if (wave->frames >= 2) {
        ScanlineEffect_SwapBuffers(wave->effect);   // the wave task has written a full table
        wave->frames = 0;
    }
    ScanlineEffect_RestartDma(wave->effect);        // every VBlank: start again at line 0
    wave->frames++;
}
```

The VBlank queue runs 60 times a second, but the wave task runs once per main-loop pass
(30 times a second, [engine.md §1](engine.md#1-the-main-loop)). So the field version swaps
every second VBlank and restarts the DMA every VBlank. The DMA must restart each frame
because it advances one entry per line and would otherwise run off the end of the table.

The other wrappers do the same with different tasks:

- the battle's `BattleAnimScanline_*` in
  [src/battle/battle_anim_util.c](../../src/battle/battle_anim_util.c) uses a VWait-queue
  task to swap and a VBlank-queue task to restart;
- the Frontier's `FrontierScanline_*` in
  [src/frontier/frontier_transition.c](../../src/frontier/frontier_transition.c).

### Example: a wave on BG3

```c
typedef struct MyWave {
    ScanlineEffect *effect;
    SysTask *task;
    u8 frames;
} MyWave;

static void Task_MyWave(SysTask *task, void *data) {
    MyWave *wave = data;
    if (wave->frames >= 2) {
        ScanlineEffect_SwapBuffers(wave->effect);
        wave->frames = 0;
    }
    ScanlineEffect_RestartDma(wave->effect);
    wave->frames++;
}

void MyWave_Start(MyWave *wave, enum HeapID heapID) {
    wave->effect = ScanlineEffect_New(heapID);
    wave->frames = 0;
    wave->task = SysTask_CreateOnVBlankQueue(Task_MyWave, wave, 1024);
    // lines 0-191, one wave per 96 lines, 8 px, moving 2 lines per pass; base offset (0, 0)
    ScanlineEffect_StartWave(wave->effect, 0, 191, 0x2AA, 0x8000, 200, (void *)REG_BG3HOFS_ADDR, 0, 1024);
}

void MyWave_Stop(MyWave *wave) {
    SysTask_Destroy(wave->task);
    ScanlineEffect_Stop(wave->effect);
    ScanlineEffect_Delete(wave->effect);   // also stops the DMA
    G2_SetBG3Offset(0, 0);                 // the register keeps the last value the DMA wrote
}
```

**Use `fill` for the BG's normal scroll.** While the DMA runs, it overwrites the offset
register on every line, so the BG's usual scroll (`BgSetPosTextAndCommit`, or the
`BgConfig` scroll) is overwritten too. Put the scroll you want into `fill`, or write it
into each table entry.

### Your own table

To do something other than a sine wave, skip `StartWave`. Write the 192 values into the
write buffer each frame (`ScanlineEffect_GetBuffer`, or your own `DoubleBuffer`), then swap
and restart the DMA in VBlank. The main menu's card scroll does this with a 2-word entry per
line (`HBlankDma_Start(buffer, REG_BG0HOFS_ADDR, 8, 1)` sets BG0's and BG1's offsets
together; [src/application/main_menu/lock_capsule_card.c](../../src/application/main_menu/lock_capsule_card.c)).

The low-level calls are `HBlankDma_Start(src, dst, bytesPerLine, wide)` and
`HBlankDma_Stop()`. `wide` 1 uses 32-bit transfers, 0 uses 16-bit ones.
`ScanlineEffect_StartDma` also flushes the data cache over the buffer first
(`DC_FlushRange`). Do the same before pointing the DMA at a buffer the CPU just wrote:
the DMA reads memory, not the cache.

The Battle Frontier points it at `REG_BG2PA_ADDR` (an affine BG's matrix) for per-line
scaling (`FrontierHBlankDma_New`,
[src/frontier/frontier_script_commands_ext.c](../../src/frontier/frontier_script_commands_ext.c)).

### Limits

- **One HBlank DMA at a time.** All of them use DMA channel 0. `ScanlineEffect_RestartDma`
  stops whatever is on it before starting its own, so two effects running together
  overwrite each other every frame. The game uses channel 1 for the file system and 3
  for graphics transfers (`GX_DEFAULT_DMAID`), so channel 0 is the free one.
- One destination per table. To change two registers, they must be next to each other
  (one 8-byte entry, as the card scroll does), or use an HBlank callback.
- The 3D layer (BG0 when 3D is on, as in the overworld) isn't scrolled by `BG0HOFS`. Use
  `G3X_SetHOffset` from an HBlank callback instead, as the poison effect does (§4).

## 3. HBlank interrupt: `Main_SetHBlankIntrCB`

[src/system.c](../../src/system.c):

```c
BOOL Main_SetHBlankIntrCB(GFIntrCB cb, void *arg);   // FALSE if one is already installed
Main_SetHBlankIntrCB(NULL, NULL);                    // remove it and turn the interrupt off
HBlankInterruptDisable();                            // the same, unconditionally
```

Installing turns on the HBlank interrupt. Your function then runs in the interrupt after
**every** line, including the invisible ones (`GX_GetVCount()` 192-262), so check the line
first. The rules:

- **Be short.** HBlank lasts only a few microseconds. Read a precomputed table and write
  a register. Don't compute, allocate, print or call anything slow. Creating,
  destroying or resizing a heap asserts in an interrupt.
- **Write the next line's value.** Use `GX_GetVCount() + 1`, wrapped (§1). The poison
  effect also checks it is still in HBlank (`reg_GX_DISPSTAT & REG_GX_DISPSTAT_HBLK_MASK`)
  before writing. `LineMask` uses `GX_IsHBlank()`.
- **There is only one slot.** `Main_SetHBlankIntrCB` refuses while another callback is
  installed, and most code only `GF_ASSERT`s on that, which does nothing outside a link
  session ([engine.md](engine.md#asserts)). The second effect then silently doesn't
  run. Many screens call `HBlankInterruptDisable()` in their setup to start from a clean
  state.
- **Remove it before the data goes away.** It keeps firing until removed, even after your
  screen's heap is destroyed.

Systems that need more than one callback multiplex the slot:

- `FadeBlankPair` ([src/screen_fade.c](../../src/screen_fade.c)) runs one callback per
  screen, for fades with masks;
- the field's `HBlankSystem` runs two (§4).

## 4. In the field: `HBlankSystem`

While the overworld map is open, the field **holds the HBlank slot**. `FieldMap` creates an
`HBlankSystem` and starts it when the map loads, and deletes it when the map closes
([src/field/fieldmap.c](../../src/field/fieldmap.c)). Field code must therefore not call
`Main_SetHBlankIntrCB`. It adds a task to the field's system instead
([src/field/hblank_system.c](../../src/field/hblank_system.c)):

```c
HBlankTask *task = HBlankSystem_StartTask(fieldSystem->mapSystems->hBlankSystem, MyCallback, myData);
...
HBlankTask_Delete(task);
```

```c
typedef void (*HBlankTaskCallback)(HBlankTask *task, void *arg);
```

There are **two** task slots. Both callbacks run after every line. A third
`HBlankSystem_StartTask` returns `NULL`.

**Handing the slot over.** Effects that need `Main_SetHBlankIntrCB` themselves, such as a
palette fade with a mask, first call `HBlankSystem_Stop`, which uninstalls the field's
callback. When they finish they call `HBlankSystem_Start` to reinstall it. The wild
encounter flashes in [src/field/encounter_effect_wild.c](../../src/field/encounter_effect_wild.c)
do this around `BeginNormalPaletteFade`.

### Example: the poison shudder

[src/field/field_poison_effect.c](../../src/field/field_poison_effect.c) shakes the
overworld sideways in bands of 10 lines. It uses every piece:

| Piece | Queue | Does |
|---|---|---|
| `PoisonEffect_Task` | main SysTask | fills the write buffer: ±1-3 px, flipping sign every 10 lines, ramping up and down |
| `PoisonEffect_SwapBuffersTask` | VBlank SysTask | swaps the buffers and marks them ready |
| `PoisonEffect_VBlankResetTask` | VBlank SysTask | resets the offset to 0 for line 0 |
| `PoisonEffect_HBlankCallback` | field `HBlankSystem` task | on each line, `G3X_SetHOffset(shown[vcount + 1])` |

When it ends it deletes the HBlank task, destroys its SysTasks and sets the offset back
to 0 (`G3X_SetHOffset(0)`).

## 5. Window effects

Wipes and masks change the **window** registers per line instead of scrolling: each line
shows a different span of a window, which cuts a shape out of the screen. These are in
[src/screen_fade_effects.c](../../src/screen_fade_effects.c) and
[src/screen_wipe_effects.c](../../src/screen_wipe_effects.c), and run through
`FadeBlankPair`:

- `ScreenWipeScanlines` stores a left/right span per line for one or both windows.
- `LineMask` stores on/off flags per line.

Their HBlank callbacks write the next line's window position. The encounter wipes in
`src/field/encounter_effect_wipe.c` (stripes, split) and `encounter_effect_util.c`
(zigzag) do the same through the field's `HBlankSystem`.

## Checklist

- [ ] The table is double-buffered: write one, show the other, swap in VBlank.
- [ ] DMA effects restart the DMA every VBlank (`ScanlineEffect_RestartDma`).
- [ ] The cache is flushed over a buffer before the DMA reads it.
- [ ] HBlank callbacks write line `vcount + 1` and return quickly.
- [ ] In the field, use `HBlankSystem_StartTask`, not `Main_SetHBlankIntrCB`.
- [ ] On the way out: remove the HBlank task or callback, stop the DMA, destroy the
      SysTasks, then reset the register the effect was writing.

## Where to look

| Effect | File |
|---|---|
| `ScanlineEffect`, `DoubleBuffer`, HBlank DMA | [src/scanline_effect.c](../../src/scanline_effect.c) |
| the HBlank slot | `Main_SetHBlankIntrCB` in [src/system.c](../../src/system.c) |
| the field's two HBlank tasks | [src/field/hblank_system.c](../../src/field/hblank_system.c) |
| poison shudder (HBlank callback, 3D layer) | [src/field/field_poison_effect.c](../../src/field/field_poison_effect.c) |
| encounter waves (DMA) | [src/field/encounter_effect_particles.c](../../src/field/encounter_effect_particles.c) |
| encounter wipes (HBlank, windows) | [src/field/encounter_effect_wipe.c](../../src/field/encounter_effect_wipe.c), [src/field/encounter_effect_util.c](../../src/field/encounter_effect_util.c) |
| battle animation waves (DMA) | `BattleAnimScanline_*` in [src/battle/battle_anim_util.c](../../src/battle/battle_anim_util.c) |
| battle menu slide (HBlank) | `HBlankCB_BattleMenuSlideIn` in [src/battle/battle_input.c](../../src/battle/battle_input.c) |
| fades with masks, window wipes | [src/screen_fade.c](../../src/screen_fade.c), [src/screen_fade_effects.c](../../src/screen_fade_effects.c), [src/screen_wipe_effects.c](../../src/screen_wipe_effects.c) |
| card scroll (8-byte DMA) | [src/application/main_menu/lock_capsule_card.c](../../src/application/main_menu/lock_capsule_card.c) |
| per-line affine (DMA to `BG2PA`) | [src/frontier/frontier_script_commands_ext.c](../../src/frontier/frontier_script_commands_ext.c) |
