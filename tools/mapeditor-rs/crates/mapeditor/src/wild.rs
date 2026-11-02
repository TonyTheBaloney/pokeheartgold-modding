// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-11-02
//! The Wild encounters tab: the open map's table in gs_enc_data.json (which table,
//! rates, slots, radio, swarms), edited for both versions or one of them. It only
//! reads the document; edits come back as actions for the window to push as commands.

use std::collections::BTreeSet;

use egui::Color32;
use gen4map_format::constants::Constants;
use gen4map_format::wild::{self, Method, EXTRAS, METHODS, NO_SPECIES, NO_TABLE, RADIO, TIMES};
use serde_json::{json, Value};

use crate::doc::MapDoc;
use crate::forms::{self, FieldForm};

const WARN: Color32 = Color32::from_rgb(0xD0, 0x80, 0x10);

pub enum WildAction {
    Set { table: usize, pointer: String, old: Option<Value>, new: Option<Value> },
    /// A new value for map.json's wild_encounters.
    SetBank(Value),
    /// Append a table for this map: empty, or a copy of its current one.
    NewTable { copy: bool },
    /// Open gs_enc_data.json at a table.
    Open(usize),
    Refused(String, String),
}

#[derive(Clone, Copy, PartialEq)]
enum Kind {
    Species,
    Level,
    /// Rates can't differ between versions (gs_enc_data.json.txt).
    Rate,
}

#[derive(Default)]
pub struct WildView {
    form: FieldForm,
    /// The version whose values are shown and edited; None: the values as written,
    /// which edits set for both.
    version: Option<&'static str>,
}

impl WildView {
    /// `users`: the other maps whose map.json names the same table.
    pub fn ui(&mut self, ui: &mut egui::Ui, doc: &MapDoc, constants: &Constants, users: &BTreeSet<String>) -> Vec<WildAction> {
        let mut out = Vec::new();
        let wild = match &doc.wild {
            Ok(w) => w,
            Err(e) => {
                ui.colored_label(WARN, format!("The wild encounter tables couldn't be read:\n{}", e));
                return out;
            }
        };
        let bank_value = doc.data.get("wild_encounters").cloned().unwrap_or_else(|| Value::String(String::new()));
        let bank = bank_value.as_str().unwrap_or("").to_string();
        let index = doc.wild_index(&constants.wild);
        self.form.begin(ui, &format!("wild {:?} {:?} {:?}", doc.folder, index, self.version));
        egui::ScrollArea::vertical().auto_shrink(false).show(ui, |ui| {
            ui.horizontal(|ui| {
                ui.label("Table");
                let mut no_icon = |_: &str| None;
                if let Some(v) = self.form.field(ui, "wild_encounters", &bank_value, Some("ENCDATA_"), None, 240.0, constants, &mut no_icon) {
                    out.push(WildAction::SetBank(v));
                }
                if let Some(i) = index {
                    let label = wild.table(i).and_then(|t| t.get("map")).and_then(Value::as_str).unwrap_or("");
                    ui.weak(format!("table {} of {} (\"map\": \"{}\")", i, wild.tables().len(), label));
                    if ui.button("Open in text editor").on_hover_text("gs_enc_data.json at this table").clicked() {
                        out.push(WildAction::Open(i));
                    }
                }
            });
            ui.horizontal(|ui| {
                let why = "Appends a table to gs_enc_data.json and points this map at it; saving defines its ENCDATA_ name in encounter_tables_narc.h";
                if ui.button("New empty table").on_hover_text(why).clicked() {
                    out.push(WildAction::NewTable { copy: false });
                }
                let has = index.is_some_and(|i| wild.table(i).is_some());
                if ui.add_enabled(has, egui::Button::new("Copy into a new table")).on_hover_text(why).clicked() {
                    out.push(WildAction::NewTable { copy: true });
                }
            });
            let Some(i) = index else {
                if bank == NO_TABLE || bank.is_empty() {
                    ui.label(format!("{} has no wild encounters ({}). Pick a table above or make a new one.", doc.folder, NO_TABLE));
                } else {
                    ui.colored_label(WARN, format!("{} isn't defined in encounter_tables_narc.h", bank));
                }
                return;
            };
            let Some(table) = wild.table(i) else {
                ui.colored_label(WARN, format!("{} is table {}, but gs_enc_data.json has {} tables", bank, i, wild.tables().len()));
                return;
            };
            if !users.is_empty() {
                let names: Vec<&str> = users.iter().map(String::as_str).collect();
                ui.colored_label(WARN, format!("Also used by {}: edits change their encounters too.", names.join(", ")));
            }
            ui.horizontal(|ui| {
                ui.label("Version");
                ui.selectable_value(&mut self.version, None, "Both").on_hover_text(
                    "Values as written: an edit sets both versions. One that differs shows as {\"HEARTGOLD\": ..., \"SOULSILVER\": ...}",
                );
                ui.selectable_value(&mut self.version, Some("HEARTGOLD"), "HeartGold");
                ui.selectable_value(&mut self.version, Some("SOULSILVER"), "SoulSilver");
            });
            let split = count_split(table);
            if split > 0 && self.version.is_none() {
                ui.weak(format!("{} values differ between the versions and show as {{\"HEARTGOLD\": ..., \"SOULSILVER\": ...}}: pick a version to edit them one at a time.", split));
            }
            let known = |n: &str| constants.names("SPECIES_").is_empty() || constants.is_known("SPECIES_", n);
            let issues = wild::issues(table, &known);
            if issues.is_empty() {
                ui.weak("No problems found.");
            }
            for s in &issues {
                ui.colored_label(WARN, s);
            }
            ui.separator();
            for m in &METHODS {
                self.method(ui, &mut out, constants, i, table, m);
            }
            self.radio(ui, &mut out, constants, i, table);
            self.extras(ui, &mut out, constants, i, table);
        });
        self.form.end();
        out
    }

