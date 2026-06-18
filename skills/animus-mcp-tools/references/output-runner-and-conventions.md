# Output, Logs, Plugin, Skill, Memory, Tool Discovery, And Conventions

Use this reference for run output, logs, plugin inspection, skill discovery
and authoring, memory, tool discovery, pagination, batch behavior, and error
remediation.

## Output and monitoring

| Tool | Key parameters |
|------|----------------|
| `animus.output.run` | `run_id` |
| `animus.output.tail` | `run_id`, `task_id`, `event_types[]`, `limit` |
| `animus.output.monitor` | `run_id`, `task_id`, `phase_id` |
| `animus.output.jsonl` | `run_id`, `entries` |
| `animus.output.artifacts` | `execution_id` |
| `animus.output.phase-outputs` | `workflow_id`, `phase_id`, `project_root` |

Note: the CLI verb was renamed `animus output read` (v0.5.13; the `output run`
alias was removed in v0.5.14), but the MCP tool name is still
`animus.output.run`.

## Logs

| Tool | Key parameters |
|------|----------------|
| `animus.logs.tail` | `plugin`, `level`, `since`, `limit`, `project_root` |

Use `animus.logs.tail` for the active log storage backend. It routes through
the daemon control wire when the daemon is running, otherwise reads the
in-tree `events.jsonl` fallback. No `--follow` equivalent: it is a bounded
fetch, not a live stream.

## Runner tools (removed)

The `animus.runner.*` MCP tools (`health`, `orphans-detect`,
`orphans-cleanup`, `restart-stats`) were removed in v0.5.13 along with the
`animus runner` CLI group. Runner/provider health is reported by
`animus.daemon.health` (`provider_plugins_healthy`) and the CLI's
`animus plugin status`; orphaned-CLI-process detection and cleanup moved to
`animus doctor` / `animus doctor --fix` (CLI only). The scoped invocation is
`animus doctor --check orphan_cli_processes` (`--fix` prunes dead tracker
entries; live PIDs get a manual-kill suggestion).

## Skills

| Tool | Key parameters |
|------|----------------|
| `animus.skill.list` | `project_root`, `source` (`installed` \| `user` \| `project` \| `agent_host` \| host id like `claude-code`) |
| `animus.skill.get` | `project_root`, `name` |
| `animus.skill.search` | `project_root`, `query`, `source`, `limit` (default 50) |
| `animus.skill.create` | `name`, `scope` (`project` default \| `user`), `description`, `prompt`, `tags`, `tool_policy`, `model`, `mcp_servers`, `category`, `activation`, `capabilities`, `overwrite`, `project_root` |
| `animus.skill.update` | `name`, `scope` (optional unless the name exists at both scopes), plus any `animus.skill.create` field to patch, `project_root` |

Skill sources include project, user, installed pack/registry, and lower-trust
agent-host probes such as `~/.claude/skills` and `~/.codex/skills`.
Agent-host skills are prompt-text-only; structural fields (`tool_policy`,
`mcp_servers`, `env`, etc.) are stripped at parse time.

`animus.skill.create` writes `.animus/config/skill_definitions/<name>.yaml`
(`scope: "project"`, default) or `~/.animus/config/skill_definitions/<name>.yaml`
(`scope: "user"`; project shadows user on name collision). Create refuses to
shadow an existing skill at the same scope unless `overwrite` is true; update
patches only the supplied fields and rejects installed/pack/agent-host
sources.

## Memory

| Tool | Key parameters |
|------|----------------|
| `animus.memory.get` | `agent_id`, `entry_id`, `project_root` |
| `animus.memory.list` | `agent_id`, `prefix`, `limit`, `project_root` |
| `animus.memory.append` | `agent_id`, `text`, `source`, `project_root` |
| `animus.memory.clear` | `agent_id`, `entry_id`, `delete_all`, `project_root` |

Top-level `animus mcp serve` exposes memory tools. Spawned workflow agents
only get the memory server when their agent profile enables memory capability.

## Plugin control

| Tool | Key parameters |
|------|----------------|
| `animus.plugin.list` | `project_root`, `include_system_path` |
| `animus.plugin.info` | `name`, `project_root`, `include_system_path` |
| `animus.plugin.ping` | `name`, `project_root`, `include_system_path` |
| `animus.plugin.call` | `name`, `method`, `params`, `project_root` |
| `animus.plugin.install` | `source`, `path`, `url`, `tag`, `name`, `sha256`, `force`, `skip_manifest_check`, `plugin_dir`, `require_signature`, `skip_signature`, `trusted_signers`, `force_rewrite_lockfile`, `project_root` |
| `animus.plugin.uninstall` | `name`, `plugin_dir`, `project_root` |
| `animus.plugin.search` | `query`, `kind`, `tag[]`, `org`, `stability`, `registry_url`, `no_cache` |
| `animus.plugin.browse` | `kind`, `installed`, `available`, `registry_url`, `no_cache` |
| `animus.plugin.update` | `name` (omit for all), `tag` (only with `name`), `dry_run`, `force` (`registry_url` / `no_cache` are deprecated and ignored) |

Plugins can also expose their own MCP tools through the plugin host; inspect
`animus.plugin.info` before assuming a plugin-specific method exists.

## Tool discovery

Meta-tools over the server's own live tool registry, for agents with tight
context budgets.

| Tool | Key parameters |
|------|----------------|
| `animus.tools.search` | `query`, `limit` (default 8, max 50) |
| `animus.tools.list` | (none) |

`search` matches tool names, descriptions, and parameter names; results are
ranked (name > description > parameter hits; an exact tool-name query ranks
first) and each match carries a compact parameter summary. `list` returns
every registered tool grouped by family with one-line summaries and no input
schemas. Results reflect the serving instance — the management-gated
`animus.interactions.*` tools only appear under `animus mcp serve
--management`.

## List tool pagination

All list tools support common pagination:

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `limit` | 25 | 200 | Maximum items to return |
| `offset` | 0 | -- | Items to skip |
| `max_tokens` | 3000 | 12000 | Token budget for response compaction (min 256) |

List responses use the `animus.mcp.list.result.v1` envelope.

## Batch behavior

The batch tools — `animus.workflow.run-multiple`,
`animus.subject.batch-create`, and `animus.subject.batch-update` — dispatch
items one at a time through the same code paths as the matching single-item
tools and accept `on_error`:

| Value | Behavior |
|-------|----------|
| `continue` | Process all items regardless of failures |
| `stop` (default) | Stop after the first failure; remaining items are marked `skipped` |

Batch responses use the `animus.mcp.batch.result.v1` envelope with
succeeded/failed/skipped counts and per-item results. Maximum batch size is
100 items per call; larger requests are rejected before any item executes.
Failed items carry the same structured `error` and `remediation` payload as
single-tool errors.

## Error remediation

When a tool fails, the structured error payload carries the wrapped CLI error
(`error`), the process `exit_code`, and raw `stderr`. For determinate failure
classes it also carries a machine-actionable `remediation` object:

| `remediation.kind` | When | Fields |
|---|---|---|
| `missing_plugin` | A required plugin is not installed | `install_command` (exact `animus plugin install ...`), `next_step` |
| `daemon_not_running` | The command needs a running daemon | `next_step` (always `animus daemon start`) |
| `invalid_input` | The CLI rejected the arguments (exit code 2) | `help` (the CLI's hint) |

Absence of `remediation` means "no known mechanical fix". Typed CLI exit
codes surface in `exit_code`: 2 invalid input, 3 not-found, 5 unavailable
(missing plugin / network / daemon).
