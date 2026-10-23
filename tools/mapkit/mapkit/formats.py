# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Checks a project against the gen4map format (docs/gen4map/FORMAT.md).

    mapkit format check

The JSON files are checked against docs/gen4map/schemas/*.schema.json with a
small JSON Schema validator (the subset those schemas use: type, enum, const,
pattern, minimum/maximum, minItems/maxItems/maxLength, properties, required,
additionalProperties, items, anyOf, $ref to #/$defs), then the cross-file
rules the schemas can't express.
"""

import json
import os
import re

from . import bdhc, landdata, layouts

FORMAT = "gen4map"
SUPPORTED_MAJOR = 1
MANIFEST = "data/gen4map.json"
SCHEMA_DIR = "docs/gen4map/schemas"


class Problem:
    def __init__(self, path, message):
        self.path, self.message = path, message

    def __str__(self):
        return "%s: %s" % (self.path, self.message)


# --- JSON Schema subset --------------------------------------------------------------

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def validate(value, schema, root=None, where="$"):
    """-> list of (json path, message)."""
    root = root or schema
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError("only local $ref is supported: %s" % ref)
        target = root
        for part in ref[2:].split("/"):
            target = target[part]
        extra = {k: v for k, v in schema.items() if k not in ("$ref", "description")}
        return validate(value, target, root, where) + (validate(value, extra, root, where) if extra else [])
    errors = []
    if "anyOf" in schema:
        results = [validate(value, s, root, where) for s in schema["anyOf"]]
        if all(results):
            # if the value has the right type for one alternative, its errors say more
            typed = [r for r in results if not r[0][1].startswith("expected ")]
            if len(typed) == 1:
                return typed[0]
            errors.append((where, "%s is not any of the allowed kinds" % json.dumps(value)[:60]))
        return errors
    t = schema.get("type")
    if t is not None:
        kinds = t if isinstance(t, list) else [t]
        if not any(_TYPES[k](value) for k in kinds):
            return [(where, "expected %s, got %s" % (" or ".join(kinds), json.dumps(value)[:60]))]
    if "const" in schema and value != schema["const"]:
        errors.append((where, "must be %s" % json.dumps(schema["const"])))
    if "enum" in schema and value not in schema["enum"]:
        errors.append((where, "must be one of %s" % ", ".join(json.dumps(e) for e in schema["enum"])))
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append((where, "%r does not match %s" % (value, schema["pattern"])))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append((where, "longer than %d" % schema["maxLength"]))
    if _TYPES["number"](value):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append((where, "%s is below %s" % (value, schema["minimum"])))
        if "maximum" in schema and value > schema["maximum"]:
            errors.append((where, "%s is above %s" % (value, schema["maximum"])))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append((where, "fewer than %d items" % schema["minItems"]))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append((where, "more than %d items" % schema["maxItems"]))
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], root, "%s[%d]" % (where, i))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for k in schema.get("required", []):
            if k not in value:
                errors.append((where, "missing %r" % k))
        for k, v in value.items():
            if k in props:
                errors += validate(v, props[k], root, "%s.%s" % (where, k))
            elif schema.get("additionalProperties") is False:
                errors.append((where, "unknown key %r" % k))
            elif isinstance(schema.get("additionalProperties"), dict):
                errors += validate(v, schema["additionalProperties"], root, "%s.%s" % (where, k))
    return errors


def load_schema(root, name):
    with open(os.path.join(root, SCHEMA_DIR, name + ".schema.json"), encoding="utf-8") as f:
        return json.load(f)


# --- project check -------------------------------------------------------------------

def _json(path, problems, root):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        problems.append(Problem(os.path.relpath(path, root), str(e)))
        return None


def check(root):
    """-> (counts, [Problem])."""
    problems = []
    rel = lambda p: os.path.relpath(p, root)  # noqa: E731
    counts = {}

    manifest = _json(os.path.join(root, MANIFEST), problems, root)
    if manifest is None:
        return counts, problems
    for where, msg in validate(manifest, load_schema(root, "manifest")):
        problems.append(Problem(MANIFEST, "%s: %s" % (where, msg)))
    version = str(manifest.get("version", "0"))
    if manifest.get("format") != FORMAT or not version.startswith("%d." % SUPPORTED_MAJOR):
        problems.append(Problem(MANIFEST, "this tool reads %s %d.x, not %s %s"
                                % (FORMAT, SUPPORTED_MAJOR, manifest.get("format"), version)))
        return counts, problems
    paths = manifest["paths"]

    # layouts
    lay_schema = load_schema(root, "layout")
    lay_index = layouts.read_index(root)
    lay_names = set()
    for e in lay_index:
        p = os.path.join(root, paths["layouts"], e["dir"], "layout.json")
        d = _json(p, problems, root)
        lay_names.add(e["dir"])
        if d is None:
            continue
        for where, msg in validate(d, lay_schema):
            problems.append(Problem(rel(p), "%s: %s" % (where, msg)))
        try:
            layouts.from_json(d, root, rel(p))
        except layouts.LayoutError as ex:
            problems.append(Problem(rel(p), str(ex)))
    on_disk = {n for n in os.listdir(os.path.join(root, paths["layouts"]))
               if os.path.isdir(os.path.join(root, paths["layouts"], n))}
    for n in sorted(on_disk - lay_names):
        problems.append(Problem(paths["layouts"], "folder %s is not in %s" % (n, paths["layout_index"])))
    counts["layouts"] = len(lay_index)

    # land data
    props_schema = load_schema(root, "props")
    try:
        chunks = landdata.chunk_dirs(root)
    except landdata.LandDataError as ex:
        problems.append(Problem(paths["landdata"], str(ex)))
        chunks = []
    heights_schema = load_schema(root, "heights")
    needed = {"permissions.txt", "props.json", "model.nsbmd"}
    for d in chunks:
        files = set(os.listdir(d))
        missing = needed - files
        if missing:
            problems.append(Problem(rel(d), "missing %s" % ", ".join(sorted(missing))))
            continue
        heights = {"terrain.bdhc", "heights.json"} & files
        if len(heights) != 1:
            problems.append(Problem(rel(d), "needs exactly one of terrain.bdhc and heights.json (has %s)"
                                    % (", ".join(sorted(heights)) or "neither")))
        elif "heights.json" in heights:
            hp = os.path.join(d, "heights.json")
            doc = _json(hp, problems, root)
            if doc is not None:
                errs = validate(doc, heights_schema)
                for where, msg in errs:
                    problems.append(Problem(rel(hp), "%s: %s" % (where, msg)))
                if not errs:
                    try:
                        bdhc.from_json(doc, rel(hp))
                    except bdhc.BdhcError as ex:
                        problems.append(Problem(rel(hp), str(ex)))
        props = _json(os.path.join(d, "props.json"), problems, root)
        if props is not None:
            for where, msg in validate(props, props_schema):
                problems.append(Problem(rel(os.path.join(d, "props.json")), "%s: %s" % (where, msg)))
        try:
            with open(os.path.join(d, "permissions.txt"), encoding="utf-8") as f:
                landdata.Permissions.from_text(f.read(), rel(os.path.join(d, "permissions.txt")))
        except landdata.LandDataError as ex:
            problems.append(Problem(rel(d), str(ex)))
    counts["land data cells"] = len(chunks)

    # maps
    from . import layout as maps_layout
    map_schema = load_schema(root, "map")
    entries = maps_layout.read_index(root)
    for e in entries:
        p = os.path.join(root, paths["maps"], e["dir"], "map.json")
        d = _json(p, problems, root)
        if d is None:
            continue
        for where, msg in validate(d, map_schema):
            problems.append(Problem(rel(p), "%s: %s" % (where, msg)))
        if d.get("id") != e["map"]:
            problems.append(Problem(rel(p), "id %s but %s lists %s" % (d.get("id"), paths["map_index"], e["map"])))
        if d.get("name") != e["dir"]:
            problems.append(Problem(rel(p), "name %r is not its folder %r" % (d.get("name"), e["dir"])))
        if d.get("layout") not in lay_names:
            problems.append(Problem(rel(p), "layout %r is not in %s" % (d.get("layout"), paths["layout_index"])))
    counts["maps"] = len(entries)
    return counts, problems
