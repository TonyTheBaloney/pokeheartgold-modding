// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Draw one cell to a PNG: cargo run --example render_cell -- ROOT LAND AREA OUT.png

use gen4map_format::manifest::Manifest;
use gen4map_format::props;
use gen4map_render::{Renderer, Sources};

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let root = std::path::PathBuf::from(&a[1]);
    let (land, area): (u16, u16) = (a[2].parse().unwrap(), a[3].parse().unwrap());
    let m = Manifest::load(&root).unwrap();
    let r = Renderer::new(Sources::from_manifest(&root, &m));
    let p = props::load(&root.join(&m.paths.landdata).join(format!("{:04}/props.json", land))).unwrap();
    let t = std::time::Instant::now();
    let img = r.render_cell(land, area, &p, 0);
    eprintln!("{:?}, errors {:?}", t.elapsed(), r.errors());
    let f = std::fs::File::create(&a[4]).unwrap();
    let mut e = png::Encoder::new(f, img.width as u32, img.height as u32);
    e.set_color(png::ColorType::Rgba);
    e.write_header().unwrap().write_image_data(&img.rgba).unwrap();
}
