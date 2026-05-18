#!/usr/bin/env bash
set -euo pipefail
NS="${1:-redhat-ods-applications}"

echo "=== ServingRuntimes ==="
oc get servingruntimes -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== ModelMesh Pods ==="
oc get pods -n "$NS" -l modelmesh-service -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Predictors ==="
oc get predictors -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'
