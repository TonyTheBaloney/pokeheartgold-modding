// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Undoable edits (tools/mapeditor/mapeditor/commands.py) and the undo stack. Each
//! command changes the MapDoc and returns what the window has to refresh.

use std::collections::BTreeMap;

use gen4map_format::permissions::Tile;
use serde_json::Value;

use crate::doc::MapDoc;

/// What an edit changed, for the window to redraw.
#[derive(Debug, Clone, PartialEq)]
pub enum Change {
    Tiles(Vec<(i64, i64)>),
    /// The event to select afterwards, if any.
    Events(Option<(String, usize)>),
    Header(String),
    Wild,
}

#[derive(Debug, Clone)]
pub enum Command {
    /// One brush stroke: {(x, y): (old, new)}.
    PaintTiles { name: String, tiles: BTreeMap<(i64, i64), (Tile, Tile)> },
    /// Events moved together (one drag): (section, index, old xy, new xy).
    MoveEvents(Vec<(String, usize, (i64, i64), (i64, i64))>),
    SetEventField { section: String, index: usize, key: String, old: Option<Value>, new: Option<Value> },
    /// `event` is filled in when first applied, so redo re-adds the same event.
    AddEvent { section: String, x: i64, y: i64, index: Option<usize>, event: Option<Value> },
    RemoveEvent { section: String, index: usize, event: Option<Value> },
    SetHeaderField { key: String, old: Option<Value>, new: Option<Value> },
    /// A value in wild table `table` at a JSON pointer.
    SetWild { table: usize, pointer: String, old: Option<Value>, new: Option<Value> },
    /// Append a wild table named `bank` and point the map at it; `old_bank` is the
    /// map's wild_encounters before.
    AddWildTable { bank: String, table: Value, old_bank: Option<Value> },
}

impl Command {
    pub fn text(&self) -> String {
        match self {
            Command::PaintTiles { name, .. } => name.clone(),
            Command::MoveEvents(m) if m.len() == 1 => "Move event".into(),
            Command::MoveEvents(m) => format!("Move {} events", m.len()),
            Command::SetEventField { key, .. } | Command::SetHeaderField { key, .. } => format!("Set {}", key),
            Command::AddEvent { .. } => "Add event".into(),
            Command::RemoveEvent { .. } => "Delete event".into(),
            Command::SetWild { .. } => "Edit wild encounters".into(),
            Command::AddWildTable { .. } => "New wild table".into(),
        }
    }

    pub fn redo(&mut self, doc: &mut MapDoc) -> Change {
        match self {
            Command::PaintTiles { tiles, .. } => {
                for (&(x, y), &(_, new)) in tiles.iter() {
                    doc.set_tile(x, y, new);
                }
                Change::Tiles(tiles.keys().copied().collect())
            }
            Command::MoveEvents(moves) => {
                for (section, index, _, new) in moves.iter() {
                    doc.move_event(section, *index, new.0, new.1);
                }
                Change::Events(moves.first().map(|m| (m.0.clone(), m.1)))
            }
            Command::SetEventField { section, index, key, new, .. } => {
                doc.set_event_field(section, *index, key, new.clone());
                Change::Events(Some((section.clone(), *index)))
            }
            Command::AddEvent { section, x, y, index, event } => {
                let i = doc.add_event(section, *x, *y, event.as_ref(), *index);
                *index = Some(i);
                *event = doc.event(section, i).cloned();
                Change::Events(Some((section.clone(), i)))
            }
            Command::RemoveEvent { section, index, event } => {
                *event = doc.remove_event(section, *index);
                Change::Events(None)
            }
            Command::SetHeaderField { key, new, .. } => {
                doc.set_header_field(key, new.clone());
                Change::Header(key.clone())
            }
            Command::SetWild { table, pointer, new, .. } => {
                if let Ok(w) = &mut doc.wild {
                    w.set(*table, pointer, new.clone());
                }
                Change::Wild
            }
            Command::AddWildTable { bank, table, .. } => {
                if let Ok(w) = &mut doc.wild {
                    w.push_table(table.clone(), bank);
                }
                doc.set_header_field("wild_encounters", Some(Value::String(bank.clone())));
                Change::Wild
            }
        }
    }

