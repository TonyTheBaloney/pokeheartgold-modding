<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-25 -->

# Battle backgrounds and platforms

> AI-generated; not affiliated with pret. See AI.md at the repository root.

What a battle shows behind the Pokémon: the **background** (a picture on BG layer 3 of
the top screen, picked by the map) and the two **platforms** the Pokémon stand on
(sprites, picked by the tile the player stands on). This page covers how both are
chosen, the files they come from, the rules a new picture must follow, and how to change
or add one. The file formats and tools are explained in [graphics.md](graphics.md).

| pokeemerald | here |
|---|---|
| `BATTLE_TERRAIN_*` (one list for picture, platforms and Nature Power) | two lists: `BattleBg` (`BATTLE_BG_*`, the picture, 23 of them) and `Terrain` (`TERRAIN_*`, the platforms and Nature Power, 24) in `include/constants/battle.h` |
| `BattleSetup_GetTerrainId` (metatile behavior, then map type) | `BattleSetup_SetBattleBgAndTerrain` (`src/battle/battle_setup.c`): the picture from the map header, the platforms from the tile |
| `gBattleTerrainInfo` (`src/battle_bg.c`): tiles, tilemap, palette per terrain | `files/a/0/0/7`: one tileset and three palettes per background, **one tilemap shared by all** |
| `graphics/battle_terrain/<name>/tiles.png`, `map.bin`, `palette.pal` | binary NARC members; no PNG sources yet (export/import in §4) |
| platforms are part of the background picture | platforms are separate sprites (`files/a/0/0/8`), drawn into the background after the intro |
| one palette | three palettes for outdoor backgrounds: morning/day, evening, night |

## 1. How a battle picks its background and platforms

### The background

`BattleSetup_SetBattleBgAndTerrain` (`src/battle/battle_setup.c`):

1. `MapHeader_GetBattleBg(mapId)`: the map's `"battle_scene"` in
   `data/maps/<MapName>/map.json`.
2. If the player is surfing: `BATTLE_BG_OCEAN`.

Some battles set it in code instead: the Battle Frontier facilities set their own
(`src/frontier/battle_*_setup.c`), the Trainer House, fixed-level facilities and link
battles use `BATTLE_BG_BUILDING_1` (`src/overlay_25.c`, `BattleSetup_InitForFixedLevelFacility`,
`BattleSetup_InitForLinkBattleWithParty`), and a recorded battle replays the one it was
saved with.

| Id | Constant | Used by | Times of day |
|---|---|---|---|
| 0 | `BATTLE_BG_GENERAL` | 87 maps (routes) | 3 |
| 1 | `BATTLE_BG_OCEAN` | 4 maps, and every battle while surfing | 3 |
| 2 | `BATTLE_BG_CITY` | 22 maps | 3 |
| 3 | `BATTLE_BG_FOREST` | 5 maps | 3 |
| 4 | `BATTLE_BG_MOUNTAIN` | 5 maps | 3 |
| 5 | `BATTLE_BG_SNOW` | 2 maps | 3 |
| 6-8 | `BATTLE_BG_BUILDING_1` / `_2` / `_3` | 308 / 6 / 43 maps | 1 |
| 9-11 | `BATTLE_BG_CAVE_1` / `_2` / `_3` | 24 / 16 / 13 maps | 1 |
| 12-16 | `BATTLE_BG_WILL`, `_KOGA`, `_BRUNO`, `_KAREN`, `_LANCE` | one Elite Four room each | 1 |
| 17 | `BATTLE_BG_DISTORTION_WORLD` | no map (a Platinum leftover) | 1 |
| 18-22 | `BATTLE_BG_BATTLE_TOWER`, `_FACTORY`, `_ARCADE`, `_CASTLE`, `_HALL` | set by the Frontier code | 1 |

To give a map another background, change its `"battle_scene"` and build.

### Time of day

`BattleSystem_GetBgTimeOfDay` (`src/battle/battle_system.c`) picks one of three palettes,
for backgrounds 0-5 only:

| Time ([day-night-and-rtc.md](day-night-and-rtc.md)) | Palette |
|---|---|
| `RTC_TIMEOFDAY_MORN`, `RTC_TIMEOFDAY_DAY` | 0 |
| `RTC_TIMEOFDAY_EVE` | 1 |
| `RTC_TIMEOFDAY_NITE`, `RTC_TIMEOFDAY_LATE` | 2 |

