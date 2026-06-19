#!/usr/bin/env python3
"""Store a TFA run summary and auto-store each classification as a learning.

Usage:
    store_run.py --results <results.json> [--launch-id <ID>] [--source <description>]

This script does three things:
1. Appends a run summary to memory/orchestrator/run_history.json
2. Stores each classification as a new_pattern learning in the component's memory
3. Increments hit_count on existing learnings that match the same error signature

The memory feedback loop: store_run -> query_learnings (next run) -> better prompts.
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

MEMORY_BASE = Path(__file__).resolve().parent.parent.parent.parent / "memory"
RUN_HISTORY_PATH = MEMORY_BASE / "orchestrator" / "run_history.json"

SUB_COMPONENT_MAP = {
    "kserve": "model-server/kserve",
    "llmd": "model-server/llmd",
    "modelmesh": "model-server/modelmesh",
}

COMPONENT_NORMALIZE = {
    "model_server": "model-server",
    "model server": "model-server",
    "model-server": "model-server",
    "model_serving": "model-server",
    "model-serving": "model-server",
    "serving_runtimes": "serving-runtimes",
    "serving-runtimes": "serving-runtimes",
    "llama_stack": "llama-stack",
    "llama-stack": "llama-stack",
    "model_registry": "model-registry",
    "model-registry": "model-registry",
    "rhoai_operators": "rhoai-operators",
    "rhoai-operators": "rhoai-operators",
    "cluster_health": "cluster-health",
    "cluster-health": "cluster-health",
    "workbenches": "workbenches",
    "dashboard": "dashboard",
    "trustyai": "trustyai",
    "pipelines": "pipelines",
    "distributed": "distributed",
}

KEYWORD_TO_COMPONENT = {
    "kserve": "model-server/kserve",
    "llmd": "model-server/llmd",
    "modelmesh": "model-server/modelmesh",
    "model_server": "model-server",
    "model-server": "model-server",
    "model_serving": "model-server",
    "model-serving": "model-server",
    "model server": "model-server",
    "serving_runtime": "serving-runtimes",
    "serving-runtime": "serving-runtimes",
    "pipeline": "pipelines",
    "dsp": "pipelines",
    "dashboard": "dashboard",
    "trustyai": "trustyai",
    "workbench": "workbenches",
    "notebook": "workbenches",
    "model_registry": "model-registry",
    "model-registry": "model-registry",
    "distributed": "distributed",
    "ray": "distributed",
    "kueue": "distributed",
    "codeflare": "distributed",
    "operator": "rhoai-operators",
    "dsc": "rhoai-operators",
    "llama": "llama-stack",
    "guardrails": "trustyai",
    "lm-eval": "model-server",
    "lmeval": "model-server",
}


def extract_component_from_suite(suite: str) -> str:
    """Extract a known component from free-form suite paths like 'tests/model_serving/upgrade'."""
    lower = suite.strip().lower().replace("_", "-")
    parts = lower.replace("\\", "/").split("/")

    for part in parts:
        clean = part.strip()
        if clean in COMPONENT_NORMALIZE:
            return COMPONENT_NORMALIZE[clean]
        if clean in SUB_COMPONENT_MAP:
            return SUB_COMPONENT_MAP[clean]
        for keyword, comp in KEYWORD_TO_COMPONENT.items():
            if keyword in clean:
                return comp

    return "generic"


def resolve_component_path(component: str) -> str:
    normalized = component.strip().lower().replace("_", "-")
    if normalized in SUB_COMPONENT_MAP:
        return SUB_COMPONENT_MAP[normalized]
    if normalized in COMPONENT_NORMALIZE:
        return COMPONENT_NORMALIZE[normalized]
    if "/" in normalized:
        return extract_component_from_suite(normalized)
    return COMPONENT_NORMALIZE.get(normalized, normalized)


def load_run_history() -> dict:
    if RUN_HISTORY_PATH.exists():
        with open(RUN_HISTORY_PATH) as f:
            return json.load(f)
    return {"version": "1.0", "runs": []}


def load_learnings(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"version": "1.0", "learnings": []}


def error_signature(entry: dict) -> str:
    """Extract a stable error signature for dedup/matching."""
    key_error = entry.get("error_message", entry.get("key_error", ""))
    root_cause = entry.get("root_cause", "")
    if key_error:
        sig = key_error[:200].strip()
    elif root_cause:
        sig = root_cause[:200].strip()
    else:
        sig = entry.get("test_name", "unknown")
    return sig.lower()


def increment_or_store(component_path: str, entry: dict) -> str:
    """Check if a similar learning exists; increment hit_count or store new."""
    learnings_path = MEMORY_BASE / "components" / component_path / "learnings.json"
    learnings_path.parent.mkdir(parents=True, exist_ok=True)
    data = load_learnings(learnings_path)

    sig = error_signature(entry)
    classification = entry.get("classification", "to_investigate")

    for existing in data.get("learnings", []):
        existing_sig = error_signature(existing)
        if existing_sig == sig and existing.get("classification") == classification:
            existing["hit_count"] = existing.get("hit_count", 1) + 1
            existing["last_seen"] = datetime.now(timezone.utc).isoformat()
            with open(learnings_path, "w") as f:
                json.dump(data, f, indent=2)
            return f"incremented:{existing['id']}"

    new_entry = {
        "id": f"learn-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "type": "new_pattern",
        "hit_count": 1,
        "classification": classification,
        "severity": entry.get("severity", "medium"),
        "confidence": entry.get("confidence", 0),
        "test_name": entry.get("test_name", entry.get("name", "")),
        "key_error": entry.get("error_message", entry.get("key_error", "")),
        "root_cause": entry.get("root_cause", ""),
        "recommendation": entry.get("fix_suggestion", entry.get("recommendation", "")),
        "source": "auto_discovered",
    }

    data["learnings"].append(new_entry)
    with open(learnings_path, "w") as f:
        json.dump(data, f, indent=2)
    return f"stored:{new_entry['id']}"


def store_run(results: list[dict], launch_id: str = "", source: str = "") -> dict:
    """Store run summary and individual learnings."""
    now = datetime.now(timezone.utc).isoformat()
    by_classification: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    learning_actions = []

    for entry in results:
        cls = entry.get("classification", "to_investigate")
        sev = entry.get("severity", "medium")
        by_classification[cls] = by_classification.get(cls, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1

        suite = entry.get("suite", entry.get("parent", "generic"))
        comp_path = resolve_component_path(suite)
        action = increment_or_store(comp_path, entry)
        learning_actions.append(action)

    run_summary = {
        "id": f"run-{uuid.uuid4().hex[:8]}",
        "timestamp": now,
        "launch_id": launch_id,
        "source": source or ("reportportal" if launch_id else "log_file"),
        "total_failures": len(results),
        "by_classification": by_classification,
        "by_severity": by_severity,
    }

    history = load_run_history()
    history["runs"].append(run_summary)
    RUN_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RUN_HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

    return {
        "run": run_summary,
        "learnings_stored": learning_actions.count(lambda a: a.startswith("stored:")),
        "learnings_incremented": sum(1 for a in learning_actions if a.startswith("incremented:")),
        "learnings_new": sum(1 for a in learning_actions if a.startswith("stored:")),
        "actions": learning_actions,
    }


def main():
    parser = argparse.ArgumentParser(description="Store TFA run + learnings")
    parser.add_argument("--results", required=True, help="Path to tfa_results.json")
    parser.add_argument("--launch-id", default="", help="RP launch ID if applicable")
    parser.add_argument("--source", default="", help="Source description")
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

    summary = store_run(results, args.launch_id, args.source)
    json.dump(summary, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
