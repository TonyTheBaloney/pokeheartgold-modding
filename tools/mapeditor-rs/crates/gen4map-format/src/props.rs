// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! props.json: the props (trees, houses, signs) placed in a cell
//! (tools/mapkit/mapkit/landdata.py). Positions are model units, cell centre at 0,
//! 16 units per tile; rotations in degrees; values are multiples of 1/4096.

use std::path::Path;

use serde::Deserialize;

use crate::{read_text, Error, Result};

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Prop {
    pub model: u32,
    pub position: [f64; 3],
    pub rotation: [f64; 3],
    pub scale: [f64; 3],
}

/// The game loads at most this many props per cell (MAP_PROP_MAX).
pub const MAX_PROPS: usize = 32;
pub const UNITS_PER_TILE: f64 = 16.0;

pub fn load(path: &Path) -> Result<Vec<Prop>> {
    let raw = read_text(path)?;
    serde_json::from_str(&raw).map_err(|e| Error(format!("{}:{}: {}", path.display(), e.line(), e)))
}
