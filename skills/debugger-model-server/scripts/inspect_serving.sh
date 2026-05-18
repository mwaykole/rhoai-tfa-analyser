#!/usr/bin/env bash
# Read-only inspection of model serving resources.
# Usage: inspect_serving.sh [namespace]
set -euo pipefail

NS="${1:-redhat-ods-applications}"

echo "=== InferenceServices ==="
oc get isvc -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Pods (model serving) ==="
oc get pods -n "$NS" -l component=predictor -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Events ==="
oc get events -n "$NS" --sort-by=.lastTimestamp 2>/dev/null | tail -30 || true
