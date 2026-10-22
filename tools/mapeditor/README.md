<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Map editor

> AI-generated, local to this fork. Do not upstream.

A porymap-style editor for this fork's maps: the layout's cells seen from
above, with collision and tile behaviors to paint and the map's events (NPCs,
warps, triggers, signs) to drag and edit. It edits the text files in
`data/maps/`, `data/layouts/` and `data/landdata/`
([maps-and-warps.md](../../docs/modding/maps-and-warps.md)); build the ROM
afterwards with `make release`.

## Setup

PySide6 (Qt 6) in a virtual environment, once:

```sh
python3 -m venv tools/mapeditor/.venv
tools/mapeditor/.venv/bin/pip install PySide6
```

Then:

```sh
tools/mapeditor/mapeditor.sh            # pick a map from the list
tools/mapeditor/mapeditor.sh Cherrygrove
```

## Window

- **Maps** (left): every map in `data/maps`. Type to filter; double-click to open.
- **Map view** (centre): the map's cells plus one ring of neighbours, dimmed when
  they belong to another map. Wheel zooms, middle button drags.
  - tile colors are behaviors (green grass, blue water, sand, ice...; others get a
    fixed color each); red overlay = blocked;
  - blue **O** objects, magenta **W** warps, green **T** trigger zones (sized),
    yellow **S** signs / hidden items, orange diamonds props (hover for details).
- **Properties** (right):
  - *Event*: every field of the selected event. Fields with constants (sprites,
    movement types, flags, vars, maps...) complete as you type.
  - *Header*: the map's `map.json` header fields.
  - *Tiles*: brush size, the behavior palette (filterable) and the tile under the
    cursor.
- **Status bar**: tile coordinates, cell, land data number, how many cells share
  that land data, collision, behavior name and attribute.

## Tools

| Tool (key) | Left mouse | Right mouse |
|---|---|---|
| Select / move events (1) | select, drag to move (snaps to tiles); rubber-band select | menu: add an object, warp, trigger or sign here; delete |
| Paint collision (2) | block tiles | open tiles |
| Paint behavior (3) | paint the palette's behavior | pick the behavior under the cursor |

`Delete` removes the selected event, `Ctrl+Z` / `Ctrl+Shift+Z` undo and redo
(strokes, moves, field edits, adds and deletes), `Ctrl+S` saves. The View menu
and toolbar toggle behavior colors, collision, grid, props, events and cell labels.

## What saving writes

- `data/maps/<Map>/map.json`: events and header, in the existing format (an
  unchanged file saves byte-identical).
- `data/landdata/NNNN/permissions.txt` of every cell you painted. **Shared land
  data**: painting a cell used elsewhere (sea, Pokémon Centers) changes every
  map that uses it.

New objects get a `local_id` like `obj_T21_new1` and script 0; add the id to
`ids.h` and a script in `scripts.pory` (`mapkit script add`), see
[npcs-and-scripts.md](../../docs/modding/npcs-and-scripts.md). `mapkit validate`
checks the result.

## Not yet

- The 3D terrain (`model.nsbmd`) and props aren't drawn; tiles are colored by
  behavior. Next step: render the NSBMD models and textures under the grid.
- Props can't be moved yet, layouts can't be resized and cells can't be
  reassigned to other land data in the editor (edit `layout.json` / `props.json`).
- Object sprites are shown as boxes, not their overworld graphics.

## Code

| File | |
|---|---|
| `mapeditor/project.py` | data layer, no Qt: `MapDoc` (map.json + layout + land data), tested |
| `mapeditor/commands.py` | undoable edits (`QUndoCommand`) |
| `mapeditor/canvas.py` | map view: cells, events, props, painting |
| `mapeditor/window.py` | main window, panels, actions |
| `tests/test_editor.py` | `QT_QPA_PLATFORM=offscreen tools/mapeditor/.venv/bin/python -m unittest discover -s tools/mapeditor/tests` |

It reads and writes through `tools/mapkit` (`layouts.py`, `landdata.py`, `edit.py`).
