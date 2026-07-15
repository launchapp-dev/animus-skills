---
name: animus-portal-operations
description: Operate the Animus portal (animus-launchapp) — the flat-named portal MCP surface and admin-only tool visibility, Claude/Codex subscription Connections, the external MCP-server catalog with Connect handshake and ext.* subject projection, the durable script registry and phase_context_schema authoring loop, team_* workflow authoring over MCP, and trigger-event observability. Use when driving a portal deployment rather than a local CLI install.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.18"   # portal at ao-cli v0.7.0-rc.18 / runner v0.4.38
---

# Portal Operations (animus-launchapp)

The portal is a hosted Animus deployment: the daemon + plugins run in a
container, config lives in Postgres (the consolidated `animus-postgres`
multi-kind plugin serves subject_backend + config_source + queue +
workflow_journal + conversation_store), and clients drive it through the
portal's own MCP server.

## Portal MCP surface — naming and visibility

- Tools are **flat snake_case** (`list_subjects`, `queue_enqueue`,
  `run_workflow`, `daemon_health`, `cost_summary`, …), encoded by hosts as
  `mcp__animus-launchapp__<name>`; params are camelCase (`subjectId`,
  `workflowRef`).
- **Admin tools are invisible to non-admins** — they are not registered at
  all for non-admin users (`team_*` writes, `script_set`/`script_remove`,
  `sql_*`). A "missing" tool usually means a role problem, not a version
  problem.
- Dispatch params follow the v0.7 breaking rename: `subjectId` everywhere
  (`taskId`/`requirementId` are gone); `list_subjects` is paginated
  (`cursor` → `next_cursor`, `status` filter; never assume page one is the
  whole board).
- Full family tables:
  [animus-mcp-tools/references/portal-launchapp-tools.md](../animus-mcp-tools/references/portal-launchapp-tools.md).

## Authoring workflows over MCP (team_* loop)

A complete custom workflow is authorable without touching YAML:

1. `team_config_get` — read the compiled config (agents, workflows, phases,
   MCP servers).
2. `team_agent_set` — upsert the agent profile (`id`, `model`, `tool`,
   `systemPrompt`, `mcpServers`, `extraConfig`).
3. `team_phase_set` — upsert phase definitions (`mode: agent|command|manual`,
   `directive`, `extraConfig` for capabilities/output_contract/retry/command).
   This writes the config_source **base** the validator sees — prefer it over
   the legacy `workflow phases upsert` overlay.
4. `team_workflow_set` — compose phases (bare names or rich
   `{id, on_verdict, max_rework_attempts}` steps) + `budget`.
5. `team_reload` — explicit daemon config apply (writes attempt auto-reload).
6. Dispatch: `queue_enqueue {subjectId: "task:TASK-123", workflowRef: "..."}`.

## Command-phase scripts: the script registry + phase_context loop

Durable, team-editable command-phase scripts without a redeploy:

1. `phase_context_schema` — fetch the authoring contract FIRST (injected
   `ANIMUS_*` env vars, the `$ANIMUS_CONTEXT_FILE` JSON schema, and the
   `phase_decision` stdout protocol). Never hand-roll it from memory.
2. `script_set {name, content, language: bash|python|typescript}` — upserts
   the Postgres row and atomically materializes
   `/data/animus-state/scripts/<name>.<ext>` (0755).
3. `team_phase_set` with `mode: command` and
   `command: {program: <interpreter>, args: ["/data/animus-state/scripts/<name>.<ext>"], parse_json_output: true}`.
4. The script prints ONE `phase_decision` JSON object to stdout —
   `{kind: "phase_decision", verdict: "advance|rework|skip|fail|<custom>",
   reason?, outputs?}` — and custom verdicts route via the workflow's
   `on_verdict` map.

Interpreters (`bash`/`python3`/`tsx`) must be in the daemon's command-phase
`tools_allowlist`. Boot seeds from `deploy/script-seeds/` never overwrite
admin edits. Scripts read Animus state deterministically via `animus mcp
call` and the CLI — no LLM tokens for mechanical steps.

