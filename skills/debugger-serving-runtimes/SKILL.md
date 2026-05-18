---
name: debugger-serving-runtimes
description: >
  Use when analyzing "serving_runtimes" component failures from RHOAI test results.
  Covers ServingRuntime/ClusterServingRuntime configuration, model format compatibility,
  and runtime container issues.
allowed-tools: Bash(*/debugger-serving-runtimes/scripts/*.sh:*),Bash(*/debugger-serving-runtimes/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Serving Runtimes Debugger

## RP Component
This skill handles the `serving_runtimes` component from ReportPortal launches.

## Key Concepts

- **ServingRuntime**: Namespace-scoped CR defining which model server to use (vLLM, TGI, Caikit)
- **ClusterServingRuntime**: Cluster-scoped equivalent
- Runtime must support the model format (ONNX, PyTorch, SafeTensors, etc.)
- Misconfigured runtime = InferenceService stays NotReady

## Known Failure Patterns

### Product Bugs
- `ServingRuntime.*not.*found|runtime.*not.*supported` → Runtime CR missing or name mismatch
- `ClusterServingRuntime.*missing` → Cluster-scoped runtime not installed
- `model.*format.*not.*supported` → Runtime doesn't support this model format

### Infrastructure Issues
- Runtime pod `CrashLoopBackOff` → Container image issue or missing config
- `ImagePullBackOff` on runtime image → Registry auth or image not found

## Diagnosis Steps

1. Read test failure logs
2. Check if ServingRuntime/ClusterServingRuntime exists and matches ISVC spec
3. Verify model format compatibility
4. If cluster access available, run `scripts/inspect_runtimes.sh`
5. Classify and output structured JSON
