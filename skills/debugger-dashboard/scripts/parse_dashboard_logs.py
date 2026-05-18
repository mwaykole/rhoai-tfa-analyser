#!/usr/bin/env python3
"""Parse dashboard UI test logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("automation_bug", r"StaleElementReference|StaleElementReferenceException"),
    ("automation_bug", r"ElementNotInteractable|element.*not.*clickable"),
    ("automation_bug", r"NoSuchElement|element.*not.*found"),
    ("automation_bug", r"timeout.*click|timeout.*element"),
    ("product_bug", r"500.*Internal.*Server.*Error"),
    ("product_bug", r"dashboard.*crash|dashboard.*unavailable"),
    ("infrastructure_issue", r"connection.*refused.*dashboard"),
    ("infrastructure_issue", r"ERR_CONNECTION_TIMED_OUT"),
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
