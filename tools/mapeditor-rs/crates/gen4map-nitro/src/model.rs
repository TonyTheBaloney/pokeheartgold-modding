// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! NSBMD models: run the structure byte code (SBC) and the shapes' display lists
//! (DS geometry engine commands) to get triangles in model units (fx32 / 4096).
//! A port of mapkit's nitro.Model; matrices follow GX: row vectors, v' = v * M,
//! MULT / TRANS / SCALE pre-multiply.

use std::collections::HashMap;
use std::sync::Arc;

use crate::texture::TextureSet;
use crate::{bail, blocks, find_block, read_dict, rgb555, sext, Bytes, Result, FX};

pub type Mat = [f64; 16];

pub const IDENTITY: Mat = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.];

pub fn mat_mul(a: &Mat, b: &Mat) -> Mat {
    let mut out = [0.0; 16];
    for r in 0..4 {
        for c in 0..4 {
            out[r * 4 + c] = (0..4).map(|k| a[r * 4 + k] * b[k * 4 + c]).sum();
        }
    }
    out
}

pub fn mat_from_3x3(m: &[f64], t: [f64; 3]) -> Mat {
    [m[0], m[1], m[2], 0., m[3], m[4], m[5], 0., m[6], m[7], m[8], 0., t[0], t[1], t[2], 1.]
}

pub fn mat_scale(s: [f64; 3]) -> Mat {
    [s[0], 0., 0., 0., 0., s[1], 0., 0., 0., 0., s[2], 0., 0., 0., 0., 1.]
}

pub fn mat_trans(t: [f64; 3]) -> Mat {
    [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., t[0], t[1], t[2], 1.]
}

pub fn transform(m: &Mat, v: [f64; 3]) -> [f64; 3] {
    let [x, y, z] = v;
    [
        x * m[0] + y * m[4] + z * m[8] + m[12],
        x * m[1] + y * m[5] + z * m[9] + m[13],
        x * m[2] + y * m[6] + z * m[10] + m[14],
    ]
}

/// Euler degrees (x, y, z) -> rotation, for props (MapPropArcData.rotation).
pub fn rotation_xyz(deg: [f64; 3]) -> Mat {
    let [rx, ry, rz] = deg.map(f64::to_radians);
    let (cx, sx, cy, sy, cz, sz) = (rx.cos(), rx.sin(), ry.cos(), ry.sin(), rz.cos(), rz.sin());
    let mx = mat_from_3x3(&[1., 0., 0., 0., cx, sx, 0., -sx, cx], [0.; 3]);
    let my = mat_from_3x3(&[cy, 0., -sy, 0., 1., 0., sy, 0., cy], [0.; 3]);
    let mz = mat_from_3x3(&[cz, sz, 0., -sz, cz, 0., 0., 0., 1.], [0.; 3]);
    mat_mul(&mx, &mat_mul(&my, &mz))
}

#[derive(Debug, Clone)]
pub struct Material {
    pub name: String,
    pub diff_amb: u32,
    pub poly_attr: u32,
    pub tex_param: u32,
    pub texture: Option<String>,
    pub palette: Option<String>,
}

impl Material {
    fn read(name: String, d: Bytes, o: usize) -> Result<Material> {
        Ok(Material {
            name,
            diff_amb: d.u32(o + 4)?,
            poly_attr: d.u32(o + 12)?,
            tex_param: d.u32(o + 20)?,
            texture: None,
            palette: None,
        })
    }

    /// Polygon alpha 0-31 (0 draws as wireframe on the DS).
    pub fn alpha(&self) -> u32 {
        (self.poly_attr >> 16) & 31
    }

    /// Texture mirrored on repeat, (s, t).
    pub fn flip(&self) -> (bool, bool) {
        (self.tex_param >> 18 & 1 != 0, self.tex_param >> 19 & 1 != 0)
    }

    pub fn repeat(&self) -> (bool, bool) {
        (self.tex_param >> 16 & 1 != 0, self.tex_param >> 17 & 1 != 0)
    }

    pub fn diffuse(&self) -> [u8; 3] {
        rgb555((self.diff_amb & 0x7FFF) as u16)
    }

    /// Back faces drawn (bit 6) / front faces drawn (bit 7) of the polygon attributes.
    pub fn sides(&self) -> (bool, bool) {
        (self.poly_attr >> 6 & 1 != 0, self.poly_attr >> 7 & 1 != 0)
    }
}

