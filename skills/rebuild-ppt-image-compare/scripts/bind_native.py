"""Deterministic picture naming/native grouping on a NEW exported copy; no rasterization."""
import argparse
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from contracts import load_project, validate, effective_state, absolute_box, inside, baseline_scene, slide_layout
from pptx_inspect import NS, relationships, inspect, image_digest


def bind(source,destination,project):
    root,spec,manifest,scene,plan=load_project(project)
    errors=validate(root,spec,manifest,scene,plan)
    if errors:
        raise ValueError(errors)
    slide_count, editable_slide = slide_layout(spec)
    destination=Path(destination)
    if destination.exists() or destination.resolve()==Path(source).resolve():
        raise ValueError("Use a new destination; never overwrite exporter source")
    scanned=inspect(source)
    with zipfile.ZipFile(source) as archive:
        presentation=ET.fromstring(archive.read("ppt/presentation.xml"))
        rels=relationships(archive,"ppt/presentation.xml")
        order=[rels[n.get(f"{{{NS['r']}}}id")] for n in presentation.findall("p:sldIdLst/p:sldId",NS)]
        if len(order)!=slide_count:
            raise ValueError(f"Expected {slide_count} slides")
        part=order[editable_slide-1]
        document=ET.fromstring(archive.read(part))
        tree=document.find("p:cSld/p:spTree",NS)
        for picture in tree.findall(".//p:pic",NS):
            nv=picture.find("p:nvPicPr/p:cNvPr",NS)
            desc=nv.get("descr","")
            if desc.startswith("ppt-rebuild:"):
                nv.set("name",desc[len("ppt-rebuild:"):])
        size=presentation.find("p:sldSz",NS)
        sx,sy=int(size.get("cx"))/spec["design_px"][0],int(size.get("cy"))/spec["design_px"][1]
        nodes={n["id"]:n for n in scene["nodes"]}
        removed,_=effective_state(manifest,scene,plan,baseline_scene(root,scene))
        # Some artifact-tool versions drop image alt/name. Bind only a UNIQUE
        # embedded-pixel digest AND geometry match; never assign by visual guess/order.
        used=set()
        for node in nodes.values():
            if node["id"] in removed or node["kind"]!="picture":
                continue
            asset=next(a for a in scene["assets"] if a["id"]==node["asset_id"])
            digest=image_digest(inside(root,asset["path"]).read_bytes())
            expected=absolute_box(node["id"],nodes)
            matches=[]
            for record in scanned["slides"][editable_slide-1]["objects"]:
                b=record["bbox_emu"]
                if record["kind"]=="picture" and record.get("image_digest")==digest and b:
                    actual=[b[0]/sx,b[1]/sy,b[2]/sx,b[3]/sy]
                    if max(abs(v-w) for v,w in zip(actual,expected))<=spec.get("geometry_tolerance_px",2):
                        matches.append(record)
            if len(matches)!=1 or matches[0]["shape_id"] in used:
                raise ValueError(f"Ambiguous/missing picture binding: {node['id']}")
            sid=matches[0]["shape_id"];used.add(sid)
            nv=next(n for n in document.findall(".//p:pic/p:nvPicPr/p:cNvPr",NS) if n.get("id")==sid)
            nv.set("name",node["name"])
            nv.set("descr","ppt-rebuild:"+node["name"])
        next_id=max(int(n.get("id",0)) for n in document.findall(".//p:cNvPr",NS))+1
        def name_of(element):
            nv=next((c for c in element if c.tag.rsplit("}",1)[-1].startswith("nv")),None)
            p=nv.find("p:cNvPr",NS) if nv is not None else None
            return p.get("name") if p is not None else None
        def depth(n):
            return 0 if not n.get("parent") else 1+depth(nodes[n["parent"]])
        groups=sorted((n for n in nodes.values() if n["id"] not in removed and n.get("native_group")),key=depth,reverse=True)
        for node in groups:
            child_names={n["name"] for n in nodes.values() if n.get("parent")==node["id"] and n["id"] not in removed}
            children=[element for element in tree if name_of(element) in child_names]
            if len(children)!=len(child_names) or not children:
                raise ValueError(f"Group children missing/ambiguous: {node['id']}")
            indices=[list(tree).index(c) for c in children]
            if max(indices)-min(indices)+1!=len(indices):
                raise ValueError(f"Grouping would change z-order; make children contiguous: {node['id']}")
            group=ET.Element(f"{{{NS['p']}}}grpSp")
            nv=ET.SubElement(group,f"{{{NS['p']}}}nvGrpSpPr")
            ET.SubElement(nv,f"{{{NS['p']}}}cNvPr",id=str(next_id),name=node["name"]);next_id+=1
            ET.SubElement(nv,f"{{{NS['p']}}}cNvGrpSpPr")
            ET.SubElement(nv,f"{{{NS['p']}}}nvPr")
            props=ET.SubElement(group,f"{{{NS['p']}}}grpSpPr")
            xf=ET.SubElement(props,f"{{{NS['a']}}}xfrm")
            x,y,w,h=absolute_box(node["id"],nodes)
            off={"x":str(round(x*sx)),"y":str(round(y*sy))}
            ext={"cx":str(round(w*sx)),"cy":str(round(h*sy))}
            for tag,attrs in (("off",off),("ext",ext),("chOff",off),("chExt",ext)):
                ET.SubElement(xf,f"{{{NS['a']}}}{tag}",attrs)
            index=min(indices)
            for child in children:
                tree.remove(child);group.append(child)
            tree.insert(index,group)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(destination,"x",zipfile.ZIP_DEFLATED) as out:
            for entry in archive.infolist():
                data=ET.tostring(document,encoding="utf-8",xml_declaration=True) if entry.filename==part else archive.read(entry.filename)
                out.writestr(entry,data)
    return destination


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True);p.add_argument("--out",required=True);p.add_argument("--project",required=True)
    a=p.parse_args();print(bind(a.input,a.out,a.project))
