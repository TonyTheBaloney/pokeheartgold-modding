<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28 -->

# Map editor (Rust)

> AI-generated; not affiliated with pret. See AI.md at the repository root.

The map editor of [tools/mapeditor](../mapeditor/README.md) rewritten in Rust: the
same window, tools and files, as one native program with no Python environment to
set up. It edits `data/maps/`, `data/layouts/` and `data/landdata/` like the Python
editor and saves them the same way, byte for byte; both can be used on the same
checkout. It also edits the maps' wild encounter tables, which the Python editor
doesn't. Build the ROM afterwards with `make release`. How and why it was made:
[CHANGE-0005](../../docs/gen4map/CHANGE-0005-rust-map-editor.md).

## Run

Rust 1.95 or newer (`cargo`), and `python3` for mapkit (constant names come from it):

```sh
tools/mapeditor-rs/mapeditor-rs.sh              # pick a map from the list
tools/mapeditor-rs/mapeditor-rs.sh Cherrygrove  # or MAP_CHERRYGROVE, T21, 67
tools/mapeditor-rs/mapeditor-rs.sh Ecruteak --3d
tools/mapeditor-rs/mapeditor-rs.sh Route29 --wild   # in the wild encounters tab
```

The script builds the release binary the first time (a few minutes) and then just
starts it. The binary is `tools/mapeditor-rs/target/release/mapeditor-rs`; it finds
the checkout from the current directory, or takes `--root DIR`.

## Using it

The window, tools, shortcuts and what saving writes are the Python editor's; its
README describes them ([Window](../mapeditor/README.md#window),
[Tools](../mapeditor/README.md#tools),
[Files in a text editor](../mapeditor/README.md#files-in-a-text-editor),
[What saving writes](../mapeditor/README.md#what-saving-writes)). Differences:

| | Python editor | Rust editor |
|---|---|---|
| Open a map | double-click in the list | double-click, or Enter on the focused row |
| Completion of constants | Qt completer | list under the field: type to filter, arrows and Enter, or click |
| Settings (text editor, view layers) | `~/.config/pokeheartgold-modding/mapeditor.conf` | `~/.config/mapeditor-rs/settings.json` (layers are remembered too) |
| Terrain pictures | drawn on the UI thread when a cell is first shown | drawn by background threads, cells in view first; shared between maps for the session |
| Several events selected | Delete removes one of them | Delete and the context menu remove all of them |
| Outside changes to map.json | file watcher | checked once a second |

### Wild encounters

The *Wild encounters* tab, next to *Map* and *3D*, shows the table the map's
`wild_encounters` names in `files/fielddata/encountdata/gs_enc_data.json`:

- *Table*: which table the map uses (completes `ENCDATA_` names; `ENCDATA_NA` for none).
  *New empty table* / *Copy into a new table* append one, named `ENCDATA_<map code>`,
  and point the map at it; saving adds its `#define` to
  `include/encounter_tables_narc.h`.
- *Version*: *Both* shows values as written and an edit sets both versions; a value
  that differs shows as `{"HEARTGOLD": ..., "SOULSILVER": ...}`. *HeartGold* or
  *SoulSilver* shows and edits that version alone.
- One section per method (grass, surfing, Rock Smash, three rods): the rate, *Add N
  slots* / *Remove all slots*, and per slot (numbered from 0, as in the JSON) its odds,
  level(s) and species (grass: morning, day, night). Then the radio species, swarms and
  night fishing; an emptied swarm field removes the key.
- Problems that would build wrong or play oddly are listed at the top (slot counts,
  levels outside 1-100, unknown species, a missing radio or night fishing species).
- Other maps using the same table are named.

Edits go through undo like the others. Saving writes `gs_enc_data.json` (unchanged
formatting, so the diff is only the edit), refusing like any file changed outside the
editor. What the fields mean and how to make the same edits by hand:
[docs/modding/wild-encounters.md](../../docs/modding/wild-encounters.md#editing-a-table-by-hand).

Anything wrong with a map (a land data cell that doesn't parse, a model that doesn't
decode, a missing constants export) is reported in a dialog or the status bar and the
rest keeps working.

`MAPEDITOR_RS_SCREENSHOT=out.png mapeditor-rs Map` saves the window to `out.png`
once the terrain is drawn, then quits (for checking the look from scripts).

## Code

A Cargo workspace; the three libraries don't depend on the UI.

| Crate | |
|---|---|
| `crates/gen4map-format` | the text formats: `map.json` (written as Python's `json.dumps` does), `layout.json`, `permissions.txt`, `props.json`, `maps.txt`, `layouts.txt`, `maps.h`, `ids.h`, the manifest; the project (maps, layouts, which maps share land data); the constants export; `wild.rs`: wild encounter tables (methods and odds, per-version values, checks, `ENCDATA_` defines) |
| `crates/gen4map-nitro` | NARC, NSBTX (all seven texture formats), NSBMD to triangles, map texture sets from their PNG folders, BDHC heights |
| `crates/gen4map-render` | top-down pictures of cells: a CPU rasterizer with the Python editor's rules (affine texture mapping, lowest triangles first) |
| `crates/mapeditor` | the editor (egui, OpenGL through glow): `doc.rs` data layer, `commands.rs` undo, `canvas.rs` map view, `forms.rs` fields, `view3d.rs` 3D tab, `sprites.rs`, `terrain.rs` background drawing, `external.rs` text editors, `wild.rs` wild encounters tab, `app.rs` window |

Paths come from `data/gen4map.json` (`paths` and `binaries`), not from this
repository's layout; `paths.wild_encounters` and `paths.wild_tables` default to the
decomp's files. Constant names (flags, sprites, map ids, species, wild tables and their
indexes...), tile behavior names and the sprite table come from `tools/mapkit/mapkit.sh export-constants`, which the
editor runs at start: C headers are read by mapkit only.

## Tests

```sh
cd tools/mapeditor-rs && cargo test
```

Unit tests, plus tests on this repository's data (skipped elsewhere), several of
them against mapkit through `tests/oracle.py`:

- every `map.json`, `permissions.txt` and `props.json` reads and writes back
  byte-identical; every map opens and saves unchanged;
- layouts, the map list, `ids.h` paths and the shared land data index equal mapkit's;
- decoded triangles of land and prop models, area and sprite textures, and BDHC heights
  equal mapkit's (positions and UVs to 1e-9, colors and pixels exactly);
- edits on a scratch copy: paint, move, set, add and delete with undo and redo; saving
  writes exactly `map.json`, the painted `permissions.txt` and `ids.h`; files changed
  outside are refused unless forced; the clean state after undo;
- wild encounters: `gs_enc_data.json` writes back byte-identical and all 142 tables pass
  the checks; on a scratch copy, a per-version edit and a removed swarm undo back to the
  same bytes, saving writes only `gs_enc_data.json`, a new table is appended with its
  `ENCDATA_` define and the map pointing at it, and an outside change is refused.

## Not yet

As for the Python editor: props, layouts and object `attr` can't be edited, events of
other maps on a layout aren't shown. Also:

- a cell with `heights.json` instead of `terrain.bdhc` stands 3D sprites at its altitude;
- the UI itself (mouse, fields, dialogs) has no automated tests; the Python editor
  drives its window offscreen in `tests/test_window.py`.
