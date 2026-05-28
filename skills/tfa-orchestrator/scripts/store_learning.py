#!/usr/bin/env python3
"""Store a learning entry in the memory layer.

Usage:
    store_learning.py --component <name> --type <type> --data <json_string>
    store_learning.py --orchestrator --type <type> --data <json_string>

Learning types: new_pattern, correction, timeout_calibration, correlation,
                new_component, false_positive
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

MEMORY_BASE = Path(__file__).resolve().parent.parent.parent.parent / "memory"

SUB_COMPONENT_MAP = {
    "kserve": "model-server/kserve",
    "llmd": "model-server/llmd",
    "modelmesh": "model-server/modelmesh",
}

VALID_TYPES = [
    "new_pattern",
    "correction",
    "timeout_calibration",
    "correlation",
    "new_component",
    "false_positive",
]


def resolve_component_path(component: str) -> str:
    """Resolve component name to its memory directory path."""
    return SUB_COMPONENT_MAP.get(component, component)


def get_learnings_path(component: str | None = None) -> Path:
    """Get path to learnings.json for a component or orchestrator."""
    if component:
        return MEMORY_BASE / "components" / resolve_component_path(component) / "learnings.json"
    return MEMORY_BASE / "orchestrator" / "learnings.json"


def load_learnings(path: Path) -> dict:
    """Load existing learnings from JSON file."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"version": "1.0", "learnings": []}


def store_learning(component: str | None, learning_type: str, data: dict) -> dict:
    """Append a learning entry.

    Args:
        component: Component name (None for orchestrator)
        learning_type: One of VALID_TYPES
        data: Learning data payload

    Returns:
        The stored learning entry
    """
    path = get_learnings_path(component)
    learnings = load_learnings(path)

    entry = {
        "id": f"learn-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": learning_type,
        **data,
        "source": data.get("source", "auto_discovered"),
    }

    learnings["learnings"].append(entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(learnings, f, indent=2)

    return entry


def main():
    parser = argparse.ArgumentParser(description="Store a learning entry")
    parser.add_argument("--component", help="Component name (omit for orchestrator)")
    parser.add_argument("--orchestrator", action="store_true", help="Store at orchestrator level")
    parser.add_argument("--type", required=True, choices=VALID_TYPES, help="Learning type")
    parser.add_argument("--data", required=True, help="JSON string with learning data")
    args = parser.parse_args()

    component = None if args.orchestrator else args.component
    if not component and not args.orchestrator:
        print("Error: specify --component or --orchestrator", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.data)
    entry = store_learning(component, args.type, data)
    json.dump(entry, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
