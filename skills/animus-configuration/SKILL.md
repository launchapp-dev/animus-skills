---
name: animus-configuration
description: Animus project config, daemon config, plugin config, agent runtime, environment variables, and state layout
user_invocable: false
auto_invoke: true
---

# Configuration

Animus has three main configuration layers: project-local `.animus/`, repo-scoped runtime state under `~/.animus/<repo-scope>/`, and global machine config (`~/.animus/config.json`, override the root with `ANIMUS_CONFIG_DIR`).

## Project-Local `.animus/`

Created by `animus init`. This is the project-authored configuration surface.

Common files:
- `.animus/config.json` — repo-local settings such as the `auto_update` block (CLI self-update) and `default_subject_kind`. Daemon settings do NOT live here.
- `.animus/workflows.yaml` and `.animus/workflows/*.yaml` — hand-edited workflow YAML overlays
- `.animus/plugins/` — project-local plugin binaries and pack overrides
- `.animus/plugins.lock` — plugin integrity lockfile

Common fields include project defaults such as `default_subject_kind`.

Persisted at `~/.animus/<repo-scope>/daemon/pm-config.json`, written only via CLI/MCP. Do not hand-edit generated JSON.

Hand-authored workflow sources. Typical uses:

### Update Config
```bash
animus daemon config --pool-size 3 --auto-run-ready true
animus daemon config --interval-secs 10 --max-tasks-per-tick 2
animus daemon config --stale-threshold-hours 24 --phase-timeout-secs 3600
```
MCP: `animus.daemon.config-set`

The running daemon re-reads these keys once per scheduler tick, so changes
apply without a restart (exception: a changed `phase_timeout_secs` reaches the
live process manager only after `animus daemon restart`).

The old git/merge policy keys (`auto_merge`, `auto_pr`,
`auto_commit_before_merge`, `auto_prune_worktrees`) were removed in v0.5.x —
merge/PR behavior now lives in workflow YAML `post_success.merge`, executed by
the workflow-runner plugin.

### Scheduler wake model

Dispatch is event-driven: `animus subject create/update/status` and
`animus queue enqueue/release` (and their MCP equivalents) nudge the daemon
awake, and cron schedules fire on precise deadlines. `interval_secs` is only
the fallback heartbeat — the maximum sleep when no event arrives — and paces
housekeeping (stale/zombie reconciliation). It is not the dispatch latency.

## Workflow Config

Hand-edited YAML. Defines agents, phases, workflows, cron schedules, and triggers. See the [workflow-authoring](../animus-workflow-authoring/SKILL.md) skill for full details.

Source locations:
- `.animus/workflows.yaml`
- `.animus/workflows/*.yaml`

Useful commands:
```bash
animus workflow config get
animus workflow config validate
animus workflow config compile
animus workflow config reload    # manual hot-reload trigger
```

A running daemon hot-reloads workflow YAML edits automatically via a
filesystem watcher; a malformed edit keeps the prior config active.

Workflow YAML supports `${VAR}` env-var interpolation for non-secret config,
with `${VAR:-default}` and `${VAR:?error}` fallback shapes. Credentials belong
in the OS keychain via `animus secret set <KEY>` (or `animus secret
import-env` for `.env` files), not in YAML.

## Agent Runtime Config

Controls which AI model/tool each agent profile uses. Compiled into
`~/.animus/<repo-scope>/config/agent-runtime-config.v2.json`.

Inspect and update through `animus workflow agent-runtime get|validate|set` rather than direct file edits.

### Tool Options
- `claude` — Claude Code CLI
- `codex` — OpenAI Codex CLI
- `gemini` — Google Gemini CLI
- `opencode` — OpenCode CLI
- `oai-runner` — OpenAI-compatible model runner

Each tool requires its provider plugin (`animus plugin install-defaults`
installs the standard set). Model ids are provider-specific strings passed
through to the provider plugin.

## Environment Variables

All env vars are `ANIMUS_*` as of v0.4.0 — the legacy `AO_*` names are not read.

