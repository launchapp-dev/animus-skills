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
    auto_pr: true
    auto_merge: false
    base_branch: main
    config:
      organization: acme
```

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
```

Cron expressions use 5 fields: `minute hour day-of-month month day-of-week`.

Common patterns:

- `*/5 * * * *` for every 5 minutes.
- `*/3 * * * *` for every 3 minutes.
- `2-59/10 * * * *` for every 10 minutes starting at `:02`.
- `37 */2 * * *` for every 2 hours at `:37`.
- `0 */3 * * *` for every 3 hours.
- `0 9 * * 1` for Monday at 9am.

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
      secret_env: MY_WEBHOOK_SECRET
      max_triggers_per_minute: 10
    input:
      source: webhook
```

Supported trigger types are:

- `file_watcher`
- `webhook`
- `github_webhook`

`file_watcher` requires `config.paths`. Webhook-style triggers use `config.secret_env` and `config.max_triggers_per_minute`. Store the secret value itself in the OS keychain with `animus secret set MY_WEBHOOK_SECRET` rather than in the daemon's environment.

## Daemon config

Use `daemon:` for project-local runtime behavior. The daemon honours exactly four fields from this block: `auto_run_ready`, `active_hours`, `phase_routing`, and `mcp`.

```yaml
daemon:
  auto_run_ready: true
  active_hours: "00:00-06:00"
  phase_routing:
    implementation:
      tool: claude
      model: claude-sonnet-4-6
```

Other `DaemonConfig` fields (`pool_size`, `interval_secs`, `max_task_retries`, `retry_cooldown_secs`) round-trip through compilation but are not read from YAML — set `pool_size` and `interval_secs` via `animus daemon config --pool-size <n> --interval-secs <n>` (persisted to `~/.animus/<repo-scope>/daemon/pm-config.json`) or the equivalent `animus daemon start` / `run` flags. `max_agents` is accepted as an alias for `pool_size`.

The daemon git/merge policy keys (`auto_merge`, `auto_pr`, `auto_commit_before_merge`, `auto_prune_worktrees`) were removed in v0.5.x; declaring them still compiles but emits a removed-key warning. Configure merge/PR behavior per workflow with `post_success.merge` instead.