    fn method(&mut self, ui: &mut egui::Ui, out: &mut Vec<WildAction>, constants: &Constants, i: usize, table: &Value, m: &Method) {
        let Some(group) = table.pointer(m.pointer) else { return };
        let rate = group.get("rate").cloned().unwrap_or(json!(0));
        let mons = group.get("mons").and_then(Value::as_array).cloned().unwrap_or_default();
        let title = if rate.as_u64().unwrap_or(0) > 0 { format!("{}: rate {}", m.label, rate) } else { format!("{}: off", m.label) };
        egui::CollapsingHeader::new(title).id_salt(m.key).default_open(!mons.is_empty()).show(ui, |ui| {
            ui.horizontal(|ui| {
                ui.label("Rate").on_hover_text("0-255: the higher, the more often a step meets a Pokémon. 0 turns the method off");
                let key = format!("{}/rate", m.pointer);
                if let Some(v) = self.edit(ui, out, &key, &rate, Kind::Rate, 44.0, constants) {
                    out.push(WildAction::Set { table: i, pointer: key, old: Some(rate.clone()), new: Some(v) });
                }
                let off = json!({"rate": 0, "mons": []});
                if mons.is_empty() {
                    if ui.button(format!("Add {} slots", m.slots())).clicked() {
                        let r = if rate.as_u64().unwrap_or(0) > 0 { rate.clone() } else { json!(10) };
                        let slots: Vec<Value> = (0..m.slots()).map(|_| wild::new_slot(m, NO_SPECIES, 5)).collect();
                        out.push(WildAction::Set { table: i, pointer: m.pointer.into(), old: Some(group.clone()), new: Some(json!({"rate": r, "mons": slots})) });
                    }
                } else if ui.button("Remove all slots").on_hover_text("Rate 0 and no slots, as maps without this method are written").clicked() {
                    out.push(WildAction::Set { table: i, pointer: m.pointer.into(), old: Some(group.clone()), new: Some(off) });
                }
            });
            if !m.note.is_empty() {
                ui.weak(m.note);
            }
            if mons.is_empty() {
                return;
            }
            let species_w = if m.is_land() { ((ui.available_width() - 150.0) / 3.0).clamp(110.0, 220.0) } else { 220.0 };
            egui::Grid::new(("wild slots", m.key)).striped(true).show(ui, |ui| {
                ui.strong("Slot");
                ui.strong("%");
                if m.is_land() {
                    ui.strong("Level");
                    for (_, name) in TIMES {
                        ui.strong(name);
                    }
                } else {
                    ui.strong("Min");
                    ui.strong("Max");
                    ui.strong("Species");
                }
                ui.end_row();
                for (n, mon) in mons.iter().enumerate() {
                    ui.label(n.to_string());
                    ui.label(m.odds.get(n).map(|o| o.to_string()).unwrap_or_else(|| "-".into()));
                    let base = format!("{}/mons/{}", m.pointer, n);
                    let cells: Vec<(String, Kind, f32)> = if m.is_land() {
                        std::iter::once(("/level".to_string(), Kind::Level, 44.0))
                            .chain(TIMES.iter().map(|(t, _)| (format!("/species/{}", t), Kind::Species, species_w)))
                            .collect()
                    } else {
                        vec![("/level/min".into(), Kind::Level, 44.0), ("/level/max".into(), Kind::Level, 44.0), ("/species".into(), Kind::Species, species_w)]
                    };
                    for (sub, kind, w) in cells {
                        let full = mon.pointer(&sub).cloned().unwrap_or(Value::Null);
                        let key = format!("{}{}", base, sub);
                        if let Some(v) = self.edit(ui, out, &key, &full, kind, w, constants) {
                            out.push(WildAction::Set { table: i, pointer: key, old: Some(full.clone()), new: Some(v) });
                        }
                    }
                    ui.end_row();
                }
            });
        });
    }

