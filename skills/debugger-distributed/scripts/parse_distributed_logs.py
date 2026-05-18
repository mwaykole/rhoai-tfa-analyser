#!/usr/bin/env python3
"""Parse distributed computing logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"RayCluster.*not.*ready"),
    ("product_bug", r"CodeFlare.*failed|AppWrapper.*failed"),
    ("product_bug", r"Kueue.*admission.*failed"),
    ("infrastructure_issue", r"Insufficient.*cpu|Insufficient.*memory"),
    ("infrastructure_issue", r"OOMKilled"),
    ("infrastructure_issue", r"head.*node.*failure"),
    ("infrastructure_issue", r"ResourceFlavor.*mismatch"),
]


def parse_logs(logs: str) -> dict:
    matches = []
    for classification, pattern in PATTERNS:
        if re.search(pattern, logs, re.IGNORECASE):
            matches.append({"classification": classification, "pattern": pattern})
    return {"matches": matches, "match_count": len(matches)}


def main():
    logs = sys.stdin.read()
    result = parse_logs(logs)
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
