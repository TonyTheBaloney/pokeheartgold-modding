<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# gen4map: a file format and tools for Gen 4 Pokémon maps

> AI-generated; not affiliated with pret. See AI.md at the repository root.

gen4map is the format this fork keeps its maps in: header and events
(`map.json`), grids (`layout.json`), terrain cells (collision, behaviors, props,
models), map textures and a manifest. It is versioned and specified independently of this
repository so that it can become a standalone tool for Generation IV (Nintendo
DS) games: Diamond/Pearl, Platinum, HeartGold/SoulSilver.

| Document | |
|---|---|
| [FORMAT.md](FORMAT.md) | **the specification**: manifest, index files, `map.json`, `layout.json`, terrain cells, map texture sets, versioning, game differences |
| [schemas/](schemas/) | JSON Schemas for `map.json`, `layout.json`, `props.json`, `heights.json`, `textures.json`, the manifest |
| [BINARY.md](BINARY.md) | what each file becomes in the ROM: NARC, matrix, land data, BDHC, zone events, map headers, area data |
| [RENDERING.md](RENDERING.md) | drawing maps from NSBMD/NSBTX: resource lookup, model and texture decoding, drawing rules; writing terrain models (§9) and textures (§10) |
| [CHANGE-0001-maps-as-files.md](CHANGE-0001-maps-as-files.md) | the change that introduced all this: what, why, verification, commits |
| [CHANGE-0002-terrain-authoring.md](CHANGE-0002-terrain-authoring.md) | format 1.1: writing NSBMD models and BDHC heights, `heights.json` |
| [CHANGE-0003-area-textures.md](CHANGE-0003-area-textures.md) | format 1.2: map textures as PNG folders, writing NSBTX |
| [ROADMAP.md](ROADMAP.md) | steps to a standalone tool and other games |

In this repository:

- Manifest: `data/gen4map.json` (format 1.2, HGSS).
- Check a project: `tools/mapkit/mapkit.sh format check`.
- Edit: `tools/mapeditor/mapeditor.sh <Map>` ([README](../../tools/mapeditor/README.md)).
- How-to for modders: [maps-and-warps.md](../modding/maps-and-warps.md), [terrain.md](../modding/terrain.md),
  [area-textures.md](../modding/area-textures.md),
  [npcs-and-scripts.md](../modding/npcs-and-scripts.md).

## Changing the format

1. Edit FORMAT.md first; bump the minor version for additions, the major version
   for anything that changes existing files.
2. Update the schemas and `tools/mapkit/mapkit/formats.py`.
3. Update the readers/writers and run `mapkit format check` plus the tests.
4. Add a `CHANGE-NNNN-*.md` record.
