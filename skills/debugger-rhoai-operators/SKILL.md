---
name: debugger-rhoai-operators
description: >
  Use when analyzing "rhoai_operators" component failures from RHOAI test results.
  Covers DataScienceCluster (DSC), DSCInitialization (DSCI), RHOAI operator
  reconciliation, and component health management.
allowed-tools: Bash(*/debugger-rhoai-operators/scripts/*.sh:*),Bash(*/debugger-rhoai-operators/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# RHOAI Operators Debugger

## RP Component
This skill handles the `rhoai_operators` component from ReportPortal launches.

## Key Concepts

- RHOAI operator manages DataScienceCluster (DSC) and DSCInitialization (DSCI)
- DSC `.status.conditions` shows which components are Ready/Degraded
- If DSC component is degraded, all tests for that component will fail
- Operator pod in `redhat-ods-operator` namespace
- Component pods in `redhat-ods-applications` namespace

## Namespaces

| Namespace | Contents |
|---|---|
| `redhat-ods-operator` | RHOAI operator pods |
| `redhat-ods-applications` | Component deployments (dashboard, model controller) |
| `redhat-ods-monitoring` | Monitoring stack |
| `rhods-notebooks` | Workbench/notebook pods |

## Known Failure Patterns

### Product Bugs
- `DSC.*not.*ready|DataScienceCluster.*degraded` → Operator failed to reconcile
- `component.*degraded|component.*not.*available` → Specific component unhealthy
- `reconcile.*error|controller.*failed` → Operator controller crash
- `operator.*panic` → Critical operator bug

### Infrastructure Issues
- `operator.*not.*ready` → Operator installation incomplete
- `CRD.*not.*found` → Operator CRD missing
- `CSV.*failed|ClusterServiceVersion.*failed` → OLM installation issue

### Test Automation Issues
- Short timeout waiting for DSC reconciliation → Needs 2-5 min

## Diagnosis Steps

1. Read test failure logs
2. Check DSC/DSCI status conditions for degraded components
3. If cluster access available, run `scripts/inspect_operators.sh`
4. Check operator pod logs for reconciliation errors
5. Determine if it's operator bug, missing CRD, or cluster issue
6. Classify and output structured JSON
