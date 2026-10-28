// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-28
//! Opening a map's files in a text editor, at a line: the presets, building the
//! command, and finding the line a script or an event starts on (a port of
//! tools/mapeditor/mapeditor/external.py).
//!
//! A command is a template split like a shell line, with {file} and {line} (1-based)
//! filled in; {term} expands to the terminal emulator found here, for editors that
//! run in a terminal.

use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

/// (name, template); the first whose program is installed is the default.
pub const PRESETS: &[(&str, &str)] = &[
    ("VS Code", "code --reuse-window --goto {file}:{line}"),
    ("VSCodium", "codium --reuse-window --goto {file}:{line}"),
    ("Neovim (terminal)", "{term} nvim +{line} {file}"),
    ("Vim (terminal)", "{term} vim +{line} {file}"),
    ("micro (terminal)", "{term} micro {file} +{line}"),
    ("Helix (terminal)", "{term} hx {file}:{line}"),
    ("Kate", "kate --line {line} {file}"),
    ("Zed", "zed {file}:{line}"),
    ("Sublime Text", "subl {file}:{line}"),
    ("System default (no line)", "xdg-open {file}"),
];

/// Terminal emulator -> the words that run a command in a new window.
const TERMINALS: &[(&str, &[&str])] = &[
    ("kitty", &["kitty"]),
    ("alacritty", &["alacritty", "-e"]),
    ("foot", &["foot"]),
    ("wezterm", &["wezterm", "start", "--"]),
    ("ghostty", &["ghostty", "-e"]),
    ("konsole", &["konsole", "-e"]),
    ("gnome-terminal", &["gnome-terminal", "--"]),
    ("xfce4-terminal", &["xfce4-terminal", "-x"]),
    ("x-terminal-emulator", &["x-terminal-emulator", "-e"]),
    ("xterm", &["xterm", "-e"]),
];

/// Split like a POSIX shell line: whitespace separates words; single quotes, double
/// quotes and backslashes quote. None if a quote isn't closed.
pub fn split(s: &str) -> Option<Vec<String>> {
    let mut out = Vec::new();
    let mut word = String::new();
    let mut in_word = false;
    let mut chars = s.chars();
    while let Some(c) = chars.next() {
        match c {
            '\'' => {
                in_word = true;
                loop {
                    match chars.next()? {
                        '\'' => break,
                        c => word.push(c),
                    }
                }
            }
            '"' => {
                in_word = true;
                loop {
                    match chars.next()? {
                        '"' => break,
                        '\\' => match chars.next()? {
                            c @ ('"' | '\\' | '$' | '`') => word.push(c),
                            '\n' => {}
                            c => {
                                word.push('\\');
                                word.push(c);
                            }
                        },
                        c => word.push(c),
                    }
                }
            }
            '\\' => {
                in_word = true;
                if let Some(c) = chars.next() {
                    if c != '\n' {
                        word.push(c);
                    }
                }
            }
            c if c.is_whitespace() => {
                if in_word {
                    out.push(std::mem::take(&mut word));
                    in_word = false;
                }
            }
            c => {
                in_word = true;
                word.push(c);
            }
        }
    }
    if in_word {
        out.push(word);
    }
    Some(out)
}

/// The program's path if it is on PATH (or a path that exists).
pub fn which(program: &str) -> Option<PathBuf> {
    if program.contains('/') {
        let p = PathBuf::from(program);
        return p.is_file().then_some(p);
    }
    std::env::split_paths(&std::env::var_os("PATH")?).map(|d| d.join(program)).find(|p| p.is_file())
}

/// The words that start a terminal running a command: $TERMINAL if set, else the first
/// known terminal installed; None if there is none.
pub fn terminal() -> Option<Vec<String>> {
    if let Ok(t) = std::env::var("TERMINAL") {
        if !t.trim().is_empty() {
            let words = split(&t)?;
            let name = Path::new(words.first()?).file_name()?.to_string_lossy().into_owned();
            if let Some((_, w)) = TERMINALS.iter().find(|(n, _)| *n == name) {
                return Some(w.iter().map(|s| s.to_string()).collect());
            }
            return Some(words.into_iter().chain(["-e".to_string()]).collect());
        }
    }
    TERMINALS.iter().find(|(n, _)| which(n).is_some()).map(|(_, w)| w.iter().map(|s| s.to_string()).collect())
}

/// The program a template runs (the terminal's editor for {term} templates).
pub fn program(template: &str) -> String {
    let words = split(template).unwrap_or_default();
    let words = if words.first().map(String::as_str) == Some("{term}") { &words[1..] } else { &words[..] };
    words.first().cloned().unwrap_or_default()
}

pub fn available(template: &str) -> bool {
    which(&program(template)).is_some() && (!template.contains("{term}") || terminal().is_some())
}

/// The first installed preset; $VISUAL / $EDITOR come before the terminal presets.
pub fn default_template() -> String {
    for (_, template) in PRESETS {
        if template.contains("{term}") {
            let editor = std::env::var("VISUAL").ok().filter(|v| !v.is_empty()).or_else(|| std::env::var("EDITOR").ok());
            if let Some(editor) = editor.filter(|e| !e.is_empty()) {
                let first = split(&editor).and_then(|w| w.into_iter().next());
                if first.is_some_and(|p| which(&p).is_some()) && terminal().is_some() {
                    return format!("{{term}} {} +{{line}} {{file}}", editor);
                }
            }
        }
        if available(template) {
            return template.to_string();
        }
    }
    PRESETS.last().unwrap().1.to_string()
}

