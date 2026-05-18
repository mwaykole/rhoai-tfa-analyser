#!/usr/bin/env python3
"""Parse RHOAI operator logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"DSC.*not.*ready|DataScienceCluster.*degraded"),
    ("product_bug", r"component.*degraded|component.*not.*available"),
    ("product_bug", r"reconcile.*error|controller.*failed"),
    ("product_bug", r"operator.*panic"),
    ("infrastructure_issue", r"operator.*not.*ready"),
    ("infrastructure_issue", r"CRD.*not.*found"),
    ("infrastructure_issue", r"CSV.*failed|ClusterServiceVersion.*failed"),
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
