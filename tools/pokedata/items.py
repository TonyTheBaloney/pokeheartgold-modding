#!/usr/bin/env python3
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
"""Items as one JSON file, built into everything the game reads about them.

data/items/items.json, keyed by item constant in item id order, like pokeemerald's
src/data/items.h (one entry per item: name, description, price, pocket, effects...):

    "ITEM_POTION": {
        "name": "Potion",
        "description": "A spray-type medicine for wounds.\\nIt restores the HP of one\\nPokémon by 20 points.",
        "price": 300,
        "holdEffect": "HOLD_EFFECT_NONE", "holdEffectParam": 0,
        "fieldPocket": "POCKET_MEDICINE", "battlePocket": ["BTLPOCKET_HP_RESTORE_F"],
        "fieldUseFunc": "ITEM_FIELD_USE_HEALING", "battleUseFunc": "ITEM_BATTLE_USE_RESTORE",
        ...
        "partyUse": true, "partyUseParam": {"hp_restore": true, "hp_restore_param": 20},
        ("partyUseIndex": 9 instead, for an item without party use: Timer Ball is ball 9)
        "icon": "item_icon_024", "palette": "item_icon_025", "gen3": "AGB_ITEM_POTION"
    }

The build makes from it (`items.py build`):

    item_data.csv       -> csv2bin -> itemtool/itemdata/item_data.narc   (ItemData, include/item.h)
    msg_0222.json       -> msgenc  -> item names         (GetItemNameIntoString)
    msg_0221.json       -> msgenc  -> item descriptions  (GetItemDescIntoString)
    item_narc_ids.h     -> src/item.c sItemNarcIds: data record, icon, palette, Gen 3 id

Usage:
    items.py build ITEMS.json OUT_DIR --include DIR
    items.py check ITEMS.json --include DIR
    items.py extract --root DIR [--out ITEMS.json]     (one-time, from the files above)
"""

import argparse
import csv
import io
import json
import os
import re
import sys

NAMES_BANK, DESCS_BANK = "msg_0222", "msg_0221"
NAMES_KEY, DESCS_KEY = 51885, 24316          # the banks' msgenc keys, kept so the ROM is unchanged
LANG = "en_US"

# item_data.csv columns in ItemData order (files/itemtool/itemdata/item_data.txt describes their widths)
TOP = ["price", "holdEffect", "holdEffectParam", "pluckEffect", "flingEffect", "flingPower", "naturalGiftPower",
       "naturalGiftType", "prevent_toss", "selectable", "fieldPocket", "battlePocket", "fieldUseFunc",
       "battleUseFunc", "partyUse"]
PARTY = ["slp_heal", "psn_heal", "brn_heal", "frz_heal", "prz_heal", "cfs_heal", "inf_heal", "guard_spec", "revive",
         "revive_all", "level_up", "evolve", "atk_stages", "def_stages", "spatk_stages", "spdef_stages",
         "speed_stages", "accuracy_stages", "critrate_stages", "pp_up", "pp_max", "pp_restore", "pp_restore_all",
         "hp_restore", "hp_ev_up", "atk_ev_up", "def_ev_up", "speed_ev_up", "spatk_ev_up", "spdef_ev_up",
         "friendship_mod_lo", "friendship_mod_med", "friendship_mod_hi", "hp_ev_up_param", "atk_ev_up_param",
         "def_ev_up_param", "speed_ev_up_param", "spatk_ev_up_param", "spdef_ev_up_param", "hp_restore_param",
         "pp_restore_param", "friendship_mod_lo_param", "friendship_mod_med_param", "friendship_mod_hi_param"]
BOOLS = {"prevent_toss", "selectable"} | {k for k in PARTY if not k.endswith(("_stages", "_param"))}
# bit widths, for range checks (include/item.h)
WIDTH = {"price": (0, 0xFFFF), "holdEffectParam": (0, 255), "pluckEffect": (0, 255), "flingEffect": (0, 255),
         "flingPower": (0, 255), "naturalGiftPower": (0, 255), "naturalGiftType": (0, 31)}
