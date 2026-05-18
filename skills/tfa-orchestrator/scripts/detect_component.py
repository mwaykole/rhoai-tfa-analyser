#!/usr/bin/env python3
"""Map a ReportPortal component name to a debugger skill directory.

Usage:
    detect_component.py <component_name>

Output:
    Prints the debugger skill directory name to stdout.
    Example: "debugger-model-server"
"""

import sys

COMPONENT_MAP = {
    "model_server": "debugger-model-server",
    "model server": "debugger-model-server",
    "kserve": "debugger-kserve",
    "llmd": "debugger-llmd",
    "modelmesh": "debugger-modelmesh",
    "model mesh": "debugger-modelmesh",
    "serving_runtimes": "debugger-serving-runtimes",
    "serving runtimes": "debugger-serving-runtimes",
    "llama_stack": "debugger-llama-stack",
    "llama stack": "debugger-llama-stack",
    "llamastack": "debugger-llama-stack",
    "pipelines": "debugger-pipelines",
    "model_registry": "debugger-model-registry",
    "model registry": "debugger-model-registry",
    "workbenches": "debugger-workbenches",
    "dashboard": "debugger-dashboard",
    "trustyai": "debugger-trustyai",
    "rhoai_operators": "debugger-rhoai-operators",
    "rhoai operators": "debugger-rhoai-operators",
    "distributed": "debugger-distributed",
    "cluster_health": "debugger-cluster-health",
    "cluster health": "debugger-cluster-health",
}

FALLBACK = "debugger-generic"


def normalize(name: str) -> str:
    """Normalize component name for matching."""
    return name.lower().replace("_", " ").replace("-", " ").strip()


def detect_skill(component_name: str) -> str:
    """Map RP component name to debugger skill directory.

    Matching order:
    1. Exact normalized match
    2. Substring containment
    3. Fallback to debugger-generic
    """
    normalized = normalize(component_name)

    if normalized in COMPONENT_MAP:
        return COMPONENT_MAP[normalized]

    for key, skill in COMPONENT_MAP.items():
        if key in normalized or normalized in key:
            return skill

    return FALLBACK


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <component_name>", file=sys.stderr)
        sys.exit(1)

    component = " ".join(sys.argv[1:])
    skill = detect_skill(component)
    print(skill)


if __name__ == "__main__":
    main()
