// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The main window (tools/mapeditor/mapeditor/window.py): map list | map view |
//! properties (event, header, tiles), with the menus, toolbar and dialogs.
//!
//! Every edit goes through the undo stack, which alone says whether there is
//! anything to save. Nothing here can close the editor on bad data: a map that fails
//! to open leaves the current one open and says why.

use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use egui::{Color32, Key, KeyboardShortcut, Modifiers};
use gen4map_format::constants::Constants;
use gen4map_format::project::Project;
use gen4map_format::CELL;
use gen4map_render::{Renderer, Sources};
use serde_json::Value;

use crate::canvas::{self, behavior_color, Action, MapView, Tool, LAYERS};
use crate::commands::{Change, Command, UndoStack};
use crate::doc::{self, MapDoc, SaveError};
use crate::external;
use crate::forms::{self, FieldForm};
use crate::settings::Settings;
use crate::sprites::{facing_index, SpriteImages};
use crate::terrain::TerrainCache;
use crate::view3d::View3D;

const READ_ONLY: [(&str, &str); 1] = [("layout", "the layout can't be changed while the map is open: edit map.json and reopen")];

fn section_name(section: &str) -> &'static str {
    match section {
        "object_events" => "Object",
        "warp_events" => "Warp",
        "coord_events" => "Trigger",
        _ => "Sign/BG",
    }
}

const SAVE: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::S);
const UNDO: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::Z);
const REDO: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND.plus(Modifiers::SHIFT), Key::Z);
const REDO_Y: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::Y);
const RELOAD: KeyboardShortcut = KeyboardShortcut::new(Modifiers::NONE, Key::F5);
const OPEN_SCRIPT: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::E);
const OPEN_EVENT: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND.plus(Modifiers::SHIFT), Key::E);
const QUIT: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::Q);
const ZOOM_IN: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::Equals);
const ZOOM_IN_PLUS: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::Plus);
const ZOOM_OUT: KeyboardShortcut = KeyboardShortcut::new(Modifiers::COMMAND, Key::Minus);

/// What to do once unsaved changes are saved or discarded.
#[derive(Debug, Clone)]
enum After {
    Open(String),
    Reload,
    Quit,
}

enum Dialog {
    Unsaved(After),
    ChangedOnDisk(Vec<String>, Option<After>),
    Message(String, String),
    ChooseEditor { command: String, then: Option<(PathBuf, usize)> },
}

#[derive(PartialEq, Eq, Clone, Copy)]
enum Tab {
    Event,
    Header,
    Tiles,
}

#[derive(PartialEq, Eq, Clone, Copy)]
enum Center {
    Map,
    View3D,
}

pub struct EditorApp {
    project: Project,
    constants: Constants,
    behaviors: BTreeMap<u8, String>,
    maps: Vec<(String, String, u16)>,
    doc: Option<MapDoc>,
    undo: UndoStack,
    view: MapView,
    view3d: View3D,
    center: Center,
    terrain: TerrainCache,
    sprites: SpriteImages,
    sprite_icons: HashMap<(String, usize, usize), Option<egui::TextureHandle>>,
    land_index: Option<HashMap<u16, BTreeSet<String>>>,
    settings: Settings,
    map_filter: String,
    behavior_filter: String,
    tab: Tab,
    event_form: FieldForm,
    header_form: FieldForm,
    status: String,
    flash: Option<(String, Instant, Duration)>,
    dialog: Option<Dialog>,
    allow_close: bool,
    last_watch: Instant,
    title: String,
    /// MAPEDITOR_RS_SCREENSHOT=file.png: save the window to the file once every cell is
    /// drawn, then quit (for checking the editor's look from scripts).
    screenshot: Option<(PathBuf, u32)>,
}

impl EditorApp {
    pub fn new(cc: &eframe::CreationContext<'_>, project: Project, start_map: Option<String>, in_3d: bool) -> EditorApp {
        let game = project.manifest.game.versions.first().cloned().unwrap_or_else(|| "HEARTGOLD".into());
        let (constants, constants_error) = match Constants::export(&project.root, &game) {
            Ok(c) => (c, None),
            Err(e) => (Constants::default(), Some(e.0)),
        };
        let mut settings = Settings::load();
        let mut view = MapView::default();
        for (k, on) in &settings.layers {
            if view.layers.contains_key(k) {
                view.layers.insert(k.clone(), *on);
            }
        }
        settings.layers = view.layers.clone();
        let renderer = Renderer::new(Sources::from_manifest(&project.root, &project.manifest));
        let mut app = EditorApp {
            behaviors: constants.behavior_names(),
            maps: doc::map_list(&project),
            sprites: SpriteImages::new(project.root.clone(), constants.sprites.clone(), constants_error.clone()),
            terrain: TerrainCache::new(renderer, cc.egui_ctx.clone()),
            constants,
            project,
            doc: None,
            undo: UndoStack::new(),
            view,
            view3d: View3D::new(cc.gl.clone()),
            center: Center::Map,
            sprite_icons: HashMap::new(),
            land_index: None,
            settings,
            map_filter: String::new(),
            behavior_filter: String::new(),
            tab: Tab::Event,
            event_form: FieldForm::default(),
            header_form: FieldForm::default(),
            status: String::new(),
            flash: None,
            dialog: None,
            allow_close: false,
            last_watch: Instant::now(),
            title: String::new(),
            screenshot: std::env::var_os("MAPEDITOR_RS_SCREENSHOT").map(|p| (PathBuf::from(p), 0)),
        };
        if let Some(e) = constants_error {
            app.dialog = Some(Dialog::Message(
                "Constants not loaded".into(),
                format!("{}\n\nThe editor works without them, but fields can't complete or check constant names, and sprites and behavior names aren't shown.", e),
            ));
        }
        if let Some(m) = start_map {
            app.open_map(&m, false, false);
        }
        if in_3d {
            app.center = Center::View3D;
        }
        app
    }

