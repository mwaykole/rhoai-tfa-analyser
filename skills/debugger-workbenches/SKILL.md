---
name: debugger-workbenches
description: >
  Use when analyzing "workbenches" / "Workbenches" component failures from
  RHOAI test results. Covers Jupyter notebook workbenches, PVC provisioning,
  large image pulls, and notebook lifecycle.
allowed-tools: Bash(*/debugger-workbenches/scripts/*.sh:*),Bash(*/debugger-workbenches/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Workbenches Debugger

## RP Component
This skill handles the `workbenches` / `Workbenches` component from ReportPortal launches.

## Key Concepts

- Jupyter notebook workbench tests
- Image pull for large workbench images can be slow (10+ min)
- PVC provisioning can cause delays
- Workbench pods run in `rhods-notebooks` namespace

## Known Failure Patterns

### Infrastructure Issues
- `ImagePullBackOff|ErrImagePull` → Large image, slow registry, or auth issue
- `PVC.*pending|PVC.*bound.*failed` → Storage class issue or quota exceeded
- `Insufficient.*cpu|Insufficient.*memory` → Resource constraints

### Product Bugs
- `Notebook.*not.*ready` → Notebook controller failed to create workbench
- `notebook.*failed.*start` → Workbench startup error

### Test Automation Issues
- Short timeout for large image pull → Needs 10+ min for multi-GB images
- `TimeoutExpiredError` with < 600s for workbench → Too short

## Timeout Expectations

| Operation | Expected Duration |
|---|---|
| Image pull (small) | 10s-1 min |
| Image pull (large workbench) | 5-15 min |
| PVC provisioning | 30s-5 min |
| Workbench ready | 2-10 min (depends on image size) |

## Diagnosis Steps

1. Read test failure logs
2. Check if it's image pull, PVC, or actual workbench error
3. If cluster access available, run `scripts/inspect_workbenches.sh`
4. Check notebook CR status and pod events
5. Classify and output structured JSON
