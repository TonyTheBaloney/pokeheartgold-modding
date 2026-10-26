<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Keeping saves compatible

> AI-generated; not affiliated with pret. See AI.md at the repository root.

[save-data.md](save-data.md) describes the save layout and what each change costs. This
guide is for a hack released in versions, where players should be able to keep their
save from one version to the next (or from retail HeartGold). It covers:

1. how the game decides whether a save is valid;
2. the two ways an update breaks a save: it stops loading, or it loads with the wrong meaning;
3. rules that keep both from happening;
4. free space you can use without changing the layout;
5. adding new saved data in the unused flash sectors (a new extra chunk), which old saves
   don't notice;
6. when the layout has to change: migrating old saves in the game or with a converter;
7. a version marker, and how to test.

If you know pokeemerald: there is no `SaveBlock` version field here either, and no
`gSaveBlock*` pointers to shuffle. The closest thing to pokeemerald's "free space at the
end of a save block" is §5, not the slack inside block 0.

## 1. What makes a save load

`SaveData_New` ([src/save.c](../../src/save.c)) calls `Save_GetSaveFilesStatus`, which reads
both copies of the main save and checks each **block** (block 0 = chunks 0–40, block 1 = the
PC) with `ValidateSaveSectorFooter`:

- the footer is read at `offset + size - 16`, where `offset` and `size` come from the
  **current build's** chunk sizes (`SaveData_InitSlotSpecs`);
- `footer->size` must equal the current build's block size;
- `footer->magic` must be `SAVE_CHUNK_MAGIC` (`0x20060623`);
- `footer->slot` must be the block number;
- the CRC-16 of the block (minus the footer) must match `footer->crc`.

If no block passes, the game treats it as no save or a corrupted one and starts fresh
(`LOAD_STATUS_NOT_EXIST` / `LOAD_STATUS_TOTAL_FAIL`). Nothing inside a block is checked
chunk by chunk when loading: the 4 bytes added after each chunk (`GetSaveChunkSizePlusCRC`)
are not compared with anything stored.

So the test is all or nothing: **if the sum of the chunk sizes in a block changes, every
old save fails**, however small the change. If the sizes stay the same, every old save
loads, whatever you changed inside.

The six **extra chunks** (Hall of Fame, Frontier records, battle videos) are separate: each
has its own footer (`struct SaveArrayFooter`) at a fixed sector, is checked only when it is
read (`ReadExtraSaveChunk`), and returns status 2 when neither copy is valid. Callers then
start it over (`AddHallOfFameEntry` in [src/game_clear.c](../../src/game_clear.c) calls
`Save_HOF_Init`). §5 uses this.

## 2. Two kinds of break

| Kind | What happens | Caused by |
|---|---|---|
| **Layout** | the save doesn't load: the game reports a corrupted save (`statusFlags` bit 1) or acts as if there is none | any chunk's `*_sizeof` changing to a different multiple of 4; a chunk added, removed or reordered; `SAVE_PAGE_MAX` changed |
| **Meaning** | the save loads, but data means something else | anything below |

Meaning breaks are worse: nothing tells the player, and the damage shows up later. Things
that are saved **by number**, so renumbering them changes old saves:

| Saved number | Where it is saved | Safe change |
|---|---|---|
| species, moves, items, abilities | party, PC, Day-Care, bag, Pokédex | add new ids after the last; never renumber ([items.md](items.md), [moves.md](moves.md), [adding-a-species.md](adding-a-species.md)) |
| flags and vars | `SAVE_FLAGS` | reuse free ones ([unknown-flags-vars.md](unknown-flags-vars.md)); never give a used flag a new job |
| story progress values (`VAR_SCENE_*`, etc.) | `SAVE_FLAGS` | add new values; don't change what an existing value means ([story-progression.md](story-progression.md)) |
| trainer ids | "defeated" flags at `TRAINER_FLAG_BASE` + id | add trainers after the last ([trainers.md](trainers.md)) |
| map ids | the player's position and warps (`SAVE_LOCAL_FIELD_DATA`) | add maps after the last `MAP_*` |
| roamer location indexes | `SAVE_ROAMER` (`ROAMER_LOC_*`) | add locations at the end ([roamers.md](roamers.md)) |
| the map the player saved on | `SAVE_LOCAL_FIELD_DATA` (x, y) | if you edit that map, an old save can put the player inside a wall: keep walkable where saves can be made (Pokémon Centers, routes) |
| phone contact ids | `SAVE_POKEGEAR` | add contacts after the last ([phone.md](phone.md)) |
| struct fields | any chunk | add fields where padding was; never reorder |
| `BoxPokemon` / `Pokemon` layout | party, PC, Day-Care, GTS, Pal Park | don't change it (it is also what trades and the Pokéwalker see) |

