#!/usr/bin/env bash
set -euo pipefail

# ReportPortal env vars — required only when analyzing RP launches, not local logs
if [[ -n "${RP_URL:-}" ]] && [[ -z "${RP_PROJECT:-}" ]]; then
    echo "Error: RP_URL is set but RP_PROJECT is missing" >&2
    exit 1
fi

# Configure Vertex AI (instead of Anthropic API key)
export CLAUDE_CODE_USE_VERTEX="${CLAUDE_CODE_USE_VERTEX:-1}"
export CLOUD_ML_PROJECT_ID="${CLOUD_ML_PROJECT_ID:-${ANTHROPIC_VERTEX_PROJECT_ID:-${GCP_PROJECT_ID:?GCP project ID required}}}"
export ANTHROPIC_VERTEX_REGION="${ANTHROPIC_VERTEX_REGION:-${CLOUD_ML_REGION:-us-east5}}"

# If GOOGLE_APPLICATION_CREDENTIALS is set, verify file exists
if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
    [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]] || \
        { echo "Error: GOOGLE_APPLICATION_CREDENTIALS file not found: $GOOGLE_APPLICATION_CREDENTIALS"; exit 1; }
fi

# Live log file — stream analysis progress here so callers can tail -f
LOG_FILE="${TFA_LOG_FILE:-/tmp/analysis.log}"
REPORT_DIR="${TFA_REPORT_DIR:-/tmp}"

# Pre-clone architecture-context so it's ready when the analysis starts
PLUGIN_DIR="${TFA_PLUGIN_DIR:-/home/claudio/tfa-plugin}"
ARCH_REPO="${ARCH_CONTEXT_REPO:-https://github.com/mwaykole/architecture-context.git}"
ARCH_BRANCH="${ARCH_CONTEXT_BRANCH:-main}"
ARCH_DIR="${PLUGIN_DIR}/architecture-context"

log() { echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*" | tee -a "$LOG_FILE"; }

: > "$LOG_FILE"
log "TFA Analysis starting"
log "Prompt: ${1:-${TFA_PROMPT:-<none>}}"

if [[ -d "${ARCH_DIR}/.git" ]]; then
    log "Pulling latest architecture-context..."
    git -C "$ARCH_DIR" pull --ff-only origin "$ARCH_BRANCH" 2>/dev/null || \
        git -C "$ARCH_DIR" fetch origin "$ARCH_BRANCH" && \
        git -C "$ARCH_DIR" reset --hard "origin/${ARCH_BRANCH}"
else
    log "Cloning architecture-context (branch: ${ARCH_BRANCH})..."
    git clone --depth=1 --branch "$ARCH_BRANCH" "$ARCH_REPO" "$ARCH_DIR"
fi
log "Architecture context ready."

# Determine the prompt: first arg, or TFA_PROMPT env var
PROMPT="${1:-${TFA_PROMPT:-}}"
if [[ -z "$PROMPT" ]]; then
    log "Error: No prompt provided."
    echo "Examples:"
    echo "  \"Analyze launch 10748 Model_server failures and post results to RP\""
    echo "  \"Analyze /workspace/logs/kserve-test.log for failures\""
    exit 1
fi

SCRIPTS="${PLUGIN_DIR}/skills/tfa-orchestrator/scripts"

# Append instructions for classification, validation, report, and memory storage
FULL_PROMPT="${PROMPT}

IMPORTANT: After classification, you MUST do these steps in order:
1. Write the classification results array to ${REPORT_DIR}/tfa_results.json
2. Run: python3 ${SCRIPTS}/validate_results.py --results ${REPORT_DIR}/tfa_results.json --fix
3. Run: python3 ${SCRIPTS}/generate_report.py --results ${REPORT_DIR}/tfa_results.json --output ${REPORT_DIR}/tfa_report.html
4. Run: python3 ${SCRIPTS}/store_run.py --results ${REPORT_DIR}/tfa_results.json
5. Print each step of your analysis as you go so progress is visible in the live log.

BEFORE classifying each failure, check memory for similar past failures:
- Run: python3 ${SCRIPTS}/retrieve_examples.py --error '<key_error_text>' --top-k 3
- Use the returned examples as reference for your classification decision."

log "Starting Claude analysis..."

log "Configuring MCP servers for Claude Code..."
mkdir -p ~/.claude
cat > ~/.claude.json << EOF
{
  "mcpServers": {
    "mcp__reportportal": {
      "command": "python3",
      "args": ["${PLUGIN_DIR}/mcps/mcp-rp/main.py"],
      "env": {
        "RP_URL": "\${RP_URL:-}",
        "RP_TOKEN": "\${RP_TOKEN:-}",
        "RP_PROJECT": "\${RP_PROJECT:-}",
        "PYTHONPATH": "${PLUGIN_DIR}/mcps/mcp-rp:\${PYTHONPATH:-}"
      }
    },
    "mcp__rhoai-jenkins": {
      "command": "python3",
      "args": ["${PLUGIN_DIR}/mcps/rhoai-jenkins-mcp/main.py"],
      "env": {
        "JENKINS_URL": "\${JENKINS_URL:-}",
        "JENKINS_USER": "\${JENKINS_USER:-}",
        "JENKINS_TOKEN": "\${JENKINS_TOKEN:-}",
        "JENKINS_PASSWORD": "\${JENKINS_TOKEN:-}",
        "PYTHONPATH": "${PLUGIN_DIR}/mcps/rhoai-jenkins-mcp:\${PYTHONPATH:-}"
      }
    }
  }
}
EOF

claude -p --dangerously-skip-permissions --bare --plugin-dir "$PLUGIN_DIR" "$FULL_PROMPT" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

log "Claude analysis completed (exit code: $EXIT_CODE)"

# Post-analysis: validate, report, and store (if Claude didn't do it)
if [[ -f "${REPORT_DIR}/tfa_results.json" ]]; then
    if ! [[ -f "${REPORT_DIR}/tfa_report.html" ]]; then
        log "Running post-hoc validation + report generation..."
        python3 "${SCRIPTS}/validate_results.py" --results "${REPORT_DIR}/tfa_results.json" --fix 2>&1 | tee -a "$LOG_FILE" || true
        python3 "${SCRIPTS}/generate_report.py" --results "${REPORT_DIR}/tfa_results.json" --output "${REPORT_DIR}/tfa_report.html" 2>&1 | tee -a "$LOG_FILE" || true
    fi

    log "Storing run in memory..."
    python3 "${SCRIPTS}/store_run.py" --results "${REPORT_DIR}/tfa_results.json" 2>&1 | tee -a "$LOG_FILE" || true

    log "HTML report: ${REPORT_DIR}/tfa_report.html"
else
    log "Warning: tfa_results.json not found — no report or memory storage"
fi

exit "$EXIT_CODE"
