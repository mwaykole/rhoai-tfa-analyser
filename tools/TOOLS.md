# TFA Plugin Tools

Shared utilities and standalone clients used by debugger skills.

## common.sh

Shared shell utilities. Source from any inspect script:

```bash
source "$(dirname "$0")/../../tools/common.sh"
```

Functions:
- `tfa_check_oc_login` — verify oc is authenticated
- `tfa_oc_get` — safe `oc get` that returns empty JSON on failure
- `tfa_log` — log to stderr (won't pollute JSON stdout)
- `tfa_timestamp` — ISO timestamp

## rp-client/

Standalone ReportPortal API client.

```bash
# Install dependencies
./tools/rp-client/install.sh

# Use from Python
from tools.rp_client import RPClient
```

Environment variables:
- `RP_URL` — ReportPortal server URL
- `RP_PROJECT` — Project name
- `RP_USERNAME` / `RP_PASSWORD` — Credentials
- `RP_TOKEN` — API token (alternative)

## jenkins-client/

Jenkins API client for build log extraction and failure analysis.

```bash
# Install dependencies
./tools/jenkins-client/install.sh

# CLI usage — get build info
python tools/jenkins-client/jenkins_client.py --build 1234 --info

# Get failed stages
python tools/jenkins-client/jenkins_client.py --build 1234 --failed-stages

# Extract error context from console log
python tools/jenkins-client/jenkins_client.py --build 1234 --errors

# Get log for a specific stage
python tools/jenkins-client/jenkins_client.py --build 1234 --stage-log "Run Tests"

# Full console output
python tools/jenkins-client/jenkins_client.py --build 1234 --console

# List build artifacts
python tools/jenkins-client/jenkins_client.py --build 1234 --artifacts
```

Environment variables:
- `JENKINS_URL` — Jenkins server URL
- `JENKINS_USER` — Jenkins username
- `JENKINS_TOKEN` — Jenkins API token
- `JENKINS_JOB` — Default job name (optional, can pass via `--job`)

Python usage:

```python
from tools.jenkins_client import JenkinsClient

client = JenkinsClient()
log = client.get_console_log(build_number=1234)
errors = client.extract_error_context(log)
stages = client.get_failed_stages(build_number=1234)
```

## must-gather/

Must-gather artifact parser for OpenShift cluster state.

```bash
# Install dependencies
./tools/must-gather/install.sh

# Parse must-gather directory
python tools/must-gather/must_gather_parser.py /path/to/must-gather
```
