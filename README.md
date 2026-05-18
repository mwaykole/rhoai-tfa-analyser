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

## Container Build & Runtime

```bash
podman build -f Containerfile.claudio -t tfa-claudio:latest .
```

### Running with Google Vertex AI

The container uses Claude Code with Google Vertex AI as the LLM backend (no Anthropic API key needed).

**Required environment variables:**

| Variable | Description |
|---|---|
| `RP_URL` | ReportPortal base URL |
| `RP_PROJECT` | ReportPortal project name (e.g., `ods_ci`) |
| `RP_USERNAME` | ReportPortal username |
| `RP_PASSWORD` | ReportPortal password |
| `CLOUD_ML_PROJECT_ID` | Google Cloud project ID with Vertex AI enabled |
| `ANTHROPIC_VERTEX_REGION` | Vertex AI region (default: `us-east5`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON key (inside container) |

**Optional:**

| Variable | Description |
|---|---|
| `CLAUDE_CODE_USE_VERTEX` | Set to `1` to enable Vertex AI (default: `1`) |
| `TFA_PROMPT` | Alternative to passing prompt as container argument |

### Run Examples

```bash
# Single launch analysis
podman run --rm \
  -e RP_URL=https://reportportal.example.com \
  -e RP_PROJECT=ods_ci \
  -e RP_USERNAME=user \
  -e RP_PASSWORD=pass \
  -e CLAUDE_CODE_USE_VERTEX=1 \
  -e CLOUD_ML_PROJECT_ID=my-gcp-project \
  -e ANTHROPIC_VERTEX_REGION=us-east5 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json \
  -v /path/to/sa-key.json:/tmp/gcp-key.json:ro \
  -v tfa-memory:/home/claudio/tfa-plugin/memory \
  tfa-claudio:latest \
  "Analyze launch 10748 Model_server failures and post results to RP"
```

### CI/CD Integration

Example pipelines are provided in the `ci/` directory:

- **`ci/Jenkinsfile`** — Jenkins pipeline with credentials binding and memory volume
- **`ci/tekton-task.yaml`** — Tekton Task + Pipeline for OpenShift Pipelines with PVC-backed memory and GCP secret mount

### No Claude SDK Required

- The Claudio base image already has Claude Code installed
- Claude Code handles the Vertex AI connection internally via environment variables
- TFA scripts only fetch data (ReportPortal, cluster) — they make no direct LLM API calls
- Intelligence comes from Claude Code reading `SKILL.md` files and reasoning about the data

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
