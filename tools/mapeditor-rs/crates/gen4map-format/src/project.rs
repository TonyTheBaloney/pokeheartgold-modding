// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! A project: a checkout whose data/gen4map.json says where maps, layouts and land
//! data are (the Rust counterpart of mapkit's Repo, for the map files only).

use std::collections::{BTreeSet, HashMap};
use std::path::{Path, PathBuf};

use serde_json::Value;

use crate::index::{self, LayoutEntry, MapEntry};
use crate::layout::Layout;
use crate::manifest::{self, Manifest};
use crate::{bail, json, Result};

/// A map that lives in the maps folder and has an id in maps.h.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MapInfo {
    pub id: u16,
    pub name: String,   // MAP_CHERRYGROVE
    pub code: String,   // T21
    pub folder: String, // Cherrygrove
}

pub struct Project {
    pub root: PathBuf,
    pub manifest: Manifest,
    pub entries: Vec<MapEntry>,
    /// Sorted by id.
    pub maps: Vec<MapInfo>,
    pub map_ids: HashMap<String, u16>,
    pub layouts: Vec<LayoutEntry>,
}

/// The nearest directory at or above `start` with a manifest.
pub fn find_root(start: &Path) -> Option<PathBuf> {
    let start = start.canonicalize().ok()?;
    start.ancestors().find(|d| d.join(manifest::PATH).is_file()).map(Path::to_path_buf)
}

fn normalize(s: &str) -> String {
    s.chars().filter(|c| c.is_ascii_alphanumeric()).map(|c| c.to_ascii_lowercase()).collect()
}

impl Project {
    pub fn open(root: &Path) -> Result<Project> {
        let manifest = Manifest::load(root)?;
        let entries = index::read_maps_txt(&root.join(&manifest.paths.map_index))?;
        let layouts = index::read_layouts_txt(&root.join(&manifest.paths.layout_index))?;
        let ids = index::read_maps_h(&root.join(&manifest.paths.map_ids))?;
        let mut map_ids = HashMap::new();
        for m in &ids {
            map_ids.entry(m.name.clone()).or_insert(m.id);
        }
        let mut maps: Vec<MapInfo> = entries
            .iter()
            .filter_map(|e| {
                let m = ids.iter().find(|m| m.name == e.map)?;
                Some(MapInfo { id: m.id, name: m.name.clone(), code: m.code.clone(), folder: e.dir.clone() })
            })
            .collect();
        maps.sort_by_key(|m| m.id);
        Ok(Project { root: root.to_path_buf(), manifest, entries, maps, map_ids, layouts })
    }

    pub fn path(&self, rel: &str) -> PathBuf {
        self.root.join(rel)
    }

    /// Accepts MAP_CHERRYGROVE, CHERRYGROVE, cherrygrove, Cherrygrove_PokeMart, T21 or 67,
    /// as mapkit's Repo.find_map does, and also the folder name.
    pub fn find_map(&self, query: &str) -> Option<&MapInfo> {
        let q = query.trim();
        if let Ok(id) = q.parse::<u16>() {
            if let Some(m) = self.maps.iter().find(|m| m.id == id) {
                return Some(m);
            }
        }
        let norm = normalize(q);
        self.maps.iter().find(|m| {
            q == m.name
                || q == m.folder
                || q.to_ascii_uppercase() == m.code
                || norm == normalize(m.name.strip_prefix("MAP_").unwrap_or(&m.name))
                || norm == normalize(&m.folder)
        })
    }

    pub fn map_dir(&self, m: &MapInfo) -> PathBuf {
        self.root.join(&self.manifest.paths.maps).join(&m.folder)
    }

    pub fn map_json(&self, m: &MapInfo) -> PathBuf {
        self.map_dir(m).join("map.json")
    }

    fn entry(&self, m: &MapInfo) -> Option<&MapEntry> {
        self.entries.iter().find(|e| e.dir == m.folder)
    }

    /// ids.h with the map's object ids: the one in the folder that owns its events.
    pub fn ids_h(&self, m: &MapInfo) -> PathBuf {
        let owner = self.entry(m).map(|e| index::bank_owner(&self.entries, e, "events")).unwrap_or(&m.folder);
        self.root.join(&self.manifest.paths.maps).join(owner).join("ids.h")
    }

    /// Folder of a layout named by map.json's "layout", if layouts.txt has it.
    pub fn layout_folder(&self, name: &str) -> Option<&str> {
        self.layouts.iter().find(|l| l.dir == name).map(|l| l.dir.as_str())
    }

    pub fn layout_path(&self, folder: &str) -> PathBuf {
        self.root.join(&self.manifest.paths.layouts).join(folder).join("layout.json")
    }

    pub fn load_layout(&self, folder: &str) -> Result<Layout> {
        Layout::load(&self.layout_path(folder), &self.map_ids)
    }

    pub fn landdata_dir(&self, number: u16) -> PathBuf {
        self.root.join(&self.manifest.paths.landdata).join(format!("{:04}", number))
    }

    pub fn area_textures_dir(&self) -> PathBuf {
        self.root.join(&self.manifest.paths.area_textures)
    }

    /// The layout folder a map uses, from its map.json.
    pub fn map_layout(&self, m: &MapInfo) -> Result<String> {
        let (d, _) = json::load(&self.map_json(m))?;
        match d.get("layout").and_then(Value::as_str).and_then(|l| self.layout_folder(l)) {
            Some(l) => Ok(l.to_string()),
            None => bail!("{} has no layout in {}", m.name, self.manifest.paths.layouts),
        }
    }

    /// {land data number: map folders that show it}, over every layout: an edit to a
    /// cell changes all of them.
    pub fn land_index(&self) -> HashMap<u16, BTreeSet<String>> {
        let mut by_layout: HashMap<String, Vec<&MapInfo>> = HashMap::new();
        for m in &self.maps {
            if let Ok(l) = self.map_layout(m) {
                by_layout.entry(l).or_default().push(m);
            }
        }
        let mut out: HashMap<u16, BTreeSet<String>> = HashMap::new();
        for (folder, maps) in by_layout {
            let Ok(lay) = self.load_layout(&folder) else { continue };
            for (i, land) in lay.land.iter().enumerate() {
                let Some(n) = land else { continue };
                let users: Vec<String> = match lay.maps.get(i) {
                    None => maps.iter().map(|m| m.folder.clone()).collect(),
                    Some(id) => maps.iter().filter(|m| m.id == *id).map(|m| m.folder.clone()).collect(),
                };
                if !users.is_empty() {
                    out.entry(*n).or_default().extend(users);
                }
            }
        }
        out
    }
}
