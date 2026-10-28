// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! layout.json: a layout's grid of cells (tools/mapkit/mapkit/layouts.py).
//!
//! ```json
//! {
//!     "name": "m_dun0101_", "width": 2, "height": 3,
//!     "land_data": [[12, 13], ...],      one row per line; null = no cell
//!     "maps": [["MAP_X", ...], ...],     only if the matrix has per-cell headers
//!     "altitudes": [[0, 2], ...]         only if it has altitudes
//! }
//! ```

use std::collections::HashMap;
use std::path::Path;

use serde_json::Value;

use crate::{bail, json, Result};

#[derive(Debug, Clone, PartialEq)]
pub struct Layout {
    pub name: String,
    pub width: usize,
    pub height: usize,
    /// Land data number of each cell, row by row; None = no cell.
    pub land: Vec<Option<u16>>,
    /// Map id of each cell's header; empty when the layout has none (every cell is the map's).
    pub maps: Vec<u16>,
    /// Altitude of each cell; empty when the layout has none.
    pub altitudes: Vec<u8>,
}

impl Layout {
    pub fn land_at(&self, cx: usize, cy: usize) -> Option<u16> {
        self.land[cy * self.width + cx]
    }

    pub fn map_at(&self, cx: usize, cy: usize) -> Option<u16> {
        self.maps.get(cy * self.width + cx).copied()
    }

    pub fn altitude_at(&self, cx: usize, cy: usize) -> u8 {
        self.altitudes.get(cy * self.width + cx).copied().unwrap_or(0)
    }

    pub fn load(path: &Path, map_ids: &HashMap<String, u16>) -> Result<Layout> {
        let (d, _) = json::load(path)?;
        Layout::from_json(&d, map_ids, &path.display().to_string())
    }

    /// As layouts.from_json: map names resolved with maps.h.
    pub fn from_json(d: &Value, map_ids: &HashMap<String, u16>, wh: &str) -> Result<Layout> {
        let Some(obj) = d.as_object() else { bail!("{}: expected an object", wh) };
        for k in obj.keys() {
            if !matches!(k.as_str(), "name" | "width" | "height" | "land_data" | "maps" | "altitudes") {
                bail!("{}: unknown key {}", wh, k);
            }
        }
        let dim = |k: &str| obj.get(k).and_then(Value::as_u64).filter(|v| (1..=255).contains(v));
        let (Some(w), Some(h)) = (dim("width"), dim("height")) else {
            bail!("{}: width and height must be 1-255", wh)
        };
        let (w, h) = (w as usize, h as usize);
        let name = match obj.get("name") {
            None => String::new(),
            Some(Value::String(s)) if s.is_ascii() && s.len() <= 255 => s.clone(),
            _ => bail!("{}: name must be ASCII, at most 255 characters", wh),
        };
        let cells = |key: &str| -> Result<Vec<&Value>> {
            let rows = obj[key].as_array().filter(|r| r.len() == h && r.iter().all(|r| r.as_array().is_some_and(|r| r.len() == w)));
            match rows {
                Some(rows) => Ok(rows.iter().flat_map(|r| r.as_array().unwrap()).collect()),
                None => bail!("{}: {} must be {} rows of {}", wh, key, h, w),
            }
        };
        let at = |key: &str, i: usize| format!("{}: {}[{}][{}]", wh, key, i / w, i % w);
        if !obj.contains_key("land_data") {
            bail!("{}: missing land_data", wh);
        }
        let mut land = Vec::with_capacity(w * h);
        for (i, v) in cells("land_data")?.into_iter().enumerate() {
            land.push(match v {
                Value::Null => None,
                v => match v.as_u64().filter(|&n| n < 0xFFFF) {
                    Some(n) => Some(n as u16),
                    None => bail!("{}: {} is not a land data number or null", at("land_data", i), v),
                },
            });
        }
        let mut maps = Vec::new();
        if obj.contains_key("maps") {
            for (i, v) in cells("maps")?.into_iter().enumerate() {
                maps.push(match v {
                    Value::String(s) if map_ids.contains_key(s) => map_ids[s],
                    v => match v.as_u64().filter(|&n| n <= 0xFFFF) {
                        Some(n) => n as u16,
                        None => bail!("{}: unknown map {}", at("maps", i), v),
                    },
                });
            }
        }
        let mut altitudes = Vec::new();
        if obj.contains_key("altitudes") {
            for (i, v) in cells("altitudes")?.into_iter().enumerate() {
                match v.as_u64().filter(|&n| n <= 255) {
                    Some(n) => altitudes.push(n as u8),
                    None => bail!("{}: altitude {} is not 0-255", at("altitudes", i), v),
                }
            }
        }
        Ok(Layout { name, width: w, height: h, land, maps, altitudes })
    }
}
