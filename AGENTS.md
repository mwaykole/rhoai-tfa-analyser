## Learned User Preferences

- Implement directly when asked; do not switch to Plan mode unless the user explicitly wants design discussion.
- Place RHOAI architecture integration under `skills/` (as `architecture-reference`), not as a committed submodule.
- Clone or pull `architecture-context` fresh on every analysis run; never rely on a static submodule or stale checkout.
- TFA prompts are free-form: accept RP launch IDs, RP URLs, file paths, directories, or Jenkins build references without rigid input modes.
- Do not hardcode mount paths like `/mnt/test.log`; use whatever path the user provides (often a Jenkins workspace path).
- Nest serving sub-skills inside `skills/debugger-model-server/` (`debugger-kserve`, `debugger-llmd`, `debugger-modelmesh`) and mirror that hierarchy in `memory/components/`.
- Do not add `ci/` pipeline definitions; DevOps owns Jenkins/Tekton integration; this repo ships the container image and plugin only.
- Bundle MCP servers (Jenkins, ReportPortal) inside the container image under `mcps/`; MCI runs must not rely on host-side MCP installs.
- Use the ReportPortal MCP server for all RP operations instead of building custom HTTP clients or fetch/post scripts.
- Sub-skills invoked by a parent debugger should reuse failure data already gathered; do not re-fetch from RP.
- Run analysis and integration tests via podman (`tfa-claudio` image), not directly on the host.
- Do not push to GitHub or GitLab remotes unless explicitly instructed; local commits only by default.

## Learned Workspace Facts

- `rhoai-tfa-analyser` is a Claude Code plugin: orchestrator + component debugger skills + `architecture-reference`.
- `architecture-context/` is a runtime git clone (gitignored); `arch_lookup.py` syncs before queries; entrypoint pre-syncs in containers.
- Serving stack routing and memory scripts resolve `kserve`/`llmd`/`modelmesh` via `SUB_COMPONENT_MAP` to nested `debugger-model-server/debugger-*` paths.
- `RP_URL` / `RP_PROJECT` are required only for ReportPortal analysis; local log analysis needs Vertex AI credentials only.
- Container entrypoint invokes `claude -p --dangerously-skip-permissions`; writes `~/.claude.json` embedding bundled `mcps/rhoai-jenkins-mcp` and `mcps/mcp-rp`; plugin dir defaults to `/home/claudio/tfa-plugin`.
- `fetch_rp_failures.py` and `post_rp_results.py` are documentation stubs; orchestrator SKILL.md documents MCP tool usage instead.
- Analysis output: component-specific HTML via `generate_report.py` (`TFA_REPORT_DIR/tfa_report.html`) with collapsible sections and index; live log at `TFA_LOG_FILE` (default `/tmp/analysis.log`).
- Entrypoint post-analysis pipeline: `validate_results.py` → `generate_report.py` → `store_run.py`.
- `retrieve_examples.py` injects similar past failures from memory as few-shot examples before classification.
- `RP_TOKEN` bearer token is the preferred ReportPortal auth over username/password.
- Jenkins URLs: orchestrator prefers `mcp__rhoai-jenkins__get_build_log`, falls back to `tools/jenkins-client/jenkins_client.py` (`JENKINS_URL`/`JENKINS_USER`/`JENKINS_TOKEN`).
- Production image `quay.io/mwaykole/tfa-claudio:latest`; companion GitLab repo `tfa_automation_gitlab` (`gitlab.cee.redhat.com/mwaykole/rhoai-tfa-analysis`) monitors RP model-server failures (Jenkins URL from launch `Jenkins job url:` description), deduplicates via `analyzed_launches.json`, gates analysis with `check_rp.py` → `monitor_rp.py` using `NEW_LAUNCHES` dotenv (no cross-pipeline API triggers—`CI_JOB_TOKEN` lacks `api` scope), and publishes `report/RHOAI-{version}/{cluster}_{cloud}/` with `tfa_report.html`, `details.md`, and `summary.md`.
