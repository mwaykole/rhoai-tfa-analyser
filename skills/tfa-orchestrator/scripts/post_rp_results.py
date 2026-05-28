#!/usr/bin/env python3
"""Post classification results back to ReportPortal.

In local/Cursor mode, the orchestrator uses MCP rp_update_test_item_issues.
This script is the fallback for containerized runs where MCP is not available.

Usage:
    post_rp_results.py --results <results.json>
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "tools" / "rp-client"))
from rp_client import RPClient

DEFECT_MAP = {
    "product_bug": "pb001",
    "automation_bug": "ab001",
    "infrastructure_issue": "si001",
    "intermittent": "ab_1kbn5su3gqpdt",
    "no_defect": "nd001",
    "to_investigate": "ti001",
}


def post_results(results: list[dict]) -> dict:
    """Post classification results to ReportPortal."""
    client = RPClient()

    issues = []
    for r in results:
        defect_code = DEFECT_MAP.get(r.get("classification", ""), "ti001")
        comment = f"[TFA] {r.get('root_cause', '')} (confidence: {r.get('confidence', 0):.0%})"
        issues.append({
            "testItemId": int(r["test_id"]),
            "issue": {"issueType": defect_code, "comment": comment},
        })

    if not issues:
        return {"updated": 0, "message": "No results to post"}

    resp = client.update_defect_types(issues)
    return {"updated": len(issues), "response": resp}


def main():
    parser = argparse.ArgumentParser(description="Post results to RP")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    args = parser.parse_args()

    with open(args.results) as f:
        results = json.load(f)

    summary = post_results(results)
    json.dump(summary, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
