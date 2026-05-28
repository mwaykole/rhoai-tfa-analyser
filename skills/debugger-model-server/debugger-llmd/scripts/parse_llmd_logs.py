#!/usr/bin/env python3
"""Parse LLMD-specific logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"no matches for kind.*LeaderWorkerSet"),
    ("product_bug", r"failed to build.*expected.*LWS"),
    ("product_bug", r"failed to reconcile.*multi-node|failed to reconcile.*workload"),
    ("product_bug", r"llminferenceservice.*failed"),
    ("infrastructure_issue", r"worker.*not.*ready|leader.*not.*ready"),
    ("infrastructure_issue", r"GPU.*unavailable|Insufficient.*nvidia"),
    ("infrastructure_issue", r"OOMKilled"),
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
