// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Key -> value forms for an event's fields and the map header (FieldForm in
//! tools/mapeditor/mapeditor/window.py). A field is committed when it loses focus or
//! Enter is pressed; fields naming constants complete from the constants export
//! (arrow keys and Enter, or the mouse), sprites with their pictures.
//!
//! Fields without focus always show the document's value, so an edit the window
//! refuses puts the old text back by itself.

use std::collections::HashMap;

use egui::{Id, TextEdit};
use serde_json::Value;

use gen4map_format::constants::Constants;

/// map.json key -> constant prefix offered as completions and checked against.
pub fn completion_prefix(key: &str) -> Option<&'static str> {
    Some(match key {
        "graphics_id" => "SPRITE_",
        "movement_type" => "MOVEMENT_TYPE_",
        "facing_dir" => "DIR_",
        "trainer_type" => "OBJECT_TYPE_",
        "flag" => "FLAG_",
        "dest_map" => "MAP_",
        "var" => "VAR_",
        "type" => "BG_TYPE_",
        "player_facing_dir" => "BG_DIR_",
        "music_day" | "music_night" => "SEQ_",
        "region_map_section" => "MAPSEC_",
        "weather" => "WEATHER_",
        "map_type" => "MAP_TYPE_",
        "battle_scene" => "BATTLE_BG_",
        "camera_type" => "CAMERA_TYPE_",
        _ => return None,
    })
}

/// Python's int(text, 0): decimal, 0x / 0o / 0b, underscores between digits, a sign.
pub fn parse_int(t: &str) -> Option<i64> {
    let (neg, body) = match t.strip_prefix('-') {
        Some(b) => (true, b),
        None => (false, t.strip_prefix('+').unwrap_or(t)),
    };
    let lower = body.to_ascii_lowercase();
    let (radix, digits) = if let Some(d) = lower.strip_prefix("0x") {
        (16, d)
    } else if let Some(d) = lower.strip_prefix("0o") {
        (8, d)
    } else if let Some(d) = lower.strip_prefix("0b") {
        (2, d)
    } else {
        // int("010", 0) is an error in Python: only "0", "00"... may start with 0
        if lower.len() > 1 && lower.starts_with('0') && lower.chars().any(|c| c != '0' && c != '_') {
            return None;
        }
        (10, lower.as_str())
    };
    let digits = digits.strip_prefix('_').filter(|_| radix != 10).unwrap_or(digits);
    if digits.is_empty() || digits.starts_with('_') || digits.ends_with('_') || digits.contains("__") {
        return None;
    }
    let v = i64::from_str_radix(&digits.replace('_', ""), radix).ok()?;
    Some(if neg { -v } else { v })
}

/// Text from a field -> a JSON value of the same kind as the old one where possible.
pub fn parse_value(text: &str, old: Option<&Value>) -> Value {
    let t = text.trim();
    if let Some(Value::Bool(_)) = old {
        return Value::Bool(matches!(t.to_ascii_lowercase().as_str(), "1" | "true" | "yes"));
    }
    if let Some(n) = parse_int(t) {
        return n.into();
    }
    if t.starts_with('[') || t.starts_with('{') || (t == "null" && old.is_some_and(Value::is_null)) {
        if let Ok(v) = serde_json::from_str(t) {
            return v;
        }
    }
    Value::String(t.to_string())
}

/// json.dumps without indent: ", " and ": " separators.
fn python_dumps(v: &Value, out: &mut String) {
    match v {
        Value::Array(a) => {
            out.push('[');
            for (i, x) in a.iter().enumerate() {
                if i > 0 {
                    out.push_str(", ");
                }
                python_dumps(x, out);
            }
            out.push(']');
        }
        Value::Object(o) => {
            out.push('{');
            for (i, (k, x)) in o.iter().enumerate() {
                if i > 0 {
                    out.push_str(", ");
                }
                out.push_str(&serde_json::to_string(k).unwrap());
                out.push_str(": ");
                python_dumps(x, out);
            }
            out.push('}');
        }
        v => out.push_str(&v.to_string()),
    }
}

pub fn show_value(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        v => {
            let mut out = String::new();
            python_dumps(v, &mut out);
            out
        }
    }
}

/// Error text if a value isn't one of the field's constants. Numbers are always
/// accepted; fields whose constants aren't known aren't checked.
pub fn check(constants: &Constants, key: &str, value: &Value) -> Option<String> {
    let prefix = completion_prefix(key)?;
    let Value::String(s) = value else { return None };
    let names = constants.names(prefix);
    (!names.is_empty() && !constants.is_known(prefix, s)).then(|| format!("{} is not a {}* constant", s, prefix))
}

