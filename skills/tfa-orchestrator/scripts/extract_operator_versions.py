#!/usr/bin/env python3
"""Extract installed operator versions from an OpenShift cluster and compare
against expected versions from architecture-context.

Usage:
    extract_operator_versions.py [--arch-version <ver>] [--output <file>]

Requires: oc CLI logged into the target cluster.

Outputs a JSON report with:
  - installed: all CSVs found on the cluster
  - expected: product version and components from architecture-context
  - mismatches: version discrepancies or missing operators
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ARCH_CONTEXT_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "architecture-context"
)
ARCH_DIR = ARCH_CONTEXT_DIR / "architecture"

SERVING_OPERATORS = {
    "kserve": ["kserve", "odh-model-controller"],
    "serverless": ["serverless-operator", "knative-serving"],
    "servicemesh": ["servicemesh", "istio"],
    "rhods": ["rhods-operator", "opendatahub-operator"],
    "gpu": ["gpu-operator", "nvidia"],
    "nfd": ["nfd", "node-feature-discovery"],
}

CSV_TO_COMPONENT = {
    "rhods-operator": "rhods-operator",
    "opendatahub-operator": "rhods-operator",
    "kserve-controller-manager": "kserve",
    "odh-model-controller": "odh-model-controller",
    "serverless-operator": "serverless",
    "servicemeshoperator": "servicemesh",
    "gpu-operator-certified": "gpu-operator",
    "nfd": "nfd",
    "authorino-operator": "authorino",
}


def run_oc(args: list[str]) -> str:
    """Run an oc command and return stdout."""
    result = subprocess.run(
        ["oc"] + args, capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_installed_csvs() -> list[dict]:
    """Get all ClusterServiceVersions from the cluster."""
    raw = run_oc([
        "get", "csv", "-A",
        "-o", "jsonpath={range .items[*]}{.metadata.namespace},{.metadata.name},{.spec.version},{.status.phase}{'\\n'}{end}"
    ])
    if not raw:
        return []

    csvs = []
    for line in raw.strip().split("\n"):
        parts = line.split(",")
        if len(parts) >= 4:
            csvs.append({
                "namespace": parts[0],
                "name": parts[1],
                "version": parts[2],
                "phase": parts[3],
            })
    return csvs


def get_dsci_info() -> dict:
    """Get DataScienceClusterInitialization info for RHOAI version."""
    raw = run_oc([
        "get", "dsci", "-A", "-o", "json"
    ])
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        items = data.get("items", [])
        if items:
            item = items[0]
            release = item.get("status", {}).get("release", {})
            return {
                "name": release.get("name", ""),
                "version": release.get("version", ""),
            }
    except (json.JSONDecodeError, KeyError):
        pass
    return {}


def get_dsc_components() -> dict:
    """Get DataScienceCluster component states."""
    raw = run_oc([
        "get", "dsc", "-A", "-o", "json"
    ])
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        items = data.get("items", [])
        if items:
            conditions = items[0].get("status", {}).get("conditions", [])
            components = items[0].get("status", {}).get("installedComponents", {})
            return {
                "components": components,
                "conditions": [
                    {"type": c.get("type"), "status": c.get("status"), "reason": c.get("reason", "")}
                    for c in conditions
                ],
            }
    except (json.JSONDecodeError, KeyError):
        pass
    return {}


def load_expected_versions(arch_version: str) -> dict:
    """Load expected component info from architecture-context."""
    ver_prefix = arch_version if arch_version.startswith("rhoai-") else f"rhoai-{arch_version}"

    ver_dir = None
    for candidate in [ver_prefix, re.sub(r"^(rhoai-\d+\.\d+)\.\d+", r"\1", ver_prefix)]:
        d = ARCH_DIR / candidate
        if d.exists():
            ver_dir = d
            break

    if not ver_dir:
        raw = arch_version.removeprefix("rhoai-")
        major_minor = re.match(r"(\d+\.\d+)", raw)
        if major_minor:
            prefix = f"rhoai-{major_minor.group(1)}"
            for d in sorted(ARCH_DIR.iterdir()):
                if d.name.startswith(prefix) and d.is_dir():
                    ver_dir = d

    if not ver_dir:
        for fallback in ["newest", "current-ga", "latest-released"]:
            d = ARCH_DIR / fallback
            if d.exists():
                ver_dir = d
                break

    if not ver_dir:
        return {}

    result = {"arch_version_dir": ver_dir.name}

    build_info = ver_dir / "build-info.json"
    if build_info.exists():
        with open(build_info) as f:
            data = json.load(f)
            result["product_version"] = data.get("product_version", "")
            result["supported_ocp"] = data.get("supported_ocp_versions", [])
            result["operator_features"] = data.get("operator_features", {})

    comp_map = ver_dir / "component-map.json"
    if comp_map.exists():
        with open(comp_map) as f:
            data = json.load(f)
            components = {}
            for key, info in data.get("components", {}).items():
                components[key] = {
                    "type": info.get("type", ""),
                    "tier": info.get("tier", ""),
                    "ref": info.get("ref", ""),
                    "shipped": info.get("shipped", False),
                }
            result["components"] = components

    return result


def find_mismatches(installed_csvs: list[dict], expected: dict, dsci: dict) -> list[dict]:
    """Compare installed operator versions against expected."""
    mismatches = []

    expected_version = expected.get("product_version", "")
    dsci_version = dsci.get("version", "")
    if expected_version and dsci_version and expected_version != dsci_version:
        mismatches.append({
            "type": "version_mismatch",
            "component": "rhods-operator",
            "detail": f"Cluster has RHOAI {dsci_version}, expected {expected_version}",
            "severity": "high",
            "installed": dsci_version,
            "expected": expected_version,
        })

    csv_names = {csv["name"].lower(): csv for csv in installed_csvs}

    serving_keywords = ["kserve", "serverless", "servicemesh", "knative"]
    serving_found = {}
    for csv in installed_csvs:
        name_lower = csv["name"].lower()
        for kw in serving_keywords:
            if kw in name_lower:
                serving_found[kw] = csv
                break

    expected_components = expected.get("components", {})
    for comp_key in ["kserve", "odh-model-controller"]:
        if comp_key in expected_components:
            info = expected_components[comp_key]
            if info.get("shipped"):
                found = any(comp_key in csv["name"].lower() for csv in installed_csvs)
                if not found and comp_key == "kserve":
                    found = "kserve" in serving_found
                if not found:
                    mismatches.append({
                        "type": "missing_operator",
                        "component": comp_key,
                        "detail": f"Expected operator '{comp_key}' not found as a CSV on cluster",
                        "severity": "medium",
                        "expected_ref": info.get("ref", ""),
                    })

    for csv in installed_csvs:
        if csv["phase"] != "Succeeded":
            mismatches.append({
                "type": "unhealthy_csv",
                "component": csv["name"],
                "detail": f"CSV {csv['name']} in namespace {csv['namespace']} has phase: {csv['phase']}",
                "severity": "high" if csv["phase"] == "Failed" else "medium",
                "phase": csv["phase"],
                "namespace": csv["namespace"],
            })

    return mismatches


def main():
    parser = argparse.ArgumentParser(description="Extract and compare operator versions")
    parser.add_argument("--arch-version", default="newest",
                        help="RHOAI version for architecture-context lookup")
    parser.add_argument("--output", "-o", help="Write JSON report to file")
    parser.add_argument("--summary", action="store_true",
                        help="Print human-readable summary")
    args = parser.parse_args()

    whoami = run_oc(["whoami"])
    if not whoami:
        print("Error: not logged into a cluster (oc whoami failed)", file=sys.stderr)
        sys.exit(1)

    csvs = get_installed_csvs()
    dsci = get_dsci_info()
    dsc = get_dsc_components()
    expected = load_expected_versions(args.arch_version)
    mismatches = find_mismatches(csvs, expected, dsci)

    serving_csvs = [
        csv for csv in csvs
        if any(kw in csv["name"].lower() for kw in
               ["kserve", "serverless", "servicemesh", "knative", "rhods", "opendatahub",
                "gpu", "nfd", "authorino", "cert-manager"])
    ]

    report = {
        "cluster_user": whoami,
        "dsci": dsci,
        "dsc_components": dsc.get("components", {}),
        "expected_product_version": expected.get("product_version", ""),
        "expected_arch_dir": expected.get("arch_version_dir", ""),
        "serving_operators": [
            {"name": c["name"], "version": c["version"], "phase": c["phase"], "namespace": c["namespace"]}
            for c in serving_csvs
        ],
        "all_csvs_count": len(csvs),
        "mismatches": mismatches,
        "mismatch_count": len(mismatches),
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.output}", file=sys.stderr)

    if args.summary or not args.output:
        print(f"Cluster user: {whoami}")
        print(f"DSCI version: {dsci.get('version', 'N/A')} ({dsci.get('name', '')})")
        print(f"Expected version: {expected.get('product_version', 'N/A')}")
        print(f"Total CSVs: {len(csvs)}")
        print(f"Serving-related CSVs: {len(serving_csvs)}")
        for csv in serving_csvs:
            status = "✓" if csv["phase"] == "Succeeded" else "✗"
            print(f"  {status} {csv['name']} v{csv['version']} ({csv['phase']})")
        if mismatches:
            print(f"\nMismatches ({len(mismatches)}):")
            for m in mismatches:
                print(f"  [{m['severity'].upper()}] {m['type']}: {m['detail']}")
        else:
            print("\nNo mismatches found.")

    if args.output:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
