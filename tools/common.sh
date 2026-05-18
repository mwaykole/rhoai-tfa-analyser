#!/usr/bin/env bash
# Shared utilities for TFA plugin scripts.
# Source this file: source "$(dirname "$0")/../../tools/common.sh"

set -euo pipefail

# Check if oc is authenticated
tfa_check_oc_login() {
    if ! command -v oc &>/dev/null; then
        echo "Error: oc binary not found" >&2
        return 1
    fi
    if ! oc whoami &>/dev/null; then
        echo "Error: not logged into OpenShift cluster" >&2
        return 1
    fi
    return 0
}

# Output JSON to stdout (helper for scripts)
tfa_json_output() {
    local key="$1"
    local value="$2"
    echo "{\"${key}\": ${value}}"
}

# Get current timestamp in ISO format
tfa_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Safe oc get that returns empty JSON on failure
tfa_oc_get() {
    oc get "$@" -o json 2>/dev/null || echo '{"items":[]}'
}

# Log message to stderr (doesn't pollute JSON stdout)
tfa_log() {
    echo "[TFA $(tfa_timestamp)] $*" >&2
}
