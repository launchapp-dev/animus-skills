# Agent, Daemon, And Task Tools

Use this reference when the Animus operation is primarily about agent control, daemon runtime control, or task lifecycle changes.

## Agent control

| Tool | Key parameters |
|------|----------------|
| `animus.agent.run` | `tool`, `model`, `prompt`, `cwd`, `timeout_secs`, `context_json`, `runtime_contract_json`, `detach`, `run_id`, `runner_scope`, `project_root` |
| `animus.agent.control` | `run_id`, `action` (`pause`, `resume`, `terminate`), `runner_scope` |
| `animus.agent.status` | `run_id`, `runner_scope` |

## Daemon management

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

## Task query tools

| Tool | Key parameters |
|------|----------------|
| `animus.task.list` | `status`, `priority`, `task_type`, `assignee_type`, `tag[]`, `risk`, `linked_requirement`, `linked_architecture_entity`, `search`, `limit`, `offset`, `max_tokens` |
| `animus.task.get` | `id` |
| `animus.task.prioritized` | `status`, `priority`, `assignee_type`, `search`, `limit`, `offset`, `max_tokens` |
| `animus.task.next` | `project_root` |
| `animus.task.stats` | `project_root` |
| `animus.task.history` | `id` |

## Task mutation tools

| Tool | Key parameters |
|------|----------------|
| `animus.task.create` | `title`, `description`, `priority`, `task_type`, `linked_requirement[]`, `linked_architecture_entity[]`, `project_root` |
| `animus.task.update` | `id`, `title`, `description`, `priority`, `status`, `assignee`, `linked_architecture_entity[]`, `replace_linked_architecture_entities`, `input_json` |
| `animus.task.delete` | `id`, `confirm`, `dry_run` |
| `animus.task.status` | `id`, `status` |
| `animus.task.assign` | `id`, `assignee`, `assignee_type`, `agent_role`, `model` |
| `animus.task.pause` | `id` |
| `animus.task.resume` | `id` |
| `animus.task.cancel` | `id`, `confirm`, `dry_run` |
| `animus.task.set-priority` | `id`, `priority` |
| `animus.task.set-deadline` | `id`, `deadline` |
| `animus.task.checklist-add` | `id`, `description` |
| `animus.task.checklist-update` | `id`, `item_id`, `completed` |
| `animus.task.bulk-status` | `updates[]`, `on_error` |
| `animus.task.bulk-update` | `updates[]`, `on_error` |

## Practical patterns

### Check system health

1. `animus.daemon.health`
2. `animus.queue.stats`
3. `animus.task.stats`

### Create and dispatch a task

1. `animus.task.create`
2. `animus.queue.enqueue`
3. `animus.daemon.health`
4. `animus.workflow.list`
