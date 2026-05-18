#!/usr/bin/env bash
set -euo pipefail
NS="${1:-redhat-ods-applications}"

echo "=== LlamaStack Resources ==="
oc get llamastacks -n "$NS" -o json 2>/dev/null || echo '{"items":[]}'

echo "=== LlamaStack Pods ==="
oc get pods -n "$NS" -l app.kubernetes.io/part-of=llama-stack -o json 2>/dev/null || echo '{"items":[]}'

echo "=== GPU Nodes ==="
oc get nodes -l nvidia.com/gpu.present=true -o json 2>/dev/null || echo '{"items":[]}'
