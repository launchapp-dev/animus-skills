# Agent, Daemon, And Subject Tools

Use this reference when the Animus operation is primarily about agent control,
daemon runtime control, or task/requirement lifecycle changes.

## Agent control

| Tool | Key parameters |
|------|----------------|
| `animus.agent.list` | `project_root` |
| `animus.agent.get` | `id`, `project_root` |
| `animus.agent.run` | `tool`, `model`, `prompt`, `cwd`, `timeout_secs`, `context_json`, `runtime_contract_json`, `detach`, `run_id`, `runner_scope`, `project_root` |
| `animus.agent.control` | `run_id`, `action` (`pause`, `resume`, `terminate`), `runner_scope` |
| `animus.agent.status` | `run_id`, `runner_scope` |
| `animus.agent.memory.get` | `agent`, `project_root` |
| `animus.agent.memory.append` | `agent`, `text`, `source`, `project_root` |
| `animus.agent.memory.clear` | `agent`, `project_root` |
| `animus.agent.message.send` | `channel`, `from`, `to`, `text`, `workflow_id`, `phase_id`, `project_root` |
| `animus.agent.message.list` | `channel`, `agent`, `limit`, `project_root` |

## Daemon management

The MCP daemon tools cover runtime state. CLI-only startup helpers such as
`animus daemon preflight`, `--auto-install`, and `--skip-preflight` are not
separate MCP tools.

| Tool | Key parameters |
|------|----------------|
| `animus.daemon.start` | `pool_size` or `max_agents`, `interval_secs`, `auto_run_ready`, `auto_merge`, `auto_pr`, `auto_commit_before_merge`, `auto_prune_worktrees_after_merge`, `startup_cleanup`, `resume_interrupted`, `reconcile_stale`, `stale_threshold_hours`, `max_tasks_per_tick`, `phase_timeout_secs`, `idle_timeout_secs`, `skip_runner`, `autonomous`, `runner_scope`, `project_root` |
| `animus.daemon.stop` | `project_root` |
| `animus.daemon.status` | `project_root` |
| `animus.daemon.health` | `project_root` |
| `animus.daemon.pause` | `project_root` |
| `animus.daemon.resume` | `project_root` |
| `animus.daemon.events` | `limit`, `project_root` |
| `animus.daemon.agents` | `project_root` |
| `animus.daemon.logs` | `limit`, `search`, `project_root` |
| `animus.daemon.config` | `project_root` |
| `animus.daemon.config-set` | `auto_merge`, `auto_pr`, `auto_commit_before_merge`, `auto_prune_worktrees_after_merge`, `auto_run_ready`, `pool_size` or `max_agents`, `interval_secs`, `max_tasks_per_tick`, `stale_threshold_hours`, `phase_timeout_secs`, `idle_timeout_secs`, `notification_config_json`, `notification_config_file`, `clear_notification_config`, `project_root` |

## Subject tools

The subject surface replaces the removed `animus.task.*` and
`animus.requirements.*` tool families. Use `kind: "task"` for local tasks,
`kind: "requirement"` for requirements, or another kind claimed by an
installed `subject_backend` plugin.

| Tool | Key parameters |
|------|----------------|
| `animus.subject.list` | `kind`, `status`, `priority`, `limit`, `offset`, `max_tokens` |
| `animus.subject.get` | `kind`, `id` |
| `animus.subject.create` | `kind`, `title`, `description`, `priority`, `status`, `labels[]`, `input_json` |
| `animus.subject.update` | `kind`, `id`, `title`, `description`, `priority`, `status`, `labels[]`, `input_json` |
| `animus.subject.next` | `kind` |
| `animus.subject.status` | `kind`, `id`, `status` |

## Practical patterns

### Check system health

1. `animus.daemon.health`
2. `animus.queue.stats`
3. `animus.subject.list` with `kind: "task"` and a small `limit`

### Create and dispatch a task

1. `animus.subject.create` with `kind: "task"` and `status: "ready"`
2. `animus.queue.enqueue` with the returned task id as `task_id`
3. `animus.daemon.health`
4. `animus.workflow.list`
