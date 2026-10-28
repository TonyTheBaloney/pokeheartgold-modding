// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Top-down pictures of a cell's 3D terrain and props, for the map view (a port of
//! tools/mapeditor/mapeditor/terrain.py, drawing without Qt).
//!
//! Each cell's model.nsbmd is drawn with the textures of its map's area (map.json
//! "area_data" -> area header -> map texture set), and each prop in props.json with
//! the area's prop models (room or field, by the header's buildModelKind) and prop
//! textures, as src/field/area_data.c and map_prop_manager.c load them. Archive
//! paths come from the manifest's "binaries", inside the build's `files/` tree.
//!
//! Looking straight down, a triangle maps texture space to the image by an affine
//! transform. Triangles are drawn lowest first so roofs and trees cover the ground.
//! One model unit is one pixel: a 32-tile cell is 512 x 512.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, PoisonError};

use gen4map_format::manifest::Manifest;
use gen4map_format::props::Prop;
use gen4map_nitro::model::{Material, Nsbmd, Triangle};
use gen4map_nitro::narc::Narc;
use gen4map_nitro::texture::TextureSet;
use gen4map_nitro::{areatex, Image};

pub const CELL_PX: usize = 512;
pub const HALF: f64 = CELL_PX as f64 / 2.0;

/// Where the renderer's binaries are: NitroFS paths from the manifest, in `files/`.
#[derive(Debug, Clone)]
pub struct Sources {
    pub area_headers: PathBuf,
    pub map_textures_narc: PathBuf,
    pub area_textures: PathBuf,
    pub prop_textures: PathBuf,
    pub prop_models_room: PathBuf,
    pub prop_models_field: PathBuf,
    pub landdata: PathBuf,
}

impl Sources {
    pub fn from_manifest(root: &Path, m: &Manifest) -> Sources {
        let bin = |key: &str, sub: Option<&str>, default: &str| {
            root.join("files").join(m.binary(key, sub).unwrap_or_else(|| default.to_string()))
        };
        Sources {
            area_headers: bin("area_headers", None, "a/0/4/2"),
            map_textures_narc: bin("map_textures", None, "a/0/4/4"),
            area_textures: root.join(&m.paths.area_textures),
            prop_textures: bin("prop_textures", None, "a/0/7/0"),
            prop_models_room: bin("prop_models", Some("room"), "a/1/4/8"),
            prop_models_field: bin("prop_models", Some("field"), "a/0/4/0"),
            landdata: root.join(&m.paths.landdata),
        }
    }
}

/// An area header (NARC a/0/4/2 member): what src/field/area_data.c loads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Area {
    pub prop_set: u16,
    pub texture_set: u16,
    /// buildModelKind: 0 = room props, otherwise field props.
    pub kind: u8,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum TexKey {
    Land(u16),
    MapSet(u16),
    PropSet(u16),
    Prop(u8, u32),
}

pub struct Mesh {
    pub triangles: Vec<Triangle>,
    pub own_textures: Option<Arc<TextureSet>>,
}

/// One triangle to draw: where its textures come from and its offset in model units.
pub struct Item {
    pub mesh: Arc<Mesh>,
    pub index: usize,
    pub tex_key: TexKey,
    pub textures: Option<Arc<TextureSet>>,
    pub offset: [f64; 3],
}

impl Item {
    pub fn triangle(&self) -> &Triangle {
        &self.mesh.triangles[self.index]
    }
}

/// A texture ready to sample: mirrored copies laid out when the material flips.
pub struct TexImage {
    pub width: usize,
    pub height: usize,
    pub rgba: Vec<u8>,
}

type ImageKey = (TexKey, String, Option<String>, (bool, bool));

#[derive(Default)]
struct Caches {
    narcs: HashMap<PathBuf, Option<Arc<Narc>>>,
    texsets: HashMap<TexKey, Option<Arc<TextureSet>>>,
    images: HashMap<ImageKey, Option<Arc<TexImage>>>,
    meshes: HashMap<TexKey, Arc<Mesh>>,
}

/// Shared by the threads that draw cells: every cache is behind one lock, held only
/// while looking up, never while decoding or drawing. A thread that panicked doesn't
/// lock the others out (the caches only ever hold finished values).
pub struct Renderer {
    pub sources: Sources,
    caches: Mutex<Caches>,
    errors: Mutex<Vec<(String, String)>>,
}

