// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Overworld sprites of objects, for the map view (a port of
//! tools/mapeditor/mapeditor/sprites.py): one frame of each object's graphics_id,
//! facing its facing_dir.
//!
//! graphics_id -> NSBTX file comes from `mapkit export-constants` (the
//! gObjectEventGraphicsInfos table). The textures are named <name>.1 ... <name>.N;
//! in that order:
//!
//! - 16 frames (standard NPCs; 17 with an extra pose): four per facing, north, south,
//!   west, east, the first of each four standing;
//! - 8 frames (follow-Pokémon): two per facing in the same order;
//! - anything else (still objects, trees, legendaries' poses): frame 1.
//!
//! SPRITE_VAR_n objects take their sprite from VAR_OBJ_n when the map loads, so they
//! can't be drawn here. Animation previews movement_type in place; the timing is the
//! editor's, not the game's.

use std::collections::{BTreeMap, HashMap};
use std::path::PathBuf;
use std::sync::Arc;

use gen4map_nitro::texture::TextureSet;
use gen4map_nitro::Image;

pub const N: usize = 0;
pub const S: usize = 1;
pub const W: usize = 2;
pub const E: usize = 3;
pub const TURN_TICKS: u64 = 8;
pub const WALK_TICKS: u64 = 16;

pub fn facing_index(v: &serde_json::Value) -> usize {
    match v {
        serde_json::Value::Number(n) => n.as_u64().unwrap_or(1) as usize,
        serde_json::Value::String(s) => match s.as_str() {
            "DIR_NORTH" => N,
            "DIR_WEST" => W,
            "DIR_EAST" => E,
            _ => S,
        },
        _ => S,
    }
}

fn frames_per_facing(frames: usize) -> Option<usize> {
    match frames {
        16 | 17 => Some(4),
        8 => Some(2),
        _ => None,
    }
}