| Variable | Purpose |
|----------|---------|
| `ANIMUS_CONFIG_DIR` | Override global config directory (default `~/.animus`) |
| `ANIMUS_PLUGIN_DIR` | Override the global plugin install directory |
| `ANIMUS_PLUGIN_PATH` | Extra colon-separated plugin discovery directories |
| `ANIMUS_DEBUG` | Verbose debug logging across CLI and daemon |
| `ANIMUS_LOG_JSON` | Emit log lines as JSON |
| `ANIMUS_DAEMON_DISABLE_TRIGGERS` | Kill-switch: skip the trigger plugin supervisor |
| `ANIMUS_DAEMON_DISABLE_SUBJECT_PLUGINS` | Kill-switch: skip subject plugin discovery |
| `ANIMUS_DAEMON_DISABLE_LOG_STORAGE_PLUGIN` | Use the in-tree `logs/events.jsonl` fallback |
| `ANIMUS_WORKFLOW_CONCURRENCY_MAX` | Cap on parallel workflow runners (also upper-bounds `pool_size`) |

See `docs/reference/configuration.md#environment-variables` in the Animus repo for the full table.

### `.animus/plugins.lock`

```
.animus/                          # project-local, authored
├── config.json                   # auto_update + repo-local settings
├── workflows.yaml
├── workflows/
├── plugins/                      # project-local plugins + pack overrides
└── plugins.lock

~/.animus/<repo-scope>/           # scoped runtime state, tool-managed
├── config/
│   ├── workflow-config.v2.json
│   ├── agent-runtime-config.v2.json
│   └── state-machines.v1.json
├── daemon/
│   ├── pm-config.json            # persisted daemon settings
│   └── daemon.log
├── runs/
├── artifacts/
├── state/
├── logs/
├── interactions/                 # pending agent questions/approvals
└── cache/
```

Key files:

- `workflow.db` stores persisted workflows, tasks, requirements, and checkpoints.
- `daemon/pm-config.json` stores persisted daemon automation settings,
  including the `notification_config` block.
- `cost-state.v1.json` stores per-workflow and per-phase token/USD spend
  rollups; budget-exceeded decisions append to `decisions.jsonl`.
- `mcp-oauth-cache/<server>.json` caches resolved OAuth tokens for
  HTTP MCP servers (`0600` on Unix).
- `config/state-machines.v1.json` stores state-machine config.
- `state/pack-selection.v1.json` stores repo-scoped pack activation and pinning.

Treat these as Animus-managed state. Prefer CLI or MCP tools over direct edits.

## Daemon config

Read current settings:

```bash
animus daemon config
```

MCP: `animus.daemon.config`

Update runtime settings:

```bash
animus daemon config --auto-merge true
animus daemon config --auto-pr true
animus daemon config --auto-commit-before-merge true
animus daemon config --pool-size 3 --auto-run-ready true
```

MCP: `animus.daemon.config-set`

Daemon startup now runs plugin preflight by default:

```bash
animus daemon preflight
animus daemon start --autonomous --auto-install
```

Notification dispatch is configured via the `notification_config` block
persisted in `daemon/pm-config.json`. Webhook URLs and headers reference
env var names through `url_env` / `headers_env` fields — commonly
`ANIMUS_NOTIFY_WEBHOOK_URL` and `ANIMUS_NOTIFY_BEARER_TOKEN` — and only
those named vars are forwarded to the notifier plugin.

## Machine-wide config

```text
~/.animus/
├── config.json
├── credentials.json
├── principals.yaml
├── packs/
│   └── <pack-id>/<version>/
├── plugins/
│   └── <plugin-name>
├── skills/
│   └── <skill-name>/SKILL.md
└── template-registries/
```

### Principals and RBAC

`~/.animus/principals.yaml` (hand-editable) declares principals, roles,
and `policy.rbac`: `single-user` (default; checks skipped) or `enforce`
(requests must resolve to a declared principal). Inspect identity with
`animus auth whoami`; `--as <principal>` is honor-system under
`single-user` and credential-checked under `enforce`.

