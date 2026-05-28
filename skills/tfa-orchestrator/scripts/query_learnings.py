#!/usr/bin/env python3
"""Search learnings by pattern, component, type, or date range.

Usage:
    query_learnings.py --component <name> [--type <type>] [--pattern <regex>] [--since <ISO_date>]
    query_learnings.py --all [--type <type>] [--pattern <regex>]

Output:
    JSON array of matching learning entries.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

MEMORY_BASE = Path(__file__).resolve().parent.parent.parent.parent / "memory"

SUB_COMPONENT_MAP = {
    "kserve": "model-server/kserve",
    "llmd": "model-server/llmd",
    "modelmesh": "model-server/modelmesh",
}


def resolve_component_path(component: str) -> str:
    """Resolve component name to its memory directory path."""
    return SUB_COMPONENT_MAP.get(component, component)


def load_all_learnings(component: str | None = None) -> list[dict]:
    """Load learnings from one or all components."""
    results = []

    if component:
        path = MEMORY_BASE / "components" / resolve_component_path(component) / "learnings.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                results.extend(data.get("learnings", []))
    else:
        for path in MEMORY_BASE.rglob("learnings.json"):
            with open(path) as f:
                data = json.load(f)
                for entry in data.get("learnings", []):
                    entry["_source_file"] = str(path.relative_to(MEMORY_BASE))
                    results.append(entry)

    return results


def filter_learnings(
    learnings: list[dict],
    learning_type: str | None = None,
    pattern: str | None = None,
    since: str | None = None,
) -> list[dict]:
    """Filter learnings by criteria."""
    results = learnings

    if learning_type:
        results = [l for l in results if l.get("type") == learning_type]

    if pattern:
        regex = re.compile(pattern, re.IGNORECASE)
        results = [l for l in results if regex.search(json.dumps(l))]

    if since:
        since_dt = datetime.fromisoformat(since)
        results = [l for l in results if datetime.fromisoformat(l["timestamp"]) >= since_dt]

    return results


def main():
    parser = argparse.ArgumentParser(description="Query learnings")
    parser.add_argument("--component", help="Component name")
    parser.add_argument("--all", action="store_true", help="Search all components")
    parser.add_argument("--type", help="Filter by learning type")
    parser.add_argument("--pattern", help="Regex pattern to search")
    parser.add_argument("--since", help="Only entries after this ISO date")
    args = parser.parse_args()

    component = None if args.all else args.component
    learnings = load_all_learnings(component)
    filtered = filter_learnings(learnings, args.type, args.pattern, args.since)
    json.dump(filtered, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
