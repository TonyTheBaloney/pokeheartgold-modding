<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# gen4map rendering: drawing a map from its NSBMD models

> AI-generated, local to this fork. Do not upstream.

How the map editor turns a map's data into pictures, precise enough to
reimplement in another tool. The reference is the game itself and
NITRO-System's G3D library, whose source is in
`subprojects/NitroSystem-071126.1/` (headers `include/nnsys/g3d/binres/res_struct.h`,
code `libraries/g3d/src/{sbc.c,kernel.c,util.c}`). Implementation:
`tools/mapkit/mapkit/nitro.py` (decoding, no GUI),
`tools/mapeditor/mapeditor/terrain.py` (top-down) and `view3d.py` (OpenGL).

## 1. Coordinate system

- Model units: fx32 / 4096. A tile is 16 units, a layout cell 512.
- x east, y up, z south. The DS uses row vectors: `v' = v · M`, and the
  geometry engine's MULT, TRANS and SCALE commands pre-multiply (`M ← N · M`).
- Cell (cx, cz) of a layout has its origin at `(512 cx + 256, 8 × altitude,
  512 cz + 256)`; its model is centred on that point (vertices span about
  ±256 in x and z). Props are placed at `(512 cx + 256 + px, py, 512 cz + 256 + pz)`:
  **their y is not raised** by the altitude.

## 2. Which resources a cell uses

The game loads one **area** at a time, the current map's, and draws every
visible cell with it (`src/field/area_data.c`, `map_load_manager.c`). So to draw
a map:

1. `area = map.json area_data`; read the area header (BINARY.md §6).
2. Terrain textures: NSBTX `a/0/4/4[mapTexNarcMemberId]`. A cell's `model.nsbmd`
   normally has no texture block of its own; if it has one, use it.
3. Props: models from `a/1/4/8` if `buildModelKind == 0` (rooms), else
   `a/0/4/0`; member = `props.json` `model`. Textures: NSBTX
   `a/0/7/0[mapPropNarcMemberId]`, or the model's own TEX0 if it has one.
   A 4-byte zero member means the area has no prop textures.
4. Materials take their texture and palette **by name** (§4): look the name up in
   the chosen NSBTX.

Cells belonging to no map (`maps` entry `MAP_EVERYWHERE`, filler sea and forest)
are drawn with the current area too; using their own header's area gives the
wrong textures.

## 3. NSBMD models

File: `BMD0` header (u16 block count, u32 block offsets), blocks `MDL0` and
optional `TEX0`.

**Dictionaries.** Every list (models, nodes, materials, shapes, textures,
palettes) is an `NNSG3dResDict`: `u8 revision, u8 count, u16 size, u16 dummy,
u16 ofsEntry`, a search tree of count+1 nodes (not needed to read), then at
`ofsEntry` a header `u16 sizeUnit, u16 ofsName` followed by `count` data entries
of `sizeUnit` bytes and, at `ofsName` (relative to that header), `count` 16-byte
NUL-padded names. Data offsets are relative to the **block that owns the
dictionary**: the model set for models, node info for nodes, the material block
for materials, the shape block for shapes.

**Model** (`NNSG3dResMdl`): `u32 size, ofsSbc, ofsMat, ofsShp, ofsEvpMtx`, then
`NNSG3dResMdlInfo` (**0x2C bytes**: counts, `fx32 posScale, invPosScale`, vertex
and polygon counts, bounding box `fx16 x,y,z,w,h,d`, `fx32 boxPosScale,
boxInvPosScale`), then the node dictionary.

**Nodes** (`NNSG3dResNodeData`): `u16 flag, fx16 _00`, then optional parts by
flag: translation (3 fx32) unless `TRANS_ZERO` (0x1); rotation unless `ROT_ZERO`
(0x2), either 8 more fx16 (with `_00` a 3×3 matrix) or, with `PIVOT_EXIST` (0x8),
two fx16 A, B expanded with the pivot table in `sbc.c` (`pivotUtil_`, flags
`PIVOT_MINUS` 0x100, `SIGN_REVC` 0x200, `SIGN_REVD` 0x400, pivot index bits 4-7);
scale (3 fx32) unless `SCALE_ONE` (0x4). The node matrix is `scale · [R | T]`.

