---
name: debugger-pipelines
description: >
  Use when analyzing "Pipelines" component failures from RHOAI test results.
  Covers Data Science Pipelines v2, Argo workflows, Tekton, artifact storage,
  and pipeline run lifecycle.
allowed-tools: Bash(*/debugger-pipelines/scripts/*.sh:*),Bash(*/debugger-pipelines/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Pipelines Debugger

## RP Component
This skill handles the `Pipelines` component from ReportPortal launches.

## Key Concepts

- DSP v2 uses Argo workflows (v1 used Tekton)
- Artifact storage issues are Infrastructure Issues
- Pipeline runs can take 5-30 minutes

## Known Failure Patterns

### Product Bugs
- `pipeline.*failed|PipelineRun.*failed` → Pipeline execution error
- `workflow.*failed` → Argo workflow controller error
- `DSP.*not.*ready` → Data Science Pipelines operator not healthy

### Infrastructure Issues
- `artifact.*upload.*failed|artifact.*storage` → S3/artifact storage issue
- `OOMKilled` on pipeline step → Step needs more memory
- `ImagePullBackOff` on step image → Pipeline step image unavailable

### Test Automation Issues
- Short timeout for complex pipelines → Some pipelines need 30 min
- `AssertionError` on pipeline output → Expected output mismatch

## Timeout Expectations

| Operation | Expected Duration |
|---|---|
| Pipeline run (simple) | 5-10 minutes |
| Pipeline run (complex) | 10-30 minutes |
| Artifact upload | 1-5 minutes |

## Diagnosis Steps

1. Read test failure logs
2. Check if DSP operator is healthy
3. If cluster access available, run `scripts/inspect_pipelines.sh`
4. Check pipeline run status and individual step failures
5. Classify and output structured JSON
