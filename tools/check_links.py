"""Validate inline local Markdown file/image links, not anchors or external sites."""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".release-private", ".git", "node_modules", ".agents", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
    "build", "dist", "scratch",
}


def markdown_files(root):
    # Prune before descent so dependency Markdown and inaccessible caches are never read.
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS)
        for name in sorted(files):
            if name.endswith(".md"):
                yield Path(directory) / name


def check(root=ROOT):
    root = Path(root)
    errors = []
    for document in markdown_files(root):
        text = re.sub(r"```.*?```", "", document.read_text(encoding="utf-8"), flags=re.S)
        for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = link.strip().split("#", 1)[0].strip("<>")
            if not target or re.match(r"[a-zA-Z]+:", target):
                continue
            if not (document.parent / target).is_file():
                errors.append(f"{document.relative_to(root)}: missing {target}")
    return errors


if __name__ == "__main__":
    errors = check()
    print("\n".join(errors) if errors else "All local Markdown links resolve.")
    raise SystemExit(bool(errors))
