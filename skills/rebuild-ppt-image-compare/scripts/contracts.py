"""Versioned project contract; standard library only. Coordinates are design pixels."""
import hashlib
import json
import math
import re
from pathlib import Path

VERSION = "2.2"
SUPPORTED_VERSIONS = {"2.1", VERSION}
KINDS = {"text", "shape", "picture", "group", "table", "chart", "formula", "connector"}


def slide_layout(spec):
    """Resolve one editable slide or an explicitly requested reference/editable pair."""
    mode = spec.get("output_mode")
    if mode is None and spec.get("schema_version") == "2.1":
        mode = "comparison"
    if mode not in ("editable_only", "comparison"):
        raise ValueError("output_mode must be editable_only or comparison")
    count = 1 if mode == "editable_only" else 2
    if type(spec.get("slides")) is not int or type(spec.get("editable_slide")) is not int or spec["slides"] != count or spec["editable_slide"] != count:
        raise ValueError(f"{mode} requires slides={count} and editable_slide={count}")
    return count, count


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inside(root, relative):
    root = Path(root).resolve()
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents:
        raise ValueError(f"Path must be inside project: {relative}")
    return candidate


def safe_name(value):
    if not re.fullmatch(r"[\w-]{1,80}", value, flags=re.UNICODE):
        raise ValueError("Name must contain 1-80 letters, numbers, underscores or hyphens")
    if value.upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}:
        raise ValueError("Reserved Windows filename")
    return value


def load_project(root):
    root = Path(root).resolve()
    spec = read_json(root / "spec/deck_spec.json")
    return root, spec, read_json(root / "spec/content_manifest.json"), read_json(root / "spec/scene_graph.json"), read_json(root / "spec/edit_plan.json")


def box(value, line=False):
    return isinstance(value, list) and len(value) == 4 and all(type(v) in (int, float) and math.isfinite(v) for v in value) and ((value[2] >= 0 and value[3] >= 0 and max(value[2:]) > 0) if line else (value[2] > 0 and value[3] > 0))


def baseline_scene(root, fallback):
    snapshot = Path(root) / "qa/baseline/scene_graph.json"
    return read_json(snapshot) if snapshot.is_file() else fallback


def effective_state(manifest, scene, plan, baseline=None):
    """Preserve baseline files; derive removals including descendants, never mutate truth."""
    nodes = {n["id"]: n for n in (baseline or scene)["nodes"]}
    removed = set(plan.get("remove_components", []))
    while True:
        more = {n["id"] for n in nodes.values() if n.get("parent") in removed}
        if more <= removed:
            break
        removed |= more
    replacements = {r["content_id"]: r["text"] for r in plan.get("replacements", [])}
    items = []
    for item in manifest["items"]:
        bindings = [b for b in item["bindings"] if b["node_id"] not in removed]
        items.append({**item, "text": replacements.get(item["id"], item.get("text")), "bindings": bindings})
    return removed, items


def absolute_box(node_id, nodes, seen=None):
    seen = set() if seen is None else seen
    if node_id in seen:
        raise ValueError("Parent cycle")
    seen.add(node_id)
    node = nodes[node_id]
    if "bbox_local" not in node:
        return node["bbox"]
    x, y, w, h = node["bbox_local"]
    parent = absolute_box(node["parent"], nodes, seen)
    return [x + parent[0], y + parent[1], w, h]


