<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-26 -->

# Graphics as PNG sources

> AI-generated; not affiliated with pret. See AI.md at the repository root.

How the binary graphics archives in `files/a/` become folders of PNG, `.pal` and JSON files
that the build packs back into the archive, the way pokeemerald keeps its `graphics/`
folder. Two archives are built this way:

| Archive | Folder | Holds |
|---|---|---|
| `a/0/0/7` | [`graphics/battle_backgrounds/`](../../graphics/battle_backgrounds/) | battle backgrounds, move animation backgrounds, the battle touch screen (§5) |
| `a/0/0/8` | [`graphics/battle_sprites/`](../../graphics/battle_sprites/) | platforms, type icons, Poké Balls, HP boxes and the other battle sprites (§6) |

Both build back byte for byte, so `make` still matches the retail ROMs. The other
graphics archives are still copied as binary files; `tools/narcgfx/narcgfx.py` turns any
of them into a folder the same way (§8). The file formats and `nitrogfx` itself are in
[graphics.md](graphics.md); how a battle uses its background and platforms is in
[battle-backgrounds.md](battle-backgrounds.md).

| pokeemerald | here |
|---|---|
| `graphics/battle_environment/tall_grass/tiles.png`, `palette.pal`, `map.bin` | `graphics/battle_backgrounds/backgrounds/general/tiles.png`, `day.pal`, `evening.pal`, `night.pal`; one `backgrounds/tilemap.NSCR` for all |
| `graphics/types/fire.png` | `graphics/battle_sprites/type_icons/fire.png` |
| C names the file: `INCGFX_U32("graphics/.../tiles.png", ".4bpp.lz")` | C names the archive and member: `GfGfxLoader_LoadCharData(NARC_a_0_0_7, 3, ...)`; `members.json` says which file is member 3 |
| one rule per extension (`%.4bpp: %.png`), exceptions in `graphics_file_rules.mk` | one rule per extension, the header flags of each file in `members.json` ("formats") |
| `.4bpp`, `.gbapal`, `.lz` generated and ignored by git | NCGR, NCLR, LZ and the archive generated in `build/`; only the sources in git |
| tilemaps stay binary (`map.bin`) | tilemaps stay binary (`.NSCR`) |
| sprite sheets as pictures, OAM layout in C | sprite PNGs as pictures, laid out by their cells (`.NCER.json`) |

## 1. What pokeemerald does

Read from pret/pokeemerald (master, October 2026):

- **Sources only.** `graphics/` holds `.png` (indexed) and `.pal` (JASC) files.
  `.gitignore` excludes `*.4bpp`, `*.8bpp`, `*.gbapal`, `*.lz`: the binary forms exist only
  in the build.
- **Generic rules.** The `Makefile` converts by extension with `gbagfx`, the tool
  `nitrogfx` was forked from:

  ```make
  %.4bpp:   %.png  ; $(GFX) $< $@
  %.gbapal: %.pal  ; $(GFX) $< $@
  %.lz:     %      ; $(GFX) $< $@
  ```

