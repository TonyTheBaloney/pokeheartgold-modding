// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The editor's data layer, without UI (tools/mapeditor/mapeditor/project.py): one
//! open map, its layout cells, their permissions and props, its events, and the wild
//! encounter tables. Edits change these values; save() writes map.json, the
//! permissions.txt of every changed cell and, when a table changed, the tables file,
//! and nothing else.
//!
//! Coordinates are global tiles in the layout (map.json "x"/"y"), as in the game.

use std::collections::{BTreeSet, HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::time::SystemTime;

use gen4map_format::ids;
use gen4map_format::json::{self, Style};
use gen4map_format::layout::Layout;
use gen4map_format::permissions::{Permissions, Tile};
use gen4map_format::project::{MapInfo, Project};
use gen4map_format::props::{self, Prop};
use gen4map_format::wild;
use gen4map_format::{read_text, write_text, CELL};
use serde_json::{json, Map, Value};

pub const EVENT_SECTIONS: [&str; 4] = ["object_events", "warp_events", "coord_events", "bg_events"];

/// Defaults for new events, pokeemerald key order.
pub fn new_event(section: &str) -> Value {
    match section {
        "object_events" => json!({"local_id": "", "graphics_id": "SPRITE_GSMAN1", "x": 0, "y": 0, "elevation": 0,
            "movement_type": "MOVEMENT_TYPE_FACE_DOWN", "movement_range_x": 0, "movement_range_y": 0,
            "facing_dir": "DIR_SOUTH", "trainer_type": "OBJECT_TYPE_NORMAL", "trainer_sight_or_param0": 0,
            "param1": 0, "param2": 0, "script": 0, "flag": "FLAG_NOTHING"}),
        "warp_events" => json!({"x": 0, "y": 0, "elevation": 0, "dest_map": "MAP_NOTHING", "dest_warp_id": 0}),
        "coord_events" => json!({"x": 0, "y": 0, "elevation": 0, "width": 1, "height": 1, "var": "VAR_TEMP_x4000",
            "var_value": 0, "script": 0}),
        _ => json!({"type": "BG_TYPE_SIGNPOST", "x": 0, "y": 0, "elevation": 0, "player_facing_dir": "BG_DIR_ALL",
            "script": 0}),
    }
}

#[derive(Debug)]
pub enum SaveError {
    /// Files changed by something else since they were read (paths relative to the root).
    ChangedOnDisk(Vec<String>),
    Failed(String),
}

impl std::fmt::Display for SaveError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SaveError::ChangedOnDisk(p) => write!(f, "changed outside the editor: {}", p.join(", ")),
            SaveError::Failed(m) => f.write_str(m),
        }
    }
}

pub fn mtime(path: &Path) -> Option<SystemTime> {
    std::fs::metadata(path).and_then(|m| m.modified()).ok()
}

/// One land data cell: data/landdata/NNNN/.
pub struct Chunk {
    pub number: u16,
    pub dir: PathBuf,
    pub permissions: Permissions,
    pub props: Vec<Prop>,
    pub path: PathBuf,
    mtime: Option<SystemTime>,
    pub dirty: bool,
}

impl Chunk {
    pub fn load(project: &Project, number: u16) -> Result<Chunk, String> {
        let dir = project.landdata_dir(number);
        let path = dir.join("permissions.txt");
        let permissions = Permissions::from_text(&read_text(&path).map_err(|e| e.0)?, &path.display().to_string()).map_err(|e| e.0)?;
        let props = props::load(&dir.join("props.json")).map_err(|e| e.0)?;
        Ok(Chunk { number, mtime: mtime(&path), dir, permissions, props, path, dirty: false })
    }

    pub fn tile(&self, tx: usize, ty: usize) -> Tile {
        self.permissions.tile(tx, ty)
    }

    /// Returns the old value; marks the cell dirty if the value changed.
    pub fn set_tile(&mut self, tx: usize, ty: usize, t: Tile) -> Tile {
        let old = self.permissions.tile(tx, ty);
        self.permissions.set_tile(tx, ty, t);
        if self.permissions.tile(tx, ty) != old {
            self.dirty = true;
        }
        old
    }

