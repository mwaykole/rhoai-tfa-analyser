#!/usr/bin/env python3
"""Parse ModelMesh-specific logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"model.*not.*loaded"),
    ("product_bug", r"ServingRuntime.*not.*found"),
    ("product_bug", r"gRPC.*UNAVAILABLE"),
    ("infrastructure_issue", r"OOMKilled"),
    ("infrastructure_issue", r"CrashLoopBackOff"),
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