    fn flash(&mut self, text: impl Into<String>, secs: u64) {
        self.flash = Some((text.into(), Instant::now(), Duration::from_secs(secs)));
    }

    fn land_users(&mut self, number: u16) -> Vec<String> {
        let project = &self.project;
        let index = self.land_index.get_or_insert_with(|| project.land_index());
        index.get(&number).map(|s| s.iter().cloned().collect()).unwrap_or_default()
    }

    // --- opening and saving ------------------------------------------------------------------

    fn request(&mut self, after: After) {
        if self.doc.is_some() && !self.undo.is_clean() {
            self.dialog = Some(Dialog::Unsaved(after));
        } else {
            self.proceed(after);
        }
    }

    fn proceed(&mut self, after: After) {
        match after {
            After::Open(folder) => self.open_map(&folder, false, false),
            After::Reload => {
                if let Some(f) = self.doc.as_ref().map(|d| d.folder.clone()) {
                    self.open_map(&f, true, true);
                }
            }
            After::Quit => self.allow_close = true,
        }
    }

    fn open_map(&mut self, folder: &str, force: bool, keep_view: bool) {
        if !force && self.doc.as_ref().is_some_and(|d| d.folder == folder) {
            return;
        }
        match MapDoc::open(&self.project, folder) {
            Ok(doc) => {
                let (x0, y0, x1, y1) = doc.bounds();
                self.status = format!("{}: layout {}, cells {},{} to {},{}", doc.map.name, doc.layout_name, x0, y0, x1, y1);
                if !doc.chunk_errors.is_empty() {
                    let lines: Vec<String> = doc.chunk_errors.iter().map(|(n, e)| format!("{:04}: {}", n, e)).collect();
                    self.dialog = Some(Dialog::Message("Some land data couldn't be read".into(), lines.join("\n")));
                }
                self.doc = Some(doc);
                self.undo.clear();
                self.view.reset(keep_view);
                self.view3d.invalidate();
            }
            Err(e) => self.dialog = Some(Dialog::Message(format!("Can't open {}", folder), e)),
        }
    }

    /// True if everything was written.
    fn save(&mut self, force: bool) -> bool {
        let Some(doc) = self.doc.as_mut() else { return true };
        match doc.save(&self.project, force) {
            Ok(()) => {
                self.undo.set_clean();
                let f = doc.folder.clone();
                self.flash(format!("Saved {}", f), 3);
                true
            }
            Err(SaveError::ChangedOnDisk(paths)) => {
                self.dialog = Some(Dialog::ChangedOnDisk(paths, None));
                false
            }
            Err(SaveError::Failed(e)) => {
                self.dialog = Some(Dialog::Message("Save failed".into(), e));
                false
            }
        }
    }

    /// map.json changed outside the editor: reload when there's nothing unsaved, else warn.
    fn watch(&mut self) {
        if self.last_watch.elapsed() < Duration::from_secs(1) {
            return;
        }
        self.last_watch = Instant::now();
        let Some(doc) = &self.doc else { return };
        if !doc.map_json.exists() || !doc.map_json_changed_outside() {
            return;
        }
        if self.undo.is_clean() {
            let f = doc.folder.clone();
            self.open_map(&f, true, true);
            self.flash("map.json changed outside the editor: reloaded", 5);
        } else if self.flash.as_ref().is_none_or(|f| !f.0.starts_with("map.json changed")) {
            self.flash("map.json changed outside the editor; you have unsaved edits (saving will ask, File > Reload map takes theirs)", 10);
        }
    }

    // --- edits ---------------------------------------------------------------------------

    fn apply(&mut self, change: Change) {
        let Some(doc) = &self.doc else { return };
        match change {
            Change::Tiles(tiles) => {
                let lands: BTreeSet<u16> = tiles.iter().filter_map(|&(x, y)| doc.cell_land(x as usize / CELL, y as usize / CELL)).collect();
                self.view.refresh_land(lands);
            }
            Change::Events(sel) => {
                match sel {
                    Some((s, i)) if doc.event(&s, i).is_some() => {
                        if let Some((x, y)) = doc.event_xy(&s, i) {
                            self.view.ensure_visible(x, y);
                        }
                        self.view.selection = [(s, i)].into();
                    }
                    _ => self.view.selection.retain(|(s, i)| doc.event(s, *i).is_some()),
                }
                self.tab = Tab::Event;
            }
            Change::Header(key) => {
                if key == "area_data" {
                    // every cell is drawn with the map's area
                    self.view3d.invalidate();
                }
            }
        }
    }

    fn push(&mut self, cmd: Command) {
        if let Some(doc) = self.doc.as_mut() {
            let c = self.undo.push(cmd, doc, false);
            self.apply(c);
        }
    }