    fn save(&mut self) -> Result<(), String> {
        if self.dirty {
            write_text(&self.path, &self.permissions.to_text()).map_err(|e| e.0)?;
            self.mtime = mtime(&self.path);
            self.dirty = false;
        }
        Ok(())
    }
}

/// The wild encounter tables (gs_enc_data.json), shared by every map. Tables are
/// addressed by position; values inside one by a JSON pointer ("/land/mons/0/level").
pub struct WildDoc {
    pub path: PathBuf,
    tables_h: PathBuf,
    data: Value,
    style: Style,
    mtime: Option<SystemTime>,
    pub dirty: bool,
    /// Tables added since the last save and their ENCDATA_ names, defined in
    /// encounter_tables_narc.h when saved.
    pub new_banks: Vec<(String, usize)>,
    /// Names defined by the last save, for the window to add to its constants.
    pub defined: Vec<(String, usize)>,
}

impl WildDoc {
    pub fn load(path: &Path, tables_h: &Path) -> Result<WildDoc, String> {
        let (data, style) = json::load(path).map_err(|e| e.0)?;
        if !data.get("encounters").is_some_and(Value::is_array) {
            return Err(format!("{}: no \"encounters\" array", path.display()));
        }
        Ok(WildDoc {
            path: path.to_path_buf(),
            tables_h: tables_h.to_path_buf(),
            mtime: mtime(path),
            data,
            style,
            dirty: false,
            new_banks: Vec::new(),
            defined: Vec::new(),
        })
    }

    pub fn tables(&self) -> &[Value] {
        self.data["encounters"].as_array().map(Vec::as_slice).unwrap_or(&[])
    }

    pub fn table(&self, index: usize) -> Option<&Value> {
        self.tables().get(index)
    }

    pub fn get(&self, index: usize, pointer: &str) -> Option<&Value> {
        self.table(index)?.pointer(pointer)
    }

    /// Set (Some) or remove (None) the value at `pointer` in a table; its parent must
    /// exist. A key comes back where the file keeps it. Returns the old value.
    pub fn set(&mut self, index: usize, pointer: &str, value: Option<Value>) -> Option<Value> {
        let (parent, last) = pointer.rsplit_once('/')?;
        let last = last.replace("~1", "/").replace("~0", "~");
        let table = self.data["encounters"].as_array_mut()?.get_mut(index)?;
        let top = parent.is_empty();
        let container = if top { table } else { table.pointer_mut(parent)? };
        let old = match container {
            Value::Object(o) => {
                let old = o.get(&last).cloned();
                if old != value {
                    match value {
                        Some(v) if o.contains_key(&last) => {
                            o.insert(last, v);
                        }
                        Some(v) => {
                            let at = if top { wild::key_position(o, &last) } else { o.len() };
                            o.shift_insert(at, last, v);
                        }
                        None => {
                            o.shift_remove(&last);
                        }
                    }
                }
                old
            }
            Value::Array(a) => {
                let i: usize = last.parse().ok()?;
                let old = a.get(i).cloned();
                match value {
                    Some(v) if i < a.len() => a[i] = v,
                    Some(v) if i == a.len() => a.push(v),
                    None if i + 1 == a.len() => {
                        a.pop();
                    }
                    _ => return None,
                }
                old
            }
            _ => return None,
        };
        self.dirty = true;
        old
    }

    /// Append a table named `bank`; returns its index.
    pub fn push_table(&mut self, table: Value, bank: &str) -> usize {
        let list = self.data["encounters"].as_array_mut().expect("checked when loaded");
        list.push(table);
        let index = list.len() - 1;
        self.new_banks.push((bank.to_string(), index));
        self.dirty = true;
        index
    }

    /// Remove the last table (undoing push_table).
    pub fn pop_table(&mut self) {
        let Some(list) = self.data["encounters"].as_array_mut() else { return };
        list.pop();
        let n = list.len();
        self.new_banks.retain(|(_, i)| *i < n);
        self.dirty = true;
    }

    /// The index of an ENCDATA_ name: one added here, or one from the constants export.
    pub fn bank_index(&self, name: &str, exported: &std::collections::BTreeMap<String, usize>) -> Option<usize> {
        self.new_banks.iter().chain(&self.defined).find(|(n, _)| n == name).map(|b| b.1).or_else(|| exported.get(name).copied())
    }

    fn changed_on_disk(&self) -> bool {
        self.dirty && mtime(&self.path) != self.mtime
    }

