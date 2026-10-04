"""Create diagnostic overlays/crops from real renders; never a similarity PASS score."""
import argparse
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from contracts import load_project, inside, absolute_box, write_json, sha256


def compare(project, rendered, destination, baseline=None):
    root,spec,_,scene,_=load_project(project)
    dest=inside(root,destination)
    if dest.exists():
        raise ValueError("Use a new comparison directory for each revision")
    dest.mkdir(parents=True)
    size=tuple(round(v) for v in spec["design_px"])
    if baseline:
        with Image.open(baseline) as image:
            if image.size!=size:
                raise ValueError("Baseline render dimensions must equal design dimensions")
            ref=image.convert("RGB")
    else:
        ref=Image.new("RGB",size,spec.get("reference_background","white"))
        x,y,w,h=map(round,spec["reference_bbox"])
        with Image.open(inside(root,spec["source"]["path"])) as image:
            ref.paste(image.convert("RGB").resize((w,h),Image.Resampling.LANCZOS),(x,y))
    with Image.open(rendered) as image:
        if image.size!=size:
            raise ValueError("Render at design_px dimensions; do not stretch a mismatched render for QA")
        actual=image.convert("RGB")
    ref.save(dest/"reference.png")
    actual.save(dest/"render.png")
    Image.blend(ref,actual,.5).save(dest/"overlay50.png")
    difference=ImageChops.difference(ref,actual)
    difference.save(dest/"difference.png")
    side=Image.new("RGB",(size[0]*2,size[1]),"white")
    side.paste(ref,(0,0)); side.paste(actual,(size[0],0)); side.save(dest/"side_by_side.png")
    nodes={n["id"]:n for n in scene["nodes"]}
    regions=[]
    for index,node in enumerate(scene["nodes"]):
        if not node.get("qa_region"):
            continue
        x,y,w,h=absolute_box(node["id"],nodes)
        box=(max(0,int(x)),max(0,int(y)),min(size[0],round(x+w)),min(size[1],round(y+h)))
        prefix=f"region-{index:03d}"
        ref.crop(box).save(dest/f"{prefix}-reference.png")
        actual.crop(box).save(dest/f"{prefix}-render.png")
        crop=difference.crop(box)
        crop.save(dest/f"{prefix}-diff.png")
        regions.append({"node_id":node["id"],"bbox":list(box),"mean_absolute_channel_difference":sum(ImageStat.Stat(crop).mean)/3,"files_prefix":prefix,"status":"NOT_RUN"})
    result={"kind":"diagnostic_only","reference_mode":"prior_render" if baseline else "source_image","render_sha256":sha256(rendered),"regions":regions,"warning":"No automatic fidelity percentage or visual PASS. Inspect images and record evidence in review.json. Prior-render mode is for non-target regression checks, not fidelity to source."}
    write_json(dest/"metrics.json",result)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",required=True)
    p.add_argument("--render",required=True)
    p.add_argument("--out",required=True,help="New project-relative internal directory, e.g. qa/diff-r1")
    p.add_argument("--baseline",help="Optional prior render for non-target regression")
    a=p.parse_args()
    print(compare(a.project,a.render,a.out,a.baseline))
