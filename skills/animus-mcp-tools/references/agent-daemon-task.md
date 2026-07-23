# Agent, Daemon, Cost, And Subject Tools

Use this reference when the Animus operation is primarily about agent control,
daemon runtime control, cost/budget visibility, or task/requirement lifecycle
changes.

## Agent control

| Tool | Key parameters |
|------|----------------|
| `animus.agent.list` | `project_root` |
| `animus.agent.get` | `id`, `project_root` |
| `animus.agent.run` | `tool`, `model`, `prompt`, `cwd`, `timeout_secs`, `context_json`, `runtime_contract_json`, `detach`, `run_id`, `project_root` |
| `animus.agent.control` | `run_id`, `action` (`pause`, `resume`, `terminate`) |
| `animus.agent.status` | `run_id` |
| `animus.agent.memory.get` | `agent`, `project_root` |
| `animus.agent.memory.append` | `agent`, `text`, `source`, `project_root` |
| `animus.agent.memory.clear` | `agent`, `project_root` |
| `animus.agent.message.send` | `channel`, `from`, `to`, `text`, `workflow_id`, `phase_id`, `project_root` |
| `animus.agent.message.list` | `channel`, `agent`, `limit`, `project_root` |

## Agent interactions and escalation

`animus.agent.ask` and `animus.agent.request_approval` are human-in-the-loop
escalation calls with two wait modes (`wait`: `block` | `suspend`):

- **Block** (default on unpinned servers): the call parks the agent until a
  human answers or the timeout elapses (default 600s, max 3600). `ask` times
  out with a structured error telling the agent to proceed on best judgment;
  `request_approval` times out as `deny` (fail closed).
- **Suspend** (default when the server is pinned to a workflow via
  `animus mcp serve --workflow-id <ID>` or `ANIMUS_MCP_WORKFLOW_ID`): the tool
  records the pending interaction, pauses the workflow, and returns
  immediately with `{ status: "pending", interaction_id, instruction }`.
  Answering the interaction resumes the workflow with the decision as
  feedback.

