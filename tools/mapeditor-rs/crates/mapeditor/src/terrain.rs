// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Drawing cells' terrain off the UI thread. Pictures are keyed by what they're made
//! of (land data, area, altitude), so maps sharing cells share pictures, and a
//! picture is drawn once per session unless its props change.
//!
//! A worker that fails (a damaged model) reports an empty picture and an error; a
//! panic in a worker is caught and reported the same way, so the editor keeps going.

use std::collections::{HashMap, VecDeque};
use std::sync::mpsc::{channel, Receiver, Sender};
use std::sync::{Arc, Condvar, Mutex};

use gen4map_format::props::Prop;
use gen4map_nitro::Image;
use gen4map_render::Renderer;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct CellKey {
    pub land: u16,
    pub area: u16,
    pub altitude: u8,
}

struct Job {
    key: CellKey,
    props: Vec<Prop>,
}

struct Queue {
    jobs: Mutex<VecDeque<Job>>,
    ready: Condvar,
}

pub enum State {
    Pending,
    Ready(egui::TextureHandle),
}

pub struct TerrainCache {
    pub renderer: Arc<Renderer>,
    queue: Arc<Queue>,
    results: Receiver<(CellKey, Image)>,
    states: HashMap<CellKey, State>,
}

impl TerrainCache {
    pub fn new(renderer: Renderer, ctx: egui::Context) -> TerrainCache {
        let renderer = Arc::new(renderer);
        let queue = Arc::new(Queue { jobs: Mutex::new(VecDeque::new()), ready: Condvar::new() });
        let (tx, rx) = channel();
        let threads = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(2).saturating_sub(1).clamp(1, 8);
        for i in 0..threads {
            let (renderer, queue, tx, ctx): (Arc<Renderer>, Arc<Queue>, Sender<_>, _) = (renderer.clone(), queue.clone(), tx.clone(), ctx.clone());
            std::thread::Builder::new()
                .name(format!("terrain-{}", i))
                .spawn(move || loop {
                    let job = {
                        let mut jobs = queue.jobs.lock().unwrap();
                        loop {
                            if let Some(j) = jobs.pop_front() {
                                break j;
                            }
                            jobs = queue.ready.wait(jobs).unwrap();
                        }
                    };
                    let k = job.key;
                    let img = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                        renderer.render_cell(k.land, k.area, &job.props, k.altitude)
                    }))
                    .unwrap_or_else(|_| Image { width: 1, height: 1, rgba: vec![0; 4] });
                    if tx.send((k, img)).is_err() {
                        return; // the editor is gone
                    }
                    ctx.request_repaint();
                })
                .expect("starting a terrain thread");
        }
        TerrainCache { renderer, queue, results: rx, states: HashMap::new() }
    }

    /// Take finished pictures into textures. Call once per frame.
    pub fn poll(&mut self, ctx: &egui::Context) {
        while let Ok((key, img)) = self.results.try_recv() {
            let color = egui::ColorImage::from_rgba_unmultiplied([img.width, img.height], &img.rgba);
            let name = format!("terrain {:04} area {} alt {}", key.land, key.area, key.altitude);
            let tex = ctx.load_texture(name, color, egui::TextureOptions::NEAREST);
            self.states.insert(key, State::Ready(tex));
        }
    }

    /// The picture, asking for it if it isn't there yet. `first`: put it at the front of
    /// the queue (cells in view).
    pub fn get(&mut self, key: CellKey, props: &[Prop], first: bool) -> Option<&egui::TextureHandle> {
        if let std::collections::hash_map::Entry::Vacant(e) = self.states.entry(key) {
            e.insert(State::Pending);
            let mut jobs = self.queue.jobs.lock().unwrap();
            let job = Job { key, props: props.to_vec() };
            if first {
                jobs.push_front(job);
            } else {
                jobs.push_back(job);
            }
            self.queue.ready.notify_one();
        }
        match self.states.get(&key) {
            Some(State::Ready(t)) => Some(t),
            _ => None,
        }
    }

    /// Cells still being drawn.
    pub fn pending(&self) -> usize {
        self.states.values().filter(|s| matches!(s, State::Pending)).count()
    }

    /// Forget pictures of an area (to redraw them, e.g. after its files changed).
    pub fn forget_area(&mut self, area: u16) {
        self.states.retain(|k, s| k.area != area || matches!(s, State::Pending));
    }

    pub fn forget_all(&mut self) {
        self.states.retain(|_, s| matches!(s, State::Pending));
    }
}