#[derive(Default)]
pub struct FieldForm {
    texts: HashMap<String, String>,
    title: String,
    /// The field whose completions are open, and the highlighted row.
    completing: Option<(String, usize)>,
    popup: Option<egui::Rect>,
    /// The field lost focus to a press on its completion list: commit on the click.
    picking: Option<String>,
}

pub struct FormOutput {
    pub edit: Option<(String, Value)>,
}

impl FieldForm {
    /// Show the fields; returns an edited (key, new value) when one is committed.
    /// `icon(name)` gives a picture for a completion row (sprites).
    pub fn show(
        &mut self,
        ui: &mut egui::Ui,
        title: &str,
        fields: &[(String, Value)],
        read_only: &[(&str, &str)],
        constants: &Constants,
        icon: &mut dyn FnMut(&str) -> Option<egui::TextureHandle>,
    ) -> FormOutput {
        if title != self.title {
            self.title = title.to_string();
            self.texts.clear();
            self.completing = None;
            self.picking = None;
        }
        let mut out = FormOutput { edit: None };
        let mut chosen: Option<(String, String)> = None;
        let pointer_over_popup = ui.input(|i| i.pointer.interact_pos()).zip(self.popup).is_some_and(|(p, r)| r.contains(p));
        let released = ui.input(|i| i.pointer.any_released());
        egui::Grid::new(("form", title)).num_columns(2).striped(true).show(ui, |ui| {
            for (key, value) in fields {
                ui.label(key);
                let id = Id::unique(("field", title, key));
                let focused = ui.memory(|m| m.has_focus(id));
                let shown = show_value(value);
                let text = self.texts.entry(key.clone()).or_insert_with(|| shown.clone());
                if !focused && self.picking.as_deref() != Some(key) {
                    text.clone_from(&shown);
                }
                let ro = read_only.iter().find(|(k, _)| k == key);
                let mut edit = TextEdit::singleline(text).id(id).desired_width(f32::INFINITY);
                if ro.is_some() {
                    edit = edit.interactive(false);
                }
                let resp = ui.add(edit);
                let resp = match ro {
                    Some((_, why)) => resp.on_hover_text(*why),
                    None => resp,
                };
                ui.end_row();
                let prefix = completion_prefix(key).filter(|p| !constants.names(p).is_empty());
                if resp.has_focus() {
                    if let Some(p) = prefix {
                        let row = match &self.completing {
                            Some((k, r)) if k == key => *r,
                            _ => 0,
                        };
                        self.completing = Some((key.clone(), row));
                        self.completion_popup(ui, &resp, key, p, constants, icon, &mut chosen);
                    }
                } else if self.picking.as_deref() == Some(key.as_str()) {
                    if let Some(p) = prefix {
                        self.completion_popup(ui, &resp, key, p, constants, icon, &mut chosen);
                    }
                    if chosen.is_none() && released {
                        // the press on the list didn't end in a choice: commit the text
                        self.picking = None;
                        self.completing = None;
                        out.edit = self.commit(key, value);
                    }
                }
                if resp.lost_focus() {
                    let enter = ui.input(|i| i.key_pressed(egui::Key::Enter));
                    let highlighted = match (&self.completing, prefix) {
                        (Some((k, row)), Some(p)) if k == key && enter => matches(constants, p, &self.texts[key]).get(*row).cloned(),
                        _ => None,
                    };
                    if pointer_over_popup && !enter && prefix.is_some() {
                        self.picking = Some(key.clone());
                    } else {
                        self.completing = None;
                        if let Some(name) = highlighted.filter(|n| *n != self.texts[key]) {
                            self.texts.insert(key.clone(), name);
                        }
                        out.edit = self.commit(key, value);
                    }
                }
            }
        });
        if let Some((key, name)) = chosen {
            self.texts.insert(key.clone(), name);
            self.picking = None;
            self.completing = None;
            if let Some((_, value)) = fields.iter().find(|(k, _)| *k == key) {
                out.edit = self.commit(&key, value);
            }
        }
        if self.completing.is_none() && self.picking.is_none() {
            self.popup = None;
        }
        out
    }

    fn commit(&self, key: &str, old: &Value) -> Option<(String, Value)> {
        let new = parse_value(self.texts.get(key)?, Some(old));
        (new != *old).then(|| (key.to_string(), new))
    }

