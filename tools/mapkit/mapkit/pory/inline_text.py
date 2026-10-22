# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Move a map's dialog from text.json into scripts.pory.

A message used by one script command becomes an inline string there:
    npcmsg(msg_0375_R30_00001)  ->  npcmsg("What? This is a big battle!\\f"
                                           "Leave me alone!\\r")
and its text.json entry keeps the message's place in the bank:
    {"id": "msg_0375_R30_00001", "from": "scr_seq_R30_000#0"}   (the script's string 0)
A message used by several commands becomes a `text <id> { ... }` block after the
first script that uses it ({"id": ..., "from": "text"}). Messages used from C/asm,
other files, raw blocks or nowhere stay in text.json.

Each map is compiled before and after and must give the same commands and the same
bank text, or it is left unchanged.
"""

import glob
import json
import os
import re

from .. import layout
from . import compiler, decompile

_SCRIPT_RE = re.compile(r"^script(?:\((?:local|global)\))?\s+(\w+)\s*\{\s*$")
_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"')
_ESC = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\f": "\\f", "\t": "\\t"}


def literal_parts(value):
    """Text -> list of "..." literals, one per line of dialog (split after \\n \\r \\f)."""
    parts = re.findall(r"[^\n\r\f]*[\n\r\f]|[^\n\r\f]+$", value) or [""]
    return ['"%s"' % "".join(_ESC.get(c, c) for c in p) for p in parts]


def text_value(message):
    t = message.get("en_US", "")
    return "".join(t) if isinstance(t, list) else t


def outside_refs(root):
    """Message ids used anywhere but map scripts.pory / text.json files."""
    refs = set()
    pat = re.compile(r"\bmsg_\d{4}_\w+?_\d{5}\b")
    for top in ("src", "asm", "include", "files", "data", "tools"):
        for path in glob.glob(os.path.join(root, top, "**", "*"), recursive=True):
            base = os.path.basename(path)
            if not os.path.isfile(path) or base in ("scripts.pory", "text.json") \
                    or not path.endswith((".c", ".h", ".s", ".inc", ".json", ".pory", ".txt")):
                continue
            if "/msgdata/msg/" in path and path.endswith(".json"):
                continue  # other text banks
            with open(path, encoding="utf-8", errors="ignore") as f:
                refs |= set(pat.findall(f.read()))
    return refs


class Converter:
    def __init__(self, repo, entry, outside):
        self.repo, self.entry = repo, entry
        self.folder = os.path.join(repo.root, layout.MAPS_DIR, entry["dir"])
        self.outside = outside

    def run(self):
        """Returns (new pory text, new bank dict, inlined, text blocks) or None if nothing to do."""
        with open(os.path.join(self.folder, "scripts.pory"), encoding="utf-8") as f:
            lines = f.read().split("\n")
        with open(os.path.join(self.folder, "text.json"), encoding="utf-8") as f:
            bank = json.load(f)
        content = {m["id"]: m for m in bank["messages"] if "en_US" in m and "from" not in m}
        tok = re.compile(r"\b(%s)\b" % "|".join(re.escape(i) for i in content)) if content else None
        if tok is None:
            return None

        # where each message id appears: (line, script) for script command lines, else None
        uses = {}
        script, in_raw, depth = None, False, 0
        for i, line in enumerate(lines):
            s = line.strip()
            if in_raw:
                if "`" in line:
                    in_raw = False
                for mm in tok.finditer(line):
                    uses.setdefault(mm.group(1), []).append(None)
                continue
            if s.startswith("raw `") and s.count("`") == 1:
                in_raw = True
                continue
            if script is None:
                m = _SCRIPT_RE.match(line)
                if m:
                    script, depth = m.group(1), 1
                    continue
                for mm in tok.finditer(line):
                    uses.setdefault(mm.group(1), []).append(None)
                continue
            if s == "}" and line == "}":
                script = None
                continue
            for mm in tok.finditer(line):
                uses.setdefault(mm.group(1), []).append((i, script))

        inline, blocks = {}, {}
        for mid, us in uses.items():
            if mid in self.outside or None in us:
                continue
            if len(us) == 1:
                inline[mid] = us[0]
            else:
                blocks[mid] = us[0][1]  # after the first script that uses it
        if not inline and not blocks:
            return None

        # rewrite script lines; number strings per script in source order
        slots = {}
        out, script, counter = [], None, {}
        after = {}  # script -> text block lines to add after it
        for mid, sc in blocks.items():
            body = literal_parts(text_value(content[mid]))
            after.setdefault(sc, []).append(["", "text %s {" % mid] + ["    " + b for b in body] + ["}"])
        for i, line in enumerate(lines):
            if script is None:
                m = _SCRIPT_RE.match(line)
                out.append(line)
                if m:
                    script = m.group(1)
                    counter.setdefault(script, 0)
                continue
            if line == "}":
                out.append(line)
                for blk in after.pop(script, []):
                    out += blk
                script = None
                continue
            pos = 0
            # walk strings and inlinable ids left to right
            events = sorted([(mm.start(), mm.end(), "str", None) for mm in _STRING_RE.finditer(line)] +
                            [(mm.start(), mm.end(), "id", mm.group(1)) for mm in tok.finditer(line)
                             if inline.get(mm.group(1), (None,))[0] == i])
            if not events:
                out.append(line)
                continue
            text = ""
            for start, end, kind, mid in events:
                text += line[pos:start]
                if kind == "str":
                    text += line[start:end]
                else:
                    slots[mid] = "%s#%d" % (script, counter[script])
                    parts = literal_parts(text_value(content[mid]))
                    col = len(text.split("\n")[-1])
                    text += ("\n" + " " * col).join(parts)
                counter[script] += 1
                pos = end
            text += line[pos:]
            out += text.split("\n")

        new_messages = []
        for m in bank["messages"]:
            if m.get("id") in slots:
                new_messages.append({"id": m["id"], "from": slots[m["id"]]})
            elif m.get("id") in blocks:
                new_messages.append({"id": m["id"], "from": "text"})
            else:
                new_messages.append(m)
        new_bank = dict(bank, messages=new_messages)
        return "\n".join(out), new_bank, len(slots), len(blocks)


def convert(repo, entry, outside, write=True):
    """Convert one map; returns (inlined, blocks) or raises CompileError if the result
    wouldn't build the same."""
    from . import compile_source, context, merged_text
    c = Converter(repo, entry, outside)
    r = c.run()
    if r is None:
        return 0, 0
    new_src, new_bank, n_inline, n_blocks = r
    pory_path = os.path.join(c.folder, "scripts.pory")
    text_path = os.path.join(c.folder, "text.json")
    with open(pory_path, encoding="utf-8") as f:
        old_src = f.read()
    with open(text_path, encoding="utf-8") as f:
        old_text = f.read()
    old_bank = json.loads(old_text)
    for game in ("HEARTGOLD", "SOULSILVER"):
        ctx = context(repo, entry, repo.macros)
        before = compile_source(old_src, ctx, {"GAME": game})
        ctx.text_slots = {m["from"]: m["id"] for m in new_bank["messages"] if "#" in m.get("from", "")}
        after = compile_source(new_src, ctx, {"GAME": game})
        if decompile.fingerprint(before.scripts_inc, repo.macros) != \
                decompile.fingerprint(after.scripts_inc, repo.macros) or before.public != after.public:
            raise compiler.CompileError("%s: commands changed" % entry["dir"])
        unfilled = []
        bank = merged_text(repo, entry, after, unfilled, new_bank)["messages"]
        want = [(m.get("id"), text_value(m), m.get("garbage")) for m in old_bank["messages"]]
        got = [(m.get("id"), text_value(m), m.get("garbage")) for m in bank]
        if want != got or unfilled:
            raise compiler.CompileError("%s: text changed" % entry["dir"])
    if write:
        with open(pory_path, "w", encoding="utf-8") as f:
            f.write(new_src)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(new_bank, indent=2, ensure_ascii=False) + "\n")
    return n_inline, n_blocks