for k in PARTY:
    if k.endswith("_stages"):
        WIDTH[k] = (0, 3 if k == "critrate_stages" else 15)
    elif k in ("hp_restore_param", "pp_restore_param"):
        WIDTH[k] = (0, 255)
    elif k.endswith("_param"):
        WIDTH[k] = (-128, 127)
NO_NATURAL_GIFT = 31   # naturalGiftType of items that aren't berries

KEYS = (["name", "description", "noData"] + TOP + ["partyUseParam", "partyUseIndex", "icon", "palette", "gen3"])
# Without party use, ItemData's party block is a union read as one byte (`dummy`, returned by
# GetItemAttr for any party attribute); the converter stored the item's position in its category
# there (balls 0-23, mail 0-11, rods 0-2). It overlaps the first 8 flags of ItemPartyParam.
INDEX_FLAGS = PARTY[:8]


class ItemError(Exception):
    pass


# --- constants ------------------------------------------------------------------------------------

def read_defines(path, prefix):
    out = {}
    with open(path, encoding="utf-8") as f:
        for name, value in re.findall(r"^#define[ \t]+(%s\w*)[ \t]+(.+?)[ \t]*(?://.*)?$" % prefix, f.read(), re.M):
            out[name] = value
    return out


class Constants:
    def __init__(self, include):
        items_h = os.path.join(include, "constants", "items.h")
        with open(items_h, encoding="utf-8") as f:
            text = f.read()
        # item ids: the #defines from ITEM_NONE up to ITEMS_COUNT
        block = text[text.index("#define ITEM_NONE "):text.index("#define ITEMS_COUNT")]
        self.items = {n: int(v) for n, v in re.findall(r"^#define\s+(ITEM_\w+)\s+(\d+)", block, re.M)}
        defs = read_defines(items_h, "")
        self.count = int(defs["ITEMS_COUNT"])
        self.by_id = {}
        for name, v in sorted(self.items.items(), key=lambda kv: kv[1]):
            if v < self.count:
                self.by_id.setdefault(v, name)
        self.field_use = self._enum(defs, "ITEM_FIELD_USE_")
        self.battle_use = self._enum(defs, "ITEM_BATTLE_USE_")
        self.pockets = self._enum(defs, "POCKET_", exclude=("POCKETS_COUNT", "POCKET_BAG_VIEW_END"))
        self.btl_pockets = {}
        for name, v in defs.items():
            m = re.fullmatch(r"\(1 << (\d)\)", v)
            if name.startswith("BTLPOCKET_") and m:
                self.btl_pockets[name] = 1 << int(m.group(1))
        self.hold_effects = self._enum(read_defines(os.path.join(include, "constants", "items.h"), ""),
                                       "HOLD_EFFECT_")
        types = read_defines(os.path.join(include, "constants", "pokemon.h"), "TYPE_")
        # the 18 types (TYPE_MUL_*, TYPE_NONE and the table markers share the prefix)
        self.types = {n: int(v) for n, v in types.items() if re.fullmatch(r"\d+", v) and int(v) < 32
                      and not n.startswith("TYPE_MUL_")}
        self.capacity = {name: int(defs[name]) for name in defs if name.startswith("NUM_BAG_")}

    @staticmethod
    def _enum(defs, prefix, exclude=()):
        return {n: int(v) for n, v in defs.items()
                if n.startswith(prefix) and n not in exclude and re.fullmatch(r"\d+", v)}


def _named(value, table, what, where):
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value in table:
        return table[value]
    raise ItemError("%s: %s %r is not a known constant" % (where, what, value))


def _name_of(value, table):
    for n, v in table.items():
        if v == value:
            return n
    return value


# --- reading and checking items.json ------------------------------------------------------------------

def load(path):
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ItemError("%s:%d: %s" % (path, e.lineno, e.msg))