## 3. Rules for save-safe updates

1. Before each release, run `python3 tools/savemap/savemap.py` on the old build and the new
   one and compare. Same block sizes: old saves load. Different: decide to migrate (§6) or
   tell players to start over.
2. Only add ids after the last one (species, items, moves, trainers, maps, contacts).
3. Store new state in free flags, vars and padding first (§4), then in a new extra chunk (§5).
4. If the layout must change, change it in one release, add a version marker (§7), and
   write the migration (§6) in the same release.
5. Keep save files from every public release and load each one in the new build (§7).

## 4. Free space inside the current layout

Using any of these doesn't change a block's size, so old saves keep loading. On a new game
the whole region is cleared to 0 before each chunk's `initFunc` runs
(`Save_InitDynamicRegion_Internal`); in an old save they hold whatever was there, usually 0.
Treat 0 as "not set yet".

| Space | Size | Notes |
|---|---|---|
| unused `FLAG_UNK_*` | 844 never referenced | [unknown-flags-vars.md](unknown-flags-vars.md) |
| unused `VAR_UNK_*` | 76 never referenced (16 bits each) | same |
| `SAVE_MISC.filler_0288` | 16 bytes | not referenced by name in `src/` ([include/save_misc_data.h](../../include/save_misc_data.h)) |
| `SAVE_MISC.filer_029C` | 4 bytes | same |
| `SAVE_MISC` bitfield after `vsRecorderColorScheme` | 3 bits | the byte holding `extraChunksExist` |
| `Daycare.padding_1DD`, `DaycareMail.padding_5E` | 3 + 2 × 2 bytes | [include/daycare.h](../../include/daycare.h) |
| chunk rounding | up to 3 bytes per chunk | a chunk's size is rounded up to 4, so a struct can grow up to the next multiple of 4 without changing anything |
| a feature you removed | the whole chunk | keep the chunk and its size (a `union` or a struct of the same `sizeof`); point your data at it |

To grow a struct inside its rounding, add the field at the end and check the chunk's size
in `savemap.py` didn't change. There is no `STATIC_ASSERT` macro in `include/`; a
negative-size array makes the build fail if the size changes:

```c
// include/save_misc_data.h, after the struct: save layout, don't grow (see save-compatibility.md)
typedef char SaveMiscSizeCheck[sizeof(SAVE_MISC_DATA) == 736 ? 1 : -1];
```

## 5. New saved data: an extra chunk in the unused sectors

Sectors 47–63 of each half of the flash are never used (68 KiB). A new **extra chunk**
there has its own footer, is read only when you ask for it, and simply comes back invalid on
an old save, so you initialize it. The main save, and so old saves, are not affected.

### Add the chunk

In [src/save_arrays.c](../../src/save_arrays.c), after the last battle video entry:

```c
DECL_CHUNK_EX(ModSave_sizeof, ModSave_Init)

const struct ExtraSaveChunkHeader gExtraSaveChunkHeaders[] = {
    ...
    {
     5,
     SAVE_PAGE_MAX + 10,
     (SAVESIZEFN)BattleRecord_sizeof,
     (SAVEINITFN)BattleRecord_Init,
     },
    {
     6,                  // must equal its position in the table
     SAVE_PAGE_MAX + 12, // sector 47: the battle videos end at 46
     (SAVESIZEFN)ModSave_sizeof,
     (SAVEINITFN)ModSave_Init,
     },
};
```

