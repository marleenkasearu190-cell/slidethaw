"""Validate local Markdown file/image links, including paths in code-free prose."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    errors = []
    for document in root.rglob("*.md"):
        if any(part in {".release-private", ".git", "node_modules", ".agents"} for part in document.relative_to(root).parts):
            continue
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
