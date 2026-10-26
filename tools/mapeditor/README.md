<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# Map editor

> AI-generated; not affiliated with pret. See AI.md at the repository root.

A porymap-style editor for this fork's maps: the layout's cells seen from
above, drawn from the game's own 3D models, with collision and tile behaviors
to paint and the map's events (NPCs, warps, triggers, signs) to drag and edit,
plus a 3D view. It edits the text files in
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
- **Map tab** (centre): the map's cells plus one ring of neighbours, dimmed when
  they belong to another map. Wheel zooms, middle button drags.
  - the terrain and props as the game draws them, seen from straight above
    (*Terrain (3D)* layer); red overlay = blocked; *Behavior colors* overlays each
    tile's behavior (green grass, blue water, sand, ice...; others a fixed color each);
  - blue **O** objects, magenta **W** warps, green **T** trigger zones (sized),
    yellow **S** signs / hidden items; *Prop markers* adds a diamond per prop
    (hover for its model and position).
- **3D tab**: the same cells in perspective. Left drag turns, right or middle drag
  pans, wheel zooms. Needs OpenGL 3.3.
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
and toolbar toggle terrain, behavior colors, collision, grid, prop markers,
events and cell labels.

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

## How the terrain is drawn

`tools/mapkit/mapkit/nitro.py` decodes NSBMD models and NSBTX textures (all
seven texture formats, node transforms, skinned envelopes, the GX display lists),
following NitroSystem's own code in `subprojects/NitroSystem-*`. For each cell
the editor takes `data/landdata/NNNN/model.nsbmd` with the textures of the open
map's area (`map.json` `area_data`: area header `files/a/0/4/2`, map textures
`data/area_textures/NNN/`), and each prop in `props.json` with the area's prop models
(`files/a/0/4/0` outdoors, `files/a/1/4/8` indoors) and prop textures
(`files/a/0/7/0`). Like the game, every visible cell uses the open map's area, the
terrain is raised by the layout's `altitudes` (8 units each) and props are not.

The map tab draws each cell once from above with QPainter (an exact affine
texture mapping per triangle, lowest first) and caches it; the 3D tab uploads the
same triangles to OpenGL (`mapeditor/view3d.py`).

Not drawn: texture and material animations (water ripples, flowers), billboard
props turning to the camera, lighting, and polygons in the DS's shadow mode. The
3D tab multiplies textures by vertex colors as the DS does; the map tab ignores
vertex colors.

## Not yet

- Props can't be moved yet, layouts can't be resized and cells can't be
  reassigned to other land data in the editor (edit `layout.json` / `props.json`).
- Object sprites are shown as boxes, not their overworld graphics.
- Map models can't be edited here: use `mapkit terrain export` / `import` with a 3D
  editor ([docs/modding/terrain.md](../../docs/modding/terrain.md)). Heights aren't
  shown yet.

## Code

| File | |
|---|---|
| `mapeditor/project.py` | data layer, no Qt: `MapDoc` (map.json + layout + land data), tested |
| `mapeditor/commands.py` | undoable edits (`QUndoCommand`) |
| `mapeditor/canvas.py` | map view: cells, events, props, painting |
| `mapeditor/terrain.py` | top-down pictures of cells from their models and props |
| `mapeditor/view3d.py` | the 3D tab (OpenGL) |
| `mapeditor/window.py` | main window, panels, actions |
| `tests/test_editor.py` | `QT_QPA_PLATFORM=offscreen tools/mapeditor/.venv/bin/python -m unittest discover -s tools/mapeditor/tests` |

It reads and writes through `tools/mapkit` (`layouts.py`, `landdata.py`, `edit.py`,
`nitro.py`).