impl Renderer {
    pub fn new(sources: Sources) -> Renderer {
        Renderer { sources, caches: Mutex::default(), errors: Mutex::default() }
    }

    fn error(&self, what: String, msg: String) {
        let mut e = self.errors.lock().unwrap_or_else(PoisonError::into_inner);
        if !e.iter().any(|(w, m)| *w == what && *m == msg) {
            e.push((what, msg));
        }
    }

    /// Things that could not be drawn: (what, why), each once.
    pub fn errors(&self) -> Vec<(String, String)> {
        self.errors.lock().unwrap_or_else(PoisonError::into_inner).clone()
    }

    fn narc(&self, path: &Path) -> Option<Arc<Narc>> {
        if let Some(n) = self.caches.lock().unwrap_or_else(PoisonError::into_inner).narcs.get(path) {
            return n.clone();
        }
        let n = match Narc::open(path) {
            Ok(n) => Some(Arc::new(n)),
            Err(e) => {
                self.error(path.display().to_string(), e.0);
                None
            }
        };
        self.caches.lock().unwrap_or_else(PoisonError::into_inner).narcs.insert(path.to_path_buf(), n.clone());
        n
    }

    pub fn area(&self, id: u16) -> Result<Area, String> {
        let narc = self.narc(&self.sources.area_headers).ok_or("no area headers")?;
        let m = narc.get(id as usize).ok_or_else(|| format!("no area {}", id))?;
        if m.len() < 8 {
            return Err(format!("area {}: header of {} bytes", id, m.len()));
        }
        let u16_at = |o: usize| u16::from_le_bytes([m[o], m[o + 1]]);
        Ok(Area { prop_set: u16_at(0), texture_set: u16_at(2), kind: m[6] })
    }

    /// A texture set, or None (areas without prop textures have a 4-byte placeholder).
    pub fn texture_set(&self, key: &TexKey) -> Option<Arc<TextureSet>> {
        if let Some(t) = self.caches.lock().unwrap_or_else(PoisonError::into_inner).texsets.get(key) {
            return t.clone();
        }
        let loaded = match key {
            TexKey::MapSet(n) => {
                let dir = self.sources.area_textures.join(format!("{:03}", n));
                if dir.is_dir() {
                    areatex::read_set(&dir).map_err(|e| e.0)
                } else {
                    // a project that keeps the binary archive
                    match self.narc(&self.sources.map_textures_narc).and_then(|a| a.get(*n as usize).map(<[u8]>::to_vec)) {
                        Some(d) => TextureSet::read_nsbtx(&d).map_err(|e| e.0),
                        None => Err(format!("no map texture set {}", n)),
                    }
                }
            }
            TexKey::PropSet(n) => match self.narc(&self.sources.prop_textures).and_then(|a| a.get(*n as usize).map(<[u8]>::to_vec)) {
                Some(d) if d.starts_with(b"BTX0") => TextureSet::read_nsbtx(&d).map_err(|e| e.0),
                _ => Err(String::new()), // no prop textures: not an error
            },
            _ => Err(String::new()),
        };
        let t = match loaded {
            Ok(t) => Some(Arc::new(t)),
            Err(e) => {
                if !e.is_empty() {
                    self.error(format!("textures {:?}", key), e);
                }
                None
            }
        };
        self.caches.lock().unwrap_or_else(PoisonError::into_inner).texsets.insert(key.clone(), t.clone());
        t
    }

    fn mesh(&self, key: TexKey, data: &[u8]) -> Result<Arc<Mesh>, String> {
        if let Some(m) = self.caches.lock().unwrap_or_else(PoisonError::into_inner).meshes.get(&key) {
            return Ok(m.clone());
        }
        let nsbmd = Nsbmd::read(data).map_err(|e| e.0)?;
        let mesh = Arc::new(Mesh { triangles: nsbmd.triangles().map_err(|e| e.0)?, own_textures: nsbmd.textures.map(Arc::new) });
        self.caches.lock().unwrap_or_else(PoisonError::into_inner).meshes.insert(key, mesh.clone());
        Ok(mesh)
    }

