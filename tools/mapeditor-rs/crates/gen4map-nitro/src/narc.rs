// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! NARC archives: BTAF (member offsets), BTNF (names, unused here), GMIF (data).
//! Members are addressed by index (BINARY.md §1).

use std::path::Path;

use crate::{bail, Bytes, Error, Result};

pub struct Narc {
    data: Vec<u8>,
    members: Vec<(usize, usize)>,
}

impl Narc {
    pub fn parse(data: Vec<u8>) -> Result<Narc> {
        let d = Bytes(&data);
        if d.slice(0, 4)? != b"NARC" {
            bail!("not a NARC");
        }
        let (mut fat, mut img) = (None, None);
        let mut off = d.u16(12)? as usize;
        while off < d.len() {
            let sig = d.slice(off, 4)?;
            let size = d.u32(off + 4)? as usize;
            match sig {
                b"BTAF" => fat = Some(off),
                b"GMIF" => img = Some(off + 8),
                _ => {}
            }
            if size == 0 {
                bail!("NARC block of size 0 at {:#x}", off);
            }
            off += size;
        }
        let (Some(fat), Some(img)) = (fat, img) else { bail!("NARC without BTAF or GMIF") };
        let n = d.u16(fat + 8)? as usize;
        let mut members = Vec::with_capacity(n);
        for i in 0..n {
            let (s, e) = (d.u32(fat + 12 + 8 * i)? as usize, d.u32(fat + 16 + 8 * i)? as usize);
            if s > e || img + e > d.len() {
                bail!("NARC member {} ({:#x}-{:#x}) outside the file", i, s, e);
            }
            members.push((img + s, img + e));
        }
        Ok(Narc { data, members })
    }

    pub fn open(path: &Path) -> Result<Narc> {
        let data = std::fs::read(path).map_err(|e| Error(format!("{}: {}", path.display(), e)))?;
        Narc::parse(data).map_err(|e| Error(format!("{}: {}", path.display(), e)))
    }

    pub fn len(&self) -> usize {
        self.members.len()
    }

    pub fn is_empty(&self) -> bool {
        self.members.is_empty()
    }

    pub fn get(&self, i: usize) -> Option<&[u8]> {
        self.members.get(i).map(|&(s, e)| &self.data[s..e])
    }
}