    fn undo(&mut self) {
        if let Some(c) = self.doc.as_mut().and_then(|d| self.undo.undo(d)) {
            self.apply(c);
        }
    }

    fn redo(&mut self) {
        if let Some(c) = self.doc.as_mut().and_then(|d| self.undo.redo(d)) {
            self.apply(c);
        }
    }

    fn stroke(&mut self, tiles: BTreeMap<(i64, i64), (gen4map_format::permissions::Tile, gen4map_format::permissions::Tile)>) {
        let Some(doc) = self.doc.as_mut() else { return };
        let name = if self.view.tool == Tool::Collision { "Paint collision" } else { "Paint behavior" };
        let lands: BTreeSet<u16> = tiles.keys().filter_map(|&(x, y)| doc.cell_land(x as usize / CELL, y as usize / CELL)).collect();
        let c = self.undo.push(Command::PaintTiles { name: name.into(), tiles }, doc, true);
        self.apply(c);
        let shared: Vec<(u16, Vec<String>)> = lands.into_iter().map(|n| (n, self.land_users(n))).filter(|(_, u)| u.len() > 1).collect();
        if !shared.is_empty() {
            let parts: Vec<String> = shared
                .iter()
                .map(|(n, users)| {
                    let names = users.iter().take(4).cloned().collect::<Vec<_>>().join(", ");
                    format!("{:04} in {} maps ({}{})", n, users.len(), names, if users.len() > 4 { ", ..." } else { "" })
                })
                .collect();
            self.flash(format!("Shared land data: this also changed {}", parts.join("; ")), 10);
        }
    }

    /// Moves from a drag; refused if any lands off the map.
    fn move_events(&mut self, moves: Vec<canvas::Move>) {
        let Some(doc) = &self.doc else { return };
        if let Some(off) = moves.iter().map(|m| m.3).find(|&(x, y)| !doc.on_map(x, y)) {
            let f = doc.folder.clone();
            self.flash(format!("Can't move events to {}, {}: not on {}", off.0, off.1, f), 5);
            return;
        }
        self.push(Command::MoveEvents(moves));
    }

    fn add_event(&mut self, section: &str, x: i64, y: i64) {
        let Some(doc) = &self.doc else { return };
        if !doc.on_map(x, y) {
            let f = doc.folder.clone();
            self.flash(format!("Can't add an event at {}, {}: not on {}", x, y, f), 5);
            return;
        }
        self.push(Command::AddEvent { section: section.into(), x, y, index: None, event: None });
    }

    fn delete_selected(&mut self) {
        // highest index first, so the others keep their indexes
        let mut sel: Vec<(String, usize)> = self.view.selection.iter().cloned().collect();
        sel.sort_by(|a, b| b.1.cmp(&a.1));
        for (s, i) in sel {
            self.push(Command::RemoveEvent { section: s, index: i, event: None });
        }
        self.view.selection.clear();
    }

    fn refuse(&mut self, key: &str, value: &Value) -> bool {
        match forms::check(&self.constants, key, value) {
            Some(e) => {
                self.dialog = Some(Dialog::Message(format!("Can't set {}", key), e));
                true
            }
            None => false,
        }
    }

    // --- files in a text editor -------------------------------------------------------------

    fn editor_template(&self) -> String {
        self.settings.editor_command.clone().unwrap_or_else(external::default_template)
    }

    fn open_file(&mut self, path: PathBuf, line: usize) {
        if self.settings.editor_command.is_none() {
            self.dialog = Some(Dialog::ChooseEditor { command: self.editor_template(), then: Some((path, line)) });
            return;
        }
        match external::launch(&self.editor_template(), &path, line, Some(&self.project.root)) {
            Ok(argv) => {
                let rel = path.strip_prefix(&self.project.root).unwrap_or(&path).display().to_string();
                let prog = Path::new(&argv[0]).file_name().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default();
                self.flash(format!("Opened {}:{} ({})", rel, line.max(1), prog), 4);
            }
            Err(e) => self.dialog = Some(Dialog::Message(format!("Can't open {}", path.display()), e)),
        }
    }

    /// (label, path) of the open map's files: its folder, layout and the land data of
    /// the cell last under the mouse.
    fn map_files(&self) -> Vec<(String, PathBuf)> {
        let Some(doc) = &self.doc else { return Vec::new() };
        let folder = doc.map_json.parent().unwrap().to_path_buf();
        let mut names: Vec<String> = std::fs::read_dir(&folder)
            .map(|d| d.filter_map(|e| e.ok()).filter(|e| e.path().is_file()).map(|e| e.file_name().to_string_lossy().into_owned()).collect())
            .unwrap_or_default();
        names.sort_by_key(|n| (n != "scripts.pory", n != "map.json", n.clone()));
        let mut out: Vec<(String, PathBuf)> = names.into_iter().map(|n| (n.clone(), folder.join(n))).collect();
        out.push((format!("layout.json ({})", doc.layout_name), self.project.layout_path(&doc.layout_name)));
        if let Some((x, y)) = self.view.hovered.filter(|&(x, y)| x >= 0 && y >= 0) {
            if let Some(c) = doc.chunk(x as usize / CELL, y as usize / CELL) {
                for name in ["permissions.txt", "props.json", "heights.json"] {
                    if c.dir.join(name).is_file() {
                        out.push((format!("land data {:04}: {}", c.number, name), c.dir.join(name)));
                    }
                }
            }
        }
        out
    }

