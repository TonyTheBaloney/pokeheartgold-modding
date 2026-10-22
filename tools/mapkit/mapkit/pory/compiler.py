# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Lower a parsed .pory program to HGSS scripts.inc / map_scripts.inc + text.

Branches, comparisons and result-writing commands come from
tools/mapkit/script_config.json; command and movement names come from the
macro files, with lowercase / pokeemerald-style aliases. Generated labels are
readable: <Script>_If_1, <Script>_EndIf_1, <Script>_While_2, ...
"""

import json
import os
import re
from dataclasses import dataclass, field

from . import parser as P

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "script_config.json")
NEGATE = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}
STANDARD_INCLUDES = ("constants/scrcmd.h", "macros/script.inc", "constants/init_script_types.h")
_SCRDEF_RE = re.compile(r"^\s*ScrDef\s+(\w+)\s*$")
_DIRS = {"north": "up", "south": "down", "west": "left", "east": "right"}


def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _snake(name):
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Za-z])(?=\d)", "_", name).lower()
    return s


def movement_aliases(macros, config):
    """pokeemerald-style names: WalkNormalNorth -> walk_up, WalkOnSpotFastEast ->
    walk_in_place_fast_right, FaceWest -> face_left, Delay15 -> delay_15."""
    out = {}
    for name, m in macros.macros.items():
        if m.kind != "movement":
            continue
        words = _snake(name).split("_")
        words = [_DIRS.get(w, w) for w in words if w != "normal"]
        alias = "_".join(words).replace("on_spot", "in_place")
        out.setdefault(alias, name)
        out.setdefault(_snake(name), name)
        out.setdefault(name.lower(), name)
    out.update(config.get("movement_aliases", {}))
    return out


@dataclass
class Context:
    macros: object                      # scripts.MacroTable
    config: dict
    ids_include: str = None             # "maps/<Map>/ids.h"
    msg_header: str = None              # "msgdata/msg/msg_0550_T21.h"
    path: str = None
    text_slots: dict = None             # "<Script>#<n>" -> message id it fills (from text.json)

    def __post_init__(self):
        self.command_lower = {n.lower(): n for n, m in self.macros.macros.items() if m.kind == "script"}
        self.moves = movement_aliases(self.macros, self.config)


@dataclass
class Result:
    scripts_inc: str
    map_scripts_inc: str
    texts: list = field(default_factory=list)      # [(id, value)]
    public: list = field(default_factory=list)     # ScrDef labels in order (script n = index + 1)


class CompileError(P.PoryError):
    pass


# --- per-script lowering -------------------------------------------------------

class ScriptEmitter:
    def __init__(self, comp, name):
        self.comp, self.name = comp, name
        self.lines = []
        self.deferred = []          # [(label, stmts)]
        self.loops = []             # [(break_label, continue_label)]
        self.n = 0
        self.move_n = 0

    def label(self, kind):
        self.n += 1
        return "%s_%s_%d" % (self.name, kind, self.n)

    def emit(self, line):
        self.lines.append("\t" + line)

    def place(self, label):
        self.lines.append(label + ":")

    def err(self, msg, line=None):
        raise CompileError(msg, self.comp.ctx.path, line)

    # body
    def run(self, body):
        if not self.stmts(body):
            self.emit(self.comp.config["default_terminator"])
        while self.deferred:
            label, stmts = self.deferred.pop(0)
            self.lines.append("")
            self.place(label)
            if not self.stmts(stmts):
                self.emit(self.comp.config["default_terminator"])
        return self.lines

    def stmts(self, body):
        term = False
        for s in body:
            term = self.stmt(s)
        return term

    def stmt(self, s):
        cfg = self.comp.config
        if isinstance(s, P.Command):
            self.emit(self.command_line(s))
            return False
        if isinstance(s, P.Label):
            self.place(s.name)
            return False
        if isinstance(s, P.Jump):
            if s.kind in ("break", "continue"):
                if not self.loops:
                    self.err("%s outside a loop or switch" % s.kind, s.line)
                target = self.loops[-1][0 if s.kind == "break" else 1]
                if target is None:
                    self.err("continue inside a switch with no loop", s.line)
                self.emit(cfg["jumps"]["goto"].format(label=target))
                return True
            line = cfg["jumps"][s.kind].format(label=s.label)
            self.emit(line)
            return s.kind != "call"
        if isinstance(s, P.If):
            return self.lower_if(s)
        if isinstance(s, P.While):
            return self.lower_while(s)
        if isinstance(s, P.Switch):
            return self.lower_switch(s)
        self.err("unsupported statement %r" % s)

    def command_line(self, c):
        name = self.comp.command(c.name, c.line)
        args = []
        for a in c.args:
            if isinstance(a, P.Text):
                # the n-th string of the script (source order) fills the text.json slot that
                # names it; a string with no slot becomes a new message
                tid = (self.comp.ctx.text_slots or {}).get(a.slot) or a.slot.replace("#", "_Text_")
                self.comp.add_text(tid, a.value, c.line)
                args.append(tid)
            elif isinstance(a, P.Moves):
                mid = "%s_Movement_%d" % (self.name, self.move_n)
                self.move_n += 1
                self.comp.movements.append(P.Movement(mid, a.items, c.line))
                args.append(mid)
            else:
                args.append(a)
        return name + (" " + ", ".join(args) if args else "")

    # if
    def lower_if(self, s):
        cfg = self.comp.config
        if len(s.branches) == 1 and s.else_body is None and len(s.branches[0][1]) == 1:
            only = s.branches[0][1][0]
            target = None
            if isinstance(only, P.Jump) and only.kind == "goto":
                target = only.label
            elif isinstance(only, P.Jump) and only.kind in ("break", "continue") and self.loops:
                target = self.loops[-1][0 if only.kind == "break" else 1]
            if target:  # if (c) { goto/break/continue } -> one conditional jump
                self.branch(s.branches[0][0], target, True)
                return False
        if len(s.branches) == 1 and s.else_body is None and self._ends(s.branches[0][1]):
            # early exit: jump out to a block placed after the script's end
            target = self.label("If")
            self.branch(s.branches[0][0], target, True)
            self.deferred.append((target, s.branches[0][1]))
            return False
        end = self.label("EndIf")
        all_term = True
        for i, (cond, body) in enumerate(s.branches):
            last = i == len(s.branches) - 1 and s.else_body is None
            nxt = end if last else self.label("Else")
            self.branch(cond, nxt, False)
            term = self.stmts(body)
            all_term = all_term and term
            if not term and not last:
                self.emit(cfg["jumps"]["goto"].format(label=end))
            if nxt != end:
                self.place(nxt)
        if s.else_body is not None:
            all_term = self.stmts(s.else_body) and all_term
        else:
            all_term = False
        self.place(end)
        return all_term

    def _ends(self, body):
        if not body:
            return False
        last = body[-1]
        return isinstance(last, P.Jump) and last.kind in ("end", "return", "goto")

    # loops
    def lower_while(self, s):
        cfg = self.comp.config
        if s.do_while:
            top, cont, end = self.label("Do"), self.label("DoCond"), self.label("EndDo")
            self.place(top)
            self.loops.append((end, cont))
            self.stmts(s.body)
            self.loops.pop()
            self.place(cont)
            self.branch(s.cond, top, True)
            self.place(end)
            return False
        top, end = self.label("While"), self.label("EndWhile")
        self.place(top)
        if s.cond is not None:
            self.branch(s.cond, end, False)
        self.loops.append((end, top))
        term = self.stmts(s.body)
        self.loops.pop()
        if not term:
            self.emit(cfg["jumps"]["goto"].format(label=top))
        self.place(end)
        return False

    def lower_switch(self, s):
        cfg = self.comp.config
        cmp = cfg["compare"]
        end = self.label("EndSwitch")
        labels = [None] * len(s.cases)
        pending = []
        for i, (value, body) in enumerate(s.cases):
            pending.append(i)
            if body or i == len(s.cases) - 1:
                lab = self.label("Default" if value is None else "Case")
                for j in pending:
                    labels[j] = lab
                pending = []
        default = None
        for i, (value, body) in enumerate(s.cases):
            if value is None:
                default = labels[i]
                continue
            self.emit(cmp["compare"].format(s.var, value))
            self.emit(cmp["=="].format(label=labels[i]))
        self.emit(cfg["jumps"]["goto"].format(label=default or end))
        self.loops.append((end, self.loops[-1][1] if self.loops else None))
        placed = set()
        for i, (value, body) in enumerate(s.cases):
            if labels[i] not in placed:
                self.place(labels[i])
                placed.add(labels[i])
            if body and not self.stmts(body) and i != len(s.cases) - 1:
                self.emit(cfg["jumps"]["goto"].format(label=end))
        self.loops.pop()
        self.place(end)
        return False

    # conditions
    def branch(self, c, target, when):
        """Emit code that jumps to `target` if `c` evaluates to `when`."""
        cfg = self.comp.config
        if c.kind == "not":
            return self.branch(c.a, target, not when)
        if c.kind == "and":
            if when:
                skip = self.label("Skip")
                self.branch(c.a, skip, False)
                self.branch(c.b, target, True)
                self.place(skip)
            else:
                self.branch(c.a, target, False)
                self.branch(c.b, target, False)
            return
        if c.kind == "or":
            if when:
                self.branch(c.a, target, True)
                self.branch(c.b, target, True)
            else:
                skip = self.label("Skip")
                self.branch(c.a, skip, True)
                self.branch(c.b, target, False)
                self.place(skip)
            return
        if c.kind == "var":
            if len(c.args) != 1:
                self.err("var() takes one variable", getattr(c, "line", None))
            self.compare(c.args[0], c.op or "!=", c.value if c.op else "0", target, when)
            return
        if c.kind in ("flag", "defeated") or c.name in cfg["conditions"]:
            name = c.name
            if c.op is not None:
                if c.op not in ("==", "!=") or c.value not in ("TRUE", "FALSE", "1", "0"):
                    self.err("%s() can only be compared with == / != TRUE or FALSE" % name, getattr(c, "line", None))
                if (c.op == "==") != (c.value in ("TRUE", "1")):
                    when = not when
            forms = cfg["conditions"][name]
            key = "true" if when else "false"
            if key in forms:
                self.emit(forms[key].format(*c.args, label=target))
            else:  # only the opposite jump exists: skip over an unconditional jump
                skip = self.label("Skip")
                self.emit(forms["false" if when else "true"].format(*c.args, label=skip))
                self.emit(cfg["jumps"]["goto"].format(label=target))
                self.place(skip)
            return
        # result-writing command used as a value: cmd(args) op value
        macro = self.comp.command(c.name, getattr(c, "line", None))
        av = cfg["autovar"].get(macro)
        if av is None:
            self.err("%s() is not a condition (add it to script_config.json conditions or autovar)" % c.name,
                     getattr(c, "line", None))
        self.emit(macro + (" " + ", ".join(c.args) if c.args else ""))
        var = c.args[av["var_arg"]] if "var_arg" in av else av["var_name"]
        self.compare(var, c.op or "!=", c.value if c.op else "0", target, when)

    def compare(self, var, op, value, target, when):
        cmp = self.comp.config["compare"]
        self.emit(cmp["compare"].format(var, value))
        self.emit(cmp[op if when else NEGATE[op]].format(label=target))


# --- whole program -------------------------------------------------------------

class Compiler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.config = ctx.config
        self.texts = []
        self.text_ids = set()
        self.movements = []

    def command(self, name, line=None):
        m = self.ctx.macros
        if name in m.macros and m.macros[name].kind == "script":
            return name
        alias = self.config["command_aliases"].get(name)
        if alias:
            return alias
        if name.lower() in self.ctx.command_lower:
            return self.ctx.command_lower[name.lower()]
        raise CompileError("unknown command %r" % name, self.ctx.path, line)

    def movement(self, name, line=None):
        if name in self.ctx.macros.macros and self.ctx.macros.macros[name].kind == "movement":
            return name
        if name in self.ctx.moves:
            return self.ctx.moves[name]
        raise CompileError("unknown movement %r" % name, self.ctx.path, line)

    def add_text(self, tid, value, line=None):
        if tid in self.text_ids:
            raise CompileError("text %s defined twice" % tid, self.ctx.path, line)
        self.text_ids.add(tid)
        self.texts.append((tid, value))

    def public_scripts(self, prog):
        """ScrDef order: the scrdefs block (and ScrDef lines in raw blocks), then top-level
        scripts in file order. A script listed in scrdefs keeps its place there."""
        blocks = [it for it in prog.items if isinstance(it, P.ScrDefs)]
        if len(blocks) > 1:
            raise CompileError("only one scrdefs block per map", self.ctx.path, blocks[1].line)
        declared = {m.group(1) for it in prog.items if isinstance(it, P.Raw)
                    for m in map(_SCRDEF_RE.match, it.text.splitlines()) if m}
        declared |= {n for b in blocks for n in b.names}
        out = []
        for it in prog.items:
            if isinstance(it, P.ScrDefs):
                out += it.names
            elif isinstance(it, P.Raw):
                out += [m.group(1) for m in map(_SCRDEF_RE.match, it.text.splitlines()) if m]
            elif isinstance(it, P.Script) and not it.local:
                if it.name not in declared:  # a raw ScrDef line already fixes its number
                    out.append(it.name)
            elif isinstance(it, P.MapScripts):
                for name, _ in self._inline_init_scripts(it):
                    out.append(name)
        if len(set(out)) != len(out):
            dup = sorted(n for n in set(out) if out.count(n) > 1)
            raise CompileError("scripts defined twice: %s" % ", ".join(dup), self.ctx.path)
        if blocks:
            missing = [n for n in blocks[0].names if n not in self._labels(prog)]
            if missing:
                raise CompileError("scrdefs: no script or label named %s" % ", ".join(missing),
                                   self.ctx.path, blocks[0].line)
        return out

    def _labels(self, prog):
        """Every label the program defines (scripts, labels inside them, raw labels)."""
        out = set()

        def walk(body):
            for s in body:
                if isinstance(s, P.Label):
                    out.add(s.name)
                elif isinstance(s, P.If):
                    for _, b in s.branches:
                        walk(b)
                    walk(s.else_body or [])
                elif isinstance(s, P.While):
                    walk(s.body)
                elif isinstance(s, P.Switch):
                    for _, b in s.cases:
                        walk(b)
        for it in prog.items:
            if isinstance(it, P.Script):
                out.add(it.name)
                walk(it.body)
            elif isinstance(it, P.Raw):
                out |= set(re.findall(r"^\s*([A-Za-z_]\w*):", it.text, re.M))
            elif isinstance(it, P.MapScripts):
                out |= {n for n, _ in self._inline_init_scripts(it)}
        return out

    @staticmethod
    def _inline_init_scripts(ms):
        out = []
        for kind, label, body in ms.entries:
            if body is not None:
                out.append(("%s_%s" % (ms.name, kind.split("_ON_")[-1].title().replace("_", "")), body))
        for i, (var, value, label, body) in enumerate(ms.frame_table):
            if body is not None:
                out.append(("%s_FrameTable_%d" % (ms.name, i), body))
        return out

    def _raw_text(self, raw):
        keep = []
        drop_includes = set(STANDARD_INCLUDES) | {self.ctx.ids_include, self.ctx.msg_header}
        for line in raw.text.split("\n"):
            s = line.strip()
            if _SCRDEF_RE.match(line) or s == "ScrDefEnd":
                continue
            m = re.match(r'#\s*include\s+"([^"]+)"', s)
            if m and m.group(1) in drop_includes:
                continue
            keep.append(line)
        return "\n".join(keep)

    def compile(self, prog):
        public = self.public_scripts(prog)
        number = {n: i + 1 for i, n in enumerate(public)}
        mapscripts = [it for it in prog.items if isinstance(it, P.MapScripts)]
        if len(mapscripts) > 1:
            raise CompileError("only one mapscripts block per map", self.ctx.path, mapscripts[1].line)

        includes = ['#include "constants/scrcmd.h"']
        if self.ctx.ids_include:
            includes.append('#include "%s"' % self.ctx.ids_include)
        if self.ctx.msg_header:
            includes.append('#include "%s"' % self.ctx.msg_header)
        includes.append('#include "macros/script.inc"')
        head = ["// Generated by tools/mapkit from %s. Do not edit." % os.path.basename(self.ctx.path or "scripts.pory")]
        head += includes + ["", ""] + ["\tScrDef %s" % n for n in public] + ["\tScrDefEnd", ""]

        body = []
        for it in prog.items:
            if isinstance(it, P.Raw):
                body.append(self._raw_text(it))
            elif isinstance(it, P.Script):
                number_texts(it.name, it.body)
                body.append("%s:" % it.name)
                body += ScriptEmitter(self, it.name).run(it.body)
                body.append("")
            elif isinstance(it, P.TextBlock):
                self.add_text(it.name, it.value, it.line)
            elif isinstance(it, P.Movement):
                body += self.movement_lines(it)  # in place, like the original files
            elif isinstance(it, P.MapScripts):
                for name, stmts in self._inline_init_scripts(it):
                    number_texts(name, stmts)
                    body.append("%s:" % name)
                    body += ScriptEmitter(self, name).run(stmts)
                    body.append("")
        for mv in self.movements:  # inline moves(...) go at the end
            body += self.movement_lines(mv)
        body += ["", "\t.balign 4, 0"]  # every original bank ends aligned
        scripts_inc = "\n".join(head + body) + "\n"
        return Result(scripts_inc, self.map_scripts(mapscripts[0] if mapscripts else None, number), self.texts, public)

    def movement_lines(self, mv):
        out = ["", "\t.balign 4, 0", "%s:" % mv.name]
        for name, count in mv.items:
            macro = self.movement(name, mv.line)
            if macro == "EndMovement":
                continue
            if "length" in self.ctx.macros.macros[macro].params:
                out.append("\t%s%s" % (macro, " %d" % count if count != 1 else ""))
            else:
                out += ["\t%s" % macro] * count
        out.append("\tEndMovement")
        return out

    def map_scripts(self, ms, number):
        def ref(label):
            if label in number:
                return "%d  // %s" % (number[label], label)
            return label
        lines = ["// Generated by tools/mapkit. Do not edit.", '#include "constants/scrcmd.h"']
        if self.ctx.ids_include:
            lines.append('#include "%s"' % self.ctx.ids_include)
        lines += ['#include "constants/init_script_types.h"', '#include "macros/script.inc"', "", ""]
        types = self.config["init_script_types"]
        table_label = None
        if ms is not None:
            inline = iter(self._inline_init_scripts(ms))
            inline_names = {}
            for kind, label, body in ms.entries:
                if body is not None:
                    inline_names[id(body)] = next(inline)[0]
            for kind, label, body in ms.entries:
                if kind not in types:
                    raise CompileError("unknown map script type %s" % kind, self.ctx.path, ms.line)
                if types[kind] == "InitScriptEntry_OnFrameTable":
                    table_label = "%s_FrameTable" % ms.name
                    lines.append("\t%s %s" % (types[kind], table_label))
                else:
                    target = inline_names[id(body)] if body is not None else label
                    lines.append("\t%s %s" % (types[kind], ref(target)))
        lines.append("\tInitScriptEntryEnd")
        lines.append("")
        if table_label:
            lines.append("%s:" % table_label)
            for i, (var, value, label, body) in enumerate(ms.frame_table):
                target = "%s_FrameTable_%d" % (ms.name, i) if body is not None else label
                lines.append("\tInitScriptGoToIfEqual %s, %s, %s" % (var, value, ref(target)))
            lines.append("\tInitScriptFrameTableEnd")
            lines.append("")
        lines.append("\tInitScriptEnd")
        return "\n".join(lines) + "\n"


def number_texts(name, body):
    """Give each inline string of a script its slot name, "<Script>#<n>", in source order."""
    n = 0

    def walk(stmts):
        nonlocal n
        for s in stmts:
            if isinstance(s, P.Command):
                for a in s.args:
                    if isinstance(a, P.Text):
                        a.slot = "%s#%d" % (name, n)
                        n += 1
            elif isinstance(s, P.If):
                for _, b in s.branches:
                    walk(b)
                walk(s.else_body or [])
            elif isinstance(s, P.While):
                walk(s.body)
            elif isinstance(s, P.Switch):
                for _, b in s.cases:
                    walk(b)
    walk(body)


def compile_source(src, ctx, switches=None):
    switches = dict({"GAME": "HEARTGOLD"}, **(switches or {}))
    prog = P.parse(src, ctx.path, switches)
    return Compiler(ctx).compile(prog)


def text_entry(tid, value):
    """msgenc JSON entry: lines split after \\n, \\r and \\f, like the existing banks."""
    parts = re.findall(r"[^\n\r\f]*[\n\r\f]|[^\n\r\f]+$", value) or [""]
    return {"id": tid, "en_US": parts if len(parts) > 1 else parts[0]}
