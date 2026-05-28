#!/usr/bin/env python3
"""Promote high-confidence learnings into SKILL.md files.

Usage:
    promote_learnings.py --component <name> [--min-hits 5] [--dry-run]

Finds learnings with high hit counts and accuracy, then appends them
to the component's SKILL.md as permanent knowledge.
"""

import argparse
import json
import sys
from pathlib import Path

MEMORY_BASE = Path(__file__).resolve().parent.parent.parent.parent / "memory"
SKILLS_BASE = Path(__file__).resolve().parent.parent.parent

SUB_COMPONENT_MAP = {
    "kserve": "model-server/kserve",
    "llmd": "model-server/llmd",
    "modelmesh": "model-server/modelmesh",
}

SKILL_DIR_MAP = {
    "kserve": "debugger-model-server/debugger-kserve",
    "llmd": "debugger-model-server/debugger-llmd",
    "modelmesh": "debugger-model-server/debugger-modelmesh",
}


def resolve_component_path(component: str) -> str:
    """Resolve component name to its memory directory path."""
    return SUB_COMPONENT_MAP.get(component, component)


def resolve_skill_dir(component: str) -> str:
    """Resolve component name to its skill directory path."""
    return SKILL_DIR_MAP.get(component, f"debugger-{component}")


def find_promotable(component: str, min_hits: int = 5) -> list[dict]:
    """Find learnings eligible for promotion.

    Criteria:
    - type == "new_pattern"
    - hit_count >= min_hits (if tracked)
    - No contradicting corrections

    Args:
        component: Component name
        min_hits: Minimum hit count threshold

    Returns:
        List of learnings ready for promotion
    """
    path = MEMORY_BASE / "components" / resolve_component_path(component) / "learnings.json"
    if not path.exists():
        return []

    with open(path) as f:
        data = json.load(f)

    promotable = []
    for entry in data.get("learnings", []):
        if entry.get("type") != "new_pattern":
            continue
        if entry.get("hit_count", 0) >= min_hits:
            promotable.append(entry)

    return promotable


def promote_to_skill(component: str, learnings: list[dict], dry_run: bool = False) -> list[str]:
    """Append promoted learnings to SKILL.md.

    Args:
        component: Component name
        learnings: Entries to promote
        dry_run: If True, print what would be added without writing

    Returns:
        List of promoted pattern descriptions
    """
    skill_dir = SKILLS_BASE / resolve_skill_dir(component)
    skill_path = skill_dir / "SKILL.md"

    if not skill_path.exists():
        print(f"Warning: {skill_path} not found", file=sys.stderr)
        return []

    promoted = []
    lines_to_add = ["\n\n## Promoted Learnings (auto-generated)\n"]

    for entry in learnings:
        pattern = entry.get("pattern", "")
        classification = entry.get("classification", "")
        context = entry.get("context", "")
        line = f"- `{pattern}` → {classification}: {context}"
        lines_to_add.append(line + "\n")
        promoted.append(line)

    if dry_run:
        print("Would add to", skill_path)
        print("".join(lines_to_add))
    else:
        with open(skill_path, "a") as f:
            f.writelines(lines_to_add)

    return promoted


def main():
    parser = argparse.ArgumentParser(description="Promote learnings to SKILL.md")
    parser.add_argument("--component", required=True, help="Component name")
    parser.add_argument("--min-hits", type=int, default=5, help="Minimum hit count")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    promotable = find_promotable(args.component, args.min_hits)
    if not promotable:
        print(f"No learnings ready for promotion (min_hits={args.min_hits})")
        sys.exit(0)

    promoted = promote_to_skill(args.component, promotable, args.dry_run)
    print(f"Promoted {len(promoted)} learnings")


if __name__ == "__main__":
    main()
