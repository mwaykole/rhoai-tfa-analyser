---
name: tfa-orchestrator
description: >
  Use when analyzing RHOAI/ODH test failures from ReportPortal. Fetches failures,
  detects the component, routes to the appropriate debugger skill, collects results,
  posts back to RP, and stores learnings. Trigger phrases: "analyze launch",
  "tfa analyze", "classify failures", "debug test failures", "reportportal failures".
allowed-tools: Bash(*/tfa-orchestrator/scripts/*.py:*),Bash(*/tfa-orchestrator/scripts/*.sh:*),Bash(*/tools/*/rp_client.py:*),Bash(*/tools/jenkins-client/*.py:*),Bash(*/tools/must-gather/*.py:*)
---

# TFA Orchestrator

The orchestrator coordinates the full test failure analysis pipeline.

## Flow

1. **Load memory** — Read `memory/orchestrator/learnings.json` for known correlations
2. **Fetch failures** — Run `scripts/fetch_rp_failures.py --launch-id <ID> [--component <name>]`
3. **Fetch Jenkins logs** (if `JENKINS_URL` is set) — Run `tools/jenkins-client/jenkins_client.py --build <NUM> --errors` to extract error context from Jenkins build logs. Use `--failed-stages` to identify which pipeline stages failed.
4. **Cluster health** — If `oc` is logged in, run `scripts/cluster_health.sh` (read-only)
5. **Route to debugger** — `scripts/detect_component.py` maps the RP component name to a skill:
   - Input: RP top-level suite name (e.g., `Model_server`, `kserve`, `Pipelines`)
   - Output: skill directory name (e.g., `debugger-model-server`, `debugger-kserve`)
   - Uses normalization (case, underscores/hyphens/spaces)
   - Falls back to `debugger-generic` for unrecognized components
6. **Invoke debugger** — Invoke the matched `debugger-*` skill with logs + cluster data
   - Debugger reads `memory/components/<name>/learnings.json` before analysis
   - Debugger writes new discoveries after analysis
7. **Collect results** — Aggregate all classifications
8. **Post to RP** — Run `scripts/post_rp_results.py` to push results back to ReportPortal
9. **Store learnings** — Run `scripts/store_learning.py` to persist:
   - New patterns discovered during this run
   - Cross-component correlations detected
   - Run summary appended to `run_history.json`

## Multi-Component Analysis

When no `--component` filter is given, iterate all failed components:

```bash
for component in $(scripts/fetch_rp_failures.py --launch-id 10748 --list-components --failed-only); do
  skill=$(scripts/detect_component.py "$component")
  # Invoke that skill with the component's failures
done
```

## Component Routing Table

| RP Component Name | Debugger Skill Directory |
|---|---|
| `Model_server` / `Model Server` | `debugger-model-server` |
| `kserve` | `debugger-kserve` |
| `llmd` | `debugger-llmd` |
| `modelmesh` | `debugger-modelmesh` |
| `serving_runtimes` | `debugger-serving-runtimes` |
| `llama_stack` | `debugger-llama-stack` |
| `Pipelines` | `debugger-pipelines` |
| `model_registry` | `debugger-model-registry` |
| `workbenches` / `Workbenches` | `debugger-workbenches` |
| `Dashboard` | `debugger-dashboard` |
| `trustyai` / `TrustyAI` | `debugger-trustyai` |
| `rhoai_operators` | `debugger-rhoai-operators` |
| `Distributed` | `debugger-distributed` |
| `cluster_health` | `debugger-cluster-health` |
| *(any other)* | `debugger-generic` |

## Output Format

Each debugger returns a JSON result per failure:

```json
{
  "test_id": "12345",
  "test_name": "test_deploy_model_vllm",
  "classification": "product_bug",
  "severity": "high",
  "confidence": 0.92,
  "root_cause": "LeaderWorkerSet CRD not installed on cluster",
  "recommendation": "Install LWS CRD before deploying LLMD",
  "jira_pattern": "RHOAIENG-*",
  "rp_defect_type": "pb001"
}
```

## Classification Categories

| Category | RP Defect Code | When |
|---|---|---|
| Product Bug | `pb001` | Real defect in RHOAI/KServe component |
| Test Automation Issue | `ab001` | Test code problem (short timeout, bad assertion) |
| Infrastructure Issue | `si001` | Cluster/env issue (pod crash, auth, GPU, OOM) |
| Intermittent Failure | `ab_1kbn5su3gqpdt` | Flaky: passes on retry, race condition |
| No Defect | `nd001` | Expected behavior, test design issue |
| To Investigate | `ti001` | Insufficient evidence for classification |

## Read-Only Cluster Access

All cluster scripts are strictly read-only:
- Allowed: `oc get`, `oc describe`, `oc logs`, `oc adm must-gather`
- Forbidden: `oc delete`, `oc apply`, `oc create`, `oc patch`, `oc edit`, `oc scale`
