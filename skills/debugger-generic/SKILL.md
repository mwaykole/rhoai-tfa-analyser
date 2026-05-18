---
name: debugger-generic
description: >
  Fallback debugger for any ReportPortal component not matched to a dedicated
  debugger skill. Applies general classification patterns and RHOAI domain
  knowledge to analyze unknown or new components.
allowed-tools: Bash(*/debugger-generic/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Generic Debugger (Fallback)

## RP Component
This skill handles any component not matched by a dedicated debugger.
When a new RP component appears, this skill provides baseline analysis.

## General Classification Patterns

### Product Bugs
- `reconcile.*error|controller.*failed|operator.*panic` → Operator/controller failure
- `no matches for kind` → Missing CRD dependency
- `500.*Internal.*Server.*Error|503.*Service.*Unavailable` → Backend service failure
- `gRPC.*UNAVAILABLE` → Service endpoint failure
- Service never becomes Ready despite generous timeout + healthy cluster → Component broken

### Infrastructure Issues
- `CrashLoopBackOff|container.*crash|exit.*code.*[1-9]` → Container crashing
- `ImagePullBackOff|ErrImagePull` → Image unavailable
- `OOMKilled|Out.*Of.*Memory` → Memory limit exceeded
- `Insufficient.*cpu|Insufficient.*memory` → Resource constraints
- `no.*such.*host|connection.*refused|dial.*tcp.*timeout` → Network/DNS failure
- `nvidia.com/gpu.*Insufficient` → GPU unavailable

### Test Automation Issues
- `TimeoutExpiredError|TimeoutSampler.*exceeded` → Test timeout (check if reasonable)
- `StaleElementReference|ElementNotInteractable` → UI test timing
- `AssertionError` → Assertion failure (could be test or product)
- `fixture.*not.*found` → Test setup issue

### Intermittent Failures
- `Connection reset` → Network flakiness
- `upstream connect error` → Service mesh timing
- Passes on retry → Timing-dependent

## Diagnosis Steps

1. Read test failure logs
2. Match against general patterns above
3. If no pattern matches, analyze log content for clues
4. Check if this might belong to a known component (suggest re-routing)
5. Classify with lower confidence (0.5-0.7) since this is fallback
6. Output structured JSON
7. Store as `new_component` learning if component is truly new

## Notes

- This skill should flag new/unknown components for the orchestrator
- Lower confidence scores (0.5-0.7) since we lack domain-specific knowledge
- Recommend creating a dedicated debugger if component appears frequently
