#!/usr/bin/env bash
set -euo pipefail

echo "=== DataScienceCluster ==="
oc get dsc -o json 2>/dev/null || echo '{"items":[]}'

echo "=== DSCInitialization ==="
oc get dsci -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Operator Pods ==="
oc get pods -n redhat-ods-operator -o json 2>/dev/null || echo '{"items":[]}'

echo "=== ClusterServiceVersions ==="
oc get csv -n redhat-ods-operator -o json 2>/dev/null || echo '{"items":[]}'
