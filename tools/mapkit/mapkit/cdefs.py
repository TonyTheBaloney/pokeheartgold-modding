# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
"""Read #define constants from C headers and evaluate simple expressions.

Handles object-like and function-like macros, #ifdef/#ifndef/#if defined()
/#else/#endif for a given set of defined names, and integer arithmetic.
Anything else (casts, sizeof, strings) makes evaluation return None.
"""

import ast
import operator
import re

_DEFINE_RE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)(\(([^)]*)\))?\s*(.*)$")
_TOKEN_RE = re.compile(r"[A-Za-z_]\w*|0[xX][0-9a-fA-F]+[uUlL]*|\d+[uUlL]*|##|<<|>>|\S")
_INT_RE = re.compile(r"^(0[xX][0-9a-fA-F]+|\d+)[uUlL]*$")

_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.LShift: operator.lshift, ast.RShift: operator.rshift,
    ast.BitOr: operator.or_, ast.BitAnd: operator.and_, ast.BitXor: operator.xor,
}
_UNOPS = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Invert: operator.invert}


def _strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNOPS:
        return _UNOPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("unsupported expression")


class Defines:
    """A table of macros. `parent` is consulted for names not defined here."""

    def __init__(self, defined=(), parent=None):
        self.objects = {}      # name -> body text
        self.functions = {}    # name -> (params, body text)
        self.origin = {}       # name -> path it came from
        self.defined = set(defined)
        self.parent = parent
        self._cache = {}

    def load(self, path):
        with open(path, encoding="utf-8", errors="replace") as f:
            text = _strip_comments(f.read())
        text = text.replace("\\\n", " ")
        stack = []  # one bool per open #if: is this branch active?
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#"):
                d = s[1:].strip()
                active = all(stack)
                if d.startswith("ifdef "):
                    stack.append(d.split()[1] in self.defined or self._has(d.split()[1]))
                elif d.startswith("ifndef "):
                    stack.append(not (d.split()[1] in self.defined or self._has(d.split()[1])))
                elif d.startswith("if "):
                    m = re.match(r"if\s+!?\s*defined\s*\(?\s*(\w+)", d)
                    if m:
                        val = m.group(1) in self.defined or self._has(m.group(1))
                        stack.append(not val if "!" in d.split("defined")[0] else val)
                    else:
                        v = self.eval(d[3:])
                        stack.append(bool(v) if v is not None else True)
                elif d.startswith("elif"):
                    stack[-1] = False
                elif d.startswith("else"):
                    if stack:
                        stack[-1] = not stack[-1]
                elif d.startswith("endif"):
                    if stack:
                        stack.pop()
                elif active and d.startswith("define"):
                    self._add_define(s, path)
                elif active and d.startswith("undef"):
                    self.objects.pop(d.split()[1], None)
                    self.functions.pop(d.split()[1], None)
        self._cache.clear()
        return self

    def _add_define(self, line, path):
        m = _DEFINE_RE.match(line)
        if not m:
            return
        name, is_func, params, body = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        if is_func is not None and line[line.index(name) + len(name)] == "(":
            self.functions[name] = ([p.strip() for p in params.split(",") if p.strip()], body)
        else:
            self.objects[name] = body
        self.origin[name] = path

    def _has(self, name):
        return name in self.objects or name in self.functions or (
            self.parent is not None and self.parent._has(name))

    def _lookup_obj(self, name):
        if name in self.objects:
            return self.objects[name]
        return self.parent._lookup_obj(name) if self.parent else None

    def _lookup_func(self, name):
        if name in self.functions:
            return self.functions[name]
        return self.parent._lookup_func(name) if self.parent else None

    def names(self, prefix=""):
        out = set(n for n in self.objects if n.startswith(prefix))
        if self.parent:
            out |= self.parent.names(prefix)
        return out

    def where(self, name):
        if name in self.origin:
            return self.origin[name]
        return self.parent.where(name) if self.parent else None

    def _expand(self, tokens, depth, seen):
        if depth > 40:
            raise ValueError("macro expansion too deep")
        out = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            func = self._lookup_func(t) if t not in seen else None
            if func and i + 1 < len(tokens) and tokens[i + 1] == "(":
                # collect arguments up to the matching paren
                args, cur, level, j = [], [], 0, i + 1
                while j < len(tokens):
                    tok = tokens[j]
                    if tok == "(":
                        level += 1
                        if level == 1:
                            j += 1
                            continue
                    elif tok == ")":
                        level -= 1
                        if level == 0:
                            break
                    if tok == "," and level == 1:
                        args.append(cur)
                        cur = []
                    else:
                        cur.append(tok)
                    j += 1
                args.append(cur)
                params, body = func
                sub = {}
                for p, a in zip(params, args):
                    sub[p] = self._expand(a, depth + 1, seen)
                body_toks = []
                for bt in _TOKEN_RE.findall(body):
                    body_toks.extend(sub.get(bt, [bt]))
                out.extend(self._expand(body_toks, depth + 1, seen | {t}))
                i = j + 1
                continue
            body = self._lookup_obj(t) if t not in seen else None
            if body is not None and re.match(r"[A-Za-z_]", t):
                out.extend(self._expand(_TOKEN_RE.findall(body), depth + 1, seen | {t}))
            else:
                out.append(t)
            i += 1
        return out

    def eval(self, expr):
        """Evaluate an int, a constant name or an arithmetic expression; None if unknown."""
        if isinstance(expr, bool):
            return int(expr)
        if isinstance(expr, int):
            return expr
        if expr is None:
            return None
        expr = str(expr).strip()
        if expr in self._cache:
            return self._cache[expr]
        try:
            toks = self._expand(_TOKEN_RE.findall(expr), 0, frozenset())
            py = []
            for t in toks:
                m = _INT_RE.match(t)
                if m:
                    py.append(str(int(m.group(1), 0)))
                elif t == "/":
                    py.append("//")
                elif re.match(r"[A-Za-z_]", t):
                    raise ValueError("undefined name " + t)
                else:
                    py.append(t)
            value = _eval_ast(ast.parse(" ".join(py), mode="eval"))
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError, RecursionError):
            value = None
        self._cache[expr] = value
        return value

    def child(self):
        return Defines(self.defined, parent=self)