def resolve(doc, c, where="items.json"):
    """items.json -> [(constant, item dict with numbers)] in id order, after checking it."""
    if not isinstance(doc, dict):
        raise ItemError("%s: expected an object keyed by item constant" % where)
    names = list(doc)
    expect = [c.by_id.get(i) for i in range(c.count)]
    if names != expect:
        for i, (got, want) in enumerate(zip(names + [None] * c.count, expect)):
            if got != want:
                raise ItemError("%s: item %d should be %s (include/constants/items.h), found %s; items must be "
                                "listed once each, in id order" % (where, i, want, got))
        raise ItemError("%s: %d items, ITEMS_COUNT is %d" % (where, len(names), c.count))
    out = []
    for name in names:
        e = doc[name]
        at = "%s: %s" % (where, name)
        if not isinstance(e, dict):
            raise ItemError("%s: expected an object" % at)
        extra = set(e) - set(KEYS)
        if extra:
            raise ItemError("%s: unknown key %r" % (at, sorted(extra)[0]))
        r = {"name": e.get("name"), "description": e.get("description"), "noData": bool(e.get("noData"))}
        for k in ("icon", "palette", "gen3"):
            if not isinstance(e.get(k), str):
                raise ItemError("%s: %s is required (an item_icon file name / AGB_ITEM_ constant)" % (at, k))
            r[k] = e[k]
        if not isinstance(r["name"], str):
            raise ItemError("%s: name is required" % at)
        if r["noData"]:
            if set(e) & (set(TOP) | {"partyUseParam"}):
                raise ItemError("%s: noData items use ITEM_NONE's record and can't set item data" % at)
        else:
            for k in TOP:
                v = e.get(k, _default(k))
                if k in BOOLS:
                    if not isinstance(v, bool):
                        raise ItemError("%s: %s must be true or false" % (at, k))
                    v = int(v)
                elif k == "holdEffect":
                    v = _named(v, c.hold_effects, k, at)
                elif k == "naturalGiftType":
                    v = _named(v, c.types, k, at)
                elif k == "fieldPocket":
                    v = _named(v, c.pockets, k, at)
                elif k == "battlePocket":
                    if not isinstance(v, list):
                        raise ItemError("%s: battlePocket must be a list of BTLPOCKET_*_F" % at)
                    v = sum(_named(x, c.btl_pockets, k, at) for x in v)
                elif k == "fieldUseFunc":
                    v = _named(v, c.field_use, k, at)
                elif k == "battleUseFunc":
                    v = _named(v, c.battle_use, k, at)
                elif k == "partyUse":
                    if not isinstance(v, bool):
                        raise ItemError("%s: partyUse must be true or false" % at)
                    v = int(v)
                if k in WIDTH and not (isinstance(v, int) and WIDTH[k][0] <= v <= WIDTH[k][1]):
                    raise ItemError("%s: %s must be %d-%d" % (at, k, *WIDTH[k]))
                r[k] = v
            p = e.get("partyUseParam", {})
            if not isinstance(p, dict):
                raise ItemError("%s: partyUseParam must be an object" % at)
            if p and not r["partyUse"]:
                raise ItemError("%s: partyUseParam needs \"partyUse\": true" % at)
            if "partyUseIndex" in e:
                n = e["partyUseIndex"]
                if r["partyUse"]:
                    raise ItemError("%s: partyUseIndex is only for items without party use" % at)
                if not (isinstance(n, int) and not isinstance(n, bool) and 0 <= n <= 255):
                    raise ItemError("%s: partyUseIndex must be 0-255" % at)
                p = {k: True for i, k in enumerate(INDEX_FLAGS) if n >> i & 1}
            bad = set(p) - set(PARTY)
            if bad:
                raise ItemError("%s: partyUseParam: unknown key %r (see ItemPartyParam, include/item.h)"
                                % (at, sorted(bad)[0]))
            for k in PARTY:
                v = p.get(k, False if k in BOOLS else 0)
                if k in BOOLS:
                    if not isinstance(v, bool):
                        raise ItemError("%s: partyUseParam.%s must be true or false" % (at, k))
                    v = int(v)
                elif not (isinstance(v, int) and WIDTH[k][0] <= v <= WIDTH[k][1]):
                    raise ItemError("%s: partyUseParam.%s must be %d-%d" % (at, k, *WIDTH[k]))
                r[k] = v
        out.append((name, r))
    return out


