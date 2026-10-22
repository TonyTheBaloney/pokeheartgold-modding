# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Give scripts and movements pokeemerald-style names.

    scr_seq_R30_010         -> Route30_EventScript_Lass
    scr_seq_R30_005         -> Route30_EventScript_RouteSign
    Route30_Movement_01D4   -> Route30_Movement_PlayerWalkDownLeft

Who an object is comes from tools/mapkit/npc_names.json (named characters first),
then the speaker in its dialog ("Archer: ..."), the trainer it battles, and the
sprite's class. Several with one name are numbered (Man1, Man2), as in
pokeemerald. Signs are named from their first line, triggers and frame-table
scripts after who they're about, map scripts <Map>_OnTransition etc. Only
generated names (scr_seq_*, <Map>_Movement_<offset>) are renamed, and only
scripts something refers to; renames go through every file that uses the label.
"""

import json
import os
import re
import unicodedata

from .. import layout
from . import compiler
from . import parser as P

CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "npc_names.json")
GENERATED_SCRIPT = re.compile(r"^scr_seq_\w+$")
_SPEAKER = re.compile(r"^([A-Z][A-Za-z.'’é]*(?: [A-Z][A-Za-z.'’é]*){0,2}):\s")
_EV_REF = re.compile(r"^_EV_(\w+)\s*\+\s*1$")
_DIRS = ("up", "down", "left", "right")
_TITLES = {"Professor": "Prof", "Mister": "Mr"}


def camel(text):
    """'Professor Elm' -> 'ProfElm', 'Mr. Pokémon' -> 'MrPokemon', 'Lt. Surge' -> 'LtSurge'."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[’'.]", "", text)
    words = [w for w in re.split(r"[^A-Za-z0-9]+", text) if w]
    words = [_TITLES.get(w, w) for w in words]
    words = [w.title() if w.isupper() and len(w) > 3 else w for w in words]  # FARFETCHD -> Farfetchd
    return "".join(w[0].upper() + w[1:] for w in words)


def first_line(value):
    line = re.split(r"[\n\r\f]", value, 1)[0]
    return re.sub(r"\{[^}]*\}", "", line).strip()


