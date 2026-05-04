---
name: mcp-tools
description: Animus MCP tool surface - agent, daemon, task, workflow, queue, requirement, output, and runner tools, including pagination and batch behavior. Use when an Animus task needs exact MCP tool names, key parameters, or tool-selection guidance.
user_invocable: false
auto_invoke: true
---

# Animus MCP Tools

Use this skill as a router, not as a wall of tables.

Open only the reference file that matches the operation:

- Read [references/agent-daemon-task.md](references/agent-daemon-task.md) for `animus.agent.*`, `animus.daemon.*`, and `animus.task.*`.
- Read [references/workflow-queue-requirements.md](references/workflow-queue-requirements.md) for `animus.workflow.*`, `animus.queue.*`, and `animus.requirements.*`.
- Read [references/output-runner-and-conventions.md](references/output-runner-and-conventions.md) for `animus.output.*`, `animus.runner.*`, pagination, batch behavior, and shared conventions.

## Rules

1. Prefer the MCP tool that performs the mutation directly instead of shelling out to `animus`.
2. Treat destructive tools as explicit actions and pass confirmation fields when required.
3. Remember that every tool accepts optional `project_root`.
4. For lists, use pagination fields instead of assuming unbounded results.
5. For batch tools, decide whether `on_error` should be `continue` or `stop`.

## Common routing

- Use `animus.task.*` for task lifecycle changes.
- Use `animus.queue.*` for dispatch order and hold or release behavior.
- Use `animus.workflow.*` for runs, definitions, approvals, and checkpoints.
- Use `animus.output.*` for logs, event streams, and phase outputs.
- Use `animus.daemon.*` for scheduler runtime state.
- Use `animus.runner.*` for orphan and health checks.

If you need exact parameters, open the domain reference instead of guessing from memory.
