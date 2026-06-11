---
name: animus-mcp-tools
description: Animus MCP tool surface - agent, daemon, subject, workflow, queue, output, runner, skill, memory, plugin, and logs tools, including pagination and batch behavior. Use when an Animus task needs exact MCP tool names, key parameters, or tool-selection guidance.
user_invocable: false
auto_invoke: true
---

# MCP Tools

Use this skill as a router, not as a wall of tables.

## Current surface rules

- Prefer the MCP tool that performs the mutation directly instead of shelling out to `animus`.
- Every tool accepts optional `project_root` unless noted otherwise.
- Tasks and requirements use `animus.subject.*`; the old `animus.task.*` and `animus.requirements.*` families were removed.
- For task operations, pass `kind: "task"`. For requirement operations, pass `kind: "requirement"`.
- For exact parameters, open the domain reference instead of guessing from memory.

## References

- Read [references/agent-daemon-task.md](references/agent-daemon-task.md) for `animus.agent.*` (including `ask`/`request_approval` escalation), `animus.interactions.*`, `animus.daemon.*`, and `animus.subject.*`.
- Read [references/workflow-queue-requirements.md](references/workflow-queue-requirements.md) for `animus.workflow.*`, `animus.queue.*`, and requirement-as-subject patterns.
- Read [references/output-runner-and-conventions.md](references/output-runner-and-conventions.md) for `animus.output.*`, `animus.runner.*`, `animus.logs.*`, `animus.skill.*`, `animus.memory.*`, `animus.plugin.*`, pagination, batch behavior, and shared conventions.

## Quick routing

- Use `animus.subject.*` for task, requirement, Linear, Jira, GitHub Issue, or other subject lifecycle changes.
- Use `animus.queue.*` for dispatch order and hold or release behavior.
- Use `animus.workflow.*` for runs, definitions, approvals, prompts, and checkpoints.
- Use `animus.output.*` for run output, JSONL, artifacts, and phase outputs.
- Use `animus.logs.*` for daemon/log-storage-backed log tailing.
- Use `animus.daemon.*` for scheduler runtime state.
- Use `animus.runner.*` for orphan and health checks.
- Use `animus.agent.ask` or `animus.agent.request_approval` to escalate to a human; both block until answered or timed out.
- Use `animus.interactions.*` to read and answer the escalation inbox (requires `animus mcp serve --management`).
- Use `animus.skill.*` to list, resolve, search, or author project skills.
- Use `animus.plugin.*` to inspect or manage installed STDIO plugins.

If an older instruction says to call `animus.task.*` or `animus.requirements.*`,
translate it to `animus.subject.*` before acting.
