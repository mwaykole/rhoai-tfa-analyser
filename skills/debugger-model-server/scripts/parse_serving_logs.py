#!/usr/bin/env python3
"""Parse model serving logs for failure patterns.

Usage:
    parse_serving_logs.py < logs.txt

Output:
    JSON with matched patterns and suggested classification.
"""

import json
import re
import sys

PATTERNS = [
    ("infrastructure_issue", r"storage-initializer.*exit.*code|InvalidAccessKeyId|AccessDenied.*S3"),
    ("infrastructure_issue", r"OOMKilled|Out.*Of.*Memory|memory.*limit.*exceeded"),
    ("infrastructure_issue", r"nvidia\.com/gpu.*Insufficient|no.*GPU.*available"),
    ("infrastructure_issue", r"ImagePullBackOff|ErrImagePull|Failed to pull image"),
    ("infrastructure_issue", r"huggingface.*401|HF_ACCESS_TOKEN|gated.*repo"),
    ("product_bug", r"InferenceService.*not.*[Rr]eady|isvc.*not.*ready"),
    ("product_bug", r"RevisionFailed|LatestCreatedRevision.*not.*[Rr]eady"),
    ("product_bug", r"500.*Internal.*Server.*Error"),
    ("product_bug", r"inference.*failed|prediction.*error|model.*output.*invalid"),
    ("automation_bug", r"TimeoutExpiredError.*wait_timeout|TimeoutSampler.*exceeded"),
]


def parse_logs(logs: str) -> dict:
    """Parse logs and return matched patterns."""
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
