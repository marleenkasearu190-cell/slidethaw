"""Bound-content audit. Structural PASS is NOT visual/release PASS; use --release."""
import argparse
import json
import unicodedata
from pathlib import Path
from contracts import load_project, validate, effective_state, absolute_box, inside, sha256, read_json, baseline_scene, slide_layout
from pptx_inspect import inspect, image_digest, NS
from freeze_baseline import freeze


def check(pptx, project, release=False, render_receipt=None, review=None):
    root, spec, manifest, scene, plan = load_project(project)
    errors = validate(root,spec,manifest,scene,plan)
    if errors:
        return {"status":"FAIL","errors":errors}
    slide_count, editable_slide = slide_layout(spec)
    if not (root/"qa/baseline/lock.json").is_file():
        return {"status":"FAIL","errors":["Baseline not frozen; run freeze_baseline.py before authoring"]}
    freeze(project)  # verifies existing immutable baseline; never creates one in QA
    deck = inspect(pptx)
    fingerprint = sha256(pptx)
    findings = []
    def need(condition, label):
        if not condition:
            errors.append(label)
    need(len(deck["slides"]) == slide_count, f"Expected exactly {slide_count} ordered slides")
    need(not deck["empty_media"], "Empty embedded media")
    if len(deck["slides"]) != slide_count:
        return {"status":"FAIL","errors":errors}
    sx,sy = [deck["size_emu"][i]/spec["design_px"][i] for i in (0,1)]
    need(abs(sx/sy-1) < .001, "Slide aspect differs from design canvas")
    def pixels(record):
        b=record["bbox_emu"]
        return None if b is None else [b[0]/sx,b[1]/sy,b[2]/sx,b[3]/sy]
    def near(a,b):
        return a is not None and max(abs(x-y) for x,y in zip(a,b)) <= spec.get("geometry_tolerance_px",2)
    source_digest=image_digest(inside(root,spec["source"]["path"]).read_bytes())
    if slide_count == 2:
        ref=deck["slides"][0]["objects"]
        need(len(ref)==1 and ref[0]["kind"]=="picture", "Slide 1 must contain only the complete reference picture")
        if len(ref)==1 and ref[0]["kind"]=="picture":
            need(ref[0]["image_digest"]==source_digest, "Slide 1 image differs from reference")
            need(not ref[0]["cropped"] and not ref[0]["hidden"], "Slide 1 reference cropped or hidden")
            need(near(pixels(ref[0]),spec["reference_bbox"]), "Slide 1 reference placement/aspect mismatch")
    records=deck["slides"][editable_slide-1]["objects"]
    by_name={}
    for obj in records:
        by_name.setdefault(obj["name"],[]).append(obj)
    nodes={n["id"]:n for n in scene["nodes"]}
    removed,items=effective_state(manifest,scene,plan,baseline_scene(root,scene))
    expected_names={n["name"] for n in scene["nodes"] if n["id"] not in removed}
    need(set(by_name)==expected_names, f"Unexpected/missing editable-slide objects: extra={sorted(set(by_name)-expected_names)}, missing={sorted(expected_names-set(by_name))}")
    for nid,node in nodes.items():
        matches=by_name.get(node["name"],[])
        if nid in removed:
            need(not matches,f"Removed object remains on editable slide: {nid}")
            continue
        need(len(matches)==1,f"Object binding must be unique: {nid}")
        if len(matches)!=1:
            continue
        obj=matches[0]
        compatible=obj["kind"]==node["kind"] or (node["kind"]=="shape" and obj["kind"]=="text" and not obj["text"]) or (node["kind"]=="formula" and obj["kind"]=="text")
        need(compatible,f"Wrong native object type: {nid}: {obj['kind']} != {node['kind']}")
        need(not obj["hidden"] and not obj["fully_transparent_text"],f"Hidden/transparent required object: {nid}")
        need(near(pixels(obj),absolute_box(nid,nodes)),f"Geometry mismatch: {nid}")
        if node.get("native_group"):
            need(obj["kind"]=="group",f"Not a native movable group: {nid}")
        parent=node.get("parent")
        if parent and nodes[parent].get("native_group"):
            need(obj["parent"]==nodes[parent]["name"],f"Child not in required native group: {nid}")
        if node["kind"]=="picture":
            asset=next(a for a in scene["assets"] if a["id"]==node["asset_id"])
            need(obj["image_digest"]==image_digest(inside(root,asset["path"]).read_bytes()),f"Embedded asset differs: {nid}")
            need(not obj["cropped"],f"Unexpected in-PPT crop (pre-crop asset instead): {nid}")
            need(obj["image_digest"]!=source_digest,f"Whole reference image used on editable slide: {nid}")
        if node["kind"]=="connector":
            start=by_name.get(nodes[node["from"]]["name"],[])
            end=by_name.get(nodes[node["to"]]["name"],[])
            if node.get("binding_required",True) and len(start)==len(end)==1:
                need(obj.get("from_id")==start[0]["shape_id"] and obj.get("to_id")==end[0]["shape_id"],f"Unbound/wrong connector: {nid}")
            head=obj.get("head") is not None and obj["head"].get("type","none")!="none"
            tail=obj.get("tail") is not None and obj["tail"].get("type","none")!="none"
            expected={"forward":(False,True),"backward":(True,False),"both":(True,True),"none":(False,False)}[node["arrow"]]
            need((head,tail)==expected,f"Arrow direction mismatch: {nid}")
    checked=0
    for item in items:
        for binding in item["bindings"]:
            nid=binding["node_id"]
            matches=by_name.get(nodes[nid]["name"],[])
            if len(matches)!=1:
                continue
            obj=matches[0]
            if not item.get("must_be_native"):
                need(bool(item.get("exception_reason")),f"Non-native content needs declared exception: {item['id']}")
                continue
            text=obj["text"]
            if "cell" in binding:
                try:
                    r,c=binding["cell"]
                    text=obj["cells"][r][c]
                except (KeyError,IndexError,TypeError):
                    errors.append(f"Missing native table cell: {item['id']}")
                    continue
            if nodes[nid]["kind"]=="formula":
                findings.append(f"Formula structure requires visual/native math review: {item['id']}")
            need(unicodedata.normalize("NFC",text)==unicodedata.normalize("NFC",item["text"]),f"Exact content mismatch at {item['id']} / {nid}: {text!r}")
            checked+=1
    for obj in records:
        b=pixels(obj)
        need(b is not None,f"Unmeasured object geometry: {obj['name']}")
        if b:
            need(b[0]>=-.1 and b[1]>=-.1 and b[0]+b[2]<=spec["design_px"][0]+.1 and b[1]+b[3]<=spec["design_px"][1]+.1,f"Out of slide: {obj['name']}")
    if release:
        need(render_receipt is not None and review is not None,"Release requires actual render receipt AND visual/edit review")
        if render_receipt:
            receipt=read_json(render_receipt)
            need(receipt.get("status")=="PASS" and receipt.get("pptx_sha256")==fingerprint,"Missing/stale/failed render receipt")
            need(receipt.get("operation")=="render" and not receipt.get("edits") and receipt.get("rendered_pptx_sha256")==fingerprint,"Edited test copy cannot serve as final-file render evidence")
            need(receipt.get("application")==spec["runtime"]["target_application"],"Receipt is from a different target application")
            need(receipt.get("slide_count")==slide_count,"Render receipt slide count mismatch")
            outputs=receipt.get("outputs",[])
            need(len(outputs)==slide_count and {o.get("slide") for o in outputs}==set(range(1,slide_count+1)),"All declared final slides must be rendered exactly once")
            for out in outputs:
                file=Path(out["path"])
                need(file.is_file() and sha256(file)==out["sha256"],"Render evidence missing/changed")
        if review:
            report=read_json(review)
            need(report.get("pptx_sha256")==fingerprint,"Visual/edit review is stale")
            for key in ("content_visual","science_assets","layout_visual","reference_visual","editability","non_target_preservation"):
                entry=report.get("checks",{}).get(key,{})
                status=entry.get("status")
                allowed_na=key in ("science_assets","non_target_preservation")
                need(status=="PASS" or (allowed_na and status=="NOT_APPLICABLE" and bool(entry.get("notes"))),f"Required review not completed: {key}")
                if status=="PASS":
                    need(bool(entry.get("evidence")) and bool(entry.get("notes")),f"Review has no evidence/explanation: {key}")
                    for evidence in entry.get("evidence",[]):
                        file=inside(root,evidence["path"])
                        need(file.is_file() and sha256(file)==evidence["sha256"],f"Review evidence missing/stale: {key}")
        expected=inside(root,spec["output"])
        need(Path(pptx).resolve()==expected,"Release candidate is not the declared final path")
        if spec.get("runtime",{}).get("profile")=="codex_artifact_tool":
            finalizer=root/"qa/finalizer.json"
            need(finalizer.is_file(),"Current Codex profile requires finalizer receipt")
            if finalizer.is_file():
                need(read_json(finalizer).get("finalSha256")==fingerprint,"Finalizer receipt is stale")
        extras=[p.name for p in expected.parent.iterdir() if p!=expected and not p.name.startswith("~$")]
        need(not extras,f"Extra deliverables in output: {extras}")
    return {"status":"FAIL" if errors else "PASS","scope":"release_evidence_gate" if release else "structural_only","pptx_sha256":fingerprint,"bound_native_carriers_checked":checked,"removed_nodes":sorted(removed),"errors":errors,"warnings":findings,"limits":"OOXML cannot establish legibility, glyph clipping, full occlusion, formula meaning or editable-chart data correctness. Actual rendered review and temporary edit tests remain required."}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("pptx")
    p.add_argument("--project",required=True)
    p.add_argument("--release",action="store_true")
    p.add_argument("--render-receipt")
    p.add_argument("--review")
    a=p.parse_args()
    try:
        result=check(a.pptx,a.project,a.release,a.render_receipt,a.review)
    except Exception as exc:
        result={"status":"FAIL","errors":[f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(result["status"]!="PASS")
