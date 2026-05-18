---
name: debugger-modelmesh
description: >
  Use when analyzing "modelmesh" component failures from RHOAI test results.
  Covers ModelMesh multi-model serving, shared runtime pods, model cache,
  and gRPC communication issues.
allowed-tools: Bash(*/debugger-modelmesh/scripts/*.sh:*),Bash(*/debugger-modelmesh/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# ModelMesh Debugger

## RP Component
This skill handles the `modelmesh` component from ReportPortal launches.

## Architecture

ModelMesh serves multiple models on shared ServingRuntime pods. Models are loaded/unloaded
dynamically based on demand. Key difference from KServe: no per-model pod.

## Known Failure Patterns

### Product Bugs
- `model.*not.*loaded` → Runtime pod issue or model format mismatch
- `ServingRuntime.*not.*found` → Runtime CR missing
- `gRPC.*UNAVAILABLE` → Inference endpoint failure

### Infrastructure Issues
- `OOMKilled` on runtime pod → Too many models loaded simultaneously
- `CrashLoopBackOff` on modelmesh-serving pods → Runtime crash

### Test Automation Issues
- Short timeout for model loading → ModelMesh cold-loads can take 2-5 min

## Diagnosis Steps

1. Read test failure logs
2. Check runtime pod logs (not individual model pods)
3. If cluster access available, run `scripts/inspect_modelmesh.sh`
4. Check if model format matches ServingRuntime capabilities
5. Classify and output structured JSON