    pub fn undo(&mut self, doc: &mut MapDoc) -> Change {
        match self {
            Command::PaintTiles { tiles, .. } => {
                for (&(x, y), &(old, _)) in tiles.iter() {
                    doc.set_tile(x, y, old);
                }
                Change::Tiles(tiles.keys().copied().collect())
            }
            Command::MoveEvents(moves) => {
                for (section, index, old, _) in moves.iter() {
                    doc.move_event(section, *index, old.0, old.1);
                }
                Change::Events(moves.first().map(|m| (m.0.clone(), m.1)))
            }
            Command::SetEventField { section, index, key, old, .. } => {
                doc.set_event_field(section, *index, key, old.clone());
                Change::Events(Some((section.clone(), *index)))
            }
            Command::AddEvent { section, index, .. } => {
                if let Some(i) = index {
                    doc.remove_event(section, *i);
                }
                Change::Events(None)
            }
            Command::RemoveEvent { section, index, event } => {
                if let Some(ev) = event {
                    let (x, y) = (ev["x"].as_i64().unwrap_or(0), ev["y"].as_i64().unwrap_or(0));
                    doc.add_event(section, x, y, Some(&ev.clone()), Some(*index));
                }
                Change::Events(Some((section.clone(), *index)))
            }
            Command::SetHeaderField { key, old, .. } => {
                doc.set_header_field(key, old.clone());
                Change::Header(key.clone())
            }
            Command::SetWild { table, pointer, old, .. } => {
                if let Ok(w) = &mut doc.wild {
                    w.set(*table, pointer, old.clone());
                }
                Change::Wild
            }
            Command::AddWildTable { old_bank, .. } => {
                if let Ok(w) = &mut doc.wild {
                    w.pop_table();
                }
                doc.set_header_field("wild_encounters", old_bank.clone());
                Change::Wild
            }
        }
    }
}

/// Commands done and undone. The stack alone says whether there is anything to save:
/// it is clean at the position it had when last saved (QUndoStack's rule).
#[derive(Default)]
pub struct UndoStack {
    done: Vec<Command>,
    undone: Vec<Command>,
    clean: Option<usize>,
}

impl UndoStack {
    pub fn new() -> UndoStack {
        UndoStack { done: Vec::new(), undone: Vec::new(), clean: Some(0) }
    }

    /// Apply a command and record it. `applied`: the edit was already made (a brush
    /// stroke paints as it goes), so only record it.
    pub fn push(&mut self, mut cmd: Command, doc: &mut MapDoc, applied: bool) -> Change {
        let change = if applied {
            match &cmd {
                Command::PaintTiles { tiles, .. } => Change::Tiles(tiles.keys().copied().collect()),
                _ => unreachable!("only strokes are pushed already applied"),
            }
        } else {
            cmd.redo(doc)
        };
        if self.clean.is_some_and(|c| c > self.done.len()) {
            self.clean = None; // the saved state was in the redo part, now gone
        }
        self.undone.clear();
        self.done.push(cmd);
        change
    }

    pub fn undo(&mut self, doc: &mut MapDoc) -> Option<Change> {
        let mut cmd = self.done.pop()?;
        let change = cmd.undo(doc);
        self.undone.push(cmd);
        Some(change)
    }

    pub fn redo(&mut self, doc: &mut MapDoc) -> Option<Change> {
        let mut cmd = self.undone.pop()?;
        let change = cmd.redo(doc);
        self.done.push(cmd);
        Some(change)
    }

    pub fn undo_text(&self) -> Option<String> {
        self.done.last().map(Command::text)
    }

    pub fn redo_text(&self) -> Option<String> {
        self.undone.last().map(Command::text)
    }

    pub fn is_clean(&self) -> bool {
        self.clean == Some(self.done.len())
    }

    pub fn set_clean(&mut self) {
        self.clean = Some(self.done.len());
    }

    pub fn clear(&mut self) {
        *self = UndoStack::new();
    }
}
