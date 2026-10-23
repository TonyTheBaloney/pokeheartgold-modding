# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Lexer and parser for the poryscript-style map script language.

Syntax follows poryscript (https://github.com/huderlem/poryscript) where it
can: script/text/movement/mapscripts/scrdefs/raw/const top-level blocks, if/elif/else,
while, do-while, switch, break/continue, goto/call/return/end, labels,
flag()/var()/defeated() conditions with ! && ||, inline strings and moves(),
poryswitch. See docs/modding/SCRIPTING.md for the HGSS differences.
"""

import re
from dataclasses import dataclass, field


class PoryError(Exception):
    def __init__(self, msg, path=None, line=None):
        self.path, self.line = path, line
        super().__init__("%s:%s: %s" % (path or "<input>", line or "?", msg))


# --- lexer -------------------------------------------------------------------

_TOKEN_RE = re.compile(r"""
    (?P<ws>[ \t\r\n]+)
  | (?P<comment>//[^\n]*|\#[^\n]*|/\*.*?\*/)
  | (?P<raw>`[^`]*`)
  | (?P<string>"(?:[^"\\]|\\.)*")
  | (?P<number>0[xX][0-9a-fA-F]+|\d+)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op>&&|\|\||==|!=|<=|>=|[{}()\[\],:;!<>*+\-/|&^~.=])
""", re.X | re.S)


@dataclass
class Tok:
    kind: str
    text: str
    line: int
    start: int
    end: int


def tokenize(src, path=None):
    out, pos, line = [], 0, 1
    while pos < len(src):
        m = _TOKEN_RE.match(src, pos)
        if not m:
            raise PoryError("unexpected character %r" % src[pos], path, line)
        kind = m.lastgroup
        text = m.group()
        if kind not in ("ws", "comment"):
            out.append(Tok(kind, text, line, m.start(), m.end()))
        line += text.count("\n")
        pos = m.end()
    out.append(Tok("eof", "", line, pos, pos))
    return out


def unescape(s):
    """Body of a "..." literal -> text. \\n \\r \\f become the control characters
    msgenc expects; {CODES} pass through."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            out.append({"n": "\n", "r": "\r", "f": "\f", "t": "\t", '"': '"', "\\": "\\"}.get(n, "\\" + n))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


# --- AST ---------------------------------------------------------------------

@dataclass
class Command:
    name: str
    args: list            # each: str (expression text) | Text | Moves
    line: int


@dataclass
class Text:
    value: str            # inline string argument


@dataclass
class Moves:
    items: list           # [(name, count)]


@dataclass
class If:
    branches: list        # [(cond, [stmts])]
    else_body: list       # [stmts] or None
    line: int


@dataclass
class While:
    cond: object          # None = forever
    body: list
    do_while: bool
    line: int


@dataclass
class Switch:
    var: str
    cases: list           # [(value text | None for default, [stmts])]
    line: int


@dataclass
class Jump:
    kind: str             # goto, call, return, end, break, continue
    label: str = None
    line: int = 0


@dataclass
class Label:
    name: str
    line: int


@dataclass
class Cond:
    kind: str             # not, and, or, flag, defeated, var, cmd, func
    args: list = field(default_factory=list)
    op: str = None
    value: str = None
    a: object = None
    b: object = None


@dataclass
class Script:
    name: str
    body: list
    local: bool
    line: int


@dataclass
class TextBlock:
    name: str
    value: str
    line: int


@dataclass
class Movement:
    name: str
    items: list
    line: int


@dataclass
class MapScripts:
    name: str
    entries: list         # [(type, label | None, [stmts] | None)]
    frame_table: list     # [(var, value, label | None, [stmts] | None)]
    frame_table_pos: int  # index in entries where the frame table entry sits, or None
    line: int


@dataclass
class ScrDefs:
    names: list           # script labels in number order (script n = index + 1)
    line: int


@dataclass
class Raw:
    text: str
    line: int


@dataclass
class Program:
    items: list
    consts: dict


# --- parser ------------------------------------------------------------------

STMT_KEYWORDS = {"if", "while", "do", "switch", "break", "continue", "goto", "call", "return", "end",
                 "poryswitch"}


class Parser:
    def __init__(self, src, path=None, switches=None):
        self.src, self.path = src, path
        self.toks = tokenize(src, path)
        self.i = 0
        self.consts = {}
        self.switches = switches or {}

    # helpers
    @property
    def tok(self):
        return self.toks[self.i]

    def peek(self, n=1):
        return self.toks[min(self.i + n, len(self.toks) - 1)]

    def error(self, msg, tok=None):
        raise PoryError(msg, self.path, (tok or self.tok).line)

    def next(self):
        t = self.tok
        self.i += 1
        return t

    def accept(self, text):
        if self.tok.text == text and self.tok.kind in ("op", "ident"):
            return self.next()
        return None

    def expect(self, text):
        t = self.accept(text)
        if t is None:
            self.error("expected %r, found %r" % (text, self.tok.text or "end of file"))
        return t

    def ident(self):
        if self.tok.kind != "ident":
            self.error("expected a name, found %r" % (self.tok.text or "end of file"))
        return self.next().text

    def skip_semis(self):
        while self.accept(";"):
            pass

    def sub(self, text):
        """Apply `const` substitutions to an argument/value."""
        return self.consts.get(text, text)

    def expr_until(self, stops):
        """Source text of an expression up to a top-level stop token (not consumed)."""
        depth, start = 0, self.tok.start
        end = start
        while True:
            t = self.tok
            if t.kind == "eof":
                self.error("unexpected end of file")
            if depth == 0 and t.text in stops and t.kind == "op":
                break
            if t.text in "([":
                depth += 1
            elif t.text in ")]":
                if depth == 0:
                    break
                depth -= 1
            end = t.end
            self.next()
        text = self.src[start:end].strip()
        if not text:
            self.error("expected a value")
        return self.sub(text)

    # top level
    def parse(self):
        items = []
        while self.tok.kind != "eof":
            items.extend(self.top())
        return Program(items, self.consts)

    def top(self):
        t = self.tok
        if t.kind == "ident" and t.text == "script":
            self.next()
            local = False
            if self.accept("("):
                scope = self.ident()
                if scope not in ("local", "global"):
                    self.error("script scope must be local or global")
                local = scope == "local"
                self.expect(")")
            name = self.ident()
            return [Script(name, self.block(), local, t.line)]
        if t.kind == "ident" and t.text == "text":
            self.next()
            name = self.ident()
            self.expect("{")
            value = self.string_value()
            self.expect("}")
            return [TextBlock(name, value, t.line)]
        if t.kind == "ident" and t.text == "movement":
            self.next()
            name = self.ident()
            self.expect("{")
            items = self.move_items("}")
            self.expect("}")
            return [Movement(name, items, t.line)]
        if t.kind == "ident" and t.text == "mapscripts":
            self.next()
            return [self.mapscripts(t.line)]
        if t.kind == "ident" and t.text == "scrdefs":
            self.next()
            self.expect("{")
            names = []
            while not self.accept("}"):
                names.append(self.ident())
                self.accept(",")
            return [ScrDefs(names, t.line)]
        if t.kind == "ident" and t.text == "raw":
            self.next()
            if self.tok.kind != "raw":
                self.error("expected a `...` block after raw")
            return [Raw(self.next().text[1:-1], t.line)]
        if t.kind == "ident" and t.text == "const":
            self.next()
            name = self.ident()
            self.expect("=")
            start = self.tok.start
            end = start
            while self.tok.kind != "eof" and self.tok.line == t.line:
                end = self.tok.end
                self.next()
            self.consts[name] = self.src[start:end].strip()
            return []
        self.error("expected script, text, movement, mapscripts, scrdefs, raw or const; found %r" % t.text)

    # strings
    def string_value(self):
        parts = []
        while self.tok.kind == "string":
            parts.append(unescape(self.next().text[1:-1]))
        if not parts:
            self.error("expected a string")
        return "".join(parts)

    # movement
    def move_items(self, stop):
        items = []
        while self.tok.text != stop:
            if self.tok.kind != "ident":
                self.error("expected a movement command, found %r" % self.tok.text)
            name = self.next().text
            count = 1
            if self.accept("*"):
                if self.tok.kind != "number":
                    self.error("expected a count after *")
                count = int(self.next().text, 0)
            items.append((name, count))
            self.accept(",")
        return items

    # mapscripts
    def mapscripts(self, line):
        name = self.ident()
        self.expect("{")
        entries, table, table_pos = [], [], None
        while not self.accept("}"):
            kind = self.ident()
            if self.accept("["):
                table_pos = len(entries)
                entries.append((kind, None, None))
                while not self.accept("]"):
                    var = self.expr_until({","})
                    self.expect(",")
                    value = self.expr_until({":", "{"})
                    if self.accept(":"):
                        table.append((var, value, self.label_ref(), None))
                    else:
                        table.append((var, value, None, self.block()))
                    self.accept(",")
                continue
            if self.accept(":"):
                entries.append((kind, self.label_ref(), None))
            else:
                entries.append((kind, None, self.block()))
        return MapScripts(name, entries, table, table_pos, line)

    def label_ref(self):
        """A script label or a constant expression, up to the end of the line."""
        t = self.tok
        start, end, line = t.start, t.end, t.line
        while self.tok.kind != "eof" and self.tok.line == line and self.tok.text not in ("]", "}"):
            end = self.tok.end
            self.next()
        return self.sub(self.src[start:end].strip())

    # statements
    def block(self):
        self.expect("{")
        body = []
        while not self.accept("}"):
            if self.tok.kind == "eof":
                self.error("missing }")
            body.extend(self.statement())
            self.skip_semis()
        return body

    def statement(self):
        t = self.tok
        if t.kind != "ident":
            self.error("expected a statement, found %r" % t.text)
        w = t.text
        if self.peek().text == ":" and self.peek().kind == "op" and w not in STMT_KEYWORDS:
            self.next()
            self.next()
            return [Label(w, t.line)]
        if w == "if":
            self.next()
            branches = [(self.paren_cond(), self.block())]
            else_body = None
            while True:
                if self.accept("elif"):
                    branches.append((self.paren_cond(), self.block()))
                elif self.accept("else"):
                    if self.tok.text == "if":  # else if
                        self.next()
                        branches.append((self.paren_cond(), self.block()))
                        continue
                    else_body = self.block()
                    break
                else:
                    break
            return [If(branches, else_body, t.line)]
        if w == "while":
            self.next()
            cond = self.paren_cond() if self.tok.text == "(" else None
            return [While(cond, self.block(), False, t.line)]
        if w == "do":
            self.next()
            body = self.block()
            self.expect("while")
            return [While(self.paren_cond(), body, True, t.line)]
        if w == "switch":
            self.next()
            self.expect("(")
            self.expect("var")
            self.expect("(")
            var = self.expr_until({")"})
            self.expect(")")
            self.expect(")")
            self.expect("{")
            cases = []
            while not self.accept("}"):
                if self.accept("case"):
                    value = self.expr_until({":"})
                    self.expect(":")
                elif self.accept("default"):
                    value = None
                    self.expect(":")
                else:
                    self.error("expected case or default")
                body = []
                while self.tok.text not in ("case", "default", "}"):
                    body.extend(self.statement())
                    self.skip_semis()
                cases.append((value, body))
            return [Switch(var, cases, t.line)]
        if w in ("break", "continue", "return", "end"):
            self.next()
            if self.accept("("):
                self.expect(")")
            return [Jump(w, None, t.line)]
        if w in ("goto", "call"):
            self.next()
            self.expect("(")
            label = self.expr_until({")"})
            self.expect(")")
            return [Jump(w, label, t.line)]
        if w == "poryswitch":
            return self.poryswitch(self.statement_list)
        return [self.command()]

    def statement_list(self):
        if self.tok.text == "{":
            return self.block()
        return self.statement()

    def poryswitch(self, body_fn):
        self.next()
        self.expect("(")
        key = self.ident()
        self.expect(")")
        self.expect("{")
        chosen, default = None, None
        want = self.switches.get(key)
        while not self.accept("}"):
            value = self.next().text
            self.accept(":")
            body = body_fn()
            if value == want:
                chosen = body
            elif value == "_":
                default = body
        out = chosen if chosen is not None else default
        if out is None:
            self.error("poryswitch(%s): no case for %r" % (key, want))
        return out

    def command(self):
        t = self.tok
        name = self.next().text
        args = []
        if self.tok.text == "(" and self.tok.line == t.line:
            self.next()
            while not self.accept(")"):
                if self.tok.kind == "string":
                    args.append(Text(self.string_value()))
                elif self.tok.text in ("moves",) and self.peek().text == "(":
                    self.next()
                    self.expect("(")
                    args.append(Moves(self.move_items(")")))
                    self.expect(")")
                else:
                    args.append(self.expr_until({","}))
                self.accept(",")
        return Command(name, args, t.line)

    # conditions
    def paren_cond(self):
        self.expect("(")
        c = self.cond_or()
        self.expect(")")
        return c

    def cond_or(self):
        c = self.cond_and()
        while self.accept("||"):
            c = Cond("or", a=c, b=self.cond_and())
        return c

    def cond_and(self):
        c = self.cond_unary()
        while self.accept("&&"):
            c = Cond("and", a=c, b=self.cond_unary())
        return c

    def cond_unary(self):
        if self.accept("!"):
            return Cond("not", a=self.cond_unary())
        if self.tok.text == "(":
            self.next()
            c = self.cond_or()
            self.expect(")")
            return c
        return self.cond_atom()

    def cond_atom(self):
        t = self.tok
        name = self.ident()
        self.expect("(")
        args = []
        while not self.accept(")"):
            args.append(self.expr_until({","}))
            self.accept(",")
        op, value = None, None
        if self.tok.text in ("==", "!=", "<", "<=", ">", ">=") and self.tok.kind == "op":
            op = self.next().text
            value = self.expr_until({"&&", "||", ")"})
        kind = name if name in ("flag", "var", "defeated") else "call"
        c = Cond(kind, args=args, op=op, value=value)
        c.name = name
        c.line = t.line
        return c


def parse(src, path=None, switches=None):
    return Parser(src, path, switches).parse()