## Connections (subscription logins)

Admin-gated. Credentials are SHARED server secrets injected into every agent
run on the deployment — never returned to clients or logged.

- **Claude**: primary flow is portal-driven OAuth (PKCE; paste the
  `code#state` from claude.ai) writing a real Claude Code
  `.credentials.json` into the durable `CLAUDE_CONFIG_DIR`
  (`/data/animus-state/claude-config`) — the genuine `claude` binary
  self-refreshes it. Fallback: paste a `claude setup-token` (~1 year),
  injected as `CLAUDE_CODE_OAUTH_TOKEN` through a wrapper installed as
  `/usr/local/bin/claude` (sets `IS_SANDBOX=1`, unsets
  `ANTHROPIC_BASE_URL`).
- **Codex**: ChatGPT-subscription device-code OAuth (verification URL +
  user code; loopback-PKCE fallback), writing `auth.json`
  (`auth_mode: "chatgpt"`) into `CODEX_HOME`
  (`/data/animus-state/codex-config`). Portal chat can run subscription
  codex models in its own harness; `max_output_tokens` is intentionally
  omitted on the codex path (the ChatGPT backend rejects it).
- **There is NO Gemini connection.** It was added and removed upstream —
  Google offers no sanctioned OAuth path for consumer Gemini subscriptions.
  API-key Gemini (AI Studio / Vertex) works through the provider plugin and
  needs no connect flow. Do not document or promise a Gemini connect.

## External MCP servers → ext.* subjects

The portal connects external MCP servers and projects their data into the
board as read-only subjects:

1. **Catalog**: ~110 curated entries (hosted-OAuth + stdio-npx) in 10
   categories; admins add one, or register a custom server (pre-registered
   OAuth `client_id` + confidential client secret supported, ao-cli rc.12+).
2. **Connect** runs a real MCP handshake (initialize + tools/list) — via the
   `animus-mcp-proxy` bridge for OAuth servers (token stays in the keychain)
   — and persists the discovered tools.
3. **Classify** proposes subject bindings for the server's entities. Three
   tiers, each degrading to the previous on failure: deterministic CRUD-pair
   finder → one-shot AI classify (samples a real list call) → autonomous
   explorer agent (journaled daemon run; read-shaped tools only; byte/step/
   wall-clock caps). All tiers force `write_enabled: false` (read-only P0).
4. **Approve** materializes the bindings to
   `/data/animus-state/mcp-subject-bindings.json`; the `animus-subject-mcp`
   plugin (subject_backend, `subject_kinds: ["ext.*"]` — the glob outranks
   animus-postgres's `*` catch-all) serves them as subjects of kind
   `ext.<server>.<entity>`, executing reads via `animus mcp call`.
5. The kinds surface in `list_kinds` and are dispatchable like any subject
   (`queue_enqueue {subjectId: "ext.krisp.meeting:<id>", workflowRef: ...}`).

## Trigger-event observability

Every trigger delivery (schedules, `triggers:` blocks, webhooks) writes a
`trigger_event` subject — status `done`, delivery metadata in `custom` —
so "did my trigger fire?" is a board/`list_subjects` query, not a log hunt.
Pruned past 30 days beyond the newest 2000 events.

## Skills on the portal — durability

GitHub `skill_install` (`source: OWNER/REPO[@ref]`) lands in the durable
on-volume registry and survives redeploys; `path` installs and
`skill_create` land in the ephemeral project scope and are wiped on
redeploy. Prefer GitHub installs for anything persistent; org-owned skill
packs re-seed on boot.

Cross-references: animus-mcp-tools (portal tool tables),
animus-workflow-authoring + animus-workflow-patterns (what the team_* loop
authors), animus-environment-operations (coder nodes the portal's runs use),
animus-subject-operations (animus-postgres / animus-subject-mcp backends).
