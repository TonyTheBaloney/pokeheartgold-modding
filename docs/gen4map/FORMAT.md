<!-- [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22 -->

# gen4map format 1.0: maps, layouts, terrain cells, events

> AI-generated, local to this fork. Do not upstream.

This is the specification of the text formats this fork stores Generation IV
(Nintendo DS) Pokémon maps in. It is written so that a separate tool can read and
write the same files for any Gen 4 game (Diamond/Pearl, Platinum,
HeartGold/SoulSilver) without this repository's build. The ROM-side binaries the
files map to are in [BINARY.md](BINARY.md); how the 3D data is drawn is in
[RENDERING.md](RENDERING.md).

The words MUST, SHOULD and MAY are used as in RFC 2119. "Reader" is any program
that loads these files; "writer" is any program that saves them.

Status: **1.0**, describing the files in this repository on 2026-10-22. Every
file conforms: `tools/mapkit/mapkit.sh format check`.

## 1. Versioning

- A project declares its format version in the manifest (§2): `"version": "1.0"`.
- Minor versions only **add** optional keys or files. A 1.x reader MUST read
  1.0 files; a 1.0 reader that meets a key it doesn't know reports an error
  (keys are closed, so typos are caught) and SHOULD tell the user to update.
- A major version changes the meaning or shape of something that exists. A
  reader MUST refuse a major version it doesn't support.
- Machine-readable definitions: `schemas/map.schema.json`, `layout.schema.json`,
  `props.schema.json`, `manifest.schema.json` (JSON Schema 2020-12). Where this
  text and a schema disagree, this text wins and the schema is a bug.

## 2. Project and manifest

A project is a directory tree. Its root holds the manifest at `data/gen4map.json`:

```json
{
    "format": "gen4map",
    "version": "1.0",
    "game": { "family": "HGSS", "versions": ["HEARTGOLD", "SOULSILVER"], "language": "en_US" },
    "paths": { "maps": "data/maps", "map_index": "data/maps/maps.txt",
               "layouts": "data/layouts", "layout_index": "data/layouts/layouts.txt",
               "landdata": "data/landdata", "constants": "include/constants",
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
| `model.nsbmd` | yes | the terrain's 3D model, NITRO-System NSBMD (RENDERING.md) |
| `terrain.bdhc` | yes | the heights the player walks on, BDHC (BINARY.md §3.2) |

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

## 8. Other files in a map folder

Not part of format 1.0, listed for completeness: `scripts.pory` (event and map
scripts, [SCRIPTING.md](../modding/SCRIPTING.md)), `text.json` (messages,
msgenc JSON), `ids.h` (object and script ids). Wild encounters stay in one file
per game (`gs_enc_data.json`), as in pokeemerald.

## 9. Differences between games

Format 1.0 is written from HeartGold/SoulSilver. The `features` flags say which
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
