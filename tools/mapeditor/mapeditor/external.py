# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-27
"""Opening a map's files in a text editor, at a line: the presets, building the
command, and finding the line a script or an event starts on. No Qt.

A command is a template split like a shell line, with {file} and {line}
(1-based) filled in; {term} expands to the terminal emulator found here, for
editors that run in a terminal.
"""

import os
import re
import shlex
import shutil
import subprocess

# (name, template); the first whose program is installed is the default
PRESETS = [
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
]

# terminal emulator -> the words that run a command in a new window
TERMINALS = [
    ("kitty", ["kitty"]),
    ("alacritty", ["alacritty", "-e"]),
    ("foot", ["foot"]),
    ("wezterm", ["wezterm", "start", "--"]),
    ("ghostty", ["ghostty", "-e"]),
    ("konsole", ["konsole", "-e"]),
    ("gnome-terminal", ["gnome-terminal", "--"]),
    ("xfce4-terminal", ["xfce4-terminal", "-x"]),
    ("x-terminal-emulator", ["x-terminal-emulator", "-e"]),
    ("xterm", ["xterm", "-e"]),
]


class ExternalError(Exception):
    pass


def terminal(env=None):
    """The words that start a terminal running a command: $TERMINAL if set, else the
    first known terminal installed; None if there is none."""
    env = os.environ if env is None else env
    if env.get("TERMINAL"):
        name = os.path.basename(env["TERMINAL"].split()[0])
        known = dict(TERMINALS)
        return known.get(name, shlex.split(env["TERMINAL"]) + ["-e"])
    for name, words in TERMINALS:
        if shutil.which(name):
            return list(words)
    return None


def program(template):
    """The program a template runs (the terminal's editor for {term} templates)."""
    words = shlex.split(template)
    if words and words[0] == "{term}":
        words = words[1:]
    return words[0] if words else ""


def available(template):
    return bool(shutil.which(program(template))) and ("{term}" not in template or terminal() is not None)


def default_template():
    """The first installed preset; $VISUAL / $EDITOR come before the terminal presets."""
    for name, template in PRESETS:
        if "{term}" in template:
            editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
            if editor and shutil.which(shlex.split(editor)[0]) and terminal():
                return "{term} %s +{line} {file}" % editor
        if available(template):
            return template
    return PRESETS[-1][1]


def command(template, path, line=1):
    """argv for opening path at line with a template."""
    words = []
    for w in shlex.split(template):
        if w == "{term}":
            t = terminal()
            if t is None:
                raise ExternalError("no terminal emulator found: set $TERMINAL")
            words += t
        else:
            words.append(w.replace("{file}", path).replace("{line}", str(max(1, line))))
    if not words:
        raise ExternalError("the editor command is empty")
    return words


def launch(template, path, line=1, cwd=None):
    """Start the editor without waiting for it."""
    argv = command(template, path, line)
    try:
        subprocess.Popen(argv, cwd=cwd, start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        raise ExternalError("couldn't run %s: %s" % (argv[0], e))
    return argv


# --- where things are ---------------------------------------------------------------

def _lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")


def label_line(path, label):
    """1-based line where a script, movement or text label is defined in a scripts.pory
    or .inc file; else its first use; else None."""
    if not label or not isinstance(label, str) or not os.path.isfile(path):
        return None
    lines = _lines(path)
    word = re.escape(label)
    definition = re.compile(r"^\s*(?:(?:script|movement|text|mart|mapscripts|raw)\s+%s\b|%s::?)" % (word, word))
    for i, l in enumerate(lines):
        if definition.match(l):
            return i + 1
    use = re.compile(r"\b%s\b" % word)
    for i, l in enumerate(lines):
        if use.search(l):
            return i + 1
    return None


def event_line(path, section, index):
    """1-based line where event `index` of a map.json section starts (its "{"), or the
    section's line, or None."""
    if not os.path.isfile(path):
        return None
    lines = _lines(path)
    start = next((i for i, l in enumerate(lines) if re.match(r'\s*"%s"\s*:' % section, l)), None)
    if start is None:
        return None
    depth, n = 0, -1
    for i in range(start, len(lines)):
        for ch in lines[i]:
            if ch in "[{":
                depth += 1
                if ch == "{" and depth == 2:
                    n += 1
                    if n == index:
                        return i + 1
            elif ch in "]}":
                depth -= 1
                if depth == 0:
                    return start + 1
    return start + 1
