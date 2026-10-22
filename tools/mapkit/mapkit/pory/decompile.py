# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""scripts.inc -> structured scripts.pory.

Each script (a ScrDef label up to the next one) is rewritten as a `script` block:
GoTo chains become if/elif/else, early exits become `if` blocks the compiler
places after the script's end, and commands are lowercased. Movement data becomes
`movement` blocks in the same place. Every script is compiled back and compared
with the original, command by command with jump targets resolved to positions;
if a form doesn't reproduce the original exactly, a plainer one is tried
(labels and `goto`), and `raw` is the last resort. So the output always builds
the same ROM.
"""

import re
from dataclasses import dataclass, field

from . import compiler
from . import parser as P

_LABEL_RE = re.compile(r"^([A-Za-z_][\w.]*):\s*(.*)$")
_INCLUDE_RE = re.compile(r'^#\s*include\s+"([^"]+)"')
_TERMINATORS = {"End", "GoTo", "Return"}
_COMPARE_JUMPS = {"GoToIfEq": "==", "GoToIfNe": "!=", "GoToIfLt": "<", "GoToIfLe": "<=",
                  "GoToIfGt": ">", "GoToIfGe": ">="}
# names that are statements in .pory; commands with these lowercase names keep their macro name
_RESERVED = {"if", "elif", "else", "while", "do", "switch", "case", "default", "break", "continue",
             "goto", "call", "return", "end", "poryswitch", "script", "text", "movement",
             "mapscripts", "raw", "const", "moves", "var", "flag", "defeated"}

# levels, best first
FULL, NO_DEFER, FLAT_IF, FLAT, RAW = range(5)
LEVEL_NAMES = ["structured", "structured (no deferred ifs)", "labels + if/goto", "labels", "raw"]


# --- reading .inc ----------------------------------------------------------------

@dataclass
class Line:
    text: str                 # original line (for raw)
    kind: str                 # label, insn, dir, include, blank
    name: str = None
    args: list = field(default_factory=list)


def read_lines(text):
    out = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        s = raw.split("//")[0].strip()
        if not s:
            out.append(Line(raw, "blank"))
            continue
        if s.startswith("#"):
            out.append(Line(raw, "include", _INCLUDE_RE.match(s).group(1) if _INCLUDE_RE.match(s) else None))
            continue
        m = _LABEL_RE.match(s)
        if m:
            out.append(Line(raw, "label", m.group(1)))
            s = m.group(2).strip()
            if not s:
                continue
        if s.startswith("."):
            out.append(Line(raw, "dir", re.sub(r"\s+", "", s)))
            continue
        parts = s.split(None, 1)
        out.append(Line(raw, "insn", parts[0], _split_args(parts[1]) if len(parts) > 1 else []))
    return out


def _split_args(text):
    from ..scripts import split_args
    return split_args(text)


# --- comparing ---------------------------------------------------------------

def fingerprint(text, macros, skip_header=False):
    """Commands with label arguments replaced by the position they point at, macro
    default arguments filled in and whitespace removed. Equal fingerprints
    assemble to equal bytes (labels outside `text` are kept by name)."""
    lines = read_lines(text)
    if skip_header:
        for i, l in enumerate(lines):
            if l.kind == "insn" and l.name == "ScrDefEnd":
                lines = lines[i + 1:]
                break
    items, pos = [], {}
    for l in lines:
        if l.kind == "label":
            pos[l.name] = len(items)
        elif l.kind in ("insn", "dir"):
            items.append(l)
    out = []
    for l in items:
        if l.kind == "dir":
            out.append((".", l.name))
            continue
        m = macros.get(l.name)
        args = list(l.args)
        if m is not None:
            for p in m.params[len(args):]:
                if p in m.defaults:
                    args.append(m.defaults[p])
        la = macros.label_arg_indexes(l.name) | ({0} if l.name == "ScrDef" else set())
        norm = []
        for i, a in enumerate(args):
            a = re.sub(r"\s+", "", a)
            norm.append(("@", pos[a]) if i in la and a in pos else a)
        out.append((l.name, tuple(norm)))
    return out


# --- conditions ----------------------------------------------------------------

@dataclass
class Cond:
    kind: str                 # flag, defeated, itemspace, var
    args: list
    op: str = None            # var: comparison; others: None
    pos: bool = True          # flag/defeated/itemspace: True = condition holds

    def negate(self):
        if self.kind == "var":
            return Cond(self.kind, self.args, compiler.NEGATE[self.op])
        return Cond(self.kind, self.args, None, not self.pos)

    def text(self):
        if self.kind == "var":
            return "var(%s) %s %s" % (self.args[0], self.op, self.args[1])
        return "%s%s(%s)" % ("" if self.pos else "!", self.kind, ", ".join(self.args))


def cond_at(ins, k):
    """(condition that makes the jump at k taken, its target label, width) or None."""
    a = ins[k]
    if a.name in ("GoToIfSet", "GoToIfUnset") and len(a.args) == 2:
        return Cond("flag", [a.args[0]], pos=a.name == "GoToIfSet"), a.args[1], 1
    if a.name in ("GoToIfDefeated", "GoToIfNotDefeated") and len(a.args) == 2:
        return Cond("defeated", [a.args[0]], pos=a.name == "GoToIfDefeated"), a.args[1], 1
    if a.name == "GoToIfNoItemSpace" and len(a.args) == 3:
        return Cond("itemspace", a.args[:2], pos=False), a.args[2], 1
    if a.name == "Compare" and len(a.args) == 2 and k + 1 < len(ins) and not ins[k + 1].labels:
        b = ins[k + 1]
        if b.name in _COMPARE_JUMPS and len(b.args) == 1:
            return Cond("var", list(a.args), _COMPARE_JUMPS[b.name]), b.args[0], 2
    return None


# --- structuring one script --------------------------------------------------------

@dataclass
class Ins:
    name: str
    args: list
    labels: list              # labels placed right before this instruction


class Structurer:
    """Turns one script's instructions into .pory statements (as text lines)."""

    def __init__(self, dec, ins, end_labels, level):
        self.dec, self.ins, self.level = dec, ins, level
        self.n = len(ins)
        self.pos = {}
        for i, it in enumerate(ins):
            for l in it.labels:
                self.pos[l] = i
        for l in end_labels:
            self.pos[l] = self.n
        self.refs = dict(dec.refs)        # label -> jumps to it (whole file)
        self.used = {}                    # label -> jumps turned into structure
        self.claimed = {}                 # start -> end of deferred blocks
        self.bodies = {}                  # start -> statements of deferred blocks
        self.queue = []                   # deferred blocks not structured yet
        self.last_claim = -1

    # helpers
    def save(self):
        return (dict(self.used), dict(self.claimed), dict(self.bodies), list(self.queue), self.last_claim)

    def restore(self, st):
        self.used, self.claimed, self.bodies, self.queue, self.last_claim = \
            dict(st[0]), dict(st[1]), dict(st[2]), list(st[3]), st[4]

    def target(self, label):
        return self.pos.get(label)

    def labels_here(self, k):
        out = []
        for l in self.ins[k].labels if k < self.n else []:
            if self.refs.get(l, 0) > self.used.get(l, 0) or l in self.dec.keep_labels:
                out.append(l)
        return out

    def use(self, label):
        self.used[label] = self.used.get(label, 0) + 1

    def terminator(self, k):
        return self.ins[k].name in _TERMINATORS

    # walk
    def run(self):
        main, k = self.walk(0, self.n, stop=True)
        self.drain()
        into = main
        while k < self.n:
            # after the first End come the deferred `if` bodies; other code there
            # (shared tails reached by goto) continues the block before it
            if self.claimed.get(k):
                into = self.bodies[k]
                k = self.claimed[k]
                continue
            more, k = self.walk(k, self.n, stop=True)
            into += more
            self.drain()
        return main

    def drain(self):
        """Structure deferred bodies in the order the compiler places them (FIFO)."""
        while self.queue:
            p = self.queue.pop(0)
            body, end = self.walk(p, self.n, stop=True)
            self.bodies[p] += body
            self.claimed[p] = end

    def walk(self, lo, hi, stop=False):
        """Statements for ins[lo:hi]. With stop, ends after the first statement
        that doesn't fall through. Returns (statements, next position)."""
        out, k = [], lo
        while k < hi:
            if k > lo and k in self.claimed:
                break
            out += [("label", l) for l in self.labels_here(k)]
            stmt, k2 = self.statement(k, hi, stop)
            out.append(stmt)
            k = k2
            if stop and self.ends(stmt):
                break
        return out, k

    def ends(self, stmt):
        if stmt[0] in ("goto", "end", "return"):
            return True
        if stmt[0] == "ifelse":
            return all(self.body_ends(b) for _, b in stmt[1]) and self.body_ends(stmt[2])
        return False

    def clean(self, body):
        """No way out of the block before its last statement (else it reads better
        as a goto)."""
        return not any(self.ends(st) for st in body[:-1])

    def body_ends(self, body):
        return bool(body) and self.ends(body[-1])

    def statement(self, k, hi, stop=False):
        a = self.ins[k]
        if a.name == "GoTo" and len(a.args) == 1:
            return ("goto", a.args[0]), k + 1
        if a.name == "Call" and len(a.args) == 1:
            return ("call", a.args[0]), k + 1
        if a.name == "End" and not a.args:
            return ("end",), k + 1
        if a.name == "Return" and not a.args:
            return ("return",), k + 1
        c = cond_at(self.ins, k) if self.level <= FLAT_IF else None
        if c is None:
            return ("cmd", a.name, a.args), k + 1
        cond, label, w = c
        p = self.target(label)
        if self.level <= NO_DEFER and p is not None and k + w < p <= hi \
                and not any(self.ins[i].labels and i in self.claimed for i in range(k + w, p)):
            # if / else: the then-part ends with GoTo past the else-part
            last = self.ins[p - 1]
            if p - 1 >= k + w and last.name == "GoTo" and len(last.args) == 1:
                q = self.target(last.args[0])
                if q is not None and p < q <= hi:
                    start = self.save()
                    self.use(label)
                    saved = self.save()
                    then, _ = self.walk(k + w, p - 1)
                    if self.body_ends(then):
                        # unreachable GoTo after a branch that already left (the
                        # original compiler wrote these): keep it as a statement
                        self.restore(saved)
                        then, _ = self.walk(k + w, p)
                    else:
                        self.use(last.args[0])
                    els, _ = self.walk(p, q)
                    if self.clean(then) and self.clean(els):
                        return self._ifelse(cond.negate(), then, els), q
                    self.restore(start)
            if not self.terminator(p - 1):
                start = self.save()
                self.use(label)
                then, _ = self.walk(k + w, p)
                if self.clean(then):
                    return ("ifelse", [(cond.negate(), then)], None), p
                self.restore(start)
        if self.level == FULL and p is not None and p > k and self.refs.get(label) == 1 \
                and self.terminator(p - 1) and p not in self.claimed and (p >= hi or stop) \
                and p > self.last_claim:
            # early exit placed after the script's end; the compiler queues these, so
            # their positions must increase in the order they're found
            self.use(label)
            self.claimed[p] = None
            self.bodies[p] = []
            self.queue.append(p)
            self.last_claim = p
            return ("ifelse", [(cond, self.bodies[p])], None), k + w
        return ("ifgoto", cond, label), k + w

    def _ifelse(self, cond, then, els):
        if len(els) == 1 and els[0][0] == "ifelse":  # else { if } -> elif
            return ("ifelse", [(cond, then)] + els[0][1], els[0][2])
        return ("ifelse", [(cond, then)], els)


