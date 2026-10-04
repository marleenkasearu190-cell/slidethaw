"""Audit distribution paths and document internals without printing sensitive values."""
import argparse
import json
import os
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".release-private", ".git", ".agents", "node_modules", "__pycache__", ".venv", ".pytest_cache", "dist", "build"}
FORBIDDEN = {".pem", ".key", ".pfx", ".p12", ".ttf", ".otf", ".woff", ".woff2", ".pyc"}
TEXT_SUFFIXES = {".md", ".py", ".mjs", ".ps1", ".html", ".json", ".yaml", ".yml", ".txt"}
PRIVATE_PATH = re.compile(r"(?:[A-Z]:[\\/](?:Users|pycharm)[\\/]|/(?:Users|home)/[^/\s]+/)", re.I)
SECRET = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")


def files(root=ROOT):
    root = Path(root)
    for parent, directories, names in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if name not in EXCLUDED]
        for name in sorted(names):
            yield Path(parent) / name


def audit(root=ROOT):
    root = Path(root)
    findings = []
    count = 0

    def finding(path, kind):
        findings.append({"file": path.relative_to(root).as_posix(), "type": kind})

    def inspect_text(path, text):
        if PRIVATE_PATH.search(text):
            finding(path, "personal_absolute_path")
        if SECRET.search(text):
            finding(path, "potential_credential")

    for path in files(root):
        count += 1
        if path.is_symlink():
            finding(path, "unexpected_file_symlink")
        if path.suffix.lower() in FORBIDDEN or path.name.startswith(".env"):
            finding(path, "forbidden_distribution_file")
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"AGENTS.md", ".gitignore", "LICENSE"}:
            inspect_text(path, path.read_text(encoding="utf-8-sig"))
        if path.suffix.lower() in {".pptx", ".docx"}:
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                if len(set(names)) != len(names):
                    finding(path, "duplicate_archive_entries")
                for name in names:
                    if any(part in name.lower() for part in ("vbaproject", "/embeddings/", "/comments/", "fontdata")):
                        finding(path, "embedded_object_font_macro_or_comment")
                    if name.endswith((".xml", ".rels")):
                        text = archive.read(name).decode("utf-8")
                        inspect_text(path, text)
                        tree = ET.fromstring(text)
                        if name.endswith(".rels") and any(node.get("TargetMode") == "External" for node in tree):
                            finding(path, "external_document_relationship")
                        if name in {"docProps/core.xml", "docProps/app.xml"}:
                            for node in tree.iter():
                                local = node.tag.rsplit("}", 1)[-1]
                                if local in {"creator", "lastModifiedBy", "Company", "Manager"} and (node.text or "").strip():
                                    finding(path, "document_personal_metadata")
                        if "/notesSlides/notesSlide" in name:
                            # Ignore slide-number placeholder fields, inspect written speaker notes.
                            for shape in tree.iter():
                                if shape.tag.endswith("}sp"):
                                    ph = next((node for node in shape.iter() if node.tag.endswith("}ph")), None)
                                    if ph is not None and ph.get("type") in {"sldNum", "hdr", "ftr", "dt", "sldImg"}:
                                        continue
                                    if any((node.text or "").strip() for node in shape.iter() if node.tag.endswith("}t")):
                                        finding(path, "speaker_notes_require_review")
    return {"status": "PASS" if not findings else "FAIL", "files_checked": count,
            "findings": findings, "limits": "Use a trusted secret scanner and source/rights review as separate checks."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    report = audit(args.root)
    print(json.dumps(report, indent=2))
    raise SystemExit(report["status"] != "PASS")
