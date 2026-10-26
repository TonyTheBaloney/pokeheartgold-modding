<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Graphics: NCGR, NCLR, NSCR, NCER, NANR

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the game stores 2D graphics, which of them are PNGs in this repository and which
are still binary, and how to change the binary ones with the two tools the build
already compiles: `nitroarc` (archives) and `nitrogfx` (graphics). Battle backgrounds
have their own guide, [battle-backgrounds.md](battle-backgrounds.md), which uses
everything here.

This page is about files. For the C side (BG layers, windows, sprites, palette slots,
fades) see [ui.md](ui.md#4-backgrounds-and-windows). 3D models and map textures
(NSBMD/NSBTX) are in [terrain.md](terrain.md), [area-textures.md](area-textures.md) and
[../gen4map/RENDERING.md](../gen4map/RENDERING.md).

| pokeemerald | here |
|---|---|
| `.png` + `.pal` in `graphics/`, converted by `gbagfx` | `.png` (+ `.NCLR` or `.pal`) where a converter exists, otherwise binary Nitro files inside NARC archives; converted by `tools/nitrogfx` (a `gbagfx` fork) |
| `INCBIN_U32("graphics/....4bpp.lz")` in C | a NARC id and member number: `GfGfxLoader_LoadCharData(NARC_a_0_0_7, 3, ...)` |
| `.4bpp`, `.8bpp` | `.NCGR` (tiles) |
| `.gbapal` | `.NCLR` (palette) |
| `.bin` tilemaps | `.NSCR` (tilemap) |
| `OamData`, `gSpriteImageTable_*`, `AnimCmd` arrays in C | `.NCER` (cells) and `.NANR` (animations) |
| `.lz` (LZ77, header byte `0x10`) | the same compression; files end in `.lz` in the build |

## 1. The file types

All of them are Nintendo's NITRO-System formats. Each starts with a four-letter magic
written backwards (`RGCN` for NCGR) and has one or more sections.

| File | Holds | pokeemerald equivalent |
|---|---|---|
| **NCGR** | tiles ("character" data): 8×8 pixel tiles, 4 bits per pixel (16 colors) or 8 (256 colors) | `.4bpp` / `.8bpp` |
| **NCLR** | palettes: 15-bit colors, 16 colors per row, up to 16 rows | `.gbapal` |
| **NSCR** | a tilemap ("screen") for a background: which tile, flip and palette row goes in each 8×8 cell | tilemap `.bin` |
| **NCER** | cells: how tiles form a sprite, as one or more OAM pieces (shape, size, offset, tile number) | the `OamData` and subsprite tables |
| **NANR** | cell animations: sequences of (cell, duration) frames | `AnimCmd` lists |
| NMCR / NMAR | multi-cells and their animations (several cells moved as one); rare | none |
| **NARC** | an archive of numbered members; nearly every graphic is a member of one | none (everything is linked into the ROM) |
| `.naix` | a C header the build writes for archives it makes, naming the members | none |

Things that matter when you draw:

- **Colors are 5 bits per channel.** A PNG's 0-255 values are cut to 0-31, so only
  multiples of 8 survive exactly. Two colors that differ by less than 8 become the same.
- **Color 0 of each palette row is transparent** (for backgrounds, the backdrop shows
  through; for sprites, whatever is behind).
- **4bpp tiles pick their palette row elsewhere.** A 4bpp tile only stores indices
  0-15. Which of the 16 rows it uses is in the tilemap entry (backgrounds) or the OAM
  (sprites). So a PNG for a 4bpp NCGR may hold several 16-color groups, but every
  8×8 tile must stay inside one of them.
- **8bpp tiles** use one 256-color palette; the tilemap's palette field is ignored.
- **A tilemap entry** is 16 bits: tile number (bits 0-9, so at most 1024 tiles per
  layer), horizontal flip (bit 10), vertical flip (bit 11), palette row (bits 12-15).
- **Sprite pieces** come in fixed sizes: 8×8, 16×16, 32×32, 64×64 (square), 16×8,
  32×8, 32×16, 64×32 (wide) and the tall versions of those. A cell is built from them.
- **Sprite tile numbering** depends on the NCGR's mapping mode (1D 32K, 64K, 128K...).
  The game uses 1D modes: each OAM piece's tiles are stored one after another, row by
  row inside the piece.

## 2. Where graphics live

**As PNG** (edit the PNG and build):

| What | Where | Guide |
|---|---|---|
| Pokémon sprites, shiny palettes | `files/poketool/pokegra/` | [pokemon.md](pokemon.md#graphics) |
| Pokémon icons, footprints | `files/poketool/icongra/poke_icon/`, `files/poketool/pokefoot/pokefoot/` | [pokemon.md](pokemon.md#graphics) |
| item icons | `files/itemtool/itemdata/item_icon/` | [items.md](items.md#icons) |
| trainer front and back sprites | `graphics/trainers/` | [trainer-classes.md](trainer-classes.md#trainer-sprites) |
| battle backgrounds, move animation backgrounds, the battle touch screen | `graphics/battle_backgrounds/` (archive `a/0/0/7`) | [graphics-sources.md](graphics-sources.md#5-graphicsbattle_backgrounds-a007), [battle-backgrounds.md](battle-backgrounds.md) |
| platforms, type icons, Poké Balls, HP boxes, other battle sprites | `graphics/battle_sprites/` (archive `a/0/0/8`) | [graphics-sources.md](graphics-sources.md#6-graphicsbattle_sprites-a008) |
| overworld sprites | exported and imported with `mapkit sprite` | [overworld-sprites.md](overworld-sprites.md) |
| Pokédex, Pokégear (map, phone, radio, options), Voltorb Flip, Unown puzzle, title screen, area windows, PC box, map previews, camera viewfinder | the folders with a `meson.build` that uses `ncgr_gen`, `ncgr_lz_gen`... (§6) | |

In those folders only the tiles are PNG. Their palettes, tilemaps, cells and animations
are usually kept as the original binary `.NCLR`, `.NSCR`, `.NCER`, `.NANR` files next
to the PNGs and copied or compressed as they are.

**As loose binary files.** Some archives are unpacked into one binary file per member,
and the build packs them: the bag (`files/graphic/bag/bag_graphics/`), the party menu
(`files/graphic/plist_gra/`), marts (`files/graphic/shop_gra/`), the starter choice
(`files/application/choose_starter/`), the naming screen (`files/data/namein/`), the
intro and opening (`files/demo/`). Nothing to unpack here: convert the member file to a
PNG, edit, convert back over the same file (§4, steps 2-3), and build.

**As binary archives.** Most of `files/a/` is copied into the ROM unchanged: look for
`prebuilt_files` in the folder's `meson.build`. These hold, among others, battle
move animation graphics and most menus. To change one, take it apart, convert, put it
back together (§4), or turn the whole archive into a folder of PNGs
([graphics-sources.md](graphics-sources.md#8-converting-another-archive)).

**Finding a NARC's id.** `include/filesystem_files_def.h` lists every archive in ROM
order: `NARC_a_0_0_9` is `files/a/0/0/9`, `NARC_graphic_font` is `files/graphic/font.narc`.
Archives the build makes from sources also get a `.naix` header (in the build folder)
naming each member, for example `NARC_voltorb_flip_voltorb_flip_00000002_NCGR_lz`.
Prebuilt archives have no names; the code uses bare member numbers.

## 3. Finding the graphics a screen uses

Search the screen's source for the loader calls. Each names an archive and a member:

| Call | Loads | File type |
|---|---|---|
| `GfGfxLoader_LoadCharData(narc, member, bgConfig, layer, offset, size, compressed, heap)` | tiles for a BG layer | NCGR |
| `GfGfxLoader_LoadScrnData(...)` | a tilemap for a BG layer | NSCR |
| `GfGfxLoader_GXLoadPal(narc, member, location, offset, size, heap)` | a palette straight to VRAM | NCLR |
| `PaletteData_LoadNarc(paletteData, narc, member, heap, buffer, size, pos)` | a palette into a `PaletteData` buffer (for fades); `pos` is in colors, so `0x70` is row 7 | NCLR |
| `SpriteSystem_LoadCharResObjFromOpenNarc`, `..._LoadPaletteBufferFromOpenNarc`, `..._LoadCellResObjFromOpenNarc`, `..._LoadAnimResObjFromOpenNarc` | a sprite's tiles, palette, cells, animation | NCGR, NCLR, NCER, NANR |
| `SpriteSystem_LoadResourceDataFromFileIdList` | a whole sprite set from a resdat list | all four |

The `compressed` argument (`TRUE`/`FALSE`) says whether the member is LZ-compressed. A
member that starts with the byte `0x10` is compressed.

If the call takes its member from a variable, run the game under gdb
([debugging.md](debugging.md#4-gdb)) and stop on the loader:

```
(gdb) break GfGfxLoader_LoadCharData
(gdb) continue
(gdb) info args        # narcId, memberNo
```

## 4. Changing a binary archive

The build compiles both tools; after one `make` they are in
`build/heartgold.us/tools/`. The steps below take `files/a/0/1/4` apart, turn one member
into a PNG and back, and put the archive back together. Each step was run on the retail
files and gives back byte-identical files.

```bash
T=$PWD/build/heartgold.us/tools
GFX=$T/nitrogfx/nitrogfx
ARC=$T/nitroarc/nitroarc
W=/tmp/gfxwork                       # anywhere outside the repository
mkdir -p $W && cp files/a/0/1/4 $W/14.narc

# 1. unpack: writes $W/14.narc.d/00000.NCLR ... 00077.NCLR
$ARC -xf $W/14.narc
```

`-xf` writes to `<archive>.d` **next to the archive**, so always copy the archive
somewhere else first; run on `files/a/0/1/4` itself it fills the repository with 78
files. The members are named by number and detected type, but stay compressed if they
were: `00064.NCGR` below starts with `0x10`.

The example is the start menu's icons: `src/start_menu.c` loads tiles 64, palette 61,
cells 62 and animation 63.

```bash
cd $W
cp 14.narc.d/00064.NCGR icons.NCGR.lz   # nitrogfx goes by the extension
cp 14.narc.d/00062.NCER icons.NCER.lz
cp 14.narc.d/00061.NCLR icons.NCLR

# 2. decompress, and turn into editable files
$GFX icons.NCGR.lz icons.NCGR
$GFX icons.NCER.lz icons.json           # cells as JSON (needed to lay out a sprite)
$GFX icons.NCLR icons.pal               # JASC palette, opens in most editors
$GFX icons.NCGR icons.png -palette icons.NCLR -cell icons.json -object

# ... edit icons.png (keep it indexed) and/or icons.pal ...

# 3. back to Nitro files, with the flags the original had (§5)
$GFX icons.png icons.NCGR.lz -cell icons.json -clobbersize -version101 -mappingtype 32 -nopad
$GFX icons.pal icons.NCLR -bitdepth 4
cp icons.NCGR.lz 14.narc.d/00064.NCGR
cp icons.NCLR    14.narc.d/00061.NCLR

# 4. repack (from inside the folder, so members keep their order) and put it back
(cd 14.narc.d && $ARC -cf $W/14.narc .)
cp $W/14.narc ~/path/to/pokeheartgold-modding/files/a/0/1/4
```

Then `make release` (plain `make` fails its checksum test after any change, as for every
mod). Keep the original archive, or use `git checkout files/a/0/1/4`, to go back.

**Order.** `nitroarc -cf` adds the files of a folder in name order, which is why the
members keep their five-digit numbers. To add a member, give it the next number
(`00078.NCGR`); never insert one in the middle, since code reads members by number.

## 5. Picking nitrogfx's flags

A file that loads in the game doesn't need to be byte-identical to retail, but copying
the original's header is the safe default, and `cmp` with the original tells you at once
whether you got it right: convert the untouched PNG back and compare.

Read the header with `xxd -l 48 file.NCGR` (after decompressing):

| You see | Flag |
|---|---|
| bytes 6-7 are `01 01` (version 1.01) instead of `00 01` | `-version101` |
| bytes 14-15 (section count) are `02 00` | `-sopc` (an extra SOPC section) |
| at 0x18 and 0x1A (tiles high, tiles wide) `ff ff ff ff` | `-clobbersize` (sprites: no fixed size) |
| at 0x1C, `04 00 00 00` | `-bitdepth 8` (`03` is 4bpp, the default) |
| at 0x20, `10 00 10 00` | `-mappingtype 64`; `10 00 00 00` is `32`, `10 00 20 00` is `128` |

For an NCLR: two sections (bytes 14-15 `02 00`) means `-pcmp`; a palette of only 16
colors needs `-bitdepth 4 -nopad` so it isn't padded to 256.

`files/meson.build` has the combinations the PNG folders use:

| Name | Flags |
|---|---|
| `VERSION101_SOPC_NCGR_FLAGS` | `-version101 -sopc` |
| `VERSION101_SOPC_8BPP_NCGR_FLAGS` | `-version101 -sopc -bitdepth 8` |
| `CLOBBER_SIZE_VERSION101_NCGR_FLAGS` | `-clobbersize -version101` |
| `CLOBBER_SIZE_VERSION101_64K_NCGR_FLAGS` / `_128K_` | the same with `-mappingtype 64` / `128` |
| `BPP4_NOPAD_PCMP_NCLR_FLAGS` | `-bitdepth 4 -nopad -pcmp` |
| `EXTFMT_LZ_FLAGS` | `-nopad -extfmt` (compression variant some archives use) |

One known oddity: some retail NCGRs announce an SOPC section in their header but the
compressed data stops before it (the battle backgrounds do). Build the NCGR with
`-sopc`, cut it to the original length, then compress:
[battle-backgrounds.md](battle-backgrounds.md#4-changing-a-background) shows it.

## 6. Drawing the PNG

- **Indexed PNG, not RGB.** The pixel values are palette indices and that is what goes
  into the NCGR. Save as indexed (in GIMP: Image → Mode → Indexed, "use custom
  palette" with the `.pal`; in Aseprite: indexed color mode) and don't let the editor
  reorder the palette.
- **The PNG's own palette is only for viewing.** The game uses the NCLR. Several PNGs
  in `files/graphic/zukan_gra/` are even grayscale: only the indices matter. Change
  colors in the `.pal`/NCLR, not in the PNG.
- **Keep the size.** Tiles are read by number and the screen's tilemap or cells point at
  them. A tileset PNG must keep its width and height; a sprite PNG must match its cells.
- **Sprites:** use `-cell file.json` when exporting, or you get the tiles in storage order
  (one OAM piece after another) instead of the picture.
- `nitrogfx` refuses a 4bpp NCGR if a pixel uses an index above 15 ("Image exceeds the
  maximum color value for a 4bpp image"); that also happens if you forget `-bitdepth 8`
  for an 8bpp file.

## 7. Turning an archive into sources

The PNG folders in §2 are archives that have been converted for good: their members are
files in the repository and `meson.build` rebuilds the NARC. `files/application/voltorb_flip`
is a small example:

```meson
voltorb_flip_ncgr_lz_sopc = ncgr_lz_gen.process(
    files('voltorb_flip_00000002.png', 'voltorb_flip_00000003.png'),
    extra_args : VERSION101_SOPC_NCGR_FLAGS + EXTFMT_LZ_FLAGS
)
voltorb_flip_nscr_lz = lz_gen.process(files('voltorb_flip_00000004.NSCR', ...),
    extra_args : EXTFMT_LZ_FLAGS)
```

and `files/application/meson.build` packs every output with
`nitroarc --create --index-namespace` into `voltorb_flip.narc` plus its `.naix`. The
generators (`ncgr_gen`, `ncgr_lz_gen`, `ncgr_cell_gen`, `nclr_gen`, `ncer_gen`,
`nanr_gen`, `lz_gen`, `copy_gen`) are defined at the top of `files/meson.build`.

To do the same for a prebuilt archive, `tools/narcgfx/narcgfx.py export` writes every
member as PNG, `.pal` or JSON with the flags that rebuild it, and `narcgfx.py build`
packs them back byte for byte: [graphics-sources.md](graphics-sources.md).

## 8. Cells and animations

`nitrogfx X.NCER X.json` and `nitrogfx X.NANR X.json` give JSON; the reverse
(`json` → `NCER` / `NANR`, with `.lz` variants) builds them. In a cell, each entry of
`"OAM"` is one piece:

| Key | Meaning |
|---|---|
| `Attr0.YCoordinate`, `Attr1.XCoordinate` | offset of the piece from the sprite's center |
| `Attr0.Shape` + `Attr1.Size` | piece size: shape 0 square, 1 wide, 2 tall; size 0-3 (e.g. shape 1 size 3 = 64×32) |
| `Attr2.CharName` | first tile of the piece in the NCGR (in units set by the mapping mode) |
| `Attr2.Palette` | palette row added to the sprite's palette |
| `minX`, `maxX`, `minY`, `maxY` | the bounding box |

In the NANR JSON, each entry of `"sequences"` has a `"frameData"` list of frames
(`"resultId"`, `"frameDelay"` in frames); `"animationResults"` turns a `resultId` into a
cell (`"index"`). Changing the frames or the cells they show needs no code change;
adding a sequence does if the code picks sequences by number (`Sprite_SetAnimCtrlSeq`).

## 9. Tilemaps

`nitrogfx` builds an NSCR from a Tiled map JSON (`layers[0].data`, `tilesets[0].firstgid`,
`width`, `height`) but cannot export one, so tilemaps are kept as binary `.NSCR` files.
To edit one, decode it yourself: a 0x24-byte header (the map's size in pixels at 0x18 and
0x1A), then one 16-bit entry per cell as in §1, in 32×32-cell blocks for maps wider than
256 pixels. Changing only the tiles (the NCGR) under an unchanged tilemap is usually
enough, as with battle backgrounds.

## Where to look

| What | File |
|---|---|
| graphics generators and flag sets | `files/meson.build` |
| NARC ids | `include/filesystem_files_def.h` |
| loaders | `include/gf_gfx_loader.h`, `include/palette.h`, `include/sprite_system.h` |
| the converter | `tools/nitrogfx/main.c` (list of conversions near the end) |
| the archiver | `tools/nitroarc/doc/nitroarc.1.adoc` |
| a whole archive to PNG and back | `tools/narcgfx/narcgfx.py` ([graphics-sources.md](graphics-sources.md)) |

## Not verified

- The edited files of §4 were only checked to rebuild byte for byte; a changed picture
  was not looked at in the game.
- That the game accepts an NCGR whose header differs from the retail one (other
  version, no SOPC). It should, since the loaders read the sections they need, but only
  retail-identical headers were tested.
- The Tiled JSON format for NSCR was read from `tools/nitrogfx/json.c`, not tried.
- The list of what the prebuilt archives hold is not complete; `a/0/0/7` and `a/0/0/8`
  are described in [graphics-sources.md](graphics-sources.md#5-graphicsbattle_backgrounds-a007).
