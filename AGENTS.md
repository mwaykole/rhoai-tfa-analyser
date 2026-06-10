## Learned User Preferences

- Implement directly when asked; do not switch to Plan mode unless the user explicitly wants design discussion.
- Place RHOAI architecture under `skills/architecture-reference`; clone or pull `architecture-context` fresh on every analysis run.
- TFA prompts are free-form: accept RP launch IDs, RP URLs, file paths, directories, or Jenkins build references without rigid input modes.
- Do not hardcode mount paths like `/mnt/test.log`; use whatever path the user provides (often a Jenkins workspace path).
- Scope RP/GitLab automation to model_server failures only (`tests/model_serving/model_server/` — kserve, llmd); exclude `tests/model_serving/model_runtime/`.
- Nest serving sub-skills inside `skills/debugger-model-server/` (`debugger-kserve`, `debugger-llmd`, `debugger-modelmesh`) and mirror that hierarchy in `memory/components/`.
- Do not add `ci/` pipeline definitions; DevOps owns Jenkins/Tekton integration; this repo ships the container image and plugin only.
- Bundle Jenkins/ReportPortal MCP servers in the container image under `mcps/`; use ReportPortal MCP for all RP operations (no custom HTTP clients).
- Sub-skills invoked by a parent debugger should reuse failure data already gathered; do not re-fetch from RP.
- Run analysis and integration tests via podman (`tfa-claudio` image); scheduled production automation runs on GitLab CI runners, not the user's laptop.
- Do not push to GitHub or GitLab remotes unless explicitly instructed; local commits only by default.

## Learned Workspace Facts

- `rhoai-tfa-analyser` is a Claude Code plugin: orchestrator + component debugger skills + `architecture-reference`.
- `architecture-context/` is a runtime git clone (gitignored); entrypoint pre-syncs in containers; `arch_lookup.py` must run before classification with version-specific docs via `RHOAI_VERSION` (from RP `RHOAI Version`/`ODH Version` attrs; maps e.g. `2.25.7` → `rhoai-2.25`, `3.5.0-ea.2` → `rhoai-3.5-ea.1`).
- Serving stack routing and memory scripts resolve `kserve`/`llmd`/`modelmesh` via `SUB_COMPONENT_MAP` to nested `debugger-model-server/debugger-*` paths.
- `RP_URL` / `RP_PROJECT` are required only for ReportPortal analysis; local log analysis needs Vertex AI credentials only.
- Container entrypoint invokes `claude -p --dangerously-skip-permissions`; writes `~/.claude.json` embedding bundled `mcps/rhoai-jenkins-mcp` and `mcps/mcp-rp`; plugin dir defaults to `/home/claudio/tfa-plugin`.
- Plugin changes (`entrypoint.sh`, skills, `arch_lookup.py`) require rebuilding and pushing `quay.io/mwaykole/tfa-claudio:latest` for GitLab CI to pick them up.
- `fetch_rp_failures.py` and `post_rp_results.py` are documentation stubs; orchestrator SKILL.md documents MCP tool usage instead.
- Analysis output: component-specific HTML via `generate_report.py` (`TFA_REPORT_DIR/tfa_report.html`) with collapsible sections and index; live log at `TFA_LOG_FILE` (default `/tmp/analysis.log`).
- Entrypoint post-analysis pipeline: `validate_results.py` → `generate_report.py` → `store_run.py`; `retrieve_examples.py` injects similar past failures from memory before classification.
- `RP_TOKEN` bearer token is the preferred ReportPortal auth over username/password.
- Jenkins URLs: orchestrator prefers `mcp__rhoai-jenkins__get_build_log`, falls back to `tools/jenkins-client/jenkins_client.py` (`JENKINS_URL`/`JENKINS_USER`/`JENKINS_TOKEN`).
- Companion GitLab repo `tfa_automation_gitlab` (`gitlab.cee.redhat.com/mwaykole/rhoai-tfa-analysis`) checks RP every 30 min for model_server failures, deduplicates via `analyzed_launches.json`, gates with `check_rp.py` → `monitor_rp.py` (`NEW_LAUNCHES` dotenv; no cross-pipeline API triggers), posts defect-type details back to RP, sends Slack alerts for `product_bug`/`automation_bug` via `SLACK_WEBHOOK_URL` CI variable, and publishes `report/RHOAI-{version}/{cluster}_{cloud}/` with `tfa_report.html`, `details.md`, and `summary.md`.
