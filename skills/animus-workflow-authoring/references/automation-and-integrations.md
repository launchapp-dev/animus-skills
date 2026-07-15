# Automation And Integrations

Use this reference when the workflow YAML touches runtime wiring beyond basic `agents`, `phases`, and `workflows`.

## Phase MCP bindings

Use `phase_mcp_bindings` when a phase should attach extra MCP servers even if they are not globally attached to every agent.

```yaml
mcp_servers:
  animus:
    command: animus
    args: ["mcp", "serve"]
  memory:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-memory"]

phase_mcp_bindings:
  research:
    servers:
      - animus
      - memory
```

Every referenced server must exist under `mcp_servers:`.

`mcp_servers:` entries accept `command`, `args`, `transport` (default
`stdio`), `url` (required for `transport: http`), `env`, `tools` (allowed
tool-name prefixes), `config`, and an `oauth:` block (HTTP transport only;
flows `client_credentials` / `refresh_token` / `manual_bearer` /
`authorization_code` via `animus mcp auth`). For `authorization_code`
providers that don't support Dynamic Client Registration, set `client_id`
(pre-registered application id) and — for confidential clients (HubSpot,
Dropbox, …) — `client_secret_env` (v0.7.0-rc.12+; resolved from process env,
then the `animus secret` keychain). All credential material is named via
`*_env` fields, never inlined.

Per-agent MCP pass-down is real on every run path: the resolved server set
rides the provider contract to any provider plugin that declares
`supports_mcp` (manifest field, plugin protocol 1.2.0; undeclared defaults
to true — the workflow path needs workflow-runner v0.4.3+). Secret-bearing
servers (all OAuth flows) are rewritten to `animus-mcp-proxy` stdio entries,
so tokens never reach CLI configs or argv. For deterministic, LLM-free access
from command phases or scripts, use `animus mcp tools <server>` and
`animus mcp call <server> <tool> --args '<json>'` (v0.7.0-rc.9+).

## Tool registry

Use `tools:` to register tool metadata Animus can reason about.

```yaml
tools:
  cli-gpt:
    executable: gpt-cli
    supports_mcp: true
    supports_write: false
    context_window: 64000
    base_args: ["--json"]
```

## Integrations

Use `integrations:` for repository-wide task and git provider settings.

```yaml
integrations:
  tasks:
    provider: github
    config:
      scope: org
  git:
    provider: github
    base_branch: main
    config:
      organization: acme
```

`integrations.git` reads only `provider`, `base_branch`, and `config` — the old
`auto_pr` / `auto_merge` keys were removed and now fail to parse. Merge/PR/commit
automation is expressed as `command:` phases running `git`/`gh` (see the workflow
patterns skill).

## Schedules

Schedules require `workflow_ref`. Older `command`-based schedules are no longer supported.

```yaml
schedules:
  - id: nightly
    cron: "0 2 * * *"
    workflow_ref: standard
    input:
      scope: nightly
      full_test: true
    enabled: true
    owner_id: rafal          # v0.7, optional — see below
```

Cron expressions use 5 fields (`minute hour day-of-month month day-of-week`)
and are evaluated in UTC. Cron shortcuts (`@daily`, …) are rejected.

`owner_id` (+ optional `claims[]`) is the v0.7 actor foundation: the
scheduler mints that user's Actor for dispatched runs, so the run uses the
owner's config partition and integrations. Omit it for global dispatch.

Common patterns:

- `*/5 * * * *` for every 5 minutes.
- `*/3 * * * *` for every 3 minutes.
- `2-59/10 * * * *` for every 10 minutes starting at `:02`.
- `37 */2 * * *` for every 2 hours at `:37`.
- `0 */3 * * *` for every 3 hours.
- `0 9 * * 1` for Monday at 9am.

Runtime semantics (event-driven scheduler, v0.5.13+): the daemon computes the
earliest upcoming occurrence across all schedules and wakes at exactly that
instant — cron fires on time, not on the next polling tick, and schedule
edits take effect immediately via config hot-reload. A 10-minute catch-up
horizon recovers at most the single most recent occurrence missed while the
daemon was busy; occurrences missed for longer (daemon down, `active_hours`
window closed) are skipped, never replayed. `interval_secs` is only a
fallback heartbeat, not the dispatch latency.

## Triggers

Animus also supports event-driven triggers.