    /// (path, line) of the selected event's script in the map's scripts file, or of the file.
    fn script_location(&self, sel: Option<(String, usize)>) -> Option<(PathBuf, usize)> {
        let doc = self.doc.as_ref()?;
        let folder = doc.map_json.parent()?;
        let path = ["scripts.pory", "scripts.inc"].iter().map(|n| folder.join(n)).find(|p| p.is_file())?;
        let label = sel.or_else(|| self.view.selected_event()).and_then(|(s, i)| doc.event(&s, i)?.get("script")?.as_str().map(String::from));
        let line = label.and_then(|l| external::label_line(&path, &l)).unwrap_or(1);
        Some((path, line))
    }

    fn open_script(&mut self, sel: Option<(String, usize)>) {
        match self.script_location(sel) {
            Some((p, l)) => self.open_file(p, l),
            None => self.flash("This map has no scripts file", 4),
        }
    }

    fn open_event_json(&mut self, sel: Option<(String, usize)>) {
        let Some(doc) = &self.doc else { return };
        let path = doc.map_json.clone();
        let line = sel.or_else(|| self.view.selected_event()).and_then(|(s, i)| external::event_line(&path, &s, i)).unwrap_or(1);
        self.open_file(path, line);
    }

    // --- UI ----------------------------------------------------------------------------------

    fn shortcuts(&mut self, ctx: &egui::Context) {
        let typing = ctx.egui_wants_keyboard_input();
        // Ctrl+Shift+X before Ctrl+X: egui matches a shortcut without Shift when Shift is held too
        let (save, redo, undo, reload, open_event, open_script, quit, zin, zout) = ctx.input_mut(|i| {
            (
                i.consume_shortcut(&SAVE),
                !typing && (i.consume_shortcut(&REDO) || i.consume_shortcut(&REDO_Y)),
                !typing && i.consume_shortcut(&UNDO),
                i.consume_shortcut(&RELOAD),
                i.consume_shortcut(&OPEN_EVENT),
                i.consume_shortcut(&OPEN_SCRIPT),
                i.consume_shortcut(&QUIT),
                i.consume_shortcut(&ZOOM_IN) || i.consume_shortcut(&ZOOM_IN_PLUS),
                i.consume_shortcut(&ZOOM_OUT),
            )
        });
        if save {
            self.save(false);
        }
        if undo {
            self.undo();
        }
        if redo {
            self.redo();
        }
        if reload && self.doc.is_some() {
            self.request(After::Reload);
        }
        if open_event {
            self.open_event_json(None);
        }
        if open_script {
            self.open_script(None);
        }
        if quit {
            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
        }
        if zin {
            self.view.zoom_by(1.25, None);
        }
        if zout {
            self.view.zoom_by(0.8, None);
        }
        if !typing {
            let (del, t1, t2, t3) = ctx.input(|i| {
                (
                    i.key_pressed(Key::Delete) && i.modifiers.is_none(),
                    i.key_pressed(Key::Num1) && i.modifiers.is_none(),
                    i.key_pressed(Key::Num2) && i.modifiers.is_none(),
                    i.key_pressed(Key::Num3) && i.modifiers.is_none(),
                )
            });
            if del && self.center == Center::Map {
                self.delete_selected();
            }
            for (on, tool) in [(t1, Tool::Select), (t2, Tool::Collision), (t3, Tool::Behavior)] {
                if on {
                    self.set_tool(tool);
                }
            }
        }
    }

    fn set_tool(&mut self, tool: Tool) {
        self.view.tool = tool;
        if tool != Tool::Select {
            self.tab = Tab::Tiles;
        }
    }

    fn menus(&mut self, ui: &mut egui::Ui) {
        egui::MenuBar::new().ui(ui, |ui| {
            ui.menu_button("File", |ui| {
                if ui.add(egui::Button::new("Save").shortcut_text("Ctrl+S")).clicked() {
                    self.save(false);
                }
                if ui.add_enabled(self.doc.is_some(), egui::Button::new("Reload map").shortcut_text("F5")).clicked() {
                    self.request(After::Reload);
                }
                ui.separator();
                ui.menu_button("Open in text editor", |ui| {
                    let files = self.map_files();
                    if files.is_empty() {
                        ui.weak("no map open");
                    }
                    for (label, path) in files {
                        if ui.button(label).clicked() {
                            self.open_file(path, 1);
                        }
                    }
                    if let Some(doc) = &self.doc {
                        ui.separator();
                        let folder = doc.map_json.parent().unwrap().to_path_buf();
                        if ui.button("Map folder in the file manager").clicked() {
                            if let Err(e) = external::launch("xdg-open {file}", &folder, 1, None) {
                                self.dialog = Some(Dialog::Message("Can't open the folder".into(), e));
                            }
                        }
                    }
                });
                if ui.add(egui::Button::new("Open script").shortcut_text("Ctrl+E")).clicked() {
                    self.open_script(None);
                }
                if ui.add(egui::Button::new("Show event in map.json").shortcut_text("Ctrl+Shift+E")).clicked() {
                    self.open_event_json(None);
                }
                if ui.button("Choose text editor...").clicked() {
                    self.dialog = Some(Dialog::ChooseEditor { command: self.editor_template(), then: None });
                }
                ui.separator();
                if ui.add(egui::Button::new("Quit").shortcut_text("Ctrl+Q")).clicked() {
                    ui.ctx().send_viewport_cmd(egui::ViewportCommand::Close);
                }
            });
            ui.menu_button("Edit", |ui| {
                let u = self.undo.undo_text().map(|t| format!("Undo {}", t)).unwrap_or("Undo".into());
                if ui.add_enabled(self.undo.undo_text().is_some(), egui::Button::new(u).shortcut_text("Ctrl+Z")).clicked() {
                    self.undo();
                }
                let r = self.undo.redo_text().map(|t| format!("Redo {}", t)).unwrap_or("Redo".into());
                if ui.add_enabled(self.undo.redo_text().is_some(), egui::Button::new(r).shortcut_text("Ctrl+Shift+Z")).clicked() {
                    self.redo();
                }
                if ui.add_enabled(!self.view.selection.is_empty(), egui::Button::new("Delete event").shortcut_text("Del")).clicked() {
                    self.delete_selected();
                }
            });
            ui.menu_button("View", |ui| {
                self.layer_toggles(ui);
                ui.separator();
                if ui.add(egui::Button::new("Zoom in").shortcut_text("Ctrl+=")).clicked() {
                    self.view.zoom_by(1.25, None);
                }
                if ui.add(egui::Button::new("Zoom out").shortcut_text("Ctrl+-")).clicked() {
                    self.view.zoom_by(0.8, None);
                }
            });
        });
    }