    /// The image a material draws with (mirrored when it flips), or None.
    pub fn image(&self, key: &TexKey, set: &TextureSet, mat: &Material) -> Option<Arc<TexImage>> {
        let tex = mat.texture.clone()?;
        let ikey = (key.clone(), tex.clone(), mat.palette.clone(), mat.flip());
        if let Some(i) = self.caches.lock().unwrap_or_else(PoisonError::into_inner).images.get(&ikey) {
            return i.clone();
        }
        let img = set.image(&tex, mat.palette.as_deref()).map(|img| Arc::new(mirrored(&img, mat.flip())));
        self.caches.lock().unwrap_or_else(PoisonError::into_inner).images.insert(ikey, img.clone());
        img
    }

    /// The triangles of a cell's terrain and props. The terrain is raised by the
    /// layout cell's altitude (altitude << 15 in fx32, CalcMapPosition in
    /// src/field/map_load_manager.c); props are not, their y is absolute.
    pub fn cell_items(&self, land: u16, area_id: u16, props: &[Prop], altitude: u8) -> Result<Vec<Item>, String> {
        let area = self.area(area_id)?;
        let path = self.sources.landdata.join(format!("{:04}", land)).join("model.nsbmd");
        let data = std::fs::read(&path).map_err(|e| format!("{}: {}", path.display(), e))?;
        let mesh = self.mesh(TexKey::Land(land), &data)?;
        let (tex_key, textures) = match &mesh.own_textures {
            Some(own) => (TexKey::Land(land), Some(own.clone())),
            None => (TexKey::MapSet(area.texture_set), self.texture_set(&TexKey::MapSet(area.texture_set))),
        };
        let mut out: Vec<Item> = (0..mesh.triangles.len())
            .map(|index| Item {
                mesh: mesh.clone(),
                index,
                tex_key: tex_key.clone(),
                textures: textures.clone(),
                offset: [0.0, altitude as f64 * 8.0, 0.0],
            })
            .collect();
        let models_path = if area.kind != 0 { &self.sources.prop_models_field } else { &self.sources.prop_models_room };
        let Some(models) = self.narc(models_path) else { return Ok(out) };
        let prop_key = TexKey::PropSet(area.prop_set);
        let prop_textures = self.texture_set(&prop_key);
        for (i, p) in props.iter().enumerate() {
            let Some(data) = models.get(p.model as usize) else {
                self.error(format!("land {:04} prop {}", land, i), format!("no prop model {}", p.model));
                continue;
            };
            let key = TexKey::Prop(area.kind, p.model);
            let mesh = match self.mesh(key.clone(), data) {
                Ok(m) => m,
                Err(e) => {
                    self.error(format!("prop model {}", p.model), e);
                    continue;
                }
            };
            let (tex_key, textures) = match &mesh.own_textures {
                Some(own) => (key, Some(own.clone())),
                None => (prop_key.clone(), prop_textures.clone()),
            };
            out.extend((0..mesh.triangles.len()).map(|index| Item {
                mesh: mesh.clone(),
                index,
                tex_key: tex_key.clone(),
                textures: textures.clone(),
                offset: p.position,
            }));
        }
        Ok(out)
    }

    /// The cell from above: CELL_PX square, transparent where nothing is drawn.
    pub fn render_cell(&self, land: u16, area_id: u16, props: &[Prop], altitude: u8) -> Image {
        let mut canvas = Canvas::new(CELL_PX, CELL_PX);
        let items = match self.cell_items(land, area_id, props, altitude) {
            Ok(items) => items,
            Err(e) => {
                self.error(format!("land {:04}", land), e);
                return canvas.into_image();
            }
        };
        // lowest first; for equal heights keep the model's own order
        let top = |it: &Item| it.triangle().v.iter().map(|v| v.pos[1] + it.offset[1]).fold(f64::MIN, f64::max);
        let mut order: Vec<usize> = (0..items.len()).collect();
        order.sort_by(|&a, &b| top(&items[a]).total_cmp(&top(&items[b])));
        for i in order {
            let it = &items[i];
            let tri = it.triangle();
            let pts = tri.v.map(|v| [v.pos[0] + it.offset[0] + HALF, v.pos[2] + it.offset[2] + HALF]);
            let area2 = (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[2][0] - pts[0][0]) * (pts[1][1] - pts[0][1]);
            if area2.abs() < 0.01 {
                continue; // a wall seen edge-on
            }
            let alpha = tri.material.as_ref().map(|m| m.alpha()).unwrap_or(31);
            let opacity = if alpha == 0 || alpha == 31 { 1.0 } else { alpha as f64 / 31.0 };
            let img = match (&tri.material, &it.textures) {
                (Some(m), Some(set)) => self.image(&it.tex_key, set, m),
                _ => None,
            };
            let fill = match img.as_ref().zip(uv_inverse(&tri.v.map(|v| v.uv), &pts)) {
                Some((img, inv)) => Fill::Texture(img.clone(), inv),
                None => {
                    let avg = |k: usize| (tri.v.iter().map(|v| v.color[k] as u32).sum::<u32>() / 3) as u8;
                    Fill::Color([avg(0), avg(1), avg(2)])
                }
            };
            canvas.fill_triangle(&pts, &fill, opacity);
        }
        canvas.into_image()
    }
}

