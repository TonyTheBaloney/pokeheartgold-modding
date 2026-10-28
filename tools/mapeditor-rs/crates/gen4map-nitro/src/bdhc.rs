// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! BDHC: the heights the player and NPCs walk on, one file per terrain cell (read by
//! src/field/bdhc.c, queried from src/field_terrain.c). A port of the reader and the
//! game's lookup in tools/mapkit/mapkit/bdhc.py: fixed-point math as the NitroSDK does
//! it, the strip search with its off-by-one, at most 10 candidate plates.
//!
//! Values are fx32 model units (one tile = 16 * 4096) relative to the cell's centre.

use crate::{bail, Bytes, Result};

pub const FX: i64 = 4096;
pub const MAX_CANDIDATES: usize = 10;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Nearest,
    Highest,
    Lowest,
}

/// FX_MulInline: (a * b + 0x800) >> 12.
fn fx_mul(a: i64, b: i64) -> i64 {
    (a * b + 0x800) >> 12
}

/// FX_Div: the hardware divides (n << 32) by d (signed, truncating), then rounds to fx32.
fn fx_div(n: i64, d: i64) -> Option<i64> {
    if d == 0 {
        return None;
    }
    let q = ((n as i128).abs() << 32) / (d as i128).abs();
    let q = if (n < 0) != (d < 0) { -q } else { q };
    Some(((q + (1 << 19)) >> 20) as i64)
}

#[derive(Debug, Clone, Default)]
pub struct Bdhc {
    pub points: Vec<(i32, i32)>,
    pub normals: Vec<(i32, i32, i32)>,
    pub constants: Vec<i32>,
    pub plates: Vec<[u16; 4]>,
    pub strips: Vec<(i32, u16, u16)>,
    pub access: Vec<u16>,
}

impl Bdhc {
    pub fn read(data: &[u8]) -> Result<Bdhc> {
        let d = Bytes(data);
        if d.slice(0, 4)? != b"BDHC" {
            bail!("not a BDHC file");
        }
        let n: Vec<usize> = (0..6).map(|i| d.u16(4 + 2 * i).map(usize::from)).collect::<Result<_>>()?;
        let mut o = 16;
        let mut b = Bdhc::default();
        for _ in 0..n[0] {
            b.points.push((d.s32(o)?, d.s32(o + 4)?));
            o += 8;
        }
        for _ in 0..n[1] {
            b.normals.push((d.s32(o)?, d.s32(o + 4)?, d.s32(o + 8)?));
            o += 12;
        }
        for _ in 0..n[2] {
            b.constants.push(d.s32(o)?);
            o += 4;
        }
        for _ in 0..n[3] {
            b.plates.push([d.u16(o)?, d.u16(o + 2)?, d.u16(o + 4)?, d.u16(o + 6)?]);
            o += 8;
        }
        for _ in 0..n[4] {
            b.strips.push((d.s32(o)?, d.u16(o + 4)?, d.u16(o + 6)?));
            o += 8;
        }
        for _ in 0..n[5] {
            b.access.push(d.u16(o)?);
            o += 2;
        }
        if o != data.len() {
            bail!("BDHC is {} bytes but its arrays end at {}", data.len(), o);
        }
        Ok(b)
    }

    /// Bdhc_FindStrip, including its off-by-one search: index or None.
    fn find_strip(&self, z: i64) -> Option<usize> {
        let mut count = self.strips.len();
        match count {
            0 => return None,
            1 => return Some(0),
            _ => {}
        }
        count -= 1;
        let (mut lo, mut mid) = (0usize, count / 2);
        loop {
            if self.strips.get(mid)?.0 as i64 > z {
                count = count.checked_sub(1)?;
                if count > lo {
                    count = mid;
                    mid = (lo + count) / 2;
                } else {
                    return Some(mid);
                }
            } else {
                lo += 1;
                if lo < count {
                    lo = mid;
                    mid = (lo + count) / 2;
                } else {
                    return Some(mid + 1);
                }
            }
        }
    }

    /// fx32 height at fx32 (x, z) as the game computes it, or None. Damaged indexes
    /// give None rather than a panic.
    pub fn height(&self, x: i64, z: i64, mode: Mode, current_y: i64) -> Option<i64> {
        let &(_, count, offset) = self.strips.get(self.find_strip(z)?)?;
        let mut cands = Vec::new();
        for i in 0..count as usize {
            let [a, b, n, c] = *self.plates.get(*self.access.get(offset as usize + i)? as usize)?;
            let ((x0, z0), (x1, z1)) = (*self.points.get(a as usize)?, *self.points.get(b as usize)?);
            let (x0, z0, x1, z1) = (x0 as i64, z0 as i64, x1 as i64, z1 as i64);
            if x0.min(x1) <= x && x <= x0.max(x1) && z0.min(z1) <= z && z <= z0.max(z1) {
                let (nx, ny, nz) = *self.normals.get(n as usize)?;
                let d = *self.constants.get(c as usize)? as i64;
                // a vertical plate (ny = 0) is the DS divider's division by zero: skipped
                if let Some(y) = fx_div(-(d + (fx_mul(nx as i64, x) + fx_mul(nz as i64, z))), ny as i64) {
                    cands.push(y);
                    if cands.len() >= MAX_CANDIDATES {
                        break;
                    }
                }
            }
        }
        match mode {
            Mode::Highest => cands.into_iter().max(),
            Mode::Lowest => cands.into_iter().min(),
            Mode::Nearest => {
                let mut best = *cands.first()?;
                for &y in &cands[1..] {
                    if (current_y - y).abs() < (current_y - best).abs() {
                        best = y;
                    }
                }
                Some(best)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixed_point() {
        assert_eq!(fx_mul(FX, 3 * FX), 3 * FX);
        assert_eq!(fx_div(-8 * FX, FX), Some(-8 * FX));
        assert_eq!(fx_div(FX, 3 * FX), Some(1365));
        assert_eq!(fx_div(1, 0), None);
    }
}
