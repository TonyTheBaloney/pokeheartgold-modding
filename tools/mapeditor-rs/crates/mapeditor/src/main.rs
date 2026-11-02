// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! mapeditor-rs [MAP] [--root DIR] [--3d | --wild]: start the editor, optionally on a
//! map (Cherrygrove, MAP_CHERRYGROVE, T21 or 67), optionally in the 3D or wild
//! encounters tab.

use std::path::PathBuf;

use gen4map_format::project::{find_root, Project};
use mapeditor::app::{Center, EditorApp};

fn main() -> std::process::ExitCode {
    let mut args = std::env::args().skip(1);
    let (mut root, mut start, mut center) = (None, None, Center::Map);
    while let Some(a) = args.next() {
        match a.as_str() {
            "--root" => root = args.next().map(PathBuf::from),
            "--3d" => center = Center::View3D,
            "--wild" => center = Center::Wild,
            "-h" | "--help" => {
                println!("usage: mapeditor-rs [MAP] [--root DIR] [--3d | --wild]\n\nMAP: Cherrygrove, MAP_CHERRYGROVE, T21 or 67. DIR: the checkout (default: found from the current directory). --3d: open in the 3D tab. --wild: open in the wild encounters tab.");
                return std::process::ExitCode::SUCCESS;
            }
            _ => start = Some(a),
        }
    }
    let here = std::env::current_dir().unwrap_or_default();
    let Some(root) = root.or_else(|| find_root(&here)) else {
        eprintln!("mapeditor-rs: not inside a checkout with data/gen4map.json (use --root)");
        return std::process::ExitCode::FAILURE;
    };
    let project = match Project::open(&root) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("mapeditor-rs: {}", e);
            return std::process::ExitCode::FAILURE;
        }
    };
    if let Some(m) = &start {
        if project.find_map(m).is_none() {
            eprintln!("mapeditor-rs: no map matches {:?}", m);
            return std::process::ExitCode::FAILURE;
        }
    }
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([1500.0, 950.0]).with_title("HGSS map editor").with_app_id("mapeditor-rs"),
        depth_buffer: 24,
        renderer: eframe::Renderer::Glow,
        ..Default::default()
    };
    let result = eframe::run_native("mapeditor-rs", options, Box::new(move |cc| Ok(Box::new(EditorApp::new(cc, project, start, center)))));
    match result {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("mapeditor-rs: {}", e);
            std::process::ExitCode::FAILURE
        }
    }
}
