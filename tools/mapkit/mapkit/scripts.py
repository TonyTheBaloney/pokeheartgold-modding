# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
"""Event script (.s) reader, driven by the macro definitions in
asm/macros/script.inc and asm/macros/movement.inc.

A macro argument is a *label* if the macro body uses it as `\\arg-.-4` (a
relative jump/data offset); that is how jump targets and movement data are
found without hard-coding command names.
"""

import re
from dataclasses import dataclass, field

_MACRO_RE = re.compile(r"^\s*\.macro\s+(\w+)\s*(.*)$")
_LABEL_RE = re.compile(r"^\s*([A-Za-z_][\w.]*):\s*(.*)$")


@dataclass
class Macro:
    name: str
    params: list
    command_id: int = None      # first `.short N` in the body, if any
    label_params: set = field(default_factory=set)
    calls: list = field(default_factory=list)  # (callee, [arg texts]) for alias macros
    kind: str = "script"        # "script" or "movement"


class MacroTable:
    def __init__(self):
        self.macros = {}

    def load(self, path, kind):
        cur = None
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        for raw in lines:
            line = raw.split("//")[0].rstrip()
            m = _MACRO_RE.match(line)
            if m:
                params = []
                for p in re.split(r"[,\s]+", m.group(2).strip()):
                    if p:
                        params.append(p.split("=")[0].split(":")[0])
                cur = Macro(m.group(1), params, kind=kind)
                self.macros[cur.name] = cur
                continue
            if cur is None:
                continue
            s = line.strip()
            if s.startswith(".endm"):
                cur = None
                continue
            if cur.command_id is None:
                mm = re.match(r"\.short\s+(0x[0-9a-fA-F]+|\d+)\s*$", s)
                if mm:
                    cur.command_id = int(mm.group(1), 0)
            for p in cur.params:
                if re.search(r"\\%s\s*-\s*\." % re.escape(p), s):
                    cur.label_params.add(p)
            first = s.split(None, 1)
            if first and not first[0].startswith("."):
                args = split_args(first[1]) if len(first) > 1 else []
                cur.calls.append((first[0], args))
        return self

    def get(self, name):
        return self.macros.get(name)

    def label_arg_indexes(self, name, _depth=0):
        """Indexes of the arguments of `name` that are labels (follows alias macros)."""
        m = self.macros.get(name)
        if m is None or _depth > 8:
            return set()
        out = {i for i, p in enumerate(m.params) if p in m.label_params}
        for callee, args in m.calls:
            for ci in self.label_arg_indexes(callee, _depth + 1):
                if ci < len(args):
                    a = args[ci].strip()
                    if a.startswith("\\") and a[1:] in m.params:
                        out.add(m.params.index(a[1:]))
        return out


def split_args(text):
    out, cur, level = [], "", 0
    for ch in text:
        if ch == "(":
            level += 1
        elif ch == ")":
            level -= 1
        if ch == "," and level == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


@dataclass
class Statement:
    line: int
    macro: str
    args: list
    label: str  # nearest label above this statement


@dataclass
class ScriptFile:
    path: str
    includes: list = field(default_factory=list)
    scrdefs: list = field(default_factory=list)     # labels in ScrDef order; index i -> script id i+1
    labels: dict = field(default_factory=dict)      # label -> line number
    statements: list = field(default_factory=list)
    unknown: list = field(default_factory=list)     # (line, text) not understood

    def script_label(self, script_id):
        """Label for a local script id (1-based, as used in events)."""
        i = script_id - 1
        return self.scrdefs[i] if 0 <= i < len(self.scrdefs) else None

    def body(self, label):
        """Statements from `label` up to the next label."""
        return [s for s in self.statements if s.label == label]


def parse(path, macros, text=None):
    """Parse a script file (or `text`, reported as `path`)."""
    sf = ScriptFile(path)
    label = None
    if text is None:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("//")[0].split("@")[0].rstrip()
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            m = re.match(r'#\s*include\s+"([^"]+)"', s)
            if m:
                sf.includes.append(m.group(1))
            continue
        m = _LABEL_RE.match(line)
        if m:
            label = m.group(1)
            sf.labels[label] = n
            s = m.group(2).strip()
            if not s:
                continue
        if s.startswith("."):
            continue  # directives (.balign etc.)
        parts = s.split(None, 1)
        name = parts[0]
        args = split_args(parts[1]) if len(parts) > 1 else []
        if name == "ScrDef":
            sf.scrdefs.append(args[0] if args else "")
            continue
        if name == "ScrDefEnd":
            continue
        if macros.get(name) is None:
            sf.unknown.append((n, s))
        sf.statements.append(Statement(n, name, args, label))
    return sf


_TERMINATORS = {"End", "GoTo", "Return", "EndMovement", "InitScriptEnd"}


def reachable(sf, macros, start):
    """Statements reachable from `start`: follows jumps/calls and falls through to
    the next label unless a block ends in End/GoTo/Return. Movement data is skipped."""
    order = sorted(sf.labels, key=sf.labels.get)
    nxt = {a: b for a, b in zip(order, order[1:])}
    by_label = {}
    for st in sf.statements:
        by_label.setdefault(st.label, []).append(st)
    out, todo, done = [], [start], set()
    while todo:
        label = todo.pop()
        if label in done or label not in sf.labels:
            continue
        done.add(label)
        body = by_label.get(label, [])
        if body and getattr(macros.get(body[0].macro), "kind", "script") == "movement":
            continue
        out.extend(body)
        for st in body:
            for i in macros.label_arg_indexes(st.macro):
                if i < len(st.args):
                    todo.append(re.split(r"[\s+\-]", st.args[i].strip())[0])
        if (not body or body[-1].macro not in _TERMINATORS) and label in nxt:
            todo.append(nxt[label])
    return sorted(out, key=lambda s: s.line)


def label_refs(sf, macros):
    """Yield (statement, label) for every label argument in the file."""
    for st in sf.statements:
        for i in macros.label_arg_indexes(st.macro):
            if i < len(st.args):
                yield st, st.args[i]


_REF_PREFIXES = ("FLAG_", "VAR_", "obj_", "msg_", "ITEM_", "SPECIES_", "TRAINER_", "SEQ_", "std_", "MAP_")


def symbol_refs(sf):
    """Yield (statement, symbol) for constants used as arguments (flags, vars, text, objects, ...)."""
    for st in sf.statements:
        for a in st.args:
            for tok in re.findall(r"[A-Za-z_]\w*", a):
                if tok.startswith(_REF_PREFIXES):
                    yield st, tok
