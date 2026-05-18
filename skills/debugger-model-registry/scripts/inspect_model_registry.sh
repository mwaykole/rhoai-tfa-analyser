#!/usr/bin/env bash
set -euo pipefail
NS="${1:-redhat-ods-applications}"

echo "=== ModelRegistry CRs ==="
oc get modelregistries -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Registry Pods ==="
oc get pods -n "$NS" -l app=model-registry -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Database Pods ==="
oc get pods -n "$NS" -l app=mariadb -o json 2>/dev/null || echo '{"items":[]}'
oc get pods -n "$NS" -l app=postgresql -o json 2>/dev/null || echo '{"items":[]}'