def _default(k):
    if k in BOOLS or k == "partyUse":
        return False
    return {"holdEffect": "HOLD_EFFECT_NONE", "naturalGiftType": NO_NATURAL_GIFT, "battlePocket": [],
            "fieldUseFunc": 0, "battleUseFunc": 0, "fieldPocket": "POCKET_ITEMS"}.get(k, 0)


def check(items, c):
    """Warnings that don't stop the build."""
    out = []
    for name, r in items:
        if len(r["name"]) > 12:
            out.append("%s: name %r is longer than 12 characters, the longest in the retail game (\"Ylw "
                       "Apricorn\" was shortened to fit); menus may cut it off" % (name, r["name"]))
    return out


# --- building -----------------------------------------------------------------------------------------

def data_records(items):
    """[(constant, item)] for each ItemData record (record 0 is ITEM_NONE), and {constant: record}."""
    records, index = [], {}
    for name, r in items:
        if name == "ITEM_NONE" or not r["noData"]:
            index[name] = len(records)
            records.append((name, r))
        else:
            index[name] = 0
    return records, index


def csv_text(records, c):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["item"] + TOP + PARTY)
    for name, r in records:
        row = [name]
        for k in TOP + PARTY:
            v = r[k]
            row.append(("true" if v else "false") if k in BOOLS else str(v))
        w.writerow(row)
    return out.getvalue()


def _message(bank, i, text):
    m = {"id": "%s_%05d" % (bank, i)}
    if text is None:
        m["garbage"] = 0
    elif "\n" in text:
        parts = text.split("\n")
        m[LANG] = [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])
    else:
        m[LANG] = text
    return m


def bank(bank_name, key, texts):
    return {"key": key, "messages": [_message(bank_name, i, t) for i, t in enumerate(texts)]}


def narc_ids_header(items, index):
    lines = ["// Generated from data/items/items.json by tools/pokedata/items.py. Don't edit: edit items.json.",
             "static const u16 sItemNarcIds[ITEMS_COUNT][4] = {"]
    for name, r in items:
        lines.append("    [%s] = { NARC_item_data_%04d_bin, NARC_item_icon_%s_NCGR, NARC_item_icon_%s_NCLR, %s },"
                     % (name, index[name], r["icon"], r["palette"], r["gen3"]))
    lines.append("};")
    return "\n".join(lines) + "\n"


def build(items_json, out_dir, include):
    c = Constants(include)
    items = resolve(load(items_json), c, items_json)
    records, index = data_records(items)
    os.makedirs(out_dir, exist_ok=True)
    outputs = {
        "item_data.csv": csv_text(records, c),
        NAMES_BANK + ".json": json.dumps(bank(NAMES_BANK, NAMES_KEY, [r["name"] for _, r in items]),
                                         ensure_ascii=False, indent=2) + "\n",
        DESCS_BANK + ".json": json.dumps(bank(DESCS_BANK, DESCS_KEY, [r["description"] for _, r in items]),
                                         ensure_ascii=False, indent=2) + "\n",
        "item_narc_ids.h": narc_ids_header(items, index),
    }
    for fn, text in outputs.items():
        p = os.path.join(out_dir, fn)
        old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if old != text:     # keep timestamps of unchanged outputs: less to rebuild
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
    for w in check(items, c):
        print("items.json: warning: %s" % w, file=sys.stderr)


# --- one-time extraction ---------------------------------------------------------------------------------

