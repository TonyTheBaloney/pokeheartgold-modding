<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# gen4map binaries: what the text formats become in the ROM

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The ROM-side formats behind [FORMAT.md](FORMAT.md), as HeartGold/SoulSilver use
them. Each section names the game code that reads the data (paths in this
repository), so every statement can be checked. All values are little-endian;
`fx32` is a signed 32-bit fixed-point number with 12 fractional bits (4096 = 1.0),
`fx16` the same in 16 bits.

| Data | ROM path (HGSS) | Text form | Codec in this repo |
|---|---|---|---|
| Map matrices | `a/0/4/1` | `layout.json` | `tools/mapkit/mapkit/matrix.py`, `layouts.py` |
| Land data | `a/0/6/5` | `data/landdata/NNNN/` | `tools/mapkit/mapkit/landdata.py`; models `nsbmd.py`, heights `bdhc.py` |
| Zone events | `a/0/3/2` | `map.json` events | `files/fielddata/eventdata/zone_event.json.txt` (build), `events.py` |
| Map headers | ARM9 `sMapHeaders` | `map.json` header | `tools/mapkit/mapkit/layout.py` (`gen-header`) |
| Area headers | `a/0/4/2` | (not yet) | `tools/mapeditor/mapeditor/terrain.py` reads it |
| Area prop lists | `a/0/4/3` | (not yet) | |
| Map textures | `a/0/4/4` | `data/area_textures/NNN/` (1.2) | `tools/mapkit/mapkit/areatex.py`, `nsbtx.py` |
| Prop textures | `a/0/7/0` | (binary NSBTX) | `tools/mapkit/mapkit/nitro.py`; `nsbtx.py` writes them |
| Prop models | `a/1/4/8` (rooms), `a/0/4/0` (field) | (binary NSBMD) | `nitro.py` |

## 1. NARC archives

Every file above except the map headers is a NARC (`NARC`, byte order `FFFE`,
version `0100`) with three blocks:

- `BTAF`: u16 member count, then per member u32 start and end offsets into `GMIF`;
- `BTNF`: file names; the map archives have none (16-byte block, one empty directory);
- `GMIF`: the members, each starting 4-aligned; padding bytes are `FF`.

A member is addressed only by its index. The writer in `landdata.py`
(`narc_bytes`) reproduces the retail land data archive byte for byte; the other
archives here are built with `nitroarc` and also match.

## 2. Map matrix (`a/0/4/1`, member = layout)

Read by `src/map_matrix.c`.

```
u8   width, height
u8   hasHeaders, hasAltitudes        booleans
u8   nameLength
char name[nameLength]                ASCII, not terminated
u16  mapHeaderIds[width*height]      if hasHeaders      -> layout.json "maps"
u8   altitudes[width*height]         if hasAltitudes    -> "altitudes"
u16  landDataIds[width*height]                          -> "land_data"; 0xFFFF = no cell
```

Cells are row-major, north to south. The game places cell (x, z) at
`(256 + 512 x, altitude × 8, 256 + 512 z)` model units (`CalcMapPosition`,
`src/field/map_load_manager.c`: `altitude << 15` in fx32).

## 3. Land data (`a/0/6/5`, member = cell)

Read by `src/field/map_load_manager.c` (`ReadMapFileHeader`, the load tasks).

```
u32 permissionsSize        always 0x800
u32 propsSize              0x30 × props
u32 modelSize
u32 bdhcSize
u32 soundplateHeader       HGSS only: 0x1234 | soundplateBytes << 16
u8  soundplates[soundplateBytes]          -> soundplates.bin (absent if 0)
u16 permissions[32*32]                    -> permissions.txt
MapPropArcData props[]                    -> props.json
u8  model[modelSize]       NSBMD          -> model.nsbmd
u8  bdhc[bdhcSize]         BDHC           -> terrain.bdhc
```

The model is read into a 0xF000-byte buffer (`MAP_LOAD_PRIMARY_BUFFER_SIZE`,
`include/field/map_load_buffers.h`); the largest retail model is 0xEFEC bytes.
It must hold exactly one model (`GF_ASSERT(modelSet->dict.numEntry == 1)`,
`LoadMapModel`); its textures are bound by name from the area's map textures.

Sections follow each other with no padding; the member is exactly
`20 + soundplateBytes + permissionsSize + propsSize + modelSize + bdhcSize` bytes
(true for all 676 retail cells). Note the header lists the sizes in the order
permissions, props, model, BDHC.

**Permissions.** Row-major, north to south. Bits 0-7 behavior (`enum
TILE_BEHAVIOR`, `include/constants/metatile_behavior.h`; checks in
`src/metatile_behavior.c`), bits 8-14 an attribute read by map object movement
(`FieldSystem_GetTileAttrBits8To14`, `src/field_terrain.c`; meaning not decoded),
bit 15 collision (`FieldSystem_CheckTileCollision`).