def validate(root, spec, manifest, scene, plan):
    """Executable schema and cross-file checks. Returns all actionable errors."""
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)
    require(spec.get("schema_version") in SUPPORTED_VERSIONS, "Unsupported schema_version")
    for name, obj in (("deck_spec", spec), ("manifest", manifest), ("scene", scene), ("edit_plan", plan)):
        require(obj.get("schema_version") == spec.get("schema_version"), f"{name}: schema_version must match deck_spec")
    require(spec.get("ready") is True, "Project is not ready: inspect source and fill contracts first")
    require(spec.get("mode") in ("faithful_rebuild", "safe_polish", "authorized_reflow"), "Invalid mode")
    try:
        _, editable_slide = slide_layout(spec)
        require(type(scene.get("slide")) is int and scene["slide"] == editable_slide, "scene.slide must match editable_slide")
    except ValueError as exc:
        errors.append(str(exc))
    require(bool(manifest.get("items")), "Content manifest cannot be empty")
    dims = spec.get("design_px", [])
    require(len(dims) == 2 and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in dims), "Invalid design_px")
    for label in ("source",):
        entry = spec.get(label, {})
        try:
            file = inside(root, entry["path"])
            require(file.is_file() and sha256(file) == entry.get("sha256"), f"{label}: source missing or hash changed")
        except (KeyError, ValueError, OSError):
            errors.append(f"{label}: invalid project path")
    source = spec.get("source", {})
    if source.get("original_copy"):
        try:
            require(sha256(inside(root, source["original_copy"])) == source.get("original_sha256"), "Original source copy changed")
        except (OSError, ValueError):
            errors.append("Original source copy missing")
    try:
        output = inside(root, spec["output"])
        require(output.parent == Path(root) / "output" and output.suffix.lower() == ".pptx", "Final output must be output/<name>.pptx")
    except (KeyError, ValueError):
        errors.append("Invalid final output path")
    pixels = source.get("size_px", [])
    rect = spec.get("reference_bbox", [])
    require(box(rect), "reference_bbox must be [x,y,w,h]")
    if box(rect) and len(dims) == 2:
        require(rect[0] >= 0 and rect[1] >= 0 and rect[0] + rect[2] <= dims[0] + .1 and rect[1] + rect[3] <= dims[1] + .1, "Reference placement extends beyond canvas")
    if box(rect) and len(pixels) == 2 and pixels[1] > 0:
        require(abs(rect[2] / rect[3] - pixels[0] / pixels[1]) < 0.005, "Reference would be stretched")
    template = spec.get("template", {})
    require(bool(template.get("family_id")), "template.family_id required")
    require(template.get("reference_match_verified") is True, "Template must match the CURRENT reference")
    if template.get("reuse_from"):
        require(template.get("reuse_family_id") == template.get("family_id"), "Template family mismatch: do not reuse a previous style/logo")
        require(bool(template.get("reuse_evidence")), "Template reuse needs current-reference comparison evidence")
    node_list = scene.get("nodes", [])
    require(bool(node_list), "Scene cannot be empty")
    nodes = {n.get("id"): n for n in node_list}
    require(len(nodes) == len(node_list) and None not in nodes, "Duplicate or missing node IDs")
    baseline = baseline_scene(root, scene)
    base_nodes = {n.get("id"): n for n in baseline.get("nodes", [])}
    require(set(nodes) == set(base_nodes), "Keep baseline node IDs; remove by edit_plan, not by deleting scene entries")
    for nid in set(nodes) & set(base_nodes):
        require(nodes[nid].get("name") == base_nodes[nid].get("name") and nodes[nid].get("kind") == base_nodes[nid].get("kind"), f"Baseline identity/type changed: {nid}")
        require(nodes[nid].get("parent") == base_nodes[nid].get("parent"), f"Baseline membership changed: {nid}; reflow may change coordinates, not silently reassign content ownership")
    names = [n.get("name") for n in node_list]
    require(len(set(names)) == len(names) and all(names), "Every editable node needs a unique actual PPT shape name")
    assets = {a.get("id"): a for a in scene.get("assets", [])}
    require(len(assets) == len(scene.get("assets", [])), "Duplicate asset IDs")
    for asset in assets.values():
        try:
            file = inside(root, asset["path"])
            require(file.is_file() and sha256(file) == asset.get("sha256"), f"Asset hash mismatch: {asset.get('id')}")
        except (KeyError, ValueError, OSError):
            errors.append(f"Invalid asset: {asset.get('id')}")
    for node in node_list:
        label = node.get("id")
        require(node.get("kind") in KINDS, f"{label}: invalid kind")
        require(node.get("parent") is None or node.get("parent") in nodes, f"{label}: unknown parent")
        require(box(node.get("bbox_local", node.get("bbox")), node.get("kind") == "connector" or node.get("geometry") == "line"), f"{label}: invalid bbox")
        if "bbox_local" in node:
            require(node.get("parent") in nodes, f"{label}: local bbox needs parent")
        try:
            bounds = absolute_box(label, nodes)
            if len(dims) == 2:
                require(bounds[0] >= 0 and bounds[1] >= 0 and bounds[0] + bounds[2] <= dims[0] + .1 and bounds[1] + bounds[3] <= dims[1] + .1, f"{label}: spec outside canvas")
        except (ValueError, KeyError, TypeError):
            errors.append(f"{label}: invalid parent chain")
        if node.get("kind") == "picture":
            require(node.get("asset_id") in assets, f"{label}: unknown asset")
        if node.get("kind") == "connector":
            require(node.get("from") in nodes and node.get("to") in nodes, f"{label}: unknown connector endpoint")
            require(node.get("arrow") in ("forward", "backward", "both", "none"), f"{label}: arrow required")
    ids = [i.get("id") for i in manifest.get("items", [])]
    require(len(set(ids)) == len(ids) and all(ids), "Duplicate/missing content IDs")
    claimed = set()
    for item in manifest.get("items", []):
        label = item.get("id")
        require(type(item.get("must_be_native")) is bool, f"{label}: must_be_native must be boolean")
        require(item.get("confirmed") is True or (not item.get("must_be_native") and bool(item.get("exception_reason"))), f"{label}: unconfirmed content without image exception")
        require(isinstance(item.get("text"), str) or (not item.get("must_be_native") and item.get("exception_reason")), f"{label}: missing text")
        require(bool(item.get("bindings")), f"{label}: no bindings")
        require(bool(item.get("source")), f"{label}: no source provenance")
        for binding in item.get("bindings", []):
            nid = binding.get("node_id")
            require(nid in nodes, f"{label}: unknown binding {nid}")
            cell = binding.get("cell")
            require(cell is None or (isinstance(cell, list) and len(cell) == 2 and all(type(v) is int and v >= 0 for v in cell)), f"{label}: cell must be zero-based [row,col]")
            key = (nid, tuple(cell or []))
            require(key not in claimed, f"{label}: duplicate binding carrier {key}; use one item per text box/cell")
            claimed.add(key)
            if item.get("must_be_native") and nid in nodes:
                require(nodes[nid].get("kind") in ("text", "table", "formula"), f"{label}: required native content bound to non-text object")
    removals = plan.get("remove_components", [])
    require(len(set(removals)) == len(removals) and all(r in nodes for r in removals), "Unknown/duplicate removed component")
    require(all(n in nodes for n in plan.get("protected_nodes", [])), "Unknown protected node")
    replacements = plan.get("replacements", [])
    replacement_ids = [r.get("content_id") for r in replacements]
    require(len(set(replacement_ids)) == len(replacement_ids) and all(r in ids for r in replacement_ids), "Unknown/duplicate content replacement")
    require(all(isinstance(r.get("text"), str) and r.get("reason") for r in replacements), "Replacements need exact text and reason")
    changed = bool(removals or replacements or spec.get("mode") != "faithful_rebuild")
    if changed:
        require(plan.get("authorized") is True and bool(plan.get("user_request")), "Changes need recorded user authorization")
    if removals:
        require(spec.get("mode") == "authorized_reflow", "Removal requires authorized_reflow")
    if not errors:
        removed, items = effective_state(manifest, scene, plan, baseline)
        require(not (removed & set(plan.get("protected_nodes", []))), "Cannot remove a protected object")
        for node in node_list:
            if node["id"] not in removed and node["kind"] == "connector":
                require(node["from"] not in removed and node["to"] not in removed, f"{node['id']}: retained connector points to removed node; include it in plan")
    return errors