#[derive(Debug, Clone, Copy)]
pub struct Vertex {
    pub pos: [f64; 3],
    /// Texels (12.4 fixed point decoded).
    pub uv: [f64; 2],
    pub color: [u8; 3],
    pub normal: Option<[f64; 3]>,
}

/// A triangle or quad as the display list drew it.
#[derive(Debug, Clone)]
pub struct Polygon {
    pub verts: Vec<Vertex>,
    pub material: Option<Arc<Material>>,
}

#[derive(Debug, Clone)]
pub struct Triangle {
    pub v: [Vertex; 3],
    pub material: Option<Arc<Material>>,
}

impl Polygon {
    pub fn triangles(&self) -> Vec<Triangle> {
        let idx: &[[usize; 3]] = if self.verts.len() == 3 { &[[0, 1, 2]] } else { &[[0, 1, 2], [0, 2, 3]] };
        idx.iter().map(|t| Triangle { v: t.map(|i| self.verts[i]), material: self.material.clone() }).collect()
    }
}

const PIVOT_UTIL: [[usize; 4]; 9] = [
    [4, 5, 7, 8], [3, 5, 6, 8], [3, 4, 6, 7], [1, 2, 7, 8], [0, 2, 6, 8],
    [0, 1, 6, 7], [1, 2, 4, 5], [0, 2, 3, 5], [0, 1, 3, 4],
];

fn sbc_len(cmd: u8) -> Option<usize> {
    Some(match cmd {
        0x00 | 0x01 | 0x0B => 1,
        0x03 | 0x04 | 0x05 | 0x07 | 0x08 => 2,
        0x02 | 0x0C | 0x0D => 3,
        0x06 => 4,
        0x0A => 9,
        _ => return None,
    })
}

fn gx_params(cmd: u8) -> Option<usize> {
    Some(match cmd {
        0x00 | 0x11 | 0x15 | 0x41 => 0,
        0x10 | 0x12 | 0x13 | 0x14 | 0x20 | 0x21 | 0x22 | 0x24..=0x2B | 0x30..=0x33 | 0x40 | 0x50 | 0x60 | 0x72 => 1,
        0x23 | 0x71 => 2,
        0x1B | 0x1C | 0x70 => 3,
        0x1A => 9,
        0x17 | 0x19 => 12,
        0x16 | 0x18 => 16,
        0x34 => 32,
        _ => return None,
    })
}

pub struct Model<'a> {
    pub name: String,
    d: Bytes<'a>,
    evp: usize,
    pos_scale: f64,
    inv_pos_scale: f64,
    nodes: Vec<usize>,
    pub materials: Vec<Arc<Material>>,
    shapes: Vec<(usize, usize)>, // display list offset, size
    sbc: usize,
    sbc_end: usize,
}

