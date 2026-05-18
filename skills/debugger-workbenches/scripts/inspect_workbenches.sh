#!/usr/bin/env bash
set -euo pipefail
NS="${1:-rhods-notebooks}"

echo "=== Notebooks ==="
oc get notebooks -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Workbench Pods ==="
oc get pods -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== PVCs ==="
oc get pvc -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Events ==="
oc get events -n "$NS" --sort-by=.lastTimestamp 2>/dev/null | tail -20 || true
