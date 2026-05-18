#!/usr/bin/env python3
"""Parse KServe-specific logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"no matches for kind.*InferenceService"),
    ("product_bug", r"failed to reconcile"),
    ("product_bug", r"RevisionFailed|LatestCreatedRevision.*not.*[Rr]eady"),
    ("product_bug", r"InferenceService.*not.*[Rr]eady"),
    ("infrastructure_issue", r"IngressNotConfigured|ingress.*not.*ready"),
    ("infrastructure_issue", r"CrashLoopBackOff|container.*crash"),
    ("infrastructure_issue", r"Insufficient.*cpu|Insufficient.*memory"),
    ("automation_bug", r"TimeoutExpiredError.*wait_timeout"),
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
