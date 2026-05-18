#!/usr/bin/env bash
# Read-only cluster health check for RHOAI/ODH.
# Outputs JSON summary of cluster state.
# STRICT: Only read operations allowed.

set -euo pipefail

check_oc_login() {
    if ! oc whoami &>/dev/null; then
        echo '{"status": "not_logged_in", "error": "oc not authenticated"}' 
        exit 0
    fi
}

get_node_status() {
    oc get nodes -o json 2>/dev/null | \
        python3 -c "
import json, sys
data = json.load(sys.stdin)
nodes = []
for node in data.get('items', []):
    name = node['metadata']['name']
    conditions = {c['type']: c['status'] for c in node['status'].get('conditions', [])}
    ready = conditions.get('Ready', 'Unknown')
    nodes.append({'name': name, 'ready': ready})
json.dump(nodes, sys.stdout)
" 2>/dev/null || echo "[]"
}

get_dsc_status() {
    oc get dsc -o json 2>/dev/null | \
        python3 -c "
import json, sys
data = json.load(sys.stdin)
items = []
for dsc in data.get('items', []):
    name = dsc['metadata']['name']
    conditions = dsc.get('status', {}).get('conditions', [])
    items.append({'name': name, 'conditions': conditions})
json.dump(items, sys.stdout)
" 2>/dev/null || echo "[]"
}

get_operator_status() {
    oc get pods -n redhat-ods-operator -o json 2>/dev/null | \
        python3 -c "
import json, sys
data = json.load(sys.stdin)
pods = []
for pod in data.get('items', []):
    name = pod['metadata']['name']
    phase = pod['status'].get('phase', 'Unknown')
    pods.append({'name': name, 'phase': phase})
json.dump(pods, sys.stdout)
" 2>/dev/null || echo "[]"
}

main() {
    check_oc_login

    echo "{"
    echo "  \"cluster_logged_in\": true,"
    echo "  \"nodes\": $(get_node_status),"
    echo "  \"dsc\": $(get_dsc_status),"
    echo "  \"operator_pods\": $(get_operator_status)"
    echo "}"
}

main