**Structure byte code (SBC)**, from `ofsSbc` to `ofsMat`. Opcode low 5 bits =
command, high 3 bits = variant; lengths from `NNS_G3dSbcCmdLen` (`util.c`).
What a renderer needs:

| Command | Bytes | Action |
|---|---|---|
| `NODEDESC` 06 | 4 (+1 per option) | variant 0x40/0x60: first restore matrix `src` (byte 4, or 5 with 0x60); then `cur ← node · cur`; variant 0x20/0x60: store `cur` at `dest` (byte 4) |
| `MTX` 03 | 2 | `cur ← stack[idx]` |
| `MAT` 04 | 2 | current material |
| `SHP` 05 | 2 | run the shape's display list with `cur` |
| `NODEMIX` 09 | 3 + 3n | `stack[dest] = Σ (ratio/256) · invM[node] · stack[src]` for the n `(src, node, ratio)` triples; `cur` = the sum (`sbc.c`, `NNSi_G3dFuncSbc_NODEMIX`). `invM` is the node's 4×3 matrix in the envelope table at `ofsEvpMtx` (per node: 12 fx32 invM, 9 fx32 invN) |
| `POSSCALE` 0B | 1 | variant 0: `cur ← scale(posScale) · cur`; 0x20: `invPosScale` |
| `NODE` 02, `BB` 07, `BBY` 08, `CALLDL` 0A, `ENVMAP` 0C, `PRJMAP` 0D | 3, 2(+opts), 2(+opts), 9, 3, 3 | visibility, billboards, environment and projection maps: drawn as static |
| `RET` 01 | 1 | end |

**Materials** (`NNSG3dResMatData`, 0x2C bytes + optional texture matrix):
`diffAmb` (diffuse RGB555 in bits 0-14), `polyAttr` (polygon mode bits 4-5:
0 modulate, 1 decal, 2 toon/highlight, 3 shadow; alpha bits 16-20),
`texImageParam` (bit 16/17 repeat S/T, 18/19 flip S/T), `flag`
(`TEXMTX_USE` 0x1 and its parts), `origWidth/Height`. The material block starts
with `u16 ofsDictTexToMatList, u16 ofsDictPlttToMatList` (relative to the block):
two dictionaries keyed by texture or palette name whose entries are `u16 offset,
u8 count, u8 flag` pointing at `count` material indices. That is how a material
gets its texture and palette (`kernel.c`, `NNS_G3dBindMdlTex`).

**Shapes** (`NNSG3dResShpData`): `u16 tag, u16 size, u32 flag, u32 ofsDL, u32
sizeDL` (offset relative to the shape data). The display list is DS geometry
engine commands, packed: one u32 holding four 8-bit command ids, then each
command's parameter words in order (parameter counts per command as in GBATEK).
Handled:

| Command | Effect |
|---|---|
| `MTX_RESTORE` 14, `MTX_STORE` 13, `MTX_IDENTITY` 15 | matrix stack |
| `MTX_LOAD_4x4/4x3` 16/17, `MTX_MULT_4x4/4x3/3x3` 18/19/1A, `MTX_SCALE` 1B, `MTX_TRANS` 1C | `cur ← N · cur` (load replaces). **Skinned models restore a matrix and then scale by posScale in the display list**; ignoring 1B breaks them |
| `COLOR` 20 | vertex color, RGB555 |
| `TEXCOORD` 22 | s, t as s16 with 4 fractional bits, in **texels** |
| `VTX_16` 23 | x, y, z as fx16 (two words) |
| `VTX_10` 24 | 10-bit x, y, z with 6 fractional bits |
| `VTX_XY` 25, `VTX_XZ` 26, `VTX_YZ` 27 | replace two coordinates, keep the third |
| `VTX_DIFF` 28 | add 10-bit signed x, y, z in units of 1/4096 |
| `BEGIN_VTXS` 40 | 0 triangles, 1 quads, 2 triangle strip, 3 quad strip |
| `END_VTXS` 41 | |

Every vertex is transformed by `cur` when it is emitted. Strips alternate winding.
Normals and lighting commands are skipped.

## 4. NSBTX textures (`TEX0`)

Block layout (offsets from the `TEX0` block): texture info at 0x08 (`u16 ofsDict`
at 0x0E, `u32 ofsTex` at 0x14), 4×4 info at 0x18 (`u32 ofsTex` at 0x24, `u32
ofsTexPlttIdx` at 0x28), palette info at 0x2C (`u16 ofsDict` at 0x34, `u32
ofsPlttData` at 0x38), then the texture dictionary.

