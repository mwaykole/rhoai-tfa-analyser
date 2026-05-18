#!/usr/bin/env python3
"""Generic log parser for unrecognized components."""

import json
import re
import sys

PATTERNS = [
    ("product_bug", r"reconcile.*error|controller.*failed|operator.*panic"),
    ("product_bug", r"no matches for kind"),
    ("product_bug", r"500.*Internal.*Server.*Error|503.*Service.*Unavailable"),
    ("product_bug", r"gRPC.*UNAVAILABLE"),
    ("infrastructure_issue", r"CrashLoopBackOff|container.*crash"),
    ("infrastructure_issue", r"ImagePullBackOff|ErrImagePull"),
    ("infrastructure_issue", r"OOMKilled|Out.*Of.*Memory"),
    ("infrastructure_issue", r"Insufficient.*cpu|Insufficient.*memory"),
    ("infrastructure_issue", r"no.*such.*host|connection.*refused"),
    ("infrastructure_issue", r"nvidia\.com/gpu.*Insufficient"),
    ("automation_bug", r"TimeoutExpiredError|TimeoutSampler.*exceeded"),
    ("automation_bug", r"StaleElementReference|ElementNotInteractable"),
    ("automation_bug", r"fixture.*not.*found"),
    ("intermittent", r"Connection reset|upstream connect error"),
]


def parse_logs(logs: str) -> dict:
    matches = []
    for classification, pattern in PATTERNS:
        if re.search(pattern, logs, re.IGNORECASE):
            matches.append({"classification": classification, "pattern": pattern})
    return {"matches": matches, "match_count": len(matches), "is_fallback": True}


def main():
    logs = sys.stdin.read()
    result = parse_logs(logs)
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