class MapNamer:
    def __init__(self, repo, entry, config, trainers, borrowers):
        self.repo, self.entry = repo, entry
        self.map = entry["dir"]
        self.config = config
        self.trainers = trainers
        folder = os.path.join(repo.root, layout.MAPS_DIR, self.map)
        with open(os.path.join(folder, "scripts.pory"), encoding="utf-8") as f:
            self.prog = P.parse(f.read(), "scripts.pory", {"GAME": "HEARTGOLD"})
        self.scripts = {it.name: it for it in self.prog.items if isinstance(it, P.Script)}
        self.movements = [it for it in self.prog.items if isinstance(it, P.Movement)]
        self.texts = {it.name: it.value for it in self.prog.items if isinstance(it, P.TextBlock)}
        m = repo.map_by_name(entry["map"])
        bank = repo.text_bank(m)
        if bank is not None:
            for msg in bank.messages:
                self.texts.setdefault(msg.get("id"), bank.text_of(msg))
        self.events = []  # (kind, record) from this map and maps that borrow its scripts
        for d in [self.map] + borrowers:
            with open(os.path.join(repo.root, layout.MAPS_DIR, d, "map.json"), encoding="utf-8") as f:
                doc = json.load(f)
            for kind in ("object_events", "bg_events", "coord_events"):
                for rec in doc.get(kind, []):
                    self.events.append((kind, rec))
        self.objects = {rec.get("local_id"): rec for k, rec in self.events if k == "object_events"}
        self.public = compiler.Compiler(compiler.Context(repo.macros, compiler.load_config())).public_scripts(self.prog)

    # --- facts about a script -------------------------------------------------

    def commands(self, body):
        out = []

        def walk(stmts):
            for s in stmts:
                if isinstance(s, P.Command):
                    out.append(s)
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
        return out

    def script_texts(self, name):
        s = self.scripts.get(name)
        out = []
        for c in self.commands(s.body) if s else []:
            for a in c.args:
                if isinstance(a, P.Text):
                    out.append(a.value)
                elif isinstance(a, str) and a in self.texts:
                    out.append(self.texts[a])
        return out

    def speaker(self, name):
        for t in self.script_texts(name):
            m = _SPEAKER.match(t)
            if m and m.group(1) not in ("PA",):
                return camel(m.group(1))
        return None

    def trainer(self, name):
        s = self.scripts.get(name)
        for c in self.commands(s.body) if s else []:
            if c.name.lower() == "trainerbattle" and c.args and isinstance(c.args[0], str):
                return self.trainer_name(c.args[0])
        return None

    def trainer_name(self, const):
        i = self.repo.defines.eval(const)
        if i is None or not 0 <= i < len(self.trainers):
            return None
        t = self.trainers[i]
        if t["class"] == "TRAINERCLASS_RIVAL":
            return "Rival"
        return camel(re.sub(r"\{[^}]*\}", "", t["name"])) or None

    def has_command(self, name, cmd):
        s = self.scripts.get(name)
        return any(c.name.lower() == cmd for c in self.commands(s.body)) if s else False

    # --- who an object is -------------------------------------------------------

    def object_name(self, rec):
        sprite = rec.get("graphics_id", "")
        label = self.script_label(rec.get("script"))
        if label and not GENERATED_SCRIPT.match(label) and "_EventScript_" in label:
            return label.split("_EventScript_", 1)[1]  # a name someone already chose
        if sprite in self.config["characters"]:
            return self.config["characters"][sprite]
        if label:
            who = self.speaker(label) or self.trainer(label)
            if who:
                return who
        m = re.match(r"std_trainer\((TRAINER_\w+)\)", str(rec.get("script")))
        if m and self.trainer_name(m.group(1)):
            return self.trainer_name(m.group(1))
        for sp in (sprite, re.sub(r"_\d+$", "", sprite)):
            if sp in self.config["classes"]:
                return self.config["classes"][sp]
        mm = re.match(r"SPRITE_FOLLOWER_MON_STATIC_(\w+)", sprite)
        if mm:
            return camel(mm.group(1).replace("_", " ").title().replace("Spiky", "").replace(" F", "F").replace(" M", "M"))
        base = re.sub(r"(_?\d+)+$", "", sprite.replace("SPRITE_", ""))
        return camel(base.replace("_", " ").title()) or "Object"

    def script_label(self, value):
        v = str(value).strip()
        m = _EV_REF.match(v)
        if m:
            v = m.group(1)
        return v if v in self.scripts else None

    def actor(self, label):
        """Who a trigger or scene is about: a speaker, an object it moves, or a trainer."""
        who = self.speaker(label)
        if who:
            return who
        s = self.scripts.get(label)
        for c in self.commands(s.body) if s else []:
            if c.args and isinstance(c.args[0], str) and c.args[0] in self.objects:
                return self.object_name(self.objects[c.args[0]])
        trainer = self.trainer(label)
        if trainer:
            return trainer
        for c in self.commands(s.body) if s else []:
            if c.name.lower() == "phonecall" and c.args and isinstance(c.args[0], str):
                return self.contact(c.args[0]) + "Call"
            if c.name.lower() == "warp" and c.args and isinstance(c.args[0], str):
                dest = self.repo.migrated.get(c.args[0])
                if dest:
                    return "WarpTo" + dest["dir"].replace("_", "")
        return ""

    def contact(self, const):
        if const in self.config.get("phone_contacts", {}):
            return self.config["phone_contacts"][const]
        return camel(const.replace("PHONE_CONTACT_", "").replace("__", ". ").replace("_", " ").title())

    # --- names ------------------------------------------------------------------

    def sign_name(self, label):
        if self.has_command(label, "trainertipsex"):
            return "TrainerTips"
        texts = self.script_texts(label)
        line = first_line(texts[0]) if texts else ""
        line = re.sub(r"^Rt\. ?", "Route ", line)
        m = re.match(r"Welcome to (.+?)!?$", line)
        if m:
            line = m.group(1)
        own = re.match(r"Route \d+", line)
        if own and camel(own.group(0)) == self.map:  # this route's own sign
            rest = re.sub(r"\b(City|Town|Ahead|to)\b", "", line[own.end():])
            return "RouteSign" + camel(rest)
        c = camel(line)
        if c in (self.map + "City", self.map + "Town"):
            return "TownSign" if c.endswith("Town") else "CitySign"
        head = re.sub(r"[!…]+$", "", line).strip()
        if line and len(line) <= 32 and not re.search(r"[.!?,…]", line.replace("Mr.", "").replace("Lt.", "")) \
                and self.has_command(label, "directionsignpostex") or (
                    head and len(head.split()) <= 4 and not re.search(r"[.?,…:“”\"{]", head) and len(texts) == 1):
            return camel(head) + "Sign"
        whole = " ".join(texts)
        for key, name in self.config.get("things", {}).items():
            if key.startswith("_"):
                continue
            if re.search(r"(?<![A-Za-z])%s(?![a-z])" % re.escape(key), whole, 0 if key[:1].isupper() and key.isupper() else re.I):
                return name
        return "Sign"

    def script_names(self):
        """{old label: base name (without the map prefix)} for scripts to rename."""
        want = {}
        for kind, rec in self.events:
            label = self.script_label(rec.get("script"))
            if not label or label in want or not GENERATED_SCRIPT.match(label):
                continue
            if kind == "object_events":
                want[label] = "EventScript_" + self.object_name(rec)
            elif kind == "bg_events":
                want[label] = "EventScript_" + self.sign_name(label)
            else:
                who = self.actor(label)
                want[label] = "EventScript_" + (who if bare(who) else who + "Trigger")
        for ms in (it for it in self.prog.items if isinstance(it, P.MapScripts)):
            for kind, label, body in ms.entries:
                if label in self.scripts and label not in want and GENERATED_SCRIPT.match(label):
                    want[label] = "On" + kind.split("_ON_")[-1].title().replace("_", "")
            for var, value, label, body in ms.frame_table:
                if label in self.scripts and label not in want and GENERATED_SCRIPT.match(label):
                    who = self.actor(label)
                    want[label] = "EventScript_" + (who if bare(who) else who + "Scene")
        return want

    def movement_names(self, script_new):
        """{old movement label: base name} for <Map>_Movement_<hex> blocks something applies."""
        actor = {}
        for name, s in self.scripts.items():
            for c in self.commands(s.body):
                if len(c.args) >= 2 and all(isinstance(a, str) for a in c.args[:2]):
                    obj, mv = c.args[0], c.args[1]
                    if mv not in actor and c.name.lower() == "applymovement":
                        actor[mv] = self.movement_actor(obj)
        want = {}
        for mv in self.movements:
            if mv.name in actor and re.fullmatch(r"%s_Movement_[0-9A-Fa-f]+" % re.escape(self.map), mv.name):
                want[mv.name] = "Movement_" + actor[mv.name] + action(mv.items)
        return want

    def movement_actor(self, obj):
        if obj == "obj_player":
            return "Player"
        if obj == "obj_partner_poke":
            return "FollowMon"
        rec = self.objects.get(obj)
        return self.object_name(rec) if rec else "Object"

    def plan(self):
        """{old: new} for this map's scripts and movements."""
        taken = set(self.scripts) | {m.name for m in self.movements} | {
            l.name for s in self.scripts.values() for l in _labels(s.body)}
        out = {}
        for want in (self.script_names(),):
            out.update(number(self.map, want, self.public + list(self.scripts), taken))
        mv = self.movement_names(out)
        out.update(number(self.map, mv, [m.name for m in self.movements], taken | set(out.values())))
        return out