Texture entry: `u32 texImageParam` (data offset ≫ 3 in bits 0-15, width `8 ≪ bits
20-22`, height `8 ≪ bits 23-25`, format bits 26-28, color 0 transparent bit 29),
`u32 extra`. Data is at `ofsTex + offset·8` (for 4×4: `tex4x4.ofsTex + offset·8`,
palette indices at `ofsTexPlttIdx + offset·4`). Palette entry: `u16 offset ≫ 3`;
colors are RGB555 at `ofsPlttData + offset·8`, running to the next palette.

| Format | Texel |
|---|---|
| 1 A3I5 | 8 bits: index 0-4, alpha 5-7 (0-7) |
| 2 4-color | 2 bits; index 0 transparent if bit 29 |
| 3 16-color | 4 bits; same |
| 4 256-color | 8 bits; same |
| 5 4×4 compressed | per 4×4 block a u32 of 2-bit codes and a u16: palette offset (bits 0-13, in pairs of colors) and mode (14-15): 0 = c0 c1 c2 transparent, 1 = c0 c1 (c0+c1)/2 transparent, 2 = c0 c1 c2 c3, 3 = c0 c1 (5c0+3c1)/8 (3c0+5c1)/8 |
| 6 A5I3 | 8 bits: index 0-2, alpha 3-7 (0-31) |
| 7 direct | RGB555, bit 15 = opaque |

Retail HGSS map and prop textures use formats 1, 2, 3, 4 and 6.

## 5. Drawing rules

- **Wrap.** Repeat per axis (bits 16/17); flip (bits 18/19) = mirrored repeat;
  neither = clamp. Texture coordinates are in texels: divide by the texture size.
- **Transparency.** Texels with alpha < half are cut out; polygons with alpha
  1-30 are blended with `alpha/31`; alpha 0 (wireframe on the DS) is drawn opaque.
- **Polygon mode.** Modulate: texture × vertex color (or the material diffuse
  when there are no `COLOR` commands). Decal: texture only. Shadow (3): not drawn.
- **Order.** Opaque first with depth writes, translucent after without.

## 6. The two views

**Top-down** (`terrain.py`). Looking straight down, the map from texture space to
the image is affine for every triangle, so each one can be filled with its
texture as a brush whose transform comes from the three (u, v) → (x, z) pairs. A
cell becomes a 512 × 512 image (1 unit = 1 pixel) drawn lowest triangle first
(by the highest vertex), so roofs and trees cover the ground. Edge-on (vertical)
triangles are skipped. Vertex colors are ignored (untextured polygons take the
average vertex color) and translucent polygons are drawn with their alpha as
opacity, with no cut-out. About 0.07 s per cell; images are cached per cell.

**Perspective** (`view3d.py`). Triangles grouped by (texture, palette, wrap,
alpha, mode) into vertex buffers (x, y, z, u, v, r, g, b); one draw call per
group; GL wrap modes map directly (`GL_REPEAT` / pre-mirrored image / clamp).
OpenGL 3.3 core.

## 7. Not handled yet

- Texture pattern and SRT animations (water, flowers; `NSBTP`/`NSBTA`, the area's
  `mapPropAnimFileId`) and material color animations.
- Billboards (`BB`, `BBY`) are drawn as modelled, not turned to the camera.
- Lighting and normals; toon/highlight shading; fog; edge marking.
- `CALLDL`, `ENVMAP`, `PRJMAP` effects.

## 8. Verification

- `tools/mapkit/tests/test_nitro.py`: every terrain model (676) and prop model
  (562) decodes (≈ 835,000 triangles); every map and prop texture decodes;
  Cherrygrove's model resolves every texture name in its area; the skinned
  Ecruteak Gym floor stays within 64 units of height; unit cases for each
  texture format.
- `tools/mapeditor/tests/test_editor.py`: a Cherrygrove cell draws over 95 % of its
  image; the OpenGL scene draws offscreen.
- Visual checks (2026-10-22) against the game's look: Cherrygrove, Goldenrod
  City, Union Cave 1F, Ecruteak Gym, Goldenrod Department Store 1F.
