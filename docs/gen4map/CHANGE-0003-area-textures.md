<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Change 0003: map textures as PNG folders

> AI-generated; not affiliated with pret. See AI.md at the repository root.

| | |
|---|---|
| Status | Done (2026-10-26), on branch `area-textures` |
| Format | gen4map 1.2 ([FORMAT.md](FORMAT.md) §10): adds map texture sets and `paths.area_textures` |
| ROM | unchanged: HeartGold and SoulSilver pass all four `meson test` checksums |

## Motivation

After [CHANGE-0002](CHANGE-0002-terrain-authoring.md) a cell's terrain could be
remodeled, but only with the textures its area already had: the map texture archive
(`a/0/4/4`) was a binary file nothing could write. pokeemerald keeps its tilesets as
PNG and palette files; the goal was the same for the textures terrain is drawn with,
so a hack can change them and add new ones.

## What changed

| Area | Before | After |
|---|---|---|
| NSBTX | decode only (`nitro.py`) | `nsbtx.py`: lossless read/write; every retail map texture set (106) and prop texture set (94) rebuilds byte for byte |
| Map textures | `files/a/0/4/4`, prebuilt | `data/area_textures/NNN/`: `textures.json`, a PNG per texture, a JASC `.pal` per palette; `mapkit areatex pack` builds the archive (`files/a/0/4/meson.build`, with a depfile) |
| Tools | none | `mapkit areatex migrate/pack/list/add/color` (`areatex.py`); `terrain export/import/check` and the map editor read the sets from the folders |
| Checks | | `mapkit format check` validates `textures.json` (`schemas/textures.schema.json`) and that every set builds |
| Docs | | [docs/modding/area-textures.md](../modding/area-textures.md); FORMAT.md 1.2 §10; RENDERING.md §10; BINARY.md; terrain.md |

## Decisions

- **One folder per archive member, numbered.** The area header names a member by
  number, so the folders keep the number (`002`), as `data/landdata/NNNN` does.
- **Texture and palette are separate files.** The game pairs them per material, not
  per texture; a set shares one palette between several textures and keeps palettes
  no texture is drawn with. A texture's `"palette"` is only for showing the PNG; it
  comes from the terrain materials that use the texture (3,238 of 3,659), else from
  the name (306), else the PNG is gray (115).
- **The PNG holds the stored values.** An indexed PNG whose pixel values are the texel
  values is exact for every format the sets use, including the translucent ones
  (`a3i5`, `a5i3`: the PNG's 256-entry palette shows each value's color and opacity).
  Nothing is quantized at build time; `areatex add` takes indexed PNGs only.
- **Copy the converter's layout.** Texels and palettes in dictionary order with
  identical data stored once, palettes padded to 16 bytes, the dictionary trees of
  `nsbmd.dict_bytes`: these reproduce every retail file, so new files are written the
  same way, which is the best available evidence they load (no emulator).
- **Prop textures stay binary.** `nsbtx.py` writes them too, but nothing needed
  editing them yet.

## Verification

- `tools/mapkit/tests/test_areatex.py`: the folders rebuild the retail archive
  (SHA-1); all 94 prop texture sets round-trip; the project check passes; adding a
  texture (16- and 4-color, own or shared palette) gives an NSBTX the decoder reads
  back with the same texels and colors; `add` refuses taken names, sizes that aren't
  powers of two and too many colors; refreshing colors keeps `a5i3` texels; stray
  files are reported.
- End to end, on a copy of the data: `areatex add 2` a 32×32 texture, `terrain export
  4`, point a material at it in `terrain.json`, `terrain import 4`: both archives
  pack, the set holds the texture and the cell's material names it.
- `make` and `make soulsilver`: all checksums OK with `files/a/0/4/4` deleted.
- **Not verified in the game.**

## Not done

- Texture animations (NSBTP/NSBTA) for new water or flowers.
- Area headers (`a/0/4/2`) as text, so a new area can name a new set without a hex edit.
- Prop textures (`a/0/7/0`) as folders.
- 4×4-compressed and direct-color textures (no map texture uses them).