Every other background always uses palette 0. The same number picks the platforms'
palette. (In a cave, `BattleSetup_InitFromSaveData` sets the battle's time to night, but
cave backgrounds have a single palette, so this doesn't change their look.)

### The platforms (`Terrain`)

`FieldSystem_GetTerrainFromStandingTile` (`src/battle/battle_setup.c`) looks at the
behavior of the tile under the player first:

| Tile | Terrain |
|---|---|
| ice | `TERRAIN_ICE` |
| tall grass, very tall grass | `TERRAIN_GRASS` |
| sand | `TERRAIN_SAND` |
| snow | `TERRAIN_SNOW` |
| mud | `TERRAIN_GREAT_MARSH` |
| cave floor | `TERRAIN_CAVE` |
| surfable water | `TERRAIN_WATER` |
| anything else | from the background, by `sBattleBgTerrains` (e.g. `BATTLE_BG_CITY` → `TERRAIN_BUILDING`, `BATTLE_BG_KOGA` → `TERRAIN_KOGA`) |

Fishing always gives `TERRAIN_WATER` (`BattleSetup_SetFishing`). Tile behaviors are
covered in [maps-and-warps.md](maps-and-warps.md).

The terrain also changes gameplay, so a new platform isn't only a picture:

| What | Where | Note |
|---|---|---|
| the move Nature Power calls | `BtlCmd_GetTerrainMove`, `sNaturePowerMoveTable` (`src/battle/battle_command.c`) | terrains above 12 count as 12 (`TERRAIN_WILL`, "indoors") |
| Secret Power's effect and animation | `BtlCmd_GetTerrainSecondaryEffect`; `sSecretPowerTerrainAnims` (`src/battle/battle_anim_system.c`, 24 entries; 24 and above show Tri Attack) | the same clamp |
| Camouflage's type | `BtlCmd_TryCamouflage`, `sCamouflageTypeTable` | the same clamp |
| Burmy's cloak after battle | `src/battle/battle_system.c`, the `SPECIES_BURMY` switch | unknown terrains give the plant cloak |

## 2. The files

### Backgrounds: `files/a/0/0/7`

The battle loads the picture in `Battle_InitBackgrounds` (`src/battle/battle_main.c`) and
again in `BattleSystem_ReinitMainBgLayers` (`src/battle/battle_022378C0.c`):

```c
GfGfxLoader_LoadCharData(NARC_a_0_0_7, backgroundId + 3, bgConfig, GF_BG_LYR_MAIN_3, 0, 0, TRUE, HEAP_ID_BATTLE);
PaletteData_LoadNarc(palette, NARC_a_0_0_7, backgroundId * 3 + 0xB0 + BattleSystem_GetBgTimeOfDay(battleSystem), HEAP_ID_BATTLE, PLTTBUF_MAIN_BG, 0, 0);
GfGfxLoader_LoadScrnData(NARC_a_0_0_7, 2, bgConfig, GF_BG_LYR_MAIN_3, 0, 0, TRUE, HEAP_ID_BATTLE);
```

| Member | What |
|---|---|
| 2 | the tilemap, **shared by every background**: 512×256 pixels, 8bpp, LZ-compressed NSCR |
| 3-25 | the tileset of background 0-22 (`backgroundId + 3`): 256×256 pixels = 1024 tiles, **8bpp** (256 colors), LZ-compressed NCGR |
| 176-244 (`0xB0`-`0xF4`) | the palettes, three per background (`0xB0 + backgroundId × 3 + time`): 256 colors each, NCLR. Backgrounds 6-22 have three too; only the first is read |
| 247-263, 271-289 | the bottom screen's tint per background (below) |
| the rest | the touch screen's graphics (`src/battle/battle_input.c`) |

The layer is set up by the third entry of `gBattleBgTemplates` (`asm/battle_main_data.s`):
BG3, 512×256, 256 colors, priority 3 (behind everything).

### Platforms: `files/a/0/0/8`

`BattleTerrain_LoadResources` (`src/battle/battle_terrain.c`) loads, for each side:

| | Player's side | Enemy's side |
|---|---|---|
| tiles (LZ NCGR, 4bpp, 128 tiles) | `sPlayerTerrainCharFiles[terrain]` (members 127-175) | `sEnemyTerrainCharFiles[terrain]` (members 130-176) |
| size | 256×32: four 64×32 pieces | 128×64: two 64×64 pieces |
| cells (NCER) / animation (NANR) | members 128 / 129 | members 131 / 132 |
| palette (16 colors, NCLR, members 1-69) | `sTerrainPaletteFiles[terrain][time]`, shared by both sides | |

The member lists are indexed by `Terrain`, so `TERRAIN_GRASS` (2) uses tiles 0x7F and
0x82 and palettes 1-3. The palette is loaded twice: as the sprites' palette, and into
row 7 of the background palette (colors 112-127). The second copy is for the next step.

**The platforms become part of the background.** During the intro the platforms are
sprites sliding in. When the intro ends, the server sends client command 46 and
`BattleSystem_SetBackground` (`src/battle/battle_system.c`) copies the background's tiles
from VRAM, draws the platform pixels into fixed tiles (color + 0x70, so they use row 7),
reloads the tiles, and frees the sprites. From then on, move animations that hide or
replace the background restore it from that copy.

### Other per-background data

| What | Where | Size |
|---|---|---|
| the color the screen is flooded with at the start of the intro, per background and time | `gBattleBgFillColors` in `asm/battle_main_data.s` (declared `[23][3]` in `src/battle/battle_main.c`) | 23 × 3 colors |
| the bottom screen's tint (palette row 0) and its touch-highlight palette | `sBackgroundPaletteIds` in `src/battle/battle_input.c`: members 247-263 / 271-287 for backgrounds 0-16, 288 / 289 for 17, `-1` (the defaults 246 / 271) for 18-22; Frontier battles always use 349 / 350 | 23 rows |
| which terrain a background gives when the tile doesn't decide | `sBattleBgTerrains` in `src/battle/battle_setup.c` | 23 |

## 3. How the picture is laid out

The tileset is 256×256 but the screen is 256×192, and the shared tilemap places the tiles
so:

```
tileset (PNG export, 256×256)                      top screen (BG3, x = 0)
y   0- 55   tile rows  0-6   ─── one to one ───►   y   0- 55   (sky / back wall)
y  56-159   tile rows  7-19  ─── mirrored ─────►   only the right half of the 512-wide
                                                   map, seen when the background scrolls
                                                   or shakes in a move animation
y 160-255   tile rows 20-31  ─── one to one ───►   y  56-151   (the ground; platforms)
                                                   y 152-191: behind the text box
```

For the battle itself, only PNG rows 0-55 and 160-255 matter. The rules, all checked
against the 23 retail backgrounds:

- **Colors 0-111 only** (palette rows 0-6). The intro restores exactly 112 colors from
  its saved copy (`RESTORE_BG_PALETTES` in `src/battle/battle_controller_opponent.c`),
  row 7 is overwritten by the platforms' palette, and rows 10 and 11 by the text box frame
  and the font. Every retail background stays within 0-111.
- **Tile 0 stays empty** (all color 0): the tilemap uses it under the text box. That is
  the 8×8 square at the PNG's top left.
- **The screen's top-left 8×8 is tile 576**, not tile 0: PNG x 0-7, y 144-151. Copy the
  top-left corner of your picture there.
- **8bpp, 1024 tiles.** Keep the PNG at 256×256 with a 256-color palette; the platform
  step copies exactly 0x10000 bytes.
- **Where the platforms land** (their non-transparent pixels replace yours): the enemy's at
  screen x 128-255, y 56-119 (PNG x 128-255, y 160-223); the player's at screen x 0-191,
  y 120-151 (PNG x 0-191, y 224-255), plus a 64×32 part just left of the screen (PNG row 19,
  y 152-159). Draw the ground under them as if they weren't there.
- **Color 0** shows the backdrop, which is palette entry 0. Retail backgrounds use black.

## 4. Changing a background

This exports the picture and day palette of `BATTLE_BG_GENERAL` (0), and builds them back.
Unchanged, every file comes back byte-identical to retail.

```bash
T=$PWD/build/heartgold.us/tools
GFX=$T/nitrogfx/nitrogfx
ARC=$T/nitroarc/nitroarc
W=/tmp/battlebg && mkdir -p $W && cp files/a/0/0/7 $W/7.narc
$ARC -xf $W/7.narc && cd $W          # → 7.narc.d/00000.NCGR ... 00350.NCLR

BG=0                                 # BATTLE_BG_*
TILES=$(printf %05d $((BG + 3)))
PAL=$(printf %05d $((0xB0 + BG * 3)))  # +1 evening, +2 night

cp 7.narc.d/$TILES.NCGR bg.NCGR.lz
$GFX bg.NCGR.lz bg.NCGR                           # decompress
$GFX 7.narc.d/$PAL.NCLR day.pal                   # palette → JASC
$GFX bg.NCGR bg.png -palette 7.narc.d/$PAL.NCLR   # 256×256, indexed

# ... edit bg.png (indexed, colors 0-111 only) and day.pal ...

$GFX bg.png new.NCGR -bitdepth 8 -version101 -sopc
head -c 65584 new.NCGR > new_cut.NCGR             # retail stops before the SOPC section
$GFX new_cut.NCGR new.NCGR.lz                     # LZ-compress
$GFX day.pal new.NCLR -pcmp
cp new.NCGR.lz 7.narc.d/$TILES.NCGR
cp new.NCLR    7.narc.d/$PAL.NCLR

(cd 7.narc.d && $ARC -cf $W/7.narc .)
cp $W/7.narc ~/path/to/pokeheartgold-modding/files/a/0/0/7
```

Then `make release`. For backgrounds 0-5, make the evening and night palettes too
(`$PAL` + 1 and + 2); they share the tiles, so they must keep the same color order. If
the picture's main color changes a lot, also change its row in `gBattleBgFillColors`,
or the intro starts from the old color: the values are 15-bit (`0x7FFF` white; red in the
low bits).

**A whole new picture.** Draw 256×152 pixels (the battle view), then build the 256×256
tileset from it: picture y 0-55 → PNG y 0-55, picture y 56-151 → PNG y 160-255, top-left
8×8 → also PNG (0, 144), PNG top-left 8×8 color 0, and fill PNG y 56-159 with something
that looks right when mirrored (a copy of the sky and ground works). Reduce it to at most
112 colors with index 0 the backdrop, and save the palette as `day.pal` with those colors
first.

## 5. Changing a platform

```bash
cp files/a/0/0/8 $W/8.narc && $ARC -xf $W/8.narc && cd $W   # from the repository root
# TERRAIN_PLAIN (0): enemy tiles 0x88 = 136, player 0x87 = 135, palettes 7/8/9
cp 8.narc.d/00136.NCGR e.NCGR.lz && $GFX e.NCGR.lz e.NCGR
cp 8.narc.d/00131.NCER e.NCER.lz && $GFX e.NCER.lz e.json
$GFX e.NCGR e.png -palette 8.narc.d/00007.NCLR -cell e.json -object   # 128×64
$GFX 8.narc.d/00007.NCLR plat.pal

# ... edit e.png (16 colors, index 0 transparent) ...

$GFX e.png e.NCGR.lz -cell e.json -clobbersize -version101 -mappingtype 64
$GFX plat.pal plat.NCLR -bitdepth 4 -nopad -pcmp
```

The player's side works the same with member 135 and cells 128 (256×32). Copy the results
over the members, repack as in §4. Look up the member numbers for other terrains in the
three tables at the top of `src/battle/battle_terrain.c` (`0x88` = 136). Some are shared:
`TERRAIN_GREAT_MARSH` (mud) and `TERRAIN_UNKNOWN` use the same enemy platform and
palettes, and `TERRAIN_UNKNOWN`'s player platform is `TERRAIN_PUDDLE`'s, so changing one
changes the other.

## 6. Adding a background

A map header stores the background in 5 bits (`battleBg : 5` in `include/map_header.h`), so
ids up to 31 fit: 9 more than retail. Members can't be inserted in `a/0/0/7`: the formulas
`backgroundId + 3` and `0xB0 + backgroundId × 3` already run into other members for id 23
(members 26 and 245). So append the new members at the end and give the loaders a table.

1. **Constant.** After `BATTLE_BG_BATTLE_HALL` in `include/constants/battle.h`:
   `BATTLE_BG_BEACH,` (23).
2. **Files.** Make the tileset and three palettes (§4) and add them to the unpacked
   `a/0/0/7` as `00351.NCGR`, `00352.NCLR`, `00353.NCLR`, `00354.NCLR`; the next
   background takes 355-358. Repack.
3. **Loaders.** Replace the two member expressions in `Battle_InitBackgrounds`
   (`src/battle/battle_main.c`) and `BattleSystem_ReinitMainBgLayers`
   (`src/battle/battle_022378C0.c`) with functions, for example in
   `src/battle/battle_system.c` (declared in `include/battle/battle_system.h`):

   ```c
   // a/0/0/7: retail backgrounds have fixed members; new ones are appended
   // as 4 members each (tiles, then 3 palettes) after the 351 retail members.
   int BattleBg_GetTilesMember(int backgroundId) {
       if (backgroundId <= BATTLE_BG_BATTLE_HALL) {
           return backgroundId + 3;
       }
       return 351 + (backgroundId - BATTLE_BG_BATTLE_HALL - 1) * 4;
   }

   int BattleBg_GetPaletteMember(int backgroundId, int timeOfDay) {
       if (backgroundId <= BATTLE_BG_BATTLE_HALL) {
           return backgroundId * 3 + 0xB0 + timeOfDay;
       }
       return BattleBg_GetTilesMember(backgroundId) + 1 + timeOfDay;
   }
   ```

4. **Time of day.** For three palettes, add the id to the `case 0 ... 5` list in
   `BattleSystem_GetBgTimeOfDay`. Otherwise only the first palette is used (make all three
   anyway, or point them at the same file).
5. **Tables with a row per background.** Each needs a new row, or it reads past its end:
   - `gBattleBgFillColors` in `asm/battle_main_data.s` (`.word day, evening, night`), and
     its size `[23][3]` in `src/battle/battle_main.c`;
   - `sBattleBgTerrains` in `src/battle/battle_setup.c` (which platforms off special
     tiles; a missing row asserts and gives `TERRAIN_MAX`, which reads past the platform
     tables);
   - `sBackgroundPaletteIds` in `src/battle/battle_input.c` (`{ -1, -1 }` for the default
     bottom screen; a missing row asserts and uses background 0's).
6. **Use it.** `"battle_scene": "BATTLE_BG_BEACH"` in a map's `map.json`.

Battle recordings store the id, so a recording with the new background shows something
else in a game without it; that only matters for sharing recordings between hacks.

Simplest alternative: `BATTLE_BG_DISTORTION_WORLD` (17) is in no map. Replace its picture
(§4) and use it; nothing else changes.

## 7. Adding a platform

1. **Constant.** Before `TERRAIN_MAX` in `include/constants/battle.h` (`TERRAIN_GIRATINA`
   is 23, so the new one is 24, and `TERRAIN_MAX` becomes 25).
2. **Files.** Two tilesets (player 256×32, enemy 128×64, made from an existing one so the
   cells still fit) and three 16-color palettes, appended to `a/0/0/8` from member 346.
3. **Tables** in `src/battle/battle_terrain.c`: a row in `sPlayerTerrainCharFiles`,
   `sEnemyTerrainCharFiles` and `sTerrainPaletteFiles` with the new member numbers.
4. **When it's used.** Either a row in `sBattleBgTerrains` (a new background that brings
   its own platforms), or a new tile check in `FieldSystem_GetTerrainFromStandingTile`.
5. **Gameplay.** It behaves as "indoors" for Nature Power, Secret Power and Camouflage
   and gives Burmy the plant cloak (§1). Change those tables if it should act otherwise;
   `sSecretPowerTerrainAnims` has 24 entries, so give it a 25th or Secret Power shows Tri
   Attack.

## Where to look

| What | File |
|---|---|
| ids | `include/constants/battle.h` (`BattleBg`, `Terrain`) |
| choosing them | `src/battle/battle_setup.c` (`BattleSetup_SetBattleBgAndTerrain`, `sBattleBgTerrains`) |
| loading the background | `src/battle/battle_main.c` (`Battle_InitBackgrounds`), `src/battle/battle_022378C0.c` |
| time of day, drawing in the platforms | `src/battle/battle_system.c` (`BattleSystem_GetBgTimeOfDay`, `BattleSystem_SetBackground`) |
| platforms | `src/battle/battle_terrain.c` |
| intro colors, BG templates | `asm/battle_main_data.s` |
| bottom screen tint | `src/battle/battle_input.c` (`sBackgroundPaletteIds`) |
| map field | `"battle_scene"` in `data/maps/<MapName>/map.json` |

## Not verified

- No changed or new background or platform was tried in the game. The export/import
  commands were run on retail files and give byte-identical results; the layout rules in
  §3 were read from the tilemap and checked against all 23 retail tilesets.
- The code in §6 and §7 is a sketch; it was not built.
- Which screens show the mirrored right half of the tilemap (only code that scrolls BG3
  was found: move animations and `src/battle/link_battle_screen.c`).
- What palette rows 8, 9 and 12-15 of the background are used for during move animations.
- That `gBattleBgFillColors` is the color seen at the start of the intro; the code fills
  the palettes with it and later restores them, but the intro was not watched frame by
  frame.