    fn layer_toggles(&mut self, ui: &mut egui::Ui) {
        for (key, label, _) in LAYERS {
            let mut on = self.view.layer(key);
            if ui.checkbox(&mut on, label).changed() {
                self.view.layers.insert(key.to_string(), on);
                self.settings.layers = self.view.layers.clone();
                self.settings.save();
            }
        }
    }

    fn toolbar(&mut self, ui: &mut egui::Ui) {
        ui.horizontal_wrapped(|ui| {
            if ui.button("Save").clicked() {
                self.save(false);
            }
            if ui.add_enabled(self.undo.undo_text().is_some(), egui::Button::new("Undo")).clicked() {
                self.undo();
            }
            if ui.add_enabled(self.undo.redo_text().is_some(), egui::Button::new("Redo")).clicked() {
                self.redo();
            }
            ui.separator();
            for (tool, label, key) in [(Tool::Select, "Select / move events", "1"), (Tool::Collision, "Paint collision", "2"), (Tool::Behavior, "Paint behavior", "3")] {
                if ui.selectable_label(self.view.tool == tool, label).on_hover_text(format!("shortcut {}", key)).clicked() {
                    self.set_tool(tool);
                }
            }
            ui.separator();
            self.layer_toggles(ui);
        });
    }

    fn map_list(&mut self, ui: &mut egui::Ui) {
        ui.add(egui::TextEdit::singleline(&mut self.map_filter).hint_text("Filter maps..."));
        let t = self.map_filter.to_lowercase();
        let current = self.doc.as_ref().map(|d| d.folder.clone());
        let mut open = None;
        egui::ScrollArea::vertical().auto_shrink(false).show(ui, |ui| {
            for (folder, name, id) in &self.maps {
                if !t.is_empty() && !folder.to_lowercase().contains(&t) && !name.to_lowercase().contains(&t) {
                    continue;
                }
                let r = ui.selectable_label(current.as_deref() == Some(folder.as_str()), folder).on_hover_text(format!("{} ({})", name, id));
                if r.double_clicked() || (r.has_focus() && ui.input(|i| i.key_pressed(Key::Enter))) {
                    open = Some(folder.clone());
                }
            }
        });
        if let Some(f) = open {
            self.request(After::Open(f));
        }
    }

    fn properties(&mut self, ui: &mut egui::Ui) {
        ui.horizontal(|ui| {
            ui.selectable_value(&mut self.tab, Tab::Event, "Event");
            ui.selectable_value(&mut self.tab, Tab::Header, "Header");
            ui.selectable_value(&mut self.tab, Tab::Tiles, "Tiles");
        });
        ui.separator();
        match self.tab {
            Tab::Event => self.event_tab(ui),
            Tab::Header => self.header_tab(ui),
            Tab::Tiles => self.tiles_tab(ui),
        }
    }

