#!/usr/bin/env bash
set -euo pipefail
NS="${1:-redhat-ods-applications}"

echo "=== RayClusters ==="
oc get rayclusters -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Kueue Workloads ==="
oc get workloads -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Kueue Queues ==="
oc get clusterqueues -o json 2>/dev/null || echo '{"items":[]}'
oc get localqueues -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== AppWrappers ==="
oc get appwrappers -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'
