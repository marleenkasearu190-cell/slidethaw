"""Install the complete Skill into a new, explicitly chosen discovery directory."""
import argparse
import shutil
from pathlib import Path

NAME = "rebuild-ppt-image-compare"
ROOT = Path(__file__).resolve().parents[1]


def install(destination_root):
    source = ROOT / "skills" / NAME
    destination = Path(destination_root).expanduser().resolve() / NAME
    if destination.exists() or destination.is_symlink():
        raise ValueError("Skill already exists; choose a new directory. Nothing was overwritten.")
    if destination == source or source in destination.parents:
        raise ValueError("Installation must be outside the packaged Skill.")
    if not (source / "SKILL.md").is_file():
        raise ValueError("Complete packaged Skill is missing.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, help="Parent skill directory, e.g. .agents/skills")
    args = parser.parse_args()
    try:
        print(install(args.destination))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Installation refused: {exc}\n")


if __name__ == "__main__":
    main()
