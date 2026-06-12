# Agent, Daemon, And Subject Tools

<<<<<<< HEAD
Use this reference when the Animus operation is primarily about agent control, daemon runtime control, or subject (task/requirement) lifecycle changes.

The `animus.task.*` and `animus.requirements.*` tool families were removed in v0.4.4; subject ops go through `animus.subject.*` with `kind=task` or `kind=requirement`.
=======
Use this reference when the Animus operation is primarily about agent control,
daemon runtime control, or task/requirement lifecycle changes.
>>>>>>> origin/main

## Agent control

| Tool | Key parameters |
|------|----------------|
| `animus.agent.list` | `project_root` |
| `animus.agent.get` | `id`, `project_root` |
<<<<<<< HEAD
| `animus.agent.run` | `tool`, `model`, `prompt`, `cwd`, `timeout_secs`, `context_json`, `runtime_contract_json`, `detach`, `run_id`, `project_root` |
| `animus.agent.control` | `run_id`, `action` (`pause`, `resume`, `terminate`) |
| `animus.agent.status` | `run_id` |
=======
| `animus.agent.run` | `tool`, `model`, `prompt`, `cwd`, `timeout_secs`, `context_json`, `runtime_contract_json`, `detach`, `run_id`, `runner_scope`, `project_root` |
| `animus.agent.control` | `run_id`, `action` (`pause`, `resume`, `terminate`), `runner_scope` |
| `animus.agent.status` | `run_id`, `runner_scope` |
>>>>>>> origin/main
| `animus.agent.memory.get` | `agent`, `project_root` |
| `animus.agent.memory.append` | `agent`, `text`, `source`, `project_root` |
| `animus.agent.memory.clear` | `agent`, `project_root` |
| `animus.agent.message.send` | `channel`, `from`, `to`, `text`, `workflow_id`, `phase_id`, `project_root` |
| `animus.agent.message.list` | `channel`, `agent`, `limit`, `project_root` |
<<<<<<< HEAD
| `animus.agent.ask` | `agent_id`, `question`, `options[]`, `timeout_secs`, `workflow_id`, `task_id`, `wait` (`block` \| `suspend`) — no `project_root` override |
| `animus.agent.request_approval` | `agent_id`, `action`, `tool_name`, `arguments`, `timeout_secs`, `workflow_id`, `task_id`, `wait` (`block` \| `suspend`) — no `project_root` override |

The two blocking escalation tools (`ask`, `request_approval`) park until a
human answers via `animus agent interactions answer` (or the
`animus.interactions.*` tools on a `--management` server). Approvals deny
fail-closed on timeout.
=======

## Agent interactions and escalation

`animus.agent.ask` and `animus.agent.request_approval` are blocking
escalation calls: they park the agent until a human answers or the timeout
elapses (default 600s, max 3600). `ask` times out with an instruction to
proceed on best judgment; `request_approval` times out as `deny` (fail
closed), and an agent profile `approval_policy` can auto-allow or auto-deny
without escalating. Both operate on the server's own project scope and do not
take `project_root`.

The `animus.interactions.*` pair is the human-side inbox. It is only
registered when the server runs with `animus mcp serve --management`, so an
agent cannot answer its own question or approve its own request.

| Tool | Key parameters |
|------|----------------|
| `animus.agent.ask` | `agent_id`, `question`, `options[]`, `timeout_secs`, `workflow_id`, `task_id` |
| `animus.agent.request_approval` | `agent_id`, `action`, `tool_name`, `arguments`, `timeout_secs`, `workflow_id`, `task_id` |
| `animus.interactions.list` | `all`, `agent_id`, `limit`, `project_root` |
| `animus.interactions.answer` | `id`, `text` (questions), `decision` + `message` (approvals), `answered_by`, `project_root` |
>>>>>>> origin/main

## Daemon management

The MCP daemon tools cover runtime state. CLI-only startup helpers such as
`animus daemon preflight`, `--auto-install`, and `--skip-preflight` are not
separate MCP tools.

| Tool | Key parameters |
|------|----------------|
| `animus.daemon.start` | `pool_size` (alias `max_agents`), `interval_secs`, `auto_run_ready`, `startup_cleanup`, `resume_interrupted`, `reconcile_stale`, `stale_threshold_hours`, `max_tasks_per_tick`, `phase_timeout_secs`, `skip_runner`, `autonomous`, `auto_install`, `skip_preflight`, `project_root` |
| `animus.daemon.stop` | `project_root` |
| `animus.daemon.status` | `project_root` |
| `animus.daemon.health` | `project_root` |
| `animus.daemon.pause` | `project_root` |
| `animus.daemon.resume` | `project_root` |
| `animus.daemon.events` | `limit`, `project_root` |
| `animus.daemon.agents` | `project_root` |
| `animus.daemon.logs` | `limit`, `search`, `project_root` |
| `animus.daemon.config` | `project_root` |
| `animus.daemon.config-set` | `auto_run_ready`, `pool_size` (alias `max_agents`), `interval_secs`, `max_tasks_per_tick`, `stale_threshold_hours`, `phase_timeout_secs`, `notification_config_json`, `notification_config_file`, `clear_notification_config`, `project_root` |

<<<<<<< HEAD
The daemon git/merge policy fields (`auto_merge`, `auto_pr`,
`auto_commit_before_merge`, `auto_prune_worktrees`) and `idle_timeout_secs`
were removed in v0.5.x — merge/PR policy lives in workflow
`post_success.merge`. `interval_secs` is the fallback heartbeat for
housekeeping, not the dispatch latency: dispatch is event-driven
(`daemon/nudge` on subject/queue mutations, plus precise cron deadlines).

## Subject tools

Set `kind` to `task`, `requirement`, or any kind claimed by an installed `subject_backend` plugin. Subject ids are wire ids (`<kind>:<native_id>`, e.g. `task:TASK-001`).

| Tool | Key parameters |
|------|----------------|
| `animus.subject.list` | `kind`, `status`, `limit`, `project_root` |
| `animus.subject.get` | `kind`, `id`, `project_root` |
| `animus.subject.create` | `kind`, `title`, `priority`, `status`, `labels[]`, `body`, `project_root` |
| `animus.subject.update` | `kind`, `id`, `priority`, `status`, `labels[]`, `project_root` |
| `animus.subject.next` | `kind`, `project_root` |
| `animus.subject.status` | `kind`, `id`, `status`, `project_root` |
=======
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
>>>>>>> origin/main

## Practical patterns

### Check system health

1. `animus.daemon.health`
2. `animus.queue.stats`
<<<<<<< HEAD
3. `animus.plugin.list` (provider/subject plugin health)

### Create and dispatch a task

1. `animus.subject.create` (`kind: "task"`)
2. `animus.queue.enqueue`
=======
3. `animus.subject.list` with `kind: "task"` and a small `limit`

### Create and dispatch a task

1. `animus.subject.create` with `kind: "task"` and `status: "ready"`
2. `animus.queue.enqueue` with the returned task id as `task_id`
>>>>>>> origin/main
3. `animus.daemon.health`
4. `animus.workflow.list`