### Packs

```bash
animus pack list
animus pack inspect --pack-id animus.task
animus pack install --path /tmp/vendor.pack --activate
animus pack pin --pack-id vendor.pack --version =1.2.3
```

### Plugins

```bash
animus plugin install-defaults --include-subjects --include-transports
animus plugin list
animus plugin lock verify
```

`animus web serve` and `animus web open` require installed transport/UI
plugins; they no longer run an in-tree web server.

## Environment variables

Core variables:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_CONFIG_DIR` | Override global config root, default `~/.animus` |
| `ANIMUS_RUNNER_CONFIG_DIR` | Override runner config directory |
| `ANIMUS_RUNNER_SCOPE` | Runner scope identifier |
| `ANIMUS_MCP_SCHEMA_DRAFT` | Select Draft-07 MCP schemas |
| `ANIMUS_MCP_ENDPOINT` | Override embedded MCP client endpoint |
| `ANIMUS_USER_ID` | Override recorded user id |
| `ANIMUS_DEBUG` | Enable verbose debug logging |
| `ANIMUS_LOG_JSON` | Emit JSON logs |
| `ANIMUS_DEBUG_MCP_STDIO` | Log raw MCP stdio frames |

Plugin and template variables:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_PLUGIN_DIR` | Override plugin install directory |
| `ANIMUS_PLUGIN_PATH` | Extra directories scanned for plugin binaries |
| `ANIMUS_TEMPLATE_REGISTRY_URL` | Override project-template registry |

Provider passthrough examples:

| Variable | Purpose |
|----------|---------|
| `ANIMUS_CLAUDE_EXTRA_ARGS` / `_JSON` | Extra Claude CLI args |
| `ANIMUS_CODEX_EXTRA_ARGS` / `_JSON` | Extra Codex CLI args |
| `ANIMUS_CODEX_EXTRA_CONFIG_OVERRIDES` / `_JSON` | Extra Codex `--config` overrides |
| `ANIMUS_CODEX_NETWORK_ACCESS` | Toggle Codex sandbox network access |
| `ANIMUS_CODEX_WEB_SEARCH` | Toggle Codex web search |

Plugin kill-switches are operator escape hatches. Example:
`ANIMUS_DAEMON_DISABLE_TRIGGERS=1` disables trigger plugin supervision on
daemon startup. Removed built-in provider and subject adapter kill-switches are
no-ops; uninstall or quarantine the plugin instead.

## Secret handling

Do not put API tokens in workflow YAML. Plugins read secrets from the daemon's
process environment, falling back to the project-scoped keychain store
populated by `animus secret set <KEY>`. Use YAML interpolation for non-secret
config only:

```yaml
subjects:
  - id: my-linear
    backend: linear
    config:
      team_id: ${LINEAR_TEAM_ID:-default-team}
      workspace: ${LINEAR_WORKSPACE:?set LINEAR_WORKSPACE}
```

Start the daemon with required secrets in the parent shell:

```bash
LINEAR_API_TOKEN=lin_api_... OPENAI_API_KEY=sk-... animus daemon start --autonomous
```

The daemon does not auto-load `.env` files. Source them before startup if
needed.

HTTP-transport `mcp_servers` entries can attach an `oauth:` block; the daemon
resolves a bearer token and injects the `Authorization` header. Credentials
are read from env vars named via `*_env` pointers (never inline in YAML), and
tokens are cached at `~/.animus/<repo-scope>/mcp-oauth-cache/<server>.json`.
Authenticate with `animus mcp auth <server>`; check `animus mcp auth-status`.

## Precedence

Workflow resolution:

For configuration in general:
1. CLI flags
2. Supported environment variables
3. Project-local pack overrides in `.animus/plugins/<pack-id>/`
4. Project YAML in `.animus/workflows.yaml` and `.animus/workflows/*.yaml`
5. Installed packs in `~/.animus/packs/`
