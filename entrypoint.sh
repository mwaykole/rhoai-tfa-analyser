#!/usr/bin/env bash
set -euo pipefail

# Validate required ReportPortal env vars
: "${RP_URL:?RP_URL is required}"
: "${RP_PROJECT:?RP_PROJECT is required}"

# Configure Vertex AI (instead of Anthropic API key)
export CLAUDE_CODE_USE_VERTEX="${CLAUDE_CODE_USE_VERTEX:-1}"
export CLOUD_ML_PROJECT_ID="${CLOUD_ML_PROJECT_ID:?GCP project ID required}"
export ANTHROPIC_VERTEX_REGION="${ANTHROPIC_VERTEX_REGION:-us-east5}"

# If GOOGLE_APPLICATION_CREDENTIALS is set, verify file exists
if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
    [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]] || \
        { echo "Error: GOOGLE_APPLICATION_CREDENTIALS file not found: $GOOGLE_APPLICATION_CREDENTIALS"; exit 1; }
fi

# Determine the prompt: first arg, or TFA_PROMPT env var
PROMPT="${1:-${TFA_PROMPT:-}}"
if [[ -z "$PROMPT" ]]; then
    echo "Error: No prompt provided. Pass as argument or set TFA_PROMPT env var."
    echo "Usage: docker run tfa-claudio:latest \"Analyze launch 10748 Model_server failures\""
    exit 1
fi

exec claude --prompt "$PROMPT"
