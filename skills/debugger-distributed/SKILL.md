---
name: debugger-distributed
description: >
  Use when analyzing "Distributed" component failures from RHOAI test results.
  Covers Kueue batch scheduling, CodeFlare distributed ML orchestration,
  Ray/KubeRay distributed execution, and resource queue management.
allowed-tools: Bash(*/debugger-distributed/scripts/*.sh:*),Bash(*/debugger-distributed/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Distributed Debugger

## RP Component
This skill handles the `Distributed` component from ReportPortal launches.

## Components

| Component | Description | Common Failures |
|---|---|---|
| Kueue | Kubernetes batch scheduler | Queue admission, ResourceFlavor mismatch |
| CodeFlare | Distributed ML orchestration | Cluster creation timeout, worker failures |
| Ray | Distributed execution framework | Head node failure, worker OOM |
| KubeRay | Ray on Kubernetes operator | RayCluster not ready, GCS failure |

## Known Failure Patterns

### Product Bugs
- `RayCluster.*not.*ready` → KubeRay operator failed to create cluster
- `CodeFlare.*failed|AppWrapper.*failed` → CodeFlare orchestration error
- `Kueue.*admission.*failed` → Queue configuration error

### Infrastructure Issues
- `Insufficient.*cpu|Insufficient.*memory` → Not enough resources for workers
- `OOMKilled` on Ray worker → Worker needs more memory
- `head.*node.*failure` → Ray head pod scheduling issue
- `ResourceFlavor.*mismatch` → Kueue resource configuration wrong

### Test Automation Issues
- Short timeout for distributed job startup → Ray clusters need 5-10 min
- Timeout for batch job completion → Complex jobs need 10-30 min

## Diagnosis Steps

1. Read test failure logs
2. Check which distributed component is failing (Kueue, CodeFlare, Ray)
3. If cluster access available, run `scripts/inspect_distributed.sh`
4. Check resource availability for workers
5. Classify and output structured JSON