    fn save(&mut self) -> Result<(), String> {
        if !self.dirty {
            return Ok(());
        }
        for (name, index) in std::mem::take(&mut self.new_banks) {
            wild::add_bank_define(&self.tables_h, &name, index).map_err(|e| e.0)?;
            self.defined.push((name, index));
        }
        json::save(&self.path, &self.data, self.style).map_err(|e| e.0)?;
        self.mtime = mtime(&self.path);
        self.dirty = false;
        Ok(())
    }
}

/// An open map: map.json, its layout and the land data of its cells.
pub struct MapDoc {
    pub map: MapInfo,
    pub folder: String,
    pub map_json: PathBuf,
    pub data: Value,
    style: Style,
    pub map_json_mtime: Option<SystemTime>,
    pub layout_name: String,
    pub layout: Layout,
    pub chunks: HashMap<u16, Chunk>,
    pub dirty: bool,
    editable: HashSet<(usize, usize)>,
    /// Land data that couldn't be read: (number, why).
    pub chunk_errors: Vec<(u16, String)>,
    /// The wild encounter tables, or why they couldn't be read.
    pub wild: Result<WildDoc, String>,
}

impl MapDoc {
    pub fn open(project: &Project, query: &str) -> Result<MapDoc, String> {
        let map = project.find_map(query).ok_or_else(|| format!("no map matches {:?}", query))?.clone();
        let map_json = project.map_json(&map);
        let (data, style) = json::load(&map_json).map_err(|e| e.0)?;
        if !data.is_object() {
            return Err(format!("{}: expected an object", map_json.display()));
        }
        let layout_name = data
            .get("layout")
            .and_then(Value::as_str)
            .and_then(|l| project.layout_folder(l))
            .ok_or_else(|| format!("{} has no layout in {}", map.name, project.manifest.paths.layouts))?
            .to_string();
        let layout = project.load_layout(&layout_name).map_err(|e| e.0)?;
        let mut doc = MapDoc {
            folder: map.folder.clone(),
            map,
            map_json_mtime: mtime(&map_json),
            map_json,
            data,
            style,
            layout_name,
            layout,
            chunks: HashMap::new(),
            dirty: false,
            editable: HashSet::new(),
            chunk_errors: Vec::new(),
            wild: WildDoc::load(&project.wild_encounters(), &project.wild_tables()),
        };
        let own = doc.own_cells();
        doc.editable = if own.is_empty() { doc.all_cells().into_iter().collect() } else { own.into_iter().collect() };
        // every cell shown (the map's and one ring around them) is loaded now, so
        // reading tiles never touches the disk afterwards
        for (cx, cy) in doc.shown_cells() {
            let Some(n) = doc.cell_land(cx, cy) else { continue };
            if doc.chunks.contains_key(&n) || doc.chunk_errors.iter().any(|e| e.0 == n) {
                continue;
            }
            match Chunk::load(project, n) {
                Ok(c) => {
                    doc.chunks.insert(n, c);
                }
                Err(e) => doc.chunk_errors.push((n, e)),
            }
        }
        Ok(doc)
    }

    // --- layout ---------------------------------------------------------------------------

    pub fn width(&self) -> usize {
        self.layout.width
    }

    pub fn height(&self) -> usize {
        self.layout.height
    }

    pub fn cell_land(&self, cx: usize, cy: usize) -> Option<u16> {
        if cx < self.width() && cy < self.height() {
            self.layout.land_at(cx, cy)
        } else {
            None
        }
    }

    /// The map whose header covers a cell (every cell is the map's in layouts without a maps grid).
    pub fn cell_map(&self, cx: usize, cy: usize) -> u16 {
        self.layout.map_at(cx, cy).unwrap_or(self.map.id)
    }

    fn all_cells(&self) -> Vec<(usize, usize)> {
        let mut out = Vec::new();
        for cy in 0..self.height() {
            for cx in 0..self.width() {
                if self.cell_land(cx, cy).is_some() {
                    out.push((cx, cy));
                }
            }
        }
        out
    }

    /// Cells this map's header covers (all of them in single-map layouts).
    pub fn own_cells(&self) -> Vec<(usize, usize)> {
        self.all_cells().into_iter().filter(|&(cx, cy)| self.cell_map(cx, cy) == self.map.id).collect()
    }