    fn radio(&mut self, ui: &mut egui::Ui, out: &mut Vec<WildAction>, constants: &Constants, i: usize, table: &Value) {
        egui::CollapsingHeader::new("Pokégear radio").id_salt("radio").default_open(true).show(ui, |ui| {
            ui.weak("While Hoenn or Sinnoh Sound plays, its first species replaces grass slots 2-3 and the second 4-5.");
            egui::Grid::new("wild radio").show(ui, |ui| {
                for (key, label) in RADIO {
                    ui.label(label);
                    let list = table.get(key).and_then(Value::as_array).cloned();
                    for n in 0..2 {
                        let full = list.as_ref().and_then(|l| l.get(n)).cloned().unwrap_or(Value::String(String::new()));
                        if let Some(v) = self.edit(ui, out, &format!("/{}/{}", key, n), &full, Kind::Species, 180.0, constants) {
                            // both entries are written, so a table without them gets two
                            let mut new: Vec<Value> = list.clone().unwrap_or_default();
                            new.resize(2, json!(NO_SPECIES));
                            new[n] = v;
                            out.push(WildAction::Set { table: i, pointer: format!("/{}", key), old: list.clone().map(Value::Array), new: Some(Value::Array(new)) });
                        }
                    }
                    ui.end_row();
                }
            });
        });
    }

    fn extras(&mut self, ui: &mut egui::Ui, out: &mut Vec<WildAction>, constants: &Constants, i: usize, table: &Value) {
        egui::CollapsingHeader::new("Swarms and night fishing").id_salt("extras").default_open(true).show(ui, |ui| {
            ui.weak("Empty: not written (builds as no species). Swarms only happen on the maps listed in src/swarm.c.");
            egui::Grid::new("wild extras").show(ui, |ui| {
                for (key, label) in EXTRAS {
                    ui.label(label);
                    let old = table.get(key).cloned();
                    let full = old.clone().unwrap_or(Value::String(String::new()));
                    if let Some(v) = self.edit(ui, out, &format!("/{}", key), &full, Kind::Species, 220.0, constants) {
                        let new = (v != Value::String(String::new())).then_some(v);
                        out.push(WildAction::Set { table: i, pointer: format!("/{}", key), old, new });
                    }
                    ui.end_row();
                }
            });
        });
    }

    /// A field for one value; returns the value to write (for the version shown) when
    /// an edit is committed and accepted. An empty species comes back as "".
    #[allow(clippy::too_many_arguments)]
    fn edit(&mut self, ui: &mut egui::Ui, out: &mut Vec<WildAction>, key: &str, full: &Value, kind: Kind, width: f32, constants: &Constants) -> Option<Value> {
        let version = if kind == Kind::Rate { None } else { self.version };
        let shown = match wild::pick(full, version) {
            Value::Null => Value::String(String::new()),
            v => v,
        };
        let prefix = (kind == Kind::Species).then_some("SPECIES_");
        let mut no_icon = |_: &str| None;
        let v = self.form.field(ui, key, &shown, prefix, None, width, constants, &mut no_icon)?;
        let refuse = match (&v, kind) {
            (Value::String(s), Kind::Species) if s.is_empty() => None,
            (_, Kind::Species) => forms::check_prefix(constants, "SPECIES_", &v),
            (Value::Number(n), Kind::Rate) if n.as_u64().is_some_and(|n| n <= 255) => None,
            (Value::Number(n), Kind::Level) if n.as_u64().is_some_and(|n| n <= 255) => None,
            (Value::Object(_), Kind::Level) if version.is_none() && wild::is_split(&v) => None,
            (_, Kind::Rate) => Some(format!("{} is not a rate (0-255)", forms::show_value(&v))),
            _ => Some(format!("{} is not a level (1-100)", forms::show_value(&v))),
        };
        if let Some(e) = refuse {
            out.push(WildAction::Refused(format!("Can't set {}", key), e));
            return None;
        }
        // in one version, an empty species (a missing value, or one emptied) is no species
        let empty = Value::String(String::new());
        let none_if_empty = |x: &Value| if version.is_some() && *x == empty { json!(NO_SPECIES) } else { x.clone() };
        let new = wild::put(&none_if_empty(full), version, none_if_empty(&v));
        (new != *full).then_some(new)
    }
}

/// Values written per version in a table.
fn count_split(v: &Value) -> usize {
    match v {
        _ if wild::is_split(v) => 1,
        Value::Object(o) => o.values().map(count_split).sum(),
        Value::Array(a) => a.iter().map(count_split).sum(),
        _ => 0,
    }
}
