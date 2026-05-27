# Output, Runner, Plugin, Skill, Memory, And Conventions

Use this reference for run output, logs, runner health, plugin inspection,
skill discovery, memory, pagination, and batch behavior.

## Output and monitoring

| Tool | Key parameters |
|------|----------------|
| `animus.output.run` | `run_id` |
| `animus.output.tail` | `run_id`, `task_id`, `event_types[]`, `limit` |
| `animus.output.monitor` | `run_id`, `task_id`, `phase_id` |
| `animus.output.jsonl` | `run_id`, `entries` |
| `animus.output.artifacts` | `execution_id` |
| `animus.output.phase-outputs` | `workflow_id`, `phase_id`, `project_root` |

## Logs

| Tool | Key parameters |
|------|----------------|
| `animus.logs.tail` | `plugin`, `level`, `since`, `limit`, `project_root` |

Use `animus.logs.tail` for the active log storage backend. It reads the
in-tree `events.jsonl` fallback when no log storage plugin is active.

## Runner

| Tool | Key parameters |
|------|----------------|
| `animus.runner.health` | `project_root` |
| `animus.runner.orphans-detect` | `project_root` |
| `animus.runner.orphans-cleanup` | `run_id`, `project_root` |
| `animus.runner.restart-stats` | `project_root` |

## Skills

| Tool | Key parameters |
|------|----------------|
| `animus.skill.list` | `project_root`, `source` |
| `animus.skill.get` | `project_root`, `name` |
| `animus.skill.search` | `project_root`, `query`, `source`, `limit` |

Skill sources include project, user, installed pack/registry, built-in
fallbacks, and lower-trust agent-host probes such as `~/.claude/skills` and
`~/.codex/skills`. Agent-host skills are prompt-text-only; structural fields
are stripped.

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

`animus.workflow.run-multiple` accepts `on_error`.

| Value | Behavior |
|-------|----------|
| `continue` | Process all items regardless of failures |
| `stop` | Stop after the first failure; remaining items are marked `skipped` |

Batch responses use the `animus.mcp.batch.result.v1` envelope. Maximum batch
size is 100 items.
