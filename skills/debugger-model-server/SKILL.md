---
name: debugger-model-server
description: >
  Use when analyzing "Model_server" / "Model Server" component failures from
  RHOAI test results. Covers vLLM, TGI, Caikit inference, S3 model downloads,
  GPU/OOM issues, and HuggingFace token problems.
allowed-tools: Bash(*/debugger-model-server/scripts/*.sh:*),Bash(*/debugger-model-server/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# Model Server Debugger

## RP Component
This skill handles the `Model_server` / `Model Server` component from ReportPortal launches.

## Resource Hierarchy

```
InferenceService (ISVC) / LLMInferenceService (LLMISVC)
  └─ Predictor / Transformer / Explainer
       └─ Knative Revision (serverless) OR Deployment (raw)
            └─ Pod(s)
                 └─ Containers: storage-initializer, kserve-container, queue-proxy
```

## Known Failure Patterns

### Infrastructure Issues
- `storage-initializer.*exit.*code|InvalidAccessKeyId|AccessDenied.*S3` → S3 credentials or bucket access
- `OOMKilled|Out.*Of.*Memory` → Model too large for container memory limit
- `nvidia.com/gpu.*Insufficient|no.*GPU.*available` → GPU resources unavailable
- `ImagePullBackOff|ErrImagePull` → Container image unavailable or registry auth failed
- `huggingface.*401|HF_ACCESS_TOKEN|gated.*repo` → HuggingFace token missing for gated model

### Product Bugs
- `InferenceService.*not.*[Rr]eady` → ISVC failed to become ready
- `RevisionFailed|LatestCreatedRevision.*not.*ready` → Model container crashed during startup
- `500.*Internal.*Server.*Error` → Backend service failure
- `inference.*failed|prediction.*error` → Model inference returned error

### Test Automation Issues
- `TimeoutExpiredError` with timeout < 300s → Test wait time too short for model load
- `AssertionError` → Wrong expected value (check which)

## Timeout Expectations

| Operation | Expected Duration |
|---|---|
| Model load (LLMs) | 5-15 minutes |
| Model load (small) | 1-2 minutes |
| Inference request | 30s most, 2-5 min large LLMs |
| Pod ready | 2-5 minutes |
| Cold start (serverless) | 30s-5 min |

## Diagnosis Steps

1. Read the test failure logs (provided by orchestrator)
2. Check if error matches known patterns above
3. If cluster access available, run `scripts/inspect_serving.sh`
4. If must-gather available, run must-gather parser for pod logs
5. Trace the KServe resource chain: ISVC → Predictor → Pod → Container logs
6. Classify: Product Bug, Infrastructure Issue, Test Automation Issue, Intermittent Failure
7. Output structured JSON result

## Output Format

```json
{
  "test_id": "<id>",
  "test_name": "<name>",
  "classification": "product_bug|infrastructure_issue|automation_bug|intermittent|to_investigate",
  "severity": "critical|high|medium|low",
  "confidence": 0.0-1.0,
  "root_cause": "<description>",
  "recommendation": "<action>",
  "rp_defect_type": "pb001|si001|ab001|ab_1kbn5su3gqpdt|ti001"
}
```
