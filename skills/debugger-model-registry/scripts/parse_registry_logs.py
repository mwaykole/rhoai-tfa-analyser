#!/usr/bin/env python3
"""Parse model registry logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"model_catalog_api.*error|registry.*internal.*error"),
    ("product_bug", r"ModelRegistry.*not.*ready"),
    ("infrastructure_issue", r"mariadb.*connection|postgres.*connection"),
    ("infrastructure_issue", r"connection.*refused.*3306|connection.*refused.*5432"),
    ("infrastructure_issue", r"timeout.*database"),
    ("automation_bug", r"model_catalog_api.*timeout"),
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
