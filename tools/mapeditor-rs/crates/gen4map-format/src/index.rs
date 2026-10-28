// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The indexes: data/maps/maps.txt, data/layouts/layouts.txt and the map ids in
//! include/constants/maps.h (tools/mapkit/mapkit/layout.py, layouts.py, repo.py).

use std::collections::BTreeMap;
use std::path::Path;

use crate::{bail, read_text, Result};

/// One line of maps.txt: `<Folder> <MAP_X> events=... scripts=... init=... text=...`.
/// A bank written `@Folder` is that folder's.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MapEntry {
    pub dir: String,
    pub map: String,
    pub banks: BTreeMap<String, String>,
}

pub fn read_maps_txt(path: &Path) -> Result<Vec<MapEntry>> {
    let mut out = Vec::new();
    for (n, line) in read_text(path)?.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let mut parts = line.split_whitespace();
        let (Some(dir), Some(map)) = (parts.next(), parts.next()) else {
            bail!("{}:{}: expected <Folder> <MAP_X> ...", path.display(), n + 1)
        };
        let mut banks = BTreeMap::new();
        for kv in parts {
            let Some((k, v)) = kv.split_once('=') else { bail!("{}:{}: {:?} is not key=value", path.display(), n + 1, kv) };
            banks.insert(k.to_string(), v.to_string());
        }
        out.push(MapEntry { dir: dir.into(), map: map.into(), banks });
    }
    Ok(out)
}

/// The folder holding an entry's bank (`events`, `scripts`, `init` or `text`),
/// following an `@Owner` reference (layout.resolve).
pub fn bank_owner<'a>(entries: &'a [MapEntry], entry: &'a MapEntry, bank: &str) -> &'a str {
    match entry.banks.get(bank).and_then(|v| v.strip_prefix('@')) {
        Some(owner) => entries.iter().find(|e| e.dir == owner).map(|e| e.dir.as_str()).unwrap_or(owner),
        None => &entry.dir,
    }
}

/// One line of layouts.txt: `<Folder> <original matrix base name>`, in NARC order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LayoutEntry {
    pub dir: String,
    pub base: String,
}

pub fn read_layouts_txt(path: &Path) -> Result<Vec<LayoutEntry>> {
    let mut out = Vec::new();
    for (n, line) in read_text(path)?.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() != 2 {
            bail!("{}:{}: expected <Folder> <base>", path.display(), n + 1);
        }
        out.push(LayoutEntry { dir: parts[0].into(), base: parts[1].into() });
    }
    Ok(out)
}

/// A map id from maps.h: `#define MAP_CHERRYGROVE 67 // MAP_T21`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MapId {
    pub name: String,
    pub id: u16,
    /// Game Freak's code from the comment (T21), or "".
    pub code: String,
}

pub fn read_maps_h(path: &Path) -> Result<Vec<MapId>> {
    let mut out = Vec::new();
    for line in read_text(path)?.lines() {
        let Some(rest) = line.strip_prefix("#define") else { continue };
        let mut toks = rest.split_whitespace();
        let (Some(name), Some(num)) = (toks.next(), toks.next()) else { continue };
        let Ok(id) = num.parse::<u16>() else { continue };
        if !name.starts_with("MAP_") {
            continue;
        }
        let code = match (toks.next(), toks.next()) {
            (Some("//"), Some(c)) => c.strip_prefix("MAP_").unwrap_or("").to_string(),
            _ => String::new(),
        };
        out.push(MapId { name: name.into(), id, code });
    }
    Ok(out)
}
