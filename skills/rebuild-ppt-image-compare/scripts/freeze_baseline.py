"""Freeze confirmed baseline content once; re-running verifies rather than overwrites."""
import argparse
import shutil
from contracts import load_project, validate, read_json, write_json, sha256


def freeze(project):
    root,spec,manifest,scene,plan=load_project(project)
    errors=validate(root,spec,manifest,scene,plan)
    if errors:
        raise ValueError(errors)
    folder=root/"qa/baseline"
    manifest_path=root/"spec/content_manifest.json"
    lock=folder/"lock.json"
    if lock.exists():
        record=read_json(lock)
        if sha256(manifest_path)!=record["manifest_sha256"] or sha256(folder/"content_manifest.json")!=record["manifest_sha256"] or sha256(folder/"scene_graph.json")!=record["scene_sha256"] or spec["source"]["sha256"]!=record["source_sha256"]:
            raise ValueError("Frozen content/baseline changed; express approved corrections in edit_plan, not baseline")
        return record
    if folder.exists():
        raise ValueError("Partial baseline directory exists; inspect it, do not overwrite")
    folder.mkdir(parents=True)
    shutil.copy2(manifest_path,folder/"content_manifest.json")
    shutil.copy2(root/"spec/scene_graph.json",folder/"scene_graph.json")
    record={"manifest_sha256":sha256(manifest_path),"scene_sha256":sha256(folder/"scene_graph.json"),"source_sha256":spec["source"]["sha256"]}
    write_json(lock,record)
    return record


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("project");a=p.parse_args();print(freeze(a.project))
