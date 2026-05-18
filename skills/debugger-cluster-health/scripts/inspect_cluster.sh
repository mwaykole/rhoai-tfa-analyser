#!/usr/bin/env bash
set -euo pipefail

echo "=== Nodes ==="
oc get nodes -o json 2>/dev/null || echo '{"items":[]}'

echo "=== ClusterOperators ==="
oc get co -o json 2>/dev/null || echo '{"items":[]}'

echo "=== MachineConfigPools ==="
oc get mcp -o json 2>/dev/null || echo '{"items":[]}'

echo "=== DSC Status ==="
oc get dsc -o json 2>/dev/null || echo '{"items":[]}'

echo "=== DSCI Status ==="
oc get dsci -o json 2>/dev/null || echo '{"items":[]}'
