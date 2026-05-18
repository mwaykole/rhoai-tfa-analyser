#!/usr/bin/env python3
"""Parse pipeline logs for failure patterns."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"pipeline.*failed|PipelineRun.*failed"),
    ("product_bug", r"workflow.*failed"),
    ("product_bug", r"DSP.*not.*ready"),
    ("infrastructure_issue", r"artifact.*upload.*failed|artifact.*storage"),
    ("infrastructure_issue", r"OOMKilled"),
    ("infrastructure_issue", r"ImagePullBackOff"),
    ("automation_bug", r"AssertionError"),
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
