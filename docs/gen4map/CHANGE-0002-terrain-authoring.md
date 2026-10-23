<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Change 0002: editable terrain models and heights

> AI-generated, local to this fork. Do not upstream.

| | |
|---|---|
| Status | Done (2026-10-22), uncommitted on branch `ai-local/battle-mart-names` |
| Format | gen4map 1.1 ([FORMAT.md](FORMAT.md) §7.3): adds `heights.json` |
| ROM | unchanged: HeartGold and SoulSilver pass all four `meson test` checksums |

## Motivation

After [CHANGE-0001](CHANGE-0001-maps-as-files.md) every part of a map was text
except a cell's 3D model (`model.nsbmd`) and its heights (`terrain.bdhc`), so
terrain could be looked at but not changed. Goals: make a cell's terrain in a 3D
editor and bring it back; edit and generate heights; document both binaries well
enough that another tool can write them.

## What changed

| Area | Before | After |
|---|---|---|
| NSBMD | decode only (`nitro.py`) | `nsbmd.py`: lossless read/write (Patricia name trees), `build_terrain` from polygons and materials; `nitro.py` gains `polygons()` (quads kept) and normals |
| BDHC | binary file, layout partly known | `bdhc.py`: lossless read/write, the game's lookup exactly (FX math, strip search, 10-candidate limit), `build` (pools, strips), `heights.json` text form, generator from triangles, `check` |
| Cells | `terrain.bdhc` required | `terrain.bdhc` or `heights.json` (format 1.1); `landdata.build` compiles the JSON |
| Tools | none | `mapkit terrain export/import/check`, `mapkit heights decompile/compile/show/at/generate` (`terrain.py`) |
| Build | land data inputs listed at configure time | the pack step writes a depfile (files read + cell folders), so new, removed or replaced cell files rebuild without reconfiguring (`files/a/0/6/meson.build`) |
| Docs | | [docs/modding/terrain.md](../modding/terrain.md); BINARY.md §3, §3.2; RENDERING.md §9; FORMAT.md 1.1; `schemas/heights.schema.json` |

## Decisions

- **Models stay NSBMD in the tree; OBJ is the exchange format.** Converting needs
  the area's texture sizes and names, and one cell can be shown with different
  areas, so import is an explicit step with a known area, not a build step. The
  sidecar `terrain.json` carries what OBJ/MTL can't (texture, palette, lighting,
  culling, fog, wrapping), so a model survives a trip through Blender.
- **Copy the retail conventions.** All 676 retail terrain models share one
  structure (one model, one identity node, no TEX0, the same SBC pattern, lit
  materials with normals or unlit with vertex colors); new models are written the
  same way, which is the best available evidence they load, without an emulator.
- **Heights as rectangles where the author gives them, sampled otherwise.** A
  `heights` object's axis-aligned rectangles become plates exactly; other faces
  (and the model, when there's no heights object) are sampled on a grid whose
  cell corners are the tile centres and edges.
- **Default: heights over every tile.** Masking by `permissions.txt` keeps roofs
  out but loses heights when collision isn't updated yet, which fails silently in
  game; it is an option (`--walkable-only`).
- **`heights.json` beside, not instead of, `terrain.bdhc`.** Retail cells keep the
  binary so the ROM stays identical (52 files can't be rebuilt from values alone);
  a cell switches to text when edited.

## Verification

- `tools/mapkit/tests/test_nsbmd.py`: all 676 retail models `write(read(f)) == f`;
  name trees found by a port of `NNS_G3dGetResDictIdxByName` for 1 to 200 names;
  retail geometry re-encoded by `build_terrain` gives the same polygons (every
  15th model; the full set was checked once: 676 of 676) at 97% of the size.
- `test_bdhc.py`: all 676 BDHC files round-trip; pools and strips rebuild them (624
  exactly, 676 with the stored pool slots); `heights.json` gives the same height at
  every 16-unit point in three modes; the strip search; FX math; generator on a
  synthetic plateau and ramp and on retail models (the model's surface at every
  tile centre of three cells; on 15 sampled cells 20,141 of 20,143 surfaces).
- `test_terrain.py`: export then import changes neither model nor heights (4
  cells); an OBJ with no sidecar gets its materials from texture names.
- Build: the land data archive is identical to the retail one; switching a cell to
  `heights.json` and back rebuilds without reconfiguring; both ROMs pass all
  checksums.
- **Not tested in the game** (no emulator available).

## Findings worth keeping

- `VTX_DIFF` offsets are 1/4096 (as decoded), not 1/512: 86% of retail DIFF vertices
  coincide with vertices given in full.
- BDHC strip `bound` is the strip's *upper* z edge; plates touching it are listed.
- Retail BDHC heights don't follow the visible model in many interiors (2-3 units
  above the floor) and on invisible floors; they came from separate collision data.
- The game uses BDHC heights without the layout altitude though it draws raised
  cells higher; unresolved.

## Open questions

- Adding textures to an area's NSBTX (needs an NSBTX writer and texture encoders).
- Texture animations (NSBTP/NSBTA) for new water or flowers.
- The altitude question above.

## Rollback

Revert the files listed above; cells edited with `terrain import` keep working
only while `bdhc.py` and the depfile rule are present (or after `mapkit heights
compile` back to `terrain.bdhc`).
