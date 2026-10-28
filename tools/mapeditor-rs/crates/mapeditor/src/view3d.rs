// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! 3D view of a map (tools/mapeditor/mapeditor/view3d.py): its cells' terrain and
//! props drawn with OpenGL through egui's glow backend, an orbit camera, and the
//! objects' sprites as billboards standing on the ground the game finds under them.
//!
//! The mesh is grouped into one vertex buffer per (texture, palette, wrap, alpha,
//! polygon mode). Like the DS: textures repeat per material (mirrored ones are
//! pre-mirrored by the renderer), color 0 / alpha-0 texels are cut out, polygons with
//! alpha < 31 are blended, and in modulation mode the texture is multiplied by the
//! vertex color. Without OpenGL 3.3 (or ES 3.0) the tab says so; nothing else changes.

use std::collections::{BTreeMap, HashMap};
use std::sync::{Arc, Mutex, PoisonError};

use eframe::glow::{self, HasContext};
use egui::{Color32, Sense};
use gen4map_format::project::Project;
use gen4map_format::CELL;
use gen4map_nitro::bdhc::{self, Bdhc};
use gen4map_nitro::Image;
use gen4map_render::{Renderer, TexImage, HALF};
use serde_json::Value;

use crate::doc::MapDoc;
use crate::sprites::{facing_index, pose, SpriteImages};

const VERTEX: &str = r#"
layout(location = 0) in vec3 pos;
layout(location = 1) in vec2 uv;
layout(location = 2) in vec3 color;
uniform mat4 mvp;
out vec2 v_uv;
out vec3 v_color;
void main() {
    gl_Position = mvp * vec4(pos, 1.0);
    v_uv = uv;
    v_color = color;
}
"#;

const FRAGMENT: &str = r#"
in vec2 v_uv;
in vec3 v_color;
uniform sampler2D tex;
uniform bool textured;
uniform bool modulate;
uniform float alpha;
out vec4 frag;
void main() {
    vec4 c = vec4(v_color, 1.0);
    if (textured) {
        vec4 t = texture(tex, v_uv);
        if (t.a < 0.5) discard;
        c = modulate ? t * vec4(v_color, 1.0) : t;
    }
    frag = vec4(c.rgb, c.a * alpha);
}
"#;

/// Column-major 4x4, as GL takes it.
type M4 = [f32; 16];

fn mul(a: &M4, b: &M4) -> M4 {
    let mut out = [0.0; 16];
    for c in 0..4 {
        for r in 0..4 {
            out[c * 4 + r] = (0..4).map(|k| a[k * 4 + r] * b[c * 4 + k]).sum();
        }
    }
    out
}

fn perspective(fovy_deg: f32, aspect: f32, near: f32, far: f32) -> M4 {
    let f = 1.0 / (fovy_deg.to_radians() / 2.0).tan();
    let mut m = [0.0; 16];
    m[0] = f / aspect;
    m[5] = f;
    m[10] = (far + near) / (near - far);
    m[11] = -1.0;
    m[14] = 2.0 * far * near / (near - far);
    m
}

