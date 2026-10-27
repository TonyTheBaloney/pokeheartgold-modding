<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27 -->

# Change 0004: a solid map editor (props, layouts, object sprites)

> AI-generated; not affiliated with pret. See AI.md at the repository root.

| | |
|---|---|
| Status | Part 1 (clean-up) done 2026-10-27; parts 2-4 planned |
| Format | 1.2 unchanged for parts 1-4; the area prop list (§3.4) would be format 1.3 |
| ROM | must stay unchanged: opening and saving a map without edits writes identical files |

## Motivation

The editor (`tools/mapeditor`, [README](../../tools/mapeditor/README.md)) shows
everything a map is made of, but it only edits collision, behaviors, events and
the header. Three things are shown but can't be edited:

| What | Shown as | Edited today with |
|---|---|---|
| props (trees, houses, signs) | drawn in the terrain; *Prop markers* adds a diamond with a tooltip | `data/landdata/NNNN/props.json` by hand |
| the layout (size, which land data each cell uses) | the grid of cells, *Cell labels* | `data/layouts/<Layout>/layout.json` by hand |
| object sprites | blue boxes labelled **O** | (display only) |

This is the `pokeemerald` → Porymap gap listed in [WIKI.md](../WIKI.md#not-documented-yet).
Before adding these, the existing editing needed to be reliable: part 1 lists the
rough edges, and came first.

Order of work: **1 clean-up → 2 object sprites → 3 props → 4 layouts.** Sprites are
display only and low risk; props edit one file per cell; layouts touch every map that
shares the layout and C tables, so they come last.

## 1. Clean-up of the current editor

**Done (2026-10-27).** Each problem was first reproduced on the unchanged code with
the editor driven offscreen (mouse events through `QTest`, fields through their
signals), then fixed; `tests/test_window.py` keeps one test per item.

### 1.1 Bugs that could lose or corrupt edits

| # | Problem | Reproduced | Fix |
|---|---|---|---|
| B1 | A failed save still counted as "saved" when switching maps or quitting (`_confirm_discard` returned `True` after any save) | save raising → the editor opened the next map; edits gone | `MainWindow.save` returns whether it wrote everything; a failed save keeps the map open |
| B2 | Dragging several selected events moved only the one under the mouse | two warps dragged 2 tiles: one moved, the other snapped back | every selected event's start is recorded on press; one `MoveEvents` undo step for the whole drag |
| B3 | Editing a field rebuilt the form inside the field's own `editingFinished` signal | the `QLineEdit` was deleted while emitting (`Shiboken.isValid` false) | `FieldForm.set_fields` updates the texts in place when the rows are the same; the scene's `selectionChanged` is blocked while event items are rebuilt |
| B4 | Painting worked on the dimmed neighbour cells, which belong to other maps | a click on cell 15,11 (`MAP_EVERYWHERE`) changed its collision | painting only touches `MapDoc.editable_cells()` |
| B5 | The shared land data warning counted cells in this layout only | Pokémon Center land 221: "1 cell" | `MapDoc.land_users` counts maps across every layout (24 for the Pokémon Center); shown on hover and after each stroke that touched shared land data |
| B6 | Changing `layout` or `area_data` in the Header tab redrew nothing | terrain cache kept after an `area_data` change | `area_data` redraws the terrain and marks the 3D tab stale; `layout` is read-only |
| B7 | Saving a map without some event sections wrote them as empty lists (found by the new round-trip test) | 49 `map.json` files changed when saved without edits | `MapDoc.events` no longer creates sections; adding an event does |

### 1.2 Smaller problems

| # | Problem | State |
|---|---|---|
| S1 | After undoing back to the saved state the title kept its `*` and closing still asked to save | fixed: the undo stack alone decides |
| S2 | Any constant name was accepted: a typo (`FLAG_HIDE_BOYY`) saved and failed only at build time | fixed: a name that isn't one of the field's constants is refused with a message and the old text comes back. `map_type` and `battle_scene` are C enums the define table didn't have (their completion was empty); they are read from `include/map_header.h` and `include/constants/battle.h` now |
| S3 | New objects got no `#define` in `ids.h`, so the map didn't build until it was added by hand | fixed: saving adds it with the lowest free number, as `mapkit npc add` does |
| S4 | Events could be dragged or added off the map's own cells, including to negative coordinates | fixed: refused with a message; the drag snaps back |
| S5 | View → Zoom in/out skipped the 0.05-8 limit the wheel has | fixed (`MapView.zoom`): 60 zoom-ins reached 652,530× before |
| S9 | Files changed outside the editor were overwritten by saving | fixed: files changed since they were read are listed and saving asks first |
| S6 | Props are drawn even when the area doesn't load their model; the game draws model 0 instead (§3.1) | open: part of the props work (§3.2) |
| S7 | Events of other maps on the same layout aren't shown, so on the Overworld the neighbouring route's warps and NPCs at the border are invisible | open |
| S8 | Events on the same tile cover each other; only the top one is selectable | open |
| S10 | Saving doesn't run `mapkit validate` or `mapkit format check` | open |
| S11 | The tile `attr` value is shown but can't be painted | open |

### 1.3 Tests

`tests/test_window.py` (new): one test per fixed item above, plus a round trip that
saves every map in a copy of the checkout without edits and compares
`data/maps`, `data/layouts` and `data/landdata` with the originals. All 21 editor
tests pass.

## 2. Object sprites

### 2.1 How the game finds a sprite

[overworld-sprites.md §1](../modding/overworld-sprites.md#1-how-an-npc-sprite-is-drawn):
`graphics_id` → `gObjectEventGraphicsInfos` (`asm/overlay_01_sprite_data.s`) →
`MMODEL_*` → `files/data/mmodel/mmodel/mmodel_NNNNNNNN.NSBTX`. `mapkit.sprites.resolve`
already does this lookup, and `mapkit sprite export` already decodes the frames.

Checked on 2026-10-27 over every `map.json`: 2,667 objects use 234 different
`graphics_id`s. All resolve except the 11 `SPRITE_VAR_n` ids (28 objects): those take
their sprite at run time from `VAR_OBJ_n` (`include/constants/vars.h:44`), set by the
map's scripts, so the editor can't know what they show.

### 2.2 Plan

- Draw each object as one frame of its sprite, 32×32 (or 64×64) centred on its tile and
  anchored at the feet. Standard 16-frame NPCs: the standing frame for `facing_dir`
  (frames 1, 5, 9, 13 for up, down, left, right). Other kinds: frame 1.
- `SPRITE_VAR_n` and anything that doesn't resolve: the current box, labelled `VAR n`
  or `?`, with the reason in the tooltip.
- Cache decoded frames per (`graphics_id`, frame). Keep a View toggle *Sprites / boxes*.
- Selection outline and the yellow highlight stay; sprites of objects hidden by a flag
  are drawn the same (the editor doesn't know flag state).
- The `graphics_id` field gets a picker with a preview, not only text completion.
- Later: the same billboards in the 3D tab.

No file format or ROM change; nothing new is written.

## 3. Props

### 3.1 What the game does

| Rule | Source |
|---|---|
| At most 32 props per cell | `MAP_PROP_MAX`, `include/field/map_load_manager.h:8` |
| `position` is model units from the cell's centre (16 per tile); `y` is absolute height, not raised by the layout's altitude | FORMAT.md §7.2; `MapPropManager_DrawWithOffset` |
| The area loads only the prop models in its **prop list** (`a/0/4/3[mapPropNarcMemberId]`, up to 550) | `src/field/area_data.c:178`, `204` |
| A prop whose model isn't in the list is drawn as **model 0** | `AreaDataManager_GetMapPropModel`, `src/field/area_data.c:102` |
| Props are part of the land data, so a prop added to a shared cell appears in every map using it | FORMAT.md §7 |

Every visible cell is drawn with the *current* map's area, so a prop in a neighbour
cell is only correct if that area also lists its model.

### 3.2 Editor

- A **Props** tool (key 4): props become selectable and draggable at their real
  position (currently markers off by default and not selectable, `canvas.py:124`).
- Move snaps to half tiles (8 units) by default, free with Shift. Moving into another
  cell moves the prop to that cell's `props.json`.
- Height: when moved, `y` is set from the cell's heights at the new spot (the same
  lookup as `mapkit heights at`, `tools/mapkit/mapkit/bdhc.py`), unless the user
  locked it. The Properties tab shows model, position, rotation and scale as fields.
- Add from a model list that shows only the current area's prop list, with a
  thumbnail; Delete removes. Refuse a 33rd prop in a cell.
- Draw props in other areas' lists with a warning outline (fixes S6); the status bar
  says "the game draws model 0 here".
- Undo commands: `MoveProp`, `SetPropField`, `AddProp`, `RemoveProp`. A moved prop
  redraws its cell's terrain image (`CellItem.invalidate(terrain=True)`) and marks the
  3D tab stale.
- Saving writes `props.json` of every changed cell with `landdata.write_props_json`.

### 3.3 Not in scope

Rotation and scale stay text fields: every retail prop has rotation 0 and scale 1, and
whether the game applies them hasn't been checked.

### 3.4 Format 1.3: the area prop list

To place a prop model an area doesn't load, the area's list in `a/0/4/3` has to
change, and that archive is still a prebuilt binary (BINARY.md §6). This is
[ROADMAP](ROADMAP.md) step 5 (`area.json`). Until then the editor can only offer the
models already listed.

## 4. Layouts: resize and cell assignment

### 4.1 Limits the tools don't check yet

| Limit | Source | Checked by `layouts.py` / `format check`? |
|---|---|---|
| width × height ≤ **799** cells | `MAP_MATRIX_MAX_SIZE`, `include/map_matrix.h:7`; `src/map_matrix.c` copies without checking, so more overflows memory | **no**, only 1-255 per side (`layouts.py:115`) |
| `name` ≤ **16** bytes | `MAP_MATRIX_MAX_NAME_LENGTH`; `GF_ASSERT` in `src/map_matrix.c:41` | **no**, accepts 255 (`layouts.py:118`); FORMAT.md §6 also says 255 |

The **Overworld is 47 × 17 = 799 cells: it is already at the limit and can't grow**
without raising `MAP_MATRIX_MAX_SIZE` (which changes field memory use). New outdoor
areas have to reuse free cells inside the grid
([adding-a-map.md §5](../modding/adding-a-map.md)). Add both checks to `layouts.py`
and FORMAT.md §6 before any resize UI (a fix to the spec, not a format change).

### 4.2 What a resize moves

Event coordinates are global tiles over the layout. Growing or shrinking on the
**north or west** side shifts every coordinate on the layout:

| Uses layout coordinates | Updated by the editor? |
|---|---|
| `map.json` events of **every** map naming the layout (`Overworld`: 97 maps; `PokemonCenter_1F`: 24) | yes, all of them, in one undo step |
| warps into the layout from other maps | no change: warps point at a warp index, not a position |
| Fly/Teleport points (`flyX`, `flyY`) and spawn points | no: C tables ([town-map-and-fly.md](../modding/town-map-and-fly.md#coordinates)); list them as a warning |
| Town Map squares (Overworld cells) | no: C tables; the Overworld can't be resized anyway |
| script commands with coordinates (set position, camera) | no: listed by a search of `scripts.pory`, as a warning |

Growing on the south or east side moves nothing. The resize dialog takes the new
size and an anchor, shows the warnings above before applying, and refuses more than
799 cells.

### 4.3 Cells

- **Assign**: set a cell's land data number from a picker (thumbnail of each land
  data, how many cells and layouts use it), or `null` for no cell.
- **New cell**: copy an existing cell to the next free `data/landdata/NNNN` (numbers
  are archive positions with no gaps, FORMAT.md §4.3). There's no mapkit command for
  this yet; add `mapkit landdata copy N` first and have the editor call it.
- Outdoor layouts also have `maps` (which header applies in each cell) and
  `altitudes`: both editable per cell, `maps` with the `MAP_*` completer.
- Undo: `ResizeLayout` (keeps the removed cells and events), `SetCell`. Saving writes
  `layout.json` with `layouts.save`.

## 5. Verification (to do)

- The rule every change keeps: open and save each map without edits, then `make`
  passes all four checksums.
- Unit tests per part (§1.3, and do/undo/redo for each new command).
- In an emulator, one edit of each kind: a moved prop (and a prop with a model the area
  doesn't list, expecting model 0), a resized indoor layout with its events shifted, a
  reassigned cell.

## Not verified

- Part 1 was tested offscreen only; the editor wasn't used on a desktop session for it.
- That a prop's `rotation` and `scale` are applied by the game (§3.3).
- How `SPRITE_VAR_n` objects are set in each map (§2.1); only the mechanism was read.
- Whether anything besides the tables in §4.2 stores layout coordinates.