    fn event_tab(&mut self, ui: &mut egui::Ui) {
        let sel = self.view.selected_event().filter(|(s, i)| self.doc.as_ref().is_some_and(|d| d.event(s, *i).is_some()));
        let script = sel.as_ref().and_then(|(s, i)| self.doc.as_ref()?.event(s, *i)?.get("script")?.as_str().map(String::from)).filter(|s| !s.is_empty());
        ui.horizontal(|ui| {
            let r = ui.add_enabled(script.is_some(), egui::Button::new("Open script"));
            let r = match &script {
                Some(s) => r.on_hover_text(format!("{} in scripts.pory (Ctrl+E)", s)),
                None => r,
            };
            if r.clicked() {
                self.open_script(sel.clone());
            }
            if ui.add_enabled(sel.is_some(), egui::Button::new("Show in map.json")).clicked() {
                self.open_event_json(sel.clone());
            }
        });
        let Some((section, index)) = sel else {
            let n = self.view.selection.len();
            ui.label(if n > 1 { format!("{} events selected", n) } else { "No event selected".into() });
            return;
        };
        let doc = self.doc.as_ref().unwrap();
        let ev = doc.event(&section, index).unwrap().clone();
        let fields: Vec<(String, Value)> = ev.as_object().map(|o| o.iter().map(|(k, v)| (k.clone(), v.clone())).collect()).unwrap_or_default();
        let ctx = ui.ctx().clone();
        if section == "object_events" {
            let g = ev.get("graphics_id").and_then(Value::as_str).unwrap_or("").to_string();
            let facing = facing_index(ev.get("facing_dir").unwrap_or(&Value::Null));
            if let Some(t) = canvas::sprite_texture(&mut self.sprite_icons, &mut self.sprites, &ctx, &g, facing, 0) {
                let [w, h] = t.size();
                ui.vertical_centered(|ui| ui.image((t.id(), egui::vec2(w as f32 * 2.0, h as f32 * 2.0))));
            }
        }
        let title = format!("{} {}", section_name(&section), index);
        ui.strong(&title);
        let (icons, sprites) = (&mut self.sprite_icons, &mut self.sprites);
        let mut icon = |name: &str| -> Option<egui::TextureHandle> {
            name.starts_with("SPRITE_").then(|| canvas::sprite_texture(icons, sprites, &ctx, name, 1, 0)).flatten()
        };
        let out = egui::ScrollArea::vertical()
            .auto_shrink(false)
            .show(ui, |ui| self.event_form.show(ui, &title, &fields, &[], &self.constants, &mut icon))
            .inner;
        if let Some((key, value)) = out.edit {
            if !self.refuse(&key, &value) {
                let old = ev.get(&key).cloned();
                self.push(Command::SetEventField { section, index, key, old, new: Some(value) });
            }
        }
    }

    fn header_tab(&mut self, ui: &mut egui::Ui) {
        let Some(doc) = &self.doc else {
            ui.label("No map open");
            return;
        };
        let fields = doc.header_fields();
        let title = doc.folder.clone();
        let mut no_icon = |_: &str| None;
        let out = egui::ScrollArea::vertical()
            .auto_shrink(false)
            .show(ui, |ui| self.header_form.show(ui, &title, &fields, &READ_ONLY, &self.constants, &mut no_icon))
            .inner;
        if let Some((key, value)) = out.edit {
            if !self.refuse(&key, &value) {
                let old = self.doc.as_ref().and_then(|d| d.data.get(&key).cloned());
                self.push(Command::SetHeaderField { key, old, new: Some(value) });
            }
        }
    }

    fn tiles_tab(&mut self, ui: &mut egui::Ui) {
        ui.label("Collision tool: left click blocks, right click opens.\nBehavior tool: left click paints the behavior below, right click picks it from the map.");
        ui.horizontal(|ui| {
            ui.label("Brush size");
            ui.add(egui::DragValue::new(&mut self.view.brush_size).range(1..=8));
        });
        ui.add(egui::TextEdit::singleline(&mut self.behavior_filter).hint_text("Filter behaviors..."));
        let t = self.behavior_filter.to_lowercase();
        let info = self.tile_info();
        let list_height = (ui.available_height() - 70.0).max(120.0);
        egui::ScrollArea::vertical().max_height(list_height).auto_shrink(false).show(ui, |ui| {
            let names: Vec<(u8, String)> = if self.behaviors.is_empty() {
                (0..=255u8).map(|v| (v, format!("{:02X}", v))).collect()
            } else {
                self.behaviors.iter().map(|(v, n)| (*v, n.clone())).collect()
            };
            for (value, name) in names {
                let text = format!("{:02X}  {}", value, name.trim_start_matches("TILE_BEHAVIOR_"));
                if !t.is_empty() && !text.to_lowercase().contains(&t) {
                    continue;
                }
                let selected = self.view.brush_behavior == value;
                let fill = behavior_color(value);
                let r = egui::Frame::new()
                    .fill(fill)
                    .stroke(if selected { egui::Stroke::new(2.0, Color32::BLACK) } else { egui::Stroke::NONE })
                    .inner_margin(egui::Margin::symmetric(4, 1))
                    .show(ui, |ui| {
                        ui.set_width(ui.available_width());
                        ui.label(egui::RichText::new(text).color(Color32::BLACK).monospace())
                    })
                    .response
                    .interact(egui::Sense::click());
                if r.clicked() {
                    self.view.brush_behavior = value;
                }
            }
        });
        ui.separator();
        ui.label(info);
    }

    fn tile_info(&mut self) -> String {
        let Some((x, y)) = self.view.hovered else { return String::new() };
        let Some(doc) = &self.doc else { return String::new() };
        let Some((c, b, a)) = doc.tile(x, y) else { return String::new() };
        let (cx, cy) = (x as usize / CELL, y as usize / CELL);
        let Some(land) = doc.cell_land(cx, cy) else { return String::new() };
        let shared = self.land_users(land).len();
        let behavior = self.behaviors.get(&b).cloned().unwrap_or_else(|| format!("{:02X}", b));
        format!(
            "tile {}, {}  (cell {},{}, land data {:04}{})  {}  {}  attr {:02X}",
            x,
            y,
            cx,
            cy,
            land,
            if shared > 1 { format!(", shared by {} maps", shared) } else { String::new() },
            if c != 0 { "blocked" } else { "open" },
            behavior,
            a
        )
    }

