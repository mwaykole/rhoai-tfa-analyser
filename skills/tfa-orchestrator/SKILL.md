---
name: tfa-orchestrator
description: >
  Use when analyzing RHOAI/ODH test failures. The user's prompt is free-form — it
  can reference a ReportPortal launch ID, a ReportPortal URL, a file path, a directory
  of logs, a Jenkins build, or any combination. Parse the prompt to determine the input
  source and act accordingly. Trigger phrases: "analyze launch", "analyze failures",
  "analyze /path/to/logs", "debug test failures", "classify failures", "tfa analyze".
allowed-tools: mcp__reportportal__rp_get_launch,mcp__reportportal__rp_list_launches,mcp__reportportal__rp_list_test_items,mcp__reportportal__rp_get_test_item,mcp__reportportal__rp_list_logs,mcp__reportportal__rp_search_logs,mcp__reportportal__rp_update_test_item_issues,Bash(*/tfa-orchestrator/scripts/*.py:*),Bash(*/tfa-orchestrator/scripts/*.sh:*),Bash(*/tools/jenkins-client/*.py:*),Bash(*/tools/must-gather/*.py:*),Bash(*/architecture-reference/scripts/*.py:*),Read
---

# TFA Orchestrator

The orchestrator coordinates the full test failure analysis pipeline.

## Prompt Interpretation

The user's prompt is **free-form**. Parse it to determine the input source:

| User says | Input source | How to handle |
|---|---|---|
| `Analyze launch 10748` | RP launch ID | MCP: `rp_get_launch(launch_id="10748")` then `rp_list_test_items(launch_id="10748", status="FAILED")` |
| `Analyze https://reportportal.example.com/...launches/all/10748` | RP URL | Extract launch ID from URL, use MCP tools |
| `Analyze /workspace/logs/kserve-test.log` | File path | Read the file directly |
| `Analyze all logs in /var/jenkins/results/` | Directory | List and read log files in the directory |
| `Analyze launch 10748 Model_server failures` | RP + component filter | MCP: get launch → list SUITE items → find matching suite → list FAILED items under that suite |
| `Analyze /path/to/test.log for kserve failures` | File + component hint | Read the file, route to debugger-kserve |
| `Analyze Jenkins build 542 failures` | Jenkins build | `tools/jenkins-client/jenkins_client.py --build 542 --errors` |

The user may provide any path — Jenkins workspace, mounted volume, local file — just read
whatever path they give. No assumptions about mount points.

## Flow

1. **Parse prompt** — Determine input source(s) and optional component filter
2. **Load memory** — Read `memory/orchestrator/learnings.json` for known correlations
3. **Retrieve few-shot examples** — For each failure being classified, first search memory:
   - Run `scripts/retrieve_examples.py --error "<key_error>" --test-name "<test_name>" [--component <name>] --top-k 5`
   - If past similar failures exist, use them as reference when classifying
   - Higher hit_count examples are more reliable (validated across multiple runs)
4. **Gather failure data** — Based on what the prompt asks for:
   - RP launch → **Try MCP first, fall back to script:**
     - **If MCP available** (local/Cursor mode): use `rp_get_launch`, `rp_list_test_items`, `rp_list_logs`
     - **If MCP unavailable** (container mode): use `scripts/fetch_rp_failures.py --launch-id <ID> [--component <name>]`
     - Either way the data shape is the same: launch metadata, suites, failed items with logs
   - File path → Read the file at the given path
   - Directory → List and read log files in the directory
   - Jenkins build → `tools/jenkins-client/jenkins_client.py --build <NUM> --errors`
   - Multiple sources → Gather from all of them
5. **Cluster health** (if `oc` is logged in) — Run `scripts/cluster_health.sh` (read-only)
6. **Detect component** — Determine from:
   - Explicit mention in the prompt (e.g., "for kserve failures", "Model_server")
   - RP component field (if from ReportPortal)
   - Log content patterns (see Component Detection table below)
   - Run `scripts/detect_component.py` with the detected component name
   - If ambiguous, analyze for multiple components
7. **Load architecture context** — Look up component architecture:
   - Run `skills/architecture-reference/scripts/arch_lookup.py --component <name> --version <ver> --section all`
   - Provides CRDs, ports, RBAC, dependencies, data flows for the component
   - Also check `--overlays --component <name>` for recent corrections
   - Use `--skip-sync` on subsequent lookups within the same run
8. **Route to debugger** — `scripts/detect_component.py` maps the component name to a skill:
   - Input: component name (e.g., `Model_server`, `kserve`, `Pipelines`)
   - Output: skill directory name (e.g., `debugger-model-server`, `debugger-kserve`)
   - Falls back to `debugger-generic` for unrecognized components
9. **Invoke debugger** — Invoke the matched `debugger-*` skill with all gathered context
   - Debugger reads `memory/components/<name>/learnings.json` before analysis
   - Debugger uses architecture context to validate expected CRDs, ports, RBAC
   - Debugger writes new discoveries after analysis
10. **Collect results** — Aggregate all classifications into a JSON array
11. **Validate results** — Enforce schema before reporting:
    - Run `scripts/validate_results.py --results /tmp/tfa_results.json --fix`
    - Normalizes classification names, clamps confidence to 0-1, fills missing RP defect codes
    - Exits non-zero if unfixable errors found (missing root_cause, invalid classification)
12. **Generate report** — Produce HTML report:
    - Run `scripts/generate_report.py --results /tmp/tfa_results.json --output /tmp/tfa_report.html [--launch-id <ID>] [--launch-name <name>]`
    - The HTML report has summary charts, severity breakdown, and detailed per-failure cards
13. **Post to RP** (if the prompt requests it):
    - **MCP**: `rp_update_test_item_issues(issues='[{"testItemId": <ID>, "issue": {"issueType": "<code>", "comment": "<root_cause>"}}]')`
    - **Script fallback**: `scripts/post_rp_results.py --results /tmp/tfa_results.json`
14. **Store run + learnings** — Persist results for future few-shot retrieval:
    - Run `scripts/store_run.py --results /tmp/tfa_results.json [--launch-id <ID>]`
    - This writes the run summary to `memory/orchestrator/run_history.json`
    - Each classification is stored as a learning in the matching component's memory
    - Duplicate patterns have their `hit_count` incremented instead of creating new entries
    - High hit_count learnings are retrieved by `retrieve_examples.py` on future runs

### Component Detection from Log Content

When the user doesn't specify a component, detect from log patterns:

| Log Pattern | Component |
|---|---|
| `InferenceService`, `serving.kserve.io`, `kserve-controller` | `kserve` |
| `LLMInferenceService`, `LeaderWorkerSet`, `llm-d` | `llmd` |
| `ServingRuntime`, `modelmesh-serving`, `model-mesh` | `modelmesh` |
| `vllm`, `text-generation-inference`, `caikit` | `model_server` |
| `DataSciencePipelinesApplication`, `dspa`, `argo` | `pipelines` |
| `ModelRegistry`, `model-registry` | `model_registry` |
| `Notebook`, `jupyter`, `workbench` | `workbenches` |
| `odh-dashboard`, `rhods-dashboard` | `dashboard` |
| `TrustyAI`, `trustyai-service` | `trustyai` |
| `DSCInitialization`, `DataScienceCluster`, `rhods-operator` | `rhoai_operators` |
| `RayCluster`, `Kueue`, `CodeFlare`, `AppWrapper` | `distributed` |
| `OGXOrchestrator`, `ogx-k8s-operator`, `llama-stack` | `llama_stack` |

## Multi-Component Analysis

When no component filter is given, iterate all failed components:

1. Get all suites: MCP `rp_list_test_items` or `scripts/fetch_rp_failures.py --launch-id <ID> --list-components --failed-only`
2. For each failed suite:
   - Map suite name to debugger skill via `scripts/detect_component.py "<suite_name>"`
   - Get failures: MCP `rp_list_test_items(status="FAILED", parent_id=...)` or `scripts/fetch_rp_failures.py --launch-id <ID> --component "<name>"`
   - Invoke the matched debugger skill with all gathered context

## Component Routing Table

| RP Component Name | Debugger Skill Directory |
|---|---|
| `Model_server` / `Model Server` | `debugger-model-server` |
| `kserve` | `debugger-model-server/debugger-kserve` |
| `llmd` | `debugger-model-server/debugger-llmd` |
| `modelmesh` | `debugger-model-server/debugger-modelmesh` |
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
