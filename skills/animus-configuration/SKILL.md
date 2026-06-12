---
name: animus-configuration
description: Animus project config, daemon config, agent runtime, environment variables, and state layout
user_invocable: false
auto_invoke: true
---

# Animus Configuration

Animus has three main configuration layers: project-local `.animus/`, repo-scoped runtime state under `~/.animus/<repo-scope>/`, and global machine config (`~/.animus/config.json`, override the root with `ANIMUS_CONFIG_DIR`).

## Project-Local `.animus/`

Created by `animus init`. This is the project-authored configuration surface.

Common files:
- `.animus/config.json` — repo-local settings such as the `auto_update` block (CLI self-update) and `default_subject_kind`. Daemon settings do NOT live here.
- `.animus/workflows.yaml` and `.animus/workflows/*.yaml` — hand-edited workflow YAML overlays
- `.animus/plugins/` — project-local plugin binaries and pack overrides
- `.animus/plugins.lock` — plugin integrity lockfile

## Daemon Config

Persisted at `~/.animus/<repo-scope>/daemon/pm-config.json`, written only via CLI/MCP. Do not hand-edit generated JSON.

### Read Config
```bash
animus daemon config
```
MCP: `animus.daemon.config`

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

## State Layout

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

## Repo Scope

`<repo-scope>` is derived from the canonical project path: `<sanitized-repo-name>-<12 hex sha256 prefix>`.

This ensures multiple projects don't collide in runtime state.

## Precedence

For model/tool selection:
1. Phase-level `runtime.model` override (in workflow YAML)
2. Agent profile `model`/`tool` (in agent-runtime-config)
3. Compiled defaults in the Animus binary

For configuration in general:
1. CLI flags
2. Supported environment variables
3. Project-local pack overrides in `.animus/plugins/<pack-id>/`
4. Project YAML in `.animus/workflows.yaml` and `.animus/workflows/*.yaml`
5. Installed packs in `~/.animus/packs/`
