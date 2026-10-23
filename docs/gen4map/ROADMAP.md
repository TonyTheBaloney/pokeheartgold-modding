<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# Roadmap: a standalone Gen 4 map tool

> AI-generated, local to this fork. Do not upstream.

The aim is a tool, outside this repository, that works on Generation IV Pokémon
maps for any of the three games, either inside a pret decomp project or directly
on a ROM. This page says what already exists, what is tied to this repository,
and the steps to get there.

## What exists (2026-10-22)

| Piece | Where | Tied to this repo? |
|---|---|---|
| Format spec, schemas, manifest | `docs/gen4map/`, `data/gen4map.json` | no |
| NARC read/write, land data, layouts, matrices | `tools/mapkit/mapkit/{landdata,layouts,matrix}.py` | lightly (paths, `maps.h` for names) |
| NSBMD/NSBTX decoder | `tools/mapkit/mapkit/nitro.py` | no |
| NSBMD writer, BDHC codec/generator, OBJ import/export | `tools/mapkit/mapkit/{nsbmd,bdhc,terrain}.py` | `terrain.py` reads map.json/layouts for the area |
| Format checker | `tools/mapkit/mapkit/formats.py` | reads the manifest |
| Top-down and 3D renderer | `tools/mapeditor/mapeditor/{terrain,view3d}.py` | ROM paths from constants in `terrain.py` |
| Editor | `tools/mapeditor/mapeditor/{project,canvas,window,commands}.py` | via mapkit's `Repo` (maps.txt, constants, scripts) |
| Map scripts compiler, events, headers, build hooks | `tools/mapkit/mapkit/{pory,layout,edit,…}` | yes (HGSS decomp layout, meson) |

## Target shape

```
gen4map/                     (separate package, Python, stdlib core + optional Qt)
  format/                    manifest, schemas, readers/writers for map.json, layout.json,
                             permissions.txt, props.json; `gen4map check`
  binary/                    NARC, matrix, land data, zone events, area data, map header
                             (per game family), NitroFS reader for .nds files
  nitro/                     NSBMD, NSBTX (later NSBTP/NSBTA animations, BDHC)
  render/                    top-down baker, OpenGL scene
  editor/                    the Qt editor
  projects/
    decomp.py                a pret decomp checkout (this repo's layout; manifest paths)
    rom.py                   a .nds: unpack to gen4map files, repack (ARM9 patch for headers)
```

The manifest is the seam: the tool only learns paths, archive locations and
feature flags from `gen4map.json`, never from hard-coded repository layout.

## Steps

1. **Make the renderer manifest-driven.** Replace the ROM path constants in
   `terrain.py` with `manifest.binaries`; read binaries from either the build's
   `files/` tree or a NitroFS image.
2. **Split mapkit.** Move the game-independent modules (`landdata`, `layouts`,
   `matrix`, `nitro`, `formats`, NARC code) into a package with no dependency on
   `Repo`; keep the decomp-specific parts (pory, header generation, build hooks)
   in this repo, importing the package.
3. **ROM projects.** A NitroFS reader/writer (FNT/FAT) and an ARM9 map header
   reader for each family; `gen4map import game.nds out/` producing the same files
   this repo has; `export` packing them back. Verify on HGSS by importing the
   retail ROM and comparing with `data/`.
4. **Platinum and Diamond/Pearl.** Check every "expected" row in FORMAT.md §9 and
   BINARY.md §7 against pret/pokeplatinum and pret/pokediamond; add `family`
   specific codecs (land data without sound plates, their map header); a
   `PLATINUM` manifest.
5. **Format 1.1.** Per-game header keys; area data (`area.json`: textures, prop
   list, prop kind) so `area_data` stops being a bare number.
6. **Editing 3D data.** Done (CHANGE-0002): models from OBJ, BDHC from the model
   or a text form (`heights.json`). Still to do: prop placement in the editor;
   layout resize and cell assignment; new textures (an NSBTX writer and texture
   encoders, so areas can gain textures from PNG sources as pokeemerald's tilesets
   do).
7. **Animations.** NSBTP/NSBTA for water and flowers in the renderer.

Each step keeps the invariant this repo already has: the unmodified data
reproduces the retail binaries byte for byte, checked by tests.