/// One period of a mirrored-repeat texture: the image and its mirror images.
fn mirrored(img: &Image, (fs, ft): (bool, bool)) -> TexImage {
    let (w, h) = (img.width, img.height);
    let (bw, bh) = (if fs { 2 * w } else { w }, if ft { 2 * h } else { h });
    let mut rgba = vec![0u8; bw * bh * 4];
    for y in 0..bh {
        for x in 0..bw {
            let sx = if x < w { x } else { 2 * w - 1 - x };
            let sy = if y < h { y } else { 2 * h - 1 - y };
            let (d, s) = ((y * bw + x) * 4, (sy * w + sx) * 4);
            rgba[d..d + 4].copy_from_slice(&img.rgba[s..s + 4]);
        }
    }
    TexImage { width: bw, height: bh, rgba }
}

/// The affine map from image pixels back to texels for one triangle, as
/// [a, b, c, d, e, f]: u = a x + b y + c, v = d x + e y + f. None if degenerate.
pub fn uv_inverse(uv: &[[f64; 2]; 3], pts: &[[f64; 2]; 3]) -> Option<[f64; 6]> {
    let (dx1, dy1, dx2, dy2) = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1], pts[2][0] - pts[0][0], pts[2][1] - pts[0][1]);
    let det = dx1 * dy2 - dx2 * dy1;
    let duv = (uv[1][0] - uv[0][0]) * (uv[2][1] - uv[0][1]) - (uv[2][0] - uv[0][0]) * (uv[1][1] - uv[0][1]);
    if det.abs() < 1e-9 || duv.abs() < 1e-9 {
        return None;
    }
    let (du1, dv1, du2, dv2) = (uv[1][0] - uv[0][0], uv[1][1] - uv[0][1], uv[2][0] - uv[0][0], uv[2][1] - uv[0][1]);
    // [u v] = [x - x0, y - y0] * inverse([[dx1 dy1], [dx2 dy2]]) * [[du1 dv1], [du2 dv2]]
    let (i00, i01, i10, i11) = (dy2 / det, -dy1 / det, -dx2 / det, dx1 / det);
    let a = i00 * du1 + i01 * du2;
    let b = i10 * du1 + i11 * du2;
    let d = i00 * dv1 + i01 * dv2;
    let e = i10 * dv1 + i11 * dv2;
    let c = uv[0][0] - a * pts[0][0] - b * pts[0][1];
    let f = uv[0][1] - d * pts[0][0] - e * pts[0][1];
    Some([a, b, c, d, e, f])
}

pub enum Fill {
    Color([u8; 3]),
    Texture(Arc<TexImage>, [f64; 6]),
}

/// An RGBA canvas with straight alpha, drawn with "source over".
pub struct Canvas {
    pub width: usize,
    pub height: usize,
    pub rgba: Vec<u8>,
}

impl Canvas {
    pub fn new(width: usize, height: usize) -> Canvas {
        Canvas { width, height, rgba: vec![0; width * height * 4] }
    }

    pub fn into_image(self) -> Image {
        Image { width: self.width, height: self.height, rgba: self.rgba }
    }

    fn blend(&mut self, x: usize, y: usize, src: [u8; 4], opacity: f64) {
        let i = (y * self.width + x) * 4;
        let sa = src[3] as f64 / 255.0 * opacity;
        if sa <= 0.0 {
            return;
        }
        let da = self.rgba[i + 3] as f64 / 255.0;
        let oa = sa + da * (1.0 - sa);
        for k in 0..3 {
            let v = (src[k] as f64 * sa + self.rgba[i + k] as f64 * da * (1.0 - sa)) / oa;
            self.rgba[i + k] = v.round().clamp(0.0, 255.0) as u8;
        }
        self.rgba[i + 3] = (oa * 255.0).round() as u8;
    }

