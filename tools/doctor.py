"""Check installed capabilities without changing the environment or reading credentials."""
import argparse
import importlib.metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md", "agents/openai.yaml", "references/production-contract.md",
    "references/implementation-pattern.md", "references/contracts.md", "references/qa-and-evals.md",
    "scripts/contracts.py", "scripts/init_compare_project.py", "scripts/validate_specs.py",
    "scripts/freeze_baseline.py", "scripts/crop_asset.py", "scripts/bind_native.py",
    "scripts/pptx_inspect.py", "scripts/qa_compare_pptx.py", "scripts/office_render.ps1",
    "scripts/visual_diff.py", "templates/build_compare.mjs", "templates/finalize_compare.mjs",
]


def probe(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def diagnose(skill_dir=None):
    skill = Path(skill_dir) if skill_dir else ROOT / "skills/rebuild-ppt-image-compare"
    checks = []

    def add(name, available, note, required_for):
        checks.append({"name": name, "status": "PASS" if available else "NOT_AVAILABLE",
                       "note": note, "required_for": required_for})

    missing = [name for name in REQUIRED if not (skill / name).is_file()]
    add("complete_skill", not missing, "Missing: " + ", ".join(missing) if missing else "All required files found", "unit")
    add("python", sys.version_info >= (3, 10), "Python " + sys.version.split()[0], "unit")
    try:
        from PIL import Image
        Image.new("RGB", (1, 1)).tobytes()
        pillow = importlib.metadata.version("Pillow")
    except (ImportError, importlib.metadata.PackageNotFoundError):
        pillow = None
    add("pillow", bool(pillow), "Pillow " + pillow if pillow else "Install requirements.txt", "unit")
    node = os.environ.get("RUNTIME_NODE") or shutil.which("node")
    modules = os.environ.get("RUNTIME_NODE_MODULES")
    artifact = False
    if node:
        script = "const p=process.argv[1]; const u=await import('node:url'); const m=await import('node:module'); const r=p?m.createRequire(u.pathToFileURL(p+'/probe.cjs')):m.createRequire(process.cwd()+'/probe.cjs'); await import(u.pathToFileURL(r.resolve('@oai/artifact-tool')));"
        artifact = probe([node, "--input-type=module", "-e", script, modules or ""])
    add("artifact_tool", artifact, "ES-module import succeeds" if artifact else "Requires a compatible host-provided @oai/artifact-tool runtime", "build")
    host = os.environ.get("SKILL_DIR")
    finalizer = bool(host and (Path(host) / "container_tools/artifact_tool_utils.mjs").is_file())
    add("host_finalizer", finalizer, "Presentations finalizer found" if finalizer else "Resolve the host Presentations Skill; it is not bundled here", "build")
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    for application, prog_id in (("WPS", "KWPP.Application"), ("PowerPoint", "PowerPoint.Application")):
        available = False
        if os.name == "nt" and powershell:
            command = f"if($null -eq [Type]::GetTypeFromProgID('{prog_id}')) {{ exit 1 }}"
            available = probe([powershell, "-NoProfile", "-Command", command])
        add(application, available, "COM registered; real render/edit tests still required" if available else "Windows desktop application/COM interface unavailable", "office")
    return {"scope": "environment_capability_only", "checks": checks,
            "limits": "Discovery is not a conversion, render, visual review or editability acceptance test."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir")
    parser.add_argument("--require", choices=("unit", "build", "wps", "powerpoint"), default="unit")
    args = parser.parse_args()
    report = diagnose(args.skill_dir)
    print(json.dumps(report, indent=2))
    needed = {"complete_skill", "python", "pillow"}
    if args.require != "unit":
        needed |= {"artifact_tool", "host_finalizer"}
    if args.require in ("wps", "powerpoint"):
        needed.add("WPS" if args.require == "wps" else "PowerPoint")
    return int(any(c["status"] != "PASS" for c in report["checks"] if c["name"] in needed))


if __name__ == "__main__":
    raise SystemExit(main())
