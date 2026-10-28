// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Textures and palettes: a TEX0 block (in an NSBTX or an NSBMD) decoded to RGBA
//! the way mapkit's nitro.Texture.decode does it.
//!
//! Formats: 1 A3I5, 2 4-color, 3 16-color, 4 256-color, 5 4x4-compressed, 6 A5I3,
//! 7 direct. A palette runs from its start to the next palette's (at most 256
//! colors); an index past its end draws magenta.

use std::collections::HashMap;

use crate::{bail, blocks, find_block, read_dict, rgb555, Bytes, Image, Result};

const MAGENTA: [u8; 3] = [255, 0, 255];

#[derive(Debug, Clone)]
pub enum Texels {
    /// One value per texel: the palette index (with the alpha bits for A3I5 / A5I3)
    /// or, for direct textures, the RGB555 color with bit 15 for opacity.
    Values(Vec<u16>),
    /// 4x4-compressed: two bits per texel per 4x4 block, and the block's palette info.
    Compressed { blocks: Vec<u32>, info: Vec<u16> },
    /// Unknown format or data past the end of the file: drawn transparent.
    Invalid(String),
}

#[derive(Debug, Clone)]
pub struct Texture {
    pub name: String,
    pub width: usize,
    pub height: usize,
    pub format: u8,
    pub color0_transparent: bool,
    pub texels: Texels,
}

impl Texture {
    /// Size and format from a TEX0 texImageParam.
    pub fn dims(param: u32) -> (usize, usize, u8) {
        (8 << ((param >> 20) & 7), 8 << ((param >> 23) & 7), ((param >> 26) & 7) as u8)
    }

    fn read(name: &str, param: u32, d: Bytes, data: usize, idx: usize) -> Texture {
        let (w, h, format) = Texture::dims(param);
        let texels = Texture::read_texels(name, w, h, format, d, data, idx).unwrap_or_else(|e| Texels::Invalid(e.0));
        Texture { name: name.into(), width: w, height: h, format, color0_transparent: param >> 29 & 1 != 0, texels }
    }

    fn read_texels(name: &str, w: usize, h: usize, format: u8, d: Bytes, data: usize, idx: usize) -> Result<Texels> {
        let n = w * h;
        Ok(match format {
            1 | 6 | 4 => Texels::Values(d.slice(data, n)?.iter().map(|&b| b as u16).collect()),
            2 | 3 => {
                let bits = if format == 2 { 2 } else { 4 };
                let per = 8 / bits;
                let raw = d.slice(data, n / per)?;
                let mask = (1u16 << bits) - 1;
                Texels::Values((0..n).map(|i| (raw[i / per] as u16 >> ((i % per) * bits)) & mask).collect())
            }
            7 => Texels::Values((0..n).map(|i| d.u16(data + 2 * i)).collect::<Result<_>>()?),
            5 => {
                let nb = (w / 4) * (h / 4);
                Texels::Compressed {
                    blocks: (0..nb).map(|b| d.u32(data + 4 * b)).collect::<Result<_>>()?,
                    info: (0..nb).map(|b| d.u16(idx + 2 * b)).collect::<Result<_>>()?,
                }
            }
            _ => bail!("texture {}: unknown format {}", name, format),
        })
    }

    /// RGBA with a palette (RGB555 values; ignored by direct textures).
    pub fn decode(&self, palette: &[u16]) -> Image {
        let (w, h) = (self.width, self.height);
        let mut out = vec![0u8; w * h * 4];
        let color = |i: usize| palette.get(i).map(|&c| rgb555(c)).unwrap_or(MAGENTA);
        let mut put = |i: usize, rgb: [u8; 3], a: u8| out[i * 4..i * 4 + 4].copy_from_slice(&[rgb[0], rgb[1], rgb[2], a]);
        match &self.texels {
            Texels::Values(values) => {
                for (i, &v) in values.iter().enumerate() {
                    match self.format {
                        1 | 6 => {
                            let ibits = if self.format == 1 { 5 } else { 3 };
                            let (idx, a) = (v & ((1 << ibits) - 1), v >> ibits);
                            let top = (1u16 << (8 - ibits)) - 1;
                            put(i, color(idx as usize), (a as u32 * 255 / top as u32) as u8);
                        }
                        7 => put(i, rgb555(v), if v & 0x8000 != 0 { 255 } else { 0 }),
                        _ => put(i, color(v as usize), if v == 0 && self.color0_transparent { 0 } else { 255 }),
                    }
                }
            }
            Texels::Compressed { blocks, info } => {
                let bw = w / 4;
                for (b, (&texels, &info)) in blocks.iter().zip(info).enumerate() {
                    let base = (info & 0x3FFF) as usize * 2;
                    let c: Vec<[u8; 3]> = (0..4).map(|k| color(base + k)).collect();
                    let mix = |p: u32, q: u32, k: usize| ((p * c[0][k] as u32 + q * c[1][k] as u32) / (p + q)) as u8;
                    let cols: [([u8; 3], u8); 4] = match info >> 14 {
                        0 => [(c[0], 255), (c[1], 255), (c[2], 255), ([0; 3], 0)],
                        1 => [(c[0], 255), (c[1], 255), ([0, 1, 2].map(|k| mix(1, 1, k)), 255), ([0; 3], 0)],
                        2 => [(c[0], 255), (c[1], 255), (c[2], 255), (c[3], 255)],
                        _ => [(c[0], 255), (c[1], 255), ([0, 1, 2].map(|k| mix(5, 3, k)), 255), ([0, 1, 2].map(|k| mix(3, 5, k)), 255)],
                    };
                    let (bx, by) = ((b % bw) * 4, (b / bw) * 4);
                    for t in 0..16 {
                        let (rgb, a) = cols[(texels >> (2 * t)) as usize & 3];
                        put((by + t / 4) * w + bx + t % 4, rgb, a);
                    }
                }
            }
            Texels::Invalid(_) => {}
        }
        Image { width: w, height: h, rgba: out }
    }
}

