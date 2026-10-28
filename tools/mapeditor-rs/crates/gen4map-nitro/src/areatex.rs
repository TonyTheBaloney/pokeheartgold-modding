// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Map texture sets kept as folders (gen4map 1.2, docs/modding/area-textures.md):
//!
//! ```text
//! data/area_textures/NNN/
//!     textures.json          {"textures": [{"name", "format", "transparent"?, "palette"?}], "palettes": [{"name", "four_color"?}]}
//!     textures/<name>.png    indexed; a pixel's value is the texel's value
//!     palettes/<name>.pal    JASC
//! ```
//!
//! Read straight into a TextureSet, with palettes laid out as mapkit's NSBTX writer
//! lays them out (each padded to 16 bytes, identical ones shared), so a palette
//! reaches as far as it does in the built file and colors decode identically.

use std::collections::HashMap;
use std::path::Path;

use serde::Deserialize;

use crate::texture::{Texels, Texture, TextureSet};
use crate::{bail, Error, Result};

#[derive(Deserialize)]
struct Doc {
    textures: Vec<TexEntry>,
    palettes: Vec<PalEntry>,
}

#[derive(Deserialize)]
struct TexEntry {
    name: String,
    format: String,
    #[serde(default)]
    transparent: bool,
}

#[derive(Deserialize)]
struct PalEntry {
    name: String,
}

fn format_id(name: &str) -> Option<u8> {
    Some(match name {
        "a3i5" => 1,
        "palette4" => 2,
        "palette16" => 3,
        "palette256" => 4,
        "a5i3" => 6,
        _ => return None,
    })
}

/// A JASC palette as RGB555 values.
pub fn read_pal(path: &Path) -> Result<Vec<u16>> {
    let text = std::fs::read_to_string(path).map_err(|e| Error(format!("{}: {}", path.display(), e)))?;
    let toks: Vec<&str> = text.split_whitespace().collect();
    if toks.len() < 3 || toks[0] != "JASC-PAL" || toks[1] != "0100" {
        bail!("{} is not a JASC palette", path.display());
    }
    let n: usize = toks[2].parse().map_err(|_| Error(format!("{}: bad color count", path.display())))?;
    let vals: Vec<u16> = toks[3..].iter().take(3 * n).filter_map(|v| v.parse().ok()).filter(|&v| v <= 255).collect();
    if vals.len() != 3 * n {
        bail!("{}: expected {} colors of 0-255 values", path.display(), n);
    }
    Ok(vals.chunks(3).map(|c| (c[0] >> 3) | (c[1] >> 3) << 5 | (c[2] >> 3) << 10).collect())
}

/// An indexed PNG: (width, height, one value per pixel).
pub fn read_indexed_png(path: &Path) -> Result<(usize, usize, Vec<u8>)> {
    let err = |e: &dyn std::fmt::Display| Error(format!("{}: {}", path.display(), e));
    let file = std::fs::File::open(path).map_err(|e| err(&e))?;
    let mut dec = png::Decoder::new(std::io::BufReader::new(file));
    dec.set_transformations(png::Transformations::IDENTITY);
    let mut reader = dec.read_info().map_err(|e| err(&e))?;
    let info = reader.info();
    if info.color_type != png::ColorType::Indexed {
        bail!("{}: save it as an indexed PNG (the pixel values are the texture's)", path.display());
    }
    let (w, h, bits) = (info.width as usize, info.height as usize, info.bit_depth as usize);
    let mut buf = vec![0; reader.output_buffer_size().ok_or_else(|| err(&"image too large"))?];
    let frame = reader.next_frame(&mut buf).map_err(|e| err(&e))?;
    let mut out = Vec::with_capacity(w * h);
    for y in 0..h {
        let row = &buf[y * frame.line_size..(y + 1) * frame.line_size];
        for x in 0..w {
            let bit = x * bits;
            let v = row[bit / 8] >> (8 - bits - bit % 8) & ((1u16 << bits) - 1) as u8;
            out.push(v);
        }
    }
    Ok((w, h, out))
}

/// A set folder as a TextureSet.
pub fn read_set(dir: &Path) -> Result<TextureSet> {
    let doc_path = dir.join("textures.json");
    let raw = std::fs::read_to_string(&doc_path).map_err(|e| Error(format!("{}: {}", doc_path.display(), e)))?;
    let doc: Doc = serde_json::from_str(&raw).map_err(|e| Error(format!("{}: {}", doc_path.display(), e)))?;
    let mut textures = Vec::new();
    for t in &doc.textures {
        let path = dir.join("textures").join(format!("{}.png", t.name));
        let Some(format) = format_id(&t.format) else {
            bail!("{}: format {:?} (palette4, palette16, palette256, a3i5 or a5i3)", path.display(), t.format)
        };
        let (w, h, values) = read_indexed_png(&path)?;
        textures.push(Texture {
            name: t.name.clone(),
            width: w,
            height: h,
            format,
            color0_transparent: t.transparent,
            texels: Texels::Values(values.into_iter().map(u16::from).collect()),
        });
    }
    // the palette block as nsbtx.write builds it
    let mut block: Vec<u16> = Vec::new();
    let mut shared: HashMap<Vec<u16>, usize> = HashMap::new();
    let mut starts = Vec::new();
    for p in &doc.palettes {
        let mut colors = read_pal(&dir.join("palettes").join(format!("{}.pal", p.name)))?;
        colors.resize(colors.len().div_ceil(8) * 8, 0);
        let at = *shared.entry(colors.clone()).or_insert_with(|| {
            block.extend(&colors);
            block.len() - colors.len()
        });
        starts.push(at);
    }
    let mut sorted = starts.clone();
    sorted.sort_unstable();
    sorted.dedup();
    let palettes = doc
        .palettes
        .iter()
        .zip(&starts)
        .map(|(p, &start)| {
            let stop = sorted.iter().copied().find(|&s| s > start).unwrap_or(block.len());
            (p.name.clone(), block[start..stop.min(start + 256)].to_vec())
        })
        .collect();
    Ok(TextureSet::new(textures, palettes))
}

#[cfg(test)]
mod tests {
    #[test]
    fn png_bits() {
        // 2-bit row 0b00_01_10_11 -> 0, 1, 2, 3
        let byte = 0b0001_1011u8;
        let vals: Vec<u8> = (0..4).map(|x| byte >> (8 - 2 - (x * 2) % 8) & 3).collect();
        assert_eq!(vals, [0, 1, 2, 3]);
    }
}
