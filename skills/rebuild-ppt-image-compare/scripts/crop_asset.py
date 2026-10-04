"""Exact original-pixel crop, without AI regeneration, resizing or source overwrite."""
import argparse
from PIL import Image
from contracts import load_project, inside, sha256, write_json, safe_name


def crop(project,name,region):
    root,spec,_,_,_=load_project(project)
    safe_name(name)
    source=inside(root,spec["source"]["path"])
    if sha256(source)!=spec["source"]["sha256"]:
        raise ValueError("Source hash changed")
    out=inside(root,f"assets/{name}.png")
    if out.exists():
        raise ValueError("Asset exists; use a new name")
    x,y,w,h=region
    with Image.open(source) as image:
        if x<0 or y<0 or w<=0 or h<=0 or x+w>image.width or y+h>image.height:
            raise ValueError("Crop outside original source pixels")
        image.crop((x,y,x+w,y+h)).save(out)
    record={"id":name,"path":f"assets/{name}.png","sha256":sha256(out),"source_sha256":sha256(source),"crop_src_px":region,"contains_text":"REVIEW_REQUIRED"}
    write_json(inside(root,f"assets/{name}.provenance.json"),record)
    return record


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",required=True)
    p.add_argument("--name",required=True)
    p.add_argument("--box",type=int,nargs=4,required=True,metavar=("X","Y","W","H"))
    a=p.parse_args()
    print(crop(a.project,a.name,a.box))
