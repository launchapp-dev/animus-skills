---
name: animus-mcp-tools
description: Animus MCP tool surface - agent, daemon, cost, subject, workflow, queue, output, skill, memory, plugin, logs, and tool-discovery tools, including pagination, batch behavior, and error remediation. Use when an Animus task needs exact MCP tool names, key parameters, or tool-selection guidance.
user_invocable: false
auto_invoke: true
animus_version: "0.5.21"   # animus CLI surface this skill targets
---

# MCP Tools

Use this skill as a router, not as a wall of tables.

## Current surface rules

- Prefer the MCP tool that performs the mutation directly instead of shelling out to `animus`.
- Every tool accepts optional `project_root` unless noted otherwise.
- Tasks and requirements use `animus.subject.*`; the old `animus.task.*` and `animus.requirements.*` families were removed.
- For task operations, pass `kind: "task"`. For requirement operations, pass `kind: "requirement"`.
- Unsure which tool fits? Call `animus.tools.search` with intent keywords (ranked matches with compact parameter summaries) or `animus.tools.list` for the full grouped catalog.
- Tool failures carry structured `remediation` payloads for determinate causes (`missing_plugin` with the exact install command, `daemon_not_running`, `invalid_input`); act on them instead of guessing.
- For exact parameters, open the domain reference instead of guessing from memory.

## References

- Read [references/agent-daemon-task.md](references/agent-daemon-task.md) for `animus.agent.*` (including `ask`/`request_approval` escalation), `animus.interactions.*`, `animus.daemon.*`, `animus.cost.*`, and `animus.subject.*` (including batch create/update).
- Read [references/workflow-queue-requirements.md](references/workflow-queue-requirements.md) for `animus.workflow.*` (including phase approve/reject), `animus.queue.*` (including bulk `subject_ids[]`), and requirement-as-subject patterns.
- Read [references/output-runner-and-conventions.md](references/output-runner-and-conventions.md) for `animus.output.*`, `animus.logs.*`, `animus.skill.*`, `animus.memory.*`, `animus.plugin.*`, `animus.tools.*`, pagination, batch behavior, error remediation, and shared conventions.

## Quick routing

- Use `animus.subject.*` for task, requirement, Linear, Jira, GitHub Issue, or other subject lifecycle changes; `batch-create`/`batch-update` for up to 100 items per call.
- Use `animus.queue.*` for dispatch order and hold or release behavior; `hold`/`release`/`drop` accept `subject_ids[]` for bulk operations.
- Use `animus.workflow.*` for runs, definitions, checkpoints, and gate decisions (`phase.approve` / `phase.reject`).
- Use `animus.output.*` for run output, JSONL, artifacts, and phase outputs.
- Use `animus.logs.*` for daemon/log-storage-backed log tailing.
- Use `animus.daemon.*` for scheduler runtime state; `animus.daemon.observe` is the merged events+logs front-door.
- Use `animus.cost.decisions` to list recorded budget-cap breaches.
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
