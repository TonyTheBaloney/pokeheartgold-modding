// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Constant names, tile behaviors and sprite files, from `mapkit export-constants`
//! (tools/mapkit/mapkit/export.py). C headers are read by mapkit only, so the
//! preprocessor rules live in one place.

use std::collections::BTreeMap;
use std::path::Path;
use std::process::Command;

use serde::Deserialize;

use crate::{Error, Result};

pub const FORMAT_VERSION: u32 = 1;

#[derive(Debug, Clone, Default, Deserialize)]
pub struct Constants {
    pub format: String,
    pub version: u32,
    pub game: String,
    /// prefix -> sorted names
    pub constants: BTreeMap<String, Vec<String>>,
    /// value (decimal string) -> TILE_BEHAVIOR_ name
    pub behaviors: BTreeMap<String, String>,
    /// SPRITE_ name -> NSBTX path relative to the root
    pub sprites: BTreeMap<String, String>,
    /// ENCDATA_ name -> index of its table in the wild encounter file (exports from
    /// before the editor edited wild encounters don't have it)
    #[serde(default)]
    pub wild: BTreeMap<String, usize>,
}

impl Constants {
    pub fn parse(text: &str) -> Result<Constants> {
        let c: Constants = serde_json::from_str(text).map_err(|e| Error(format!("constants export: {}", e)))?;
        if c.format != "mapkit-constants" || c.version != FORMAT_VERSION {
            return Err(Error(format!(
                "constants export is {} version {}, expected mapkit-constants version {}",
                c.format, c.version, FORMAT_VERSION
            )));
        }
        Ok(c)
    }

    /// Run `python3 -m mapkit export-constants` from root/tools/mapkit.
    pub fn export(root: &Path, game: &str) -> Result<Constants> {
        let out = Command::new("python3")
            .args(["-m", "mapkit", "--root"])
            .arg(root)
            .args(["--version", game, "export-constants"])
            .env("PYTHONPATH", root.join("tools/mapkit"))
            .output()
            .map_err(|e| Error(format!("can't run python3 for mapkit: {}", e)))?;
        if !out.status.success() {
            return Err(Error(format!("mapkit export-constants failed: {}", String::from_utf8_lossy(&out.stderr).trim())));
        }
        Constants::parse(&String::from_utf8_lossy(&out.stdout))
    }

    /// Sorted names with a prefix; empty if the prefix isn't exported (then values
    /// with it aren't checked).
    pub fn names(&self, prefix: &str) -> &[String] {
        self.constants.get(prefix).map(Vec::as_slice).unwrap_or(&[])
    }

    pub fn is_known(&self, prefix: &str, name: &str) -> bool {
        self.names(prefix).binary_search_by(|n| n.as_str().cmp(name)).is_ok()
    }

    /// Make a name known (one the editor just defined).
    pub fn add_name(&mut self, prefix: &str, name: &str) {
        let names = self.constants.entry(prefix.to_string()).or_default();
        if let Err(i) = names.binary_search_by(|n| n.as_str().cmp(name)) {
            names.insert(i, name.to_string());
        }
    }

    pub fn behavior_names(&self) -> BTreeMap<u8, String> {
        self.behaviors.iter().filter_map(|(k, v)| Some((k.parse().ok()?, v.clone()))).collect()
    }
}
