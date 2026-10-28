// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The map view (tools/mapeditor/mapeditor/canvas.py): layout cells drawn top-down
//! (terrain, behavior colors, collision, grid), props as markers, events as boxes or
//! their overworld sprites. Scene units are pixels at zoom 1: a tile is TILE pixels,
//! a cell 512, and a sprite texel one pixel (a 32x32 NPC is two tiles wide).
//!
//! The view never changes events while dragging them: it draws them offset and
//! reports the move when the mouse is released, so a refused move needs no undoing.
//! Brush strokes do paint as they go (like the Python editor) and are reported whole.

use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::sync::Arc;

use egui::{Align2, Color32, CornerRadius, FontId, Pos2, Rect, Sense, Stroke, StrokeKind, Vec2};
use gen4map_format::permissions::Tile;
use gen4map_format::CELL;
use gen4map_nitro::Image;
use serde_json::Value;

use crate::doc::MapDoc;
use crate::sprites::{facing_index, pose, SpriteImages};
use crate::terrain::{CellKey, TerrainCache};

pub const TILE: f32 = 16.0;
const CELL_PX: f32 = CELL as f32 * TILE;
pub const ANIMATION_MS: u64 = 150; // one animation tick: a walk-cycle frame
/// Drawing order: later sections are on top (and hit first).
pub const DRAW_ORDER: [&str; 4] = ["coord_events", "bg_events", "warp_events", "object_events"];

pub fn event_color(section: &str) -> Color32 {
    match section {
        "object_events" => Color32::from_rgb(40, 120, 230),
        "warp_events" => Color32::from_rgb(200, 40, 200),
        "coord_events" => Color32::from_rgb(40, 170, 70),
        _ => Color32::from_rgb(230, 170, 20),
    }
}

pub fn event_label(section: &str) -> &'static str {
    match section {
        "object_events" => "O",
        "warp_events" => "W",
        "coord_events" => "T",
        _ => "S",
    }
}

fn crc32(data: &[u8]) -> u32 {
    let mut crc = 0xFFFF_FFFFu32;
    for &b in data {
        crc ^= b as u32;
        for _ in 0..8 {
            crc = if crc & 1 != 0 { (crc >> 1) ^ 0xEDB8_8320 } else { crc >> 1 };
        }
    }
    !crc
}

fn hsv(h: f32, s: f32, v: f32) -> Color32 {
    // colorsys.hsv_to_rgb
    let i = (h * 6.0).floor();
    let f = h * 6.0 - i;
    let (p, q, t) = (v * (1.0 - s), v * (1.0 - s * f), v * (1.0 - s * (1.0 - f)));
    let (r, g, b) = match i as i32 % 6 {
        0 => (v, t, p),
        1 => (q, v, p),
        2 => (p, v, t),
        3 => (p, q, v),
        4 => (t, p, v),
        _ => (v, p, q),
    };
    Color32::from_rgb((r * 255.0) as u8, (g * 255.0) as u8, (b * 255.0) as u8)
}

