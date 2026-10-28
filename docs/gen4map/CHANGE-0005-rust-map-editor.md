<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28 -->

# Change 0005: the map editor in Rust

> AI-generated; not affiliated with pret. See AI.md at the repository root.

| | |
|---|---|
| Status | Stages 1-8 done (2026-10-28), uncommitted on branch `mod/new-game-start` |
| Format | 1.2 unchanged |
| ROM | unchanged: the editor writes the same files the Python editor writes, byte for byte |

## Motivation

The map editor ([tools/mapeditor](../../tools/mapeditor/README.md), CHANGE-0001 and
[CHANGE-0004](CHANGE-0004-map-editor.md)) is Python and PySide6. It needs a virtual
environment with Qt, and several of the bugs fixed in CHANGE-0004 came from Qt object
lifetimes (B3: a field deleted inside its own signal). The goal was the same editor as
one native program, built as a separate tool on the gen4map files, which is also the
shape [ROADMAP.md](ROADMAP.md) asks for.

## Decisions

- **The editor is rewritten, the build pipeline is not.** mapkit (scripts compiler,
  header generation, meson hooks, packing) stays Python; the Rust editor reads and
  writes only the text files. Whatever it does, the ROM build is unchanged.
- **C headers are read by mapkit only.** Constant names need the preprocessor rules in
  `cdefs.py`; the sprite table is in assembly. `mapkit export-constants` (new,
  `tools/mapkit/mapkit/export.py`) writes them as JSON and the editor runs it at start
  (0.2 s). Without it the editor still works, without completions or sprites.
- **Paths from the manifest.** Map files from `paths`; the renderer's archives from
  `binaries`, inside `files/` (ROADMAP step 1).
- **egui with glow (OpenGL).** Immediate mode has no widget lifetimes to get wrong; glow
  keeps the 3D view a direct port of the Python editor's OpenGL 3.3 code.
- **Python as the reference.** Every decoder was checked against mapkit's output on
  the repository's data, not against a reading of the formats.

## What was built

`tools/mapeditor-rs/`, a Cargo workspace ([README](../../tools/mapeditor-rs/README.md)):

| Crate | Port of | Checked against Python |
|---|---|---|
| `gen4map-format` | `edit.load_json/save_json`, `landdata.Permissions`, props, `layouts.from_json`, maps.txt / layouts.txt / maps.h, `Repo.find_map`, `edit._add_define`, `project._land_index` | all 540 `map.json` and 676 cells round-trip byte for byte; layouts, map list, `ids.h` paths and the shared land data index equal |
| `gen4map-nitro` | `nitro.py` (NARC, NSBTX, NSBMD), `areatex.texture_set` (via the folders, palettes laid out as `nsbtx.write` does), `bdhc.Bdhc.height` | triangles of 10 land models and 24 prop models; every texture of 4 area sets with 3 palettes each; 5 sprite files; heights at every tile centre of 6 cells |
| `gen4map-render` | `mapeditor/terrain.py` without Qt (CPU rasterizer) | rendered and looked at; textures missing from an area are drawn flat as in Python |
| `mapeditor` | `project.py`, `commands.py`, `canvas.py`, `window.py`, `external.py`, `sprites.py`, `view3d.py` | every map opens and saves unchanged; edits on a scratch copy write exactly the expected files |

Stages, each usable before the next: read-only view; events (select, drag, rubber band,
add, delete); collision and behavior painting; header; undo / redo; files changed
outside; 3D tab; sprites and their animation. The text-editor integration of CHANGE-0004
part 5 came along.

Found while porting, in the Python editor (not fixed there): with several events
selected, Delete removes only one of them.

## Not done

- The UI has no automated tests (the Python editor drives its window offscreen); the
  data layer and undo stack are tested. `MAPEDITOR_RS_SCREENSHOT` saves the window for
  looking at it.
- Cells with `heights.json` (none in the repository yet) stand 3D sprites at the cell's
  altitude: building BDHC strips from the text form isn't ported.
- CHANGE-0004 parts 3-4 (props, layouts) and its open items S6-S8, S10, S11 apply to
  both editors.