    #[allow(clippy::too_many_arguments)]
    fn completion_popup(
        &mut self,
        ui: &egui::Ui,
        field: &egui::Response,
        key: &str,
        prefix: &str,
        constants: &Constants,
        icon: &mut dyn FnMut(&str) -> Option<egui::TextureHandle>,
        chosen: &mut Option<(String, String)>,
    ) {
        let text = self.texts.get(key).cloned().unwrap_or_default();
        let found = matches(constants, prefix, &text);
        if found.is_empty() || (found.len() == 1 && found[0] == text) {
            self.popup = None;
            return;
        }
        let mut row = self.completing.as_ref().map(|c| c.1).unwrap_or(0).min(found.len() - 1);
        if field.has_focus() {
            ui.input_mut(|i| {
                if i.consume_key(egui::Modifiers::NONE, egui::Key::ArrowDown) {
                    row = (row + 1).min(found.len() - 1);
                }
                if i.consume_key(egui::Modifiers::NONE, egui::Key::ArrowUp) {
                    row = row.saturating_sub(1);
                }
            });
            self.completing = Some((key.to_string(), row));
        }
        let area = egui::Area::new(field.id.with("completions"))
            .order(egui::Order::Foreground)
            .fixed_pos(field.rect.left_bottom())
            .show(ui.ctx(), |ui| {
                egui::Frame::popup(ui.style()).show(ui, |ui| {
                    ui.set_width(field.rect.width().max(220.0));
                    egui::ScrollArea::vertical().max_height(260.0).show(ui, |ui| {
                        for (i, name) in found.iter().take(300).enumerate() {
                            let r = ui
                                .horizontal(|ui| {
                                    if let Some(t) = icon(name) {
                                        let [w, h] = t.size();
                                        let s = 24.0 / (w.max(h) as f32);
                                        ui.image((t.id(), egui::vec2(w as f32 * s, h as f32 * s)));
                                    }
                                    ui.selectable_label(i == row, name)
                                })
                                .inner;
                            if i == row && field.has_focus() {
                                r.scroll_to_me(None);
                            }
                            if r.clicked() {
                                *chosen = Some((key.to_string(), name.clone()));
                            }
                        }
                        if found.len() > 300 {
                            ui.weak(format!("... {} more: type to narrow", found.len() - 300));
                        }
                    });
                });
            });
        self.popup = Some(area.response.rect);
    }
}

/// Constants with a prefix containing `text` (case-insensitive); all of them if `text`
/// is empty or already one of them.
fn matches(constants: &Constants, prefix: &str, text: &str) -> Vec<String> {
    let names = constants.names(prefix);
    let t = text.trim().to_ascii_lowercase();
    if t.is_empty() {
        return names.to_vec();
    }
    names.iter().filter(|n| n.to_ascii_lowercase().contains(&t)).cloned().collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn values_like_python() {
        assert_eq!(parse_value("12", Some(&json!(3))), json!(12));
        assert_eq!(parse_value("0x1F", Some(&json!(3))), json!(31));
        assert_eq!(parse_value("-4", None), json!(-4));
        assert_eq!(parse_value("1_000", None), json!(1000));
        assert_eq!(parse_value("010", None), json!("010"));
        assert_eq!(parse_value("yes", Some(&json!(false))), json!(true));
        assert_eq!(parse_value("nope", Some(&json!(true))), json!(false));
        assert_eq!(parse_value("[1, 2]", None), json!([1, 2]));
        assert_eq!(parse_value(" FLAG_X ", None), json!("FLAG_X"));
        assert_eq!(parse_value("null", Some(&Value::Null)), Value::Null);
        assert_eq!(show_value(&json!([1, {"a": true}])), "[1, {\"a\": true}]");
        assert_eq!(show_value(&json!("MAP_X")), "MAP_X");
        assert_eq!(show_value(&json!(false)), "false");
    }

    #[test]
    fn checking() {
        let c = Constants::parse(
            r#"{"format": "mapkit-constants", "version": 1, "game": "HEARTGOLD",
                "constants": {"FLAG_": ["FLAG_A", "FLAG_B"], "CAMERA_TYPE_": []}, "behaviors": {}, "sprites": {}}"#,
        )
        .unwrap();
        assert_eq!(check(&c, "flag", &json!("FLAG_A")), None);
        assert!(check(&c, "flag", &json!("FLAG_C")).is_some());
        assert_eq!(check(&c, "flag", &json!(5)), None);
        assert_eq!(check(&c, "camera_type", &json!("ANYTHING")), None);
        assert_eq!(check(&c, "x", &json!("ANYTHING")), None);
        assert_eq!(matches(&c, "FLAG_", "b"), ["FLAG_B"]);
    }
}
