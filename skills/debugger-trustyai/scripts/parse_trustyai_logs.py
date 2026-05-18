#!/usr/bin/env python3
"""Parse TrustyAI logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"TrustyAI.*not.*ready|trustyai.*service.*unavailable"),
    ("product_bug", r"explanation.*failed|fairness.*metric.*error"),
    ("infrastructure_issue", r"TrustyAI.*operator.*not.*installed"),
    ("infrastructure_issue", r"connection.*refused.*trustyai"),
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
