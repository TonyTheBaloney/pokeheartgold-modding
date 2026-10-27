<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27 -->

# Change 0004: a solid map editor (props, layouts, object sprites)

> AI-generated; not affiliated with pret. See AI.md at the repository root.

| | |
|---|---|
| Status | Parts 1 (clean-up), 2 (object sprites) and 5 (files in a text editor) done 2026-10-27; parts 3-4 planned |
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
`mapkit.sprites.texture_paths` (new) reads the tables once for the whole list.

Checked on 2026-10-27 over every `map.json`: 2,667 objects use 234 different
`graphics_id`s. All resolve except the 11 `SPRITE_VAR_n` ids (28 objects): those take
their sprite at run time from `VAR_OBJ_n` (`include/constants/vars.h:44`), set by the
map's scripts, so the editor can't know what they show.

Every one of those 223 sprites decodes with `nitro.load_nsbtx`. The kinds, by objects
using them: 16 frames of 32×32 (1,920 objects), 1 frame of 16×16 (400), 8 frames with a
second (shiny) palette (follow-Pokémon, 137), single 64×64 or 32×32 frames (116),
17 frames (33), 7 frames (33).

### 2.2 Frames

Textures are named `<name>.1` to `<name>.N`; sorted by that number:

| Frames | Standing frame for north, south, west, east | Checked |
|---|---|---|
| 16 (standard NPCs), 17 (one extra pose) | 1, 5, 9, 13 | rendered: 1-4 back, 5-8 front; frame 13 is frame 9 mirrored in BOY1, GSMAN1, GSWOMAN1 |
| 8 (follow-Pokémon) | 1, 3, 5, 7 | rendered Pikachu and Groudon: back, front, facing left, facing right |
| others | 1 | still objects, Apricorn trees, legendaries' poses |

### 2.3 Done (2026-10-27)

- Objects are drawn as that frame (`mapeditor/sprites.py`), one texel per scene pixel,
  centred on their tile with the frame's bottom on the tile's bottom; objects further
  south are drawn over those north of them. The tile is outlined in the event color
  (yellow when selected), and clicks select by the tile, not the whole sprite, so a
  tall sprite doesn't hide the event on the tile north of it.
- `SPRITE_VAR_n` objects and any sprite that can't be found stay boxes (**V** / **?**)
  with the reason in the tooltip; with no sprite table at all, every object is a box.
- Frames are decoded on first use and cached per (`graphics_id`, facing). View →
  *Sprites* switches back to boxes.
- Changing `graphics_id` or `facing_dir` redraws the object. The Event tab shows the
  selected object's sprite, and the `graphics_id` completion list shows each sprite,
  decoded only for the rows on screen.
- Tests (`SpriteTest` in `tests/test_window.py`): frame choice; Cherrygrove's six
  objects drawn as 32×32 sprites, west and east mirrored; Dragon's Den's `SPRITE_VAR`
  objects stay boxes with the reason; edits and the toggle redraw; completion icons;
  a missing sprite table.

Added the same day:

- **Animation** (`sprites.pose`, a 150 ms clock in the map view): each `movement_type`
  is previewed in place, since the editor never moves objects. Wanderers and the 24
  `PATH_*` types walk (the four-frame cycle) and turn through their directions in
  order (path types parse them from the name), `BACK_AND_FORTH` alternates its facing
  and the opposite, `LOOK_*` and the spins turn, follow-Pokémon sheets alternate their
  two frames, the rest stand facing `facing_dir`. `LOOK_AROUND` is random in the game
  and a fixed order here. View → *Animate sprites* turns it off.
- **3D tab**: the same frames as billboards, upright and turned to the camera around
  the vertical, one texel per world unit, bottom on the ground. The ground is the
  cell's heights at the tile's centre, the plate nearest the object's `elevation` where
  they overlap (`Bdhc_GetHeight` with the walker's height, `src/field_terrain.c`), the
  cell's altitude where there is none. Rendered Cherrygrove offscreen and looked at.
- Tests: poses per movement kind; 64 ticks of a wanderer show every walk frame in
  every direction and stopping restores the standing frame; the 3D sprite list; a
  billboard drawn offscreen covers the screen centre at an angle.

Still to do: the shiny palette of follow-Pokémon (palette 0 is always used). Objects
hidden by a flag are drawn like the others: the editor doesn't know flag state.

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

## 5. Files in a text editor

Added 2026-10-27, outside the original plan: scripts, text and the other map files
open in the user's editor at the right line (`mapeditor/external.py`).

- `Ctrl+E` opens the selected event's script in `scripts.pory` at its definition
  (`script`, `movement`, `text`... `Label {`, or `Label:` in an `.inc`); `Ctrl+Shift+E`
  opens `map.json` at the event's `{`. Both from the Event tab and the right-click menu.
- File → Open in text editor lists the map folder's files, its `layout.json` and the
  hovered cell's land data files.
- Editors are command templates with `{file}`, `{line}` and `{term}` (a terminal for
  Neovim, Vim, micro, Helix); presets for the common editors, the first installed one
  as default, `$VISUAL`/`$EDITOR` before the terminal presets. Kept in `QSettings`.
- `map.json` is watched: changed outside and nothing unsaved → reloaded at the same
  view; unsaved edits → a warning (saving already asks, §1.2 S9).
- Tests (`ExternalEditorTest`, with launching mocked): command building and terminal
  choice, script and event lines (the event's block parses back to the same event),
  the actions open the right file and line, the files menu, reload when clean and
  keeping unsaved edits.

Not tried with a real editor in the tests. Kate's `--line` was taken as 1-based from
its help text, not checked.

## 6. Verification (to do)

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
- Where the game puts a sprite relative to its tile: the editor puts the frame's bottom
  on the tile's bottom, which looks right top-down but wasn't compared with the game.
- Whether anything besides the tables in §4.2 stores layout coordinates.