fn look_at(eye: [f32; 3], target: [f32; 3], up: [f32; 3]) -> M4 {
    let sub = |a: [f32; 3], b: [f32; 3]| [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    let norm = |v: [f32; 3]| {
        let l = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt().max(1e-9);
        [v[0] / l, v[1] / l, v[2] / l]
    };
    let cross = |a: [f32; 3], b: [f32; 3]| [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    let dot = |a: [f32; 3], b: [f32; 3]| a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    let f = norm(sub(target, eye));
    let s = norm(cross(f, up));
    let u = cross(s, f);
    [s[0], u[0], -f[0], 0.0, s[1], u[1], -f[1], 0.0, s[2], u[2], -f[2], 0.0, -dot(s, eye), -dot(u, eye), dot(f, eye), 1.0]
}

pub struct Camera {
    pub target: [f32; 3],
    pub distance: f32,
    /// Degrees, 0 = looking north.
    pub yaw: f32,
    /// Degrees above the horizon.
    pub pitch: f32,
}

impl Camera {
    fn matrix(&self, aspect: f32) -> M4 {
        let (p, y) = (self.pitch.to_radians(), self.yaw.to_radians());
        let t = self.target;
        let d = self.distance;
        let eye = [t[0] + y.sin() * p.cos() * d, t[1] + p.sin() * d, t[2] + y.cos() * p.cos() * d];
        mul(&perspective(40.0, aspect, 4.0, 20000.0), &look_at(eye, t, [0.0, 1.0, 0.0]))
    }
}

/// A batch's vertices on the CPU: x y z u v r g b per vertex.
struct BatchData {
    image: Option<Arc<TexImage>>,
    wrap: (bool, bool),
    alpha: f32,
    modulate: bool,
    data: Vec<f32>,
}

struct GpuBatch {
    vao: glow::VertexArray,
    vbo: glow::Buffer,
    texture: Option<glow::Texture>,
    count: i32,
    alpha: f32,
    modulate: bool,
}

struct Program {
    program: glow::Program,
    mvp: Option<glow::UniformLocation>,
    tex: Option<glow::UniformLocation>,
    textured: Option<glow::UniformLocation>,
    modulate: Option<glow::UniformLocation>,
    alpha: Option<glow::UniformLocation>,
}

type SpriteKey = (String, usize, usize);

/// A sprite to draw this frame: where it stands, which picture.
struct Billboard {
    pos: [f32; 3],
    key: SpriteKey,
    image: Arc<Image>,
}

#[derive(Default)]
struct Scene {
    program: Option<Program>,
    failed: Option<String>,
    batches: Vec<GpuBatch>,
    pending: Option<Vec<BatchData>>,
    sprite_vao: Option<(glow::VertexArray, glow::Buffer)>,
    sprite_textures: HashMap<SpriteKey, glow::Texture>,
}

fn compile(gl: &glow::Context, version: &str) -> Result<Program, String> {
    unsafe {
        let program = gl.create_program()?;
        let mut shaders = Vec::new();
        for (kind, src) in [(glow::VERTEX_SHADER, VERTEX), (glow::FRAGMENT_SHADER, FRAGMENT)] {
            let s = gl.create_shader(kind)?;
            // GLSL 3.30 accepts (and ignores) precision qualifiers; ES needs one
            gl.shader_source(s, &format!("{}\nprecision mediump float;\n{}", version, src));
            gl.compile_shader(s);
            if !gl.get_shader_compile_status(s) {
                let log = gl.get_shader_info_log(s);
                gl.delete_shader(s);
                gl.delete_program(program);
                return Err(log);
            }
            gl.attach_shader(program, s);
            shaders.push(s);
        }
        gl.link_program(program);
        for s in shaders {
            gl.detach_shader(program, s);
            gl.delete_shader(s);
        }
        if !gl.get_program_link_status(program) {
            let log = gl.get_program_info_log(program);
            gl.delete_program(program);
            return Err(log);
        }
        let loc = |n: &str| gl.get_uniform_location(program, n);
        Ok(Program { mvp: loc("mvp"), tex: loc("tex"), textured: loc("textured"), modulate: loc("modulate"), alpha: loc("alpha"), program })
    }
}

fn upload_texture(gl: &glow::Context, w: usize, h: usize, rgba: &[u8], wrap: (bool, bool)) -> Option<glow::Texture> {
    unsafe {
        let t = gl.create_texture().ok()?;
        gl.bind_texture(glow::TEXTURE_2D, Some(t));
        gl.pixel_store_i32(glow::UNPACK_ALIGNMENT, 1);
        gl.tex_image_2d(glow::TEXTURE_2D, 0, glow::RGBA8 as i32, w as i32, h as i32, 0, glow::RGBA, glow::UNSIGNED_BYTE, glow::PixelUnpackData::Slice(Some(rgba)));
        gl.tex_parameter_i32(glow::TEXTURE_2D, glow::TEXTURE_MIN_FILTER, glow::NEAREST as i32);
        gl.tex_parameter_i32(glow::TEXTURE_2D, glow::TEXTURE_MAG_FILTER, glow::NEAREST as i32);
        let mode = |r: bool| if r { glow::REPEAT } else { glow::CLAMP_TO_EDGE } as i32;
        gl.tex_parameter_i32(glow::TEXTURE_2D, glow::TEXTURE_WRAP_S, mode(wrap.0));
        gl.tex_parameter_i32(glow::TEXTURE_2D, glow::TEXTURE_WRAP_T, mode(wrap.1));
        gl.bind_texture(glow::TEXTURE_2D, None);
        Some(t)
    }
}

fn vertex_array(gl: &glow::Context, data: &[f32], usage: u32) -> Option<(glow::VertexArray, glow::Buffer)> {
    unsafe {
        let vao = gl.create_vertex_array().ok()?;
        let vbo = gl.create_buffer().ok()?;
        gl.bind_vertex_array(Some(vao));
        gl.bind_buffer(glow::ARRAY_BUFFER, Some(vbo));
        let bytes: Vec<u8> = data.iter().flat_map(|f| f.to_ne_bytes()).collect();
        gl.buffer_data_u8_slice(glow::ARRAY_BUFFER, &bytes, usage);
        let stride = 8 * 4;
        for (loc, size, offset) in [(0u32, 3i32, 0i32), (1, 2, 12), (2, 3, 20)] {
            gl.enable_vertex_attrib_array(loc);
            gl.vertex_attrib_pointer_f32(loc, size, glow::FLOAT, false, stride, offset);
        }
        gl.bind_vertex_array(None);
        gl.bind_buffer(glow::ARRAY_BUFFER, None);
        Some((vao, vbo))
    }
}

impl Scene {
    fn release_batches(&mut self, gl: &glow::Context) {
        unsafe {
            for b in self.batches.drain(..) {
                gl.delete_vertex_array(b.vao);
                gl.delete_buffer(b.vbo);
                if let Some(t) = b.texture {
                    gl.delete_texture(t);
                }
            }
        }
    }

    /// `clip`: the view's rect in pixels (x, y from the bottom, w, h); clearing stays inside it.
    fn paint(&mut self, gl: &glow::Context, clip: [i32; 4], mvp: &M4, yaw: f32, sprites: &[Billboard]) {
        if self.program.is_none() && self.failed.is_none() {
            match compile(gl, "#version 330 core").or_else(|e| compile(gl, "#version 300 es").map_err(|e2| format!("{}\n{}", e, e2))) {
                Ok(p) => self.program = Some(p),
                Err(e) => self.failed = Some(e),
            }
        }
        let Some(p) = &self.program else { return };
        let program = p.program;
        let (u_mvp, u_tex, u_textured, u_modulate, u_alpha) = (p.mvp, p.tex, p.textured, p.modulate, p.alpha);
        if let Some(pending) = self.pending.take() {
            self.release_batches(gl);
            for b in pending {
                if b.data.is_empty() {
                    continue;
                }
                let Some((vao, vbo)) = vertex_array(gl, &b.data, glow::STATIC_DRAW) else { continue };
                let texture = b.image.as_ref().and_then(|i| upload_texture(gl, i.width, i.height, &i.rgba, b.wrap));
                self.batches.push(GpuBatch { vao, vbo, texture, count: (b.data.len() / 8) as i32, alpha: b.alpha, modulate: b.modulate });
            }
            // opaque first
            self.batches.sort_by_key(|a| a.alpha < 1.0);
        }
        unsafe {
            // egui's scissor is its panel's: narrow it to the view so the clear spares the widgets around it
            gl.enable(glow::SCISSOR_TEST);
            gl.scissor(clip[0], clip[1], clip[2], clip[3]);
            gl.clear_color(0.12, 0.13, 0.16, 1.0);
            gl.clear_depth_f32(1.0);
            gl.depth_mask(true);
            gl.clear(glow::COLOR_BUFFER_BIT | glow::DEPTH_BUFFER_BIT);
            gl.enable(glow::DEPTH_TEST);
            gl.depth_func(glow::LEQUAL);
            gl.disable(glow::CULL_FACE);
            gl.disable(glow::BLEND);
            gl.use_program(Some(program));
            gl.uniform_matrix_4_f32_slice(u_mvp.as_ref(), false, mvp);
            gl.uniform_1_i32(u_tex.as_ref(), 0);
            gl.active_texture(glow::TEXTURE0);
            for b in &self.batches {
                if b.alpha < 1.0 {
                    gl.enable(glow::BLEND);
                    gl.blend_func(glow::SRC_ALPHA, glow::ONE_MINUS_SRC_ALPHA);
                    gl.depth_mask(false);
                }
                gl.uniform_1_i32(u_textured.as_ref(), b.texture.is_some() as i32);
                gl.uniform_1_i32(u_modulate.as_ref(), b.modulate as i32);
                gl.uniform_1_f32(u_alpha.as_ref(), b.alpha);
                gl.bind_texture(glow::TEXTURE_2D, b.texture);
                gl.bind_vertex_array(Some(b.vao));
                gl.draw_arrays(glow::TRIANGLES, 0, b.count);
                if b.alpha < 1.0 {
                    gl.disable(glow::BLEND);
                    gl.depth_mask(true);
                }
            }
            gl.bind_vertex_array(None);
        }
        self.paint_sprites(gl, program, yaw, sprites, (u_textured, u_modulate, u_alpha));
        unsafe {
            gl.bind_texture(glow::TEXTURE_2D, None);
            gl.use_program(None);
            gl.disable(glow::DEPTH_TEST);
            gl.depth_mask(true);
        }
    }

    /// Billboards after the terrain, each standing upright on its point, one texel per
    /// world unit, turned to face the camera around the vertical.
    #[allow(clippy::type_complexity)]
    fn paint_sprites(
        &mut self,
        gl: &glow::Context,
        program: glow::Program,
        yaw: f32,
        sprites: &[Billboard],
        (u_textured, u_modulate, u_alpha): (Option<glow::UniformLocation>, Option<glow::UniformLocation>, Option<glow::UniformLocation>),
    ) {
        if sprites.is_empty() {
            return;
        }
        let (rx, rz) = (yaw.to_radians().cos(), -yaw.to_radians().sin());
        let mut groups: BTreeMap<SpriteKey, Vec<f32>> = BTreeMap::new();
        for s in sprites {
            if !self.sprite_textures.contains_key(&s.key) {
                if let Some(t) = upload_texture(gl, s.image.width, s.image.height, &s.image.rgba, (false, false)) {
                    self.sprite_textures.insert(s.key.clone(), t);
                }
            }
            let (hw, h) = (s.image.width as f32 / 2.0, s.image.height as f32);
            let [x, y, z] = s.pos;
            let data = groups.entry(s.key.clone()).or_default();
            for (dx, dy, u, v) in [(-hw, 0.0, 0.0, 1.0), (hw, 0.0, 1.0, 1.0), (hw, h, 1.0, 0.0), (-hw, 0.0, 0.0, 1.0), (hw, h, 1.0, 0.0), (-hw, h, 0.0, 0.0)] {
                data.extend([x + rx * dx, y + dy, z + rz * dx, u, v, 1.0, 1.0, 1.0]);
            }
        }
        let mut raw = Vec::new();
        let mut spans = Vec::new();
        for (key, data) in &groups {
            spans.push((key.clone(), (raw.len() / 8) as i32, (data.len() / 8) as i32));
            raw.extend_from_slice(data);
        }
        unsafe {
            if let Some((vao, vbo)) = self.sprite_vao.take() {
                gl.delete_vertex_array(vao);
                gl.delete_buffer(vbo);
            }
            let Some((vao, vbo)) = vertex_array(gl, &raw, glow::STREAM_DRAW) else { return };
            self.sprite_vao = Some((vao, vbo));
            gl.use_program(Some(program));
            gl.uniform_1_i32(u_textured.as_ref(), 1);
            gl.uniform_1_i32(u_modulate.as_ref(), 0);
            gl.uniform_1_f32(u_alpha.as_ref(), 1.0);
            gl.bind_vertex_array(Some(vao));
            for (key, first, count) in spans {
                gl.bind_texture(glow::TEXTURE_2D, self.sprite_textures.get(&key).copied());
                gl.draw_arrays(glow::TRIANGLES, first, count);
            }
            gl.bind_vertex_array(None);
        }
    }
}

pub struct View3D {
    gl: Option<Arc<glow::Context>>,
    scene: Arc<Mutex<Scene>>,
    camera: Camera,
    stale: bool,
    heights: HashMap<u16, Option<Bdhc>>,
    start: std::time::Instant,
}

impl View3D {
    pub fn new(gl: Option<Arc<glow::Context>>) -> View3D {
        View3D {
            gl,
            scene: Arc::default(),
            camera: Camera { target: [0.0; 3], distance: 900.0, yaw: 0.0, pitch: 50.0 },
            stale: true,
            heights: HashMap::new(),
            start: std::time::Instant::now(),
        }
    }

    /// The map or its area changed: rebuild the scene when next shown.
    pub fn invalidate(&mut self) {
        self.stale = true;
        self.heights.clear();
    }

    /// World height (model units) an object standing on global tile x, y is drawn at:
    /// the cell's heights at the tile's centre, nearest `elevation` (fx32) where plates
    /// overlap, as src/field_terrain.c finds it; the cell's altitude when it has none
    /// there. (A cell with heights.json instead of terrain.bdhc uses its altitude.)
    fn ground(&mut self, project: &Project, doc: &MapDoc, x: i64, y: i64, elevation: i64) -> f32 {
        if x < 0 || y < 0 {
            return 0.0;
        }
        let (cx, cy) = (x as usize / CELL, y as usize / CELL);
        let Some(land) = doc.cell_land(cx, cy) else { return 0.0 };
        let heights = self.heights.entry(land).or_insert_with(|| {
            std::fs::read(project.landdata_dir(land).join("terrain.bdhc")).ok().and_then(|d| Bdhc::read(&d).ok())
        });
        let fx = bdhc::FX;
        let at = |t: i64| ((t % CELL as i64) * 16 + 8 - 256) * fx;
        match heights.as_ref().and_then(|h| h.height(at(x), at(y), bdhc::Mode::Nearest, elevation)) {
            Some(h) => h as f32 / fx as f32,
            None => doc.cell_altitude(cx, cy) as f32 * 8.0,
        }
    }

    fn build(&mut self, doc: &MapDoc, renderer: &Renderer) {
        let cells = doc.shown_cells();
        let mut batches: Vec<BatchData> = Vec::new();
        let mut index: HashMap<String, usize> = HashMap::new();
        let area = doc.area();
        for &(cx, cy) in &cells {
            let Some(chunk) = doc.chunk(cx, cy) else { continue };
            let (ox, oz) = ((cx * CELL * 16) as f64 + HALF, (cy * CELL * 16) as f64 + HALF);
            // errors show in the renderer's list; the other cells are drawn
            let Ok(items) = renderer.cell_items(chunk.number, area, &chunk.props, doc.cell_altitude(cx, cy)) else { continue };
            for it in items {
                let tri = it.triangle();
                let mat = tri.material.as_deref();
                let mode = mat.map(|m| (m.poly_attr >> 4) & 3).unwrap_or(0);
                if mode == 3 {
                    continue; // shadow volume polygons, not drawn as surfaces
                }
                let alpha = mat.map(|m| if m.alpha() == 0 { 31 } else { m.alpha() }).unwrap_or(31);
                let img = match (mat, &it.textures) {
                    (Some(m), Some(set)) => renderer.image(&it.tex_key, set, m),
                    _ => None,
                };
                let (key, wrap, size) = match (&img, mat) {
                    (Some(i), Some(m)) => (
                        format!("{:?} {:?} {:?} {:?} {:?} {} {}", it.tex_key, m.texture, m.palette, m.flip(), m.repeat(), alpha, mode),
                        m.repeat(),
                        (i.width as f64, i.height as f64),
                    ),
                    _ => (format!("color {}", alpha), (false, false), (1.0, 1.0)),
                };
                let bi = *index.entry(key).or_insert_with(|| {
                    batches.push(BatchData { image: img.clone(), wrap, alpha: alpha as f32 / 31.0, modulate: mode == 0, data: Vec::new() });
                    batches.len() - 1
                });
                let data = &mut batches[bi].data;
                for v in &tri.v {
                    data.extend([
                        (v.pos[0] + it.offset[0] + ox) as f32,
                        (v.pos[1] + it.offset[1]) as f32,
                        (v.pos[2] + it.offset[2] + oz) as f32,
                        (v.uv[0] / size.0) as f32,
                        (v.uv[1] / size.1) as f32,
                        v.color[0] as f32 / 255.0,
                        v.color[1] as f32 / 255.0,
                        v.color[2] as f32 / 255.0,
                    ]);
                }
            }
        }
        self.scene.lock().unwrap_or_else(PoisonError::into_inner).pending = Some(batches);
        // the camera looks at the map's own cells
        let own = doc.own_cells();
        let own = if own.is_empty() { cells } else { own };
        if !own.is_empty() {
            let n = own.len() as f32;
            let cx = own.iter().map(|c| c.0 as f32).sum::<f32>() / n;
            let cy = own.iter().map(|c| c.1 as f32).sum::<f32>() / n;
            let cell = (CELL * 16) as f32;
            self.camera.target = [(cx + 0.5) * cell, 0.0, (cy + 0.5) * cell];
            let span = |f: fn(&(usize, usize)) -> usize| own.iter().map(f).max().unwrap() - own.iter().map(f).min().unwrap();
            self.camera.distance = 700.0 * (span(|c| c.0).max(span(|c| c.1)) + 1) as f32;
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn ui(
        &mut self,
        ui: &mut egui::Ui,
        doc: &MapDoc,
        renderer: &Renderer,
        project: &Project,
        sprites: &mut SpriteImages,
        layers: &BTreeMap<String, bool>,
    ) {
        if self.gl.is_none() {
            ui.centered_and_justified(|ui| ui.label("The 3D view needs the OpenGL backend."));
            return;
        }
        if let Some(e) = self.scene.lock().unwrap_or_else(PoisonError::into_inner).failed.clone() {
            ui.label(format!("The 3D view needs OpenGL 3.3 or OpenGL ES 3.0; the shaders didn't compile:\n{}", e));
            return;
        }
        if self.stale {
            self.build(doc, renderer);
            self.stale = false;
        }
        ui.weak("Left drag turns, right or middle drag pans, wheel zooms");
        let (rect, response) = ui.allocate_exact_size(ui.available_size(), Sense::click_and_drag());
        let d = response.drag_delta();
        if response.dragged_by(egui::PointerButton::Primary) {
            self.camera.yaw -= d.x * 0.4;
            self.camera.pitch = (self.camera.pitch + d.y * 0.4).clamp(5.0, 89.0);
        } else if response.dragged_by(egui::PointerButton::Secondary) || response.dragged_by(egui::PointerButton::Middle) {
            let y = self.camera.yaw.to_radians();
            let k = self.camera.distance / 600.0;
            let (right, fwd) = ([y.cos(), -y.sin()], [-y.sin(), -y.cos()]);
            self.camera.target[0] += right[0] * (-d.x * k) + fwd[0] * (d.y * k);
            self.camera.target[2] += right[1] * (-d.x * k) + fwd[1] * (d.y * k);
        }
        if response.hovered() {
            let scroll = ui.input(|i| i.smooth_scroll_delta.y);
            if scroll != 0.0 {
                self.camera.distance = (self.camera.distance * 0.85f32.powf(scroll / 50.0)).clamp(50.0, 15000.0);
            }
        }
        // the objects shown in the map tab, standing on the ground
        let mut billboards = Vec::new();
        let on = |k: &str| layers.get(k).copied().unwrap_or(false);
        let tick = self.start.elapsed().as_millis() as u64 / crate::canvas::ANIMATION_MS;
        if on("events") && on("sprites") {
            for ev in doc.events("object_events") {
                let (Some(x), Some(y)) = (ev.get("x").and_then(Value::as_i64), ev.get("y").and_then(Value::as_i64)) else { continue };
                let g = ev.get("graphics_id").and_then(Value::as_str).unwrap_or("");
                if sprites.why_not(g).is_some() {
                    continue;
                }
                let facing = facing_index(ev.get("facing_dir").unwrap_or(&Value::Null));
                let (facing, step) = if on("animate") {
                    pose(ev.get("movement_type").and_then(Value::as_str).unwrap_or(""), facing, sprites.frames(g), tick)
                } else {
                    (facing, 0)
                };
                let Some(image) = sprites.image(g, facing, step) else { continue };
                let elevation = ev.get("elevation").and_then(Value::as_i64).unwrap_or(0);
                let ground = self.ground(project, doc, x, y, elevation);
                billboards.push(Billboard { pos: [(x * 16 + 8) as f32, ground, (y * 16 + 8) as f32], key: (g.to_string(), facing, step), image });
            }
        }
        if on("animate") && !billboards.is_empty() {
            ui.ctx().request_repaint_after(std::time::Duration::from_millis(crate::canvas::ANIMATION_MS));
        }
        let mvp = self.camera.matrix(rect.width() / rect.height().max(1.0));
        let yaw = self.camera.yaw;
        let scene = self.scene.clone();
        let callback = egui::PaintCallback {
            rect,
            callback: Arc::new(eframe::egui_glow::CallbackFn::new(move |info, painter| {
                let v = info.viewport_in_pixels();
                let clip = [v.left_px, v.from_bottom_px, v.width_px, v.height_px];
                scene.lock().unwrap_or_else(PoisonError::into_inner).paint(painter.gl(), clip, &mvp, yaw, &billboards);
            })),
        };
        ui.painter().rect_filled(rect, 0.0, Color32::from_rgb(30, 33, 40));
        ui.painter().add(callback);
    }
}