    /// Cells whose tiles and events belong to this map: own_cells, or every cell when
    /// the map's header covers none (a layout without a maps grid naming it).
    pub fn editable_cells(&self) -> &HashSet<(usize, usize)> {
        &self.editable
    }

    /// True if global tile x, y is in one of editable_cells().
    pub fn on_map(&self, x: i64, y: i64) -> bool {
        x >= 0 && y >= 0 && self.editable.contains(&((x as usize) / CELL, (y as usize) / CELL))
    }

    /// (x0, y0, x1, y1) in cells around own_cells, inclusive.
    pub fn bounds(&self) -> (usize, usize, usize, usize) {
        let own = self.own_cells();
        let cells: Vec<(usize, usize)> = if own.is_empty() {
            (0..self.height()).flat_map(|cy| (0..self.width()).map(move |cx| (cx, cy))).collect()
        } else {
            own
        };
        let xs = cells.iter().map(|c| c.0);
        let ys = cells.iter().map(|c| c.1);
        (xs.clone().min().unwrap_or(0), ys.clone().min().unwrap_or(0), xs.max().unwrap_or(0), ys.max().unwrap_or(0))
    }

    /// bounds() and one ring of neighbouring cells for context, clipped to the layout.
    pub fn shown_bounds(&self) -> (usize, usize, usize, usize) {
        let (x0, y0, x1, y1) = self.bounds();
        (x0.saturating_sub(1), y0.saturating_sub(1), (x1 + 1).min(self.width() - 1), (y1 + 1).min(self.height() - 1))
    }

    /// The cells with land data inside shown_bounds().
    pub fn shown_cells(&self) -> Vec<(usize, usize)> {
        let (x0, y0, x1, y1) = self.shown_bounds();
        let mut out = Vec::new();
        for cy in y0..=y1 {
            for cx in x0..=x1 {
                if self.cell_land(cx, cy).is_some() {
                    out.push((cx, cy));
                }
            }
        }
        out
    }

    pub fn chunk(&self, cx: usize, cy: usize) -> Option<&Chunk> {
        self.chunks.get(&self.cell_land(cx, cy)?)
    }

    /// Area data id to draw a cell with. The game loads one area at a time, the
    /// current map's (src/field/area_data.c), and draws every visible cell with it.
    pub fn area(&self) -> u16 {
        self.data.get("area_data").and_then(Value::as_u64).unwrap_or(0) as u16
    }

    pub fn cell_altitude(&self, cx: usize, cy: usize) -> u8 {
        self.layout.altitude_at(cx, cy)
    }

    /// (collision, behavior, attr) at global tile x, y, or None outside the loaded cells.
    pub fn tile(&self, x: i64, y: i64) -> Option<Tile> {
        if x < 0 || y < 0 {
            return None;
        }
        let (x, y) = (x as usize, y as usize);
        Some(self.chunk(x / CELL, y / CELL)?.tile(x % CELL, y % CELL))
    }

    /// Returns the old value, or None outside the loaded cells.
    pub fn set_tile(&mut self, x: i64, y: i64, t: Tile) -> Option<Tile> {
        if x < 0 || y < 0 {
            return None;
        }
        let (x, y) = (x as usize, y as usize);
        let n = self.cell_land(x / CELL, y / CELL)?;
        Some(self.chunks.get_mut(&n)?.set_tile(x % CELL, y % CELL, t))
    }

    /// (cx, cy, index, prop, tile x, tile y) for the cells in bounds().
    pub fn props(&self) -> Vec<(usize, usize, usize, &Prop, f64, f64)> {
        let (x0, y0, x1, y1) = self.bounds();
        let mut out = Vec::new();
        for cy in y0..=y1 {
            for cx in x0..=x1 {
                let Some(c) = self.chunk(cx, cy) else { continue };
                for (i, p) in c.props.iter().enumerate() {
                    let tx = (cx * CELL) as f64 + CELL as f64 / 2.0 + p.position[0] / props::UNITS_PER_TILE;
                    let ty = (cy * CELL) as f64 + CELL as f64 / 2.0 + p.position[2] / props::UNITS_PER_TILE;
                    out.push((cx, cy, i, p, tx, ty));
                }
            }
        }
        out
    }

