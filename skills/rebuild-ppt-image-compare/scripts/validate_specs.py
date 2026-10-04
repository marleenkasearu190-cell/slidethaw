"""Check actual contracts including IDs, paths, source hashes, permissions and styles."""
import argparse
import json
from contracts import load_project, validate, effective_state, baseline_scene


def run(project):
    values = load_project(project)
    errors = validate(*values)
    result = {"status": "FAIL" if errors else "PASS", "errors": errors}
    if not errors:
        removed, items = effective_state(values[2], values[3], values[4], baseline_scene(values[0], values[3]))
        result.update(removed_nodes=sorted(removed), removed_content_ids=[i["id"] for i in items if not i["bindings"]], active_content_ids=[i["id"] for i in items if i["bindings"]])
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project")
    a = p.parse_args()
    try:
        result = run(a.project)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        result = {"status": "FAIL", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(result["status"] != "PASS")
