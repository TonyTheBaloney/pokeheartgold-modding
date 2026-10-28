// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The gen4map text formats (docs/gen4map/FORMAT.md) as this repository keeps them:
//! map.json, layout.json, permissions.txt, props.json, the maps.txt / layouts.txt
//! indexes and the manifest. Readers and writers match tools/mapkit byte for byte,
//! so a file read and written back without edits is unchanged.

pub mod constants;
pub mod ids;
pub mod index;
pub mod json;
pub mod layout;
pub mod manifest;
pub mod permissions;
pub mod project;
pub mod props;

use std::fmt;

/// Tiles per side of a layout cell (land data).
pub const CELL: usize = 32;

#[derive(Debug, Clone)]
pub struct Error(pub String);

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for Error {}

impl From<std::io::Error> for Error {
    fn from(e: std::io::Error) -> Self {
        Error(e.to_string())
    }
}

pub type Result<T> = std::result::Result<T, Error>;

/// `Err(Error(format!(...)))`
#[macro_export]
macro_rules! bail {
    ($($arg:tt)*) => { return Err($crate::Error(format!($($arg)*))) };
}

/// Read a file, naming it in the error.
pub fn read_text(path: &std::path::Path) -> Result<String> {
    std::fs::read_to_string(path).map_err(|e| Error(format!("{}: {}", path.display(), e)))
}

/// Write a file, naming it in the error.
pub fn write_text(path: &std::path::Path, text: &str) -> Result<()> {
    std::fs::write(path, text).map_err(|e| Error(format!("{}: {}", path.display(), e)))
}