impl<'a> Model<'a> {
    fn read(name: String, d: Bytes<'a>, o: usize) -> Result<Model<'a>> {
        let (ofs_sbc, ofs_mat, ofs_shp) = (d.u32(o + 4)? as usize, d.u32(o + 8)? as usize, d.u32(o + 12)? as usize);
        let evp = o + d.u32(o + 16)? as usize;
        let info = o + 20;
        let pos_scale = d.s32(info + 8)? as f64 / FX;
        let inv_pos_scale = d.s32(info + 12)? as f64 / FX;
        let node_info = o + 20 + 0x2C; // NNSG3dResMdlInfo is 0x2C bytes
        let nodes = read_dict(d, node_info)?.into_iter().map(|(_, p)| Ok(node_info + d.u32(p)? as usize)).collect::<Result<_>>()?;
        let mat_base = o + ofs_mat;
        let mut materials = Vec::new();
        for (n, p) in read_dict(d, mat_base + 4)? {
            materials.push(Material::read(n, d, mat_base + d.u32(p)? as usize)?);
        }
        for (dict_ofs, is_tex) in [(d.u16(mat_base)?, true), (d.u16(mat_base + 2)?, false)] {
            for (name, p) in read_dict(d, mat_base + dict_ofs as usize)? {
                let (lst, num) = (mat_base + d.u16(p)? as usize, d.u8(p + 2)? as usize);
                for j in 0..num {
                    if let Some(m) = materials.get_mut(d.u8(lst + j)? as usize) {
                        *(if is_tex { &mut m.texture } else { &mut m.palette }) = Some(name.clone());
                    }
                }
            }
        }
        let shp_base = o + ofs_shp;
        let mut shapes = Vec::new();
        for (_, p) in read_dict(d, shp_base)? {
            let s = shp_base + d.u32(p)? as usize;
            shapes.push((s + d.u32(s + 8)? as usize, d.u32(s + 12)? as usize));
        }
        Ok(Model {
            name,
            d,
            evp,
            pos_scale,
            inv_pos_scale,
            nodes,
            materials: materials.into_iter().map(Arc::new).collect(),
            shapes,
            sbc: o + ofs_sbc,
            sbc_end: o + ofs_mat,
        })
    }

    /// invM of a node's envelope matrix (sbc.c NNSi_G3dFuncSbc_NODEMIX).
    fn inv_bind(&self, node: usize) -> Result<Mat> {
        let o = self.evp + node * (12 + 9) * 4;
        let v: Vec<f64> = (0..12).map(|i| Ok(self.d.s32(o + 4 * i)? as f64 / FX)).collect::<Result<_>>()?;
        Ok(mat_from_3x3(&v[0..9], [v[9], v[10], v[11]]))
    }

    fn node_matrix(&self, idx: usize) -> Result<Mat> {
        let d = self.d;
        let o = self.nodes[idx];
        let (flag, a00) = (d.u16(o)?, d.s16(o + 2)?);
        let mut p = o + 4;
        let fx3 = |p: usize| -> Result<[f64; 3]> {
            Ok([d.s32(p)? as f64 / FX, d.s32(p + 4)? as f64 / FX, d.s32(p + 8)? as f64 / FX])
        };
        let mut t = [0.0; 3];
        if flag & 0x1 == 0 {
            t = fx3(p)?;
            p += 12;
        }
        let mut rot = [1., 0., 0., 0., 1., 0., 0., 0., 1.];
        if flag & 0x2 == 0 {
            if flag & 0x8 != 0 {
                let (a, b) = (d.s16(p)? as f64 / FX, d.s16(p + 2)? as f64 / FX);
                let piv = ((flag >> 4) & 0xF) as usize;
                let Some(u) = PIVOT_UTIL.get(piv) else { bail!("{}: node {} pivot {}", self.name, idx, piv) };
                rot = [0.0; 9];
                rot[piv] = if flag & 0x100 != 0 { -1.0 } else { 1.0 };
                rot[u[0]] = a;
                rot[u[1]] = b;
                rot[u[2]] = if flag & 0x200 != 0 { -b } else { b };
                rot[u[3]] = if flag & 0x400 != 0 { -a } else { a };
                p += 4;
            } else {
                rot[0] = a00 as f64 / FX;
                for i in 0..8 {
                    rot[i + 1] = d.s16(p + 2 * i)? as f64 / FX;
                }
                p += 16;
            }
        }
        let mut m = mat_from_3x3(&rot, t);
        if flag & 0x4 == 0 {
            m = mat_mul(&mat_scale(fx3(p)?), &m);
        }
        Ok(m)
    }

    pub fn triangles(&self) -> Result<Vec<Triangle>> {
        Ok(self.polygons()?.iter().flat_map(Polygon::triangles).collect())
    }

    /// Run the structure byte code and every shape's display list (quads kept).
    pub fn polygons(&self) -> Result<Vec<Polygon>> {
        let d = self.d;
        let mut out = Vec::new();
        let mut cur = IDENTITY;
        let mut stack: HashMap<u8, Mat> = HashMap::new();
        let mut material: Option<Arc<Material>> = None;
        let mut c = self.sbc;
        while c < self.sbc_end {
            let op = d.u8(c)?;
            let (cmd, opt) = (op & 0x1F, op & 0xE0);
            if cmd == 0x01 {
                break; // RET
            }
            if cmd == 0x09 {
                // NODEMIX dest, n, n * (src, node, ratio): weighted invM[node] * stack[src]
                let n = d.u8(c + 2)? as usize;
                let mut acc = [0.0; 16];
                for k in 0..n {
                    let e = d.slice(c + 3 + 3 * k, 3)?;
                    let x = mat_mul(&self.inv_bind(e[1] as usize)?, stack.get(&e[0]).unwrap_or(&IDENTITY));
                    let w = e[2] as f64 / 256.0;
                    for (a, v) in acc.iter_mut().zip(x) {
                        *a += w * v;
                    }
                }
                (acc[3], acc[7], acc[11], acc[15]) = (0.0, 0.0, 0.0, 1.0);
                cur = acc;
                stack.insert(d.u8(c + 1)?, cur);
                c += 3 + 3 * n;
                continue;
            }
            let Some(mut length) = sbc_len(cmd) else { bail!("{}: unknown SBC command {:02X}", self.name, op) };
            match cmd {
                0x03 => cur = stack.get(&d.u8(c + 1)?).copied().unwrap_or(cur), // MTX: restore
                0x04 => material = self.materials.get(d.u8(c + 1)? as usize).cloned(), // MAT
                0x05 => {
                    // SHP
                    if let Some(&shape) = self.shapes.get(d.u8(c + 1)? as usize) {
                        out.extend(self.run_dl(shape, cur, &mut stack, &material)?);
                    }
                }
                0x06 => {
                    // NODEDESC node, parent, attr [dest] [src]
                    if opt == 0x40 || opt == 0x60 {
                        let src = d.u8(if opt == 0x40 { c + 4 } else { c + 5 })?;
                        cur = stack.get(&src).copied().unwrap_or(cur);
                        length += 1;
                    }
                    let node = d.u8(c + 1)? as usize;
                    if node < self.nodes.len() {
                        cur = mat_mul(&self.node_matrix(node)?, &cur);
                    }
                    if opt == 0x20 || opt == 0x60 {
                        stack.insert(d.u8(c + 4)?, cur);
                        length += 1;
                    }
                }
                0x07 | 0x08 => {
                    // billboards: keep the matrix, skip the extra arguments
                    if opt == 0x20 || opt == 0x60 {
                        length += 1;
                    }
                    if opt == 0x40 || opt == 0x60 {
                        length += 1;
                    }
                }
                0x0B => {
                    // POSSCALE
                    let s = if opt == 0 { self.pos_scale } else { self.inv_pos_scale };
                    cur = mat_mul(&mat_scale([s, s, s]), &cur);
                }
                _ => {}
            }
            c += length;
        }
        Ok(out)
    }

    fn run_dl(
        &self,
        (start, size): (usize, usize),
        mtx: Mat,
        stack: &mut HashMap<u8, Mat>,
        material: &Option<Arc<Material>>,
    ) -> Result<Vec<Polygon>> {
        let d = self.d;
        let mut o = start;
        let end = start + size;
        let mut polys = Vec::new();
        let mut cur = mtx;
        let mut prim: Option<u32> = None;
        let mut verts: Vec<Vertex> = Vec::new();
        let mut vtx = [0.0f64; 3];
        let mut uv = [0.0f64; 2];
        let mut color = material.as_ref().map(|m| m.diffuse()).unwrap_or([255, 255, 255]);
        let mut normal: Option<[f64; 3]> = None;
        while o < end {
            let cmds: [u8; 4] = d.slice(o, 4)?.try_into().unwrap();
            o += 4;
            for cmd in cmds {
                let Some(n) = gx_params(cmd) else { bail!("{}: unknown GX command {:02X}", self.name, cmd) };
                let p = o;
                o += 4 * n;
                match cmd {
                    0x14 => cur = stack.get(&((d.u32(p)? & 31) as u8)).copied().unwrap_or(cur), // MTX_RESTORE
                    0x13 => {
                        stack.insert((d.u32(p)? & 31) as u8, cur); // MTX_STORE
                    }
                    0x15 => cur = IDENTITY,
                    0x16..=0x1C => {
                        // load / multiply / scale / translate
                        let v: Vec<f64> = (0..n).map(|i| Ok(d.s32(p + 4 * i)? as f64 / FX)).collect::<Result<_>>()?;
                        let m: Mat = match cmd {
                            0x16 | 0x18 => v.as_slice().try_into().unwrap(),
                            0x17 | 0x19 => mat_from_3x3(&v[0..9], [v[9], v[10], v[11]]),
                            0x1A => mat_from_3x3(&v, [0.; 3]),
                            0x1B => mat_scale([v[0], v[1], v[2]]),
                            _ => mat_trans([v[0], v[1], v[2]]),
                        };
                        cur = if cmd == 0x16 || cmd == 0x17 { m } else { mat_mul(&m, &cur) };
                    }
                    0x20 => color = rgb555(d.u32(p)? as u16), // COLOR
                    0x21 => {
                        // NORMAL, three s0.9 fields
                        let v = d.u32(p)?;
                        normal = Some([0, 10, 20].map(|s| sext((v >> s) & 0x3FF, 10) as f64 / 512.0));
                    }
                    0x22 => {
                        // TEXCOORD, 12.4 texels
                        let v = d.u32(p)?;
                        uv = [sext(v & 0xFFFF, 16) as f64 / 16.0, sext(v >> 16, 16) as f64 / 16.0];
                    }
                    0x23 => {
                        // VTX_16
                        let (a, b) = (d.u32(p)?, d.u32(p + 4)?);
                        vtx = [sext(a & 0xFFFF, 16) as f64 / FX, sext(a >> 16, 16) as f64 / FX, sext(b & 0xFFFF, 16) as f64 / FX];
                        emit(prim, &mut verts, &mut polys, material, Vertex { pos: transform(&cur, vtx), uv, color, normal });
                    }
                    0x24 => {
                        // VTX_10, 4.6
                        let v = d.u32(p)?;
                        vtx = [0, 10, 20].map(|s| sext((v >> s) & 0x3FF, 10) as f64 / 64.0);
                        emit(prim, &mut verts, &mut polys, material, Vertex { pos: transform(&cur, vtx), uv, color, normal });
                    }
                    0x25..=0x27 => {
                        // VTX_XY / XZ / YZ
                        let v = d.u32(p)?;
                        let (a, b) = (sext(v & 0xFFFF, 16) as f64 / FX, sext(v >> 16, 16) as f64 / FX);
                        match cmd {
                            0x25 => (vtx[0], vtx[1]) = (a, b),
                            0x26 => (vtx[0], vtx[2]) = (a, b),
                            _ => (vtx[1], vtx[2]) = (a, b),
                        }
                        emit(prim, &mut verts, &mut polys, material, Vertex { pos: transform(&cur, vtx), uv, color, normal });
                    }
                    0x28 => {
                        // VTX_DIFF: offsets in 1/4096
                        let v = d.u32(p)?;
                        let off = [0, 10, 20].map(|s| sext((v >> s) & 0x3FF, 10) as f64 / FX);
                        vtx = [vtx[0] + off[0], vtx[1] + off[1], vtx[2] + off[2]];
                        emit(prim, &mut verts, &mut polys, material, Vertex { pos: transform(&cur, vtx), uv, color, normal });
                    }
                    0x40 => {
                        prim = Some(d.u32(p)? & 3); // BEGIN_VTXS
                        verts.clear();
                    }
                    0x41 => {
                        prim = None; // END_VTXS
                        verts.clear();
                    }
                    _ => {}
                }
            }
        }
        Ok(polys)
    }
}

/// Add a vertex to the primitive being drawn; emit a polygon when one is complete.
fn emit(prim: Option<u32>, verts: &mut Vec<Vertex>, polys: &mut Vec<Polygon>, material: &Option<Arc<Material>>, v: Vertex) {
    verts.push(v);
    let n = verts.len();
    let poly = |vs: Vec<Vertex>| Polygon { verts: vs, material: material.clone() };
    match prim {
        Some(0) if n.is_multiple_of(3) => polys.push(poly(verts[n - 3..].to_vec())),
        Some(1) if n.is_multiple_of(4) => polys.push(poly(verts[n - 4..].to_vec())),
        Some(2) if n >= 3 => {
            let (a, b, c) = (verts[n - 3], verts[n - 2], verts[n - 1]);
            polys.push(poly(if n % 2 == 1 { vec![a, b, c] } else { vec![b, a, c] }));
        }
        Some(3) if n >= 4 && n.is_multiple_of(2) => {
            let (a, b, c, e) = (verts[n - 4], verts[n - 3], verts[n - 2], verts[n - 1]);
            polys.push(poly(vec![a, b, e, c]));
        }
        _ => {}
    }
}

/// An NSBMD file: its models and its own textures (most map models have none).
pub struct Nsbmd<'a> {
    pub models: Vec<Model<'a>>,
    pub textures: Option<TextureSet>,
}

impl<'a> Nsbmd<'a> {
    pub fn read(data: &'a [u8]) -> Result<Nsbmd<'a>> {
        let d = Bytes(data);
        let b = blocks(d, b"BMD0")?;
        let Some(base) = find_block(&b, b"MDL0") else { bail!("NSBMD without MDL0") };
        let mut models = Vec::new();
        for (n, p) in read_dict(d, base + 8)? {
            models.push(Model::read(n, d, base + d.u32(p)? as usize)?);
        }
        let textures = match find_block(&b, b"TEX0") {
            Some(o) => Some(TextureSet::read_tex0(d, o)?),
            None => None,
        };
        Ok(Nsbmd { models, textures })
    }

    /// Every model's triangles.
    pub fn triangles(&self) -> Result<Vec<Triangle>> {
        let mut out = Vec::new();
        for m in &self.models {
            out.extend(m.triangles()?);
        }
        Ok(out)
    }
}
