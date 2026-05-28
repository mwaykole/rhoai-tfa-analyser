---
name: architecture-reference
description: >
  Use when analyzing RHOAI/ODH test failures that need architectural context —
  CRDs, ports, RBAC, dependencies, data flows, deployment modes, or network topology.
  Fetches the latest architecture-context repo on every run so data is always current.
  Trigger phrases: "architecture context", "component architecture", "check CRDs",
  "check RBAC", "check dependencies", "what ports does X use", "how does X connect to Y".
allowed-tools: Bash(*/architecture-reference/scripts/*.py:*),Bash(*/architecture-reference/scripts/*.sh:*)
---

# RHOAI Architecture Reference

Provides structured architecture documentation for all RHOAI/ODH components.
The architecture data is cloned fresh from GitHub on every invocation so
debugger skills always work with the latest architectural context.

## How It Works

The `arch_lookup.py` script automatically syncs before any query:

1. **First run** — shallow-clones `architecture-context` into the repo root
2. **Subsequent runs** — `git pull --ff-only` to get latest changes
3. **Query** — reads the requested component/section from local files

The cloned `architecture-context/` directory is gitignored — it exists only
at runtime and is never committed.

### Environment Overrides

| Variable | Default | Purpose |
|---|---|---|
| `ARCH_CONTEXT_REPO` | `https://github.com/mwaykole/architecture-context.git` | Git remote URL |
| `ARCH_CONTEXT_BRANCH` | `main` | Branch to track |

## Data Layout (after sync)

```
architecture-context/                    # cloned at runtime, gitignored
  architecture/
    rhoai-{version}/
      {component}.md                     # structured component architecture
      {component}.json                   # machine-readable extract
      PLATFORM.md                        # aggregated platform view
      diagrams/                          # Mermaid, PNG, C4, ASCII diagrams
  overlays/                              # corrections between regeneration cycles
```

## Available Versions

| Symlink | Points To |
|---------|-----------|
| `current-ga` | Latest GA release |
| `latest-released` | Latest released version |
| `early-access` | Latest EA release |
| `newest` | Most recent (GA or EA) |
| `rhoai.next` | Bleeding-edge (~70 components) |

Concrete versions: `rhoai-2.6` through `rhoai-3.5-ea.1` (grows over time).

## Usage

### Targeted component lookups:

```bash
# What CRDs does kserve own?
scripts/arch_lookup.py --component kserve --version 3.4 --section crds

# What ports/services does kserve expose?
scripts/arch_lookup.py --component kserve --version 3.4 --section network

# What RBAC permissions does kserve need?
scripts/arch_lookup.py --component kserve --version 3.4 --section rbac

# What does kserve depend on?
scripts/arch_lookup.py --component kserve --version 3.4 --section dependencies

# How do requests flow through kserve?
scripts/arch_lookup.py --component kserve --version 3.4 --section dataflows

# Full architecture doc
scripts/arch_lookup.py --component kserve --version 3.4 --section all
```

### Cross-component / platform-level queries:

```bash
# Platform-wide architecture overview
scripts/arch_lookup.py --version 3.4 --platform

# List all components for a version
scripts/arch_lookup.py --version 3.4 --list-components
```

### Check active overlays for corrections:

```bash
scripts/arch_lookup.py --overlays --component kserve
```

### Skip sync (use cached data when offline or for speed):

```bash
scripts/arch_lookup.py --skip-sync --component kserve --version 3.4 --section crds
```

## Component Name Mapping

The architecture-context uses repository names. Map from RP component names:

| RP Component | Architecture File |
|---|---|
| `Model_server` | `vllm.md`, `caikit-nlp.md`, `text-generation-inference.md` |
| `kserve` | `kserve.md` |
| `llmd` | `llm-d.md` |
| `modelmesh` | `modelmesh-serving.md` |
| `serving_runtimes` | `odh-model-controller.md` |
| `llama_stack` | `ogx-k8s-operator.md` |
| `Pipelines` | `data-science-pipelines.md`, `data-science-pipelines-operator.md` |
| `model_registry` | `model-registry.md`, `model-registry-operator.md` |
| `workbenches` | `notebooks.md` |
| `Dashboard` | `odh-dashboard.md` |
| `trustyai` | `trustyai-service.md`, `trustyai-service-operator.md` |
| `rhoai_operators` | `rhods-operator.md` |
| `Distributed` | `kubeflow.md`, `codeflare-sdk.md`, `kueue.md` |

## What Each Architecture Doc Contains

| Section | Contents |
|---------|----------|
| **Metadata** | Repo URL, version, commit, OCP versions, CPU arches, image count |
| **Architecture Components** | Sub-components table (name, type, purpose) |
| **APIs Exposed** | CRD table + HTTP endpoint table |
| **Dependencies** | External + internal RHOAI dependency tables |
| **Network Architecture** | Services, ingress, egress tables with ports/encryption/auth |
| **Security** | RBAC cluster roles, secrets, auth & authz |
| **Data Flows** | Step-by-step source → destination chains |
| **Integration Points** | Inter-component interaction table |

## When to Use This Skill

- A failure involves CRD or API errors → check **APIs Exposed**
- A failure involves connectivity/timeout → check **Network Architecture** + **Data Flows**
- A failure involves permission denied / RBAC → check **Security > RBAC**
- A failure involves missing dependencies → check **Dependencies**
- Understanding how components interact → check **Integration Points** or **PLATFORM.md**
- Verifying expected behavior against architecture → read the full component doc
