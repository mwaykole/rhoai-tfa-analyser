---
name: debugger-model-registry
description: >
  Use when analyzing "model_registry" component failures from RHOAI test results.
  Covers Model Registry service, MariaDB/PostgreSQL backend, catalog API,
  and model version management.
allowed-tools: Bash(*/debugger-model-registry/scripts/*.sh:*),Bash(*/debugger-model-registry/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Model Registry Debugger

## RP Component
This skill handles the `model_registry` component from ReportPortal launches.

## Key Concepts

- Requires MariaDB or PostgreSQL backend
- Database connection issues are Infrastructure Issues
- Model catalog API may take 30-60s to become ready

## Known Failure Patterns

### Product Bugs
- `model_catalog_api.*error|registry.*internal.*error` → Registry service bug
- `ModelRegistry.*not.*ready` → Operator reconciliation failure

### Infrastructure Issues
- `mariadb.*connection|postgres.*connection` → Database not ready or credentials wrong
- `connection.*refused.*3306|connection.*refused.*5432` → DB service down
- `timeout.*database` → DB startup too slow

### Test Automation Issues
- `model_catalog_api.*timeout` → API server startup slow, increase wait
- Short timeout for registry readiness → Needs 1-2 min

## Diagnosis Steps

1. Read test failure logs
2. Check if database backend is healthy
3. If cluster access available, run `scripts/inspect_model_registry.sh`
4. Check ModelRegistry CR status conditions
5. Classify and output structured JSON