    // --- events ---------------------------------------------------------------------------

    /// The section's events; a map without the section reads as empty and keeps not
    /// having it (adding an event creates it).
    pub fn events(&self, section: &str) -> &[Value] {
        self.data.get(section).and_then(Value::as_array).map(Vec::as_slice).unwrap_or(&[])
    }

    pub fn event(&self, section: &str, index: usize) -> Option<&Value> {
        self.events(section).get(index)
    }

    fn event_mut(&mut self, section: &str, index: usize) -> Option<&mut Map<String, Value>> {
        self.data.get_mut(section)?.as_array_mut()?.get_mut(index)?.as_object_mut()
    }

    /// Returns the old value (None if the key was missing).
    pub fn set_event_field(&mut self, section: &str, index: usize, key: &str, value: Option<Value>) -> Option<Value> {
        let ev = self.event_mut(section, index)?;
        let old = ev.get(key).cloned();
        if old != value {
            match value {
                Some(v) => {
                    ev.insert(key.to_string(), v);
                }
                None => {
                    ev.shift_remove(key);
                }
            }
            self.dirty = true;
        }
        old
    }

    pub fn event_xy(&self, section: &str, index: usize) -> Option<(i64, i64)> {
        let ev = self.event(section, index)?;
        Some((ev.get("x")?.as_i64()?, ev.get("y")?.as_i64()?))
    }

    pub fn move_event(&mut self, section: &str, index: usize, x: i64, y: i64) -> Option<(i64, i64)> {
        let old = self.event_xy(section, index)?;
        if old != (x, y) {
            let ev = self.event_mut(section, index)?;
            ev.insert("x".into(), x.into());
            ev.insert("y".into(), y.into());
            self.dirty = true;
        }
        Some(old)
    }

    /// Insert an event (a copy of `template`, or the section's default) at x, y; returns its index.
    pub fn add_event(&mut self, section: &str, x: i64, y: i64, template: Option<&Value>, index: Option<usize>) -> usize {
        let mut ev = template.cloned().unwrap_or_else(|| new_event(section));
        ev["x"] = x.into();
        ev["y"] = y.into();
        if section == "object_events" && ev.get("local_id").and_then(Value::as_str).is_none_or(str::is_empty) {
            ev["local_id"] = self.new_local_id().into();
        }
        let obj = self.data.as_object_mut().expect("map.json is an object");
        let list = obj.entry(section).or_insert_with(|| Value::Array(Vec::new()));
        if !list.is_array() {
            *list = Value::Array(Vec::new());
        }
        let list = list.as_array_mut().unwrap();
        let index = index.unwrap_or(list.len()).min(list.len());
        list.insert(index, ev);
        self.dirty = true;
        index
    }

    pub fn remove_event(&mut self, section: &str, index: usize) -> Option<Value> {
        let list = self.data.get_mut(section)?.as_array_mut()?;
        if index >= list.len() {
            return None;
        }
        self.dirty = true;
        Some(list.remove(index))
    }

    fn new_local_id(&self) -> String {
        let used: HashSet<&str> = self.events("object_events").iter().filter_map(|e| e.get("local_id")?.as_str()).collect();
        let code = self.data.get("code").and_then(Value::as_str).filter(|c| !c.is_empty()).unwrap_or(&self.folder);
        let base = format!("obj_{}_new", code);
        let n = (1..).find(|n| !used.contains(format!("{}{}", base, n).as_str())).unwrap();
        format!("{}{}", base, n)
    }

    // --- header ---------------------------------------------------------------------------

    pub fn header_fields(&self) -> Vec<(String, Value)> {
        self.data
            .as_object()
            .map(|o| o.iter().filter(|(k, _)| !EVENT_SECTIONS.contains(&k.as_str())).map(|(k, v)| (k.clone(), v.clone())).collect())
            .unwrap_or_default()
    }

    pub fn set_header_field(&mut self, key: &str, value: Option<Value>) -> Option<Value> {
        let obj = self.data.as_object_mut()?;
        let old = obj.get(key).cloned();
        if old != value {
            match value {
                Some(v) => {
                    obj.insert(key.to_string(), v);
                }
                None => {
                    obj.shift_remove(key);
                }
            }
            self.dirty = true;
        }
        old
    }

    // --- saving ---------------------------------------------------------------------------

