---
name: debugger-trustyai
description: >
  Use when analyzing "trustyai" / "TrustyAI" component failures from RHOAI test results.
  Covers model explainability service, metric collection, TrustyAI operator,
  and fairness/bias monitoring.
allowed-tools: Bash(*/debugger-trustyai/scripts/*.sh:*),Bash(*/debugger-trustyai/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# TrustyAI Debugger

## RP Component
This skill handles the `trustyai` / `TrustyAI` component from ReportPortal launches.

## Key Concepts

- Model explainability service
- Requires TrustyAI operator installed
- May need time to collect inference data before explanations work
- Depends on model serving being healthy first

## Known Failure Patterns

### Product Bugs
- `TrustyAI.*not.*ready|trustyai.*service.*unavailable` → Operator/service failure
- `explanation.*failed|fairness.*metric.*error` → TrustyAI computation error

### Infrastructure Issues
- `TrustyAI.*operator.*not.*installed` → Operator missing
- `connection.*refused.*trustyai` → Service pod not running

### Test Automation Issues
- Short timeout for metric collection → Needs inference data first
- Tests run before enough inference data collected → Expected delay

## Diagnosis Steps

1. Read test failure logs
2. Check if TrustyAI operator/service is installed and healthy
3. If cluster access available, run `scripts/inspect_trustyai.sh`
4. Verify model serving is healthy (TrustyAI depends on it)
5. Classify and output structured JSON