# --- printing -------------------------------------------------------------------

class Printer:
    def __init__(self, dec):
        self.dec = dec

    def stmts(self, body, depth):
        out = []
        ind = "    " * depth
        for s in body:
            t = s[0]
            if t == "label":
                out.append("    " * max(depth - 1, 0) + "%s:" % s[1])
            elif t == "cmd":
                out.append(ind + self.dec.command_text(s[1], s[2]))
            elif t in ("goto", "call"):
                out.append(ind + "%s(%s)" % (t, s[1]))
            elif t in ("end", "return"):
                out.append(ind + t)
            elif t == "ifgoto":
                out.append(ind + "if (%s) { goto(%s) }" % (s[1].text(), s[2]))
            elif t == "ifelse":
                for i, (c, b) in enumerate(s[1]):
                    out.append(ind + "%s (%s) {" % ("if" if i == 0 else "} elif", c.text()))
                    out += self.stmts(b, depth + 1)
                if s[2] is not None:
                    out.append(ind + "} else {")
                    out += self.stmts(s[2], depth + 1)
                out.append(ind + "}")
        return out


def scrdefs_block(names):
    return ["// Script numbers, from 1, in this order (map.json and mapscripts use the labels).",
            "scrdefs {"] + ["    " + n for n in names] + ["}"]


