// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! permissions.txt: a cell's collision, behavior and attribute grids
//! (tools/mapkit/mapkit/landdata.py Permissions). The game's permission word is
//! `behavior | attr << 8 | collision << 15`.

use crate::{bail, Result, CELL};

const N: usize = CELL * CELL;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Permissions {
    pub collision: Vec<u8>, // 0 or 1
    pub behavior: Vec<u8>,
    pub attr: Vec<u8>, // 0-0x7F
}

impl Default for Permissions {
    fn default() -> Self {
        Permissions { collision: vec![0; N], behavior: vec![0; N], attr: vec![0; N] }
    }
}

/// (collision, behavior, attr) of one tile.
pub type Tile = (u8, u8, u8);

impl Permissions {
    pub fn tile(&self, x: usize, y: usize) -> Tile {
        let i = y * CELL + x;
        (self.collision[i], self.behavior[i], self.attr[i])
    }

    pub fn set_tile(&mut self, x: usize, y: usize, t: Tile) {
        let i = y * CELL + x;
        self.collision[i] = (t.0 != 0) as u8;
        self.behavior[i] = t.1;
        self.attr[i] = t.2 & 0x7F;
    }

    pub fn words(&self) -> Vec<u16> {
        (0..N).map(|i| self.behavior[i] as u16 | (self.attr[i] as u16) << 8 | (self.collision[i] as u16) << 15).collect()
    }

    pub fn from_words(words: &[u16]) -> Permissions {
        Permissions {
            collision: words.iter().map(|w| (w >> 15 & 1) as u8).collect(),
            behavior: words.iter().map(|w| (w & 0xFF) as u8).collect(),
            attr: words.iter().map(|w| (w >> 8 & 0x7F) as u8).collect(),
        }
    }

    pub fn to_text(&self) -> String {
        let hex_grid = |v: &[u8], out: &mut String| {
            for y in 0..CELL {
                let row: Vec<String> = (0..CELL).map(|x| format!("{:02X}", v[y * CELL + x])).collect();
                out.push_str(&row.join(" "));
                out.push('\n');
            }
        };
        let mut out = String::from("[collision]  # blocks movement, . is open\n");
        for y in 0..CELL {
            out.extend((0..CELL).map(|x| if self.collision[y * CELL + x] != 0 { '#' } else { '.' }));
            out.push('\n');
        }
        out.push_str("[behavior]  TILE_BEHAVIOR_* value in hex (include/constants/metatile_behavior.h)\n");
        hex_grid(&self.behavior, &mut out);
        if self.attr.iter().any(|&a| a != 0) {
            out.push_str("[attr]  bits 8-14 of the permission word, hex (FieldSystem_GetTileAttrBits8To14)\n");
            hex_grid(&self.attr, &mut out);
        }
        out
    }

    pub fn from_text(text: &str, wh: &str) -> Result<Permissions> {
        let mut sections: Vec<(String, Vec<(usize, &str)>)> = Vec::new();
        for (n, line) in text.lines().enumerate() {
            let n = n + 1;
            let line = line.strip_suffix('\r').unwrap_or(line);
            if let Some(rest) = line.strip_prefix('[') {
                let name = rest.split(']').next().unwrap_or("").trim();
                if !matches!(name, "collision" | "behavior" | "attr") {
                    bail!("{}:{}: unknown section {:?}", wh, n, name);
                }
                sections.retain(|(s, _)| s != name);
                sections.push((name.to_string(), Vec::new()));
            } else if !line.trim().is_empty() {
                match sections.last_mut() {
                    Some((_, rows)) => rows.push((n, line.trim())),
                    None => bail!("{}:{}: grid before a [section] line", wh, n),
                }
            }
        }
        for name in ["collision", "behavior"] {
            if !sections.iter().any(|(s, _)| s == name) {
                bail!("{}: missing [{}] section", wh, name);
            }
        }
        let mut p = Permissions::default();
        for (name, rows) in &sections {
            if rows.len() != CELL {
                bail!("{}: {} has {} rows, not {}", wh, name, rows.len(), CELL);
            }
            let mut values = Vec::with_capacity(N);
            for &(n, row) in rows {
                if name == "collision" {
                    if row.chars().count() != CELL || row.chars().any(|c| c != '#' && c != '.') {
                        bail!("{}:{}: expected {} of # or .", wh, n, CELL);
                    }
                    values.extend(row.chars().map(|c| (c == '#') as u8));
                } else {
                    let toks: Vec<&str> = row.split_whitespace().collect();
                    if toks.len() != CELL {
                        bail!("{}:{}: expected {} hex values, got {}", wh, n, CELL, toks.len());
                    }
                    let limit = if name == "behavior" { 0xFF } else { 0x7F };
                    for t in toks {
                        let v = u32::from_str_radix(t, 16).map_err(|_| crate::Error(format!("{}:{}: not hex", wh, n)))?;
                        if v > limit {
                            bail!("{}:{}: {} values go up to {:02X}", wh, n, name, limit);
                        }
                        values.push(v as u8);
                    }
                }
            }
            match name.as_str() {
                "collision" => p.collision = values,
                "behavior" => p.behavior = values,
                _ => p.attr = values,
            }
        }
        Ok(p)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trip() {
        let mut p = Permissions::default();
        p.set_tile(3, 4, (1, 0x21, 0));
        let q = Permissions::from_text(&p.to_text(), "t").unwrap();
        assert_eq!(p, q);
        assert!(!p.to_text().contains("[attr]"));
        p.set_tile(0, 0, (0, 0, 5));
        assert!(p.to_text().contains("[attr]"));
        assert_eq!(Permissions::from_words(&p.words()), p);
    }
}