- **Exceptions in one file.** `graphics_file_rules.mk` overrides the rule for the files
  that need more than the default: a tile count (`-num_tiles`), a sprite width
  (`-mwidth`), a palette size (`-num_colors 224` for the title screen logo), or several
  files joined with `cat` (Castform's forms).
- **The C names the source.** `src/data/graphics/battle_environment.h`:

  ```c
  const u32 gBattleEnvironmentTiles_TallGrass[] = INCGFX_U32("graphics/battle_environment/tall_grass/tiles.png", ".4bpp.lz");
  const u32 gBattleEnvironmentPalette_TallGrass[] = INCGFX_U32("graphics/battle_environment/tall_grass/palette.pal", ".gbapal.lz");
  const u32 gBattleEnvironmentTilemap_TallGrass[] = INCGFX_U32("graphics/battle_environment/tall_grass/map.bin", ".lz");
  ```

  `scaninc` and `preproc` turn that into a dependency on, and an include of,
  `build/assets/graphics/.../tiles.4bpp.lz`, which the rules above make from the PNG.
  (Older pokeemerald, and most hacks, write `INCBIN_U32("graphics/.../tiles.4bpp.lz")`
  instead; the effect is the same.)
- **Tilemaps are not PNGs.** `map.bin` is committed as binary; only the tiles and the
  palette are editable as images.
- **Matching.** `gbagfx` writes the same bytes as the original files, so the ROM still
  matches with every graphic built from PNG.
- **Battle backgrounds** (`graphics/battle_environment/<name>/`): `tiles.png` (4bpp),
  `palette.pal`, `map.bin`, and for some `anim_tiles.png` + `anim_map.bin` or extra
  palettes (`gym.pal`, `leader.pal`, `groudon.pal`).

## 2. Why the DS needs more than file extensions

- **Members are numbered.** The code loads "member 3 of `a/0/0/7`". A converted archive
  must give back every member at its number, in order, including the ones that aren't
  2D graphics (3D models, data).
- **Each file has its own header.** An NCGR records its version, whether it has an SOPC
  section, the sprite mapping mode, whether it is tiles or a bitmap; an NCLR its color
  count, PCMP section, and a few odd fields. These can't be told from the PNG, so they go
  next to it, as pokeemerald's exceptions do. Here every file has some, so they are
  stored for every member (§4).
- **Compression varies per member.** LZ with or without padding to 4 bytes, and the
  `0x11` variant (`-extfmt`). Inside one archive, members can differ.
- **NSCR, NCER, NANR.** Tilemaps can't be exported to an image by `nitrogfx`, so they
  stay binary (as `map.bin` does in pokeemerald). Cells and animations become JSON.

## 3. How graphics are built here

| Way | Used by | Sources | Flags |
|---|---|---|---|
| Meson generators (`ncgr_gen`, `ncgr_lz_gen`, `nclr_gen`, `lz_gen`...) | the folders in [graphics.md §2](graphics.md#2-where-graphics-live) (Pokédex, Pokégear, Voltorb Flip...) | `<archive>_000000NN.png` + binary NSCR/NCER/NANR next to them; `meson.build` lists each file | one call per group of files with the same flags |
| A Python builder with its own table | trainer sprites, `a/0/5/8` and `a/0/0/6` (`tools/pokedata/trainer_pics.py`, [trainer-classes.md](trainer-classes.md#trainer-sprites)) | named PNGs + `data/trainer_graphics/*.json` | inside the builder |
| **`narcgfx` folders** | `a/0/0/7`, `a/0/0/8` | named PNG/pal/JSON + `members.json` | per member, in `members.json` |
| Copied as is (`prebuilt_files`) | the other 192 archives in `files/a/` | the binary NARC | none |

`narcgfx` works for any archive without code of its own: `members.json` is the table. The
generators couldn't take the prebuilt archives as they are: `ncgr_lz_gen` and `lz_gen`
always pass `-nopad`, but 641 compressed members in `files/a/` are padded, and many
archives mix several flag sets.

## 4. An archive folder

A folder holds the source files, in subfolders by what they are, and `members.json`:

```json
{
  "formats": {
    "ncgr_v101_sopc_8bpp_cut_lz": {"flags": ["-version101", "-sopc", "-bitdepth", "8"], "truncate": 65584, "lz": []},
    "nclr_8bpp_pcmp": {"flags": ["-bitdepth", "8", "-pcmp"]}
  },
  "members": [
    {"file": "unused/00000.png", "format": "ncgr_lz"},
    {"file": "unused/00001.NSCR"},
    {"file": "backgrounds/tilemap.NSCR"},
    {"file": "backgrounds/general/tiles.png", "format": "ncgr_v101_sopc_8bpp_cut_lz", "palette": "backgrounds/general/day.pal"},
```

**`members`** lists the archive's members in order: the first entry is member 0, the
next member 1, and so on. The code reads members by number, so the order is what links a
file to the code; the file name is for people.

**The extension says what a file becomes** (pokeemerald's pattern rules):

| Extension | Becomes | |
|---|---|---|
| `.png` | NCGR (tiles) | indexed; the build reads only the indices |
| `.pal` | NCLR (palette) | JASC |
| `.NCER.json` | NCER (cells) | [graphics.md §8](graphics.md#8-cells-and-animations) |
| `.NANR.json` | NANR (cell animation) | |
| anything else | copied as it is | `.NSCR` tilemaps, and the few graphics `nitrogfx` can't rebuild byte for byte (§10) |

**An entry** has:

| Key | Meaning |
|---|---|
| `file` | the source, relative to the folder |
| `format` | a name from `formats`: the header the retail file had (§9) |
| `cell` | on a sprite's PNG: the `.NCER.json` whose cells lay out the picture. Without it, the PNG is a strip of tiles in storage order |
| `palette`, `palette_row` | which `.pal` (and which 16-color row of it, for 4bpp graphics) the game shows this picture with. Only `narcgfx color` reads it (§7) |

**A format** is a set of `nitrogfx` flags (§9) with a name made from them, like the flag
sets in `files/meson.build` (`VERSION101_SOPC_NCGR_FLAGS`). `lz` compresses the result
(`[]` pads to 4 bytes, `["-nopad"]` doesn't, `["-nopad", "-extfmt"]` is the `0x11`
header); `truncate` cuts the NCGR before compressing (the battle backgrounds announce an
SOPC section their data doesn't have). A new file takes the format of the files like it.

**The build.** `files/a/0/0/meson.build` runs `narcgfx.py build` on each folder:

```meson
foreach narc : [['7', 'battle_backgrounds'], ['8', 'battle_sprites']]
    nitrofs_files += custom_target(narc[1],
        input : files('../../../../graphics' / narc[1] / 'members.json'),
        output : narc[0],
        command : [narcgfx_py, 'build', '@INPUT@', '@OUTPUT@', '--nitrogfx', nitrogfx_exe,
                   '--nitroarc', nitroarc_exe, '--work', '@PRIVATE_DIR@', '--depfile', '@DEPFILE@'],
        depfile : narc[1] + '.d',
        depend_files : narcgfx_depends,
    )
endforeach
```

The depfile lists every source, so changing one PNG rebuilds that archive.
`tools/narcgfx/test_narcgfx.py` checks that both folders give the retail archives, and
that every file in a folder is in its `members.json` exactly once.

## 5. `graphics/battle_backgrounds/` (`a/0/0/7`)

Everything the battle draws on background layers: the picture behind the Pokémon, the
backgrounds of move animations, and the touch screen.

| Path | What | Members | Loaded by |
|---|---|---|---|
| `backgrounds/<name>/tiles.png` | the battle background, one folder per `BATTLE_BG_*` (`general`, `ocean`... `battle_hall`, 23): 256×256, 8bpp | `id + 3` | `Battle_InitBackgrounds` (`src/battle/battle_main.c`), `BattleSystem_ReinitMainBgLayers` (`src/battle/battle_022378C0.c`) |
| `backgrounds/<name>/day.pal`, `evening.pal`, `night.pal` | its palettes by time of day; backgrounds 6-22 read only `day.pal` | `0xB0 + id × 3 + time` | the same |
| `backgrounds/tilemap.NSCR` | the tilemap shared by all of them | 2 | the same |
| `move_backgrounds/<name>/tiles.png`, `map.NSCR`, `palette.pal` | a move animation background, named after the first move that shows it (table below) | 46-172, 290-348 | `sBattleAnimBackgroundFiles` (`src/battle/battle_anim_system.c`) |
| `move_backgrounds/<name>/map_flipped.NSCR`, `map_contest.NSCR` | its tilemap when the target is on the player's side / in a contest, where it differs | | the same |
| `move_backgrounds/<name>/<move>.pal` | another palette for the same picture, used by `<move>` (`surf/muddy_water.pal`) | | the same |
| `move_backgrounds/battler_copy.NSCR` | the tilemap a Pokémon's picture is copied into (animation command `CopyBattlerToBg`) | 268 | `battle_anim_system.c` |
| `move_window_backgrounds/stat_up`, `stat_down`, `restore_hp`, `metal` | the backgrounds seen through a Pokémon's shape (stat changes, HP restore; Harden, Iron Defense, Iron Tail, Metal Claw) | 48-55, 291-294 | `gBattleAnimObjWindowBgFiles` (`asm/battle_anim_data.s`) |
| `touch_screen/tiles.png`, `palette.pal` | the bottom screen during battle; `frontier_tiles.png`, `frontier_palette.pal` in the Battle Frontier | 28, 246, 173, 349 | `src/battle/battle_input.c` |
| `touch_screen/command.NSCR`, `fight.NSCR`, `target.NSCR`, `two_options.NSCR`, `backdrop.NSCR`... | the tilemap of each menu (`*_layer2` is the second layer of the same menu) | 36-43, 174 | `sBottomScreenBgTilemapId`, `battle_input.c` |
| `touch_screen/tint/<name>.pal`, `highlight/<name>.pal` | the touch screen's tint and button highlight for each battle background (0-17; the Frontier ones use the defaults) | 247-263, 271-289, 350 | `sBackgroundPaletteIds`, `battle_input.c` |
| `trade/mon_picture.NSCR`, `mon_picture_not_flipped.NSCR` | the Pokémon's frame in the trade animation | 266, 267 | `src/application/trade_sequence/trade_sequence.c` |
| `unused/NNNNN.*` | 36 members nothing loads; named by member number | | |

Move animation backgrounds by the id the animation scripts use (`SwitchBackground`,
`SetBackground`...; files `a/0/1/0` and `a/0/6/1`). Several ids share a picture with
another palette, in the same folder:

| Id | Folder | Palette | Used by |
|---|---|---|---|
| 0 | `mega_kick` | `palette` | Mega Kick |
| 1 | `mega_kick` | `palette` | Dynamic Punch |
| 2 | `hyper_beam` | `megahorn` | Megahorn |
| 3 | `mega_kick` | `palette` | Superpower |
| 4 | `mega_kick` | `palette` | Psycho Boost |
| 5 | `mega_kick` | `giga_impact` | Giga Impact |
| 6 | `double_edge` | `palette` | Double-Edge |
| 7 | `power_whip` | `palette` | Power Whip |
| 8 | `double_edge` | `unused_8` | no script |
| 9 | `hydro_pump` | `palette` | Hydro Pump |
| 10 | `hydro_pump` | `palette` | Mist Ball |
| 11 | `hyper_beam` | `aura_sphere` | Aura Sphere |
| 12 | `hydro_pump` | `focus_blast` | Focus Blast |
| 13 | `hydro_pump` | `gunk_shot` | Gunk Shot |
| 14 | `hyper_beam` | `palette` | Hyper Beam |
| 15 | `brave_bird` | `unused_15` | no script |
| 16 | `brave_bird` | `palette` | no script |
| 17 | `hyper_beam` | `hydro_cannon` | Hydro Cannon |
| 18 | `brave_bird` | `palette` | Brave Bird, Sky Attack |
| 19 | `thunder` | `palette` | Thunder |
| 20 | `confusion` | `palette` | Confusion |
| 21 | `selfdestruct` | `palette` | Selfdestruct |
| 22 | `fire_blast` | `palette` | Fire Blast |
| 23 | `waterfall` | `palette` | Waterfall |
| 24 | `nightmare` | `palette` | Nightmare |
| 25 | `aeroblast` | `palette` | Aeroblast |
| 26 | `zap_cannon` | `palette` | Zap Cannon |
| 27 | `zap_cannon` | `volt_tackle` | Volt Tackle |
| 28 | `outrage` | `palette` | Outrage |
| 29 | `sacred_fire` | `palette` | Sacred Fire |
| 30 | `outrage` | `palette` | no script |
| 31 | `focus_punch` | `palette` | Focus Punch |
| 32 | `focus_punch` | `palette` | Overheat |
| 33 | `focus_punch` | `palette` | Flare Blitz |
| 34 | `frenzy_plant` | `palette` | Frenzy Plant |
| 35 | `water_pulse` | `palette` | Water Pulse, Whirlpool |
| 36 | `close_combat` | `palette` | Agility, Close Combat |
| 37 | `unused_37` | `palette` | no script |
| 38 | `leaf_storm` | `palette` | Leaf Storm |
| 39 | `rock_wrecker` | `palette` | Rock Wrecker |
| 40 | `head_smash` | `palette` | Head Smash |
| 41 | `spacial_rend` | `palette` | Spacial Rend |
| 42 | `lunar_dance` | `palette` | Lunar Dance |
| 43 | `magma_storm` | `palette` | Magma Storm |
| 44 | `dark_void` | `palette` | Dark Void |
| 45 | `unused_45` | `palette` | no script |
| 46 | `unused_46` | `palette` | no script |
| 47 | `extreme_speed` | `palette` | Agility, Extreme Speed |
| 48 | `surf` | `palette` | Surf |
| 49 | `surf` | `muddy_water` | Muddy Water |
| 50 | `blizzard` | `palette` | Blizzard |
| 51 | `seismic_toss` | `palette` | Seismic Toss |
| 52 | `psychic` | `palette` | Psychic |
| 53 | `fissure` | `palette` | Fissure |
| 54 | `moonlight` | `palette` | Moonlight |
| 55 | `fly` | `palette` | Fly, Sky Uppercut |
| 56 | `cosmic_power` | `palette` | Cosmic Power, Wish |
| 57 | `trick_room` | `palette` | Trick Room |
| 58 | `hyper_fang` | `palette` | Hyper Fang |

"no script": no move or effect animation uses the id; the folders `unused_37`,
`unused_45`, `unused_46` and the palettes `unused_8`, `unused_15` exist only for them.
The Confusion palette (`confusion/palette.NCLR`) is kept binary (§10).

## 6. `graphics/battle_sprites/` (`a/0/0/8`)

The battle's sprites, plus the type icons the rest of the game shares. Sprites are drawn
as pictures through their cells (`"cell"` in `members.json`).

| Path | What | Members | Loaded by |
|---|---|---|---|
| `platforms/<name>/player.png` (256×32), `enemy.png` (128×64) | the platforms, one folder per `TERRAIN_*` | 127, 130, 133-176 | `sPlayerTerrainCharFiles`, `sEnemyTerrainCharFiles` (`src/battle/battle_terrain.c`) |
| `platforms/<name>/day.pal`, `evening.pal`, `night.pal` | their palettes by time of day | 1-69 | `sTerrainPaletteFiles` |
| `platforms/player_cells.NCER.json`, `player_anim.NANR.json`, `enemy_*` | the layout shared by all platforms of a side | 128, 129, 131, 132 | `battle_terrain.c` |
| `type_icons/<type>.png` | the type icons (`fire`... `mystery`) and contest categories (`cool`, `beauty`, `cute`, `smart`, `tough`), 32×16 | 219-241 | `sTypeIconGfxCharFileIds` (`src/type_icon_resources.c`); the summary, bag, PC, battle and more |
| `type_icons/category_physical.png`, `_special`, `_status` | the move category icons | 244-246 | `sMoveCategoryGfxCharFileIds` |
| `type_icons/palette.pal`, `cells.NCER.json`, `anim.NANR.json` | shared by all icons; the palette has 3 rows, picked per type by `sTypeIconGfxPlttOverrides` (`"palette_row"`) | 74, 242, 243 | the same |
| `balls/<ball>/tiles.png`, `cells`, `anim`, `palette.pal` | the thrown ball, one folder per ball (`master`... `sport`, `park`), and `safari_rock`, `safari_bait` | 83-109, 259-339 | `gBallSpriteResources` (`asm/battle_anim_data.s`) |
| `hp_boxes/<box>/` (`player_single`, `enemy_double_1`... `safari`, `arrow`), `palette.pal`, `safari_palette.pal` | the HP boxes and the arrow over the active Pokémon | 71, 81, 183-203, 253-255 | `src/battle/battle_hp_bar.c` |
| `party_gauge/` | the row of balls when a trainer sends out | 110, 340-342 | `src/battle/party_gauge.c` |
| `cursor/` | the cursor for the D-pad on the touch screen | 80, 250-252 | `src/battle/battle_cursor.c` |
| `level_up_box/` | the stat window on level up | 82, 256-258 | `src/battle/battle_command.c` |
| `touch_screen/palette.pal`, `player_balls/`, `opponent_balls/`, `bug_contest_net/` | sprites on the touch screen | 72, 204-209, 343-345 | `src/battle/battle_input.c` |
| `mon_picture/`, `frontier_mon_picture/` | an 80×80 sprite whose tiles the code replaces with a Pokémon's picture | 75-78, 111-114 | Pokédex, PC, Hall of Fame, battle animations, Frontier |
| `unused/` | members nothing loads: an unused ball, frames, an arrow... | 0, 70, 73, 79, 115-126, 177-182, 210-218, 247-249 | |

Members shared between ids appear once, under the first one: `TERRAIN_UNKNOWN` has no
folder (it uses `puddle/player.png`, `great_marsh/enemy.png` and Great Marsh's palettes),
so changing those changes both. Several platforms are identical copies in separate files
(the Elite Four players', the Frontier's): change each one you want changed.

## 7. Editing

- **Draw on the PNG, keep it indexed and the same size**
  ([graphics.md §6](graphics.md#6-drawing-the-png)). Pixel values are palette indices;
  change colors in the `.pal`.
- **Colors.** The PNGs carry the colors of their `"palette"` so they look as in game.
  After changing a `.pal`, refresh them (the build ignores PNG colors, so this changes
  nothing in the ROM):

  ```bash
  python3 tools/narcgfx/narcgfx.py color graphics/battle_sprites/members.json
  ```

- **Sprites** are pictures laid out by their cells: draw where the picture is, and keep
  to the area the cells cover (a pixel outside every cell is lost).
- **Rules of the screen still apply**: battle backgrounds use colors 0-111 and a fixed
  tile layout ([battle-backgrounds.md §3](battle-backgrounds.md#3-how-the-picture-is-laid-out)).
- **Renaming** a file: `narcgfx.py move graphics/battle_sprites/members.json OLD NEW`
  renames it and every entry that points at it. Keep the extension.
- **Adding a member:** put the file in the folder and add its entry **at the end** of
  `members`, with the format of a file like it. Its member number is its position; the
  code must ask for that number. Never insert in the middle: every member after it would
  move.

Then `make release` (plain `make` fails its checksum test after any change, as for every
mod).

## 8. Converting another archive

Build once (`make`) so the tools exist. For an archive `files/a/X/Y/Z`:

```bash
T=$PWD/build/heartgold.us/tools
GFX=$T/nitrogfx/nitrogfx
N=tools/narcgfx/narcgfx.py

# 1. what's in it; "ok" members become editable, the rest stay binary
python3 $N flags files/a/0/1/4 --nitrogfx $GFX

# 2. every member as a numbered file, plus members.json
python3 $N export files/a/0/1/4 graphics/field_menus --nitrogfx $GFX

# 3. names: find what each member is (graphics.md §3) and move it; here the start
#    menu's icons (src/start_menu.c loads tiles 64, cells 62)
python3 $N move graphics/field_menus/members.json 00064.png start_menu/icons.png
python3 $N move graphics/field_menus/members.json 00062.NCER.json start_menu/icons.NCER.json

# 4. sprites as pictures, and their colors (after adding "palette" to entries by hand)
python3 $N cells graphics/field_menus/members.json start_menu/icons.png start_menu/icons.NCER.json --nitrogfx $GFX
python3 $N color graphics/field_menus/members.json
```

`cells` checks that the picture gives back the same tiles and refuses otherwise (cells
that overlap or leave tiles out); such a sprite stays a strip.

5. **Build it**: in the archive's `meson.build`, remove the name from `prebuilt_files` and
   add a `custom_target` like the one in §4 (or add the pair to its `foreach`), with `../`
   up to the repository root. Then delete `files/a/X/Y/Z`.
6. **Check**: `make` passes all four checksums, and so does `make soulsilver` (every
   archive in `files/a/` is the same in both games). Add the folder to `FOLDERS` in
   `tools/narcgfx/test_narcgfx.py`.

Members you can't trace keep their numbers under `unused/` or as they are; names can
come later with `move`.

## 9. The flags, read from the headers

`narcgfx` reads each file's header and picks the flags below; every combination was then
checked by rebuilding. This completes [graphics.md §5](graphics.md#5-picking-nitrogfxs-flags).

**NCGR** (offsets in the decompressed file):

| Header | Flag | Members in `files/a/` |
|---|---|---|
| version `01 01` at 6 | `-version101` | almost all |
| 2 sections at 14 | `-sopc` | 935 |
| `ff ff` at 0x18 (no fixed size: sprites) | `-clobbersize` | 1,651 |
| `04` at 0x1C | `-bitdepth 8` | 195 |
| `10 00 00 00` / `10 00 10 00` / `10 00 20 00` / `10 00 30 00` at 0x20 | `-mappingtype 32` / `64` / `128` / `256` | |
| `01` at 0x24 (a bitmap, not 8×8 tiles; the dress-up accessories in `a/0/2/6`) | `-scan` | 119 |
| more bytes in the header than in the data | build, then cut (`truncate`) | 23 (the battle backgrounds) |

**NCLR:**

| Header | Flag |
|---|---|
| `03` / `04` at 0x18 | `-bitdepth 4` / `-bitdepth 8` |
| fewer than 256 colors | `-nopad` |
| the size at 0x20 is `0x200` minus the real size (a retail quirk) | `-invertsize` |
| a PCMP section | `-pcmp`; if its first palette number isn't 0, `-pcmp -start N` |
| a byte at 0x1A | `-comp N` |
| the last color is the letters `IR` | `-ir` |

**LZ:** first byte `0x10`: try padded (no flag) and `-nopad`; `0x11`: `-nopad -extfmt`.
In `files/a/`: 2,054 `-nopad`, 641 padded, 380 `-extfmt`.

## 10. What stays binary

Of the 6,506 2D graphics members in the 123 archives of `files/a/` that have any
(counted before `a/0/0/7` and `a/0/0/8` became folders), these don't come back byte for
byte and are kept as binary files in the export:

| What | Count | Where | Why |
|---|---|---|---|
| NSCR tilemaps | 1,072 | everywhere | `nitrogfx` can't export them ([graphics.md §9](graphics.md#9-tilemaps)) |
| extended palettes (16 × 256 colors, `01` at 0x1C) | 115 | `a/2/4/5` (68), `a/1/8/3` (35), `a/2/1/9` (11), `a/1/9/9` (1) | the `.pal` export keeps only the first 16 colors |
| palettes with a gap in their PCMP list (rows 0 and 9, or 0 and 9-14) | 6 | one each in `a/0/0/7`, `a/0/1/4`, `a/0/8/7`, `a/1/1/0`, `a/1/2/7`, `a/1/5/4` | `-pcmp` only writes consecutive rows |
| NCGRs | 6 | `a/2/1/9` (3), `a/2/4/5` (1), `a/1/4/9` (2) | `nitrogfx`'s compressor gives other bytes for the first 4; the 2 in `a/1/4/9` need `-vram`, which isn't read from the header |

They still load and can still be changed by hand ([graphics.md §4](graphics.md#4-changing-a-binary-archive));
`narcgfx flags` names each one. A file that doesn't match retail would probably still
load (the loaders read the sections they need), but that is not what `narcgfx` aims for.

The other 71 prebuilt archives hold no 2D graphics (3D models, textures, data); `export`
works on them too, but gives only binary files.

## Where to look

| What | File |
|---|---|
| the two folders | `graphics/battle_backgrounds/`, `graphics/battle_sprites/` |
| the build rule | `files/a/0/0/meson.build`; `narcgfx_py` in `meson.build` |
| build, export, flags, move, cells, color | `tools/narcgfx/narcgfx.py`; tests in `tools/narcgfx/test_narcgfx.py` |
| reading and packing NARCs | `tools/pokedata/pokedata.py` (`narc_members`, `pack`) |
| the other builders | `files/meson.build` (generators), `tools/pokedata/trainer_pics.py` |
| prebuilt archives | `prebuilt_files` in `files/a/*/*/meson.build` |

## Not verified

- Both folders build the retail archives (`make` and `make soulsilver`, all checksums
  OK); the other 192 prebuilt archives were exported and rebuilt with `narcgfx` outside
  the build and compared with `cmp`: all identical.
- No edited picture was looked at in the game.
- What each member is was traced from the loaders and tables named above, and for move
  backgrounds by decoding the animation scripts; the move names in §5 are only as good as
  that decoding. Members under `unused/` have no loader in `src/` or `asm/`.
- The "used by" column of the appendix is the source files that name the archive;
  archives with "not traced" are loaded through a variable or a table.
- pokeemerald was read at its master branch of October 2026; its build has changed over
  the years (`INCBIN` → `INCGFX`, `battle_terrain` → `battle_environment`).

## Appendix: prebuilt archives with 2D graphics

The archives as they were in retail (`a/0/0/7` and `a/0/0/8` are now folders). "Editable" is what `narcgfx export` turns into PNG, `.pal` or JSON; "kept binary" is
copied unchanged. Counts are members.

| Archive | Used by | Members | Editable | Kept binary |
|---|---|---|---|---|
| `a/0/0/7` | **now `graphics/battle_backgrounds/`** (§5) | 351 | 81 NCGR, 171 NCLR | 98 NSCR, 1 NCLR |
| `a/0/0/8` | **now `graphics/battle_sprites/`** (§6) | 346 | 125 NCGR, 109 NCLR, 56 NCER, 56 NANR |  |
| `a/0/0/9` | `battle_anim_system` | 32 | 16 NCLR | 16 bin |
| `a/0/1/4` | `start_menu`, `touch_save_app`, `naming_screen` | 78 | 24 NCGR, 10 NCLR, 19 NCER, 19 NANR | 5 NSCR, 1 NCLR |
| `a/0/1/5` | `bag_app`, `bag_app_display` | 95 | 15 NCGR, 13 NCLR, 8 NCER, 8 NANR | 18 NSBTP, 16 NSBCA, 13 NSCR, 2 NSBMD, 2 NSBTA |
| `a/0/1/9` | `pc_box`, `pc_box_text`, `pc_box_sprites` | 87 | 35 NCGR, 30 NCLR, 5 NCER, 5 NANR | 12 NSCR |
| `a/0/2/2` | `battle_anim_system` | 37 | 37 NCGR |  |
| `a/0/2/3` | `battle_anim_system` | 39 | 39 NCLR |  |
| `a/0/2/4` | `battle_anim_system` | 37 | 37 NCER |  |
| `a/0/2/5` | `battle_anim_system` | 37 | 37 NANR |  |
| `a/0/2/6` | `accessory_portrait`, `dress_up` | 236 | 150 NCGR, 26 NCLR, 8 NCER, 8 NANR | 43 NSCR, 1 bin |
| `a/0/2/8` | not traced | 7 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 1 NSCR |
| `a/0/3/5` | `font_sprite` | 12 | 12 NCER |  |
| `a/0/3/6` | `render_window_icons` | 54 | 53 NCGR, 1 NCLR |  |
| `a/0/3/8` | `render_window_icons`, `alph_puzzle`, `evolution_scene` | 51 | 26 NCGR, 23 NCLR, 1 NCER, 1 NANR |  |
| `a/0/3/9` | `pokemon_summary`, `link_battle_screen`, `battle_party_menu` | 137 | 88 NCGR, 9 NCLR, 14 NCER, 14 NANR | 12 NSCR |
| `a/0/4/5` | not traced | 9 | 3 NCGR, 2 NCLR, 2 NCER, 2 NANR |  |
| `a/0/4/8` | not traced | 53 | 14 NCGR, 8 NCLR, 13 NCER, 13 NANR | 5 NSCR |
| `a/0/4/9` | `overlay_trainer_card_main_sprites`, `overlay_trainer_card_main`, `pokeathlon_course_mon_gfx` | 78 | 22 NCGR, 42 NCLR, 2 NCER, 2 NANR | 10 NSCR |
| `a/0/5/0` | not traced | 3 | 1 NCGR, 1 NCLR | 1 NSCR |
| `a/0/5/1` | not traced | 134 | 65 NCGR, 65 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/0/5/2` | `wireless_trade_select_mon`, `main_menu_util` | 13 | 4 NCGR, 1 NCLR, 2 NCER, 2 NANR | 4 NSCR |
| `a/0/5/3` | not traced | 116 | 71 NCGR, 45 NCLR |  |
| `a/0/5/4` | not traced | 21 | 2 NCGR, 5 NCLR, 2 NCER, 2 NANR | 10 NSCR |
| `a/0/6/0` | `bag_app_display`, `touch_mart_app`, `shop_menu` | 26 | 6 NCGR, 5 NCLR, 3 NCER, 3 NANR | 9 NSCR |
| `a/0/6/2` | not traced | 8 | 2 NCGR, 2 NCLR, 2 NCER, 2 NANR |  |
| `a/0/6/3` | `weather_manager` | 59 | 16 NCGR, 14 NCLR, 9 NCER, 9 NANR | 7 NSCR, 4 bin |
| `a/0/6/4` | not traced | 11 | 3 NCGR, 2 NCLR, 3 NCER, 3 NANR |  |
| `a/0/6/7` | not traced | 130 | 28 NCGR, 27 NCLR, 18 NCER, 18 NANR | 39 NSCR |
| `a/0/7/1` | `battle_party_menu` | 28 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 22 NSCR |
| `a/0/7/2` | `options_app` | 20 | 5 NCGR, 4 NCLR, 4 NCER, 4 NANR | 3 NSCR |
| `a/0/7/3` | `union_chat_log` | 8 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/0/7/6` | `easy_chat_app_view` | 17 | 5 NCGR, 4 NCLR, 1 NCER, 1 NANR | 6 NSCR |
| `a/0/7/7` | `battle_bag_menu` | 4 | 1 NCGR, 1 NCLR | 2 NSCR |
| `a/0/7/8` | `drawing_session` | 9 | 3 NCGR, 2 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/0/7/9` | `mailbox_app`, `mail_view` | 37 | 12 NCGR, 12 NCLR | 13 NSCR |
| `a/0/8/0` | not traced | 16 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 8 NSCR |
| `a/0/8/3` | not traced | 4 | 1 NCGR, 1 NCLR, 1 NCER, 1 NANR |  |
| `a/0/8/5` | `palpad` | 18 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 10 NSCR |
| `a/0/8/7` | `ball_capsule_editor` | 120 | 91 NCGR, 6 NCLR, 9 NCER, 9 NANR | 4 NSCR, 1 NCLR |
| `a/0/8/8` | `nintendo_wfc_connect_unused_session`, `nintendo_wfc_connect`, `wii_message_settings_screen` | 48 | 10 NCGR, 12 NCLR, 3 NCER, 3 NANR | 20 NSCR |
| `a/0/8/9` | `trade_sequence_approach`, `trade_sequence_receive`, `trade_sequence` | 28 | 8 NCGR, 8 NCLR, 2 NCER, 2 NANR | 7 NSCR, 1 NSBMD |
| `a/0/9/1` | `overlay_trainer_card_signature` | 10 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/0/9/7` | `hall_of_fame_showcase` | 17 | 5 NCGR, 4 NCLR, 3 NCER, 3 NANR | 2 NSCR |
| `a/1/0/0` | `nintendo_wfc_connect_unused`, `spin_trade_group_app`, `gts` | 49 | 13 NCGR, 11 NCLR, 3 NCER, 3 NANR | 19 NSCR |
| `a/1/0/1` | `register_hall_of_fame` | 20 | 5 NCGR, 4 NCLR, 3 NCER, 3 NANR | 5 NSCR |
| `a/1/0/4` | `link_battle_screen` | 9 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 3 NSCR |
| `a/1/0/9` | `encounter_effect`, `encounter_effect_leaders`, `frontier_brain_intro` | 242 | 64 NCGR, 65 NCLR, 44 NCER, 44 NANR | 23 NSCR, 2 bin |
| `a/1/1/0` | `move_relearner_app` | 22 | 6 NCGR, 3 NCLR, 4 NCER, 4 NANR | 4 NSCR, 1 NCLR |
| `a/1/1/3` | `migrate_from_agb`, `mystery_gift_app`, `lock_capsule_card` | 50 | 14 NCGR, 14 NCLR, 6 NCER, 6 NANR | 10 NSCR |
| `a/1/1/5` | `evolution_scene`, `hatch_egg_gfx` | 11 | 3 NCGR, 3 NCLR, 2 NCER, 2 NANR | 1 NSCR |
| `a/1/1/8` | `battle_room_results` | 11 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 3 NSCR |
| `a/1/2/2` | not traced | 67 | 25 NCGR, 8 NCLR, 5 NCER, 5 NANR | 20 NSCR, 3 NSBMD, 1 NSBTA |
| `a/1/2/3` | `geonet_globe_app` | 8 | 1 NCGR, 1 NCLR | 5 NSBMD, 1 NSCR |
| `a/1/2/4` | not traced | 4 | 1 NCGR, 1 NCLR, 1 NCER, 1 NANR |  |
| `a/1/2/6` | `certificates_app` | 25 | 8 NCGR, 7 NCLR, 2 NCER, 2 NANR | 6 NSCR |
| `a/1/2/7` | not traced | 25 | 5 NCGR, 4 NCLR, 2 NCER, 2 NANR | 11 NSCR, 1 NCLR |
| `a/1/3/0` | not traced | 7 | 3 NCGR, 1 NCLR | 3 NSCR |
| `a/1/4/2` | not traced | 31 | 10 NCGR, 7 NCLR, 4 NCER, 4 NANR | 6 NSCR |
| `a/1/4/9` | `pokeathlon_course_mon_gfx` | 12 | 2 NCGR, 4 NCER, 4 NANR | 2 NCGR |
| `a/1/5/1` | `box_mon_selector` | 9 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 3 NSCR |
| `a/1/5/3` | `pokeathlon_course_sprites` | 38 | 12 NCGR, 2 NCLR, 12 NCER, 12 NANR |  |
| `a/1/5/4` | `pokeathlon_course_ceremony`, `pokeathlon_results_announcement` | 35 | 12 NCGR, 8 NCLR, 5 NCER, 5 NANR | 4 NSCR, 1 NCLR |
| `a/1/5/6` | `pokeathlon_hurdle_dash_track`, `pokeathlon_hurdle_dash` | 33 | 8 NCGR, 7 NCLR, 7 NCER, 7 NANR | 4 NSCR |
| `a/1/5/7` | not traced | 7 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 1 NSCR |
| `a/1/5/8` | not traced | 7 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 1 NSCR |
| `a/1/5/9` | not traced | 7 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 1 NSCR |
| `a/1/6/0` | `pokeathlon_results_plates`, `pokeathlon_results_announcement` | 10 | 3 NCGR, 2 NCLR, 1 NCER, 1 NANR | 3 NSCR |
| `a/1/6/1` | not traced | 4 | 1 NCGR, 1 NCLR, 1 NCER, 1 NANR |  |
| `a/1/6/2` | `certificates_app`, `pokemon_summary`, `wireless_trade_select_mon` | 79 | 34 NCGR, 17 NCLR, 6 NCER, 3 NANR | 19 NSCR |
| `a/1/6/4` | `battle_finger` | 4 | 1 NCGR, 1 NCLR, 1 NCER, 1 NANR |  |
| `a/1/6/6` | `safari_area_customizer` | 30 | 15 NCGR, 4 NCLR, 2 NCER, 2 NANR | 7 NSCR |
| `a/1/6/7` | `pokeathlon_circle_push_field`, `pokeathlon_circle_push` | 33 | 8 NCGR, 8 NCLR, 3 NCER, 3 NANR | 11 NSCR |
| `a/1/6/8` | `pokeathlon_lamp_jump` | 15 | 5 NCGR, 3 NCLR, 1 NCER, 1 NANR | 5 NSCR |
| `a/1/7/1` | `photo_album_app`, `view_photo` | 13 | 4 NCGR, 2 NCLR, 1 NCER, 1 NANR | 5 NSCR |
| `a/1/7/3` | `bug_contest_swap_mon` | 10 | 4 NCGR, 2 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/1/7/6` | `overlay_mic_test` | 22 | 6 NCGR, 6 NCLR, 4 NCER, 4 NANR | 2 NSCR |
| `a/1/7/7` | `pokeathlon_event_record`, `pokeathlon_course_record`, `pokeathlon_util` | 74 | 22 NCGR, 16 NCLR, 7 NCER, 7 NANR | 22 NSCR |
| `a/1/7/8` | `pokeathlon_relay_run_hud`, `pokeathlon_relay_run` | 18 | 4 NCGR, 4 NCLR, 2 NCER, 2 NANR | 6 NSCR |
| `a/1/7/9` | `vs_recorder_frontier_record`, `vs_recorder_screen`, `field2d_char_sprite` | 319 | 154 NCGR, 153 NCLR, 6 NCER, 6 NANR |  |
| `a/1/8/1` | not traced | 12 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 4 NSCR |
| `a/1/8/3` | `battle_room_results`, `battle_arcade_game_board`, `frontier_map_bg_animation` | 197 | 50 NCGR, 14 NCLR | 98 NSCR, 35 NCLR |
| `a/1/8/4` | `battle_castle_display`, `battle_factory_app_gfx`, `battle_arcade_game_board` | 65 | 16 NCGR, 13 NCLR, 18 NCER, 18 NANR |  |
| `a/1/8/6` | `field2d_char_sprite` | 49 | 16 NCGR, 1 NCLR, 16 NCER, 16 NANR |  |
| `a/1/8/7` | `spin_trade_app` | 27 | 3 NCGR, 2 NCLR | 11 NSBMD, 6 NSCR, 5 NSBCA |
| `a/1/8/9` | `plaza_game_swalot_plop`, `plaza_game_mime_jr_top` | 47 | 5 NCGR, 5 NCLR, 3 NCER, 3 NANR | 14 NSBMD, 7 NSCR, 6 NSBCA, 2 NSBTP, 2 NSBTA |
| `a/1/9/0` | `code_entry`, `code_entry_gfx` | 23 | 6 NCGR, 7 NCLR, 4 NCER, 4 NANR | 2 NSCR |
| `a/1/9/1` | `vs_recorder`, `vs_recorder_ui`, `vs_recorder_box_data` | 258 | 62 NCGR, 84 NCLR, 19 NCER, 19 NANR | 74 NSCR |
| `a/1/9/2` | `wifi_plaza_visitor_profiles` | 57 | 14 NCGR, 5 NCLR, 12 NCER, 12 NANR | 10 NSCR, 4 NSBMD |
| `a/1/9/3` | `plaza_game_mime_jr_top` | 86 | 10 NCGR, 8 NCLR, 6 NCER, 6 NANR | 28 NSBMD, 16 NSBCA, 10 NSCR, 2 NSBTA |
| `a/1/9/6` | `plaza_news`, `wifi_plaza_survey` | 7 | 2 NCGR, 1 NCLR | 4 NSCR |
| `a/1/9/7` | `wii_message_settings_screen` | 13 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 5 NSCR |
| `a/1/9/8` | `wobbuffet_pop`, `plaza_game_mime_jr_top`, `plaza_game` | 27 | 7 NCGR, 7 NCLR, 4 NCER, 4 NANR | 4 NSCR, 1 bin |
| `a/1/9/9` | `wobbuffet_pop_balloon_mesh`, `wobbuffet_pop`, `wobbuffet_pop_scene` | 59 | 10 NCGR, 5 NCLR, 3 NCER, 3 NANR | 22 NSBMD, 10 NSCR, 4 NSBCA, 1 NCLR, 1 NSBTX |
| `a/2/0/5` | `scratch_off_cards` | 41 | 9 NCGR, 19 NCLR, 4 NCER, 4 NANR | 5 NSCR |
| `a/2/0/7` | `wifi_plaza_lobby_events`, `wifi_plaza_instrument`, `wifi_plaza_survey` | 208 | 50 NCGR, 8 NCLR, 18 NCER, 18 NANR | 42 NSCR, 39 NSBTX, 17 NSBMD, 12 NSBTP, 3 NSBCA, 1 NSBMA |
| `a/2/0/8` | `footprint_stamp` | 30 | 7 NCGR, 6 NCLR, 5 NCER, 5 NANR | 4 NSCR, 3 NSBMD |
| `a/2/1/3` | `wifi_plaza_room` | 57 | 18 NCGR, 3 NCLR, 18 NCER, 18 NANR |  |
| `a/2/1/5` | `spin_trade_group_app`, `spin_trade_app` | 19 | 5 NCGR, 5 NCLR, 4 NCER, 4 NANR | 1 NSCR |
| `a/2/1/6` | `berry_pots_app` | 140 | 67 NCGR, 67 NCLR, 2 NCER, 2 NANR | 2 NSCR |
| `a/2/1/7` | `pokeathlon_snow_throw`, `pokeathlon_snow_throw_display` | 22 | 6 NCGR, 5 NCLR, 3 NCER, 3 NANR | 5 NSCR |
| `a/2/1/8` | `apricorn_box_screens` | 11 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 3 NSCR |
| `a/2/1/9` | `pokeathlon_course_ui`, `pokeathlon_event_intro` | 62 | 19 NCGR, 2 NCLR, 1 NCER, 1 NANR | 25 NSCR, 11 NCLR, 3 NCGR |
| `a/2/2/3` | `safari_decoration` | 13 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 5 NSCR |
| `a/2/2/4` | `pokeathlon_pennant_capture_play`, `pokeathlon_pennant_capture_display` | 18 | 6 NCGR, 4 NCLR, 2 NCER, 2 NANR | 4 NSCR |
| `a/2/2/8` | not traced | 540 | 533 NCGR, 1 NCLR, 3 NCER, 3 NANR |  |
| `a/2/3/2` | `pokeathlon_block_smash` | 19 | 5 NCGR, 5 NCLR, 3 NCER, 3 NANR | 3 NSCR |
| `a/2/3/4` | `pokeathlon_goal_roll_display`, `pokeathlon_goal_roll_field`, `pokeathlon_goal_roll` | 20 | 6 NCGR, 5 NCLR, 2 NCER, 2 NANR | 5 NSCR |
| `a/2/3/5` | `pokeathlon_disc_catch_scoreboard`, `pokeathlon_disc_catch` | 27 | 6 NCGR, 5 NCLR, 3 NCER, 3 NANR | 10 NSCR |
| `a/2/3/6` | `nintendo_wfc_connect`, `number_entry` | 14 | 4 NCGR, 4 NCLR, 2 NCER, 2 NANR | 2 NSCR |
| `a/2/3/7` | `comm_club_buttons`, `evolution_scene`, `oaks_speech_yesnomenu` | 18 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 10 NSCR |
| `a/2/3/9` | `unown_report` | 16 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 8 NSCR |
| `a/2/4/0` | `pokeathlon_ring_drop_display` | 25 | 8 NCGR, 5 NCLR, 3 NCER, 3 NANR | 6 NSCR |
| `a/2/4/1` | `pokeathlon_box_graphics` | 8 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/2/4/2` | `aprijuice_screen` | 11 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 2 NSCR, 1 bin |
| `a/2/4/5` | `arceus_cinematic` | 208 | 68 NCGR, 1 NCLR, 1 NCER, 1 NANR | 68 NSCR, 68 NCLR, 1 NCGR |
| `a/2/4/7` | `pokewalker_app`, `pokewalker_ui` | 24 | 4 NCGR, 4 NCLR, 2 NCER, 2 NANR | 12 NSCR |
| `a/2/4/9` | `pokewalker_event_log` | 26 | 6 NCGR, 4 NCLR, 4 NCER, 4 NANR | 8 NSCR |
| `a/2/5/0` | `mailbox_app`, `mailbox_app_sprites` | 11 | 3 NCGR, 3 NCLR, 1 NCER, 1 NANR | 3 NSCR |
| `a/2/5/1` | `dowsing_mchn` | 8 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/2/5/7` | `pokewalker_app_modes` | 7 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 1 NSCR |
| `a/2/5/9` | `friend_roster_app` | 8 | 2 NCGR, 2 NCLR, 1 NCER, 1 NANR | 2 NSCR |
| `a/2/6/3` | `credits` | 192 | 46 NCGR, 45 NCLR, 44 NCER, 44 NANR | 13 NSCR |
