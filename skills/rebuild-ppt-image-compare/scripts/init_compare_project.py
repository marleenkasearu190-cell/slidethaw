"""Create a NEW isolated project; never overwrite a previous reconstruction."""
import argparse
import shutil
from pathlib import Path
from PIL import Image, ImageOps
from contracts import VERSION, safe_name, sha256, write_json


def initialize(source, parent, name, output_mode="editable_only"):
    if output_mode not in ("editable_only", "comparison"):
        raise ValueError("Unknown output_mode")
    slide_count = 1 if output_mode == "editable_only" else 2
    source = Path(source).resolve(strict=True)
    name = safe_name(name)
    parent = Path(parent).resolve()
    project = parent / name
    if project.exists():
        raise ValueError(f"Project already exists; use a new revision name: {project}")
    with Image.open(source) as im:
        size = ImageOps.exif_transpose(im).size
    project.mkdir(parents=True, exist_ok=False)
    for sub in ("source", "assets", "spec", "src", "tmp", "qa", "output"):
        (project / sub).mkdir()
    original = project / "source" / ("original" + source.suffix.lower())
    shutil.copy2(source, original)
    reference = project / "source/reference.png"
    with Image.open(source) as im:
        ImageOps.exif_transpose(im).convert("RGBA").save(reference)
    w = 1920
    h = round(w * size[1] / size[0], 6)
    spec = {"schema_version": VERSION, "ready": False, "project": name,
            "mode": "faithful_rebuild", "output_mode": output_mode, "slides": slide_count, "editable_slide": slide_count,
            "source": {"path": "source/reference.png", "sha256": sha256(reference), "size_px": list(size), "original_path": str(source), "original_copy": original.relative_to(project).as_posix(), "original_sha256": sha256(original)},
            "design_px": [w, h], "reference_bbox": [0, 0, w, h],
            "output": f"output/{name}_{'editable' if slide_count == 1 else 'compare'}.pptx",
            "template": {"family_id": name, "reference_match_verified": False, "reuse_from": None},
            "runtime": {"profile": "codex_artifact_tool", "builder_version": None, "target_application": "WPS", "smoke_fingerprint": None},
            "style_tokens": {}, "geometry_tolerance_px": 2}
    write_json(project / "spec/deck_spec.json", spec)
    write_json(project / "spec/content_manifest.json", {"schema_version": VERSION, "items": []})
    write_json(project / "spec/scene_graph.json", {"schema_version": VERSION, "slide": slide_count, "nodes": [], "assets": []})
    write_json(project / "spec/edit_plan.json", {"schema_version": VERSION, "authorized": False, "user_request": "", "remove_components": [], "replacements": [], "protected_nodes": []})
    write_json(project / "qa/review.json", {"schema_version": VERSION, "pptx_sha256": None, "checks": {key: {"status": "NOT_RUN", "evidence": [], "notes": ""} for key in ("content_visual", "science_assets", "layout_visual", "reference_visual", "editability", "non_target_preservation")}})
    return project


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True)
    p.add_argument("--project-root", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--output-mode", choices=("editable_only", "comparison"), default="editable_only")
    a = p.parse_args()
    print(initialize(a.source, a.project_root, a.name, a.output_mode))