    /// Fill the pixels whose centres are inside the triangle (top-left rule, so
    /// triangles sharing an edge don't both draw it).
    pub fn fill_triangle(&mut self, pts: &[[f64; 2]; 3], fill: &Fill, opacity: f64) {
        let mut p = *pts;
        let area = (p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1]);
        if area < 0.0 {
            p.swap(1, 2);
        }
        let x0 = p.iter().map(|q| q[0]).fold(f64::MAX, f64::min).floor().max(0.0) as usize;
        let y0 = p.iter().map(|q| q[1]).fold(f64::MAX, f64::min).floor().max(0.0) as usize;
        let x1 = (p.iter().map(|q| q[0]).fold(f64::MIN, f64::max).ceil() as i64).min(self.width as i64);
        let y1 = (p.iter().map(|q| q[1]).fold(f64::MIN, f64::max).ceil() as i64).min(self.height as i64);
        if x1 <= 0 || y1 <= 0 {
            return;
        }
        // edge i goes p[i] -> p[i+1]; inside is where every edge function is >= 0
        let edges: Vec<([f64; 2], [f64; 2], bool)> = (0..3)
            .map(|i| {
                let (a, b) = (p[i], p[(i + 1) % 3]);
                // of two triangles sharing an edge, each walks it the other way; the one
                // walking it upward (leftward if horizontal) owns the pixels on it
                let top_left = (a[1] == b[1] && b[0] < a[0]) || b[1] < a[1];
                (a, b, top_left)
            })
            .collect();
        for y in y0..y1 as usize {
            let cy = y as f64 + 0.5;
            for x in x0..x1 as usize {
                let cx = x as f64 + 0.5;
                let inside = edges.iter().all(|&(a, b, tl)| {
                    let w = (b[0] - a[0]) * (cy - a[1]) - (b[1] - a[1]) * (cx - a[0]);
                    w > 0.0 || (w == 0.0 && tl)
                });
                if !inside {
                    continue;
                }
                let src = match fill {
                    Fill::Color(c) => [c[0], c[1], c[2], 255],
                    Fill::Texture(img, m) => {
                        let u = m[0] * cx + m[1] * cy + m[2];
                        let v = m[3] * cx + m[4] * cy + m[5];
                        let tx = (u.floor() as i64).rem_euclid(img.width as i64) as usize;
                        let ty = (v.floor() as i64).rem_euclid(img.height as i64) as usize;
                        let i = (ty * img.width + tx) * 4;
                        [img.rgba[i], img.rgba[i + 1], img.rgba[i + 2], img.rgba[i + 3]]
                    }
                };
                self.blend(x, y, src, opacity);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn affine_inverse() {
        let uv = [[0.0, 0.0], [8.0, 0.0], [0.0, 8.0]];
        let pts = [[10.0, 10.0], [26.0, 10.0], [10.0, 26.0]];
        let m = uv_inverse(&uv, &pts).unwrap();
        let at = |x: f64, y: f64| (m[0] * x + m[1] * y + m[2], m[3] * x + m[4] * y + m[5]);
        assert_eq!(at(10.0, 10.0), (0.0, 0.0));
        assert_eq!(at(26.0, 10.0), (8.0, 0.0));
        assert_eq!(at(18.0, 26.0), (4.0, 8.0));
    }

    #[test]
    fn shared_edges_draw_once() {
        let mut c = Canvas::new(8, 8);
        let half = Fill::Color([255, 0, 0]);
        c.fill_triangle(&[[0.0, 0.0], [8.0, 0.0], [8.0, 8.0]], &half, 0.5);
        c.fill_triangle(&[[0.0, 0.0], [8.0, 8.0], [0.0, 8.0]], &half, 0.5);
        // every pixel covered exactly once: alpha 0.5 everywhere
        assert!(c.rgba.chunks(4).all(|p| p[3] == 128), "{:?}", c.rgba.chunks(4).map(|p| p[3]).collect::<Vec<_>>());
    }
}
