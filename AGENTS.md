## Learned User Preferences

- Implement directly when asked; do not switch to Plan mode unless the user explicitly wants design discussion.
- Place RHOAI architecture integration under `skills/` (as `architecture-reference`), not as a committed submodule.
- Clone or pull `architecture-context` fresh on every analysis run; never rely on a static submodule or stale checkout.
- TFA prompts are free-form: accept RP launch IDs, RP URLs, file paths, directories, or Jenkins build references without rigid input modes.
- Do not hardcode mount paths like `/mnt/test.log`; use whatever path the user provides (often a Jenkins workspace path).
- Nest related serving sub-skills inside `skills/debugger-model-server/` (`debugger-kserve`, `debugger-llmd`, `debugger-modelmesh`).
- Mirror skill hierarchy in `memory/components/` (e.g. `model-server/kserve` under the parent component).
- Do not add `ci/` pipeline definitions; DevOps owns Jenkins/Tekton integration; this repo ships the container image and plugin only.
- Use the ReportPortal MCP server for all RP operations instead of building custom HTTP clients or fetch/post scripts.
- Sub-skills invoked by a parent debugger should reuse failure data already gathered; do not re-fetch from RP.

## Learned Workspace Facts

- `rhoai-tfa-analyser` is a Claude Code plugin: orchestrator + component debugger skills + `architecture-reference`.
- `architecture-context/` is a runtime git clone (gitignored); `arch_lookup.py` syncs before queries; entrypoint pre-syncs in containers.
- Serving stack routing: `kserve` / `llmd` / `modelmesh` map to `debugger-model-server/debugger-*` paths in `detect_component.py` and `plugin.json`.
- Memory scripts (`store_learning.py`, `query_learnings.py`, `promote_learnings.py`) resolve `kserve`/`llmd`/`modelmesh` via `SUB_COMPONENT_MAP` to nested paths.
- `RP_URL` / `RP_PROJECT` are required only for ReportPortal analysis; local log analysis needs Vertex AI credentials only.
- Container entrypoint invokes `claude -p --dangerously-skip-permissions`; plugin dir defaults to `/home/claudio/tfa-plugin`.
- `fetch_rp_failures.py` and `post_rp_results.py` are documentation stubs; orchestrator SKILL.md documents MCP tool usage instead.
