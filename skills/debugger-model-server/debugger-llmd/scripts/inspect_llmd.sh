#!/usr/bin/env bash
# Read-only inspection of LLMD resources.
set -euo pipefail

NS="${1:-redhat-ods-applications}"

echo "=== LLMInferenceServices ==="
oc get llminferenceservices -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== LeaderWorkerSets ==="
oc get leaderworkersets -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Leader/Worker Pods ==="
oc get pods -n "$NS" -l leaderworkerset.sigs.k8s.io/name -o json 2>/dev/null || echo '{"items":[]}'

echo "=== Events ==="
oc get events -n "$NS" --sort-by=.lastTimestamp 2>/dev/null | tail -30 || true
