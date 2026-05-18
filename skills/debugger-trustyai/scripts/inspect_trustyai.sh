#!/usr/bin/env bash
set -euo pipefail
NS="${1:-redhat-ods-applications}"

echo "=== TrustyAI Services ==="
oc get trustyaiservices -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== TrustyAI Pods ==="
oc get pods -n "$NS" -l app=trustyai -o json 2>/dev/null || echo '{"items":[]}'
