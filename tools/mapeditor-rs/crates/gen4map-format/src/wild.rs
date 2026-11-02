// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-11-02
//! Wild encounter tables (docs/modding/wild-encounters.md): the `encounters` array of
//! gs_enc_data.json, one table per position, named by the `ENCDATA_` defines of
//! encounter_tables_narc.h. The build turns each table into an EncounterData
//! (include/wild_encounter.h) through gs_enc_data.json.txt, once per version.
//!
//! A species or level may differ between the versions: `{"HEARTGOLD": a, "SOULSILVER": b}`.
//! pick() reads one side of such a value, put() writes one side and joins the two
//! sides back into a plain value when they agree.

use std::path::Path;

use serde_json::{json, Value};

use crate::{bail, read_text, write_text, Result};

pub const VERSIONS: [&str; 2] = ["HEARTGOLD", "SOULSILVER"];
pub const NO_TABLE: &str = "ENCDATA_NA";
pub const NO_SPECIES: &str = "SPECIES_NONE";

/// One way to meet wild Pokémon: its key in a table, the JSON pointer of its
/// `{"rate", "mons"}` object, the chance of each slot and which slots other keys
/// replace (src/field/encounter_check.c).
pub struct Method {
    pub key: &'static str,
    pub label: &'static str,
    pub pointer: &'static str,
    pub odds: &'static [u8],
    pub note: &'static str,
}

impl Method {
    pub fn slots(&self) -> usize {
        self.odds.len()
    }

    /// Grass slots have one level and a species per time of day; the others a level
    /// range and one species.
    pub fn is_land(&self) -> bool {
        self.key == "land"
    }
}

pub const METHODS: [Method; 6] = [
    Method {
        key: "land",
        label: "Grass",
        pointer: "/land",
        odds: &[20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1],
        note: "A grass swarm replaces slots 0-1; Hoenn/Sinnoh Sound on the radio replace 2-3 and 4-5.",
    },
    Method { key: "surf", label: "Surfing", pointer: "/surf", odds: &[60, 30, 5, 4, 1], note: "A surfing swarm replaces slot 0." },
    Method { key: "rock_smash", label: "Rock Smash", pointer: "/rock_smash", odds: &[80, 20], note: "" },
    Method { key: "old_rod", label: "Old Rod", pointer: "/fishing/old_rod", odds: &[40, 30, 15, 10, 5], note: "A fishing swarm replaces slot 2." },
    Method {
        key: "good_rod",
        label: "Good Rod",
        pointer: "/fishing/good_rod",
        odds: &[40, 30, 15, 10, 5],
        note: "Night fishing replaces slot 3 at night; a fishing swarm replaces slots 0, 2 and 3.",
    },
    Method {
        key: "super_rod",
        label: "Super Rod",
        pointer: "/fishing/super_rod",
        odds: &[40, 30, 15, 10, 5],
        note: "Night fishing replaces slot 1 at night; a fishing swarm replaces every slot.",
    },
];

/// Grass species keys and their names.
pub const TIMES: [(&str, &str); 3] = [("morn", "Morning"), ("day", "Day"), ("nite", "Night")];

/// Pokégear radio replacements: two species each.
pub const RADIO: [(&str, &str); 2] = [("hoenn", "Hoenn Sound"), ("sinnoh", "Sinnoh Sound")];

/// Optional single species; a missing key builds as 0 (no species).
pub const EXTRAS: [(&str, &str); 4] =
    [("landSwarm", "Grass swarm"), ("surfSwarm", "Surfing swarm"), ("nightFish", "Night fishing"), ("fishSwarm", "Fishing swarm")];

/// The order of a table's keys in gs_enc_data.json.
const TABLE_KEYS: [&str; 11] =
    ["map", "land", "surf", "rock_smash", "fishing", "hoenn", "sinnoh", "landSwarm", "surfSwarm", "nightFish", "fishSwarm"];

pub fn is_split(v: &Value) -> bool {
    v.as_object().is_some_and(|o| VERSIONS.iter().any(|k| o.contains_key(*k)))
}

