---
name: animus-mcp-tools
description: Select and call the correct Animus MCP tool across local dotted names and hosted Portal flat names, including exact parameters, pagination, batch behavior, and structured remediation. Use when an operation needs a precise MCP tool contract; use the domain operations skill for higher-level procedure or policy.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---

# MCP Tools

Use this skill as a router, not as a wall of tables.

## Two naming surfaces

- **Local `animus mcp serve`** exposes dotted names: `animus.subject.list`,
  `animus.queue.enqueue`, … (encoded by Claude Code as
  `mcp__animus__animus_subject_list`).
- **The portal (animus-launchapp)** exposes flat snake_case names on its own
  MCP server: `list_subjects`, `queue_enqueue`, `run_workflow`,
  `daemon_health`, `cost_summary`, … (the encoded server prefix is chosen by
  the client, such as `mcp__launchapp__<name>`), plus portal-only families — `team_*`,
  `script_*`, `skill_*`, `phase_context_schema`, notes/kinds/sql tools.
  Admin schemas may be hidden by one client or discoverable and return
  `forbidden` in another. Tool visibility never grants authority.

Similar local and portal operations do not guarantee parameter parity. For
example, the core queue surface can expose idempotency/input fields that the
current portal MCP wrapper omits. Inspect the connected tool schema. Read
[references/portal-launchapp-tools.md](references/portal-launchapp-tools.md)
for the portal-only families.

## Current surface rules

- Prefer the MCP tool that performs the mutation directly instead of shelling out to `animus`.
- Treat destructive tools as explicit actions and pass the required confirmation fields when calling them.
- Every tool accepts optional `project_root` unless noted otherwise.
- Actor-bound workflow MCP intentionally exposes fewer tools than a trusted
  management server; agents must not assume run/control/config/global access.
- Tasks and requirements use `animus.subject.*`; the old `animus.task.*` and `animus.requirements.*` families were removed.
- For task operations, pass `kind: "task"`. For requirement operations, pass `kind: "requirement"`.
- Unsure which tool fits? Call `animus.tools.search` with intent keywords (ranked matches with compact parameter summaries) or `animus.tools.list` for the full grouped catalog.
- Tool failures carry structured `remediation` payloads for determinate causes (`missing_plugin` with the exact install command, `daemon_not_running`, `invalid_input`); act on them instead of guessing.
- For exact parameters, open the domain reference instead of guessing from memory.

## References

- Read [references/agent-daemon-task.md](references/agent-daemon-task.md) for `animus.agent.*` (including `ask`/`request_approval` escalation), `animus.interactions.*`, `animus.daemon.*`, `animus.cost.*`, and `animus.subject.*` (including batch create/update).
- Read [references/workflow-queue-requirements.md](references/workflow-queue-requirements.md) for `animus.workflow.*` (including phase approve/reject and the `config.set` / `config.agent-set` / `config.workflow-set` write-back verbs), `animus.queue.*` (including bulk `subject_ids[]`), and requirement-as-subject patterns.
- Read [references/output-runner-and-conventions.md](references/output-runner-and-conventions.md) for `animus.output.*`, `animus.logs.*`, `animus.skill.*`, `animus.memory.*`, `animus.plugin.*`, `animus.tools.*`, pagination, batch behavior, error remediation, and shared conventions.
- Read [references/portal-launchapp-tools.md](references/portal-launchapp-tools.md) for the portal-only tool families: `team_*` (workflow/agent/phase authoring), `script_*` (durable command-phase scripts), `phase_context_schema` (command-phase authoring contract), and the portal `skill_*` family.

## Quick routing

- Use `animus.subject.*` for task, requirement, Linear, Jira, GitHub Issue, or other subject lifecycle changes; `batch-create`/`batch-update` for up to 100 items per call.
- Use `animus.queue.*` for dispatch order and hold or release behavior; `hold`/`release`/`drop` accept `subject_ids[]` for bulk operations.
- Use `animus.workflow.*` for runs, definitions, checkpoints, and gate decisions (`phase.approve` / `phase.reject`).
- Use `animus.output.*` for run output, JSONL, artifacts, and phase outputs.
- Use `animus.logs.*` for daemon/log-storage-backed log tailing.
- Use `animus.daemon.*` for scheduler runtime state; `animus.daemon.observe` is the merged events+logs front-door.
- Use `animus.cost.decisions` to list recorded budget-cap breaches; `animus.budget.get` / `animus.budget.set` read and set the fleet daily spend cap (`budget.*` is v0.7-rc/portal only — not on 0.6.x local installs).
- Use `animus.environment.*` (`list`, `get`, `teardown`, `reap`) to inspect and reap environment-plugin run nodes; `reap` defaults to dead-only (v0.7-rc.26+/portal only — not on 0.6.x local installs).
- Use `animus.agent.ask` or `animus.agent.request_approval` to escalate to a human; block mode parks until answered or timed out, suspend mode (default on workflow-pinned servers) pauses the workflow and returns immediately.
- Use `animus.interactions.*` to read and answer the escalation inbox (requires `animus mcp serve --management`).
- Use `animus.skill.*` to list, resolve, search, or author project- or user-scoped skills.
- Use `animus.plugin.*` to inspect or manage installed STDIO plugins.
- Use `animus.tools.search` / `animus.tools.list` to discover tools on the live registry without carrying every schema.

If an older instruction says to call `animus.task.*` or `animus.requirements.*`,
translate it to `animus.subject.*` before acting. The `animus.runner.*` family
was removed in v0.5.13: runner health is covered by `animus.daemon.health`
(`provider_plugins_healthy`) and orphan detection/cleanup moved to the CLI
(`animus doctor --fix`).
