#!/usr/bin/env bash
set -euo pipefail
NS="${1:-redhat-ods-applications}"

echo "=== PipelineRuns ==="
oc get pipelineruns -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Workflows ==="
oc get workflows -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== DSP Pods ==="
oc get pods -n "$NS" -l app.kubernetes.io/part-of=data-science-pipelines -o json 2>/dev/null || echo '{"items":[]}'
