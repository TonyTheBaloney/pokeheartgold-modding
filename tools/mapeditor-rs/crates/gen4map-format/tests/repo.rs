// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The format crate against this repository's data: every file read and written back
//! unchanged, and the same answers as the Python tools (tests/oracle.py).
//! Skipped when the crate isn't inside the checkout.

use std::collections::{BTreeMap, BTreeSet};
use std::path::PathBuf;
use std::process::Command;

use gen4map_format::layout::Layout;
use gen4map_format::permissions::Permissions;
use gen4map_format::project::Project;
use gen4map_format::{json, props};
use serde_json::Value;

fn root() -> Option<PathBuf> {
    let r = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../..").canonicalize().ok()?;
    r.join("data/gen4map.json").is_file().then_some(r)
}

pub fn oracle(root: &PathBuf, args: &[&str]) -> Value {
    let out = Command::new("python3")
        .arg(root.join("tools/mapeditor-rs/tests/oracle.py"))
        .arg(root)
        .args(args)
        .output()
        .expect("python3");
    assert!(out.status.success(), "oracle {:?}: {}", args, String::from_utf8_lossy(&out.stderr));
    serde_json::from_slice(&out.stdout).unwrap()
}

#[test]
fn map_json_round_trip() {
    let Some(root) = root() else { return };
    let mut n = 0;
    for e in std::fs::read_dir(root.join("data/maps")).unwrap() {
        let p = e.unwrap().path().join("map.json");
        if !p.is_file() {
            continue;
        }
        let raw = std::fs::read_to_string(&p).unwrap();
        let (v, style) = json::load(&p).unwrap();
        assert_eq!(json::to_string(&v, style), raw, "{}", p.display());
        n += 1;
    }
    assert!(n > 500, "only {} map.json files", n);
}

#[test]
fn landdata_round_trip() {
    let Some(root) = root() else { return };
    let project = Project::open(&root).unwrap();
    let mut n = 0u16;
    while project.landdata_dir(n).is_dir() {
        let dir = project.landdata_dir(n);
        let raw = std::fs::read_to_string(dir.join("permissions.txt")).unwrap();
        let p = Permissions::from_text(&raw, "permissions.txt").unwrap();
        assert_eq!(p.to_text(), raw, "{}", dir.display());
        let props = props::load(&dir.join("props.json")).unwrap();
        assert!(props.len() <= props::MAX_PROPS);
        n += 1;
    }
    assert!(n > 600, "only {} land data cells", n);
}

#[test]
fn layouts_match_python() {
    let Some(root) = root() else { return };
    let project = Project::open(&root).unwrap();
    let py = oracle(&root, &["layouts"]);
    let py = py.as_object().unwrap();
    assert_eq!(py.len(), project.layouts.len());
    for l in &project.layouts {
        let lay: Layout = project.load_layout(&l.dir).unwrap();
        let p = &py[&l.dir];
        assert_eq!(p["width"], lay.width, "{}", l.dir);
        assert_eq!(p["height"], lay.height, "{}", l.dir);
        let land: Vec<Option<u64>> = serde_json::from_value(p["land"].clone()).unwrap();
        assert_eq!(land, lay.land.iter().map(|v| v.map(u64::from)).collect::<Vec<_>>(), "{}", l.dir);
        assert_eq!(p["maps"], serde_json::to_value(&lay.maps).unwrap(), "{}", l.dir);
        assert_eq!(p["altitudes"], serde_json::to_value(&lay.altitudes).unwrap(), "{}", l.dir);
    }
}

#[test]
fn maps_match_python() {
    let Some(root) = root() else { return };
    let project = Project::open(&root).unwrap();
    let py = oracle(&root, &["maps"]);
    let py = py.as_array().unwrap();
    assert_eq!(py.len(), project.maps.len());
    for (p, m) in py.iter().zip(&project.maps) {
        assert_eq!(p[0], m.folder.as_str());
        assert_eq!(p[1], m.name.as_str());
        assert_eq!(p[2], m.id);
        assert_eq!(root.join(p[3].as_str().unwrap()), project.ids_h(m), "{}", m.name);
        assert_eq!(p[4].as_str(), project.map_layout(m).ok().as_deref(), "{}", m.name);
        assert_eq!(project.find_map(&m.folder), Some(m));
    }
    assert_eq!(project.find_map("T21").map(|m| m.folder.as_str()), Some("Cherrygrove"));
    assert_eq!(project.find_map("cherrygrove").map(|m| m.folder.as_str()), Some("Cherrygrove"));
}

#[test]
fn land_index_matches_python() {
    let Some(root) = root() else { return };
    let project = Project::open(&root).unwrap();
    let py: BTreeMap<String, BTreeSet<String>> = serde_json::from_value(oracle(&root, &["land-index"])).unwrap();
    let rs: BTreeMap<String, BTreeSet<String>> =
        project.land_index().into_iter().map(|(k, v)| (k.to_string(), v)).collect();
    assert_eq!(py, rs);
}