/// The value one version builds with (`None`: the value as written).
pub fn pick(v: &Value, version: Option<&str>) -> Value {
    match version {
        Some(ver) if is_split(v) => v.get(ver).cloned().unwrap_or(Value::Null),
        _ => v.clone(),
    }
}

/// `old` with one version's side set to `new` (`None`: both sides). Sides that agree
/// are written once.
pub fn put(old: &Value, version: Option<&str>, new: Value) -> Value {
    let Some(ver) = version else { return new };
    let side = |k: &str| if is_split(old) { old.get(k).cloned().unwrap_or(Value::Null) } else { old.clone() };
    let [hg, ss] = VERSIONS.map(|k| if k == ver { new.clone() } else { side(k) });
    if hg == ss {
        hg
    } else {
        json!({"HEARTGOLD": hg, "SOULSILVER": ss})
    }
}

/// Every value a field builds with: both sides of a split value, else the value.
fn sides(v: &Value) -> Vec<&Value> {
    if is_split(v) {
        VERSIONS.iter().filter_map(|k| v.get(*k)).collect()
    } else {
        vec![v]
    }
}

pub fn new_slot(method: &Method, species: &str, level: u8) -> Value {
    if method.is_land() {
        json!({"level": level, "species": {"morn": species, "day": species, "nite": species}})
    } else {
        json!({"level": {"min": level, "max": level}, "species": species})
    }
}

/// A table with no encounters, as the unused tables are written.
pub fn empty_table(label: &str) -> Value {
    let none = || json!({"rate": 0, "mons": []});
    json!({"map": label, "land": none(), "surf": none(), "rock_smash": none(),
        "fishing": {"old_rod": none(), "good_rod": none(), "super_rod": none()}, "hoenn": [], "sinnoh": []})
}

/// Where a missing table key goes: before the first key that follows it in the file's
/// order (at the end for keys outside that order).
pub fn key_position(obj: &serde_json::Map<String, Value>, key: &str) -> usize {
    let rank = |k: &str| TABLE_KEYS.iter().position(|t| *t == k);
    let Some(r) = rank(key) else { return obj.len() };
    obj.keys().position(|k| rank(k).is_some_and(|kr| kr > r)).unwrap_or(obj.len())
}

