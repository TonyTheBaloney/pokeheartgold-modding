// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! JSON files written the way mapkit writes them (tools/mapkit/mapkit/edit.py
//! load_json / save_json): Python's `json.dumps(indent=N, ensure_ascii=False)`, keys
//! in file order, keeping the file's indentation, final newline and line endings.

use std::path::Path;

use serde::Serialize;
use serde_json::ser::PrettyFormatter;
use serde_json::Value;

use crate::{read_text, write_text, Error, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Style {
    pub indent: usize,
    pub newline: bool,
    pub crlf: bool,
}

impl Default for Style {
    fn default() -> Self {
        Style { indent: 4, newline: true, crlf: false }
    }
}

impl Style {
    /// The style of a file's text: the indentation of its first key (4 if it has none).
    pub fn of(raw: &str) -> Style {
        let rest = raw.strip_prefix('{').and_then(|r| r.strip_prefix("\r\n").or_else(|| r.strip_prefix('\n')));
        let indent = rest.map(|r| r.len() - r.trim_start_matches(' ').len()).filter(|&n| n > 0).unwrap_or(4);
        Style { indent, newline: raw.ends_with('\n'), crlf: raw.contains("\r\n") }
    }
}

pub fn parse(raw: &str, path: &Path) -> Result<Value> {
    serde_json::from_str(raw).map_err(|e| Error(format!("{}:{}: {}", path.display(), e.line(), e)))
}

pub fn load(path: &Path) -> Result<(Value, Style)> {
    let raw = read_text(path)?;
    Ok((parse(&raw, path)?, Style::of(&raw)))
}

/// Python's json.dumps with `indent` and ensure_ascii=False: serde_json's pretty
/// layout is the same (": ", one value per line, [] and {} when empty, the same
/// escapes). Only floats could differ (Python 1e-05, Rust 1e-5); map.json has none.
pub fn to_string(value: &Value, style: Style) -> String {
    let indent = vec![b' '; style.indent];
    let mut out = Vec::new();
    let mut ser = serde_json::Serializer::with_formatter(&mut out, PrettyFormatter::with_indent(&indent));
    value.serialize(&mut ser).expect("serializing a Value can't fail");
    let mut text = String::from_utf8(out).expect("serde_json writes UTF-8");
    if style.newline {
        text.push('\n');
    }
    if style.crlf {
        text = text.replace('\n', "\r\n");
    }
    text
}

pub fn save(path: &Path, value: &Value, style: Style) -> Result<()> {
    write_text(path, &to_string(value, style))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn python_layout() {
        let v: Value = serde_json::from_str(r#"{"a": 1, "b": [], "c": {}, "d": [1, "é\u001f"], "e": true}"#).unwrap();
        assert_eq!(
            to_string(&v, Style::default()),
            "{\n    \"a\": 1,\n    \"b\": [],\n    \"c\": {},\n    \"d\": [\n        1,\n        \"é\\u001f\"\n    ],\n    \"e\": true\n}\n"
        );
    }

    #[test]
    fn style_detection() {
        assert_eq!(Style::of("{\r\n  \"a\": 1\r\n}"), Style { indent: 2, newline: false, crlf: true });
        assert_eq!(Style::of("{}\n"), Style { indent: 4, newline: true, crlf: false });
    }
}
