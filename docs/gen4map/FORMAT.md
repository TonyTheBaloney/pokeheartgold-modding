<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22 -->

# gen4map format 1.2: maps, layouts, terrain cells, map textures, events

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This is the specification of the text formats this fork stores Generation IV
(Nintendo DS) Pokémon maps in. It is written so that a separate tool can read and
write the same files for any Gen 4 game (Diamond/Pearl, Platinum,
HeartGold/SoulSilver) without this repository's build. The ROM-side binaries the
files map to are in [BINARY.md](BINARY.md); how the 3D data is drawn is in
[RENDERING.md](RENDERING.md).

The words MUST, SHOULD and MAY are used as in RFC 2119. "Reader" is any program
that loads these files; "writer" is any program that saves them.

Status: **1.2**, describing the files in this repository on 2026-10-26. Every
file conforms: `tools/mapkit/mapkit.sh format check`.

| Version | Adds |
|---|---|
| 1.0 | maps, layouts, terrain cells, manifest |
| 1.1 | `heights.json`, a text form of a cell's heights in place of `terrain.bdhc` (§7.3; [CHANGE-0002](CHANGE-0002-terrain-authoring.md)) |
| 1.2 | map texture sets as PNG and palette files, `paths.area_textures` (§10; [CHANGE-0003](CHANGE-0003-area-textures.md)) |

## 1. Versioning

- A project declares its format version in the manifest (§2): `"version": "1.2"`.
- Minor versions only **add** optional keys or files. A 1.x reader MUST read
  1.0 files; a 1.0 reader that meets a key it doesn't know reports an error
  (keys are closed, so typos are caught) and SHOULD tell the user to update.
- A major version changes the meaning or shape of something that exists. A
  reader MUST refuse a major version it doesn't support.
- Machine-readable definitions: `schemas/map.schema.json`, `layout.schema.json`,
  `props.schema.json`, `heights.schema.json`, `textures.schema.json`, `manifest.schema.json` (JSON Schema
  2020-12). Where this
  text and a schema disagree, this text wins and the schema is a bug.

## 2. Project and manifest

A project is a directory tree. Its root holds the manifest at `data/gen4map.json`:

```json
{
    "format": "gen4map",
    "version": "1.2",
    "game": { "family": "HGSS", "versions": ["HEARTGOLD", "SOULSILVER"], "language": "en_US" },
    "paths": { "maps": "data/maps", "map_index": "data/maps/maps.txt",
               "layouts": "data/layouts", "layout_index": "data/layouts/layouts.txt",
               "landdata": "data/landdata", "area_textures": "data/area_textures",
               "constants": "include/constants",
               "map_ids": "include/constants/maps.h",
               "tile_behaviors": "include/constants/metatile_behavior.h" },
    "binaries": { "map_matrix": "a/0/4/1", "zone_event": "a/0/3/2", "land_data": "a/0/6/5", ... },
    "features": { "land_data_soundplates": true, "layout_cell_maps": true,
                  "layout_altitudes": true, "map_header_in_arm9": true }
}
```

| Key | Meaning |
|---|---|
| `format` | always `"gen4map"` |
| `version` | `"<major>.<minor>"` |
| `game.family` | `DP`, `PLATINUM` or `HGSS`: which binary layouts apply (BINARY.md) |
| `game.versions` | the ROM versions the project builds; `language` the text language kept |
| `paths` | where the text files are, relative to the project root |
| `binaries` | where each binary lives **in the ROM's file system** (NitroFS paths), so a tool can read a retail ROM directly; objects group alternatives (`prop_models.room` / `.field`) |
| `features` | which optional parts this game has (§9) |

Paths use `/`. Unknown `paths`, `binaries` and `features` keys are allowed (a
newer tool may add some); everything else is closed.

## 3. Common rules

- **Encoding.** UTF-8, LF line ends, a final newline. JSON is indented with 4
  spaces; writers SHOULD keep the existing key order and formatting so an
  unchanged file saves byte-identical (diffs show only real edits).
