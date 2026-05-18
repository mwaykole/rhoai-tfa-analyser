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

## must-gather/

Must-gather artifact parser for OpenShift cluster state.

```bash
# Install dependencies
./tools/must-gather/install.sh

# Parse must-gather directory
python tools/must-gather/must_gather_parser.py /path/to/must-gather
```