/// Index of a frame in a sheet of `frames`: the standing frame for a facing (0-3), plus
/// `step` into the walk cycle for sheets that have one.
pub fn frame_for(frames: usize, facing: usize, step: usize) -> usize {
    match frames_per_facing(frames) {
        Some(per) if facing <= 3 => facing * per + step % per,
        _ => 0,
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    Walk,
    Turn,
}

/// (kind, directions) for a movement type, None if it stands still. Directions
/// None: its own facing, then the opposite.
pub fn movement(t: &str) -> Option<(Kind, Option<Vec<usize>>)> {
    use Kind::*;
    let fixed: Option<(Kind, &[usize])> = match t {
        "MOVEMENT_TYPE_LOOK_AROUND" => Some((Turn, &[S, W, N, E])), // random in the game
        "MOVEMENT_TYPE_WANDER_AROUND" => Some((Walk, &[S, W, N, E])),
        "MOVEMENT_TYPE_WANDER_UP_DOWN" => Some((Walk, &[N, S])),
        "MOVEMENT_TYPE_WANDER_LEFT_RIGHT" => Some((Walk, &[W, E])),
        "MOVEMENT_TYPE_LOOK_UP_LEFT" => Some((Turn, &[N, W])),
        "MOVEMENT_TYPE_LOOK_UP_RIGHT" => Some((Turn, &[N, E])),
        "MOVEMENT_TYPE_LOOK_DOWN_LEFT" => Some((Turn, &[S, W])),
        "MOVEMENT_TYPE_LOOK_DOWN_RIGHT" => Some((Turn, &[S, E])),
        "MOVEMENT_TYPE_LOOK_UP_DOWN_LEFT" => Some((Turn, &[N, S, W])),
        "MOVEMENT_TYPE_LOOK_UP_DOWN_RIGHT" => Some((Turn, &[N, S, E])),
        "MOVEMENT_TYPE_LOOK_UP_LEFT_RIGHT" => Some((Turn, &[N, W, E])),
        "MOVEMENT_TYPE_LOOK_DOWN_LEFT_RIGHT" => Some((Turn, &[S, W, E])),
        "MOVEMENT_TYPE_LOOK_UP_DOWN" => Some((Turn, &[N, S])),
        "MOVEMENT_TYPE_LOOK_LEFT_RIGHT" => Some((Turn, &[W, E])),
        "MOVEMENT_TYPE_SPIN_COUNTERCLOCKWISE" => Some((Turn, &[N, W, S, E])),
        "MOVEMENT_TYPE_SPIN_CLOCKWISE" | "MOVEMENT_TYPE_ALTERNATING_SPIN" => Some((Turn, &[N, E, S, W])),
        _ => None,
    };
    if let Some((k, d)) = fixed {
        return Some((k, Some(d.to_vec())));
    }
    if t == "MOVEMENT_TYPE_BACK_AND_FORTH" {
        return Some((Walk, None));
    }
    // MOVEMENT_TYPE_PATH_<D>_<D>_<D>_<D>[_n]: walks a rectangle in the named directions
    let rest = t.strip_prefix("MOVEMENT_TYPE_PATH_")?;
    let mut words: Vec<&str> = rest.split('_').collect();
    if words.len() == 5 && words[4].chars().all(|c| c.is_ascii_digit()) && !words[4].is_empty() {
        words.pop();
    }
    if words.len() != 4 {
        return None;
    }
    let dirs: Option<Vec<usize>> = words
        .iter()
        .map(|w| match *w {
            "NORTH" => Some(N),
            "SOUTH" => Some(S),
            "WEST" => Some(W),
            "EAST" => Some(E),
            _ => None,
        })
        .collect();
    Some((Walk, Some(dirs?)))
}

/// (facing 0-3, walk step) of an object at animation tick `tick`.
pub fn pose(movement_type: &str, facing: usize, frames: usize, tick: u64) -> (usize, usize) {
    let per = frames_per_facing(frames);
    let mut step = if per == Some(2) { ((tick / 2) % 2) as usize } else { 0 }; // follow-Pokémon step in place
    let Some((kind, dirs)) = movement(movement_type) else { return (facing, step) };
    let opposite = |f: usize| match f {
        N => S,
        S => N,
        W => E,
        E => W,
        f => f,
    };
    let dirs = dirs.unwrap_or_else(|| vec![facing, opposite(facing)]);
    let ticks = if kind == Kind::Walk { WALK_TICKS } else { TURN_TICKS };
    let facing = dirs[((tick / ticks) % dirs.len() as u64) as usize];
    if kind == Kind::Walk && per == Some(4) {
        step = (tick % 4) as usize;
    }
    (facing, step)
}

struct Sheet {
    set: TextureSet,
    /// Texture names in frame order.
    frames: Vec<String>,
    palette: Option<String>,
}

pub struct SpriteImages {
    root: PathBuf,
    paths: BTreeMap<String, String>,
    sheets: HashMap<String, Option<Arc<Sheet>>>,
    images: HashMap<(String, usize, usize), Option<Arc<Image>>>,
    /// Why the sprite table is missing (the constants export failed), if it is.
    pub error: Option<String>,
}

impl SpriteImages {
    pub fn new(root: PathBuf, paths: BTreeMap<String, String>, error: Option<String>) -> SpriteImages {
        SpriteImages { root, paths, sheets: HashMap::new(), images: HashMap::new(), error }
    }

    fn sheet(&mut self, path: &str) -> Option<Arc<Sheet>> {
        if let Some(s) = self.sheets.get(path) {
            return s.clone();
        }
        let sheet = std::fs::read(self.root.join(path)).ok().and_then(|d| TextureSet::read_nsbtx(&d).ok()).and_then(|set| {
            let number = |n: &str| -> u64 {
                let digits: String = n.chars().rev().take_while(char::is_ascii_digit).collect();
                digits.chars().rev().collect::<String>().parse().unwrap_or(0)
            };
            let mut frames: Vec<String> = set.textures.iter().map(|t| t.name.clone()).collect();
            frames.sort_by_key(|n| number(n)); // stable: equal numbers keep file order
            let palette = set.palettes.first().map(|p| p.0.clone());
            (!frames.is_empty()).then(|| Arc::new(Sheet { set, frames, palette }))
        });
        self.sheets.insert(path.to_string(), sheet.clone());
        sheet
    }

    /// None if the sprite can be drawn, else a short reason.
    pub fn why_not(&mut self, graphics_id: &str) -> Option<String> {
        if let Some(n) = graphics_id.strip_prefix("SPRITE_VAR_").filter(|n| n.chars().all(|c| c.is_ascii_digit())) {
            return Some(format!("set when the map loads, from VAR_OBJ_{}", n));
        }
        let Some(path) = self.paths.get(graphics_id).cloned() else {
            return Some(self.error.clone().unwrap_or_else(|| "no row in gObjectEventGraphicsInfos".into()));
        };
        if self.sheet(&path).is_none() {
            return Some(format!("no texture file {}", path));
        }
        None
    }

    /// How many frames the sprite has (0 if it can't be drawn).
    pub fn frames(&mut self, graphics_id: &str) -> usize {
        if self.why_not(graphics_id).is_some() {
            return 0;
        }
        let path = self.paths[graphics_id].clone();
        self.sheet(&path).map(|s| s.frames.len()).unwrap_or(0)
    }

    /// The object's frame for a facing and walk step (0 = standing), or None (see why_not).
    pub fn image(&mut self, graphics_id: &str, facing: usize, step: usize) -> Option<Arc<Image>> {
        let key = (graphics_id.to_string(), facing, step);
        if let Some(i) = self.images.get(&key) {
            return i.clone();
        }
        let img = if self.why_not(graphics_id).is_none() {
            let path = self.paths[graphics_id].clone();
            self.sheet(&path).and_then(|s| {
                let name = &s.frames[frame_for(s.frames.len(), facing, step)];
                s.set.image(name, s.palette.as_deref()).map(Arc::new)
            })
        } else {
            None
        };
        self.images.insert(key, img.clone());
        img
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn poses() {
        assert_eq!(frame_for(16, S, 0), 4);
        assert_eq!(frame_for(8, E, 1), 7);
        assert_eq!(frame_for(1, E, 3), 0);
        assert_eq!(pose("MOVEMENT_TYPE_FACE_DOWN", S, 16, 99), (S, 0));
        assert_eq!(pose("MOVEMENT_TYPE_WANDER_UP_DOWN", S, 16, 17), (S, 1));
        assert_eq!(pose("MOVEMENT_TYPE_LOOK_LEFT_RIGHT", N, 16, 8), (E, 0));
        assert_eq!(pose("MOVEMENT_TYPE_BACK_AND_FORTH", W, 16, 16), (E, 0));
        assert_eq!(pose("MOVEMENT_TYPE_FACE_DOWN", S, 8, 2), (S, 1));
        assert_eq!(movement("MOVEMENT_TYPE_PATH_NORTH_EAST_SOUTH_WEST_2").unwrap().1, Some(vec![N, E, S, W]));
        assert!(movement("MOVEMENT_TYPE_PATH_NORTH").is_none());
    }
}
