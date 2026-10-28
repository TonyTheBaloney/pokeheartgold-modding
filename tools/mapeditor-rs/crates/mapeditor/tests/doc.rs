// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The editor's data layer and undo stack on this repository's maps, following the
//! checks in tools/mapeditor/tests and docs/gen4map/CHANGE-0004-map-editor.md §1.
//! Edits run on a copy of the files they touch (a scratch project whose manifest
//! points at copies), so the checkout is never written. Skipped outside the checkout.

use std::path::{Path, PathBuf};

use gen4map_format::project::Project;
use mapeditor::commands::{Command, UndoStack};
use mapeditor::doc::{MapDoc, SaveError};
use serde_json::{json, Value};

fn root() -> Option<PathBuf> {
    let r = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../..").canonicalize().ok()?;
    r.join("data/gen4map.json").is_file().then_some(r)
}

fn copy_dir(from: &Path, to: &Path) {
    std::fs::create_dir_all(to).unwrap();
    for e in std::fs::read_dir(from).unwrap() {
        let e = e.unwrap();
        let p = e.path();
        if p.is_dir() {
            copy_dir(&p, &to.join(e.file_name()));
        } else {
            std::fs::copy(&p, to.join(e.file_name())).unwrap();
        }
    }
}

/// A scratch project: copies of data/maps, data/layouts, the land data the map uses,
/// the manifest and maps.h. Returns its root.
fn scratch(root: &Path, name: &str, lands: &[u16]) -> PathBuf {
    let dir = std::env::temp_dir().join(format!("mapeditor-rs-test-{}-{}", name, std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    copy_dir(&root.join("data/maps"), &dir.join("data/maps"));
    copy_dir(&root.join("data/layouts"), &dir.join("data/layouts"));
    for &n in lands {
        copy_dir(&root.join(format!("data/landdata/{:04}", n)), &dir.join(format!("data/landdata/{:04}", n)));
    }
    std::fs::create_dir_all(dir.join("include/constants")).unwrap();
    std::fs::copy(root.join("include/constants/maps.h"), dir.join("include/constants/maps.h")).unwrap();
    std::fs::copy(root.join("data/gen4map.json"), dir.join("data/gen4map.json")).unwrap();
    dir
}

/// Every file under dir, with its bytes.
fn snapshot(dir: &Path) -> Vec<(PathBuf, Vec<u8>)> {
    let mut out = Vec::new();
    let mut stack = vec![dir.to_path_buf()];
    while let Some(d) = stack.pop() {
        for e in std::fs::read_dir(d).unwrap() {
            let p = e.unwrap().path();
            if p.is_dir() {
                stack.push(p);
            } else {
                out.push((p.clone(), std::fs::read(&p).unwrap()));
            }
        }
    }
    out.sort();
    out
}

#[test]
fn every_map_opens_and_saves_unchanged() {
    let Some(root) = root() else { return };
    let project = Project::open(&root).unwrap();
    for m in &project.maps {
        let mut doc = MapDoc::open(&project, &m.folder).unwrap_or_else(|e| panic!("{}: {}", m.folder, e));
        assert!(doc.chunk_errors.is_empty(), "{}: {:?}", m.folder, doc.chunk_errors);
        assert!(!doc.modified());
        // nothing to write: save touches no file (B7: no empty sections added)
        let before = std::fs::read(&doc.map_json).unwrap();
        doc.save(&project, false).unwrap();
        assert_eq!(std::fs::read(&doc.map_json).unwrap(), before, "{}", m.folder);
        // the serialized document is byte-identical too, as a forced write would produce
        assert_eq!(
            gen4map_format::json::to_string(&doc.data, gen4map_format::json::Style::of(&String::from_utf8(before).unwrap())).into_bytes(),
            std::fs::read(&doc.map_json).unwrap()
        );
    }
}

#[test]
fn edits_save_and_undo() {
    let Some(root) = root() else { return };
    let real = Project::open(&root).unwrap();
    let doc = MapDoc::open(&real, "Cherrygrove").unwrap();
    let lands: Vec<u16> = doc.chunks.keys().copied().collect();
    let dir = scratch(&root, "edits", &lands);
    let project = Project::open(&dir).unwrap();
    let original = snapshot(&dir);
    let mut doc = MapDoc::open(&project, "Cherrygrove").unwrap();
    let mut undo = UndoStack::new();
    assert!(undo.is_clean());

    // paint one tile, as a stroke does: applied first, then pushed
    let (x0, y0, _, _) = doc.bounds();
    let (x, y) = ((x0 * 32 + 5) as i64, (y0 * 32 + 5) as i64);
    let old = doc.tile(x, y).unwrap();
    let new = (1 - old.0, old.1, old.2);
    doc.set_tile(x, y, new);
    undo.push(Command::PaintTiles { name: "Paint collision".into(), tiles: [((x, y), (old, new))].into() }, &mut doc, true);
    assert!(!undo.is_clean());
    undo.undo(&mut doc);
    assert_eq!(doc.tile(x, y), Some(old));
    assert!(undo.is_clean(), "undoing back to the saved state is clean (S1)");
    undo.redo(&mut doc);
    assert_eq!(doc.tile(x, y), Some(new));

    // move an event, set a field, add an object, delete it, undo the delete
    let (ex, ey) = doc.event_xy("warp_events", 0).unwrap();
    undo.push(Command::MoveEvents(vec![("warp_events".into(), 0, (ex, ey), (ex + 1, ey))]), &mut doc, false);
    assert_eq!(doc.event_xy("warp_events", 0), Some((ex + 1, ey)));
    let old_flag = doc.event("object_events", 0).unwrap().get("flag").cloned();
    undo.push(
        Command::SetEventField { section: "object_events".into(), index: 0, key: "flag".into(), old: old_flag.clone(), new: Some(json!("FLAG_NOTHING")) },
        &mut doc,
        false,
    );
    let n = doc.events("object_events").len();
    undo.push(Command::AddEvent { section: "object_events".into(), x: ex, y: ey, index: None, event: None }, &mut doc, false);
    assert_eq!(doc.events("object_events").len(), n + 1);
    let added = doc.event("object_events", n).unwrap().clone();
    assert_eq!(added["local_id"], json!("obj_T21_new1"));
    undo.push(Command::RemoveEvent { section: "object_events".into(), index: n, event: None }, &mut doc, false);
    undo.undo(&mut doc);
    assert_eq!(doc.event("object_events", n), Some(&added));

    // events can only be on the map's own cells (B4, S4)
    assert!(doc.on_map(ex, ey));
    assert!(!doc.on_map(-1, 0));

    // save: map.json, the painted cell's permissions.txt and ids.h (S3) change, nothing else
    doc.save(&project, false).unwrap();
    undo.set_clean();
    let after = snapshot(&dir);
    let changed: Vec<String> = original
        .iter()
        .zip(&after)
        .filter(|(a, b)| a.1 != b.1)
        .map(|(a, _)| a.0.strip_prefix(&dir).unwrap().display().to_string())
        .collect();
    let land = doc.cell_land(x as usize / 32, y as usize / 32).unwrap();
    let mut expected = vec![
        "data/maps/Cherrygrove/ids.h".to_string(),
        "data/maps/Cherrygrove/map.json".to_string(),
        format!("data/landdata/{:04}/permissions.txt", land),
    ];
    expected.sort();
    let mut changed_sorted = changed.clone();
    changed_sorted.sort();
    assert_eq!(changed_sorted, expected);
    let ids = std::fs::read_to_string(dir.join("data/maps/Cherrygrove/ids.h")).unwrap();
    assert!(ids.contains("#define obj_T21_new1 6\n"), "{}", ids);

    // reopened, the edits are there
    let reopened = MapDoc::open(&project, "Cherrygrove").unwrap();
    assert_eq!(reopened.tile(x, y), Some(new));
    assert_eq!(reopened.event_xy("warp_events", 0), Some((ex + 1, ey)));
    assert_eq!(reopened.event("object_events", 0).unwrap()["flag"], json!("FLAG_NOTHING"));

    // a file changed by something else is reported, not overwritten (S9)
    let mut doc = reopened;
    doc.set_header_field("weather", Some(json!(1)));
    std::thread::sleep(std::time::Duration::from_millis(20));
    let text = std::fs::read_to_string(&doc.map_json).unwrap();
    std::fs::write(&doc.map_json, text.replace("\"weather\": 0", "\"weather\": 2")).unwrap();
    match doc.save(&project, false) {
        Err(SaveError::ChangedOnDisk(p)) => assert_eq!(p, ["data/maps/Cherrygrove/map.json"]),
        other => panic!("expected ChangedOnDisk, got {:?}", other),
    }
    doc.save(&project, true).unwrap();
    let v: Value = serde_json::from_str(&std::fs::read_to_string(&doc.map_json).unwrap()).unwrap();
    assert_eq!(v["weather"], json!(1));
    std::fs::remove_dir_all(dir).unwrap();
}

#[test]
fn undo_clean_state() {
    let Some(root) = root() else { return };
    let project = Project::open(&root).unwrap();
    let mut doc = MapDoc::open(&project, "Cherrygrove").unwrap();
    let mut undo = UndoStack::new();
    let set = |v| Command::SetHeaderField { key: "weather".into(), old: Some(json!(0)), new: Some(json!(v)) };
    undo.push(set(1), &mut doc, false);
    undo.set_clean();
    undo.undo(&mut doc);
    assert!(!undo.is_clean());
    // a new edit after undoing past the saved state: that state can't come back
    undo.push(set(2), &mut doc, false);
    assert!(!undo.is_clean());
    undo.undo(&mut doc);
    assert!(!undo.is_clean());
    assert_eq!(doc.data["weather"], json!(0));
}
