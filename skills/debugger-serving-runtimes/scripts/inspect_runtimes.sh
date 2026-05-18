#!/usr/bin/env bash
set -euo pipefail
NS="${1:-redhat-ods-applications}"

echo "=== ServingRuntimes (namespace) ==="
oc get servingruntimes -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== ClusterServingRuntimes ==="
oc get clusterservingruntimes -o json 2>/dev/null || echo '{"items":[]}'