def bare(who):
    """Names that already say what happens (no Trigger/Scene suffix)."""
    return who.startswith("WarpTo") or who.endswith("Call")


def plan_all(repo, maps=None):
    """{map dir: {old: new}} for maps that own their scripts.pory."""
    with open(CONFIG, encoding="utf-8") as f:
        config = json.load(f)
    with open(repo.path("files/poketool/trainer/trainers.json"), encoding="utf-8") as f:
        trainers = json.load(f)["trainers"]
    out = {}
    for m in maps if maps is not None else repo.maps:
        e = repo.migrated.get(m.name)
        pe = repo.pory_entry(m)
        if not e or pe is None or pe["dir"] != e["dir"]:
            continue
        borrowers = [o["dir"] for o in repo.migrated.values() if o["scripts"] == "@" + e["dir"]]
        out[e["dir"]] = MapNamer(repo, e, config, trainers, borrowers).plan()
    return out


_TEXT_FILES = (".pory", ".json", ".h", ".c", ".s", ".inc", ".md", ".py")


def apply(repo, plans):
    """Rename everywhere: map folders, C/asm/includes, docs and tests. Returns files changed."""
    renames = {old: new for p in plans.values() for old, new in p.items()}
    word = re.compile(r"[A-Za-z_]\w*")

    def sub(mm):
        w = mm.group(0)
        if w in renames:
            return renames[w]
        if w.startswith("_EV_") and w[4:] in renames:
            return "_EV_" + renames[w[4:]]
        return w
    roots = ["data/maps", "src", "asm", "include", "files", "docs/modding", "tools/mapkit/tests",
             "tools/mapkit/README.md"]
    changed = []
    for r in roots:
        top = repo.path(r)
        paths = [top] if os.path.isfile(top) else [os.path.join(d, f) for d, _, fs in os.walk(top) for f in fs]
        for path in paths:
            if not path.endswith(_TEXT_FILES):
                continue
            with open(path, encoding="utf-8", newline="", errors="strict") as f:
                try:
                    text = f.read()
                except UnicodeDecodeError:
                    continue
            new = word.sub(sub, text)
            if os.path.basename(path) == "map.json":
                # pokeemerald style: refer to the map's own scripts by label
                own = set(plans.get(os.path.basename(os.path.dirname(path)), {}).values())
                new = re.sub(r'"_EV_(\w+) \+ 1"', lambda mm: '"%s"' % mm.group(1) if mm.group(1) in own else mm.group(0), new)
            if new != text:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(new)
                changed.append(path)
    return changed