/// What would make a table build wrong or behave oddly in the game. `known(name)` says
/// whether a SPECIES_ name exists (always true when the names aren't known).
pub fn issues(table: &Value, known: &dyn Fn(&str) -> bool) -> Vec<String> {
    let mut out = Vec::new();
    let species_ok = |out: &mut Vec<String>, v: &Value, at: &str, active: bool| {
        for s in sides(v) {
            match s {
                Value::String(n) if !known(n) => out.push(format!("{}: {} is not a species", at, n)),
                Value::String(n) if active && n == NO_SPECIES => out.push(format!("{}: no species", at)),
                Value::String(_) => {}
                Value::Number(n) if n.as_u64().is_some_and(|n| n <= 0xFFFF) => {}
                v => out.push(format!("{}: {} is not a species", at, v)),
            }
        }
    };
    let level_ok = |out: &mut Vec<String>, v: Option<&Value>, at: &str| {
        for s in v.map(sides).unwrap_or_default() {
            if !s.as_u64().is_some_and(|n| (1..=100).contains(&n)) {
                out.push(format!("{}: level {} is not 1-100", at, s));
            }
        }
    };
    let rate = |m: &Method| table.pointer(m.pointer).and_then(|g| g.get("rate")).and_then(Value::as_u64).unwrap_or(0);
    for m in &METHODS {
        let Some(group) = table.pointer(m.pointer) else {
            out.push(format!("{}: missing", m.label));
            continue;
        };
        let r = group.get("rate").unwrap_or(&Value::Null);
        if !r.as_u64().is_some_and(|n| n <= 255) {
            out.push(format!("{}: rate {} is not 0-255", m.label, r));
        }
        let mons = group.get("mons").and_then(Value::as_array).map(Vec::as_slice).unwrap_or(&[]);
        let active = rate(m) > 0;
        if mons.len() > m.slots() || (active && mons.len() != m.slots()) {
            out.push(format!("{}: {} slots, needs {}", m.label, mons.len(), m.slots()));
        }
        if !active {
            continue;
        }
        for (i, mon) in mons.iter().enumerate() {
            let at = format!("{} slot {}", m.label, i);
            if m.is_land() {
                level_ok(&mut out, mon.get("level"), &at);
                for (t, name) in TIMES {
                    let v = mon.pointer(&format!("/species/{}", t)).unwrap_or(&Value::Null);
                    species_ok(&mut out, v, &format!("{} ({})", at, name), true);
                }
            } else {
                level_ok(&mut out, mon.pointer("/level/min"), &format!("{} min", at));
                level_ok(&mut out, mon.pointer("/level/max"), &format!("{} max", at));
                for ver in VERSIONS {
                    let lv = |k: &str| mon.pointer(&format!("/level/{}", k)).map(|v| pick(v, Some(ver))).and_then(|v| v.as_u64());
                    if let (Some(lo), Some(hi)) = (lv("min"), lv("max")) {
                        if lo > hi {
                            out.push(format!("{}: min {} above max {}", at, lo, hi));
                            break;
                        }
                    }
                }
                species_ok(&mut out, mon.get("species").unwrap_or(&Value::Null), &at, true);
            }
        }
    }
    let land = rate(&METHODS[0]) > 0;
    for (key, label) in RADIO {
        let list = table.get(key).and_then(Value::as_array).map(Vec::as_slice).unwrap_or(&[]);
        if list.len() > 2 {
            out.push(format!("{}: {} species, at most 2", label, list.len()));
        }
        if land && list.len() < 2 {
            out.push(format!("{}: grass slots 2-5 become no species while it plays (set 2 species)", label));
        }
        for (i, v) in list.iter().enumerate() {
            species_ok(&mut out, v, &format!("{} {}", label, i), land);
        }
    }
    for (key, label) in EXTRAS {
        if let Some(v) = table.get(key) {
            species_ok(&mut out, v, label, false);
        }
    }
    if (rate(&METHODS[4]) > 0 || rate(&METHODS[5]) > 0) && table.get("nightFish").is_none_or(|v| sides(v).iter().any(|s| s.as_str() == Some(NO_SPECIES))) {
        out.push("Night fishing: Good Rod slot 3 and Super Rod slot 1 become no species at night".into());
    }
    out
}

/// The 1-based line of table `index` in gs_enc_data.json's text: each table has one
/// `"map"` key and nothing else does.
pub fn table_line(text: &str, index: usize) -> Option<usize> {
    text.lines().enumerate().filter(|(_, l)| l.trim_start().starts_with("\"map\":")).nth(index).map(|(n, _)| n + 1)
}

/// An unused `ENCDATA_<code>` name (`_2`, `_3`... appended when taken).
pub fn bank_name(code: &str, taken: &dyn Fn(&str) -> bool) -> String {
    let code: String = code.chars().map(|c| if c.is_ascii_alphanumeric() { c.to_ascii_uppercase() } else { '_' }).collect();
    let base = format!("ENCDATA_{}", code);
    std::iter::once(base.clone()).chain((2..).map(|n| format!("{}_{}", base, n))).find(|n| !taken(n)).unwrap()
}

