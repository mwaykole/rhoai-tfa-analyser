#!/usr/bin/env python3
"""Fetch test failures from ReportPortal for a given launch.

Usage:
    fetch_rp_failures.py --launch-id <ID> [--component <name>] [--list-components] [--failed-only]

Environment variables:
    RP_URL        - ReportPortal server URL
    RP_PROJECT    - ReportPortal project name
    RP_USERNAME   - ReportPortal username
    RP_PASSWORD   - ReportPortal password
    RP_TOKEN      - ReportPortal API token (alternative to username/password)

Output:
    JSON to stdout with failures and their logs.
"""

import argparse
import json
import os
import sys


def get_config():
    """Load RP connection config from environment."""
    return {
        "url": os.environ.get("RP_URL", ""),
        "project": os.environ.get("RP_PROJECT", ""),
        "username": os.environ.get("RP_USERNAME", ""),
        "password": os.environ.get("RP_PASSWORD", ""),
        "token": os.environ.get("RP_TOKEN", ""),
    }


def fetch_failures(launch_id: str, component: str | None = None) -> dict:
    """Fetch failures from ReportPortal.

    Args:
        launch_id: RP launch ID
        component: Optional component filter

    Returns:
        Dict with launch info and failures
    """
    # TODO: Implement RP API calls using tools/rp-client/rp_client.py
    raise NotImplementedError("RP client integration pending")


def list_components(launch_id: str, failed_only: bool = False) -> list[str]:
    """List top-level components (suites) for a launch.

    Args:
        launch_id: RP launch ID
        failed_only: Only return components with failures

    Returns:
        List of component names
    """
    # TODO: Implement using tools/rp-client/rp_client.py
    raise NotImplementedError("RP client integration pending")


def main():
    parser = argparse.ArgumentParser(description="Fetch RP failures")
    parser.add_argument("--launch-id", required=True, help="ReportPortal launch ID")
    parser.add_argument("--component", help="Filter by component name")
    parser.add_argument("--list-components", action="store_true", help="List components only")
    parser.add_argument("--failed-only", action="store_true", help="Only failed components")
    args = parser.parse_args()

    config = get_config()
    if not config["url"]:
        print("Error: RP_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if args.list_components:
        components = list_components(args.launch_id, args.failed_only)
        for c in components:
            print(c)
    else:
        result = fetch_failures(args.launch_id, args.component)
        json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