/// argv for opening path at line with a template.
pub fn command(template: &str, path: &Path, line: usize) -> Result<Vec<String>, String> {
    let mut words = Vec::new();
    for w in split(template).ok_or("the editor command has an unclosed quote")? {
        if w == "{term}" {
            words.extend(terminal().ok_or("no terminal emulator found: set $TERMINAL")?);
        } else {
            words.push(w.replace("{file}", &path.to_string_lossy()).replace("{line}", &line.max(1).to_string()));
        }
    }
    if words.is_empty() {
        return Err("the editor command is empty".into());
    }
    Ok(words)
}

/// Start the editor without waiting for it.
pub fn launch(template: &str, path: &Path, line: usize, cwd: Option<&Path>) -> Result<Vec<String>, String> {
    let argv = command(template, path, line)?;
    let mut cmd = Command::new(&argv[0]);
    cmd.args(&argv[1..]).stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
    if let Some(d) = cwd {
        cmd.current_dir(d);
    }
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        cmd.process_group(0); // keep running if the editor quits
    }
    let mut child = cmd.spawn().map_err(|e| format!("couldn't run {}: {}", argv[0], e))?;
    // reap it in the background so it doesn't linger as a zombie
    std::thread::spawn(move || child.wait());
    Ok(argv)
}

// --- where things are --------------------------------------------------------------------

fn is_word(c: char) -> bool {
    c.is_alphanumeric() || c == '_'
}

/// Does `line` contain `word` as a whole word?
fn has_word(line: &str, word: &str) -> bool {
    line.match_indices(word).any(|(i, _)| {
        let before = line[..i].chars().next_back();
        let after = line[i + word.len()..].chars().next();
        !before.is_some_and(is_word) && !after.is_some_and(is_word)
    })
}

/// 1-based line where a script, movement or text label is defined in a scripts.pory or
/// .inc file; else its first use; else None.
pub fn label_line(path: &Path, label: &str) -> Option<usize> {
    if label.is_empty() {
        return None;
    }
    let text = std::fs::read_to_string(path).ok()?;
    let lines: Vec<&str> = text.split('\n').collect();
    let defines = |l: &str| {
        let t = l.trim_start();
        if let Some(rest) = t.strip_prefix(label) {
            return rest.starts_with(':');
        }
        let mut words = t.split_whitespace();
        matches!(words.next(), Some("script" | "movement" | "text" | "mart" | "mapscripts" | "raw"))
            && words.next().is_some_and(|w| w == label || (w.starts_with(label) && !w[label.len()..].starts_with(is_word)))
    };
    if let Some(i) = lines.iter().position(|l| defines(l)) {
        return Some(i + 1);
    }
    lines.iter().position(|l| has_word(l, label)).map(|i| i + 1)
}

/// 1-based line where event `index` of a map.json section starts (its "{"), or the
/// section's line, or None.
pub fn event_line(path: &Path, section: &str, index: usize) -> Option<usize> {
    let text = std::fs::read_to_string(path).ok()?;
    let lines: Vec<&str> = text.split('\n').collect();
    let key = format!("\"{}\"", section);
    let start = lines.iter().position(|l| l.trim_start().strip_prefix(&key).is_some_and(|r| r.trim_start().starts_with(':')))?;
    let (mut depth, mut n) = (0i32, -1i64);
    for (i, line) in lines.iter().enumerate().skip(start) {
        for ch in line.chars() {
            match ch {
                '[' | '{' => {
                    depth += 1;
                    if ch == '{' && depth == 2 {
                        n += 1;
                        if n == index as i64 {
                            return Some(i + 1);
                        }
                    }
                }
                ']' | '}' => {
                    depth -= 1;
                    if depth == 0 {
                        return Some(start + 1);
                    }
                }
                _ => {}
            }
        }
    }
    Some(start + 1)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn splitting() {
        assert_eq!(split(r#"a 'b c' "d \"e\"" f\ g"#).unwrap(), ["a", "b c", "d \"e\"", "f g"]);
        assert_eq!(split("'open").map(|_| ()), None);
        assert_eq!(program("{term} nvim +{line} {file}"), "nvim");
    }

    #[test]
    fn commands() {
        let argv = command("code --goto {file}:{line}", Path::new("/a b/map.json"), 0).unwrap();
        assert_eq!(argv, ["code", "--goto", "/a b/map.json:1"]);
        assert!(command("", Path::new("x"), 1).is_err());
    }

    #[test]
    fn lines() {
        let dir = std::env::temp_dir().join(format!("external-test-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let pory = dir.join("scripts.pory");
        std::fs::write(&pory, "mapscripts X_MapScripts {}\n\nscript X_Foo {\n    goto X_FooBar\n}\nscript X_FooBar {}\n").unwrap();
        assert_eq!(label_line(&pory, "X_Foo"), Some(3));
        assert_eq!(label_line(&pory, "X_FooBar"), Some(6));
        assert_eq!(label_line(&pory, "X_Nope"), None);
        let json = dir.join("map.json");
        std::fs::write(&json, "{\n    \"id\": 1,\n    \"warp_events\": [\n        {\n            \"x\": 1\n        },\n        {\n            \"x\": 2\n        }\n    ]\n}\n").unwrap();
        assert_eq!(event_line(&json, "warp_events", 1), Some(7));
        assert_eq!(event_line(&json, "warp_events", 5), Some(3));
        assert_eq!(event_line(&json, "bg_events", 0), None);
        std::fs::remove_dir_all(dir).unwrap();
    }
}