    fn context_menu(&mut self, response: &egui::Response) {
        if self.view.tool != Tool::Select || self.doc.is_none() {
            return;
        }
        response.context_menu(|ui| {
            let Some((x, y)) = self.view.context_tile else { return };
            let on_map = self.doc.as_ref().is_some_and(|d| d.on_map(x, y));
            for section in doc::EVENT_SECTIONS {
                if ui.add_enabled(on_map, egui::Button::new(format!("Add {} here ({}, {})", section_name(section).to_lowercase(), x, y))).clicked() {
                    self.add_event(section, x, y);
                    ui.close();
                }
            }
            if let Some(sel) = self.view.selected_event() {
                ui.separator();
                let script = self.doc.as_ref().and_then(|d| d.event(&sel.0, sel.1)?.get("script")?.as_str().map(String::from)).filter(|s| !s.is_empty());
                if let Some(s) = script {
                    if ui.button(format!("Open script {}", s)).clicked() {
                        self.open_script(Some(sel.clone()));
                        ui.close();
                    }
                }
                if ui.button("Show in map.json").clicked() {
                    self.open_event_json(Some(sel.clone()));
                    ui.close();
                }
            }
            if !self.view.selection.is_empty() {
                let n = self.view.selection.len();
                if ui.button(if n > 1 { format!("Delete {} selected events", n) } else { "Delete selected event".into() }).clicked() {
                    self.delete_selected();
                    ui.close();
                }
            }
        });
    }

    fn dialogs(&mut self, ctx: &egui::Context) {
        let Some(dialog) = self.dialog.take() else { return };
        let mut keep = true;
        let mut then: Option<Box<dyn FnOnce(&mut EditorApp)>> = None;
        let modal = egui::Modal::new(egui::Id::unique("dialog")).show(ctx, |ui| {
            ui.set_max_width(520.0);
            match &dialog {
                Dialog::Unsaved(after) => {
                    let name = self.doc.as_ref().map(|d| d.folder.clone()).unwrap_or_default();
                    ui.heading("Unsaved changes");
                    ui.label(format!("Save changes to {}?", name));
                    ui.horizontal(|ui| {
                        let (after, after2) = (after.clone(), after.clone());
                        if ui.button("Save").clicked() {
                            keep = false;
                            then = Some(Box::new(move |app: &mut EditorApp| {
                                if app.save(false) {
                                    app.proceed(after);
                                } else if let Some(Dialog::ChangedOnDisk(_, a)) = &mut app.dialog {
                                    *a = Some(after);
                                }
                            }));
                        }
                        if ui.button("Discard").clicked() {
                            keep = false;
                            then = Some(Box::new(move |app: &mut EditorApp| {
                                app.undo.set_clean();
                                app.proceed(after2)
                            }));
                        }
                        if ui.button("Cancel").clicked() {
                            keep = false;
                        }
                    });
                }
                Dialog::ChangedOnDisk(paths, after) => {
                    let name = self.doc.as_ref().map(|d| d.folder.clone()).unwrap_or_default();
                    ui.heading("Files changed outside the editor");
                    ui.label(format!(
                        "These files were changed since {} was opened:\n\n{}\n\nOverwrite them with the editor's version? (Cancel, then Reload map, keeps theirs and drops your edits.)",
                        name,
                        paths.join("\n")
                    ));
                    ui.horizontal(|ui| {
                        if ui.button("Overwrite").clicked() {
                            keep = false;
                            let after = after.clone();
                            then = Some(Box::new(move |app: &mut EditorApp| {
                                if app.save(true) {
                                    if let Some(a) = after {
                                        app.proceed(a);
                                    }
                                }
                            }));
                        }
                        if ui.button("Cancel").clicked() {
                            keep = false;
                        }
                    });
                }
                Dialog::Message(title, text) => {
                    ui.heading(title);
                    egui::ScrollArea::vertical().max_height(400.0).show(ui, |ui| ui.label(text));
                    if ui.button("OK").clicked() {
                        keep = false;
                    }
                }
                Dialog::ChooseEditor { command, then: open } => {
                    let mut command = command.clone();
                    ui.heading("Text editor");
                    egui::ComboBox::from_label("Editor").selected_text(
                        external::PRESETS.iter().find(|p| p.1 == command).map(|p| p.0).unwrap_or("Custom"),
                    ).show_ui(ui, |ui| {
                        for (name, tpl) in external::PRESETS {
                            let label = if external::available(tpl) { name.to_string() } else { format!("{} (not installed)", name) };
                            if ui.selectable_label(command == *tpl, label).clicked() {
                                command = tpl.to_string();
                            }
                        }
                    });
                    ui.horizontal(|ui| {
                        ui.label("Command");
                        ui.add(egui::TextEdit::singleline(&mut command).desired_width(400.0));
                    });
                    let term = external::terminal().map(|t| t.join(" ")).unwrap_or_else(|| "none found, set $TERMINAL".into());
                    ui.label(format!("{{file}} is the file, {{line}} the line (from 1). {{term}} runs the rest in a terminal: {}.", term));
                    let mut done = false;
                    ui.horizontal(|ui| {
                        if ui.button("OK").clicked() && !command.trim().is_empty() {
                            done = true;
                        }
                        if ui.button("Cancel").clicked() {
                            keep = false;
                        }
                    });
                    if done {
                        keep = false;
                        let (cmd, open) = (command.trim().to_string(), open.clone());
                        then = Some(Box::new(move |app: &mut EditorApp| {
                            app.settings.editor_command = Some(cmd);
                            app.settings.save();
                            if let Some((p, l)) = open {
                                app.open_file(p, l);
                            }
                        }));
                    } else if keep {
                        // keep the edited command for the next frame
                        self.dialog = Some(Dialog::ChooseEditor { command, then: open.clone() });
                    }
                }
            }
        });
        if modal.should_close() && !matches!(dialog, Dialog::Unsaved(_) | Dialog::ChangedOnDisk(..)) {
            keep = false;
        }
        if keep && self.dialog.is_none() {
            self.dialog = Some(dialog);
        }
        if let Some(f) = then {
            f(self);
        }
    }

