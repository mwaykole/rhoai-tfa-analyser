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
export ANTHROPIC_VERTEX_PROJECT_ID="${CLOUD_ML_PROJECT_ID}"
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
ARCH_LOOKUP="${PLUGIN_DIR}/skills/architecture-reference/scripts/arch_lookup.py"

# Resolve architecture version: env var > extract from prompt > fallback to newest
RHOAI_VERSION="${RHOAI_VERSION:-}"
if [[ -z "$RHOAI_VERSION" ]]; then
    # Try extracting version from the prompt (e.g. "RHOAI version 2.25" or "3.5-ea.1")
    RHOAI_VERSION=$(echo "$PROMPT" | grep -oP '(?i)(?:rhoai|version)\s+(\d+\.\d+(?:[.-]\S+)?)' | grep -oP '\d+\.\d+(?:[.-]\S+)?' | head -1)
fi
if [[ -z "$RHOAI_VERSION" ]]; then
    # Try extracting from Jenkins URL path (e.g. /job/2.25/ or /job/3.5-ea.1/)
    RHOAI_VERSION=$(echo "$PROMPT" | grep -oP '/job/(\d+\.\d+(?:[.-][a-z0-9.]+)?)/' | grep -oP '\d+\.\d+(?:[.-][a-z0-9.]+)?' | head -1)
fi
ARCH_VERSION="${RHOAI_VERSION:-newest}"
log "Architecture version resolved: ${ARCH_VERSION}"

# Append instructions for classification, validation, report, and memory storage
FULL_PROMPT="${PROMPT}

IMPORTANT ANALYSIS STEPS — follow in order:

STEP 1: Load architecture context BEFORE classifying.
For each component being analyzed, run the architecture lookup to understand CRDs, ports,
RBAC, dependencies, and data flows. This context is critical for accurate classification.
The RHOAI version for this analysis is: ${ARCH_VERSION}
- Run: python3 ${ARCH_LOOKUP} --skip-sync --component model_server --version ${ARCH_VERSION} --section all
- Also run: python3 ${ARCH_LOOKUP} --skip-sync --component kserve --version ${ARCH_VERSION} --section all
- If the version is not found, try: python3 ${ARCH_LOOKUP} --skip-sync --version ${ARCH_VERSION} --list-components
  then fall back to --version newest
- Use the architecture data to understand expected behavior, CRD schemas, network topology,
  and dependency chains when diagnosing each failure.
- When a failure involves connectivity/timeout: check network section
- When a failure involves CRD/API errors: check crds section
- When a failure involves permission denied: check rbac section
- When a failure involves missing components: check dependencies section

STEP 2: Check memory for similar past failures BEFORE classifying each failure:
- Run: python3 ${SCRIPTS}/retrieve_examples.py --error '<key_error_text>' --top-k 3
- Use the returned examples as reference for your classification decision.

STEP 3: Classify each failure using architecture context + memory + log evidence.

STEP 4: After classification, you MUST do these steps in order:
1. Write the classification results array to ${REPORT_DIR}/tfa_results.json
2. Run: python3 ${SCRIPTS}/validate_results.py --results ${REPORT_DIR}/tfa_results.json --fix
3. Run: python3 ${SCRIPTS}/generate_report.py --results ${REPORT_DIR}/tfa_results.json --output ${REPORT_DIR}/tfa_report.html
4. Run: python3 ${SCRIPTS}/store_run.py --results ${REPORT_DIR}/tfa_results.json
5. Print each step of your analysis as you go so progress is visible in the live log."

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
