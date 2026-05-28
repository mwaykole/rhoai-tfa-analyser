#!/usr/bin/env python3
"""Look up RHOAI component architecture data, fetching latest from GitHub first.

On every invocation, clones or pulls the architecture-context repository
so that architecture docs are always up to date.

Usage:
    arch_lookup.py --component <name> --version <ver> [--section <section>]
    arch_lookup.py --version <ver> --platform
    arch_lookup.py --version <ver> --list-components
    arch_lookup.py --overlays [--component <name>]

Examples:
    arch_lookup.py --component kserve --version 3.4 --section crds
    arch_lookup.py --component kserve --version 3.4 --section network
    arch_lookup.py --component kserve --version 3.4 --section rbac
    arch_lookup.py --component kserve --version 3.4 --section dependencies
    arch_lookup.py --component kserve --version 3.4 --section dataflows
    arch_lookup.py --component kserve --version 3.4 --section all
    arch_lookup.py --version 3.4 --platform
    arch_lookup.py --version 3.4 --list-components
    arch_lookup.py --overlays --component kserve
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARCH_CONTEXT_DIR = REPO_ROOT / "architecture-context"
ARCH_DIR = ARCH_CONTEXT_DIR / "architecture"
OVERLAYS_DIR = ARCH_CONTEXT_DIR / "overlays"

REPO_URL = os.environ.get(
    "ARCH_CONTEXT_REPO",
    "https://github.com/mwaykole/architecture-context.git",
)
REPO_BRANCH = os.environ.get("ARCH_CONTEXT_BRANCH", "main")

RP_TO_ARCH_FILES = {
    "model_server": ["vllm", "caikit-nlp", "text-generation-inference"],
    "model server": ["vllm", "caikit-nlp", "text-generation-inference"],
    "kserve": ["kserve"],
    "llmd": ["llm-d"],
    "modelmesh": ["modelmesh-serving"],
    "model mesh": ["modelmesh-serving"],
    "serving_runtimes": ["odh-model-controller"],
    "serving runtimes": ["odh-model-controller"],
    "llama_stack": ["ogx-k8s-operator"],
    "llama stack": ["ogx-k8s-operator"],
    "llamastack": ["ogx-k8s-operator"],
    "pipelines": ["data-science-pipelines", "data-science-pipelines-operator"],
    "model_registry": ["model-registry", "model-registry-operator"],
    "model registry": ["model-registry", "model-registry-operator"],
    "workbenches": ["notebooks"],
    "dashboard": ["odh-dashboard"],
    "trustyai": ["trustyai-service", "trustyai-service-operator"],
    "rhoai_operators": ["rhods-operator"],
    "rhoai operators": ["rhods-operator"],
    "distributed": ["kubeflow", "codeflare-sdk", "kueue"],
    "cluster_health": [],
    "cluster health": [],
}

SECTION_PATTERNS = {
    "crds": r"(?:## APIs Exposed|### Custom Resource Definitions).*?(?=\n## |\Z)",
    "network": r"## Network Architecture.*?(?=\n## |\Z)",
    "rbac": r"(?:## Security|### RBAC).*?(?=\n## |\Z)",
    "dependencies": r"## Dependencies.*?(?=\n## |\Z)",
    "dataflows": r"## Data Flows.*?(?=\n## |\Z)",
    "integration": r"## Integration Points.*?(?=\n## |\Z)",
    "metadata": r"## .*?Metadata.*?(?=\n## |\Z)",
    "purpose": r"## Purpose.*?(?=\n## |\Z)",
    "components": r"## Architecture Components.*?(?=\n## |\Z)",
}


def sync_architecture_context() -> None:
    """Clone or pull the architecture-context repository to ensure latest data."""
    git_dir = ARCH_CONTEXT_DIR / ".git"
    if git_dir.exists():
        print("[arch-sync] Pulling latest architecture-context...", file=sys.stderr)
        result = subprocess.run(
            ["git", "pull", "--ff-only", "origin", REPO_BRANCH],
            cwd=ARCH_CONTEXT_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[arch-sync] Pull failed, resetting to origin/{REPO_BRANCH}",
                  file=sys.stderr)
            subprocess.run(
                ["git", "fetch", "origin", REPO_BRANCH],
                cwd=ARCH_CONTEXT_DIR,
                capture_output=True,
            )
            subprocess.run(
                ["git", "reset", "--hard", f"origin/{REPO_BRANCH}"],
                cwd=ARCH_CONTEXT_DIR,
                capture_output=True,
            )
        else:
            status = result.stdout.strip()
            if "Already up to date" in status:
                print("[arch-sync] Already up to date.", file=sys.stderr)
            else:
                print(f"[arch-sync] Updated: {status}", file=sys.stderr)
    else:
        print(f"[arch-sync] Cloning {REPO_URL} (branch: {REPO_BRANCH})...",
              file=sys.stderr)
        result = subprocess.run(
            ["git", "clone", "--depth=1", "--branch", REPO_BRANCH,
             REPO_URL, str(ARCH_CONTEXT_DIR)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[arch-sync] Clone failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        print("[arch-sync] Clone complete.", file=sys.stderr)


def resolve_version(version: str) -> Path:
    """Resolve a version string to the architecture directory path."""
    if not version.startswith("rhoai-"):
        version = f"rhoai-{version}"
    ver_dir = ARCH_DIR / version
    if ver_dir.exists():
        return ver_dir
    if ver_dir.is_symlink():
        return ver_dir.resolve()
    for symlink in ["current-ga", "latest-released", "newest"]:
        candidate = ARCH_DIR / symlink
        if candidate.exists():
            return candidate
    print(f"Version directory not found: {ver_dir}", file=sys.stderr)
    print(f"Available: {sorted(p.name for p in ARCH_DIR.iterdir())}", file=sys.stderr)
    sys.exit(1)


def find_arch_files(component: str, ver_dir: Path) -> list[Path]:
    """Find architecture .md files for a component in a version directory."""
    normalized = component.lower().replace("_", " ").replace("-", " ").strip()
    arch_names = RP_TO_ARCH_FILES.get(normalized)

    if arch_names is not None:
        files = []
        for name in arch_names:
            md = ver_dir / f"{name}.md"
            if md.exists():
                files.append(md)
        return files

    direct = ver_dir / f"{component}.md"
    if direct.exists():
        return [direct]

    normalized_file = component.lower().replace(" ", "-").replace("_", "-")
    direct2 = ver_dir / f"{normalized_file}.md"
    if direct2.exists():
        return [direct2]

    matches = []
    for f in ver_dir.glob("*.md"):
        if f.name == "PLATFORM.md":
            continue
        if component.lower() in f.stem.lower():
            matches.append(f)
    return matches


def extract_section(content: str, section: str) -> str:
    """Extract a specific section from a markdown architecture doc."""
    if section == "all":
        return content

    pattern = SECTION_PATTERNS.get(section)
    if not pattern:
        print(f"Unknown section: {section}", file=sys.stderr)
        print(f"Available: {', '.join(SECTION_PATTERNS.keys())}, all", file=sys.stderr)
        sys.exit(1)

    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(0).strip()
    return f"Section '{section}' not found in document."


def list_components(ver_dir: Path) -> list[str]:
    """List all component names available in a version directory."""
    components = []
    for f in sorted(ver_dir.glob("*.md")):
        if f.name == "PLATFORM.md":
            continue
        components.append(f.stem)
    return components


def find_overlays(component: str | None) -> list[Path]:
    """Find relevant overlays, optionally filtered by component."""
    if not OVERLAYS_DIR.exists():
        return []

    overlays = []
    for f in sorted(OVERLAYS_DIR.glob("*.md")):
        if f.name == "README.md":
            continue
        if component is None:
            overlays.append(f)
            continue
        content = f.read_text()
        comp_lower = component.lower()
        if comp_lower in content.lower():
            overlays.append(f)
    return overlays


def main():
    parser = argparse.ArgumentParser(description="RHOAI architecture lookup")
    parser.add_argument("--component", "-c", help="Component name (RP or repo name)")
    parser.add_argument("--version", "-v", help="RHOAI version (e.g. 3.4, 3.4-ea.1)")
    parser.add_argument("--section", "-s", default="all",
                        help="Section to extract: crds, network, rbac, dependencies, "
                             "dataflows, integration, metadata, purpose, components, all")
    parser.add_argument("--platform", "-p", action="store_true",
                        help="Show PLATFORM.md instead of component docs")
    parser.add_argument("--list-components", "-l", action="store_true",
                        help="List available components for a version")
    parser.add_argument("--overlays", "-o", action="store_true",
                        help="Show active overlays")
    parser.add_argument("--skip-sync", action="store_true",
                        help="Skip git clone/pull (use cached data)")
    args = parser.parse_args()

    if not args.skip_sync:
        sync_architecture_context()

    if args.overlays:
        overlays = find_overlays(args.component)
        if not overlays:
            print("No matching overlays found.")
            return
        for overlay in overlays:
            content = overlay.read_text()
            if "status: superseded" in content.lower():
                continue
            print(f"--- {overlay.name} ---")
            print(content)
            print()
        return

    if not args.version:
        parser.error("--version is required (unless using --overlays)")

    ver_dir = resolve_version(args.version)

    if args.list_components:
        components = list_components(ver_dir)
        print(f"Components in {ver_dir.name} ({len(components)}):")
        for c in components:
            print(f"  {c}")
        return

    if args.platform:
        platform_md = ver_dir / "PLATFORM.md"
        if not platform_md.exists():
            print(f"PLATFORM.md not found in {ver_dir}", file=sys.stderr)
            sys.exit(1)
        content = platform_md.read_text()
        print(extract_section(content, args.section))
        return

    if not args.component:
        parser.error("--component is required for component lookups")

    files = find_arch_files(args.component, ver_dir)
    if not files:
        print(f"No architecture files found for '{args.component}' in {ver_dir.name}",
              file=sys.stderr)
        print(f"Available: {', '.join(list_components(ver_dir)[:20])}...", file=sys.stderr)
        sys.exit(1)

    for f in files:
        content = f.read_text()
        print(f"=== {f.name} ===")
        print(extract_section(content, args.section))
        if len(files) > 1:
            print()


if __name__ == "__main__":
    main()