/// Colors for behaviors that matter most when reading a map; the rest get a stable hashed color.
pub fn behavior_color(b: u8) -> Color32 {
    match b {
        0x00 => Color32::from_rgb(236, 236, 228), // normal ground
        0x02 => Color32::from_rgb(96, 176, 72),   // tall grass
        0x03 => Color32::from_rgb(56, 136, 48),   // very tall grass
        0x06 => Color32::from_rgb(150, 120, 80),  // headbutt tree
        0x08 => Color32::from_rgb(170, 150, 120), // cave floor
        0x10 => Color32::from_rgb(90, 140, 220),  // river
        0x15 => Color32::from_rgb(60, 110, 210),  // sea
        0x11 => Color32::from_rgb(40, 60, 160),   // whirlpool
        0x13 => Color32::from_rgb(120, 170, 255), // waterfall
        0x16 => Color32::from_rgb(150, 190, 230), // puddle
        0x17 => Color32::from_rgb(170, 210, 235), // shallow water
        0x20 => Color32::from_rgb(200, 240, 250), // ice
        0x21 => Color32::from_rgb(230, 210, 150), // sand
        0xFF => Color32::from_rgb(60, 60, 60),    // none
        b => hsv((crc32(&[b]) % 360) as f32 / 360.0, 0.45, 0.92),
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Tool {
    Select,
    Collision,
    Behavior,
}

/// View layers: (key, label, default).
pub const LAYERS: [(&str, &str, bool); 9] = [
    ("terrain", "Terrain (3D)", true),
    ("behavior", "Behavior colors", false),
    ("collision", "Collision", true),
    ("grid", "Grid", true),
    ("props", "Prop markers", false),
    ("events", "Events", true),
    ("sprites", "Sprites", true),
    ("animate", "Animate sprites", true),
    ("cells", "Cell labels", false),
];

pub type EventRef = (String, usize);
pub type Move = (String, usize, (i64, i64), (i64, i64));

enum Drag {
    Events { start: (i64, i64), now: (i64, i64), origins: Vec<(String, usize, (i64, i64))> },
    Band { start: Pos2, now: Pos2, add: bool },
    Stroke { open: bool, tiles: BTreeMap<(i64, i64), (Tile, Tile)>, last: (i64, i64) },
    Pan,
}

/// What happened in the view this frame, for the window to act on.
#[derive(Debug)]
pub enum Action {
    Stroke(BTreeMap<(i64, i64), (Tile, Tile)>),
    Moved(Vec<Move>),
    Picked(u8),
    SelectionChanged,
}

pub struct MapView {
    pub zoom: f32,
    /// Scene point at the view's top-left corner.
    pub offset: Vec2,
    pub layers: BTreeMap<String, bool>,
    pub tool: Tool,
    pub brush_behavior: u8,
    pub brush_size: usize,
    pub selection: BTreeSet<EventRef>,
    pub hovered: Option<(i64, i64)>,
    /// Tile of the last right click (for the context menu).
    pub context_tile: Option<(i64, i64)>,
    pub tick: u64,
    drag: Option<Drag>,
    center_on_show: bool,
    viewport: Rect,
    tile_images: HashMap<u16, (egui::TextureHandle, egui::TextureHandle)>,
    sprite_textures: HashMap<(String, usize, usize), Option<egui::TextureHandle>>,
    start: std::time::Instant,
}

impl Default for MapView {
    fn default() -> Self {
        MapView {
            zoom: 1.0,
            offset: Vec2::ZERO,
            layers: LAYERS.iter().map(|&(k, _, on)| (k.to_string(), on)).collect(),
            tool: Tool::Select,
            brush_behavior: 0,
            brush_size: 1,
            selection: BTreeSet::new(),
            hovered: None,
            context_tile: None,
            tick: 0,
            drag: None,
            center_on_show: true,
            viewport: Rect::NOTHING,
            tile_images: HashMap::new(),
            sprite_textures: HashMap::new(),
            start: std::time::Instant::now(),
        }
    }
}

/// An object's sprite picture as a texture, shared by the 2D and 3D views.
pub fn sprite_texture(
    cache: &mut HashMap<(String, usize, usize), Option<egui::TextureHandle>>,
    sprites: &mut SpriteImages,
    ctx: &egui::Context,
    graphics_id: &str,
    facing: usize,
    step: usize,
) -> Option<egui::TextureHandle> {
    let key = (graphics_id.to_string(), facing, step);
    if let Some(t) = cache.get(&key) {
        return t.clone();
    }
    let tex = sprites.image(graphics_id, facing, step).map(|img: Arc<Image>| {
        let color = egui::ColorImage::from_rgba_unmultiplied([img.width, img.height], &img.rgba);
        ctx.load_texture(format!("sprite {} {} {}", graphics_id, facing, step), color, egui::TextureOptions::NEAREST)
    });
    cache.insert(key, tex.clone());
    tex
}

impl MapView {
    pub fn layer(&self, key: &str) -> bool {
        self.layers.get(key).copied().unwrap_or(false)
    }

    /// A new map: forget per-map state, centre on it when next shown.
    pub fn reset(&mut self, keep_view: bool) {
        self.selection.clear();
        self.drag = None;
        self.hovered = None;
        self.tile_images.clear();
        if !keep_view {
            self.center_on_show = true;
        }
    }

    /// Rebuild the behavior and collision pictures of land data (after edits to it).
    pub fn refresh_land(&mut self, numbers: impl IntoIterator<Item = u16>) {
        for n in numbers {
            self.tile_images.remove(&n);
        }
    }

    pub fn refresh_all_tiles(&mut self) {
        self.tile_images.clear();
    }

    pub fn zoom_by(&mut self, factor: f32, anchor: Option<Pos2>) {
        let new = (self.zoom * factor).clamp(0.05, 8.0);
        let anchor = anchor.unwrap_or(self.viewport.center());
        let scene = self.to_scene(anchor);
        self.zoom = new;
        self.offset = scene.to_vec2() - (anchor - self.viewport.min) / self.zoom;
    }

    fn to_screen(&self, scene: Pos2) -> Pos2 {
        self.viewport.min + (scene.to_vec2() - self.offset) * self.zoom
    }

    fn to_scene(&self, screen: Pos2) -> Pos2 {
        ((screen - self.viewport.min) / self.zoom + self.offset).to_pos2()
    }

    fn tile_at(&self, screen: Pos2) -> (i64, i64) {
        let s = self.to_scene(screen);
        ((s.x / TILE).floor() as i64, (s.y / TILE).floor() as i64)
    }

    fn tile_rect(&self, x: f32, y: f32, w: f32, h: f32) -> Rect {
        Rect::from_min_max(self.to_screen(Pos2::new(x * TILE, y * TILE)), self.to_screen(Pos2::new((x + w) * TILE, (y + h) * TILE)))
    }

    pub fn center_on(&mut self, scene: Pos2) {
        self.offset = scene.to_vec2() - self.viewport.size() / (2.0 * self.zoom);
    }

    /// Scroll so an event is in view.
    pub fn ensure_visible(&mut self, x: i64, y: i64) {
        let r = self.tile_rect(x as f32, y as f32, 1.0, 1.0);
        if !self.viewport.contains_rect(r) {
            self.center_on(Pos2::new((x as f32 + 0.5) * TILE, (y as f32 + 0.5) * TILE));
        }
    }

    /// The single selected event, if exactly one is.
    pub fn selected_event(&self) -> Option<EventRef> {
        (self.selection.len() == 1).then(|| self.selection.iter().next().unwrap().clone())
    }

    fn event_size(section: &str, ev: &Value) -> (i64, i64) {
        if section == "coord_events" {
            let g = |k: &str| ev.get(k).and_then(Value::as_i64).unwrap_or(1).max(1);
            (g("width"), g("height"))
        } else {
            (1, 1)
        }
    }

    /// The topmost event whose tiles include x, y.
    fn event_at(&self, doc: &MapDoc, x: i64, y: i64) -> Option<EventRef> {
        for section in DRAW_ORDER.iter().rev() {
            for (i, ev) in doc.events(section).iter().enumerate().rev() {
                let (Some(ex), Some(ey)) = (ev.get("x").and_then(Value::as_i64), ev.get("y").and_then(Value::as_i64)) else { continue };
                let (w, h) = Self::event_size(section, ev);
                if (ex..ex + w).contains(&x) && (ey..ey + h).contains(&y) {
                    return Some((section.to_string(), i));
                }
            }
        }
        None
    }

    fn brush_tiles(&self, x: i64, y: i64) -> Vec<(i64, i64)> {
        let n = self.brush_size as i64;
        let r = n / 2;
        (-r..n - r).flat_map(|dy| (-r..n - r).map(move |dx| (x + dx, y + dy))).collect()
    }

    /// Paint the brush at a tile, recording old and new values in the stroke.
    fn paint_at(&mut self, doc: &mut MapDoc, x: i64, y: i64) -> Vec<u16> {
        let Some(Drag::Stroke { open, tiles, .. }) = &mut self.drag else { return Vec::new() };
        let open = *open;
        let mut lands = Vec::new();
        let n = self.brush_size as i64;
        let r = n / 2;
        for (tx, ty) in (-r..n - r).flat_map(|dy| (-r..n - r).map(move |dx| (x + dx, y + dy))) {
            // neighbouring cells belong to other maps
            let Some(cur) = doc.tile(tx, ty).filter(|_| doc.on_map(tx, ty)) else { continue };
            let new = match self.tool {
                Tool::Collision => ((!open) as u8, cur.1, cur.2),
                _ => (cur.0, self.brush_behavior, cur.2),
            };
            if new != cur {
                let old = tiles.get(&(tx, ty)).map(|t| t.0).unwrap_or(cur);
                tiles.insert((tx, ty), (old, new));
                doc.set_tile(tx, ty, new);
                lands.extend(doc.cell_land(tx as usize / CELL, ty as usize / CELL));
            }
        }
        lands
    }

    fn tile_images(&mut self, ctx: &egui::Context, doc: &MapDoc, cx: usize, cy: usize) -> Option<(egui::TextureId, egui::TextureId)> {
        let chunk = doc.chunk(cx, cy)?;
        if !self.tile_images.contains_key(&chunk.number) {
            let mut beh = egui::ColorImage::filled([CELL, CELL], Color32::BLACK);
            let mut col = egui::ColorImage::filled([CELL, CELL], Color32::TRANSPARENT);
            for ty in 0..CELL {
                for tx in 0..CELL {
                    let (c, b, _) = chunk.tile(tx, ty);
                    beh[(tx, ty)] = behavior_color(b);
                    if c != 0 {
                        col[(tx, ty)] = Color32::from_rgba_unmultiplied(220, 30, 30, 110);
                    }
                }
            }
            let opts = egui::TextureOptions::NEAREST;
            let n = chunk.number;
            self.tile_images.insert(
                n,
                (ctx.load_texture(format!("behavior {}", n), beh, opts), ctx.load_texture(format!("collision {}", n), col, opts)),
            );
        }
        self.tile_images.get(&chunk.number).map(|(b, c)| (b.id(), c.id()))
    }

    /// Draw the map and handle the mouse. Returns what the window has to act on, and the
    /// view's response (for its context menu).
    pub fn ui(
        &mut self,
        ui: &mut egui::Ui,
        doc: &mut MapDoc,
        terrain: &mut TerrainCache,
        sprites: &mut SpriteImages,
    ) -> (Vec<Action>, egui::Response) {
        let (rect, response) = ui.allocate_exact_size(ui.available_size(), Sense::click_and_drag());
        self.viewport = rect;
        let ctx = ui.ctx().clone();
        let mut actions = Vec::new();
        if self.center_on_show && rect.width() > 1.0 {
            let own = doc.own_cells();
            let cells = if own.is_empty() { doc.shown_cells() } else { own };
            let n = cells.len().max(1) as f32;
            let cx = cells.iter().map(|c| c.0 as f32).sum::<f32>() / n;
            let cy = cells.iter().map(|c| c.1 as f32).sum::<f32>() / n;
            self.center_on(Pos2::new((cx + 0.5) * CELL_PX, (cy + 0.5) * CELL_PX));
            self.center_on_show = false;
        }
        self.handle_input(ui, &response, doc, &mut actions);

        let painter = ui.painter_at(rect);
        painter.rect_filled(rect, CornerRadius::ZERO, Color32::from_rgb(40, 40, 46));
        let area = doc.area();
        let grid = self.layer("grid") && self.zoom * TILE >= 6.0;
        let mut shown = doc.shown_cells();
        // cells nearest the middle of the view are drawn first
        let mid = self.to_scene(rect.center());
        shown.sort_by_key(|&(cx, cy)| {
            let d = Pos2::new((cx as f32 + 0.5) * CELL_PX, (cy as f32 + 0.5) * CELL_PX) - mid;
            (d.length() as i64, cx, cy)
        });
        for &(cx, cy) in &shown {
            let r = self.tile_rect((cx * CELL) as f32, (cy * CELL) as f32, CELL as f32, CELL as f32);
            let visible = r.intersects(rect);
            let Some(chunk) = doc.chunk(cx, cy) else {
                if visible {
                    painter.rect_filled(r, CornerRadius::ZERO, Color32::from_rgb(90, 20, 20));
                    painter.text(r.center(), Align2::CENTER_CENTER, "land data unreadable", FontId::proportional(12.0), Color32::WHITE);
                }
                continue;
            };
            let uv = Rect::from_min_max(Pos2::ZERO, Pos2::new(1.0, 1.0));
            if self.layer("terrain") {
                // ask for every shown cell, those in view first
                let key = CellKey { land: chunk.number, area, altitude: doc.cell_altitude(cx, cy) };
                let tex = terrain.get(key, &chunk.props, visible).map(|t| t.id());
                if !visible {
                    continue;
                }
                painter.rect_filled(r, CornerRadius::ZERO, Color32::from_rgb(24, 24, 28));
                match tex {
                    Some(t) => {
                        painter.image(t, r, uv, Color32::WHITE);
                    }
                    None => {
                        painter.text(r.center(), Align2::CENTER_CENTER, "drawing...", FontId::proportional(12.0), Color32::GRAY);
                    }
                }
                if self.layer("behavior") {
                    if let Some((beh, _)) = self.tile_images(&ctx, doc, cx, cy) {
                        painter.image(beh, r, uv, Color32::from_white_alpha(128));
                    }
                }
            } else if !visible {
                continue;
            } else if self.layer("behavior") {
                if let Some((beh, _)) = self.tile_images(&ctx, doc, cx, cy) {
                    painter.image(beh, r, uv, Color32::WHITE);
                }
            } else {
                painter.rect_filled(r, CornerRadius::ZERO, Color32::from_rgb(236, 236, 228));
            }
            if self.layer("collision") {
                if let Some((_, col)) = self.tile_images(&ctx, doc, cx, cy) {
                    painter.image(col, r, uv, Color32::WHITE);
                }
            }
            if grid {
                let s = Stroke::new(1.0, Color32::from_black_alpha(40));
                for i in 1..CELL {
                    let f = i as f32 * TILE * self.zoom;
                    painter.line_segment([Pos2::new(r.min.x + f, r.min.y), Pos2::new(r.min.x + f, r.max.y)], s);
                    painter.line_segment([Pos2::new(r.min.x, r.min.y + f), Pos2::new(r.max.x, r.min.y + f)], s);
                }
            }
            if doc.cell_map(cx, cy) != doc.map.id {
                painter.rect_filled(r, CornerRadius::ZERO, Color32::from_black_alpha(110)); // another map's cell
            }
            painter.rect_stroke(r, CornerRadius::ZERO, Stroke::new(1.0, Color32::from_black_alpha(160)), StrokeKind::Inside);
            if self.layer("cells") {
                painter.text(
                    r.min + Vec2::new(4.0, 4.0),
                    Align2::LEFT_TOP,
                    format!("cell {},{}  land {:04}", cx, cy, chunk.number),
                    FontId::monospace(11.0),
                    Color32::BLACK,
                );
            }
        }
        terrain.poll(&ctx);

        if self.layer("props") {
            let shown_set: BTreeSet<(usize, usize)> = shown.iter().copied().collect();
            for (cx, cy, i, p, tx, ty) in doc.props() {
                if !shown_set.contains(&(cx, cy)) {
                    continue;
                }
                let c = self.to_screen(Pos2::new(tx as f32 * TILE, ty as f32 * TILE));
                let d = 5.0;
                let pts = vec![c + Vec2::new(0.0, -d), c + Vec2::new(d, 0.0), c + Vec2::new(0.0, d), c + Vec2::new(-d, 0.0)];
                painter.add(egui::Shape::convex_polygon(pts, Color32::from_rgba_unmultiplied(240, 200, 120, 200), Stroke::new(1.0, Color32::from_rgb(90, 60, 20))));
                if response.hover_pos().is_some_and(|h| (h - c).length() < d) {
                    response.clone().on_hover_text(format!(
                        "prop {} in cell {},{}: model {}\nposition {:?}\nrotation {:?}\nscale {:?}",
                        i, cx, cy, p.model, p.position, p.rotation, p.scale
                    ));
                }
            }
        }

        if self.layer("events") {
            self.draw_events(ui, &painter, &response, doc, sprites);
        }
        if let Some(Drag::Band { start, now, .. }) = &self.drag {
            let r = Rect::from_two_pos(*start, *now);
            painter.rect_filled(r, CornerRadius::ZERO, Color32::from_rgba_unmultiplied(80, 140, 255, 40));
            painter.rect_stroke(r, CornerRadius::ZERO, Stroke::new(1.0, Color32::from_rgb(80, 140, 255)), StrokeKind::Inside);
        }
        (actions, response)
    }

    fn draw_events(&mut self, ui: &egui::Ui, painter: &egui::Painter, response: &egui::Response, doc: &MapDoc, sprites: &mut SpriteImages) {
        let ctx = ui.ctx().clone();
        let offset = match &self.drag {
            Some(Drag::Events { start, now, .. }) => (now.0 - start.0, now.1 - start.1),
            _ => (0, 0),
        };
        let animate = self.layer("animate");
        let mut any_sprite = false;
        let hover_tile = response.hover_pos().map(|p| self.tile_at(p));
        let mut tooltip = None;
        // objects further south are drawn over those north of them, as in the game
        let mut objects: Vec<(usize, &Value)> = doc.events("object_events").iter().enumerate().collect();
        objects.sort_by_key(|(_, e)| e.get("y").and_then(Value::as_i64).unwrap_or(0));
        for section in DRAW_ORDER {
            let list: Vec<(usize, &Value)> =
                if section == "object_events" { objects.clone() } else { doc.events(section).iter().enumerate().collect() };
            for (i, ev) in list {
                let (Some(mut x), Some(mut y)) = (ev.get("x").and_then(Value::as_i64), ev.get("y").and_then(Value::as_i64)) else { continue };
                let selected = self.selection.contains(&(section.to_string(), i));
                if selected {
                    x += offset.0;
                    y += offset.1;
                }
                let (w, h) = Self::event_size(section, ev);
                let r = self.tile_rect(x as f32, y as f32, w as f32, h as f32);
                let color = event_color(section);
                let mut note = None;
                let mut sprite = None;
                if section == "object_events" {
                    let g = ev.get("graphics_id").and_then(Value::as_str).unwrap_or("");
                    note = sprites.why_not(g);
                    if note.is_none() && self.layer("sprites") {
                        let facing = facing_index(ev.get("facing_dir").unwrap_or(&Value::Null));
                        let (facing, step) = if animate {
                            let mt = ev.get("movement_type").and_then(Value::as_str).unwrap_or("");
                            pose(mt, facing, sprites.frames(g), self.tick)
                        } else {
                            (facing, 0)
                        };
                        sprite = sprite_texture(&mut self.sprite_textures, sprites, &ctx, g, facing, step);
                    }
                }
                if r.intersects(self.viewport.expand(64.0 * self.zoom)) {
                    match &sprite {
                        Some(tex) => {
                            any_sprite = true;
                            let [sw, sh] = tex.size();
                            // centred on the tile, its bottom on the tile's bottom
                            let min = Pos2::new(x as f32 * TILE + (TILE - sw as f32) / 2.0, (y + 1) as f32 * TILE - sh as f32);
                            let sr = Rect::from_min_max(self.to_screen(min), self.to_screen(min + Vec2::new(sw as f32, sh as f32)));
                            painter.image(tex.id(), sr, Rect::from_min_max(Pos2::ZERO, Pos2::new(1.0, 1.0)), Color32::WHITE);
                            let stroke = if selected { Stroke::new(2.0, Color32::YELLOW) } else { Stroke::new(1.0, color.gamma_multiply(0.63)) };
                            painter.rect_stroke(r, CornerRadius::ZERO, stroke, StrokeKind::Inside);
                        }
                        None => {
                            let fill = color.gamma_multiply(if section == "coord_events" { 0.35 } else { 0.78 });
                            painter.rect_filled(r, CornerRadius::ZERO, fill);
                            let stroke = if selected {
                                Stroke::new(2.0, Color32::YELLOW)
                            } else {
                                let darker = |c: u8| (c as u16 * 2 / 3) as u8; // u16: 230 * 2 overflows u8
                                Stroke::new(1.0, Color32::from_rgb(darker(color.r()), darker(color.g()), darker(color.b())))
                            };
                            painter.rect_stroke(r, CornerRadius::ZERO, stroke, StrokeKind::Inside);
                            let mut label = event_label(section);
                            if let Some(n) = &note {
                                label = if n.starts_with("set when") { "V" } else { "?" };
                            }
                            if self.zoom * TILE >= 8.0 {
                                let first = self.tile_rect(x as f32, y as f32, 1.0, 1.0);
                                painter.text(first.center(), Align2::CENTER_CENTER, label, FontId::proportional((7.0 * self.zoom).clamp(6.0, 30.0)), Color32::WHITE);
                            }
                        }
                    }
                }
                if hover_tile.is_some_and(|(hx, hy)| (x..x + w).contains(&hx) && (y..y + h).contains(&hy)) {
                    tooltip = Some(describe(section, i, ev, note.as_deref()));
                }
            }
        }
        if let Some(t) = tooltip {
            if self.drag.is_none() {
                response.clone().on_hover_text(t);
            }
        }
        if animate && any_sprite {
            self.tick = self.start.elapsed().as_millis() as u64 / ANIMATION_MS;
            ui.ctx().request_repaint_after(std::time::Duration::from_millis(ANIMATION_MS));
        }
    }

    fn handle_input(&mut self, ui: &egui::Ui, response: &egui::Response, doc: &mut MapDoc, actions: &mut Vec<Action>) {
        use egui::PointerButton::*;
        let (pointer, modifiers, scroll) = ui.input(|i| (i.pointer.clone(), i.modifiers, i.smooth_scroll_delta.y));
        let pos = pointer.latest_pos();
        let over = response.hovered() || response.contains_pointer();
        self.hovered = pos.filter(|p| self.viewport.contains(*p)).map(|p| self.tile_at(p));

        if over && scroll != 0.0 && self.drag.is_none() {
            self.zoom_by(1.25f32.powf(scroll / 50.0), pos);
        }
        let pressed = |b| over && pointer.button_pressed(b);
        // middle button pans in every tool
        if pressed(Middle) {
            self.drag = Some(Drag::Pan);
        }
        if let (Some(Drag::Pan), true) = (&self.drag, pointer.button_down(Middle)) {
            self.offset -= pointer.delta() / self.zoom;
            return;
        }
        if matches!(self.drag, Some(Drag::Pan)) {
            self.drag = None;
        }

        match self.tool {
            Tool::Select => {
                if pressed(Primary) {
                    let p = pos.unwrap_or_default();
                    let t = self.tile_at(p);
                    match self.event_at(doc, t.0, t.1) {
                        Some(ev) => {
                            let toggle = modifiers.shift || modifiers.command;
                            if toggle {
                                if !self.selection.remove(&ev) {
                                    self.selection.insert(ev);
                                }
                            } else if !self.selection.contains(&ev) {
                                self.selection = [ev].into();
                            }
                            actions.push(Action::SelectionChanged);
                            let origins = self.selection.iter().filter_map(|(s, i)| Some((s.clone(), *i, doc.event_xy(s, *i)?))).collect();
                            self.drag = Some(Drag::Events { start: t, now: t, origins });
                        }
                        None => {
                            let add = modifiers.shift || modifiers.command;
                            if !add && !self.selection.is_empty() {
                                self.selection.clear();
                                actions.push(Action::SelectionChanged);
                            }
                            self.drag = Some(Drag::Band { start: p, now: p, add });
                        }
                    }
                }
                if pressed(Secondary) {
                    let t = self.tile_at(pos.unwrap_or_default());
                    self.context_tile = Some(t);
                    if let Some(ev) = self.event_at(doc, t.0, t.1) {
                        if !self.selection.contains(&ev) {
                            self.selection = [ev].into();
                            actions.push(Action::SelectionChanged);
                        }
                    }
                }
                let down = pointer.button_down(Primary);
                let ptile = pos.map(|p| self.tile_at(p));
                match &mut self.drag {
                    Some(Drag::Events { now, .. }) if down => {
                        if let Some(t) = ptile {
                            *now = t;
                        }
                    }
                    Some(Drag::Band { now, .. }) if down => {
                        if let Some(p) = pos {
                            *now = p;
                        }
                    }
                    Some(Drag::Events { .. } | Drag::Band { .. }) => match self.drag.take() {
                        Some(Drag::Events { start, now, origins }) => {
                            let (dx, dy) = (now.0 - start.0, now.1 - start.1);
                            let moves: Vec<Move> = origins
                                .into_iter()
                                .filter(|_| (dx, dy) != (0, 0))
                                .map(|(s, i, o)| (s, i, o, (o.0 + dx, o.1 + dy)))
                                .collect();
                            if !moves.is_empty() {
                                actions.push(Action::Moved(moves));
                            }
                        }
                        Some(Drag::Band { start, now, add }) => {
                            let band = Rect::from_two_pos(self.to_scene(start), self.to_scene(now));
                            if !add {
                                self.selection.clear();
                            }
                            for section in DRAW_ORDER {
                                for (i, ev) in doc.events(section).iter().enumerate() {
                                    let (Some(x), Some(y)) = (ev.get("x").and_then(Value::as_i64), ev.get("y").and_then(Value::as_i64)) else { continue };
                                    let (w, h) = Self::event_size(section, ev);
                                    let r = Rect::from_min_size(Pos2::new(x as f32 * TILE, y as f32 * TILE), Vec2::new(w as f32 * TILE, h as f32 * TILE));
                                    if band.width() > 2.0 && band.intersects(r) {
                                        self.selection.insert((section.to_string(), i));
                                    }
                                }
                            }
                            actions.push(Action::SelectionChanged);
                        }
                        _ => {}
                    },
                    _ => {}
                }
            }
            Tool::Collision | Tool::Behavior => {
                if self.tool == Tool::Behavior && pressed(Secondary) {
                    if let Some(t) = pos.and_then(|p| {
                        let (x, y) = self.tile_at(p);
                        doc.tile(x, y)
                    }) {
                        actions.push(Action::Picked(t.1));
                    }
                    return;
                }
                if pressed(Primary) || (self.tool == Tool::Collision && pressed(Secondary)) {
                    let t = self.tile_at(pos.unwrap_or_default());
                    self.drag = Some(Drag::Stroke { open: pressed(Secondary), tiles: BTreeMap::new(), last: t });
                    let lands = self.paint_at(doc, t.0, t.1);
                    self.refresh_land(lands);
                }
                if let Some(Drag::Stroke { last, .. }) = &self.drag {
                    let last = *last;
                    if pointer.button_down(Primary) || pointer.button_down(Secondary) {
                        if let Some(p) = pos {
                            let t = self.tile_at(p);
                            // every tile between the last position and this one: fast strokes leave no gaps
                            let steps = (t.0 - last.0).abs().max((t.1 - last.1).abs()).max(1);
                            let mut lands = Vec::new();
                            for k in 1..=steps {
                                let x = last.0 + (t.0 - last.0) * k / steps;
                                let y = last.1 + (t.1 - last.1) * k / steps;
                                lands.extend(self.paint_at(doc, x, y));
                            }
                            self.refresh_land(lands);
                            if let Some(Drag::Stroke { last, .. }) = &mut self.drag {
                                *last = t;
                            }
                        }
                    } else if let Some(Drag::Stroke { tiles, .. }) = self.drag.take() {
                        if !tiles.is_empty() {
                            actions.push(Action::Stroke(tiles));
                        }
                    }
                }
            }
        }
    }

    /// Paint brush outline under the mouse (call after ui()).
    pub fn draw_brush(&self, ui: &egui::Ui) {
        if self.tool == Tool::Select {
            return;
        }
        if let Some((x, y)) = self.hovered {
            let painter = ui.painter_at(self.viewport);
            for (tx, ty) in self.brush_tiles(x, y) {
                let r = self.tile_rect(tx as f32, ty as f32, 1.0, 1.0);
                painter.rect_stroke(r, CornerRadius::ZERO, Stroke::new(1.0, Color32::from_white_alpha(180)), StrokeKind::Inside);
            }
        }
    }

    /// Unused stroke data (a stroke in progress) is dropped when the map changes.
    pub fn stroke_in_progress(&self) -> bool {
        matches!(self.drag, Some(Drag::Stroke { .. }))
    }
}

/// The text shown when hovering an event.
pub fn describe(section: &str, index: usize, e: &Value, note: Option<&str>) -> String {
    let s = |k: &str| match e.get(k) {
        Some(Value::String(v)) => v.clone(),
        Some(v) => v.to_string(),
        None => "None".into(),
    };
    let name = match section {
        "object_events" => format!("{}  {}", s("local_id"), s("graphics_id")),
        "warp_events" => format!("warp {} -> {}:{}", index, s("dest_map"), s("dest_warp_id")),
        "coord_events" => format!("trigger {} == {}", s("var"), s("var_value")),
        _ => s("type"),
    };
    let mut text = format!("{}  ({}, {}, elevation {})\nscript: {}", name, s("x"), s("y"), s("elevation"), s("script"));
    if let Some(n) = note {
        text += &format!("\nsprite not shown: {}", n);
    }
    text
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn colors() {
        assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
        assert_eq!(behavior_color(2), Color32::from_rgb(96, 176, 72));
        // the hashed colors are the Python editor's (colorsys, zlib.crc32)
        assert_eq!(behavior_color(0x5A), hsv((crc32(&[0x5A]) % 360) as f32 / 360.0, 0.45, 0.92));
    }
}
