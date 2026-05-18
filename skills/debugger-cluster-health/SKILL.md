---
name: debugger-cluster-health
description: >
  Use when analyzing "cluster_health" component failures from RHOAI test results.
  Covers pre-flight cluster readiness checks, node health, operator status,
  and fundamental infrastructure validation.
allowed-tools: Bash(*/debugger-cluster-health/scripts/*.sh:*),Bash(*/debugger-cluster-health/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Cluster Health Debugger

## RP Component
This skill handles the `cluster_health` component from ReportPortal launches.

## Key Concepts

- Pre-flight checks for cluster readiness
- Failures here indicate fundamental cluster issues
- Should block other component tests if these fail
- If cluster_health fails, expect cascade failures in other components

## Known Failure Patterns

### Infrastructure Issues (most common for this component)
- `node.*NotReady|node.*not.*ready` → Cluster node unhealthy
- `operator.*not.*ready` → Operator installation incomplete or degraded
- `DSC.*not.*ready` → DataScienceCluster resource not reconciled
- `etcd.*unhealthy|api.*server.*error` → Control plane issues
- `certificate.*expired` → Cluster certificate rotation needed

### Product Bugs
- `DSC.*reconcile.*failed` → RHOAI operator bug
- `component.*install.*failed` → Component installation broken

## Cross-Component Impact

When cluster_health fails, inform the orchestrator that downstream components
are likely to fail too. The orchestrator should note this correlation:
- Node NotReady → Model_server, kserve, workbenches will all fail
- DSC not ready → All RHOAI components affected
- Operator not ready → Component-specific features broken

## Diagnosis Steps

1. Read test failure logs
2. Determine severity of cluster issue
3. If cluster access available, run `scripts/inspect_cluster.sh`
4. Check if this is a transient issue (node restart) or persistent
5. Classify (almost always Infrastructure Issue for this component)
6. Output structured JSON with cross-component impact note