**Props** (`MapPropArcData`, `src/field/map_prop_manager.c`), 0x30 bytes:

```
s32   buildModel           prop model number (member of the area's prop model archive)
fx32  translation[3]       from the cell centre; y absolute (not raised by altitude)
fx32  rotation[3]
fx32  scale[3]
u8    padding[8]           always 0
```

At most 32 are loaded (`MAP_PROP_MAX`, `include/field/map_load_manager.h`). The
game adds only the cell's x and z to a prop's translation
(`MapPropManager_DrawWithOffset`).

### 3.1 Sound plates

`SoundplateStruct` (`include/field/field_control.h`): the u32 header above is its
first word (two bytes `34 12`, then u16 `dataSize`), followed by 8-byte
`Soundplate` records (sound id, volume index, two unknown bytes, x, z, x and z
bounds). Kept as raw bytes in format 1.x; at most 0x200 bytes.

### 3.2 BDHC (terrain heights)

Read by `src/field/bdhc.c` (`Bdhc_Load`, `Bdhc_GetHeight`); structures in
`include/field/bdhc.h`; queried by `src/field_terrain.c` (`Terrain_CalcHeight`).
Codec, query and generator: `tools/mapkit/mapkit/bdhc.py`.

```
char magic[4]                 "BDHC"
u16  pointsCount, normalsCount, constantsCount, platesCount, stripsCount, accessListCount
BdhcPoint  points[]           fx32 x, z: corners of plate rectangles
VecFx32    normals[]          fx32 x, y, z
fx32       constants[]
BdhcPlate  plates[]           u16 firstPoint, secondPoint, normal, constant
BdhcStrip  strips[]           fx32 bound (z), u16 count, u16 offset into accessList
u16        accessList[]       plate indices
```

Coordinates are model units relative to the **cell's centre** (x east, z south):
the caller subtracts `(32 × cell + 16) × 16` from the walker's position. The
result is used as the walker's y as it is; **the layout's altitude is not added**
(the model is drawn raised by it, §2). On every retail raised cell checked, the
BDHC heights are cell-local (ground at 0) while the cell is walkable; how the two
agree in game isn't worked out yet.

**Plates.** `firstPoint` is the rectangle's (min x, min z) corner and
`secondPoint` its (max x, max z) corner (true for all retail plates; the game
accepts either order). Inside the rectangle, edges included, the height is the
plane `normal · (x, y, z) + constant = 0` solved for y. Retail normals are unit
length (rounded to fx32); 87% of plates are flat (normal (0, 4096, 0)), almost all
slopes run along one axis, and one plate (land data 464) is vertical, which gives
no height.

**Lookup** (`Bdhc_GetHeight(mode, currentY, x, z)`):

1. Find the strip for z with `Bdhc_FindStrip`: a binary search over the strips'
   `bound` values; it returns the first strip whose bound is ≥ z (with an
   off-by-one walk at exact bounds that `bdhc.py` copies).
2. Test the strip's plates in access-list order; for each whose rectangle holds
   (x, z), compute `y = FX_Div(-(constant + (FX_Mul(nx, x) + FX_Mul(nz, z))), ny)`.
   Stop after **10** such plates (`BDHC_MAX_HEIGHT_CANDIDATES`).
