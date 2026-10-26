<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Area textures: the textures terrain is drawn with

> AI-generated; not affiliated with pret. See AI.md at the repository root.

Every map's 3D terrain is painted with the textures of its **area**: one set of
textures and palettes per area, loaded when the player enters it. The sets are
folders of PNG and `.pal` files in `data/area_textures/`, which the build packs into
the archive the game reads (`a/0/4/4`), byte for byte the retail one when unchanged.
This page covers how the game uses them, how to change one, and how to add a texture
and use it on terrain. The terrain models themselves are in [terrain.md](terrain.md).

| pokeemerald | here |
|---|---|
| a tileset: `data/tilesets/primary/general/tiles.png`, one sheet of 8×8 tiles | a texture set: `data/area_textures/NNN/textures/<name>.png`, one PNG per texture, any power-of-two size from 8 to 1024 |
| `palettes/00.pal` ... `15.pal`, picked by slot | `palettes/<name>.pal`, picked by name; 4, 8, 16 or more colors |
| `metatiles.bin` arranges tiles; the map grid names metatiles | the terrain models (`data/landdata/NNNN/model.nsbmd`) name a texture and a palette per material |
| a primary and a secondary tileset per layout (`src/data/tilesets/headers.h`) | one texture set per area: `map.json` `"area_data"` → area header (`a/0/4/2`) → set |
| `anim/` frames swapped by C callbacks (water, flowers) | texture animations in NITRO files (`a/1/4/0`, prop animations); not editable yet |
| limits: tile and palette counts of the tileset | limits: names, sizes, and texture memory (§7) |

## 1. How the game uses them

`AreaDataManager_Load` (`src/field/area_data.c`), when an area loads:

1. reads the area header, member `area_data` of `a/0/4/2`: its second field,
   `mapTexNarcMemberId`, names a member of `a/0/4/4`, the area's texture set;
2. loads that whole set into texture memory (`GF3dRender_AllocAndLoadTexResources`) and
   keeps only its name lists on the heap;
3. for each cell drawn, binds the terrain model's materials to the set
   (`GF3dRender_BindModelSet`): a material's texture and palette are found **by name**.

So a texture is in memory while its area is loaded, whether any cell uses it or not,
and a material that names a texture the set doesn't have is drawn without it. In the
retail game area *N* uses set *N* (0 to 105). Map props (signs, trees that aren't part
of the terrain) have their own textures in `a/0/7/0`, not covered here.

## 2. The folder

```
data/area_textures/002/          set 2 (New Bark, Cherrygrove, Routes 26, 27, 29-31)
    textures.json                the textures and palettes, in order
    textures/road01.png          one PNG per texture
    textures/tree01gs.png
    palettes/road01.pal          one JASC palette per palette
    palettes/tree01.pal
```

`textures.json`, one entry per line:

```json
{"textures": [
  {"name": "cavekn", "format": "palette16", "transparent": true, "palette": "cavekn_pl"},
  {"name": "grass02", "format": "palette4", "palette": "grass02_pl"},
  {"name": "sea_line02", "format": "a5i3", "palette": "sea_line02_pl"},
  ...
], "palettes": [
  {"name": "cavekn_pl"},
  {"name": "grass02_pl", "four_color": true},
  ...
]}
```

| Key | Meaning |
|---|---|
| `name` | what materials name; at most 16 characters, unique within the set (a texture and a palette may share a name) |
| `format` | how the texels are stored (table below) |
| `transparent` | color 0 is see-through (absent: drawn) |
| `palette` | the palette terrain draws this texture with. Only the PNG's colors come from it; the game pairs texture and palette per material |
| `four_color` | a 4-color palette, for `palette4` textures |

| Format | Colors | Bits per texel | Retail use | Count |
|---|---|---|---|---|
| `palette16` | 16 | 4 | almost everything: ground, roads, walls, trees | 2,662 |
| `palette4` | 4 | 2 | simple fills: grass shading, shadows, sand | 871 |
| `palette256` | 256 | 8 | three pictures (posters, stone tablets) | 3 |
| `a5i3` | 8, each with 32 levels of opacity | 8 | water edges, soft shadows | 96 |
| `a3i5` | 32, each with 8 levels of opacity | 8 | glass, light | 27 |

**The PNG is the texture.** Each is an indexed PNG whose pixel values are the stored
values: 0-15 for `palette16`, 0-3 for `palette4`. In `a5i3` / `a3i5` PNGs a value holds
the color in its low 3 / 5 bits and the opacity in the rest, as the game stores it; the
PNG's palette shows every value with its color and opacity, so it looks right in an
image viewer. The colors a PNG shows come from its `"palette"`: 3,238 textures from the
material that draws them, 306 by name (`<texture>` or `<texture>_pl`); 115 that no
terrain uses show gray.

## 3. Finding a texture

```sh
tools/mapkit/mapkit.sh areatex list 2             # textures of set 2, formats, sizes, bytes
tools/mapkit/mapkit.sh terrain export 4 work/c    # a cell's model with the textures it uses
```

Which set a map uses: its `map.json` `"area_data"` is the area; in the retail game,
area and set have the same number. `terrain export` writes the textures a cell's
materials use as `work/c/textures/<texture>-<palette>.png`, and `terrain.json` names them.

## 4. Changing a texture

