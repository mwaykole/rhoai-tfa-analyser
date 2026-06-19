#!/usr/bin/env python3
"""Retrieve similar past failures as few-shot examples for classification.

Usage:
    retrieve_examples.py --error <error_text> [--component <name>] [--top-k 5]
    retrieve_examples.py --test-name <name> [--component <name>] [--top-k 5]

Searches memory/components/*/learnings.json for past classifications that
match the given error text or test name. Returns the top-K most similar
entries formatted as few-shot examples for the LLM prompt.

Similarity is computed using token overlap (Jaccard similarity on word tokens),
which is lightweight and requires no external dependencies. Entries with higher
hit_count are boosted as they represent validated patterns.
"""

import argparse
import json
import re
import sys
from pathlib import Path

MEMORY_BASE = Path(__file__).resolve().parent.parent.parent.parent / "memory"

SUB_COMPONENT_MAP = {
    "kserve": "model-server/kserve",
    "llmd": "model-server/llmd",
    "modelmesh": "model-server/modelmesh",
}

COMPONENT_NORMALIZE = {
    "model_server": "model-server",
    "model server": "model-server",
    "serving_runtimes": "serving-runtimes",
    "llama_stack": "llama-stack",
    "model_registry": "model-registry",
    "rhoai_operators": "rhoai-operators",
    "cluster_health": "cluster-health",
}


def tokenize(text: str) -> set[str]:
    """Split text into lowercase word tokens for Jaccard similarity."""
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity coefficient."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def resolve_component_path(component: str) -> str:
    normalized = component.strip().lower().replace("_", " ").replace("-", " ")
    if normalized in SUB_COMPONENT_MAP:
        return SUB_COMPONENT_MAP[normalized]
    return COMPONENT_NORMALIZE.get(normalized, component.lower().replace("_", "-"))


def load_all_learnings(component: str | None = None) -> list[dict]:
    """Load learnings from one component or all."""
    results = []
    if component:
        comp_path = resolve_component_path(component)
        path = MEMORY_BASE / "components" / comp_path / "learnings.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                for entry in data.get("learnings", []):
                    entry["_component"] = comp_path
                    results.append(entry)
    else:
        for path in MEMORY_BASE.rglob("learnings.json"):
            if "orchestrator" in str(path):
                continue
            with open(path) as f:
                data = json.load(f)
                comp = str(path.parent.relative_to(MEMORY_BASE / "components"))
                for entry in data.get("learnings", []):
                    entry["_component"] = comp
                    results.append(entry)
    return results


def retrieve_similar(
    query: str,
    learnings: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Find the most similar past learnings to a query string."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    scored = []
    for entry in learnings:
        if not entry.get("classification"):
            continue

        entry_text = " ".join([
            entry.get("key_error", ""),
            entry.get("error_message", ""),
            entry.get("root_cause", ""),
            entry.get("test_name", ""),
        ])
        entry_tokens = tokenize(entry_text)
        sim = jaccard(query_tokens, entry_tokens)

        hit_boost = min(entry.get("hit_count", 1) / 10, 0.2)
        final_score = sim + hit_boost

        if final_score > 0.05:
            scored.append((final_score, entry))

    scored.sort(key=lambda x: -x[0])
    return [entry for _, entry in scored[:top_k]]


def format_examples(examples: list[dict]) -> str:
    """Format retrieved examples as few-shot prompt text."""
    if not examples:
        return ""

    lines = ["## Past similar failures (use these as reference for classification):\n"]
    for i, ex in enumerate(examples, 1):
        lines.append(f"### Example {i} (seen {ex.get('hit_count', 1)} times)")
        lines.append(f"- **Test:** {ex.get('test_name', 'unknown')}")
        lines.append(f"- **Error:** {ex.get('key_error', 'N/A')}")
        lines.append(f"- **Classification:** {ex.get('classification', 'unknown')}")
        lines.append(f"- **Severity:** {ex.get('severity', 'medium')}")
        lines.append(f"- **Root cause:** {ex.get('root_cause', 'N/A')}")
        if ex.get("recommendation"):
            lines.append(f"- **Fix:** {ex['recommendation']}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Retrieve few-shot examples from memory")
    parser.add_argument("--error", help="Error text to match against")
    parser.add_argument("--test-name", help="Test name to match against")
    parser.add_argument("--component", help="Limit search to this component")
    parser.add_argument("--top-k", type=int, default=5, help="Number of examples to return")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    args = parser.parse_args()

    query = " ".join(filter(None, [args.error, args.test_name]))
    if not query:
        print("Error: provide --error and/or --test-name", file=sys.stderr)
        sys.exit(1)

    learnings = load_all_learnings(args.component)
    if not learnings:
        if args.json:
            json.dump([], sys.stdout)
        else:
            print("No past learnings found — first run, classifying from scratch.")
        sys.exit(0)

    examples = retrieve_similar(query, learnings, args.top_k)

    if args.json:
        clean = [{k: v for k, v in ex.items() if not k.startswith("_")} for ex in examples]
        json.dump(clean, sys.stdout, indent=2)
    else:
        print(format_examples(examples))


if __name__ == "__main__":
    main()