3. None: no height (the walker keeps its y). One: that one. Several: by `mode`
   (0 nearest to `currentY`, the field's normal use; 1 highest; 2 lowest).

`FX_Mul(a, b) = (a·b + 0x800) >> 12`; `FX_Div(n, d)` divides `n << 32` by `d` on
the hardware divider (truncating) and rounds: `(q + 2^19) >> 20`
(`subprojects/NitroSDK-*/libraries/fx/src/fx_cp.c`).

**How the retail files are laid out** (all 676 follow it, checked by
`tools/mapkit/tests/test_bdhc.py`):

- Points, normals and constants are pools in order of first use by the plates;
  points never repeat. In 52 files a normal or constant value appears twice
  (the converter merged values before rounding), so the order can't always be
  rebuilt from the values alone.
- Let z<sub>0</sub> < z<sub>1</sub> < ... be the distinct z edges of all plates.
  There is one strip per interval (z<sub>k</sub>, z<sub>k+1</sub>), `bound` =
  z<sub>k+1</sub> (the upper edge, although the header calls it lowerBound), and it
  lists, in plate order, every plate with `z0 ≤ z`<sub>k+1</sub> and
  `z1 > z`<sub>k</sub> (plates touching the strip's upper edge are included,
  since lookups include edges).
- The access list is the strips' lists one after the other.

**Limits.** Everything after the header must fit the 0x9000-byte buffer
(`MAP_LOAD_SECONDARY_BUFFER_SIZE`; `Bdhc_SetBuffers` asserts). Counts are u16. The
largest retail file is 10,794 bytes.

The text form is `heights.json` (FORMAT.md §7.3).

## 4. Zone events (`a/0/3/2`, member = a map's events)

Template: `files/fielddata/eventdata/zone_event.json.txt`; read by
`src/map_events.c` into a 0x800-byte buffer (asserts the size is smaller).

```
u32 bgCount;     bgCount × { u16 scriptId, u16 type, u32 x, u32 z, u32 y, u32 dir }               20 bytes
u32 objectCount; objectCount × { u16 id, spriteId, movement, type, eventFlag, scriptId,
                                 facingDirection, param0, param1, param2, xRange, yRange, x, z;
                                 u32 y }                                                           32 bytes
u32 warpCount;   warpCount × { u16 x, z, header, anchor; u32 y }                                 12 bytes
u32 coordCount;  coordCount × { u16 scriptId, x, z, w, h, y, val, var }                           16 bytes
```

| map.json | binary |
|---|---|
| `bg_events[]`: `script`, `type`, `x`, `y`, `elevation`, `player_facing_dir` | `scriptId`, `type`, `x`, `z`, `y`, `dir` |
| `object_events[]`: `local_id`, `graphics_id`, `movement_type`, `trainer_type`, `flag`, `script`, `facing_dir`, `trainer_sight_or_param0`, `param1`, `param2`, `movement_range_x/y`, `x`, `y`, `elevation` | `id`, `spriteId`, `movement`, `type`, `eventFlag`, `scriptId`, `facingDirection`, `param0..2`, `xRange`, `yRange`, `x`, `z`, `y` |
| `warp_events[]`: `x`, `y`, `dest_map`, `dest_warp_id`, `elevation` | `x`, `z`, `header`, `anchor`, `y` |
| `coord_events[]`: `script`, `x`, `y`, `width`, `height`, `elevation`, `var_value`, `var` | `scriptId`, `x`, `z`, `w`, `h`, `y`, `val`, `var` |

Note the binary order of bgs first, while `map.json` lists objects first.
`anchor` 0x100 with `header` 0xFFF is the dynamic warp.

## 5. Map headers (ARM9, `sMapHeaders` in `src/data/map_headers.h`)

`MapHeader` (`include/map_header.h`), 24 bytes, one per map id. Bit fields are
allocated from the least significant bit.

```
0x00 u8   wildEncounterBank                         wild_encounters
0x01 u8   areaDataBank                              area_data
0x02 u16  moveModelBank:4, worldMapX:6, worldMapY:6 move_model_bank, world_map_x, world_map_y
0x04 u16  matrixId                                  layout (index in layouts.txt)
0x06 u16  scriptsBank        0x08 u16 scriptHeaderBank      (maps.txt scripts / init)
0x0A u16  msgBank                                   (maps.txt text)
0x0C u16  dayMusicId         0x0E u16 nightMusicId          music_day, music_night
0x10 u16  eventsBank                                (maps.txt events)
0x12 u16  mapsec:8, areaIcon:4, momCallIntroParam:4 region_map_section, area_icon, mom_call_intro
0x14 u32  regionNo:1, weather:7, mapType:4, cameraType:6, followMode:2, battleBg:5,
          bikeAllowed:1, runningAllowed_Unused:1, escapeRopeAllowed:1, flyAllowed:1,
          outgoingCalls:1, incomingCalls:1, radioSignal:1
```

Because the table is in the ARM9 binary, editing headers in a retail ROM means
patching ARM9; this repository compiles it from `map.json` instead.

## 6. Area data

**Area header** (`a/0/4/2`, member = `area_data`), 8 bytes (`AreaDataHeader`,
`src/field/area_data.c`):

```
u16 mapPropNarcMemberId    prop list (a/0/4/3) and prop textures (a/0/7/0) member
u16 mapTexNarcMemberId     map textures (a/0/4/4) member
u16 mapPropAnimFileId      0xFFFF = none
u8  buildModelKind         0 = room props (a/1/4/8), otherwise field props (a/0/4/0)
u8  lightKind
```

**Prop list** (`a/0/4/3`): u16 count, then count u16 prop model numbers the area
loads (at most 550, `AREA_DATA_MAX_MAP_PROPS`). Areas without prop textures
have a 4-byte all-zero member in `a/0/7/0` instead of an NSBTX.

**Textures and models** are NITRO-System NSBTX and NSBMD files; see
[RENDERING.md](RENDERING.md).

## 7. Diamond/Pearl and Platinum

Not checked yet. Expected from the shared engine: the same NARC, matrix, event and
prop layouts at different ROM paths; land data without the sound plate word and
block (a 16-byte header); a different `MapHeader`. Each needs confirming against
pret/pokeplatinum and pret/pokediamond before a tool relies on it.
