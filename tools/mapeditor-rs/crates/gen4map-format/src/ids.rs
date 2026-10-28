// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! A map's ids.h: `#define obj_T21_gsboy1 1` for objects, `_EV_<label> N` for
//! scripts. Only plain numeric defines are read; new object ids are added the way
//! mapkit's edit._add_define does.

use std::collections::HashMap;
use std::path::Path;

use crate::{bail, read_text, write_text, Result};

pub fn read(path: &Path) -> Result<HashMap<String, i64>> {
    Ok(parse(&read_text(path)?))
}

pub fn parse(text: &str) -> HashMap<String, i64> {
    let mut out = HashMap::new();
    for line in text.lines() {
        let Some(rest) = line.trim_start().strip_prefix("#define") else { continue };
        let mut toks = rest.split_whitespace();
        if let (Some(name), Some(v), None) = (toks.next(), toks.next(), toks.next()) {
            let n = match v.strip_prefix("0x") {
                Some(h) => i64::from_str_radix(h, 16).ok(),
                None => v.parse().ok(),
            };
            if let Some(n) = n {
                out.insert(name.to_string(), n);
            }
        }
    }
    out
}

/// Add `#define name value` after the last define starting with `after_prefix`,
/// or before the closing #endif. Keeps the file's line endings.
pub fn add_define(path: &Path, name: &str, value: i64, after_prefix: &str) -> Result<()> {
    let text = read_text(path)?;
    let nl = if text.contains("\r\n") { "\r\n" } else { "\n" };
    let mut lines: Vec<String> = text.split(nl).map(String::from).collect();
    let defines = |l: &str, prefix: &str| {
        l.strip_prefix("#define").is_some_and(|r| r.starts_with(char::is_whitespace) && r.trim_start().starts_with(prefix))
    };
    if lines.iter().any(|l| defines(l, name) && l.split_whitespace().nth(1) == Some(name)) {
        bail!("{} already defines {}", path.display(), name);
    }
    let at = match lines.iter().rposition(|l| defines(l, after_prefix)) {
        Some(i) => i + 1,
        None => match lines.iter().rposition(|l| l.starts_with("#endif")) {
            Some(i) => i,
            None => bail!("{}: no #endif to add {} before", path.display(), name),
        },
    };
    lines.insert(at, format!("#define {} {}", name, value));
    write_text(path, &lines.join(nl))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds_after_last_object() {
        let dir = std::env::temp_dir().join(format!("ids-test-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let p = dir.join("ids.h");
        std::fs::write(&p, "#ifndef X\n#define X\n\n#define _EV_A 0\n\n#define obj_a 0\n#define obj_b    1\n\n#endif // X\n").unwrap();
        add_define(&p, "obj_c", 2, "obj_").unwrap();
        let t = std::fs::read_to_string(&p).unwrap();
        assert!(t.contains("#define obj_b    1\n#define obj_c 2\n\n#endif"));
        assert_eq!(parse(&t)["obj_c"], 2);
        assert!(add_define(&p, "obj_c", 3, "obj_").is_err());
        add_define(&p, "x_new", 9, "x_").unwrap();
        assert!(std::fs::read_to_string(&p).unwrap().ends_with("#define x_new 9\n#endif // X\n"));
        std::fs::remove_dir_all(dir).unwrap();
    }
}