`animus.agent.ask` accepts two shapes: (1) a flat single question —
`question` plus optional `options[]`, returning `{ id, answer,
answered_by }`; or (2) a
structured `questions[]` array (multi-question / multi-select / described
options — parity with claude's native AskUserQuestion channel), each entry
`{ question, header?, options: [{ label, description? }], multi_select? }`,
returning `{ id, answers: { <question>: <label | [labels] | text> },
response?, answer }` where `answer` is a readable join kept for back-compat.
At least one of `question` / `questions` must be present.

An agent profile's `approval_policy` can auto-allow or auto-deny without
escalating. Both tools operate on the server's own project scope and take no
`project_root`. The agent identity can be pinned with
`animus mcp serve --agent-id <ID>` (or `ANIMUS_MCP_AGENT_ID`), making the
payload `agent_id` ignored so an agent cannot claim a sibling profile.

`animus.agent.request_approval` also conforms to the Claude Agent SDK
permission-prompt-tool contract: the claude transport wires it as
`--permission-prompt-tool`, the CLI invokes it with
`{ tool_name, input, tool_use_id }` (`action` is derived from `tool_name`
when omitted), and the result's text block carries the SDK payload —
`{ "behavior": "allow", "updatedInput": ..., "updatedPermissions"? }` or
`{ "behavior": "deny", "message" }` — with the legacy
`{ tool, result: { decision, source, ... } }` envelope kept alongside. Native
`AskUserQuestion` calls become structured Question records (bypassing the
approval policy) answered via `animus agent interactions answer --select
"<question|header|index>=<label[,label...]>"` (plus `--text` for freeform;
allowed approvals also take `--remember` and `--updated-input <json>`).
In suspend mode, voluntary calls get the pending payload, but native
prompt-tool calls get `behavior: "deny"` with an end-your-turn instruction
(the CLI cannot park on a pending payload); the workflow pauses and the
session resumes with the answer threaded in as feedback.

The `animus.interactions.*` pair is the human-side inbox over the
pending-interaction store (`~/.animus/<repo-scope>/interactions/`). It is only
registered when the server runs with `animus mcp serve --management`, so an
agent cannot answer its own question or approve its own request. The CLI
equivalent is `animus agent interactions {list, show, answer}`.

| Tool | Key parameters |
|------|----------------|
| `animus.agent.ask` | `agent_id`, `question`, `options[]`, `questions[]` (structured form; see above), `timeout_secs`, `workflow_id`, `task_id`, `wait` (`block` \| `suspend`) |
| `animus.agent.request_approval` | `agent_id`, `action` (derived from `tool_name` when omitted), `tool_name`, `input` \| `arguments`, `tool_use_id`, `suggestions`, `timeout_secs`, `workflow_id`, `task_id`, `wait` (`block` \| `suspend`) |
| `animus.interactions.list` | `all`, `agent_id`, `limit`, `project_root` |
| `animus.interactions.answer` | `id`, `text` (questions), `decision` + `message` (approvals), `answers` + `response` (structured AskUserQuestion records), `updated_input`, `updated_permissions`, `remember` (allowed approvals), `answered_by`, `project_root` |

When `animus.interactions.answer` resolves a suspend-mode record, it triggers
the workflow resume with the decision as feedback; a resume failure never
fails the answer and the response carries a `workflow_resume.guidance`
command instead.

## Daemon management

The MCP daemon tools cover runtime state. CLI-only startup helpers such as
`animus daemon preflight`, `--auto-install`, and `--skip-preflight` are not
exposed on `animus.daemon.start`.

| Tool | Key parameters |
|------|----------------|
| `animus.daemon.start` | `pool_size` (alias `max_agents`), `interval_secs`, `stale_threshold_hours`, `max_tasks_per_tick`, `phase_timeout_secs`, `startup_cleanup`, `reconcile_stale`, `project_root` |
| `animus.daemon.stop` | `project_root` |
| `animus.daemon.status` | `project_root` |
| `animus.daemon.health` | `project_root` — payload carries a `healthy` boolean verdict and `provider_plugins_healthy` |
| `animus.daemon.pause` | `project_root` |
| `animus.daemon.resume` | `project_root` |
| `animus.daemon.events` | `limit`, `project_root` |
| `animus.daemon.agents` | `project_root` |
| `animus.daemon.logs` | `limit`, `search`, `project_root` |
| `animus.daemon.config` | `project_root` |
| `animus.daemon.config-set` | `pool_size` (alias `max_agents`), `interval_secs`, `max_tasks_per_tick`, `stale_threshold_hours`, `phase_timeout_secs`, `max_daily_usd` (fleet daily spend cap; non-positive persists as explicit uncapped; v0.7-rc/portal only — absent on 0.6.x local installs), `notification_config_json`, `notification_config_file`, `clear_notification_config`, `project_root` |
| `animus.daemon.observe` | `since`, `source` (`logs`/`events`/`stream`/`workflow`), `workflow_id`, `limit`, `project_root` |

`animus.daemon.observe` is the observability front-door: it returns the
merged, chronological window of daemon events + logs (or routes to a single
`source`). It is non-streaming and works offline — the daemon need not be
running.

## Cost and budget

| Tool | Key parameters |
|------|----------------|
| `animus.cost.decisions` | `since`, `project_root` |
| `animus.budget.get` | `project_root` — fleet daily cap, rolling-24h spend, remaining headroom, exceeded/dispatch-paused flags, plus every configured per-workflow/per-phase cap. Works offline |
| `animus.budget.set` | `max_daily_usd`, `clear`, `project_root` — set or clear the fleet daily cap (wraps `daemon config --max-daily-usd`; hot-reloaded; `{clear: true}` uncaps) |

`animus.budget.get` / `animus.budget.set` are v0.7-rc/portal only — 0.6.x
local installs expose just `animus.cost.decisions` (use the CLI's
`animus daemon config --max-daily-usd` there instead).

`animus.cost.decisions` lists recorded budget-cap breaches from the scoped
breach log. Works offline. On the rc/portal line a latched fleet-cap breach
also flips `animus.daemon.health` to Degraded with `dispatch_paused` /
`daily_cap_exceeded` fields (on 0.6.x the latch appears under the health
payload's `budget_enforcement.daily_cap` instead).

## Subject tools

The subject surface replaces the removed `animus.task.*` and
`animus.requirements.*` tool families (removed in v0.4.4). Use `kind: "task"`
for local tasks, `kind: "requirement"` for requirements, or another kind
claimed by an installed `subject_backend` plugin. Every subject tool also
accepts an optional `project_root` parameter.

| Tool | Key parameters |
|------|----------------|
| `animus.subject.list` | `kind`, `status`, `limit` (default 50; `0` = uncapped), `cursor` — the result carries `next_cursor` (+ `total` when the backend reports it); page until `next_cursor` is null instead of raising `limit` |
| `animus.subject.get` | `kind`, `id` (wire id `<kind>:<native_id>`) |
| `animus.subject.create` | `kind`, `title`, `priority`, `status`, `labels[]`, `body`, `data` (JSON custom fields → the subject's `custom` bag) |
| `animus.subject.update` | `kind`, `id`, `title`, `priority`, `status`, `labels[]`, `body`, `data` |
| `animus.subject.next` | `kind` |
| `animus.subject.status` | `kind`, `id`, `status` |
| `animus.subject.batch-create` | `kind`, `items[]` (`title`, `status`, `priority`, `labels[]`, `body`, `data`), `on_error` |
| `animus.subject.batch-update` | `kind`, `items[]` (`id`, `status`, `priority`, `labels[]`, `data`), `on_error` |

`title` on `animus.subject.update` (rename) and the `data` param on
`create`/`update`/`batch-create`/`batch-update` are v0.7-rc/portal only —
0.6.x local installs accept `body` but not `title`/`data` on these tools
(matching the CLI, where `--title`/`--data` are rc-only).

The batch tools dispatch up to 100 items per call through the same code paths
as the single-item tools; `on_error` is `"stop"` (default) or `"continue"`.
Each item's `data` is a JSON object of custom fields merged into the
subject's `custom` bag; an update item carrying only `id` + `data` is valid
(each update item needs at least one of `status` / `priority` / `labels` /
`data`).
CLI mirrors exist: `animus subject batch-create` / `batch-update` take the
items array via `--file <json>` and honor `--on-error stop|continue`.
See the conventions reference for batch envelope and remediation details.

## Practical patterns

### Check system health

1. `animus.daemon.health`
2. `animus.queue.stats`
3. `animus.subject.list` with `kind: "task"` and a small `limit`

### Create and dispatch a task

1. `animus.subject.create` with `kind: "task"` and `status: "ready"`
2. `animus.queue.enqueue` with the returned id as `subject_id` (qualified `task:<id>`)
3. `animus.daemon.health`
4. `animus.workflow.list`
