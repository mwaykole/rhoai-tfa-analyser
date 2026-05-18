#!/usr/bin/env python3
"""Parse workbench logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("infrastructure_issue", r"ImagePullBackOff|ErrImagePull"),
    ("infrastructure_issue", r"PVC.*pending|PVC.*bound.*failed"),
    ("infrastructure_issue", r"Insufficient.*cpu|Insufficient.*memory"),
    ("product_bug", r"Notebook.*not.*ready"),
    ("product_bug", r"notebook.*failed.*start"),
    ("automation_bug", r"TimeoutExpiredError"),
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