```yaml
triggers:
  - id: docs-change
    type: file_watcher
    workflow_ref: docs-workflow
    enabled: true
    config:
      paths:
        - "docs/**/*.md"
      ignore:
        - "docs/archive/**"
      debounce_secs: 5

  - id: incoming-webhook
    type: webhook
    workflow_ref: respond-to-webhook
    enabled: true
    config:
      secret_env: ANIMUS_WEBHOOK_SECRET
      max_triggers_per_minute: 10
    input:
      source: webhook
```

Supported trigger types are:

- `file_watcher` — built-in glob watcher; requires `config.paths`
  (`debounce_secs` default 5, `ignore` globs optional). Watcher events
  survive failed spawns — the baseline no longer advances on a dispatch
  failure.
- `webhook` / `github_webhook` — HTTP ingress is provided by an installed
  transport plugin honoring `config.secret_env` and
  `config.max_triggers_per_minute`. `config:` is optional — when omitted it
  defaults to no signing secret and `max_triggers_per_minute: 10`; validation
  only rejects an explicit `max_triggers_per_minute: 0`. Store the secret value
  itself in the OS keychain with `animus secret set MY_WEBHOOK_SECRET` rather
  than in the daemon's environment.
- `plugin` — an external `trigger_backend` plugin emits events. The
  per-trigger `config:` map is currently NOT forwarded to the plugin
  (plugins source their own config); `ANIMUS_DAEMON_DISABLE_TRIGGERS=1`
  suppresses plugin triggers only.

Test a `webhook` / `github_webhook` trigger locally with
`animus trigger fire <trigger_id> --payload <json>`, which appends a
synthetic event to the same pending-events queue the daemon drains.
(`trigger fire` is webhook-only — `file_watcher` and `plugin` triggers must be
exercised by producing their real underlying event.)

## Inter-workflow dependencies (fan-in)

Runs can declare upstream dependencies via two reserved run-vars
(v0.7.0-rc.6, TASK-208 — passed as workflow input/`--var`, not YAML fields):

- `ANIMUS_DEPENDS_ON` — JSON array or comma list of upstream run ids.
- `ANIMUS_JOIN_POLICY` — `block` (default: wait for all upstream runs to be
  terminal), `proceed`, or `cancel`.

The join barrier fires exactly once when all upstream runs reach a terminal
state — use it to fan several parallel runs into a downstream aggregation
workflow.

## Daemon config

Use `daemon:` for project-local runtime behavior. Only four fields are read
from workflow YAML:

```yaml
daemon:
  active_hours: "00:00-06:00"   # local-time window gating schedule + trigger dispatch
  phase_routing:                # per-phase model/tool routing at daemon spawn time
    per_phase:                  # per-phase overrides MUST nest under per_phase:
      implementation:
        tool: claude
        model: claude-sonnet-4-6
  mcp: {}                       # daemon-side MCP runtime config
  budget:                       # fleet-wide spend cap across all workflows
    max_cost_usd_per_day: 50.0
    on_exceed: pause            # pause (default) | fail | warn
```

The daemon is queue-only: it dispatches enqueued subjects (`animus queue enqueue`)
and cron `schedules:` fires — Ready subjects are NEVER auto-dispatched. There is
no `auto_run_ready` field; declaring it emits a removed-key warning.

Everything else is set elsewhere or gone:

- `interval_secs` and `pool_size` (alias `max_agents`) round-trip in YAML
  but the daemon ignores them there — set them via
  `animus daemon config --interval-secs <n> --pool-size <n>` (persisted,
  hot-reloaded) or flags on `animus daemon run` / `animus daemon start`.
- `max_task_retries` / `retry_cooldown_secs` have no runtime sink at all.
- The daemon git policy keys (`auto_merge`, `auto_pr`,
  `auto_commit_before_merge`, `auto_prune_worktrees`) were **removed**, along
  with their CLI flags and `integrations.git.auto_merge` / `auto_pr`. Animus no
  longer performs git operations as runner automation: express commit/push/PR/merge
  as `command:` phases running `git`/`gh`. Old pm-config.json files still load.

Declaring any of these unenforced/removed keys compiles fine but emits a
warning on compile stderr and in the `warnings` array of
`animus workflow config validate` / `compile`.

Outside `active_hours`, both schedules and triggers are suppressed; missed
cron fires are not replayed when the window reopens, while webhook/plugin
events stay queued and drain when it opens. `schedules:` and `triggers:`
entries merge by `id` across `.animus/workflows/*.yaml` files; the `daemon:`
block field-merges across overlays.