Edit `textures/<name>.png` (keep it indexed, see [graphics.md §6](graphics.md#6-drawing-the-png))
and/or `palettes/<palette>.pal`, then `make release`. After changing a `.pal`, refresh the
PNGs' colors (this doesn't change the ROM):

```sh
tools/mapkit/mapkit.sh areatex color 2
```

- A texture changes **everywhere its area draws it**: every cell, in every map of every
  area that uses the set.
- **Sets don't share files.** Common textures (`tree01gs`, `road01`, `sea_on`) are copies
  in many sets; change each set whose maps should change (`grep -l '"tree01gs"'
  data/area_textures/*/textures.json`).
- A different size is fine (any power of two, 8 to 1024, width and height separately);
  the terrain's texture coordinates are in texels, so a 64×64 texture where a 32×32 one
  was shows its top-left quarter. Keep the size, or rescale the UVs in Blender.

## 5. Adding a texture

Draw it as an **indexed PNG**: width and height each 8, 16, 32, 64 or 128 (up to 1024),
at most 16 colors (4 for the cheapest format), color 0 transparent if it has see-through
parts. Then:

```sh
tools/mapkit/mapkit.sh areatex add 2 work/brick.png
# set 002: texture brick (palette16), palette brick_pl
```

This copies the PNG to `textures/brick.png`, makes `palettes/brick_pl.pal` from the PNG's
colors, and adds both to `textures.json`. Options:

| Option | |
|---|---|
| `--name N` | the texture's name (default: the file name); letters, digits, `_` and `.`, at most 13 characters (16 with `--palette`) |
| `--palette P` | use the set's palette `P` instead of making one |
| `--format palette4\|palette16\|palette256` | default: the smallest that holds the PNG's colors |
| `--transparent` / `--opaque` | color 0 see-through or drawn (default: transparent if the PNG's color 0 is) |

**Use it on terrain.** In Blender, give a material the image
`data/area_textures/002/textures/brick.png`: on import, a material whose image is
`<texture>.png` gets that texture and the palette `<texture>_pl`. Or, in the exported
`terrain.json`, set a material's `"texture": "brick", "palette": "brick_pl"`. Then:

```sh
tools/mapkit/mapkit.sh terrain import 4 work/c/model.obj
tools/mapkit/mapkit.sh terrain check 4      # every material's texture is in the set
make release
```

The texture is only in set 2: a cell that maps of another area also show needs it in
that area's set too (`terrain check` lists the areas).

**By hand**, add a line to each list of `textures.json` and the two files; the build
checks every PNG against its format.

**Translucent textures** (`a5i3`, `a3i5`) can't be made by `add`: copy a retail one as a
template (`sea_line02.png` in set 2 is `a5i3`), keep its format, and draw with values
whose high bits are the opacity (for `a5i3`, value = opacity × 8 + color, opacity 0-31).

## 6. Removing or renaming

Remove the PNG/`.pal` and its line. Rename the file and the `name` together. A material
that still names the old texture draws untextured; `mapkit terrain check` finds them.
The two area animations (`a/1/4/0`) animate materials by name, not textures, so they
are not affected.

## 7. Limits

| What | Limit |
|---|---|
| names | 1-16 characters; unique among a set's textures, and among its palettes |
| per set | 255 textures and 255 palettes |
| texture size | width and height each 8, 16, 32 ... 1024 |
| texture memory | the field has 256 KB for textures and 32 KB for palettes (`FieldMap_SetVramBanks`, `GF3dRender_InitSimpleManager`: two 128 KB slots, four 8 KB slots), shared by the area's map textures, its prop textures and the field's other 3D graphics |

Retail areas use at most about 85 KB of texels (area 6: 45 KB of map textures plus
40 KB of prop textures; the median area uses 27 KB) and 4 KB of palettes. A 32×32
`palette16` texture is 512 bytes, `palette4` 256, `a5i3` 1,024. `areatex list` prints
a set's total. What else in the field takes texture memory, and so how much is really
free, hasn't been measured: staying near the retail sizes is the safe course. If a set
doesn't fit, `GF3dRender_AllocAndLoadTexResources` fails an assert, which is silent in
a release build ([debugging.md](debugging.md#5-assertions)), and textures come out
wrong.

Identical textures and palettes in a set are stored once (as the retail converter
did), so copies cost nothing.

## 8. A new set

Copy a set to the next number (`data/area_textures/106/`) and change it. To use it, an
area header must name it: member *N* of `a/0/4/2`, bytes 2-3 (little-endian), is
`mapTexNarcMemberId` ([BINARY.md §6](../gen4map/BINARY.md#6-area-data)). `a/0/4/2` is still a binary
archive, so a new area needs a hex edit or a script for now; adding textures to the
area's existing set is the easy path.

## Where to look

| What | File |
|---|---|
| the sets | `data/area_textures/NNN/` |
| commands | `tools/mapkit/mapkit/areatex.py` (`mapkit areatex ...`) |
| NSBTX reading and writing | `tools/mapkit/mapkit/nsbtx.py` |
| loading an area | `src/field/area_data.c` (`AreaDataManager_Load`) |
| the build rule | `files/a/0/4/meson.build` |
| the file format, for tool writers | [FORMAT.md §10](../gen4map/FORMAT.md#10-map-texture-set-area_texturesnnn-12), [BINARY.md](../gen4map/BINARY.md), [CHANGE-0003](../gen4map/CHANGE-0003-area-textures.md) |

## Not verified

- **Not tried in the game**: no emulator was available. The sets build byte for byte,
  and a texture added with `add` and put on a cell with `terrain import` builds into
  both archives; but no new texture has been looked at on screen.
- How much texture memory is free in the field beyond what retail areas use (§7).
- `a3i5` / `a5i3` textures drawn from scratch; only retail ones were rebuilt.
