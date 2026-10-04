"""Read-only OOXML inspection. Does not claim to render glyphs or solve occlusion."""
import hashlib
import io
import math
import posixpath
import zipfile
from xml.etree import ElementTree as ET

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
IDENTITY = (1, 0, 0, 1, 0, 0)


def matrix(a, b):
    return (a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1], a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3], a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5])


def transformed_box(m, x, y, w, h):
    points = [(m[0]*a+m[2]*b+m[4], m[1]*a+m[3]*b+m[5]) for a, b in ((x,y),(x+w,y),(x,y+h),(x+w,y+h))]
    xs, ys = zip(*points)
    return [min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)]


def text_of(root):
    paras = root.findall(".//a:p", NS)
    lines = []
    for para in paras:
        parts = []
        for child in para:
            if child.tag == f"{{{NS['a']}}}br":
                parts.append("\n")
            else:
                parts.extend(n.text or "" for n in child.findall(".//a:t", NS))
        lines.append("".join(parts))
    return "\n".join(lines)


def relationships(z, part):
    relpath = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
    if relpath not in z.namelist():
        return {}
    result = {}
    for r in ET.fromstring(z.read(relpath)):
        if r.get("TargetMode") == "External":
            continue
        target = r.get("Target", "")
        name = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))
        if name.startswith("../"):
            raise ValueError("Relationship escapes package")
        result[r.get("Id")] = name
    return result


def image_digest(data):
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert("RGBA")
            return hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest()
    except Exception:
        return hashlib.sha256(data).hexdigest()


def inspect(path):
    slides = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(set(names)) != len(names):
            raise ValueError("Duplicate ZIP entries")
        p = ET.fromstring(z.read("ppt/presentation.xml"))
        size = p.find("p:sldSz", NS)
        width, height = int(size.get("cx")), int(size.get("cy"))
        rels = relationships(z, "ppt/presentation.xml")
        order = [rels[n.get(f"{{{NS['r']}}}id")] for n in p.findall("p:sldIdLst/p:sldId", NS)]
        for part in order:
            root = ET.fromstring(z.read(part))
            slide_rels = relationships(z, part)
            records = []

            def walk(tree, parent_matrix=IDENTITY, parent_name=None, hidden_parent=False):
                for element in tree:
                    tag = element.tag.rsplit("}", 1)[-1]
                    if tag not in ("sp", "pic", "grpSp", "graphicFrame", "cxnSp"):
                        continue
                    nv = next((n for n in element if n.tag.rsplit("}",1)[-1].startswith("nv")), None)
                    props = nv.find("p:cNvPr", NS) if nv is not None else None
                    name = props.get("name", "") if props is not None else ""
                    sid = props.get("id") if props is not None else None
                    hidden = hidden_parent or (props is not None and props.get("hidden") in ("1", "true"))
                    xf = element.find("p:grpSpPr/a:xfrm", NS) if tag == "grpSp" else element.find("p:spPr/a:xfrm", NS)
                    if xf is None:
                        xf = element.find("p:xfrm", NS)
                    bounds = None
                    child_matrix = parent_matrix
                    if xf is not None:
                        off, ext = xf.find("a:off", NS), xf.find("a:ext", NS)
                        if off is not None and ext is not None:
                            x,y,w,h = [float(v) for v in (off.get("x",0),off.get("y",0),ext.get("cx",0),ext.get("cy",0))]
                            angle = float(xf.get("rot",0))/60000*math.pi/180
                            cs, sn = math.cos(angle), math.sin(angle)
                            fx = -1 if xf.get("flipH") in ("1","true") else 1
                            fy = -1 if xf.get("flipV") in ("1","true") else 1
                            rotation = (cs*fx,sn*fx,-sn*fy,cs*fy,0,0)
                            centered = matrix((1,0,0,1,x+w/2,y+h/2), matrix(rotation, (1,0,0,1,-w/2,-h/2)))
                            world = matrix(parent_matrix, centered)
                            bounds = transformed_box(world,0,0,w,h)
                            if tag == "grpSp":
                                co, ce = xf.find("a:chOff",NS), xf.find("a:chExt",NS)
                                if co is None or ce is None or float(ce.get("cx",0)) == 0 or float(ce.get("cy",0)) == 0:
                                    raise ValueError(f"Invalid group transform: {name}")
                                sx,sy = w/float(ce.get("cx")),h/float(ce.get("cy"))
                                child_matrix = matrix(world,(sx,0,0,sy,-float(co.get("x",0))*sx,-float(co.get("y",0))*sy))
                    table = element.find(".//a:tbl",NS)
                    chart = element.find(".//c:chart",NS)
                    kind = "group" if tag == "grpSp" else "picture" if tag == "pic" else "connector" if tag == "cxnSp" else "table" if table is not None else "chart" if chart is not None else "text" if element.find("p:txBody",NS) is not None else "shape"
                    record = {"name":name,"shape_id":sid,"kind":kind,"parent":parent_name,"bbox_emu":bounds,"hidden":hidden,"text":text_of(element) if tag != "grpSp" else "","xml":element}
                    if table is not None:
                        record["cells"] = [[text_of(c) for c in row.findall("a:tc",NS)] for row in table.findall("a:tr",NS)]
                    if kind == "picture":
                        blip = element.find(".//a:blip",NS)
                        media_part = slide_rels.get(blip.get(f"{{{NS['r']}}}embed")) if blip is not None else None
                        record["media_part"] = media_part
                        record["image_digest"] = image_digest(z.read(media_part)) if media_part else None
                        record["media_sha256"] = hashlib.sha256(z.read(media_part)).hexdigest() if media_part else None
                        crop = element.find(".//a:srcRect",NS)
                        record["cropped"] = crop is not None and any(float(v) != 0 for v in crop.attrib.values())
                    if kind == "connector":
                        for key, query in (("from_id",".//a:stCxn"),("to_id",".//a:endCxn")):
                            endpoint = element.find(query,NS)
                            record[key] = endpoint.get("id") if endpoint is not None else None
                        record["head"] = element.find(".//a:headEnd",NS)
                        record["tail"] = element.find(".//a:tailEnd",NS)
                    run_props = element.findall(".//a:rPr",NS)
                    record["fully_transparent_text"] = bool(run_props) and all(any(a.get("val") == "0" for a in r.findall(".//a:alpha",NS)) for r in run_props)
                    records.append(record)
                    if tag == "grpSp":
                        walk(element, child_matrix, name, hidden)
            walk(root.find("p:cSld/p:spTree",NS))
            slides.append({"part":part,"objects":records})
        return {"size_emu":[width,height],"slides":slides,"empty_media":[n for n in names if n.startswith("ppt/media/") and not n.endswith("/") and not z.read(n)]}