- **Names, not numbers.** A value that the game stores as a number but that has a
  named constant SHOULD be written as the name (`"SPRITE_GSBOY1"`,
  `"MAP_CHERRYGROVE"`, `"FLAG_HIDE_CAMERON"`). A plain integer MUST also be
  accepted. Names are C identifiers (`[A-Za-z_][A-Za-z0-9_]*`) resolved from the
  project's constants (`paths.constants`, `paths.map_ids`).
- **Coordinates** are tiles. `x` grows east, `y` grows **south**, `elevation` is
  height. (The DS code calls these x, z and y; the names here are pokeemerald's.)
  Event coordinates are **global** over the map's layout: `global = cell * 32 +
  local`.
- **3D units.** One tile is 16 model units. A layout cell is 512 × 512 units.
  Fixed-point values (`fx32`, 1.0 = 4096) are written as decimal numbers that MUST
  be exact multiples of 1/4096.
- **Ranges.** Every number fits the binary field it becomes; the schemas give
  each field's range and BINARY.md its width. Writers MUST reject values that
  don't fit (the game would silently truncate them).

## 4. Index files

The ROM addresses everything by position in an archive, and this repository's
build derives constant names from the original file names. The index files keep
both stable no matter how folders are named.

### 4.1 `maps.txt`

```
# comment
<Folder> <MAP_ID> events=<base> scripts=<base> init=<base> text=<base>
```

One line per map, in any order. `<Folder>` is the map folder under `paths.maps`.
Each `<base>` is the original bank file name (`064_T21`, `scr_seq_0850_T21`,
`scr_seq_0623_T21_hdr`, `msg_0550_T21`), or `@<Folder>` meaning "the bank of
that other map's folder" (shared banks; the lowest map id owns them).

### 4.2 `layouts.txt`

```
# comment
<Folder> <matrix base name>
```

One line per layout, **in matrix archive order** (line N = matrix N). `<Folder>`
is under `paths.layouts`; the base name (`map_matrix_0002_D01R0101`) is what the
ROM's file and constant names came from.

### 4.3 Land data

Land data folders are named by number, `NNNN` (four digits, from `0000`, no
gaps): folder N is member N of the land data archive. There is no index file.

## 5. Map: `<maps>/<Folder>/map.json`

One JSON object: the map's header, then its events. Schema: `schemas/map.schema.json`.

### 5.1 Header

| Key | Type | Meaning (HGSS `MapHeader` field, BINARY.md §5) |
|---|---|---|
| `id` | `MAP_*` | the map's id; MUST match `maps.txt` |
| `name` | string | the folder name; MUST equal it |
| `code` | string | Game Freak's code (`T21`); MAY be empty |
| `layout` | name | a folder in `layouts.txt` (`matrixId`) |
| `music_day`, `music_night` | `SEQ_*` | background music |
| `region_map_section` | `MAPSEC_*` | name popup and Town Map position |
| `weather` | 0-127 | weather id |
| `map_type` | `MAP_TYPE_*` | town, route, cave, interior... |
| `battle_scene` | `BATTLE_BG_*` | battle background |
| `allow_cycling`, `allow_escaping`, `allow_running`, `allow_fly` | bool | `allow_running` is unused by HGSS |
| `allow_outgoing_calls`, `allow_incoming_calls`, `radio_signal` | bool | Pokégear |
| `wild_encounters` | `ENCDATA_*` | wild table, `ENCDATA_NA` for none |
| `camera_type` | 0-63 | camera preset |
| `follow_mode` | `MAP_FOLLOWMODE_*` | following Pokémon rules |
| `region` | `MAP_REGION_*` | Johto / Kanto |
| `area_icon`, `mom_call_intro` | 0-15 | |
| `world_map_x`, `world_map_y` | 0-63 | |
| `area_data` | 0-255 | area header: which textures and props the terrain uses (RENDERING.md §2) |
| `move_model_bank` | 0-15 | overworld sprite set |

All header keys are REQUIRED. The bank fields (scripts, text, events) are not in
`map.json`: they follow from `maps.txt`.

### 5.2 Events

Four optional arrays. A map whose events live in another folder (`events=@Folder`
in `maps.txt`) has none of them. In the ROM all four together MUST stay under
0x800 bytes: 16 + 32 per object + 12 per warp + 16 per trigger + 20 per bg.

**`object_events`**: NPCs, items on the ground, trainers.

| Key | Type | Meaning |
|---|---|---|
| `local_id` | name or 0-65535 | object id, defined in the map's `ids.h` |
| `graphics_id` | `SPRITE_*` | overworld sprite |
| `x`, `y`, `elevation` | int | global tiles; height |
| `movement_type` | `MOVEMENT_TYPE_*` | |
| `movement_range_x`, `movement_range_y` | int | wander range |
| `facing_dir` | `DIR_*` | initial facing |
| `trainer_type` | `OBJECT_TYPE_*` | normal, trainer (sees ahead), trainer looking all ways... |
| `trainer_sight_or_param0` | int | sight range for trainers, else a movement parameter |
| `param1`, `param2` | int | movement parameters |
| `script` | script ref (§5.3) | runs when talked to |
| `flag` | `FLAG_*` | the object is hidden while set; `FLAG_NOTHING` for never |

**`warp_events`**: doors, stairs, cave exits.

| Key | Type | Meaning |
|---|---|---|
| `x`, `y`, `elevation` | int | |
| `dest_map` | `MAP_*` | where it leads (0xFFF = the saved dynamic warp) |
| `dest_warp_id` | int | **index** of the destination map's warp to arrive on (0x100 = dynamic) |

**`coord_events`**: trigger zones.

| Key | Type | Meaning |
|---|---|---|
| `x`, `y`, `elevation`, `width`, `height` | int | the rectangle, in tiles |
| `var`, `var_value` | `VAR_*`, int or name | the script runs while `var == var_value` |
| `script` | script ref | |

**`bg_events`**: signs and hidden items.

| Key | Type | Meaning |
|---|---|---|
| `type` | `BG_TYPE_*` | `BG_TYPE_NORMAL`, `BG_TYPE_SIGNPOST`, `BG_TYPE_HIDDEN_ITEM` |
| `x`, `y`, `elevation` | int | |
| `player_facing_dir` | `BG_DIR_*` | which way the player must face |
| `script` | script ref | for hidden items, the `std_hiddenitem_*` script that sets the item |

Event order is meaningful: a warp's index (what other maps' `dest_warp_id` point
to) is its position in `warp_events`, and the game numbers objects in order.
Writers MUST keep the order unless the user reorders on purpose.

### 5.3 Script references

A `script` value is one of:

- a **label** in the map's `scripts.pory` / `ids.h` (`Cherrygrove_EventScript_GuideGent`):
  stored as that script's position in the map's script table + 1;
- a shared script constant (`std_colosseum_exit`);
- a one-argument macro (`std_trainer(TRAINER_X)`, `std_trainer_2(TRAINER_X)`);
- a number.

## 6. Layout: `<layouts>/<Folder>/layout.json`

Schema: `schemas/layout.schema.json`.

```json
{
    "name": "m_dun0101_",
    "width": 2,
    "height": 3,
    "land_data": [
        [383, 384],
        [385, 386],
        [387, 388]
    ]
}
```

| Key | Type | Meaning |
|---|---|---|
| `name` | ASCII, ≤ 255 | stored in the matrix, not used by the game |
| `width`, `height` | 1-255 | cells |
| `land_data` | rows of int or `null` | land data number of each cell; `null` = no cell |
| `maps` | rows of `MAP_*` | OPTIONAL (feature `layout_cell_maps`): which map's header applies in each cell |
| `altitudes` | rows of 0-255 | OPTIONAL (feature `layout_altitudes`): each cell's terrain is raised by altitude × 8 units |

Grids are lists of rows, north to south, each `width` long, `height` rows. Writers
SHOULD put one row per line. A layout without `maps` belongs entirely to the maps
that name it.

A map's own area is the set of cells whose `maps` entry is the map (all cells if
the layout has no `maps`). Several maps MAY share one layout (the outdoor grid;
every Pokémon Center).

## 7. Terrain cell: `<landdata>/NNNN/`

One 32 × 32-tile cell. Several layout cells MAY name the same land data; editing
it changes all of them.

| File | Required | Content |
|---|---|---|
| `permissions.txt` | yes | collision, behavior and attribute per tile (§7.1) |
| `props.json` | yes | placed props (§7.2) |
| `soundplates.bin` | no | feature `land_data_soundplates`: the cell's sound plates, raw (BINARY.md §3) |
| `model.nsbmd` | yes | the terrain's 3D model, NITRO-System NSBMD (RENDERING.md); at most 0xF000 bytes, one model |
| `terrain.bdhc` | one of these two | the heights the player walks on, BDHC (BINARY.md §3.2) |
| `heights.json` | | (1.1) the same heights as text (§7.3) |

A cell MUST have exactly one of `terrain.bdhc` and `heights.json`. A 1.0 reader
doesn't know `heights.json`; projects that use it declare 1.1.

### 7.1 `permissions.txt`

```
[collision]  # blocks movement, . is open
######......##########..........
... 32 rows of 32 characters ...
[behavior]  TILE_BEHAVIOR_* value in hex (include/constants/metatile_behavior.h)
00 00 02 02 ... 32 rows of 32 two-digit hex values ...
[attr]  bits 8-14 of the permission word, hex (FieldSystem_GetTileAttrBits8To14)
00 00 ... 32 rows ...
```

Grammar:

```
file     = section section [section]
section  = "[" name "]" [text] LF 32*row
name     = "collision" | "behavior" | "attr"
row      = 32 ("#" | ".") LF                 ; collision
         | hex2 31(" " hex2) LF              ; behavior (00-FF), attr (00-7F)
```

- Rows run north to south, characters west to east.
- `[collision]` and `[behavior]` are REQUIRED; `[attr]` MAY be left out when every
  value is 0. Text after `]` on a section line is a comment.
- Blank lines are ignored. Sections MAY come in any order; writers SHOULD write
  collision, behavior, attr.
- Each tile is the u16 `behavior | attr << 8 | collision << 15`.

Behaviors are the game's `TILE_BEHAVIOR_*` values (tall grass `02`, river `10`,
sea `15`, ice `20`, doors, ledges...). The look of a tile comes from the model,
not the behavior: change both together.

### 7.2 `props.json`

Schema: `schemas/props.schema.json`. At most 32 props per cell.

```json
[
    { "model": 29, "position": [-88.0, 17.0, -56.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0] }
]
```

| Key | Meaning |
|---|---|
| `model` | prop model number in the area's prop model archive (RENDERING.md §2) |
| `position` | model units from the cell's centre: x east, y height (absolute, not raised by the layout's altitude), z south |
| `rotation` | x, y, z; every retail prop is 0 |
| `scale` | x, y, z; every retail prop is 1 |

Writers SHOULD put one prop per line.

### 7.3 `heights.json` (1.1)

Schema: `schemas/heights.schema.json`. The plates of the cell's BDHC
(BINARY.md §3.2) as text; a writer compiles them to the binary.

```json
{
    "plates": [
        {"x": [-256, 0], "z": [-256, 256], "y": 0},
        {"x": [-64, 0], "z": [-128, -96], "ramp": {"along": "x", "y": [0, 32]}},
        {"x": [64, 96], "z": [0, 32], "normal": [0, 0.70703125, 0.70703125], "d": -45.25}
    ]
}
```

| Key | Meaning |
|---|---|
| `x`, `z` | the plate's rectangle, `[min, max]`, model units from the cell's centre (x east, z south); MUST be ordered |
| `y` | flat plate at that height (normal (0, 1, 0), d = −y) |
| `normal`, `d` | the plane `normal · (x, y, z) + d = 0`, values as stored (fx32 / 4096) |
| `ramp` | `{"along": "x" or "z", "y": [y0, y1]}`: rising linearly from y0 at the low edge to y1 at the high edge; writers store the unit normal rounded to fx32 and the d that puts the low edge at y0 |

- Each plate has exactly one of `y`, `normal` + `d`, `ramp`. Every number MUST be
  a multiple of 1/4096.
- Order is meaningful only where plates overlap at the same height: the game tests
  them in order (BINARY.md §3.2). Writers SHOULD keep the order and SHOULD write
  one plate per line.
- A plate with normal y = 0 is legal (one retail file has one) but has no height;
  checkers SHOULD warn.
- Compiling: pools, strips and the access list are derived from the plates
  (BINARY.md §3.2), so a decompiled retail file gives the same heights at every
  point; for 52 of the 676 retail files the compiled bytes differ (the originals
  repeat pool entries).

## 8. Other files in a map folder

Not part of format 1.x, listed for completeness: `scripts.pory` (event and map
scripts, [SCRIPTING.md](../modding/SCRIPTING.md)), `text.json` (messages,
msgenc JSON), `ids.h` (object and script ids). Wild encounters stay in one file
per game (`gs_enc_data.json`), as in pokeemerald.

## 9. Differences between games

Format 1.x is written from HeartGold/SoulSilver. The `features` flags say which
optional parts a game has.

| Feature | HGSS | Platinum | Diamond/Pearl |
|---|---|---|---|
| `land_data_soundplates` (sound plate block in land data) | yes | no (expected) | no (expected) |
| `layout_cell_maps`, `layout_altitudes` | yes | yes (expected) | yes (expected) |
| `map_header_in_arm9` (headers are a C table, not a file) | yes | yes (expected) | yes (expected) |

"Expected" entries come from the shared engine and haven't been checked against
pret/pokeplatinum or pret/pokediamond yet; checking them is the first step of
supporting those games (ROADMAP.md). Map header fields also differ between games
(Sinnoh has no Pokégear call or radio fields); format 1.x keeps the HGSS keys and
a later minor version adds per-game keys.

## 10. Map texture set: `<area_textures>/NNN/` (1.2)

The textures and palettes terrain models are drawn with: one folder per member of
the map texture archive (`binaries.map_textures`), `NNN` its member number in three
digits, numbered from `000` without gaps. An area header names its set (BINARY.md
§6); materials name textures and palettes in it (RENDERING.md §2). A project without
`paths.area_textures` keeps the binary archive.

| File | |
|---|---|
| `textures.json` | the set's textures and palettes in file order |
| `textures/<name>.png` | one per texture |
| `palettes/<name>.pal` | one per palette, JASC-PAL |

```json
{"textures": [
  {"name": "cavekn", "format": "palette16", "transparent": true, "palette": "cavekn_pl"},
  {"name": "sea_line02", "format": "a5i3", "palette": "sea_line02_pl"}
], "palettes": [
  {"name": "cavekn_pl"},
  {"name": "grass02_pl", "four_color": true}
]}
```

- `name`: 1 to 16 characters of `A-Z a-z 0-9 _ . -`, unique among the set's textures
  and among its palettes; at most 255 of each.
- `format`: `palette4`, `palette16`, `palette256`, `a3i5`, `a5i3` (NSBTX formats 2, 3,
  4, 1, 6; RENDERING.md §4). 4×4-compressed and direct textures are not part of 1.2.
- `transparent` (default `false`): texture bit 29, color 0 see-through.
- `palette` (string or `null`): the palette the texture is meant to be shown with. A
  writer of the archive MUST ignore it; a reader MAY use it to show the PNG.
- `four_color` (default `false`): the palette's dictionary flag 1, for `palette4`
  textures; such a palette has exactly 4 colors.
- PNG: indexed, width and height each a power of two from 8 to 1024. A pixel's value
  is the texel's value: the color index for the palette formats (below 4, 16, 256),
  the whole byte (opacity in the high bits) for `a3i5` and `a5i3`. The PNG's own
  palette is not read.
- Palette: a JASC color `r g b` (0-255) is the RGB555 color `(r >> 3, g >> 3, b >> 3)`.
  Writers SHOULD write `c << 3 | c >> 2` per channel so the file round-trips.

The archive member is the NSBTX that RENDERING.md §10 describes, built from the lists
in this order. Checked by `schemas/textures.schema.json` and `mapkit format check`
(every PNG fits its format, every listed file exists and no other).
