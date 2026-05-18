#!/usr/bin/env bash
# Read-only inspection of KServe resources.
set -euo pipefail

NS="${1:-redhat-ods-applications}"

echo "=== InferenceServices ==="
oc get isvc -A -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Knative Services ==="
oc get ksvc -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Revisions ==="
oc get revisions -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== ServingRuntimes ==="
oc get servingruntimes -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'