/// Add `#define NAME ENCDATA(_000000NN)` after the last table define of
/// encounter_tables_narc.h, aligned like the others. Keeps the file's line endings.
pub fn add_bank_define(path: &Path, name: &str, index: usize) -> Result<()> {
    let text = read_text(path)?;
    let nl = if text.contains("\r\n") { "\r\n" } else { "\n" };
    let mut lines: Vec<String> = text.split(nl).map(String::from).collect();
    let is_bank = |l: &str| l.starts_with("#define ENCDATA_") && l.contains("ENCDATA(_");
    if lines.iter().any(|l| is_bank(l) && l.split_whitespace().nth(1) == Some(name)) {
        bail!("{} already defines {}", path.display(), name);
    }
    let Some(last) = lines.iter().rposition(|l| is_bank(l)) else {
        bail!("{}: no ENCDATA_ defines to add {} after", path.display(), name);
    };
    lines.insert(last + 1, format!("#define {:<18} ENCDATA(_{:08})", name, index));
    write_text(path, &lines.join(nl))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn versions() {
        let plain = json!("SPECIES_PIDGEY");
        assert_eq!(pick(&plain, Some("SOULSILVER")), plain);
        let split = put(&plain, Some("SOULSILVER"), json!("SPECIES_RATTATA"));
        assert_eq!(split, json!({"HEARTGOLD": "SPECIES_PIDGEY", "SOULSILVER": "SPECIES_RATTATA"}));
        assert_eq!(pick(&split, Some("HEARTGOLD")), plain);
        assert_eq!(pick(&split, None), split);
        assert_eq!(put(&split, Some("SOULSILVER"), plain.clone()), plain, "sides that agree join");
        assert_eq!(put(&split, None, json!(3)), json!(3));
    }

    #[test]
    fn checks() {
        let known = |n: &str| n.starts_with("SPECIES_") && n != "SPECIES_TYPO";
        let mut t = empty_table("X");
        assert!(issues(&t, &known).is_empty());
        t["land"]["rate"] = json!(20);
        let found = issues(&t, &known);
        assert!(found.iter().any(|i| i == "Grass: 0 slots, needs 12"), "{:?}", found);
        t["land"]["mons"] = Value::Array((0..12).map(|_| new_slot(&METHODS[0], "SPECIES_PIDGEY", 3)).collect());
        t["hoenn"] = json!(["SPECIES_PLUSLE", "SPECIES_MINUN"]);
        t["sinnoh"] = json!(["SPECIES_SHINX", "SPECIES_SHINX"]);
        assert!(issues(&t, &known).is_empty());
        t["land"]["mons"][0]["species"]["nite"] = json!({"HEARTGOLD": "SPECIES_TYPO", "SOULSILVER": "SPECIES_NONE"});
        t["land"]["mons"][1]["level"] = json!(0);
        t["surf"] = json!({"rate": 10, "mons": (0..5).map(|_| json!({"level": {"min": 9, "max": 4}, "species": "SPECIES_GOLDEEN"})).collect::<Vec<_>>()});
        t["fishing"]["good_rod"]["rate"] = json!(5);
        let found = issues(&t, &known);
        for want in [
            "Grass slot 0 (Night): SPECIES_TYPO is not a species",
            "Grass slot 0 (Night): no species",
            "Grass slot 1: level 0 is not 1-100",
            "Surfing slot 0: min 9 above max 4",
            "Good Rod: 0 slots, needs 5",
            "Night fishing: Good Rod slot 3 and Super Rod slot 1 become no species at night",
        ] {
            assert!(found.iter().any(|i| i == want), "missing {:?} in {:?}", want, found);
        }
    }

    #[test]
    fn keys_and_names() {
        let t = json!({"map": "X", "land": 0, "hoenn": [], "sinnoh": [], "nightFish": 1});
        let o = t.as_object().unwrap();
        assert_eq!(key_position(o, "landSwarm"), 4);
        assert_eq!(key_position(o, "fishSwarm"), 5);
        assert_eq!(key_position(o, "other"), 5);
        assert_eq!(bank_name("r29", &|n| n == "ENCDATA_R29"), "ENCDATA_R29_2");
        assert_eq!(table_line("{\n \"encounters\": [\n  {\n   \"map\": \"A\"\n  },\n  {\n   \"map\": \"B\"", 1), Some(7));
    }

    #[test]
    fn bank_define() {
        let dir = std::env::temp_dir().join(format!("wild-test-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let p = dir.join("encounter_tables_narc.h");
        std::fs::write(&p, "#define ENCDATA_NA 255\n#define ENCDATA_T20        ENCDATA(_00000000)\n\n#endif\n").unwrap();
        add_bank_define(&p, "ENCDATA_NEW", 142).unwrap();
        assert_eq!(
            std::fs::read_to_string(&p).unwrap(),
            "#define ENCDATA_NA 255\n#define ENCDATA_T20        ENCDATA(_00000000)\n#define ENCDATA_NEW        ENCDATA(_00000142)\n\n#endif\n"
        );
        assert!(add_bank_define(&p, "ENCDATA_NEW", 143).is_err());
        std::fs::remove_dir_all(dir).unwrap();
    }
}