# --- whole file ------------------------------------------------------------------

class Decompiler:
    def __init__(self, ctx, map_name, text):
        self.ctx = ctx
        self.macros = ctx.macros
        self.map_name = map_name
        self.text = text.replace("\r\n", "\n")
        self.lines = read_lines(self.text)
        self.reverse_cmd = {v: k for k, v in ctx.config["command_aliases"].items() if k != "message"}
        self.reverse_move = {}
        for alias, macro in ctx.moves.items():
            if ctx.moves.get(alias) == macro and macro not in self.reverse_move:
                self.reverse_move[macro] = alias
        self.renames = {}
        self.stats = {}
        self.keep_labels = set()
        self.levels = {}                  # script -> level it was written at

    # names
    def command_text(self, name, args):
        if name in self.reverse_cmd:
            shown = self.reverse_cmd[name]
        elif name.lower() not in _RESERVED and self.ctx.command_lower.get(name.lower()) == name:
            shown = name.lower()
        else:
            shown = name
        args = [self.renames.get(a, a) for a in args]
        return shown + ("(%s)" % ", ".join(args) if args else "")

    # pieces
    def split(self):
        """[('header', lines), ('code', name, [Line]), ('move', name, [Line]), ('raw', [Line])]"""
        lines = self.lines
        i = 0
        header = []
        while i < len(lines):
            header.append(lines[i])
            if lines[i].kind == "insn" and lines[i].name == "ScrDefEnd":
                i += 1
                break
            i += 1
        self.scrdefs = [l.args[0] for l in header if l.kind == "insn" and l.name == "ScrDef"]
        units = [("header", header)]
        public = set(self.scrdefs)
        cur = None

        def flush():
            nonlocal cur
            if cur is not None:
                units.append(cur)
            cur = None

        while i < len(lines):
            l = lines[i]
            if l.kind == "dir" and l.name == ".balign4,0":
                # movement data: .balign, one label, movement commands, EndMovement
                j = i + 1
                while j < len(lines) and lines[j].kind == "blank":
                    j += 1
                k = j + 1
                ok = j < len(lines) and lines[j].kind == "label"
                while ok and k < len(lines) and lines[k].kind == "insn" and lines[k].name != "EndMovement":
                    m = self.macros.get(lines[k].name)
                    ok = m is not None and m.kind == "movement"
                    k += 1
                ok = ok and k < len(lines) and lines[k].kind == "insn" and lines[k].name == "EndMovement"
                flush()
                if ok:
                    units.append(("move", lines[j].name, lines[j + 1:k + 1]))
                    i = k + 1
                else:
                    units.append(("raw", [l]))
                    i += 1
                continue
            if l.kind == "label" and (l.name in public or cur is None or cur[0] != "code"):
                flush()
                cur = ("code", l.name, [])
                i += 1
                continue
            if cur is None:
                if l.kind == "blank":
                    i += 1
                    continue
                cur = ("raw", [])
            (cur[2] if cur[0] == "code" else cur[1]).append(l)
            i += 1
        flush()
        return units

    def merge(self, units):
        """A script that is only a label (two numbers for one script) or that runs on
        into the next one can't be its own block: it becomes a label inside the next
        or the next becomes a label inside it."""
        out = []
        for u in units:
            prev = out[-1] if out else None
            if u[0] == "code" and prev is not None and prev[0] == "code":
                insns = [l for l in prev[2] if l.kind == "insn"]
                if not insns or insns[-1].name not in _TERMINATORS:
                    out[-1] = ("code", prev[1], prev[2] + [Line(u[1] + ":", "label", u[1])] + u[2])
                    continue
            out.append(u)
        return out

    def count_refs(self):
        refs = {}
        for l in self.lines:
            if l.kind != "insn" or l.name in ("ScrDef",):
                continue
            for i in self.macros.label_arg_indexes(l.name):
                if i < len(l.args):
                    refs[l.args[i]] = refs.get(l.args[i], 0) + 1
        self.refs = refs

    # movement
    def movement_text(self, name, body):
        items = []
        for l in body:
            if l.name == "EndMovement":
                continue
            count = 1
            if l.args:
                if len(l.args) != 1 or not re.fullmatch(r"\d+", l.args[0]):
                    return None
                count = int(l.args[0])
            items.append(self.reverse_move.get(l.name, l.name) + (" * %d" % count if count != 1 else ""))
        new = self.renames.get(name, name)
        if not items:
            return ["movement %s {}" % new]
        return ["movement %s {" % new] + ["    " + it for it in items] + ["}"]

    # code
    def code_ins(self, body):
        ins, pending = [], []
        for l in body:
            if l.kind == "label":
                pending.append(l.name)
            elif l.kind == "insn":
                ins.append(Ins(l.name, l.args, pending))
                pending = []
            elif l.kind in ("dir", "include"):
                return None, None
        return ins, pending

    def script_text(self, name, local, body, level):
        ins, end_labels = self.code_ins(body)
        if ins is None or end_labels:
            return None
        if level == FLAT:
            stmts = []
            for it in ins:
                stmts += [("label", l) for l in it.labels]
                stmts.append(self._flat(it))
        else:
            stmts = Structurer(self, ins, end_labels, level).run()
        head = "script(local) %s {" % name if local else "script %s {" % name
        return [head] + Printer(self).stmts(stmts, 1) + ["}"]

    def _flat(self, it):
        if it.name == "GoTo" and len(it.args) == 1:
            return ("goto", it.args[0])
        if it.name == "Call" and len(it.args) == 1:
            return ("call", it.args[0])
        if it.name in ("End", "Return") and not it.args:
            return (it.name.lower(),)
        return ("cmd", it.name, it.args)

    def check(self, pory_lines, orig_lines):
        """Does this .pory piece compile to the same commands as the original lines?"""
        src = "\n".join(pory_lines) + "\n"
        try:
            res = compiler.compile_source(src, self.ctx)
        except P.PoryError:
            return False
        orig = "\n".join(l.text for l in orig_lines)
        a = fingerprint(orig, self.macros)
        b = fingerprint(self._unrename(res.scripts_inc), self.macros, skip_header=True)
        return a == b[:-1]  # without the alignment the compiler ends the file with

    def _unrename(self, text):
        for old, new in self.renames.items():
            text = re.sub(r"\b%s\b" % re.escape(new), old, text)
        return text

    def raw_text(self, lines):
        text = "\n".join(l.text for l in lines)
        for old, new in self.renames.items():
            text = re.sub(r"(?<![\w.])%s\b" % re.escape(old), new, text)
        return text

    def run(self, own_includes):
        """Returns (pory lines for the scripts part, {level name: count})."""
        self.count_refs()
        units = self.split()
        # movement labels: _0350 -> <Map>_Movement_0350
        for u in units:
            if u[0] == "move" and re.fullmatch(r"_[0-9A-Fa-f]+", u[1]):
                self.renames[u[1]] = "%s_Movement%s" % (self.map_name, u[1])
        out, scripts_order, stats = [], [], {}
        extra = [l.text for l in units[0][1] if l.kind == "include" and l.name not in own_includes]
        if extra:
            out += ["raw `"] + extra + ["`", ""]
        self.keep_labels = set(self.scrdefs)  # numbered: kept even with no jumps to them
        units = self.merge(units)
        last = units[-1]
        if last[0] == "raw" and [l.name for l in last[1] if l.kind != "blank"] == [".balign4,0"]:
            units = units[:-1]  # the compiler ends every file with it
        for u in units[1:]:
            if u[0] == "move":
                mv = self.movement_text(u[1], u[2])
                orig = [Line("\t.balign 4, 0", "dir", ".balign4,0"), Line(u[1] + ":", "label", u[1])] + u[2]
                if mv is not None and self.check(mv, orig):
                    out += mv + [""]
                    stats["movement"] = stats.get("movement", 0) + 1
                else:
                    out += ["raw `", self.raw_text(orig), "`", ""]
                    stats["raw"] = stats.get("raw", 0) + 1
                continue
            if u[0] == "raw":
                text = self.raw_text(u[1]).strip("\n")
                if text.strip():
                    out += ["raw `", text, "`", ""]
                continue
            name, body = u[1], u[2]
            local = name not in self.scrdefs
            orig = [Line(name + ":", "label", name)] + body
            done = False
            for level in (FULL, NO_DEFER, FLAT_IF, FLAT):
                text = self.script_text(name, local, body, level)
                if text is not None and self.check(text, orig):
                    out += text + [""]
                    stats[LEVEL_NAMES[level]] = stats.get(LEVEL_NAMES[level], 0) + 1
                    self.levels[name] = level
                    if not local:
                        scripts_order.append(name)
                    done = True
                    break
            if not done:
                out += ["raw `", self.raw_text(orig).strip("\n"), "`", ""]
                stats["raw"] = stats.get("raw", 0) + 1
                self.levels[name] = RAW
        if scripts_order != self.scrdefs:
            # numbers follow ScrDef order, which isn't file order here: keep the table
            out = scrdefs_block(self.scrdefs) + [""] + out
        return out, stats