def _labels(body):
    for s in body:
        if isinstance(s, P.Label):
            yield s
        elif isinstance(s, P.If):
            for _, b in s.branches:
                yield from _labels(b)
            yield from _labels(s.else_body or [])


def number(prefix, want, order, taken):
    """Map prefix + base names; numbered 1..n where several share one, in `order`."""
    pos = {n: i for i, n in reversed(list(enumerate(order)))}
    by = {}
    for old in sorted(want, key=lambda n: pos.get(n, 1 << 30)):
        by.setdefault(want[old], []).append(old)
    out = {}
    for base, olds in by.items():
        if len(olds) == 1 and "%s_%s" % (prefix, base) not in taken:
            out[olds[0]] = "%s_%s" % (prefix, base)
            continue
        n = 1
        for old in olds:
            while "%s_%s%d" % (prefix, base, n) in taken:
                n += 1
            out[old] = "%s_%s%d" % (prefix, base, n)
            n += 1
    return out


def _snake(name):
    return compiler._snake(name) if re.search(r"[A-Z]", name) else name


def action(items):
    """What a movement does, pokeemerald-style: FaceLeft, WalkUpLeft, Exit, JumpDown, Exclamation."""
    words = []
    for name, count in items:
        n = _snake(name).replace("on_spot", "in_place")
        n = n.replace("north", "up").replace("south", "down").replace("west", "left").replace("east", "right")
        words.append(n)
    words = [w.replace("run_", "walk_") for w in words]
    core = [w for w in words if not w.startswith("delay")]
    dirs = lambda ws: [d for w in ws for d in _DIRS if w.endswith("_" + d)]
    facing = lambda w: w.startswith("face_") or "in_place" in w
    if not core:
        return "Delay"
    if any(w.startswith("warp_") for w in core):
        return "Warp" + ("In" if any(w == "warp_in" for w in core) else "Out")
    if core[-1] == "set_invisible":
        return "Exit"
    if all(facing(w) for w in core):
        if len(set(dirs(core))) > 2:
            return "Spin"
        d = dirs(core[-1:])
        return "Face" + (d[0].title() if d else "")
    if all(w.startswith("emote") or facing(w) for w in core):
        emote = next(w for w in core if w.startswith("emote"))
        return "Exclamation" if "exclamation" in emote else ("Question" if "question" in emote else "Emote")
    walks = [w for w in core if w.startswith("walk") and "in_place" not in w]
    if walks:
        seq = []
        for d in dirs(walks):
            if not seq or seq[-1] != d:
                seq.append(d)
        return "Walk" + "".join(d.title() for d in seq[:2])
    jumps = [w for w in core if "jump" in w]
    if jumps:
        d = dirs(jumps[:1])
        return "Jump" + (d[0].title() if d else "")
    return "Move"