    fn update_title(&mut self, ctx: &egui::Context) {
        let name = self.doc.as_ref().map(|d| d.folder.clone()).unwrap_or_else(|| "no map".into());
        let dirty = self.doc.is_some() && !self.undo.is_clean();
        let title = format!("{}{} - HGSS map editor", name, if dirty { " *" } else { "" });
        if title != self.title {
            ctx.send_viewport_cmd(egui::ViewportCommand::Title(title.clone()));
            self.title = title;
        }
    }
}

impl eframe::App for EditorApp {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut eframe::Frame) {
        let ctx = ui.ctx().clone();
        if ctx.input(|i| i.viewport().close_requested()) && !self.allow_close
            && self.doc.is_some() && !self.undo.is_clean() {
                ctx.send_viewport_cmd(egui::ViewportCommand::CancelClose);
                if self.dialog.is_none() {
                    self.dialog = Some(Dialog::Unsaved(After::Quit));
                }
            }
        if self.allow_close {
            self.allow_close = false;
            self.undo.set_clean();
            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
        }
        if self.dialog.is_none() {
            self.shortcuts(&ctx);
        }
        self.watch();
        self.update_title(&ctx);

        egui::Panel::top("menu").show(ui, |ui| {
            self.menus(ui);
            self.toolbar(ui);
        });
        egui::Panel::bottom("status").show(ui, |ui| {
            let text = match &self.flash {
                Some((t, at, d)) if at.elapsed() < *d => t.clone(),
                _ => {
                    let hover = self.tile_info();
                    if hover.is_empty() { self.status.clone() } else { hover }
                }
            };
            ui.horizontal(|ui| {
                ui.label(text);
                let pending = self.terrain.pending();
                if pending > 0 {
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| ui.weak(format!("drawing {} cells", pending)));
                }
            });
        });
        egui::Panel::left("maps").resizable(true).default_size(220.0).show(ui, |ui| {
            ui.strong("Maps");
            self.map_list(ui);
        });
        egui::Panel::right("properties").resizable(true).default_size(380.0).min_size(360.0).show(ui, |ui| {
            self.properties(ui);
        });
        egui::CentralPanel::default().show(ui, |ui| {
            ui.horizontal(|ui| {
                ui.selectable_value(&mut self.center, Center::Map, "Map");
                ui.selectable_value(&mut self.center, Center::View3D, "3D");
            });
            let Some(doc) = self.doc.as_mut() else {
                ui.centered_and_justified(|ui| ui.label("Pick a map from the list (double-click)"));
                return;
            };
            match self.center {
                Center::Map => {
                    let (actions, response) = self.view.ui(ui, doc, &mut self.terrain, &mut self.sprites);
                    self.view.draw_brush(ui);
                    for a in actions {
                        match a {
                            Action::Stroke(tiles) => self.stroke(tiles),
                            Action::Moved(moves) => self.move_events(moves),
                            Action::Picked(b) => {
                                self.view.brush_behavior = b;
                                self.behavior_filter.clear();
                            }
                            Action::SelectionChanged => {
                                if self.view.selection.len() == 1 {
                                    self.tab = Tab::Event;
                                }
                            }
                        }
                    }
                    self.context_menu(&response);
                }
                Center::View3D => {
                    self.view3d.ui(ui, doc, &self.terrain.renderer, &self.project, &mut self.sprites, &self.view.layers);
                }
            }
        });
        self.dialogs(&ctx);
        self.take_screenshot(&ctx);
    }
}

impl EditorApp {
    fn take_screenshot(&mut self, ctx: &egui::Context) {
        let Some((path, frames)) = &mut self.screenshot else { return };
        *frames += 1;
        ctx.request_repaint();
        // a few frames for the layout to settle, then wait for the terrain threads
        if *frames < 20 || (self.terrain.pending() > 0 && *frames < 2000) {
            return;
        }
        let (path, ctx2) = (path.clone(), ctx.clone());
        self.screenshot = None;
        ctx.request_screenshot(move |img| {
            let result = std::fs::File::create(&path).map_err(|e| e.to_string()).and_then(|f| {
                let mut e = png::Encoder::new(std::io::BufWriter::new(f), img.size[0] as u32, img.size[1] as u32);
                e.set_color(png::ColorType::Rgba);
                e.write_header().and_then(|mut w| w.write_image_data(img.as_raw())).map_err(|e| e.to_string())
            });
            if let Err(e) = result {
                eprintln!("mapeditor-rs: screenshot {}: {}", path.display(), e);
            }
            ctx2.send_viewport_cmd(egui::ViewportCommand::Close);
        });
    }
}