def _messages(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    out = []
    for m in d["messages"]:
        if LANG not in m:
            out.append(None)
        else:
            v = m[LANG]
            out.append("".join(v) if isinstance(v, list) else v)
    return d, out


def extract(root, out_path):
    include = os.path.join(root, "include")
    c = Constants(include)
    src = open(os.path.join(root, "src/item.c"), encoding="utf-8").read()
    if "sItemNarcIds[ITEMS_COUNT][4] = {" not in src:
        raise ItemError("extract reads the files items.json replaced (item_data.csv, msg_0221/0222.json, the "
                        "table in src/item.c); this tree already uses data/items/items.json")
    t = src[src.index("sItemNarcIds[ITEMS_COUNT][4] = {"):]
    t = t[:t.index("};")]
    table = re.findall(r"\[(\w+)\]\s*=\s*\{\s*NARC_item_data_(\d+)_bin,\s*NARC_item_icon_(\w+?)_NCGR,\s*"
                       r"NARC_item_icon_(\w+?)_NCLR,\s*(\w+)\s*\}", t)
    if [n for n, *_ in table] != [c.by_id[i] for i in range(c.count)]:
        raise ItemError("sItemNarcIds isn't one entry per item in id order")
    rows = list(csv.DictReader(open(os.path.join(root, "files/itemtool/itemdata/item_data.csv"), encoding="utf-8")))
    _, names = _messages(os.path.join(root, "files/msgdata/msg", NAMES_BANK + ".json"))
    _, descs = _messages(os.path.join(root, "files/msgdata/msg", DESCS_BANK + ".json"))
    rev = {"holdEffect": {v: k for k, v in c.hold_effects.items()},
           "fieldUseFunc": {v: k for k, v in c.field_use.items()},
           "battleUseFunc": {v: k for k, v in c.battle_use.items()},
           "fieldPocket": {v: k for k, v in c.pockets.items()},
           "naturalGiftType": {v: k for k, v in c.types.items()}}
    doc = {}
    for i, (name, data, icon, pal, gen3) in enumerate(table):
        e = {"name": names[i], "description": descs[i]}
        data = int(data)
        if data == 0 and name != "ITEM_NONE":
            e["noData"] = True
        else:
            row = rows[data]
            for k in TOP:
                v = row[k]
                if k in BOOLS or k == "partyUse":
                    e[k] = v == "true" if k in BOOLS else v != "0"
                    continue
                n = int(v) if re.fullmatch(r"-?\d+", v) else _named(v, {**c.hold_effects, **c.pockets, **c.types},
                                                                     k, name)
                if k == "battlePocket":
                    e[k] = [f for f, bit in sorted(c.btl_pockets.items(), key=lambda kv: kv[1]) if n & bit]
                elif k in rev:
                    e[k] = rev[k].get(n, n)
                else:
                    e[k] = n
            if e["naturalGiftType"] == NO_NATURAL_GIFT and e["naturalGiftPower"] == 0:
                del e["naturalGiftType"], e["naturalGiftPower"]
            p = {}
            for k in PARTY:
                v = row[k]
                if k in BOOLS:
                    if v == "true":
                        p[k] = True
                elif int(v) != 0:
                    p[k] = int(v)
            if p and not e["partyUse"]:
                if set(p) - set(INDEX_FLAGS):
                    raise ItemError("%s: party data beyond the index byte without party use" % name)
                e["partyUseIndex"] = sum(1 << i for i, k in enumerate(INDEX_FLAGS) if p.get(k))
            elif p:
                e["partyUseParam"] = p
        e["icon"], e["palette"], e["gen3"] = icon, pal, gen3
        doc[name] = e
    write_json(out_path, doc)
    return doc


def write_json(path, doc):
    """One item per block, short values on one line, like battle_moves.json."""
    lines = ["{"]
    names = list(doc)
    for i, name in enumerate(names):
        e = doc[name]
        lines.append("    %s: {" % json.dumps(name))
        keys = [k for k in KEYS if k in e]
        for j, k in enumerate(keys):
            lines.append("        %s: %s%s" % (json.dumps(k), json.dumps(e[k], ensure_ascii=False),
                                               "," if j + 1 < len(keys) else ""))
        lines.append("    }" + ("," if i + 1 < len(names) else ""))
    lines.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("items_json"); p.add_argument("out_dir"); p.add_argument("--include", required=True)
    p = sub.add_parser("check")
    p.add_argument("items_json"); p.add_argument("--include", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--root", required=True); p.add_argument("--out", default="data/items/items.json")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "build":
            build(a.items_json, a.out_dir, a.include)
        elif a.cmd == "check":
            c = Constants(a.include)
            items = resolve(load(a.items_json), c, a.items_json)
            ws = check(items, c)
            for w in ws:
                print("warning: %s" % w)
            print("%d items, %d data records; %d warning(s)" % (len(items), len(data_records(items)[0]), len(ws)))
        else:
            extract(a.root, a.out)
    except ItemError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
