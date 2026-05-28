#!/usr/bin/env python3
"""Fetch test failures from ReportPortal for a given launch.

In local/Cursor mode, the orchestrator uses MCP tools directly (preferred).
This script is the fallback for containerized runs where MCP is not available.

Usage:
    fetch_rp_failures.py --launch-id <ID> [--component <name>] [--list-components] [--failed-only]

Environment variables:
    RP_URL        - ReportPortal server URL
    RP_PROJECT    - ReportPortal project name
    RP_TOKEN      - ReportPortal API token
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "tools" / "rp-client"))
from rp_client import RPClient


def get_client() -> RPClient:
    """Create RP client from environment."""
    url = os.environ.get("RP_URL", "")
    if not url:
        print("Error: RP_URL environment variable not set", file=sys.stderr)
        sys.exit(1)
    return RPClient()


def fetch_failures(launch_id: int, component: str | None = None) -> dict:
    """Fetch failures from ReportPortal."""
    client = get_client()
    launch = client.get_launch(launch_id)

    suites_result = client.get_test_items(launch_id, item_type="SUITE", size=100)
    suites = suites_result.get("content", [])
    suite_map = {s["name"]: s for s in suites}

    parent_id = None
    if component:
        comp_lower = component.lower().replace("_", " ").replace("-", " ")
        for name, suite in suite_map.items():
            if name.lower().replace("_", " ").replace("-", " ") == comp_lower:
                parent_id = suite["id"]
                break
        if not parent_id:
            for name, suite in suite_map.items():
                if comp_lower in name.lower():
                    parent_id = suite["id"]
                    break

    failed_items = client.get_failed_items_with_logs(launch_id, parent_id=parent_id)

    return {
        "launch": {
            "id": launch.get("id"),
            "name": launch.get("name"),
            "status": launch.get("status"),
            "start_time": launch.get("startTime"),
            "end_time": launch.get("endTime"),
            "statistics": launch.get("statistics", {}),
        },
        "component_filter": component,
        "suites": [
            {"name": s["name"], "id": s["id"], "status": s.get("status", "unknown")}
            for s in suites
        ],
        "total_failures": len(failed_items),
        "failures": [
            {
                "id": item["id"],
                "name": item.get("name", ""),
                "type": item.get("type", ""),
                "status": item.get("status", ""),
                "parent": (item.get("pathNames", {}).get("itemPaths", [{}])[-1].get("name", "")
                           if item.get("pathNames", {}).get("itemPaths") else ""),
                "issue": item.get("issue", {}),
                "logs": [
                    {"id": l.get("id"), "level": l.get("level", ""), "message": l.get("message", "")}
                    for l in item.get("logs", [])
                ],
            }
            for item in failed_items
        ],
    }


def list_components(launch_id: int, failed_only: bool = False) -> list[dict]:
    """List top-level suites for a launch."""
    client = get_client()
    suites_result = client.get_test_items(launch_id, item_type="SUITE", size=100)
    suites = suites_result.get("content", [])
    if failed_only:
        suites = [s for s in suites if s.get("status") == "FAILED"]
    return [{"name": s["name"], "id": s["id"], "status": s.get("status", "unknown")} for s in suites]


def main():
    parser = argparse.ArgumentParser(description="Fetch RP failures")
    parser.add_argument("--launch-id", required=True, type=int, help="ReportPortal launch ID")
    parser.add_argument("--component", help="Filter by component/suite name")
    parser.add_argument("--list-components", action="store_true", help="List components only")
    parser.add_argument("--failed-only", action="store_true", help="Only failed components")
    args = parser.parse_args()

    if args.list_components:
        components = list_components(args.launch_id, args.failed_only)
        json.dump(components, sys.stdout, indent=2)
    else:
        result = fetch_failures(args.launch_id, args.component)
        json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