    pub fn modified(&self) -> bool {
        self.dirty || self.chunks.values().any(|c| c.dirty) || self.wild.as_ref().is_ok_and(|w| w.dirty)
    }

    /// The wild table index map.json names, if there is one.
    pub fn wild_index(&self, exported: &std::collections::BTreeMap<String, usize>) -> Option<usize> {
        let bank = self.data.get("wild_encounters")?.as_str()?;
        self.wild.as_ref().ok()?.bank_index(bank, exported)
    }

    /// Files this save would write that something else changed since they were read.
    pub fn changed_on_disk(&self, root: &Path) -> Vec<String> {
        let rel = |p: &Path| p.strip_prefix(root).unwrap_or(p).display().to_string();
        let mut out = Vec::new();
        if self.dirty && mtime(&self.map_json) != self.map_json_mtime {
            out.push(rel(&self.map_json));
        }
        let mut cells: Vec<&Chunk> = self.chunks.values().filter(|c| c.dirty && mtime(&c.path) != c.mtime).collect();
        cells.sort_by_key(|c| c.number);
        out.extend(cells.iter().map(|c| rel(&c.path)));
        if let Ok(w) = &self.wild {
            if w.changed_on_disk() {
                out.push(rel(&w.path));
            }
        }
        out
    }

    /// local_ids of objects that ids.h doesn't define (objects added in the editor).
    pub fn missing_object_ids(&self, project: &Project) -> Vec<String> {
        let defs = ids::read(&project.ids_h(&self.map)).unwrap_or_default();
        self.events("object_events")
            .iter()
            .filter_map(|e| e.get("local_id")?.as_str())
            .filter(|id| !defs.contains_key(*id))
            .map(String::from)
            .collect()
    }

    /// Write what changed. Refuses with ChangedOnDisk, unless `force`, when a file to be
    /// written was changed by something else since it was read.
    pub fn save(&mut self, project: &Project, force: bool) -> Result<(), SaveError> {
        if !force {
            let changed = self.changed_on_disk(&project.root);
            if !changed.is_empty() {
                return Err(SaveError::ChangedOnDisk(changed));
            }
        }
        if self.dirty {
            self.define_object_ids(project).map_err(SaveError::Failed)?;
            json::save(&self.map_json, &self.data, self.style).map_err(|e| SaveError::Failed(e.0))?;
            self.map_json_mtime = mtime(&self.map_json);
            self.dirty = false;
        }
        let mut numbers: Vec<u16> = self.chunks.keys().copied().collect();
        numbers.sort_unstable();
        for n in numbers {
            self.chunks.get_mut(&n).unwrap().save().map_err(SaveError::Failed)?;
        }
        if let Ok(w) = &mut self.wild {
            w.save().map_err(SaveError::Failed)?;
        }
        Ok(())
    }

    /// Give new objects a #define in ids.h, as `mapkit npc add` does: the lowest number
    /// no object of the map uses.
    fn define_object_ids(&self, project: &Project) -> Result<(), String> {
        let missing = self.missing_object_ids(project);
        if missing.is_empty() {
            return Ok(());
        }
        let path = project.ids_h(&self.map);
        let defs = ids::read(&path).map_err(|e| e.0)?;
        let mut used: BTreeSet<i64> = self
            .events("object_events")
            .iter()
            .filter_map(|e| match e.get("local_id")? {
                Value::String(s) => defs.get(s).copied(),
                v => v.as_i64(),
            })
            .collect();
        for name in missing {
            let Some(num) = (0..256).find(|n| !used.contains(n)) else {
                return Err(format!("{}: no free object number for {}", path.display(), name));
            };
            ids::add_define(&path, &name, num, "obj_").map_err(|e| e.0)?;
            used.insert(num);
        }
        Ok(())
    }

    /// Re-read map.json's time after a reload or an outside change was accepted.
    pub fn map_json_changed_outside(&self) -> bool {
        mtime(&self.map_json) != self.map_json_mtime
    }
}

/// [(folder, MAP_* name, map id)] for every map, by folder.
pub fn map_list(project: &Project) -> Vec<(String, String, u16)> {
    let mut out: Vec<_> = project.maps.iter().map(|m| (m.folder.clone(), m.name.clone(), m.id)).collect();
    out.sort();
    out
}
