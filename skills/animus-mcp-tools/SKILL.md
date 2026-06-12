---
name: animus-mcp-tools
description: Animus MCP tool surface - agent, daemon, subject, workflow, queue, output, plugin, and skill tools, including pagination and batch behavior. Use when an Animus task needs exact MCP tool names, key parameters, or tool-selection guidance.
user_invocable: false
auto_invoke: true
---

# Animus MCP Tools

Use this skill as a router, not as a wall of tables.

Open only the reference file that matches the operation:

- Read [references/agent-daemon-task.md](references/agent-daemon-task.md) for `animus.agent.*`, `animus.daemon.*`, and `animus.subject.*`.
- Read [references/workflow-queue-requirements.md](references/workflow-queue-requirements.md) for `animus.workflow.*` and `animus.queue.*`.
- Read [references/output-runner-and-conventions.md](references/output-runner-and-conventions.md) for `animus.output.*`, pagination, batch behavior, and shared conventions.

## Rules

1. Prefer the MCP tool that performs the mutation directly instead of shelling out to `animus`.
2. Treat destructive tools as explicit actions and pass confirmation fields when required.
3. Most project-scoped tools accept optional `project_root` (the blocking `animus.agent.ask` / `animus.agent.request_approval` escalation tools do not).
4. For lists, use pagination fields instead of assuming unbounded results.
5. For batch tools, decide whether `on_error` should be `continue` or `stop`.

## Common routing

- Use `animus.subject.*` with `kind=task` or `kind=requirement` for task and requirement lifecycle changes (the `animus.task.*` / `animus.requirements.*` families were removed in v0.4.4).
- Use `animus.queue.*` for dispatch order and hold or release behavior.
- Use `animus.workflow.*` for runs, definitions, approvals, and checkpoints.
- Use `animus.output.*` for logs, event streams, and phase outputs.
- Use `animus.daemon.*` for scheduler runtime state.
- Runner tools were removed in v0.5.13: use `animus.plugin.list`/`animus plugin status` for provider health and `animus doctor --check orphan_cli_processes` for orphan cleanup.

If you need exact parameters, open the domain reference instead of guessing from memory.
