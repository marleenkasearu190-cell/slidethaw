"""Manually specified synthetic fixture; not an automatic image-recognition pipeline."""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/rebuild-ppt-image-compare"
sys.path.insert(0, str(SKILL / "scripts"))
from contracts import load_project
from crop_asset import crop
from init_compare_project import initialize


def prepare(parent, name, output_mode):
    source = Path(__file__).resolve().parent / "source.png"
    project = initialize(source, parent, name, output_mode)
    _, spec, manifest, scene, plan = load_project(project)
    spec.update(ready=True, design_px=[1280, 720], reference_bbox=[0, 0, 1280, 720],
                background="#FFFFFF", style_tokens={"font_zh": "Arial", "font_latin": "Arial"},
                font_policy={"basis": "design", "families": ["Arial"]})
    spec["source"].pop("original_path", None)
    spec["template"]["reference_match_verified"] = True
    spec["template"]["family_id"] = "slidethaw-synthetic-overview"
    spec["runtime"]["builder_version"] = "Skill metadata 2.2; host runtime recorded separately"
    nodes = []
    items = []

    def text(identifier, value, bbox, size, bold=False, parent=None, color="#20242A"):
        nodes.append({"id": identifier, "name": identifier, "kind": "text", "parent": parent,
                      "bbox": bbox, "z": len(nodes) + 1, "qa_region": True,
                      "text_style": {"fontSize": size, "bold": bold, "color": color,
                                     "typeface": "Arial", "autoFit": "none", "verticalAlignment": "top",
                                     "insets": {"top": 0, "right": 0, "bottom": 0, "left": 0}}})
        items.append({"id": identifier, "text": value, "confirmed": True, "must_be_native": True,
                      "source": {"path": "source/reference.png", "region_px": bbox},
                      "bindings": [{"node_id": identifier}]})

    text("page.title", "Slide image reconstruction", [72, 52, 1136, 80], 56, True)
    text("page.subtitle", "Synthetic fixture for content and editing tests", [76, 148, 1128, 46], 26)
    nodes.append({"id": "page.rule", "name": "page.rule", "kind": "shape", "parent": None,
                  "bbox": [72, 216, 1136, 4], "z": 3, "fill": "#137A67"})
    nodes.append({"id": "content.module", "name": "content.module", "kind": "group", "parent": None,
                  "bbox": [72, 272, 710, 252], "z": 4, "native_group": True, "qa_region": True})
    nodes.append({"id": "content.frame", "name": "content.frame", "kind": "shape", "parent": "content.module",
                  "bbox": [73, 273, 708, 250], "z": 5, "fill": "none", "line": {"fill": "#C5CBD0", "width": 2}})
    text("content.heading", "Editable structure", [98, 298, 656, 52], 34, True, "content.module")
    text("content.line1", "Native text boxes", [98, 362, 656, 43], 27, parent="content.module")
    text("content.line2", "Grouped frame and labels", [98, 405, 656, 43], 27, parent="content.module")
    text("content.line3", "Exact content bindings", [98, 448, 656, 43], 27, parent="content.module")
    text("image.caption", "Preserved image crop", [882, 496, 316, 42], 22)
    text("page.footer", "SYNTHETIC DEMO / No research data or institutional assets", [76, 628, 1128, 44], 22, color="#555B62")
    scene["nodes"] = nodes
    manifest["items"] = items
    for filename, data in (("deck_spec", spec), ("content_manifest", manifest), ("scene_graph", scene), ("edit_plan", plan)):
        (project / "spec" / f"{filename}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    asset = crop(project, "synthetic-pattern", [882, 288, 288, 192])
    scene["assets"].append(asset)
    scene["nodes"].append({"id": "image.pattern", "name": "image.pattern", "kind": "picture", "parent": None,
                           "bbox": [882, 288, 288, 192], "z": 20, "asset_id": asset["id"], "qa_region": True})
    manifest["items"].append({"id": "image.pattern", "text": None, "confirmed": True, "must_be_native": False,
                              "exception_reason": "Self-authored synthetic raster pattern preserved as a local crop",
                              "source": {"path": "source/reference.png", "region_px": [882, 288, 288, 192]},
                              "bindings": [{"node_id": "image.pattern"}]})
    for filename, data in (("scene_graph", scene), ("content_manifest", manifest)):
        (project / "spec" / f"{filename}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    for template in ("build_compare.mjs", "finalize_compare.mjs"):
        shutil.copy2(SKILL / "templates" / template, project / "src" / template)
    edit = {"test_only": True, "operations": [
        {"op": "text", "shape_name": "page.title", "value": "Slide image editing check"},
        {"op": "move", "shape_name": "content.module", "require_group": True, "dx_design_px": 8, "dy_design_px": 0},
    ]}
    (project / "qa/edit-test-plan.json").write_text(json.dumps(edit, indent=2), encoding="utf-8")
    return project


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output-mode", choices=("editable_only", "comparison"), default="editable_only")
    args = parser.parse_args()
    print(prepare(args.project_root, args.name, args.output_mode))
