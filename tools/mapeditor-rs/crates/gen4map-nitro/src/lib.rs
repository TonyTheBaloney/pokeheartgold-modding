// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! NITRO-System files for drawing maps: NARC archives, NSBTX textures and NSBMD
//! models decoded to triangles, and map texture sets kept as PNG folders. A port of
//! tools/mapkit/mapkit/{nitro,landdata,areatex}.py (decoding only); the tests
//! compare it with them.
//!
//! Every read is bounds-checked: a damaged file is an error, never a panic.

pub mod areatex;
pub mod bdhc;
pub mod model;
pub mod narc;
pub mod texture;

use std::fmt;

#[derive(Debug, Clone)]
pub struct Error(pub String);

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for Error {}

pub type Result<T> = std::result::Result<T, Error>;

macro_rules! bail {
    ($($arg:tt)*) => { return Err($crate::Error(format!($($arg)*))) };
}
pub(crate) use bail;

/// fx32 / fx16 one.
pub const FX: f64 = 4096.0;

/// Little-endian reads that fail instead of panicking past the end.
#[derive(Clone, Copy)]
pub struct Bytes<'a>(pub &'a [u8]);

impl<'a> Bytes<'a> {
    pub fn len(&self) -> usize {
        self.0.len()
    }

    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    pub fn slice(&self, o: usize, n: usize) -> Result<&'a [u8]> {
        o.checked_add(n)
            .and_then(|end| self.0.get(o..end))
            .ok_or_else(|| Error(format!("read of {} bytes at {:#x} past the end ({:#x})", n, o, self.0.len())))
    }

    pub fn u8(&self, o: usize) -> Result<u8> {
        Ok(self.slice(o, 1)?[0])
    }

    pub fn u16(&self, o: usize) -> Result<u16> {
        Ok(u16::from_le_bytes(self.slice(o, 2)?.try_into().unwrap()))
    }

    pub fn s16(&self, o: usize) -> Result<i16> {
        Ok(self.u16(o)? as i16)
    }

    pub fn u32(&self, o: usize) -> Result<u32> {
        Ok(u32::from_le_bytes(self.slice(o, 4)?.try_into().unwrap()))
    }

    pub fn s32(&self, o: usize) -> Result<i32> {
        Ok(self.u32(o)? as i32)
    }
}

/// Sign-extend the low `bits` of v.
pub fn sext(v: u32, bits: u32) -> i32 {
    let shift = 32 - bits;
    ((v << shift) as i32) >> shift
}

/// RGB555 -> RGB888 as mapkit does it (c * 255 // 31).
pub fn rgb555(c: u16) -> [u8; 3] {
    let f = |v: u16| ((v & 31) as u32 * 255 / 31) as u8;
    [f(c), f(c >> 5), f(c >> 10)]
}

/// The blocks of a NITRO file with signature `sig`: [(block signature, offset)].
pub fn blocks(d: Bytes, sig: &[u8; 4]) -> Result<Vec<([u8; 4], usize)>> {
    if d.slice(0, 4)? != sig {
        bail!("not a {} file", String::from_utf8_lossy(sig));
    }
    let n = d.u16(14)? as usize;
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let o = d.u32(16 + 4 * i)? as usize;
        out.push((d.slice(o, 4)?.try_into().unwrap(), o));
    }
    Ok(out)
}

pub fn find_block(blocks: &[([u8; 4], usize)], sig: &[u8; 4]) -> Option<usize> {
    blocks.iter().find(|(s, _)| s == sig).map(|&(_, o)| o)
}

/// An NNSG3dResDict at `base`: [(name, offset of the entry's data)] in entry order.
pub fn read_dict(d: Bytes, base: usize) -> Result<Vec<(String, usize)>> {
    let num = d.u8(base + 1)? as usize;
    let hdr = base + d.u16(base + 6)? as usize;
    let size_unit = d.u16(hdr)? as usize;
    let ofs_name = d.u16(hdr + 2)? as usize;
    let mut out = Vec::with_capacity(num);
    for i in 0..num {
        let raw = d.slice(hdr + ofs_name + 16 * i, 16)?;
        let end = raw.iter().position(|&b| b == 0).unwrap_or(16);
        out.push((String::from_utf8_lossy(&raw[..end]).into_owned(), hdr + 4 + size_unit * i));
    }
    Ok(out)
}

/// An RGBA image, row by row.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Image {
    pub width: usize,
    pub height: usize,
    pub rgba: Vec<u8>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn helpers() {
        assert_eq!(sext(0x3FF, 10), -1);
        assert_eq!(sext(0x1FF, 10), 511);
        assert_eq!(rgb555(0x7FFF), [255, 255, 255]);
        assert_eq!(rgb555(1), [8, 0, 0]);
        assert!(Bytes(&[1, 2, 3]).u32(0).is_err());
        assert!(Bytes(&[1, 2, 3]).u16(usize::MAX).is_err());
    }
}