The chunk is written as `sizeof` + 16 bytes (the footer) starting at that sector, so it may
use up to 17 sectors (69,616 bytes of data) before it runs past sector 63. A second mod
chunk goes at the next free sector.

Don't use the "keyed" functions (`ReadExtraSaveChunkKeyed` / `WriteExtraSaveChunkKeyed`):
their keys live in `SAVE_MISC.extraChunkKeys[2][5]`, which only has room for ids 1–5. The
plain `ReadExtraSaveChunk` / `WriteExtraSaveChunk` write both copies every time and keep
the newer one on reading.

### Tie it to the current game

Starting a new game clears the main save, not the extra sectors, so a new game would read
the previous game's mod data. Store something from the main save in the chunk and compare
it on reading. The player's 32-bit trainer ID (with the secret ID) is random per game:

```c
typedef struct ModSave {
    u32 owner;   // PlayerProfile_GetTrainerID when written
    u8 version;  // layout of the rest; 1 for the first release
    u8 padding[3];
    // your data, append only
} ModSave;
```

### Read and write it

The Hall of Fame shows the pattern: read on demand, check, use, write.

```c
ModSave *ModSave_Load(SaveData *saveData, enum HeapID heapID) {
    int status;
    ModSave *data = ReadExtraSaveChunk(saveData, heapID, 6, &status);
    u32 owner = PlayerProfile_GetTrainerID(Save_PlayerData_GetProfile(saveData));
    if (status != 1 || data->owner != owner) {
        MI_CpuClear8(data, ModSave_sizeof());
        ModSave_Init(data);
        data->owner = owner;
    }
    return data; // caller frees with Heap_Free
}

void ModSave_Store(SaveData *saveData, ModSave *data) {
    WriteExtraSaveChunk(saveData, 6, data);
}
```

This writes to flash immediately and synchronously, so it suits data that changes at
specific moments (a quest completed, a record set). For data that changes all the time, keep
a copy in RAM (on a heap that lives the whole game; see [engine.md](engine.md) for heap room)
and write it right after the main save succeeds, in `Field_SaveGameNormal`
([src/field/save_stats_printer.c](../../src/field/save_stats_printer.c)).

**Limits of this approach:**

- The main save and the extra chunk are written separately. If the power goes off between
  them, the extra chunk is one save behind (or ahead) of the main save. Design the data so
  that's harmless, or store `saveData->saveCounter` in it and treat a mismatch as stale.
- Raising `SAVE_PAGE_MAX` moves every extra chunk, including this one (§6).
- Retail and other hacks never write these sectors, so an old save's sectors are erased
  flash (0xFF) and fail the magic check, as intended.

## 6. When the layout has to change

Sometimes there's no way around it: more PC boxes, a bigger bag pocket, more flags than are
free. Then either ask players to start over, or migrate.

### Make future migrations easy

- **Add, don't move.** Add new chunks just before `SAVE_PCSTORAGE` (the end of block 0),
  and new fields at the end of a chunk's struct. Then every old chunk's bytes are still
  valid; only their offset changed, and the new bytes need their default values.
- Raise sizes by a margin (for example 64 more flags, not 3), so the next release doesn't
  need another migration.
- Put the version marker (§7) in first.

### In-game migration (outline)

The footer's `size` field tells the layouts apart: an old save's block 0 footer, read at the
**old** offset, has the **old** size. Two functions in `src/save.c` read the main save, and
both need to know the old layout:

- `Save_GetSaveFilesStatus` picks the valid, newest copy (at boot, from `SaveData_New`);
- `Save_LoadDynamicRegion` then reads that copy into `dynamic_region` and validates it
  **again** with the current layout. It also runs when the player picks Continue
  (`SaveData_TryLoadOnContinue`).

A migration would:

1. Keep the old release's chunk sizes as a table (from `savemap.py` on the old build), and a
   function that turns them into old `SaveArrayHeader` offsets and `SaveSlotSpec`s, using
   the same arithmetic as `SaveData_InitSubstructs` and `SaveData_InitSlotSpecs`.
2. In `Save_GetSaveFilesStatus`: when both copies fail with the current layout, validate
   them again with the old specs, and remember that the save is old. The function already
   reads both copies into two `SAVE_PAGE_MAX * SAVE_SECTOR_SIZE` buffers (`HEAP_ID_3`); if
   the old layout was bigger, read enough sectors to cover it.
3. In `Save_LoadDynamicRegion`, for an old save: read the old blocks into a temporary
   buffer and validate them with the old specs; run `Save_InitDynamicRegion_Internal` so
   every chunk gets its defaults; then copy each old chunk's bytes (the smaller of old and
   new size) to its new offset in `dynamic_region`. Fix up anything whose meaning changed
   (for example a bag pocket that grew: move the following pockets' items).
4. Set `saveCounter` and `lastGoodSector` from the old footer, as
   `Save_RecordWhichLatestGoodSector` does.
5. Call `Save_SetAllPCBoxesModified(saveData)`: the PC is saved box by box, only the boxes
   marked modified. Without this, the next save writes a new block 1 footer over PC boxes
   still in their old positions.
6. The next normal save writes the new layout. Until then both flash copies are old, so a
   crash before saving just migrates again.

If `SAVE_PAGE_MAX` changed, the extra chunks moved too: read them from the old sectors
(`old SAVE_PAGE_MAX + n`) and write them to the new ones, or the Hall of Fame and battle
videos are lost.

### Converter outside the game

The same steps can be done on the `.sav` file by a script, which keeps the game code
unchanged: read each half, validate the old layout, rebuild blocks in the new layout,
recompute each block's footer (`count`, `size`, `magic`, `slot`, `crc`) and write the file.
The CRC is NitroSDK's `MATH_CalcCRC16CCITT` (polynomial `0x1021`, initial value `0xFFFF`)
over the block without its 16-byte footer. Check your implementation reproduces the
`crc` of an unmodified save before trusting it. Players on real hardware can't run a
converter without a save dumping tool, so the in-game migration reaches more people.

## 7. Version marker and testing

### Version marker

The save has no version field. Take one byte of `SAVE_MISC.filler_0288` (§4) as a
**mod save version**:

| Value | Meaning |
|---|---|
| 0 | retail, or a release before you added the marker |
| 1, 2… | your layouts and meanings, one number per release that changed either |

Read it after loading (`Save_Misc_Get`) and run fix-ups for each version between the
save's and the current one, then store the current number. This also covers meaning changes
that need no layout change: a flag moved to a new job, a var whose values were renumbered,
a player position on a map you redrew.

In a new game, set it in `Save_Misc_Init`, so new saves are never mistaken for old ones.

### Testing

- Keep one save from each public release, from early in the game and from the
  post-game. melonDS stores the 512 KiB flash as a plain `.sav`; DeSmuME's `.dsv` adds a
  trailer after it.
- For each new build: `savemap.py` (same block sizes?), then load every kept save and check
  the continue screen (name, badges, time), the party, a few PC boxes (including the last
  one), the bag, the Pokédex count, the Hall of Fame, and that the player stands where they
  saved.
- Save in the new build, reload, and check again: this catches a migration that loads but
  writes something wrong.
- Then start a new game, save, and check that nothing from the old game shows up (§5).

## Not verified

- That nothing reads or writes `SAVE_MISC.filler_0288` / `filer_029C` through a whole-struct
  copy or a raw offset (they have no references by name in `src/`).
- The `ModSave` and migration code above has not been built or run; it is a sketch based on
  `src/save.c`.
- Whether NitroSDK's CRC-16/CCITT applies a final XOR (the SDK header only gives the
  polynomial and initial value).
- Which other chunks store map ids (`SAVE_MAP_OBJECTS`, the Pokégear map, phone data were
  not checked); assume any of them may, and only add maps at the end.
