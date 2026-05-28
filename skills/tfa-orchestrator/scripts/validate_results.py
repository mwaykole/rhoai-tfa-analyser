#!/usr/bin/env python3
"""Validate TFA classification results against a strict schema.

Usage:
    validate_results.py --results <results.json> [--fix]

Validates each classification entry for required fields, valid enums,
and value ranges. With --fix, auto-corrects recoverable issues
(e.g., clamps confidence to 0-1, normalizes classification names).

Exit codes:
    0 — all entries valid (or fixed with --fix)
    1 — validation errors found
"""

import argparse
import json
import sys
from pathlib import Path

VALID_CLASSIFICATIONS = {
    "product_bug",
    "infrastructure_issue",
    "automation_bug",
    "intermittent",
    "to_investigate",
    "no_defect",
}

CLASSIFICATION_ALIASES = {
    "product bug": "product_bug",
    "productbug": "product_bug",
    "pb": "product_bug",
    "infrastructure": "infrastructure_issue",
    "infra": "infrastructure_issue",
    "infra_issue": "infrastructure_issue",
    "automation": "automation_bug",
    "test_automation": "automation_bug",
    "test automation": "automation_bug",
    "flaky": "intermittent",
    "intermittent_failure": "intermittent",
    "unknown": "to_investigate",
    "investigate": "to_investigate",
    "nodefect": "no_defect",
    "no defect": "no_defect",
}

VALID_SEVERITIES = {"critical", "high", "medium", "low"}

RP_DEFECT_CODES = {
    "product_bug": "pb001",
    "automation_bug": "ab001",
    "infrastructure_issue": "si001",
    "intermittent": "ab_1kbn5su3gqpdt",
    "no_defect": "nd001",
    "to_investigate": "ti001",
}


def normalize_classification(value: str) -> str | None:
    """Normalize a classification value to a valid enum."""
    lower = value.strip().lower().replace("-", "_")
    if lower in VALID_CLASSIFICATIONS:
        return lower
    return CLASSIFICATION_ALIASES.get(lower)


def validate_entry(entry: dict, index: int, fix: bool = False) -> list[str]:
    """Validate a single classification entry. Returns list of error messages."""
    errors = []

    if "test_name" not in entry and "name" not in entry:
        errors.append(f"[{index}] missing test_name")

    cls = entry.get("classification", "")
    if not cls:
        errors.append(f"[{index}] missing classification")
    else:
        normalized = normalize_classification(cls)
        if normalized is None:
            errors.append(f"[{index}] invalid classification: '{cls}'")
        elif normalized != cls and fix:
            entry["classification"] = normalized

    sev = entry.get("severity", "")
    if sev and sev.lower() not in VALID_SEVERITIES:
        errors.append(f"[{index}] invalid severity: '{sev}'")
    elif sev and fix:
        entry["severity"] = sev.lower()
    elif not sev and fix:
        entry["severity"] = "medium"

    conf = entry.get("confidence")
    if conf is not None:
        try:
            conf_val = float(conf)
            if conf_val > 1 and conf_val <= 100:
                if fix:
                    entry["confidence"] = round(conf_val / 100, 2)
            elif conf_val < 0 or conf_val > 100:
                errors.append(f"[{index}] confidence out of range: {conf_val}")
        except (TypeError, ValueError):
            errors.append(f"[{index}] confidence not a number: {conf}")

    if not entry.get("root_cause") and not entry.get("root_cause_summary"):
        errors.append(f"[{index}] missing root_cause")

    if fix and entry.get("classification") in RP_DEFECT_CODES:
        if not entry.get("rp_defect_type"):
            entry["rp_defect_type"] = RP_DEFECT_CODES[entry["classification"]]

    return errors


def validate_results(results: list[dict], fix: bool = False) -> tuple[list[dict], list[str]]:
    """Validate all results. Returns (validated_results, all_errors)."""
    all_errors = []
    for i, entry in enumerate(results):
        errors = validate_entry(entry, i, fix=fix)
        all_errors.extend(errors)
    return results, all_errors


def main():
    parser = argparse.ArgumentParser(description="Validate TFA results JSON")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    parser.add_argument("--fix", action="store_true", help="Auto-fix recoverable issues in-place")
    args = parser.parse_args()

    path = Path(args.results)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    if isinstance(data, dict):
        results = data.get("classified_failures", data.get("failures", [data]))
    elif isinstance(data, list):
        results = data
    else:
        print("Error: results must be a JSON array or object", file=sys.stderr)
        sys.exit(1)

    validated, errors = validate_results(results, fix=args.fix)

    if errors:
        for err in errors:
            print(f"VALIDATION: {err}", file=sys.stderr)
        if not args.fix:
            print(f"\n{len(errors)} validation error(s). Use --fix to auto-correct.", file=sys.stderr)
            sys.exit(1)

    if args.fix:
        with open(path, "w") as f:
            json.dump(validated, f, indent=2)
        fixed_count = len(errors)
        print(json.dumps({"status": "fixed", "entries": len(validated), "fixes_applied": fixed_count}))
    else:
        print(json.dumps({"status": "valid", "entries": len(validated)}))


if __name__ == "__main__":
    main()
