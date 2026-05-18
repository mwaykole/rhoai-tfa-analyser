#!/usr/bin/env python3
"""Parse cluster health logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("infrastructure_issue", r"node.*NotReady|node.*not.*ready"),
    ("infrastructure_issue", r"operator.*not.*ready"),
    ("infrastructure_issue", r"DSC.*not.*ready"),
    ("infrastructure_issue", r"etcd.*unhealthy|api.*server.*error"),
    ("infrastructure_issue", r"certificate.*expired"),
    ("product_bug", r"DSC.*reconcile.*failed"),
    ("product_bug", r"component.*install.*failed"),
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
