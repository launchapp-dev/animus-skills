# Output And Conventions

Use this reference when reading Animus execution output or deciding how to shape list and batch requests.

## Output and monitoring

| Tool | Key parameters |
|------|----------------|
| `animus.output.run` | `run_id` |
| `animus.output.tail` | `run_id`, `task_id`, `event_types[]`, `limit` |
| `animus.output.monitor` | `run_id`, `task_id`, `phase_id` |
| `animus.output.jsonl` | `run_id`, `entries` |
| `animus.output.artifacts` | `execution_id` |
| `animus.output.phase-outputs` | `workflow_id`, `phase_id`, `project_root` |

## Provider health and orphan cleanup

The `animus.runner.*` tool family was removed in v0.5.13. Use instead:

- Provider plugin health: `animus.plugin.list` / CLI `animus plugin status` (includes per-provider state and the aggregate `provider_plugins_healthy` flag)
- Daemon-level health: `animus.daemon.health`
- Orphaned CLI processes: CLI `animus doctor --check orphan_cli_processes` (`--fix` prunes dead tracker entries; live PIDs get a manual kill suggestion)

Restart statistics are CLI-only (`animus runner restart-stats`); there is no
matching MCP tool.

Most project-scoped MCP tools accept optional `project_root` (the blocking
`animus.agent.ask` / `animus.agent.request_approval` tools deliberately do
not).

| Tool | Key parameters |
|------|----------------|
| `animus.skill.list` | `project_root`, `source` |
| `animus.skill.get` | `project_root`, `name` |
| `animus.skill.search` | `project_root`, `query`, `source`, `limit` |
| `animus.skill.create` | `name`, `description`, `prompt`, `tags[]`, `tool_policy`, `model`, `mcp_servers[]`, `category`, `activation`, `capabilities`, `overwrite`, `project_root` |
| `animus.skill.update` | `name`, plus any patchable field (`description`, `prompt`, `tags[]`, `tool_policy`, `model`, `mcp_servers[]`, `category`, `capabilities`), `project_root` |

Skill sources include project, user, installed pack/registry, built-in
fallbacks, and lower-trust agent-host probes such as `~/.claude/skills` and
`~/.codex/skills`. Agent-host skills are prompt-text-only; structural fields
are stripped.

`animus.skill.create` and `animus.skill.update` write project-scoped skills
only, at `.animus/config/skill_definitions/<name>.yaml`. Create refuses to
overwrite unless `overwrite` is true; update patches only the supplied fields
and fails for non-project skills.

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
| `animus.plugin.install` | `source`, `path`, `url`, `tag`, `name`, `sha256`, `force`, `skip_manifest_check`, `plugin_dir`, `require_signature`, `skip_signature`, `trusted_signers` |
| `animus.plugin.uninstall` | `name`, `plugin_dir` |
| `animus.plugin.search` | `query`, `kind`, `tag[]`, `org`, `stability`, `registry_url`, `no_cache` |
| `animus.plugin.browse` | `kind`, `installed`, `available`, `registry_url`, `no_cache` |
| `animus.plugin.update` | `name`, `tag`, `dry_run`, `force`, `registry_url`, `no_cache` |

Plugins can also expose their own MCP tools through the plugin host; inspect
`animus.plugin.info` before assuming a plugin-specific method exists.

## List tool pagination

All list tools support common pagination:

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `limit` | 25 | 200 | Maximum items to return |
| `offset` | 0 | -- | Items to skip |
| `max_tokens` | 3000 | 12000 | Token budget for response compaction |

List responses use the `animus.mcp.list.result.v1` envelope.

## Batch behavior

The batch tool `animus.workflow.run-multiple` accepts `on_error` (the `animus.task.bulk-*` tools were removed in v0.4.4).

| Value | Behavior |
|-------|----------|
| `continue` | Process all items regardless of failures |
| `stop` | Stop after the first failure; remaining items are marked `skipped` |

Batch responses use the `animus.mcp.batch.result.v1` envelope. Maximum batch
size is 100 items.
