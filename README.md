# RHOAI TFA Analyser - Claudio Plugin

A Claude Code plugin that analyzes RHOAI/ODH test failures from ReportPortal using component-specific debugger skills with persistent memory.

## Overview

This plugin replaces the standalone TFA CLI with a set of Claude Code skills where Claude IS the LLM. Each ReportPortal component gets a dedicated debugger skill containing domain knowledge, failure patterns, and diagnosis workflows.

## Architecture

```
User/CI triggers Claude Code
       │
       ▼
┌─────────────────────┐
│  tfa-orchestrator   │  ← Routes failures to component debuggers
│  SKILL.md           │
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ fetch  │ │ detect │  ← Fetch from RP, detect component
│ _rp_   │ │ _comp  │
└────┬───┘ └────┬───┘
     │          │
     ▼          ▼
┌──────────────────────────────────────────────┐
│  debugger-model-server   │ debugger-kserve   │
│  debugger-llmd           │ debugger-pipelines│
│  debugger-workbenches    │ debugger-dashboard│
│  ... (14 component skills + 1 generic)       │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   memory/   │  ← Persistent learnings per component
                    │ learnings   │
                    └─────────────┘
```

## ReportPortal Component Mapping

| RP Component | Debugger Skill | Domain |
|---|---|---|
| `Model_server` | `debugger-model-server` | vLLM, TGI, Caikit, S3 model download |
| `kserve` | `debugger-kserve` | InferenceService, Knative, Serverless |
| `llmd` | `debugger-llmd` | LLMInferenceService, LeaderWorkerSet |
| `modelmesh` | `debugger-modelmesh` | Multi-model serving |
| `serving_runtimes` | `debugger-serving-runtimes` | ServingRuntime config |
| `llama_stack` | `debugger-llama-stack` | LlamaStack operator |
| `Pipelines` | `debugger-pipelines` | DSP v2, Argo workflows |
| `model_registry` | `debugger-model-registry` | Model Registry, MariaDB |
| `workbenches` | `debugger-workbenches` | Jupyter notebooks, PVC |
| `Dashboard` | `debugger-dashboard` | RHOAI Dashboard UI |
| `trustyai` | `debugger-trustyai` | Model explainability |
| `rhoai_operators` | `debugger-rhoai-operators` | DSC/DSCI/Operator |
| `Distributed` | `debugger-distributed` | Kueue, CodeFlare, Ray |
| `cluster_health` | `debugger-cluster-health` | Pre-flight checks |

## Usage

```bash
# Install plugin into Claude Code
claude plugin install --scope user .

# Trigger analysis (Claude Code will invoke the orchestrator)
# "Analyze launch 10748 failures for Model_server component"
```

## Container Build

```bash
make build
# or
podman build -f Containerfile.claudio -t tfa-claudio:latest .
```

## Memory / Learning Layer

After every analysis run, the system stores learnings in `memory/`:
- Per-component patterns, corrections, timeout calibrations
- Cross-component correlations at the orchestrator level
- Run history for trend analysis

High-confidence learnings (>5 hits, 100% accuracy) can be promoted into SKILL.md files.

## Read-Only Cluster Access

All cluster inspect scripts are strictly read-only:
- Allowed: `oc get`, `oc describe`, `oc logs`
- Forbidden: `oc delete`, `oc apply`, `oc create`, `oc patch`, `oc edit`

## Development

```bash
make install   # Install Python dependencies
make lint      # Lint shell and Python scripts
make test      # Run tests
```
