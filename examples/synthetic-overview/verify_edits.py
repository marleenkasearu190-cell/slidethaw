"""Check this fixture's temporary edits and unchanged pixels outside the target regions."""
import argparse
import json
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/rebuild-ppt-image-compare/scripts"))
from pptx_inspect import inspect


def outside_difference(before, after, regions):
    with Image.open(before) as image:
        original = image.convert("RGB")
    with Image.open(after) as image:
        edited = image.convert("RGB")
    if original.size != edited.size:
        raise ValueError("Render dimensions changed")
    mask = Image.new("L", original.size, 255)
    draw = ImageDraw.Draw(mask)
    for region in regions:
        draw.rectangle(region, fill=0)
    diff = ImageChops.difference(original, edited)
    diff.paste((0, 0, 0), mask=ImageChops.invert(mask))
    return diff.getbbox()


def verify(project, application):
    project = Path(project)
    slug = application.lower()
    spec = json.loads((project / "spec/deck_spec.json").read_text())
    slide = spec["editable_slide"] - 1
    original = project / spec["output"]
    edited = project / f"qa/{slug}-edit-r1/temporary-edit-test.pptx"
    before = {item["name"]: item for item in inspect(original)["slides"][slide]["objects"]}
    after = {item["name"]: item for item in inspect(edited)["slides"][slide]["objects"]}
    errors = []
    if after["page.title"]["text"] != "Slide image editing check":
        errors.append("Edited title did not persist")
    for name, item in before.items():
        if name == "page.title":
            continue
        changed = name == "content.module" or item["parent"] == "content.module"
        target = list(item["bbox_emu"])
        if changed:
            target[0] += 8 * 9525
        if max(abs(a - b) for a, b in zip(target, after[name]["bbox_emu"])) > 300:
            errors.append("Object movement differs: " + name)
        if item["text"] != after[name]["text"]:
            errors.append("Non-target text changed: " + name)
    pixel_bbox = outside_difference(project / f"qa/{slug}-render-r1/slide-1.png",
                                    project / f"qa/{slug}-edit-r1/slide-1.png",
                                    [(60, 40, 1220, 140), (60, 260, 804, 540)])
    if pixel_bbox is not None:
        errors.append("Pixels changed outside the title/module test regions")
    return {"status": "PASS" if not errors else "FAIL", "application": application,
            "checks": ["saved title text", "group and child movement", "non-target object text/geometry", "non-target render pixels"],
            "outside_change_bbox": pixel_bbox, "errors": errors,
            "limits": "Fixture-specific checks supplement actual visual review; no fidelity score."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--application", choices=("WPS", "PowerPoint"), required=True)
    args = parser.parse_args()
    result = verify(args.project, args.application)
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] != "PASS")