/// Textures and palettes by name, in file order.
#[derive(Debug, Clone, Default)]
pub struct TextureSet {
    pub textures: Vec<Texture>,
    pub palettes: Vec<(String, Vec<u16>)>,
    tex_index: HashMap<String, usize>,
    pal_index: HashMap<String, usize>,
}

impl TextureSet {
    pub fn new(textures: Vec<Texture>, palettes: Vec<(String, Vec<u16>)>) -> TextureSet {
        // a repeated name finds the last one, as a Python dict built in order does
        let tex_index = textures.iter().enumerate().map(|(i, t)| (t.name.clone(), i)).collect();
        let pal_index = palettes.iter().enumerate().map(|(i, p)| (p.0.clone(), i)).collect();
        TextureSet { textures, palettes, tex_index, pal_index }
    }

    /// The TEX0 block at `base`.
    pub fn read_tex0(d: Bytes, base: usize) -> Result<TextureSet> {
        let tex_ofs = base + d.u32(base + 0x14)? as usize; // texInfo.ofsTex
        let tex_dict = base + d.u16(base + 0x0E)? as usize; // texInfo.ofsDict
        let t4_ofs = base + d.u32(base + 0x24)? as usize; // tex4x4Info.ofsTex
        let t4_idx = base + d.u32(base + 0x28)? as usize; // tex4x4Info.ofsTexPlttIdx
        let pal_dict = base + d.u16(base + 0x34)? as usize; // plttInfo.ofsDict
        let pal_ofs = base + d.u32(base + 0x38)? as usize; // plttInfo.ofsPlttData
        let mut textures = Vec::new();
        for (name, p) in read_dict(d, tex_dict)? {
            let param = d.u32(p)?;
            let off = ((param & 0xFFFF) << 3) as usize;
            textures.push(if (param >> 26) & 7 == 5 {
                Texture::read(&name, param, d, t4_ofs + off, t4_idx + off / 2)
            } else {
                Texture::read(&name, param, d, tex_ofs + off, 0)
            });
        }
        let entries = read_dict(d, pal_dict)?;
        let mut starts: Vec<usize> = entries.iter().map(|&(_, p)| d.u16(p).map(|v| (v as usize) << 3)).collect::<Result<_>>()?;
        starts.sort_unstable();
        starts.dedup();
        let end = base + d.u32(base + 4)? as usize;
        let mut palettes = Vec::new();
        for (name, p) in entries {
            let start = pal_ofs + ((d.u16(p)? as usize) << 3);
            let stop = starts.iter().map(|s| pal_ofs + s).find(|&s| s > start).unwrap_or(end);
            let count = (stop.saturating_sub(start) / 2).min(256);
            palettes.push((name, (0..count).map(|i| d.u16(start + 2 * i)).collect::<Result<_>>()?));
        }
        Ok(TextureSet::new(textures, palettes))
    }

    /// An NSBTX file.
    pub fn read_nsbtx(data: &[u8]) -> Result<TextureSet> {
        let d = Bytes(data);
        match find_block(&blocks(d, b"BTX0")?, b"TEX0") {
            Some(o) => TextureSet::read_tex0(d, o),
            None => bail!("NSBTX without TEX0"),
        }
    }

    pub fn texture(&self, name: &str) -> Option<&Texture> {
        self.tex_index.get(name).map(|&i| &self.textures[i])
    }

    pub fn palette(&self, name: &str) -> Option<&[u16]> {
        self.pal_index.get(name).map(|&i| self.palettes[i].1.as_slice())
    }

    /// A texture drawn with a palette (none: every index draws magenta).
    pub fn image(&self, texture: &str, palette: Option<&str>) -> Option<Image> {
        let t = self.texture(texture)?;
        Some(t.decode(palette.and_then(|p| self.palette(p)).unwrap_or(&[])))
    }
}
