// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! The decoders against mapkit's (tools/mapeditor-rs/tests/oracle.py) on this
//! repository's models and textures. Skipped outside the checkout.

use std::path::PathBuf;
use std::process::Command;

use gen4map_nitro::areatex;
use gen4map_nitro::model::{Nsbmd, Triangle};
use gen4map_nitro::narc::Narc;
use gen4map_nitro::texture::TextureSet;
use serde_json::Value;

fn root() -> Option<PathBuf> {
    let r = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../..").canonicalize().ok()?;
    r.join("data/gen4map.json").is_file().then_some(r)
}

fn oracle(root: &PathBuf, args: &[&str]) -> Value {
    let out = Command::new("python3")
        .arg(root.join("tools/mapeditor-rs/tests/oracle.py"))
        .arg(root)
        .args(args)
        .output()
        .expect("python3");
    assert!(out.status.success(), "oracle {:?}: {}", args, String::from_utf8_lossy(&out.stderr));
    serde_json::from_slice(&out.stdout).unwrap()
}

fn close(a: &Value, b: f64) -> bool {
    (a.as_f64().unwrap() - b).abs() < 1e-9
}

fn same_triangles(py: &Value, rs: &[Triangle], what: &str) {
    let py = py.as_array().unwrap();
    assert_eq!(py.len(), rs.len(), "{}: triangle count", what);
    for (i, (p, t)) in py.iter().zip(rs).enumerate() {
        for k in 0..3 {
            let v = &t.v[k];
            for j in 0..3 {
                assert!(close(&p["pos"][k][j], v.pos[j]), "{} tri {} pos: {} vs {:?}", what, i, p["pos"], v.pos);
                assert_eq!(p["color"][k][j], v.color[j], "{} tri {} color", what, i);
            }
            for j in 0..2 {
                assert!(close(&p["uv"][k][j], v.uv[j]), "{} tri {} uv", what, i);
            }
        }
        assert_eq!(p["material"].as_str(), t.material.as_ref().map(|m| m.name.as_str()), "{} tri {} material", what, i);
    }
}

#[test]
fn land_meshes_match_python() {
    let Some(root) = root() else { return };
    for n in [0, 1, 89, 117, 208, 221, 300, 450, 600, 675] {
        let data = std::fs::read(root.join(format!("data/landdata/{:04}/model.nsbmd", n))).unwrap();
        let rs = Nsbmd::read(&data).unwrap().triangles().unwrap();
        same_triangles(&oracle(&root, &["mesh", &n.to_string()]), &rs, &format!("land {}", n));
    }
}

#[test]
fn prop_meshes_match_python() {
    let Some(root) = root() else { return };
    for (kind, path) in [(0, "files/a/1/4/8"), (1, "files/a/0/4/0")] {
        let narc = Narc::open(&root.join(path)).unwrap();
        let step = (narc.len() / 12).max(1);
        for n in (0..narc.len()).step_by(step) {
            let rs = Nsbmd::read(narc.get(n).unwrap()).and_then(|m| m.triangles());
            let out = Command::new("python3")
                .arg(root.join("tools/mapeditor-rs/tests/oracle.py"))
                .arg(&root)
                .args(["prop-mesh", &kind.to_string(), &n.to_string()])
                .output()
                .unwrap();
            match rs {
                Ok(rs) => same_triangles(&serde_json::from_slice(&out.stdout).unwrap(), &rs, &format!("prop {} {}", kind, n)),
                Err(e) => assert!(!out.status.success(), "prop {} {}: Rust failed ({}) but Python didn't", kind, n, e),
            }
        }
    }
}

#[test]
fn area_textures_match_python() {
    let Some(root) = root() else { return };
    for set in [0, 2, 7, 20] {
        let dir = root.join(format!("data/area_textures/{:03}", set));
        if !dir.is_dir() {
            continue;
        }
        let ts = areatex::read_set(&dir).unwrap();
        for t in ts.textures.iter() {
            // with its first palette and with every texture's own-named palette, as the terrain asks
            for pal in ts.palettes.iter().map(|p| p.0.clone()).take(3) {
                let py = oracle(&root, &["texture", &set.to_string(), &t.name, &pal]);
                let img = ts.image(&t.name, Some(&pal)).unwrap();
                assert_eq!(py["width"], img.width);
                assert_eq!(py["height"], img.height);
                let hex: String = img.rgba.iter().map(|b| format!("{:02x}", b)).collect();
                assert!(py["rgba"] == hex.as_str(), "set {} texture {} palette {}", set, t.name, pal);
            }
        }
    }
}

#[test]
fn sprites_match_python() {
    let Some(root) = root() else { return };
    for n in [0, 12, 100, 250, 400] {
        let rel = format!("files/data/mmodel/mmodel/mmodel_{:08}.NSBTX", n);
        let Ok(data) = std::fs::read(root.join(&rel)) else { continue };
        let ts = TextureSet::read_nsbtx(&data).unwrap();
        let first_pal = ts.palettes.first().map(|p| p.0.clone());
        for t in ts.textures.iter().take(4) {
            let py = oracle(&root, &["nsbtx", &rel, &t.name, "-"]);
            let img = ts.image(&t.name, first_pal.as_deref()).unwrap();
            let hex: String = img.rgba.iter().map(|b| format!("{:02x}", b)).collect();
            assert!(py["rgba"] == hex.as_str(), "{} {}", rel, t.name);
        }
    }
}

#[test]
fn heights_match_python() {
    use gen4map_nitro::bdhc::{Bdhc, Mode, FX};
    let Some(root) = root() else { return };
    for n in [0, 30, 89, 208, 221, 450] {
        let b = Bdhc::read(&std::fs::read(root.join(format!("data/landdata/{:04}/terrain.bdhc", n))).unwrap()).unwrap();
        let py = oracle(&root, &["heights", &n.to_string()]);
        let at = |t: i64| (t * 16 + 8 - 256) * FX;
        let rs: Vec<Option<i64>> = (0..32).flat_map(|z| (0..32).map(move |x| (x, z))).map(|(x, z)| b.height(at(x), at(z), Mode::Nearest, 0)).collect();
        assert_eq!(py, serde_json::to_value(rs).unwrap(), "land {}", n);
    }
}
