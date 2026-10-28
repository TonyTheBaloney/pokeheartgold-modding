// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! data/gen4map.json: where a project keeps each kind of file (FORMAT.md §2).
//! Tools learn paths from here, not from this repository's layout.

use std::collections::BTreeMap;
use std::path::Path;

use serde::Deserialize;

use crate::{read_text, Error, Result};

pub const PATH: &str = "data/gen4map.json";

#[derive(Debug, Clone, Deserialize)]
pub struct Manifest {
    pub format: String,
    pub version: String,
    pub game: Game,
    pub paths: Paths,
    #[serde(default)]
    pub binaries: BTreeMap<String, serde_json::Value>,
    #[serde(default)]
    pub features: BTreeMap<String, bool>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Game {
    pub family: String,
    pub versions: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Paths {
    pub maps: String,
    pub map_index: String,
    pub layouts: String,
    pub layout_index: String,
    pub landdata: String,
    #[serde(default = "default_area_textures")]
    pub area_textures: String,
    pub map_ids: String,
    pub tile_behaviors: String,
}

fn default_area_textures() -> String {
    "data/area_textures".into()
}

impl Manifest {
    pub fn load(root: &Path) -> Result<Manifest> {
        let path = root.join(PATH);
        let raw = read_text(&path)?;
        let m: Manifest = serde_json::from_str(&raw).map_err(|e| Error(format!("{}: {}", path.display(), e)))?;
        if m.format != "gen4map" {
            return Err(Error(format!("{}: format is {:?}, not gen4map", path.display(), m.format)));
        }
        Ok(m)
    }

    /// A NitroFS path from "binaries" (`a/0/4/2`), as a string; nested ones with a key.
    pub fn binary(&self, key: &str, sub: Option<&str>) -> Option<String> {
        let v = self.binaries.get(key)?;
        match sub {
            Some(s) => v.get(s)?.as_str().map(String::from),
            None => v.as_str().map(String::from),
        }
    }
}
